//! Portable, validated application configuration.

use directories::ProjectDirs;
use serde::{Deserialize, Serialize};
use std::collections::BTreeMap;
use std::env;
use std::fs;
use std::path::{Path, PathBuf};
use tempfile::NamedTempFile;
use thiserror::Error;

const APP_QUALIFIER: &str = "io.github.othmaneblial";
const APP_ORGANIZATION: &str = "OthmaneBlial";
const APP_NAME: &str = "Voice Transcriber";

#[derive(Debug, Error)]
pub enum ConfigError {
    #[error("could not read configuration: {0}")]
    Read(#[from] std::io::Error),
    #[error("configuration JSON is invalid: {0}")]
    Json(#[from] serde_json::Error),
    #[error("invalid configuration: {0}")]
    Invalid(String),
}

#[derive(Debug, Clone, Copy, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum ProviderMode {
    Groq,
    LocalWhisperCpp,
}

impl Default for ProviderMode {
    fn default() -> Self {
        Self::Groq
    }
}

#[derive(Debug, Clone, Copy, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum CaptureMode {
    Toggle,
    PushToTalk,
}

impl Default for CaptureMode {
    fn default() -> Self {
        Self::Toggle
    }
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
#[serde(default)]
pub struct AppConfig {
    pub api_key: String,
    pub cloud_boundary_confirmed: bool,
    pub font_size: u32,
    pub language: String,
    pub translate_to_english: bool,
    pub opacity: f32,
    pub window_width: u32,
    pub window_height: u32,
    pub sticky_mode: bool,
    pub input_device_index: Option<usize>,
    pub input_device_identity: String,
    pub onboarding_complete: bool,
    pub capture_mode: CaptureMode,
    pub copy_on_final: bool,
    pub history_enabled: bool,
    pub history_retention_days: u32,
    pub provider_mode: ProviderMode,
    pub local_binary_path: String,
    pub local_model_path: String,
}

impl Default for AppConfig {
    fn default() -> Self {
        Self {
            api_key: String::new(),
            cloud_boundary_confirmed: false,
            font_size: 17,
            language: "auto".into(),
            translate_to_english: false,
            opacity: 1.0,
            window_width: 760,
            window_height: 700,
            sticky_mode: false,
            input_device_index: None,
            input_device_identity: String::new(),
            onboarding_complete: false,
            capture_mode: CaptureMode::Toggle,
            copy_on_final: false,
            history_enabled: false,
            history_retention_days: 30,
            provider_mode: ProviderMode::Groq,
            local_binary_path: String::new(),
            local_model_path: String::new(),
        }
    }
}

impl AppConfig {
    pub fn validate(&self) -> Result<(), ConfigError> {
        if !(10..=72).contains(&self.font_size) {
            return Err(ConfigError::Invalid(
                "font_size must be between 10 and 72".into(),
            ));
        }
        if !(0.55..=1.0).contains(&self.opacity) {
            return Err(ConfigError::Invalid(
                "opacity must be between 0.55 and 1.0".into(),
            ));
        }
        if !(480..=4096).contains(&self.window_width) || !(360..=4096).contains(&self.window_height)
        {
            return Err(ConfigError::Invalid(
                "window dimensions are outside the safe range".into(),
            ));
        }
        if !matches!(
            self.language.as_str(),
            "auto" | "en" | "fr" | "es" | "de" | "it" | "pt" | "ar" | "zh"
        ) {
            return Err(ConfigError::Invalid(format!(
                "unsupported language: {}",
                self.language
            )));
        }
        if !(1..=365).contains(&self.history_retention_days) {
            return Err(ConfigError::Invalid(
                "history_retention_days must be between 1 and 365".into(),
            ));
        }
        if !self.input_device_identity.is_empty()
            && (self.input_device_identity.len() != 24
                || !self.input_device_identity.chars().all(|character| {
                    character.is_ascii_hexdigit() && !character.is_ascii_uppercase()
                }))
        {
            return Err(ConfigError::Invalid(
                "input_device_identity must be empty or 24 lowercase hex characters".into(),
            ));
        }
        Ok(())
    }

    pub fn has_api_key(&self, environment: &BTreeMap<String, String>) -> bool {
        let key = environment
            .get("GROQ_API_KEY")
            .filter(|value| !value.trim().is_empty())
            .map(String::as_str)
            .unwrap_or(&self.api_key);
        key.trim().len() >= 10 && !key.to_ascii_lowercase().contains("your_api_key")
    }

    pub fn effective_api_key(&self) -> String {
        env::var("GROQ_API_KEY")
            .ok()
            .filter(|value| !value.trim().is_empty())
            .unwrap_or_else(|| self.api_key.clone())
    }
}

#[derive(Debug, Clone)]
pub struct ConfigStore {
    directory: PathBuf,
    file: PathBuf,
}

impl ConfigStore {
    pub fn new() -> Result<Self, ConfigError> {
        let project_dirs = ProjectDirs::from(APP_QUALIFIER, APP_ORGANIZATION, APP_NAME)
            .ok_or_else(|| {
                ConfigError::Invalid("platform configuration directory unavailable".into())
            })?;
        Ok(Self::at(project_dirs.config_dir()))
    }

    pub fn at(directory: impl AsRef<Path>) -> Self {
        let directory = directory.as_ref().to_path_buf();
        Self {
            file: directory.join("config.json"),
            directory,
        }
    }

    pub fn path(&self) -> &Path {
        &self.file
    }

    pub fn load(&self) -> Result<AppConfig, ConfigError> {
        if !self.file.exists() {
            return Ok(AppConfig::default());
        }
        let bytes = fs::read(&self.file)?;
        let config: AppConfig = serde_json::from_slice(&bytes)?;
        config.validate()?;
        Ok(config)
    }

    pub fn save(&self, config: &AppConfig) -> Result<(), ConfigError> {
        config.validate()?;
        fs::create_dir_all(&self.directory)?;
        let serialized = serde_json::to_vec_pretty(config)?;
        let mut temporary = NamedTempFile::new_in(&self.directory)?;
        use std::io::Write;
        temporary.write_all(&serialized)?;
        temporary.write_all(b"\n")?;
        temporary.as_file().sync_all()?;
        temporary
            .persist(&self.file)
            .map_err(|error| ConfigError::Read(error.error))?;
        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::collections::BTreeMap;

    #[test]
    fn defaults_are_safe_and_provider_is_explicit() {
        let config = AppConfig::default();
        config.validate().unwrap();
        assert_eq!(config.provider_mode, ProviderMode::Groq);
        assert!(!config.cloud_boundary_confirmed);
        assert!(!config.has_api_key(&BTreeMap::new()));
    }

    #[test]
    fn save_load_is_atomic_and_round_trips() {
        let temporary = tempfile::tempdir().unwrap();
        let store = ConfigStore::at(temporary.path().join("config"));
        let mut config = AppConfig::default();
        config.input_device_identity = "abcdef0123456789abcdef01".into();
        config.language = "fr".into();
        store.save(&config).unwrap();
        assert_eq!(store.load().unwrap(), config);
        assert!(store.path().is_file());
    }

    #[test]
    fn invalid_identity_is_rejected() {
        let mut config = AppConfig::default();
        config.input_device_identity = "not-a-fingerprint".into();
        let error = config.validate().unwrap_err().to_string();
        assert!(error.contains("input_device_identity"));
    }

    #[test]
    fn environment_key_wins_without_being_persisted() {
        let mut config = AppConfig::default();
        config.api_key = "saved-key-12345".into();
        let mut environment = BTreeMap::new();
        environment.insert("GROQ_API_KEY".into(), "environment-key-12345".into());
        assert!(config.has_api_key(&environment));
        assert_eq!(config.api_key, "saved-key-12345");
    }
}
