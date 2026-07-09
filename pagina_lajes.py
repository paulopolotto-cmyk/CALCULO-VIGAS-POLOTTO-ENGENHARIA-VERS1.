# -*- coding: utf-8 -*-
"""
Página LAJES — Polotto Engenharia (motor de cálculo em motor_laje.py).
Laje maciça (1 e 2 direções, 9 casos de apoio) e pré-moldada treliçada.
Calcula a laje, transfere as reações para as vigas e as cargas para os
pilares (integração com os módulos existentes). NBR 6118 / 6120 / 14859.
"""
import io

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.backends.backend_pdf import PdfPages
import numpy as np
import streamlit as st

import motor_laje as ml
from ui_comum import (NAVY, CINZA_TXT, aplicar_estilo, header, sec,
                      seletor_unidade, tabela, seletor_pagina, mostrar_figura)

aplicar_estilo()
header("Cálculo de Lajes — Maciça e Pré-moldada",
       "Laje → Vigas → Pilares · NBR 6118 / 6120 / 14859")
seletor_pagina("lajes")

fu, un_f, un_fm = seletor_unidade()
ss = st.session_state

# Realce visual: chip de vão selecionado em âmbar + borda âmbar nos campos de
# parâmetro (confirma ao engenheiro o que foi escolhido e entra no cálculo).
st.markdown("""<style>
[data-testid="stButtonGroup"] button[kind="pillsActive"]{
  background:linear-gradient(135deg,#F6C86B,#E8A33D)!important;
  border-color:#E8A33D!important;font-weight:800!important;}
[data-testid="stButtonGroup"] button[kind="pillsActive"] *{
  color:#16265B!important;}
[data-testid="stNumberInput"] input,
[data-testid="stSelectbox"] [data-baseweb="select"]>div:first-child{
  border-left:4px solid #E8A33D!important;}
</style>""", unsafe_allow_html=True)

VAOS_RAPIDOS = [(2, 1), (2, 2), (3, 3), (3.5, 3.5), (3.5, 4), (4, 4),
                (4.5, 4.5), (5, 5), (5.5, 4.5), (6, 5), (6.5, 7), (7, 7)]
LADOS = [("sup", "Superior"), ("inf", "Inferior"),
         ("esq", "Esquerda"), ("dir", "Direita")]

# ------------------------------------------------------------ estado
_defaults = {
    "laje_tipo": "Pré-moldada treliçada", "laje_lx": 4.0, "laje_ly": 4.0,
    "laje_h_mac": 10.0, "laje_h_trel": 16, "laje_ench": "EPS",
    "laje_cont": "biapoiada", "laje_fck": 25, "laje_uso": "Dormitório / sala / cozinha",
    "laje_grev": 1.0, "laje_gpar": 0.0,
    "laje_sup": "Apoiada", "laje_inf": "Apoiada",
    "laje_esq": "Apoiada", "laje_dir": "Apoiada",
    "vao_pills": "4×4",
}
for _k, _v in _defaults.items():
    if _k not in ss:
        ss[_k] = _v


def _fN(v_kN):
    v = v_kN * fu
    if fu > 1:
        return f"{v:,.0f}".replace(",", ".")
    return f"{v:,.1f}".replace(",", " ").replace(".", ",")


def _f2(v, casas=2):
    """Número em formato PT-BR (vírgula decimal)."""
    return f"{v:.{casas}f}".replace(".", ",")


def _apoios_dict():
    m = {"Apoiada": "apoiado", "Engastada": "engastado", "Livre": "livre"}
    return {e: m[ss[f"laje_{e}"]] for e in ("sup", "inf", "esq", "dir")}


@st.cache_data(show_spinner=False)
def _calc_macica(lx, ly, apoios_t, h, fck, grev, uso, gpar):
    d = dict(lx=lx, ly=ly, apoios=dict(apoios_t), h=h, fck=fck,
             g_rev=grev, q_uso=uso, g_parede=gpar)
    return ml.calcular_laje_macica(d)


@st.cache_data(show_spinner=False)
def _calc_trelica(lx, ly, h, ench, cont, fck, grev, uso, gpar):
    d = dict(lx=lx, ly=ly, h=h, enchimento=ench, continuidade=cont, fck=fck,
             g_rev=grev, q_uso=uso, g_parede=gpar)
    return ml.calcular_laje_trelicada(d)


@st.cache_data(show_spinner=False)
def _comparativo(lx0, ly0, fck, grev, uso, gpar, h_mac, h_trel, ench):
    return ml.comparativo(dict(lx=lx0, ly=ly0, fck=fck, g_rev=grev, q_uso=uso,
                               g_parede=gpar, h_macica=h_mac, h_trelica=h_trel,
                               enchimento=ench))


# ================================================= ENTRADAS ==============
sec(1, "Tipo de laje", destaque=True)
ss.laje_tipo = st.radio(
    "Sistema", ["Pré-moldada treliçada", "Maciça"],
    index=0 if ss.laje_tipo.startswith("Pré") else 1, horizontal=True,
    label_visibility="collapsed",
    help="Treliçada (vigota + EPS/cerâmico): dominante em residências. "
         "Maciça: laje de concreto cheia, armada em 1 ou 2 direções.")
is_trel = ss.laje_tipo.startswith("Pré")

sec(2, "Vãos do pano (lx × ly)")
st.caption("Toque em um vão padrão ou digite abaixo. **lx** = menor vão "
           "(direção principal da armação).")
_opts = [f"{a:g}×{b:g}" for a, b in VAOS_RAPIDOS]
_cur = f"{float(ss.laje_lx):g}×{float(ss.laje_ly):g}"
# vão livre (não é um preset) → remove o destaque do chip (evita flicker)
if _cur not in _opts and ss.get("vao_pills") is not None:
    ss["vao_pills"] = None
_pick = st.pills("Vãos padrão", _opts, selection_mode="single",
                 label_visibility="collapsed", key="vao_pills")
if _pick and _pick != _cur:
    _a, _b = _pick.split("×")
    ss.laje_lx, ss.laje_ly = float(_a), float(_b)
    st.rerun()
cvx, cvy = st.columns(2)
# usam a MESMA chave do estado (laje_lx/laje_ly) → ficam sempre em sincronia
# com o chip de vão selecionado acima (sem defasagem/valor antigo).
cvx.number_input("Vão lx [m]", 0.5, 12.0, step=0.1, format="%.2f",
                 key="laje_lx")
cvy.number_input("Vão ly [m]", 0.5, 12.0, step=0.1, format="%.2f",
                 key="laje_ly")
lx0, ly0 = float(ss.laje_lx), float(ss.laje_ly)
lam = max(lx0, ly0) / min(lx0, ly0)

# Ao mudar o vão (ou a vinculação), sugere automaticamente a ALTURA COMERCIAL
# da laje pela norma. O engenheiro pode alterar depois — a escolha manual é
# mantida enquanto o vão não mudar.
_spk = (round(lx0, 2), round(ly0, 2), is_trel, ss.get("laje_cont"))
if ss.get("_span_auto") != _spk:
    ss["_span_auto"] = _spk
    _q = ml.CARGAS_USO.get(ss.laje_uso, 1.5)          # carga de uso atual
    if is_trel:
        # a partir do pré-dim (L/30) sobe até a menor altura comercial que
        # passa na flecha
        _hr = ml.h_recomendada_trelica(min(lx0, ly0),
                                       ss.get("laje_cont") == "continua")
        _best = None
        for _h in sorted(ml.PP_TRELICA):              # 12,16,20,25
            if _h < _hr - 0.5:
                continue
            _r = _calc_trelica(lx0, ly0, _h, ss.laje_ench,
                               ss.get("laje_cont", "biapoiada"),
                               int(ss.laje_fck), ss.laje_grev, _q, ss.laje_gpar)
            if not _r.get("erros") and _r["flecha"]["nivel"] != "vermelho":
                _best = _h
                break
        ss.laje_h_trel = _best or max(ml.PP_TRELICA)
    else:
        # a partir do pré-dim (L/40, ou L/45 se 1 direção) sobe até passar
        _h0 = int(max(8, round(min(lx0, ly0) * 100.0 /
                               (40.0 if lam <= 2 else 45.0))))
        _apt = tuple(sorted(_apoios_dict().items()))
        _best = None
        for _h in range(_h0, 21):
            _r = _calc_macica(lx0, ly0, _apt, float(_h), int(ss.laje_fck),
                              ss.laje_grev, _q, ss.laje_gpar)
            if not _r.get("erros") and _r["flecha"]["nivel"] != "vermelho":
                _best = _h
                break
        ss.laje_h_mac = float(_best or 20)

if is_trel:
    sec(3, "Laje treliçada — altura e enchimento")
    c1, c2, c3 = st.columns(3)
    ss.laje_h_trel = c1.selectbox("Altura h [cm]", list(ml.PP_TRELICA.keys()),
                                  index=list(ml.PP_TRELICA).index(ss.laje_h_trel),
                                  help="Altura total (enchimento + capa). Ex.: "
                                       "16 = 12+4 cm.")
    ss.laje_ench = c2.selectbox("Enchimento", ["EPS", "ceramico"],
                                index=0 if ss.laje_ench == "EPS" else 1,
                                format_func=lambda s: "EPS (isopor)" if s == "EPS"
                                else "Cerâmico (lajota)")
    ss.laje_cont = c3.selectbox("Vinculação", ["biapoiada", "continua"],
                                index=0 if ss.laje_cont == "biapoiada" else 1,
                                format_func=lambda s: "Biapoiada" if s == "biapoiada"
                                else "Contínua")
    _capa = ml.PP_TRELICA[int(ss.laje_h_trel)][0]
    _ench_txt = "EPS" if ss.laje_ench == "EPS" else "cerâmica"
    st.success(f"✔ **Laje comercial adotada: treliçada H{int(ss.laje_h_trel)} "
               f"({int(ss.laje_h_trel - _capa)}+{int(_capa)} cm) {_ench_txt}** — "
               f"altura sugerida pela norma para vão de "
               f"{_f2(min(lx0, ly0))} m. Ajuste acima se quiser outra. "
               f"Vigotas no menor vão; PP por catálogo NBR 14859.")
else:
    sec(3, "Laje maciça — espessura e apoios")
    ss.laje_h_mac = st.number_input(
        "Espessura h [cm]", 6.0, 20.0, float(ss.laje_h_mac), 1.0, "%.0f",
        help="Mínimo NBR 6118 (13.2.4.1): 8 cm (piso), 7 cm (forro).")
    st.success(f"✔ **Espessura adotada: {int(ss.laje_h_mac)} cm** — sugerida "
               f"pela norma para o vão (λ = {_f2(lam)}). Ajuste acima se "
               f"quiser outra.")
    st.markdown("**Condições de apoio das 4 bordas** "
                "(Engastada = continuidade com laje vizinha):")
    pcol = st.columns(4)
    for i, (e, nome) in enumerate(LADOS):
        ss[f"laje_{e}"] = pcol[i].selectbox(
            nome, ["Apoiada", "Engastada"],
            index=0 if ss[f"laje_{e}"] == "Apoiada" else 1, key=f"sel_{e}")

sec(4, "Cargas e material")
c1, c2 = st.columns(2)
ss.laje_uso = c1.selectbox("Uso do ambiente (NBR 6120)", list(ml.CARGAS_USO),
                           index=list(ml.CARGAS_USO).index(ss.laje_uso),
                           help="Carga acidental de uso (Tabela 10 da NBR 6120).")
q_uso = ml.CARGAS_USO[ss.laje_uso]
ss.laje_fck = c2.selectbox("Concreto fck [MPa]", [20, 25, 30, 35, 40],
                           index=[20, 25, 30, 35, 40].index(ss.laje_fck))
c3, c4 = st.columns(2)
un_area = "kgf/m²" if fu > 1 else "kN/m²"
grev_disp = c3.number_input(f"Revestimento/contrapiso [{un_area}]", 0.0,
                            5.0 * fu, 1.0 * fu, 0.1 * fu,
                            f"%.{0 if fu > 1 else 2}f",
                            help="Contrapiso + piso + forro. Usual ≈ 1,0 kN/m².")
ss.laje_grev = grev_disp / fu
gpar_disp = c4.number_input(f"Parede sobre a laje [{un_area}]", 0.0,
                            8.0 * fu, ss.laje_gpar * fu, 0.1 * fu,
                            f"%.{0 if fu > 1 else 2}f",
                            help="Parede apoiada sobre a laje, distribuída na "
                                 "área (comprimento×altura×peso ÷ área do pano). "
                                 "Ref.: bloco cerâmico furado ~1,8 kN/m² de "
                                 "parede; drywall ~1,0. 0 se não há.")
ss.laje_gpar = gpar_disp / fu
st.caption(f"Carga de uso adotada: **{q_uso:.1f} kN/m²** "
           f"({q_uso * 101.9716:.0f} kgf/m²).")

# ================================================= CÁLCULO ==============
if is_trel:
    res = _calc_trelica(lx0, ly0, int(ss.laje_h_trel), ss.laje_ench,
                        ss.laje_cont, int(ss.laje_fck), ss.laje_grev,
                        q_uso, ss.laje_gpar)
else:
    ap = _apoios_dict()
    res = _calc_macica(lx0, ly0, tuple(sorted(ap.items())),
                       float(ss.laje_h_mac), int(ss.laje_fck), ss.laje_grev,
                       q_uso, ss.laje_gpar)

if res.get("erros"):
    for e in res["erros"]:
        st.error(e)
    st.stop()

lx, ly = res["lx"], res["ly"]
fl = res["flecha"]


# --------- monta reações por borda (unifica maciça e treliçada) ---------
def _reacoes_por_borda():
    """Retorna {borda: {'q','qd','L','nome'}} + cantos (pilares)."""
    if is_trel:
        rp = res["reacoes"]
        # vigotas no menor vão -> principais nas bordas de comprimento ly
        if lx == min(lx0, ly0):     # lx é o menor (padrão do motor)
            b = {"esq": ("principal", ly), "dir": ("principal", ly),
                 "inf": ("marginal", lx), "sup": ("marginal", lx)}
        else:
            b = {"inf": ("principal", lx), "sup": ("principal", lx),
                 "esq": ("marginal", ly), "dir": ("marginal", ly)}
        out = {}
        for e, (tp, L) in b.items():
            out[e] = {"q": rp[f"{tp}_q"], "qd": rp[f"{tp}_qd"], "L": L,
                      "tipo": tp}
        return out
    else:
        rr = res["reacoes"]
        rd = res["reacoes_d"]
        return {e: {"q": rr[e]["q_eq"], "qd": rd[e]["q_eq"],
                    "L": rr[e]["L"], "tipo": "-"} for e in ml.BORDAS}


reac = _reacoes_por_borda()
# nomeia vigas V1..V4 (sup, inf, esq, dir) e pilares P1..P4 (cantos)
VIGA_NOME = {"sup": "V1", "inf": "V2", "esq": "V3", "dir": "V4"}
# cantos: (nome, borda_a, borda_b, comprimentos)
CANTOS = [("P1", "sup", "esq"), ("P2", "sup", "dir"),
          ("P3", "inf", "esq"), ("P4", "inf", "dir")]


def _cargas_pilares():
    g_viga = 0.14 * 0.40 * ml.PESO_CONCRETO      # ~viga 14x40 kN/m
    out = []
    for nome, ba, bb in CANTOS:
        # reação de canto = metade da reação de cada viga adjacente
        Na = (reac[ba]["q"] + g_viga) * reac[ba]["L"] / 2.0
        Nb = (reac[bb]["q"] + g_viga) * reac[bb]["L"] / 2.0
        out.append({"nome": nome, "Nk": Na + Nb})
    return out


pilares = _cargas_pilares()


# ---------------------------------------------------- desenho do pano ----
def fig_pano():
    fig, ax = plt.subplots(figsize=(6.6, 6.6 * ly / lx if ly >= lx else 6.6))
    if is_trel:
        # laje 1 direção: colore as duas metades que descarregam nas vigas
        # principais (perpendiculares às vigotas), sem padrão de charneiras.
        if lx <= ly:                 # vigotas em x → principais em esq/dir
            ax.add_patch(mpatches.Rectangle((0, 0), lx / 2, ly,
                         facecolor="#FEF9C3", edgecolor="none", alpha=.5))
            ax.add_patch(mpatches.Rectangle((lx / 2, 0), lx / 2, ly,
                         facecolor="#FEE2E2", edgecolor="none", alpha=.5))
        else:                        # vigotas em y → principais em inf/sup
            ax.add_patch(mpatches.Rectangle((0, 0), lx, ly / 2,
                         facecolor="#FEF9C3", edgecolor="none", alpha=.5))
            ax.add_patch(mpatches.Rectangle((0, ly / 2), lx, ly / 2,
                         facecolor="#FEE2E2", edgecolor="none", alpha=.5))
    else:
        # laje 2 direções: áreas tributárias por charneiras plásticas
        ap = _apoios_dict()
        n = 160
        w = {"apoiado": 1.0, "engastado": 1.0 / np.sqrt(3), "livre": 1e9}
        xs = (np.arange(n) + 0.5) / n * lx
        ys = (np.arange(n) + 0.5) / n * ly
        X, Y = np.meshgrid(xs, ys)
        D = np.stack([X * w[ap["esq"]], (lx - X) * w[ap["dir"]],
                      Y * w[ap["inf"]], (ly - Y) * w[ap["sup"]]])
        idx = D.argmin(axis=0)
        cmap = matplotlib.colors.ListedColormap(
            ["#DBEAFE", "#DCFCE7", "#FEF9C3", "#FEE2E2"])
        ax.imshow(idx.T, origin="lower", extent=[0, lx, 0, ly], cmap=cmap,
                  alpha=0.55, aspect="auto", zorder=0)
    # contorno da laje
    ax.add_patch(mpatches.Rectangle((0, 0), lx, ly, fill=False,
                 edgecolor=NAVY, lw=2.2, zorder=3))
    # direção da armação
    if is_trel:
        d_short = "x" if lx <= ly else "y"
        nlin = 7
        for k in range(1, nlin):
            if d_short == "x":
                ax.plot([0, lx], [ly * k / nlin, ly * k / nlin], color="#64748B",
                        lw=0.8, ls=(0, (6, 4)), zorder=2)
            else:
                ax.plot([lx * k / nlin, lx * k / nlin], [0, ly], color="#64748B",
                        lw=0.8, ls=(0, (6, 4)), zorder=2)
        ax.text(lx / 2, ly / 2, "vigotas\n↕" if d_short == "y" else "vigotas\n↔",
                ha="center", va="center", fontsize=9, color="#334155",
                fontweight="bold", zorder=4,
                bbox=dict(boxstyle="round", fc="white", ec="#94A3B8", alpha=.85))
    else:
        ax.text(lx / 2, ly / 2,
                f"maciça\narmada em {res['direcao']} direç"
                f"{'ões' if res['direcao'] == 2 else 'ão'}",
                ha="center", va="center", fontsize=9, color="#334155",
                fontweight="bold", zorder=4,
                bbox=dict(boxstyle="round", fc="white", ec="#94A3B8", alpha=.85))
    # bordas engastadas (hachura) e vigas com carga
    seg = {"sup": ((0, ly), (lx, ly)), "inf": ((0, 0), (lx, 0)),
           "esq": ((0, 0), (0, ly)), "dir": ((lx, 0), (lx, ly))}
    ap_real = _apoios_dict() if not is_trel else {e: "apoiado" for e in ml.BORDAS}
    for e, ((x0, y0), (x1, y1)) in seg.items():
        eng = ap_real.get(e) == "engastado"
        ax.plot([x0, x1], [y0, y1], color="#B45309" if eng else NAVY,
                lw=5 if eng else 3, solid_capstyle="butt", zorder=5)
        # rótulo da viga + carga
        xm, ym = (x0 + x1) / 2, (y0 + y1) / 2
        dx, dy = (0, -0.06 * ly) if e in ("sup",) else (0, 0.05 * ly) if e == "inf" \
            else (0.10 * lx, 0) if e == "esq" else (-0.10 * lx, 0)
        ax.annotate(f"{VIGA_NOME[e]}\n{_fN(reac[e]['q'])} {un_fm}",
                    (xm, ym), (xm + dx, ym + dy), ha="center", va="center",
                    fontsize=8, color="#0F172A", fontweight="bold", zorder=6,
                    bbox=dict(boxstyle="round", fc="#FFFFFF", ec=NAVY, alpha=.9))
    # pilares nos cantos
    pc = {"P1": (0, ly), "P2": (lx, ly), "P3": (0, 0), "P4": (lx, 0)}
    for pl in pilares:
        x, y = pc[pl["nome"]]
        ax.plot(x, y, "s", ms=15, color="#B91C1C", mec="white", mew=1.5,
                zorder=7)
        ax.annotate(f"{pl['nome']}\n{_fN(pl['Nk'])} {un_f}", (x, y),
                    (x + (0.13 * lx if x == 0 else -0.13 * lx),
                     y + (0.11 * ly if y == 0 else -0.11 * ly)),
                    ha="center", va="center", fontsize=7.5, color="#7a1010",
                    fontweight="bold", zorder=8,
                    bbox=dict(boxstyle="round", fc="#FEE2E2", ec="#B91C1C",
                              alpha=.95))
    ax.set_xlim(-0.22 * lx, 1.22 * lx)
    ax.set_ylim(-0.20 * ly, 1.20 * ly)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title(f"Pano {lx:.2f} × {ly:.2f} m — reações nas vigas (kN/m) e "
                 f"cargas nos pilares ({un_f})", fontsize=9.5, color=NAVY,
                 fontweight="bold")
    return fig


# ================================================= RESULTADOS ==========
sec(5, "Resultado da laje", destaque=True)

# veredito de flecha
_cor = {"verde": ("🟢", "APROVADA (flecha OK)"), "amarelo": ("🟡", "no limite"),
        "vermelho": ("🔴", "flecha excede o limite")}
ic, txt = _cor[fl["nivel"]]
if fl["nivel"] == "verde":
    st.success(f"{ic} Laje **{txt}**.")
elif fl["nivel"] == "amarelo":
    st.warning(f"{ic} Laje **{txt}** — revise a espessura/altura.")
else:
    st.error(f"{ic} Laje **{txt}** — aumente a espessura/altura ou reduza o vão.")

m1, m2, m3 = st.columns(3)
m1.metric("Carga total p", f"{_f2(res['p'])} kN/m²",
          f"{res['p'] * 101.9716:.0f} kgf/m²", delta_color="off")
m2.metric("Flecha total", f"{_f2(fl['total_mm'], 1)} mm",
          f"limite {_f2(fl['lim_visual_mm'], 1)} mm", delta_color="off")
if is_trel:
    m3.metric("Direção", "1 (menor vão)")
else:
    m3.metric("λ = ly/lx", f"{_f2(res['lambda'])}",
              f"armada em {res['direcao']} direç.", delta_color="off")

for a in res.get("avisos", []):
    st.warning("⚠️ " + a)

# desenho do pano
mostrar_figura(fig_pano())

# tabela de cargas
sec(6, "Cargas na laje")
tabela([
    {"Parcela": "Peso próprio", "kN/m²": _f2(res['g_pp']),
     "kgf/m²": f"{res['g_pp'] * 101.9716:.0f}"},
    {"Parcela": "Revestimento", "kN/m²": _f2(ss.laje_grev),
     "kgf/m²": f"{ss.laje_grev * 101.9716:.0f}"},
    {"Parcela": "Parede", "kN/m²": _f2(ss.laje_gpar),
     "kgf/m²": f"{ss.laje_gpar * 101.9716:.0f}"},
    {"Parcela": "Uso (NBR 6120)", "kN/m²": _f2(q_uso),
     "kgf/m²": f"{q_uso * 101.9716:.0f}"},
    {"Parcela": "TOTAL p", "kN/m²": _f2(res['p']),
     "kgf/m²": f"{res['p'] * 101.9716:.0f}"},
])

# momentos e armadura
sec(7, "Esforços e armadura")
if is_trel:
    tabela([
        {"Item": "Momento no vão (caract.)", "Valor": f"{_f2(res['M'])} kN·m/m"},
        {"Item": "Momento de cálculo Md", "Valor": f"{_f2(res['Md'])} kN·m/m"},
        {"Item": "Cortante V", "Valor": f"{_f2(res['V'])} kN/m"},
        {"Item": "Armadura na nervura", "Valor":
         (f"{_f2(res['As_por_m'])} cm²/m" if res['As_por_m'] else "seção ↑")},
        {"Item": "Altura recomendada", "Valor":
         f"h ≈ {res['h_reco']:.0f} cm" + ("" if res['ok_vao'] else " ⚠️ subir h")},
    ])
else:
    mm = res["momentos"]
    ar = res["armaduras"]

    def _asfmt(v):
        return _f2(v) if v else "seção ↑"

    linhas = [
        {"Direção": "Vão x (+)", "M caract.": _f2(mm['mx_pos']),
         "Md": _f2(mm['Mdx']), "As (cm²/m)": _asfmt(ar['x_pos']['As_adot'])},
        {"Direção": "Vão y (+)", "M caract.": _f2(mm['my_pos']),
         "Md": _f2(mm['Mdy']), "As (cm²/m)": _asfmt(ar['y_pos']['As_adot'])},
    ]
    if mm["mx_eng"] > 0:
        linhas.append({"Direção": "Engaste x (−)", "M caract.": _f2(mm['mx_eng']),
                       "Md": _f2(mm['Mdxe']), "As (cm²/m)": _asfmt(ar['x_neg']['As_adot'])})
    if mm["my_eng"] > 0:
        linhas.append({"Direção": "Engaste y (−)", "M caract.": _f2(mm['my_eng']),
                       "Md": _f2(mm['Mdye']), "As (cm²/m)": _asfmt(ar['y_neg']['As_adot'])})
    tabela(linhas)
    st.caption("Momentos em kN·m/m; armadura As em cm²/m (por faixa de 1 m).")

# flecha detalhada
sec(8, "Flecha (ELS)")
_ff = fl.get("fator_fissuracao", 1.0)
_estadio = ("Estádio II (fissurada, Branson)" if _ff > 1.01
            else "Estádio I (não fissurada)")
tabela([
    {"Item": "Flecha imediata (quase-perm.)", "Valor": f"{_f2(fl['imediata_mm'])} mm"},
    {"Item": "Flecha total (com fluência ×3)", "Valor": f"{_f2(fl['total_mm'])} mm"},
    {"Item": "Rigidez adotada", "Valor": _estadio},
    {"Item": "Limite visual  L/250", "Valor":
     f"{_f2(fl['lim_visual_mm'], 1)} mm  " + ("✅" if fl['ok_visual'] else "🔴")},
    {"Item": "Limite após alvenaria", "Valor":
     f"{_f2(fl['lim_alv_mm'], 1)} mm  " + ("✅" if fl['ok_alv'] else "🔴")},
])
if fl["contraflecha_mm"] > 0:
    st.info(f"💡 Sugestão de **contra-flecha ≈ {fl['contraflecha_mm']:.0f} mm** "
            f"(≤ L/350) para compensar a flecha visual.")

# reações por viga
sec(9, f"Reações da laje nas vigas ({un_fm})")
tabela([{"Viga": VIGA_NOME[e], "Borda": nome, "Comprimento":
         f"{_f2(reac[e]['L'])} m", "Carga q": f"{_fN(reac[e]['q'])} {un_fm}"}
        for e, nome in LADOS])

# cargas nos pilares
sec(10, f"Cargas estimadas nos pilares ({un_f})")
tabela([{"Pilar": p["nome"], "Nk (característica)": f"{_fN(p['Nk'])} {un_f}",
         "Nd (cálculo ×1,4)": f"{_fN(p['Nk'] * 1.4)} {un_f}"} for p in pilares])
st.caption("Carga de canto = metade da reação de cada viga adjacente + peso "
           "próprio estimado da viga. É pré-dimensionamento — confira no "
           "módulo de Pilares.")


# ================================================= INTEGRAÇÃO ==========
sec(11, "Integração — enviar para os módulos", destaque=True)
ci1, ci2 = st.columns(2)
with ci1:
    st.markdown("**➡️ Enviar uma viga para o módulo de Vigas**")
    vsel = st.selectbox("Qual viga?", [f"{VIGA_NOME[e]} — borda {nome} "
                        f"(L={_f2(reac[e]['L'])} m, q={_fN(reac[e]['q'])} {un_fm})"
                        for e, nome in LADOS], key="viga_sel")
    e_sel = LADOS[[f"{VIGA_NOME[e]}" for e, _ in LADOS].index(vsel.split(" —")[0])][0]
    if st.button("🏗️ Enviar para Vigas", width="stretch", key="btn_viga"):
        ss.viga_b, ss.viga_h = 14.0, 40.0
        ss.viga_fck, ss.viga_cob = int(ss.laje_fck), 2.5
        ss.lista_vaos = [{"tipo": "Normal", "L": float(reac[e_sel]["L"]),
                          "q": float(reac[e_sel]["q"]), "P": 0.0, "a": 0.0}]
        ss.res = None
        ss.edit_index = None
        st.toast(f"{VIGA_NOME[e_sel]} enviada para Vigas: "
                 f"L={_f2(reac[e_sel]['L'])} m · q={_fN(reac[e_sel]['q'])} "
                 f"{un_fm} (seção 14×40).", icon="🏗️")
        try:
            st.switch_page("pagina_vigas.py")
        except Exception:
            st.info("Viga carregada. Abra a aba **Vigas** no seletor acima "
                    "para ver e calcular.")
with ci2:
    st.markdown("**➡️ Enviar um pilar para o módulo de Pilares**")
    psel = st.selectbox("Qual pilar?", [f"{p['nome']} — Nk={_fN(p['Nk'])} {un_f}"
                        for p in pilares], key="pil_sel")
    p_i = [p["nome"] for p in pilares].index(psel.split(" —")[0])
    if st.button("🏛️ Enviar para Pilares", width="stretch", key="btn_pil"):
        ss.pilar_b, ss.pilar_h, ss.pilar_l0 = 19.0, 19.0, 2.8
        ss.pilar_fck, ss.pilar_caa = int(ss.laje_fck), "II"
        ss.pilar_Nk = float(pilares[p_i]["Nk"]) * fu
        ss.res_pilar = None
        st.toast(f"{pilares[p_i]['nome']} enviado para Pilares: "
                 f"Nk={_fN(pilares[p_i]['Nk'])} {un_f}.", icon="🏛️")
        try:
            st.switch_page("pagina_pilar.py")
        except Exception:
            st.info("Pilar carregado. Abra a aba **Pilares** no seletor "
                    "acima para ver e calcular.")


# ================================================= QUANTITATIVOS ========
sec(12, "Quantitativos do pano")
q = res["quant"]
if is_trel:
    tabela([
        {"Material": "Área do pano", "Quantidade": f"{_f2(q['area'])} m²"},
        {"Material": "Concreto (capa+nervuras)", "Quantidade":
         f"{_f2(q['vol_conc'], 3)} m³"},
        {"Material": "Vigotas treliçadas", "Quantidade":
         f"{q['n_vigotas']} un · {_f2(q['comp_vigotas'], 1)} m"},
        {"Material": "Elementos de enchimento", "Quantidade":
         f"≈ {q['n_element']} un"},
    ])
else:
    tabela([
        {"Material": "Área do pano", "Quantidade": f"{_f2(q['area'])} m²"},
        {"Material": "Concreto", "Quantidade": f"{_f2(q['vol_conc'], 3)} m³"},
        {"Material": "Forma (fundo)", "Quantidade": f"{_f2(q['forma'])} m²"},
        {"Material": "Aço (estimado)", "Quantidade":
         f"{_f2(q['kg_aco'], 1)} kg ({_f2(q['taxa_aco'], 1)} kg/m²)"},
    ])


# ================================================= COMPARATIVO ==========
sec(13, "Comparativo rápido — treliçada × maciça")
h_mac_c = float(ss.laje_h_mac) if not is_trel else max(8.0, min(lx0, ly0) * 100 / 40)
comp = _comparativo(lx0, ly0, int(ss.laje_fck), ss.laje_grev, q_uso,
                    ss.laje_gpar, h_mac_c, int(ss.laje_h_trel), ss.laje_ench)
cm_, ct_ = comp["macica"], comp["trelicada"]


def _sit(nivel):
    ic = {"verde": "🟢 OK", "amarelo": "🟡 no limite",
          "vermelho": "🔴 excede"}
    return ic.get(nivel, nivel)


tabela([
    {"Critério": "Peso próprio (kN/m²)", "Treliçada": _f2(ct_['g_pp']),
     "Maciça": _f2(cm_['g_pp'])},
    {"Critério": "Carga total p (kN/m²)", "Treliçada": _f2(ct_['p']),
     "Maciça": _f2(cm_['p'])},
    {"Critério": "Flecha total (mm)", "Treliçada": _f2(ct_['flecha']['total_mm'], 1),
     "Maciça": _f2(cm_['flecha']['total_mm'], 1)},
    {"Critério": "Situação flecha", "Treliçada": _sit(ct_['flecha']['nivel']),
     "Maciça": _sit(cm_['flecha']['nivel'])},
])
_leve = "treliçada" if ct_["g_pp"] < cm_["g_pp"] else "maciça"
st.caption(f"➡️ A **{_leve}** é mais leve neste pano. A treliçada costuma "
           "reduzir peso próprio e fôrma; a maciça vence vãos bidirecionais "
           "e cargas concentradas com mais folga.")


# ================================================= PDF ==================
def gerar_pdf():
    buf = io.BytesIO()
    with PdfPages(buf) as pdf:
        fig = plt.figure(figsize=(8.27, 11.69))       # A4
        fig.text(0.5, 0.95, "POLOTTO ENGENHARIA — Memória de Cálculo de Laje",
                 ha="center", fontsize=13, fontweight="bold", color=NAVY)
        linhas = [
            f"Tipo: {ss.laje_tipo}", f"Pano: {lx:.2f} × {ly:.2f} m  (λ={lam:.2f})",
            (f"Altura: {res['h']} cm ({res.get('capa','')} cap)" if is_trel
             else f"Espessura: {res['h']:.0f} cm  ·  {res['direcao']} direção(ões)"),
            f"fck = {ss.laje_fck} MPa   ·   Uso: {ss.laje_uso} (q={q_uso:.1f} kN/m²)",
            "",
            f"CARGAS: pp={res['g_pp']:.2f}  rev={ss.laje_grev:.2f}  "
            f"par={ss.laje_gpar:.2f}  uso={q_uso:.2f}  →  p={res['p']:.2f} kN/m²",
            "",
            "FLECHA (ELS): imediata=%.2f mm · total(×3)=%.2f mm · limite L/250=%.1f mm · %s"
            % (fl["imediata_mm"], fl["total_mm"], fl["lim_visual_mm"],
               "OK" if fl["nivel"] != "vermelho" else "EXCEDE"),
            "",
            "REAÇÕES NAS VIGAS (kN/m, característica):",
        ]
        for e, nome in LADOS:
            linhas.append(f"   {VIGA_NOME[e]} (borda {nome}, L={reac[e]['L']:.2f} m): "
                          f"q = {reac[e]['q']:.2f} kN/m")
        linhas += ["", "CARGAS NOS PILARES (kN):"]
        for p in pilares:
            linhas.append(f"   {p['nome']}: Nk = {p['Nk']:.1f} kN  "
                          f"(Nd = {p['Nk'] * 1.4:.1f} kN)")
        linhas += ["", "Norma: NBR 6118 / 6120 / 14859.",
                   "Ferramenta de PRÉ-DIMENSIONAMENTO — não substitui projeto "
                   "estrutural assinado por profissional habilitado."]
        fig.text(0.08, 0.88, "\n".join(linhas), va="top", fontsize=9,
                 family="monospace")
        pdf.savefig(fig)
        plt.close(fig)
        fig2 = fig_pano()
        pdf.savefig(fig2)
        plt.close(fig2)
    return buf.getvalue()


sec(14, "Memória de cálculo (PDF)")
# Gera o PDF só quando solicitado (evita reprocessar a figura a cada rerun).
if st.button("📄 Preparar memória em PDF", width="stretch"):
    ss.laje_pdf = gerar_pdf()
    ss.laje_pdf_nome = f"laje_{lx:.1f}x{ly:.1f}.pdf"
if ss.get("laje_pdf"):
    st.download_button("⬇️ Baixar PDF gerado", data=ss.laje_pdf,
                       file_name=ss.get("laje_pdf_nome", "laje.pdf"),
                       mime="application/pdf", width="stretch")

st.divider()
st.caption("⚠️ Ferramenta de **pré-dimensionamento e estudo**. Não substitui "
           "o projeto estrutural elaborado e assinado por profissional "
           "habilitado (ART/RRT).")
