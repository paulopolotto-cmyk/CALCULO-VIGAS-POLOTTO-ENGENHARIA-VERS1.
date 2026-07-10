# -*- coding: utf-8 -*-
"""Página PROJETO COMPLETO — Polotto Engenharia.

Fluxo: (1) sobe a planta (PDF do CAD) → desenha pilares/vigas no EDITOR VISUAL
embutido → ENVIAR gera o `estrutura_*.json`; (2) sobe esse JSON aqui → resumo e
(em construção) detalhamento das vigas contínuas e pilares.

Módulo NOVO e independente: NÃO altera Vigas/Pilares/Lajes/Pilares Prévios (a
versão aprovada continua intacta). Usa `editor_lancamento.py`.
"""
import json

import streamlit as st
import streamlit.components.v1 as components

from ui_comum import aplicar_estilo, header, sec, seletor_pagina, tabela
import editor_lancamento as el
import calc_projeto as cp

aplicar_estilo()
header("Projeto Completo — Planta → Lançamento → Cálculo",
       "Suba a planta, desenhe os pilares e vigas, e detalhe a estrutura")
seletor_pagina("completo")

modo = st.radio(
    "O que você quer fazer?",
    ["📐 Inserir planta (PDF) e desenhar a estrutura",
     "📄 Já tenho o arquivo do editor (JSON) — calcular / detalhar"],
    index=0)

# ============================================================ 1) PLANTA → EDITOR
if modo.startswith("📐"):
    sec(1, "Inserir a planta (PDF vetorial do CAD)")
    up = st.file_uploader("Planta baixa em PDF (exportada do AutoCAD)", type=["pdf"])
    if up is not None:
        with st.spinner("Lendo a planta…"):
            try:
                dados = el.extrair_planta(up.getvalue())
            except Exception as e:
                st.error(f"Não consegui ler a planta: {e}")
                st.stop()
        st.success(f"Planta lida! Detectei **{len(dados['VX'])} eixos verticais** e "
                   f"**{len(dados['HY'])} horizontais** de parede (para o snap).")

        sec(2, "Calibrar a escala")
        larg = st.number_input(
            "Largura total aproximada da construção (m) — só para acertar a escala",
            min_value=1.0, max_value=300.0, value=15.0, step=0.5)
        S = el.estimar_escala(dados, larg)
        st.caption(f"Escala adotada: **1 m ≈ {S} pontos**. Se as medidas saírem "
                   "erradas no desenho, ajuste a largura acima.")

        sec(3, "Desenhar pilares e vigas")
        proj = up.name.rsplit(".", 1)[0]
        lskey = "lanc_" + "".join(ch for ch in proj if ch.isalnum())[:20]
        html = el.build_editor(dados, S, proj=proj, lskey=lskey or "lanc_proj")
        components.html(html, height=820, scrolling=True)
        st.info("Desenhe os **pilares (+Pilar)** e as **vigas (+Viga)**. Ao terminar, "
                "clique **ENVIAR** — ele baixa o `estrutura_*.json`. Depois volte aqui em "
                "**📄 Já tenho o arquivo** e suba esse arquivo para o cálculo/detalhamento.")

# ============================================================ 2) JSON → CÁLCULO
else:
    sec(1, "Subir o arquivo do editor")
    up = st.file_uploader("Arquivo gerado pelo botão ENVIAR (estrutura_*.json)",
                          type=["json"])
    if up is not None:
        try:
            data = json.loads(up.getvalue().decode("utf-8"))
        except Exception as e:
            st.error(f"Arquivo inválido (não é um JSON): {e}")
            st.stop()
        if "pilares" not in data:
            st.error("Esse arquivo não tem a estrutura de envio. Use o arquivo baixado "
                     "pelo botão **ENVIAR** do editor (estrutura_*.json).")
            st.stop()

        proj = data.get("projeto") or up.name.rsplit(".", 1)[0]
        rr = el.resumo_estrutura(data)
        sec(2, "Resumo da estrutura")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Pilares", rr["n_pilares"])
        c2.metric("Vigas (trechos)", rr["n_vigas"])
        c3.metric("Vigas contínuas", rr["n_continuas"])
        c4.metric("Total → fundação", f"{rr['total_tf']} tf")

        with st.spinner("Rodando o cálculo NBR 6118 de todas as vigas, baldrames e pilares…"):
            r = cp.calcular_projeto(data)

        # ---- vigas de cobertura
        sec(3, "Vigas de cobertura (viga contínua NBR 6118)")
        st.caption(f"Laje lançada na direção "
                   f"**{'horizontal' if r['principal']=='H' else 'vertical'}** "
                   f"(cobertura q ≈ {r['q_cob']} kN/m²). A seção cresce sozinha se o vão exigir.")
        tabela([{"Viga": v["nome"], "Seção": v["secao"], "Nº vãos": v["nvaos"],
                 "Vãos (m)": " + ".join(f"{x:.2f}" for x in v["vaos"]),
                 "Carga w (kN/m)": v["w"], "M máx (kN·m)": v["mmax"],
                 "Aço (kg)": v["peso"] if v["peso"] else "—"} for v in r["vigas"]])

        # ---- baldrames
        sec(4, "Baldrames (vigas de fundação sob as paredes)")
        st.caption(f"Carga de parede ≈ {r['wall']} kN/m sobre cada linha de baldrame.")
        tabela([{"Baldrame": b["nome"], "Seção": b["secao"], "Nº vãos": b["nvaos"],
                 "Vãos (m)": " + ".join(f"{x:.2f}" for x in b["vaos"]),
                 "Carga w (kN/m)": b["w"], "M máx (kN·m)": b["mmax"],
                 "Aço (kg)": b["peso"] if b["peso"] else "—"} for b in r["baldrames"]])

        # ---- pilares
        sec(5, "Pilares (pré-dimensionamento — casa térrea)")
        tabela([{"Pilar": p["pilar"], "Seção (cm)": p["secao"],
                 "Carga (tf)": p["carga_tf"], "Armadura": p["armadura"],
                 "Aço (kg)": p["peso"]} for p in r["pilares"]])

        # ---- fundação
        sec(6, "Cargas na fundação")
        st.metric("Carga total à fundação (cobertura + alvenaria/baldrames)",
                  f"{r['fund_tf']} tf")
        st.caption("A carga de cada sapata/estaca é a carga do pilar correspondente na "
                   "tabela acima. O dimensionamento das fundações depende do SPT do terreno.")

        # ---- QUANTITATIVO de aço a comprar
        sec(7, "Relação de aço a comprar (por etapa e total)", destaque=True)
        q1, q2, q3, q4 = st.columns(4)
        q1.metric("Vigas", f"{r['aco_vigas']} kg")
        q2.metric("Pilares", f"{r['aco_pilares']} kg")
        q3.metric("Baldrames", f"{r['aco_baldrames']} kg")
        q4.metric("TOTAL", f"{r['aco_total']} kg")
        tabela([
            {"Etapa": "Vigas de cobertura", "Aço CA-50/60 (kg)": r["aco_vigas"]},
            {"Etapa": "Pilares", "Aço CA-50/60 (kg)": r["aco_pilares"]},
            {"Etapa": "Baldrames", "Aço CA-50/60 (kg)": r["aco_baldrames"]},
            {"Etapa": "TOTAL A COMPRAR", "Aço CA-50/60 (kg)": r["aco_total"]},
        ])
        st.caption("Inclui ~10% de perdas/emendas em vigas e baldrames e ~8% nos pilares.")
        if r["falhas"]:
            st.warning("Verificar manualmente (não passaram nem no maior perfil): "
                       + ", ".join(r["falhas"]))

        # ---- relatório HTML para baixar
        html_rel = cp.relatorio_html(r, proj)
        st.download_button("📥 Baixar relatório completo (HTML)",
                           data=html_rel.encode("utf-8"),
                           file_name=f"relatorio_{proj}.html", mime="text/html")
