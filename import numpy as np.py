# -*- coding: utf-8 -*-
"""
POLOTTO ENGENHARIA — Cálculo Estrutural (NBR 6118)
Ponto de entrada do app: navegação entre Vigas e Pilares.

(O nome deste arquivo é histórico — é o arquivo principal configurado no
deploy do Streamlit Cloud. As páginas ficam em pagina_vigas.py e
pagina_pilar.py; os motores de cálculo em motor_viga.py e motor_pilar.py.)
"""
import streamlit as st

# (Removido o laço de importlib.reload por execução: no Streamlit Cloud cada
# deploy já sobe um processo NOVO com o código fresco, então recarregar módulos
# a cada rerun era desnecessário e — no Python 3.14 — corrompia módulos
# interdependentes, causando "cannot import name ... from 'ui_comum'".)

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
except TypeError:  # versões antigas do Streamlit sem position="top"
    nav = st.navigation(_paginas)
nav.run()
