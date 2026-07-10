# -*- coding: utf-8 -*-
"""Relatório COMPLETO em PDF do Projeto Completo — um PDF grande com o
detalhamento de CADA viga e CADA pilar (as MESMAS figuras das telas manuais,
via desenhos_viga / desenhos_pilar) + memorial de cálculo por elemento.

Reusa os motores e desenhos aprovados; não altera nenhuma tela.
"""
import io

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

import motor_viga as mv
from ui_comum import NAVY, AMBAR, CINZA_TXT
import desenhos_viga as dv
import desenhos_pilar as dp

A4 = (8.27, 11.69)          # retrato (polegadas)


# ------------------------------------------------------------ páginas de texto
def _pag_texto(pdf, texto, titulo=None, mono=True, fs=9):
    fig = plt.figure(figsize=A4)
    fig.patch.set_facecolor("white")
    y = 0.965
    if titulo:
        fig.text(0.06, 0.975, titulo, fontsize=13, fontweight="bold",
                 color=NAVY, va="top")
        fig.text(0.06, 0.945, "─" * 92, fontsize=8, color=AMBAR, va="top")
        y = 0.925
    fig.text(0.06, y, texto, fontsize=fs, va="top", ha="left",
             family="monospace" if mono else "sans-serif", color="#0f172a",
             linespacing=1.35)
    pdf.savefig(fig)
    plt.close(fig)


def _capa(pdf, r, proj):
    fig = plt.figure(figsize=A4)
    fig.patch.set_facecolor("white")
    fig.text(0.5, 0.90, "POLOTTO ENGENHARIA", ha="center", fontsize=20,
             fontweight="bold", color=NAVY)
    fig.text(0.5, 0.865, "Projeto Completo — Detalhamento estrutural",
             ha="center", fontsize=13, color=CINZA_TXT)
    fig.text(0.5, 0.83, f"Projeto: {proj}", ha="center", fontsize=12,
             fontweight="bold", color="#0f172a")
    fig.text(0.5, 0.80, "NBR 6118 · concreto C25 · aço CA-50A",
             ha="center", fontsize=10, color=CINZA_TXT)

    linhas = [
        "RESUMO",
        f"   Vigas de cobertura ....... {len(r['vigas'])}",
        f"   Baldrames ................ {len(r['baldrames'])}",
        f"   Pilares .................. {len(r['pilares'])}",
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


# ------------------------------------------------------------ memoriais
def _mem_viga(v):
    res = v["res"]
    d = res["dados"]
    est = res["estatica"]
    L = [f"Seção {d['b']:.0f}×{d['h']:.0f} cm · C{d['fck']:.0f} · CA-50 · "
         f"c={d['cob']:.1f} cm · d={d['d']:.1f} cm",
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
    L.append("ESTRIBOS (2 ramos, CA-50):")
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


def _mem_pilar(p):
    rp = p["res"]
    opt = p["opt"]
    d = rp["dados"]
    L = [f"Seção {d['b']:.0f}×{d['h']:.0f} cm · C{d['fck']:.0f} · CAA {d['caa']} "
         f"(c={d['cob']:.1f} cm)",
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
        L.append(f"ESTRIBOS: ø{opt['phi_t']:.1f} c/{opt['s_est']:.0f} cm — "
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
def _elemento_viga(pdf, v):
    res = v["res"]
    cab = f"VIGA {v['nome']} — {v['secao']} cm — {v['nvaos']} vão(s)"
    if not res or "estatica" not in res:
        _pag_texto(pdf, "Não foi possível calcular esta viga.", titulo=cab)
        return
    _salva(pdf, dv.fig_esquema(res), cab + "  ·  Esquema de cargas")
    _salva(pdf, dv.fig_diagramas(res), "Diagramas de momento e cortante")
    if res.get("quantitativo"):
        _salva(pdf, dv.fig_corte_longitudinal(res))   # já se autointitula
        tipo, idx, tit = _corte_args(res)
        _salva(pdf, dv.fig_corte_estribo(res, tipo, idx, tit),
               "Corte transversal e estribo")
    _pag_texto(pdf, _mem_viga(v), titulo=f"Memorial — Viga {v['nome']}")


def _elemento_pilar(pdf, p):
    rp = p["res"]
    opt = p["opt"]
    cab = f"PILAR {p['pilar']} — {p['secao']} cm — Nk {p['Nk']} kN"
    if not rp or not opt:
        _pag_texto(pdf, _mem_pilar(p), titulo=cab)
        return
    _salva(pdf, dp.fig_secao(rp, opt), cab + "  ·  Corte transversal")
    _salva(pdf, dp.fig_pilar_longitudinal(rp, opt))   # já se autointitula
    _pag_texto(pdf, _mem_pilar(p), titulo=f"Memorial — Pilar {p['pilar']}")


def gerar_pdf(r, proj="projeto"):
    """Monta o PDF completo e devolve os bytes."""
    buf = io.BytesIO()
    with PdfPages(buf) as pdf:
        _capa(pdf, r, proj)
        _divisoria(pdf, "VIGAS DE COBERTURA")
        for v in r["vigas"]:
            _elemento_viga(pdf, v)
        _divisoria(pdf, "BALDRAMES")
        for b in r["baldrames"]:
            _elemento_viga(pdf, b)
        _divisoria(pdf, "PILARES")
        for p in r["pilares"]:
            _elemento_pilar(pdf, p)
    return buf.getvalue()
