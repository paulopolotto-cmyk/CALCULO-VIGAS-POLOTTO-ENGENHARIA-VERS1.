# -*- coding: utf-8 -*-
"""
POLOTTO ENGENHARIA — Cálculo Estrutural (NBR 6118)
Ponto de entrada usado no EXECUTÁVEL (.exe). Conteúdo idêntico ao arquivo
principal do deploy web ("import numpy as np.py"), só com nome sem espaços.
"""
import importlib
import sys

import streamlit as st

for _m in ("ui_comum", "motor_viga", "motor_pilar", "motor_laje", "editor_lancamento",
           "desenhos_viga", "desenhos_pilar", "calc_projeto", "calc_laje_projeto",
           "relatorio_pdf"):
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
    st.Page("pagina_projeto_completo.py", title="Projeto Completo", icon="📐"),
]

try:
    nav = st.navigation(_paginas, position="top")
except TypeError:
    nav = st.navigation(_paginas)
nav.run()
