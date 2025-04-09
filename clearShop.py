import cv2
import numpy as np
import pygetwindow as gw
import os
import pyautogui
import time
import json
from stateManager import state_manager

class TemplateConfig:
    def __init__(self, filename, region=None):
        self.filename = filename
        self.region = tuple(region) if region else None
        self.template = None

class BoxState:
    EMPTY = "empty"
    WITH_ITEM = "with_item"
    SOLD = "sold"

class ClearShopBot:
    def __init__(self):
        # Carregar configurações do arquivo JSON
        self.config = self._load_config()
        
        # Configurar janela
        self.window_name = self.config["window"]["name"]
        self.emulator_width = self.config["window"]["width"]
        self.emulator_height = self.config["window"]["height"]
        self.window_height = self.config["window"]["window_height"]
        self.top_offset = self.window_height - self.emulator_height
        
        # Configurar templates para cada caixa
        self.box_templates = {}
        for box_name, box_config in self.config["boxes"].items():
            self.box_templates[box_name] = {
                BoxState.EMPTY: TemplateConfig(
                    filename=box_config["empty"]["filename"],
                    region=box_config["empty"]["region"]
                ),
                BoxState.WITH_ITEM: TemplateConfig(
                    filename=box_config["with_item"]["filename"],
                    region=box_config["with_item"]["region"]
                ),
                BoxState.SOLD: TemplateConfig(
                    filename=box_config["sold"]["filename"],
                    region=box_config["sold"]["region"]
                )
            }
        
        # Carregar templates
        self._load_templates()

    def _load_config(self):
        """Carrega as configurações do arquivo JSON"""
        config_path = os.path.join(
            os.path.dirname(__file__),
            'cfg',
            'clearShopCFG.json'
        )
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            raise Exception(f"Erro ao carregar arquivo de configuração: {e}")

    def _load_templates(self):
        """Carrega todas as imagens de template necessárias"""
        template_dir = os.path.join(os.path.dirname(__file__), 'dataset', 'variable')
        
        for box_configs in self.box_templates.values():
            for config in box_configs.values():
                path = os.path.join(template_dir, config.filename)
                try:
                    template = cv2.imread(path, cv2.IMREAD_COLOR)
                    if template is None:
                        raise FileNotFoundError(f"Não foi possível carregar: {path}")
                    config.template = template
                except Exception as e:
                    print(f"Erro ao carregar template {config.filename}: {e}")

    def get_emulator_window(self):
        """Obtém e ativa a janela do emulador"""
        try:
            windows = gw.getWindowsWithTitle(self.window_name)
            if not windows:
                print(f"Janela '{self.window_name}' não encontrada")
                return None
            
            window = windows[0]
            window.activate()
            return window
        except Exception as e:
            print(f"Erro ao obter janela do emulador: {e}")
            return None

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

    def encontrar_template_na_tela(self, screenshot, template_config):
        """
        Procura um template específico na tela e retorna se encontrou e a posição central
        """
        try:
            if template_config.region:
                x, y, w, h = template_config.region
                roi = screenshot[y:y+h, x:x+w]
            else:
                roi = screenshot
                x, y = 0, 0

            # Template matching
            resultado = cv2.matchTemplate(roi, template_config.template, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(resultado)

            # Se encontrou com confiança maior que 0.8
            if max_val >= 0.8:
                template_h, template_w = template_config.template.shape[:2]
                
                if template_config.region:
                    centro_x = max_loc[0] + x + template_w // 2
                    centro_y = max_loc[1] + y + template_h // 2
                else:
                    centro_x = max_loc[0] + template_w // 2
                    centro_y = max_loc[1] + template_h // 2

                return True, (centro_x, centro_y)

            return False, None

        except Exception as e:
            print(f"Erro ao procurar template: {e}")
            return False, None

    def clicar_elemento(self, centro):
        """Clica em uma posição específica da tela"""
        if centro:
            window = self.get_emulator_window()
            if window:
                x, y = centro
                pyautogui.click(
                    window.left + x,
                    window.top + self.top_offset + y
                )
                return True
        return False

    def check_box(self, box_name, screenshot):
        """Verifica o estado de uma caixa específica"""
        configs = self.box_templates[box_name]
        
        # Verifica se está vendida
        encontrou, centro = self.encontrar_template_na_tela(screenshot, configs[BoxState.SOLD])
        if encontrou:
            self.clicar_elemento(centro)
            time.sleep(self.config["delays"]["after_collect"])
            return BoxState.SOLD
            
        # Verifica se tem item
        encontrou, _ = self.encontrar_template_na_tela(screenshot, configs[BoxState.WITH_ITEM])
        if encontrou:
            return BoxState.WITH_ITEM
            
        # Verifica se está vazia
        encontrou, _ = self.encontrar_template_na_tela(screenshot, configs[BoxState.EMPTY])
        if encontrou:
            return BoxState.EMPTY
            
        return None

    def check_shop(self):
        """Verifica todas as caixas da loja"""
        try:
            # Verifica se está na loja
            if state_manager.get_current_state() != "Dentro da Loja":
                raise Exception("Bot não está dentro da loja!")

            # Captura a tela inicial
            screenshot = self.capture_screen()
            if screenshot is None:
                raise Exception("Não foi possível capturar a tela")

            # Verifica cada caixa
            boxes_status = {}
            boxes_with_items = []
            boxes_empty = []
            boxes_sold = []

            for box_name in self.box_templates.keys():
                status = self.check_box(box_name, screenshot)
                boxes_status[box_name] = status
                
                if status == BoxState.WITH_ITEM:
                    boxes_with_items.append(box_name)
                elif status == BoxState.EMPTY:
                    boxes_empty.append(box_name)
                elif status == BoxState.SOLD:
                    boxes_sold.append(box_name)

            # Prepara o relatório
            report = []
            if boxes_sold:
                report.append(f"Coletado dinheiro de {len(boxes_sold)} caixas")
            if boxes_with_items:
                report.append(f"Caixas com itens: {', '.join(boxes_with_items)}")
            if boxes_empty:
                report.append(f"Caixas vazias: {', '.join(boxes_empty)}")

            return " | ".join(report) if report else "Nenhuma ação necessária"

        except Exception as e:
            print(f"Erro ao verificar loja: {e}")
            return f"Erro: {str(e)}"