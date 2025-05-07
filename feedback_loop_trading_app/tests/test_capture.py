import unittest
from src.ocr.capture import Capture

class TestCapture(unittest.TestCase):

    def setUp(self):
        self.capture = Capture()

    def test_capture_screenshot(self):
        # Assuming the capture method returns the path of the saved screenshot
        screenshot_path = self.capture.capture_screenshot()
        self.assertTrue(os.path.exists(screenshot_path), "Screenshot was not saved.")

    def test_capture_region(self):
        # Assuming the capture method can take a specific region
        region = {"top": 100, "left": 100, "width": 800, "height": 600}
        screenshot_path = self.capture.capture_screenshot(region=region)
        self.assertTrue(os.path.exists(screenshot_path), "Screenshot for specified region was not saved.")

    def test_capture_quality(self):
        # Assuming the capture method returns an image object
        image = self.capture.capture_screenshot()
        self.assertIsNotNone(image, "Captured image is None.")
        self.assertGreater(image.size[0], 0, "Captured image width is 0.")
        self.assertGreater(image.size[1], 0, "Captured image height is 0.")

if __name__ == '__main__':
    unittest.main()