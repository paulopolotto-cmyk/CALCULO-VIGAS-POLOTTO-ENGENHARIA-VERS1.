# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all
from PyInstaller.utils.hooks import copy_metadata

datas = [('app_polotto.py', '.'), ('pagina_vigas.py', '.'), ('pagina_pilar.py', '.'), ('pagina_pilar_previo.py', '.'), ('pagina_lajes.py', '.'), ('pagina_projeto_completo.py', '.'), ('editor_lancamento.py', '.'), ('calc_projeto.py', '.'), ('editor_template.html', '.'), ('motor_viga.py', '.'), ('motor_pilar.py', '.'), ('motor_laje.py', '.'), ('ui_comum.py', '.'), ('assets', 'assets'), ('.streamlit', '.streamlit')]
binaries = []
hiddenimports = []
datas += copy_metadata('streamlit')
tmp_ret = collect_all('streamlit')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]


a = Analysis(
    ['polotto_launcher.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='PolottoEngenharia',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
