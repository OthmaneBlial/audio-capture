import stat
import tempfile
import unittest
from pathlib import Path

from onboarding import (
    GROQ_DATA_CONTROLS_URL,
    GROQ_PROVIDER_FACTS_REVIEWED,
    GROQ_SPEECH_TO_TEXT_URL,
    OnboardingError,
    groq_cloud_disclosure,
    validate_cloud_setup,
    validate_local_setup,
)


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

    def test_cloud_disclosure_covers_retention_location_and_billing_floor(self) -> None:
        provider_facts, billing_facts = groq_cloud_disclosure()
        self.assertEqual(GROQ_PROVIDER_FACTS_REVIEWED, "2026-09-01")
        self.assertIn("not retained by default", provider_facts)
        self.assertIn("up to 30 days", provider_facts)
        self.assertIn("Zero Data Retention", provider_facts)
        self.assertIn("US GCP", provider_facts)
        self.assertIn("10-second minimum billed length", billing_facts)
        self.assertIn("separate request", billing_facts)
        self.assertTrue(GROQ_DATA_CONTROLS_URL.startswith("https://"))
        self.assertTrue(GROQ_SPEECH_TO_TEXT_URL.startswith("https://"))

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
