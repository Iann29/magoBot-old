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

class HayDayBot:
    def __init__(self):
        # Carregar configurações do arquivo JSON
        self.config = self._load_config()
        
        # Configurar janela
        self.window_name = self.config["window"]["name"]
        self.emulator_width = self.config["window"]["width"]
        self.emulator_height = self.config["window"]["height"]
        self.window_height = self.config["window"]["window_height"]
        self.top_offset = self.window_height - self.emulator_height
        
        # Configurar templates
        self.template_configs = {}
        for name, template_data in self.config["templates"].items():
            self.template_configs[name] = TemplateConfig(
                filename=template_data["filename"],
                region=template_data["region"]
            )
        
        # Carregar templates
        self._load_templates()
        
    def _load_config(self):
        """Carrega as configurações do arquivo JSON"""
        config_path = os.path.join(
            os.path.dirname(__file__),
            'cfg',
            'adicionarClienteCFG.json'
        )
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            raise Exception(f"Erro ao carregar arquivo de configuração: {e}")
        
    def _load_templates(self):
        """Carrega todas as imagens de template necessárias"""
        template_dir = os.path.join(os.path.dirname(__file__), 'dataset', 'buttons')
        
        for config in self.template_configs.values():
            path = os.path.join(template_dir, config.filename)
            try:
                template = cv2.imread(path, cv2.IMREAD_COLOR)
                if template is None:
                    raise FileNotFoundError(f"Não foi possível carregar: {path}")
                config.template = template
            except Exception as e:
                print(f"Erro ao carregar template {config.filename}: {e}")

    def encontrar_template_na_tela(self, screenshot, template_name):
        """
        Procura um template específico na tela e retorna se encontrou e a posição central
        """
        config = self.template_configs[template_name]
        
        try:
            if config.region:
                x, y, w, h = config.region
                roi = screenshot[y:y+h, x:x+w]
            else:
                roi = screenshot
                x, y = 0, 0

            # Template matching
            resultado = cv2.matchTemplate(roi, config.template, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(resultado)

            # Se encontrou com confiança maior que 0.8
            if max_val >= 0.8:
                template_h, template_w = config.template.shape[:2]
                
                if config.region:
                    centro_x = max_loc[0] + x + template_w // 2
                    centro_y = max_loc[1] + y + template_h // 2
                else:
                    centro_x = max_loc[0] + template_w // 2
                    centro_y = max_loc[1] + template_h // 2

                return True, (centro_x, centro_y)

            return False, None

        except Exception as e:
            print(f"Erro ao procurar template {template_name}: {e}")
            return False, None

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

    def adicionar_cliente(self, tag_cliente):
        """
        Executa a sequência de ações para adicionar um cliente
        Retorna True se todas as ações foram bem sucedidas
        """
        try:
            # Verifica o estado atual
            current_state = state_manager.get_current_state()
            
            # Se estiver na loja, primeiro sair dela
            if current_state == "Dentro da Loja":
                screenshot = self.capture_screen()
                if screenshot is None:
                    raise Exception("Não foi possível capturar a tela")
                    
                # Procura e clica no botão de fechar loja
                encontrou, centro = self.encontrar_template_na_tela(screenshot, "close_shop")
                if not encontrou or not self.clicar_elemento(centro):
                    raise Exception("Botão de fechar loja não encontrado")
                time.sleep(self.config["delays"]["after_close_shop"])
            elif current_state != "Inicio":
                raise Exception("Bot deve estar na tela inicial ou dentro da loja!")

            # 1. Procurar e clicar no botão de amigos
            screenshot = self.capture_screen()
            if screenshot is None:
                raise Exception("Não foi possível capturar a tela")

            encontrou, centro = self.encontrar_template_na_tela(screenshot, "friend_button")
            if not encontrou or not self.clicar_elemento(centro):
                raise Exception("Botão de amigos não encontrado")
            time.sleep(self.config["delays"]["after_friend_button"])

            # 2. Procurar e clicar no botão do livro
            screenshot = self.capture_screen()
            encontrou, centro = self.encontrar_template_na_tela(screenshot, "book_button")
            if not encontrou or not self.clicar_elemento(centro):
                raise Exception("Botão do livro não encontrado")
            time.sleep(self.config["delays"]["after_book_button"])

            # 3. Procurar e clicar no campo de digitar tag
            screenshot = self.capture_screen()
            encontrou, centro = self.encontrar_template_na_tela(screenshot, "digitar_tag")
            if not encontrou or not self.clicar_elemento(centro):
                raise Exception("Campo de tag não encontrado")
            time.sleep(self.config["delays"]["after_tag_field"])

            # 4. Digitar a tag do cliente
            pyautogui.write(tag_cliente)
            time.sleep(self.config["delays"]["after_typing"])

            # 5. Procurar e clicar no botão procurar (PT/EN)
            screenshot = self.capture_screen()
            encontrou_pt, centro_pt = self.encontrar_template_na_tela(screenshot, "procurar_pt")
            encontrou_en, centro_en = self.encontrar_template_na_tela(screenshot, "procurar_en")
            
            if encontrou_pt and self.clicar_elemento(centro_pt):
                pass
            elif encontrou_en and self.clicar_elemento(centro_en):
                pass
            else:
                raise Exception("Botão procurar não encontrado")
            time.sleep(self.config["delays"]["after_search"])

            # 6. Procurar e clicar no botão adicionar cliente (PT/EN)
            screenshot = self.capture_screen()
            encontrou_pt, centro_pt = self.encontrar_template_na_tela(screenshot, "adicionar_cliente_pt")
            encontrou_en, centro_en = self.encontrar_template_na_tela(screenshot, "adicionar_cliente_en")
            
            if not (encontrou_pt and self.clicar_elemento(centro_pt)) and \
               not (encontrou_en and self.clicar_elemento(centro_en)):
                # Se não encontrou o botão de adicionar cliente, a tag está errada
                print("Tag do cliente está errada ou cliente não encontrado")
                # Ações de recuperação
                self._realizar_acoes_recuperacao()
                return False
                
            time.sleep(self.config["delays"]["after_add_client"])

            # 7. Clicar no botão de sair
            screenshot = self.capture_screen()
            encontrou, centro = self.encontrar_template_na_tela(screenshot, "exit_cliente")
            if not encontrou or not self.clicar_elemento(centro):
                raise Exception("Botão de sair não encontrado")
            time.sleep(self.config["delays"]["after_exit"])

            # 8. Clicar no botão de amigos (retorno)
            screenshot = self.capture_screen()
            encontrou, centro = self.encontrar_template_na_tela(screenshot, "friend_button_return")
            if not encontrou or not self.clicar_elemento(centro):
                raise Exception("Botão de amigos (retorno) não encontrado")

            print("Cliente adicionado com sucesso!")
            return True

        except Exception as e:
            print(f"Erro ao adicionar cliente: {e}")
            return False

    def _realizar_acoes_recuperacao(self):
        """Realiza as ações de recuperação quando o cliente não é encontrado"""
        try:
            # 1. Clicar no botão de sair
            screenshot = self.capture_screen()
            encontrou, centro = self.encontrar_template_na_tela(screenshot, "exit_cliente")
            if encontrou and self.clicar_elemento(centro):
                time.sleep(self.config["delays"]["after_exit"])
                
                # 2. Clicar no botão de amigos (retorno)
                screenshot = self.capture_screen()
                encontrou, centro = self.encontrar_template_na_tela(screenshot, "friend_button_return")
                if encontrou:
                    self.clicar_elemento(centro)
        except Exception as e:
            print(f"Erro nas ações de recuperação: {e}")