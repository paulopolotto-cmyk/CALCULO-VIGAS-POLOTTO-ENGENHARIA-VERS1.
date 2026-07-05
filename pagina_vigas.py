# -*- coding: utf-8 -*-
"""
Página VIGAS — Polotto Engenharia (motor de cálculo em motor_viga.py).
Dimensionamento conforme NBR 6118 (ELU flexão e cortante).
"""
import io
import json
import math

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st

import motor_viga as mv
from ui_comum import (NAVY, AMBAR, VERMELHO, VERDE, CINZA_TXT, CONCRETO,
                      aplicar_estilo, header, sec)

aplicar_estilo()
header("Cálculo de Vigas Contínuas",
       "Concreto armado · NBR 6118 · CA-50 · ELU flexão e cortante")

# ------------------------------------------------------------ estado
ss = st.session_state
if 'lista_vaos' not in ss:
    ss.lista_vaos = []
if 'edit_index' not in ss:
    ss.edit_index = None
if 'res' not in ss:
    ss.res = None
if 'res_fp' not in ss:
    ss.res_fp = None
if 'confirmar_limpar' not in ss:
    ss.confirmar_limpar = False


def nomes_tramos(lista):
    """Nomes derivados da posição (renumeração sempre correta)."""
    nomes, n_norm = [], 0
    for t in lista:
        if t['tipo'] == 'Normal':
            n_norm += 1
            nomes.append(f"Vão {n_norm}")
        else:
            nomes.append(t['tipo'])
    return nomes


# ------------------------------------------------------------ seção 1
sec(1, "Seção, concreto e aço")
c1, c2 = st.columns(2)
b = c1.number_input("Base bw [cm]", min_value=10.0, max_value=100.0,
                    value=15.0, step=1.0, format="%.0f")
h = c2.number_input("Altura h [cm]", min_value=15.0, max_value=200.0,
                    value=50.0, step=1.0, format="%.0f")
c3, c4 = st.columns(2)
fck = c3.number_input("Concreto fck [MPa]", min_value=20, max_value=50,
                      value=25, step=5)
cob = c4.number_input("Cobrimento c [cm]", min_value=2.0, max_value=5.0,
                      value=2.5, step=0.5, format="%.1f",
                      help="CAA I: 2,5 · CAA II: 3,0 · CAA III: 4,0 (Tab. 7.2)")
pp = st.checkbox("Incluir peso próprio automaticamente "
                 f"(g = {25.0 * b * h / 1e4:.2f} kN/m)", value=True)
st.caption("Aço: CA-50 (longitudinal e estribos) · γf=1,4 · γc=1,4 · γs=1,15")

dados_g = {'b': b, 'h': h, 'fck': fck, 'cob': cob, 'peso_proprio': pp}

# ------------------------------------------------------------ seção 2
sec(2, "Tramos da viga")

nomes = nomes_tramos(ss.lista_vaos)
editando = ss.edit_index is not None

if editando and ss.edit_index >= len(ss.lista_vaos):
    ss.edit_index = None          # proteção extra contra índice órfão
    editando = False

if not editando:
    with st.form("form_tramo", clear_on_submit=False):
        tipo = st.selectbox("Tipo do tramo",
                            ["Normal", "Balanço Esquerdo", "Balanço Direito"])
        cL, cQ = st.columns(2)
        L_in = cL.number_input("Comprimento L [m]", min_value=0.1,
                               max_value=30.0, value=4.0, step=0.1,
                               format="%.2f")
        q_in = cQ.number_input("Carga distribuída q [kN/m]", min_value=0.0,
                               max_value=500.0, value=15.0, step=0.5,
                               format="%.2f")
        cP, cA = st.columns(2)
        P_in = cP.number_input("Carga concentrada P [kN]", min_value=0.0,
                               max_value=2000.0, value=0.0, step=1.0,
                               format="%.2f")
        a_in = cA.number_input("Posição de P: a [m] (da esquerda do tramo)",
                               min_value=0.0, max_value=30.0, value=0.0,
                               step=0.05, format="%.2f")
        inserir = st.form_submit_button("➕ Inserir tramo", width="stretch")
    if inserir:
        erros_t = []
        if P_in > 0 and not (0 <= a_in <= L_in):
            erros_t.append(f"A posição da carga (a = {a_in:.2f} m) precisa "
                           f"estar dentro do tramo (0 ≤ a ≤ {L_in:.2f} m).")
        if tipo == "Balanço Esquerdo" and any(
                t['tipo'] == tipo for t in ss.lista_vaos):
            erros_t.append("Já existe um Balanço Esquerdo.")
        if tipo == "Balanço Direito" and any(
                t['tipo'] == tipo for t in ss.lista_vaos):
            erros_t.append("Já existe um Balanço Direito.")
        if erros_t:
            for e in erros_t:
                st.error(e)
        else:
            ss.lista_vaos.append({'tipo': tipo, 'L': L_in, 'q': q_in,
                                  'P': P_in, 'a': a_in})
            ss.res = None
            st.rerun()
else:
    i = ss.edit_index
    t = ss.lista_vaos[i]
    st.info(f"✏️ Editando: **{nomes[i]}**")
    with st.form("form_edicao"):
        tipos = ["Normal", "Balanço Esquerdo", "Balanço Direito"]
        tipo_e = st.selectbox("Tipo do tramo", tipos,
                              index=tipos.index(t['tipo']))
        cL, cQ = st.columns(2)
        L_e = cL.number_input("Comprimento L [m]", min_value=0.1,
                              max_value=30.0, value=float(t['L']), step=0.1,
                              format="%.2f")
        q_e = cQ.number_input("Carga distribuída q [kN/m]", min_value=0.0,
                              max_value=500.0, value=float(t['q']), step=0.5,
                              format="%.2f")
        cP, cA = st.columns(2)
        P_e = cP.number_input("Carga concentrada P [kN]", min_value=0.0,
                              max_value=2000.0, value=float(t['P']), step=1.0,
                              format="%.2f")
        a_e = cA.number_input("Posição de P: a [m] (da esquerda do tramo)",
                              min_value=0.0, max_value=30.0,
                              value=float(t['a']), step=0.05, format="%.2f")
        cs, cc = st.columns(2)
        salvar = cs.form_submit_button("💾 Salvar", width="stretch")
        cancelar = cc.form_submit_button("✖ Cancelar", width="stretch")
    if salvar:
        erros_t = []
        if P_e > 0 and not (0 <= a_e <= L_e):
            erros_t.append(f"A posição da carga (a = {a_e:.2f} m) precisa "
                           f"estar dentro do tramo (0 ≤ a ≤ {L_e:.2f} m).")
        outros = [x for k, x in enumerate(ss.lista_vaos) if k != i]
        if tipo_e == "Balanço Esquerdo" and any(
                x['tipo'] == tipo_e for x in outros):
            erros_t.append("Já existe um Balanço Esquerdo.")
        if tipo_e == "Balanço Direito" and any(
                x['tipo'] == tipo_e for x in outros):
            erros_t.append("Já existe um Balanço Direito.")
        if erros_t:
            for e in erros_t:
                st.error(e)
        else:
            ss.lista_vaos[i] = {'tipo': tipo_e, 'L': L_e, 'q': q_e,
                                'P': P_e, 'a': a_e}
            ss.edit_index = None
            ss.res = None
            st.rerun()
    if cancelar:
        ss.edit_index = None
        st.rerun()

# lista de tramos
if ss.lista_vaos:
    st.write("")
    nomes = nomes_tramos(ss.lista_vaos)
    for i, t in enumerate(ss.lista_vaos):
        linha = (f"**{nomes[i]}** · L = {t['L']:.2f} m · "
                 f"q = {t['q']:.2f} kN/m")
        if t['P'] > 0:
            linha += f" · P = {t['P']:.1f} kN em a = {t['a']:.2f} m"
        if editando:
            st.markdown(f'<div class="pol-tramo">{linha}</div>',
                        unsafe_allow_html=True)
        else:
            ct, ce, cd = st.columns([5, 1, 1])
            ct.markdown(f'<div class="pol-tramo">{linha}</div>',
                        unsafe_allow_html=True)
            if ce.button("✏️", key=f"ed_{i}", help="Editar tramo"):
                ss.edit_index = i
                st.rerun()
            if cd.button("🗑️", key=f"dl_{i}", help="Excluir tramo"):
                ss.lista_vaos.pop(i)
                ss.res = None
                st.rerun()

    st.write("")
    calcular = st.button("⚡ CALCULAR VIGA", type="primary",
                         width="stretch", disabled=editando)
else:
    calcular = False
    st.caption("Insira os tramos da viga para calcular "
               "(pelo menos 1 vão normal).")

# --------------------------------------------------- cálculo + invalidação
fp_atual = json.dumps([dados_g, ss.lista_vaos], sort_keys=True)
if calcular:
    ss.res = mv.calcular_viga(dados_g, [
        {'nome': n, **t} for n, t in zip(nomes_tramos(ss.lista_vaos),
                                         ss.lista_vaos)])
    ss.res_fp = fp_atual
elif ss.res is not None and ss.res_fp != fp_atual:
    ss.res = None
    st.info("Os dados mudaram — toque em **CALCULAR VIGA** para atualizar "
            "os resultados.")


# =================================================================== figuras
def _posicoes_apoios(est):
    """x global de cada apoio (m); x=0 na ponta esquerda da viga."""
    off = est['bal_esq']['L'] if est['bal_esq'] else 0.0
    xs = [off]
    for v in est['vaos']:
        xs.append(xs[-1] + v['L'])
    return xs


def fig_esquema(res):
    est = res['estatica']
    xs_ap = _posicoes_apoios(est)
    L_tot = xs_ap[-1] + (est['bal_dir']['L'] if est['bal_dir'] else 0.0)
    fig, ax = plt.subplots(figsize=(7.2, 3.4), dpi=150)
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
        ax.text(xa, -1.05, f"{chr(65 + j)}\n{est['Reacoes'][j]:.1f} kN",
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
            ax.text((xi + xf) / 2, 1.05, f"q = {tr['q']:.2f} kN/m",
                    ha='center', va='bottom', color=NAVY, fontsize=10,
                    fontweight='bold')
        if tr['P'] > 0:
            xp = xi + tr['a']
            ax.annotate('', xy=(xp, 0.26), xytext=(xp, 2.35),
                        arrowprops=dict(arrowstyle='-|>', color=VERMELHO,
                                        lw=2.2))
            ax.text(xp, 2.42, f"P = {tr['P']:.1f} kN",
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


def fig_diagramas(res):
    est = res['estatica']
    xs_ap = _posicoes_apoios(est)
    fig, (axm, axv) = plt.subplots(2, 1, figsize=(7.2, 5.6), dpi=150,
                                   sharex=True)
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
            axm.annotate(f"{m:.1f}", xy=(xa, m), fontsize=10,
                         fontweight='bold', color=VERMELHO,
                         ha='center', va='bottom')
    x0 = xs_ap[0]
    for v in est['vaos']:
        if v['M_pos'] > 0.05:
            axm.annotate(f"{v['M_pos']:.1f}", xy=(x0 + v['x_pos'],
                                                  v['M_pos']),
                         fontsize=10, fontweight='bold', color=VERDE,
                         ha='center', va='top')
        x0 += v['L']

    axm.invert_yaxis()  # convenção: momento positivo para baixo
    axm.set_ylabel("M [kN·m]", fontsize=11)
    axv.set_ylabel("V [kN]", fontsize=11)
    axv.set_xlabel("x [m]", fontsize=11)
    fig.tight_layout()
    return fig


def fig_detalhamento(res):
    est = res['estatica']
    q = res['quantitativo']
    xs_ap = _posicoes_apoios(est)
    L_tot = xs_ap[-1] + (est['bal_dir']['L'] if est['bal_dir'] else 0.0)
    fig, ax = plt.subplots(figsize=(7.2, 3.6), dpi=150)
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
    ax.set_xlim(-9, b + 4)
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


# ================================================================ memorial
def gerar_memorial(res, nomes_lista):
    d = res['dados']
    est = res['estatica']
    ln = []
    ln.append("=" * 62)
    ln.append("MEMORIAL DE CÁLCULO — VIGA CONTÍNUA (NBR 6118)")
    ln.append("Polotto Engenharia")
    ln.append("=" * 62)
    ln.append(f"Seção: {d['b']:.0f} x {d['h']:.0f} cm | fck = {d['fck']:.0f} "
              f"MPa | Aço CA-50 | c = {d['cob']:.1f} cm | d = {d['d']:.1f} cm")
    if d['g_pp'] > 0:
        ln.append(f"Peso próprio incluído: g = {d['g_pp']:.2f} kN/m")
    ln.append("")
    ln.append("TRAMOS:")
    for n, v in zip(nomes_lista, ss.lista_vaos):
        s = (f"  {n}: L = {v['L']:.2f} m | q = {v['q']:.2f} kN/m")
        if v['P'] > 0:
            s += f" | P = {v['P']:.1f} kN em a = {v['a']:.2f} m"
        ln.append(s)
    ln.append("")
    ln.append("MOMENTOS NOS APOIOS (kN·m):")
    for j, m in enumerate(est['M_apoios']):
        ln.append(f"  Apoio {chr(65 + j)}: {m:8.2f}")
    ln.append("MOMENTOS POSITIVOS MÁXIMOS (kN·m):")
    for i, v in enumerate(est['vaos']):
        ln.append(f"  Vão {i + 1}: {v['M_pos']:8.2f}  (x = {v['x_pos']:.2f} m)")
    ln.append("REAÇÕES (kN):")
    for j, r in enumerate(est['Reacoes']):
        ln.append(f"  Apoio {chr(65 + j)}: {r:8.2f}")
    ln.append("")
    ln.append("ARMADURA LONGITUDINAL:")
    for j, fx in enumerate(res['flex_apoios']):
        if fx['sel'] and not fx['sel'].get('construtiva'):
            ln.append(f"  Apoio {chr(65 + j)} (neg.): As = {fx['As']:.2f} cm²"
                      f" -> {fx['sel']['texto']}")
    for i, fx in enumerate(res['flex_vaos']):
        if fx['sel']:
            ln.append(f"  Vão {i + 1} (pos.):  As = "
                      f"{(fx['As'] or 0):.2f} cm² -> {fx['sel']['texto']}")
    ln.append("")
    ln.append("ESTRIBOS (2 ramos, CA-50):")
    for i, e in enumerate(res['estribos']):
        ln.append(f"  Vão {i + 1}: {e['texto']}  (Vsd = {e['Vsd']:.1f} kN)")
    if res['estribo_be']:
        ln.append(f"  Balanço esq.: {res['estribo_be']['texto']}")
    if res['estribo_bd']:
        ln.append(f"  Balanço dir.: {res['estribo_bd']['texto']}")
    if res['pele']:
        ln.append("")
        ln.append(f"ARMADURA DE PELE (h > 60): {res['pele']['texto']}")
    q = res['quantitativo']
    if q:
        ln.append("")
        ln.append("QUANTITATIVO DE AÇO:")
        for p in q['posicoes']:
            ln.append(f"  {p['pos']:<4} {p['descr']:<32} ø{p['phi']:>4.1f}  "
                      f"{p['qtd']:>3} un x {p['comp_unit']:6.2f} m  "
                      f"= {p['peso']:7.2f} kg")
        ln.append(f"  PESO TOTAL: {q['peso_total']:.2f} kg | "
                  f"COMPRA (+10%): {q['peso_compra']:.2f} kg")
    ln.append("")
    ln.append("AVISOS / LIMITAÇÕES:")
    for a in res['avisos']:
        ln.append(f"  - {a}")
    ln.append("")
    ln.append("Documento gerado automaticamente — conferir por "
              "profissional habilitado.")
    return "\n".join(ln)


# ================================================================ resultados
if ss.res is not None:
    res = ss.res
    st.write("---")
    if 'erros' in res:
        sec("!", "Corrija a entrada de dados")
        for e in res['erros']:
            st.error(e)
    else:
        est = res['estatica']
        nomes_l = nomes_tramos(ss.lista_vaos)

        # ---- falhas de dimensionamento em destaque
        if res['falha_biela']:
            st.error("🚫 **ESMAGAMENTO DA BIELA (cortante):** Vsd > VRd2. "
                     "REDIMENSIONAR a seção (aumentar bw, h ou fck). "
                     "Quantitativo bloqueado.")
        if res['falha_flexao']:
            locais = []
            for j, fx in enumerate(res['flex_apoios']):
                if fx.get('falha'):
                    locais.append(f"apoio {chr(65 + j)}")
            for i, fx in enumerate(res['flex_vaos']):
                if fx.get('falha'):
                    locais.append(f"vão {i + 1}")
            st.error("🚫 **SEÇÃO INSUFICIENTE À FLEXÃO** em: "
                     + ", ".join(locais)
                     + ". REDIMENSIONAR (aumentar h, bw ou fck). "
                       "Quantitativo bloqueado.")

        # ---- avisos de escopo
        with st.expander("⚠️ Avisos e hipóteses de cálculo", expanded=False):
            for a in res['avisos']:
                st.markdown(f"- {a}")

        # ---- esquema estrutural
        sec(3, "Esquema estrutural e reações")
        f1 = fig_esquema(res)
        st.pyplot(f1, width="stretch")
        plt.close(f1)

        # ---- diagramas
        sec(4, "Diagramas de esforços")
        f2 = fig_diagramas(res)
        st.pyplot(f2, width="stretch")
        plt.close(f2)

        # ---- armaduras
        sec(5, "Armadura longitudinal")
        rows = []
        for j, fx in enumerate(res['flex_apoios']):
            mk = est['M_apoios'][j]
            if fx.get('falha'):
                barras = "❌ REDIMENSIONAR"
                as_txt = "—"
            else:
                barras = fx['sel']['texto']
                as_txt = f"{fx['As']:.2f}" if fx['As'] else "—"
            if abs(mk) > 0.05 or fx.get('falha'):
                rows.append({"Posição": f"Apoio {chr(65 + j)} (neg.)",
                             "Mk [kN·m]": f"{mk:.2f}",
                             "As [cm²]": as_txt, "Barras": barras})
        for i, fx in enumerate(res['flex_vaos']):
            if fx.get('falha'):
                barras = "❌ REDIMENSIONAR"
                as_txt = "—"
            else:
                barras = fx['sel']['texto']
                as_txt = f"{fx['As']:.2f}" if fx['As'] else "—"
            rows.append({"Posição": f"Vão {i + 1} (pos.)",
                         "Mk [kN·m]": f"{est['vaos'][i]['M_pos']:.2f}",
                         "As [cm²]": as_txt, "Barras": barras})
        st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")
        if res['pele']:
            st.info(f"**Armadura de pele (h > 60 cm):** {res['pele']['texto']}")

        # ---- estribos
        sec(6, "Estribos (2 ramos)")
        rows = []
        tramos_e = [(f"Vão {i + 1}", e)
                    for i, e in enumerate(res['estribos'])]
        if res['estribo_be']:
            tramos_e.insert(0, ("Balanço esq.", res['estribo_be']))
        if res['estribo_bd']:
            tramos_e.append(("Balanço dir.", res['estribo_bd']))
        for nome, e in tramos_e:
            if e.get('falha_biela'):
                rows.append({"Tramo": nome, "Vsd [kN]": f"{e['Vsd']:.1f}",
                             "Estribo": "❌ Vsd > VRd2", "Obs.": ""})
            else:
                rows.append({"Tramo": nome, "Vsd [kN]": f"{e['Vsd']:.1f}",
                             "Estribo": e['texto'],
                             "Obs.": e['aviso'] or ""})
        st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")

        # ---- quantitativo
        q = res['quantitativo']
        if q:
            sec(7, "Detalhamento")
            f3 = fig_detalhamento(res)
            st.pyplot(f3, width="stretch")
            png = io.BytesIO()
            f3.savefig(png, format='png', dpi=200, bbox_inches='tight')
            plt.close(f3)

            # ---- corte transversal + detalhe do estribo
            opcoes_corte = [('vao', i, f"Vão {i + 1} (meio do vão)")
                            for i in range(len(est['vaos']))]
            for j, fx in enumerate(res['flex_apoios']):
                if fx.get('sel') and not fx['sel'].get('construtiva'):
                    opcoes_corte.append(('apoio', j, f"Apoio {chr(65 + j)}"))
            k = st.selectbox("Posição do corte transversal:",
                             range(len(opcoes_corte)),
                             format_func=lambda k: opcoes_corte[k][2])
            tipo_c, idx_c, titulo_c = opcoes_corte[k]
            f4 = fig_corte_estribo(res, tipo_c, idx_c, titulo_c)
            st.pyplot(f4, width="stretch")
            png_corte = io.BytesIO()
            f4.savefig(png_corte, format='png', dpi=200,
                       bbox_inches='tight')
            plt.close(f4)

            sec(8, "Quantitativo de aço")
            dfq = pd.DataFrame([{
                "Pos": p['pos'], "Descrição": p['descr'],
                "ø [mm]": p['phi'], "Qtd": p['qtd'],
                "Comp. [m]": round(p['comp_unit'], 2),
                "Peso [kg]": round(p['peso'], 2)} for p in q['posicoes']])
            st.dataframe(dfq, hide_index=True, width="stretch")

            m1, m2 = st.columns(2)
            m1.metric("Peso total de aço", f"{q['peso_total']:.1f} kg")
            m2.metric("Compra (+10%)", f"{q['peso_compra']:.1f} kg")

            dfc = pd.DataFrame([{
                "ø [mm]": c['phi'],
                "Comp. total [m]": round(c['comp_total'], 1),
                "c/ 10% [m]": round(c['comp_compra'], 1),
                "Barras 12 m": c['barras_12m'],
                "Peso compra [kg]": round(c['peso_compra'], 2)}
                for c in q['lista_compra']])
            st.markdown("**🛒 Lista de compra (barras comerciais de 12 m):**")
            st.dataframe(dfc, hide_index=True, width="stretch")
            for av in q['avisos']:
                st.warning(av)

            # ---- exportação
            sec(9, "Exportar")
            ce1, ce2 = st.columns(2)
            ce1.download_button(
                "📄 Memorial (.txt)",
                gerar_memorial(res, nomes_l).encode('utf-8'),
                file_name=f"Viga_{b:.0f}x{h:.0f}_memorial.txt",
                mime="text/plain", width="stretch")
            ce2.download_button(
                "🖼️ Detalhamento (.png)", png.getvalue(),
                file_name=f"Viga_{b:.0f}x{h:.0f}_detalhamento.png",
                mime="image/png", width="stretch")
            st.download_button(
                "🖼️ Corte transversal + estribo (.png)",
                png_corte.getvalue(),
                file_name=f"Viga_{b:.0f}x{h:.0f}_corte_{titulo_c}.png",
                mime="image/png", width="stretch")

# ------------------------------------------------------------ limpar tudo
st.write("")
if not ss.confirmar_limpar:
    if st.button("🔄 Limpar tudo e reiniciar", width="stretch"):
        if ss.lista_vaos:
            ss.confirmar_limpar = True
            st.rerun()
else:
    st.warning("Apagar **todos** os tramos e resultados?")
    cs, cn = st.columns(2)
    if cs.button("✔ Sim, apagar tudo", width="stretch"):
        ss.lista_vaos = []
        ss.edit_index = None
        ss.res = None
        ss.res_fp = None
        ss.confirmar_limpar = False
        st.rerun()
    if cn.button("✖ Não, voltar", width="stretch"):
        ss.confirmar_limpar = False
        st.rerun()

st.caption("Ferramenta de apoio — os resultados devem ser conferidos por "
           "profissional habilitado. ELS (flecha/fissuração) não verificado.")
