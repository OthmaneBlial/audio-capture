"""Feature-flagged whisper.cpp prototype using memory-backed WAV input on Linux."""

from __future__ import annotations

import io
import itertools
import logging
import os
import subprocess
import threading
import time
import wave
from concurrent.futures import Future, ThreadPoolExecutor
from pathlib import Path
from typing import Any, Callable, Mapping, Optional

from .provider import ProviderBoundary, ProviderCapabilities, ProviderError

LOGGER = logging.getLogger(__name__)
EXPERIMENTAL_FLAG = "VOICE_TRANSCRIBER_EXPERIMENTAL_LOCAL"


def local_mode_enabled(
    environ: Optional[Mapping[str, str]] = None,
    *,
    flatpak_info: Path = Path("/.flatpak-info"),
) -> bool:
    """Enable only by explicit source-install flag; the Flatpak ships no model/runtime."""
    values = environ if environ is not None else os.environ
    return values.get(EXPERIMENTAL_FLAG, "").strip() == "1" and not flatpak_info.exists()


class LocalWhisperTranscriptionService:
    """Run a user-supplied whisper.cpp CLI without writing speech to disk."""

    provider_id = "local_whisper_cpp"
    capabilities = ProviderCapabilities(
        provider_id=provider_id,
        display_name="Local whisper.cpp (experimental)",
        transcription=True,
        translation_to_english=True,
        automatic_language=True,
        supported_languages=("auto", "en", "fr", "es", "de", "it", "pt", "ar", "zh"),
        language_notes="Actual quality and availability depend on the user-supplied model.",
        cancellation="Queued work is cancellable; close terminates an active CLI process.",
        limits="Source install only; user supplies a compatible CLI and GGML model.",
    )
    boundary = ProviderBoundary(
        label="Local model · experimental",
        audio_destination="Memory-backed file descriptor passed to a local whisper.cpp process",
        credential="No provider credential",
        storage_statement="The app writes no raw-audio file; the user-supplied model remains on disk.",
    )
    MAX_AUDIO_BYTES = 5_120_000

    def __init__(
        self,
        *,
        binary_path: str,
        model_path: str,
        sample_rate: int = 16000,
        language: Optional[str] = None,
        translate: bool = False,
        on_transcription: Optional[Callable[[str], None]] = None,
        on_error: Optional[Callable[[Exception], None]] = None,
        on_request_state: Optional[Callable[[str, str, Optional[str]], None]] = None,
        max_workers: int = 1,
        max_pending_requests: int = 2,
        timeout_seconds: float = 180.0,
        process_factory: Callable[..., Any] = subprocess.Popen,
        memfd_factory: Optional[Callable[[str, int], int]] = None,
        environ: Optional[Mapping[str, str]] = None,
        flatpak_info: Path = Path("/.flatpak-info"),
    ) -> None:
        if sample_rate != 16000:
            raise ValueError("local whisper.cpp prototype requires 16 kHz PCM")
        if max_workers != 1 or max_pending_requests < 1:
            raise ValueError("local prototype uses one worker and a positive queue bound")
        self._binary_path = Path(binary_path).expanduser()
        self._model_path = Path(model_path).expanduser()
        self._sample_rate = sample_rate
        self._language = language or "auto"
        self._translate = translate
        self._on_transcription = on_transcription
        self._on_error = on_error
        self._on_request_state = on_request_state
        self._timeout_seconds = timeout_seconds
        self._process_factory = process_factory
        self._memfd_factory = memfd_factory or getattr(os, "memfd_create", None)
        self._enabled = local_mode_enabled(environ, flatpak_info=flatpak_info)
        self._executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="LocalWhisper")
        self._pending = threading.BoundedSemaphore(max_pending_requests)
        self._lock = threading.RLock()
        self._futures: set[Future[Optional[str]]] = set()
        self._processes: set[Any] = set()
        self._request_ids = itertools.count(1)
        self._closed = False
        self.last_latency_ms: Optional[float] = None

    @property
    def configured(self) -> bool:
        return (
            self._enabled
            and self._memfd_factory is not None
            and self._binary_path.is_file()
            and os.access(self._binary_path, os.X_OK)
            and self._model_path.is_file()
        )

    def update_config(
        self,
        api_key: Optional[str] = None,
        language: Optional[str] = None,
        translate: bool = False,
    ) -> None:
        del api_key
        with self._lock:
            if language is not None:
                self._language = language or "auto"
            self._translate = translate

    def transcribe(self, audio_data: bytes) -> Optional[str]:
        try:
            self._validate(audio_data)
            wav_data = self._pcm_to_wav(audio_data)
            started = time.perf_counter()
            text = self._run_cli(wav_data).strip()
            self.last_latency_ms = (time.perf_counter() - started) * 1000
            if text and self._on_transcription:
                self._on_transcription(text)
            return text
        except Exception as error:
            normalized = self._normalize_error(error)
            if self._on_error:
                self._on_error(normalized)
            return None

    def transcribe_async(self, audio_data: bytes) -> Optional[Future[Optional[str]]]:
        request_id = f"local-segment-{next(self._request_ids)}"
        with self._lock:
            if self._closed:
                self._report_request(request_id, "error", "Service is shutting down")
                return None
        if not self._pending.acquire(blocking=False):
            error = ProviderError("Local transcription queue is full.", code="queue_full", retryable=True)
            if self._on_error:
                self._on_error(error)
            self._report_request(request_id, "error", "Queue is full")
            return None
        self._report_request(request_id, "pending", "Running local model")
        future = self._executor.submit(self.transcribe, audio_data)
        with self._lock:
            self._futures.add(future)
        future.add_done_callback(lambda completed: self._finish_request(request_id, completed))
        return future

    def cancel_pending(self) -> int:
        cancelled = 0
        with self._lock:
            for future in list(self._futures):
                if future.cancel():
                    cancelled += 1
            for process in list(self._processes):
                try:
                    process.terminate()
                except OSError:
                    pass
        return cancelled

    def close(self, wait: bool = False) -> None:
        with self._lock:
            self._closed = True
        self.cancel_pending()
        self._executor.shutdown(wait=wait, cancel_futures=True)

    def _run_cli(self, wav_data: bytes) -> str:
        if not self.configured:
            raise ProviderError(
                "Experimental local mode is not ready. Enable the source-install flag and choose an executable whisper-cli plus a GGML model.",
                code="not_configured",
            )
        assert self._memfd_factory is not None
        descriptor = self._memfd_factory("voice-transcriber-segment", 0)
        try:
            os.write(descriptor, wav_data)
            os.lseek(descriptor, 0, os.SEEK_SET)
            command = [
                str(self._binary_path),
                "--model",
                str(self._model_path),
                "--file",
                f"/proc/self/fd/{descriptor}",
                "--language",
                self._language,
                "--no-timestamps",
                "--no-prints",
            ]
            if self._translate:
                command.append("--translate")
            process = self._process_factory(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                pass_fds=(descriptor,),
            )
            with self._lock:
                self._processes.add(process)
            try:
                stdout, stderr = process.communicate(timeout=self._timeout_seconds)
            except subprocess.TimeoutExpired as error:
                process.terminate()
                process.communicate()
                raise ProviderError(
                    "The local model timed out. Try a smaller model or shorter segment.",
                    code="timeout",
                    retryable=True,
                ) from error
            finally:
                with self._lock:
                    self._processes.discard(process)
            if process.returncode != 0:
                # Some third-party builds may echo recognized text or file paths to stderr.
                # Keep only exit status in logs; the user-facing error remains actionable.
                LOGGER.debug("Local whisper.cpp exited with status %s", process.returncode)
                raise ProviderError(
                    "The local model could not transcribe this segment. Check the CLI/model compatibility.",
                    code="local_process_failed",
                    retryable=True,
                )
            return stdout
        finally:
            os.close(descriptor)

    def _validate(self, audio_data: bytes) -> None:
        if not isinstance(audio_data, bytes) or not audio_data:
            raise ProviderError("No speech audio was captured.", code="empty_audio", retryable=True)
        if len(audio_data) > self.MAX_AUDIO_BYTES:
            raise ProviderError("Speech segment is too long.", code="audio_too_large", retryable=True)
        if len(audio_data) % 2:
            raise ProviderError("Captured audio is malformed.", code="malformed_audio", retryable=True)

    def _pcm_to_wav(self, pcm_data: bytes) -> bytes:
        buffer = io.BytesIO()
        with wave.open(buffer, "wb") as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(self._sample_rate)
            wav_file.writeframes(pcm_data)
        return buffer.getvalue()

    @staticmethod
    def _normalize_error(error: Exception) -> ProviderError:
        if isinstance(error, ProviderError):
            return error
        return ProviderError(
            "The local model failed unexpectedly. Check the experimental-mode logs.",
            code="local_unexpected",
        )

    def _finish_request(self, request_id: str, future: Future[Optional[str]]) -> None:
        self._pending.release()
        with self._lock:
            self._futures.discard(future)
        try:
            text = future.result()
        except Exception:
            text = None
        self._report_request(
            request_id,
            "complete" if text else "error",
            "Added to transcript" if text else "Local transcription failed",
        )

    def _report_request(self, request_id: str, state: str, detail: str) -> None:
        if self._on_request_state:
            self._on_request_state(request_id, state, detail)
