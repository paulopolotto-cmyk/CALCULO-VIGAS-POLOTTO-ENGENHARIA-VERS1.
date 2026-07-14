# -*- coding: utf-8 -*-
"""Identidade visual compartilhada dos apps Polotto (vigas e pilares)."""
import base64 as _b64
import html as _html
import io as _io
import os as _os

import streamlit as st
import streamlit.components.v1 as components

# Fundo BRANCO em TODAS as figuras matplotlib do app (desenhos, plantas,
# diagramas). No modo escuro do celular, um fundo transparente/escuro sumia com
# o texto preto — forçar branco garante legibilidade em qualquer aparelho.
try:
    import matplotlib as _mpl
    _mpl.rcParams["figure.facecolor"] = "white"
    _mpl.rcParams["axes.facecolor"] = "white"
    _mpl.rcParams["savefig.facecolor"] = "white"
except Exception:
    pass

# Logo oficial Polotto (embutido como data-URI: funciona na web, no túnel e
# no .exe, sem depender de arquivo externo em runtime).
_LOGO_URI = None


def _logo_uri():
    global _LOGO_URI
    if _LOGO_URI is None:
        try:
            _p = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)),
                               "assets", "logo_polotto.png")
            with open(_p, "rb") as _f:
                _LOGO_URI = ("data:image/png;base64,"
                             + _b64.b64encode(_f.read()).decode("ascii"))
        except Exception:
            _LOGO_URI = ""      # cai no logo textual (fallback) se faltar
    return _LOGO_URI

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
/* ===== TRAVA o app em tema CLARO — o MODO ESCURO do celular escurecia o fundo
   e sumia com os textos escuros. Agora o fundo é sempre claro e o texto escuro
   fica legível em qualquer aparelho (Samsung/iPhone, claro ou escuro). Vale p/
   qualquer projeto. ===== */
:root, html { color-scheme: light only !important; }
html, body, .stApp,
[data-testid="stAppViewContainer"], [data-testid="stMain"],
[data-testid="stHeader"], [data-testid="stToolbar"], [data-testid="stBottom"],
.main, .block-container, section.main {
    background-color: #F4F6FA !important;
}
/* (o texto padrão fica escuro pelo tema `light` do config.toml + color-scheme
   acima; NÃO forço `color` global para não pintar o texto BRANCO dos botões
   azuis de escuro — o que tornava os botões ilegíveis) */

/* ===== TIPOGRAFIA: sans-serif legível, NEGRITO, tamanho NORMAL, cor NAVY
   (nunca preta) — hierarquia clara: titulo > rotulo > corpo > apoio ===== */
[data-testid="stMarkdownContainer"] p,
[data-testid="stMarkdownContainer"] li {
    font-size: 0.98rem; line-height: 1.5; font-weight: 600; color: #263449;
}
[data-testid="stMarkdownContainer"] strong { font-weight: 800; color: #16213E; }
[data-testid="stCaptionContainer"],
[data-testid="stCaptionContainer"] p,
[data-testid="stCaptionContainer"] div {
    font-size: 0.9rem !important; font-weight: 600 !important;
    color: #5B6B82 !important;          /* texto de APOIO: cinza-azulado neutro */
}
[data-testid="stAlert"] p, [data-testid="stAlert"] li {
    font-size: 0.96rem; line-height: 1.45; font-weight: 600;
}
[data-testid="stWidgetLabel"] p, [data-testid="stWidgetLabel"] label {
    font-weight: 700 !important; font-size: 0.95rem !important; color: #1E293B !important;
}
[data-testid="stMetricValue"] { font-weight: 800 !important; color: #1E3A8A !important; }
[data-testid="stMetricLabel"] p { font-weight: 700 !important; color: #5B6B82 !important; }
.pol-tab td, .pol-tab th { font-weight: 700 !important; }

/* esconde os steppers +/- dos number_inputs (melhor no touch) */
[data-testid="stNumberInput"] button { display: none; }
[data-testid="stNumberInput"] input { font-weight: 700; font-size: 0.98rem; }
[data-testid="stTextInput"] input { font-weight: 700; font-size: 0.98rem; }
[data-baseweb="select"] > div { font-weight: 700; }

/* ===== NAVEGAÇÃO: esconde a barra padrão (usamos o seletor CALCULAR) ===== */
[data-testid="stNavLink"] { display: none !important; }

/* rótulos "CALCULAR" e perguntas em destaque */
.pol-calc-label {
    font-weight: 800; color: #1E3A8A; font-size: 1.08rem; margin: 4px 0 6px;
}
.pol-pergunta {
    font-weight: 800; color: #1E3A8A; font-size: 1.06rem; margin: 12px 0 3px;
}

/* seletor de MÓDULO (Vigas / Lajes / Pilares / …) — ativo em ÂMBAR, demais
   em contorno navy discreto; tamanho equilibrado, lado a lado */
.pol-pg-ativo {
    background: linear-gradient(135deg, #F6C86B, #E8A33D);
    color: #16265B !important; font-weight: 800; font-size: 1.02rem;
    padding: 11px 10px; border-radius: 12px;
    box-shadow: 0 3px 10px rgba(180,83,9,.26);
    min-height: 48px; box-sizing: border-box;
    display: flex; align-items: center; justify-content: center;
}
[data-testid="stPageLink"] { width: 100%; }
[data-testid="stPageLink"] a {
    background: #F1F5FB; border: 1.5px solid #C9D6F5; border-radius: 12px;
    padding: 11px 10px !important; min-height: 48px;
    width: 100%; box-sizing: border-box;
    display: flex; align-items: center; justify-content: center;
    transition: all .12s ease;
}
[data-testid="stPageLink"] a:hover {
    background: #E6EDF9; border-color: #1E3A8A; transform: translateY(-1px);
}
[data-testid="stPageLink"] a * {
    color: #1E3A8A !important; font-size: 1.02rem !important;
    font-weight: 800 !important;
}
.pol-pg-inativo {
    background: #F1F5FB; border: 1.5px solid #C9D6F5; border-radius: 12px;
    color: #1E3A8A !important; font-weight: 800; font-size: 1.02rem;
    padding: 11px 10px; min-height: 48px; box-sizing: border-box;
    display: flex; align-items: center; justify-content: center;
}

/* ===== ETAPAS 1·Lançar / 2·Conferir / 3·Calcular =====
   ÂMBAR por padrão; ficam AZUL (navy) quando a etapa está ATIVA (clicada) ===== */
[class*="st-key-step_"] button[kind="secondary"] {
    background: linear-gradient(135deg, #F6C86B, #E8A33D) !important;
    color: #16265B !important; border: 1px solid #E8A33D !important;
    font-weight: 800 !important; box-shadow: 0 2px 7px rgba(180,83,9,.18) !important;
}
[class*="st-key-step_"] button[kind="secondary"]:hover:not(:disabled) { filter: brightness(1.05); }
[class*="st-key-step_"] button[kind="secondary"]:disabled {
    background: #F1E7CE !important; color: #A78E5C !important;
    border-color: #E7D8B0 !important; box-shadow: none !important;
}
[class*="st-key-step_"] button[kind="primary"] {
    background: linear-gradient(135deg, #16265B, #1E3A8A) !important;
    color: #fff !important; border: none !important;
    box-shadow: 0 3px 10px rgba(30,58,138,.32) !important;
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
    color: #fff; border-radius: 14px; padding: 13px 18px 11px;
    margin-bottom: 4px; text-align: center;
}
a.pol-marca-link { text-decoration: none !important; display: block; }
a.pol-marca-link:hover .marca-txt { color: #F0C879; }
a.pol-marca-link:hover .logo-badge { transform: scale(1.05); }
a.pol-marca-link:hover .pol-logo-card {
    transform: translateY(-1px); box-shadow: 0 6px 22px rgba(0,0,0,.32);
}
a.pol-marca-link:hover .pol-site-hint {
    background: #F0C879; color: #16265B;
}
/* cartão branco onde o logo oficial (preto+laranja) fica legível */
.pol-logo-card {
    display: inline-block; background: #fff; border-radius: 11px;
    padding: 8px 14px; box-shadow: 0 3px 12px rgba(0,0,0,.22);
    transition: transform .12s ease, box-shadow .12s ease;
}
.pol-logo-card .pol-logo-img {
    display: block; margin: 0 auto; height: auto;
    width: 100%; max-width: 185px !important;   /* logo PROPORCIONAL (menor, ainda legível) */
}
.pol-header .marca {
    display: flex; align-items: center; justify-content: center; gap: 12px;
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
    background: #F0C879; margin: 12px auto 10px;
}
.pol-header h1 {
    font-size: 1.08rem; line-height: 1.3; margin: 0;
    color: #DDE7FB; font-weight: 700;
}
.pol-header .sub { color: #A9BCE8; font-size: .82rem; margin-top: 3px; }

/* título de seção — limpo; o número vira um "chip"; SEM cortar (quebra linha) */
.pol-sec {
    display: flex; align-items: center; gap: 10px;
    font-weight: 800; color: #1E3A8A;
    font-size: clamp(1.02rem, 4vw, 1.16rem); line-height: 1.25;
    white-space: normal; margin: 16px 0 6px;
}
.pol-sec .num {
    background: #1E3A8A; color: #fff; border-radius: 999px;
    min-width: 25px; height: 25px; display: inline-flex;
    align-items: center; justify-content: center; font-size: .82rem;
    flex: 0 0 auto; box-shadow: 0 1px 3px rgba(30,58,138,.3);
}
/* seção de ENTRADA em destaque — CARTÃO claro com barra lateral navy (leve,
   sem faixa pesada) + número em chip âmbar */
.pol-sec.destaque {
    background: #F3F6FC; color: #1E3A8A;
    padding: 10px 13px; border-radius: 11px;
    border-left: 4px solid #1E3A8A;
    margin: 16px 0 8px; box-shadow: 0 1px 3px rgba(16,33,68,.06);
}
.pol-sec.destaque .num {
    background: linear-gradient(135deg, #F6C86B, #E8A33D); color: #16265B;
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

/* ===== NEGRITO no conteúdo principal (rótulos e corpo); o texto de APOIO
   (captions) fica mais leve p/ hierarquia limpa ===== */
[data-testid="stMarkdownContainer"], [data-testid="stMarkdownContainer"] *,
[data-testid="stWidgetLabel"], [data-testid="stWidgetLabel"] * {
    font-weight: 700 !important;
}
[data-testid="stWidgetLabel"] p { font-size: 0.95rem !important; }
[data-testid="stMetricValue"] { font-weight: 800 !important; }
[data-testid="stMetricLabel"] * { font-weight: 700 !important; }
/* números digitados: negrito, tamanho NORMAL */
[data-testid="stNumberInput"] input, [data-testid="stTextInput"] input,
[data-baseweb="select"] div {
    font-weight: 700 !important; font-size: 0.98rem !important;
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

/* ===== AÇÃO PRIMÁRIA (Inserir / Salvar) em ÂMBAR — tamanho equilibrado ===== */
[data-testid="stFormSubmitButton"] button {
    background: linear-gradient(135deg, #E8A33D, #B45309) !important;
    color: #ffffff !important; border: none !important;
    font-size: 1.0rem !important; font-weight: 800 !important;
    min-height: 46px !important; letter-spacing: .01em; border-radius: 10px !important;
    box-shadow: 0 3px 10px rgba(180,83,9,.26);
}
[data-testid="stFormSubmitButton"] button:hover { filter: brightness(1.07); }
/* botão primário (Calcular etc.) em NAVY — normal e firme */
div.stButton > button[kind="primary"] {
    font-size: 1.04rem !important; font-weight: 800 !important;
    min-height: 48px !important; border-radius: 10px !important;
}
/* botões em geral: cantos suaves e altura confortável de toque */
div.stButton > button, [data-testid="stFormSubmitButton"] button {
    border-radius: 10px; min-height: 44px;
}
div.stButton > button[kind="secondary"] {
    border: 1.5px solid #C9D6F5; color: #1E3A8A; background: #F8FAFD;
}
div.stButton > button[kind="secondary"]:hover { border-color: #1E3A8A; background: #EEF3FC; }

/* ===== CALLOUTS (dica/sucesso/alerta): cantos suaves + leve elevação ===== */
[data-testid="stAlert"] {
    border-radius: 10px !important; box-shadow: 0 1px 3px rgba(16,33,68,.05);
}
/* inputs/selects: cantos suaves + FOCO visível (acessibilidade/toque) */
[data-testid="stNumberInput"] input, [data-testid="stTextInput"] input,
[data-baseweb="select"] > div {
    border-radius: 9px !important;
}
[data-testid="stNumberInput"] input:focus, [data-testid="stTextInput"] input:focus {
    outline: 2px solid #93B4F5 !important; outline-offset: 1px;
}
/* divisórias suaves */
hr { border-color: #E4E9F2 !important; }

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


def compor_a4(pngs, orient="retrato", titulo=None):
    """Junta várias imagens PNG (bytes) numa ÚNICA folha A4 — empilhadas e
    escaladas para a largura, mantendo a proporção de cada uma (sem distorcer).
    Serve para reduzir o nº de folhas impressas (ex.: armação + corte na mesma
    folha). Devolve os bytes PNG da folha composta (fundo branco)."""
    import matplotlib.pyplot as plt
    import matplotlib.image as _mpimg
    imgs = [_mpimg.imread(_io.BytesIO(p)) for p in pngs if p]
    if not imgs:
        return b""
    A4 = (8.27, 11.69) if orient == "retrato" else (11.69, 8.27)
    ratios = [im.shape[0] / im.shape[1] for im in imgs]   # altura/largura de cada
    fig, axs = plt.subplots(len(imgs), 1, figsize=A4,
                            gridspec_kw={"height_ratios": ratios})
    fig.patch.set_facecolor("white")
    if len(imgs) == 1:
        axs = [axs]
    for ax, im in zip(axs, imgs):
        ax.imshow(im)
        ax.axis("off")
    top = 0.965 if titulo else 0.99
    fig.subplots_adjust(left=0.01, right=0.99, top=top, bottom=0.01, hspace=0.04)
    if titulo:
        fig.suptitle(titulo, fontsize=13, fontweight="bold", color="#1E3A8A", y=0.992)
    buf = _io.BytesIO()
    fig.savefig(buf, format="png", dpi=160, facecolor="white")
    plt.close(fig)
    return buf.getvalue()


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
    uri = _logo_uri()
    if uri:                        # logo oficial (imagem) num cartão branco
        marca = (f'<div class="pol-logo-card">'
                 f'<img class="pol-logo-img" src="{uri}" '
                 f'alt="Polotto Engenharia — desde 1978"></div>')
    else:                          # fallback textual (se o arquivo faltar)
        marca = ('<div class="marca"><span class="logo-badge">P</span>'
                 '<span class="marca-txt">Polotto <em>Engenharia</em>'
                 '<span class="ext">&#8599;</span></span></div>')
    st.markdown(f"""
<div class="pol-header">
  <a class="pol-marca-link" href="https://polottoengenharia.com.br"
     target="_blank" rel="noopener" title="Abrir polottoengenharia.com.br">
    {marca}
    <div class="pol-site-hint">&#127760; polottoengenharia.com.br
      &nbsp;·&nbsp; clique para visitar</div>
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


# ---- Sobrecargas de uso (cargas acidentais) — NBR 6120:2019 [kN/m²] ----
SOBRECARGAS_USO = {
    "Residência — dormitório/sala": 1.5,
    "Residência — cozinha/área de serviço": 2.0,
    "Escritório": 2.5,
    "Corredor/escada": 3.0,
    "Loja/comércio": 4.0,
    "Garagem — veículos leves": 3.0,
    "Cobertura — só manutenção/acesso": 1.0,
}
# Paredes — peso por m² de parede (alvenaria + revestimento) [kN/m²]
PAREDES = {
    "Sem parede": 0.0,
    "Bloco cerâmico furado 15 cm": 1.8,
    "Bloco de concreto 14 cm": 2.8,
    "Tijolo maciço (1 vez)": 3.6,
    "Divisória leve / drywall": 1.0,
}
# Tipos de laje: 'macica' calcula 25·espessura; 'direto' pede o valor;
# número = peso próprio típico em kN/m² (NBR 6120)
TIPOS_LAJE = {
    "Maciça (informar espessura)": "macica",
    "Nervurada / treliçada com EPS": 2.0,
    "Lajota cerâmica pré-fabricada": 2.5,
    "Pré-moldada comum": 2.2,
    "Informar o peso direto": "direto",
}


def assistente_carga(fu, un_fm, key="asst"):
    """Assistente que estima a carga distribuída q [kN/m] de uma viga a
    partir de componentes comuns (NBR 6120). Retorna q em kN/m se o usuário
    confirmar, senão None. As cargas de área e o resultado são exibidos na
    unidade escolhida (kN ou kgf); o cálculo interno é sempre em kN.
    """
    un_area = "kgf/m²" if fu > 1 else "kN/m²"
    ca = 0 if fu > 1 else 2                      # casas decimais p/ área

    def _fa(v_kN):                               # formata carga de área
        return f"{v_kN * fu:.{ca}f}"

    q_kN = None
    with st.expander("🧮 Montar a carga (sobrecargas comuns) — opcional"):
        st.caption("Some os componentes que apoiam na viga. Os valores "
                   "seguem a NBR 6120. O peso próprio da viga é somado "
                   "depois, automaticamente. Fórmula: q = (laje + "
                   "revestimento + sobrecarga de uso) × largura de "
                   "influência + parede.")

        # ---- Largura de influência da laje (o "tamanho de laje" que pesa
        #      sobre a viga). Pode ser calculada pelos vãos das lajes de cada
        #      lado ou digitada direto.
        modo_inf = st.radio(
            "Como definir a largura de influência da laje?",
            ["Pelos vãos das lajes (o programa calcula)",
             "Digitar a largura direto"],
            key=f"{key}_modo", horizontal=True,
            help="A largura de influência é a FAIXA de laje que descarrega "
                 "nesta viga. Vale metade do vão da laje de cada lado — a "
                 "outra metade vai para a viga vizinha. É esse valor que "
                 "transforma a carga por m² em carga por metro de viga.")
        if modo_inf.startswith("Pelos vãos"):
            cle, cld = st.columns(2)
            L_esq = cle.number_input(
                "Vão da laje à ESQUERDA [m]", min_value=0.0, max_value=12.0,
                value=4.0, step=0.1, format="%.2f", key=f"{key}_le",
                help="Distância desta viga até a viga/apoio vizinho do lado "
                     "esquerdo (= vão da laje desse lado). Use 0 se a viga é "
                     "de borda (não há laje à esquerda).")
            L_dir = cld.number_input(
                "Vão da laje à DIREITA [m]", min_value=0.0, max_value=12.0,
                value=4.0, step=0.1, format="%.2f", key=f"{key}_ld",
                help="Idem, do lado direito. Use 0 se não há laje desse lado.")
            larg = (L_esq + L_dir) / 2.0
            st.caption(
                f"➡️ Largura de influência = (vão esq + vão dir) ÷ 2 = "
                f"({L_esq:.2f} + {L_dir:.2f}) ÷ 2 = **{larg:.2f} m**  ·  "
                f"cada laje entrega metade do seu vão para esta viga.")
        else:
            larg = st.number_input(
                "Largura de influência da laje [m]", min_value=0.0,
                max_value=15.0, value=4.0, step=0.1, format="%.2f",
                key=f"{key}_lg",
                help="Faixa de laje que descarrega nesta viga = soma das "
                     "metades dos vãos de laje de cada lado. Ex.: viga entre "
                     "duas lajes de 4 m → 2 m + 2 m = 4 m. Viga de borda "
                     "(laje só de um lado, vão 4 m) → ~2 m.")
        tipo_laje = st.selectbox(
            "Tipo de laje", list(TIPOS_LAJE.keys()), key=f"{key}_tl",
            help="A laje maciça calcula o peso pela espessura "
                 "(25 kN/m³ × espessura — NBR 6120). As demais usam pesos "
                 "próprios típicos.")
        _tl = TIPOS_LAJE[tipo_laje]
        if _tl == "macica":
            esp = st.number_input(
                "Espessura da laje maciça [cm]", min_value=5.0,
                max_value=30.0, value=10.0, step=1.0, format="%.0f",
                key=f"{key}_esp",
                help="Espessura da laje maciça. Residências: 8 a 12 cm. "
                     "Peso = 25 kN/m³ × espessura → laje de 10 cm = "
                     "2,5 kN/m² (255 kgf/m²); de 12 cm = 3,0 (306 kgf/m²).")
            laje = 25.0 * esp / 100.0
        elif _tl == "direto":
            laje_d = st.number_input(
                f"Peso próprio da laje [{un_area}]", min_value=0.0,
                max_value=15.0 * fu, value=2.5 * fu, step=0.5 * fu,
                format=f"%.{ca}f", key=f"{key}_lj",
                help="Informe o peso próprio da laje por m².")
            laje = laje_d / fu
        else:
            laje = _tl
        st.caption(f"➡️ Peso próprio da laje adotado: **{_fa(laje)} "
                   f"{un_area}** (= {laje:.2f} kN/m²).")
        c3, c4 = st.columns(2)
        revest_d = c3.number_input(
            f"Revestimento/contrapiso [{un_area}]", min_value=0.0,
            max_value=5.0 * fu, value=1.0 * fu, step=0.5 * fu,
            format=f"%.{ca}f", key=f"{key}_rv",
            help="Contrapiso + piso + forro. Usual ≈ 1,0 kN/m² "
                 "(102 kgf/m²).")
        revest = revest_d / fu
        uso_lbl = c4.selectbox(
            "Sobrecarga de uso (NBR 6120)", list(SOBRECARGAS_USO.keys()),
            key=f"{key}_uso",
            format_func=lambda k: f"{k} ({_fa(SOBRECARGAS_USO[k])} "
                                  f"{un_area})",
            help="Carga acidental (de uso) conforme o ambiente — NBR 6120, "
                 "Tabela 10.")
        uso = SOBRECARGAS_USO[uso_lbl]
        c5, c6 = st.columns(2)
        par_lbl = c5.selectbox(
            "Parede sobre a viga", list(PAREDES.keys()), key=f"{key}_pl",
            format_func=lambda k: (k if PAREDES[k] == 0 else
                                   f"{k} ({_fa(PAREDES[k])} {un_area})"),
            help="Tipo de parede que apoia diretamente na viga (se houver).")
        alt_par = c6.number_input(
            "Altura da parede [m]", min_value=0.0, max_value=8.0, value=2.8,
            step=0.1, format="%.2f", key=f"{key}_ap",
            disabled=(PAREDES[par_lbl] == 0.0),
            help="Pé-direito da parede sobre a viga (altura da alvenaria).")
        parede = PAREDES[par_lbl] * alt_par                    # kN/m
        carga_m2 = laje + revest + uso                         # kN/m²
        q_laje = carga_m2 * larg                               # kN/m (só laje)
        q_kN_calc = q_laje + parede                            # kN/m (total)

        # ---- Descrição matemática (embaixo da linha de influência) ----
        st.markdown("---")
        st.markdown("**📐 Como esta carga foi calculada (por metro de viga):**")
        st.markdown(
            f"**1)** Carga da laje por m² = {_fa(laje)} (peso próprio) + "
            f"{_fa(revest)} (revest.) + {_fa(uso)} (uso, NBR 6120) = "
            f"**{_fa(carga_m2)} {un_area}**")
        st.markdown(
            f"**2)** × largura de influência **{larg:.2f} m** "
            f"(= faixa de laje que apoia na viga) = "
            f"**{q_laje * fu:.{ca}f} {un_fm}**")
        if parede > 0:
            st.markdown(
                f"**3)** + parede sobre a viga "
                f"({_fa(PAREDES[par_lbl])} {un_area} × {alt_par:.2f} m de "
                f"altura) = {parede * fu:.{ca}f} {un_fm}")
        st.markdown(
            f"### ➡️ q ≈ {q_kN_calc * KGF_POR_KN:,.0f} kgf/m"
            .replace(",", ".")
            + f"  ·  {q_kN_calc:.2f} kN/m")
        st.caption("O peso próprio da própria viga é somado depois, "
                   "automaticamente, no cálculo estrutural.")
        if st.button(f"✔ Usar esta carga ({q_kN_calc * fu:.{0 if fu > 1 else 1}f}"
                     f" {un_fm})", key=f"{key}_btn", width="stretch"):
            q_kN = q_kN_calc
    return q_kN


# 1 kN = 101,9716 kgf  (1 kgf = 9,80665 N)
KGF_POR_KN = 101.9716


# ---- Exemplos completos (casos do cotidiano) ----
EXEMPLOS_VIGA = [
    {"nome": "Viga biapoiada residencial",
     "descr": "1 vão de 4,5 m, uso residencial. O caso mais simples.",
     "secao": {"b": 15.0, "h": 45.0, "fck": 25, "cob": 2.5},
     "tramos": [{"tipo": "Normal", "L": 4.5, "q": 18.0, "P": 0.0, "a": 0.0}]},
    {"nome": "Viga contínua de 2 vãos",
     "descr": "Vãos de 5 e 4 m — viga apoiada em 3 pilares.",
     "secao": {"b": 15.0, "h": 50.0, "fck": 25, "cob": 2.5},
     "tramos": [{"tipo": "Normal", "L": 5.0, "q": 20.0, "P": 0.0, "a": 0.0},
                {"tipo": "Normal", "L": 4.0, "q": 18.0, "P": 0.0, "a": 0.0}]},
    {"nome": "Viga de 3 vãos",
     "descr": "5 / 4 / 5 m — viga contínua típica de pequeno edifício.",
     "secao": {"b": 15.0, "h": 55.0, "fck": 30, "cob": 3.0},
     "tramos": [{"tipo": "Normal", "L": 5.0, "q": 22.0, "P": 0.0, "a": 0.0},
                {"tipo": "Normal", "L": 4.0, "q": 20.0, "P": 0.0, "a": 0.0},
                {"tipo": "Normal", "L": 5.0, "q": 22.0, "P": 0.0, "a": 0.0}]},
    {"nome": "Viga com balanço (marquise)",
     "descr": "Balanço de 1,5 m + vão de 4,5 m.",
     "secao": {"b": 15.0, "h": 50.0, "fck": 25, "cob": 2.5},
     "tramos": [{"tipo": "Balanço Esquerdo", "L": 1.5, "q": 15.0,
                 "P": 0.0, "a": 0.0},
                {"tipo": "Normal", "L": 4.5, "q": 20.0, "P": 0.0, "a": 0.0}]},
    {"nome": "Viga com carga concentrada",
     "descr": "Vão de 6 m recebendo uma viga (P = 80 kN no meio).",
     "secao": {"b": 20.0, "h": 60.0, "fck": 30, "cob": 3.0},
     "tramos": [{"tipo": "Normal", "L": 6.0, "q": 15.0, "P": 80.0,
                 "a": 3.0}]},
    {"nome": "Viga alta (com armadura de pele)",
     "descr": "h = 70 cm > 60 → exige armadura de pele (NBR 6118).",
     "secao": {"b": 20.0, "h": 70.0, "fck": 30, "cob": 3.0},
     "tramos": [{"tipo": "Normal", "L": 6.0, "q": 25.0, "P": 0.0,
                 "a": 0.0}]},
]

EXEMPLOS_PILAR = [
    {"nome": "Pilar de residência (térreo)",
     "descr": "20×30, pé-direito 2,8 m, carga 400 kN.",
     "dados": {"b": 20.0, "h": 30.0, "l0": 2.8, "fck": 25, "Nk": 400.0,
               "caa": "I"}},
    {"nome": "Pilar de canto (pequeno)",
     "descr": "20×20, 2,8 m, carga leve 250 kN.",
     "dados": {"b": 20.0, "h": 20.0, "l0": 2.8, "fck": 25, "Nk": 250.0,
               "caa": "II"}},
    {"nome": "Pilar mais carregado",
     "descr": "20×40, 3,0 m, 900 kN (pilar central de edifício baixo).",
     "dados": {"b": 20.0, "h": 40.0, "l0": 3.0, "fck": 30, "Nk": 900.0,
               "caa": "II"}},
]


def _botao_pagina(alvo, atual, path, label, icon):
    if atual == alvo:
        st.markdown(f'<div class="pol-pg-ativo">{icon} {label}</div>',
                    unsafe_allow_html=True)
        return
    try:                       # link real (dentro da navegação st.navigation)
        st.page_link(path, label=label, icon=icon)
    except Exception:          # fallback (execução direta / sem navegação)
        st.markdown(f'<div class="pol-pg-inativo">{icon} {label}</div>',
                    unsafe_allow_html=True)


def seletor_pagina(atual):
    """Seletor destacado CALCULAR → Vigas / Pilares (no corpo da página).

    atual: 'vigas' ou 'pilar' — define qual botão fica em âmbar (ativo).
    """
    st.markdown('<div class="pol-calc-label">Calcular — clique na opção '
                'abaixo:</div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        _botao_pagina("vigas", atual, "pagina_vigas.py", "Vigas", "🏗️")
    with c2:
        _botao_pagina("pilar", atual, "pagina_pilar.py", "Pilares", "🏛️")
    # módulos adicionais (largura total, logo abaixo dos dois botões)
    _botao_pagina("lajes", atual, "pagina_lajes.py",
                  "Lajes (maciça e pré-moldada)", "🧱")
    _botao_pagina("previo", atual, "pagina_pilar_previo.py",
                  "Pilares Prévios — casas térreas", "🏠")
    _botao_pagina("completo", atual, "pagina_projeto_completo.py",
                  "Projeto Completo — inserir planta e lançar", "📐")


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
