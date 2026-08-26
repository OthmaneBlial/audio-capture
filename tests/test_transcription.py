import io
import sys
import threading
import types
import unittest
import wave
from typing import Optional

fake_groq = types.ModuleType("groq")
fake_groq.Groq = object
sys.modules.setdefault("groq", fake_groq)

from transcription.groq_service import GroqTranscriptionService


class FakeTranscriptions:
    def __init__(
        self, response: str = " hello world ", wait_event: Optional[threading.Event] = None
    ) -> None:
        self.response = response
        self.wait_event = wait_event
        self.calls: list[dict[str, object]] = []
        self.started = threading.Event()

    def create(self, **kwargs: object) -> str:
        self.calls.append(kwargs)
        self.started.set()
        if self.wait_event:
            self.wait_event.wait(timeout=2)
        return self.response


class FakeClient:
    def __init__(self, transcriptions: FakeTranscriptions) -> None:
        self.audio = types.SimpleNamespace(
            transcriptions=transcriptions,
            translations=types.SimpleNamespace(create=transcriptions.create),
        )


class FakeFactory:
    def __init__(self, client: FakeClient) -> None:
        self.client = client
        self.kwargs: dict[str, object] = {}

    def __call__(self, **kwargs: object) -> FakeClient:
        self.kwargs = kwargs
        return self.client


class GroqTranscriptionServiceTests(unittest.TestCase):
    def test_encodes_wav_and_returns_trimmed_text(self) -> None:
        transcriptions = FakeTranscriptions()
        factory = FakeFactory(FakeClient(transcriptions))
        received: list[str] = []
        service = GroqTranscriptionService(
            api_key="valid-test-key-12345",
            client_factory=factory,
            on_transcription=received.append,
        )
        try:
            self.assertEqual(service.transcribe(b"\x00\x00" * 160), "hello world")
            self.assertEqual(received, ["hello world"])
            self.assertEqual(factory.kwargs["timeout"], 25.0)
            wav_data = transcriptions.calls[0]["file"][1]
            assert isinstance(wav_data, io.BytesIO)
            with wave.open(wav_data) as wav_file:
                self.assertEqual(wav_file.getframerate(), 16000)
                self.assertEqual(wav_file.getnchannels(), 1)
                self.assertEqual(wav_file.getsampwidth(), 2)
        finally:
            service.close(wait=True)

    def test_malformed_audio_and_missing_key_have_actionable_errors(self) -> None:
        errors: list[Exception] = []
        service = GroqTranscriptionService(api_key="", on_error=errors.append)
        try:
            self.assertIsNone(service.transcribe(b"\x00"))
            self.assertIn("malformed", str(errors[-1]).lower())
            self.assertIsNone(service.transcribe(b"\x00\x00"))
            self.assertIn("no groq api key", str(errors[-1]).lower())
        finally:
            service.close(wait=True)

    def test_pending_queue_is_bounded(self) -> None:
        release = threading.Event()
        transcriptions = FakeTranscriptions(wait_event=release)
        errors: list[Exception] = []
        service = GroqTranscriptionService(
            api_key="valid-test-key-12345",
            client_factory=FakeFactory(FakeClient(transcriptions)),
            on_error=errors.append,
            max_workers=1,
            max_pending_requests=1,
        )
        try:
            first = service.transcribe_async(b"\x00\x00" * 80)
            self.assertIsNotNone(first)
            self.assertTrue(transcriptions.started.wait(timeout=1))
            self.assertIsNone(service.transcribe_async(b"\x00\x00" * 80))
            self.assertIn("queue is full", str(errors[-1]).lower())
            release.set()
            assert first is not None
            self.assertEqual(first.result(timeout=2), "hello world")
        finally:
            release.set()
            service.close(wait=True)
