import json
import stat
import tempfile
import unittest
from dataclasses import dataclass
from pathlib import Path

from config import ConfigManager
from diagnostics import collect_diagnostics, diagnostics_json, format_diagnostics


@dataclass
class FakeDevice:
    index: int
    is_default: bool = False


class DiagnosticsTests(unittest.TestCase):
    def _config(self, directory: str, **values: object) -> ConfigManager:
        config = ConfigManager(Path(directory), environ={})
        if values:
            config.update(values)
        return config

    def test_ready_report_does_not_contact_provider_or_expose_key(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            secret = "gsk-super-secret-value"
            config = self._config(directory, api_key=secret, input_device_index=7)
            provider_calls: list[str] = []

            report = collect_diagnostics(
                config,
                app_version="test",
                environ={"XDG_SESSION_TYPE": "wayland"},
                system_name="Linux",
                release_info={"ID": "ubuntu", "PRETTY_NAME": "Ubuntu Test"},
                gtk_probe=lambda: "3.24.0",
                device_probe=lambda: [FakeDevice(7, True)],
                provider_probe=lambda key: provider_calls.append(key) or ("pass", "reachable"),
            )

            self.assertTrue(report["ready"])
            self.assertEqual(report["checks"]["provider"]["status"], "skip")
            self.assertEqual(provider_calls, [])
            self.assertNotIn(secret, diagnostics_json(report))
            self.assertNotIn(secret, format_diagnostics(report))

    def test_explicit_provider_probe_is_reported_without_key_material(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            secret = "gsk-another-secret"
            config = self._config(directory, api_key=secret)
            calls: list[str] = []

            report = collect_diagnostics(
                config,
                app_version="test",
                probe_provider=True,
                environ={"XDG_SESSION_TYPE": "x11"},
                system_name="Linux",
                release_info={"ID": "debian", "PRETTY_NAME": "Debian Test"},
                gtk_probe=lambda: "3.24.1",
                device_probe=lambda: [FakeDevice(1, True)],
                provider_probe=lambda key: calls.append(key) or ("pass", "Groq accepted the credential."),
            )

            self.assertEqual(calls, [secret])
            self.assertTrue(report["checks"]["provider"]["contacted"])
            self.assertNotIn(secret, json.dumps(report))

    def test_missing_native_dependencies_and_key_produce_actions(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            config = self._config(directory, input_device_index=9)

            def missing_gtk() -> str:
                raise ImportError("no gi")

            def missing_audio() -> list[FakeDevice]:
                raise RuntimeError("no portaudio")

            report = collect_diagnostics(
                config,
                app_version="test",
                environ={},
                system_name="Darwin",
                release_info={},
                gtk_probe=missing_gtk,
                device_probe=missing_audio,
            )

            self.assertFalse(report["ready"])
            self.assertEqual(report["checks"]["platform"]["status"], "fail")
            self.assertEqual(report["checks"]["gtk"]["error_type"], "ImportError")
            self.assertEqual(report["checks"]["microphones"]["error_type"], "RuntimeError")
            self.assertFalse(report["checks"]["configuration"]["api_key_present"])
            self.assertGreaterEqual(len(report["next_actions"]), 4)

    def test_unproven_linux_distribution_is_warning_not_false_support(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            config = self._config(directory, api_key="gsk-valid-test-key")
            report = collect_diagnostics(
                config,
                app_version="test",
                environ={"DISPLAY": ":0"},
                system_name="Linux",
                release_info={"ID": "fedora", "PRETTY_NAME": "Fedora Test"},
                gtk_probe=lambda: "3.24.0",
                device_probe=lambda: [FakeDevice(2, True)],
            )

            self.assertTrue(report["ready"])
            self.assertEqual(report["checks"]["platform"]["status"], "warn")
            self.assertEqual(report["checks"]["desktop_session"]["session_type"], "x11")

    def test_saved_unavailable_microphone_fails_readiness(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            config = self._config(
                directory,
                api_key="gsk-valid-test-key",
                input_device_index=4,
            )
            report = collect_diagnostics(
                config,
                app_version="test",
                environ={"XDG_SESSION_TYPE": "x11"},
                system_name="Linux",
                release_info={"ID": "ubuntu"},
                gtk_probe=lambda: "3.24.0",
                device_probe=lambda: [FakeDevice(1, True)],
            )

            self.assertFalse(report["ready"])
            self.assertEqual(report["checks"]["selected_microphone"]["status"], "fail")

    def test_local_provider_diagnostics_validate_files_without_network_or_paths(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            binary = Path(directory) / "whisper-cli"
            model = Path(directory) / "ggml-model.bin"
            binary.write_text("placeholder")
            binary.chmod(stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR)
            model.write_bytes(b"model")
            config = self._config(
                directory,
                provider_mode="local_whisper_cpp",
                local_binary_path=str(binary),
                local_model_path=str(model),
            )
            provider_calls: list[str] = []
            report = collect_diagnostics(
                config,
                app_version="test",
                probe_provider=True,
                environ={
                    "XDG_SESSION_TYPE": "wayland",
                    "VOICE_TRANSCRIBER_EXPERIMENTAL_LOCAL": "1",
                },
                system_name="Linux",
                release_info={"ID": "ubuntu"},
                gtk_probe=lambda: "3.24.0",
                device_probe=lambda: [FakeDevice(1, True)],
                provider_probe=lambda key: provider_calls.append(key) or ("pass", "unexpected"),
            )

            payload = diagnostics_json(report)
            self.assertTrue(report["ready"])
            self.assertEqual(report["checks"]["provider"]["provider"], "local_whisper_cpp")
            self.assertFalse(report["checks"]["provider"]["contacted"])
            self.assertEqual(provider_calls, [])
            self.assertNotIn(str(binary), payload)
            self.assertNotIn(str(model), payload)
