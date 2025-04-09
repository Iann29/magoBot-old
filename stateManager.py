import cv2
import numpy as np
import pygetwindow as gw
import os
import pyautogui
import time
import threading
from typing import Optional, Dict

class StateManager:
    def __init__(self):
        self.window_name = "FARMs"
        self.emulator_width = 640
        self.emulator_height = 480
        self.window_height = 514
        self.top_offset = self.window_height - self.emulator_height
        
        self.current_state = "Desconhecido"
        self.is_running = False
        self.monitor_thread = None
        
        # Template para verificação de estado
        self.state_templates = {
            "Inicio": {
                "filename": "estado_inicio.png",
                "region": (1, 406, 73, 74),
                "template": None,
                "directory": "states"  # Diretório onde está o template
            },
            "Dentro da Loja": {
                "filename": "dentro_da_loja.png",
                "region": (78, 81, 131, 98),
                "template": None,
                "directory": "states"  # Diretório onde está o template
            },
            "Escolhendo Item": {
                "filename": "escolhendo_item.png",
                "region": (117, 207, 45, 51),
                "template": None,
                "directory": "states"  # Diretório onde está o template
            },
            "Adicionando Cliente": {
                "filename": "adicionando_cliente.png",
                "region": (67, 45, 129, 126),
                "template": None,
                "directory": "states"  # Diretório onde está o template
            },
            "Dentro do Jornal": {
                "filename": "dentro_do_jornal2.png",
                "region": (141, 111, 60, 70),
                "template": None,
                "directory": "states"  # Diretório onde está o template
            },
            "Dentro do Jornal": {
                "filename": "dentro_do_jornal.png",
                "region": (518, 117, 50, 51),
                "template": None,
                "directory": "states"  # Diretório onde está o template
            },
            "Fazenda do Cliente": {
                "filename": "fazenda_cliente.png",
                "region": (1, 408, 59, 72),
                "template": None,
                "directory": "states"  # Diretório onde está o template
            },
            "Barra de Amigos": {
                "filename": "book.png",
                "region": (198, 397, 96, 83),
                "template": None,
                "directory": "states"  # Diretório onde está o template
            }
        }
        
        self._load_templates()
    
    def _load_templates(self):
        """Carrega as imagens de template para verificação de estado"""
        base_dir = os.path.join(os.path.dirname(__file__), 'dataset')
        
        for state, config in self.state_templates.items():
            # Constrói o caminho completo usando o diretório específico
            path = os.path.join(base_dir, config["directory"], config["filename"])
            try:
                template = cv2.imread(path, cv2.IMREAD_COLOR)
                if template is None:
                    raise FileNotFoundError(f"Não foi possível carregar: {path}")
                print(f"Template {config['filename']} carregado com sucesso. Shape: {template.shape}")
                config["template"] = template
            except Exception as e:
                print(f"Erro ao carregar template {config['filename']}: {e}")

    def get_emulator_window(self):
        """Obtém e ativa a janela do emulador"""
        try:
            windows = gw.getWindowsWithTitle(self.window_name)
            if not windows:
                return None
            return windows[0]
        except Exception:
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
        except Exception:
            return None

    def check_state(self, screenshot) -> str:
        """
        Verifica o estado atual baseado nos templates com sistema de prioridade.
        Detecta todos os estados possíveis e escolhe o mais específico.
        """
        if screenshot is None:
            return "Desconhecido"
            
        # Dicionário para armazenar todos os estados detectados e suas confidências
        detected_states = {}
        
        for state, config in self.state_templates.items():
            try:
                if config["template"] is None:
                    continue
                    
                x, y, w, h = config["region"]
                
                # Verifica se a região está dentro dos limites da screenshot
                if y+h > screenshot.shape[0] or x+w > screenshot.shape[1]:
                    print(f"Região inválida para o estado {state}")
                    continue
                    
                roi = screenshot[y:y+h, x:x+w]
                
                # Verifica se as dimensões são compatíveis
                if roi.shape[0] < config["template"].shape[0] or roi.shape[1] < config["template"].shape[1]:
                    print(f"ROI menor que template para o estado {state}")
                    continue
                
                resultado = cv2.matchTemplate(roi, config["template"], cv2.TM_CCOEFF_NORMED)
                min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(resultado)
                
                # Se encontrou match com confiança maior que 0.8
                if max_val >= 0.8:
                    detected_states[state] = max_val
                    
            except Exception as e:
                print(f"Erro ao verificar estado {state}: {e}")
                print(f"ROI shape: {roi.shape if 'roi' in locals() else 'N/A'}")
                print(f"Template shape: {config['template'].shape if config['template'] is not None else 'N/A'}")
        
        # Se não detectou nenhum estado
        if not detected_states:
            return "Desconhecido"
            
        # Se detectou apenas o estado "Inicio"
        if len(detected_states) == 1 and "Inicio" in detected_states:
            return "Inicio"
            
        # Se detectou múltiplos estados, remove o "Inicio" e escolhe o com maior confiança
        if "Inicio" in detected_states and len(detected_states) > 1:
            del detected_states["Inicio"]
        
        # Retorna o estado com maior confiança
        return max(detected_states.items(), key=lambda x: x[1])[0]

    def monitor_state(self):
        """Monitora continuamente o estado do jogo"""
        while self.is_running:
            try:
                screenshot = self.capture_screen()
                novo_estado = self.check_state(screenshot)
                
                if novo_estado != self.current_state:
                    print(f"Estado mudou: {self.current_state} -> {novo_estado}")
                    self.current_state = novo_estado
                
                time.sleep(0.1)  # Pequeno delay para não sobrecarregar
                
            except Exception as e:
                print(f"Erro no monitoramento: {e}")
                time.sleep(1)

    def start(self):
        """Inicia o monitoramento de estado em uma thread separada"""
        if not self.is_running:
            self.is_running = True
            self.monitor_thread = threading.Thread(target=self.monitor_state)
            self.monitor_thread.daemon = True
            self.monitor_thread.start()
            print("Monitoramento de estado iniciado")

    def stop(self):
        """Para o monitoramento de estado"""
        self.is_running = False
        if self.monitor_thread:
            self.monitor_thread.join()
            self.monitor_thread = None
            print("Monitoramento de estado parado")

    def get_current_state(self) -> str:
        """Retorna o estado atual"""
        return self.current_state

# Singleton para ser usado por outras partes do código
state_manager = StateManager()

if __name__ == "__main__":
    # Teste do StateManager
    manager = StateManager()
    manager.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        manager.stop()
        print("Programa finalizado")