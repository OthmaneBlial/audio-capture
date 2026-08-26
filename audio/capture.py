"""Real-time, bounded microphone capture using PyAudio."""

from __future__ import annotations

import logging
import queue
import threading
from typing import Callable, Optional

import pyaudio

LOGGER = logging.getLogger(__name__)


class AudioCapture:
    """Capture fixed 30 ms PCM frames from the system-default microphone."""

    SAMPLE_RATE = 16000
    CHANNELS = 1
    FORMAT = pyaudio.paInt16
    BYTES_PER_SAMPLE = 2
    FRAME_DURATION_MS = 30
    FRAMES_PER_BUFFER = int(SAMPLE_RATE * FRAME_DURATION_MS / 1000)
    QUEUE_CAPACITY = 100

    def __init__(self, on_audio_chunk: Optional[Callable[[bytes], None]] = None) -> None:
        self._pyaudio: Optional[pyaudio.PyAudio] = None
        self._stream: Optional[pyaudio.Stream] = None
        self._running = threading.Event()
        self._lock = threading.RLock()
        self._audio_queue: queue.Queue[Optional[bytes]] = queue.Queue(maxsize=self.QUEUE_CAPACITY)
        self._on_audio_chunk = on_audio_chunk
        self._capture_thread: Optional[threading.Thread] = None
        self._dropped_frames = 0

    def start(self) -> None:
        """Open the selected microphone and begin collecting frames."""
        with self._lock:
            if self._running.is_set():
                return
            self._clear_queue()
            self._dropped_frames = 0
            try:
                self._pyaudio = pyaudio.PyAudio()
                device = self._pyaudio.get_default_input_device_info()
                LOGGER.info("Using input device: %s", device.get("name", "unknown"))
                self._stream = self._pyaudio.open(
                    format=self.FORMAT,
                    channels=self.CHANNELS,
                    rate=self.SAMPLE_RATE,
                    input=True,
                    frames_per_buffer=self.FRAMES_PER_BUFFER,
                    start=True,
                )
            except Exception as error:
                self._cleanup_resources()
                raise RuntimeError(
                    "Could not open the default microphone. Check that a microphone is connected "
                    "and that this app has permission to use it."
                ) from error

            self._running.set()
            self._capture_thread = threading.Thread(
                target=self._capture_loop, daemon=True, name="AudioCapture"
            )
            self._capture_thread.start()

    def _capture_loop(self) -> None:
        while self._running.is_set():
            try:
                stream = self._stream
                if stream is None or not stream.is_active():
                    if self._running.is_set():
                        LOGGER.warning("Microphone stream stopped unexpectedly")
                    break
                data = stream.read(self.FRAMES_PER_BUFFER, exception_on_overflow=False)
                self._put_frame(data)
                if self._on_audio_chunk:
                    self._on_audio_chunk(data)
            except (OSError, IOError) as error:
                if self._running.is_set():
                    LOGGER.warning("Microphone capture stopped: %s", error)
                break
            except Exception:
                if self._running.is_set():
                    LOGGER.exception("Unexpected microphone capture failure")
                break
        self._running.clear()

    def _put_frame(self, data: bytes) -> None:
        try:
            self._audio_queue.put_nowait(data)
        except queue.Full:
            try:
                self._audio_queue.get_nowait()
                self._audio_queue.put_nowait(data)
                self._dropped_frames += 1
                if self._dropped_frames == 1 or self._dropped_frames % 50 == 0:
                    LOGGER.warning("Audio processing is behind; dropped %d frame(s)", self._dropped_frames)
            except queue.Empty:
                # A consumer won a race; dropping this frame preserves real-time behavior.
                self._dropped_frames += 1

    def stop(self) -> None:
        """Stop capture, wait briefly for the reader, and release native resources."""
        with self._lock:
            self._running.clear()
            capture_thread = self._capture_thread

        if capture_thread and capture_thread.is_alive():
            capture_thread.join(timeout=1.0)
            if capture_thread.is_alive():
                LOGGER.warning("Audio capture thread did not finish before shutdown timeout")

        with self._lock:
            self._capture_thread = None
            self._cleanup_resources()
            self._clear_queue()
            try:
                self._audio_queue.put_nowait(None)
            except queue.Full:
                pass

    def _cleanup_resources(self) -> None:
        if self._stream is not None:
            try:
                if self._stream.is_active():
                    self._stream.stop_stream()
                self._stream.close()
            except Exception:
                LOGGER.debug("Could not close microphone stream", exc_info=True)
            finally:
                self._stream = None
        if self._pyaudio is not None:
            try:
                self._pyaudio.terminate()
            except Exception:
                LOGGER.debug("Could not terminate PyAudio", exc_info=True)
            finally:
                self._pyaudio = None

    def _clear_queue(self) -> None:
        while True:
            try:
                self._audio_queue.get_nowait()
            except queue.Empty:
                return

    def get_audio_chunk(self, timeout: float = 0.1) -> Optional[bytes]:
        """Return the next capture frame, or ``None`` when none arrives in time."""
        try:
            return self._audio_queue.get(timeout=max(0.0, timeout))
        except queue.Empty:
            return None

    @property
    def is_running(self) -> bool:
        return self._running.is_set()

    @property
    def dropped_frames(self) -> int:
        return self._dropped_frames

    @property
    def sample_rate(self) -> int:
        return self.SAMPLE_RATE

    @property
    def frame_duration_ms(self) -> int:
        return self.FRAME_DURATION_MS

    def __enter__(self) -> "AudioCapture":
        self.start()
        return self

    def __exit__(self, _exc_type: object, _exc: object, _traceback: object) -> None:
        self.stop()
