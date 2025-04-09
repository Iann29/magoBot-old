import cv2
import numpy as np
import pygetwindow as gw
import os
import pyautogui
import time
import json
import logging
from datetime import datetime
from stateManager import state_manager
from verifyNumber import NumberVerifier

# Configuração de debug
DEBUG_MODE = True

# Configurar logging
log_filename = f'kit_terra_debug_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
logging.basicConfig(filename=log_filename, level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(message)s')

def debug_log(message):
    """Função para log de depuração que é fácil de remover depois"""
    if DEBUG_MODE:
        print(f"DEBUG: {message}")
        logging.debug(message)

class TemplateConfig:
    def __init__(self, filename, region=None, directory=None):
        self.filename = filename
        self.region = tuple(region) if region else None
        self.template = None
        self.directory = directory

class KitTerraBot:
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
        
        # Inicializar verificador de números
        self.number_verifier = NumberVerifier()

    def _load_config(self):
        """Carrega as configurações do arquivo JSON"""
        config_path = os.path.join(
            os.path.dirname(__file__),
            'cfg',
            'kitTerraCFG.json'
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

    def get_emulator_window(self):
        """Obtém e ativa a janela do emulador"""
        try:
            debug_log(f"Buscando janela com título: {self.window_name}")
            windows = gw.getWindowsWithTitle(self.window_name)
            if not windows:
                debug_log(f"Janela '{self.window_name}' não encontrada")
                print(f"Janela '{self.window_name}' não encontrada")
                return None
            
            window = windows[0]
            debug_log(f"Janela encontrada: {window.title} | Posição: {window.left},{window.top} | Tamanho: {window.width}x{window.height}")
            window.activate()
            return window
        except Exception as e:
            debug_log(f"Erro ao obter janela do emulador: {e}")
            print(f"Erro ao obter janela do emulador: {e}")
            return None

    def capture_screen(self):
        """Captura a tela do emulador"""
        window = self.get_emulator_window()
        if not window:
            debug_log("Não foi possível obter a janela do emulador para captura")
            return None

        try:
            capture_region = (
                window.left,
                window.top + self.top_offset,
                self.emulator_width,
                self.emulator_height
            )
            debug_log(f"Capturando tela com região: {capture_region} | top_offset: {self.top_offset}")
            screenshot = pyautogui.screenshot(region=capture_region)
            return cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
        except Exception as e:
            debug_log(f"Erro ao capturar tela: {e}")
            print(f"Erro ao capturar tela: {e}")
            return None

    def encontrar_template_na_tela(self, screenshot, box_config=None, template_name=None):
        """
        Procura um template específico na tela e retorna se encontrou e a posição central
        Pode receber tanto uma box_config quanto um template_name
        """
        if box_config:
            config = box_config
            debug_name = "box config"
        elif template_name:
            config = self.template_configs[template_name]
            debug_name = template_name
        else:
            debug_log("Chamada de encontrar_template_na_tela sem configuração")
            return False, None
        
        try:
            if config.region:
                x, y, w, h = config.region
                debug_log(f"Procurando template '{debug_name}' na região: {x},{y},{w},{h}")
                roi = screenshot[y:y+h, x:x+w]
            else:
                roi = screenshot
                x, y = 0, 0
                debug_log(f"Procurando template '{debug_name}' em toda a tela")

            # Template matching
            resultado = cv2.matchTemplate(roi, config.template, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(resultado)
            debug_log(f"Resultado do template matching para '{debug_name}': confiança={max_val:.4f}, posição={max_loc}")

            # Se encontrou com confiança maior que 0.8
            if max_val >= 0.8:
                template_h, template_w = config.template.shape[:2]
                
                if config.region:
                    centro_x = max_loc[0] + x + template_w // 2
                    centro_y = max_loc[1] + y + template_h // 2
                else:
                    centro_x = max_loc[0] + template_w // 2
                    centro_y = max_loc[1] + template_h // 2

                debug_log(f"Template '{debug_name}' encontrado! Centro em: {centro_x},{centro_y}")
                return True, (centro_x, centro_y)

            debug_log(f"Template '{debug_name}' NÃO encontrado. Confiança muito baixa: {max_val:.4f}")
            return False, None

        except Exception as e:
            debug_log(f"Erro ao procurar template '{debug_name}': {e}")
            print(f"Erro ao procurar template: {e}")
            return False, None

    def clicar_elemento(self, centro):
        """Clica em uma posição específica da tela"""
        if centro:
            window = self.get_emulator_window()
            if window:
                x, y = centro
                click_x = window.left + x
                click_y = window.top + self.top_offset + y
                debug_log(f"Tentando clicar em: ({click_x}, {click_y})")
                debug_log(f"  Detalhes: janela em ({window.left}, {window.top}), offset={self.top_offset}, posição relativa=({x}, {y})")
                
                # Salvar posição atual do mouse para debug
                mouse_antes = pyautogui.position()
                debug_log(f"  Posição do mouse antes: {mouse_antes}")
                
                # Clique
                pyautogui.click(click_x, click_y)
                
                # Verificar posição após o clique
                mouse_depois = pyautogui.position()
                debug_log(f"  Posição do mouse depois: {mouse_depois}")
                
                return True
            else:
                debug_log("Falha ao clicar: Janela não encontrada")
        else:
            debug_log("Falha ao clicar: Centro não especificado")
        return False

    def clicar_posicao(self, posicao):
        """Clica em uma posição absoluta da tela"""
        window = self.get_emulator_window()
        if window:
            x, y = posicao
            click_x = window.left + x
            click_y = window.top + self.top_offset + y
            debug_log(f"Clicando na posição absoluta: ({click_x}, {click_y})")
            debug_log(f"  Detalhes: janela em ({window.left}, {window.top}), offset={self.top_offset}, posição=({x}, {y})")
            
            # Clique
            pyautogui.click(click_x, click_y)
            return True
        else:
            debug_log("Falha ao clicar em posição: Janela não encontrada")
        return False

    def _verify_and_adjust_quantity(self, target_quantity):
        """Verifica e ajusta a quantidade de um item"""
        current_quantity = self.number_verifier.verify_number()
        if current_quantity is None:
            print("Não foi possível verificar a quantidade")
            return False
            
        current_quantity = int(current_quantity)
        print(f"Quantidade atual: {current_quantity}, Alvo: {target_quantity}")
        
        # Se quantidade é 9, precisa diminuir uma vez
        if target_quantity == 9:
            screenshot = self.capture_screen()
            encontrou, centro = self.encontrar_template_na_tela(
                screenshot, 
                template_name="quantidade_menos"
            )
            if encontrou:
                self.clicar_elemento(centro)
                time.sleep(self.config["delays"]["after_click_quantidade"])
        
        # Procura e clica no botão de diminuir quantidade máxima
        screenshot = self.capture_screen()
        encontrou, centro = self.encontrar_template_na_tela(
            screenshot, 
            template_name="quantidade_super_menos"
        )
        if encontrou:
            self.clicar_elemento(centro)
            time.sleep(self.config["delays"]["after_click_quantidade"])
            
        return True

    def vender_item(self, box_name, item_name, quantidade):
        """Executa a sequência de ações para vender um item específico"""
        try:
            debug_log(f"\n----- Iniciando venda de {item_name} na {box_name} (qtd={quantidade}) -----")
            # Verifica se está na loja
            current_state = state_manager.get_current_state()
            debug_log(f"Estado atual: {current_state}")
            if current_state != "Dentro da Loja":
                debug_log(f"ERRO: Estado atual é {current_state}, não 'Dentro da Loja'")
                raise Exception("Conta sem itens!")

            # Captura a tela inicial
            debug_log("Capturando tela inicial...")
            screenshot = self.capture_screen()
            if screenshot is None:
                debug_log("Falha ao capturar tela inicial")
                raise Exception("Não foi possível capturar a tela")

            # 1. Primeiro verifica se a caixa está vendida
            debug_log(f"Verificando se a caixa {box_name} está vendida")
            encontrou, centro = self.encontrar_template_na_tela(
                screenshot, 
                box_config=self.box_templates[box_name]["sold"]
            )
            if encontrou:
                debug_log(f"Caixa {box_name} está vendida, clicando para coletar: {centro}")
                # Se encontrou caixa vendida, clica nela para coletar
                click_result = self.clicar_elemento(centro)
                debug_log(f"Resultado do clique: {'Sucesso' if click_result else 'Falha'}")
                debug_log(f"Aguardando {self.config['delays']['after_collect']} segundos após coletar")
                time.sleep(self.config["delays"]["after_collect"])
                
                # Após coletar, captura nova screenshot e continua o processo
                debug_log("Capturando tela após coletar...")
                screenshot = self.capture_screen()
                if screenshot is None:
                    debug_log("Falha ao capturar tela após coletar")
                    raise Exception("Não foi possível capturar a tela após coletar")
            else:
                debug_log(f"Caixa {box_name} não está vendida")

            # 2. Verifica se a caixa está vazia
            debug_log(f"Verificando se a caixa {box_name} está vazia")
            encontrou, centro = self.encontrar_template_na_tela(
                screenshot, 
                box_config=self.box_templates[box_name]["empty"]
            )
            if encontrou:
                debug_log(f"Caixa {box_name} está vazia, clicando nela: {centro}")
                # Caixa está vazia, pode prosseguir
                click_result = self.clicar_elemento(centro)
                debug_log(f"Resultado do clique na caixa: {'Sucesso' if click_result else 'Falha'}")
                debug_log(f"Aguardando {self.config['delays']['after_click_box']} segundos após clicar na caixa")
                time.sleep(self.config["delays"]["after_click_box"])
                
                # Clica no slot específico
                slot_position = self.config["click_positions"]["slot_click"]
                debug_log(f"Clicando no slot específico: {slot_position}")
                click_result = self.clicar_posicao(slot_position)
                debug_log(f"Resultado do clique no slot: {'Sucesso' if click_result else 'Falha'}")
                debug_log(f"Aguardando {self.config['delays']['after_click_slot']} segundos após clicar no slot")
                time.sleep(self.config["delays"]["after_click_slot"])
                
                # Procura pelo item específico
                debug_log(f"Capturando tela para procurar pelo item {item_name}...")
                screenshot = self.capture_screen()
                if screenshot is None:
                    debug_log("Falha ao capturar tela para buscar item")
                    return f"Erro: Não foi possível capturar a tela para buscar {item_name}"
                
                debug_log(f"Procurando template do item {item_name}")
                encontrou, centro_item = self.encontrar_template_na_tela(
                    screenshot, 
                    template_name=item_name
                )
                if not encontrou:
                    debug_log(f"Template do item {item_name} NÃO encontrado")
                    return f"{item_name} não encontrado!"
                
                # Clica no item encontrado
                debug_log(f"Item {item_name} encontrado, clicando na posição: {centro_item}")
                click_result = self.clicar_elemento(centro_item)
                debug_log(f"Resultado do clique no item: {'Sucesso' if click_result else 'Falha'}")
                debug_log(f"Aguardando {self.config['delays']['after_click_item']} segundos após clicar no item")
                time.sleep(self.config["delays"]["after_click_item"])
                
                # Verifica e ajusta quantidade
                debug_log(f"Ajustando quantidade para {quantidade}")
                if not self._verify_and_adjust_quantity(quantidade):
                    debug_log("Falha ao ajustar quantidade")
                    return "Erro ao ajustar quantidade"
                
                # Verifica se tem a quantidade correta de itens
                debug_log("Verificando número exibido na tela...")
                result = self.number_verifier.verify_number()
                debug_log(f"Número encontrado na verificação: {result} (Esperado: {quantidade})")
                print(f"Número encontrado na verificação: {result} (Esperado: {quantidade})")
                if result is None or str(result) != str(quantidade):
                    debug_log(f"Conta está sem {item_name} suficiente")
                    print(f"Conta está sem {item_name}")
                    return f"Conta está sem {item_name}"
                
                # Procura e clica no botão de vender (PT/EN)
                debug_log("Capturando tela para procurar botão de vender...")
                screenshot = self.capture_screen()
                if screenshot is None:
                    debug_log("Falha ao capturar tela para botão de vender")
                    return "Erro: Não foi possível capturar a tela para localizar botão de vender"
                
                # Procurando botão em português
                debug_log("Procurando botão de vender em português")
                encontrou_pt, centro_pt = self.encontrar_template_na_tela(
                    screenshot, 
                    template_name="vender_pt"
                )
                debug_log(f"Botão PT encontrado: {encontrou_pt}, posição: {centro_pt}")
                
                # Procurando botão em inglês
                debug_log("Procurando botão de vender em inglês")
                encontrou_en, centro_en = self.encontrar_template_na_tela(
                    screenshot, 
                    template_name="vender_en"
                )
                debug_log(f"Botão EN encontrado: {encontrou_en}, posição: {centro_en}")
                
                # Tenta clicar no botão encontrado
                if encontrou_pt:
                    debug_log(f"Clicando no botão de vender PT na posição: {centro_pt}")
                    click_result = self.clicar_elemento(centro_pt)
                    debug_log(f"Resultado do clique no botão PT: {'Sucesso' if click_result else 'Falha'}")
                    
                    if click_result:
                        debug_log(f"Processo de venda concluído: {box_name} ({item_name})")
                        return f"Processo de venda concluído - {box_name} ({item_name})"
                    else:
                        debug_log("Falha ao clicar no botão de vender PT")
                elif encontrou_en:
                    debug_log(f"Clicando no botão de vender EN na posição: {centro_en}")
                    click_result = self.clicar_elemento(centro_en)
                    debug_log(f"Resultado do clique no botão EN: {'Sucesso' if click_result else 'Falha'}")
                    
                    if click_result:
                        debug_log(f"Processo de venda concluído: {box_name} ({item_name})")
                        return f"Processo de venda concluído - {box_name} ({item_name})"
                    else:
                        debug_log("Falha ao clicar no botão de vender EN")
                else:
                    debug_log("Botão de vender não encontrado (PT ou EN)")
                    return "Botão de vender não encontrado"
                    
            # 3. Se não encontrou caixa vazia, verifica se tem item
            else:
                debug_log(f"Caixa {box_name} não está vazia, verificando se já possui itens")
                encontrou, _ = self.encontrar_template_na_tela(
                    screenshot, 
                    box_config=self.box_templates[box_name]["with_item"]
                )
                if encontrou:
                    debug_log(f"Caixa {box_name} já possui itens")
                    return "Caixa já possui itens!"
            
            debug_log(f"Não foi possível determinar o estado da caixa {box_name}")
            return "Não foi possível determinar o estado da caixa"

        except Exception as e:
            debug_log(f"ERRO ao vender {item_name} em {box_name}: {str(e)}")
            print(f"Erro ao vender {item_name} em {box_name}: {e}")
            return f"Erro: {str(e)}"

    def vender_escritura(self, box_name, quantidade=10):
        """Vende uma escritura na caixa especificada"""
        return self.vender_item(box_name, "escritura", quantidade)

    def vender_marreta(self, box_name, quantidade=10):
        """Vende uma marreta na caixa especificada"""
        return self.vender_item(box_name, "marreta", quantidade)

    def vender_estaca(self, box_name, quantidade=10):
        """Vende uma estaca na caixa especificada"""
        return self.vender_item(box_name, "estaca", quantidade)

    def vender_kit_terra(self):
        """Gerencia a venda do kit terra completo (estacas, escrituras e marretas)"""
        try:
            debug_log("========== INICIANDO VENDA KIT TERRA COMPLETO ==========")
            # Verifica se está na loja
            current_state = state_manager.get_current_state()
            debug_log(f"Estado atual: {current_state}")
            if current_state != "Dentro da Loja":
                debug_log(f"ERRO: Estado atual é {current_state}, não 'Dentro da Loja'")
                raise Exception("Bot não está dentro da loja!")
            
            # Define a sequência de vendas
            sequencia_vendas = [
                # Estacas (3 caixas)
                {"caixa": "box1", "item": "estaca", "quantidade": 9},  # Primeira caixa com 9
                {"caixa": "box2", "item": "estaca", "quantidade": 10},
                {"caixa": "box3", "item": "estaca", "quantidade": 10},
                
                # Escrituras (3 caixas)
                {"caixa": "box4", "item": "escritura", "quantidade": 10},
                {"caixa": "box5", "item": "escritura", "quantidade": 10},
                {"caixa": "box6", "item": "escritura", "quantidade": 10},
                
                # Marretas (3 caixas)
                {"caixa": "box7", "item": "marreta", "quantidade": 10},
                {"caixa": "box8", "item": "marreta", "quantidade": 10},
                {"caixa": "box9", "item": "marreta", "quantidade": 10}
            ]
            
            debug_log(f"Sequência planejada: {len(sequencia_vendas)} vendas a serem realizadas")
            resultados = []
            
            # Executa cada venda na sequência
            for i, venda in enumerate(sequencia_vendas):
                debug_log(f"\n==== Iniciando venda #{i+1}: {venda['item']} na {venda['caixa']} (qtd={venda['quantidade']}) ====\n")
                
                # Tenta capturar a tela para debug
                if DEBUG_MODE:
                    debug_screenshot = self.capture_screen()
                    if debug_screenshot is not None:
                        debug_filename = f"debug_antes_venda_{i+1}_{datetime.now().strftime('%H%M%S')}.png"
                        cv2.imwrite(debug_filename, debug_screenshot)
                        debug_log(f"Screenshot salvo em {debug_filename}")
                
                # Tenta vender o item
                resultado = self.vender_item(
                    box_name=venda["caixa"],
                    item_name=venda["item"],
                    quantidade=venda["quantidade"]
                )
                debug_log(f"Resultado da venda #{i+1}: {resultado}")
                resultados.append(resultado)
                
                # Se encontrou erro de itens ou algum erro crítico, interrompe
                if "Conta está sem" in resultado or "Erro:" in resultado:
                    debug_log(f"Interrompendo processo devido a erro: {resultado}")
                    break
                    
                # Pequeno delay entre as tentativas
                delay = self.config["delays"].get("between_boxes", 0.5)
                debug_log(f"Aguardando {delay} segundos antes da próxima venda")
                time.sleep(delay)
            
            # Análise dos resultados
            sucessos = sum(1 for r in resultados if "Processo de venda concluído" in r)
            ocupadas = sum(1 for r in resultados if "Caixa já possui itens" in r)
            sem_itens = any("Conta está sem" in r for r in resultados)
            
            debug_log(f"Resultado final:\n - Sucessos: {sucessos}\n - Caixas ocupadas: {ocupadas}\n - Sem itens: {sem_itens}")
            
            # Prepara o relatório
            if sem_itens:
                mensagem = f"Vendidos {sucessos} itens. Processo interrompido: Conta sem itens"
            elif sucessos > 0:
                mensagem = f"Vendidos {sucessos} itens com sucesso! ({ocupadas} caixas já ocupadas)"
            elif ocupadas == len(resultados):
                mensagem = "Todas as caixas já possuem itens!"
            else:
                erros = [r for r in resultados if "Erro:" in r]
                if erros:
                    mensagem = f"Erro durante o processo: {erros[0]}"
                else:
                    mensagem = "Não foi possível vender nenhum item"
                    
            debug_log(f"Retornando mensagem: {mensagem}")
            debug_log("========== FIM DA VENDA KIT TERRA COMPLETO ==========\n")
            return mensagem

        except Exception as e:
            debug_log(f"ERRO CRÍTICO na venda do kit terra: {e}")
            print(f"Erro ao gerenciar venda de kit terra: {e}")
            return f"Erro: {str(e)}"