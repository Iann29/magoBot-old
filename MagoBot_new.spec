# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all

# Coleta todos os dados e dependências necessários
datas = [
    ('cfg', 'cfg'),  # Pasta de configurações
    ('dataset', 'dataset'),  # Pasta de datasets
    ('API', 'API'),  # Pasta da API
    ('*.json', '.'),  # Arquivos JSON
    ('*.py', '.'),  # Arquivos Python
]

# Dependências binárias
binaries = []

# Imports ocultos necessários
hiddenimports = [
    'cv2',
    'numpy',
    'pygetwindow',
    'pyautogui',
    'PIL',
    'PIL._tkinter_finder',
    'requests',
    'keyboard',
    'json',
    'threading',
    'tkinter',
    'tkinter.ttk',
    'tkinter.messagebox',
    'tkinter.colorchooser'
]

# Coleta todas as dependências do OpenCV
tmp_ret = collect_all('cv2')
datas += tmp_ret[0]
binaries += tmp_ret[1]
hiddenimports += tmp_ret[2]

# Configuração principal do Analysis
a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=2  # Otimização máxima
)

# Configuração do PYZ (arquivo ZIP Python)
pyz = PYZ(a.pure)

# Configuração do executável
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='MagoBot',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    version='version_info.txt',
    icon=['dataset\\gato.ico'],
    uac_admin=True  # Solicita privilégios de administrador
)
