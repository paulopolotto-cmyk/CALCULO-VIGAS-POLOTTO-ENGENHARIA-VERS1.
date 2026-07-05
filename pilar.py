# -*- coding: utf-8 -*-
"""
Atalho para rodar SÓ a página de pilares:  streamlit run pilar.py
(No app principal, os pilares estão na navegação do arquivo de entrada.)
"""
import pathlib
import runpy

import streamlit as st

st.set_page_config(page_title="Polotto Engenharia — Pilares",
                   page_icon="🏛️", layout="centered")

runpy.run_path(str(pathlib.Path(__file__).with_name("pagina_pilar.py")),
               run_name="__main__")
