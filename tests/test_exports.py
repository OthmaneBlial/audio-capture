import datetime as dt
import stat
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from exports import build_export, write_export


class ExportTests(unittest.TestCase):
    def setUp(self):
        self.moment = dt.datetime(2026, 8, 26, 18, 30, tzinfo=dt.timezone.utc)

    def test_builds_plain_markdown_and_timestamped_documents(self):
        plain = build_export(" Hello ", "text", created_at=self.moment)
        markdown = build_export("Hello", "markdown", created_at=self.moment)
        timestamped = build_export("Hello", "timestamped", created_at=self.moment)

        self.assertEqual(plain.content, "Hello\n")
        self.assertEqual(markdown.content, "# Voice transcript\n\nHello\n")
        self.assertEqual(markdown.extension, ".md")
        self.assertEqual(timestamped.content, "[2026-08-26 18:30:00 UTC] Hello\n")

    def test_owner_only_write_and_empty_rejection(self):
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory) / "nested" / "result.txt"
            write_export(destination, build_export("Private", "text", created_at=self.moment))
            self.assertEqual(destination.read_text(), "Private\n")
            self.assertEqual(stat.S_IMODE(destination.stat().st_mode), 0o600)
        with self.assertRaises(ValueError):
            build_export("  ", "text")

    def test_failed_atomic_write_preserves_existing_destination(self):
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory) / "result.txt"
            destination.write_text("old content\n", encoding="utf-8")
            with mock.patch("exports.os.fsync", side_effect=OSError("full disk")):
                with self.assertRaises(OSError):
                    write_export(destination, build_export("new content", "text"))
            self.assertEqual(destination.read_text(encoding="utf-8"), "old content\n")

    def test_symbolic_link_destination_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "target.txt"
            target.write_text("keep\n", encoding="utf-8")
            link = Path(directory) / "result.txt"
            link.symlink_to(target)
            with self.assertRaisesRegex(OSError, "symbolic link"):
                write_export(link, build_export("new", "text"))
            self.assertEqual(target.read_text(encoding="utf-8"), "keep\n")


if __name__ == "__main__":
    unittest.main()
