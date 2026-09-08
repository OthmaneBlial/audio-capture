//! Opt-in, bounded transcript history with portable app-data locations.

use chrono::{DateTime, Duration, Utc};
use serde::{Deserialize, Serialize};
use std::fs;
use std::path::{Path, PathBuf};
use tempfile::NamedTempFile;
use thiserror::Error;
use uuid::Uuid;

const MAX_ENTRIES: usize = 500;
const MAX_TEXT_CHARS: usize = 100_000;
const MAX_TOTAL_CHARS: usize = 500_000;

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct HistoryEntry {
    pub id: Uuid,
    pub created_at: DateTime<Utc>,
    pub text: String,
}

#[derive(Debug, Serialize, Deserialize)]
struct HistoryFile {
    schema_version: u8,
    entries: Vec<HistoryEntry>,
}

#[derive(Debug, Error)]
pub enum HistoryError {
    #[error("history I/O failed: {0}")]
    Io(#[from] std::io::Error),
    #[error("history JSON is invalid: {0}")]
    Json(#[from] serde_json::Error),
    #[error("history cannot be trusted: {0}")]
    Invalid(String),
}

#[derive(Debug, Clone)]
pub struct HistoryStore {
    directory: PathBuf,
    file: PathBuf,
}

impl HistoryStore {
    pub fn at(directory: impl AsRef<Path>) -> Self {
        let directory = directory.as_ref().to_path_buf();
        Self {
            file: directory.join("history.json"),
            directory,
        }
    }

    pub fn path(&self) -> &Path {
        &self.file
    }

    pub fn list(&self, retention_days: u32) -> Result<Vec<HistoryEntry>, HistoryError> {
        validate_retention(retention_days)?;
        let mut entries = self.read()?;
        let cutoff = Utc::now() - Duration::days(i64::from(retention_days));
        entries.retain(|entry| entry.created_at >= cutoff);
        let bounded = bounded(entries);
        Ok(bounded.into_iter().rev().collect())
    }

    pub fn add(&self, text: &str, retention_days: u32) -> Result<HistoryEntry, HistoryError> {
        validate_retention(retention_days)?;
        let clean = text.trim();
        if clean.is_empty() {
            return Err(HistoryError::Invalid(
                "history text must not be empty".into(),
            ));
        }
        if clean.chars().count() > MAX_TEXT_CHARS {
            return Err(HistoryError::Invalid("history entry is too large".into()));
        }
        let mut entries = self.read()?;
        if let Some(previous) = entries.last() {
            if previous.text == clean {
                return Ok(previous.clone());
            }
        }
        let entry = HistoryEntry {
            id: Uuid::new_v4(),
            created_at: Utc::now(),
            text: clean.to_owned(),
        };
        entries.push(entry.clone());
        self.write(&bounded(entries))?;
        Ok(entry)
    }

    pub fn delete(&self, id: Uuid) -> Result<bool, HistoryError> {
        let mut entries = self.read()?;
        let original = entries.len();
        entries.retain(|entry| entry.id != id);
        if entries.len() == original {
            return Ok(false);
        }
        self.write(&entries)?;
        Ok(true)
    }

    pub fn clear(&self) -> Result<(), HistoryError> {
        if self.file.exists() {
            fs::remove_file(&self.file)?;
        }
        let _ = fs::remove_dir(&self.directory);
        Ok(())
    }

    fn read(&self) -> Result<Vec<HistoryEntry>, HistoryError> {
        if self.file.is_symlink() {
            return Err(HistoryError::Invalid(
                "history file is a symbolic link".into(),
            ));
        }
        if !self.file.exists() {
            return Ok(Vec::new());
        }
        let bytes = fs::read(&self.file)?;
        if bytes.len() > 5_000_000 {
            return Err(HistoryError::Invalid(
                "history file exceeds safety limit".into(),
            ));
        }
        let payload: HistoryFile = serde_json::from_slice(&bytes)?;
        if payload.schema_version != 1 {
            return Err(HistoryError::Invalid("unsupported history schema".into()));
        }
        if payload
            .entries
            .iter()
            .any(|entry| entry.text.trim().is_empty())
        {
            return Err(HistoryError::Invalid(
                "history contains an empty entry".into(),
            ));
        }
        Ok(payload.entries)
    }

    fn write(&self, entries: &[HistoryEntry]) -> Result<(), HistoryError> {
        fs::create_dir_all(&self.directory)?;
        let payload = HistoryFile {
            schema_version: 1,
            entries: entries.to_vec(),
        };
        let bytes = serde_json::to_vec_pretty(&payload)?;
        let mut temporary = NamedTempFile::new_in(&self.directory)?;
        use std::io::Write;
        temporary.write_all(&bytes)?;
        temporary.write_all(b"\n")?;
        temporary.as_file().sync_all()?;
        temporary
            .persist(&self.file)
            .map_err(|error| HistoryError::Io(error.error))?;
        Ok(())
    }
}

fn validate_retention(days: u32) -> Result<(), HistoryError> {
    if !(1..=365).contains(&days) {
        return Err(HistoryError::Invalid(
            "retention must be between 1 and 365 days".into(),
        ));
    }
    Ok(())
}

fn bounded(mut entries: Vec<HistoryEntry>) -> Vec<HistoryEntry> {
    let mut chars = 0;
    while entries.len() > MAX_ENTRIES || chars > MAX_TOTAL_CHARS {
        if let Some(removed) = entries.first() {
            chars = chars.saturating_sub(removed.text.chars().count());
        }
        entries.remove(0);
    }
    entries
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn history_is_opt_in_at_call_site_and_bounded() {
        let temporary = tempfile::tempdir().unwrap();
        let store = HistoryStore::at(temporary.path().join("history"));
        for index in 0..550 {
            store.add(&format!("entry-{index}"), 30).unwrap();
        }
        assert_eq!(store.list(30).unwrap().len(), MAX_ENTRIES);
    }

    #[test]
    fn entries_can_be_deleted_and_cleared() {
        let temporary = tempfile::tempdir().unwrap();
        let store = HistoryStore::at(temporary.path().join("history"));
        let entry = store.add("keep me", 30).unwrap();
        assert!(store.delete(entry.id).unwrap());
        assert!(store.list(30).unwrap().is_empty());
        store.add("remove me", 30).unwrap();
        store.clear().unwrap();
        assert!(!store.path().exists());
    }
}
