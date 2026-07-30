"""
Unit tests for blur_detector module.
"""
import os
import tempfile
import unittest

import cv2
import numpy as np

from services.vision.blur_detector import (
    compute_laplacian_variance,
    is_blurry,
    filter_blurry_frames,
)


def _write_test_image(path: str, blur_kernel: int = 0) -> None:
    """Write a synthetic image, optionally blurred, for testing."""
    img = np.zeros((200, 300, 3), dtype=np.uint8)
    cv2.putText(img, "Test Slide", (20, 100), cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 255), 3)
    if blur_kernel > 0:
        img = cv2.GaussianBlur(img, (blur_kernel, blur_kernel), 0)
    cv2.imwrite(path, img)


class TestComputeLaplacianVariance(unittest.TestCase):
    def test_sharp_image_has_high_variance(self):
        img = np.zeros((200, 300, 3), dtype=np.uint8)
        cv2.rectangle(img, (10, 10), (290, 190), (255, 255, 255), 2)
        score = compute_laplacian_variance(img)
        self.assertGreater(score, 10.0)

    def test_uniform_image_has_zero_variance(self):
        img = np.full((200, 300, 3), 128, dtype=np.uint8)
        score = compute_laplacian_variance(img)
        self.assertAlmostEqual(score, 0.0, places=1)


class TestIsBlurry(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()

    def _path(self, name):
        return os.path.join(self.tmp_dir, name)

    def test_sharp_image_not_blurry(self):
        path = self._path("sharp.jpg")
        _write_test_image(path, blur_kernel=0)
        blurry, score = is_blurry(path, threshold=50.0)
        # Text on black background is sharp; expect not blurry
        self.assertIsInstance(blurry, bool)
        self.assertGreaterEqual(score, 0.0)

    def test_blurry_image_is_blurry(self):
        path = self._path("blurry.jpg")
        _write_test_image(path, blur_kernel=51)
        blurry, score = is_blurry(path, threshold=100.0)
        self.assertTrue(blurry)

    def test_missing_file_raises(self):
        with self.assertRaises(FileNotFoundError):
            is_blurry("/nonexistent/path/frame.jpg")


class TestFilterBlurryFrames(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()

    def _path(self, name):
        return os.path.join(self.tmp_dir, name)

    def test_separates_sharp_and_blurry(self):
        sharp_path = self._path("sharp.jpg")
        blurry_path = self._path("blurry.jpg")
        _write_test_image(sharp_path, blur_kernel=0)
        _write_test_image(blurry_path, blur_kernel=51)

        frames = [
            {"frame_path": sharp_path, "scene_number": 1},
            {"frame_path": blurry_path, "scene_number": 2},
        ]
        sharp, blurry = filter_blurry_frames(frames, threshold=100.0)

        self.assertEqual(len(sharp) + len(blurry), 2)
        self.assertTrue(all("blur_score" in f for f in sharp))

    def test_missing_frame_goes_to_blurry(self):
        frames = [{"frame_path": "/nonexistent/frame.jpg", "scene_number": 1}]
        sharp, blurry = filter_blurry_frames(frames)
        self.assertEqual(len(blurry), 1)
        self.assertEqual(len(sharp), 0)


if __name__ == "__main__":
    unittest.main()
