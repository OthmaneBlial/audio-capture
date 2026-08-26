"""Transcription providers and their explicit capability/data contracts."""

from .groq_service import GroqTranscriptionService, TranscriptionError
from .provider import ProviderBoundary, ProviderCapabilities, ProviderError, TranscriptionProvider

__all__ = [
    "GroqTranscriptionService",
    "ProviderBoundary",
    "ProviderCapabilities",
    "ProviderError",
    "TranscriptionError",
    "TranscriptionProvider",
]
