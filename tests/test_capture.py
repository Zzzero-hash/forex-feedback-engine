import unittest
import os
from src.ocr.capture import Capture

class TestCapture(unittest.TestCase):

    def setUp(self):
        self.capture = Capture()

    def test_capture_screenshot(self):
        # Use save_screenshot to write to file and return path
        filename = "test_capture.png"
        screenshot_path = self.capture.save_screenshot(filename)
        self.assertTrue(os.path.exists(screenshot_path), "Screenshot was not saved.")

    def test_capture_region(self):
        # Use save_screenshot with specified region
        region = {"top": 100, "left": 100, "width": 800, "height": 600}
        filename = "test_capture_region.png"
        screenshot_path = self.capture.save_screenshot(filename, region=region)
        self.assertTrue(os.path.exists(screenshot_path), "Screenshot for specified region was not saved.")

    def test_capture_quality(self):
        # Capture screenshot as PIL Image for quality check
        image = self.capture.capture_screenshot()
        self.assertIsNotNone(image, "Captured image is None.")
        self.assertGreater(image.size[0], 0, "Captured image width is 0.")
        self.assertGreater(image.size[1], 0, "Captured image height is 0.")

if __name__ == '__main__':
    unittest.main()