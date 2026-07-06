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
                      aplicar_estilo, header, sec, seletor_unidade, tabela)

aplicar_estilo()
header("Cálculo de Vigas Contínuas",
       "Concreto armado · NBR 6118 · CA-50 · ELU flexão e cortante")

# unidade de força (kN ou kgf) — o cálculo interno é sempre em kN
fu, un_f, un_fm = seletor_unidade()


def _cf(casas=1):
    return 0 if fu > 1 else casas


def fmt_f(x_kN, casas=1):
    """Formata uma força (kN interno) na unidade escolhida, com rótulo."""
    return f"{x_kN * fu:.{_cf(casas)}f} {un_f}"

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
g_pp_disp = 25.0 * b * h / 1e4 * fu
pp = st.checkbox("Incluir peso próprio automaticamente "
                 f"(g = {g_pp_disp:.{_cf(2)}f} {un_fm})", value=True)
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
    st.caption("💡 Toque em cada campo de carga e digite — eles já começam "
               "vazios (comprimento, carga, posição).")
    with st.form("form_tramo", clear_on_submit=True):
        tipo = st.selectbox("Tipo do tramo",
                            ["Normal", "Balanço Esquerdo", "Balanço Direito"])
        cL, cQ = st.columns(2)
        L_in = cL.number_input("Comprimento L [m]", min_value=0.1,
                               max_value=30.0, value=None, step=0.1,
                               format="%.2f", placeholder="ex: 4,50")
        q_disp = cQ.number_input(f"Carga distribuída q [{un_fm}]",
                                 min_value=0.0, max_value=500.0 * fu,
                                 value=None, step=0.5 * fu,
                                 format=f"%.{_cf(2)}f", placeholder="ex: 15")
        cP, cA = st.columns(2)
        P_disp = cP.number_input(f"Carga concentrada P [{un_f}]",
                                 min_value=0.0, max_value=2000.0 * fu,
                                 value=None, step=1.0 * fu,
                                 format=f"%.{_cf(2)}f",
                                 placeholder="0 se não houver")
        a_in = cA.number_input("Posição de P: a [m] (da esquerda do tramo)",
                               min_value=0.0, max_value=30.0, value=None,
                               step=0.05, format="%.2f",
                               placeholder="0 se não houver")
        inserir = st.form_submit_button("➕ INSERIR TRAMO", width="stretch")
    if inserir:
        q_in = (q_disp or 0.0) / fu          # -> kN (interno)
        P_in = (P_disp or 0.0) / fu
        a_val = a_in or 0.0
        erros_t = []
        if L_in is None or L_in <= 0:
            erros_t.append("Informe o comprimento L do tramo "
                           "(maior que zero).")
        if L_in and P_in > 0 and not (0 <= a_val <= L_in):
            erros_t.append(f"A posição da carga (a = {a_val:.2f} m) precisa "
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
                                  'P': P_in, 'a': a_val})
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
        q_e_disp = cQ.number_input(f"Carga distribuída q [{un_fm}]",
                                   min_value=0.0, max_value=500.0 * fu,
                                   value=float(t['q']) * fu, step=0.5 * fu,
                                   format=f"%.{_cf(2)}f")
        cP, cA = st.columns(2)
        P_e_disp = cP.number_input(f"Carga concentrada P [{un_f}]",
                                   min_value=0.0, max_value=2000.0 * fu,
                                   value=float(t['P']) * fu, step=1.0 * fu,
                                   format=f"%.{_cf(2)}f")
        a_e = cA.number_input("Posição de P: a [m] (da esquerda do tramo)",
                              min_value=0.0, max_value=30.0,
                              value=float(t['a']), step=0.05, format="%.2f")
        cs, cc = st.columns(2)
        salvar = cs.form_submit_button("💾 Salvar", width="stretch")
        cancelar = cc.form_submit_button("✖ Cancelar", width="stretch")
    if salvar:
        q_e = q_e_disp / fu
        P_e = P_e_disp / fu
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
                 f"q = {t['q'] * fu:.{_cf(2)}f} {un_fm}")
        if t['P'] > 0:
            linha += (f" · P = {t['P'] * fu:.{_cf(1)}f} {un_f} "
                      f"em a = {t['a']:.2f} m")
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


def fig_esquema(res, fu=1.0, un_f="kN"):
    cf = 0 if fu > 1 else 1
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

    fig, ax = plt.subplots(figsize=(7.2, 3.8), dpi=150)
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
        ln.append(f"Peso próprio incluído: g = {d['g_pp'] * fu:.{_cf(2)}f} "
                  f"{un_fm}")
    ln.append(f"Unidade de força: {un_f}")
    ln.append("")
    ln.append("TRAMOS:")
    for n, v in zip(nomes_lista, ss.lista_vaos):
        s = (f"  {n}: L = {v['L']:.2f} m | "
             f"q = {v['q'] * fu:.{_cf(2)}f} {un_fm}")
        if v['P'] > 0:
            s += (f" | P = {v['P'] * fu:.{_cf(1)}f} {un_f} "
                  f"em a = {v['a']:.2f} m")
        ln.append(s)
    ln.append("")
    ln.append(f"MOMENTOS NOS APOIOS ({un_f}·m):")
    for j, m in enumerate(est['M_apoios']):
        ln.append(f"  Apoio {chr(65 + j)}: {m * fu:10.{_cf(2)}f}")
    ln.append(f"MOMENTOS POSITIVOS MÁXIMOS ({un_f}·m):")
    for i, v in enumerate(est['vaos']):
        ln.append(f"  Vão {i + 1}: {v['M_pos'] * fu:10.{_cf(2)}f}  "
                  f"(x = {v['x_pos']:.2f} m)")
    ln.append(f"REAÇÕES ({un_f}):")
    for j, r in enumerate(est['Reacoes']):
        ln.append(f"  Apoio {chr(65 + j)}: {r * fu:10.{_cf(2)}f}")
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
        ln.append(f"  Vão {i + 1}: {e['texto']}  "
                  f"(Vsd = {e['Vsd'] * fu:.{_cf(1)}f} {un_f})")
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
    z = zonas_furos(res)
    ln.append("")
    ln.append("ZONAS PARA FUROS DE TUBULAÇÃO (orientativo, NBR 6118 §21.3):")
    ln.append(f"  Diâmetro máx.: {z['diam_max']:.0f} cm (h/3 e ≤ 12 cm) | "
              f"terço médio da altura | distância entre furos ≥ 2h")
    if z['janelas']:
        for j in z['janelas']:
            ln.append(f"  Vão {j['vao']}: furar entre x = {j['x_ini']:.2f} m "
                      f"e x = {j['x_fim']:.2f} m (largura {j['larg']:.2f} m, "
                      f"medido da ponta esquerda da viga)")
    else:
        ln.append("  Nenhuma zona dispensada de verificação (vãos < 4h).")
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
        f1 = fig_esquema(res, fu, un_f)
        st.pyplot(f1, width="stretch")
        plt.close(f1)

        # ---- diagramas
        sec(4, "Diagramas de esforços")
        f2 = fig_diagramas(res, fu, un_f)
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
                             f"Mk [{un_f}·m]": f"{mk * fu:.{_cf(2)}f}",
                             "As [cm²]": as_txt, "Barras": barras})
        for i, fx in enumerate(res['flex_vaos']):
            if fx.get('falha'):
                barras = "❌ REDIMENSIONAR"
                as_txt = "—"
            else:
                barras = fx['sel']['texto']
                as_txt = f"{fx['As']:.2f}" if fx['As'] else "—"
            rows.append({"Posição": f"Vão {i + 1} (pos.)",
                         f"Mk [{un_f}·m]":
                             f"{est['vaos'][i]['M_pos'] * fu:.{_cf(2)}f}",
                         "As [cm²]": as_txt, "Barras": barras})
        tabela(rows)
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
            vsd_txt = f"{e['Vsd'] * fu:.{_cf(1)}f}"
            if e.get('falha_biela'):
                rows.append({"Tramo": nome, f"Vsd [{un_f}]": vsd_txt,
                             "Estribo": "❌ Vsd > VRd2", "Obs.": ""})
            else:
                rows.append({"Tramo": nome, f"Vsd [{un_f}]": vsd_txt,
                             "Estribo": e['texto'],
                             "Obs.": e['aviso'] or ""})
        tabela(rows)

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

            # ---- zona segura para furos
            sec(8, "Onde furar a viga (passagem de tubulação)")
            st.caption("Verde = pode furar · Vermelho = evitar. A **linha "
                       "neutra** tem tensão de flexão nula, mas o cortante é "
                       "máximo nela — por isso o furo deve ficar no **terço "
                       "médio** da altura e **longe dos apoios (≥ 2h)**.")
            f5 = fig_furos(res)
            st.pyplot(f5, width="stretch")
            png_furos = io.BytesIO()
            f5.savefig(png_furos, format='png', dpi=200,
                       bbox_inches='tight')
            plt.close(f5)
            zf = zonas_furos(res)
            if zf['janelas']:
                linhas = [f"Vão {j['vao']}: entre **{j['x_ini']:.2f} m** e "
                          f"**{j['x_fim']:.2f} m** (medido da ponta esquerda "
                          f"da viga)" for j in zf['janelas']]
                st.success("**Furo pequeno permitido** (Ø ≤ "
                           f"{zf['diam_max']:.0f} cm), no terço médio da "
                           "altura, em:\n\n- " + "\n- ".join(linhas))
            else:
                st.warning("Nenhuma zona dispensada de verificação nesta viga "
                           "(vãos curtos, < 4h). Qualquer furo exige análise "
                           "específica do projetista.")
            st.caption("Guia simplificado para furos pequenos de tubulação "
                       "(NBR 6118 §21.3). **Nunca corte armaduras.** Aberturas "
                       "maiores exigem dimensionamento específico com armadura "
                       "de reforço.")

            sec(9, "Quantitativo de aço")
            tabela([{
                "Pos": p['pos'], "Descrição": p['descr'],
                "ø [mm]": p['phi'], "Qtd": p['qtd'],
                "Comp. [m]": f"{p['comp_unit']:.2f}",
                "Peso [kg]": f"{p['peso']:.2f}"} for p in q['posicoes']])

            m1, m2 = st.columns(2)
            m1.metric("Peso total de aço", f"{q['peso_total']:.1f} kg")
            m2.metric("Compra (+10%)", f"{q['peso_compra']:.1f} kg")

            st.markdown("**🛒 Lista de compra (barras comerciais de 12 m):**")
            tabela([{
                "ø [mm]": c['phi'],
                "Comp. total [m]": f"{c['comp_total']:.1f}",
                "c/ 10% [m]": f"{c['comp_compra']:.1f}",
                "Barras 12 m": c['barras_12m'],
                "Peso compra [kg]": f"{c['peso_compra']:.2f}"}
                for c in q['lista_compra']])
            for av in q['avisos']:
                st.warning(av)

            # ---- exportação
            sec(10, "Exportar")
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
            ce3, ce4 = st.columns(2)
            ce3.download_button(
                "🖼️ Corte + estribo (.png)",
                png_corte.getvalue(),
                file_name=f"Viga_{b:.0f}x{h:.0f}_corte_{titulo_c}.png",
                mime="image/png", width="stretch")
            ce4.download_button(
                "🖼️ Zona de furos (.png)", png_furos.getvalue(),
                file_name=f"Viga_{b:.0f}x{h:.0f}_furos.png",
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
