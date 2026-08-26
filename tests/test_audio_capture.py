import importlib.util
import struct
import sys
import types
import unittest
from pathlib import Path


class FakeStream:
    def __init__(self) -> None:
        self.closed = False

    def is_active(self) -> bool:
        return not self.closed

    def stop_stream(self) -> None:
        self.closed = True

    def close(self) -> None:
        self.closed = True


class FakePyAudio:
    def __init__(self) -> None:
        self.terminated = False
        self.open_options: dict[str, object] = {}
        self.stream = FakeStream()
        self.devices = {
            0: {"name": "Desktop speakers", "maxInputChannels": 0, "index": 0},
            2: {"name": "  USB   microphone  ", "maxInputChannels": 2, "index": 2},
            5: {"name": "Built-in microphone", "maxInputChannels": 1, "index": 5},
        }

    def get_default_input_device_info(self) -> dict[str, object]:
        return self.devices[2]

    def get_device_count(self) -> int:
        return 6

    def get_device_info_by_index(self, index: int) -> dict[str, object]:
        return self.devices.get(index, {"name": f"Output {index}", "maxInputChannels": 0, "index": index})

    def open(self, **kwargs: object) -> FakeStream:
        self.open_options = kwargs
        return self.stream

    def terminate(self) -> None:
        self.terminated = True


class FakeThread:
    def __init__(self, **_kwargs: object) -> None:
        pass

    def start(self) -> None:
        pass

    def is_alive(self) -> bool:
        return False


def load_capture_module() -> types.ModuleType:
    fake_pyaudio = types.ModuleType("pyaudio")
    fake_pyaudio.paInt16 = 8
    fake_pyaudio.PyAudio = FakePyAudio
    fake_pyaudio.Stream = FakeStream
    sys.modules["pyaudio"] = fake_pyaudio
    module_path = Path(__file__).resolve().parents[1] / "audio" / "capture.py"
    spec = importlib.util.spec_from_file_location("test_audio_capture", module_path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class AudioCaptureTests(unittest.TestCase):
    def setUp(self) -> None:
        self.module = load_capture_module()

    def test_list_input_devices_filters_outputs_marks_default_and_releases_client(self) -> None:
        client = FakePyAudio()

        devices = self.module.list_input_devices(pyaudio_factory=lambda: client)

        self.assertEqual([(device.index, device.name) for device in devices], [(2, "USB microphone"), (5, "Built-in microphone")])
        self.assertTrue(devices[0].is_default)
        self.assertTrue(client.terminated)

    def test_selected_device_is_opened_and_released(self) -> None:
        client = FakePyAudio()
        capture = self.module.AudioCapture(device_index=5, pyaudio_factory=lambda: client)
        original_thread = self.module.threading.Thread
        self.module.threading.Thread = FakeThread
        try:
            capture.start()
            self.assertEqual(capture.selected_device.name, "Built-in microphone")
            self.assertEqual(client.open_options["input_device_index"], 5)
        finally:
            capture.stop()
            self.module.threading.Thread = original_thread
        self.assertTrue(client.terminated)

    def test_signal_level_is_bounded_and_tracks_louder_pcm(self) -> None:
        silence = b"\x00\x00" * 20
        quiet = struct.pack("<20h", *([250] * 20))
        loud = struct.pack("<20h", *([6000] * 20))

        self.assertEqual(self.module.AudioCapture.level_from_pcm(silence), 0.0)
        self.assertGreater(self.module.AudioCapture.level_from_pcm(loud), self.module.AudioCapture.level_from_pcm(quiet))
        self.assertLessEqual(self.module.AudioCapture.level_from_pcm(loud), 1.0)

    def test_invalid_device_index_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            self.module.AudioCapture(device_index=-1)
