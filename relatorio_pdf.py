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


def fig_planta(r):
    """Planta de forma: eixos de vigas/baldrames (amarelo) e pilares (vermelho),
    com a MESMA numeração do detalhamento (VH1…, VV…, P1…). Permite localizar
    cada elemento no projeto."""
    pilares = r.get("pilares", [])
    seg = []
    for v in r.get("vigas", []):
        if v.get("ini") is None:
            continue
        if v["dir"] == "H":
            seg.append((v["ini"], v["pos"], v["fim"], v["pos"], v["nome"]))
        else:
            seg.append((v["pos"], v["ini"], v["pos"], v["fim"], v["nome"]))
    xs = [p["x_m"] for p in pilares if p.get("x_m") is not None]
    ys = [p["y_m"] for p in pilares if p.get("y_m") is not None]
    for x1, y1, x2, y2, _ in seg:
        xs += [x1, x2]
        ys += [y1, y2]
    if not xs or not ys:
        return None
    W = max(1.0, max(xs) - min(xs))
    H = max(1.0, max(ys) - min(ys))
    fig, ax = plt.subplots(figsize=(min(12.0, max(7.0, 0.7 * W + 2.0)),
                                    min(16.0, max(6.0, 0.7 * H + 2.0))), dpi=150)
    fig.patch.set_facecolor("white")
    for x1, y1, x2, y2, _ in seg:
        ax.plot([x1, x2], [y1, y2], color=AMBAR, lw=3.6,
                solid_capstyle="round", zorder=2)
    off = max(0.45, 0.03 * max(W, H))
    for x1, y1, x2, y2, nome in seg:
        xm, ym = (x1 + x2) / 2, (y1 + y2) / 2
        if abs(x2 - x1) >= abs(y2 - y1):       # viga horizontal: rótulo fora da linha
            ym -= off
        else:                                   # viga vertical: rótulo ao lado
            xm -= off
        ax.text(xm, ym, nome, fontsize=14, color="#78350F", fontweight="bold",
                ha="center", va="center", zorder=5,
                bbox=dict(boxstyle="round,pad=0.25", fc="white", ec="none",
                          alpha=0.92))
    s = max(0.28, 0.022 * max(W, H))
    for p in pilares:
        x, y = p.get("x_m"), p.get("y_m")
        if x is None:
            continue
        ax.add_patch(plt.Rectangle((x - s / 2, y - s / 2), s, s,
                                   facecolor=VERMELHO, edgecolor="white",
                                   lw=0.8, zorder=6))
        ax.text(x + s * 0.8, y, p["pilar"], fontsize=13, color=NAVY,
                fontweight="bold", ha="left", va="center", zorder=7)
    ax.set_aspect("equal")                 # y NÃO invertido: cresce p/ cima como
    #                                        no editor (mesma orientação do desenho)
    ax.set_xlabel("x (m)", fontsize=9)
    ax.set_ylabel("y (m)", fontsize=9)
    ax.tick_params(labelsize=8)
    ax.grid(alpha=0.15)
    ax.set_title("PLANTA DE FORMA — VIGAS/BALDRAMES (amarelo) e PILARES "
                 "(vermelho)", fontsize=13, fontweight="bold", color=NAVY)
    fig.tight_layout()
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
        L.append(f"  Vão {i+1}: {e['texto']}  (Vsd={e['Vsd']:.1f} kN)")
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
        L.append(f"  Vão {i+1}: {e['texto']}")
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
