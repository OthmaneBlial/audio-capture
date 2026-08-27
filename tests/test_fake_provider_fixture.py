"""Unit tests for the test-only fake provider boundary contract fixture."""

from __future__ import annotations

import threading
import unittest

from fake_provider_fixture import FakeProviderConfig, FakeTranscriptionProvider

from transcription.provider import ProviderError

SYNTHETIC_PCM = b"\x00\x00" * 80


class FakeProviderFixtureTests(unittest.TestCase):
    def test_declares_capabilities_languages_translation_and_boundary(self) -> None:
        provider = FakeTranscriptionProvider()
        try:
            self.assertEqual(provider.provider_id, "fake")
            self.assertTrue(provider.configured)
            self.assertTrue(provider.capabilities.transcription)
            self.assertTrue(provider.capabilities.translation_to_english)
            self.assertTrue(provider.capabilities.automatic_language)
            self.assertIn("fr", provider.capabilities.supported_languages)
            self.assertIn("Bounded", provider.capabilities.limits)
            self.assertIn("cancel", provider.capabilities.cancellation.lower())
            self.assertIn("in-process", provider.boundary.audio_destination.lower())
            self.assertEqual(provider.boundary.credential, "None")
            self.assertIn("No PCM", provider.boundary.storage_statement)
        finally:
            provider.close(wait=True)

    def test_complete_path_is_deterministic_without_io(self) -> None:
        received: list = []
        states: list = []
        provider = FakeTranscriptionProvider(
            FakeProviderConfig(default_text="synthetic phrase"),
            on_transcription=received.append,
            on_request_state=lambda rid, state, detail: states.append((rid, state, detail)),
        )
        try:
            future = provider.transcribe_async(SYNTHETIC_PCM)
            self.assertIsNotNone(future)
            assert future is not None
            self.assertEqual(future.result(timeout=2), "synthetic phrase")
            self._wait_for(lambda: any(state == "complete" for _, state, _ in states))
            self.assertEqual(received, ["synthetic phrase"])
            self.assertEqual([state for _, state, _ in states], ["pending", "complete"])
            joined = " ".join(detail or "" for _, _, detail in states)
            self.assertNotIn("synthetic phrase", joined)
            for record in provider.request_records():
                self.assertNotIn("synthetic phrase", record.detail)
                self.assertEqual(record.audio_byte_length, len(SYNTHETIC_PCM))
                self.assertIsInstance(record.request_id, str)
        finally:
            provider.close(wait=True)

    def test_error_outcome_normalizes_and_reports_state(self) -> None:
        errors: list = []
        states: list = []
        provider = FakeTranscriptionProvider(
            outcomes=[RuntimeError("HTTP 401 invalid api key")],
            on_error=errors.append,
            on_request_state=lambda _rid, state, _detail: states.append(state),
        )
        try:
            future = provider.transcribe_async(SYNTHETIC_PCM)
            assert future is not None
            self.assertIsNone(future.result(timeout=2))
            self._wait_for(lambda: "error" in states)
            self.assertEqual(states, ["pending", "error"])
            self.assertEqual(len(errors), 1)
            self.assertIsInstance(errors[0], ProviderError)
            self.assertEqual(errors[0].code, "authentication")
            self.assertFalse(errors[0].retryable)
        finally:
            provider.close(wait=True)

    def test_provider_error_codes_for_rate_limit_and_network(self) -> None:
        provider = FakeTranscriptionProvider(
            outcomes=[
                RuntimeError("429 rate limit"),
                RuntimeError("connection timed out"),
            ],
        )
        try:
            errors: list = []
            provider._on_error = errors.append
            self.assertIsNone(provider.transcribe(SYNTHETIC_PCM))
            self.assertIsNone(provider.transcribe(SYNTHETIC_PCM))
            self.assertEqual([error.code for error in errors], ["rate_limit", "network"])
            self.assertTrue(all(error.retryable for error in errors))
        finally:
            provider.close(wait=True)

    def test_bounded_queue_rejects_excess_work(self) -> None:
        release = threading.Event()
        errors: list = []
        provider = FakeTranscriptionProvider(
            FakeProviderConfig(max_workers=1, max_pending_requests=1),
            hold_event=release,
            on_error=errors.append,
        )
        try:
            first = provider.transcribe_async(SYNTHETIC_PCM)
            self.assertIsNotNone(first)
            # Worker holds the only pending slot while blocked on hold_event.
            threading.Event().wait(0.05)
            second = provider.transcribe_async(SYNTHETIC_PCM)
            self.assertIsNone(second)
            self.assertTrue(errors)
            self.assertIsInstance(errors[-1], ProviderError)
            self.assertEqual(errors[-1].code, "queue_full")
            self.assertIn("queue is full", str(errors[-1]).lower())
            release.set()
            assert first is not None
            self.assertEqual(first.result(timeout=2), "test transcript")
        finally:
            release.set()
            provider.close(wait=True)

    def test_cancellation_of_queued_work(self) -> None:
        release = threading.Event()
        states: list = []
        provider = FakeTranscriptionProvider(
            FakeProviderConfig(max_workers=1, max_pending_requests=4),
            hold_event=release,
            on_request_state=lambda rid, state, _detail: states.append((rid, state)),
        )
        try:
            first = provider.transcribe_async(SYNTHETIC_PCM)
            second = provider.transcribe_async(SYNTHETIC_PCM)
            self.assertIsNotNone(first)
            self.assertIsNotNone(second)
            # First is running (held); second should still be cancellable in the queue.
            cancelled = provider.cancel_pending()
            self.assertGreaterEqual(cancelled, 1)
            release.set()
            assert first is not None
            self.assertEqual(first.result(timeout=2), "test transcript")
            self._wait_for(lambda: any(state == "cancelled" for _, state in states))
            self.assertIn("cancelled", [state for _, state in states])
            self.assertIn("complete", [state for _, state in states])
        finally:
            release.set()
            provider.close(wait=True)

    def test_request_tracking_stores_neither_pcm_nor_transcript(self) -> None:
        secret_text = "unique-transcript-token-zz9"
        pcm = b"\x11\x22" * 64
        provider = FakeTranscriptionProvider(FakeProviderConfig(default_text=secret_text))
        try:
            self.assertEqual(provider.transcribe(pcm), secret_text)
            future = provider.transcribe_async(pcm)
            assert future is not None
            self.assertEqual(future.result(timeout=2), secret_text)
            self._wait_for(
                lambda: any(record.state == "complete" for record in provider.request_records())
            )
            blob = repr(provider.request_records())
            self.assertNotIn(secret_text, blob)
            self.assertNotIn(pcm.hex(), blob)
            for record in provider.request_records():
                self.assertEqual(record.audio_byte_length, len(pcm))
                self.assertNotEqual(record.detail, secret_text)
        finally:
            provider.close(wait=True)

    def test_translation_language_config_and_invalid_audio(self) -> None:
        errors: list = []
        provider = FakeTranscriptionProvider(
            FakeProviderConfig(default_text="words"),
            on_error=errors.append,
        )
        try:
            provider.update_config(language="fr", translate=True)
            self.assertEqual(provider.transcribe(SYNTHETIC_PCM), "en:words")
            self.assertIsNone(provider.transcribe(b"\x00"))
            self.assertTrue(errors)
            self.assertEqual(errors[-1].code, "invalid_audio")
            provider.set_configured(False)
            self.assertFalse(provider.configured)
            self.assertIsNone(provider.transcribe(SYNTHETIC_PCM))
            self.assertEqual(errors[-1].code, "not_configured")
        finally:
            provider.close(wait=True)

    def test_fixture_requires_no_network_native_audio_key_or_model(self) -> None:
        """Sanity: constructing and driving the fixture needs only the stdlib + package."""
        import sys

        blocked = {
            "socket",
            "ssl",
            "http.client",
            "urllib.request",
            "subprocess",
            "pyaudio",
            "webrtcvad",
        }
        removed = {}
        for name in list(blocked):
            if name in sys.modules:
                removed[name] = sys.modules.pop(name)
        try:
            provider = FakeTranscriptionProvider()
            try:
                self.assertTrue(provider.configured)
                self.assertEqual(provider.transcribe(SYNTHETIC_PCM), "test transcript")
                self.assertEqual(provider.cancel_pending(), 0)
            finally:
                provider.close(wait=True)
        finally:
            sys.modules.update(removed)

    def _wait_for(self, predicate, attempts: int = 200) -> None:
        for _ in range(attempts):
            if predicate():
                return
            threading.Event().wait(0.001)
        self.fail("condition not met in time")


if __name__ == "__main__":
    unittest.main()
