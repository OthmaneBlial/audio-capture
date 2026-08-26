import tempfile
import unittest
from pathlib import Path

from benchmarks.prepare_librispeech import deterministic_sample
from benchmarks.run_benchmark import normalize_words, percentile, word_error_counts


class BenchmarkHarnessTests(unittest.TestCase):
    def test_word_error_counts_normalize_case_and_punctuation(self):
        self.assertEqual(normalize_words("Hello, CAFÉ!"), ["hello", "café"])
        self.assertEqual(word_error_counts("one two three", "one too three"), (1, 3))
        self.assertEqual(word_error_counts("keep these words", "keep words"), (1, 3))

    def test_percentile_is_interpolated_and_requires_values(self):
        self.assertEqual(percentile([10.0, 20.0, 30.0], 0.5), 20.0)
        self.assertEqual(percentile([10.0, 20.0], 0.95), 19.5)
        with self.assertRaises(ValueError):
            percentile([], 0.5)

    def test_corpus_selection_is_deterministic_and_speaker_diverse(self):
        entries = [
            {"id": "2-1-0001", "speaker": "2"},
            {"id": "1-1-0002", "speaker": "1"},
            {"id": "1-1-0001", "speaker": "1"},
            {"id": "2-1-0002", "speaker": "2"},
        ]
        self.assertEqual(
            [entry["id"] for entry in deterministic_sample(entries, 3)],
            ["1-1-0001", "2-1-0001", "1-1-0002"],
        )

    def test_manifest_helpers_leave_no_implicit_corpus_files(self):
        with tempfile.TemporaryDirectory() as directory:
            self.assertEqual(list(Path(directory).iterdir()), [])


if __name__ == "__main__":
    unittest.main()
