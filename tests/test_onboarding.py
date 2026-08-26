import stat
import tempfile
import unittest
from pathlib import Path

from onboarding import OnboardingError, validate_cloud_setup, validate_local_setup


class OnboardingTests(unittest.TestCase):
    def test_cloud_setup_requires_plausible_key_and_explicit_confirmation(self) -> None:
        with self.assertRaises(OnboardingError):
            validate_cloud_setup("short", data_boundary_confirmed=True)
        with self.assertRaises(OnboardingError):
            validate_cloud_setup("gsk-valid-looking-key", data_boundary_confirmed=False)

    def test_cloud_setup_normalizes_key_after_confirmation(self) -> None:
        self.assertEqual(
            validate_cloud_setup("  gsk-valid-looking-key  ", data_boundary_confirmed=True),
            "gsk-valid-looking-key",
        )

    def test_local_setup_requires_executable_and_model(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            binary = Path(directory) / "whisper-cli"
            model = Path(directory) / "ggml-model.bin"
            binary.write_text("binary")
            model.write_bytes(b"model")
            with self.assertRaisesRegex(OnboardingError, "executable"):
                validate_local_setup(str(binary), str(model))
            binary.chmod(stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR)
            self.assertEqual(validate_local_setup(str(binary), str(model)), (str(binary), str(model)))
