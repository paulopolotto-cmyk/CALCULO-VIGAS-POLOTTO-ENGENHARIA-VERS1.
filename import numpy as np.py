# -*- coding: utf-8 -*-
"""
POLOTTO ENGENHARIA — Cálculo Estrutural (NBR 6118)
Ponto de entrada do app: navegação entre Vigas e Pilares.

(O nome deste arquivo é histórico — é o arquivo principal configurado no
deploy do Streamlit Cloud. As páginas ficam em pagina_vigas.py e
pagina_pilar.py; os motores de cálculo em motor_viga.py e motor_pilar.py.)
"""
import streamlit as st

st.set_page_config(page_title="Polotto Engenharia — Cálculo Estrutural",
                   page_icon="🏗️", layout="centered")

_paginas = [
    st.Page("pagina_vigas.py", title="Vigas", icon="🏗️", default=True),
    st.Page("pagina_pilar.py", title="Pilares", icon="🏛️"),
]

try:
    nav = st.navigation(_paginas, position="top")
except TypeError:  # versões antigas do Streamlit sem position="top"
    nav = st.navigation(_paginas)
nav.run()
