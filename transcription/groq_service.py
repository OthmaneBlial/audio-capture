"""Bounded Groq Whisper transcription service."""

from __future__ import annotations

import io
import itertools
import logging
import threading
import wave
from concurrent.futures import Future, ThreadPoolExecutor
from typing import Callable, Optional

from .groq_transport import GroqHTTPTransport
from .provider import ProviderBoundary, ProviderCapabilities, ProviderError

LOGGER = logging.getLogger(__name__)


class TranscriptionError(ProviderError):
    """An actionable error returned by the speech-to-text boundary."""


class GroqTranscriptionService:
    """Convert short PCM speech segments to text using Groq's Whisper endpoint.

    The service keeps at most ``max_pending_requests`` work items in memory and
    has a small worker pool. This protects a long speaking session from creating
    an unbounded number of API threads when the network is slow or rate limited.
    """

    MODEL = "whisper-large-v3-turbo"
    MAX_AUDIO_BYTES = 5_120_000  # 160 seconds at 16 kHz mono, 16-bit PCM
    provider_id = "groq"
    capabilities = ProviderCapabilities(
        provider_id=provider_id,
        display_name="Groq cloud",
        transcription=True,
        translation_to_english=True,
        automatic_language=True,
        supported_languages=("auto", "en", "fr", "es", "de", "it", "pt", "ar", "zh"),
        language_notes="Languages exposed by the current application UI.",
        cancellation="Queued requests can be cancelled; an active HTTP request ends at its timeout.",
        limits="Four in-memory requests maximum; provider account limits also apply.",
    )
    boundary = ProviderBoundary(
        label="Groq cloud",
        audio_destination="Completed speech segment sent to Groq over HTTPS",
        credential="User-managed Groq API key",
        storage_statement="This app does not save raw audio; provider handling follows the user's account and current policy.",
    )

    def __init__(
        self,
        api_key: Optional[str] = None,
        sample_rate: int = 16000,
        channels: int = 1,
        sample_width: int = 2,
        language: Optional[str] = None,
        on_transcription: Optional[Callable[[str], None]] = None,
        on_error: Optional[Callable[[Exception], None]] = None,
        on_request_state: Optional[Callable[[str, str, Optional[str]], None]] = None,
        *,
        max_workers: int = 2,
        max_pending_requests: int = 4,
        request_timeout_seconds: float = 25.0,
        transport_factory: Callable[..., GroqHTTPTransport] = GroqHTTPTransport,
    ) -> None:
        if sample_rate not in (8000, 16000, 32000, 48000):
            raise ValueError("sample_rate must be supported by Whisper PCM input")
        if channels != 1 or sample_width != 2:
            raise ValueError("only 16-bit mono PCM is supported")
        if max_workers < 1 or max_pending_requests < 1:
            raise ValueError("max_workers and max_pending_requests must be positive")

        self._sample_rate = sample_rate
        self._channels = channels
        self._sample_width = sample_width
        self._language: Optional[str] = None
        self._on_transcription = on_transcription
        self._on_error = on_error
        self._on_request_state = on_request_state
        self._transport_factory = transport_factory
        self._request_timeout_seconds = request_timeout_seconds
        self._lock = threading.RLock()
        self._transport: Optional[GroqHTTPTransport] = None
        self._task = "transcribe"
        self._executor = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="Transcription")
        self._pending = threading.BoundedSemaphore(max_pending_requests)
        self._futures: set[Future[Optional[str]]] = set()
        self._closed = False
        self._request_ids = itertools.count(1)
        self.update_config(api_key=api_key, language=language)

    @property
    def configured(self) -> bool:
        """Whether a usable Groq HTTP transport is available."""
        with self._lock:
            return self._transport is not None

    def update_config(
        self,
        api_key: Optional[str] = None,
        language: Optional[str] = None,
        translate: bool = False,
    ) -> None:
        """Apply runtime configuration without logging credentials."""
        with self._lock:
            if api_key is not None:
                cleaned_key = api_key.strip()
                self._transport = (
                    self._build_transport(cleaned_key) if self._is_plausible_key(cleaned_key) else None
                )
            if language is not None:
                self._language = language if language != "auto" else None
            self._task = "translate" if translate else "transcribe"

    def transcribe(self, audio_data: bytes) -> Optional[str]:
        """Transcribe PCM synchronously and report a useful error on failure."""
        try:
            self._validate_audio(audio_data)
            with self._lock:
                if self._closed:
                    raise TranscriptionError("The transcription service is shutting down.")
                transport = self._transport
                task = self._task
                language = self._language
            if transport is None:
                raise TranscriptionError(
                    "No Groq API key is configured. Add GROQ_API_KEY to your environment or save a key in Settings."
                )

            wav_buffer = self._pcm_to_wav(audio_data)
            text = transport.transcribe(
                wav_buffer.getvalue(),
                model=self.MODEL,
                language=language,
                translate=task == "translate",
            ).strip()
            if text and self._on_transcription:
                self._on_transcription(text)
            return text
        except Exception as error:
            normalized = self._normalize_error(error)
            LOGGER.warning("Transcription request failed: %s", normalized)
            if self._on_error:
                self._on_error(normalized)
            return None

    def transcribe_async(self, audio_data: bytes) -> Optional[Future[Optional[str]]]:
        """Queue a request, dropping only excess work with a clear user-facing error."""
        request_id = f"segment-{next(self._request_ids)}"
        with self._lock:
            if self._closed:
                self._report_error(TranscriptionError("The transcription service is shutting down."))
                self._notify_request(request_id, "error", "Service is shutting down")
                return None
        if not self._pending.acquire(blocking=False):
            self._report_error(
                TranscriptionError("Transcription queue is full. Please wait a moment before continuing.")
            )
            self._notify_request(request_id, "error", "Queue is full")
            return None

        self._notify_request(request_id, "pending", "Waiting for Groq")
        future = self._executor.submit(self.transcribe, audio_data)
        with self._lock:
            self._futures.add(future)
        future.add_done_callback(lambda completed: self._finish_request(request_id, completed))
        return future

    def _finish_request(self, request_id: str, future: Future[Optional[str]]) -> None:
        self._pending.release()
        with self._lock:
            self._futures.discard(future)
        try:
            text = future.result()
        except Exception:
            text = None
        if text:
            self._notify_request(request_id, "complete", "Added to transcript")
        else:
            self._notify_request(request_id, "error", "Transcription failed")

    def cancel_pending(self) -> int:
        """Cancel work that has not begun; active urllib calls finish at their timeout."""
        cancelled = 0
        with self._lock:
            for future in list(self._futures):
                if future.cancel():
                    cancelled += 1
        return cancelled

    def _notify_request(self, request_id: str, state: str, detail: str) -> None:
        if self._on_request_state:
            try:
                self._on_request_state(request_id, state, detail)
            except Exception:
                LOGGER.debug("Request-state callback failed", exc_info=True)

    def close(self, wait: bool = False) -> None:
        """Stop accepting work and release worker resources."""
        with self._lock:
            if self._closed:
                return
            self._closed = True
        self.cancel_pending()
        self._executor.shutdown(wait=wait, cancel_futures=True)

    def _build_transport(self, api_key: str) -> GroqHTTPTransport:
        return self._transport_factory(api_key=api_key, timeout=self._request_timeout_seconds)

    @staticmethod
    def _is_plausible_key(api_key: str) -> bool:
        return len(api_key) >= 10 and "your_api_key" not in api_key.lower()

    def _validate_audio(self, audio_data: bytes) -> None:
        if not isinstance(audio_data, bytes) or not audio_data:
            raise TranscriptionError("No speech audio was captured. Try speaking for a little longer.")
        if len(audio_data) > self.MAX_AUDIO_BYTES:
            raise TranscriptionError("Speech segment is too long. Stop and restart listening to continue.")
        if len(audio_data) % (self._channels * self._sample_width) != 0:
            raise TranscriptionError("Captured audio is malformed. Restart listening and try again.")

    def _pcm_to_wav(self, pcm_data: bytes) -> io.BytesIO:
        buffer = io.BytesIO()
        with wave.open(buffer, "wb") as wav_file:
            wav_file.setnchannels(self._channels)
            wav_file.setsampwidth(self._sample_width)
            wav_file.setframerate(self._sample_rate)
            wav_file.writeframes(pcm_data)
        buffer.seek(0)
        return buffer

    def _normalize_error(self, error: Exception) -> Exception:
        if isinstance(error, TranscriptionError):
            return error
        message = str(error).strip()
        lowered = message.lower()
        if any(marker in lowered for marker in ("401", "authentication", "invalid api key")):
            return TranscriptionError(
                "Groq rejected the API key. Check Settings or GROQ_API_KEY and try again.",
                code="authentication",
            )
        if any(marker in lowered for marker in ("429", "rate limit")):
            return TranscriptionError(
                "Groq is rate limiting requests. Wait a few seconds, then continue.",
                code="rate_limit",
                retryable=True,
            )
        if any(marker in lowered for marker in ("timeout", "timed out", "connection")):
            return TranscriptionError(
                "Could not reach Groq. Check your connection and try again.",
                code="network",
                retryable=True,
            )
        return TranscriptionError(
            "Groq could not transcribe this segment. Try again or check the app logs.",
            code="provider_error",
            retryable=True,
        )

    def _report_error(self, error: Exception) -> None:
        LOGGER.warning("Transcription request rejected: %s", error)
        if self._on_error:
            self._on_error(error)

    def __enter__(self) -> "GroqTranscriptionService":
        return self

    def __exit__(self, _exc_type: object, _exc: object, _traceback: object) -> None:
        self.close(wait=False)
