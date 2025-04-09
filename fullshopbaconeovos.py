import cv2
import numpy as np
import pygetwindow as gw
import os
import pyautogui
import time
import json
from stateManager import state_manager

class TemplateConfig:
    def __init__(self, filename, region=None, directory=None):
        self.filename = filename
        self.region = tuple(region) if region else None
        self.template = None
        self.directory = directory

class FullShopBaconEOvosBot:
    def __init__(self):
        # Carregar configurações do arquivo JSON
        self.config = self._load_config()
        
        # Configurar janela
        self.window_name = self.config["window"]["name"]
        self.emulator_width = self.config["window"]["width"]
        self.emulator_height = self.config["window"]["height"]
        self.window_height = self.config["window"]["window_height"]
        self.top_offset = self.window_height - self.emulator_height
        
        # Configurar templates normais
        self.template_configs = {}
        for name, template_data in self.config["templates"].items():
            self.template_configs[name] = TemplateConfig(
                filename=template_data["filename"],
                region=template_data["region"],
                directory=template_data.get("directory", "")
            )
        
        # Configurar box templates
        self.box_templates = {}
        for box_name, box_data in self.config["boxes"].items():
            self.box_templates[box_name] = {
                "empty": TemplateConfig(
                    filename=box_data["empty"]["filename"],
                    region=box_data["empty"]["region"],
                    directory="variable"
                ),
                "with_item": TemplateConfig(
                    filename=box_data["with_item"]["filename"],
                    region=box_data["with_item"]["region"],
                    directory="variable"
                ),
                "sold": TemplateConfig(
                    filename=box_data["sold"]["filename"],
                    region=box_data["sold"]["region"],
                    directory="variable"
                )
            }
        
        # Carregar templates
        self._load_templates()
        
    def _load_config(self):
        """Carrega as configurações do arquivo JSON"""
        config_path = os.path.join(
            os.path.dirname(__file__),
            'cfg',
            'FullshopBaconeOvosCFG.json'
        )
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            raise Exception(f"Erro ao carregar arquivo de configuração: {e}")
        
    def _load_templates(self):
        """Carrega todas as imagens de template necessárias"""
        base_dir = os.path.join(os.path.dirname(__file__), 'dataset')
        
        # Carrega templates normais
        for config in self.template_configs.values():
            path = os.path.join(base_dir, config.directory, config.filename)
            try:
                template = cv2.imread(path, cv2.IMREAD_COLOR)
                if template is None:
                    raise FileNotFoundError(f"Não foi possível carregar: {path}")
                config.template = template
            except Exception as e:
                print(f"Erro ao carregar template {config.filename}: {e}")
                
        # Carrega templates das boxes
        for box_configs in self.box_templates.values():
            for config in box_configs.values():
                path = os.path.join(base_dir, config.directory, config.filename)
                try:
                    template = cv2.imread(path, cv2.IMREAD_COLOR)
                    if template is None:
                        raise FileNotFoundError(f"Não foi possível carregar: {path}")
                    config.template = template
                except Exception as e:
                    print(f"Erro ao carregar template {config.filename}: {e}")

    def _find_template(self, template_config, threshold=0.8):
        """Procura um template na tela"""
        window = gw.getWindowsWithTitle(self.window_name)[0]
        x, y = window.left, window.top + self.top_offset
        
        if template_config.region:
            region = (
                x + template_config.region[0],
                y + template_config.region[1],
                template_config.region[2],
                template_config.region[3]
            )
            screenshot = pyautogui.screenshot(region=region)
        else:
            screenshot = pyautogui.screenshot(region=(
                x, y, self.emulator_width, self.emulator_height
            ))
            
        screenshot = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
        
        result = cv2.matchTemplate(
            screenshot,
            template_config.template,
            cv2.TM_CCOEFF_NORMED
        )
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
        
        if max_val >= threshold:
            if template_config.region:
                return (
                    max_loc[0] + template_config.region[0] + x,
                    max_loc[1] + template_config.region[1] + y
                )
            return max_loc[0] + x, max_loc[1] + y
        return None

    def _click_template(self, template_name, offset_x=0, offset_y=0, duration=0.5):
        """Clica em um template"""
        template_config = self.template_configs.get(template_name)
        if not template_config:
            print(f"Template {template_name} não encontrado")
            return False
            
        position = self._find_template(template_config)
        if position:
            x, y = position
            template_height = template_config.template.shape[0]
            template_width = template_config.template.shape[1]
            
            click_x = x + template_width // 2 + offset_x
            click_y = y + template_height // 2 + offset_y
            
            pyautogui.moveTo(click_x, click_y, duration=duration)
            pyautogui.click()
            return True
        return False

    def _check_box_state(self, box_name):
        """Verifica o estado de uma box (vazia, com item ou vendida)"""
        box_configs = self.box_templates.get(box_name)
        if not box_configs:
            print(f"Box {box_name} não encontrada")
            return None
            
        for state, config in box_configs.items():
            if self._find_template(config, threshold=0.9):
                return state
        return None

    def vender_bacon_e_ovos(self):
        """Gerencia a venda do bacon e ovos"""
        try:
            # Verifica se está na loja
            if state_manager.get_current_state() != "Dentro da Loja":
                raise Exception("Bot não está dentro da loja!")
            
            # Define a sequência de vendas (10 caixas com bacon e ovos)
            sequencia_vendas = [
                {"caixa": f"box{i}", "item": "baconeovos", "quantidade": 10} for i in range(1, 11)
            ]
            
            resultados = []
            
            # Executa cada venda na sequência
            for venda in sequencia_vendas:
                resultado = self.vender_item(
                    box_name=venda["caixa"],
                    item_name=venda["item"],
                    quantidade=venda["quantidade"]
                )
                resultados.append(resultado)
                
                # Se encontrou erro de itens ou algum erro crítico, interrompe
                if "Conta está sem itens" in resultado or "Erro:" in resultado:
                    break
                    
                # Pequeno delay entre as tentativas
                time.sleep(self.config["delays"].get("between_boxes", 0.5))
            
            # Análise dos resultados
            sucessos = sum(1 for r in resultados if "Processo de venda concluído" in r)
            ocupadas = sum(1 for r in resultados if "Caixa já possui itens" in r)
            sem_itens = any("Conta está sem itens" in r for r in resultados)
            
            # Prepara o relatório
            if sem_itens:
                return f"Vendidos {sucessos} itens. Processo interrompido: Conta sem itens"
            elif sucessos > 0:
                return f"Vendidos {sucessos} itens com sucesso! ({ocupadas} caixas já ocupadas)"
            elif ocupadas == len(resultados):
                return "Todas as caixas já possuem itens!"
            else:
                erros = [r for r in resultados if "Erro:" in r]
                if erros:
                    return f"Erro durante o processo: {erros[0]}"
                return "Não foi possível vender nenhum item"

        except Exception as e:
            print(f"Erro ao gerenciar venda de bacon e ovos: {e}")
            return f"Erro: {str(e)}"

    def vender_item(self, box_name, item_name, quantidade):
        """Executa a sequência de ações para vender um item específico"""
        try:
            # Verifica se está na loja
            if state_manager.get_current_state() != "Dentro da Loja":
                raise Exception("Conta sem itens!")

            # Captura a tela inicial
            screenshot = self.capture_screen()
            if screenshot is None:
                raise Exception("Não foi possível capturar a tela")

            # 1. Primeiro verifica se a caixa está vendida
            encontrou, centro = self.encontrar_template_na_tela(
                screenshot, 
                box_config=self.box_templates[box_name]["sold"]
            )
            if encontrou:
                # Se encontrou caixa vendida, clica nela para coletar
                self.clicar_elemento(centro)
                time.sleep(self.config["delays"]["after_collect"])
                
                # Após coletar, captura nova screenshot e continua o processo
                screenshot = self.capture_screen()
                if screenshot is None:
                    raise Exception("Não foi possível capturar a tela após coletar")

            # 2. Verifica se a caixa está vazia
            encontrou, centro = self.encontrar_template_na_tela(
                screenshot, 
                box_config=self.box_templates[box_name]["empty"]
            )
            if encontrou:
                # Caixa está vazia, pode prosseguir
                self.clicar_elemento(centro)
                time.sleep(self.config["delays"]["after_click_box"])
                
                # Clica no slot específico
                self.clicar_posicao(self.config["click_positions"]["slot_click"])
                time.sleep(self.config["delays"]["after_click_slot"])
                
                # Procura pelo item específico
                screenshot = self.capture_screen()
                encontrou, centro_item = self.encontrar_template_na_tela(
                    screenshot, 
                    template_name=item_name
                )
                if not encontrou:
                    return f"{item_name} não encontrado!"
                
                # Clica no item encontrado
                self.clicar_elemento(centro_item)
                time.sleep(self.config["delays"]["after_click_item"])
                
                # Procura e clica no botão de aumentar quantidade máxima
                screenshot = self.capture_screen()
                encontrou, centro = self.encontrar_template_na_tela(
                    screenshot, 
                    template_name="quantidade_super_mais"
                )
                if encontrou:
                    self.clicar_elemento(centro)
                    time.sleep(self.config["delays"]["after_click_quantidade"])
                
                # Verifica se tem a quantidade correta de itens
                screenshot = self.capture_screen()
                template_verificacao = f"verificar_{quantidade}"
                encontrou, _ = self.encontrar_template_na_tela(
                    screenshot, 
                    template_name=template_verificacao
                )
                if not encontrou:
                    print(f"Quantidade incorreta para {item_name}, tentando diminuir...")
                    # Tenta diminuir a quantidade
                    screenshot = self.capture_screen()
                    encontrou, centro = self.encontrar_template_na_tela(
                        screenshot, 
                        template_name="quantiaMenos"
                    )
                    if encontrou:
                        self.clicar_elemento(centro)
                        time.sleep(self.config["delays"]["after_click_quantidade"])
                        
                        # Verifica novamente a quantidade
                        screenshot = self.capture_screen()
                        encontrou, _ = self.encontrar_template_na_tela(
                            screenshot, 
                            template_name=template_verificacao
                        )
                        if not encontrou:
                            print(f"Conta está sem {item_name} suficiente mesmo após diminuir")
                            return f"Conta está sem {item_name}"
                    else:
                        print(f"Conta está sem {item_name}")
                        return f"Conta está sem {item_name}"
                
                # Procura e clica no botão de vender (PT/EN)
                screenshot = self.capture_screen()
                encontrou_pt, centro_pt = self.encontrar_template_na_tela(
                    screenshot, 
                    template_name="vender_pt"
                )
                encontrou_en, centro_en = self.encontrar_template_na_tela(
                    screenshot, 
                    template_name="vender_en"
                )
                
                if encontrou_pt and self.clicar_elemento(centro_pt):
                    return f"Processo de venda concluído - {box_name} ({item_name})"
                elif encontrou_en and self.clicar_elemento(centro_en):
                    return f"Processo de venda concluído - {box_name} ({item_name})"
                else:
                    return "Botão de vender não encontrado"
                    
            # 3. Se não encontrou caixa vazia, verifica se tem item
            encontrou, _ = self.encontrar_template_na_tela(
                screenshot, 
                box_config=self.box_templates[box_name]["with_item"]
            )
            if encontrou:
                return "Caixa já possui itens!"
            
            return "Não foi possível determinar o estado da caixa"

        except Exception as e:
            print(f"Erro ao vender {item_name} em {box_name}: {e}")
            return f"Erro: {str(e)}"

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

    def encontrar_template_na_tela(self, screenshot, box_config=None, template_name=None):
        """
        Procura um template específico na tela e retorna se encontrou e a posição central
        Pode receber tanto uma box_config quanto um template_name
        """
        if box_config:
            config = box_config
        elif template_name:
            config = self.template_configs[template_name]
        else:
            return False, None
        
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

    def clicar_posicao(self, posicao):
        """Clica em uma posição absoluta da tela"""
        window = self.get_emulator_window()
        if window:
            x, y = posicao
            pyautogui.click(
                window.left + x,
                window.top + self.top_offset + y
            )
            return True
        return False
