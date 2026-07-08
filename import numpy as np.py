# -*- coding: utf-8 -*-
"""
POLOTTO ENGENHARIA — Cálculo Estrutural (NBR 6118)
Ponto de entrada do app: navegação entre Vigas e Pilares.

(O nome deste arquivo é histórico — é o arquivo principal configurado no
deploy do Streamlit Cloud. As páginas ficam em pagina_vigas.py e
pagina_pilar.py; os motores de cálculo em motor_viga.py e motor_pilar.py.)
"""
import importlib
import sys

import streamlit as st

# Recarrega os módulos auxiliares do disco a cada execução. Evita que o
# Streamlit Cloud fique preso numa versão antiga em cache de um módulo
# importado (motor_viga/motor_pilar/ui_comum) após um deploy que muda ao
# mesmo tempo um módulo e uma página — causa comum de ImportError/AttributeError.
for _m in ("ui_comum", "motor_viga", "motor_pilar", "motor_laje"):
    if _m in sys.modules:
        try:
            importlib.reload(sys.modules[_m])
        except Exception:
            pass

st.set_page_config(page_title="Polotto Engenharia — Cálculo Estrutural",
                   page_icon="🏗️", layout="centered")

_paginas = [
    st.Page("pagina_vigas.py", title="Vigas", icon="🏗️", default=True),
    st.Page("pagina_pilar.py", title="Pilares", icon="🏛️"),
    st.Page("pagina_lajes.py", title="Lajes", icon="🧱"),
    st.Page("pagina_pilar_previo.py", title="Pilares Prévios", icon="🏠"),
]

try:
    nav = st.navigation(_paginas, position="top")
except TypeError:  # versões antigas do Streamlit sem position="top"
    nav = st.navigation(_paginas)
nav.run()
