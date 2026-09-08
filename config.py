"""Validated, private on-disk configuration for Voice Transcriber."""

from __future__ import annotations

import json
import logging
import os
import tempfile
from collections.abc import Mapping
from pathlib import Path
from typing import Any, Optional

LOGGER = logging.getLogger(__name__)


class ConfigError(ValueError):
    """Raised when a configuration value cannot be used safely."""


class ConfigManager:
    """Manage settings with explicit defaults, file, and environment precedence.

    Precedence is ``defaults < config file < environment``. The settings file is
    atomically replaced with owner-only permissions so a saved API key is never
    accidentally written as a world-readable file on a typical Linux desktop.
    """

    DEFAULT_CONFIG: dict[str, Any] = {
        "api_key": "",
        "cloud_boundary_confirmed": False,
        "font_size": 17,
        "language": "auto",
        "translate_to_english": False,
        "opacity": 1.0,
        "window_width": 560,
        "window_height": 520,
        "sticky_mode": False,
        "input_device_index": None,
        "input_device_identity": "",
        "onboarding_complete": False,
        "capture_mode": "toggle",
        "copy_on_final": False,
        "history_enabled": False,
        "history_retention_days": 30,
        "provider_mode": "groq",
        "local_binary_path": "",
        "local_model_path": "",
    }
    ENVIRONMENT_KEYS = {"api_key": "GROQ_API_KEY"}
    SUPPORTED_LANGUAGES = {"auto", "en", "fr", "es", "de", "it", "pt", "ar", "zh"}

    def __init__(
        self,
        config_dir: Optional[Path] = None,
        environ: Optional[Mapping[str, str]] = None,
    ) -> None:
        self._environ = environ if environ is not None else os.environ
        if config_dir is None:
            configured_base = self._environ.get("XDG_CONFIG_HOME", "").strip()
            base_dir = (
                Path(configured_base).expanduser()
                if configured_base
                else Path.home() / ".config"
            )
            self._config_dir = base_dir / "voice-transcriber"
        else:
            self._config_dir = Path(config_dir)
        self._config_file = self._config_dir / "config.json"
        self._file_config: dict[str, Any] = {}
        self._config = self.DEFAULT_CONFIG.copy()
        self.load()

    @property
    def path(self) -> Path:
        """Return the configuration file path for diagnostics and tests."""
        return self._config_file

    def load(self) -> None:
        """Load valid settings from disk, preserving defaults for invalid values."""
        self._file_config = {}
        if not self._config_file.exists():
            self._config = self.DEFAULT_CONFIG.copy()
            return

        try:
            with self._config_file.open("r", encoding="utf-8") as config_file:
                saved_config = json.load(config_file)
            if not isinstance(saved_config, dict):
                raise ConfigError("configuration root must be a JSON object")
            self._file_config = self._validated_values(saved_config, ignore_unknown=True)
        except (OSError, json.JSONDecodeError, ConfigError) as error:
            LOGGER.warning("Ignoring invalid configuration at %s: %s", self._config_file, error)
            self._file_config = {}

        self._config = self.DEFAULT_CONFIG.copy()
        self._config.update(self._file_config)

    def save(self) -> None:
        """Atomically write user settings with owner-only permissions."""
        descriptor: Optional[int] = None
        temp_path: Optional[Path] = None
        try:
            self._config_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
            try:
                self._config_dir.chmod(0o700)
            except OSError:
                LOGGER.debug("Could not tighten permissions on %s", self._config_dir, exc_info=True)

            descriptor, temp_name = tempfile.mkstemp(
                prefix=".config-", suffix=".json", dir=self._config_dir, text=True
            )
            temp_path = Path(temp_name)
            with os.fdopen(descriptor, "w", encoding="utf-8") as config_file:
                descriptor = None
                json.dump(self._config, config_file, indent=2, sort_keys=True)
                config_file.write("\n")
                config_file.flush()
                os.fsync(config_file.fileno())
            os.chmod(temp_path, 0o600)
            os.replace(temp_path, self._config_file)
            self._file_config = self._config.copy()
        except OSError as error:
            raise ConfigError(f"Could not save settings to {self._config_file}: {error}") from error
        finally:
            if descriptor is not None:
                try:
                    os.close(descriptor)
                except OSError:
                    pass
            if temp_path is not None and temp_path.exists():
                temp_path.unlink(missing_ok=True)

    def get(self, key: str) -> Any:
        """Get a setting after applying environment-variable precedence."""
        if key not in self.DEFAULT_CONFIG:
            raise ConfigError(f"Unknown setting: {key}")
        environment_name = self.ENVIRONMENT_KEYS.get(key)
        if environment_name:
            environment_value = self._environ.get(environment_name, "").strip()
            if environment_value:
                return environment_value
        return self._config[key]

    def source_for(self, key: str) -> str:
        """Return ``environment``, ``config``, or ``default`` for a setting."""
        if key not in self.DEFAULT_CONFIG:
            raise ConfigError(f"Unknown setting: {key}")
        environment_name = self.ENVIRONMENT_KEYS.get(key)
        if environment_name and self._environ.get(environment_name, "").strip():
            return "environment"
        return "config" if key in self._file_config else "default"

    def saved_value(self, key: str) -> Any:
        """Return the configured value without applying environment overrides."""
        if key not in self.DEFAULT_CONFIG:
            raise ConfigError(f"Unknown setting: {key}")
        return self._config[key]

    def set(self, key: str, value: Any) -> None:
        """Set one validated setting and persist it."""
        self.update({key: value})

    def update(self, values: Mapping[str, Any]) -> None:
        """Persist a group of values as one atomic configuration update."""
        validated = self._validated_values(values, ignore_unknown=False)
        previous = self._config.copy()
        self._config.update(validated)
        try:
            self.save()
        except Exception:
            # A failed write must not leave the running process claiming a
            # preference that will disappear on the next restart.
            self._config = previous
            raise

    def has_api_key(self) -> bool:
        """Return whether a plausible Groq key is configured, without exposing it."""
        key = self.get("api_key")
        return isinstance(key, str) and len(key.strip()) >= 10 and "your_api_key" not in key.lower()

    def _validated_values(self, values: Mapping[str, Any], *, ignore_unknown: bool) -> dict[str, Any]:
        validated: dict[str, Any] = {}
        for key, value in values.items():
            if key not in self.DEFAULT_CONFIG:
                if ignore_unknown:
                    LOGGER.warning("Ignoring unknown setting in %s: %s", self._config_file, key)
                    continue
                raise ConfigError(f"Unknown setting: {key}")
            validated[key] = self._validate_value(key, value)
        return validated

    def _validate_value(self, key: str, value: Any) -> Any:
        if key == "api_key":
            if not isinstance(value, str):
                raise ConfigError("API key must be text")
            return value.strip()
        if key in {"local_binary_path", "local_model_path"}:
            if not isinstance(value, str):
                raise ConfigError(f"{key} must be text")
            return value.strip()
        if key == "input_device_identity":
            if not isinstance(value, str):
                raise ConfigError("input_device_identity must be text")
            identity = value.strip().lower()
            if identity and (
                len(identity) != 24 or any(character not in "0123456789abcdef" for character in identity)
            ):
                raise ConfigError("input_device_identity must be an empty string or a 24-character hex value")
            return identity
        if key == "provider_mode":
            if value not in {"groq", "local_whisper_cpp"}:
                raise ConfigError("provider_mode must be groq or local_whisper_cpp")
            return value
        if key == "language":
            if value not in self.SUPPORTED_LANGUAGES:
                raise ConfigError(f"Unsupported language: {value!r}")
            return value
        if key in {
            "translate_to_english",
            "sticky_mode",
            "onboarding_complete",
            "cloud_boundary_confirmed",
            "copy_on_final",
            "history_enabled",
        }:
            if not isinstance(value, bool):
                raise ConfigError(f"{key} must be true or false")
            return value
        if key == "font_size":
            if isinstance(value, bool) or not isinstance(value, int) or not 12 <= value <= 32:
                raise ConfigError("font_size must be an integer between 12 and 32")
            return value
        if key == "history_retention_days":
            if isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= 365:
                raise ConfigError("history_retention_days must be an integer between 1 and 365")
            return value
        if key == "capture_mode":
            if value not in {"toggle", "push_to_talk"}:
                raise ConfigError("capture_mode must be toggle or push_to_talk")
            return value
        if key == "opacity":
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not 0.5 <= value <= 1.0:
                raise ConfigError("opacity must be between 0.5 and 1.0")
            return float(value)
        if key in {"window_width", "window_height"}:
            if isinstance(value, bool) or not isinstance(value, int):
                raise ConfigError(f"{key} must be an integer")
            limits = (360, 1800) if key == "window_width" else (320, 1200)
            if not limits[0] <= value <= limits[1]:
                raise ConfigError(f"{key} must be between {limits[0]} and {limits[1]}")
            return value
        if key == "input_device_index":
            if value is None:
                return None
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise ConfigError("input_device_index must be a non-negative integer or null")
            return value
        raise ConfigError(f"Unsupported setting: {key}")
