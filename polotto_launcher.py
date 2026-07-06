# -*- coding: utf-8 -*-
"""
Lançador do executável Polotto Engenharia.
Ao dar dois cliques no .exe, inicia o servidor Streamlit local e abre o
programa no navegador padrão. Funciona offline (Windows).
"""
import os
import sys

# Garante que as dependências pesadas entrem no bundle do PyInstaller
# (o analisador precisa "ver" estes imports).
import numpy            # noqa: F401
import matplotlib       # noqa: F401
import matplotlib.pyplot  # noqa: F401
import streamlit        # noqa: F401
import motor_viga       # noqa: F401
import motor_pilar      # noqa: F401
import ui_comum         # noqa: F401


def _base_dir():
    # Em .exe (PyInstaller onefile) os arquivos ficam em sys._MEIPASS.
    return getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))


def main():
    base = _base_dir()
    # o diretório dos arquivos precisa estar no sys.path e ser o CWD, para o
    # st.Page("pagina_vigas.py") e os imports (motor_viga, ui_comum) acharem
    # os arquivos.
    if base not in sys.path:
        sys.path.insert(0, base)
    os.chdir(base)

    app = os.path.join(base, "app_polotto.py")
    from streamlit.web import cli as stcli
    sys.argv = [
        "streamlit", "run", app,
        "--server.port=8501",
        "--server.address=localhost",
        "--server.headless=false",          # abre o navegador
        "--browser.gatherUsageStats=false",
        "--global.developmentMode=false",
    ]
    sys.exit(stcli.main())


if __name__ == "__main__":
    main()
