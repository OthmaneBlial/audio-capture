"""Pure validation helpers for the first-run privacy agreement."""

from __future__ import annotations

import os
from pathlib import Path

GROQ_PROVIDER_FACTS_REVIEWED = "2026-09-01"
GROQ_DATA_CONTROLS_URL = "https://console.groq.com/docs/your-data"
GROQ_SPEECH_TO_TEXT_URL = "https://console.groq.com/docs/speech-to-text"


class OnboardingError(ValueError):
    """Raised when first-run setup cannot safely enable transcription."""


def groq_cloud_disclosure() -> tuple[str, str]:
    """Return dated provider facts shown before a first cloud transcription."""
    return (
        f"Provider facts reviewed {GROQ_PROVIDER_FACTS_REVIEWED}: Groq says inference input/output "
        "is not retained by default, but it may be logged for reliability or abuse review for "
        "up to 30 days. Zero Data Retention is available; retained customer data is in US GCP.",
        "Speech-to-text requests have a 10-second minimum billed length. Voice Transcriber sends "
        "each completed speech segment as a separate request, so short segments can be billed "
        "above their spoken duration.",
    )


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


def validate_local_setup(binary_path: object, model_path: object) -> tuple[str, str]:
    """Validate user-supplied experimental local runtime paths without executing them."""
    if not isinstance(binary_path, str) or not binary_path.strip():
        raise OnboardingError("Choose the whisper-cli executable for experimental local mode.")
    if not isinstance(model_path, str) or not model_path.strip():
        raise OnboardingError("Choose a GGML model file for experimental local mode.")
    binary = Path(binary_path).expanduser()
    model = Path(model_path).expanduser()
    if not binary.is_file() or not os.access(binary, os.X_OK):
        raise OnboardingError("The selected whisper-cli path is not an executable file.")
    if not model.is_file():
        raise OnboardingError("The selected GGML model path is not a file.")
    return str(binary), str(model)
