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

    def test_retained_state_is_bounded_after_many_requests(self):
        tracker = SegmentTracker(max_visible=4)
        for index in range(10_000):
            tracker.update(f"request-{index}", "complete")

        self.assertEqual(tracker.retained_count, 4)
        self.assertEqual([item.ordinal for item in tracker.visible()], [9_997, 9_998, 9_999, 10_000])

    def test_clear_discards_visible_states(self):
        tracker = SegmentTracker(max_visible=2)
        tracker.update("request-a", "pending")
        tracker.update("request-b", "complete")
        tracker.clear()
        self.assertEqual(tracker.visible(), [])
        self.assertEqual(tracker.retained_count, 0)


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

    def test_clear_discards_undo_and_redo_snapshots(self):
        history = UndoHistory()
        history.remember("before clear")
        self.assertEqual(history.undo("after clear"), "before clear")
        history.remember("before redo")
        history.clear()
        self.assertFalse(history.can_undo)
        self.assertFalse(history.can_redo)
        self.assertEqual(history.undo("new transcript"), "new transcript")


if __name__ == "__main__":
    unittest.main()
