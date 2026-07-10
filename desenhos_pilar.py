# -*- coding: utf-8 -*-
"""Desenhos dos pilares (figuras matplotlib) — extraído de pagina_pilar.py para
ser reusado pela tela manual (por parte) e pelo relatório do Projeto Completo.
Funções PURAS: recebem o `res` de motor_pilar + a opção de armadura escolhida
e devolvem uma Figure."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from ui_comum import NAVY, AMBAR, CINZA_TXT, CONCRETO


def fig_secao(res, opt):
    d = res['dados']
    bb, hh, cob = d['b'], d['h'], d['cob']
    fig, ax = plt.subplots(figsize=(4.6, 4.6), dpi=150)
    fig.patch.set_facecolor('white')
    ax.add_patch(plt.Rectangle((0, 0), bb, hh, facecolor=CONCRETO,
                               edgecolor=CINZA_TXT, lw=2.0))
    ax.add_patch(plt.Rectangle((cob, cob), bb - 2 * cob, hh - 2 * cob,
                               facecolor='none', edgecolor=NAVY,
                               lw=1.6, ls='--'))
    xs = [p[0] for p in opt['pos']]
    ys = [p[1] for p in opt['pos']]
    ax.scatter(xs, ys, s=110, color=AMBAR, edgecolor='white',
               linewidth=1.0, zorder=5)
    ax.annotate('', xy=(bb, -2.2), xytext=(0, -2.2),
                arrowprops=dict(arrowstyle='<->', color=CINZA_TXT, lw=1.0))
    ax.text(bb / 2, -2.8, f"b = {bb:.0f} cm", ha='center', va='top',
            fontsize=11, fontweight='bold', color=CINZA_TXT)
    ax.annotate('', xy=(-2.2, hh), xytext=(-2.2, 0),
                arrowprops=dict(arrowstyle='<->', color=CINZA_TXT, lw=1.0))
    ax.text(-2.9, hh / 2, f"h = {hh:.0f} cm", ha='right', va='center',
            fontsize=11, fontweight='bold', color=CINZA_TXT, rotation=90)
    ax.text(bb / 2, hh + 1.6,
            f"{opt['texto']}  ·  estribo ø{opt['phi_t']:.1f} "
            f"c/{opt['s_est']:.0f}",
            ha='center', va='bottom', fontsize=11, fontweight='bold',
            color=NAVY)
    ax.set_xlim(-8, bb + 4)
    ax.set_ylim(-6, hh + 5)
    ax.set_aspect('equal')
    ax.axis('off')
    fig.tight_layout()
    return fig


_VERM = "#B91C1C"


def fig_pilar_longitudinal(res, opt):
    """Corte longitudinal do pilar: armadura longitudinal, estribos com
    espaçamento, arranque na fundação e ancoragem na viga (encaixe)."""
    d = res['dados']
    b = d['b']
    l0 = d['l0']
    phi = opt['phi']
    nlong = opt['n']
    phit = opt['phi_t']
    sest = opt['s_est']
    n_est = opt['n_est']

    Wp, Hp = 30.0, 150.0                       # pilar (esquemático)
    cobd = 4.5
    xl, xr = cobd, Wp - cobd
    fw, fh = Wp * 2.3, 24.0                     # fundação
    vw, vh = Wp * 2.6, 28.0                     # viga

    fig, ax = plt.subplots(figsize=(5.0, 7.0), dpi=150)
    fig.patch.set_facecolor('white')
    # fundação (base)
    ax.add_patch(plt.Rectangle((Wp / 2 - fw / 2, -fh), fw, fh,
                 facecolor=CONCRETO, edgecolor=CINZA_TXT, lw=1.5, hatch='...'))
    ax.text(Wp / 2, -fh - 3.5, "FUNDAÇÃO (sapata / baldrame)", ha='center',
            va='top', fontsize=8.5, color=CINZA_TXT, fontweight='bold')
    # viga da laje (topo) = engaste
    ax.add_patch(plt.Rectangle((Wp / 2 - vw / 2, Hp), vw, vh,
                 facecolor=CONCRETO, edgecolor=CINZA_TXT, lw=1.5, hatch='///'))
    ax.text(Wp / 2, Hp + vh + 3.5, "VIGA DA LAJE (engaste no topo)",
            ha='center', va='bottom', fontsize=8.5, color=CINZA_TXT,
            fontweight='bold')
    # pilar (concreto)
    ax.add_patch(plt.Rectangle((0, 0), Wp, Hp, facecolor='#EEF2F7',
                 edgecolor=CINZA_TXT, lw=2.0))
    # barras longitudinais (2 faces visíveis) + gancho de ancoragem na viga
    for xb, dh in ((xl, 7), (xr, -7)):
        ax.plot([xb, xb], [-fh * 0.5, Hp + vh * 0.62], color=_VERM, lw=2.4,
                zorder=6)
        ax.plot([xb, xb + dh], [Hp + vh * 0.62, Hp + vh * 0.62], color=_VERM,
                lw=2.4, zorder=6)                # gancho na viga
    # arranque de espera na fundação (barras tracejadas âmbar, traspasse)
    for xb in (xl + 3.2, xr - 3.2):
        ax.plot([xb, xb], [-fh * 0.7, 42], color=AMBAR, lw=1.8,
                ls=(0, (4, 2)), zorder=5)
    # estribos (hoops) no espaçamento real proporcional
    n_show = min(n_est, 16)
    for k in range(n_show):
        yy = 5 + (Hp - 10) * k / max(1, n_show - 1)
        ax.add_patch(plt.Rectangle((cobd - 1.6, yy - 0.6),
                     Wp - 2 * (cobd - 1.6), 1.2, facecolor='none',
                     edgecolor=_VERM, lw=1.1, zorder=4))
    # cotas
    ax.annotate('', xy=(-13, 0), xytext=(-13, Hp),
                arrowprops=dict(arrowstyle='<->', color=NAVY, lw=1.3))
    ax.text(-16, Hp / 2, f"pé-direito\nl0 = {l0:.2f} m", ha='right',
            va='center', fontsize=9, color=NAVY, fontweight='bold',
            rotation=90)
    ax.annotate('', xy=(0, -fh - 9), xytext=(Wp, -fh - 9),
                arrowprops=dict(arrowstyle='<->', color=NAVY, lw=1.3))
    ax.text(Wp / 2, -fh - 11, f"b = {b:.0f} cm", ha='center', va='top',
            fontsize=9, color=NAVY, fontweight='bold')
    # bracket de espaçamento dos estribos (lado direito)
    yb1, yb2 = 5 + (Hp - 10) * 2 / max(1, n_show - 1), 5
    ax.annotate('', xy=(Wp + 10, yb1), xytext=(Wp + 10, yb2),
                arrowprops=dict(arrowstyle='<->', color=_VERM, lw=1.2))
    ax.text(Wp + 12, (yb1 + yb2) / 2, f"c/ {sest:.0f} cm", ha='left',
            va='center', fontsize=8, color=_VERM, fontweight='bold')
    # rótulos com caixa branca (instruções p/ obra)
    _wb = dict(boxstyle="round,pad=0.25", fc="white", ec="none", alpha=.9)
    ax.text(Wp + 12, Hp * 0.62,
            f"{nlong} barras\nø{phi:.1f} mm\n(longitudinal)", ha='left',
            va='center', fontsize=8, color=_VERM, fontweight='bold', bbox=_wb)
    ax.text(Wp + 12, Hp * 0.30,
            f"estribos\nø{phit:.1f} mm\nc/ {sest:.0f} cm", ha='left',
            va='center', fontsize=8, color=_VERM, fontweight='bold', bbox=_wb)
    ax.text(xr + 9, Hp + vh * 0.55,
            f"barras ancoram\nna viga (≈ {int(round(40 * phi / 10))} cm)",
            ha='left', va='center', fontsize=7.5, color=NAVY,
            fontweight='bold', bbox=_wb)
    ax.text(xr - 3.2 + 9, 30, f"arranque de espera\n(traspasse ≈ "
            f"{int(round(50 * phi / 10))} cm)", ha='left', va='center',
            fontsize=7.5, color=AMBAR, fontweight='bold', bbox=_wb)
    ax.set_xlim(-26, Wp + 60)
    ax.set_ylim(-fh - 16, Hp + vh + 9)
    ax.set_aspect('equal')
    ax.axis('off')
    ax.set_title("Corte longitudinal do pilar (execução)", fontsize=10.5,
                 color=NAVY, fontweight='bold')
    fig.tight_layout()
    return fig
