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

/* ===== NAVEGAÇÃO DO TOPO (Vigas / Pilares) EM DESTAQUE ===== */
[data-testid="stNavLink"] {
    padding: 10px 22px !important;
    margin: 4px 6px !important;
    border-radius: 12px !important;
    border: 2px solid #C9D6F5 !important;
    background: #EEF3FC !important;
    transition: all .12s ease;
}
[data-testid="stNavLink"] * {
    font-size: 1.12rem !important;
    font-weight: 800 !important;
    color: #1E3A8A !important;
}
[data-testid="stNavLink"]:hover {
    background: #DCE6FA !important;
    border-color: #1E3A8A !important;
    transform: translateY(-1px);
}
/* aba ativa: fundo azul cheio */
[data-testid="stNavLink"][aria-current="page"],
[data-testid="stNavLink"].active {
    background: linear-gradient(135deg, #1E3A8A, #24479E) !important;
    border-color: #16265B !important;
    box-shadow: 0 3px 10px rgba(30,58,138,.35);
}
[data-testid="stNavLink"][aria-current="page"] *,
[data-testid="stNavLink"].active * {
    color: #fff !important;
}

/* cabeçalho da marca */
.pol-header {
    background: linear-gradient(135deg, #16265B, #1E3A8A 55%, #24479E);
    color: #fff; border-radius: 14px; padding: 22px 22px 18px;
    margin-bottom: 4px;
}
a.pol-marca-link { text-decoration: none !important; display: inline-block; }
a.pol-marca-link:hover .marca-txt { color: #F0C879; }
a.pol-marca-link:hover .logo-badge { transform: scale(1.05); }
a.pol-marca-link:hover .pol-site-hint {
    background: #F0C879; color: #16265B;
}
.pol-header .marca {
    display: flex; align-items: center; gap: 12px;
}
.pol-header .marca-txt .ext {
    font-size: .95rem; color: #F0C879; vertical-align: super;
    margin-left: 2px;
}
.pol-site-hint {
    display: inline-flex; align-items: center; gap: 5px;
    margin-top: 7px; padding: 3px 10px; border-radius: 999px;
    background: rgba(240,200,121,.16); border: 1px solid #F0C879;
    color: #F0C879; font-size: .74rem; font-weight: 700;
    letter-spacing: .02em; transition: all .12s ease;
}
.pol-header .logo-badge {
    background: linear-gradient(160deg, #F6C86B, #E8A33D);
    color: #16265B; font-weight: 900; border-radius: 10px;
    min-width: 46px; height: 46px; display: inline-flex;
    align-items: center; justify-content: center;
    font-size: 1.7rem; box-shadow: 0 2px 10px rgba(0,0,0,.28);
    transition: transform .12s ease;
}
.pol-header .marca-txt {
    font-size: clamp(1.45rem, 6vw, 1.9rem); font-weight: 800;
    letter-spacing: .05em; line-height: 1.1; color: #fff;
    text-transform: uppercase;
}
.pol-header .marca-txt em {
    font-style: normal; color: #F0C879;
}
.pol-header .divisor {
    height: 3px; width: 72px; border-radius: 99px;
    background: #F0C879; margin: 10px 0 10px;
}
.pol-header h1 {
    font-size: 1.08rem; line-height: 1.3; margin: 0;
    color: #DDE7FB; font-weight: 700;
}
.pol-header .sub { color: #A9BCE8; font-size: .82rem; margin-top: 3px; }

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
  <a class="pol-marca-link" href="https://polottoengenharia.com.br"
     target="_blank" rel="noopener" title="Abrir polottoengenharia.com.br">
    <div class="marca">
      <span class="logo-badge">P</span>
      <div>
        <span class="marca-txt">Polotto <em>Engenharia</em><span
          class="ext">&#8599;</span></span>
        <div class="pol-site-hint">&#127760; polottoengenharia.com.br
          &nbsp;·&nbsp; clique para visitar</div>
      </div>
    </div>
  </a>
  <div class="divisor"></div>
  <h1>{titulo}</h1>
  <div class="sub">{subtitulo}</div>
</div>
""", unsafe_allow_html=True)


def sec(num, titulo):
    st.markdown(f'<div class="pol-sec"><span class="num">{num}</span>'
                f'{titulo}</div>', unsafe_allow_html=True)


def rodape(texto):
    st.caption(texto)


# 1 kN = 101,9716 kgf  (1 kgf = 9,80665 N)
KGF_POR_KN = 101.9716


def seletor_unidade(key="unidade_forca"):
    """Seletor de sistema de unidades de força.

    Retorna (fu, un_f, un_fm):
      fu    = fator para converter kN -> unidade escolhida (mostrar = valor_kN * fu)
      un_f  = rótulo da força ('kN' ou 'kgf')
      un_fm = rótulo da carga distribuída ('kN/m' ou 'kgf/m')
    O cálculo interno é sempre em kN; a conversão é só na tela.
    """
    op = st.radio("Unidade de força", ["kN · kN/m", "kgf · kgf/m"],
                  horizontal=True, key=key,
                  help="Escolha o sistema de unidades das cargas e dos "
                       "esforços. O cálculo é o mesmo; muda só a exibição.")
    if op.startswith("kgf"):
        return KGF_POR_KN, "kgf", "kgf/m"
    return 1.0, "kN", "kN/m"
