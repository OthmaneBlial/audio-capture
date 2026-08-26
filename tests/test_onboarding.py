import unittest

from onboarding import OnboardingError, validate_cloud_setup


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
