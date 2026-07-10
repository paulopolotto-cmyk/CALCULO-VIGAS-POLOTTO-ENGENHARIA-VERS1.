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

        r = el.resumo_estrutura(data)
        sec(2, "Resumo da estrutura")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Pilares", r["n_pilares"])
        c2.metric("Vigas (trechos)", r["n_vigas"])
        c3.metric("Vigas contínuas", r["n_continuas"])
        c4.metric("Total → fundação", f"{r['total_tf']} tf")

        sec(3, "Vigas contínuas (segmentos alinhados agrupados)")
        if r["linhas"]:
            rows = [{"Viga contínua": f"{'VH' if l['dir']=='H' else 'VV'}{i+1}",
                     "Nº de vãos": l["nvaos"],
                     "Comprimento": f"{l['comp']:.2f} m",
                     "Vãos (m)": " + ".join(f"{v:.2f}" for v in l["vaos"])}
                    for i, l in enumerate(r["linhas"])]
            tabela(rows)
            st.caption(f"Vão máximo entre apoios: **{r['vao_max']:.2f} m**.")
        else:
            st.warning("Nenhuma viga encontrada no arquivo.")

        sec(4, "Relação de cargas dos pilares")
        prows = [{"Pilar": p.get("pilar"),
                  "Carga (tf)": p.get("carga_tf", "-"),
                  "Seção": p.get("secao", "-"),
                  "Forma": p.get("forma", "-")} for p in r["pilares"]]
        tabela(prows)

        st.info("✅ Leitura e **agrupamento das vigas contínuas** prontos. "
                "**Em construção (próxima etapa):** o detalhamento completo — cada viga "
                "contínua rodada no motor NBR 6118 (momentos, cortante, armadura e desenho) "
                "e cada pilar dimensionado — reusando os motores de Vigas e Pilares.")
