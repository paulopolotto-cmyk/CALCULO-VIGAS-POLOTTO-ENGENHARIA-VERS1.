# -*- coding: utf-8 -*-
"""
Página PILARES — Polotto Engenharia (motor de cálculo em motor_pilar.py).
NBR 6118: esbeltez, M1d,min, 2ª ordem (pilar-padrão) e flexo-compressão.
"""
import io
import json

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

import motor_pilar as mp
from ui_comum import (NAVY, AMBAR, CINZA_TXT, CONCRETO,
                      aplicar_estilo, header, sec, seletor_unidade, tabela,
                      seletor_pagina)

aplicar_estilo()
header("Cálculo de Pilares",
       "Concreto armado · NBR 6118 · esbeltez + 2ª ordem (pilar-padrão) "
       "· flexo-compressão")

seletor_pagina("pilar")

# unidade de força (kN ou kgf) — cálculo interno sempre em kN
fu, un_f, un_fm = seletor_unidade()
_cfp = 0 if fu > 1 else 1

ss = st.session_state
if 'res_pilar' not in ss:
    ss.res_pilar = None
if 'res_pilar_fp' not in ss:
    ss.res_pilar_fp = None

# ------------------------------------------------------------ entrada
sec(1, "Inserir os dados do pilar", destaque=True)
c1, c2 = st.columns(2)
b = c1.number_input("Base b [cm] (menor dimensão)", min_value=14.0,
                    max_value=120.0, value=20.0, step=1.0, format="%.0f")
h = c2.number_input("Altura h [cm] (maior dimensão)", min_value=14.0,
                    max_value=300.0, value=30.0, step=1.0, format="%.0f")
c3, c4 = st.columns(2)
l0 = c3.number_input("Altura livre l0 [m]", min_value=0.5, max_value=10.0,
                     value=2.8, step=0.1, format="%.2f",
                     help="Adotado le = l0. Se a vinculação real levar a le "
                          "maior, informe aqui o le.")
fck = c4.number_input("Concreto fck [MPa]", min_value=20, max_value=50,
                      value=25, step=5)
c5, c6 = st.columns(2)
caa = c5.selectbox("Classe de agressividade (CAA)",
                   ["I", "II", "III", "IV"], index=0,
                   help="Define o cobrimento nominal: I=2,5 · II=3,0 · "
                        "III=4,0 · IV=5,0 cm (Tabela 7.2). Veja abaixo qual "
                        "escolher.")
Nk_disp = c6.number_input(f"Força normal CARACTERÍSTICA Nk [{un_f}]",
                          min_value=1.0, max_value=20000.0 * fu,
                          value=None, step=10.0 * fu, format="%.0f",
                          placeholder="digite a carga",
                          help="O programa aplica γf = 1,4 e γn "
                               "automaticamente. NÃO digite o valor já "
                               "majorado.")
Nk = (Nk_disp or 0.0) / fu          # -> kN (interno)
st.caption("Aço CA-50 · γf=1,4 · γc=1,4 · γs=1,15 · "
           "pilar interno de estrutura contraventada")

with st.expander("ℹ️ Classe de agressividade (CAA) — qual escolher?"):
    st.markdown(
        "A CAA define o **cobrimento** do aço conforme o ambiente "
        "(NBR 6118, Tabelas 6.1 e 7.2). Escolha pelo local da obra:\n\n"
        "- **I — Fraca** (cobrimento 2,5 cm): rural ou interno seco. "
        "Ambiente protegido, baixa umidade. *Ex.: interior de residências.*\n"
        "- **II — Moderada** (3,0 cm): **urbana** — o caso mais comum em "
        "cidade. *Ex.: a maioria das obras residenciais urbanas.*\n"
        "- **III — Forte** (4,0 cm): **marinha** (orla) ou **industrial**. "
        "Perto do mar ou de indústria; risco grande de corrosão.\n"
        "- **IV — Muito forte** (5,0 cm): respingos de maré ou ambiente "
        "quimicamente agressivo. Risco elevado.\n\n"
        "👉 Na dúvida em obra **urbana**, use **II**. Em local seco e "
        "protegido, **I**. Perto do **mar/indústria**, **III** ou **IV**.")

dados = {'b': b, 'h': h, 'l0': l0, 'fck': fck, 'Nk': Nk, 'caa': caa}
fp = json.dumps(dados, sort_keys=True)

calcular = st.button("⚡ CALCULAR PILAR", type="primary", width="stretch")
if calcular:
    ss.res_pilar = mp.calcular_pilar(dados)
    ss.res_pilar_fp = fp
elif ss.res_pilar is not None and ss.res_pilar_fp != fp:
    ss.res_pilar = None
    st.info("Os dados mudaram — toque em **CALCULAR PILAR** para atualizar.")


# ------------------------------------------------------------ desenho
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


def gerar_memorial(res, opt):
    d = res['dados']
    ln = []
    ln.append("=" * 62)
    ln.append("MEMORIAL DE CÁLCULO — PILAR (NBR 6118)")
    ln.append("Polotto Engenharia")
    ln.append("=" * 62)
    ln.append(f"Seção: {d['b']:.0f} x {d['h']:.0f} cm | fck = {d['fck']:.0f} "
              f"MPa | CAA {d['caa']} (c = {d['cob']:.1f} cm)")
    ln.append(f"l0 = {d['l0']:.2f} m | Nk = {d['Nk'] * fu:.0f} {un_f} | "
              f"γn = {res['gamma_n']:.2f} | Nd = {res['Nd'] * fu:.0f} "
              f"{un_f} | ν = {res['ni']:.3f}")
    ln.append("")
    ln.append("ESBELTEZ E 2ª ORDEM (por direção):")
    for nome, dd in res['direcoes'].items():
        so = "SIM" if dd['segunda_ordem'] else "não"
        ln.append(f"  Direção {nome} (h_i={dd['h_i']:.0f} cm): "
                  f"λ = {dd['lambda']:.1f} | λ1 = {dd['lambda1']:.1f} | "
                  f"2ª ordem: {so} | e2 = {dd['e2']:.2f} cm | "
                  f"Md,tot = {dd['Md_tot'] / 100 * fu:.{_cfp}f} {un_f}·m")
    ln.append("")
    ln.append(f"ARMADURA ADOTADA: {opt['texto']} "
              f"(As = {opt['As_ef']:.2f} cm² | mín = {res['As_min']:.2f} | "
              f"máx = {res['As_max']:.2f})")
    ln.append(f"  Folga de capacidade: direção x = {opt['folga_x']:.2f} | "
              f"direção y = {opt['folga_y']:.2f}")
    ln.append(f"  Corte por barra: {opt['comp_barra']:.2f} m")
    ln.append(f"ESTRIBOS: ø{opt['phi_t']:.1f} mm c/{opt['s_est']:.0f} cm — "
              f"{opt['n_est']} un x {opt['comp_est']:.2f} m")
    ln.append(f"PESO DE AÇO: longitudinal {opt['peso_long']:.2f} kg + "
              f"estribos {opt['peso_est']:.2f} kg = "
              f"{opt['peso_total']:.2f} kg")
    ln.append("")
    ln.append("AVISOS / HIPÓTESES:")
    for a in res['avisos']:
        ln.append(f"  - {a}")
    ln.append("")
    ln.append("Documento gerado automaticamente — conferir por "
              "profissional habilitado.")
    return "\n".join(ln)


# ------------------------------------------------------------ resultados
if ss.res_pilar is not None:
    res = ss.res_pilar
    st.write("---")
    if 'erros' in res:
        sec("!", "Corrija a entrada de dados")
        for e in res['erros']:
            st.error(e)
    else:
        sec(2, "Esforços e esbeltez")
        m1, m2, m3 = st.columns(3)
        m1.metric("Nd de cálculo", f"{res['Nd'] * fu:.0f} {un_f}",
                  help=f"Nk × γf(1,4) × γn({res['gamma_n']:.2f})")
        m2.metric("λ direção x", f"{res['direcoes']['x']['lambda']:.0f}")
        m3.metric("λ direção y", f"{res['direcoes']['y']['lambda']:.0f}")
        rows = []
        for nome, dd in res['direcoes'].items():
            rows.append({
                "Direção": f"{nome} (h={dd['h_i']:.0f} cm)",
                "λ": f"{dd['lambda']:.1f}",
                "λ1": f"{dd['lambda1']:.1f}",
                "2ª ordem": "SIM" if dd['segunda_ordem'] else "não",
                "e2 [cm]": f"{dd['e2']:.2f}",
                f"Md,tot [{un_f}·m]":
                    f"{dd['Md_tot'] / 100 * fu:.{_cfp}f}"})
        tabela(rows)

        with st.expander("⚠️ Avisos e hipóteses de cálculo"):
            for a in res['avisos']:
                st.markdown(f"- {a}")

        if not res['opcoes']:
            st.error("🚫 **SEÇÃO INSUFICIENTE** para Nd = "
                     f"{res['Nd'] * fu:.0f} {un_f} com os momentos de 2ª "
                     "ordem da norma — nenhum arranjo de armadura atende "
                     "dentro do limite de 4% de aço. **Aumente b, h ou o "
                     "fck.**")
        else:
            sec(3, "Escolha do arranjo de armadura")
            economica = res['opcoes'][0]
            st.success(f"💡 Opção mais econômica: **{economica['texto']}** "
                       f"({economica['peso_total']:.1f} kg de aço)")
            textos = [f"{o['texto']} — {o['peso_total']:.1f} kg "
                      f"(As = {o['As_ef']:.2f} cm²)" for o in res['opcoes']]
            idx = st.selectbox("Arranjos aprovados (norma + capacidade):",
                               range(len(textos)),
                               format_func=lambda i: textos[i])
            opt = res['opcoes'][idx]

            cg, ct = st.columns([5, 5])
            with cg:
                f = fig_secao(res, opt)
                st.pyplot(f, width="stretch")
                png = io.BytesIO()
                f.savefig(png, format='png', dpi=200, bbox_inches='tight')
                plt.close(f)
            with ct:
                st.metric("Armadura", opt['texto'])
                st.metric("As efetivo",
                          f"{opt['As_ef']:.2f} cm²",
                          help=f"mínimo {res['As_min']:.2f} · "
                               f"máximo {res['As_max']:.2f}")
                st.metric("Folga de capacidade",
                          f"{min(opt['folga_x'], opt['folga_y']):.2f}×",
                          help="M_Rd / Md,tot na direção crítica")

            sec(4, "Ferragem e pesos")
            tabela([
                {"Elemento": "Longitudinal", "Bitola": f"ø{opt['phi']:.1f}",
                 "Qtd": f"{opt['n']} un",
                 "Comp. [m]": f"{opt['comp_barra']:.2f}",
                 "Peso [kg]": f"{opt['peso_long']:.2f}"},
                {"Elemento": f"Estribos c/{opt['s_est']:.0f} cm",
                 "Bitola": f"ø{opt['phi_t']:.1f}",
                 "Qtd": f"{opt['n_est']} un",
                 "Comp. [m]": f"{opt['comp_est']:.2f}",
                 "Peso [kg]": f"{opt['peso_est']:.2f}"}])
            st.metric("Peso total de aço", f"{opt['peso_total']:.2f} kg")

            sec(5, "Exportar")
            ce1, ce2 = st.columns(2)
            ce1.download_button(
                "📄 Memorial (.txt)",
                gerar_memorial(res, opt).encode('utf-8'),
                file_name=f"Pilar_{b:.0f}x{h:.0f}_memorial.txt",
                mime="text/plain", width="stretch")
            ce2.download_button(
                "🖼️ Seção (.png)", png.getvalue(),
                file_name=f"Pilar_{b:.0f}x{h:.0f}_secao.png",
                mime="image/png", width="stretch")

st.caption("Ferramenta de apoio — os resultados devem ser conferidos por "
           "profissional habilitado. Flexão oblíqua e momentos aplicados "
           "não considerados.")
