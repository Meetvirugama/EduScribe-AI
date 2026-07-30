"""
Unit tests for transcript_matcher module.
"""
import json
import os
import tempfile
import unittest

from services.vision.transcript_matcher import TranscriptMatcherService


class TestFindMatchingSegment(unittest.TestCase):
    def setUp(self):
        self.matcher = TranscriptMatcherService()
        self.segments = [
            {"start": 0.0, "end": 10.0, "text": "Introduction to binary search"},
            {"start": 10.0, "end": 25.0, "text": "The algorithm divides the array"},
            {"start": 25.0, "end": 40.0, "text": "Time complexity is O log n"},
        ]

    def test_exact_range_match(self):
        seg = self.matcher.find_matching_segment(5000, self.segments)
        self.assertIsNotNone(seg)
        self.assertEqual(seg["text"], "Introduction to binary search")

    def test_nearest_midpoint_fallback(self):
        # 50s is after all segments; should match last segment
        seg = self.matcher.find_matching_segment(50_000, self.segments)
        self.assertIsNotNone(seg)
        self.assertEqual(seg["text"], "Time complexity is O log n")

    def test_empty_segments_returns_none(self):
        result = self.matcher.find_matching_segment(5000, [])
        self.assertIsNone(result)


class TestScoreSimilarity(unittest.TestCase):
    def setUp(self):
        self.matcher = TranscriptMatcherService()

    def test_identical_strings_max_score(self):
        score = self.matcher.score_similarity("binary search", "binary search")
        self.assertAlmostEqual(score, 1.0, places=1)

    def test_empty_strings_zero_score(self):
        self.assertEqual(self.matcher.score_similarity("", "anything"), 0.0)
        self.assertEqual(self.matcher.score_similarity("anything", ""), 0.0)

    def test_unrelated_strings_low_score(self):
        score = self.matcher.score_similarity("photosynthesis", "quicksort pivot")
        self.assertLess(score, 0.4)


class TestMatchFramesToTranscript(unittest.TestCase):
    def setUp(self):
        self.matcher = TranscriptMatcherService()
        self.tmp = tempfile.mkdtemp()

    def _write_transcript(self, segments: list) -> str:
        path = os.path.join(self.tmp, "transcript.json")
        with open(path, "w") as f:
            json.dump(segments, f)
        return path

    def test_frames_enriched_with_similarity(self):
        path = self._write_transcript([
            {"start": 0.0, "end": 10.0, "text": "Binary search"},
        ])
        frames = [{"timestamp_ms": 5000, "clean_text": "Binary Search", "scene_number": 1}]
        result = self.matcher.match_frames_to_transcript(frames, path)
        self.assertEqual(len(result), 1)
        self.assertIn("transcript_similarity", result[0])
        self.assertGreater(result[0]["transcript_similarity"], 0.5)

    def test_missing_transcript_returns_zero_similarity(self):
        frames = [{"timestamp_ms": 1000, "clean_text": "test", "scene_number": 1}]
        result = self.matcher.match_frames_to_transcript(frames, "/nonexistent/t.json")
        self.assertEqual(result[0]["transcript_similarity"], 0.0)


if __name__ == "__main__":
    unittest.main()
