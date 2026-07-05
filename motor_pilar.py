# -*- coding: utf-8 -*-
"""
Motor de cálculo de pilares retangulares de concreto armado — NBR 6118.
Polotto Engenharia. Módulo PURO (sem Streamlit), testável.

Fluxo normativo implementado (auditoria 05/07/2026):
- Nd = γn·γf·Nk, com γn = 1,95 − 0,05·(menor dimensão) para b < 19 cm (Tab. 13.1)
- Esbeltez λ = 3,46·le/h_i nas DUAS direções (seção retangular)
- Momento mínimo de 1ª ordem M1d,min = Nd·(1,5 + 0,03·h_i) [kN·cm] (11.3.3.4.3)
- λ1 = 25 + 12,5·e1/h_i (αb = 1), limitado a 35 ≤ λ1 ≤ 90 (15.8.2)
- λ > λ1 → 2ª ordem pelo pilar-padrão com curvatura aproximada (15.8.3.3.2):
  e2 = (le²/10)·[0,005/(h_i·(ν+0,5))]
- λ > 90 → bloqueado (fora do método simplificado); λ > 200 proibido (15.8.1)
- Verificação em FLEXO-COMPRESSÃO por compatibilidade de deformações
  (bloco retangular 0,85·fcd·0,8x; pivôs B e C; aço elastoplástico)
- Arranjos: φ ≤ b/8 (18.4.2.1); espaçamento entre barras ≤ min(2b, 40) por
  face (18.4.2.2); espaçamento livre real do arranjo ≥ max(2; φ; 1,2·d_agr);
  As entre max(0,15·Nd/fyd; 0,4%Ac) e 4%Ac (17.3.5.3)
- Estribos: φt ≥ max(5; φ/4); s ≤ min(20; b; 12φ) (18.4.3)
"""
import math

GAMMA_F = 1.4
GAMMA_C = 1.4
GAMMA_S = 1.15
FYK = 50.0
FYD = FYK / GAMMA_S     # kN/cm²
ES = 21000.0            # kN/cm²
ECU = 0.0035            # deformação última do concreto (fck ≤ 50)
EC2 = 0.0020            # início do patamar (fck ≤ 50)

PESO_LINEAR = {5.0: 0.154, 6.3: 0.245, 8.0: 0.395, 10.0: 0.617,
               12.5: 0.963, 16.0: 1.578, 20.0: 2.466, 25.0: 3.853}
AREA_BITOLA = {5.0: 0.196, 6.3: 0.312, 8.0: 0.503, 10.0: 0.785,
               12.5: 1.227, 16.0: 2.011, 20.0: 3.142, 25.0: 4.909}
BITOLAS_LONG = [10.0, 12.5, 16.0, 20.0, 25.0]
D_MAX_AGREGADO = 1.9    # cm

COBRIMENTO_CAA = {'I': 2.5, 'II': 3.0, 'III': 4.0, 'IV': 5.0}  # Tab. 7.2


# ---------------------------------------------------------------- validação
def validar(dados):
    erros = []
    b, h = dados['b'], dados['h']
    fck, l0, Nk = dados['fck'], dados['l0'], dados['Nk']
    if min(b, h) < 14:
        erros.append("Menor dimensão %.0f cm < 14 cm — proibido pela "
                     "NBR 6118 (item 13.2.3)." % min(b, h))
    if b * h < 360:
        erros.append("Área da seção %.0f cm² < 360 cm² (mínimo do item "
                     "13.2.3)." % (b * h))
    if max(b, h) > 5 * min(b, h):
        erros.append("h/b = %.1f > 5: o elemento é PILAR-PAREDE (item "
                     "14.4.2.4) — fora do escopo deste programa."
                     % (max(b, h) / min(b, h)))
    if not (20 <= fck <= 50):
        erros.append("fck = %.0f MPa fora da faixa 20–50 MPa (grupo I)."
                     % fck)
    if l0 <= 0:
        erros.append("Altura livre l0 deve ser maior que zero.")
    if Nk <= 0:
        erros.append("Força normal Nk deve ser maior que zero.")
    lam_max = 3.46 * (l0 * 100.0) / min(b, h)
    if lam_max > 200:
        erros.append("Esbeltez λ = %.0f > 200 — proibido (item 15.8.1)."
                     % lam_max)
    elif lam_max > 90:
        erros.append("Esbeltez λ = %.0f > 90 — fora do método do pilar-"
                     "padrão com curvatura aproximada usado por este "
                     "programa. Aumente a seção ou reduza l0." % lam_max)
    return erros


# --------------------------------------------------- posições das barras
def posicoes_barras(n, phi_mm, b, h, cob, phi_t_mm):
    """Distribui n barras (n PAR): 4 nos cantos + pares nas duas faces
    MAIORES (mesma lógica do desenho). Retorna lista [(x, y)] em cm,
    origem no canto inferior esquerdo da seção b×h."""
    phi = phi_mm / 10.0
    phi_t = phi_t_mm / 10.0
    x0 = cob + phi_t + phi / 2.0
    x1 = b - x0
    y0 = cob + phi_t + phi / 2.0
    y1 = h - y0
    pos = [(x0, y0), (x1, y0), (x0, y1), (x1, y1)]
    pares = max(0, (n - 4) // 2)
    if pares:
        if h >= b:  # faces maiores são as verticais (x = x0 e x = x1)
            dy = (y1 - y0) / (pares + 1)
            for i in range(1, pares + 1):
                pos.append((x0, y0 + i * dy))
                pos.append((x1, y0 + i * dy))
        else:       # faces maiores são as horizontais (y = y0 e y = y1)
            dx = (x1 - x0) / (pares + 1)
            for i in range(1, pares + 1):
                pos.append((x0 + i * dx, y0))
                pos.append((x0 + i * dx, y1))
    return pos[:n]


def _check_espacamentos(pos, phi_mm, b, h):
    """Verifica espaçamento LIVRE mínimo e espaçamento MÁXIMO entre eixos
    de barras adjacentes na mesma face. Retorna (ok_min, ok_max)."""
    phi = phi_mm / 10.0
    s_min = max(2.0, phi, 1.2 * D_MAX_AGREGADO)
    s_max = min(2.0 * min(b, h), 40.0)
    ok_min, ok_max = True, True
    tol = 0.51
    # agrupa por face (mesma coordenada x ou y, com tolerância)
    for eixo in (0, 1):
        grupos = {}
        for p in pos:
            chave = round(p[eixo], 1)
            grupos.setdefault(chave, []).append(p[1 - eixo])
        for chave, vals in grupos.items():
            if len(vals) < 2:
                continue
            vals = sorted(vals)
            for v1, v2 in zip(vals, vals[1:]):
                gap_eixos = v2 - v1
                if gap_eixos - phi < s_min - 1e-9:
                    ok_min = False
                if gap_eixos > s_max + 1e-9:
                    ok_max = False
    # caso 4 barras: espaçamento máximo é a própria distância entre cantos
    if len(pos) == 4:
        xs = sorted({round(p[0], 1) for p in pos})
        ys = sorted({round(p[1], 1) for p in pos})
        if len(xs) == 2 and xs[1] - xs[0] > s_max:
            ok_max = False
        if len(ys) == 2 and ys[1] - ys[0] > s_max:
            ok_max = False
    return ok_min, ok_max


# ------------------------------------- flexo-compressão (compatibilidade)
def momento_resistente(b, h, barras, area, fck, Nd):
    """M_Rd (kN·cm) em torno do eixo horizontal (comprime o TOPO da seção
    de altura h), para a normal Nd. barras: profundidades y (cm) medidas do
    TOPO. Retorna -1 se a seção não equilibra Nd nem totalmente comprimida.
    Bloco retangular 0,85·fcd·0,8x; pivô B (x ≤ h) e pivô C (x > h)."""
    fcd = (fck / 10.0) / GAMMA_C
    scd = 0.85 * fcd

    def deform(y, x):
        if x <= h:                       # pivô B: eps_topo = ECU
            return ECU * (x - y) / x
        yc = (1.0 - EC2 / ECU) * h       # pivô C em 3h/7
        return EC2 * (x - y) / (x - yc)

    def esforcos(x):
        y_bloco = min(0.8 * x, h)
        Nc = scd * b * y_bloco
        Mc = Nc * (h / 2.0 - y_bloco / 2.0)
        N, M = Nc, Mc
        for y in barras:
            eps = deform(y, x)
            sig = max(-FYD, min(FYD, ES * eps))
            if eps > 0 and y <= y_bloco:
                sig -= scd                # desconta concreto deslocado
            F = area * sig
            N += F
            M += F * (h / 2.0 - y)
        return N, M

    x_lo, x_hi = 1e-4 * h, 40.0 * h
    N_hi, _ = esforcos(x_hi)
    if N_hi < Nd:                        # nem totalmente comprimida resiste
        return -1.0
    N_lo, _ = esforcos(x_lo)
    if N_lo > Nd:                        # Nd menor que capacidade mínima —
        return -1.0                      # não ocorre em pilar comprimido
    for _ in range(80):                  # bisseção
        xm = 0.5 * (x_lo + x_hi)
        Nm, Mm = esforcos(xm)
        if Nm < Nd:
            x_lo = xm
        else:
            x_hi = xm
    _, M = esforcos(0.5 * (x_lo + x_hi))
    return max(0.0, M)


# --------------------------------------------------------------- principal
def calcular_pilar(dados):
    """dados: {'b','h','l0'(m),'fck','Nk','caa'}.

    Retorna {'erros': [...]} ou dict completo com opções válidas de armadura
    (ordenadas por peso), esforços e verificações.
    """
    erros = validar(dados)
    if erros:
        return {'erros': erros}

    b, h = float(dados['b']), float(dados['h'])
    l0 = float(dados['l0'])
    fck = float(dados['fck'])
    Nk = float(dados['Nk'])
    caa = dados.get('caa', 'II')
    cob = COBRIMENTO_CAA.get(caa, 3.0)

    dim_min = min(b, h)
    gamma_n = 1.95 - 0.05 * dim_min if dim_min < 19.0 else 1.0
    Nd = Nk * GAMMA_F * gamma_n
    fcd = (fck / 10.0) / GAMMA_C
    Ac = b * h
    ni = Nd / (Ac * fcd)
    le = l0 * 100.0  # cm (le = l0 adotado; ver aviso)

    # ------- esforços de 2ª ordem por DIREÇÃO (x: dimensão b; y: dimensão h)
    direcoes = {}
    for nome, h_i in (('x', b), ('y', h)):
        lam = 3.46 * le / h_i
        M1d_min = Nd * (1.5 + 0.03 * h_i)          # kN·cm (11.3.3.4.3)
        e1 = M1d_min / Nd                           # cm
        lam1 = 25.0 + 12.5 * e1 / h_i               # αb = 1
        lam1 = min(max(lam1, 35.0), 90.0)
        if lam > lam1:
            curv = min(0.005 / (h_i * (ni + 0.5)), 0.005 / h_i)  # 1/cm
            e2 = (le ** 2 / 10.0) * curv            # cm
        else:
            e2 = 0.0
        Md_tot = M1d_min + Nd * e2                  # kN·cm (αb = 1)
        direcoes[nome] = {'h_i': h_i, 'lambda': lam, 'lambda1': lam1,
                          'M1d_min': M1d_min, 'e2': e2, 'Md_tot': Md_tot,
                          'segunda_ordem': lam > lam1}

    # ------- limites de armadura
    As_min = max(0.15 * Nd / FYD, 0.004 * Ac)       # 17.3.5.3.1/2
    As_max = 0.04 * Ac                              # 17.3.5.3.2 (fora emenda)

    # ------- busca de arranjos válidos
    opcoes = []
    phi_max_mm = dim_min * 10.0 / 8.0               # φ ≤ b/8 (18.4.2.1)
    for phi in BITOLAS_LONG:
        if phi < 10.0 or phi > phi_max_mm:
            continue
        area = AREA_BITOLA[phi]
        phi_t = max(5.0, phi / 4.0)                 # estribo (18.4.3)
        for n in range(4, 21, 2):                   # pares, 4 a 20
            As_ef = n * area
            if As_ef < As_min - 1e-9:
                continue
            if As_ef > As_max + 1e-9:
                break
            pos = posicoes_barras(n, phi, b, h, cob, phi_t)
            ok_min, ok_max = _check_espacamentos(pos, phi, b, h)
            if not ok_min or not ok_max:
                continue
            # ---- verificação em flexo-compressão nas duas direções
            aprovado = True
            folgas = {}
            for nome in ('x', 'y'):
                dd = direcoes[nome]
                if nome == 'y':
                    # flexão em torno do eixo x: profundidade na dimensão h
                    barras_y = [h - p[1] for p in pos]
                    MRd = momento_resistente(b, h, barras_y, area, fck, Nd)
                else:
                    # flexão em torno do eixo y: profundidade na dimensão b
                    barras_y = [b - p[0] for p in pos]
                    MRd = momento_resistente(h, b, barras_y, area, fck, Nd)
                if MRd < dd['Md_tot'] - 1e-6:
                    aprovado = False
                    break
                folgas[nome] = MRd / dd['Md_tot'] if dd['Md_tot'] > 0 else 9.9
            if not aprovado:
                continue
            # ---- estribos e pesos
            s_est = min(20.0, b, h, 12.0 * phi / 10.0)
            comp_barra = l0 + 40.0 * (phi / 10.0) / 100.0
            peso_long = n * comp_barra * PESO_LINEAR[phi]
            n_est = int(math.ceil(l0 * 100.0 / s_est)) + 1
            comp_est = (2.0 * ((b - 2 * cob) + (h - 2 * cob)) + 10.0) / 100.0
            phi_t_com = min(BITOLAS_ESTRIBO_VALIDAS(phi_t))
            peso_est = n_est * comp_est * PESO_LINEAR[phi_t_com]
            opcoes.append({'n': n, 'phi': phi, 'As_ef': As_ef,
                           'texto': '%d ø%.1f mm' % (n, phi),
                           'pos': pos, 'folga_x': folgas['x'],
                           'folga_y': folgas['y'],
                           'phi_t': phi_t_com, 's_est': s_est,
                           'n_est': n_est, 'comp_barra': comp_barra,
                           'comp_est': comp_est,
                           'peso_long': peso_long, 'peso_est': peso_est,
                           'peso_total': peso_long + peso_est})
            break  # menor n desta bitola já achado — próxima bitola

    opcoes.sort(key=lambda o: o['peso_total'])

    avisos = [
        "le adotado igual a l0 (altura livre). Se a vinculação real "
        "conduzir a le maior, refaça com l0 = le.",
        "Momento mínimo M1d,min aplicado nas duas direções "
        "(não simultaneamente), com αb = 1,0.",
        "Comprimento de corte = l0 + 40φ (estimativa de arranque/traspasse) "
        "— detalhar emendas conforme itens 9.4/9.5 da NBR 6118.",
        "Flexão oblíqua composta, cargas horizontais e momentos aplicados "
        "não são considerados — pilar interno de pórtico contraventado.",
    ]
    if gamma_n > 1.0:
        avisos.insert(0, "Menor dimensão %.0f cm < 19 cm → γn = %.2f "
                         "aplicado (Tabela 13.1)." % (dim_min, gamma_n))

    return {'dados': {'b': b, 'h': h, 'l0': l0, 'fck': fck, 'Nk': Nk,
                      'caa': caa, 'cob': cob},
            'Nd': Nd, 'gamma_n': gamma_n, 'ni': ni,
            'direcoes': direcoes,
            'As_min': As_min, 'As_max': As_max,
            'opcoes': opcoes, 'avisos': avisos}


def BITOLAS_ESTRIBO_VALIDAS(phi_t_min):
    """Menor bitola comercial de estribo >= phi_t_min (mm)."""
    return [p for p in (5.0, 6.3, 8.0, 10.0) if p >= phi_t_min - 1e-9]
