from mss import mss
import numpy as np
import cv2

class Capture:
    def __init__(self, monitor_area):
        self.monitor_area = monitor_area

    def take_screenshot(self):
        with mss() as sct:
            img = sct.grab(self.monitor_area)
            img_np = np.array(img)
            img_bgr = cv2.cvtColor(img_np, cv2.COLOR_BGRA2BGR)
            return img_bgr

    def save_screenshot(self, filename):
        img = self.take_screenshot()
        cv2.imwrite(filename, img)