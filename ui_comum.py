# -*- coding: utf-8 -*-
"""Identidade visual compartilhada dos apps Polotto (vigas e pilares)."""
import base64 as _b64
import html as _html
import io as _io

import streamlit as st
import streamlit.components.v1 as components

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

/* ===== NAVEGAÇÃO: esconde a barra padrão (usamos o seletor CALCULAR) ===== */
[data-testid="stNavLink"] { display: none !important; }

/* rótulos "CALCULAR" e perguntas em destaque */
.pol-calc-label {
    font-weight: 800; color: #1E3A8A; font-size: 1.08rem; margin: 4px 0 6px;
}
.pol-pergunta {
    font-weight: 800; color: #1E3A8A; font-size: 1.06rem; margin: 12px 0 3px;
}

/* seletor CALCULAR (Vigas / Pilares) — botões do MESMO tamanho, lado a lado */
.pol-pg-ativo {
    background: linear-gradient(135deg, #F6C86B, #E8A33D);
    color: #16265B !important; font-weight: 800; font-size: 1.2rem;
    padding: 13px 10px; border-radius: 12px;
    box-shadow: 0 3px 10px rgba(180,83,9,.32);
    min-height: 54px; box-sizing: border-box;
    display: flex; align-items: center; justify-content: center;
}
[data-testid="stPageLink"] { width: 100%; }
[data-testid="stPageLink"] a {
    background: #EEF3FC; border: 2px solid #1E3A8A; border-radius: 12px;
    padding: 13px 10px !important; min-height: 54px;
    width: 100%; box-sizing: border-box;
    display: flex; align-items: center; justify-content: center;
    transition: all .12s ease;
}
[data-testid="stPageLink"] a:hover {
    background: #DCE6FA; transform: translateY(-1px);
}
[data-testid="stPageLink"] a * {
    color: #1E3A8A !important; font-size: 1.2rem !important;
    font-weight: 800 !important;
}
/* mantém os 2 botões (Vigas | Pilares) LADO A LADO mesmo no celular.
   Escopo: só a linha que contém um stPageLink (o seletor CALCULAR),
   sem afetar as colunas dos campos de entrada. */
[data-testid="stHorizontalBlock"]:has([data-testid="stPageLink"]) {
    flex-wrap: nowrap !important; gap: 10px !important;
}
[data-testid="stHorizontalBlock"]:has([data-testid="stPageLink"])
    > [data-testid="stColumn"] {
    min-width: 0 !important; flex: 1 1 0 !important; width: 50% !important;
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
    display: flex; align-items: center; gap: 9px;
    font-weight: 800; color: #1E3A8A;
    font-size: clamp(1.08rem, 4.2vw, 1.22rem); white-space: nowrap;
    margin: 10px 0 4px;
}
.pol-sec .num {
    background: #1E3A8A; color: #fff; border-radius: 999px;
    min-width: 26px; height: 26px; display: inline-flex;
    align-items: center; justify-content: center; font-size: .85rem;
    flex: 0 0 auto;
}
/* seção de ENTRADA em destaque (barra âmbar/azul) */
.pol-sec.destaque {
    background: linear-gradient(135deg, #16265B, #1E3A8A 60%, #24479E);
    color: #fff; padding: 10px 14px; border-radius: 11px;
    margin: 14px 0 8px; box-shadow: 0 2px 8px rgba(30,58,138,.22);
}
.pol-sec.destaque .num {
    background: #F0C879; color: #16265B;
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

/* ===== LEITURA REFORÇADA (negrito e um pouco maior, bom no celular) ===== */
[data-testid="stMarkdownContainer"], [data-testid="stMarkdownContainer"] *,
[data-testid="stWidgetLabel"], [data-testid="stWidgetLabel"] *,
[data-testid="stCaptionContainer"], [data-testid="stCaptionContainer"] * {
    font-weight: 700 !important;
}
[data-testid="stWidgetLabel"] p { font-size: 1.02rem !important; }
[data-testid="stMetricValue"] { font-weight: 800 !important; }
[data-testid="stMetricLabel"] * { font-weight: 700 !important; }
/* números digitados: negrito e maiores */
[data-testid="stNumberInput"] input, [data-testid="stTextInput"] input,
[data-baseweb="select"] div {
    font-weight: 800 !important; font-size: 1.08rem !important;
}

/* ===== SELETOR DE UNIDADE (kN / kgf): maior e negrito ===== */
[data-testid="stRadio"] [role="radiogroup"] { gap: 10px; }
[data-testid="stRadio"] [role="radiogroup"] label {
    background: #EEF3FC; border: 2px solid #C9D6F5; border-radius: 10px;
    padding: 8px 14px;
}
[data-testid="stRadio"] [role="radiogroup"] label p,
[data-testid="stRadio"] [role="radiogroup"] label div {
    font-size: 1.12rem !important; font-weight: 800 !important;
    color: #1E3A8A !important;
}
/* opção selecionada em ÂMBAR (destaque) */
[data-testid="stRadio"] [role="radiogroup"] label:has(input:checked) {
    background: linear-gradient(135deg, #F6C86B, #E8A33D) !important;
    border-color: #E8A33D !important;
    box-shadow: 0 2px 8px rgba(180,83,9,.28);
}
[data-testid="stRadio"] [role="radiogroup"] label:has(input:checked) p,
[data-testid="stRadio"] [role="radiogroup"] label:has(input:checked) div {
    color: #16265B !important;
}

/* ===== BOTÕES DE AÇÃO (Inserir / Salvar) grandes e em ÂMBAR ===== */
[data-testid="stFormSubmitButton"] button {
    background: linear-gradient(135deg, #E8A33D, #B45309) !important;
    color: #ffffff !important; border: none !important;
    font-size: 1.16rem !important; font-weight: 800 !important;
    min-height: 54px !important; letter-spacing: .01em;
    box-shadow: 0 3px 10px rgba(180,83,9,.30);
}
[data-testid="stFormSubmitButton"] button:hover { filter: brightness(1.07); }
/* botão primário CALCULAR: maior e mais forte */
div.stButton > button[kind="primary"] {
    font-size: 1.2rem !important; font-weight: 800 !important;
    min-height: 56px !important;
}

/* ===== TABELAS DE RESULTADO (HTML, negrito + rolagem horizontal) ===== */
.pol-tab-wrap {
    overflow-x: auto; -webkit-overflow-scrolling: touch;
    margin: 4px 0 10px; border: 1px solid #DDE3EC; border-radius: 10px;
}
.pol-tab { border-collapse: collapse; width: 100%; }
.pol-tab th {
    background: #1E3A8A; color: #fff !important; font-weight: 800;
    font-size: .95rem; padding: 9px 11px; text-align: left;
    white-space: nowrap;
}
.pol-tab td {
    border-top: 1px solid #E4E9F1; padding: 8px 11px;
    font-weight: 700; color: #14213D; font-size: .98rem; white-space: nowrap;
}
.pol-tab tbody tr:nth-child(even) td { background: #F4F6FA; }

/* ===== FIGURAS DE RESULTADO (rolagem horizontal p/ vigas com muitos vãos) */
.pol-fig-wrap {
    overflow-x: auto; -webkit-overflow-scrolling: touch;
    border: 1px solid #DDE3EC; border-radius: 10px; background: #fff;
    margin: 4px 0 8px;
}
.pol-fig-wrap img { display: block; height: auto; }
.pol-fig-wrap.wide img { margin: 0 auto; }
</style>
"""


_ZOOM_JS = """
<script>
(function () {
  var ALVO = 'width=device-width, initial-scale=1, minimum-scale=1, ' +
             'maximum-scale=5, user-scalable=yes';
  function libera() {
    try {
      var doc = (window.parent || window).document;
      var vp = doc.querySelector('meta[name="viewport"]');
      if (!vp) { vp = doc.createElement('meta'); vp.setAttribute('name',
                 'viewport'); doc.getElementsByTagName('head')[0]
                 .appendChild(vp); }
      if (vp.getAttribute('content') !== ALVO) {
        vp.setAttribute('content', ALVO);
      }
      doc.documentElement.style.touchAction = 'pan-x pan-y pinch-zoom';
      doc.body.style.touchAction = 'pan-x pan-y pinch-zoom';
    } catch (e) {}
  }
  libera();
  try {
    var d = (window.parent || window).document;
    new MutationObserver(libera).observe(d.head,
      { childList: true, subtree: true, attributes: true });
  } catch (e) {}
  var n = 0, iv = setInterval(function () {
    libera(); if (++n > 12) clearInterval(iv);
  }, 500);
})();
</script>
"""


def aplicar_estilo():
    st.markdown(_CSS, unsafe_allow_html=True)
    # libera o zoom de pinça no celular (Streamlit bloqueia por padrão)
    components.html(_ZOOM_JS, height=0)


def mostrar_figura(fig, dpi=170):
    """Mostra uma figura matplotlib com rolagem horizontal.

    Se a figura for larga (> 7,6 pol — viga com muitos vãos), é exibida no
    tamanho natural dentro de um contêiner rolável, para ficar legível no
    celular. Caso contrário, ocupa a largura disponível.
    Retorna os bytes PNG (para reuso em botão de download).
    """
    import matplotlib.pyplot as plt
    buf = _io.BytesIO()
    fig.savefig(buf, format="png", dpi=dpi, bbox_inches="tight")
    plt.close(fig)
    dados = buf.getvalue()
    b64 = _b64.b64encode(dados).decode()
    largura_pol = fig.get_size_inches()[0]
    if largura_pol > 7.6:
        style = f"width:{int(largura_pol * 96)}px;max-width:none"
        cls = "pol-fig-wrap wide"
    else:
        style = "width:100%"
        cls = "pol-fig-wrap"
    st.markdown(
        f'<div class="{cls}"><img alt="resultado" '
        f'src="data:image/png;base64,{b64}" style="{style}"></div>',
        unsafe_allow_html=True)
    return dados


def tabela(rows):
    """Renderiza uma tabela HTML (negrito, cabeçalho azul, rolagem horizontal).

    rows: lista de dicts {coluna: valor}. Substitui st.dataframe para permitir
    negrito e melhor leitura no celular.
    """
    if not rows:
        return
    cols = list(rows[0].keys())
    th = "".join(f"<th>{_html.escape(str(c))}</th>" for c in cols)
    corpo = ""
    for r in rows:
        tds = "".join(f"<td>{_html.escape(str(r.get(c, '')))}</td>"
                      for c in cols)
        corpo += f"<tr>{tds}</tr>"
    st.markdown(
        f'<div class="pol-tab-wrap"><table class="pol-tab"><thead><tr>{th}'
        f'</tr></thead><tbody>{corpo}</tbody></table></div>',
        unsafe_allow_html=True)


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


def sec(num, titulo, destaque=False):
    cls = "pol-sec destaque" if destaque else "pol-sec"
    st.markdown(f'<div class="{cls}"><span class="num">{num}</span>'
                f'{titulo}</div>', unsafe_allow_html=True)


def rodape(texto):
    st.caption(texto)


# 1 kN = 101,9716 kgf  (1 kgf = 9,80665 N)
KGF_POR_KN = 101.9716


def seletor_pagina(atual):
    """Seletor destacado CALCULAR → Vigas / Pilares (no corpo da página).

    atual: 'vigas' ou 'pilar' — define qual botão fica em âmbar (ativo).
    """
    st.markdown('<div class="pol-calc-label">Calcular — Vigas ou Pilares '
                '— clique abaixo:</div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        if atual == "vigas":
            st.markdown('<div class="pol-pg-ativo">🏗️ Vigas</div>',
                        unsafe_allow_html=True)
        else:
            st.page_link("pagina_vigas.py", label="Vigas", icon="🏗️")
    with c2:
        if atual == "pilar":
            st.markdown('<div class="pol-pg-ativo">🏛️ Pilares</div>',
                        unsafe_allow_html=True)
        else:
            st.page_link("pagina_pilar.py", label="Pilares", icon="🏛️")


def seletor_unidade(key="unidade_forca"):
    """Seletor de sistema de unidades de força.

    Retorna (fu, un_f, un_fm):
      fu    = fator para converter kN -> unidade escolhida (mostrar = valor_kN * fu)
      un_f  = rótulo da força ('kN' ou 'kgf')
      un_fm = rótulo da carga distribuída ('kN/m' ou 'kgf/m')
    O cálculo interno é sempre em kN; a conversão é só na tela.
    """
    st.markdown('<div class="pol-pergunta">Qual unidade de carga você quer '
                'usar?</div>', unsafe_allow_html=True)
    op = st.radio("Unidade de força", ["kN · kN/m", "kgf · kgf/m"],
                  index=1, horizontal=True, key=key,
                  label_visibility="collapsed",
                  help="Escolha o sistema de unidades das cargas e dos "
                       "esforços. O cálculo é o mesmo; muda só a exibição.")
    if op.startswith("kgf"):
        return KGF_POR_KN, "kgf", "kgf/m"
    return 1.0, "kN", "kN/m"
