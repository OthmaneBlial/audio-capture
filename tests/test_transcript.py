import unittest

from transcript import SegmentTracker, UndoHistory


class SegmentTrackerTests(unittest.TestCase):
    def test_states_have_stable_ordinals_and_bounded_visibility(self):
        tracker = SegmentTracker(max_visible=2)
        first = tracker.update("request-a", "pending")
        tracker.update("request-a", "complete")
        tracker.update("request-b", "error", "Provider unavailable")
        tracker.update("request-c", "pending")

        self.assertEqual(first.ordinal, 1)
        self.assertEqual([item.ordinal for item in tracker.visible()], [2, 3])
        self.assertEqual(tracker.visible()[0].detail, "Provider unavailable")

    def test_invalid_state_and_identifier_are_rejected(self):
        tracker = SegmentTracker()
        with self.assertRaises(ValueError):
            tracker.update("", "pending")
        with self.assertRaises(ValueError):
            tracker.update("request", "unknown")  # type: ignore[arg-type]


class UndoHistoryTests(unittest.TestCase):
    def test_undo_redo_and_new_edit_contract(self):
        history = UndoHistory(limit=2)
        history.remember("")
        history.remember("one")
        self.assertEqual(history.undo("one two"), "one")
        self.assertEqual(history.undo("one"), "")
        self.assertEqual(history.redo(""), "one")
        history.remember("replacement")
        self.assertFalse(history.can_redo)

    def test_limit_discards_oldest_snapshot(self):
        history = UndoHistory(limit=2)
        history.remember("a")
        history.remember("b")
        history.remember("c")
        self.assertEqual(history.undo("d"), "c")
        self.assertEqual(history.undo("c"), "b")
        self.assertEqual(history.undo("b"), "b")


if __name__ == "__main__":
    unittest.main()
