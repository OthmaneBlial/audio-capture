"""Deterministic fake TranscriptionProvider for contract tests.

Test-only: no sockets, microphones, API keys, subprocesses, or local models.
Synthetic PCM/text only; request-state tracking never stores audio or transcripts.
"""

from __future__ import annotations

import itertools
import threading
from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import dataclass
from typing import Callable, List, Optional, Sequence, Union

from transcription.provider import (
    ProviderBoundary,
    ProviderCapabilities,
    ProviderError,
)

Outcome = Union[str, BaseException, None]


@dataclass(frozen=True)
class FakeProviderConfig:
    """Optional knobs for a single fake-provider instance."""

    provider_id: str = "fake"
    display_name: str = "Fake provider (test)"
    transcription: bool = True
    translation_to_english: bool = True
    automatic_language: bool = True
    supported_languages: tuple = (
        "auto",
        "en",
        "fr",
        "es",
        "de",
        "it",
        "pt",
        "ar",
        "zh",
    )
    language_notes: str = "Synthetic languages for contract tests only."
    cancellation: str = "Queued requests can be cancelled before a worker starts."
    limits: str = "Bounded in-memory queue; no network or native audio."
    boundary_label: str = "Fake test boundary"
    audio_destination: str = "Discarded in-process; never leaves the test runner"
    credential: str = "None"
    storage_statement: str = "No PCM, transcript, or credential is retained by the fixture."
    max_workers: int = 1
    max_pending_requests: int = 4
    configured: bool = True
    default_text: str = "test transcript"


@dataclass(frozen=True)
class RequestRecord:
    """In-memory request metadata without PCM or transcript content."""

    request_id: str
    audio_byte_length: int
    state: str
    detail: str
    language: Optional[str] = None
    translate: bool = False


class FakeTranscriptionProvider:
    """A TranscriptionProvider double with deterministic lifecycle outcomes.

    Use this fixture when a test needs the shared provider contract
    (capabilities, boundary wording, queue, cancellation, normalized errors,
    request-state callbacks) without opening a socket or microphone.
    """

    MAX_AUDIO_BYTES = 5_120_000

    def __init__(
        self,
        config: Optional[FakeProviderConfig] = None,
        *,
        outcomes: Optional[Sequence[Outcome]] = None,
        hold_event: Optional[threading.Event] = None,
        on_transcription: Optional[Callable[[str], None]] = None,
        on_error: Optional[Callable[[Exception], None]] = None,
        on_request_state: Optional[Callable[[str, str, Optional[str]], None]] = None,
    ) -> None:
        self._config = config or FakeProviderConfig()
        if self._config.max_workers < 1 or self._config.max_pending_requests < 1:
            raise ValueError("max_workers and max_pending_requests must be positive")

        self.provider_id = self._config.provider_id
        self.capabilities = ProviderCapabilities(
            provider_id=self._config.provider_id,
            display_name=self._config.display_name,
            transcription=self._config.transcription,
            translation_to_english=self._config.translation_to_english,
            automatic_language=self._config.automatic_language,
            supported_languages=tuple(self._config.supported_languages),
            language_notes=self._config.language_notes,
            cancellation=self._config.cancellation,
            limits=self._config.limits,
        )
        self.boundary = ProviderBoundary(
            label=self._config.boundary_label,
            audio_destination=self._config.audio_destination,
            credential=self._config.credential,
            storage_statement=self._config.storage_statement,
        )

        self._configured = self._config.configured
        self._default_text = self._config.default_text
        self._outcomes: List[Outcome] = list(outcomes) if outcomes is not None else []
        self._hold_event = hold_event
        self._on_transcription = on_transcription
        self._on_error = on_error
        self._on_request_state = on_request_state

        self._language: Optional[str] = None
        self._translate = False
        self._lock = threading.RLock()
        self._executor = ThreadPoolExecutor(
            max_workers=self._config.max_workers,
            thread_name_prefix="FakeProvider",
        )
        self._pending = threading.BoundedSemaphore(self._config.max_pending_requests)
        self._futures: set = set()
        self._request_ids = itertools.count(1)
        self._closed = False
        self._requests: List[RequestRecord] = []
        self.submitted_audio_lengths: List[int] = []

    @property
    def configured(self) -> bool:
        return self._configured and not self._closed

    def set_configured(self, value: bool) -> None:
        """Toggle readiness without requiring a real credential or binary."""
        with self._lock:
            self._configured = value

    def update_config(
        self,
        api_key: Optional[str] = None,
        language: Optional[str] = None,
        translate: bool = False,
    ) -> None:
        del api_key  # accepted for protocol compatibility; never stored
        with self._lock:
            if language is not None:
                self._language = None if language == "auto" else language
            self._translate = bool(translate)

    def request_records(self) -> tuple:
        """Return request metadata snapshots (no PCM or transcript text)."""
        with self._lock:
            return tuple(self._requests)

    def transcribe(self, audio_data: bytes) -> Optional[str]:
        """Run one synthetic transcription synchronously."""
        try:
            self._validate_audio(audio_data)
            with self._lock:
                if self._closed:
                    raise ProviderError(
                        "The fake transcription service is shutting down.",
                        code="shutdown",
                    )
                if not self._configured:
                    raise ProviderError(
                        "Fake provider is not configured.",
                        code="not_configured",
                    )
                language = self._language
                translate = self._translate
            text = self._next_outcome()
            if isinstance(text, BaseException):
                raise text
            if text is None:
                text = self._default_text
            assert isinstance(text, str)
            if translate and language and language != "en":
                # Deterministic marker only; not real translation.
                text = "en:" + text
            if text and self._on_transcription:
                self._on_transcription(text)
            return text
        except Exception as error:
            normalized = self._normalize_error(error)
            if self._on_error:
                self._on_error(normalized)
            return None

    def transcribe_async(self, audio_data: bytes) -> Optional[Future]:
        """Queue work with the same bounded pending contract as real providers."""
        request_id = "fake-%s" % (next(self._request_ids),)
        audio_len = len(audio_data) if isinstance(audio_data, (bytes, bytearray)) else -1
        self.submitted_audio_lengths.append(audio_len)

        with self._lock:
            language = self._language
            translate = self._translate
            if self._closed:
                self._record_and_notify(
                    request_id,
                    audio_len,
                    "error",
                    "Service is shutting down",
                    language=language,
                    translate=translate,
                )
                self._report_error(
                    ProviderError(
                        "The fake transcription service is shutting down.",
                        code="shutdown",
                    )
                )
                return None

        if not self._pending.acquire(blocking=False):
            self._record_and_notify(
                request_id,
                audio_len,
                "error",
                "Queue is full",
                language=language,
                translate=translate,
            )
            self._report_error(
                ProviderError(
                    "Transcription queue is full. Please wait a moment before continuing.",
                    code="queue_full",
                    retryable=True,
                )
            )
            return None

        self._record_and_notify(
            request_id,
            audio_len,
            "pending",
            "Waiting for fake provider",
            language=language,
            translate=translate,
        )
        future = self._executor.submit(self._run_async_body, bytes(audio_data))
        with self._lock:
            self._futures.add(future)

        def _done(completed: Future) -> None:
            self._finish_request(request_id, audio_len, completed)

        future.add_done_callback(_done)
        return future

    def cancel_pending(self) -> int:
        """Cancel work that has not begun; in-flight hold_event work finishes."""
        cancelled = 0
        with self._lock:
            for future in list(self._futures):
                if future.cancel():
                    cancelled += 1
        return cancelled

    def close(self, wait: bool = False) -> None:
        with self._lock:
            if self._closed:
                return
            self._closed = True
        self.cancel_pending()
        self._executor.shutdown(wait=wait, cancel_futures=True)

    def _run_async_body(self, audio_data: bytes) -> Optional[str]:
        if self._hold_event is not None:
            self._hold_event.wait(timeout=5)
        return self.transcribe(audio_data)

    def _finish_request(
        self,
        request_id: str,
        audio_len: int,
        future: Future,
    ) -> None:
        try:
            if future.cancelled():
                self._record_and_notify(
                    request_id,
                    audio_len,
                    "cancelled",
                    "Request cancelled",
                )
                return
            try:
                text = future.result()
            except Exception:
                text = None
            if text:
                # Detail must never echo transcript content.
                self._record_and_notify(
                    request_id,
                    audio_len,
                    "complete",
                    "Added to transcript",
                )
            else:
                self._record_and_notify(
                    request_id,
                    audio_len,
                    "error",
                    "Transcription failed",
                )
        finally:
            with self._lock:
                self._futures.discard(future)
            try:
                self._pending.release()
            except ValueError:
                pass

    def _next_outcome(self) -> Outcome:
        with self._lock:
            if self._outcomes:
                return self._outcomes.pop(0)
        return self._default_text

    def _validate_audio(self, audio_data: bytes) -> None:
        if not isinstance(audio_data, (bytes, bytearray)) or not audio_data:
            raise ProviderError(
                "No speech audio was captured. Try speaking for a little longer.",
                code="invalid_audio",
            )
        if len(audio_data) > self.MAX_AUDIO_BYTES:
            raise ProviderError(
                "Speech segment is too long. Stop and restart listening to continue.",
                code="audio_too_long",
            )
        if len(audio_data) % 2 != 0:
            raise ProviderError(
                "Captured audio is malformed. Restart listening and try again.",
                code="invalid_audio",
            )

    def _normalize_error(self, error: Exception) -> Exception:
        if isinstance(error, ProviderError):
            return error
        message = str(error).strip().lower()
        if any(marker in message for marker in ("401", "authentication", "invalid api key")):
            return ProviderError(
                "Provider rejected authentication. Check credentials and try again.",
                code="authentication",
            )
        if any(marker in message for marker in ("429", "rate limit")):
            return ProviderError(
                "Provider is rate limiting requests. Wait a few seconds, then continue.",
                code="rate_limit",
                retryable=True,
            )
        if any(marker in message for marker in ("timeout", "timed out", "connection")):
            return ProviderError(
                "Could not reach the provider. Check your connection and try again.",
                code="network",
                retryable=True,
            )
        return ProviderError(
            "The provider could not transcribe this segment. Try again.",
            code="provider_error",
            retryable=True,
        )

    def _report_error(self, error: Exception) -> None:
        if self._on_error:
            self._on_error(error)

    def _record_and_notify(
        self,
        request_id: str,
        audio_byte_length: int,
        state: str,
        detail: str,
        *,
        language: Optional[str] = None,
        translate: bool = False,
    ) -> None:
        # Never retain PCM bytes or transcript text in request tracking.
        record = RequestRecord(
            request_id=request_id,
            audio_byte_length=audio_byte_length,
            state=state,
            detail=detail,
            language=language,
            translate=translate,
        )
        with self._lock:
            self._requests.append(record)
        if self._on_request_state:
            try:
                self._on_request_state(request_id, state, detail)
            except Exception:
                pass

    def __enter__(self) -> "FakeTranscriptionProvider":
        return self

    def __exit__(self, _exc_type: object, _exc: object, _traceback: object) -> None:
        self.close(wait=False)
