# -*- coding: utf-8 -*-
"""Projeto Completo — leitura de planta (PDF), editor visual de lancamento e
agrupamento de vigas continuas. NAO altera os modulos aprovados (Vigas/Pilares/
Lajes/Pilares Previos); e um modulo NOVO usado so pela pagina 'Projeto Completo'.
"""
import os, io, base64, json

_DIR = os.path.dirname(os.path.abspath(__file__))
_TEMPLATE = os.path.join(_DIR, "editor_template.html")


# ---------------------------------------------------------------- leitura do PDF
def extrair_planta(pdf_bytes, zoom=2.2):
    """Le um PDF vetorial e devolve o fundo (data-uri) + eixos de parede + regiao.
    Retorna dict(img, VX, HY, X0, Y0, VW, VH, page_pt).
    """
    import fitz
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    pg = doc[0]
    vseg = []  # (xpos, comprimento)  verticais
    hseg = []  # (ypos, comprimento)  horizontais
    for d in pg.get_drawings():
        for it in d["items"]:
            if it[0] == "l":
                a, b = it[1], it[2]
                if abs(a.x - b.x) < 0.9 and abs(a.y - b.y) > 2:
                    vseg.append(((a.x + b.x) / 2, abs(a.y - b.y)))
                elif abs(a.y - b.y) < 0.9 and abs(a.x - b.x) > 2:
                    hseg.append(((a.y + b.y) / 2, abs(a.x - b.x)))
            elif it[0] == "re":
                r = it[1]
                vseg.append((r.x0, abs(r.y1 - r.y0))); vseg.append((r.x1, abs(r.y1 - r.y0)))
                hseg.append((r.y0, abs(r.x1 - r.x0))); hseg.append((r.y1, abs(r.x1 - r.x0)))
    if not vseg or not hseg:
        raise ValueError("Nao encontrei linhas vetoriais na planta (o PDF pode ser "
                         "uma imagem/escaneado). Use um PDF exportado do CAD.")
    xs = [p for p, _ in vseg]; ys = [p for p, _ in hseg]
    X0 = max(0, min(xs) - 12); Y0 = max(0, min(ys) - 12)
    X1 = min(pg.rect.width, max(xs) + 12); Y1 = min(pg.rect.height, max(ys) + 12)
    VW = round(X1 - X0, 1); VH = round(Y1 - Y0, 1)

    def eixos(segs, thr=600):
        w = {}
        for pos, L in segs:
            if L > 0.05:
                k = round(pos, 1); w[k] = w.get(k, 0) + L
        cl = []
        for k in sorted(w):
            if cl and k - cl[-1][0] <= 18:
                p, c = cl[-1]; t = c + w[k]; cl[-1] = ((p * c + k * w[k]) / t, t)
            else:
                cl.append((k, w[k]))
        return sorted(round(p, 1) for p, c in cl if c > thr)

    VX = [x for x in eixos(vseg) if X0 < x < X0 + VW]
    HY = [y for y in eixos(hseg) if Y0 < y < Y0 + VH]

    pix = pg.get_pixmap(matrix=fitz.Matrix(zoom, zoom),
                        clip=fitz.Rect(X0, Y0, X0 + VW, Y0 + VH))
    img = "data:image/png;base64," + base64.b64encode(pix.tobytes("png")).decode()
    return dict(img=img, VX=VX, HY=HY, X0=round(X0, 1), Y0=round(Y0, 1),
                VW=VW, VH=VH, page_pt=(round(pg.rect.width, 1), round(pg.rect.height, 1)))


def estimar_escala(dados, largura_m):
    """S (pt/m) a partir de uma largura real informada da construcao."""
    if largura_m and largura_m > 0:
        return round(dados["VW"] / largura_m, 2)
    return 39.0


# ---------------------------------------------------------------- monta o editor
def build_editor(dados, S, proj="Projeto", pillars=None, mins=None, lskey="lanc_proj"):
    tpl = open(_TEMPLATE, encoding="utf-8").read()
    rep = {
        "__IMG__": dados["img"],
        "__VX__": json.dumps(dados["VX"]),
        "__HY__": json.dumps(dados["HY"]),
        "__PILLARS__": json.dumps(pillars or []),
        "__MIN__": json.dumps(mins or []),
        "__X0__": str(dados["X0"]), "__Y0__": str(dados["Y0"]),
        "__VW__": str(dados["VW"]), "__VH__": str(dados["VH"]),
        "__S__": str(S), "__POOL__": "[0,0,0,0]",
        "__LSKEY__": lskey, "__PROJ__": proj,
    }
    for k, v in rep.items():
        tpl = tpl.replace(k, v)
    return tpl


# ---------------------------------------------------- vigas continuas (do JSON)
def agrupar_vigas_continuas(vigas, tol=0.20):
    """Agrupa segmentos de viga alinhados (mesma linha) em vigas continuas.
    Cada viga tem x1_m,y1_m,x2_m,y2_m. Retorna lista de linhas continuas:
      dict(dir='H'|'V', pos=coord_fixa, segmentos=[(a,b)], vaos=[m...], comp=total_m).
    """
    segs = []
    for v in vigas:
        x1, y1, x2, y2 = v.get("x1_m"), v.get("y1_m"), v.get("x2_m"), v.get("y2_m")
        if None in (x1, y1, x2, y2):
            continue
        if abs(y1 - y2) <= abs(x1 - x2):      # horizontal
            segs.append(("H", (y1 + y2) / 2, min(x1, x2), max(x1, x2)))
        else:                                  # vertical
            segs.append(("V", (x1 + x2) / 2, min(y1, y2), max(y1, y2)))
    linhas = []
    for dirn in ("H", "V"):
        grupo = sorted([s for s in segs if s[0] == dirn], key=lambda z: (round(z[1] / tol), z[2]))
        # agrupa por posicao (mesma linha) dentro da tolerancia
        faixas = []
        for _, pos, a, b in grupo:
            achou = None
            for fx in faixas:
                if abs(fx["pos"] - pos) <= tol:
                    achou = fx; break
            if achou is None:
                achou = {"pos": pos, "iv": []}; faixas.append(achou)
            achou["iv"].append((a, b))
        for fx in faixas:
            iv = sorted(fx["iv"])
            # mescla intervalos adjacentes/sobrepostos em runs continuos
            runs = [list(iv[0])]
            for a, b in iv[1:]:
                if a <= runs[-1][1] + tol:
                    runs[-1][1] = max(runs[-1][1], b)
                else:
                    runs.append([a, b])
            # nós = extremos + emendas dos segmentos (para dividir em vãos)
            pts = sorted(set([a for a, b in iv] + [b for a, b in iv]))
            for a, b in runs:
                ns = [q for q in pts if a - tol <= q <= b + tol]
                ns = sorted(set([round(q, 2) for q in ns]))
                vaos = [round(ns[i + 1] - ns[i], 2) for i in range(len(ns) - 1) if ns[i + 1] - ns[i] > 0.1]
                if vaos:
                    linhas.append(dict(dir=dirn, pos=round(fx["pos"], 2),
                                       ini=round(a, 2), fim=round(b, 2),
                                       vaos=vaos, comp=round(b - a, 2), nvaos=len(vaos)))
    return linhas


def resumo_estrutura(data):
    """Resumo pronto p/ exibir a partir do estrutura_*.json do editor."""
    pil = data.get("pilares", [])
    vg = data.get("vigas", [])
    linhas = agrupar_vigas_continuas(vg)
    total_tf = data.get("total_tf")
    if total_tf is None:
        total_tf = round(sum(p.get("carga_tf", 0) for p in pil), 1)
    return dict(
        n_pilares=len(pil), n_vigas=len(vg), n_continuas=len(linhas),
        total_tf=total_tf, pilares=pil, linhas=linhas,
        vao_max=round(max([mx for l in linhas for mx in l["vaos"]] or [0]), 2),
    )
