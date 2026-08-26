"""Pure validation helpers for the first-run privacy agreement."""

from __future__ import annotations


class OnboardingError(ValueError):
    """Raised when first-run setup cannot safely enable transcription."""


def validate_cloud_setup(api_key: str, *, data_boundary_confirmed: bool) -> str:
    """Return a normalized key only after explicit cloud-boundary confirmation."""
    cleaned_key = api_key.strip()
    if len(cleaned_key) < 10 or "your_api_key" in cleaned_key.lower():
        raise OnboardingError("Add a valid Groq API key before completing setup.")
    if not data_boundary_confirmed:
        raise OnboardingError(
            "Confirm that completed speech segments will be sent to Groq before continuing."
        )
    return cleaned_key
