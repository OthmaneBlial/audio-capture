import datetime as dt
import json
import stat
import tempfile
import unittest
from pathlib import Path

from history import HistoryStore


class Clock:
    def __init__(self, value):
        self.value = value

    def __call__(self):
        return self.value


class HistoryStoreTests(unittest.TestCase):
    def test_opt_in_store_deduplicates_prunes_and_uses_private_permissions(self):
        with tempfile.TemporaryDirectory() as directory:
            clock = Clock(dt.datetime(2026, 8, 1, tzinfo=dt.timezone.utc))
            store = HistoryStore(Path(directory) / "history", now=clock)
            first = store.add("first", retention_days=7)
            duplicate = store.add("first", retention_days=7)
            self.assertEqual(first.id, duplicate.id)
            clock.value = dt.datetime(2026, 8, 10, tzinfo=dt.timezone.utc)
            second = store.add("second", retention_days=7)

            self.assertEqual([item.id for item in store.list(retention_days=7)], [second.id])
            self.assertEqual(stat.S_IMODE(store.path.stat().st_mode), 0o600)
            self.assertEqual(stat.S_IMODE(store.path.parent.stat().st_mode), 0o700)

    def test_delete_clear_and_invalid_or_future_schema_fail_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            store = HistoryStore(Path(directory) / "history")
            entry = store.add("temporary", retention_days=30)
            self.assertTrue(store.delete(entry.id))
            self.assertEqual(store.list(retention_days=30), [])
            store.add("temporary", retention_days=30)
            store.clear()
            self.assertFalse(store.path.exists())

            store.path.parent.mkdir(parents=True)
            future_payload = json.dumps({"schema_version": 99, "entries": [{"text": "secret"}]})
            store.path.write_text(future_payload)
            with self.assertRaisesRegex(ValueError, "unsupported history schema"):
                store.list(retention_days=30)
            self.assertEqual(store.path.read_text(), future_payload)

    def test_retention_validation(self):
        with tempfile.TemporaryDirectory() as directory:
            store = HistoryStore(Path(directory))
            for value in (0, 366, True):
                with self.assertRaises(ValueError):
                    store.list(retention_days=value)  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()
