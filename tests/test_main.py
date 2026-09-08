import sys
import tempfile
import threading
import types
import unittest
from typing import Optional
from unittest import mock

from config import ConfigManager
from main import VoiceTranscriberApp


class FakeWindow:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.input_sources: list[str] = []
        self.levels: list[float] = []
        self.transcripts: list[str] = []
        self.statuses: list[tuple[str, str, Optional[int]]] = []
        self.segment_states_cleared = 0

    def show_error(self, message: str) -> None:
        self.errors.append(message)

    def set_input_source(self, name: str) -> None:
        self.input_sources.append(name)

    def set_input_level(self, level: float) -> None:
        self.levels.append(level)

    def append_text(self, text: str) -> None:
        self.transcripts.append(text)

    def set_status(
        self, message: str, style_class: str = "", *, reset_after_ms: Optional[int] = None
    ) -> None:
        self.statuses.append((message, style_class, reset_after_ms))

    def clear_segment_states(self) -> None:
        self.segment_states_cleared += 1


class FakeAudioCapture:
    instances: list["FakeAudioCapture"] = []

    def __init__(
        self, *, device_index: Optional[int], on_level: object, queue_audio: bool = True
    ) -> None:
        self.device_index = device_index
        self.on_level = on_level
        self.queue_audio = queue_audio
        self.sample_rate = 16_000
        self.frame_duration_ms = 30
        self.selected_device = types.SimpleNamespace(name="Test microphone")
        self.started = False
        self.stopped = False
        self.stop_clear_queue: Optional[bool] = None
        self.dropped_frames = 0
        self.queued_chunks: list[bytes] = []
        self.__class__.instances.append(self)

    def start(self) -> None:
        self.started = True

    def stop(self, *, clear_queue: bool = True) -> None:
        self.stopped = True
        self.stop_clear_queue = clear_queue

    def get_audio_chunk(self, timeout: float = 0.0) -> Optional[bytes]:
        del timeout
        return self.queued_chunks.pop(0) if self.queued_chunks else None


class FakeVad:
    def __init__(self, **_kwargs: object) -> None:
        self.flushed = False
        self.processed: list[bytes] = []

    def process_frame(self, frame: bytes) -> None:
        self.processed.append(frame)
        return None

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

    def join(self, timeout: Optional[float] = None) -> None:
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
    app._active_request_ids = set()
    app._monitor_audio = None
    app._reported_dropped_frames = 0
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
        self._apps: list[VoiceTranscriberApp] = []
        self.audio_module = types.ModuleType("audio")
        self.audio_module.AudioCapture = FakeAudioCapture
        self.audio_module.VoiceActivityDetector = FakeVad

    def tearDown(self) -> None:
        for app in self._apps:
            app._test_tmpdir.cleanup()

    def _new_app(self, *, consented: bool) -> VoiceTranscriberApp:
        app = make_app(consented=consented)
        self._apps.append(app)
        return app

    def test_groq_start_requires_cloud_boundary_confirmation_at_controller(self) -> None:
        app = self._new_app(consented=False)
        with mock.patch.dict(sys.modules, {"audio": self.audio_module}):
            self.assertFalse(app._start_listening())
        self.assertEqual(FakeAudioCapture.instances, [])
        self.assertIn("cloud data boundary", app._window.errors[0])

    def test_confirmed_groq_start_and_stop_manage_capture(self) -> None:
        app = self._new_app(consented=True)
        with mock.patch.dict(sys.modules, {"audio": self.audio_module}):
            with mock.patch("main.threading.Thread", FakeThread):
                self.assertTrue(app._start_listening())
                self.assertTrue(app._running.is_set())
                self.assertEqual(len(FakeAudioCapture.instances), 1)
                self.assertTrue(FakeAudioCapture.instances[0].started)
                app._stop_listening()
        self.assertFalse(app._running.is_set())
        self.assertTrue(FakeAudioCapture.instances[0].stopped)
        self.assertFalse(FakeAudioCapture.instances[0].stop_clear_queue)

    def test_result_from_inactive_request_is_ignored(self) -> None:
        app = self._new_app(consented=True)
        app._active_request_ids.add("segment-active")
        app._on_transcription_result("segment-stale", "stale text")
        app._on_transcription_result("segment-active", "accepted text")
        self.assertEqual(app._window.transcripts, ["accepted text"])

    def test_error_from_inactive_request_is_ignored(self) -> None:
        app = self._new_app(consented=True)
        app._on_transcription_error_result("segment-stale", RuntimeError("stale"))
        app._active_request_ids.add("segment-active")
        app._on_transcription_error_result("segment-active", RuntimeError("active"))
        self.assertEqual(app._window.errors, ["active"])

    def test_reset_generation_clears_visible_segment_states(self) -> None:
        app = self._new_app(consented=True)
        app._transcriber.reset_session = mock.Mock()
        app._reset_transcription_generation()
        self.assertEqual(app._window.segment_states_cleared, 1)
        app._transcriber.reset_session.assert_called_once_with()

    def test_microphone_test_does_not_require_provider_configuration(self) -> None:
        app = self._new_app(consented=False)
        app._transcriber.configured = False
        with mock.patch.dict(sys.modules, {"audio": self.audio_module}):
            self.assertTrue(app._start_microphone_test(device_index=3))
            self.assertEqual(FakeAudioCapture.instances[0].device_index, 3)
            self.assertFalse(FakeAudioCapture.instances[0].queue_audio)
            app._stop_microphone_test()
        self.assertTrue(FakeAudioCapture.instances[0].stopped)

    def test_stop_drains_frames_admitted_before_capture_close(self) -> None:
        app = self._new_app(consented=True)
        with mock.patch.dict(sys.modules, {"audio": self.audio_module}):
            with mock.patch("main.threading.Thread", FakeThread):
                self.assertTrue(app._start_listening())
                app._audio.queued_chunks.append(b"queued-frame")
                app._vad.process_frame = lambda _frame: b"\x00\x00"
                app._transcriber.transcribe_async = mock.Mock()
                app._stop_listening()
        app._transcriber.transcribe_async.assert_called_once_with(b"\x00\x00")

    def test_audio_backpressure_is_visible_and_deduplicated(self) -> None:
        app = self._new_app(consented=True)
        audio = types.SimpleNamespace(dropped_frames=3)
        app._report_audio_drops(audio)
        app._report_audio_drops(audio)
        audio.dropped_frames = 4
        app._report_audio_drops(audio)
        self.assertEqual(
            [message for message, _style, _reset in app._window.statuses],
            [
                "Audio buffer full · 3 frame(s) dropped. Please repeat that phrase.",
                "Audio buffer full · 4 frame(s) dropped. Please repeat that phrase.",
            ],
        )
        self.assertTrue(all(style == "warning" for _message, style, _reset in app._window.statuses))


if __name__ == "__main__":
    unittest.main()
