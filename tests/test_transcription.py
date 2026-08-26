import io
import json
import threading
import unittest
import urllib.error
import wave
from typing import Optional

from transcription.groq_service import GroqTranscriptionService
from transcription.groq_transport import GroqHTTPTransport, GroqTransportError


class FakeTransport:
    def __init__(
        self,
        response: str = " hello world ",
        wait_event: Optional[threading.Event] = None,
    ) -> None:
        self.response = response
        self.wait_event = wait_event
        self.calls: list[dict[str, object]] = []
        self.started = threading.Event()

    def transcribe(self, wav_data: bytes, **kwargs: object) -> str:
        self.calls.append({"wav_data": wav_data, **kwargs})
        self.started.set()
        if self.wait_event:
            self.wait_event.wait(timeout=2)
        return self.response


class FakeFactory:
    def __init__(self, transport: FakeTransport) -> None:
        self.transport = transport
        self.kwargs: dict[str, object] = {}

    def __call__(self, **kwargs: object) -> FakeTransport:
        self.kwargs = kwargs
        return self.transport


class FakeResponse:
    def __init__(self, payload: dict[str, object]) -> None:
        self._payload = json.dumps(payload).encode()

    def __enter__(self) -> "FakeResponse":
        return self

    def __exit__(self, *_args: object) -> None:
        return None

    def read(self) -> bytes:
        return self._payload


class GroqTranscriptionServiceTests(unittest.TestCase):
    def test_encodes_wav_and_returns_trimmed_text(self) -> None:
        transport = FakeTransport()
        factory = FakeFactory(transport)
        received: list[str] = []
        service = GroqTranscriptionService(
            api_key="valid-test-key-12345",
            transport_factory=factory,
            on_transcription=received.append,
        )
        try:
            self.assertEqual(service.transcribe(b"\x00\x00" * 160), "hello world")
            self.assertEqual(received, ["hello world"])
            self.assertEqual(factory.kwargs["timeout"], 25.0)
            wav_data = transport.calls[0]["wav_data"]
            assert isinstance(wav_data, bytes)
            with wave.open(io.BytesIO(wav_data)) as wav_file:
                self.assertEqual(wav_file.getframerate(), 16000)
                self.assertEqual(wav_file.getnchannels(), 1)
                self.assertEqual(wav_file.getsampwidth(), 2)
        finally:
            service.close(wait=True)

    def test_translation_and_language_are_explicit_transport_capabilities(self) -> None:
        transport = FakeTransport()
        service = GroqTranscriptionService(
            api_key="valid-test-key-12345",
            language="fr",
            transport_factory=FakeFactory(transport),
        )
        try:
            service.transcribe(b"\x00\x00" * 80)
            self.assertEqual(transport.calls[-1]["language"], "fr")
            self.assertFalse(transport.calls[-1]["translate"])

            service.update_config(translate=True)
            service.transcribe(b"\x00\x00" * 80)
            self.assertTrue(transport.calls[-1]["translate"])
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
        transport = FakeTransport(wait_event=release)
        errors: list[Exception] = []
        service = GroqTranscriptionService(
            api_key="valid-test-key-12345",
            transport_factory=FakeFactory(transport),
            on_error=errors.append,
            max_workers=1,
            max_pending_requests=1,
        )
        try:
            first = service.transcribe_async(b"\x00\x00" * 80)
            self.assertIsNotNone(first)
            self.assertTrue(transport.started.wait(timeout=1))
            self.assertIsNone(service.transcribe_async(b"\x00\x00" * 80))
            self.assertIn("queue is full", str(errors[-1]).lower())
            release.set()
            assert first is not None
            self.assertEqual(first.result(timeout=2), "hello world")
        finally:
            release.set()
            service.close(wait=True)

    def test_async_requests_report_bounded_user_visible_states(self) -> None:
        states: list[tuple[str, str, Optional[str]]] = []
        service = GroqTranscriptionService(
            api_key="valid-test-key-12345",
            transport_factory=FakeFactory(FakeTransport()),
            on_request_state=lambda request_id, state, detail: states.append(
                (request_id, state, detail)
            ),
        )
        try:
            future = service.transcribe_async(b"\x00\x00" * 80)
            assert future is not None
            self.assertEqual(future.result(timeout=2), "hello world")
            # The completion callback can run immediately after Future.result returns.
            for _ in range(100):
                if any(state == "complete" for _, state, _ in states):
                    break
                threading.Event().wait(0.001)
            self.assertEqual([state for _, state, _ in states], ["pending", "complete"])
            self.assertEqual(states[0][0], states[1][0])
            self.assertNotIn("hello world", " ".join(detail or "" for _, _, detail in states))
        finally:
            service.close(wait=True)


class GroqHTTPTransportTests(unittest.TestCase):
    def test_posts_multipart_wav_and_reads_json_without_putting_key_in_body(self) -> None:
        captured: dict[str, object] = {}

        def opener(request: object, *, timeout: float) -> FakeResponse:
            captured["request"] = request
            captured["timeout"] = timeout
            return FakeResponse({"text": "transcribed"})

        transport = GroqHTTPTransport(
            api_key="gsk-transport-secret",
            timeout=4.5,
            opener=opener,
        )
        result = transport.transcribe(
            b"RIFF-fake-wav",
            model="whisper-test",
            language="fr",
            translate=False,
        )

        self.assertEqual(result, "transcribed")
        self.assertEqual(captured["timeout"], 4.5)
        request = captured["request"]
        body = request.data
        self.assertIn(b'name="file"; filename="speech.wav"', body)
        self.assertIn(b"RIFF-fake-wav", body)
        self.assertIn(b"whisper-test", body)
        self.assertIn(b"fr", body)
        self.assertNotIn(b"gsk-transport-secret", body)
        self.assertTrue(request.full_url.endswith("/transcriptions"))

    def test_normalizes_http_errors_without_response_body(self) -> None:
        def rejected(_request: object, *, timeout: float) -> FakeResponse:
            del timeout
            raise urllib.error.HTTPError("https://example.invalid", 401, "denied", {}, None)

        transport = GroqHTTPTransport(api_key="gsk-test-secret", opener=rejected)
        with self.assertRaisesRegex(GroqTransportError, "HTTP 401"):
            transport.transcribe(
                b"wav",
                model="whisper-test",
                language=None,
                translate=False,
            )
