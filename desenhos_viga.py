# -*- coding: utf-8 -*-
"""Desenhos das vigas (figuras matplotlib) — extraído de pagina_vigas.py para
ser reusado tanto pela tela manual (por parte) quanto pelo relatório do
Projeto Completo. São funções PURAS: recebem o `res` de motor_viga e devolvem
uma Figure. NÃO alteram o comportamento das telas aprovadas."""
import math

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from ui_comum import NAVY, AMBAR, VERMELHO, VERDE, CINZA_TXT, CONCRETO


def _posicoes_apoios(est):
    """x global de cada apoio (m); x=0 na ponta esquerda da viga."""
    off = est['bal_esq']['L'] if est['bal_esq'] else 0.0
    xs = [off]
    for v in est['vaos']:
        xs.append(xs[-1] + v['L'])
    return xs


def _larg_fig(est, base=7.2, por_tramo=1.9):
    n = (len(est['vaos']) + (1 if est['bal_esq'] else 0)
         + (1 if est['bal_dir'] else 0))
    return min(26.0, max(base, por_tramo * n))   # teto p/ não estourar


def fig_esquema(res, fu=1.0, un_f="kN"):
    cf = 0 if fu > 1 else 1
    est = res['estatica']
    xs_ap = _posicoes_apoios(est)
    L_tot = xs_ap[-1] + (est['bal_dir']['L'] if est['bal_dir'] else 0.0)
    fig, ax = plt.subplots(figsize=(_larg_fig(est), 3.4), dpi=150)
    fig.patch.set_facecolor('white')
    ax.set_xlim(-0.05 * L_tot, 1.05 * L_tot)
    ax.set_ylim(-2.6, 3.2)
    ax.axis('off')

    # corpo da viga
    ax.fill_between([0, L_tot], -0.22, 0.22, color=CONCRETO, zorder=1)
    ax.plot([0, L_tot], [0.22, 0.22], color=CINZA_TXT, lw=1.2)
    ax.plot([0, L_tot], [-0.22, -0.22], color=CINZA_TXT, lw=1.2)

    # apoios + reações
    for j, xa in enumerate(xs_ap):
        ax.plot(xa, -0.22, marker='^', color=NAVY, ms=16, zorder=3)
        ax.text(xa, -1.05,
                f"{chr(65 + j)}\n{est['Reacoes'][j] * fu:.{cf}f} {un_f}",
                ha='center', va='top', color=NAVY, fontsize=11,
                fontweight='bold')

    # cargas distribuídas (faixa por tramo)
    tramos_x = []
    if est['bal_esq']:
        tramos_x.append((0.0, est['bal_esq']['L'], est['bal_esq']))
    x0 = xs_ap[0]
    for v in est['vaos']:
        tramos_x.append((x0, x0 + v['L'], v))
        x0 += v['L']
    if est['bal_dir']:
        tramos_x.append((xs_ap[-1], xs_ap[-1] + est['bal_dir']['L'],
                         est['bal_dir']))
    for xi, xf, tr in tramos_x:
        if tr['q'] > 0:
            ax.fill_between([xi, xf], 0.55, 0.95, color=NAVY, alpha=0.12)
            ax.plot([xi, xf], [0.95, 0.95], color=NAVY, lw=1.0)
            for xa in [xi + k * (xf - xi) / 4 for k in range(5)]:
                ax.annotate('', xy=(xa, 0.26), xytext=(xa, 0.92),
                            arrowprops=dict(arrowstyle='->', color=NAVY,
                                            lw=0.9))
            ax.text((xi + xf) / 2, 1.05,
                    f"q = {tr['q'] * fu:.{cf}f} {un_f}/m",
                    ha='center', va='bottom', color=NAVY, fontsize=10,
                    fontweight='bold')
        if tr['P'] > 0:
            xp = xi + tr['a']
            ax.annotate('', xy=(xp, 0.26), xytext=(xp, 2.35),
                        arrowprops=dict(arrowstyle='-|>', color=VERMELHO,
                                        lw=2.2))
            ax.text(xp, 2.42, f"P = {tr['P'] * fu:.{cf}f} {un_f}",
                    ha='center', va='bottom', color=VERMELHO, fontsize=10.5,
                    fontweight='bold')

    # cotas
    for xi, xf, _tr in tramos_x:
        ax.annotate('', xy=(xi, -1.9), xytext=(xf, -1.9),
                    arrowprops=dict(arrowstyle='<->', color=CINZA_TXT,
                                    lw=1.0))
        ax.text((xi + xf) / 2, -1.78, f"{xf - xi:.2f} m", ha='center',
                va='bottom', color=CINZA_TXT, fontsize=10,
                fontweight='bold')
    fig.tight_layout()
    return fig


def fig_diagramas(res, fu=1.0, un_f="kN"):
    cf = 0 if fu > 1 else 1
    est = res['estatica']
    xs_ap = _posicoes_apoios(est)
    fig, (axm, axv) = plt.subplots(2, 1, figsize=(_larg_fig(est), 5.6),
                                   dpi=150, sharex=True)
    fig.patch.set_facecolor('white')

    # monta diagrama global
    segs = []
    if est['bal_esq']:
        segs.append((0.0, est['bal_esq']))
    x0 = xs_ap[0]
    for v in est['vaos']:
        segs.append((x0, v))
        x0 += v['L']
    if est['bal_dir']:
        segs.append((xs_ap[-1], est['bal_dir']))

    for off, tr in segs:
        xg = off + tr['xs']
        axm.plot(xg, tr['Mx'], color=NAVY, lw=1.8)
        axm.fill_between(xg, tr['Mx'], 0, color=NAVY, alpha=0.10)
        axv.plot(xg, tr['Vx'], color=AMBAR, lw=1.8)
        axv.fill_between(xg, tr['Vx'], 0, color=AMBAR, alpha=0.10)

    for ax in (axm, axv):
        ax.axhline(0, color=CINZA_TXT, lw=1.0)
        for xa in xs_ap:
            ax.axvline(xa, color=CONCRETO, lw=0.8, ls='--')
        ax.tick_params(labelsize=10)
        ax.grid(alpha=0.18)

    # anota extremos de momento
    for j, xa in enumerate(xs_ap):
        m = est['M_apoios'][j]
        if abs(m) > 0.05:
            axm.annotate(f"{m * fu:.{cf}f}", xy=(xa, m), fontsize=10,
                         fontweight='bold', color=VERMELHO,
                         ha='center', va='bottom')
    x0 = xs_ap[0]
    for v in est['vaos']:
        if v['M_pos'] > 0.05:
            axm.annotate(f"{v['M_pos'] * fu:.{cf}f}",
                         xy=(x0 + v['x_pos'], v['M_pos']),
                         fontsize=10, fontweight='bold', color=VERDE,
                         ha='center', va='top')
        x0 += v['L']

    axm.invert_yaxis()  # convenção: momento positivo para baixo
    axm.set_ylabel(f"M [{un_f}·m]", fontsize=11)
    axv.set_ylabel(f"V [{un_f}]", fontsize=11)
    axv.set_xlabel("x [m]", fontsize=11)
    fig.tight_layout()
    return fig


def fig_detalhamento(res):
    est = res['estatica']
    q = res['quantitativo']
    xs_ap = _posicoes_apoios(est)
    L_tot = xs_ap[-1] + (est['bal_dir']['L'] if est['bal_dir'] else 0.0)
    fig, ax = plt.subplots(figsize=(_larg_fig(est), 3.6), dpi=150)
    fig.patch.set_facecolor('white')
    ax.set_xlim(-0.05 * L_tot, 1.05 * L_tot)
    ax.set_ylim(-2.5, 2.3)
    ax.axis('off')

    ax.fill_between([0, L_tot], -0.35, 0.35, color=CONCRETO, zorder=1)
    for j, xa in enumerate(xs_ap):
        ax.plot(xa, -0.35, marker='^', color=NAVY, ms=14, zorder=3)

    # negativos (vermelho, no topo, comprimento real)
    for p in q['posicoes']:
        if 'apoio' in p:
            xa = xs_ap[p['apoio']]
            xi = max(0.0, xa - p['comp_unit'] / 2)
            xf = min(L_tot, xa + p['comp_unit'] / 2)
            if p['apoio'] == 0 and est['bal_esq']:
                xi, xf = 0.0, min(L_tot, xa + p['comp_unit']
                                  - est['bal_esq']['L'])
            if p['apoio'] == len(xs_ap) - 1 and est['bal_dir']:
                xi = max(0.0, xa - (p['comp_unit'] - est['bal_dir']['L']))
                xf = L_tot
            ax.plot([xi, xf], [0.22, 0.22], color=VERMELHO, lw=3.2,
                    solid_capstyle='butt')
            ax.text(xa, 0.48,
                    f"{p['qtd']} ø{p['phi']:.1f}\nc={p['comp_unit']:.2f} m",
                    ha='center', va='bottom', color=VERMELHO, fontsize=9.5,
                    fontweight='bold')
    # positivos (verde, embaixo, por vão)
    x0 = xs_ap[0]
    for i, v in enumerate(est['vaos']):
        p = next((p for p in q['posicoes'] if p.get('vao') == i), None)
        if p:
            ax.plot([x0 + 0.05, x0 + v['L'] - 0.05], [-0.22, -0.22],
                    color=VERDE, lw=3.2, solid_capstyle='butt')
            ax.text(x0 + v['L'] / 2, -0.62,
                    f"{p['qtd']} ø{p['phi']:.1f} · c={p['comp_unit']:.2f} m",
                    ha='center', va='top', color=VERDE, fontsize=9.5,
                    fontweight='bold')
        x0 += v['L']
    # estribos (texto por tramo)
    x0 = xs_ap[0]
    for i, (v, e) in enumerate(zip(est['vaos'], res['estribos'])):
        ax.text(x0 + v['L'] / 2, -1.55, f"est. {e['texto']}", ha='center',
                va='top', color=AMBAR, fontsize=9.5, fontweight='bold',
                style='italic')
        x0 += v['L']
    if est['bal_esq'] and res['estribo_be']:
        ax.text(est['bal_esq']['L'] / 2, -1.55,
                f"est. {res['estribo_be']['texto']}", ha='center', va='top',
                color=AMBAR, fontsize=9.5, fontweight='bold', style='italic')
    if est['bal_dir'] and res['estribo_bd']:
        ax.text(xs_ap[-1] + est['bal_dir']['L'] / 2, -1.55,
                f"est. {res['estribo_bd']['texto']}", ha='center', va='top',
                color=AMBAR, fontsize=9.5, fontweight='bold', style='italic')

    d = res['dados']
    ax.text(0.99, 0.97, f"Seção {d['b']:.0f}×{d['h']:.0f} · C{d['fck']:.0f}",
            transform=ax.transAxes, ha='right', va='top', fontsize=10,
            fontweight='bold', color=CINZA_TXT)
    fig.tight_layout()
    return fig


# ============================================== corte transversal + estribo
def _dados_corte(res, tipo, idx):
    """Barras inferior/superior e estribo da seção escolhida."""
    n_vaos = len(res['estatica']['vaos'])
    if tipo == 'vao':
        sel_inf = res['flex_vaos'][idx]['sel']
        sel_sup = None                       # meio do vão: porta-estribos
        e = res['estribos'][idx]
    else:                                    # corte no apoio
        i_adj = idx if idx < n_vaos else idx - 1
        sel_inf = res['flex_vaos'][i_adj]['sel']
        sel_sup = res['flex_apoios'][idx]['sel']
        e = res['estribos'][i_adj]
    return sel_inf, sel_sup, e


def _desenha_fileiras(ax, sel, b, h, cob, phi_t, lado, cor):
    """Desenha as barras (círculos em escala) na parte inferior/superior."""
    n = sel['n']
    phi = sel['phi'] / 10.0
    camadas = sel.get('camadas', 1)
    por_camada = int(math.ceil(n / camadas))
    ev = max(2.0, phi)
    x0 = cob + phi_t + phi / 2.0
    x1 = b - x0
    desenhadas = 0
    for cam in range(camadas):
        cnt = min(por_camada, n - desenhadas)
        if cnt <= 0:
            break
        y = cob + phi_t + phi / 2.0 + cam * (phi + ev)
        if lado == 'sup':
            y = h - y
        xs = [(x0 + x1) / 2.0] if cnt == 1 else np.linspace(x0, x1, cnt)
        for x in xs:
            ax.add_patch(plt.Circle((x, y), phi / 2.0, color=cor,
                                    ec='white', lw=0.6, zorder=6))
        desenhadas += cnt


def fig_corte_estribo(res, tipo, idx, titulo):
    """Figura dupla: corte transversal (esq.) + detalhe do estribo (dir.)."""
    d = res['dados']
    b, h, cob = d['b'], d['h'], d['cob']
    q = res['quantitativo']
    sel_inf, sel_sup, e = _dados_corte(res, tipo, idx)
    phi_t = e['phi_t'] / 10.0

    fig, (ax, ax2) = plt.subplots(1, 2, figsize=(7.2, 4.6), dpi=150)
    fig.patch.set_facecolor('white')

    # ------------------- corte transversal
    ax.add_patch(plt.Rectangle((0, 0), b, h, facecolor=CONCRETO,
                               edgecolor=CINZA_TXT, lw=2.0))
    ax.add_patch(plt.Rectangle((cob, cob), b - 2 * cob, h - 2 * cob,
                               facecolor='none', edgecolor=AMBAR,
                               lw=1.8, zorder=4))
    _desenha_fileiras(ax, sel_inf, b, h, cob, phi_t, 'inf', VERDE)
    if sel_sup is not None:
        _desenha_fileiras(ax, sel_sup, b, h, cob, phi_t, 'sup', VERMELHO)
        txt_sup = f"{sel_sup['n']} ø{sel_sup['phi']:.1f} (neg.)"
        cor_sup = VERMELHO
    else:
        # porta-estribos 2 ø8 nos cantos superiores
        for x in (cob + phi_t + 0.4, b - cob - phi_t - 0.4):
            ax.add_patch(plt.Circle((x, h - cob - phi_t - 0.4), 0.4,
                                    color=CINZA_TXT, ec='white', lw=0.6,
                                    zorder=6))
        txt_sup = "2 ø8.0 (porta-estribos)"
        cor_sup = CINZA_TXT
    ax.text(b / 2, h + 1.0, txt_sup, ha='center', va='bottom',
            color=cor_sup, fontsize=10, fontweight='bold')
    ax.text(b / 2, -1.0,
            f"{sel_inf['n']} ø{sel_inf['phi']:.1f} (pos.)"
            + (" · 2 camadas" if sel_inf.get('camadas', 1) == 2 else ""),
            ha='center', va='top', color=VERDE, fontsize=10,
            fontweight='bold')
    # armadura de pele (h > 60) — barras nas 2 faces laterais
    pl = res.get('pele')
    if pl:
        cor_pl = "#7C3AED"
        phi_pl = pl['phi'] / 10.0
        xL = cob + phi_t + phi_pl / 2.0
        xR = b - xL
        y0 = cob + phi_t + phi_pl / 2.0
        ys = np.linspace(y0, h - y0, pl['n_face'] + 2)[1:-1]
        for yy in ys:
            for xx in (xL, xR):
                ax.add_patch(plt.Circle((xx, yy), phi_pl / 2.0, color=cor_pl,
                                        ec='white', lw=0.5, zorder=6))
        # rótulo à direita da seção, com linha de chamada (sem sobrepor)
        ax.annotate(f"pele: {pl['n_face']} ø{pl['phi']:.1f}\nc/ {pl['s']:.0f} cm",
                    xy=(xR, h / 2), xytext=(b + 4.0, h / 2),
                    ha='left', va='center', fontsize=8.5, color=cor_pl,
                    fontweight='bold',
                    arrowprops=dict(arrowstyle='-', color=cor_pl, lw=0.8))
    # cotas
    ax.annotate('', xy=(b, -3.2), xytext=(0, -3.2),
                arrowprops=dict(arrowstyle='<->', color=CINZA_TXT, lw=1.0))
    ax.text(b / 2, -3.8, f"bw = {b:.0f} cm", ha='center', va='top',
            fontsize=10, fontweight='bold', color=CINZA_TXT)
    ax.annotate('', xy=(-2.4, h), xytext=(-2.4, 0),
                arrowprops=dict(arrowstyle='<->', color=CINZA_TXT, lw=1.0))
    ax.text(-3.1, h / 2, f"h = {h:.0f} cm", ha='right', va='center',
            fontsize=10, fontweight='bold', color=CINZA_TXT, rotation=90)
    ax.set_title(f"Corte — {titulo}", fontsize=11, fontweight='bold',
                 color=NAVY)
    ax.set_xlim(-9, b + (16 if res.get('pele') else 4))
    ax.set_ylim(-7, h + 4)
    ax.set_aspect('equal')
    ax.axis('off')

    # ------------------- detalhe do estribo
    be, he = b - 2 * cob, h - 2 * cob
    gancho = max(5 * phi_t, 5.0)
    ax2.add_patch(plt.Rectangle((0, 0), be, he, facecolor='none',
                                edgecolor=AMBAR, lw=2.6,
                                joinstyle='round'))
    # ganchos a 45° no canto superior esquerdo
    g = gancho / math.sqrt(2)
    ax2.plot([0, g], [he, he - g], color=AMBAR, lw=2.6,
             solid_capstyle='round')
    ax2.plot([0, g * 0.85], [he - 1.1, he - 1.1 - g * 0.85], color=AMBAR,
             lw=2.6, solid_capstyle='round')
    # cotas
    ax2.annotate('', xy=(be, -2.0), xytext=(0, -2.0),
                 arrowprops=dict(arrowstyle='<->', color=CINZA_TXT, lw=1.0))
    ax2.text(be / 2, -2.6, f"{be:.0f} cm", ha='center', va='top',
             fontsize=10, fontweight='bold', color=CINZA_TXT)
    ax2.annotate('', xy=(be + 2.0, 0), xytext=(be + 2.0, he),
                 arrowprops=dict(arrowstyle='<->', color=CINZA_TXT, lw=1.0))
    ax2.text(be + 2.7, he / 2, f"{he:.0f} cm", ha='left', va='center',
             fontsize=10, fontweight='bold', color=CINZA_TXT, rotation=90)
    ax2.annotate(f"ganchos 45°\n≥ {gancho:.0f} cm", xy=(g, he - g),
                 xytext=(be * 0.45, he * 0.86), fontsize=9,
                 color=CINZA_TXT,
                 arrowprops=dict(arrowstyle='->', color=CINZA_TXT, lw=0.8))
    comp_corte = q['comp_estribo'] if q else None
    linhas = [f"Estribo {e['texto']}"]
    if comp_corte:
        linhas.append(f"corte unit. ≈ {comp_corte:.2f} m")
    linhas.append(f"cobrimento {cob:.1f} cm")
    ax2.text(be / 2, -5.2, "\n".join(linhas), ha='center', va='top',
             fontsize=10, fontweight='bold', color=NAVY)
    ax2.set_title("Detalhe do estribo", fontsize=11, fontweight='bold',
                  color=NAVY)
    ax2.set_xlim(-4, be + 8)
    ax2.set_ylim(-11, he + 4)
    ax2.set_aspect('equal')
    ax2.axis('off')

    fig.tight_layout()
    return fig


# ===================================== corte longitudinal (armação) profissional
def _barra_ferro(ax, x1, x2, y, cor, hook=1, lw=3.0, h=0.11):
    """Desenha uma barra reta com ganchos (dobras) nas pontas."""
    ax.plot([x1, x2], [y, y], color=cor, lw=lw, solid_capstyle='round',
            zorder=6)
    for xe in (x1, x2):
        ax.plot([xe, xe], [y, y + hook * h], color=cor, lw=lw,
                solid_capstyle='round', zorder=6)


def _cota(ax, x1, x2, y, texto, cor, dy=0.07):
    ax.annotate('', xy=(x2, y), xytext=(x1, y),
                arrowprops=dict(arrowstyle='<->', color=cor, lw=0.9))
    ax.plot([x1, x1], [y - 0.05, y + 0.05], color=cor, lw=0.8)
    ax.plot([x2, x2], [y - 0.05, y + 0.05], color=cor, lw=0.8)
    ax.text((x1 + x2) / 2, y + dy, texto, ha='center', va='bottom',
            fontsize=8.5, color=cor, fontweight='bold')


def fig_corte_longitudinal(res):
    est = res['estatica']
    q = res['quantitativo']
    d = res['dados']
    xs_ap = _posicoes_apoios(est)
    off_e = est['bal_esq']['L'] if est['bal_esq'] else 0.0
    L_tot = xs_ap[-1] + (est['bal_dir']['L'] if est['bal_dir'] else 0.0)
    n_seg = (len(est['vaos']) + (1 if est['bal_esq'] else 0)
             + (1 if est['bal_dir'] else 0))
    # base 7.2" faz vigas de 1-2 vãos caberem na tela (sem rolagem/corte);
    # 3+ vãos crescem e rolam horizontalmente.
    W = min(28.0, max(7.2, 2.6 * n_seg))
    fig, ax = plt.subplots(figsize=(W, 5.2), dpi=150)
    fig.patch.set_facecolor('white')
    ax.set_xlim(-0.06 * L_tot, 1.13 * L_tot)
    ax.set_ylim(-2.35, 2.25)
    ax.axis('off')

    # ---- concreto (elevação) e apoios
    ax.add_patch(plt.Rectangle((0, 0), L_tot, 1.0, facecolor='#EEF1F6',
                               edgecolor=CINZA_TXT, lw=1.6, zorder=1))
    for j, xa in enumerate(xs_ap):
        ax.plot(xa, 0.0, marker='^', color=NAVY, ms=15, zorder=4,
                clip_on=False)
        ax.text(xa, -0.16, f"{chr(65 + j)}", ha='center', va='top',
                fontsize=10, fontweight='bold', color=NAVY)

    # ---- estribos (ticks verticais) por trecho + rótulo
    def _desenha_estribos(xi, xf, e, rotulo_y):
        if not e or e.get('falha_biela'):
            return
        s = e['s'] / 100.0
        n = 0
        xk = xi + 0.02
        while xk <= xf - 0.01 and n < 400:
            ax.plot([xk, xk], [0.12, 0.88], color=AMBAR, lw=0.8, zorder=3)
            xk += s
            n += 1
        n_est = int(math.ceil((xf - xi) * 100.0 / e['s'])) + 1
        ax.text((xi + xf) / 2, rotulo_y,
                f"estribos {e['texto']} ({n_est} un)", ha='center',
                va='top', fontsize=8.5, color='#78350F', fontweight='bold',
                style='italic')

    x0 = xs_ap[0]
    for i, v in enumerate(est['vaos']):
        _desenha_estribos(x0, x0 + v['L'], res['estribos'][i], -1.28)
        x0 += v['L']
    if est['bal_esq']:
        _desenha_estribos(0.0, off_e, res['estribo_be'], -1.28)
    if est['bal_dir']:
        _desenha_estribos(xs_ap[-1], L_tot, res['estribo_bd'], -1.28)

    # ---- porta-estribos (2 ø8) — linha fina no topo
    pe = next((p for p in q['posicoes'] if 'Porta' in p['descr']), None)
    if pe:
        ax.plot([0.05, L_tot - 0.05], [0.9, 0.9], color=CINZA_TXT, lw=1.6,
                zorder=5)

    # ---- barras NEGATIVAS (topo) com cotas e marcas
    for p in q['posicoes']:
        if 'apoio' not in p:
            continue
        j = p['apoio']
        xa = xs_ap[j]
        Lb = p['comp_unit']
        xi, xf = max(0.0, xa - Lb / 2), min(L_tot, xa + Lb / 2)
        if j == 0 and est['bal_esq']:
            xi, xf = 0.0, min(L_tot, Lb - off_e + xa - off_e * 0)
            xi, xf = 0.0, min(L_tot, xa + (Lb - off_e))
        if j == len(xs_ap) - 1 and est['bal_dir']:
            xi, xf = max(0.0, xa - (Lb - est['bal_dir']['L'])), L_tot
        _barra_ferro(ax, xi, xf, 0.84, VERMELHO, hook=-1)
        _cota(ax, xi, xf, 1.28, f"C = {Lb:.2f} m", VERMELHO)
        ax.text((xi + xf) / 2, 1.55,
                f"{p['pos']}  {p['qtd']} ø{p['phi']:.1f}", ha='center',
                va='bottom', fontsize=9, fontweight='bold', color=VERMELHO)

    # ---- barras POSITIVAS (fundo) com cotas e marcas
    x0 = xs_ap[0]
    for i, v in enumerate(est['vaos']):
        p = next((p for p in q['posicoes'] if p.get('vao') == i), None)
        if p:
            Lb = p['comp_unit']
            cx = x0 + v['L'] / 2.0
            xi, xf = max(0.0, cx - Lb / 2), min(L_tot, cx + Lb / 2)
            _barra_ferro(ax, xi, xf, 0.16, VERDE, hook=1)
            _cota(ax, xi, xf, -0.55, f"C = {Lb:.2f} m", VERDE, dy=-0.22)
            ax.text(cx, -0.92, f"{p['pos']}  {p['qtd']} ø{p['phi']:.1f}",
                    ha='center', va='top', fontsize=9, fontweight='bold',
                    color=VERDE)
        x0 += v['L']

    # ---- cotas dos vãos (base)
    tramos = []
    if est['bal_esq']:
        tramos.append((0.0, off_e))
    xc = xs_ap[0]
    for v in est['vaos']:
        tramos.append((xc, xc + v['L']))
        xc += v['L']
    if est['bal_dir']:
        tramos.append((xs_ap[-1], L_tot))
    for xi, xf in tramos:
        _cota(ax, xi, xf, -1.75, f"{xf - xi:.2f} m", CINZA_TXT, dy=-0.24)

    ax.text(0.0, 2.08, "CORTE LONGITUDINAL — ARMAÇÃO", ha='left',
            va='bottom', fontsize=11, fontweight='bold', color=NAVY)
    ax.text(L_tot, 2.08,
            f"Seção {d['b']:.0f}×{d['h']:.0f} cm · C{d['fck']:.0f} · CA-50",
            ha='right', va='bottom', fontsize=9.5, fontweight='bold',
            color=CINZA_TXT)
    # legenda
    ax.plot([0.0, 0.6], [-2.15, -2.15], color=VERMELHO, lw=3)
    ax.text(0.7, -2.15, "negativo (topo)", va='center', fontsize=8.5,
            color=VERMELHO, fontweight='bold')
    ax.plot([0.0, 0.6], [-2.32, -2.32], color=VERDE, lw=3)
    ax.text(0.7, -2.32, "positivo (fundo)", va='center', fontsize=8.5,
            color=VERDE, fontweight='bold')
    fig.tight_layout()
    return fig


# ========================================== zona segura para furos na viga
def zonas_furos(res):
    """Janelas horizontais seguras para furo pequeno (por vão interno).

    Critério (guia prático, NBR 6118 §21.3 — furos que atravessam a largura):
    - horizontal: a ≥ 2h da face de cada apoio (região de baixo cortante);
    - vertical: terço médio da altura (em torno da linha neutra), longe da
      armadura de tração (fundo) e da zona comprimida (topo);
    - diâmetro do furo ≤ h/3 e ≤ 12 cm; distância entre furos ≥ 2h.
    Balanços e regiões próximas aos apoios ficam de fora (cortante alto).
    """
    est = res['estatica']
    h_cm = res['dados']['h']
    dois_h = 2.0 * h_cm / 100.0                     # m
    xs_ap = _posicoes_apoios(est)
    janelas = []
    for i in range(len(est['vaos'])):
        xa, xb = xs_ap[i], xs_ap[i + 1]
        xi, xf = xa + dois_h, xb - dois_h
        if xf - xi > 0.10:                          # janela útil ≥ 10 cm
            janelas.append({'vao': i + 1, 'x_ini': xi, 'x_fim': xf,
                            'larg': xf - xi})
    return {'janelas': janelas, 'dois_h': dois_h, 'xs_ap': xs_ap,
            'diam_max': min(h_cm / 3.0, 12.0)}


def fig_furos(res):
    est = res['estatica']
    h_cm = res['dados']['h']
    z = zonas_furos(res)
    xs_ap = z['xs_ap']
    off_e = est['bal_esq']['L'] if est['bal_esq'] else 0.0
    L_tot = xs_ap[-1] + (est['bal_dir']['L'] if est['bal_dir'] else 0.0)

    fig, ax = plt.subplots(
        figsize=(min(26.0, max(7.2, 2.0 * (len(est['vaos']) + 2))), 3.8),
        dpi=150)
    fig.patch.set_facecolor('white')
    ax.set_xlim(-0.05 * L_tot, 1.13 * L_tot)
    ax.set_ylim(-0.55, 1.55)
    ax.axis('off')

    # corpo da viga
    ax.add_patch(plt.Rectangle((0, 0), L_tot, 1.0, facecolor='#EEF1F6',
                               edgecolor=CINZA_TXT, lw=1.5, zorder=1))
    # terços superior e inferior = evitar (armaduras / zona comprimida)
    for y0 in (0.0, 2.0 / 3.0):
        ax.add_patch(plt.Rectangle((0, y0), L_tot, 1.0 / 3.0,
                                   facecolor='none', edgecolor=VERMELHO,
                                   hatch='///', lw=0.0, alpha=0.30, zorder=2))
    # terço médio (faixa candidata, em torno da linha neutra)
    ax.add_patch(plt.Rectangle((0, 1.0 / 3.0), L_tot, 1.0 / 3.0,
                               facecolor=VERDE, alpha=0.08, zorder=2))
    ax.text(-0.01 * L_tot, 1.0 / 6.0, "fundo: armadura de tração",
            ha='left', va='center', fontsize=7.5, color=VERMELHO,
            rotation=0, alpha=0.9)
    ax.text(-0.01 * L_tot, 5.0 / 6.0, "topo: zona comprimida",
            ha='left', va='center', fontsize=7.5, color=VERMELHO, alpha=0.9)

    # zonas de alto cortante (perto dos apoios) e balanços = evitar (altura toda)
    evitar = []
    if off_e > 0:
        evitar.append((0.0, off_e))
    if est['bal_dir']:
        evitar.append((xs_ap[-1], L_tot))
    for xa in xs_ap:
        evitar.append((max(0.0, xa - z['dois_h']),
                       min(L_tot, xa + z['dois_h'])))
    for xi, xf in evitar:
        if xf > xi:
            ax.add_patch(plt.Rectangle((xi, 0), xf - xi, 1.0,
                                       facecolor='none', edgecolor=VERMELHO,
                                       hatch='xxx', lw=0.0, alpha=0.22,
                                       zorder=3))

    # janelas seguras (terço médio, longe dos apoios) = pode furar
    for j in z['janelas']:
        ax.add_patch(plt.Rectangle((j['x_ini'], 1.0 / 3.0), j['larg'],
                                   1.0 / 3.0, facecolor=VERDE, alpha=0.45,
                                   edgecolor=VERDE, lw=2.2, zorder=4))
        xm = 0.5 * (j['x_ini'] + j['x_fim'])
        ax.plot(xm, 0.5, marker='o', ms=12, markerfacecolor='white',
                markeredgecolor='#0f5132', markeredgewidth=1.8, zorder=6)
        ax.text(xm, 0.20, "furo OK", ha='center', va='center',
                color='#0f5132', fontsize=8.5, fontweight='bold', zorder=6)

    # linha neutra
    ax.plot([0, L_tot], [0.5, 0.5], color=NAVY, lw=1.7,
            ls=(0, (6, 3)), zorder=5)
    ax.annotate("linha neutra", xy=(L_tot, 0.5),
                xytext=(L_tot * 1.015, 0.5), ha='left', va='center',
                fontsize=9, fontweight='bold', color=NAVY,
                arrowprops=dict(arrowstyle='-', color=NAVY, lw=0.8))

    # apoios
    for jdx, xa in enumerate(xs_ap):
        ax.plot(xa, 0.0, marker='^', color=NAVY, ms=13, zorder=7,
                clip_on=False)
        ax.text(xa, -0.13, chr(65 + jdx), ha='center', va='top',
                fontsize=9, fontweight='bold', color=NAVY)

    # cota do 2h no primeiro vão
    if xs_ap:
        x0 = xs_ap[0]
        ax.annotate('', xy=(x0 + z['dois_h'], -0.34), xytext=(x0, -0.34),
                    arrowprops=dict(arrowstyle='<->', color=CINZA_TXT,
                                    lw=1.0))
        ax.text(x0 + z['dois_h'] / 2, -0.40,
                f"≥ 2h = {z['dois_h']:.2f} m", ha='center', va='top',
                fontsize=8.5, color=CINZA_TXT, fontweight='bold')

    # título / limite de diâmetro
    ax.text(L_tot / 2, 1.42,
            f"Furo pequeno (tubulação): Ø ≤ {z['diam_max']:.0f} cm "
            f"(h/3 e ≤ 12 cm) · distância entre furos ≥ 2h",
            ha='center', va='top', fontsize=9, fontweight='bold',
            color=NAVY)
    if not z['janelas']:
        ax.text(L_tot / 2, 0.5,
                "Sem zona dispensada de verificação\n"
                "(vãos < 4h) — consultar projetista",
                ha='center', va='center', fontsize=9, color=VERMELHO,
                fontweight='bold', zorder=8)
    fig.tight_layout()
    return fig
