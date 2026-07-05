# -*- coding: utf-8 -*-
"""Identidade visual compartilhada dos apps Polotto (vigas e pilares)."""
import streamlit as st

# paleta "azul engenharia"
NAVY = "#1E3A8A"
NAVY_ESC = "#16265B"
AMBAR = "#B45309"
VERMELHO = "#B91C1C"
VERDE = "#15803D"
CINZA_TXT = "#334155"
CONCRETO = "#CBD5E1"

_CSS = """
<style>
/* esconde os steppers +/- dos number_inputs (melhor no touch) */
[data-testid="stNumberInput"] button { display: none; }
[data-testid="stNumberInput"] input { font-weight: 600; }

/* cabeçalho da marca */
.pol-header {
    background: linear-gradient(135deg, #16265B, #1E3A8A 55%, #24479E);
    color: #fff; border-radius: 14px; padding: 20px 22px 18px;
    margin-bottom: 4px;
}
.pol-header .eyebrow {
    text-transform: uppercase; letter-spacing: .14em; font-size: .72rem;
    color: #F0C879; font-weight: 700; margin-bottom: 2px;
}
.pol-header h1 { font-size: 1.35rem; line-height: 1.3; margin: 0; color: #fff; }
.pol-header .sub { color: #C9D6F5; font-size: .85rem; margin-top: 4px; }

/* título de seção */
.pol-sec {
    display: flex; align-items: center; gap: 8px;
    font-weight: 700; color: #1E3A8A; font-size: 1.02rem;
    margin: 6px 0 2px;
}
.pol-sec .num {
    background: #1E3A8A; color: #fff; border-radius: 999px;
    width: 24px; height: 24px; display: inline-flex;
    align-items: center; justify-content: center; font-size: .8rem;
}

/* linha de tramo na lista */
.pol-tramo {
    background: #fff; border: 1px solid #DDE3EC; border-radius: 10px;
    padding: 8px 12px; font-size: .9rem; line-height: 1.5;
}

/* botões */
div.stButton > button, div[data-testid="stFormSubmitButton"] > button {
    border-radius: 10px; font-weight: 700; min-height: 46px;
}

/* dataframes ocupam a largura toda */
[data-testid="stDataFrame"] { width: 100%; }
</style>
"""


def aplicar_estilo():
    st.markdown(_CSS, unsafe_allow_html=True)


def header(titulo, subtitulo):
    st.markdown(f"""
<div class="pol-header">
  <div class="eyebrow">Polotto Engenharia</div>
  <h1>{titulo}</h1>
  <div class="sub">{subtitulo}</div>
</div>
""", unsafe_allow_html=True)


def sec(num, titulo):
    st.markdown(f'<div class="pol-sec"><span class="num">{num}</span>'
                f'{titulo}</div>', unsafe_allow_html=True)


def rodape(texto):
    st.caption(texto)
