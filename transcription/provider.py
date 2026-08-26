"""Small provider contract shared by cloud and experimental local backends."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Optional, Protocol


@dataclass(frozen=True)
class ProviderCapabilities:
    provider_id: str
    display_name: str
    transcription: bool
    translation_to_english: bool
    automatic_language: bool
    supported_languages: tuple[str, ...]
    language_notes: str
    cancellation: str
    limits: str


@dataclass(frozen=True)
class ProviderBoundary:
    label: str
    audio_destination: str
    credential: str
    storage_statement: str


class ProviderError(RuntimeError):
    """Normalized provider error with stable code and retry guidance."""

    def __init__(self, message: str, *, code: str = "provider_error", retryable: bool = False):
        super().__init__(message)
        self.code = code
        self.retryable = retryable


class TranscriptionProvider(Protocol):
    provider_id: str
    capabilities: ProviderCapabilities
    boundary: ProviderBoundary

    @property
    def configured(self) -> bool: ...

    def transcribe_async(self, audio_data: bytes): ...

    def update_config(
        self,
        api_key: Optional[str] = None,
        language: Optional[str] = None,
        translate: bool = False,
    ) -> None: ...

    def cancel_pending(self) -> int: ...

    def close(self, wait: bool = False) -> None: ...


TranscriptionCallback = Callable[[str], None]
ErrorCallback = Callable[[Exception], None]
RequestStateCallback = Callable[[str, str, Optional[str]], None]
