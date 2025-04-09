import cv2
import numpy as np
import pygetwindow as gw
import os
import pyautogui
import time
import json
import keyboard
from stateManager import state_manager

class TemplateConfig:
    def __init__(self, filename, region=None, directory=None):
        self.filename = filename
        self.region = tuple(region) if region else None
        self.template = None
        self.directory = directory

class SeeLoja:
    def __init__(self):
        # Carregar configurações do arquivo JSON
        self.config = self._load_config()
        
        # Configurar janela
        self.window_name = self.config["window"]["name"]
        self.emulator_width = self.config["window"]["width"]
        self.emulator_height = self.config["window"]["height"]
        self.window_height = self.config["window"]["window_height"]
        self.top_offset = self.window_height - self.emulator_height
        
        # Status das boxes
        self.box_status = {f"box{i}": "gray" for i in range(1, 11)}
        
        # Flag para box10 ativa/desativa
        self.box10_enabled = True
        
        # Configurar templates
        self.template_configs = {}
        for name, template_data in self.config["templates"].items():
            self.template_configs[name] = TemplateConfig(
                filename=template_data["filename"],
                region=template_data.get("region"),
                directory=template_data.get("directory", "")
            )
        
        # Carregar templates
        self._load_templates()
        
        # Cache da janela do emulador
        self.window = None

    def _load_config(self):
        """Carrega as configurações do arquivo JSON"""
        config_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "cfg",
            "seeLojaCFG.json"
        )
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _load_templates(self):
        """Carrega todas as imagens de template necessárias"""
        for name, config in self.template_configs.items():
            template_path = os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                "dataset",
                config.directory,
                config.filename
            )
            if os.path.exists(template_path):
                template = cv2.imread(template_path)
                if template is not None:
                    config.template = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)

    def get_emulator_window(self):
        """Obtém e ativa a janela do emulador"""
        if self.window is None:
            try:
                windows = gw.getWindowsWithTitle(self.window_name)
                if not windows:
                    print(f"Janela '{self.window_name}' não encontrada")
                    return None
                
                self.window = windows[0]
            except Exception as e:
                print(f"Erro ao obter janela do emulador: {e}")
                return None
        
        try:
            self.window.activate()
        except Exception:
            self.window = None
            return self.get_emulator_window()
        
        return self.window

    def capture_screen(self):
        """Captura a tela do emulador"""
        window = self.get_emulator_window()
        if not window:
            return None

        try:
            screenshot = pyautogui.screenshot(region=(
                window.left,
                window.top + self.top_offset,
                self.emulator_width,
                self.emulator_height
            ))
            return cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
        except Exception as e:
            print(f"Erro ao capturar tela: {e}")
            return None

    def encontrar_template_na_tela(self, screenshot, template_name, region=None):
        """Procura um template específico na tela"""
        config = self.template_configs[template_name]
        if config.template is None:
            return False

        try:
            if region:
                x, y, w, h = region
                roi = screenshot[y:y+h, x:x+w]
            else:
                roi = screenshot

            # Converter ROI para escala de cinza
            roi_gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)

            # Template matching
            resultado = cv2.matchTemplate(roi_gray, config.template, cv2.TM_CCOEFF_NORMED)
            _, max_val, _, _ = cv2.minMaxLoc(resultado)

            return max_val >= 0.8

        except Exception as e:
            print(f"Erro ao procurar template {template_name}: {e}")
            return False

    def verificar_box(self, box_name, check_state=False, window=None, screenshot=None):
        """Verifica o estado de uma box específica"""
        try:
            if check_state and state_manager.get_current_state() != "Dentro da Loja":
                print("Não está dentro da loja!")
                return False

            # Usa a janela passada ou obtém uma nova
            if window is None:
                window = self.get_emulator_window()
                if not window:
                    return False

            # Clica na posição da box
            click_pos = self.config["click_positions"][box_name]
            pyautogui.click(
                window.left + click_pos[0],
                window.top + self.top_offset + click_pos[1]
            )
            time.sleep(self.config["delays"]["after_click"])

            # Usa o screenshot passado ou captura um novo
            if screenshot is None:
                screenshot = self.capture_screen()
                if screenshot is None:
                    return False

            # Verifica se está escolhendo item
            if self.encontrar_template_na_tela(screenshot, "escolhendo_item", self.template_configs["escolhendo_item"].region):
                keyboard.press_and_release('esc')
                time.sleep(self.config["delays"]["after_esc"])
                self.box_status[box_name] = "green"
                return True

            # Verifica se tem lixeira (item vendido)
            if self.encontrar_template_na_tela(screenshot, "lixo", self.template_configs["lixo"].region):
                keyboard.press_and_release('esc')
                time.sleep(self.config["delays"]["after_esc"])
                self.box_status[box_name] = "red"
                return True

            # Se não encontrou nenhum dos dois, está vazia
            self.box_status[box_name] = "green"
            return True

        except Exception as e:
            print(f"Erro ao verificar {box_name}: {e}")
            self.box_status[box_name] = "gray"
            return False

    def sync_shop(self):
        """Sincroniza o estado de todas as boxes"""
        try:
            # Obtém a janela uma única vez
            window = self.get_emulator_window()
            if not window:
                return "Erro: Não foi possível encontrar a janela do emulador"

            # Verifica o estado apenas na primeira box
            first_box = list(self.config["click_positions"].keys())[0]
            if not self.verificar_box(first_box, check_state=True, window=window):
                return "Aviso: Entre na loja primeiro"

            # Verifica as outras boxes sem checar o estado
            boxes_to_check = list(self.config["click_positions"].keys())[1:]
            
            # Se box10 está desativada, remove da lista
            if not self.box10_enabled:
                boxes_to_check = [box for box in boxes_to_check if box != "box10"]
                self.box_status["box10"] = "orange"  # Define status como laranja quando desativada
            
            for box_name in boxes_to_check:
                self.verificar_box(box_name, check_state=False, window=window)
                time.sleep(self.config["delays"]["between_boxes"])
            
            return "Loja sincronizada com sucesso!"
        except Exception as e:
            print(f"Erro ao sincronizar loja: {e}")
            return f"Erro ao sincronizar loja: {str(e)}"

    def toggle_box10(self):
        """Ativa/desativa a box10"""
        self.box10_enabled = not self.box10_enabled
        if not self.box10_enabled:
            self.box_status["box10"] = "orange"  # Define status como laranja quando desativada
        return self.box10_enabled

    def get_box_status(self):
        """Retorna o status atual de todas as boxes"""
        return self.box_status
