from mss import mss
import numpy as np
import cv2
import tempfile
import os
from PIL import Image

class Screenshot:
    """Wrapper for a PIL Image that also behaves as a path for os.PathLike."""
    def __init__(self, pil_img, path):
        self._pil_img = pil_img
        self._path = path

    def __fspath__(self):
        return self._path

    def __getattr__(self, name):
        return getattr(self._pil_img, name)

class Capture:
    def __init__(self, monitor_area=None):
        # Set monitor area to provided region or primary monitor by default
        if monitor_area is None:
            with mss() as sct:
                self.monitor_area = sct.monitors[1]
        else:
            self.monitor_area = monitor_area

    def take_screenshot(self, region=None):
        area = region or self.monitor_area
        with mss() as sct:
            img = sct.grab(area)
            img_np = np.array(img)
            img_bgr = cv2.cvtColor(img_np, cv2.COLOR_BGRA2BGR)
            return img_bgr

    def save_screenshot(self, filename, region=None):
        img = self.take_screenshot(region)
        cv2.imwrite(filename, img)
        return filename

    def capture_screenshot(self, filename=None, region=None):
        """
        Capture screenshot, save to filename or temporary file, and return a Screenshot object.
        """
        img = self.take_screenshot(region)
        # Convert BGR to RGB for PIL
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(img_rgb)
        # Determine file path
        if filename:
            save_path = filename
        else:
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
            save_path = tmp.name
            tmp.close()
        pil_img.save(save_path)
        return Screenshot(pil_img, save_path)