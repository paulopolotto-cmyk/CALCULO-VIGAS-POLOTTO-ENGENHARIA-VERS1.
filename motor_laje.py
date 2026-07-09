# -*- coding: utf-8 -*-
"""
Motor de cálculo de LAJES de concreto armado — Polotto Engenharia.
Módulo PURO (sem Streamlit), testável. NBR 6118:2014/2023, NBR 6120:2019,
NBR 14859 (lajes pré-fabricadas treliçadas).

Cobre:
- Laje MACIÇA armada em 1 ou 2 direções (9 casos de apoio). Momentos e flechas
  pela solução da placa de Kirchhoff por DIFERENÇAS FINITAS (estêncil bi-
  harmônico de 13 pontos, nós-fantasma p/ borda apoiada/engastada) — validado
  contra Timoshenko (ver docs/lajes). Reações por CHARNEIRAS PLÁSTICAS
  (NBR 6118 14.7.6.1) por grade ponderada (45°/60°).
- Laje PRÉ-MOLDADA treliçada (unidirecional): esforços, flecha e reações.
- Cargas NBR 6120:2019 (Tab. 10). Flecha diferida por fluência (ξ∞=2).
- Reforço (flexão simples), As_min, e quantitativos.

Ferramenta de PRÉ-DIMENSIONAMENTO; não substitui projeto estrutural assinado.
"""
import math

import numpy as np

# ---------------------------------------------------------------- constantes
GAMMA_C = 1.4
GAMMA_S = 1.15
GAMMA_F = 1.4
FYK = 50.0                      # CA-50 [kN/cm²... na verdade 500 MPa]
FYD = 50.0 / GAMMA_S           # = 43,478 kN/cm²  (fyk=500 MPa = 50 kN/cm²)
NU = 0.2                        # coef. de Poisson do concreto (NBR 6118 8.2.9)
PESO_CONCRETO = 25.0            # kN/m³ (NBR 6120)
PESO_ESP_ACO = 7850.0          # kg/m³

# NBR 6120:2019, Tabela 10 — cargas acidentais de uso (kN/m²).
# (valores confirmados por verificação cruzada — ver docs/lajes)
CARGAS_USO = {
    "Dormitório / sala / cozinha": 1.5,
    "Banheiro": 1.5,
    "Despensa / área de serviço / lavanderia": 2.0,
    "Corredor (dentro da unidade)": 1.5,
    "Corredor / hall de uso comum": 3.0,
    "Escritório": 2.5,
    "Sótão": 2.0,
    "Forro (sem acesso a pessoas)": 0.5,
    "Terraço / varanda (com acesso)": 2.5,
    "Garagem / veículos leves (≤ 25 kN)": 3.0,
}

# Peso próprio de laje treliçada (kN/m²), por altura total e enchimento.
# EPS: coerente com a fórmula geométrica (nervuras + capa, intereixo 42 cm).
# Cerâmico: faixa de catálogo nacional (editável por fabricante).
# capa: 4 cm até h=16; 5 cm para h>=20.
PP_TRELICA = {
    #  h_cm: (capa_cm, g_EPS, g_ceramico) — designação comercial h = ench+capa
    12: (4.0, 1.5, 2.0),     # 8+4
    16: (4.0, 1.7, 2.4),     # 12+4
    20: (4.0, 2.0, 2.9),     # 16+4
    25: (5.0, 2.4, 3.4),     # 20+5
}
INTEREIXO = 0.42               # m (espaçamento típico entre vigotas)
LARG_NERVURA = 0.09            # m (largura média da nervura)

# Espessura mínima de laje maciça (NBR 6118 13.2.4.1) [cm]
ESP_MIN_MACICA = {
    "piso": 8.0, "forro": 7.0, "balanco": 10.0,
    "veiculo_leve": 10.0, "veiculo_pesado": 12.0,
}

# ρ_min (%) para armadura de flexão — NBR 6118 Tab. 17.3.1 (CA-50)
RHO_MIN = {20: 0.150, 25: 0.150, 30: 0.173, 35: 0.201,
           40: 0.230, 45: 0.259, 50: 0.288}

BORDAS = ("esq", "dir", "inf", "sup")


# --------------------------------------------------------------- utilidades
def modulo_ecs(fck):
    """Módulo de elasticidade secante Ecs [kN/m²] (NBR 6118 8.2.8, fck<=50)."""
    eci = 5600.0 * math.sqrt(fck)            # MPa (αE=1,0)
    ai = min(1.0, 0.8 + 0.2 * fck / 80.0)
    ecs_mpa = ai * eci
    return ecs_mpa * 1000.0                   # MPa -> kN/m²


def _fcd(fck):
    return (fck / 10.0) / GAMMA_C             # kN/cm²


def as_flexao(Md_kNcm, b_cm, d_cm, fck):
    """Área de aço de flexão simples (kN, cm). Retorna (As_cm2, x/d, ok)."""
    if d_cm <= 0 or Md_kNcm <= 0:
        return 0.0, 0.0, True
    fcd = _fcd(fck)
    mu = Md_kNcm / (b_cm * d_cm ** 2 * 0.85 * fcd)
    disc = 0.64 - 1.28 * mu
    if disc < 0:                              # seção insuficiente (mu>0,5)
        return None, None, False
    xi = (0.8 - math.sqrt(disc)) / 0.64       # x/d
    z = d_cm * (1.0 - 0.4 * xi)
    As = Md_kNcm / (z * FYD)
    return As, xi, xi <= 0.45                  # x/d<=0,45 (dutilidade s/ redistr.)


def as_min(fck, h_cm, b_cm=100.0):
    """As mínima de flexão (cm²) na largura b (NBR 6118 17.3.5.2.1 / Tab 17.3)."""
    rho = RHO_MIN.get(int(round(fck)), 0.15) / 100.0
    return rho * b_cm * h_cm


ES = 21000.0                                    # kN/cm² (módulo do aço CA-50)


def fator_fissuracao(fck, Ic, yt, Ma, As, d, Ecs_kNcm2, b, alfa=1.5):
    """Fator Ic/Ieq (>=1) da rigidez equivalente de Branson (NBR 6118
    17.3.2.1.1). Todas as grandezas em cm/kN. Ma na comb. quase-permanente.
    alfa = 1,5 (seção retangular) ou 1,2 (T / duplo-T) — item 17.3.1.
    Retorna (fator, Mr)."""
    if As <= 0 or Ma <= 0 or Ic <= 0 or Ecs_kNcm2 <= 0:
        return 1.0, 0.0
    fctm = 0.3 * fck ** (2.0 / 3.0) / 10.0      # kN/cm²
    Mr = alfa * fctm * Ic / yt                   # kN·cm
    if Ma <= Mr:
        return 1.0, Mr                           # não fissura -> rigidez bruta
    ae = ES / Ecs_kNcm2                           # αe = Es/Ecs
    aa = b / 2.0
    bb = ae * As
    cc = -ae * As * d
    x = (-bb + math.sqrt(bb * bb - 4.0 * aa * cc)) / (2.0 * aa)   # LN fissurada
    Icr = b * x ** 3 / 3.0 + ae * As * (d - x) ** 2
    r = (Mr / Ma) ** 3
    Ieq = min(Ic, max(Icr, r * Ic + (1.0 - r) * Icr))
    return Ic / Ieq, Mr


def vrd1(fck, bw_cm, d_cm, As_cm2):
    """Cortante resistente de laje/nervura SEM armadura transversal VRd1 (kN),
    NBR 6118 19.4.1."""
    fctk_inf = 0.7 * 0.3 * fck ** (2.0 / 3.0) / 10.0    # kN/cm²
    fctd = fctk_inf / GAMMA_C
    tau_rd = 0.25 * fctd
    rho1 = min(As_cm2 / (bw_cm * d_cm), 0.02) if bw_cm * d_cm > 0 else 0.0
    k = max(1.0, 1.6 - d_cm / 100.0)             # d em m
    return tau_rd * k * (1.2 + 40.0 * rho1) * bw_cm * d_cm    # kN


# ---------------------------------------------- reações por charneiras (D2)
def reacoes_charneiras(lx, ly, apoios, p, n=400):
    """Reações da laje nas 4 bordas por charneiras plásticas (NBR 6118
    14.7.6.1) via grade ponderada. apoios: {'esq','dir','inf','sup'} ->
    'apoiado'|'engastado'|'livre'. Bordas: esq(x=0), dir(x=lx), inf(y=0),
    sup(y=ly). Retorna {borda: {'area','forca','q_eq','L'}} (kN, kN/m, m)."""
    w = {"apoiado": 1.0, "engastado": 1.0 / math.sqrt(3.0), "livre": 1e9}
    xs = (np.arange(n) + 0.5) / n * lx
    ys = (np.arange(n) + 0.5) / n * ly
    X, Y = np.meshgrid(xs, ys)
    D = np.stack([X * w[apoios["esq"]], (lx - X) * w[apoios["dir"]],
                  Y * w[apoios["inf"]], (ly - Y) * w[apoios["sup"]]])
    idx = D.argmin(axis=0)
    cell = (lx / n) * (ly / n)
    Ledge = {"esq": ly, "dir": ly, "inf": lx, "sup": lx}
    out = {}
    for k, e in enumerate(BORDAS):
        A = float(np.count_nonzero(idx == k) * cell)
        F = p * A
        out[e] = {"area": A, "forca": F, "L": Ledge[e],
                  "q_eq": F / Ledge[e] if Ledge[e] > 0 else 0.0}
    return out


# ------------------------------------------- placa de Kirchhoff (D4) -------
def solve_placa(lx, ly, edges, nu=NU, p=1.0, D=1.0, div=24):
    """Resolve D·∇⁴w = p (placa fina, Kirchhoff) por diferenças finitas.
    edges: {'esq','dir','inf','sup'} -> 'apoiado'(SS) | 'engastado'(fixo).
    Retorna dict com w (grade), momentos máximos e a malha. Validado vs
    Timoshenko (ver docs/lajes)."""
    h = min(lx, ly) / div
    N = max(8, int(round(lx / h)))
    M = max(8, int(round(ly / h)))
    hx, hy = lx / N, ly / M
    s = {"apoiado": -1.0, "engastado": 1.0, "livre": -1.0}
    se, sd, si, ssu = (s[edges["esq"]], s[edges["dir"]],
                       s[edges["inf"]], s[edges["sup"]])
    nun = (N - 1) * (M - 1)

    def ix(i, j):
        return (i - 1) * (M - 1) + (j - 1)

    A = np.zeros((nun, nun))
    b = np.full(nun, p / D)
    cxx, cyy = 1.0 / hx ** 4, 1.0 / hy ** 4
    cxy = 2.0 / (hx ** 2 * hy ** 2)
    for i in range(1, N):
        for j in range(1, M):
            r = ix(i, j)

            def add(ti, tj, c):
                if ti == -1:
                    ti, c = 1, c * se
                elif ti == N + 1:
                    ti, c = N - 1, c * sd
                if tj == -1:
                    tj, c = 1, c * si
                elif tj == M + 1:
                    tj, c = M - 1, c * ssu
                if ti <= 0 or ti >= N or tj <= 0 or tj >= M:
                    return
                A[r, ix(ti, tj)] += c
            for dt, c in ((-2, 1), (-1, -4), (0, 6), (1, -4), (2, 1)):
                add(i + dt, j, c * cxx)
            for dt, c in ((-2, 1), (-1, -4), (0, 6), (1, -4), (2, 1)):
                add(i, j + dt, c * cyy)
            mixed = {(1, 1): 1, (1, 0): -2, (1, -1): 1, (0, 1): -2,
                     (0, 0): 4, (0, -1): -2, (-1, 1): 1, (-1, 0): -2,
                     (-1, -1): 1}
            for (di, dj), c in mixed.items():
                add(i + di, j + dj, c * cxy)
    wv = np.linalg.solve(A, b)
    w = np.zeros((N + 1, M + 1))
    for i in range(1, N):
        for j in range(1, M):
            w[i, j] = wv[ix(i, j)]
    # momentos positivos de vão (nós interiores)
    Mx = np.zeros_like(w)
    My = np.zeros_like(w)
    for i in range(1, N):
        for j in range(1, M):
            wxx = (w[i + 1, j] - 2 * w[i, j] + w[i - 1, j]) / hx ** 2
            wyy = (w[i, j + 1] - 2 * w[i, j] + w[i, j - 1]) / hy ** 2
            Mx[i, j] = -D * (wxx + nu * wyy)
            My[i, j] = -D * (wyy + nu * wxx)
    # momentos negativos de engaste (fórmula do nó-fantasma: M_n=-D·2w_in/h²)
    mx_eng = my_eng = 0.0
    if edges["esq"] == "engastado":
        mx_eng = min(mx_eng, min(-D * 2 * w[1, j] / hx ** 2
                                 for j in range(1, M)))
    if edges["dir"] == "engastado":
        mx_eng = min(mx_eng, min(-D * 2 * w[N - 1, j] / hx ** 2
                                 for j in range(1, M)))
    if edges["inf"] == "engastado":
        my_eng = min(my_eng, min(-D * 2 * w[i, 1] / hy ** 2
                                 for i in range(1, N)))
    if edges["sup"] == "engastado":
        my_eng = min(my_eng, min(-D * 2 * w[i, M - 1] / hy ** 2
                                 for i in range(1, N)))
    return {"w": w, "wmax": float(w.max()),
            "mx_pos": float(Mx.max()), "my_pos": float(My.max()),
            "mx_eng": float(mx_eng), "my_eng": float(my_eng),
            "N": N, "M": M, "hx": hx, "hy": hy}


# --------------------------------------------------- flecha diferida (D5)
def alfa_f(rho_linha=0.0):
    """Fator de fluência αf = Δξ/(1+50ρ'), ξ(∞)=2 (NBR 6118 17.3.2.1.2)."""
    return 2.0 / (1.0 + 50.0 * rho_linha)


def _classifica_flecha(delta_i_mm, delta_dif_mm, L_m):
    """Verifica flecha total (visual) e após alvenaria. Retorna dict."""
    L_mm = L_m * 1000.0
    total = delta_i_mm + delta_dif_mm            # δ_total = (1+αf)·δ_i
    lim_visual = L_mm / 250.0
    lim_alv = min(L_mm / 500.0, 10.0)
    pos_alv = delta_dif_mm                        # parcela após alvenaria ≈ diferida
    ok_visual = total <= lim_visual
    ok_alv = pos_alv <= lim_alv
    folga = min(lim_visual / total if total > 0 else 9,
                lim_alv / pos_alv if pos_alv > 0 else 9)
    if ok_visual and ok_alv and folga > 1.20:
        nivel = "verde"
    elif ok_visual and ok_alv:
        nivel = "amarelo"
    else:
        nivel = "vermelho"
    return {"imediata_mm": delta_i_mm, "total_mm": total,
            "pos_alv_mm": pos_alv, "lim_visual_mm": lim_visual,
            "lim_alv_mm": lim_alv, "ok_visual": ok_visual, "ok_alv": ok_alv,
            "nivel": nivel, "contraflecha_mm": max(0.0, total - lim_visual)}


# =================================================== LAJE MACIÇA ===========
def calcular_laje_macica(dados):
    """dados: lx, ly [m]; apoios {esq,dir,inf,sup}; h [cm]; fck; g_rev, q_uso,
    g_parede [kN/m²]; opcional: div. Retorna resultado completo ou {'erros'}."""
    erros = []
    lx = float(dados["lx"])
    ly = float(dados["ly"])
    if lx <= 0 or ly <= 0:
        return {"erros": ["Vãos devem ser maiores que zero."]}
    # convenção: lx = menor vão
    if lx > ly:
        lx, ly = ly, lx
        troca = True
    else:
        troca = False
    h = float(dados["h"])
    fck = float(dados["fck"])
    apoios = dict(dados.get("apoios",
                  {e: "apoiado" for e in BORDAS}))
    g_rev = float(dados.get("g_rev", 1.0))
    q_uso = float(dados.get("q_uso", 1.5))
    g_par = float(dados.get("g_parede", 0.0))

    lam = ly / lx
    h_cm = h
    psi2 = float(dados.get("psi2", 0.3))            # quase-perm. residencial
    g_pp = PESO_CONCRETO * h_cm / 100.0
    g_tot = g_pp + g_rev + g_par                    # permanente
    q = q_uso                                       # acidental
    p = g_tot + q                                   # kN/m² característica
    pd = GAMMA_F * p                                # ELU
    p_qp = g_tot + psi2 * q                         # quase-perm. (flecha)

    avisos = []
    if "livre" in apoios.values():
        avisos.append("Bordo livre (balanço) ainda não é tratado pelo solver "
                      "de placa — momentos/flecha aproximados; prefira apoiada "
                      "ou engastada.")
    # espessura mínima
    h_min = ESP_MIN_MACICA["piso"]
    if h_cm < h_min:
        avisos.append(f"Espessura {h_cm:.0f} cm < mínimo {h_min:.0f} cm "
                      f"(NBR 6118 13.2.4.1).")
    # direção
    if lam > 2.0:
        direcao = 1
        avisos.append(f"λ = {lam:.2f} > 2 → laje armada em UMA direção "
                      f"(menor vão). Momento M = p·lx²/8.")
    else:
        direcao = 2

    cob = 2.0                                       # cobrimento laje (cm)
    d_x = h_cm - cob - 0.5                           # d camada externa
    d_y = h_cm - cob - 1.5                           # d camada interna

    Ecs = modulo_ecs(fck)                            # kN/m²
    Dpl = Ecs * (h_cm / 100.0) ** 3 / (12.0 * (1 - NU ** 2))  # kN·m

    # Resolve a placa UMA vez com carga unitária (p=1); escala depois:
    # momentos ∝ p (ELU usa pd); flecha ∝ p (ELS usa p_qp).
    if direcao == 2:
        edges = {e: ("engastado" if apoios.get(e) == "engastado"
                     else "apoiado") for e in BORDAS}
        sol = solve_placa(lx, ly, edges, nu=NU, p=1.0, D=Dpl,
                          div=int(dados.get("div", 22)))
        mxu, myu = sol["mx_pos"], sol["my_pos"]      # por unidade de p
        mxeu, myeu = abs(sol["mx_eng"]), abs(sol["my_eng"])
        wu = sol["wmax"]                             # por unidade de p (m)
    else:
        eng_e = (apoios.get("esq") == "engastado"
                 or apoios.get("dir") == "engastado")
        if eng_e:
            mxu, mxeu = lx ** 2 / 14.0, lx ** 2 / 8.0
        else:
            mxu, mxeu = lx ** 2 / 8.0, 0.0
        myu = myeu = 0.0
        I_m = 1.0 * (h_cm / 100.0) ** 3 / 12.0
        wu = (5.0 / 384.0) * lx ** 4 / (Ecs * I_m)   # por unidade de p (m)

    # momentos característicos (exibição) e de cálculo (armadura)
    mx_pos, my_pos, mx_eng, my_eng = mxu * p, myu * p, mxeu * p, myeu * p
    Mdx, Mdy, Mdxe, Mdye = mxu * pd, myu * pd, mxeu * pd, myeu * pd

    # armaduras (por metro) — a partir do MOMENTO DE CÁLCULO
    def _arm(Md_kNm, d):
        As, xi, ok = as_flexao(Md_kNm * 100.0, 100.0, d, fck)
        As_m = as_min(fck, h_cm)
        if As is None:
            return {"As": None, "ok_dut": False, "xi": None,
                    "As_adot": None, "As_min": As_m}
        return {"As": As, "xi": xi, "ok_dut": ok,
                "As_adot": max(As, As_m), "As_min": As_m}

    arm = {
        "x_pos": _arm(Mdx, d_x), "y_pos": _arm(Mdy, d_y),
        "x_neg": _arm(Mdxe, d_x), "y_neg": _arm(Mdye, d_y),
    }
    if any(a["As"] is None for a in arm.values()):
        avisos.append("Momento alto para a espessura (x/d>0,5) — aumente h.")

    # flecha: rigidez FISSURADA de Branson na direção governante (ELS q.p.)
    delta_i_bruta = wu * p_qp * 1000.0               # mm (estádio I)
    Ecs_cm = Ecs * 1e-4                              # kN/m² -> kN/cm²
    Ic = 100.0 * h_cm ** 3 / 12.0                    # cm⁴ (b=100 cm)
    if mx_pos >= my_pos:
        Ma, As_g, d_g = mxu * p_qp * 100.0, \
            (arm["x_pos"]["As_adot"] or as_min(fck, h_cm)), d_x
    else:
        Ma, As_g, d_g = myu * p_qp * 100.0, \
            (arm["y_pos"]["As_adot"] or as_min(fck, h_cm)), d_y
    fator_fis, Mr = fator_fissuracao(fck, Ic, h_cm / 2.0, Ma, As_g, d_g,
                                     Ecs_cm, 100.0)
    delta_i = delta_i_bruta * fator_fis
    af = alfa_f(0.0)
    flecha = _classifica_flecha(delta_i, af * delta_i, lx)
    flecha["fator_fissuracao"] = fator_fis

    # cortante ELU sem estribos (NBR 6118 19.4.1)
    Vsd = pd * lx / 2.0                              # kN/m
    VRd1 = vrd1(fck, 100.0, d_x, arm["x_pos"]["As_adot"] or as_min(fck, h_cm))
    if Vsd > VRd1:
        avisos.append(f"Cortante Vsd={Vsd:.1f} > VRd1={VRd1:.1f} kN/m — "
                      f"laje exigiria armadura de cisalhamento; aumente h.")
    if any(a["As"] is None for a in arm.values()):
        avisos.append("Momento alto para a espessura: seção comprimida "
                      "demais (x/d>0,5). Aumente h.")

    # reações
    reac = reacoes_charneiras(lx, ly, apoios, p)
    reac_d = reacoes_charneiras(lx, ly, apoios, pd)

    # quantitativos (por m² e total do pano)
    area = lx * ly
    vol_conc = area * h_cm / 100.0                   # m³
    forma = area                                     # m² (fundo)
    # kg de aço ≈ (As_x + As_y) [cm²/m] × área [m²] → cm²·m; +30% (negativas,
    # ancoragem, distribuição). As_x·lx·ly + As_y·lx·ly = (As_x+As_y)·área.
    As_soma = (arm["x_pos"]["As_adot"] or 0) + (arm["y_pos"]["As_adot"] or 0)
    kg_aco = As_soma * (lx * ly) / 1e4 * PESO_ESP_ACO * 1.30

    return {
        "tipo": "macica", "lx": lx, "ly": ly, "trocou_dir": troca,
        "lambda": lam, "direcao": direcao, "h": h_cm, "h_min": h_min,
        "g_pp": g_pp, "g_total": g_tot, "q_uso": q_uso, "p": p, "pd": pd,
        "momentos": {"mx_pos": mx_pos, "my_pos": my_pos,
                     "mx_eng": mx_eng, "my_eng": my_eng,
                     "Mdx": Mdx, "Mdy": Mdy, "Mdxe": Mdxe, "Mdye": Mdye},
        "p_qp": p_qp,
        "armaduras": arm, "flecha": flecha,
        "reacoes": reac, "reacoes_d": reac_d,
        "quant": {"area": area, "vol_conc": vol_conc, "forma": forma,
                  "kg_aco": kg_aco, "taxa_aco": kg_aco / area if area else 0},
        "Ecs": Ecs, "avisos": avisos, "erros": erros,
    }


# =============================================== LAJE TRELIÇADA ============
def h_recomendada_trelica(lx, continua=False):
    """Altura recomendada (cm) por pré-dimensionamento (flecha)."""
    coef = 35.0 if continua else 30.0
    return lx * 100.0 / coef


def calcular_laje_trelicada(dados):
    """dados: lx, ly [m]; h [cm em {12,16,20,25}]; enchimento 'EPS'|'ceramico';
    continuidade 'biapoiada'|'continua'; fck; g_rev, q_uso, g_parede."""
    lx = float(dados["lx"])
    ly = float(dados["ly"])
    if lx <= 0 or ly <= 0:
        return {"erros": ["Vãos devem ser maiores que zero."]}
    # vigotas armam no MENOR vão (a laje "vence" o menor vão)
    if lx > ly:
        lx, ly = ly, lx
    h = int(dados["h"])
    if h not in PP_TRELICA:
        return {"erros": [f"Altura {h} cm não tabelada "
                          f"(use {list(PP_TRELICA)})."]}
    ench = dados.get("enchimento", "EPS")
    continua = dados.get("continuidade", "biapoiada") == "continua"
    fck = float(dados["fck"])
    g_rev = float(dados.get("g_rev", 1.0))
    q_uso = float(dados.get("q_uso", 1.5))
    g_par = float(dados.get("g_parede", 0.0))

    psi2 = float(dados.get("psi2", 0.3))
    capa, g_eps, g_cer = PP_TRELICA[h]
    g_pp = g_eps if ench.upper().startswith("E") else g_cer
    g_tot = g_pp + g_rev + g_par
    p = g_tot + q_uso                                # kN/m² característica
    pd = GAMMA_F * p                                 # ELU
    p_qp = g_tot + psi2 * q_uso                      # quase-perm. (flecha)

    avisos = []
    # pré-dimensionamento / vão-limite
    h_reco = h_recomendada_trelica(lx, continua)
    ok_vao = h >= h_reco - 0.5
    if not ok_vao:
        avisos.append(f"Vão {lx:.2f} m exige laje mais alta: recomendada "
                      f"h ≈ {h_reco:.0f} cm (escolhida {h} cm). Considere "
                      f"altura maior ou vigota protendida.")

    # esforços característicos (exibição) e de cálculo (armadura, ×γf)
    if continua:
        cM, cMap = 1.0 / 10.0, 1.0 / 8.0
    else:
        cM, cMap = 1.0 / 8.0, 0.0
    M = p * lx ** 2 * cM                             # característico (vão)
    M_ap = p * lx ** 2 * cMap                        # característico (apoio)
    Md = pd * lx ** 2 * cM                           # de cálculo (vão)
    V = p * lx / 2.0

    # inércia da seção T homogeneizada (concreto bruto), por nervura
    bf = INTEREIXO                                   # m
    hf = capa / 100.0
    bw = LARG_NERVURA
    ht = h / 100.0
    A_fl = bf * hf
    A_web = bw * (ht - hf)
    A_t = A_fl + A_web
    y_fl = hf / 2.0
    y_web = hf + (ht - hf) / 2.0
    yc = (A_fl * y_fl + A_web * y_web) / A_t         # do topo
    I = (bf * hf ** 3 / 12.0 + A_fl * (yc - y_fl) ** 2
         + bw * (ht - hf) ** 3 / 12.0 + A_web * (yc - y_web) ** 2)
    I_m = I / bf                                      # por metro de largura
    Ecs = modulo_ecs(fck)

    # armadura de tração na nervura — seção T (mesa comprimida = capa, b=bf),
    # momento de CÁLCULO por nervura
    bf_cm = INTEREIXO * 100.0                         # 42 cm
    bw_cm = bw * 100.0                                # 9 cm
    d = h - 2.0 - 0.5
    As_nerv, xi, ok = as_flexao(Md * INTEREIXO * 100.0, bf_cm, d, fck)
    # As_min da nervura sobre a ÁREA BRUTA da seção T (capa + alma)
    Ac_rib = bf_cm * capa + bw_cm * (h - capa)       # cm² por nervura
    As_min_rib = (RHO_MIN.get(int(round(fck)), 0.15) / 100.0) * Ac_rib
    if As_nerv is not None:
        if xi is not None and 0.8 * xi * d > capa + 1e-6:
            avisos.append("Linha neutra abaixo da capa — seção T real; a "
                          "armadura da nervura pode estar subestimada.")
        if not ok:
            avisos.append(f"x/d = {xi:.2f} > 0,45 na nervura — pouca "
                          f"ductilidade; aumente a altura da laje.")
        As_nerv_adot = max(As_nerv, As_min_rib)
        As_por_m = As_nerv_adot / INTEREIXO
    else:
        As_nerv_adot = As_min_rib
        As_por_m = None
        avisos.append("Momento alto para a nervura (seção insuficiente) — "
                      "aumente a altura ou use vigota protendida.")

    # flecha: rigidez FISSURADA de Branson (por nervura), ELS quase-perm.
    delta_i_bruta = (5.0 / 384.0) * p_qp * lx ** 4 / (Ecs * I_m) * 1000.0
    if continua:
        delta_i_bruta *= 0.4                         # ~ contínua vs biapoiada
    Ecs_cm = Ecs * 1e-4
    Ic_cm = I * 1e8                                  # m⁴ (por nervura) -> cm⁴
    yt_cm = (ht - yc) * 100.0                        # fibra tracionada (base)
    Ma_rib = p_qp * lx ** 2 * cM * INTEREIXO * 100.0  # kN·cm por nervura
    fator_fis, Mr = fator_fissuracao(fck, Ic_cm, yt_cm, Ma_rib, As_nerv_adot,
                                     d, Ecs_cm, bf_cm, alfa=1.2)  # seção T
    delta_i = delta_i_bruta * fator_fis
    af = alfa_f(0.0)
    flecha = _classifica_flecha(delta_i, af * delta_i, lx)
    flecha["fator_fissuracao"] = fator_fis

    # cortante ELU sem estribos por nervura (NBR 6118 19.4.1)
    Vsd_rib = pd * lx / 2.0 * INTEREIXO              # kN por nervura
    VRd1_rib = vrd1(fck, bw_cm, d, As_nerv_adot)
    if Vsd_rib > VRd1_rib:
        avisos.append(f"Cortante Vsd={Vsd_rib:.1f} > VRd1={VRd1_rib:.1f} kN "
                      f"por nervura — aumente a altura (ou preveja estribos).")

    # reações: 2 vigas perpendiculares às vigotas <- p·lx/2 (kN/m)
    q_apoio = p * lx / 2.0
    q_apoio_d = pd * lx / 2.0
    # vigas paralelas (faixa marginal lx/4 -> p·lx/8)
    q_marg = p * lx / 8.0
    q_marg_d = pd * lx / 8.0

    # quantitativos
    area = lx * ly
    n_vigotas = math.ceil(ly / INTEREIXO)            # vigotas ao longo de ly
    comp_vigotas = n_vigotas * lx                    # m lineares
    vol_conc = area * (capa / 100.0
                       + (bw / bf) * (ht - hf))       # capa + nervuras
    n_element = math.ceil(area / (INTEREIXO * 0.25))  # blocos/EPS aprox

    return {
        "tipo": "trelicada", "lx": lx, "ly": ly, "h": h, "capa": capa,
        "enchimento": ench, "continua": continua,
        "g_pp": g_pp, "g_total": g_tot, "q_uso": q_uso, "p": p, "pd": pd,
        "h_reco": h_reco, "ok_vao": ok_vao, "p_qp": p_qp,
        "M": M, "M_ap": M_ap, "Md": Md, "V": V,
        "As_nerv": As_nerv, "As_por_m": As_por_m, "xi": xi,
        "flecha": flecha,
        "reacoes": {"principal_q": q_apoio, "principal_qd": q_apoio_d,
                    "marginal_q": q_marg, "marginal_qd": q_marg_d,
                    "L_principal": ly, "L_marginal": lx},
        "quant": {"area": area, "vol_conc": vol_conc, "n_vigotas": n_vigotas,
                  "comp_vigotas": comp_vigotas, "n_element": n_element},
        "Ecs": Ecs, "avisos": avisos, "erros": [],
    }


# ------------------------------------------------- comparativo pré x maciça
def comparativo(dados_base):
    """Compara treliçada x maciça para o mesmo pano. dados_base contém lx, ly,
    fck, g_rev, q_uso, g_parede e (opcional) h_macica, h_trelica, enchimento."""
    dm = dict(dados_base)
    dm["h"] = dados_base.get("h_macica", 10.0)
    dm.setdefault("apoios", {e: "apoiado" for e in BORDAS})
    rm = calcular_laje_macica(dm)
    dt = dict(dados_base)
    dt["h"] = dados_base.get("h_trelica", 16)
    dt["enchimento"] = dados_base.get("enchimento", "EPS")
    rt = calcular_laje_trelicada(dt)
    return {"macica": rm, "trelicada": rt}
