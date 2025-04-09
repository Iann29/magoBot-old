import tkinter as tk
from tkinter import ttk
import json
import os
from PIL import Image, ImageTk
import pyautogui
import time
from verifyNumber import NumberVerifier
from stateManager import state_manager
import pygetwindow as gw
import cv2
import numpy as np
import sys

def get_resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class OnlyOneBox:
    def __init__(self, box_number):
        """Inicializa a janela de configuração de box"""
        self.box_number = box_number
        self.images = {}  # Cache para as imagens
        self.number_verifier = NumberVerifier()  # Instancia o verificador de números
        self.root = None  # Referência para a janela principal
        self.box_frames = {}  # Dicionário para guardar referência aos frames das boxes
        
        # Define o diretório base
        self.base_dir = get_resource_path("")
        
        # Carrega a configuração
        config_path = get_resource_path("cfg/onlyoneBoxCFG.json")
        with open(config_path, "r") as f:
            self.config = json.load(f)
            
    def _get_window_position(self):
        """Obtém a posição da janela do emulador"""
        windows = gw.getWindowsWithTitle(state_manager.window_name)
        if not windows:
            print("Janela do emulador não encontrada")
            return None, None
            
        window = windows[0]
        try:
            window.activate()
            return window.left, window.top + state_manager.top_offset
        except Exception as e:
            print(f"Erro ao obter posição da janela: {e}")
            return None, None
            
    def _click_at(self, x, y):
        """Clica em uma posição relativa à janela do emulador"""
        window_x, window_y = self._get_window_position()
        if window_x is not None and window_y is not None:
            pyautogui.click(window_x + x, window_y + y)
            time.sleep(0.01)  # Delay mínimo após clique
            
    def _find_and_click_template(self, template_path, region=None):
        """Encontra e clica em um template na tela"""
        window_x, window_y = self._get_window_position()
        if window_x is None or window_y is None:
            return False
            
        # Define a região de busca
        if region is None:
            region = (0, 0, 640, 480)  # Tamanho padrão da janela
            
        # Captura a tela na região especificada
        x, y, width, height = region
        screenshot = pyautogui.screenshot(region=(
            window_x + x,
            window_y + y,
            width,
            height
        ))
        screenshot = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
        
        # Carrega e procura o template
        template = cv2.imread(get_resource_path(template_path))
        if template is None:
            print(f"Erro ao carregar template: {template_path}")
            return False
            
        result = cv2.matchTemplate(screenshot, template, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
        
        # Se encontrou uma correspondência boa
        if max_val > 0.8:  # Ajuste este valor conforme necessário
            template_h, template_w = template.shape[:2]
            center_x = max_loc[0] + template_w // 2
            center_y = max_loc[1] + template_h // 2
            
            # Clica no centro do template encontrado
            self._click_at(x + center_x, y + center_y)
            return True
            
        print(f"Template não encontrado: {template_path}")
        return False
        
    def _load_item_image(self, image_path):
        """Carrega a imagem de um item"""
        if image_path not in self.images:
            try:
                # Ajusta o caminho para ser relativo ao diretório backend
                full_path = get_resource_path(os.path.join("dataset", "icons", os.path.basename(image_path)))
                print(f"Tentando carregar imagem de: {full_path}")
                
                image = Image.open(full_path)
                # Redimensiona para o tamanho do frame
                size = (self.config["item_frame"]["width"], self.config["item_frame"]["height"])
                image = image.resize(size, Image.Resampling.LANCZOS)
                self.images[image_path] = ImageTk.PhotoImage(image)
            except Exception as e:
                print(f"Erro ao carregar imagem {image_path}: {e}")
                # Cria uma imagem placeholder vermelha para erro
                placeholder = Image.new('RGB', (self.config["item_frame"]["width"], 
                                              self.config["item_frame"]["height"]), 
                                      color='red')
                self.images[image_path] = ImageTk.PhotoImage(placeholder)
        return self.images[image_path]

    def _create_item_button(self, parent, item):
        """Cria um botão para um item com imagem e nome"""
        frame = ttk.Frame(parent, style='Dark.TFrame')
        
        # Guarda referência do frame no dicionário
        self.box_frames[self.box_number] = frame
        
        # Carrega a imagem do item
        image = self._load_item_image(item["image"])
        
        # Cria o botão com imagem
        button = ttk.Button(
            frame,
            image=image,
            command=lambda: self._show_item_config(item),
            style='Item.TButton',
            width=self.config["item_frame"]["width"]
        )
        button.pack(expand=False, pady=2)
        
        # Adiciona o texto abaixo do botão
        label = ttk.Label(
            frame, 
            text=item["name"],
            wraplength=self.config["item_frame"]["width"] + 20,
            anchor="center",
            font=("TkDefaultFont", 9),
            justify="center",
            style='Dark.TLabel'
        )
        label.pack(pady=2)
        
        return frame

    def _show_item_config(self, item):
        """Mostra a janela de configuração do item"""
        config_window = tk.Toplevel()
        config_window.title(f"Configurar {item['name']}")
        config_window.geometry("300x400")
        config_window.resizable(False, False)
        
        # Configura o estilo
        style = ttk.Style()
        style.configure("Config.TLabel", font=("Arial", 12))
        style.configure("Config.TButton", font=("Arial", 11), padding=5)
        style.configure("Config.TCombobox", font=("Arial", 11), padding=5)
        
        # Frame principal com padding
        main_frame = ttk.Frame(config_window, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Título do item
        title_label = ttk.Label(main_frame, text=item['name'], font=("Arial", 14, "bold"))
        title_label.pack(pady=(0, 20))
        
        # Frame para quantidade
        quantity_frame = ttk.LabelFrame(main_frame, text="Quantidade", padding=10)
        quantity_frame.pack(fill=tk.X, pady=(0, 20))
        
        quantity_var = tk.StringVar(value="1")
        quantity_combo = ttk.Combobox(quantity_frame, 
                                    textvariable=quantity_var,
                                    values=[str(i) for i in range(1, 11)],
                                    state="readonly",
                                    font=("Arial", 12),
                                    width=10)
        quantity_combo.pack(pady=10)
        
        # Frame para valor
        value_frame = ttk.LabelFrame(main_frame, text="Valor", padding=10)
        value_frame.pack(fill=tk.X, pady=(0, 20))
        
        value_var = tk.StringVar(value="MIN")
        
        # Frame para os botões de valor
        button_frame = ttk.Frame(value_frame)
        button_frame.pack(pady=10)
        
        min_button = ttk.Button(button_frame, 
                              text="MIN", 
                              style="Config.TButton",
                              width=10,
                              command=lambda: value_var.set("MIN"))
        min_button.pack(side=tk.LEFT, padx=5)
        
        max_button = ttk.Button(button_frame, 
                              text="MAX",
                              style="Config.TButton",
                              width=10,
                              command=lambda: value_var.set("MAX"))
        max_button.pack(side=tk.LEFT, padx=5)
        
        # Frame para botões de ação
        action_frame = ttk.Frame(main_frame)
        action_frame.pack(fill=tk.X, pady=(20, 0))
        
        cancel_button = ttk.Button(action_frame,
                                 text="Cancelar",
                                 style="Config.TButton",
                                 command=config_window.destroy)
        cancel_button.pack(side=tk.LEFT, expand=True, padx=5)
        
        confirm_button = ttk.Button(action_frame,
                                  text="Confirmar",
                                  style="Config.TButton",
                                  command=lambda: self._on_confirm(config_window, item, quantity_var, value_var))
        confirm_button.pack(side=tk.LEFT, expand=True, padx=5)
        
        # Centraliza a janela
        config_window.transient(self.root)
        config_window.grab_set()
        
        # Atualiza o estilo dos botões quando o valor muda
        def update_button_style(*args):
            current_value = value_var.get()
            min_button.state(['!pressed', '!active'])
            max_button.state(['!pressed', '!active'])
            if current_value == "MIN":
                min_button.state(['pressed'])
            else:
                max_button.state(['pressed'])
                
        value_var.trace_add("write", update_button_style)
        update_button_style()
        
    def _on_confirm(self, window, item, quantity_var, value_var):
        """Callback quando o usuário confirma a configuração"""
        window.destroy()
        self._process_sale(item, int(quantity_var.get()), value_var.get())
        
    def _process_sale(self, item, quantity, value_type):
        """Processa a venda do item"""
        print(f"Processando venda: {item['name']} x{quantity} ({value_type})")
        
        # 1. Clica na box usando a posição do seeLojaCFG.json
        config_path = get_resource_path("cfg/seeLojaCFG.json")
        with open(config_path, "r") as f:
            cfg = json.load(f)
            box_pos = cfg["click_positions"][f"box{self.box_number}"]
            self._click_at(box_pos[0], box_pos[1])
            
        # Aguarda a interface responder
        time.sleep(0.2)  # Reduzido para 0.1s
            
        # 2. Clica no menu de itens
        self._click_at(141, 231)
        time.sleep(0.1)  # Reduzido para 0.1s
        
        # 3. Procura e clica no template do item
        template_name = item['image'].replace('icon', '').lower()
        template_path = get_resource_path(os.path.join("dataset", "itens", template_name))
        
        # Região exata onde os itens aparecem no menu
        search_region = (171, 146, 174, 218)  # x, y, width, height
        print(f"Procurando template em: x={search_region[0]}, y={search_region[1]}, w={search_region[2]}, h={search_region[3]}")
        
        if not self._find_and_click_template(template_path, region=search_region):
            print("Não foi possível encontrar o item na tela")
            return
            
        time.sleep(0.1)  # Reduzido para 0.1s
        
        # 4. Ajusta a quantidade
        current_quantity = self.number_verifier.verify_number()
        
        if current_quantity is not None:
            current_quantity = int(current_quantity)
            clicks_needed = current_quantity - quantity
            button_pos = (379, 174) if clicks_needed > 0 else (468, 173)
            
            for _ in range(abs(clicks_needed)):
                self._click_at(button_pos[0], button_pos[1])
                time.sleep(0.01)  # Reduzido para 0.01s
        
        # 5. Ajusta o valor
        if value_type == "MIN":
            self._click_at(400, 241)
        else:
            self._click_at(443, 242)
            
        time.sleep(0.05)  # Reduzido para 0.05s
            
        # 6. Clica em vender
        self._click_at(419, 355)
        
        # 7. Marca a box como configurada
        self.mark_box_as_occupied()
        
    def mark_box_as_occupied(self):
        """Marca a box como ocupada na interface"""
        if self.root and hasattr(self, 'box_frames') and self.box_number in self.box_frames:
            frame = self.box_frames[self.box_number]
            frame.configure(style='Occupied.TFrame')
            
    def _filter_items(self, category=None):
        """Filtra os itens pela categoria selecionada"""
        # Limpa o frame de itens atual
        for widget in self.items_frame.winfo_children():
            widget.destroy()
            
        # Filtra os itens pela categoria
        filtered_items = [
            item for item in self.config["items"]
            if category is None or category == "" or item["category"] == category
        ]
        
        # Recria o grid com os itens filtrados
        cols = self.config["item_frame"]["columns"]
        for i, item in enumerate(filtered_items):
            row = i // cols
            col = i % cols
            frame = self._create_item_button(self.items_frame, item)
            frame.grid(row=row, column=col, padx=1, pady=1)

    def _on_category_selected(self, event):
        """Callback quando uma categoria é selecionada"""
        category = self.category_combo.get()
        self._filter_items(None if category == "Todas" else category)

    def show(self):
        """Mostra a janela de seleção de item"""
        # Cria a janela
        self.window = tk.Toplevel()
        self.window.title(f"{self.config['window']['title']} {self.box_number}")
        self.window.geometry(f"{self.config['window']['width']}x{self.config['window']['height']}")
        self.window.resizable(False, False)  # Desabilita redimensionamento
        self.window.configure(bg='#2b2b2b')  # Fundo escuro
        
        # Cria estilo customizado para os botões e combobox
        style = ttk.Style()
        style.configure('Item.TButton', 
                       padding=2,
                       width=self.config["item_frame"]["width"])
                       
        # Estilo para o frame
        style.configure('Dark.TFrame', background='#2b2b2b')
        
        # Estilo para labels
        style.configure('Dark.TLabel',
                       background='#2b2b2b',
                       foreground='white')
        
        # Estilo para o combobox
        style.configure('Dark.TCombobox',
                       fieldbackground='#3c3c3c',
                       background='#3c3c3c',
                       foreground='white',
                       arrowcolor='white',
                       selectbackground='#4a4a4a',
                       selectforeground='white')
        
        # Estilo para frames de box ocupada
        style.configure('Occupied.TFrame', background='#ff6b6b')
        
        # Frame principal
        main_frame = ttk.Frame(self.window, style='Dark.TFrame')
        main_frame.pack(expand=True, fill="both", padx=10, pady=10)
        
        # Combobox para filtrar por categoria
        category_frame = ttk.Frame(main_frame, style='Dark.TFrame')
        category_frame.pack(fill="x", padx=3, pady=(0, 10))
        
        ttk.Label(category_frame, 
                 text="Categoria:", 
                 style='Dark.TLabel',
                 font=('TkDefaultFont', 9)).pack(side="left", padx=(0, 5))
                 
        self.category_combo = ttk.Combobox(
            category_frame,
            values=["Todas"] + self.config["categories"],
            state="readonly",
            width=20,
            style='Dark.TCombobox',
            font=('TkDefaultFont', 9)
        )
        self.category_combo.set("Todas")
        self.category_combo.pack(side="left")
        
        # Frame para os itens em grid
        self.items_frame = ttk.Frame(main_frame, style='Dark.TFrame')
        self.items_frame.pack(expand=True, fill="both", padx=3)
        
        # Mostra todos os itens inicialmente
        self._filter_items()
        
        # Bind para o evento de seleção
        self.category_combo.bind('<<ComboboxSelected>>', self._on_category_selected)
        
        # Força o foco na janela e atualiza
        self.window.focus_force()
        self.window.update()
