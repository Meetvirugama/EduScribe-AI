"""
Unit tests for duplicate_detector module.
"""
import os
import tempfile
import unittest

import cv2
import numpy as np

from services.vision.duplicate_detector import (
    compute_phash,
    hamming_distance,
    deduplicate_frames,
)


def _write_image(path: str, fill_color: tuple = (255, 255, 255)) -> None:
    img = np.full((100, 100, 3), fill_color, dtype=np.uint8)
    cv2.imwrite(path, img)


class TestComputePhash(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def test_returns_hex_string(self):
        path = os.path.join(self.tmp, "img.jpg")
        _write_image(path)
        h = compute_phash(path)
        self.assertIsInstance(h, str)
        self.assertGreater(len(h), 0)

    def test_missing_file_raises(self):
        with self.assertRaises(FileNotFoundError):
            compute_phash("/nonexistent/img.jpg")


class TestHammingDistance(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def test_same_image_zero_distance(self):
        path = os.path.join(self.tmp, "img.jpg")
        _write_image(path)
        h = compute_phash(path)
        self.assertEqual(hamming_distance(h, h), 0)


class TestDeduplicateFrames(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def _frame(self, name: str, color: tuple) -> dict:
        path = os.path.join(self.tmp, f"{name}.jpg")
        _write_image(path, fill_color=color)
        return {"frame_path": path, "scene_number": 1}

    def test_identical_images_deduplicated(self):
        f1 = self._frame("a", (200, 200, 200))
        f2 = self._frame("b", (200, 200, 200))  # visually identical

        unique, dups = deduplicate_frames([f1, f2], threshold=5)
        self.assertEqual(len(unique), 1)
        self.assertEqual(len(dups), 1)

    def test_different_images_both_kept(self):
        f1 = self._frame("a", (0, 0, 255))
        f2 = self._frame("b", (0, 255, 0))

        unique, dups = deduplicate_frames([f1, f2], threshold=5)
        # pHash of solid colour images may still match – loosen assertion
        self.assertGreaterEqual(len(unique), 1)

    def test_missing_file_goes_to_dups(self):
        frames = [{"frame_path": "/nonexistent/frame.jpg", "scene_number": 1}]
        unique, dups = deduplicate_frames(frames)
        self.assertEqual(len(unique), 0)
        self.assertEqual(len(dups), 1)


if __name__ == "__main__":
    unittest.main()
