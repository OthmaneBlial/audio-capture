"""Small provider contract shared by cloud and experimental local backends."""

from __future__ import annotations

import itertools
import threading
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
TranscriptionResultCallback = Callable[[str, str], None]
ErrorCallback = Callable[[Exception], None]
RequestStateCallback = Callable[[str, str, Optional[str]], None]


class OrderedResultBuffer:
    """Release asynchronous text results in their submission order.

    Providers may run multiple HTTP or local workers, but the transcript is a
    linear document. The buffer retains only a bounded set of in-flight result
    metadata; callers must register and complete every accepted request.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._sequences = itertools.count(1)
        self._request_sequences: dict[str, int] = {}
        self._completed: dict[int, tuple[str, Optional[str], str, str]] = {}
        self._next_to_release = 1

    def register(self, request_id: str) -> None:
        with self._lock:
            if request_id in self._request_sequences:
                raise ValueError(f"request already registered: {request_id}")
            self._request_sequences[request_id] = next(self._sequences)

    def complete(
        self,
        request_id: str,
        text: Optional[str],
        state: str = "complete",
        detail: str = "Added to transcript",
    ) -> list[tuple[str, Optional[str], str, str]]:
        """Mark a request complete and return every newly releasable result."""
        with self._lock:
            sequence = self._request_sequences.pop(request_id, None)
            if sequence is None:
                return []
            self._completed[sequence] = (request_id, text, state, detail)
            ready: list[tuple[str, Optional[str], str, str]] = []
            while self._next_to_release in self._completed:
                ready.append(self._completed.pop(self._next_to_release))
                self._next_to_release += 1
            return ready
