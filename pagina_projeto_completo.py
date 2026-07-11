# -*- coding: utf-8 -*-
"""Página PROJETO COMPLETO — Polotto Engenharia.

Fluxo em 3 telas encadeadas:
  1) LANÇAR   — editor visual (desenha pilares/vigas sobre a planta) → ENVIAR
  2) CONFERIR — mostra a planta NUMERADA (VH/VV/P) para o usuário conferir com
                o desenho; botões "Editar" (volta) ou "Enviar para o cálculo".
  3) CALCULAR — só aqui roda o detalhamento (tabelas, aço, PDFs completo/reduzido).

O cálculo só roda DEPOIS que o usuário confere a planta e confirma. Módulo NOVO
e independente: NÃO altera as telas aprovadas (Vigas/Pilares/Lajes/Prévios).
"""
import json

import streamlit as st
import streamlit.components.v1 as components

from ui_comum import aplicar_estilo, header, sec, seletor_pagina, tabela
import editor_lancamento as el
import calc_projeto as cp
import relatorio_pdf as rpdf

aplicar_estilo()
header("Projeto Completo — Lançar → Conferir → Calcular",
       "Desenhe, confira a planta com o seu projeto e mande para o cálculo")
seletor_pagina("completo")

ss = st.session_state
ss.setdefault("pc_vista", "lancar")
ss.setdefault("pc_planta", None)     # planta extraída do PDF (fundo do editor)
ss.setdefault("pc_data", None)       # estrutura JSON (lançamento salvo)
ss.setdefault("pc_proj", "projeto")
ss.setdefault("pc_larg", 15.0)


def _vista(v):
    ss.pc_vista = v
    st.rerun()


def _stepper():
    """Barra de etapas CLICÁVEL — clique em '1 · Lançar' para voltar ao editor."""
    atual = ss.pc_vista
    tem_dados = ss.get("pc_data") is not None
    cols = st.columns(3)
    for col, (v, txt) in zip(cols, [("lancar", "1 · Lançar"),
                                    ("conferir", "2 · Conferir"),
                                    ("calcular", "3 · Calcular")]):
        with col:
            rotulo = ("🔵 " if v == atual else "") + txt
            if st.button(rotulo, key=f"step_{v}", width="stretch",
                         type="primary" if v == atual else "secondary",
                         disabled=(v != "lancar" and not tem_dados)):
                if v != atual:
                    _vista(v)
    st.caption("↑ Clique em **1 · Lançar** para voltar ao editor e mexer nas "
               "vigas/pilares.")


_stepper()

# ============================================================ 1) LANÇAR
if ss.pc_vista == "lancar":
    sec(1, "Suba a planta (PDF) e desenhe os pilares e vigas")
    up = st.file_uploader("Planta baixa em PDF (do CAD) — fundo para desenhar",
                          type=["pdf"], key="pc_pdf")
    if up is not None:
        with st.spinner("Lendo a planta…"):
            try:
                ss.pc_planta = el.extrair_planta(up.getvalue())
                ss.pc_proj = up.name.rsplit(".", 1)[0]
            except Exception as e:
                st.error(f"Não consegui ler a planta: {e}")

    if ss.pc_planta is not None:
        d = ss.pc_planta
        st.success(f"Planta lida ({len(d['VX'])} eixos verticais, "
                   f"{len(d['HY'])} horizontais para o snap).")
        ss.pc_larg = st.number_input(
            "Largura total da construção (m) — só para acertar a escala",
            min_value=1.0, max_value=300.0, value=float(ss.pc_larg), step=0.5)
        S = el.estimar_escala(d, ss.pc_larg)
        st.caption(f"Escala: 1 m ≈ {S} pontos. Desenhe os **pilares (+Pilar)** e "
                   "as **vigas (+Viga)**. Ao terminar, clique **ENVIAR** — ele "
                   "baixa o `estrutura_*.json`.")
        lskey = "lanc_" + "".join(c for c in ss.pc_proj if c.isalnum())[:20]
        html = el.build_editor(d, S, proj=ss.pc_proj, lskey=lskey or "lanc_proj")
        components.html(html, height=820, scrolling=True)
    elif ss.pc_data is not None:
        st.success(f"✏️ Editando o seu projeto — **{len(ss.pc_data.get('pilares', []))} "
                   f"pilares** e **{len(ss.pc_data.get('vigas', []))} vigas** já "
                   "carregados. Fundo em branco; para ver a planta da casa atrás, "
                   "suba o PDF acima.")
        html = el.build_editor_from_data(ss.pc_data)
        components.html(html, height=820, scrolling=True)
        st.caption("Complete/ajuste as vigas e pilares e clique **ENVIAR** (baixa o "
                   "arquivo). Depois suba o arquivo **abaixo** para conferir de novo.")
    else:
        st.info("Para desenhar do zero, suba o **PDF** acima. Se já tem o arquivo do "
                "projeto salvo, suba ele **abaixo** — dá para editar mesmo sem o PDF.")

    sec(2, "Salvou? Suba o arquivo para CONFERIR a planta")
    st.caption("No editor, clique **ENVIAR** (baixa o `estrutura_*.json`). Depois "
               "solte o arquivo aqui — a próxima tela mostra a planta numerada "
               "para você conferir com o seu desenho.")
    upj = st.file_uploader("Arquivo do editor (estrutura_*.json)",
                           type=["json"], key="pc_json")
    if upj is not None:
        d = None
        try:
            d = json.loads(upj.getvalue().decode("utf-8"))
        except Exception as e:
            st.error(f"Arquivo inválido (não é um JSON): {e}")
        if d is not None and "pilares" not in d:
            st.error("Esse arquivo não é o do lançamento. Use o arquivo baixado "
                     "pelo botão **ENVIAR** do editor (estrutura_*.json).")
            d = None
        if d is not None:
            st.success(f"✅ Arquivo lido: **{len(d.get('pilares', []))} pilares** e "
                       f"**{len(d.get('vigas', []))} trechos de viga**. "
                       "Clique abaixo para ver a planta e conferir.")
            if st.button("👁️ Ver a planta numerada para CONFERIR →",
                         type="primary", width="stretch"):
                ss.pc_data = d
                ss.pc_proj = d.get("projeto") or ss.pc_proj
                for k in ("pdf_completo", "pdf_reduzido", "pc_r"):
                    ss.pop(k, None)
                _vista("conferir")

# ============================================================ 2) CONFERIR
elif ss.pc_vista == "conferir":
    sec(1, "Confira a planta com o seu desenho")
    st.caption("Compare este croqui com a planta que você lançou. **Faltou ou "
               "sobrou** alguma viga ou pilar?")
    planta = rpdf.fig_planta(cp.planta_do_json(ss.pc_data))
    if planta is not None:
        st.pyplot(planta, width="stretch")
        st.caption("Vigas/baldrames em **amarelo** (VH…, VV…) e pilares em "
                   "**vermelho** (P…) — a mesma numeração que vai no detalhamento.")
    else:
        st.warning("Sem coordenadas para desenhar a planta.")

    rr = el.resumo_estrutura(ss.pc_data)
    c1, c2, c3 = st.columns(3)
    c1.metric("Pilares", rr["n_pilares"])
    c2.metric("Vigas (trechos)", rr["n_vigas"])
    c3.metric("Vigas contínuas", rr["n_continuas"])

    st.write("")
    b1, b2 = st.columns(2)
    if b1.button("✏️ Editar (faltou/sobrou algo)", width="stretch"):
        _vista("lancar")
    if b2.button("✅ Está certo — enviar para o cálculo", type="primary",
                 width="stretch"):
        _vista("calcular")

# ============================================================ 3) CALCULAR
else:
    proj = ss.pc_proj
    if st.button("↩️ Voltar para conferir / editar a planta"):
        _vista("conferir")

    if ss.get("pc_r") is None:
        with st.spinner("Rodando o cálculo NBR 6118 de todas as vigas, baldrames "
                        "e pilares…"):
            ss["pc_r"] = cp.calcular_projeto(ss.pc_data)
    r = ss["pc_r"]

    st.info("**Materiais adotados:** concreto **C25** (fck = 25 MPa) · aço "
            "longitudinal **CA-50A** (fyk = 500 MPa) · **estribos CA-50A ou "
            "CA-60A** · γc = 1,4 · γs = 1,15 · γf = 1,4 — NBR 6118.")

    # ---- vigas de cobertura
    sec(1, "Vigas de cobertura (viga contínua NBR 6118)")
    st.caption(f"Laje lançada na direção "
               f"**{'horizontal' if r['principal']=='H' else 'vertical'}** "
               f"(cobertura q ≈ {r['q_cob']} kN/m²). A seção cresce sozinha se o "
               "vão exigir.")
    tabela([{"Viga": v["nome"], "Seção": v["secao"], "Nº vãos": v["nvaos"],
             "Vãos (m)": " + ".join(f"{x:.2f}" for x in v["vaos"]),
             "Carga w (kN/m)": v["w"], "M máx (kN·m)": v["mmax"],
             "Aço (kg)": v["peso"] if v["peso"] else "—"} for v in r["vigas"]])

    # ---- baldrames
    sec(2, "Baldrames (vigas de fundação sob as paredes)")
    st.caption(f"Carga de parede ≈ {r['wall']} kN/m sobre cada linha de baldrame.")
    tabela([{"Baldrame": b["nome"], "Seção": b["secao"], "Nº vãos": b["nvaos"],
             "Vãos (m)": " + ".join(f"{x:.2f}" for x in b["vaos"]),
             "Carga w (kN/m)": b["w"], "M máx (kN·m)": b["mmax"],
             "Aço (kg)": b["peso"] if b["peso"] else "—"} for b in r["baldrames"]])

    # ---- pilares
    sec(3, "Pilares (NBR 6118 — 14×30, seção cresce pela norma)")
    tabela([{"Pilar": p["pilar"], "Seção (cm)": p["secao"],
             "Carga (tf)": p["carga_tf"], "Armadura": p["armadura"],
             "Aço (kg)": p["peso"]} for p in r["pilares"]])

    # ---- fundação
    sec(4, "Cargas na fundação")
    st.metric("Carga total à fundação (cobertura + alvenaria/baldrames)",
              f"{r['fund_tf']} tf")
    st.caption("A carga de cada sapata/estaca é a carga do pilar correspondente na "
               "tabela acima. O dimensionamento das fundações depende do SPT do terreno.")

    # ---- QUANTITATIVO de aço a comprar
    sec(5, "Relação de aço a comprar (por etapa e total)", destaque=True)
    q1, q2, q3, q4 = st.columns(4)
    q1.metric("Vigas", f"{r['aco_vigas']} kg")
    q2.metric("Pilares", f"{r['aco_pilares']} kg")
    q3.metric("Baldrames", f"{r['aco_baldrames']} kg")
    q4.metric("TOTAL", f"{r['aco_total']} kg")
    tabela([
        {"Etapa": "Vigas de cobertura", "Aço CA-50A (kg)": r["aco_vigas"]},
        {"Etapa": "Pilares", "Aço CA-50A (kg)": r["aco_pilares"]},
        {"Etapa": "Baldrames", "Aço CA-50A (kg)": r["aco_baldrames"]},
        {"Etapa": "TOTAL A COMPRAR", "Aço CA-50A (kg)": r["aco_total"]},
    ])
    st.caption("Inclui ~10% de perdas/emendas em vigas e baldrames e ~8% nos pilares.")
    if r["falhas"]:
        st.warning("Verificar manualmente (não passaram nem no maior perfil): "
                   + ", ".join(r["falhas"]))

    # ---- relatório resumido em HTML (rápido)
    sec(6, "Baixar os relatórios")
    html_rel = cp.relatorio_html(r, proj)
    st.download_button("📥 Relatório resumido (HTML — abre no navegador)",
                       data=html_rel.encode("utf-8"),
                       file_name=f"relatorio_{proj}.html", mime="text/html")

    # ---- detalhamento em PDF — dois níveis (sob demanda, ~1 min cada)
    st.markdown("**Detalhamento em PDF de cada viga e cada pilar** — a planta "
                "numerada vai na frente. Escolha o nível (gera sob demanda):")
    n_el = len(r["vigas"]) + len(r["baldrames"]) + len(r["pilares"])
    cpdf1, cpdf2 = st.columns(2)
    with cpdf1:
        st.markdown("**🛠️ Completo** — esquema de cargas, diagramas de momento e "
                    "cortante, cortes de armação e memorial completo.")
        if st.button(f"Gerar COMPLETO ({n_el} elem.)", width="stretch"):
            ss.pop("pdf_completo", None)
            with st.spinner("Desenhando tudo (esquema, diagramas, cortes e "
                            "memorial)…"):
                ss["pdf_completo"] = rpdf.gerar_pdf(r, proj)
            st.success("PDF completo pronto!")
        if ss.get("pdf_completo"):
            st.download_button("📥 Baixar COMPLETO (PDF)",
                               data=ss["pdf_completo"],
                               file_name=f"detalhamento_{proj}.pdf",
                               mime="application/pdf", width="stretch")
    with cpdf2:
        st.markdown("**📄 Reduzido** — só as **armações** (cortes + quantitativo), "
                    "**sem** os diagramas de momento/cortante. PDF bem menor.")
        if st.button(f"Gerar REDUZIDO ({n_el} elem.)", width="stretch"):
            ss.pop("pdf_reduzido", None)
            with st.spinner("Desenhando só as armações…"):
                ss["pdf_reduzido"] = rpdf.gerar_pdf(r, proj, reduzido=True)
            st.success("PDF reduzido pronto!")
        if ss.get("pdf_reduzido"):
            st.download_button("📥 Baixar REDUZIDO (PDF)",
                               data=ss["pdf_reduzido"],
                               file_name=f"detalhamento_reduzido_{proj}.pdf",
                               mime="application/pdf", width="stretch")
