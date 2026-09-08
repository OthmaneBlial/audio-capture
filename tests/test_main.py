import sys
import tempfile
import threading
import types
import unittest
from unittest import mock

from config import ConfigManager
from main import VoiceTranscriberApp


class FakeWindow:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.input_sources: list[str] = []
        self.levels: list[float] = []

    def show_error(self, message: str) -> None:
        self.errors.append(message)

    def set_input_source(self, name: str) -> None:
        self.input_sources.append(name)

    def set_input_level(self, level: float) -> None:
        self.levels.append(level)


class FakeAudioCapture:
    instances: list["FakeAudioCapture"] = []

    def __init__(self, *, device_index: int | None, on_level: object) -> None:
        self.device_index = device_index
        self.on_level = on_level
        self.sample_rate = 16_000
        self.frame_duration_ms = 30
        self.selected_device = types.SimpleNamespace(name="Test microphone")
        self.started = False
        self.stopped = False
        self.__class__.instances.append(self)

    def start(self) -> None:
        self.started = True

    def stop(self) -> None:
        self.stopped = True


class FakeVad:
    def __init__(self, **_kwargs: object) -> None:
        self.flushed = False

    def flush(self) -> None:
        self.flushed = True
        return None


class FakeThread:
    instances: list["FakeThread"] = []

    def __init__(self, *, target: object, args: tuple[object, ...], daemon: bool, name: str) -> None:
        self.target = target
        self.args = args
        self.daemon = daemon
        self.name = name
        self.started = False
        self.__class__.instances.append(self)

    def start(self) -> None:
        self.started = True

    def is_alive(self) -> bool:
        return False

    def join(self, timeout: float | None = None) -> None:
        del timeout


class FakeTranscriber:
    provider_id = "groq"
    configured = True

    def transcribe_async(self, _audio: bytes) -> None:
        raise AssertionError("transcription should not be needed in this lifecycle test")


def make_app(*, consented: bool) -> VoiceTranscriberApp:
    app = VoiceTranscriberApp.__new__(VoiceTranscriberApp)
    app._running = threading.Event()
    app._lifecycle_lock = threading.RLock()
    app._processing_thread = None
    app._audio = None
    app._vad = None
    app._input_device_override = None
    app._test_tmpdir = tempfile.TemporaryDirectory()
    app._config = ConfigManager(
        config_dir=app._test_tmpdir.name,
        environ={"GROQ_API_KEY": "gsk-test-key-12345"},
    )
    app._config._config["cloud_boundary_confirmed"] = consented
    app._transcriber = FakeTranscriber()
    app._window = FakeWindow()
    return app


class VoiceTranscriberAppTests(unittest.TestCase):
    def setUp(self) -> None:
        FakeAudioCapture.instances.clear()
        FakeThread.instances.clear()
        self.audio_module = types.ModuleType("audio")
        self.audio_module.AudioCapture = FakeAudioCapture
        self.audio_module.VoiceActivityDetector = FakeVad

    def test_groq_start_requires_cloud_boundary_confirmation_at_controller(self) -> None:
        app = make_app(consented=False)
        with mock.patch.dict(sys.modules, {"audio": self.audio_module}):
            self.assertFalse(app._start_listening())
        self.assertEqual(FakeAudioCapture.instances, [])
        self.assertIn("cloud data boundary", app._window.errors[0])

    def test_confirmed_groq_start_and_stop_manage_capture(self) -> None:
        app = make_app(consented=True)
        with mock.patch.dict(sys.modules, {"audio": self.audio_module}):
            with mock.patch("main.threading.Thread", FakeThread):
                self.assertTrue(app._start_listening())
                self.assertTrue(app._running.is_set())
                self.assertEqual(len(FakeAudioCapture.instances), 1)
                self.assertTrue(FakeAudioCapture.instances[0].started)
                app._stop_listening()
        self.assertFalse(app._running.is_set())
        self.assertTrue(FakeAudioCapture.instances[0].stopped)


if __name__ == "__main__":
    unittest.main()
