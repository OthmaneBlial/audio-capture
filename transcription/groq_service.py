"""Bounded Groq Whisper transcription service."""

from __future__ import annotations

import io
import logging
import threading
import wave
from concurrent.futures import Future, ThreadPoolExecutor
from typing import Callable, Optional

from groq import Groq

LOGGER = logging.getLogger(__name__)


class TranscriptionError(RuntimeError):
    """An actionable error returned by the speech-to-text boundary."""


class GroqTranscriptionService:
    """Convert short PCM speech segments to text using Groq's Whisper endpoint.

    The service keeps at most ``max_pending_requests`` work items in memory and
    has a small worker pool. This protects a long speaking session from creating
    an unbounded number of API threads when the network is slow or rate limited.
    """

    MODEL = "whisper-large-v3-turbo"
    MAX_AUDIO_BYTES = 5_120_000  # 160 seconds at 16 kHz mono, 16-bit PCM

    def __init__(
        self,
        api_key: Optional[str] = None,
        sample_rate: int = 16000,
        channels: int = 1,
        sample_width: int = 2,
        language: Optional[str] = None,
        on_transcription: Optional[Callable[[str], None]] = None,
        on_error: Optional[Callable[[Exception], None]] = None,
        *,
        max_workers: int = 2,
        max_pending_requests: int = 4,
        request_timeout_seconds: float = 25.0,
        client_factory: Callable[..., Groq] = Groq,
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
        self._client_factory = client_factory
        self._request_timeout_seconds = request_timeout_seconds
        self._lock = threading.RLock()
        self._client: Optional[Groq] = None
        self._task = "transcribe"
        self._executor = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="Transcription")
        self._pending = threading.BoundedSemaphore(max_pending_requests)
        self._closed = False
        self.update_config(api_key=api_key, language=language)

    @property
    def configured(self) -> bool:
        """Whether a usable Groq client is available."""
        with self._lock:
            return self._client is not None

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
                self._client = self._build_client(cleaned_key) if self._is_plausible_key(cleaned_key) else None
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
                client = self._client
                task = self._task
                language = self._language
            if client is None:
                raise TranscriptionError(
                    "No Groq API key is configured. Add GROQ_API_KEY to your environment or save a key in Settings."
                )

            wav_buffer = self._pcm_to_wav(audio_data)
            if task == "translate":
                response = client.audio.translations.create(
                    file=("speech.wav", wav_buffer, "audio/wav"),
                    model=self.MODEL,
                    response_format="text",
                )
            else:
                response = client.audio.transcriptions.create(
                    file=("speech.wav", wav_buffer, "audio/wav"),
                    model=self.MODEL,
                    language=language,
                    response_format="text",
                )
            text = response.strip() if isinstance(response, str) else str(response).strip()
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
        with self._lock:
            if self._closed:
                self._report_error(TranscriptionError("The transcription service is shutting down."))
                return None
        if not self._pending.acquire(blocking=False):
            self._report_error(
                TranscriptionError("Transcription queue is full. Please wait a moment before continuing.")
            )
            return None

        future = self._executor.submit(self.transcribe, audio_data)
        future.add_done_callback(lambda _future: self._pending.release())
        return future

    def close(self, wait: bool = False) -> None:
        """Stop accepting work and release worker resources."""
        with self._lock:
            if self._closed:
                return
            self._closed = True
        self._executor.shutdown(wait=wait, cancel_futures=True)

    def _build_client(self, api_key: str) -> Groq:
        try:
            return self._client_factory(
                api_key=api_key,
                timeout=self._request_timeout_seconds,
                max_retries=0,
            )
        except TypeError:
            # Supports injected test clients and older SDKs. Current Groq clients
            # receive explicit timeouts and disabled SDK retries.
            return self._client_factory(api_key=api_key)

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
            return TranscriptionError("Groq rejected the API key. Check Settings or GROQ_API_KEY and try again.")
        if any(marker in lowered for marker in ("429", "rate limit")):
            return TranscriptionError("Groq is rate limiting requests. Wait a few seconds, then continue.")
        if any(marker in lowered for marker in ("timeout", "timed out", "connection")):
            return TranscriptionError("Could not reach Groq. Check your connection and try again.")
        return TranscriptionError("Groq could not transcribe this segment. Try again or check the app logs.")

    def _report_error(self, error: Exception) -> None:
        LOGGER.warning("Transcription request rejected: %s", error)
        if self._on_error:
            self._on_error(error)

    def __enter__(self) -> "GroqTranscriptionService":
        return self

    def __exit__(self, _exc_type: object, _exc: object, _traceback: object) -> None:
        self.close(wait=False)
