# -*- coding: utf-8 -*-
"""Projeto Completo — LAJES pré-moldadas (treliçadas).

Detecta os CÔMODOS (painéis fechados pelas vigas) na planta de forma, define a
direção das vigotas no MENOR vão, atribui a sobrecarga por TIPO de cômodo
(NBR 6120) e calcula cada laje no motor_laje (NBR 6118). As reações de cada
laje viram carga nas vigas. Módulo NOVO — não altera os módulos aprovados.
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

import motor_laje as ml

TIPO_PADRAO = "Dormitório / sala / cozinha"
FCK = 25.0

_TIPO_CURTO = {
    "Dormitório / sala / cozinha": "Dorm/sala",
    "Banheiro": "Banho",
    "Despensa / área de serviço / lavanderia": "Á. serviço",
    "Corredor (dentro da unidade)": "Corredor",
    "Corredor / hall de uso comum": "Hall",
    "Escritório": "Escrit.",
    "Sótão": "Sótão",
    "Forro (sem acesso a pessoas)": "Forro",
    "Terraço / varanda (com acesso)": "Varanda",
    "Garagem / veículos leves (≤ 25 kN)": "Garagem",
}


def tipo_curto(t):
    return _TIPO_CURTO.get(t, (t or "")[:9])


# ------------------------------------------------------- detecção dos cômodos
def _segmentos(vigas):
    """Separa as vigas em horizontais (y, x0, x1) e verticais (x, y0, y1)."""
    H, V = [], []
    for v in vigas:
        x1, y1 = v.get("x1_m"), v.get("y1_m")
        x2, y2 = v.get("x2_m"), v.get("y2_m")
        if None in (x1, y1, x2, y2):
            continue
        if abs(y1 - y2) <= abs(x1 - x2):        # horizontal
            H.append((round((y1 + y2) / 2, 2), min(x1, x2), max(x1, x2)))
        else:                                    # vertical
            V.append((round((x1 + x2) / 2, 2), min(y1, y2), max(y1, y2)))
    return H, V


def detectar_comodos(vigas, tol=0.30, area_min=1.5, lado_min=0.6):
    """Acha os retângulos fechados por vigas (cômodos). Devolve lista de dicts
    com x0,x1,y0,y1, centro, Lx, Ly, menor, maior, área e direção da vigota."""
    H, V = _segmentos(vigas)
    Xs = sorted(set(round(x, 2) for x, _, _ in V))
    Ys = sorted(set(round(y, 2) for y, _, _ in H))
    if len(Xs) < 2 or len(Ys) < 2:
        return []

    def beam_h(y, x0, x1):
        return any(abs(yy - y) <= tol and a <= x0 + tol and b >= x1 - tol
                   for yy, a, b in H)

    def beam_v(x, y0, y1):
        return any(abs(xx - x) <= tol and a <= y0 + tol and b >= y1 - tol
                   for xx, a, b in V)

    nX, nY = len(Xs) - 1, len(Ys) - 1
    parent = {(i, j): (i, j) for i in range(nX) for j in range(nY)}

    def find(c):
        root = c
        while parent[root] != root:
            root = parent[root]
        while parent[c] != root:
            parent[c], c = root, parent[c]
        return root

    def union(a, b):
        parent[find(a)] = find(b)

    # células vizinhas ficam no MESMO cômodo se NÃO há viga na fronteira
    for i in range(nX):
        for j in range(nY):
            if i + 1 < nX and not beam_v(Xs[i + 1], Ys[j], Ys[j + 1]):
                union((i, j), (i + 1, j))
            if j + 1 < nY and not beam_h(Ys[j + 1], Xs[i], Xs[i + 1]):
                union((i, j), (i, j + 1))

    grupos = {}
    for i in range(nX):
        for j in range(nY):
            grupos.setdefault(find((i, j)), []).append((i, j))

    comodos = []
    for cells in grupos.values():
        cset = set(cells)
        fechado = True
        for (i, j) in cells:                     # todas as bordas externas = viga?
            if ((i - 1, j) not in cset and not beam_v(Xs[i], Ys[j], Ys[j + 1])) or \
               ((i + 1, j) not in cset and not beam_v(Xs[i + 1], Ys[j], Ys[j + 1])) or \
               ((i, j - 1) not in cset and not beam_h(Ys[j], Xs[i], Xs[i + 1])) or \
               ((i, j + 1) not in cset and not beam_h(Ys[j + 1], Xs[i], Xs[i + 1])):
                fechado = False
                break
        if not fechado:
            continue
        x0 = min(Xs[i] for i, j in cells)
        x1 = max(Xs[i + 1] for i, j in cells)
        y0 = min(Ys[j] for i, j in cells)
        y1 = max(Ys[j + 1] for i, j in cells)
        area = sum((Xs[i + 1] - Xs[i]) * (Ys[j + 1] - Ys[j]) for i, j in cells)
        Lx, Ly = round(x1 - x0, 2), round(y1 - y0, 2)
        if area < area_min or min(Lx, Ly) < lado_min:
            continue
        # retângulo cheio? (união de células forma o retângulo do bounding box)
        preenchido = abs(area - Lx * Ly) < 0.05 * Lx * Ly
        comodos.append(dict(x0=x0, x1=x1, y0=y0, y1=y1,
                            cx=round((x0 + x1) / 2, 2), cy=round((y0 + y1) / 2, 2),
                            Lx=Lx, Ly=Ly, area=round(area, 2),
                            menor=min(Lx, Ly), maior=max(Lx, Ly),
                            vigota=("H" if Lx <= Ly else "V"),  # corre no menor vão
                            retangular=preenchido))
    comodos.sort(key=lambda c: (-c["cy"], c["cx"]))    # cima→baixo, esq→dir
    for i, c in enumerate(comodos):
        c["nome"] = f"L{i+1}"
    return comodos


# ------------------------------------------------------------ cálculo da laje
def altura_laje(menor_m, continua=False):
    """Menor altura tabelada que atende o pré-dimensionamento (flecha)."""
    h_reco = ml.h_recomendada_trelica(menor_m, continua)
    for h in (12, 16, 20, 25):
        if h >= h_reco - 0.5:
            return h
    return 25


def calcular_laje(comodo, tipo=TIPO_PADRAO, vigota=None, fck=FCK,
                  telhado=False, g_telhado=0.5):
    """Roda uma laje treliçada no motor_laje. `vigota` (H/V) força a direção;
    `telhado`=True soma o peso do telhado (g_telhado kN/m²) à carga permanente.
    O peso próprio da laje já é incluído pelo motor."""
    d = dict(comodo)
    if vigota:
        d["vigota"] = vigota
    # o vão das vigotas é o lado perpendicular à direção em que elas correm
    if d["vigota"] == "H":            # vigotas correm em x -> vencem Lx
        lx, ly = d["Lx"], d["Ly"]
    else:                              # vigotas correm em y -> vencem Ly
        lx, ly = d["Ly"], d["Lx"]
    q = ml.CARGAS_USO.get(tipo, 1.5)
    g_extra = float(g_telhado) if telhado else 0.0    # peso do telhado (kN/m²)
    h = altura_laje(min(lx, ly))
    dados = {"lx": lx, "ly": ly, "h": h, "enchimento": "EPS",
             "continuidade": "biapoiada", "fck": fck, "g_rev": 1.0,
             "g_parede": g_extra, "q_uso": q}
    r = ml.calcular_laje_trelicada(dados)
    det = None if r.get("erros") else ml.detalhar_armadura_trelica(r)
    aco = sum(x["peso"] for x in det["quadro"] if x["kind"] == "barra") if det else 0.0
    vig = (r.get("quant") or {}).get("comp_vigotas", 0.0)
    return dict(nome=comodo["nome"], comodo=comodo, tipo=tipo, q_uso=q,
                vigota=d["vigota"], h=h, telhado=telhado, g_telhado=g_extra,
                res=r, det=det, aco_barras=round(aco, 1), vigotas_m=round(vig, 1),
                area=comodo["area"], falha=bool(r.get("erros")))


def calcular_lajes(comodos, tipos=None, vigotas=None, telhados=None,
                   fck=FCK, g_telhado=0.5):
    """Calcula todas as lajes. tipos/vigotas/telhados = dicts {nome: valor}."""
    tipos = tipos or {}
    vigotas = vigotas or {}
    telhados = telhados or {}
    return [calcular_laje(c, tipo=tipos.get(c["nome"], TIPO_PADRAO),
                          vigota=vigotas.get(c["nome"]),
                          telhado=bool(telhados.get(c["nome"], False)),
                          g_telhado=g_telhado, fck=fck)
            for c in comodos]


def comodo_manual(x0, x1, y0, y1, nome):
    """Cria um cômodo (laje) lançado à mão pelo engenheiro, a partir dos limites."""
    x0, x1 = sorted((float(x0), float(x1)))
    y0, y1 = sorted((float(y0), float(y1)))
    Lx, Ly = round(x1 - x0, 2), round(y1 - y0, 2)
    return dict(x0=x0, x1=x1, y0=y0, y1=y1,
                cx=round((x0 + x1) / 2, 2), cy=round((y0 + y1) / 2, 2),
                Lx=Lx, Ly=Ly, area=round(Lx * Ly, 2),
                menor=min(Lx, Ly), maior=max(Lx, Ly),
                vigota=("H" if Lx <= Ly else "V"), retangular=True,
                nome=nome, manual=True)


def tipos_disponiveis():
    return list(ml.CARGAS_USO.keys())


def resumo_lajes(lajes):
    """Totais das lajes: aço em barras a comprar (+10%), metros de vigota, área."""
    return dict(
        n=len(lajes),
        aco_barras=round(sum(L["aco_barras"] for L in lajes) * 1.10, 1),
        vigotas_m=round(sum(L["vigotas_m"] for L in lajes), 1),
        area=round(sum(L["area"] for L in lajes), 1),
        falhas=[L["nome"] for L in lajes if L["falha"]],
    )


# ------------------------------------------------------------ desenho da planta
def fig_lajes(data, lajes):
    """Planta com os cômodos: direção das vigotas (seta), tipo, dimensões e h."""
    vigas = data.get("vigas", [])
    pilares = data.get("pilares", [])
    if not lajes:
        return None
    W = max((c["comodo"]["x1"] for c in lajes), default=15)
    H = max((c["comodo"]["y1"] for c in lajes), default=15)
    fig, ax = plt.subplots(figsize=(min(12.0, max(7.0, 0.7 * W + 2)),
                                    min(16.0, max(6.0, 0.7 * H + 2))), dpi=140)
    fig.patch.set_facecolor("white")
    for v in vigas:                                    # vigas amarelas
        ax.plot([v.get("x1_m"), v.get("x2_m")], [v.get("y1_m"), v.get("y2_m")],
                color="#d98a04", lw=3.0, solid_capstyle="round", zorder=2)
    for L in lajes:                                    # cômodos + direção
        c = L["comodo"]
        manual = c.get("manual")
        ax.add_patch(Rectangle((c["x0"], c["y0"]), c["Lx"], c["Ly"],
                               facecolor=("#16a34a" if manual else "#3b82f6"),
                               alpha=0.12, edgecolor=("#15803d" if manual else "#1d4ed8"),
                               lw=1.2, ls=("--" if manual else "-"), zorder=1))
        m = 0.18 * min(c["Lx"], c["Ly"])
        if L["vigota"] == "H":
            ax.annotate("", xy=(c["x1"] - m, c["cy"]), xytext=(c["x0"] + m, c["cy"]),
                        arrowprops=dict(arrowstyle="<->", color="#1d4ed8", lw=1.4))
        else:
            ax.annotate("", xy=(c["cx"], c["y1"] - m), xytext=(c["cx"], c["y0"] + m),
                        arrowprops=dict(arrowstyle="<->", color="#1d4ed8", lw=1.4))
        tel = " · telhado" if L.get("telhado") else ""
        ax.text(c["cx"], c["cy"],
                f"{L['nome']}  ({tipo_curto(L['tipo'])})\n{c['Lx']}×{c['Ly']} m · "
                f"h{L['h']}{tel}", ha="center", va="center", fontsize=8.5,
                fontweight="bold", color="#1e3a8a", zorder=6,
                bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="none", alpha=0.88))
    for p in pilares:                                  # pilares
        x, y = p.get("x_m"), p.get("y_m")
        if x is None:
            continue
        ax.add_patch(Rectangle((x - 0.16, y - 0.16), 0.32, 0.32,
                               facecolor="#b91c1c", zorder=7))
    ax.set_aspect("equal")
    ax.set_xlabel("x (m)", fontsize=9)
    ax.set_ylabel("y (m)", fontsize=9)
    ax.tick_params(labelsize=8)
    ax.grid(alpha=0.15)
    ax.set_title("LAJES — direção das vigotas (seta = menor vão) e tipo do cômodo",
                 fontsize=12, fontweight="bold", color="#0f2b4c")
    fig.tight_layout()
    return fig


def fig_lajes_plotly(data, lajes):
    """Planta INTERATIVA (Plotly): clicar numa laje gira a direção da vigota.
    O ÚNICO trace com pontos é o dos marcadores das lajes (customdata=nome);
    vigas, direção e pilares são FORMAS — assim o clique cai sempre na laje."""
    import plotly.graph_objects as go
    shapes = []
    for L in lajes:                                    # cômodos (retângulos)
        c = L["comodo"]
        manual = c.get("manual")
        shapes.append(dict(type="rect", x0=c["x0"], y0=c["y0"], x1=c["x1"],
                           y1=c["y1"], layer="below",
                           line=dict(color=("#15803d" if manual else "#1d4ed8"),
                                     width=1.2, dash=("dot" if manual else "solid")),
                           fillcolor=("rgba(22,163,74,0.10)" if manual
                                      else "rgba(59,130,246,0.10)")))
    for v in data.get("vigas", []):                    # vigas (linhas amarelas)
        shapes.append(dict(type="line", x0=v.get("x1_m"), y0=v.get("y1_m"),
                           x1=v.get("x2_m"), y1=v.get("y2_m"), layer="below",
                           line=dict(color="#d98a04", width=4)))
    for p in data.get("pilares", []):                  # pilares (quadrados)
        x, y = p.get("x_m"), p.get("y_m")
        if x is None:
            continue
        shapes.append(dict(type="rect", x0=x - 0.16, y0=y - 0.16, x1=x + 0.16,
                           y1=y + 0.16, fillcolor="#b91c1c", line=dict(width=0),
                           layer="below"))
    cxs, cys, txt, cd = [], [], [], []
    for L in lajes:                                    # setas (direção) + centros
        c = L["comodo"]
        m = 0.20 * min(c["Lx"], c["Ly"])
        if L["vigota"] == "H":
            shapes.append(dict(type="line", x0=c["x0"] + m, y0=c["cy"],
                               x1=c["x1"] - m, y1=c["cy"],
                               line=dict(color="#1d4ed8", width=2.5)))
            seta = "↔"
        else:
            shapes.append(dict(type="line", x0=c["cx"], y0=c["y0"] + m,
                               x1=c["cx"], y1=c["y1"] - m,
                               line=dict(color="#1d4ed8", width=2.5)))
            seta = "↕"
        cxs.append(c["cx"])
        cys.append(c["cy"])
        tel = " · telhado" if L.get("telhado") else ""
        txt.append(f"<b>{L['nome']}</b> {seta} ({tipo_curto(L['tipo'])})<br>"
                   f"{c['Lx']}×{c['Ly']} m · h{L['h']}{tel}")
        cd.append(L["nome"])
    fig = go.Figure(go.Scatter(
        x=cxs, y=cys, mode="markers+text", customdata=cd, hovertext=txt,
        hoverinfo="text", text=txt, textposition="middle center",
        textfont=dict(size=11, color="#1e3a8a"), name="lajes", showlegend=False,
        marker=dict(size=30, color="rgba(37,99,235,0.18)",
                    line=dict(color="#1d4ed8", width=1))))
    H = max((L["comodo"]["y1"] for L in lajes), default=15)
    fig.update_layout(shapes=shapes, margin=dict(l=8, r=8, t=54, b=8),
                      height=int(min(900, max(420, 42 * H))),
                      plot_bgcolor="white", clickmode="event+select",
                      dragmode="pan", showlegend=False,
                      title=dict(text="Clique numa laje para GIRAR a direção da "
                                 "vigota (seta). O padrão é o menor vão.",
                                 font=dict(size=13, color="#0f2b4c")))
    fig.update_yaxes(scaleanchor="x", scaleratio=1, title_text="y (m)",
                     gridcolor="#eef2f7")
    fig.update_xaxes(title_text="x (m)", gridcolor="#eef2f7")
    return fig
