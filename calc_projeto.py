# -*- coding: utf-8 -*-
"""Projeto Completo — CÁLCULO/DETALHAMENTO automático a partir do estrutura_*.json
(saída do editor visual). Reusa os MESMOS motores das telas aprovadas:
motor_viga (viga contínua NBR 6118, Três Momentos) para as vigas de cobertura e
os baldrames, e motor_pilar (NBR 6118, 2ª ordem/flexo-compressão) para os pilares.
NÃO altera os módulos aprovados.

Padrões (para os testes): concreto C25, aço CA-50A; VIGAS com base bw = 14 cm e
altura h = 10% do MAIOR vão (uma seção por viga contínua); PILARES 14×30 que
crescem pela norma se a armadura passar do limite. Saída: detalhamento completo
por viga/baldrame/pilar (figuras + memorial) + quantitativo de aço por etapa
(vigas, pilares, baldrames) e TOTAL a comprar, além das cargas de fundação.
"""
import motor_viga as mv
import motor_pilar as mp
from editor_lancamento import agrupar_vigas_continuas

Q_COB = 3.0    # kN/m² cobertura (compatibilidade; hoje calculado por composição)
# --- composição da carga da cobertura (kN/m²) — laje de FORRO com telhado ---
G_PERM = 2.5   # laje de forro pré-moldada (EPS + capa) + revestimento/regularização
Q_FORRO = 0.5  # sobrecarga de forro sem acesso a pessoas (NBR 6120)
G_TELHADO = {  # telhado = telha (NBR 6120/catálogo) + madeiramento (estimativa)
    "fibrocimento": 0.30,   # Eternit/fibrocimento 6 mm + madeira (~30 kgf/m²)
    "ceramica": 0.80,       # telha cerâmica + madeira (~80 kgf/m²)
}
WALL = 6.0     # kN/m parede sobre baldrame (~15 cm rebocada, altura ~2,85 m)
FCK = 25.0     # concreto C25 (padrão)
BW = 14        # base padrão das vigas/baldrames (assenta na parede) [cm]
L0_PILAR = 3.0  # pé-direito livre dos pilares (comprimento de flambagem) [m]
CAA = "II"     # classe de agressividade (urbana) — cobrimento dos pilares
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
    if not res:                       # viga que não pôde ser detalhada (vão nulo)
        return None
    q = res.get("quantitativo")
    return round(q["peso_total"], 1) if q and q.get("peso_total") else None


def _detalhar(nome, vaos, w, b=BW, h=40):
    tramos = [{"tipo": "Normal", "nome": f"{nome}.{k+1}", "L": float(v),
               "q": float(w), "P": 0.0, "a": 0.0}
              for k, v in enumerate(vaos) if v and v > 0.1]
    if not tramos:
        return None
    dados = {"b": b, "h": h, "fck": FCK, "cob": 2.5, "peso_proprio": True}
    return mv.calcular_viga(dados, tramos)


def _altura_viga(vaos):
    """Altura padrão h = 10% do MAIOR vão (múltiplo de 5, mínimo 30 cm)."""
    vv = [v for v in vaos if v and v > 0.1]
    h = 10.0 * max(vv) if vv else 40.0          # 10% do maior vão (cm)
    return max(30, int(5 * round(h / 5.0)))


def _detalhar_viga(nome, vaos, w, b=BW):
    """Detalha a partir de h = 10% do maior vão; só cresce se ainda falhar."""
    h0 = _altura_viga(vaos)
    res = None
    for h in range(h0, 105, 5):
        res = _detalhar(nome, vaos, w, b=b, h=h)
        if res is None:
            return None, h
        if not (res.get("falha_flexao") or res.get("falha_biela")):
            return res, h
    return res, 100


def _detalhar_pilar(carga_tf):
    """Dimensiona no motor_pilar. Padrão 14×30; cresce a seção pela norma
    (h, depois b) até haver arranjo de armadura válido (≤ 4% de aço)."""
    Nk = max(1.0, float(carga_tf or 0.0)) * 9.81        # tf -> kN
    tentativas = ([(14, h) for h in range(30, 75, 5)]    # 14×30 .. 14×70
                  + [(19, h) for h in range(30, 100, 5)]  # b=19 (sem γn)
                  + [(25, h) for h in range(30, 130, 5)])
    rp = None
    for b, h in tentativas:
        rp = mp.calcular_pilar({"b": b, "h": h, "l0": L0_PILAR, "fck": FCK,
                                "Nk": Nk, "caa": CAA})
        if "erros" not in rp and rp.get("opcoes"):
            return rp, rp["opcoes"][0], f"{b}x{h}", round(Nk)
    return rp, None, "14x30", round(Nk)


def _mmax(res):
    if not res:
        return 0.0
    ms = [abs(m) for m in res.get("estatica", {}).get("M_apoios", [])]
    ms += [abs(f.get("Mk", 0) or 0) for f in res.get("flex_vaos", [])]
    return round(max(ms + [0.0]), 1)


def _nomear_linhas(linhas):
    """Numeração PROFISSIONAL das vigas contínuas: horizontais VH de cima→baixo
    (maior y = VH1) e verticais VV de esq→dir (menor x = VV1), cada família
    reiniciando em 1. Devolve (nomes_viga, nomes_baldrame) — dicts índice→nome."""
    H = sorted((k for k, l in enumerate(linhas) if l["dir"] == "H"),
               key=lambda k: -linhas[k]["pos"])
    V = sorted((k for k, l in enumerate(linhas) if l["dir"] == "V"),
               key=lambda k: linhas[k]["pos"])
    nomes = {}
    for n, k in enumerate(H, 1):
        nomes[k] = f"VH{n}"
    for n, k in enumerate(V, 1):
        nomes[k] = f"VV{n}"
    bnomes = {k: f"VB{n}" for n, k in enumerate(H + V, 1)}   # Viga Baldrame
    return nomes, bnomes


def planta_do_json(data):
    """Geometria da planta (croqui) direto do JSON, SEM rodar o cálculo — para
    a tela de conferência. Agrupa as vigas contínuas e nomeia VH/VV como no
    detalhamento; devolve no mesmo formato que `fig_planta` consome."""
    linhas = agrupar_vigas_continuas(data.get("vigas", []))
    nomes, bnomes = _nomear_linhas(linhas)
    vigas = [dict(nome=nomes[i], dir=l["dir"],
                  pos=l["pos"], ini=l["ini"], fim=l["fim"])
             for i, l in enumerate(linhas)]
    baldrames = [dict(nome=bnomes[i], dir=l["dir"],
                      pos=l["pos"], ini=l["ini"], fim=l["fim"])
                 for i, l in enumerate(linhas)]
    return dict(vigas=vigas, baldrames=baldrames,
                pilares=data.get("pilares", []), lajes=data.get("lajes", []))


def calcular_projeto(data, g_telhado=None, wall=WALL, h_pilar=3.0):
    """Roda o projeto inteiro a partir do JSON do editor. `g_telhado` (kN/m²) é o
    peso do telhado escolhido; a carga de cobertura vira composição transparente:
    q_cob = laje-forro+revest. (G_PERM) + sobrecarga de forro (Q_FORRO) + telhado."""
    if g_telhado is None:
        g_telhado = G_TELHADO["fibrocimento"]
    g_telhado = float(g_telhado)
    q_cob = round(G_PERM + Q_FORRO + g_telhado, 2)
    vigas = data.get("vigas", [])
    pilares = data.get("pilares", [])
    linhas = agrupar_vigas_continuas(vigas)
    nomes, bnomes = _nomear_linhas(linhas)
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
        nome = nomes[i]
        res, h = _detalhar_viga(nome, l["vaos"], w)
        vigas_det.append(dict(nome=nome, dir=l["dir"], nvaos=len(l["vaos"]),
                              comp=l["comp"], vaos=l["vaos"], w=w, secao=f"{BW}x{h}",
                              pos=l["pos"], ini=l["ini"], fim=l["fim"],
                              mmax=_mmax(res), peso=_peso(res),
                              falha=bool(res and (res.get("falha_flexao") or res.get("falha_biela"))),
                              res=res))
    # ---- baldrames (mesmas linhas, carga de parede)
    baldr_det = []
    for i, l in enumerate(linhas):
        nome = bnomes[i]
        res, h = _detalhar_viga(nome, l["vaos"], wall)
        baldr_det.append(dict(nome=nome, dir=l["dir"], nvaos=len(l["vaos"]),
                              comp=l["comp"], vaos=l["vaos"], w=wall, secao=f"{BW}x{h}",
                              pos=l["pos"], ini=l["ini"], fim=l["fim"],
                              mmax=_mmax(res), peso=_peso(res),
                              falha=bool(res and (res.get("falha_flexao") or res.get("falha_biela"))),
                              res=res))
    # ---- pilares (dimensionados no motor_pilar; 14×30 crescendo pela norma)
    pil_det = []
    aco_pil = 0.0
    for i, p in enumerate(pilares):
        nome = p.get("pilar", f"P{i+1}")
        carga = p.get("carga_tf", 0) or 0
        rp, opt, secao, Nk = _detalhar_pilar(carga)
        peso = opt["peso_total"] if opt else 0.0
        aco_pil += peso
        pil_det.append(dict(pilar=nome, secao=secao, carga_tf=carga, Nk=Nk,
                            x_m=p.get("x_m"), y_m=p.get("y_m"),
                            armadura=(opt["texto"] if opt else "SEÇÃO INSUFICIENTE"),
                            estribo=(f"ø{opt['phi_t']:.1f} c/{opt['s_est']:.0f}"
                                     if opt else "—"),
                            peso=round(peso, 1), falha=opt is None,
                            res=rp, opt=opt))

    # ---- ordena as listas na sequência dos nomes (tabelas em ordem)
    def _num(n):
        return int("".join(c for c in n if c.isdigit()) or 0)
    vigas_det.sort(key=lambda v: (0 if v["nome"].startswith("VH") else 1, _num(v["nome"])))
    baldr_det.sort(key=lambda b_: _num(b_["nome"]))
    pil_det.sort(key=lambda p: _num(p["pilar"]))

    # ---- quantitativo de aço (a comprar) por etapa
    aco_vigas = round(sum(v["peso"] for v in vigas_det if v["peso"]) * 1.10, 1)
    aco_baldr = round(sum(b_["peso"] for b_ in baldr_det if b_["peso"]) * 1.10, 1)
    aco_pilares = round(aco_pil * 1.08, 1)
    aco_total = round(aco_vigas + aco_pilares + aco_baldr, 1)
    fund_tf = data.get("total_tf")
    if fund_tf is None:
        fund_tf = round(sum(p.get("carga_tf", 0) for p in pilares), 1)
    falhas = ([v["nome"] for v in (vigas_det + baldr_det) if v["falha"]]
              + [p["pilar"] for p in pil_det if p["falha"]])

    return dict(vigas=vigas_det, baldrames=baldr_det, pilares=pil_det,
                aco_vigas=aco_vigas, aco_pilares=aco_pilares, aco_baldrames=aco_baldr,
                aco_total=aco_total, fund_tf=fund_tf, principal=principal,
                q_cob=q_cob, wall=wall, falhas=falhas, lajes=data.get("lajes", []),
                carga_comp=dict(g_perm=G_PERM, q_forro=Q_FORRO, g_telhado=g_telhado,
                                q_cob=q_cob))


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
<p class="sub">Projeto: <b>{proj}</b> · Detalhamento automático NBR 6118 · concreto C{int(FCK)} (fck = {int(FCK)} MPa) · aço CA-50A · γc=1,4 · γs=1,15</p>

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
