import logging
import stat
import tempfile
import unittest
from pathlib import Path

from config import ConfigManager
from exports import build_export, write_export
from history import HistoryStore
from transcription.groq_service import GroqTranscriptionService


class FailingTransport:
    def transcribe(self, _wav_data: bytes, **_kwargs: object) -> str:
        raise RuntimeError("provider rejected gsk-never-log-this transcript-never-log-this")


class PrivacyRegressionTests(unittest.TestCase):
    def test_defaults_do_not_persist_transcript_history(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            config = ConfigManager(Path(directory) / "config", environ={})
            store = HistoryStore(Path(directory) / "history")
            self.assertFalse(config.get("history_enabled"))
            self.assertFalse(store.path.exists())

    def test_cloud_transcription_creates_no_audio_file_and_redacts_provider_detail(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            before = set(root.rglob("*"))
            service = GroqTranscriptionService(
                api_key="gsk-secret-that-must-not-appear",
                transport_factory=lambda **_kwargs: FailingTransport(),
            )
            logger = logging.getLogger("transcription.groq_service")
            try:
                with self.assertLogs(logger, level="WARNING") as captured:
                    self.assertIsNone(service.transcribe(b"\x00\x00" * 160))
            finally:
                service.close(wait=True)
            output = " ".join(captured.output)
            self.assertNotIn("gsk-secret", output)
            self.assertNotIn("transcript-never", output)
            self.assertEqual(set(root.rglob("*")), before)

    def test_explicit_text_storage_is_owner_only_and_deletable(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            exported = root / "export" / "transcript.txt"
            write_export(exported, build_export("private text", "text"))
            self.assertEqual(stat.S_IMODE(exported.stat().st_mode), 0o600)
            store = HistoryStore(root / "history")
            store.add("private text", retention_days=7)
            self.assertEqual(stat.S_IMODE(store.path.stat().st_mode), 0o600)
            store.clear()
            self.assertFalse(store.path.exists())

    def test_privacy_documents_cover_every_sensitive_surface(self) -> None:
        root = Path(__file__).resolve().parents[1]
        combined = (
            (root / "docs" / "PRIVACY.md").read_text(encoding="utf-8")
            + (root / "docs" / "THREAT-MODEL.md").read_text(encoding="utf-8")
        ).lower()
        for term in (
            "microphone",
            "voice activity",
            "memory",
            "groq",
            "api key",
            "export",
            "history",
            "logs",
            "crash",
            "retention",
        ):
            self.assertIn(term, combined)


if __name__ == "__main__":
    unittest.main()
