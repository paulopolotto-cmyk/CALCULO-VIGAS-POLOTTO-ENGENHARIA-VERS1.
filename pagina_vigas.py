# -*- coding: utf-8 -*-
"""
Página VIGAS — Polotto Engenharia (motor de cálculo em motor_viga.py).
Dimensionamento conforme NBR 6118 (ELU flexão e cortante).
"""
import io
import json
import math
import zipfile

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import streamlit as st

import motor_viga as mv
from ui_comum import (NAVY, AMBAR, VERMELHO, VERDE, CINZA_TXT, CONCRETO,
                      aplicar_estilo, header, sec, seletor_unidade, tabela,
                      mostrar_figura, seletor_pagina, assistente_carga,
                      EXEMPLOS_VIGA)

aplicar_estilo()
header("Cálculo de Vigas Contínuas e Pilares",
       "Concreto armado · NBR 6118 · CA-50A")

seletor_pagina("vigas")

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
if 'q_sugerido' not in ss:
    ss.q_sugerido = None
for _k, _v in (('viga_b', 15.0), ('viga_h', 50.0), ('viga_fck', 25),
               ('viga_cob', 2.5)):
    if _k not in ss:
        ss[_k] = _v


def carregar_exemplo_viga(ex):
    ss.viga_b = float(ex['secao']['b'])
    ss.viga_h = float(ex['secao']['h'])
    ss.viga_fck = int(ex['secao']['fck'])
    ss.viga_cob = float(ex['secao']['cob'])
    ss.lista_vaos = [dict(t) for t in ex['tramos']]
    ss.res = None
    ss.edit_index = None
    ss.q_sugerido = None
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


# ------------------------------------------------------------ exemplos
with st.expander("📚 Exemplos prontos — carregue um caso do cotidiano"):
    st.caption("Toque em **Carregar** para preencher a viga com um exemplo "
               "e ver como o programa funciona. Depois é só calcular.")
    for _i, _ex in enumerate(EXEMPLOS_VIGA):
        _ce, _cb = st.columns([4, 1.2])
        _ce.markdown(f"**{_ex['nome']}**  \n{_ex['descr']}")
        if _cb.button("Carregar", key=f"exv_{_i}", width="stretch"):
            carregar_exemplo_viga(_ex)
            st.rerun()

# ------------------------------------------------------------ seção 1
sec(1, "Inserir seção, concreto e aço", destaque=True)
c1, c2 = st.columns(2)
b = c1.number_input(
    "Base bw [cm]", min_value=10.0, max_value=100.0, step=1.0,
    format="%.0f", key="viga_b",
    help="Largura (base) da viga. Mínimo 12 cm pela NBR 6118. "
         "Ex.: 15 cm é comum em residências.")
h = c2.number_input(
    "Altura h [cm]", min_value=15.0, max_value=200.0, step=1.0,
    format="%.0f", key="viga_h",
    help="Altura total da viga. Regra prática: da ordem de L/12 a L/10 do "
         "maior vão. Ex.: vão de 5 m → h ≈ 40 a 50 cm.")
c3, c4 = st.columns(2)
fck = c3.number_input(
    "Concreto fck [MPa]", min_value=20, max_value=50, step=5, key="viga_fck",
    help="Resistência do concreto aos 28 dias. Em residências use 25 ou "
         "30 MPa. O programa cobre de 20 a 50 MPa.")
cob = c4.number_input(
    "Cobrimento c [cm]", min_value=2.0, max_value=5.0, step=0.5,
    format="%.1f", key="viga_cob",
    help="Distância do aço até a face do concreto (proteção). CAA I "
         "(interno seco) 2,5 · CAA II (urbano) 3,0 · CAA III "
         "(marinho/industrial) 4,0 cm — Tabela 7.2 da NBR 6118.")
g_pp_disp = 25.0 * b * h / 1e4 * fu
pp = st.checkbox("Incluir peso próprio automaticamente "
                 f"(g = {g_pp_disp:.{_cf(2)}f} {un_fm})", value=True)
st.caption("Aço: CA-50A (longitudinal e estribos) · γf=1,4 · γc=1,4 · γs=1,15")

dados_g = {'b': b, 'h': h, 'fck': fck, 'cob': cob, 'peso_proprio': pp}

# ------------------------------------------------------------ seção 2
sec(2, "Inserir os tramos da viga", destaque=True)

nomes = nomes_tramos(ss.lista_vaos)
editando = ss.edit_index is not None

if editando and ss.edit_index >= len(ss.lista_vaos):
    ss.edit_index = None          # proteção extra contra índice órfão
    editando = False

if not editando:
    q_novo = assistente_carga(fu, un_fm)
    if q_novo is not None:
        ss.q_sugerido = q_novo
        st.rerun()
    if ss.get('q_sugerido'):
        st.caption(f"💡 Carga sugerida pelo assistente: "
                   f"**{ss.q_sugerido * fu:.{_cf(1)}f} {un_fm}** "
                   "(já preenchida no campo abaixo; pode alterar).")
    st.caption("💡 Toque em cada campo e digite — os campos de carga "
               "começam vazios (comprimento, carga, posição).")
    with st.form("form_tramo", clear_on_submit=False):
        tipo = st.selectbox("Tipo do tramo",
                            ["Normal", "Balanço Esquerdo", "Balanço Direito"])
        cL, cQ = st.columns(2)
        L_in = cL.number_input(
            "Comprimento L [m]", min_value=0.1, max_value=30.0, value=None,
            step=0.1, format="%.2f", placeholder="ex: 4,50",
            help="Vão: distância entre os eixos dos apoios (ou o "
                 "comprimento do balanço), em metros.")
        q_ini = (ss.q_sugerido * fu) if ss.get('q_sugerido') else None
        q_disp = cQ.number_input(
            f"Carga distribuída q [{un_fm}]", min_value=0.0,
            max_value=500.0 * fu, value=q_ini, step=0.5 * fu,
            format=f"%.{_cf(2)}f",
            placeholder=("ex: 1500" if fu > 1 else "ex: 15"),
            help="Carga por metro ao longo do tramo (laje + parede + "
                 "revestimento + sobrecarga, somados). Use o assistente "
                 "'🧮 Montar a carga' acima se tiver dúvida. O peso próprio "
                 "da viga já é somado automaticamente.")
        cP, cA = st.columns(2)
        P_disp = cP.number_input(
            f"Carga concentrada P [{un_f}]", min_value=0.0,
            max_value=2000.0 * fu, value=None, step=1.0 * fu,
            format=f"%.{_cf(2)}f", placeholder="0 se não houver",
            help="Carga pontual (ex.: uma viga que se apoia sobre esta). "
                 "Deixe vazio se não houver.")
        a_in = cA.number_input(
            "Posição de P: a [m] (da esquerda do tramo)", min_value=0.0,
            max_value=30.0, value=None, step=0.05, format="%.2f",
            placeholder="0 se não houver",
            help="Distância da carga P até o apoio da ESQUERDA do tramo, em "
                 "metros. Só preencha se houver P.")
        inserir = st.form_submit_button("➕ INSERIR TRAMO", width="stretch")
    if inserir:
        q_in = (q_disp or 0.0) / fu          # -> kN (interno)
        P_in = (P_disp or 0.0) / fu
        a_val = a_in if a_in is not None else 0.0
        erros_t = []
        if L_in is None or L_in <= 0:
            erros_t.append("Informe o comprimento L do tramo "
                           "(maior que zero).")
        if P_in > 0 and a_in is None:
            erros_t.append("Informe a posição a (m, a partir da esquerda do "
                           "tramo) da carga concentrada P.")
        elif L_in and P_in > 0 and not (0 <= a_val <= L_in):
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
        linha = (f"<b>{nomes[i]}</b> · L = {t['L']:.2f} m · "
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
    try:
        ss.res = mv.calcular_viga(dados_g, [
            {'nome': n, **t} for n, t in zip(nomes_tramos(ss.lista_vaos),
                                             ss.lista_vaos)])
    except Exception as _e:
        ss.res = {'erros': [f"Não foi possível calcular: {_e}. "
                            "Confira os dados (comprimentos maiores que "
                            "zero, cargas e posições válidas)."]}
    ss.res_fp = fp_atual
elif ss.res is not None and ss.res_fp != fp_atual:
    ss.res = None
    st.info("Os dados mudaram — toque em **CALCULAR VIGA** para atualizar "
            "os resultados.")


# =================================================================== figuras
from desenhos_viga import (  # desenhos extraídos (mesmas figuras da tela)
    _posicoes_apoios, _larg_fig, fig_esquema, fig_diagramas,
    fig_detalhamento, _dados_corte, _desenha_fileiras, fig_corte_estribo,
    _barra_ferro, _cota, fig_corte_longitudinal, zonas_furos, fig_furos)



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
              f"MPa | Aço CA-50A | c = {d['cob']:.1f} cm | d = {d['d']:.1f} cm")
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
    ln.append("ESTRIBOS (2 ramos, CA-50A):")
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
    fl = mv.verificar_flecha(res)
    ln.append("")
    ln.append("FLECHA (ELS-DEF, NBR 6118 17.3.2 — carga total quase-perm.):")
    ln.append(f"  Ecs = {fl['Ecs_MPa']:.0f} MPa | Mr = {fl['Mr_kNm']:.1f} kN·m "
              f"| αf = {fl['alfa_f']:.2f}")
    for it in (fl['vaos'] + fl['balancos']):
        situ = "OK" if it['ok'] else "EXCEDE"
        s = (f"  {it['nome']}: {it['estadio']} | imediata "
             f"{it['flecha_imediata_mm']:.1f} mm | total "
             f"{it['flecha_total_mm']:.1f} mm | limite "
             f"{it['limite_mm']:.1f} mm -> {situ}")
        if not it['ok']:
            s += (f" | contra-flecha {it['contra_flecha_mm']:.0f} mm "
                  f"(resíduo {it['residual_mm']:.1f} mm)")
        ln.append(s)

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
        fl_els = mv.verificar_flecha(res) if res.get('quantitativo') else None

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

        # ---- veredito / resumo no topo
        if not res['falha_flexao'] and not res['falha_biela'] and fl_els:
            _q = res['quantitativo']
            _itfl = fl_els['vaos'] + fl_els['balancos']
            _fmax = max((it['flecha_total_mm'] for it in _itfl), default=0.0)
            if all(it['ok'] for it in _itfl):
                st.success("✅ **VIGA APROVADA** — flexão, cortante e flecha "
                           "dentro dos limites da NBR 6118.")
            else:
                st.warning("⚠️ **Aprovada no ELU (flexão e cortante)**, mas a "
                           "**flecha** passou do limite em algum vão — veja a "
                           "seção *Flecha* abaixo (contra-flecha ou aumentar "
                           "a altura h).")
            _r1, _r2, _r3 = st.columns(3)
            _r1.metric("Aço total", f"{_q['peso_total']:.0f} kg")
            _r2.metric("Cortante máx",
                       f"{est['V_max'] * fu:.{_cf(1)}f} {un_f}")
            _r3.metric("Flecha máx", f"{_fmax:.1f} mm")

        # ---- avisos de escopo
        with st.expander("⚠️ Avisos e hipóteses de cálculo", expanded=False):
            for a in res['avisos']:
                st.markdown(f"- {a}")

        # ---- esquema estrutural
        sec(3, "Esquema estrutural e reações")
        png_esq = mostrar_figura(fig_esquema(res, fu, un_f))

        # ---- diagramas
        sec(4, "Diagramas de esforços")
        png_diag = mostrar_figura(fig_diagramas(res, fu, un_f))
        st.caption("🔎 Para ampliar: use o zoom de pinça; se não funcionar no "
                   "seu celular, deslize a figura para o lado ou baixe a "
                   "imagem em **Exportar** e abra na galeria (lá o zoom "
                   "sempre funciona).")

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
            st.info("🧵 **Armadura de pele (h > 60 cm — NBR 6118 "
                    f"17.3.5.2.3):** {res['pele']['texto']}. Já desenhada no "
                    "corte transversal e incluída no quantitativo e na "
                    "compra de aço.")

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
            png = mostrar_figura(fig_detalhamento(res))

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
            png_corte = mostrar_figura(
                fig_corte_estribo(res, tipo_c, idx_c, titulo_c))

            st.markdown("**📐 Corte longitudinal — detalhamento da armação "
                        "(comprimentos, marcas e estribos):**")
            png_long = mostrar_figura(fig_corte_longitudinal(res))

            # ---- zona segura para furos
            sec(8, "Onde furar a viga (passagem de tubulação)")
            st.caption("Verde = pode furar · Vermelho = evitar. A **linha "
                       "neutra** tem tensão de flexão nula, mas o cortante é "
                       "máximo nela — por isso o furo deve ficar no **terço "
                       "médio** da altura e **longe dos apoios (≥ 2h)**.")
            png_furos = mostrar_figura(fig_furos(res))
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

            # ---- flecha (ELS)
            sec(9, "Flecha (ELS)")
            fl = fl_els
            itens = fl['vaos'] + fl['balancos']
            tabela([{
                "Local": it['nome'],
                "Estádio": it['estadio'],
                "Imediata": f"{it['flecha_imediata_mm']:.1f} mm",
                "Total (c/ fluência)": f"{it['flecha_total_mm']:.1f} mm",
                "Limite L/250": f"{it['limite_mm']:.1f} mm",
                "Situação": "✅ OK" if it['ok'] else "❌ Excede"}
                for it in itens])
            st.caption("Flecha total = imediata × (1 + αf, αf=1,32 fluência). "
                       "Carga total tratada como quase-permanente "
                       "(conservador). Limite L/250 (visual, Tab. 13.3); "
                       "balanço usa 2×L. Contra-flecha ≤ L/350.")
            _alv = [it for it in itens if not it['ok_alv']]
            if _alv:
                st.info("🧱 **Se houver parede de alvenaria sobre/sob a "
                        "viga**, o limite é mais rígido: **L/500 (≤ 10 mm)** "
                        "para não trincar (Tab. 13.3). Passam desse limite: "
                        + "; ".join(f"{it['nome']} "
                          f"({it['flecha_total_mm']:.1f} > "
                          f"{it['limite_alv_mm']:.1f} mm)" for it in _alv)
                        + ". Nesse caso aumente a altura h — a contra-flecha "
                        "não evita a fissura da parede.")
            else:
                st.caption("🧱 Todas as flechas também atendem o limite de "
                           "alvenaria L/500 (≤ 10 mm) para paredes.")
            for it in itens:
                if it['ok']:
                    continue
                cf = it['contra_flecha_mm']
                if it['resolve_com_cf']:
                    st.warning(
                        f"**{it['nome']}:** flecha total {it['flecha_total_mm']:.1f} "
                        f"mm passa do limite {it['limite_mm']:.1f} mm. "
                        f"➡️ Execute **contra-flecha ≈ {cf:.0f} mm** "
                        f"(arredonde p/ múltiplo de 5 mm). Resíduo visível "
                        f"{it['residual_mm']:.1f} mm fica dentro do limite. ✅")
                else:
                    st.error(
                        f"**{it['nome']}:** flecha total {it['flecha_total_mm']:.1f} "
                        f"mm excede muito o limite {it['limite_mm']:.1f} mm. A "
                        f"contra-flecha máxima (L/350 = {cf:.0f} mm) **não "
                        f"resolve** (resíduo {it['residual_mm']:.1f} mm). "
                        f"➡️ **Aumente a altura h** da viga.")
            if all(it['ok'] for it in itens):
                st.success("✅ Todas as flechas estão dentro do limite "
                           "L/250 — sem necessidade de contra-flecha.")

            sec(10, "Quantitativo de aço")
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
            sec(11, "Exportar")

            # pacote ZIP com tudo (memorial + todas as figuras)
            nome_base = f"Viga_{b:.0f}x{h:.0f}"
            zbuf = io.BytesIO()
            with zipfile.ZipFile(zbuf, "w", zipfile.ZIP_DEFLATED) as z:
                z.writestr(f"{nome_base}_memorial.txt",
                           gerar_memorial(res, nomes_l))
                z.writestr("1_esquema_reacoes.png", png_esq)
                z.writestr("2_diagramas_M_V.png", png_diag)
                z.writestr("3_detalhamento.png", png)
                z.writestr("4_corte_longitudinal.png", png_long)
                z.writestr("5_corte_transversal.png", png_corte)
                z.writestr("6_zona_furos.png", png_furos)
            st.download_button(
                "📦 BAIXAR TUDO (.zip) — memorial + todos os desenhos",
                zbuf.getvalue(), file_name=f"{nome_base}_completo.zip",
                mime="application/zip", type="primary", width="stretch")
            st.caption("Ou baixe um de cada vez para mandar ao cliente/obra "
                       "só o que precisa (abra as imagens na galeria p/ zoom):")

            ce1, ce2 = st.columns(2)
            ce1.download_button(
                "📄 Memorial (.txt)",
                gerar_memorial(res, nomes_l).encode('utf-8'),
                file_name=f"{nome_base}_memorial.txt",
                mime="text/plain", width="stretch")
            ce2.download_button(
                "🖼️ Esquema e reações", png_esq,
                file_name=f"{nome_base}_esquema.png",
                mime="image/png", width="stretch")
            ce3, ce4 = st.columns(2)
            ce3.download_button(
                "🖼️ Diagramas M e V", png_diag,
                file_name=f"{nome_base}_diagramas.png",
                mime="image/png", width="stretch")
            ce4.download_button(
                "🖼️ Detalhamento", png,
                file_name=f"{nome_base}_detalhamento.png",
                mime="image/png", width="stretch")
            ce5, ce6 = st.columns(2)
            ce5.download_button(
                "🖼️ Corte longitudinal", png_long,
                file_name=f"{nome_base}_corte_longitudinal.png",
                mime="image/png", width="stretch")
            ce6.download_button(
                "🖼️ Corte transversal", png_corte,
                file_name=f"{nome_base}_corte_{titulo_c}.png",
                mime="image/png", width="stretch")
            st.download_button(
                "🖼️ Zona de furos", png_furos,
                file_name=f"{nome_base}_furos.png",
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
