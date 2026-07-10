# -*- coding: utf-8 -*-
"""Projeto Completo — CÁLCULO/DETALHAMENTO automático a partir do estrutura_*.json
(saída do editor visual). Reusa motor_viga (viga contínua NBR 6118, Três Momentos)
para as vigas de cobertura e os baldrames; pilares em pré-dimensionamento (térrea).
NÃO altera os módulos aprovados.

Saída: detalhamento por viga contínua / baldrame / pilar + quantitativo de aço por
etapa (vigas, pilares, baldrames) e TOTAL a comprar, além das cargas de fundação.
"""
import motor_viga as mv
from editor_lancamento import agrupar_vigas_continuas

Q_COB = 3.0    # kN/m² cobertura (laje EPS 16+4 + telha fibrocimento + sobrecarga)
WALL = 6.0     # kN/m parede sobre baldrame (~15 cm rebocada, altura ~2,85 m)
FCK = 25.0
PESO_LIN = {5.0: 0.154, 6.3: 0.245, 8.0: 0.395, 10.0: 0.617,
            12.5: 0.963, 16.0: 1.578, 20.0: 2.466}   # kg/m


def _trib(pos, arr):
    """Largura tributária (m) de uma linha de viga entre suas paralelas."""
    if len(arr) < 2:
        return 3.0
    i = arr.index(pos)
    a = (arr[i] - arr[i - 1]) / 2 if i > 0 else (arr[i + 1] - arr[i]) / 2
    b = (arr[i + 1] - arr[i]) / 2 if i < len(arr) - 1 else (arr[i] - arr[i - 1]) / 2
    return max(0.6, a + b)


def _peso(res):
    q = res.get("quantitativo")
    return round(q["peso_total"], 1) if q and q.get("peso_total") else None


def _detalhar(nome, vaos, w, b=14, h=40):
    tramos = [{"tipo": "Normal", "nome": f"{nome}.{k+1}", "L": float(v),
               "q": float(w), "P": 0.0, "a": 0.0}
              for k, v in enumerate(vaos) if v and v > 0.1]
    if not tramos:
        return None
    dados = {"b": b, "h": h, "fck": FCK, "cob": 2.5, "peso_proprio": True}
    return mv.calcular_viga(dados, tramos)


def _detalhar_auto(nome, vaos, w, b=14):
    """Detalha aumentando a altura (40→50→60→70) até a viga passar."""
    res = None
    for h in (40, 50, 60, 70):
        res = _detalhar(nome, vaos, w, b=b, h=h)
        if res is None:
            return None, h
        if not (res.get("falha_flexao") or res.get("falha_biela")):
            return res, h
    return res, 70


def _mmax(res):
    if not res:
        return 0.0
    ms = [abs(m) for m in res.get("estatica", {}).get("M_apoios", [])]
    ms += [abs(f.get("Mk", 0) or 0) for f in res.get("flex_vaos", [])]
    return round(max(ms + [0.0]), 1)


def calcular_projeto(data, q_cob=Q_COB, wall=WALL, h_pilar=3.0):
    """Roda o projeto inteiro a partir do JSON do editor."""
    vigas = data.get("vigas", [])
    pilares = data.get("pilares", [])
    linhas = agrupar_vigas_continuas(vigas)
    posH = sorted(set(l["pos"] for l in linhas if l["dir"] == "H"))
    posV = sorted(set(l["pos"] for l in linhas if l["dir"] == "V"))
    # direção principal (mais linhas = onde as vigotas se apoiam) recebe a laje;
    # a outra direção carrega só o peso próprio (modelo unidirecional simplificado).
    principal = "H" if len(posH) >= len(posV) else "V"

    # ---- vigas de cobertura
    vigas_det = []
    for i, l in enumerate(linhas):
        arr = posH if l["dir"] == "H" else posV
        w = round(q_cob * _trib(l["pos"], arr), 2) if l["dir"] == principal else 0.0
        nome = f"{'VH' if l['dir'] == 'H' else 'VV'}{i+1}"
        res, h = _detalhar_auto(nome, l["vaos"], w)
        vigas_det.append(dict(nome=nome, dir=l["dir"], nvaos=len(l["vaos"]),
                              comp=l["comp"], vaos=l["vaos"], w=w, secao=f"14x{h}",
                              mmax=_mmax(res), peso=_peso(res),
                              falha=bool(res and (res.get("falha_flexao") or res.get("falha_biela"))),
                              res=res))
    # ---- baldrames (mesmas linhas, carga de parede, 14x40)
    baldr_det = []
    for i, l in enumerate(linhas):
        nome = f"B{i+1}"
        res, h = _detalhar_auto(nome, l["vaos"], wall)
        baldr_det.append(dict(nome=nome, dir=l["dir"], nvaos=len(l["vaos"]),
                              comp=l["comp"], vaos=l["vaos"], w=wall, secao=f"14x{h}",
                              mmax=_mmax(res), peso=_peso(res),
                              falha=bool(res and (res.get("falha_flexao") or res.get("falha_biela"))),
                              res=res))
    # ---- pilares (pré-dimensionamento: seção do editor + armadura mínima)
    pil_det = []
    aco_pil = 0.0
    for i, p in enumerate(pilares):
        sec = str(p.get("secao", "14x30"))
        try:
            bb, hh = [float(x) for x in sec.lower().replace("+", "").split("x")[:2]]
        except Exception:
            bb, hh = 14.0, 30.0
        L_long = 4 * (h_pilar + 0.5)                 # 4 ø10 (pé-direito + arranque)
        n_est = int(h_pilar / 0.15) + 1              # estribos ø5 c/15
        per = 2 * ((bb - 4) + (hh - 4)) / 100 + 0.10  # m por estribo
        peso = L_long * PESO_LIN[10.0] + n_est * per * PESO_LIN[5.0]
        aco_pil += peso
        pil_det.append(dict(pilar=p.get("pilar", f"P{i+1}"), secao=sec,
                            carga_tf=p.get("carga_tf", 0),
                            armadura="4 ø10 + estribo ø5 c/15", peso=round(peso, 1)))

    # ---- quantitativo de aço (a comprar) por etapa
    aco_vigas = round(sum(v["peso"] for v in vigas_det if v["peso"]) * 1.10, 1)
    aco_baldr = round(sum(b_["peso"] for b_ in baldr_det if b_["peso"]) * 1.10, 1)
    aco_pilares = round(aco_pil * 1.08, 1)
    aco_total = round(aco_vigas + aco_pilares + aco_baldr, 1)
    fund_tf = data.get("total_tf")
    if fund_tf is None:
        fund_tf = round(sum(p.get("carga_tf", 0) for p in pilares), 1)
    falhas = [v["nome"] for v in (vigas_det + baldr_det) if v["falha"]]

    return dict(vigas=vigas_det, baldrames=baldr_det, pilares=pil_det,
                aco_vigas=aco_vigas, aco_pilares=aco_pilares, aco_baldrames=aco_baldr,
                aco_total=aco_total, fund_tf=fund_tf, principal=principal,
                q_cob=q_cob, wall=wall, falhas=falhas)


# ------------------------------------------------------------ relatório HTML
def _linha_viga(v):
    vaos = " + ".join(f"{x:.2f}" for x in v["vaos"])
    aco = f"{v['peso']}" if v["peso"] else "—"
    return (f"<tr><td>{v['nome']}</td><td>{v['secao']}</td><td>{v['nvaos']}</td>"
            f"<td>{vaos}</td><td>{v['w']}</td><td>{v['mmax']}</td>"
            f"<td class='r'>{aco}</td></tr>")


def relatorio_html(r, proj="projeto"):
    """Relatório autossuficiente (HTML) — abre no navegador e imprime em PDF."""
    vrows = "".join(_linha_viga(v) for v in r["vigas"])
    brows = "".join(_linha_viga(b) for b in r["baldrames"])
    prows = "".join(
        f"<tr><td>{p['pilar']}</td><td>{p['secao']}</td><td>{p['carga_tf']}</td>"
        f"<td>{p['armadura']}</td><td class='r'>{p['peso']}</td></tr>"
        for p in r["pilares"])
    aviso = ""
    if r["falhas"]:
        aviso = ("<p class='warn'>⚠ Verificar manualmente (não passaram nem no maior "
                 "perfil): " + ", ".join(r["falhas"]) + "</p>")
    dir_txt = "horizontal" if r["principal"] == "H" else "vertical"
    return f"""<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Relatório — {proj}</title><style>
:root{{--az:#0f2b4c;--am:#d98a04;--ln:#e2e8f0;}}
*{{box-sizing:border-box}}body{{font-family:Segoe UI,Arial,sans-serif;color:#0f172a;
margin:0;padding:28px;background:#f8fafc;font-size:16px;line-height:1.5}}
h1{{color:var(--az);margin:0 0 4px;font-size:26px}}
h2{{color:var(--az);border-left:6px solid var(--am);padding-left:10px;margin:26px 0 10px;font-size:20px}}
.sub{{color:#475569;margin:0 0 18px}}
.cards{{display:flex;gap:14px;flex-wrap:wrap;margin:8px 0 4px}}
.card{{flex:1 1 150px;background:#fff;border:1px solid var(--ln);border-radius:12px;
padding:14px 16px;box-shadow:0 1px 3px rgba(15,43,76,.06)}}
.card .lbl{{color:#64748b;font-size:13px;text-transform:uppercase;letter-spacing:.04em}}
.card .val{{color:var(--az);font-size:26px;font-weight:800;margin-top:2px}}
.card.tot{{background:var(--az)}}.card.tot .lbl{{color:#c7d7ec}}.card.tot .val{{color:#fff}}
table{{width:100%;border-collapse:collapse;background:#fff;border:1px solid var(--ln);
border-radius:10px;overflow:hidden;font-size:15px}}
th{{background:var(--az);color:#fff;text-align:left;padding:9px 11px;font-weight:600}}
td{{padding:8px 11px;border-top:1px solid var(--ln)}}td.r{{text-align:right;font-weight:700}}
tr:nth-child(even) td{{background:#f6f9fc}}
.cap{{color:#64748b;font-size:13px;margin:6px 0 0}}
.warn{{background:#fef3c7;border:1px solid #f59e0b;color:#92400e;padding:10px 12px;border-radius:8px}}
@media print{{body{{background:#fff;padding:0}}.card{{box-shadow:none}}}}
</style></head><body>
<h1>Polotto Engenharia — Projeto Completo</h1>
<p class="sub">Projeto: <b>{proj}</b> · Detalhamento automático NBR 6118 · concreto {int(FCK)} MPa · aço CA-50/60</p>

<h2>Aço a comprar (por etapa e total)</h2>
<div class="cards">
<div class="card"><div class="lbl">Vigas</div><div class="val">{r['aco_vigas']} kg</div></div>
<div class="card"><div class="lbl">Pilares</div><div class="val">{r['aco_pilares']} kg</div></div>
<div class="card"><div class="lbl">Baldrames</div><div class="val">{r['aco_baldrames']} kg</div></div>
<div class="card tot"><div class="lbl">Total</div><div class="val">{r['aco_total']} kg</div></div>
</div>
<p class="cap">Inclui ~10% de perdas/emendas em vigas e baldrames e ~8% nos pilares.</p>
{aviso}

<h2>Vigas de cobertura</h2>
<p class="cap">Laje lançada na direção {dir_txt} · cobertura q ≈ {r['q_cob']} kN/m². Seção cresce sozinha se o vão exigir.</p>
<table><tr><th>Viga</th><th>Seção</th><th>Nº vãos</th><th>Vãos (m)</th><th>w (kN/m)</th><th>M máx (kN·m)</th><th>Aço (kg)</th></tr>{vrows}</table>

<h2>Baldrames (fundação sob as paredes)</h2>
<p class="cap">Carga de parede ≈ {r['wall']} kN/m em cada linha.</p>
<table><tr><th>Baldrame</th><th>Seção</th><th>Nº vãos</th><th>Vãos (m)</th><th>w (kN/m)</th><th>M máx (kN·m)</th><th>Aço (kg)</th></tr>{brows}</table>

<h2>Pilares</h2>
<table><tr><th>Pilar</th><th>Seção (cm)</th><th>Carga (tf)</th><th>Armadura</th><th>Aço (kg)</th></tr>{prows}</table>

<h2>Cargas na fundação</h2>
<div class="cards"><div class="card"><div class="lbl">Carga total (cobertura + alvenaria)</div>
<div class="val">{r['fund_tf']} tf</div></div></div>
<p class="cap">A carga de cada sapata/estaca é a carga do pilar correspondente. O dimensionamento das fundações depende do SPT do terreno.</p>
</body></html>"""
