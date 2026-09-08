import importlib.util
import sys
import types
import unittest
from pathlib import Path


class FakeVad:
    decisions: list[bool] = []

    def __init__(self, _aggressiveness: int) -> None:
        self._index = 0

    def is_speech(self, _frame: bytes, _sample_rate: int) -> bool:
        result = self.decisions[self._index]
        self._index += 1
        return result


def load_vad_module() -> types.ModuleType:
    fake_webrtcvad = types.ModuleType("webrtcvad")
    fake_webrtcvad.Vad = FakeVad
    sys.modules["webrtcvad"] = fake_webrtcvad
    module_path = Path(__file__).resolve().parents[1] / "audio" / "vad.py"
    spec = importlib.util.spec_from_file_location("test_voice_activity_detector", module_path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class VoiceActivityDetectorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.module = load_vad_module()

    def test_invalid_duration_ranges_are_rejected(self) -> None:
        detector = self.module.VoiceActivityDetector
        with self.assertRaises(ValueError):
            detector(silence_threshold_ms=10)
        with self.assertRaises(ValueError):
            detector(min_speech_ms=10)
        with self.assertRaises(ValueError):
            detector(min_speech_ms=300, max_speech_ms=200)

    def test_segment_includes_detected_speech_and_trailing_silence(self) -> None:
        FakeVad.decisions = [True, False]
        detector = self.module.VoiceActivityDetector(
            sample_rate=16000,
            frame_duration_ms=30,
            silence_threshold_ms=30,
            min_speech_ms=30,
            max_speech_ms=120,
        )
        frame = b"\x01\x00" * 480

        self.assertIsNone(detector.process_frame(frame))
        segment = detector.process_frame(frame)

        self.assertEqual(segment, frame + frame)
        self.assertFalse(detector.is_speaking)

    def test_default_minimum_speech_duration_allows_short_word(self) -> None:
        FakeVad.decisions = [True] * 10 + [False] * 19
        detector = self.module.VoiceActivityDetector(
            sample_rate=16_000,
            frame_duration_ms=30,
            silence_threshold_ms=600,
            min_speech_ms=300,
            max_speech_ms=20_000,
        )
        frame = b"\x01\x00" * 480

        segment = None
        for _ in FakeVad.decisions:
            segment = detector.process_frame(frame) or segment

        self.assertIsNotNone(segment)
        self.assertFalse(detector.is_speaking)

    def test_speech_shorter_than_minimum_never_starts_a_segment(self) -> None:
        FakeVad.decisions = [True] * 5 + [False] * 30
        detector = self.module.VoiceActivityDetector(
            sample_rate=16_000,
            frame_duration_ms=30,
            silence_threshold_ms=600,
            min_speech_ms=300,
            max_speech_ms=20_000,
        )
        frame = b"\x01\x00" * 480

        segments = [detector.process_frame(frame) for _ in FakeVad.decisions]

        self.assertEqual([item for item in segments if item], [])
        self.assertFalse(detector.is_speaking)

    def test_non_bytes_frame_is_rejected(self) -> None:
        detector = self.module.VoiceActivityDetector(silence_threshold_ms=30, min_speech_ms=30)
        with self.assertRaises(TypeError):
            detector.process_frame("not pcm")
