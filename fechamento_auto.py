# -*- coding: utf-8 -*-
"""Fechamento AUTOMÁTICO das vigas.

A partir do lançamento do engenheiro, SUGERE vigas ortogonais (90°) para:
  1) FECHAR os vãos abertos (a laje precisa de viga em todos os lados);
  2) DIVIDIR painéis grandes com uma viga no meio (reduz o vão);
  3) remover vigas em DUPLICIDADE (mesma linha, sobrepostas).
Depois RENUMERA os pilares (P1..Pn de cima→baixo, esq→dir); as vigas VH/VV são
renumeradas sozinhas pelo agrupamento contínuo.

O engenheiro ACEITA/RECUSA cada viga sugerida por clique (planta interativa) e
ajusta como quiser. Módulo NOVO — reusa a geometria de calc_laje_projeto e NÃO
altera nenhum módulo aprovado.
"""
import copy
import math

import calc_laje_projeto as cl

# cores do design (ui_comum)
AMBAR = "#B45309"      # vigas do engenheiro
VERDE = "#15803D"      # viga nova ACEITA
CINZA = "#94A3B8"      # viga nova RECUSADA
VERMELHO = "#B91C1C"   # pilares
NAVY = "#0F2B4C"

LIM_VIGOTA = 5.5   # m — vão máximo da vigota pré-moldada (MENOR lado do painel)
LIM_MEIO = 6.0     # m — acima disso no OUTRO lado, entra viga no meio
TOL = 0.30         # m — tolerância p/ "existe viga nessa aresta?"


# --------------------------------------------------------------- geometria base
def _grade_raw(vigas):
    """Grade crua (mesma de detectar_comodos/regioes_abertas) + listas H/V."""
    H, V = cl._segmentos(vigas)
    Xs = sorted(set(round(x, 2) for x, _, _ in V))
    Ys = sorted(set(round(y, 2) for y, _, _ in H))
    return Xs, Ys, H, V


def _bh(H, y, x0, x1, tol=TOL):
    return any(abs(yy - y) <= tol and a <= x0 + tol and b >= x1 - tol
               for yy, a, b in H)


def _bv(V, x, y0, y1, tol=TOL):
    return any(abs(xx - x) <= tol and a <= y0 + tol and b >= y1 - tol
               for xx, a, b in V)


def _runs(vals):
    """Junta inteiros consecutivos em faixas (i0,i1) inclusivas."""
    out = []
    for v in vals:
        if out and v == out[-1][1] + 1:
            out[-1][1] = v
        else:
            out.append([v, v])
    return [(a, b) for a, b in out]


def _retangulos(cells):
    """Decompõe um conjunto de células (i,j) em retângulos que não se sobrepõem
    (varredura gulosa baixo→cima, esq→dir). Serve para fechar uma área irregular
    em cômodos retangulares e dividir cada um."""
    restante = set(cells)
    rects = []
    while restante:
        i0, j0 = min(restante, key=lambda c: (c[1], c[0]))
        i1 = i0
        while (i1 + 1, j0) in restante:
            i1 += 1
        j1 = j0
        while all((i, j1 + 1) in restante for i in range(i0, i1 + 1)):
            j1 += 1
        for i in range(i0, i1 + 1):
            for j in range(j0, j1 + 1):
                restante.discard((i, j))
        rects.append((i0, i1, j0, j1))
    return rects


def _snap(val, lo, hi, linhas, tol=0.80):
    """Aproxima a divisão para uma linha de grade existente (encaixa nos pilares)."""
    dentro = [g for g in linhas if lo + 0.30 < g < hi - 0.30]
    if dentro:
        best = min(dentro, key=lambda g: abs(g - val))
        if abs(best - val) <= tol:
            return round(best, 2)
    return round(val, 2)


# ------------------------------------------------------------- fechar / dividir
def _cercar(cells, Xs, Ys, H, V, novas):
    """Acrescenta as arestas de contorno do painel que ainda NÃO têm viga."""
    vert, horiz = {}, {}
    for (i, j) in cells:
        if (i - 1, j) not in cells and not _bv(V, Xs[i], Ys[j], Ys[j + 1]):
            vert.setdefault(i, set()).add(j)
        if (i + 1, j) not in cells and not _bv(V, Xs[i + 1], Ys[j], Ys[j + 1]):
            vert.setdefault(i + 1, set()).add(j)
        if (i, j - 1) not in cells and not _bh(H, Ys[j], Xs[i], Xs[i + 1]):
            horiz.setdefault(j, set()).add(i)
        if (i, j + 1) not in cells and not _bh(H, Ys[j + 1], Xs[i], Xs[i + 1]):
            horiz.setdefault(j + 1, set()).add(i)
    for i, js in vert.items():
        for (j0, j1) in _runs(sorted(js)):
            novas.append(dict(dir="V", pos=Xs[i], a=Ys[j0], b=Ys[j1 + 1],
                              motivo="fechar"))
    for j, iss in horiz.items():
        for (i0, i1) in _runs(sorted(iss)):
            novas.append(dict(dir="H", pos=Ys[j], a=Xs[i0], b=Xs[i1 + 1],
                              motivo="fechar"))


def _subdividir(a, Xs, Ys, novas, lim_vigota, lim_meio):
    """Se o painel é um retângulo cheio e grande, coloca viga(s) no meio.
    Vigota corre no MENOR lado (≤ lim_vigota fica); o OUTRO lado, se passa de
    lim_meio, ganha viga(s) intermediária(s)."""
    x0, x1, y0, y1 = a["x0"], a["x1"], a["y0"], a["y1"]
    Lx, Ly = round(x1 - x0, 2), round(y1 - y0, 2)
    if Lx < 0.3 or Ly < 0.3:
        return
    if abs(a["area"] - Lx * Ly) >= 0.05 * Lx * Ly:      # não é retângulo cheio
        return
    limX = lim_vigota if Lx <= Ly else lim_meio
    limY = lim_vigota if Ly <= Lx else lim_meio
    nx = max(1, int(math.ceil(Lx / limX - 1e-9)))       # nº de painéis em X
    ny = max(1, int(math.ceil(Ly / limY - 1e-9)))
    for k in range(1, nx):
        xs = _snap(x0 + k * Lx / nx, x0, x1, Xs)
        novas.append(dict(dir="V", pos=xs, a=y0, b=y1, motivo="dividir"))
    for k in range(1, ny):
        ys = _snap(y0 + k * Ly / ny, y0, y1, Ys)
        novas.append(dict(dir="H", pos=ys, a=x0, b=x1, motivo="dividir"))


def _nome_no(pilares, x, y, tol=0.30):
    best, bd = "", tol
    for p in pilares:
        px, py = p.get("x_m"), p.get("y_m")
        if px is None:
            continue
        d = abs(px - x) + abs(py - y)
        if d <= bd:
            bd, best = d, p.get("pilar", "")
    return best


def _para_vigas(novas, data, H, V):
    """Converte as sugestões em vigas, pulando o que já existe ou repete."""
    pil = data.get("pilares", [])
    out, seen = [], []
    for n in novas:
        d, pos, a, b = n["dir"], n["pos"], n["a"], n["b"]
        if b - a < 0.30:
            continue
        if d == "V" and _bv(V, pos, a, b):
            continue
        if d == "H" and _bh(H, pos, a, b):
            continue
        dup = False
        for (dd, pp, aa, bb) in seen:
            if dd == d and abs(pp - pos) <= 0.15 and aa - 0.15 <= a and bb + 0.15 >= b:
                dup = True
                break
        if dup:
            continue
        seen.append((d, pos, a, b))
        if d == "H":
            x1_m, y1_m, x2_m, y2_m = a, pos, b, pos
        else:
            x1_m, y1_m, x2_m, y2_m = pos, a, pos, b
        out.append(dict(
            dir=d, pos=round(pos, 2), a=round(a, 2), b=round(b, 2),
            motivo=n["motivo"],
            de=_nome_no(pil, x1_m, y1_m), ate=_nome_no(pil, x2_m, y2_m),
            x1_m=round(x1_m, 2), y1_m=round(y1_m, 2),
            x2_m=round(x2_m, 2), y2_m=round(y2_m, 2),
            vao_m=round(b - a, 2), aviso=False, origem="auto"))
    return out


def fechar_vaos_auto(data, lim_vigota=LIM_VIGOTA, lim_meio=LIM_MEIO):
    """Sugere as vigas (fechar + dividir). Devolve lista de dicts com dir/pos/a/b
    (para desenhar) e os campos de viga (para aplicar)."""
    vigas = data.get("vigas", [])
    Xs, Ys, H, V = _grade_raw(vigas)
    if len(Xs) < 2 or len(Ys) < 2:
        return []
    idxX = {round(x, 2): i for i, x in enumerate(Xs)}
    idxY = {round(y, 2): j for j, y in enumerate(Ys)}
    novas = []
    for a in cl.regioes_abertas(vigas):                 # 1) fechar vãos abertos
        cells = set()
        for (cx0, cy0, cx1, cy1) in a.get("celulas", []):
            i, j = idxX.get(round(cx0, 2)), idxY.get(round(cy0, 2))
            if i is not None and j is not None:
                cells.add((i, j))
        if not cells:
            continue
        # quebra a área irregular em retângulos: cerca cada um (cria as vigas
        # entre os cômodos) e ainda divide o que ficar grande
        for (i0, i1, j0, j1) in _retangulos(cells):
            rc = {(i, j) for i in range(i0, i1 + 1) for j in range(j0, j1 + 1)}
            _cercar(rc, Xs, Ys, H, V, novas)
            _subdividir(dict(x0=Xs[i0], x1=Xs[i1 + 1], y0=Ys[j0], y1=Ys[j1 + 1],
                             area=(Xs[i1 + 1] - Xs[i0]) * (Ys[j1 + 1] - Ys[j0])),
                        Xs, Ys, novas, lim_vigota, lim_meio)
    for c in cl.detectar_comodos(vigas):                # 2) dividir cômodos grandes
        _subdividir(c, Xs, Ys, novas, lim_vigota, lim_meio)
    return _para_vigas(novas, data, H, V)


# --------------------------------------------------------- duplicidade / aplicar
def _seg(v):
    x1, y1, x2, y2 = v.get("x1_m"), v.get("y1_m"), v.get("x2_m"), v.get("y2_m")
    if None in (x1, y1, x2, y2):
        return None
    if abs(y1 - y2) <= abs(x1 - x2):
        return ("H", round((y1 + y2) / 2, 2), min(x1, x2), max(x1, x2))
    return ("V", round((x1 + x2) / 2, 2), min(y1, y2), max(y1, y2))


def dedup_vigas(vigas, tol=0.15):
    """Remove vigas em DUPLICIDADE = a MESMA viga desenhada mais de uma vez
    (mesma linha e MESMOS extremos, dentro da tolerância). NÃO remove sub-trechos
    de uma viga maior — esses definem os NÓS (apoios) da viga contínua, tirá-los
    mudaria os vãos e o cálculo. Mantém a 1ª ocorrência de cada duplicata."""
    segs = [_seg(v) for v in vigas]
    remove = set()
    for i, si in enumerate(segs):
        if si is None:
            continue
        for j in range(i):
            sj = segs[j]
            if sj is None or j in remove:
                continue
            if si[0] == sj[0] and abs(si[1] - sj[1]) <= tol \
                    and abs(si[2] - sj[2]) <= tol and abs(si[3] - sj[3]) <= tol:
                remove.add(i)              # i é cópia exata de j (mais antigo)
                break
    return [v for k, v in enumerate(vigas) if k not in remove]


STRAIGHT_ANG = 15.0    # graus — abaixo disso endireita p/ 90°; acima o Paulo ajusta
SNAP_LINHA = 0.20      # m — junta vigas paralelas coladas numa linha só (= tol do agrupar)
STUB_MIN = 0.30        # m — viga menor que isso é toco (lixo do desenho)


def endireitar_vigas(data, ang=STRAIGHT_ANG, stub=STUB_MIN):
    """Endireita as vigas quase-ortogonais (jitter < ang graus) para 90° exato e
    remove tocos (< stub m). Diagonal DE VERDADE (ângulo grande) é mantida — o
    engenheiro ajusta à mão. Devolve (data, n_endireitadas, n_tocos)."""
    d = copy.deepcopy(data)
    out, n_end, n_stub = [], 0, 0
    for v in d.get("vigas", []):
        x1, y1, x2, y2 = v.get("x1_m"), v.get("y1_m"), v.get("x2_m"), v.get("y2_m")
        if None in (x1, y1, x2, y2):
            out.append(v)
            continue
        dx, dy = x2 - x1, y2 - y1
        if math.hypot(dx, dy) < stub:                 # toco / lixo
            n_stub += 1
            continue
        menor, maior = min(abs(dx), abs(dy)), max(abs(dx), abs(dy))
        if menor > 0.01 and maior > 0.01 and math.degrees(math.atan2(menor, maior)) <= ang:
            if abs(dx) >= abs(dy):                     # horizontal
                ym = round((y1 + y2) / 2, 2)
                v = dict(v, y1_m=ym, y2_m=ym)
            else:                                       # vertical
                xm = round((x1 + x2) / 2, 2)
                v = dict(v, x1_m=xm, x2_m=xm)
            n_end += 1
        out.append(v)
    d["vigas"] = out
    return d, n_end, n_stub


def _merge_pos(vals, tol):
    """Agrupa posições próximas (≤ tol) e mapeia cada uma p/ a média do grupo."""
    rep = {}
    grupos = []
    for x in sorted(vals):
        if grupos and x - grupos[-1][-1] <= tol:
            grupos[-1].append(x)
        else:
            grupos.append([x])
    for g in grupos:
        r = round(sum(g) / len(g), 2)
        for x in g:
            rep[round(x, 2)] = r
    return rep


def snap_linhas(data, tol=SNAP_LINHA):
    """Cola as vigas paralelas quase-coincidentes (jitter ≤ tol) numa linha só —
    tira as 'linhas duplas' que aparecem no desenho à mão. Só mexe no eixo fixo."""
    d = copy.deepcopy(data)
    Hy = [s[1] for v in d.get("vigas", []) if (s := _seg(v)) and s[0] == "H"]
    Vx = [s[1] for v in d.get("vigas", []) if (s := _seg(v)) and s[0] == "V"]
    repH, repV = _merge_pos(Hy, tol), _merge_pos(Vx, tol)
    for v in d.get("vigas", []):
        s = _seg(v)
        if s is None:
            continue
        if s[0] == "H":
            ym = repH.get(round(s[1], 2), s[1])
            v["y1_m"] = v["y2_m"] = ym
        else:
            xm = repV.get(round(s[1], 2), s[1])
            v["x1_m"] = v["x2_m"] = xm
    return d


def alinhar_pilares(data, tol=0.35):
    """Encosta cada pilar no EIXO das vigas e VIRA na direção certa da parede:
    - posição: snap do x ao eixo vertical mais próximo e do y ao horizontal (≤ tol);
      num encontro de vigas, vai para o CRUZAMENTO dos eixos.
    - orientação: o lado de 14 cm fica ATRAVESSADO na parede (o de 30 cm corre ao
      longo). Numa parede VERTICAL (viga V) o pilar fica em pé (sentido vertical);
      numa HORIZONTAL, deitado. Assim ele não invade o cômodo. Num CANTO (as duas)
      mantém o sentido atual. Pilar longe de qualquer viga (>tol) fica como está.
    A seção (14×30) e o cálculo NÃO mudam — só a posição/orientação do desenho."""
    d = copy.deepcopy(data)
    H, V = cl._segmentos(d.get("vigas", []))       # H:(y,x0,x1)  V:(x,y0,y1)
    n = 0
    for p in d.get("pilares", []):
        px, py = p.get("x_m"), p.get("y_m")
        if px is None or py is None:
            continue
        vx = [x for (x, y0, y1) in V if y0 - tol <= py <= y1 + tol and abs(x - px) <= tol]
        hy = [y for (y, x0, x1) in H if x0 - tol <= px <= x1 + tol and abs(y - py) <= tol]
        nx = round(min(vx, key=lambda x: abs(x - px)), 2) if vx else px
        ny = round(min(hy, key=lambda y: abs(y - py)), 2) if hy else py
        mudou = abs(nx - px) > 0.005 or abs(ny - py) > 0.005
        p["x_m"], p["y_m"] = nx, ny
        if p.get("forma") != "quadrado":           # vira p/ o 14 cm ficar na parede
            novo = "vertical" if (vx and not hy) else ("horizontal" if (hy and not vx) else None)
            if novo and p.get("sentido") != novo:
                p["sentido"] = novo
                mudou = True
        if mudou:
            n += 1
    return d, n


def limpar_lancamento(data):
    """Faxina no lançamento à mão: endireita (90°), cola linhas paralelas coladas,
    tira tocos e DUPLICATAS exatas, e ALINHA os pilares no eixo das vigas (14 cm
    dentro da parede / no cruzamento). NÃO restrutura apoios (calc estável).
    Devolve (data_limpo, stats)."""
    d, n_end, n_stub = endireitar_vigas(data)
    d = snap_linhas(d)
    antes = len(d.get("vigas", []))
    d["vigas"] = dedup_vigas(d.get("vigas", []))
    d, n_pil = alinhar_pilares(d)
    return d, dict(endireitadas=n_end, tocos=n_stub,
                   duplicadas=antes - len(d["vigas"]), pilares_alinhados=n_pil)


def renumerar_pilares(data):
    """Renumera P1..Pn (cima→baixo, esq→dir) e atualiza o de/ate das vigas."""
    d = copy.deepcopy(data)
    pil = d.get("pilares", [])
    ordem = sorted(range(len(pil)),
                   key=lambda k: (-round(pil[k].get("y_m", 0), 1),
                                  round(pil[k].get("x_m", 0), 1)))
    for novo_i, k in enumerate(ordem, 1):
        pil[k]["pilar"] = f"P{novo_i}"
    for v in d.get("vigas", []):
        n1 = _nome_no(pil, v.get("x1_m"), v.get("y1_m"))
        n2 = _nome_no(pil, v.get("x2_m"), v.get("y2_m"))
        if n1:
            v["de"] = n1
        if n2:
            v["ate"] = n2
    return d


def _viga_limpa(n):
    return {k: n[k] for k in ("de", "ate", "x1_m", "y1_m", "x2_m", "y2_m",
                              "vao_m", "aviso", "origem") if k in n}


def aplicar_fechamento(data, novas_aceitas):
    """Limpa a base (endireita/cola/dedup), junta as vigas aceitas e renumera."""
    d = copy.deepcopy(data)
    d, _, _ = endireitar_vigas(d)
    d = snap_linhas(d)
    d["vigas"] = dedup_vigas(d.get("vigas", [])
                             + [_viga_limpa(n) for n in novas_aceitas])
    return renumerar_pilares(d)


# ------------------------------------------------------------ planta interativa
def fig_fechamento_plotly(data, novas, aceitas):
    """Planta INTERATIVA: clicar numa viga verde tira/põe. O único trace com
    pontos é o dos marcadores das sugestões (customdata=índice)."""
    import plotly.graph_objects as go
    shapes = []
    for a in cl.regioes_abertas(data.get("vigas", [])):     # vãos abertos (fundo)
        for (cx0, cy0, cx1, cy1) in a.get("celulas", []):
            shapes.append(dict(type="rect", x0=cx0, y0=cy0, x1=cx1, y1=cy1,
                               layer="below", line=dict(width=0),
                               fillcolor="rgba(239,68,68,0.10)"))
    for v in data.get("vigas", []):                          # vigas do engenheiro
        shapes.append(dict(type="line", x0=v.get("x1_m"), y0=v.get("y1_m"),
                           x1=v.get("x2_m"), y1=v.get("y2_m"), layer="below",
                           line=dict(color=AMBAR, width=4)))
    for k, n in enumerate(novas):                            # sugestões (linhas)
        ok = k in aceitas
        if n["dir"] == "H":
            x0, y0, x1, y1 = n["a"], n["pos"], n["b"], n["pos"]
        else:
            x0, y0, x1, y1 = n["pos"], n["a"], n["pos"], n["b"]
        shapes.append(dict(type="line", x0=x0, y0=y0, x1=x1, y1=y1,
                           line=dict(color=(VERDE if ok else CINZA),
                                     width=(6 if ok else 2),
                                     dash=("solid" if ok else "dot"))))
    for p in data.get("pilares", []):                        # pilares
        x, y = p.get("x_m"), p.get("y_m")
        if x is None:
            continue
        shapes.append(dict(type="rect", x0=x - 0.16, y0=y - 0.16, x1=x + 0.16,
                           y1=y + 0.16, fillcolor=VERMELHO, line=dict(width=0),
                           layer="below"))
    mx, my, txt, cd, col = [], [], [], [], []
    for k, n in enumerate(novas):
        ok = k in aceitas
        if n["dir"] == "H":
            cx, cy = (n["a"] + n["b"]) / 2, n["pos"]
        else:
            cx, cy = n["pos"], (n["a"] + n["b"]) / 2
        mx.append(cx)
        my.append(cy)
        txt.append("✓" if ok else "✗")
        cd.append(str(k))
        col.append(VERDE if ok else "#CBD5E1")
    hov = [("viga nova (%s) — clique p/ %s"
            % ("fecha o vão" if n["motivo"] == "fechar" else "divide o vão",
               "TIRAR" if k in aceitas else "PÔR"))
           for k, n in enumerate(novas)]
    fig = go.Figure(go.Scatter(
        x=mx, y=my, mode="markers+text", customdata=cd, text=txt,
        textposition="middle center", textfont=dict(size=13, color="white"),
        hovertext=hov, hoverinfo="text", showlegend=False,
        marker=dict(size=22, color=col, line=dict(color=NAVY, width=1))))
    ys = [v.get("y2_m") for v in data.get("vigas", []) if v.get("y2_m") is not None]
    Hh = max(ys) if ys else 15
    fig.update_layout(shapes=shapes, margin=dict(l=8, r=8, t=54, b=8),
                      height=int(min(950, max(440, 42 * Hh))), plot_bgcolor="white",
                      clickmode="event+select", dragmode="pan", showlegend=False,
                      title=dict(text="Verde = viga nova (clique p/ tirar/pôr) · "
                                 "âmbar = suas vigas · vermelho-claro = vão aberto",
                                 font=dict(size=12, color=NAVY)))
    fig.update_yaxes(scaleanchor="x", scaleratio=1, title_text="y (m)",
                     gridcolor="#eef2f7")
    fig.update_xaxes(title_text="x (m)", gridcolor="#eef2f7")
    return fig
