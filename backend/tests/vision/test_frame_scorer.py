"""
Unit tests for frame_scorer module.
"""
import unittest

from services.vision.frame_scorer import (
    compute_frame_score,
    rank_and_select_frames,
)


class TestComputeFrameScore(unittest.TestCase):
    def test_empty_frame_returns_low_score(self):
        score = compute_frame_score({})
        self.assertGreaterEqual(score, 0.0)
        self.assertLessEqual(score, 1.0)

    def test_high_quality_frame_scores_higher(self):
        rich = {
            "clean_text": "def binary_search(arr, target):\n    lo, hi = 0, len(arr) - 1",
            "transcript_similarity": 0.85,
            "blur_score": 500.0,
            "duration_ms": 30000,
        }
        empty = {
            "clean_text": "",
            "transcript_similarity": 0.0,
            "blur_score": 20.0,
            "duration_ms": 500,
        }
        self.assertGreater(compute_frame_score(rich), compute_frame_score(empty))

    def test_score_clamped_to_unit_interval(self):
        extreme = {
            "clean_text": "x" * 5000,
            "transcript_similarity": 1.0,
            "blur_score": 999999.0,
            "duration_ms": 9999999,
        }
        score = compute_frame_score(extreme)
        self.assertLessEqual(score, 1.0)
        self.assertGreaterEqual(score, 0.0)

    def test_code_heuristic_boosts_score(self):
        with_code = {"clean_text": "def foo(): return 42", "transcript_similarity": 0.0, "blur_score": 200.0, "duration_ms": 5000}
        no_code = {"clean_text": "This is a slide", "transcript_similarity": 0.0, "blur_score": 200.0, "duration_ms": 5000}
        self.assertGreater(compute_frame_score(with_code), compute_frame_score(no_code))


class TestRankAndSelectFrames(unittest.TestCase):
    def _make_frames(self):
        return [
            {"clean_text": "", "transcript_similarity": 0.1, "blur_score": 50.0, "duration_ms": 2000},
            {"clean_text": "import numpy as np\n# matrix multiplication", "transcript_similarity": 0.9, "blur_score": 800.0, "duration_ms": 45000},
            {"clean_text": "Summary", "transcript_similarity": 0.5, "blur_score": 300.0, "duration_ms": 10000},
        ]

    def test_returns_all_frames(self):
        frames = self._make_frames()
        result = rank_and_select_frames(frames, top_n=1)
        self.assertEqual(len(result), 3)

    def test_top_1_selects_exactly_one(self):
        frames = self._make_frames()
        result = rank_and_select_frames(frames, top_n=1)
        selected = [f for f in result if f["is_selected"]]
        self.assertEqual(len(selected), 1)

    def test_best_frame_is_selected(self):
        frames = self._make_frames()
        result = rank_and_select_frames(frames, top_n=1)
        selected = [f for f in result if f["is_selected"]][0]
        # The code frame should win
        self.assertIn("import numpy", selected.get("clean_text", ""))

    def test_empty_list_returns_empty(self):
        self.assertEqual(rank_and_select_frames([], top_n=1), [])


if __name__ == "__main__":
    unittest.main()
