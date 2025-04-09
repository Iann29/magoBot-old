import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
import sys
import threading
import time
import pyautogui
import keyboard
import logging
from datetime import datetime
from PIL import Image, ImageTk

import stateManager
import onlyoneBox
import adicionarCliente
import KitTerra
import KitCeleiro
import KitSilo
import KitSerra
import KitMachado
import KitPa
import clearShop
import openAgent
import fullshopbaconeovos
import seeLoja
import ctypes
import mensagensprontas
from tkinter import colorchooser

# Adiciona o diretório atual ao PYTHONPATH
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

# Importa os módulos da API
from API.client import ConnectionManager

# Configuração do emulador
BASE_PATH = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(BASE_PATH, 'cfg', 'emulator_config.json')
ADMIN_CONFIG_FILE = os.path.join(BASE_PATH, 'cfg', 'adminConfig.json')
TEMPLATE_DIR = os.path.join(BASE_PATH, 'templates')

# Configuração do emulador
DEFAULT_EMULATOR_NAME = "FARMs"

# Configuração do arquivo de admin

def load_emulator_config():
    """Carrega a configuração do emulador do arquivo JSON"""
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
    except Exception:
        pass
    return {"window_name": DEFAULT_EMULATOR_NAME}

def save_emulator_config(config):
    """Salva a configuração do emulador no arquivo JSON"""
    os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=4)

def load_admin_config():
    """Carrega a configuração do admin do arquivo JSON"""
    try:
        if os.path.exists(ADMIN_CONFIG_FILE):
            with open(ADMIN_CONFIG_FILE, 'r') as f:
                return json.load(f)
    except Exception:
        pass
    return {"last_admin": "", "admins": [], "is_logged_in": False}

def save_admin_config(config):
    """Salva a configuração do admin no arquivo JSON"""
    os.makedirs(os.path.dirname(ADMIN_CONFIG_FILE), exist_ok=True)
    with open(ADMIN_CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=4)

# Configuração do ctypes para manipulação de janelas
user32 = ctypes.windll.user32
SW_RESTORE = 9
SW_SHOWNORMAL = 1

# Funções do Windows API
GetForegroundWindow = user32.GetForegroundWindow
GetForegroundWindow.restype = ctypes.c_void_p

SetForegroundWindow = user32.SetForegroundWindow
SetForegroundWindow.argtypes = [ctypes.c_void_p]
SetForegroundWindow.restype = ctypes.c_bool

ShowWindow = user32.ShowWindow
ShowWindow.argtypes = [ctypes.c_void_p, ctypes.c_int]
ShowWindow.restype = ctypes.c_bool

IsIconic = user32.IsIconic
IsIconic.argtypes = [ctypes.c_void_p]
IsIconic.restype = ctypes.c_bool

FindWindowW = user32.FindWindowW
FindWindowW.argtypes = [ctypes.c_wchar_p, ctypes.c_wchar_p]
FindWindowW.restype = ctypes.c_void_p

def window_management():
    """Funções auxiliares para gerenciamento de janelas"""

    def bring_window_to_front(window_title: str) -> bool:
        """Traz uma janela específica para frente"""
        hwnd = FindWindowW(None, window_title)
        if hwnd == 0:
            return False

        # Verifica se a janela está minimizada
        if IsIconic(hwnd):
            ShowWindow(hwnd, SW_RESTORE)

        # Define a janela como foreground e força a atualização
        ShowWindow(hwnd, SW_SHOWNORMAL)
        SetForegroundWindow(hwnd)

        return GetForegroundWindow() == hwnd

    def check_window_status(window_title: str) -> str:
        """Verifica o status de uma janela específica"""
        hwnd = FindWindowW(None, window_title)
        if hwnd == 0:
            return "Não encontrado"

        if IsIconic(hwnd):
            return "Minimizado"

        if GetForegroundWindow() == hwnd:
            return "Em foco"

        return "Aberto (não focado)"

    return {
        'bring_window_to_front': bring_window_to_front,
        'check_window_status': check_window_status
    }

# Instancia as funções de gerenciamento de janelas
window_utils = window_management()

class HayDayGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("HayDay Bot v0.12.0")  # Atualizada versão para 0.8.6
        # Definindo o ícone da janela
        icon_path = os.path.join(BASE_PATH, "dataset", "gato.png")
        if os.path.exists(icon_path):
            # Convertendo PNG para ICO em memória
            ico_path = os.path.join(BASE_PATH, "dataset", "gato.ico")
            if not os.path.exists(ico_path):
                img = Image.open(icon_path)
                img.save(ico_path, format='ICO', sizes=[(32,32)])
            self.root.iconbitmap(ico_path)
            icon = ImageTk.PhotoImage(file=icon_path)
            self.root.iconphoto(True, icon)
        
        # Configurar o grid principal
        self.root.grid_rowconfigure(0, weight=0)  # Frame de conexão não expande
        self.root.grid_rowconfigure(1, weight=1)  # Notebook ocupa o resto do espaço
        self.root.grid_columnconfigure(0, weight=1)
        
        # Inicializa o estilo
        self.style = ttk.Style()
        
        # Configurando o tema geral da interface
        self.root.configure(bg='#1a1a1a')  # Fundo preto suave
        self.style.configure("TFrame", background='#1a1a1a')
        self.style.configure("TLabelframe", background='#1a1a1a', foreground='white')
        self.style.configure("TLabelframe.Label", background='#1a1a1a', foreground='white')
        self.style.configure("TLabel", background='#1a1a1a', foreground='white')
        self.style.configure("TButton", background='#1a1a1a', foreground='black')
        
        # Tema escuro personalizado para Combobox padrão (outros dropdowns)
        self.style.map('TCombobox',
            background=[('readonly', '#2d2d2d'), ('active', '#404040')],
            fieldbackground=[('readonly', '#2d2d2d'), ('disabled', '#1a1a1a')],
            foreground=[('readonly', 'white'), ('disabled', 'gray')],
            selectbackground=[('readonly', '#404040')],
            selectforeground=[('readonly', 'white')],
            borderwidth=[('readonly', 1)],
            relief=[('readonly', 'solid')])
            
        # Configurações para os outros Comboboxes
        self.root.option_add('*TCombobox*Listbox.background', '#2d2d2d')
        self.root.option_add('*TCombobox*Listbox.foreground', 'white')
        self.root.option_add('*TCombobox*Listbox.selectBackground', '#404040')
        self.root.option_add('*TCombobox*Listbox.selectForeground', 'white')
        self.root.option_add('*TCombobox*Listbox.font', ('Arial', 11))
            
        # Estilo específico para o Combobox de Admin
        admin_style = ttk.Style()
        admin_style.configure('Admin.TCombobox', 
                           padding=3,
                           background='#1a1a1a',
                           foreground='white',
                           arrowcolor='white',
                           fieldbackground='#1a1a1a',
                           selectbackground='#1a1a1a',
                           font=('Arial', 11))
                           
        admin_style.map('Admin.TCombobox',
            background=[('readonly', '#1a1a1a'), ('active', '#1a1a1a')],
            fieldbackground=[('readonly', '#1a1a1a'), ('disabled', '#1a1a1a')],
            foreground=[('readonly', 'white'), ('disabled', 'gray')],
            selectbackground=[('readonly', '#1a1a1a')],
            selectforeground=[('readonly', 'white')],
            borderwidth=[('readonly', 1)],
            relief=[('readonly', 'solid')])
            
        # Configurações específicas para a lista do Combobox de Admin
        self.root.option_add('*Admin.TCombobox*Listbox.background', '#1a1a1a')
        self.root.option_add('*Admin.TCombobox*Listbox.foreground', 'white')
        self.root.option_add('*Admin.TCombobox*Listbox.selectBackground', '#1a1a1a')
        self.root.option_add('*Admin.TCombobox*Listbox.selectForeground', 'white')
        self.root.option_add('*Admin.TCombobox*Listbox.font', ('Arial', 11))        
        # Carrega configuração do emulador
        self.emulator_config = load_emulator_config()
        
        # Carrega configuração do admin (apenas lista de admins)
        self.admin_config = load_admin_config()
        
        # Configuração da janela
        self.root.minsize(300, 900)  # Reduzido o tamanho mínimo
        self.root.maxsize(300, 900)  # Reduzido o tamanho máximo

        # Frame para conexão com o site
        self.connection_frame = ttk.LabelFrame(root, text="Conexão com o Site", style="TLabelframe")
        self.connection_frame.grid(row=0, column=0, padx=1, pady=(0,1), sticky="ew")
        
        # Frame para seleção de admin
        self.admin_frame = ttk.Frame(self.connection_frame)
        self.admin_frame.grid(row=0, column=0, columnspan=2, sticky="ew", padx=5, pady=1)
        
        # Label e Combobox para seleção de admin
        ttk.Label(self.admin_frame, text="Admin:").grid(row=0, column=0, padx=2, pady=2, sticky="w")
        
        self.admin_var = tk.StringVar()
        self.admin_combo = ttk.Combobox(self.admin_frame, textvariable=self.admin_var, values=self.admin_config["admins"], state="readonly")
        self.admin_combo.grid(row=0, column=1, padx=2, pady=2, sticky="ew")
        
        def on_admin_select(event):
            selected = self.admin_var.get()
            if selected:
                self.admin_config["last_admin"] = selected
                save_admin_config(self.admin_config)
        
        self.admin_combo.bind('<<ComboboxSelected>>', on_admin_select)
        
        # Status da conexão
        self.connection_status = ttk.Label(self.connection_frame, text="Status: Desconectado", style="TLabel")
        self.connection_status.grid(row=1, column=0, padx=2, pady=2, sticky="w")
        
        # Frame para os botões de conexão
        self.connection_buttons_frame = ttk.Frame(self.connection_frame)
        self.connection_buttons_frame.grid(row=1, column=1, sticky="e", pady=1)
        
        # Botões de conectar/desconectar
        self.connect_button = ttk.Button(self.connection_buttons_frame, text="Conectar", width=10, command=self.connect_to_site)
        self.connect_button.grid(row=0, column=0, padx=2, pady=2)
        
        self.disconnect_button = ttk.Button(self.connection_buttons_frame, text="Desconectar", width=10, command=self.disconnect_from_site, state="disabled")
        self.disconnect_button.grid(row=0, column=1, padx=2, pady=2)
        
        # Criar notebook para as abas
        self.notebook = ttk.Notebook(root)
        self.notebook.grid(row=1, column=0, sticky="nsew", padx=1, pady=1)

        # Aba principal
        self.main_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.main_frame, text="Principal", padding=1)
        
        # Configurar grid do main_frame
        self.main_frame.grid_columnconfigure(0, weight=1)

        # Segunda aba (Configurações)
        self.second_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.second_frame, text="Configurações", padding=1)
        
        # Configurar grid do second_frame
        self.second_frame.grid_rowconfigure(1, weight=1)
        self.second_frame.grid_columnconfigure(0, weight=1)

        # Terceira aba (Moedas)
        self.coins_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.coins_frame, text="Moedas", padding=1)
        
        # Configurar grid do coins_frame
        self.coins_frame.grid_rowconfigure(0, weight=1)
        self.coins_frame.grid_columnconfigure(0, weight=1)

        # Quarta aba (Mensagens)
        self.messages_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.messages_frame, text="Mensagens", padding=1)
        
        # Configurar grid do messages_frame
        self.messages_frame.grid_rowconfigure(0, weight=1)
        self.messages_frame.grid_columnconfigure(0, weight=1)

        # Frame para seleção de aplicativo
        app_frame = ttk.LabelFrame(self.second_frame, text="Abrir Aplicativo")
        app_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=5)
        
        # Configurar grid do app_frame
        app_frame.grid_columnconfigure(0, weight=1)

        # Dropdown para seleção do aplicativo
        ttk.Label(app_frame, text="Selecione o aplicativo:").grid(row=0, column=0, pady=5, sticky="ew")
        self.open_agent = openAgent.OpenAgent()
        self.app_var = tk.StringVar()
        self.app_dropdown = ttk.Combobox(
            app_frame, 
            textvariable=self.app_var,
            values=self.open_agent.get_app_list(),
            state="readonly",
            justify="center"  # Centralizando o texto do combobox
        )
        self.app_dropdown.grid(row=1, column=0, padx=10, pady=5, sticky="ew")
        self.app_dropdown.set("TERRA")

        # Botão para abrir o aplicativo
        self.open_app_button = ttk.Button(
            app_frame,
            text="Abrir Aplicativo",
            command=self.open_selected_app,
            style="Accent.TButton"
        )
        self.open_app_button.grid(row=2, column=0, pady=5)

        # Configuração do Emulador no main_frame
        emulator_frame = ttk.LabelFrame(self.main_frame, text="Configuração do Emulador")
        emulator_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=5)
        
        # Configurar grid do emulator_frame
        emulator_frame.grid_columnconfigure(0, weight=1)

        ttk.Label(emulator_frame, text="Nome da Janela:").grid(row=0, column=0, pady=5)
        self.emulator_name = tk.StringVar(value=self.emulator_config["window_name"])
        self.emulator_entry = ttk.Entry(emulator_frame, textvariable=self.emulator_name)
        self.emulator_entry.grid(row=1, column=0, sticky="ew", padx=5)
        
        ttk.Button(
            emulator_frame,
            text="Salvar Configuração",
            command=self.save_emulator_settings
        ).grid(row=2, column=0, pady=5)

        # Estado e Status
        status_frame = ttk.LabelFrame(self.main_frame, text="Status do Sistema")
        status_frame.grid(row=2, column=0, sticky="nsew", padx=10, pady=5)
        status_frame.grid_columnconfigure(0, weight=1)

        # Frame para o estado atual
        state_container = ttk.Frame(status_frame)
        state_container.grid(row=0, column=0, sticky="ew", padx=5, pady=2)
        state_container.grid_columnconfigure(1, weight=1)

        ttk.Label(
            state_container,
            text="HD Estado:",
            font=('Arial', 10, 'bold'),
            foreground='#ADD8E6'  # Azul claro
        ).grid(row=0, column=0, padx=(0, 5))

        self.state_label = ttk.Label(
            state_container,
            text=stateManager.state_manager.current_state,
            font=('Arial', 10, 'bold'),
            foreground='#90EE90'  # Verde claro
        )
        self.state_label.grid(row=0, column=1, sticky="w")

        # Frame para o status
        status_container = ttk.Frame(status_frame)
        status_container.grid(row=1, column=0, sticky="ew", padx=5, pady=2)
        status_container.grid_columnconfigure(1, weight=1)

        ttk.Label(
            status_container,
            text="Status:",
            font=('Arial', 10, 'bold'),
            foreground='#ADD8E6'  # Azul claro
        ).grid(row=0, column=0, padx=(0, 5))

        self.status_label = ttk.Label(
            status_container,
            text="Pronto",
            font=('Arial', 10, 'bold'),
            foreground='#90EE90'  # Verde claro
        )
        self.status_label.grid(row=0, column=1, sticky="w")

        # Frame para o status do emulador
        emulator_container = ttk.Frame(status_frame)
        emulator_container.grid(row=2, column=0, sticky="ew", padx=5, pady=2)
        emulator_container.grid_columnconfigure(1, weight=1)

        ttk.Label(
            emulator_container,
            text="Emulador:",
            font=('Arial', 10, 'bold'),
            foreground='#ADD8E6'  # Azul claro
        ).grid(row=0, column=0, padx=(0, 5))

        self.emulator_status_label = ttk.Label(
            emulator_container,
            text="Verificando...",
            font=('Arial', 10, 'bold'),
            foreground='#90EE90'  # Verde claro
        )
        self.emulator_status_label.grid(row=0, column=1, sticky="w")

        # Tag input
        tag_frame = ttk.Frame(self.main_frame)
        tag_frame.grid(row=3, column=0, sticky="nsew", pady=5)
        tag_frame.grid_columnconfigure(0, weight=1)

        ttk.Label(tag_frame, text="Tag do Cliente:").grid(row=0, column=0)
        self.tag_entry = ttk.Entry(tag_frame)
        self.tag_entry.grid(row=1, column=0, sticky="ew", padx=10)

        # Frame para os botões principais
        self.main_buttons_frame = ttk.LabelFrame(self.main_frame, text="Ações")
        self.main_buttons_frame.grid(row=4, column=0, sticky="nsew", padx=10, pady=2)
        
        # Configurar grid do main_buttons_frame
        self.main_buttons_frame.grid_columnconfigure(0, weight=1)

        # Aplicando o gradiente no frame de ações
        actions_gradient_canvas = tk.Canvas(self.main_buttons_frame, highlightthickness=0)
        actions_gradient_canvas.place(relx=0, rely=0, relwidth=1, relheight=1)
        
        # Criando o gradiente para o frame de ações
        actions_gradient_colors = ['#1a1a1a', '#1f2d3f', '#23354d', '#264d73']  # Do preto ao azul
        for i in range(len(actions_gradient_colors)-1):
            actions_gradient_canvas.create_rectangle(0, i * (300/len(actions_gradient_colors)), 
                                                500, (i+1) * (300/len(actions_gradient_colors)), 
                                                fill=actions_gradient_colors[i], 
                                                outline=actions_gradient_colors[i])

        # Configuração de estilo para os botões de ação
        self.style.configure('Action.TButton',
                          padding=8,
                          font=('Arial', 10, 'bold'),
                          background='#264d73',
                          foreground='black')  # Mudando para preto
        
        self.style.map('Action.TButton',
                    background=[('active', '#1f2d3f')],
                    foreground=[('active', 'black')])  # Mantendo preto quando ativo

        # Botões principais com espaçamento e estilo melhorado
        self.add_client_button = ttk.Button(
            self.main_buttons_frame,
            text="Adicionar Cliente",
            command=self.start_bot_thread,
            style="Action.TButton"
        )
        self.add_client_button.grid(row=0, column=0, padx=5, pady=2, sticky="ew")

        self.focus_button = ttk.Button(
            self.main_buttons_frame,
            text="Focar Emulador",
            command=self.focus_emulator,
            style="Action.TButton"
        )
        self.focus_button.grid(row=1, column=0, padx=5, pady=2, sticky="ew")

        self.clear_shop_button = ttk.Button(
            self.main_buttons_frame,
            text="Limpar Loja",
            command=self.start_clear_shop_thread,
            style="Action.TButton"
        )
        self.clear_shop_button.grid(row=2, column=0, padx=5, pady=2, sticky="ew")

        # Frame para a visualização da loja
        self.shop_frame = ttk.LabelFrame(self.main_frame, text="Status da Loja")
        self.shop_frame.grid(row=5, column=0, sticky="nsew", padx=10, pady=2)
        
        # Configurar grid do shop_frame
        self.shop_frame.grid_columnconfigure(0, weight=1)

        # Frame para as caixas da loja (5x2 grid)
        self.boxes_frame = ttk.Frame(self.shop_frame)
        self.boxes_frame.grid(row=0, column=0, padx=10, pady=2)
        
        # Configurar grid do boxes_frame
        for i in range(2):
            self.boxes_frame.grid_rowconfigure(i, weight=1)
        for i in range(5):
            self.boxes_frame.grid_columnconfigure(i, weight=1)

        # Criar canvas para cada box na ordem correta do Hayday
        self.box_canvases = {}
        # Primeira linha: 1,3,5,7,9
        box_order_row1 = [1,3,5,7,9]
        for col, box_num in enumerate(box_order_row1):
            canvas = tk.Canvas(self.boxes_frame, width=50, height=50, bg='gray')
            canvas.grid(row=0, column=col, padx=5, pady=2)
            canvas.bind("<Button-1>", lambda e, bn=box_num: self.on_box_click(bn))
            self.box_canvases[f"box{box_num}"] = canvas
            
        # Segunda linha: 2,4,6,8,10
        box_order_row2 = [2,4,6,8,10]
        for col, box_num in enumerate(box_order_row2):
            canvas = tk.Canvas(self.boxes_frame, width=50, height=50, bg='gray')
            canvas.grid(row=1, column=col, padx=5, pady=2)
            canvas.bind("<Button-1>", lambda e, bn=box_num: self.on_box_click(bn))
            self.box_canvases[f"box{box_num}"] = canvas

        # Frame para os botões da loja
        shop_buttons_frame = ttk.Frame(self.shop_frame)
        shop_buttons_frame.grid(row=1, column=0, pady=2)

        # Botão Sync Shop
        self.sync_button = ttk.Button(shop_buttons_frame, text="Sync Shop", command=self.sync_shop)
        self.sync_button.grid(row=0, column=0, padx=5)

        # Botão Toggle Box10
        self.toggle_box10_button = ttk.Button(shop_buttons_frame, text="Box10: ON", command=self.toggle_box10)
        self.toggle_box10_button.grid(row=0, column=1, padx=5)

        # Frame para os kits
        kits_frame = ttk.LabelFrame(self.main_frame, text="Kits")
        kits_frame.grid(row=6, column=0, sticky="nsew", padx=10, pady=2)
        
        # Configurar grid do kits_frame
        kits_frame.grid_columnconfigure(0, weight=1)

        # Aplicando o gradiente no frame dos kits
        gradient_canvas = tk.Canvas(kits_frame, highlightthickness=0)
        gradient_canvas.place(relx=0, rely=0, relwidth=1, relheight=1)
        
        # Criando o gradiente
        kits_gradient_colors = ['#1a1a1a', '#2d1f3f', '#3d2359', '#4d2673']  # Do preto ao roxo
        for i in range(len(kits_gradient_colors)-1):
            gradient_canvas.create_rectangle(0, i * (400/len(kits_gradient_colors)), 
                                          500, (i+1) * (400/len(kits_gradient_colors)), 
                                          fill=kits_gradient_colors[i], 
                                          outline=kits_gradient_colors[i])
        
        kit_buttons = [
            ("Vender Kit Terra", self.start_kit_terra_thread, "Terra.TButton"),
            ("Vender Kit Celeiro", self.start_kit_celeiro_thread, "Celeiro.TButton"),
            ("Vender Kit Silo", self.start_kit_silo_thread, "Silo.TButton"),
            ("Vender Kit Serra", self.start_kit_serra_thread, "Serra.TButton"),
            ("Vender Kit Machado", self.start_kit_machado_thread, "Machado.TButton"),
            ("Vender Kit Pá", self.start_kit_pa_thread, "Pa.TButton")
        ]

        for i, (text, command, style) in enumerate(kit_buttons):
            btn = ttk.Button(kits_frame, text=text, command=command, style=style)
            btn.grid(row=i, column=0, sticky="ew", pady=2)
            setattr(self, f"kit_button_{i}", btn)

        # Botões de Moedas
        coins_buttons_frame = ttk.LabelFrame(self.coins_frame, text="Ações de Moedas")
        coins_buttons_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=5)
        coins_buttons_frame.grid_columnconfigure(0, weight=1)

        self.full_bacon_ovos_button = ttk.Button(
            coins_buttons_frame,
            text="Full Bacon e Ovos",
            command=self.start_fullshop_bacon_ovos_thread,
            style="Clear.TButton",
            width=20  # Define uma largura fixa para o botão
        )
        self.full_bacon_ovos_button.grid(row=0, column=0, sticky="ew", pady=2, padx=5)

        # Frame para as mensagens
        messages_container = ttk.Frame(self.messages_frame)
        messages_container.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        messages_container.grid_columnconfigure(0, weight=1)
        messages_container.grid_rowconfigure(0, weight=1)

        # Criar um Canvas e um Frame interno para permitir rolagem
        canvas = tk.Canvas(messages_container, bg=self.root.cget('bg'), highlightthickness=0)
        scrollbar = ttk.Scrollbar(messages_container, orient="vertical", command=canvas.yview, style='Transparent.Vertical.TScrollbar')
        scrollable_frame = ttk.Frame(canvas)

        # Configurar o scrollable_frame para ter largura fixa
        scrollable_frame.grid_columnconfigure(0, weight=1)

        def configure_scroll_region(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
            canvas.itemconfig("win", width=canvas.winfo_width() - 4)  # -4 para dar uma pequena margem

        def configure_canvas(event):
            canvas.itemconfig("win", width=canvas.winfo_width() - 4)  # -4 para dar uma pequena margem

        scrollable_frame.bind("<Configure>", configure_scroll_region)
        canvas.bind("<Configure>", configure_canvas)

        # Criar a janela no canvas com uma tag para poder redimensionar depois
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw", tags="win")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Configurar o estilo da barra de rolagem para ser mais fina e transparente
        self.style.configure('Transparent.Vertical.TScrollbar',
                           background='#1a1a1a',
                           bordercolor='#1a1a1a',
                           arrowcolor='#1a1a1a',
                           troughcolor='#1a1a1a',
                           width=8)

        # Carregar cores das categorias
        self.category_colors = self.load_category_colors()

        # Para cada categoria de mensagens
        for i, (categoria, mensagens) in enumerate(mensagensprontas.mensagens_categorias.items()):
            # Configurar estilo personalizado para a categoria
            style_name = f"Custom.{categoria}.TLabelframe"
            self.style.configure(style_name, background='#1a1a1a')
            self.style.configure(f"{style_name}.Label", 
                               background='#1a1a1a',
                               foreground=self.category_colors.get(categoria, "#ffffff"))

            # Criar um LabelFrame para a categoria
            category_frame = ttk.LabelFrame(scrollable_frame, text=categoria, style=style_name)
            category_frame.grid(row=i, column=0, sticky="ew", padx=3, pady=2)
            category_frame.grid_columnconfigure(0, weight=1)

            # Adicionar menu de contexto para mudar cor
            self.create_category_context_menu(categoria, category_frame)

            # Frame para organizar os botões em grid
            buttons_frame = ttk.Frame(category_frame)
            buttons_frame.grid(row=0, column=0, sticky="ew", padx=3, pady=3)
            
            # Configurar o grid para ter 2 colunas com pesos iguais
            buttons_frame.grid_columnconfigure(0, weight=1, uniform='col')
            buttons_frame.grid_columnconfigure(1, weight=1, uniform='col')

            # Adicionar botões para cada mensagem na categoria
            for j, (key, msg) in enumerate(mensagens.items()):
                # Criar um nome curto para o botão (primeiras 20 caracteres)
                short_text = msg[:20] + "..." if len(msg) > 20 else msg
                
                # Calcular posição do botão (2 colunas)
                row = j // 2
                col = j % 2

                btn = ttk.Button(
                    buttons_frame,
                    text=short_text,
                    command=lambda m=msg: self.copy_to_clipboard(m),
                    style='Message.TButton'
                )
                btn.grid(row=row, column=col, sticky="ew", pady=2, padx=3)
                
                # Criar tooltip
                self.create_tooltip(btn, msg)

        # Configurar o grid do canvas e scrollbar
        canvas.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")

        # Estilo personalizado para os botões de mensagem
        self.style.configure('Message.TButton',
                           padding=4)

        # Bind da roda do mouse para rolagem
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        canvas.bind_all("<MouseWheel>", _on_mousewheel)

        # Bot instances
        self.bot = None
        self.bot_thread = None
        self.kit_terra_bot = None
        self.kit_terra_thread = None
        self.kit_celeiro_bot = None
        self.kit_celeiro_thread = None
        self.kit_silo_bot = None
        self.kit_silo_thread = None
        self.kit_serra_bot = None
        self.kit_serra_thread = None
        self.kit_machado_bot = None
        self.kit_machado_thread = None
        self.kit_pa_bot = None
        self.kit_pa_thread = None
        self.fullshop_bacon_ovos_bot = None
        self.fullshop_bacon_ovos_thread = None
        self.clear_shop_bot = None
        self.clear_shop_thread = None
        self.see_loja = seeLoja.SeeLoja()
        self.connection_manager = None
        self.state_update_thread = None
        self.stop_state_update = False

        # Eventos
        # self.api_link.bind("<Button-1>", self.copy_api_url)
        # self.api_link.bind("<Enter>", lambda e: self.api_link.configure(foreground="purple"))
        # self.api_link.bind("<Leave>", lambda e: self.api_link.configure(foreground="blue"))

        # Inicia o monitoramento de estado
        if not stateManager.state_manager.is_running:
            stateManager.state_manager.start()
            
        # Espera um pouco para o estado ser detectado
        time.sleep(0.2)
        
        # Carrega a configuração do admin (apenas lista de admins)
        self.admin_config = load_admin_config()
        
        # Inicia a atualização do estado na GUI
        self.update_state()
        
        # Registra o callback para quando a janela for fechada
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def focus_emulator(self):
        """Função para focar o emulador com efeito visual"""
        if window_utils['bring_window_to_front']("FARMs"):
            self.flash_focus_button()

    def flash_focus_button(self):
        """Cria um efeito de flash no botão de foco"""
        self.focus_button.configure(style="Flash.TButton")
        self.root.after(200, lambda: self.focus_button.configure(style="TButton"))

    # def copy_api_url(self, event):
    #     """Copia o URL da API para a área de transferência"""
    #     api_url = "http://localhost:5000/api/adicionar-cliente"
    #     self.root.clipboard_clear()
    #     self.root.clipboard_append(api_url)

    #     # Feedback visual temporário
    #     original_color = self.api_link.cget("foreground")
    #     self.api_link.configure(foreground="green")
    #     self.root.after(500, lambda: self.api_link.configure(foreground=original_color))

    #     # Mostra mensagem de confirmação
    #     messagebox.showinfo("Copiado!", "URL da API copiado para a área de transferência!")

    def update_state(self):
        """Atualiza o estado atual na interface"""
        try:
            # Atualiza estado do bot
            current_state = stateManager.state_manager.current_state
            self.state_label.config(
                text=current_state,
                foreground='#90EE90' if current_state in ["Inicio", "Dentro da Loja"] else '#FFB6C1'  # Verde claro se estado ok, rosa claro se não
            )

            # Atualiza status do emulador
            emulator_status = window_utils['check_window_status']("FARMs")
            status_color = {
                "Em foco": '#90EE90',      # Verde claro
                "Aberto (não focado)": '#FFD700',  # Dourado
                "Minimizado": '#FFB6C1',    # Rosa claro
                "Não encontrado": '#FF6B6B'  # Vermelho claro
            }.get(emulator_status, '#FFB6C1')
            
            self.emulator_status_label.config(
                text=emulator_status,
                foreground=status_color
            )
        except Exception as e:
            print(f"Erro ao atualizar estado: {e}")

        # Atualiza a cada 100ms
        self.root.after(100, self.update_state)

    def start_bot_thread(self):
        """Start the bot in a separate thread to prevent GUI freezing"""
        # Validar se está na tela inicial ou dentro da loja
        current_state = stateManager.state_manager.get_current_state()
        if current_state != "Inicio" and current_state != "Dentro da Loja":
            messagebox.showwarning("Aviso", "Por favor, vá para a tela inicial do jogo ou entre na loja!")
            return
            
        # Validar se a tag foi inserida
        tag = self.tag_entry.get().strip()
        if not tag:
            messagebox.showwarning("Aviso", "Por favor, insira a tag do cliente!")
            return
            
        if self.bot_thread and self.bot_thread.is_alive():
            messagebox.showwarning("Aviso", "Bot já está em execução!")
            return
            
        self.add_client_button.state(['disabled'])
        self.status_label.config(text="Status: Iniciando bot...")
        
        self.bot_thread = threading.Thread(target=lambda: self.run_bot(tag))
        self.bot_thread.daemon = True
        self.bot_thread.start()

    def run_bot(self, tag):
        """Execute the bot functionality"""
        try:
            if not hasattr(self, 'bot') or self.bot is None:
                self.bot = adicionarCliente.HayDayBot()
            # Atualiza o nome da janela
            self.bot.window_name = self.emulator_config["window_name"]
            self.status_label.config(text="Status: Adicionando cliente...")

            if self.bot.adicionar_cliente(tag):
                self.status_label.config(text="Status: Cliente adicionado com sucesso!")
                messagebox.showinfo("Sucesso", "Cliente adicionado com sucesso!")
            else:
                raise Exception("Falha ao adicionar cliente")

        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao executar o bot: {str(e)}")
            self.status_label.config(text="Status: Erro ao adicionar cliente")
        finally:
            self.add_client_button.state(['!disabled'])

    def start_kit_terra_thread(self):
        """Inicia o processo de venda do Kit Terra em uma thread separada"""
        # Validar se está na loja
        if stateManager.state_manager.get_current_state() != "Dentro da Loja":
            messagebox.showwarning("Aviso", "Por favor, entre na loja primeiro!")
            return

        if self.kit_terra_thread and self.kit_terra_thread.is_alive():
            messagebox.showwarning("Aviso", "Kit Terra já está em execução!")
            return

        self.kit_button_0.state(['disabled'])
        self.status_label.config(text="Status: Iniciando venda do Kit Terra...")

        self.kit_terra_thread = threading.Thread(target=self.run_kit_terra)
        self.kit_terra_thread.daemon = True
        self.kit_terra_thread.start()

    def run_kit_terra(self):
        """Executa a funcionalidade do Kit Terra"""
        try:
            if not hasattr(self, 'kit_terra_bot') or self.kit_terra_bot is None:
                self.kit_terra_bot = KitTerra.KitTerraBot()
            # Atualiza o nome da janela
            self.kit_terra_bot.window_name = self.emulator_config["window_name"]
            self.status_label.config(text="Status: Vendendo Kit Terra...")

            resultado = self.kit_terra_bot.vender_kit_terra()

            if "Processo de venda concluído" in resultado:
                self.status_label.config(text="Status: Kit Terra vendido com sucesso!")
                messagebox.showinfo("Sucesso", "Kit Terra vendido com sucesso!")
            else:
                if resultado == "Caixa já possui itens!":
                    self.status_label.config(text="Status: Todas as caixas estão ocupadas")
                    messagebox.showwarning("Aviso", "Todas as caixas estão ocupadas!")
                else:
                    messagebox.showwarning("Aviso", resultado)
                    self.status_label.config(text=f"Status: {resultado}")

        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao vender Kit Terra: {str(e)}")
            self.status_label.config(text="Status: Erro ao vender Kit Terra")
        finally:
            self.kit_button_0.state(['!disabled'])

    def start_kit_celeiro_thread(self):
        """Inicia o processo de venda do Kit Celeiro em uma thread separada"""
        if self.kit_celeiro_thread and self.kit_celeiro_thread.is_alive():
            messagebox.showwarning("Aviso", "Kit Celeiro já está em execução!")
            return

        self.kit_button_1.state(['disabled'])
        self.status_label.config(text="Status: Iniciando venda do Kit Celeiro...")

        self.kit_celeiro_thread = threading.Thread(target=self.run_kit_celeiro)
        self.kit_celeiro_thread.daemon = True
        self.kit_celeiro_thread.start()

    def run_kit_celeiro(self):
        """Executa a funcionalidade do Kit Celeiro"""
        try:
            if not hasattr(self, 'kit_celeiro_bot') or self.kit_celeiro_bot is None:
                self.kit_celeiro_bot = KitCeleiro.KitCeleiroBot()
            # Atualiza o nome da janela
            self.kit_celeiro_bot.window_name = self.emulator_config["window_name"]
            self.status_label.config(text="Status: Vendendo Kit Celeiro...")

            resultado = self.kit_celeiro_bot.vender_kit_celeiro()

            if "Processo de venda concluído" in resultado:
                self.status_label.config(text="Status: Kit Celeiro vendido com sucesso!")
                messagebox.showinfo("Sucesso", "Kit Celeiro vendido com sucesso!")
            else:
                if resultado == "Caixa já possui itens!":
                    self.status_label.config(text="Status: Todas as caixas estão ocupadas")
                    messagebox.showwarning("Aviso", "Todas as caixas estão ocupadas!")
                else:
                    messagebox.showwarning("Aviso", resultado)
                    self.status_label.config(text=f"Status: {resultado}")

        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao vender Kit Celeiro: {str(e)}")
            self.status_label.config(text="Status: Erro ao vender Kit Celeiro")
        finally:
            self.kit_button_1.state(['!disabled'])

    def start_kit_silo_thread(self):
        """Inicia o processo de venda do Kit Silo em uma thread separada"""
        # Validar se está na loja
        if stateManager.state_manager.get_current_state() != "Dentro da Loja":
            messagebox.showwarning("Aviso", "Por favor, entre na loja primeiro!")
            return

        if self.kit_silo_thread and self.kit_silo_thread.is_alive():
            messagebox.showwarning("Aviso", "Kit Silo já está em execução!")
            return

        self.kit_button_2.state(['disabled'])
        self.status_label.config(text="Status: Iniciando venda do Kit Silo...")

        self.kit_silo_thread = threading.Thread(target=self.run_kit_silo)
        self.kit_silo_thread.daemon = True
        self.kit_silo_thread.start()

    def run_kit_silo(self):
        """Executa a funcionalidade do Kit Silo"""
        try:
            if not hasattr(self, 'kit_silo_bot') or self.kit_silo_bot is None:
                self.kit_silo_bot = KitSilo.KitSiloBot()
            # Atualiza o nome da janela
            self.kit_silo_bot.window_name = self.emulator_config["window_name"]
            self.status_label.config(text="Status: Vendendo Kit Silo...")

            resultado = self.kit_silo_bot.vender_kit_silo()

            if "Processo de venda concluído" in resultado:
                self.status_label.config(text="Status: Kit Silo vendido com sucesso!")
                messagebox.showinfo("Sucesso", "Kit Silo vendido com sucesso!")
            else:
                if resultado == "Caixa já possui itens!":
                    self.status_label.config(text="Status: Todas as caixas estão ocupadas")
                    messagebox.showwarning("Aviso", "Todas as caixas estão ocupadas!")
                else:
                    messagebox.showwarning("Aviso", resultado)
                    self.status_label.config(text=f"Status: {resultado}")

        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao vender Kit Silo: {str(e)}")
            self.status_label.config(text="Status: Erro ao vender Kit Silo")
        finally:
            self.kit_button_2.state(['!disabled'])

    def start_kit_serra_thread(self):
        """Inicia o processo de venda do Kit Serra em uma thread separada"""
        # Validar se está na loja
        if stateManager.state_manager.get_current_state() != "Dentro da Loja":
            messagebox.showwarning("Aviso", "Por favor, entre na loja primeiro!")
            return

        if self.kit_serra_thread and self.kit_serra_thread.is_alive():
            messagebox.showwarning("Aviso", "Kit Serra já está em execução!")
            return

        self.kit_button_3.state(['disabled'])
        self.status_label.config(text="Status: Iniciando venda do Kit Serra...")

        self.kit_serra_thread = threading.Thread(target=self.run_kit_serra)
        self.kit_serra_thread.daemon = True
        self.kit_serra_thread.start()

    def run_kit_serra(self):
        """Executa a funcionalidade do Kit Serra"""
        try:
            if not hasattr(self, 'kit_serra_bot') or self.kit_serra_bot is None:
                self.kit_serra_bot = KitSerra.KitSerraBot()
            # Atualiza o nome da janela
            self.kit_serra_bot.window_name = self.emulator_config["window_name"]
            self.status_label.config(text="Status: Vendendo Kit Serra...")

            resultado = self.kit_serra_bot.vender_kit_serra()

            if "Processo de venda concluído" in resultado:
                self.status_label.config(text="Status: Kit Serra vendido com sucesso!")
                messagebox.showinfo("Sucesso", "Kit Serra vendido com sucesso!")
            else:
                if resultado == "Caixa já possui itens!":
                    self.status_label.config(text="Status: Todas as caixas estão ocupadas")
                    messagebox.showwarning("Aviso", "Todas as caixas estão ocupadas!")
                else:
                    messagebox.showwarning("Aviso", resultado)
                    self.status_label.config(text=f"Status: {resultado}")

        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao vender Kit Serra: {str(e)}")
            self.status_label.config(text="Status: Erro ao vender Kit Serra")
        finally:
            self.kit_button_3.state(['!disabled'])

    def start_kit_machado_thread(self):
        """Inicia o processo de venda do Kit Machado em uma thread separada"""
        # Validar se está na loja
        if stateManager.state_manager.get_current_state() != "Dentro da Loja":
            messagebox.showwarning("Aviso", "Por favor, entre na loja primeiro!")
            return

        if self.kit_machado_thread and self.kit_machado_thread.is_alive():
            messagebox.showwarning("Aviso", "Kit Machado já está em execução!")
            return

        self.kit_button_4.state(['disabled'])
        self.status_label.config(text="Status: Iniciando venda do Kit Machado...")

        self.kit_machado_thread = threading.Thread(target=self.run_kit_machado)
        self.kit_machado_thread.daemon = True
        self.kit_machado_thread.start()

    def run_kit_machado(self):
        """Executa a funcionalidade do Kit Machado"""
        try:
            if not hasattr(self, 'kit_machado_bot') or self.kit_machado_bot is None:
                self.kit_machado_bot = KitMachado.KitMachadoBot()
            # Atualiza o nome da janela
            self.kit_machado_bot.window_name = self.emulator_config["window_name"]
            self.status_label.config(text="Status: Vendendo Kit Machado...")

            resultado = self.kit_machado_bot.vender_kit_machado()

            if "Processo de venda concluído" in resultado:
                self.status_label.config(text="Status: Kit Machado vendido com sucesso!")
                messagebox.showinfo("Sucesso", "Kit Machado vendido com sucesso!")
            else:
                if resultado == "Caixa já possui itens!":
                    self.status_label.config(text="Status: Todas as caixas estão ocupadas")
                    messagebox.showwarning("Aviso", "Todas as caixas estão ocupadas!")
                else:
                    messagebox.showwarning("Aviso", resultado)
                    self.status_label.config(text=f"Status: {resultado}")

        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao vender Kit Machado: {str(e)}")
            self.status_label.config(text="Status: Erro ao vender Kit Machado")
        finally:
            self.kit_button_4.state(['!disabled'])

    def start_kit_pa_thread(self):
        """Inicia o processo de venda do Kit Pá em uma thread separada"""
        # Validar se está na loja
        if stateManager.state_manager.get_current_state() != "Dentro da Loja":
            messagebox.showwarning("Aviso", "Por favor, entre na loja primeiro!")
            return

        if self.kit_pa_thread and self.kit_pa_thread.is_alive():
            messagebox.showwarning("Aviso", "Kit Pá já está em execução!")
            return

        self.kit_button_5.state(['disabled'])
        self.status_label.config(text="Status: Iniciando venda do Kit Pá...")

        self.kit_pa_thread = threading.Thread(target=self.run_kit_pa)
        self.kit_pa_thread.daemon = True
        self.kit_pa_thread.start()

    def run_kit_pa(self):
        """Executa a funcionalidade do Kit Pá"""
        try:
            if not hasattr(self, 'kit_pa_bot') or self.kit_pa_bot is None:
                self.kit_pa_bot = KitPa.KitPaBot()
            # Atualiza o nome da janela
            self.kit_pa_bot.window_name = self.emulator_config["window_name"]
            self.status_label.config(text="Status: Vendendo Kit Pá...")

            resultado = self.kit_pa_bot.vender_kit_pa()

            if "Processo de venda concluído" in resultado:
                self.status_label.config(text="Status: Kit Pá vendido com sucesso!")
                messagebox.showinfo("Sucesso", "Kit Pá vendido com sucesso!")
            else:
                if resultado == "Caixa já possui itens!":
                    self.status_label.config(text="Status: Todas as caixas estão ocupadas")
                    messagebox.showwarning("Aviso", "Todas as caixas estão ocupadas!")
                else:
                    messagebox.showwarning("Aviso", resultado)
                    self.status_label.config(text=f"Status: {resultado}")

        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao vender Kit Pá: {str(e)}")
            self.status_label.config(text="Status: Erro ao vender Kit Pá")
        finally:
            self.kit_button_5.state(['!disabled'])

    def start_fullshop_bacon_ovos_thread(self):
        """Inicia o processo de venda do Bacon e Ovos em uma thread separada"""
        if self.fullshop_bacon_ovos_thread and self.fullshop_bacon_ovos_thread.is_alive():
            messagebox.showwarning("Aviso", "Bot já está em execução!")
            return
            
        self.status_label.config(text="Status: Iniciando venda de Bacon e Ovos...")
        
        self.fullshop_bacon_ovos_thread = threading.Thread(target=self.run_fullshop_bacon_ovos)
        self.fullshop_bacon_ovos_thread.daemon = True
        self.fullshop_bacon_ovos_thread.start()

    def run_fullshop_bacon_ovos(self):
        """Executa a funcionalidade de venda do Bacon e Ovos"""
        try:
            if not hasattr(self, 'fullshop_bacon_ovos_bot') or self.fullshop_bacon_ovos_bot is None:
                self.fullshop_bacon_ovos_bot = fullshopbaconeovos.FullShopBaconEOvosBot()
            
            self.fullshop_bacon_ovos_bot.window_name = self.emulator_config["window_name"]
            self.status_label.config(text="Status: Vendendo Bacon e Ovos...")

            if self.fullshop_bacon_ovos_bot.vender_bacon_e_ovos():
                self.status_label.config(text="Status: Bacon e Ovos vendidos com sucesso!")
                self.full_bacon_ovos_button.state(['!disabled'])
            else:
                self.status_label.config(text="Status: Erro ao vender Bacon e Ovos")
                self.full_bacon_ovos_button.state(['!disabled'])
        except Exception as e:
            self.status_label.config(text=f"Status: Erro - {str(e)}")
            self.full_bacon_ovos_button.state(['!disabled'])

    def start_clear_shop_thread(self):
        """Inicia o processo de limpeza da loja em uma thread separada"""
        # Validar se está na loja
        if stateManager.state_manager.get_current_state() != "Dentro da Loja":
            messagebox.showwarning("Aviso", "Por favor, entre na loja primeiro!")
            return

        if self.clear_shop_thread and self.clear_shop_thread.is_alive():
            messagebox.showwarning("Aviso", "Limpeza da loja já está em execução!")
            return

        self.clear_shop_button.state(['disabled'])
        self.status_label.config(text="Status: Iniciando limpeza da loja...")

        self.clear_shop_thread = threading.Thread(target=self.run_clear_shop)
        self.clear_shop_thread.daemon = True
        self.clear_shop_thread.start()

    def run_clear_shop(self):
        """Executa a funcionalidade de limpeza da loja"""
        try:
            if not hasattr(self, 'clear_shop_bot') or self.clear_shop_bot is None:
                self.clear_shop_bot = clearShop.ClearShopBot()
            # Atualiza o nome da janela
            self.clear_shop_bot.window_name = self.emulator_config["window_name"]
            self.status_label.config(text="Status: Verificando loja...")

            resultado = self.clear_shop_bot.check_shop()

            # Atualiza o status com o resultado
            self.status_label.config(text=f"Status: {resultado}")
            messagebox.showinfo("Resultado", resultado)

        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao limpar loja: {str(e)}")
            self.status_label.config(text="Status: Erro ao limpar loja")
        finally:
            self.clear_shop_button.state(['!disabled'])

    def save_emulator_settings(self):
        """Salva as configurações do emulador e atualiza os componentes"""
        window_name = self.emulator_name.get().strip()
        if not window_name:
            messagebox.showwarning("Aviso", "Nome da janela não pode estar vazio!")
            return
            
        # Atualiza a configuração
        self.emulator_config["window_name"] = window_name
        save_emulator_config(self.emulator_config)
        
        # Atualiza o state manager
        stateManager.state_manager.window_name = window_name
        
        # Reinicia o monitoramento de estado
        stateManager.state_manager.stop()
        stateManager.state_manager.start()
        
        messagebox.showinfo("Sucesso", "Configuração do emulador atualizada!")

    def on_closing(self):
        """Função chamada quando a janela é fechada"""
        try:
            if hasattr(self, 'connection_manager') and self.connection_manager and self.connection_manager.is_connected:
                messagebox.showwarning("Aviso", "Por favor, clique no botão 'Desconectar' antes de fechar o programa!")
                return False  # Impede o fechamento do programa
        except Exception as e:
            print(f"Erro ao verificar conexão: {str(e)}")
    
        # Se não estiver conectado, fecha normalmente
        try:
            stateManager.state_manager.stop()
        except Exception:
            pass
    
        self.root.destroy()
        return True

    def open_selected_app(self):
        """Abre o aplicativo selecionado via ADB"""
        app_name = self.app_var.get()
        if not app_name:
            messagebox.showwarning("Aviso", "Por favor, selecione um aplicativo!")
            return

        self.open_app_button.state(['disabled'])
        try:
            success, message = self.open_agent.open_app(app_name)
            if success:
                # Cria uma janela de mensagem personalizada
                success_window = tk.Toplevel(self.root)
                success_window.title("Sucesso")
                success_window.geometry("300x120")
                success_window.configure(bg='#1a1a1a')
                success_window.resizable(False, False)
                
                # Centraliza a janela
                success_window.transient(self.root)
                success_window.grab_set()
                x = self.root.winfo_x() + (self.root.winfo_width() // 2) - (300 // 2)
                y = self.root.winfo_y() + (self.root.winfo_height() // 2) - (120 // 2)
                success_window.geometry(f"+{x}+{y}")
                
                # Frame para conteúdo
                content_frame = ttk.Frame(success_window)
                content_frame.pack(expand=True, fill='both', padx=10, pady=10)
                
                # Mensagem
                message_label = ttk.Label(
                    content_frame,
                    text=message,
                    font=('Arial', 11),
                    foreground='#90EE90',  # Verde claro
                    background='#1a1a1a',
                    wraplength=280
                )
                message_label.pack(pady=(10, 20))
                
                # Botão OK
                ok_button = ttk.Button(
                    content_frame,
                    text="OK",
                    command=success_window.destroy,
                    style='Accent.TButton'
                )
                ok_button.pack()
                
                # Fecha a janela após 1 segundo
                success_window.after(1000, success_window.destroy)
            else:
                messagebox.showerror("Erro", message)
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao abrir aplicativo: {str(e)}")
        finally:
            self.open_app_button.state(['!disabled'])

    def copy_to_clipboard(self, text):
        """Copia o texto para a área de transferência"""
        if "%item%" in text and "XX" in text:
            self.process_coins_message(text)
        else:
            self.root.clipboard_clear()
            self.root.clipboard_append(text)

    def create_tooltip(self, widget, text):
        """Cria um tooltip para o widget"""
        tooltip = tk.Toplevel(widget)
        tooltip.withdraw()
        tooltip.overrideredirect(True)
        
        # Usando tk.Label em vez de ttk.Label para suportar emojis coloridos
        label = tk.Label(
            tooltip,
            text=text,
            justify='left',
            relief='solid',
            borderwidth=1,
            wraplength=300,
            font=('Segoe UI Emoji', 10),  # Fonte que suporta emojis coloridos
            bg='lightyellow',
            fg='black',
            padx=5,
            pady=5
        )
        label.grid(row=0, column=0)

        def show_tooltip(event=None):
            tooltip.deiconify()
            # Posicionar o tooltip abaixo do widget
            x = widget.winfo_rootx()
            y = widget.winfo_rooty() + widget.winfo_height() + 5
            tooltip.geometry(f"+{x}+{y}")
            
        def hide_tooltip(event=None):
            tooltip.withdraw()

        widget.bind('<Enter>', show_tooltip)
        widget.bind('<Leave>', hide_tooltip)
        
        # Estilo para o tooltip
        self.style.configure('Tooltip.TLabel', 
                           background='lightyellow',
                           foreground='black',
                           padding=3)

    def get_item_by_level(self, level):
        """Retorna o item apropriado baseado no nível"""
        if level >= 40:
            return "*Anéis de diamante*"
        elif level >= 21:
            return "*Calças de lã*"
        elif level >= 11:
            return "*Bacon e Ovos*"
        return "*Item não disponível para este nível*"

    def process_coins_message(self, template_msg):
        """Processa a mensagem de moedas com input de nível"""
        try:
            # Criar uma janela de diálogo para input
            dialog = tk.Toplevel(self.root)
            dialog.title("Nível do Jogador")
            dialog.geometry("300x150")
            dialog.transient(self.root)
            dialog.grab_set()

            # Centralizar a janela
            dialog.geometry("+%d+%d" % (
                self.root.winfo_rootx() + self.root.winfo_width()/2 - 150,
                self.root.winfo_rooty() + self.root.winfo_height()/2 - 75))

            # Label
            tk.Label(dialog, text="Digite o nível do jogador:", pady=10).pack()

            # Entry
            entry = tk.Entry(dialog, width=10)
            entry.pack(pady=5)
            entry.focus_set()

            def process():
                try:
                    level = int(entry.get())
                    item = self.get_item_by_level(level)
                    final_msg = template_msg.replace("XX", str(level)).replace("%item%", item)
                    self.root.clipboard_clear()
                    self.root.clipboard_append(final_msg)
                    dialog.destroy()
                except ValueError:
                    tk.messagebox.showerror("Erro", "Por favor, digite um número válido!")

            # Botões
            button_frame = tk.Frame(dialog)
            button_frame.pack(pady=20)

            tk.Button(button_frame, text="OK", command=process, width=10).pack(side=tk.LEFT, padx=5)
            tk.Button(button_frame, text="Cancelar", command=dialog.destroy, width=10).pack(side=tk.LEFT, padx=5)

            # Bind Enter key
            entry.bind('<Return>', lambda e: process())
            dialog.bind('<Escape>', lambda e: dialog.destroy())

        except Exception as e:
            print(f"Erro ao processar mensagem: {e}")

    def load_category_colors(self):
        """Carrega as cores das categorias do arquivo de configuração"""
        try:
            with open(os.path.join(BASE_PATH, 'cfg', 'category_colors.json'), 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}

    def save_category_colors(self):
        """Salva as cores das categorias no arquivo de configuração"""
        with open(os.path.join(BASE_PATH, 'cfg', 'category_colors.json'), 'w', encoding='utf-8') as f:
            json.dump(self.category_colors, f, indent=4)

    def change_category_color(self, category, frame):
        """Abre o seletor de cor e muda a cor da categoria"""
        color = colorchooser.askcolor(title="Escolha a cor para " + category)[1]
        if color:
            self.category_colors[category] = color
            # Atualizar o estilo do LabelFrame
            style_name = f"Custom.{category}.TLabelframe.Label"
            self.style.configure(style_name, foreground=color)
            frame.configure(style=f"Custom.{category}.TLabelframe")
            self.save_category_colors()

    def create_category_context_menu(self, category, label):
        """Cria menu de contexto para a categoria"""
        menu = tk.Menu(self.root, tearoff=0)
        menu.add_command(label="Mudar cor", command=lambda: self.change_category_color(category, label))
        
        def show_menu(event):
            menu.post(event.x_root, event.y_root)
            
        label.bind("<Button-3>", show_menu)  # Botão direito do mouse

    def toggle_box10(self):
        """Ativa/desativa a box10"""
        is_enabled = self.see_loja.toggle_box10()
        self.toggle_box10_button.configure(text=f"Box10: {'ON' if is_enabled else 'OFF'}")
        # Atualiza a cor da box10 imediatamente para laranja quando desativada
        self.box_canvases["box10"].configure(bg="orange" if not is_enabled else self.box_canvases["box10"].cget("bg"))

    def sync_shop(self):
        """Sincroniza o estado da loja"""
        result = self.see_loja.sync_shop()
        if "Aviso:" in result:
            messagebox.showwarning("Aviso", result)
        elif "Erro:" in result:
            messagebox.showerror("Erro", result)
        else:
            # Atualiza as cores das boxes
            self.update_box_colors()
            messagebox.showinfo("Sucesso", result)

    def update_box_colors(self):
        """Atualiza as cores das boxes baseado no status"""
        status = self.see_loja.get_box_status()
        for box_name, canvas in self.box_canvases.items():
            color = status[box_name]
            canvas.configure(bg=color)

    def on_box_click(self, box_number):
        """Callback quando uma box é clicada"""
        if stateManager.state_manager.get_current_state() != "Dentro da Loja":
            messagebox.showwarning("Aviso", "Você precisa estar dentro da loja para configurar uma box!")
            return
            
        print(f"Box {box_number} clicada")
        # Cria e mostra a janela de configuração da box
        box_config = onlyoneBox.OnlyOneBox(box_number)
        box_config.show()

    def connect_to_site(self):
        """Função para conectar ao site"""
        admin = self.admin_var.get()
        if admin:
            try:
                self.connection_manager = ConnectionManager('http://89.117.32.205:8000', admin)
                response = self.connection_manager.connect()
                if response:
                    self.connection_status.configure(text="Status: Conectado")
                    self.connect_button.configure(state="disabled")
                    self.disconnect_button.configure(state="normal")
                    messagebox.showinfo("Sucesso", "Conectado com sucesso!")
                    
                    # Inicia a thread de atualização de estado
                    self.stop_state_update = False
                    self.state_update_thread = threading.Thread(target=self._update_state_loop)
                    self.state_update_thread.daemon = True
                    self.state_update_thread.start()
                else:
                    # Verifica se o admin já está conectado
                    connected_admins = self.connection_manager.get_status().get('connected_admins', [])
                    if admin in [a["admin"] for a in connected_admins]:
                        messagebox.showerror("Erro", f"O admin '{admin}' já está conectado em outro local!\nDesconecte do outro local antes de tentar conectar aqui.")
                    else:
                        messagebox.showerror("Erro", "Falha ao conectar")
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao conectar: {str(e)}")
        else:
            messagebox.showwarning("Aviso", "Selecione um admin antes de conectar!")

    def disconnect_from_site(self):
        """Função para desconectar do site"""
        if self.connection_manager:
            try:
                # Para a thread de atualização de estado
                self.stop_state_update = True
                if self.state_update_thread:
                    self.state_update_thread.join(timeout=2)
                
                response = self.connection_manager.disconnect()
                if response:
                    self.connection_status.configure(text="Status: Desconectado")
                    self.connect_button.configure(state="normal")
                    self.disconnect_button.configure(state="disabled")
                    messagebox.showinfo("Sucesso", "Desconectado com sucesso!")
                else:
                    messagebox.showerror("Erro", "Falha ao desconectar")
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao desconectar: {str(e)}")

    def check_site_status(self):
        """Função para verificar o status do site"""
        try:
            if self.connection_manager:
                status = self.connection_manager.get_status()
                if status:
                    messagebox.showinfo("Status", "Conectado ao site")
                else:
                    messagebox.showinfo("Status", "Desconectado do site")
            else:
                messagebox.showinfo("Status", "Desconectado do site")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao verificar status: {str(e)}")

    def _update_state_loop(self):
        """Loop para atualizar o estado do bot no servidor"""
        while not self.stop_state_update:
            if self.connection_manager:
                self.connection_manager.update_state()
            time.sleep(5)  # Atualiza a cada 5 segundos

def main():
    root = tk.Tk()
    app = HayDayGUI(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()

if __name__ == "__main__":
    main()