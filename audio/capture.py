"""Real-time, bounded microphone capture using PyAudio."""

from __future__ import annotations

import logging
import math
import queue
import struct
import threading
import time
from dataclasses import dataclass
from typing import Any, Callable, Optional

import pyaudio

LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class InputDevice:
    """A microphone input reported by PortAudio without exposing its raw payload."""

    index: int
    name: str
    max_input_channels: int
    is_default: bool = False


def list_input_devices(*, pyaudio_factory: Callable[[], Any] = pyaudio.PyAudio) -> list[InputDevice]:
    """Return the usable microphone inputs and always release PortAudio afterwards."""
    client: Any = None
    try:
        client = pyaudio_factory()
        try:
            default_info = client.get_default_input_device_info()
            default_index = int(default_info.get("index"))
        except Exception:
            default_index = None

        devices: list[InputDevice] = []
        for index in range(int(client.get_device_count())):
            info = client.get_device_info_by_index(index)
            channels = int(info.get("maxInputChannels", 0))
            if channels <= 0:
                continue
            name = " ".join(str(info.get("name", f"Input {index}")).split()) or f"Input {index}"
            devices.append(
                InputDevice(
                    index=index,
                    name=name,
                    max_input_channels=channels,
                    is_default=index == default_index,
                )
            )
        return devices
    except Exception as error:
        raise RuntimeError(
            "Could not list microphone inputs. Check that your audio system is available."
        ) from error
    finally:
        if client is not None:
            try:
                client.terminate()
            except Exception:
                LOGGER.debug("Could not terminate PyAudio after listing input devices", exc_info=True)


class AudioCapture:
    """Capture fixed 30 ms PCM frames from a selected or default microphone."""

    SAMPLE_RATE = 16000
    CHANNELS = 1
    FORMAT = pyaudio.paInt16
    BYTES_PER_SAMPLE = 2
    FRAME_DURATION_MS = 30
    FRAMES_PER_BUFFER = int(SAMPLE_RATE * FRAME_DURATION_MS / 1000)
    QUEUE_CAPACITY = 100
    LEVEL_INTERVAL_SECONDS = 0.08

    def __init__(
        self,
        on_audio_chunk: Optional[Callable[[bytes], None]] = None,
        *,
        device_index: Optional[int] = None,
        on_level: Optional[Callable[[float], None]] = None,
        pyaudio_factory: Callable[[], Any] = pyaudio.PyAudio,
    ) -> None:
        if (
            isinstance(device_index, bool)
            or (device_index is not None and not isinstance(device_index, int))
            or (isinstance(device_index, int) and device_index < 0)
        ):
            raise ValueError("device_index must be a non-negative integer or None")
        self._pyaudio: Optional[pyaudio.PyAudio] = None
        self._stream: Optional[pyaudio.Stream] = None
        self._running = threading.Event()
        self._lock = threading.RLock()
        self._audio_queue: queue.Queue[Optional[bytes]] = queue.Queue(maxsize=self.QUEUE_CAPACITY)
        self._on_audio_chunk = on_audio_chunk
        self._on_level = on_level
        self._device_index = device_index
        self._pyaudio_factory = pyaudio_factory
        self._selected_device: Optional[InputDevice] = None
        self._last_level_at = 0.0
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
                self._pyaudio = self._pyaudio_factory()
                device = self._selected_input_device()
                if int(device.get("maxInputChannels", 0)) <= 0:
                    raise RuntimeError("The selected device does not provide a microphone input")
                device_name = " ".join(str(device.get("name", "unknown microphone")).split())
                self._selected_device = InputDevice(
                    index=int(device.get("index", self._device_index if self._device_index is not None else -1)),
                    name=device_name or "unknown microphone",
                    max_input_channels=int(device.get("maxInputChannels", 0)),
                    is_default=self._device_index is None,
                )
                LOGGER.info("Using input device: %s", self._selected_device.name)
                open_options: dict[str, Any] = {
                    "format": self.FORMAT,
                    "channels": self.CHANNELS,
                    "rate": self.SAMPLE_RATE,
                    "input": True,
                    "frames_per_buffer": self.FRAMES_PER_BUFFER,
                    "start": True,
                }
                if self._device_index is not None:
                    open_options["input_device_index"] = self._device_index
                self._stream = self._pyaudio.open(**open_options)
            except Exception as error:
                self._cleanup_resources()
                microphone = "the selected microphone" if self._device_index is not None else "the default microphone"
                raise RuntimeError(
                    f"Could not open {microphone}. Check that a microphone is connected "
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
                self._emit_level(data)
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

    def _selected_input_device(self) -> dict[str, Any]:
        if self._pyaudio is None:
            raise RuntimeError("PyAudio is not initialized")
        if self._device_index is None:
            return self._pyaudio.get_default_input_device_info()
        return self._pyaudio.get_device_info_by_index(self._device_index)

    @staticmethod
    def level_from_pcm(data: bytes) -> float:
        """Return a stable 0..1 signal level for signed 16-bit PCM audio."""
        sample_count = len(data) // 2
        if sample_count == 0:
            return 0.0
        samples = struct.unpack(f"<{sample_count}h", data[: sample_count * 2])
        rms = math.sqrt(sum(sample * sample for sample in samples) / sample_count)
        if rms <= 1.0:
            return 0.0
        dbfs = 20 * math.log10(rms / 32768.0)
        return max(0.0, min(1.0, (dbfs + 55.0) / 55.0))

    def _emit_level(self, data: bytes) -> None:
        if self._on_level is None:
            return
        now = time.monotonic()
        if now - self._last_level_at < self.LEVEL_INTERVAL_SECONDS:
            return
        self._last_level_at = now
        try:
            self._on_level(self.level_from_pcm(data))
        except Exception:
            LOGGER.debug("Input-level callback failed", exc_info=True)

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
        self._selected_device = None

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
    def selected_device(self) -> Optional[InputDevice]:
        """Return the current microphone identity while capture is active."""
        return self._selected_device

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
