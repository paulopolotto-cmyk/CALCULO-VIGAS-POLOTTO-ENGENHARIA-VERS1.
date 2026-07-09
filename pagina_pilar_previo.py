# -*- coding: utf-8 -*-
"""
Página PILARES PRÉVIOS — Polotto Engenharia.

Pré-dimensionamento de pilares de CASAS TÉRREAS pelo método das ÁREAS DE
INFLUÊNCIA (áreas tributárias). Para modelos típicos de mercado (60, 120,
220, 300, 350 e 400 m²) estima a carga que chega a um pilar de CANTO, de
BORDA e CENTRAL e sugere a seção usando o MESMO motor NBR 6118 do programa
de Pilares (motor_pilar.py) — sem alterá-lo.

Programa NOVO e independente: não modifica os cálculos de Vigas nem de
Pilares. É um PRÉ-dimensionamento rápido; o dimensionamento final de cada
pilar deve ser conferido no programa "Pilares" com a carga real do projeto.
"""
import math

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import streamlit as st

import motor_pilar as mp
from ui_comum import (NAVY, CINZA_TXT, aplicar_estilo, header, sec,
                      seletor_unidade, tabela, seletor_pagina, mostrar_figura)

aplicar_estilo()
header("Pilares Prévios — Casas Térreas",
       "Pré-dimensionamento por área de influência · NBR 6118 / 6120")
seletor_pagina("previo")

# Fonte um pouco maior no corpo de texto desta página (melhor leitura na obra)
st.markdown("""<style>
[data-testid="stMarkdownContainer"] p,
[data-testid="stMarkdownContainer"] li { font-size: 1.08rem; line-height: 1.55; }
[data-testid="stCaptionContainer"] p,
[data-testid="stCaptionContainer"] { font-size: 1.0rem !important; }
[data-testid="stAlert"] p, [data-testid="stAlert"] li { font-size: 1.06rem;
  line-height: 1.55; }
</style>""", unsafe_allow_html=True)

# unidade de força (kN ou kgf) — cálculo interno sempre em kN
fu, un_f, un_fm = seletor_unidade()
_un_area = "kgf/m²" if fu > 1 else "kN/m²"
_ca = 0 if fu > 1 else 2


def _fN(v_kN):
    """Formata uma força (kN internos) na unidade escolhida."""
    v = v_kN * fu
    if fu > 1:
        return f"{v:,.0f} {un_f}".replace(",", ".")
    return f"{v:,.1f} {un_f}".replace(",", " ").replace(".", ",")


def _fa(v_kN):
    """Formata carga de área (kN/m² internos) na unidade escolhida."""
    return f"{v_kN * fu:.{_ca}f}"


# ------------------------------------------------------- modelos de mercado
MODELOS = {
    "Casa 60 m² — 2 dormitórios (padrão popular)": {
        "area": 60, "vao": 3.5, "pd": 2.8, "fck": 25, "caa": "II",
        "laje": 2.5, "telhado": 1.0, "revest": 0.5, "sobre": 1.0, "carros": 1,
        "desc": "2 dorm., sala, cozinha, banheiro, hall de distribuição e "
                "pequena área de serviço. Laje pré-moldada + telha cerâmica. "
                "Garagem frontal p/ 1 carro (só cobertura apoiada em 2 "
                "pilares, fora do corpo da casa)."},
    "Casa 120 m² — 3 dormitórios (suítes)": {
        "area": 120, "vao": 4.0, "pd": 2.8, "fck": 25, "caa": "II",
        "laje": 2.5, "telhado": 1.0, "revest": 0.7, "sobre": 1.0, "carros": 2,
        "desc": "3 dorm. (suítes), sala de estar, escritório, hall, lavabo, "
                "cozinha + área gourmet, área de serviço. Garagem p/ 2 "
                "carros."},
    "Casa 220 m² — 4 dormitórios": {
        "area": 220, "vao": 4.0, "pd": 3.0, "fck": 25, "caa": "II",
        "laje": 2.8, "telhado": 1.0, "revest": 0.8, "sobre": 1.0, "carros": 2,
        "desc": "Como a de 120 m² + 1 dorm. (4 no total), sala de TV, "
                "despensa etc. Garagem p/ 2 carros."},
    "Casa 300 m² — alto padrão": {
        "area": 300, "vao": 4.5, "pd": 3.0, "fck": 30, "caa": "II",
        "laje": 3.0, "telhado": 1.1, "revest": 0.9, "sobre": 1.0, "carros": 3,
        "desc": "Padrão superior, todos os cômodos da de 4 dorm., acabamentos "
                "mais pesados. Garagem p/ 3 carros."},
    "Casa 350 m² — alto padrão": {
        "area": 350, "vao": 4.5, "pd": 3.0, "fck": 30, "caa": "II",
        "laje": 3.0, "telhado": 1.1, "revest": 1.0, "sobre": 1.0, "carros": 3,
        "desc": "Alto padrão, vãos maiores e acabamentos pesados. Garagem "
                "p/ 3 carros."},
    "Casa 400 m² — alto padrão": {
        "area": 400, "vao": 5.0, "pd": 3.0, "fck": 30, "caa": "II",
        "laje": 3.0, "telhado": 1.2, "revest": 1.0, "sobre": 1.0, "carros": 3,
        "desc": "Alto padrão, vãos de ~5 m, laje/telhado mais pesados. "
                "Garagem p/ 3+ carros."},
    "Personalizado": {
        "area": 100, "vao": 4.0, "pd": 2.8, "fck": 25, "caa": "II",
        "laje": 2.5, "telhado": 1.0, "revest": 0.7, "sobre": 1.0, "carros": 2,
        "desc": "Defina você mesmo todos os parâmetros abaixo."},
}

# majoração por continuidade das vigas (aumento da reação no apoio)
MAJ = {"canto": 1.00, "borda": 1.10, "central": 1.20}
FCK_OPC = [20, 25, 30, 35, 40, 45, 50]
CAA_OPC = ["I", "II", "III", "IV"]


# ---------------------------------------------------- desenho das tributárias
def fig_influencia(L, cargas):
    fig, ax = plt.subplots(figsize=(6.4, 5.2))
    xs = [0, L, 2 * L]
    ys = [0, L, 2 * L]
    # áreas tributárias representativas
    ax.add_patch(mpatches.Rectangle((L / 2, L / 2), L, L, facecolor="#FCA5A5",
                 edgecolor="none", alpha=.55, zorder=1))          # central
    ax.add_patch(mpatches.Rectangle((L / 2, 0), L, L / 2, facecolor="#93C5FD",
                 edgecolor="none", alpha=.65, zorder=1))          # borda
    ax.add_patch(mpatches.Rectangle((0, 0), L / 2, L / 2, facecolor="#FCD34D",
                 edgecolor="none", alpha=.85, zorder=1))          # canto
    for x in xs:
        ax.plot([x, x], [0, 2 * L], color=NAVY, lw=1.6, zorder=2)
    for y in ys:
        ax.plot([0, 2 * L], [y, y], color=NAVY, lw=1.6, zorder=2)

    def cor(i, j):
        bi, bj = i in (0, 2), j in (0, 2)
        if bi and bj:
            return "#B45309"       # canto (âmbar escuro)
        if bi or bj:
            return "#1E3A8A"       # borda (azul)
        return "#B91C1C"           # central (vermelho)

    for i, x in enumerate(xs):
        for j, y in enumerate(ys):
            ax.plot(x, y, 's', ms=13, color=cor(i, j),
                    markeredgecolor="white", markeredgewidth=1.2, zorder=3)
    ax.text(L / 4, L / 4, f"canto\n{(L / 2) ** 2:.1f} m²", ha="center",
            va="center", fontsize=8, fontweight="bold", color="#7c4a00",
            zorder=4)
    ax.text(L, L / 4, f"borda\n{L * (L / 2):.1f} m²", ha="center", va="center",
            fontsize=8, fontweight="bold", color="#14307a", zorder=4)
    ax.text(L, 1.30 * L, f"central\n{L * L:.1f} m²", ha="center", va="center",
            fontsize=8.2, fontweight="bold", color="#7a1010", zorder=4)
    # carga Nk em CADA pilar (etiqueta junto a todos os 9 marcadores)
    for i, x in enumerate(xs):
        for j, y in enumerate(ys):
            if i == 1 and j == 1:
                continue                     # central -> balão separado
            t = "canto" if (i in (0, 2) and j in (0, 2)) else "borda"
            dx = 0.0 if i == 1 else (-0.42 * L if i == 0 else 0.42 * L)
            dy = 0.0 if j == 1 else (-0.42 * L if j == 0 else 0.42 * L)
            ax.text(x + dx, y + dy, _fN(cargas[t]), ha="center", va="center",
                    fontsize=6.6, fontweight="bold", color=cor(i, j), zorder=6,
                    bbox=dict(boxstyle="round,pad=0.2", fc="white",
                              ec=cor(i, j), alpha=.96))
    ax.annotate(_fN(cargas["central"]), xy=(L, L), xytext=(1.6 * L, L),
                ha="left", va="center", fontsize=6.8, color="#B91C1C",
                fontweight="bold", zorder=6,
                bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="#B91C1C",
                          alpha=.96),
                arrowprops=dict(arrowstyle="->", color="#B91C1C", lw=1.1))
    ax.annotate("", xy=(0, -0.62 * L), xytext=(L, -0.62 * L),
                arrowprops=dict(arrowstyle="<->", color=CINZA_TXT, lw=1.3))
    ax.text(L / 2, -0.74 * L, f"vão = {L:.1f} m", ha="center", va="top",
            fontsize=9, color=CINZA_TXT, fontweight="bold")
    ax.text(L, 2.62 * L, "carga Nk em cada pilar", ha="center", va="bottom",
            fontsize=7.5, color=CINZA_TXT, fontweight="bold")
    ax.set_xlim(-1.0 * L, 3.0 * L)
    ax.set_ylim(-0.9 * L, 2.85 * L)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title("Áreas de influência — canto, borda e central",
                 fontsize=10.5, color=NAVY, fontweight="bold")
    return fig


# --------------------------------------------------- dimensionamento (motor)
def dimensionar(Nk_kN, l0, fck, caa, b_pref):
    """Acha a MENOR seção (a partir de b_pref) que passa no motor NBR 6118."""
    larguras = [float(b_pref)] + [x for x in (19.0, 20.0, 25.0, 30.0)
                                  if x > b_pref]
    alturas = [30.0, 35.0, 40.0, 45.0, 50.0, 60.0, 70.0]
    for b in larguras:
        for h in alturas:
            if h < b:
                continue
            res = mp.calcular_pilar({'b': b, 'h': h, 'l0': l0, 'fck': fck,
                                     'Nk': max(Nk_kN, 0.1), 'caa': caa})
            if res.get('opcoes'):
                op = res['opcoes'][0]
                lam = max(res['direcoes']['x']['lambda'],
                          res['direcoes']['y']['lambda'])
                return {'b': b, 'h': h, 'Nd': res['Nd'], 'op': op, 'lam': lam,
                        'folga': min(op['folga_x'], op['folga_y'])}
    return None


# ============================================================== INTERFACE ===
sec(1, "Escolha o modelo de casa (térrea)")
nome_m = st.selectbox(
    "Modelo de referência", list(MODELOS.keys()),
    help="Modelos térreos típicos de mercado. TODOS os valores abaixo são "
         "editáveis — ajuste ao seu projeto.")
M = MODELOS[nome_m]
st.caption("🏠 " + M["desc"])

sec(2, "Parâmetros estruturais")
c1, c2 = st.columns(2)
vao = c1.number_input(
    "Vão típico entre pilares (malha) [m]", 2.5, 8.0, float(M["vao"]), 0.1,
    "%.2f", help="Distância média entre pilares. Em casas fica entre 3,5 e "
                 "5 m. É o que define as áreas de influência.")
pd = c2.number_input(
    "Pé-direito / altura livre do pilar l₀ [m]", 2.4, 5.0, float(M["pd"]), 0.1,
    "%.2f", help="Altura livre do pilar (do topo do baldrame à viga de "
                 "cobertura). Influencia a esbeltez.")
c3, c4 = st.columns(2)
fck = c3.selectbox("Concreto fck [MPa]", FCK_OPC,
                   index=FCK_OPC.index(int(M["fck"])),
                   help="Resistência do concreto. Casas: 25 a 30 MPa.")
caa = c4.selectbox("Classe de agressividade (CAA)", CAA_OPC,
                   index=CAA_OPC.index(M["caa"]),
                   help="I = rural/seco · II = urbano · III = marinho/"
                        "industrial · IV = respingos de maré. Define o "
                        "cobrimento.")
b_pref = st.select_slider(
    "Largura do pilar (encaixe na parede) [cm]", options=[14, 19, 20, 25],
    value=14, help="Menor dimensão do pilar. 14 cm embute em parede de 15 cm; "
                   "19–20 cm em parede de 20 cm. O programa acha a altura "
                   "necessária.")

sec(3, "Carga da cobertura (o que pesa sobre os pilares)")
st.caption("Casa térrea: os pilares recebem a **laje de forro/cobertura + o "
           "telhado**; as paredes descarregam no baldrame. Valores por m² "
           "conforme NBR 6120 — edite se quiser.")
cc1, cc2 = st.columns(2)
laje = cc1.number_input(
    f"Laje pré-moldada (forro) [{_un_area}]", 0.0, 8.0 * fu, M["laje"] * fu,
    0.1 * fu, f"%.{_ca}f",
    help="Peso próprio da laje pré-moldada de forro (lajota/EPS + capa) ≈ "
         "2,2 a 3,0 kN/m².") / fu
telhado = cc2.number_input(
    f"Telhado (telha + madeira) [{_un_area}]", 0.0, 4.0 * fu, M["telhado"] * fu,
    0.1 * fu, f"%.{_ca}f",
    help="Telha cerâmica + estrutura de madeira, na projeção horizontal ≈ "
         "1,0 kN/m².") / fu
cc3, cc4 = st.columns(2)
revest = cc3.number_input(
    f"Revestimento/regularização [{_un_area}]", 0.0, 4.0 * fu, M["revest"] * fu,
    0.1 * fu, f"%.{_ca}f",
    help="Contrapiso/regularização + forro/gesso.") / fu
sobre = cc4.number_input(
    f"Sobrecarga de cobertura [{_un_area}]", 0.0, 4.0 * fu, M["sobre"] * fu,
    0.1 * fu, f"%.{_ca}f",
    help="Sobrecarga de uso da cobertura (acesso p/ manutenção) — NBR 6120.") \
    / fu
carga = laje + telhado + revest + sobre
st.markdown(f"**Carga total da cobertura = {_fa(carga)} {_un_area}**  "
            f"(= {carga:.2f} kN/m²)")

# -------------------------------------------------------------- resultados
sec(4, "Pilares sugeridos — canto · borda · central", destaque=True)
TIPOS = [("Canto", "canto", "🟨"), ("Borda", "borda", "🟦"),
         ("Central", "central", "🟥")]
AREAS = {"canto": (vao / 2) * (vao / 2), "borda": vao * (vao / 2),
         "central": vao * vao}
linhas = []
detalhe = {}
sec_area_max = 0.0
sec_rec = None
for rot, chave, ic in TIPOS:
    A = AREAS[chave]
    Nk = carga * A * MAJ[chave]
    d = dimensionar(Nk, pd, fck, caa, b_pref)
    detalhe[chave] = (A, Nk, d)
    if d:
        secao = f"{d['b']:.0f}×{d['h']:.0f} cm"
        arm = d['op']['texto']
        uso = f"{min(100.0, 100.0 / max(d['folga'], 1e-6)):.0f}%"
        lam_txt = f"{d['lam']:.0f}"
        nd_txt = _fN(d['Nd'])
        if d['b'] * d['h'] > sec_area_max:
            sec_area_max = d['b'] * d['h']
            sec_rec = secao
    else:
        secao, arm, uso, lam_txt, nd_txt = "↑ aumentar", "—", "—", "—", "—"
    linhas.append({"Pilar": f"{ic} {rot}", "Área infl.": f"{A:.1f} m²",
                   "Nk": _fN(Nk), "Nd": nd_txt, "Seção": secao,
                   "Armadura": arm, "λ": lam_txt, "Uso": uso})
tabela(linhas)
if sec_rec:
    st.success(f"✅ Para **padronizar a obra**, uma seção única de "
               f"**{sec_rec}** atende os três tipos de pilar deste modelo "
               f"(canto, borda e central).")

sec(5, "Como a área de influência foi considerada")
st.caption("Cada pilar recebe a carga de **metade do vão para cada lado**. "
           "Canto = ¼ do painel; borda = ½ painel; central = 1 painel "
           "inteiro. Sobre isso aplica-se a majoração de continuidade "
           "(canto 1,00 · borda 1,10 · central 1,20).")
_cargas_fig = {c: detalhe[c][1] for c in ("canto", "borda", "central")}
mostrar_figura(fig_influencia(vao, _cargas_fig))

sec(6, "Memória de cálculo")
for rot, chave, ic in TIPOS:
    A, Nk, d = detalhe[chave]
    txt = (f"**{ic} Pilar de {rot.lower()}**: A_infl = {A:.2f} m² × "
           f"{carga:.2f} kN/m² × {MAJ[chave]:.2f} (continuidade) → "
           f"Nk = **{_fN(Nk)}**")
    if d:
        txt += (f"; Nd = γf·γn·Nk = **{_fN(d['Nd'])}** → seção "
                f"**{d['b']:.0f}×{d['h']:.0f} cm** com **{d['op']['texto']}** "
                f"(λ = {d['lam']:.0f}).")
    else:
        txt += " — carga/esbeltez pedem seção maior (ver programa Pilares)."
    st.markdown(txt)

with st.expander("🚗 Cobertura de garagem/varanda (só telhado leve) — "
                 "opcional"):
    st.caption("Pilares que sustentam apenas uma cobertura leve (telha + "
               "estrutura), SEM laje — ex.: garagem frontal fora do corpo "
               "da casa.")
    gc1, gc2 = st.columns(2)
    A_gar = gc1.number_input(
        "Área de telhado por pilar [m²]", 2.0, 40.0, float(M["carros"]) * 6.0,
        1.0, "%.1f", help="Área de cobertura que chega em cada pilar da "
                          "garagem (~5 a 7 m² por vaga).")
    q_gar = gc2.number_input(
        f"Carga do telhado [{_un_area}]", 0.5 * fu, 3.0 * fu, 1.5 * fu,
        0.1 * fu, f"%.{_ca}f",
        help="Telha + estrutura + sobrecarga leve.") / fu
    Nk_g = q_gar * A_gar
    dg = dimensionar(Nk_g, pd, fck, caa, b_pref)
    if dg:
        st.markdown(f"Nk ≈ **{_fN(Nk_g)}** → seção **{dg['b']:.0f}×"
                    f"{dg['h']:.0f} cm** com **{dg['op']['texto']}** "
                    f"(λ = {dg['lam']:.0f}).")
    else:
        st.warning("Carga alta para a esbeltez — dimensione no programa "
                   "Pilares.")

sec(7, "Estimativa de quantidade de pilares")
_Lx = math.sqrt(M["area"] * 1.35)
_Ly = M["area"] / _Lx
_nbx = max(1, round(_Lx / vao))
_nby = max(1, round(_Ly / vao))
_npil = (_nbx + 1) * (_nby + 1)
st.caption(f"Estimativa grosseira para ~{M['area']:.0f} m² "
           f"(≈ {_Lx:.1f} × {_Ly:.1f} m) com malha de {vao:.1f} m: "
           f"**≈ {_npil} pilares** (grelha {_nbx + 1} × {_nby + 1}). "
           f"Ajuste ao projeto arquitetônico real.")

sec(8, "Importante — limites deste pré-dimensionamento")
st.info(
    "• Método das **áreas de influência** (tributárias): é uma **estimativa** "
    "para orçamento/lançamento, não substitui o cálculo do pórtico.\n\n"
    "• Considera **só a cobertura** (laje de forro + telhado). As paredes "
    "vão ao baldrame. Se houver **2º pavimento ou laje de piso**, este "
    "programa NÃO se aplica.\n\n"
    "• **Não** inclui vento, sismo, empuxo, vigas em balanço nem momentos "
    "aplicados.\n\n"
    "• Coeficientes de continuidade usuais (canto 1,00 · borda 1,10 · "
    "central 1,20).\n\n"
    "• As seções sugeridas já respeitam a NBR 6118 (mín. 14 cm, área ≥ "
    "360 cm², esbeltez λ ≤ 90) — verificadas pelo mesmo motor do programa "
    "Pilares.")
st.markdown("👉 Para o **dimensionamento final** de cada pilar, abra o "
            "programa **Pilares** e informe o **Nk** obtido aqui.")
