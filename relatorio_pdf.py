# -*- coding: utf-8 -*-
"""Relatório COMPLETO em PDF do Projeto Completo — um PDF grande com o
detalhamento de CADA viga e CADA pilar (as MESMAS figuras das telas manuais,
via desenhos_viga / desenhos_pilar) + memorial de cálculo por elemento.

Reusa os motores e desenhos aprovados; não altera nenhuma tela.
"""
import io
import textwrap

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

import motor_viga as mv
from ui_comum import NAVY, AMBAR, VERMELHO, CINZA_TXT
import desenhos_viga as dv
import desenhos_pilar as dp

A4 = (8.27, 11.69)          # retrato (polegadas)


# ------------------------------------------------------------ agrupar iguais
def _kv(v):
    """Duas vigas/baldrames são iguais se têm a mesma seção, os mesmos vãos
    e a mesma carga (o desenho e o memorial saem idênticos)."""
    return (v["secao"], tuple(round(x, 2) for x in v["vaos"]), round(v["w"], 1))


def _kp(p):
    """Dois pilares são iguais se têm a mesma seção e a mesma armadura
    (mesmo detalhe de execução)."""
    return (p["secao"], p.get("armadura", ""), p.get("estribo", ""))


def _agrupar(elems, keyfn, repfn=None):
    """Agrupa elementos iguais preservando a ordem de aparição. Devolve
    [{'membros': [...], 'rep': elem_representativo}]. rep = mais crítico
    (repfn) ou o primeiro."""
    grupos, ordem = {}, []
    for e in elems:
        k = keyfn(e)
        if k not in grupos:
            grupos[k] = []
            ordem.append(k)
        grupos[k].append(e)
    out = []
    for k in ordem:
        m = grupos[k]
        rep = max(m, key=repfn) if repfn else m[0]
        out.append({"membros": m, "rep": rep})
    return out


def _rotulo(prefixo, nomes):
    if len(nomes) == 1:
        return f"{prefixo} {nomes[0]}"
    return f"{prefixo} {nomes[0]} (+{len(nomes)-1} iguais)"


def _tipos(n):
    return f"{n} tipo" + ("" if n == 1 else "s")


# ------------------------------------------------------------ páginas de texto
def _wrap(texto, largura=92):
    """Quebra linhas longas (mantendo a indentação) para não vazar da página."""
    out = []
    for ln in texto.split("\n"):
        if len(ln) <= largura:
            out.append(ln)
            continue
        ind = ln[:len(ln) - len(ln.lstrip())]
        out.append(textwrap.fill(ln, width=largura, subsequent_indent=ind + "  ",
                                 break_long_words=False, break_on_hyphens=False))
    return "\n".join(out)


def _pag_texto(pdf, texto, titulo=None, mono=True, fs=9):
    fig = plt.figure(figsize=A4)
    fig.patch.set_facecolor("white")
    y = 0.965
    if titulo:
        fig.text(0.06, 0.975, titulo, fontsize=13, fontweight="bold",
                 color=NAVY, va="top")
        fig.text(0.06, 0.945, "─" * 92, fontsize=8, color=AMBAR, va="top")
        y = 0.925
    fig.text(0.06, y, _wrap(texto), fontsize=fs, va="top", ha="left",
             family="monospace" if mono else "sans-serif", color="#0f172a",
             linespacing=1.35)
    pdf.savefig(fig)
    plt.close(fig)


def _capa(pdf, r, proj, nv, nb, npil, reduzido=False):
    fig = plt.figure(figsize=A4)
    fig.patch.set_facecolor("white")
    fig.text(0.5, 0.90, "POLOTTO ENGENHARIA", ha="center", fontsize=20,
             fontweight="bold", color=NAVY)
    fig.text(0.5, 0.865, ("Projeto Completo — Relatório REDUZIDO (só armações)"
                          if reduzido else
                          "Projeto Completo — Detalhamento estrutural"),
             ha="center", fontsize=13, color=CINZA_TXT)
    if reduzido:
        fig.text(0.5, 0.842, "sem diagramas de momento/cortante — ver o completo",
                 ha="center", fontsize=9, color=CINZA_TXT, style="italic")
    fig.text(0.5, 0.83, f"Projeto: {proj}", ha="center", fontsize=12,
             fontweight="bold", color="#0f172a")
    fig.text(0.5, 0.80, "NBR 6118 · concreto C25 (fck 25 MPa) · aço CA-50A · "
             "elementos iguais agrupados", ha="center", fontsize=10,
             color=CINZA_TXT)

    linhas = [
        "RESUMO            (total · tipos p/ detalhar)",
        f"   Vigas de cobertura ....... {len(r['vigas']):>2}  ·  {_tipos(nv)}",
        f"   Baldrames ................ {len(r['baldrames']):>2}  ·  {_tipos(nb)}",
        f"   Pilares .................. {len(r['pilares']):>2}  ·  {_tipos(npil)}",
        f"   Carga total à fundação ... {r['fund_tf']} tf",
        "",
        "AÇO A COMPRAR (por etapa)",
        f"   Vigas de cobertura ....... {r['aco_vigas']} kg",
        f"   Pilares .................. {r['aco_pilares']} kg",
        f"   Baldrames ................ {r['aco_baldrames']} kg",
        f"   ────────────────────────────────────",
        f"   TOTAL .................... {r['aco_total']} kg",
    ]
    fig.text(0.5, 0.66, "\n".join(linhas), ha="center", va="top", fontsize=12,
             family="monospace", color="#0f172a", linespacing=1.7,
             bbox=dict(boxstyle="round,pad=1.0", fc="#f6f9fc", ec=NAVY, lw=1.5))
    if r["falhas"]:
        fig.text(0.5, 0.20, "Verificar manualmente: " + ", ".join(r["falhas"]),
                 ha="center", fontsize=9, color="#b91c1c", fontweight="bold")
    fig.text(0.5, 0.06, "Documento gerado automaticamente — conferir por "
             "profissional habilitado.", ha="center", fontsize=8,
             color=CINZA_TXT, style="italic")
    pdf.savefig(fig)
    plt.close(fig)


def _divisoria(pdf, titulo):
    fig = plt.figure(figsize=A4)
    fig.patch.set_facecolor("white")
    fig.text(0.5, 0.5, titulo, ha="center", va="center", fontsize=26,
             fontweight="bold", color=NAVY)
    pdf.savefig(fig)
    plt.close(fig)


# OBSERVAÇÃO NOS CÁLCULOS — o que o motor do programa executa (o engenheiro sabe)
OBS_CALCULOS = [
    ("1)  DIREÇÃO e USO (sobrecarga) da laje na tabela",
     "A direção e o tipo de uso escolhidos na tabela mudam o dimensionamento da "
     "PRÓPRIA laje (altura e armadura). Porém, a carga lançada nas VIGAS de "
     "cobertura usa a direção lançada no editor e a carga de cobertura UNIFORME "
     "(q_cob = laje de forro + revestimento + sobrecarga de forro + telhado). A "
     "sobrecarga por ambiente (uso de cada cômodo) NÃO é somada individualmente "
     "na viga de cobertura."),
    ("2)  VÃO de dimensionamento da laje pré-moldada",
     "As lajes pré-moldadas são SEMPRE dimensionadas pelo MENOR vão (o vão da "
     "vigota). Girar a seta muda o desenho e a distribuição da carga nas vigas, "
     "mas NÃO altera a altura/armadura da PRÓPRIA laje — que continua calculada "
     "pelo menor vão."),
]


def _pagina_observacao(pdf):
    """Página 'OBSERVAÇÃO NOS CÁLCULOS' — deixa claro o que o motor executa."""
    fig = plt.figure(figsize=A4)
    fig.patch.set_facecolor("white")
    fig.text(0.5, 0.93, "OBSERVAÇÃO NOS CÁLCULOS", ha="center", fontsize=23,
             fontweight="bold", color="#B45309")
    fig.text(0.5, 0.885, "O que o programa executa — para o engenheiro conferir e "
             "decidir.", ha="center", fontsize=11, color=CINZA_TXT, style="italic")
    y = 0.80
    for tit, txt in OBS_CALCULOS:
        fig.text(0.09, y, tit, ha="left", va="top", fontsize=14, fontweight="bold",
                 color="#0f172a")
        y -= 0.05
        wrapped = _wrap(txt, 82)
        fig.text(0.09, y, wrapped, ha="left", va="top", fontsize=12.5,
                 color="#1e293b", linespacing=1.7)
        y -= 0.042 * (wrapped.count("\n") + 1) + 0.06
    fig.text(0.5, 0.05, "Documento gerado automaticamente — conferir por "
             "profissional habilitado (NBR 6118 / NBR 6120).", ha="center",
             fontsize=8, color=CINZA_TXT, style="italic")
    pdf.savefig(fig)
    plt.close(fig)


def _sec_dims(secao, sentido, across=None):
    """Dimensões REAIS (m) do pilar a partir da seção ('14x30') e do sentido.
    `across` força o lado CURTO (atravessa a parede): pilar em parede de 25 cm = 20 cm."""
    import re
    n = re.findall(r"\d+\.?\d*", str(secao or ""))
    if len(n) >= 2:
        a, b = float(n[0]) / 100.0, float(n[1]) / 100.0
    else:
        a, b = 0.14, 0.30
    lo, hi = min(a, b), max(a, b)
    if across and abs(a - b) > 0.01:   # só retangular: lado curto vira `across`
        lo = across
    if sentido == "vertical":
        return lo, hi          # lado curto no x, longo no y
    if sentido == "horizontal":
        return hi, lo          # longo no x, curto no y
    return a, b                # quadrado / indefinido


def _laje_span(lx, ly, hbs, vbs, dirn, default, tol=0.20):
    """Vão do painel na direção da seta (p/ a seta caber dentro da laje)."""
    if dirn == "V":
        top = [y for (y, xa, xb) in hbs if y > ly + 0.05 and xa - tol <= lx <= xb + tol]
        bot = [y for (y, xa, xb) in hbs if y < ly - 0.05 and xa - tol <= lx <= xb + tol]
        if top and bot:
            return min(top) - max(bot)
    else:
        rit = [x for (x, ya, yb) in vbs if x > lx + 0.05 and ya - tol <= ly <= yb + tol]
        lef = [x for (x, ya, yb) in vbs if x < lx - 0.05 and ya - tol <= ly <= yb + tol]
        if rit and lef:
            return min(rit) - max(lef)
    return default


def _deoverlap(fig, ax, texts, passos=8):
    """Afasta os rótulos que se sobrepõem — empurra cada par no eixo de MENOR
    sobreposição, usando as caixas REAIS já renderizadas. Deixa os nomes legíveis
    em áreas densas (sem biblioteca externa)."""
    texts = [t for t in texts if t and t.get_text()]
    if len(texts) < 2:
        return
    try:
        fig.canvas.draw()
        rend = fig.canvas.get_renderer()
    except Exception:
        return
    inv = ax.transData.inverted()
    for _ in range(passos):
        boxes = [t.get_window_extent(rend) for t in texts]
        moveu = False
        for i in range(len(texts)):
            for j in range(i + 1, len(texts)):
                a, b = boxes[i], boxes[j]
                ox = min(a.x1, b.x1) - max(a.x0, b.x0)
                oy = min(a.y1, b.y1) - max(a.y0, b.y0)
                if ox <= 0 or oy <= 0:
                    continue                       # não se tocam
                cia, cja = (a.y0 + a.y1), (b.y0 + b.y1)
                cxa, cxb = (a.x0 + a.x1), (b.x0 + b.x1)
                if oy <= ox:                        # separa na vertical (menos desloc.)
                    s = oy / 2 + 1.0
                    di = (0, s) if cia >= cja else (0, -s)
                else:                               # separa na horizontal
                    s = ox / 2 + 1.0
                    di = (s, 0) if cxa >= cxb else (-s, 0)
                for t, sgn in ((texts[i], 1.0), (texts[j], -1.0)):
                    x, y = t.get_position()
                    px, py = ax.transData.transform((x, y))
                    nx, ny = inv.transform((px + sgn * di[0], py + sgn * di[1]))
                    t.set_position((nx, ny))
                moveu = True
        if not moveu:
            break
        fig.canvas.draw()


def _planta(vigas, pilares, lajes, titulo, cor_viga, cor_pilar):
    """Desenha UMA planta: vigas (cor_viga, rotuladas fora da linha), pilares no
    TAMANHO REAL da seção (cor_pilar) com P# e dimensão, e as setas das LAJES
    (azul) cabendo dentro do painel. `vigas` = lista com nome/dir/pos/ini/fim."""
    seg = []
    for v in vigas:
        if v.get("ini") is None:
            continue
        esp = v.get("parede", 0.15)
        if v["dir"] == "H":
            seg.append((v["ini"], v["pos"], v["fim"], v["pos"], v["nome"], esp))
        else:
            seg.append((v["pos"], v["ini"], v["pos"], v["fim"], v["nome"], esp))
    xs = [p["x_m"] for p in pilares if p.get("x_m") is not None]
    ys = [p["y_m"] for p in pilares if p.get("y_m") is not None]
    for x1, y1, x2, y2, _, _ in seg:
        xs += [x1, x2]
        ys += [y1, y2]
    if not xs or not ys:
        return None
    W = max(1.0, max(xs) - min(xs))
    H = max(1.0, max(ys) - min(ys))
    fig, ax = plt.subplots(figsize=(min(12.0, max(7.0, 0.7 * W + 2.0)),
                                    min(16.0, max(6.0, 0.7 * H + 2.0))), dpi=150)
    fig.patch.set_facecolor("white")
    for x1, y1, x2, y2, _, esp in seg:                    # viga = PAREDE (15 ou 25 cm)
        if abs(x2 - x1) >= abs(y2 - y1):                  # horizontal
            xa, xb = min(x1, x2), max(x1, x2)
            ax.add_patch(plt.Rectangle((xa, y1 - esp / 2), max(esp, xb - xa), esp,
                                       facecolor=cor_viga, edgecolor="none", zorder=2))
        else:                                             # vertical
            ya, yb = min(y1, y2), max(y1, y2)
            ax.add_patch(plt.Rectangle((x1 - esp / 2, ya), esp, max(esp, yb - ya),
                                       facecolor=cor_viga, edgecolor="none", zorder=2))
    off = max(0.42, 0.03 * max(W, H))
    labs = []
    for x1, y1, x2, y2, nome, _ in seg:                   # rótulo AFASTADO da viga
        xm, ym = (x1 + x2) / 2, (y1 + y2) / 2
        if abs(x2 - x1) >= abs(y2 - y1):
            ym += off
        else:
            xm += off
        labs.append(ax.text(xm, ym, nome, fontsize=12, color="#0F172A",
                    fontweight="bold", ha="center", va="center", zorder=5,
                    bbox=dict(boxstyle="round,pad=0.2", fc="white", ec=cor_viga,
                              lw=0.7)))
    hbs = [(y1, min(x1, x2), max(x1, x2)) for x1, y1, x2, y2, _, _ in seg
           if abs(y1 - y2) < abs(x1 - x2)]
    vbs = [(x1, min(y1, y2), max(y1, y2)) for x1, y1, x2, y2, _, _ in seg
           if abs(x1 - x2) <= abs(y1 - y2)]
    walls25 = [(x1, y1, x2, y2) for x1, y1, x2, y2, _, esp in seg if esp >= 0.20]

    def _on25(px, py, tol=0.22):                          # pilar numa parede de 25 cm?
        for x1, y1, x2, y2 in walls25:
            if abs(x2 - x1) >= abs(y2 - y1):
                if abs(y1 - py) <= tol and min(x1, x2) - tol <= px <= max(x1, x2) + tol:
                    return True
            elif abs(x1 - px) <= tol and min(y1, y2) - tol <= py <= max(y1, y2) + tol:
                return True
        return False

    lo = max(0.34, 0.028 * max(W, H))
    for p in pilares:                                     # pilar no TAMANHO real
        x, y = p.get("x_m"), p.get("y_m")
        if x is None:
            continue
        wx, hy = _sec_dims(p.get("secao", "14x30"), p.get("sentido"),
                           across=(0.20 if _on25(x, y) else None))
        ax.add_patch(plt.Rectangle((x - wx / 2, y - hy / 2), wx, hy,
                                   facecolor=cor_pilar, edgecolor="white",
                                   lw=1.0, zorder=6))
        labs.append(ax.text(x + lo, y + lo * 0.35, p.get("pilar", "P"), fontsize=11,
                    color=cor_pilar, fontweight="bold", ha="left", va="center",
                    zorder=7, bbox=dict(boxstyle="round,pad=0.12", fc="white",
                                        ec="none", alpha=0.9)))
        if p.get("secao"):                                # dimensão do pilar
            labs.append(ax.text(x + lo, y - lo * 0.5, str(p["secao"]), fontsize=8,
                        color="#475569", fontweight="bold", ha="left", va="center",
                        zorder=7))
    for i, L in enumerate(lajes or [], 1):                # setas das LAJES (azul)
        x, y = L.get("x_m"), L.get("y_m")
        if x is None or y is None:
            continue
        span = _laje_span(x, y, hbs, vbs, L.get("dir"), default=1.4)
        a = min(1.1, max(0.30, 0.34 * span))              # cabe no painel
        if L.get("dir") == "V":
            ax.annotate("", xy=(x, y + a), xytext=(x, y - a),
                        arrowprops=dict(arrowstyle="<->", color="#1D4ED8", lw=2.2),
                        zorder=8)
            lox, loy = max(0.3, a * 0.5), 0
        else:
            ax.annotate("", xy=(x + a, y), xytext=(x - a, y),
                        arrowprops=dict(arrowstyle="<->", color="#1D4ED8", lw=2.2),
                        zorder=8)
            lox, loy = 0, max(0.3, a * 0.55)
        labs.append(ax.text(x + lox, y + loy, L.get("nome", f"L{i}"), fontsize=9.5,
                    color="#1D4ED8", fontweight="bold", ha="center", va="center",
                    zorder=9, bbox=dict(boxstyle="round,pad=0.12", fc="white",
                                        ec="none", alpha=0.9)))
    mgx, mgy = 0.04 * W + 0.4, 0.04 * H + 0.4   # as paredes são add_patch: fixo a vista
    ax.set_xlim(min(xs) - mgx, max(xs) + mgx)
    ax.set_ylim(min(ys) - mgy, max(ys) + mgy)
    ax.set_aspect("equal")                 # y NÃO invertido: cresce p/ cima
    ax.set_xlabel("x (m)", fontsize=9)
    ax.set_ylabel("y (m)", fontsize=9)
    ax.tick_params(labelsize=8)
    ax.grid(alpha=0.12)
    ax.set_title(titulo, fontsize=13, fontweight="bold", color=NAVY)
    fig.tight_layout()
    _deoverlap(fig, ax, labs)              # afasta os nomes que se sobrepõem
    return fig


KGF = 101.97                # kgf por kN (1 kN ≈ 101,97 kgf) — pesos em kgf
COR_FORMA = "#F5B301"       # amarelo bem vivo (planta de forma)
COR_FUND = "#E11D2E"        # vermelho bem vivo (planta de fundação)
COR_PIL_FORMA = "#1E3A8A"   # pilar na forma = azul-marinho
COR_PIL_FUND = "#111827"    # pilar na fundação = quase preto (diferencia)


def fig_planta(r):
    """PLANTA DE FORMA — vigas de cobertura (VH/VV, AMARELO) + LAJES + pilares."""
    tit = "PLANTA DE FORMA — VIGAS de cobertura (amarelo) e PILARES (azul)"
    if r.get("lajes"):
        tit += " · SETAS das LAJES (azul)"
    return _planta(r.get("vigas", []), r.get("pilares", []), r.get("lajes", []),
                   tit, COR_FORMA, COR_PIL_FORMA)


def fig_planta_fundacao(r):
    """PLANTA DE FUNDAÇÃO — vigas BALDRAMES (VB, VERMELHO) + pilares, SEM lajes."""
    return _planta(r.get("baldrames", []), r.get("pilares", []), [],
                   "PLANTA DE FUNDAÇÃO — VIGAS BALDRAMES VB (vermelho) e "
                   "PILARES (preto)", COR_FUND, COR_PIL_FUND)


def _pp_viga(secao):
    """Peso próprio da viga (kN/m) a partir da seção '14x40' (× 25 kN/m³)."""
    import re
    n = re.findall(r"\d+\.?\d*", str(secao or ""))
    if len(n) >= 2:
        return round((float(n[0]) / 100.0) * (float(n[1]) / 100.0) * 25.0, 2)
    return 0.0


def _seg_bounds(vigas, pilares):
    """Segmentos (x1,y1,x2,y2,viga) e dimensões da planta (p/ as plantas de carga)."""
    seg = []
    for v in vigas:
        if v.get("ini") is None:
            continue
        if v["dir"] == "H":
            seg.append((v["ini"], v["pos"], v["fim"], v["pos"], v))
        else:
            seg.append((v["pos"], v["ini"], v["pos"], v["fim"], v))
    xs = [p["x_m"] for p in pilares if p.get("x_m") is not None]
    ys = [p["y_m"] for p in pilares if p.get("y_m") is not None]
    for x1, y1, x2, y2, _ in seg:
        xs += [x1, x2]
        ys += [y1, y2]
    if not xs or not ys:
        return None
    return seg, max(1.0, max(xs) - min(xs)), max(1.0, max(ys) - min(ys))


def fig_cargas_pilares(r):
    """Planta com a CARGA de cada pilar em número GRANDE (tf) — para a fundação."""
    pilares = r.get("pilares", [])
    gb = _seg_bounds(r.get("vigas", []), pilares)
    if gb is None:
        return None
    seg, W, H = gb
    fig, ax = plt.subplots(figsize=(min(12.0, max(7.0, 0.7 * W + 2)),
                                    min(16.0, max(6.0, 0.7 * H + 2))), dpi=150)
    fig.patch.set_facecolor("white")
    for x1, y1, x2, y2, _ in seg:                    # vigas de fundo (cinza claro)
        ax.plot([x1, x2], [y1, y2], color="#CBD5E1", lw=2.4, zorder=1)
    s = max(0.16, 0.014 * max(W, H))
    labs = []
    for p in pilares:
        x, y = p.get("x_m"), p.get("y_m")
        if x is None:
            continue
        ax.add_patch(plt.Rectangle((x - s / 2, y - s / 2), s, s, facecolor=VERMELHO,
                                   edgecolor="white", lw=0.8, zorder=6))
        carga = p.get("carga_tf", 0) or 0
        labs.append(ax.text(x, y + 1.4 * s, f"{carga:.1f}", fontsize=14,
                    color="#B91C1C", fontweight="bold", ha="center", va="bottom",
                    zorder=8, bbox=dict(boxstyle="round,pad=0.16", fc="#FEF3C7",
                                        ec="#B45309", lw=0.7)))
        labs.append(ax.text(x, y - 1.2 * s, p.get("pilar", ""), fontsize=8.5,
                    color=NAVY, fontweight="bold", ha="center", va="top", zorder=8))
    ax.set_aspect("equal")
    ax.grid(alpha=0.12)
    ax.set_xlabel("x (m)", fontsize=9)
    ax.set_ylabel("y (m)", fontsize=9)
    ax.tick_params(labelsize=8)
    ax.set_title("PLANTA DE CARGAS NOS PILARES — carga (tf) para a FUNDAÇÃO",
                 fontsize=13, fontweight="bold", color=NAVY)
    fig.tight_layout()
    _deoverlap(fig, ax, labs)
    return fig


def fig_cargas_vigas(r):
    """Planta com a CARGA (kN/m) que cada viga de cobertura recebe (laje+telhado+pp)."""
    pilares = r.get("pilares", [])
    gb = _seg_bounds(r.get("vigas", []), pilares)
    if gb is None:
        return None
    seg, W, H = gb
    fig, ax = plt.subplots(figsize=(min(12.0, max(7.0, 0.7 * W + 2)),
                                    min(16.0, max(6.0, 0.7 * H + 2))), dpi=150)
    fig.patch.set_facecolor("white")
    labs = []
    for x1, y1, x2, y2, v in seg:
        wt = round(((v.get("w", 0) or 0) + _pp_viga(v.get("secao"))) * KGF)  # kgf/m
        ax.plot([x1, x2], [y1, y2], color=COR_FORMA, lw=4.4,
                solid_capstyle="round", zorder=2)
        xm, ym = (x1 + x2) / 2, (y1 + y2) / 2
        labs.append(ax.text(xm, ym, f"{v.get('nome', '')}\n{wt} kgf/m", fontsize=9,
                    color="#0F172A", fontweight="bold", ha="center", va="center",
                    zorder=6, bbox=dict(boxstyle="round,pad=0.18", fc="white",
                                        ec=COR_FORMA, lw=0.7)))
    s = max(0.14, 0.012 * max(W, H))
    for p in pilares:
        x, y = p.get("x_m"), p.get("y_m")
        if x is None:
            continue
        ax.add_patch(plt.Rectangle((x - s / 2, y - s / 2), s, s, facecolor=VERMELHO,
                                   edgecolor="white", lw=0.7, zorder=5))
    ax.set_aspect("equal")
    ax.grid(alpha=0.12)
    ax.set_xlabel("x (m)", fontsize=9)
    ax.set_ylabel("y (m)", fontsize=9)
    ax.tick_params(labelsize=8)
    ax.set_title("PLANTA DE CARGAS NAS VIGAS — kgf/m (laje + telhado + peso próprio)",
                 fontsize=13, fontweight="bold", color=NAVY)
    fig.tight_layout()
    _deoverlap(fig, ax, labs)
    return fig


# ------------------------------------------------------------ memoriais
def _mem_viga(v):
    res = v["res"]
    d = res["dados"]
    est = res["estatica"]
    L = [f"Seção {d['b']:.0f}×{d['h']:.0f} cm · C{d['fck']:.0f} (fck {d['fck']:.0f} "
         f"MPa) · aço CA-50A · c={d['cob']:.1f} cm · d={d['d']:.1f} cm",
         f"Carga da laje q = {v['w']:.2f} kN/m" +
         (f"  ·  peso próprio g = {d['g_pp']:.2f} kN/m" if d.get("g_pp", 0) > 0 else ""),
         ""]
    L.append("MOMENTOS NOS APOIOS (kN·m):")
    L.append("  " + "   ".join(f"{chr(65+j)}={m:.1f}"
                               for j, m in enumerate(est["M_apoios"])))
    L.append("MOMENTOS POSITIVOS MÁX (kN·m):")
    for i, vv in enumerate(est["vaos"]):
        L.append(f"  Vão {i+1}: {vv['M_pos']:.1f}  (x={vv['x_pos']:.2f} m)")
    L.append("REAÇÕES DE APOIO (kN):")
    L.append("  " + "   ".join(f"{chr(65+j)}={rr:.1f}"
                               for j, rr in enumerate(est["Reacoes"])))
    L.append("")
    L.append("ARMADURA LONGITUDINAL:")
    for j, fx in enumerate(res["flex_apoios"]):
        if fx["sel"] and not fx["sel"].get("construtiva"):
            L.append(f"  Apoio {chr(65+j)} (neg.): As={fx['As']:.2f} cm²  ->  "
                     f"{fx['sel']['texto']}")
    for i, fx in enumerate(res["flex_vaos"]):
        if fx["sel"]:
            L.append(f"  Vão {i+1} (pos.): As={(fx['As'] or 0):.2f} cm²  ->  "
                     f"{fx['sel']['texto']}")
    L.append("")
    L.append("ESTRIBOS (2 ramos, CA-50A ou CA-60A):")
    for i, e in enumerate(res["estribos"]):
        if e.get("texto"):
            L.append(f"  Vão {i+1}: {e['texto']}  (Vsd={e.get('Vsd', 0):.1f} kN)")
        else:
            L.append(f"  Vão {i+1}: SEÇÃO INSUFICIENTE na biela — Vsd="
                     f"{e.get('Vsd', 0):.1f} > Vrd2={e.get('Vrd2', 0):.1f} kN "
                     "(aumentar a seção)")
    if res.get("pele"):
        L.append(f"ARMADURA DE PELE: {res['pele']['texto']}")
    q = res.get("quantitativo")
    if q:
        L.append("")
        L.append("QUANTITATIVO DE AÇO DESTA VIGA:")
        for p in q["posicoes"]:
            L.append(f"  {p['pos']:<4} {p['descr']:<26} ø{p['phi']:>4.1f}  "
                     f"{p['qtd']:>3} un × {p['comp_unit']:6.2f} m = "
                     f"{p['peso']:7.2f} kg")
        L.append(f"  PESO: {q['peso_total']:.1f} kg  ·  COMPRA (+10%): "
                 f"{q.get('peso_compra', q['peso_total']*1.1):.1f} kg")
    try:
        fl = mv.verificar_flecha(res)
        L.append("")
        L.append("FLECHA (ELS-DEF, quase-permanente):")
        for it in (fl["vaos"] + fl["balancos"]):
            situ = "OK" if it["ok"] else "EXCEDE"
            L.append(f"  {it['nome']}: total {it['flecha_total_mm']:.1f} mm / "
                     f"limite {it['limite_mm']:.1f} mm  ->  {situ}")
    except Exception:
        pass
    return "\n".join(L)


def _mem_pilar(p, nomes=None):
    rp = p.get("res") or {}
    opt = p.get("opt")
    d = rp.get("dados")
    L = []
    if nomes and len(nomes) > 1:
        L.append(f"IGUAIS ({len(nomes)}): " + ", ".join(nomes))
        L.append("Mesmo detalhe de execução; dimensionado para o mais carregado.")
        L.append("")
    if not d:
        L.append(f"Pilar {p['pilar']}: seção {p['secao']} — não foi possível "
                 f"dimensionar (Nk={p.get('Nk')} kN). Revisar manualmente.")
        return "\n".join(L)
    L += [f"Seção {d['b']:.0f}×{d['h']:.0f} cm · C{d['fck']:.0f} (fck {d['fck']:.0f} "
          f"MPa) · aço CA-50A · CAA {d['caa']} (c={d['cob']:.1f} cm)",
          f"l0={d['l0']:.2f} m · Nk={p['Nk']} kN (carga {p['carga_tf']} tf) · "
          f"Nd={rp['Nd']:.0f} kN · γn={rp['gamma_n']:.2f} · ν={rp['ni']:.3f}",
          "",
          "ESBELTEZ E 2ª ORDEM:"]
    for nome, dd in rp["direcoes"].items():
        so = "SIM" if dd["segunda_ordem"] else "não"
        L.append(f"  Direção {nome}: λ={dd['lambda']:.1f} (λ1={dd['lambda1']:.1f}) "
                 f"· 2ª ordem: {so} · Md,tot={dd['Md_tot']/100:.1f} kN·m")
    L.append("")
    if opt:
        L.append(f"ARMADURA ADOTADA: {opt['texto']}  (As={opt['As_ef']:.2f} cm² · "
                 f"mín {rp['As_min']:.2f} · máx {rp['As_max']:.2f})")
        L.append(f"ESTRIBOS (CA-50A ou CA-60A): ø{opt['phi_t']:.1f} c/{opt['s_est']:.0f} cm — "
                 f"{opt['n_est']} un × {opt['comp_est']:.2f} m")
        L.append(f"PESO DE AÇO: long {opt['peso_long']:.2f} + estribos "
                 f"{opt['peso_est']:.2f} = {opt['peso_total']:.2f} kg")
    else:
        L.append("SEÇÃO INSUFICIENTE mesmo no maior perfil — revisar manualmente.")
    if rp.get("avisos"):
        L.append("")
        L.append("HIPÓTESES/AVISOS:")
        for a in rp["avisos"]:
            L.append(f"  - {a}")
    return "\n".join(L)


def _mem_viga_red(v, nomes=None):
    """Memorial REDUZIDO da viga: só armadura + quantitativo (sem momentos,
    reações, cortantes ou flecha)."""
    res = v["res"]
    d = res["dados"]
    L = []
    if nomes and len(nomes) > 1:
        L.append(f"IGUAIS ({len(nomes)}): " + ", ".join(nomes))
        L.append("Mesmo desenho e ferragem para todas.")
        L.append("")
    L.append(f"Seção {d['b']:.0f}×{d['h']:.0f} cm · C{d['fck']:.0f} (fck "
             f"{d['fck']:.0f} MPa) · aço CA-50A · c={d['cob']:.1f} cm")
    L.append("")
    L.append("ARMADURA LONGITUDINAL:")
    for j, fx in enumerate(res["flex_apoios"]):
        if fx["sel"] and not fx["sel"].get("construtiva"):
            L.append(f"  Apoio {chr(65+j)} (neg.): {fx['sel']['texto']}")
    for i, fx in enumerate(res["flex_vaos"]):
        if fx["sel"]:
            L.append(f"  Vão {i+1} (pos.): {fx['sel']['texto']}")
    if res.get("pele"):
        L.append(f"  Pele: {res['pele']['texto']}")
    L.append("")
    L.append("ESTRIBOS (2 ramos, CA-50A ou CA-60A):")
    for i, e in enumerate(res["estribos"]):
        if e.get("texto"):
            L.append(f"  Vão {i+1}: {e['texto']}")
        else:
            L.append(f"  Vão {i+1}: SEÇÃO INSUFICIENTE na biela "
                     f"(Vsd={e.get('Vsd', 0):.1f} > Vrd2={e.get('Vrd2', 0):.1f} kN)")
    q = res.get("quantitativo")
    if q:
        L.append("")
        L.append("QUANTITATIVO DE AÇO DESTA VIGA:")
        for p in q["posicoes"]:
            L.append(f"  {p['pos']:<4} {p['descr']:<26} ø{p['phi']:>4.1f}  "
                     f"{p['qtd']:>3} un × {p['comp_unit']:6.2f} m = "
                     f"{p['peso']:7.2f} kg")
        L.append(f"  PESO: {q['peso_total']:.1f} kg  ·  COMPRA (+10%): "
                 f"{q.get('peso_compra', q['peso_total']*1.1):.1f} kg")
    return "\n".join(L)


def _mem_pilar_red(p, nomes=None):
    """Memorial REDUZIDO do pilar: só armadura (sem esbeltez/2ª ordem)."""
    rp = p.get("res") or {}
    opt = p.get("opt")
    d = rp.get("dados")
    L = []
    if nomes and len(nomes) > 1:
        L.append(f"IGUAIS ({len(nomes)}): " + ", ".join(nomes))
        L.append("Mesmo detalhe; dimensionado para o mais carregado.")
        L.append("")
    if not d:
        L.append(f"Pilar {p['pilar']}: seção {p['secao']} — não foi possível "
                 f"dimensionar (Nk={p.get('Nk')} kN). Revisar manualmente.")
        return "\n".join(L)
    L.append(f"Seção {d['b']:.0f}×{d['h']:.0f} cm · C{d['fck']:.0f} · aço "
             f"CA-50A · CAA {d['caa']} (c={d['cob']:.1f} cm)")
    L.append(f"Carga Nk = {p['Nk']} kN ({p['carga_tf']} tf)")
    L.append("")
    if opt:
        L.append(f"ARMADURA: {opt['texto']}")
        L.append(f"ESTRIBOS (CA-50A ou CA-60A): ø{opt['phi_t']:.1f} "
                 f"c/{opt['s_est']:.0f} cm — {opt['n_est']} un × "
                 f"{opt['comp_est']:.2f} m")
        L.append(f"PESO DE AÇO: {opt['peso_total']:.2f} kg")
    return "\n".join(L)


def _corte_args(res):
    est = res["estatica"]
    ms = [abs(m) for m in est["M_apoios"]]
    if ms and max(ms) > 0.1:
        j = ms.index(max(ms))
        return ("apoio", j, f"Apoio {chr(65+j)}")
    return ("vao", 0, "Vão 1")


def _salva(pdf, fig, titulo=None):
    if titulo:
        fig.suptitle(titulo, fontsize=13, fontweight="bold", color=NAVY, y=0.995)
    pdf.savefig(fig, bbox_inches="tight")
    plt.close(fig)


# ------------------------------------------------------------ elementos
def _elemento_viga(pdf, v, membros, reduzido=False):
    res = v["res"]
    nomes = [m["nome"] for m in membros]
    cab = _rotulo("VIGA", nomes) + f" — {v['secao']} cm — {v['nvaos']} vão(s)"
    if not res or "estatica" not in res:
        _pag_texto(pdf, "Não foi possível calcular esta viga.", titulo=cab)
        return
    if not reduzido:
        _salva(pdf, dv.fig_esquema(res), cab + "  ·  Esquema de cargas")
        _salva(pdf, dv.fig_diagramas(res), "Diagramas de momento e cortante")
    if res.get("quantitativo"):
        _salva(pdf, dv.fig_corte_longitudinal(res), cab if reduzido else None)
        tipo, idx, tit = _corte_args(res)
        _salva(pdf, dv.fig_corte_estribo(res, tipo, idx, tit),
               "Corte transversal e estribo")
    if reduzido:
        mem = _mem_viga_red(v, nomes)
    else:
        mem = _mem_viga(v)
        if len(nomes) > 1:
            mem = (f"IGUAIS ({len(nomes)}): " + ", ".join(nomes)
                   + "\nMesmo desenho e ferragem para todas.\n\n" + mem)
    _pag_texto(pdf, mem, titulo="Memorial — " + _rotulo("Viga", nomes))


def _elemento_pilar(pdf, p, membros, reduzido=False):
    rp = p["res"]
    opt = p["opt"]
    nomes = [m["pilar"] for m in membros]
    cab = _rotulo("PILAR", nomes) + f" — {p['secao']} cm"
    memf = _mem_pilar_red if reduzido else _mem_pilar
    if not rp or not opt:
        _pag_texto(pdf, memf(p, nomes), titulo=cab)
        return
    _salva(pdf, dp.fig_secao(rp, opt), cab + "  ·  Corte transversal")
    _salva(pdf, dp.fig_pilar_longitudinal(rp, opt))   # já se autointitula
    _pag_texto(pdf, memf(p, nomes), titulo="Memorial — " + _rotulo("Pilar", nomes))


def gerar_pdf(r, proj="projeto", reduzido=False):
    """Monta o PDF (elementos iguais agrupados) e devolve os bytes.
    reduzido=True: só armações (cortes + quantitativo), sem os diagramas de
    momento/cortante nem os memoriais de esforços."""
    gv = _agrupar(r["vigas"], _kv)
    gb = _agrupar(r["baldrames"], _kv)
    gp = _agrupar(r["pilares"], _kp, repfn=lambda p: p.get("Nk", 0))
    buf = io.BytesIO()
    with PdfPages(buf) as pdf:
        _capa(pdf, r, proj, len(gv), len(gb), len(gp), reduzido=reduzido)
        planta = fig_planta(r)
        if planta is not None:
            _salva(pdf, planta)
        planta_fund = fig_planta_fundacao(r)      # planta de fundação (baldrames VB)
        if planta_fund is not None:
            _salva(pdf, planta_fund)
        cargp = fig_cargas_pilares(r)             # cargas nos pilares (p/ fundação)
        if cargp is not None:
            _salva(pdf, cargp)
        cargv = fig_cargas_vigas(r)               # cargas nas vigas
        if cargv is not None:
            _salva(pdf, cargv)
        _pagina_observacao(pdf)                   # OBSERVAÇÃO NOS CÁLCULOS
        _divisoria(pdf, f"VIGAS DE COBERTURA\n({_tipos(len(gv))} · "
                   f"{len(r['vigas'])} vigas)")
        for g in gv:
            _elemento_viga(pdf, g["rep"], g["membros"], reduzido=reduzido)
        _divisoria(pdf, f"BALDRAMES\n({_tipos(len(gb))} · "
                   f"{len(r['baldrames'])} baldrames)")
        for g in gb:
            _elemento_viga(pdf, g["rep"], g["membros"], reduzido=reduzido)
        _divisoria(pdf, f"PILARES\n({_tipos(len(gp))} · "
                   f"{len(r['pilares'])} pilares)")
        for g in gp:
            _elemento_pilar(pdf, g["rep"], g["membros"], reduzido=reduzido)
    return buf.getvalue()
