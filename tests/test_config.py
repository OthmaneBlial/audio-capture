import json
import stat
import tempfile
import unittest
from pathlib import Path

from config import ConfigError, ConfigManager


class ConfigManagerTests(unittest.TestCase):
    def test_environment_overrides_saved_api_key_without_overwriting_it(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            config = ConfigManager(Path(temporary_directory), environ={})
            config.update({"api_key": "saved-key-12345", "language": "fr"})

            overridden = ConfigManager(
                Path(temporary_directory), environ={"GROQ_API_KEY": "environment-key-12345"}
            )

            self.assertEqual(overridden.get("api_key"), "environment-key-12345")
            self.assertEqual(overridden.saved_value("api_key"), "saved-key-12345")
            self.assertEqual(overridden.source_for("api_key"), "environment")
            self.assertEqual(overridden.get("language"), "fr")

    def test_save_is_atomic_json_with_private_permissions(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            config = ConfigManager(Path(temporary_directory), environ={})
            config.update({"font_size": 21, "opacity": 0.8})

            payload = json.loads(config.path.read_text(encoding="utf-8"))
            self.assertEqual(payload["font_size"], 21)
            self.assertEqual(payload["opacity"], 0.8)
            self.assertEqual(stat.S_IMODE(config.path.stat().st_mode), 0o600)

    def test_invalid_values_are_rejected_and_corrupt_file_falls_back_to_defaults(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            config_directory = Path(temporary_directory)
            config = ConfigManager(config_directory, environ={})
            with self.assertRaises(ConfigError):
                config.set("font_size", 99)

            config_directory.mkdir(exist_ok=True)
            (config_directory / "config.json").write_text('{"font_size":"huge"}', encoding="utf-8")
            recovered = ConfigManager(config_directory, environ={})
            self.assertEqual(recovered.get("font_size"), ConfigManager.DEFAULT_CONFIG["font_size"])

    def test_unknown_setting_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            config = ConfigManager(Path(temporary_directory), environ={})
            with self.assertRaises(ConfigError):
                config.get("not-a-setting")

    def test_input_device_preference_round_trips_and_rejects_invalid_indexes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            config_directory = Path(temporary_directory)
            config = ConfigManager(config_directory, environ={})
            config.set("input_device_index", 4)

            reloaded = ConfigManager(config_directory, environ={})
            self.assertEqual(reloaded.get("input_device_index"), 4)

            for invalid in (-1, True, "4"):
                with self.assertRaises(ConfigError):
                    config.set("input_device_index", invalid)

    def test_onboarding_completion_is_explicit_and_boolean(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            config = ConfigManager(Path(temporary_directory), environ={})
            self.assertFalse(config.get("onboarding_complete"))

            config.set("onboarding_complete", True)
            self.assertTrue(ConfigManager(Path(temporary_directory), environ={}).get("onboarding_complete"))

            for invalid in (1, "true", None):
                with self.assertRaises(ConfigError):
                    config.set("onboarding_complete", invalid)

    def test_daily_dictation_preferences_are_private_validated_and_off_by_default(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            config = ConfigManager(Path(temporary_directory), environ={})
            self.assertFalse(config.get("copy_on_final"))
            self.assertFalse(config.get("history_enabled"))
            self.assertEqual(config.get("capture_mode"), "toggle")
            config.update(
                {
                    "copy_on_final": True,
                    "history_enabled": True,
                    "history_retention_days": 14,
                    "capture_mode": "push_to_talk",
                }
            )
            reloaded = ConfigManager(Path(temporary_directory), environ={})
            self.assertTrue(reloaded.get("copy_on_final"))
            self.assertEqual(reloaded.get("history_retention_days"), 14)
            for key, invalid in (
                ("history_retention_days", 0),
                ("history_retention_days", 366),
                ("capture_mode", "global"),
                ("copy_on_final", 1),
            ):
                with self.assertRaises(ConfigError):
                    config.set(key, invalid)

    def test_provider_choice_and_local_paths_are_validated(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            config = ConfigManager(Path(temporary_directory), environ={})
            self.assertEqual(config.get("provider_mode"), "groq")
            config.update(
                {
                    "provider_mode": "local_whisper_cpp",
                    "local_binary_path": " /opt/whisper-cli ",
                    "local_model_path": " /models/ggml.bin ",
                }
            )
            self.assertEqual(config.get("local_binary_path"), "/opt/whisper-cli")
            with self.assertRaises(ConfigError):
                config.set("provider_mode", "mystery")
