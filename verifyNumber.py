import cv2
import numpy as np
import pygetwindow as gw
import pyautogui
import sys
from stateManager import state_manager
import os
import sys

def get_resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class NumberVerifier:
    def __init__(self):
        self.templates = {}
        # Carrega os templates dos números
        for i in range(1, 11):  # 1 a 10
            template_path = get_resource_path(f'dataset/numbers/{i}.png')
            if os.path.exists(template_path):
                template = cv2.imread(template_path)
                if template is not None:
                    template = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
                    self.templates[str(i)] = template

    def get_screenshot(self, x, y, width, height):
        """Captura screenshot da região específica"""
        windows = gw.getWindowsWithTitle(state_manager.window_name)
        if not windows:
            return None
            
        window = windows[0]
        try:
            window.activate()
        except Exception:
            return None
            
        x_offset = window.left
        y_offset = window.top + state_manager.top_offset
        screenshot = pyautogui.screenshot(region=(x_offset + x, y_offset + y, width, height))
        img = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
        return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    def verify_number(self, x=390, y=165, width=20, height=29):
        """Verifica qual número está na região usando template matching"""
        img = self.get_screenshot(x, y, width, height)
        if img is None:
            return None

        best_match = None
        best_val = -1

        for number, template in self.templates.items():
            result = cv2.matchTemplate(img, template, cv2.TM_CCOEFF_NORMED)
            _, max_val, _, _ = cv2.minMaxLoc(result)

            if max_val > best_val:
                best_val = max_val
                best_match = number

        return best_match if best_val > 0.5 else None

# Exemplo de uso
if __name__ == "__main__":
    verifier = NumberVerifier()
    result = verifier.verify_number()
    print(f"Número encontrado: {result}")
