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
import copy
import json

import streamlit as st
import streamlit.components.v1 as components

import pandas as pd
import matplotlib.pyplot as plt

from ui_comum import aplicar_estilo, header, sec, seletor_pagina, tabela
import editor_lancamento as el
import calc_projeto as cp
import calc_laje_projeto as cl
import fechamento_auto as fa
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
    editando = ss.pc_data is not None and ss.pc_planta is None
    if editando:
        sec(1, "Edite as vigas e os pilares — mexa direto no desenho")
        n_p = len(ss.pc_data.get("pilares", []))
        n_v = len(ss.pc_data.get("vigas", []))
        st.success(f"✏️ **Você está EDITANDO o seu projeto** — **{n_p} pilares** e "
                   f"**{n_v} vigas** já estão no desenho abaixo, prontos para mexer.")
        st.info("**Para editar e voltar a conferir — 3 passos:**  \n"
                "**1)** mexa no **desenho abaixo**: arraste para mover, **+Pilar / "
                "+Viga** para acrescentar, **Excluir** para tirar.  \n"
                "**2)** clique **➤ ENVIAR** (botão verde do editor) — baixa um arquivo "
                "`estrutura_*.json` na pasta **Downloads**.  \n"
                "**3)** suba esse arquivo na caixa **📁 logo abaixo do editor** e "
                "clique **👁️ Ver a planta para CONFERIR**.")
        with st.expander("🖼️ Ver as paredes da casa (PDF) atrás do desenho"):
            up = st.file_uploader("Planta em PDF (do CAD)", type=["pdf"], key="pc_pdf")
            if up is not None:
                with st.spinner("Lendo a planta…"):
                    try:
                        ss.pc_planta = el.extrair_planta(up.getvalue())
                        ss.pc_proj = up.name.rsplit(".", 1)[0]
                        st.rerun()
                    except Exception as e:
                        st.error(f"Não consegui ler a planta: {e}")
        html = el.build_editor_from_data(ss.pc_data)
        components.html(html, height=820, scrolling=True)
    else:
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
        else:
            st.info("Para desenhar do zero, suba o **PDF** acima. Se já tem o arquivo "
                    "do projeto salvo, suba ele **abaixo** — dá para editar mesmo sem "
                    "o PDF.")

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
                d_limpo, _stats = fa.limpar_lancamento(d)   # endireita + tira dup.
                d_limpo = fa.renumerar_pilares(d_limpo)     # P1..Pn profissional
                ss.pc_data = d_limpo
                ss["pc_limpeza"] = _stats
                ss.pc_proj = d.get("projeto") or ss.pc_proj
                for k in ("pdf_completo", "pdf_reduzido", "pc_r", "pc_comodos",
                          "laje_tipos", "laje_vigota", "laje_telhado",
                          "laje_manuais", "laje_excluidas", "laje_mcount",
                          "fecha_novas", "fecha_ok", "fecha_backup"):
                    ss.pop(k, None)
                _vista("conferir")

# ============================================================ 2) CONFERIR
elif ss.pc_vista == "conferir":
    sec(1, "Confira as DUAS plantas — Forma (lajes) e Fundação (baldrames)")
    _lz = ss.get("pc_limpeza")
    if _lz and (_lz["endireitadas"] or _lz["duplicadas"] or _lz["tocos"]):
        st.info(f"🧹 **Limpei o seu lançamento ao carregar:** endireitei "
                f"**{_lz['endireitadas']}** viga(s) tortas (para 90°), removi "
                f"**{_lz['duplicadas']}** viga(s) em duplicidade e **{_lz['tocos']}** "
                "toco(s). As diagonais de verdade foram mantidas. Se sumiu algo que "
                "você queria, é só ir em **Editar**.")
    st.caption("Compare os croquis com a planta que você lançou. **Faltou ou "
               "sobrou** alguma viga, pilar ou laje?")
    _pj = cp.planta_do_json(ss.pc_data)
    st.markdown("**① Planta de FORMA** — vigas de cobertura (**VH/VV**) + as "
                "**lajes** (setas azuis do sentido da vigota).")
    _pf = rpdf.fig_planta(_pj)
    if _pf is not None:
        st.pyplot(_pf, width="stretch")
        plt.close(_pf)
    else:
        st.warning("Sem coordenadas para desenhar a planta.")
    st.markdown("**② Planta de FUNDAÇÃO** — vigas **baldrames (VB)** sob as paredes. "
                "**Não tem laje** e **não precisa de fechamento**.")
    _pfu = rpdf.fig_planta_fundacao(_pj)
    if _pfu is not None:
        st.pyplot(_pfu, width="stretch")
        plt.close(_pfu)
    st.caption("Amarelo = vigas (forma **VH/VV** · fundação **VB**) · vermelho = "
               "pilares (**P**) · azul = **lajes** (sentido da vigota). Mesma "
               "numeração do detalhamento — as **duas** plantas vão para o cálculo.")

    rr = el.resumo_estrutura(ss.pc_data)
    c1, c2, c3 = st.columns(3)
    c1.metric("Pilares", rr["n_pilares"])
    c2.metric("Vigas (trechos)", rr["n_vigas"])
    c3.metric("Vigas contínuas", rr["n_continuas"])

    # ---- fechamento das LAJES (só a planta de FORMA precisa)
    sec(2, "Fechamento das LAJES (vale só para a planta de FORMA)")
    st.caption("A laje precisa de viga em volta para apoiar — isso vale **só na "
               "planta de forma**. A **fundação (baldrames VB) NÃO precisa fechar** "
               "(não recebe laje).")
    _com = cl.detectar_comodos(ss.pc_data.get("vigas", []))
    _ab = cl.regioes_abertas(ss.pc_data.get("vigas", []))
    _grandes = [c for c in _com if c["menor"] > cl.VAO_GRANDE]
    def _dir_laje(c):
        dr = c["vigota"]
        for L in ss.pc_data.get("lajes", []):
            xm, ym = L.get("x_m"), L.get("y_m")
            if xm is not None and ym is not None \
                    and c["x0"] <= xm <= c["x1"] and c["y0"] <= ym <= c["y1"]:
                dr = L.get("dir", dr)
                break
        return "↔ horizontal" if dr == "H" else "↕ vertical"

    if _ab or _grandes:
        _fd = cl.fig_diagnostico(ss.pc_data, _com, _ab)
        st.pyplot(_fd, width="stretch")
        plt.close(_fd)
    if _ab:
        st.warning(f"⚠️ **{len(_ab)} área(s) da FORMA ainda SEM viga fechando** "
                   "(vermelho hachurado) — a laje não teria apoio. Muitas vezes falta "
                   "só **um pedacinho de viga** até o pilar ou a viga vizinha. Use o "
                   "**Fechar automático** logo abaixo (o programa completa), ou feche à "
                   "mão no **Editar**.")
    else:
        st.success(f"✅ **Lajes FECHADAS e prontas para o cálculo!** As **{len(_com)} "
                   "laje(s)** têm viga em volta e a direção definida — pode seguir para "
                   "o cálculo.")
        if _com:
            st.caption("Cada laje fechada, com o sentido da vigota: "
                       + " · ".join(f"**{c['nome']}** {_dir_laje(c)}" for c in _com))
    if _grandes:
        st.warning("⚠️ **Vão grande** (laranja): " + ", ".join(
            f"{c['nome']} = {c['menor']:.1f} m" for c in _grandes)
            + " — a laje está fechada, mas a vigota passa de ~5 m; considere uma "
            "**viga no meio** (divide a laje) ou **vigota protendida**.")

    # ---- fechamento AUTOMÁTICO das vigas (sugestão do programa)
    sec(3, "Fechar os vãos automaticamente (sugestão — você aceita ou não)")
    if ss.get("fecha_backup") is not None:
        st.info("O **fechamento automático foi aplicado**. Se preferir completar à "
                "mão, dá para **desfazer** e voltar ao seu lançamento original:")
        if st.button("↩️ Desfazer o fechamento automático (voltar ao meu lançamento)",
                     width="stretch"):
            ss.pc_data = ss.pop("fecha_backup")
            for k in ("fecha_novas", "fecha_ok", "pc_r", "pc_comodos", "laje_tipos",
                      "laje_vigota", "laje_telhado", "laje_manuais", "laje_excluidas",
                      "laje_mcount", "pdf_completo", "pdf_reduzido"):
                ss.pop(k, None)
            st.toast("Fechamento desfeito — voltei ao seu lançamento.")
            _vista("conferir")
    st.caption("O programa olha o seu projeto e sugere **vigas a 90°** (verde) para "
               "**fechar** as áreas abertas e **dividir** os painéis grandes, e depois "
               "**renumera os pilares**. Você **clica em cada viga verde** para tirá-la "
               "ou pô-la de volta — e ajusta o resto no **Editar**.")
    cfa1, cfa2 = st.columns(2)
    _lv = cfa1.number_input("Vão máx. da vigota (menor lado da laje) — m",
                            min_value=2.0, max_value=12.0,
                            value=float(ss.get("fecha_lv", fa.LIM_VIGOTA)), step=0.5)
    _lm = cfa2.number_input("Pôr viga no meio quando o outro lado passa de — m",
                            min_value=2.0, max_value=12.0,
                            value=float(ss.get("fecha_lm", fa.LIM_MEIO)), step=0.5)
    if st.button("🔧 Sugerir o fechamento das vigas", width="stretch"):
        ss["fecha_lv"], ss["fecha_lm"] = _lv, _lm
        ss["fecha_novas"] = fa.fechar_vaos_auto(ss.pc_data, lim_vigota=_lv,
                                                lim_meio=_lm)
        ss["fecha_ok"] = set(range(len(ss["fecha_novas"])))
        ss["fecha_plot"] = ss.get("fecha_plot", 0) + 1
        st.rerun()

    _novas = ss.get("fecha_novas")
    if _novas is not None:
        if not _novas:
            st.success("👍 Nada a fechar — a estrutura já está fechada e sem vão "
                       "grande demais para a pré-moldada.")
        else:
            ss.setdefault("fecha_ok", set(range(len(_novas))))
            ss.setdefault("fecha_plot", 0)
            _nf = sum(1 for n in _novas if n["motivo"] == "fechar")
            st.caption(f"Sugeri **{len(_novas)} vigas**: **{_nf}** para fechar vão e "
                       f"**{len(_novas) - _nf}** para dividir painel grande. "
                       "🟢 verde = **vai entrar** · cinza pontilhada = recusada. "
                       "👆 **clique na viga** para trocar.")
            _evf = st.plotly_chart(
                fa.fig_fechamento_plotly(ss.pc_data, _novas, ss["fecha_ok"]),
                key=f"fechaplot_{ss['fecha_plot']}", on_select="rerun",
                selection_mode="points", config={"displayModeBar": False})
            try:
                _ptsf = _evf["selection"]["points"]
            except Exception:
                _ptsf = None
            if _ptsf:
                _idx = _ptsf[0].get("customdata")
                if isinstance(_idx, (list, tuple)):
                    _idx = _idx[0] if _idx else None
                if _idx is not None:
                    _idx = int(_idx)
                    if _idx in ss["fecha_ok"]:
                        ss["fecha_ok"].discard(_idx)
                    else:
                        ss["fecha_ok"].add(_idx)
                    ss["fecha_plot"] += 1
                    st.rerun()
            _nok = len(ss["fecha_ok"])
            if st.button(f"✅ Aplicar as {_nok} viga(s) aceita(s) e renumerar os "
                         "pilares", type="primary", width="stretch"):
                ss["fecha_backup"] = copy.deepcopy(ss.pc_data)   # p/ poder desfazer
                _aceitas = [_novas[i] for i in sorted(ss["fecha_ok"])]
                ss.pc_data = fa.aplicar_fechamento(ss.pc_data, _aceitas)
                for k in ("fecha_novas", "fecha_ok", "pc_r", "pc_comodos",
                          "laje_tipos", "laje_vigota", "laje_telhado",
                          "laje_manuais", "laje_excluidas", "laje_mcount",
                          "pdf_completo", "pdf_reduzido", "pc_limpeza"):
                    ss.pop(k, None)
                st.success("Vigas aplicadas e pilares renumerados! Veja a planta "
                           "atualizada no topo.")
                _vista("conferir")

    st.write("")
    st.markdown("#### O que você quer fazer agora?")
    b1, b2 = st.columns(2)
    if b1.button("✏️ Editar (faltou/sobrou algo)", type="primary", width="stretch"):
        st.toast("Abrindo o editor do desenho…")
        _vista("lancar")
    if b2.button("✅ Está certo — enviar para o cálculo", type="primary",
                 width="stretch"):
        _vista("calcular")
    ca, cb = st.columns(2)
    ca.caption("✏️ **Editar** te leva de volta ao **desenho** para mexer nas vigas e "
               "pilares. Lá aparece o **passo a passo** (mexer → ENVIAR → subir o "
               "arquivo de novo).")
    cb.caption("✅ **Está certo** manda para o **cálculo** (tabelas, aço, fundação e "
               "os PDFs). Você ainda pode voltar depois.")

# ============================================================ 3) CALCULAR
else:
    proj = ss.pc_proj
    if st.button("↩️ Voltar para conferir / editar a planta"):
        _vista("conferir")

    # ---- TIPO DE TELHADO — define o peso da cobertura que entra no cálculo ----
    _TELS = {"Fibrocimento (Eternit 6 mm) + madeira": cp.G_TELHADO["fibrocimento"],
             "Cerâmica + madeira": cp.G_TELHADO["ceramica"]}
    ss.setdefault("telhado_tipo", next(iter(_TELS)))
    ss.setdefault("g_telhado", _TELS[ss["telhado_tipo"]])
    st.markdown("#### 🏠 Tipo de telhado (casa térrea — laje de forro)")
    ct1, ct2 = st.columns([2, 1])
    _tt = ct1.selectbox("Cobertura", list(_TELS.keys()),
                        index=(list(_TELS).index(ss["telhado_tipo"])
                               if ss["telhado_tipo"] in _TELS else 0))
    if _tt != ss["telhado_tipo"]:
        ss["telhado_tipo"] = _tt
        ss["g_telhado"] = _TELS[_tt]
        ss.pop("pc_r", None)
        st.rerun()
    _gt = ct2.number_input("Peso do telhado (kN/m²) — pode ajustar", min_value=0.0,
                           max_value=3.0, value=float(ss["g_telhado"]), step=0.05,
                           format="%.2f")
    if abs(_gt - ss["g_telhado"]) > 1e-6:
        ss["g_telhado"] = _gt
        ss.pop("pc_r", None)
        st.rerun()
    _qc = cp.G_PERM + cp.Q_FORRO + ss["g_telhado"]
    st.caption(f"Cobertura = laje-forro+revest. **{cp.G_PERM:.1f}** + sobrecarga de "
               f"forro **{cp.Q_FORRO:.1f}** + telhado **{ss['g_telhado']:.2f}** = "
               f"**{_qc:.2f} kN/m²**. Peso da telha: NBR 6120/catálogo · madeiramento: "
               "estimativa (ajuste ao lado se o seu for diferente). A responsabilidade "
               "do valor é do engenheiro.")

    if ss.get("pc_r") is None:
        with st.spinner("Rodando o cálculo NBR 6118 de todas as vigas, baldrames "
                        "e pilares…"):
            ss["pc_r"] = cp.calcular_projeto(ss.pc_data, g_telhado=ss["g_telhado"])
    r = ss["pc_r"]

    st.info("**Materiais adotados:** concreto **C25** (fck = 25 MPa) · aço "
            "longitudinal **CA-50A** (fyk = 500 MPa) · **estribos CA-50A ou "
            "CA-60A** · γc = 1,4 · γs = 1,15 · γf = 1,4 — NBR 6118.")

    # ---- LAJES pré-moldadas — lançamento (direção, tipo, telhado, add/excluir)
    sec(1, "Lajes pré-moldadas — direção, tipo de uso e telhado")
    if ss.get("pc_comodos") is None:
        ss["pc_comodos"] = cl.detectar_comodos(ss.pc_data.get("vigas", []))
    ss.setdefault("laje_manuais", [])
    ss.setdefault("laje_excluidas", [])
    ss.setdefault("laje_tipos", {})
    ss.setdefault("laje_vigota", {})
    ss.setdefault("laje_telhado", {})
    ss.setdefault("laje_mcount", 0)
    ss.setdefault("laje_flip", 0)
    ss.setdefault("g_telhado", 0.5)

    # sentido lançado no EDITOR (botão +Laje) vira o padrão do cômodo onde a seta caiu
    for _L in ss.pc_data.get("lajes", []):
        _xm, _ym = _L.get("x_m"), _L.get("y_m")
        if _xm is None or _ym is None:
            continue
        for _c in ss["pc_comodos"]:
            if (_c["nome"] not in ss["laje_vigota"]
                    and _c["x0"] <= _xm <= _c["x1"] and _c["y0"] <= _ym <= _c["y1"]):
                ss["laje_vigota"][_c["nome"]] = "V" if _L.get("dir") == "V" else "H"
                break

    comodos = ([c for c in ss["pc_comodos"] if c["nome"] not in ss["laje_excluidas"]]
               + ss["laje_manuais"])

    st.caption(f"Telhado adotado: **{ss['g_telhado']:.2f} kN/m²** "
               f"({ss.get('telhado_tipo', '')}) — definido lá em cima; aqui ele entra "
               "nas lajes marcadas com **Telhado**.")
    st.caption("O programa acha os cômodos fechados por vigas; **complete com "
               "➕ Adicionar laje** o que faltou e **exclua** o que não for laje. A "
               "**direção** já vem no menor vão (troque H/V). Marque **Telhado** onde a "
               "cobertura apoia. O **peso próprio** de cada laje já entra (NBR 6120).")

    if comodos:
        _rows = [{"Laje": c["nome"], "Origem": "à mão" if c.get("manual") else "auto",
                  "Dim (m)": f"{c['Lx']}×{c['Ly']}", "Área": c["area"],
                  "Direção": ss["laje_vigota"].get(c["nome"], c["vigota"]),
                  "Uso (sobrecarga NBR 6120)":
                      ss["laje_tipos"].get(c["nome"], cl.TIPO_PADRAO),
                  "Telhado": bool(ss["laje_telhado"].get(c["nome"], False)),
                  "Excluir": False} for c in comodos]
        _ed = st.data_editor(
            pd.DataFrame(_rows), hide_index=True, width="stretch",
            key=f"laje_ed_{len(comodos)}_{len(ss['laje_excluidas'])}",
            column_config={
                "Laje": st.column_config.TextColumn(disabled=True, width="small"),
                "Origem": st.column_config.TextColumn(disabled=True, width="small"),
                "Dim (m)": st.column_config.TextColumn(disabled=True),
                "Área": st.column_config.NumberColumn(disabled=True, format="%.2f"),
                "Direção": st.column_config.SelectboxColumn(
                    options=["H", "V"], help="H = vigotas na horizontal · V = na vertical"),
                "Uso (sobrecarga NBR 6120)": st.column_config.SelectboxColumn(
                    options=cl.tipos_disponiveis(), width="large"),
                "Telhado": st.column_config.CheckboxColumn(help="Recebe o peso do telhado?"),
                "Excluir": st.column_config.CheckboxColumn(help="Marque para remover"),
            })
        _rem = []
        for _, _r in _ed.iterrows():
            nm = _r["Laje"]
            ss["laje_tipos"][nm] = _r["Uso (sobrecarga NBR 6120)"]
            ss["laje_vigota"][nm] = _r["Direção"]
            ss["laje_telhado"][nm] = bool(_r["Telhado"])
            if _r["Excluir"]:
                _rem.append(nm)
        if _rem:
            ss["laje_excluidas"] = list(set(ss["laje_excluidas"])
                                        | {n for n in _rem if not n.startswith("M")})
            ss["laje_manuais"] = [c for c in ss["laje_manuais"]
                                  if c["nome"] not in _rem]
            st.rerun()
        lajes = cl.calcular_lajes(comodos, ss["laje_tipos"], ss["laje_vigota"],
                                  ss["laje_telhado"], g_telhado=ss["g_telhado"])
        # planta INTERATIVA — clicar numa laje GIRA a direção da vigota
        _ev = st.plotly_chart(cl.fig_lajes_plotly(ss.pc_data, lajes),
                              key=f"lajeplot_{ss['laje_flip']}", on_select="rerun",
                              selection_mode="points",
                              config={"displayModeBar": False})
        try:
            _pts = _ev["selection"]["points"]
        except Exception:
            _pts = None
        if _pts:
            _nm = _pts[0].get("customdata")
            if isinstance(_nm, (list, tuple)):
                _nm = _nm[0] if _nm else None
            if _nm:
                _cur = (ss["laje_vigota"].get(_nm)
                        or next((c["vigota"] for c in comodos if c["nome"] == _nm), "H"))
                ss["laje_vigota"][_nm] = "V" if _cur == "H" else "H"
                ss["laje_flip"] += 1
                st.rerun()
        st.caption("👆 **Clique numa laje** na planta para **girar a direção** da "
                   "vigota (a seta muda na hora). O padrão vem no menor vão. "
                   "🟦 detectada · 🟩 tracejada = lançada à mão.")
        rl = cl.resumo_lajes(lajes)
        st.caption(f"Total: **{rl['area']} m²** de laje · **{rl['vigotas_m']} m** de "
                   f"vigota · aço complementar **{rl['aco_barras']} kg**. "
                   "🟦 detectada · 🟩 tracejada = lançada à mão.")
    else:
        st.info("Nenhuma laje ainda — use **➕ Adicionar laje** abaixo para lançar.")
        lajes = []
        rl = {"aco_barras": 0.0, "vigotas_m": 0.0, "area": 0.0, "falhas": []}

    with st.expander("➕ Adicionar laje (onde a detecção não pegou)"):
        _Xs, _Ys = cl.eixos_grade(ss.pc_data)
        if len(_Xs) < 2 or len(_Ys) < 2:
            st.caption("Não há linhas de viga suficientes para lançar laje à mão.")
        else:
            st.caption("Escolha os limites da laje pelas **linhas de viga** — ela sai "
                       "alinhada à estrutura. (Se faltar viga num lado, o ideal é "
                       "acrescentar a viga no editor; aqui é o jeito rápido.)")
            a1, a2, a3, a4 = st.columns(4)
            _x0 = a1.selectbox("x de (m)", _Xs, index=0, key="nlx0")
            _x1 = a2.selectbox("x até (m)", _Xs, index=min(1, len(_Xs) - 1), key="nlx1")
            _y0 = a3.selectbox("y de (m)", _Ys, index=0, key="nly0")
            _y1 = a4.selectbox("y até (m)", _Ys, index=min(1, len(_Ys) - 1), key="nly1")
            _tp = st.selectbox("Tipo de uso (sobrecarga)", cl.tipos_disponiveis(),
                               key="nltp")
            _tl = st.checkbox("Recebe telhado", key="nltl")
            if st.button("➕ Adicionar esta laje", type="primary"):
                if abs(_x1 - _x0) < 0.3 or abs(_y1 - _y0) < 0.3:
                    st.warning("Escolha limites diferentes (x de ≠ x até e y de ≠ y até).")
                else:
                    ss["laje_mcount"] += 1
                    _nm = f"M{ss['laje_mcount']}"
                    ss["laje_manuais"].append(cl.comodo_manual(_x0, _x1, _y0, _y1, _nm))
                    ss["laje_tipos"][_nm] = _tp
                    ss["laje_telhado"][_nm] = _tl
                    st.rerun()

    # ---- vigas de cobertura
    sec(2, "Vigas de cobertura (viga contínua NBR 6118)")
    st.caption(f"Laje lançada na direção "
               f"**{'horizontal' if r['principal']=='H' else 'vertical'}** "
               f"(cobertura q ≈ {r['q_cob']} kN/m²). A seção cresce sozinha se o "
               "vão exigir.")
    tabela([{"Viga": v["nome"], "Seção": v["secao"], "Nº vãos": v["nvaos"],
             "Vãos (m)": " + ".join(f"{x:.2f}" for x in v["vaos"]),
             "Carga w (kN/m)": v["w"], "M máx (kN·m)": v["mmax"],
             "Aço (kg)": v["peso"] if v["peso"] else "—"} for v in r["vigas"]])
    st.markdown("**📊 Planta de CARGAS NAS VIGAS** (kN/m — laje + telhado + peso próprio):")
    _fcv = rpdf.fig_cargas_vigas(r)
    if _fcv is not None:
        st.pyplot(_fcv, width="stretch")
        plt.close(_fcv)
    st.caption("Carga total de cada viga. **Modelo unidirecional:** a laje descarrega "
               f"nas vigas **{'horizontais (VH)' if r['principal']=='H' else 'verticais (VV)'}** "
               "(direção principal); as da outra direção levam só o **peso próprio** "
               "(~1 kN/m). Se quiser, evoluo para carga nos dois sentidos (reação real "
               "da laje).")

    # ---- baldrames
    sec(3, "Baldrames (vigas de fundação sob as paredes)")
    st.caption(f"Carga de parede ≈ {r['wall']} kN/m sobre cada linha de baldrame.")
    tabela([{"Baldrame": b["nome"], "Seção": b["secao"], "Nº vãos": b["nvaos"],
             "Vãos (m)": " + ".join(f"{x:.2f}" for x in b["vaos"]),
             "Carga w (kN/m)": b["w"], "M máx (kN·m)": b["mmax"],
             "Aço (kg)": b["peso"] if b["peso"] else "—"} for b in r["baldrames"]])

    # ---- pilares
    sec(4, "Pilares (NBR 6118 — 14×30, seção cresce pela norma)")
    tabela([{"Pilar": p["pilar"], "Seção (cm)": p["secao"],
             "Carga (tf)": p["carga_tf"], "Armadura": p["armadura"],
             "Aço (kg)": p["peso"]} for p in r["pilares"]])

    # ---- fundação
    sec(5, "Cargas na fundação (para escolher bloco / estaca / sapata)")
    st.metric("Carga total à fundação (cobertura + alvenaria/baldrames)",
              f"{r['fund_tf']} tf")
    st.markdown("**📊 Planta de CARGAS NOS PILARES** (tf) — a carga de cada pilar em "
                "número grande, para você projetar a fundação:")
    _fcp = rpdf.fig_cargas_pilares(r)
    if _fcp is not None:
        st.pyplot(_fcp, width="stretch")
        plt.close(_fcp)
    st.caption("Relação de cargas por pilar (carga do pilar = carga na fundação "
               "correspondente):")
    tabela([{"Pilar": p["pilar"], "Carga (tf)": p["carga_tf"],
             "Carga (kN)": round((p.get("carga_tf") or 0) * 9.81, 0),
             "Seção (cm)": p["secao"]} for p in r["pilares"]])
    st.caption("O dimensionamento das fundações (bloco, estaca, sapata) depende do "
               "**SPT do terreno**. As cargas dos pilares vêm do lançamento (área de "
               "influência + paredes).")

    # ---- QUANTITATIVO de aço a comprar
    sec(6, "Relação de aço a comprar (por etapa e total)", destaque=True)
    aco_lajes = rl["aco_barras"]
    total_geral = round(r["aco_total"] + aco_lajes, 1)
    q1, q2, q3, q4, q5 = st.columns(5)
    q1.metric("Vigas", f"{r['aco_vigas']} kg")
    q2.metric("Pilares", f"{r['aco_pilares']} kg")
    q3.metric("Baldrames", f"{r['aco_baldrames']} kg")
    q4.metric("Lajes", f"{aco_lajes} kg")
    q5.metric("TOTAL", f"{total_geral} kg")
    tabela([
        {"Etapa": "Vigas de cobertura", "Aço CA-50A (kg)": r["aco_vigas"]},
        {"Etapa": "Pilares", "Aço CA-50A (kg)": r["aco_pilares"]},
        {"Etapa": "Baldrames", "Aço CA-50A (kg)": r["aco_baldrames"]},
        {"Etapa": "Lajes (reforço + distribuição)", "Aço CA-50A (kg)": aco_lajes},
        {"Etapa": "TOTAL A COMPRAR", "Aço CA-50A (kg)": total_geral},
    ])
    st.caption(f"Inclui ~10% de perdas/emendas. Lajes: além do aço, prever "
               f"**{rl['vigotas_m']} m de vigota** e **{rl['area']} m² de laje** "
               "(EPS + capa). As vigotas já trazem a treliça (CA-60).")
    if r["falhas"] or rl["falhas"]:
        st.warning("Verificar manualmente: " + ", ".join(r["falhas"] + rl["falhas"]))

    # ---- relatório resumido em HTML (rápido)
    sec(7, "Baixar os relatórios")
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
