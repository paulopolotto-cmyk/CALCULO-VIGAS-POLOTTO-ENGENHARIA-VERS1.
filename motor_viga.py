# -*- coding: utf-8 -*-
"""
Motor de cálculo de vigas contínuas de concreto armado — NBR 6118.
Polotto Engenharia.

Módulo PURO (sem Streamlit) para permitir testes automatizados.
Convenção: 'a' é sempre a distância da carga concentrada medida a partir da
extremidade ESQUERDA do tramo (em todos os tipos de tramo).

Correções implementadas nesta versão (auditoria 05/07/2026):
- Equação dos Três Momentos com termos de carga concentrada corretos por lado:
  vão à esquerda do apoio usa P·a·b·(L+a)/(6L); à direita usa P·a·b·(L+b)/(6L)
- Momentos de engaste dos balanços com braços de alavanca corretos
- Momento positivo máximo REAL (varredura do diagrama M(x)), não o do meio do vão
- Estribos dimensionados com o cortante real de cada tramo (inclui P,
  continuidade e balanços)
- Flexão com sigma_cd = 0,85·fcd (NBR 6118, 17.2.2)
- As_min pela Tabela 17.3 (taxa cresce com fck)
- Vrd2 = 0,27·alfa_v2·fcd·bw·d sem fator espúrio (Modelo I, 17.4.2.2)
- Taxa mínima de estribos com fywk (não fyd)
- Espaçamento máximo com a condição 0,67·Vrd2 (18.3.3.2) e mínimo construtivo
- Escolha de bitolas que verifica se as barras cabem na largura (18.3.2.2)
- Comprimento das barras negativas calculado por apoio (decalagem + lb)
- Quantitativo por posição real (todos os vãos/apoios/balanços), pesos corretos
- Validações completas de entrada (0 <= a <= L, L > 0, fck 20-50, bw >= 12...)
"""
import math

import numpy as np

# ---------------------------------------------------------------- constantes
GAMMA_F = 1.4   # majoração de ações
GAMMA_C = 1.4   # minoração do concreto
GAMMA_S = 1.15  # minoração do aço

FYK = 50.0            # kN/cm² — CA-50
FYD = FYK / GAMMA_S   # 43,48 kN/cm²
FYWK = 50.0           # kN/cm² — estribos CA-50
ES = 21000.0          # kN/cm² — módulo do aço (Es = 210 GPa, item 8.3.5)

PESO_LINEAR = {5.0: 0.154, 6.3: 0.245, 8.0: 0.395, 10.0: 0.617,
               12.5: 0.963, 16.0: 1.578, 20.0: 2.466, 25.0: 3.853}   # kg/m
AREA_BITOLA = {5.0: 0.196, 6.3: 0.312, 8.0: 0.503, 10.0: 0.785,
               12.5: 1.227, 16.0: 2.011, 20.0: 3.142, 25.0: 4.909}   # cm²
BITOLAS_LONG = [10.0, 12.5, 16.0, 20.0]
BITOLAS_ESTRIBO = [5.0, 6.3, 8.0]
D_MAX_AGREGADO = 1.9   # cm (brita 1 / 19 mm)
GANCHO_ESTRIBO = 10.0  # cm somados ao corte de cada estribo (2 ganchos)

# Tabela 17.3 da NBR 6118 — taxa mínima de armadura de flexão (%)
RHO_MIN = [(20, 0.150), (25, 0.150), (30, 0.150), (35, 0.164),
           (40, 0.179), (45, 0.194), (50, 0.208)]


# ---------------------------------------------------------------- validação
def validar(dados, tramos):
    """Valida dados gerais e tramos. Retorna lista de erros (vazia se ok)."""
    erros = []
    b, h, fck = dados['b'], dados['h'], dados['fck']
    cob = dados.get('cob', 2.5)

    if b < 12:
        erros.append("Base bw = %.0f cm é menor que o mínimo da norma "
                     "(bw ≥ 12 cm — NBR 6118, item 13.2.2)." % b)
    if not (20 <= fck <= 50):
        erros.append("fck = %.0f MPa fora da faixa coberta pelo programa "
                     "(20 a 50 MPa — grupo I da NBR 6118)." % fck)
    if h < cob + 10:
        erros.append("Altura h = %.0f cm muito pequena para o cobrimento "
                     "de %.1f cm." % (h, cob))
    if not (2.0 <= cob <= 5.0):
        erros.append("Cobrimento c = %.1f cm fora da faixa usual "
                     "(2,0 a 5,0 cm — Tabela 7.2 da NBR 6118)." % cob)

    normais = [t for t in tramos if t['tipo'] == 'Normal']
    bal_e = [t for t in tramos if t['tipo'] == 'Balanço Esquerdo']
    bal_d = [t for t in tramos if t['tipo'] == 'Balanço Direito']

    if len(normais) < 1:
        erros.append("A viga precisa de pelo menos 1 vão normal entre apoios.")
    if len(bal_e) > 1:
        erros.append("Só é permitido UM balanço esquerdo (há %d)." % len(bal_e))
    if len(bal_d) > 1:
        erros.append("Só é permitido UM balanço direito (há %d)." % len(bal_d))

    for t in tramos:
        nome = t.get('nome', t['tipo'])
        if t['L'] <= 0:
            erros.append("%s: comprimento L deve ser maior que zero." % nome)
        if t['q'] < 0:
            erros.append("%s: carga distribuída q não pode ser negativa." % nome)
        if t['P'] < 0:
            erros.append("%s: carga concentrada P não pode ser negativa." % nome)
        if t['P'] > 0 and not (0 <= t['a'] <= t['L']):
            erros.append("%s: a posição da carga (a = %.2f m) precisa estar "
                         "dentro do tramo (0 ≤ a ≤ %.2f m)."
                         % (nome, t['a'], t['L']))
    return erros


# ---------------------------------------------------------------- estática
def _rot_como_vao_esquerdo(v):
    """Termo de Clapeyron do vão quando ele fica à ESQUERDA do apoio:
    rotação na extremidade direita do vão isostático → P·a·b·(L+a)/(6L)."""
    L, q, P, a = v['L'], v['q'], v['P'], v['a']
    b_ = L - a
    termo_q = q * L ** 3 / 24.0
    termo_p = P * a * b_ * (L + a) / (6.0 * L) if P > 0 else 0.0
    return termo_q + termo_p


def _rot_como_vao_direito(v):
    """Termo de Clapeyron do vão quando ele fica à DIREITA do apoio:
    rotação na extremidade esquerda do vão isostático → P·a·b·(L+b)/(6L)."""
    L, q, P, a = v['L'], v['q'], v['P'], v['a']
    b_ = L - a
    termo_q = q * L ** 3 / 24.0
    termo_p = P * a * b_ * (L + b_) / (6.0 * L) if P > 0 else 0.0
    return termo_q + termo_p


def resolver_estatica(vaos, bal_esq=None, bal_dir=None, n_pontos=501):
    """Resolve a viga contínua (Equação dos Três Momentos).

    vaos: lista de dicts {'L','q','P','a'} (vãos normais, esq→dir)
    bal_esq / bal_dir: dict do balanço ou None.
    Retorna dict com momentos, reações, cortantes e diagramas.
    """
    n = len(vaos)

    # Momentos de engaste dos balanços — braços corretos:
    # balanço esquerdo: apoio na direita do tramo → braço do P é (L - a)
    # balanço direito:  apoio na esquerda do tramo → braço do P é a
    if bal_esq:
        be = bal_esq
        MA = -(be['q'] * be['L'] ** 2 / 2.0 + be['P'] * (be['L'] - be['a']))
    else:
        MA = 0.0
    if bal_dir:
        bd = bal_dir
        MZ = -(bd['q'] * bd['L'] ** 2 / 2.0 + bd['P'] * bd['a'])
    else:
        MZ = 0.0

    # Momentos nos apoios
    if n == 1:
        M_apoios = [MA, MZ]
    else:
        ni = n - 1  # apoios internos (incógnitas)
        A = np.zeros((ni, ni))
        B = np.zeros(ni)
        for i in range(ni):
            Le, Ld = vaos[i]['L'], vaos[i + 1]['L']
            A[i, i] = 2.0 * (Le + Ld)
            if i > 0:
                A[i, i - 1] = Le
            if i < ni - 1:
                A[i, i + 1] = Ld
            # vão i está à ESQUERDA do apoio i; vão i+1 à DIREITA
            B[i] = -6.0 * (_rot_como_vao_esquerdo(vaos[i])
                           + _rot_como_vao_direito(vaos[i + 1]))
        B[0] -= vaos[0]['L'] * MA
        B[-1] -= vaos[-1]['L'] * MZ
        M_sol = np.linalg.solve(A, B)
        M_apoios = [MA] + [float(m) for m in M_sol] + [MZ]

    # Esforços por vão (diagramas analíticos varridos em malha fina)
    reacoes = np.zeros(n + 1)
    info_vaos = []
    for i, v in enumerate(vaos):
        L, q, P, a = v['L'], v['q'], v['P'], v['a']
        Me, Md = M_apoios[i], M_apoios[i + 1]
        b_ = L - a
        V0 = q * L / 2.0 + (P * b_ / L if P > 0 else 0.0) + (Md - Me) / L
        Vfim_reac = q * L / 2.0 + (P * a / L if P > 0 else 0.0) + (Me - Md) / L

        xs = np.linspace(0.0, L, n_pontos)
        Mx = Me + V0 * xs - q * xs ** 2 / 2.0 - P * np.maximum(0.0, xs - a)
        Vx = V0 - q * xs - P * (xs > a).astype(float)

        M_pos = max(0.0, float(Mx.max()))
        x_pos = float(xs[int(Mx.argmax())])
        V_max = max(abs(V0), abs(Vfim_reac), float(np.abs(Vx).max()))

        reacoes[i] += V0
        reacoes[i + 1] += Vfim_reac
        info_vaos.append({'L': L, 'q': q, 'P': P, 'a': a,
                          'M_esq': Me, 'M_dir': Md,
                          'M_pos': M_pos, 'x_pos': x_pos,
                          'V_esq': V0, 'V_dir': Vfim_reac, 'V_max': V_max,
                          'xs': xs, 'Mx': Mx, 'Vx': Vx})

    # Balanços: cortante e diagramas
    info_be = None
    if bal_esq:
        be = bal_esq
        L, q, P, a = be['L'], be['q'], be['P'], be['a']
        reacoes[0] += q * L + P
        xs = np.linspace(0.0, L, n_pontos)
        # ponta livre em x=0, apoio em x=L
        Mx = -(q * xs ** 2 / 2.0 + P * np.maximum(0.0, xs - a))
        Vx = -(q * xs + P * (xs > a).astype(float))
        info_be = {'L': L, 'q': q, 'P': P, 'a': a,
                   'V_max': q * L + P, 'xs': xs, 'Mx': Mx, 'Vx': Vx}
    info_bd = None
    if bal_dir:
        bd = bal_dir
        L, q, P, a = bd['L'], bd['q'], bd['P'], bd['a']
        reacoes[-1] += q * L + P
        xs = np.linspace(0.0, L, n_pontos)
        # apoio em x=0, ponta livre em x=L
        Mx = -(q * (L - xs) ** 2 / 2.0 + P * np.where(xs <= a, a - xs, 0.0))
        Vx = q * (L - xs) + P * (xs < a).astype(float)
        info_bd = {'L': L, 'q': q, 'P': P, 'a': a,
                   'V_max': q * L + P, 'xs': xs, 'Mx': Mx, 'Vx': Vx}

    V_max_global = max([v['V_max'] for v in info_vaos]
                       + ([info_be['V_max']] if info_be else [])
                       + ([info_bd['V_max']] if info_bd else []))

    return {'M_apoios': M_apoios, 'Reacoes': [float(r) for r in reacoes],
            'vaos': info_vaos, 'bal_esq': info_be, 'bal_dir': info_bd,
            'V_max': V_max_global}


# ------------------------------------------------------------ flexão (ELU)
def altura_util(h, cob, phi_long_mm=12.5, phi_estribo_mm=5.0, camadas=1):
    """d = h - (cobrimento + estribo + centroide da armadura)."""
    phi = phi_long_mm / 10.0
    phi_t = phi_estribo_mm / 10.0
    ev = max(2.0, phi, 0.6 * D_MAX_AGREGADO)  # esp. livre vertical entre camadas
    if camadas == 1:
        centroide = phi / 2.0
    else:
        centroide = phi + ev / 2.0  # centroide de 2 camadas iguais
    return h - (cob + phi_t + centroide)


def rho_min_flexao(fck):
    """Taxa mínima (%) — Tabela 17.3 da NBR 6118, interpolada."""
    fcks = [p[0] for p in RHO_MIN]
    rhos = [p[1] for p in RHO_MIN]
    return float(np.interp(fck, fcks, rhos))


def as_flexao(Mk, b, d, h, fck):
    """Dimensiona As (cm²) para o momento característico Mk (kN·m).

    Retorna dict {'As','As_calc','kmd','xi','minima'} ou
    {'falha': 'kmd', 'kmd': ...} quando exige armadura dupla/redimensionar.
    """
    As_min = rho_min_flexao(fck) / 100.0 * b * h
    if abs(Mk) <= 0.05:
        return {'As': 0.0, 'As_calc': 0.0, 'kmd': 0.0, 'xi': 0.0,
                'minima': False}
    Md = abs(Mk) * 100.0 * GAMMA_F              # kN·m → kN·cm, majorado
    fcd = (fck / 10.0) / GAMMA_C                # kN/cm²
    sigma_cd = 0.85 * fcd                       # NBR 6118, 17.2.2
    kmd = Md / (b * d * d * sigma_cd)
    if kmd > 0.2952:                            # x/d = 0,45 (fck ≤ 50)
        return {'falha': 'kmd', 'kmd': kmd}
    xi = 1.25 * (1.0 - math.sqrt(1.0 - 2.0 * kmd))
    As_calc = Md / (d * (1.0 - 0.4 * xi) * FYD)
    As = max(As_calc, As_min)
    return {'As': As, 'As_calc': As_calc, 'kmd': kmd, 'xi': xi,
            'minima': As_calc < As_min}


def escolher_barras(As_req, b, cob, phi_estribo_mm=5.0):
    """Escolhe bitola/quantidade que CABE na largura da viga (18.3.2.2).

    Retorna dict {'n','phi','As_ef','camadas','texto','construtiva'} ou None.
    """
    if As_req <= 0:
        return {'n': 2, 'phi': 8.0, 'As_ef': 2 * AREA_BITOLA[8.0],
                'camadas': 1, 'construtiva': True, 'texto': '2 ø8.0 (constr.)'}
    phi_t = phi_estribo_mm / 10.0
    for camadas in (1, 2):
        for phi_mm in BITOLAS_LONG:
            area = AREA_BITOLA[phi_mm]
            n = max(2, int(math.ceil(As_req / area)))
            por_camada = int(math.ceil(n / camadas))
            phi = phi_mm / 10.0
            eh = max(2.0, phi, 1.2 * D_MAX_AGREGADO)
            largura = (2.0 * (cob + phi_t) + por_camada * phi
                       + (por_camada - 1) * eh)
            if largura <= b + 1e-9:
                extra = ' em 2 camadas' if camadas == 2 else ''
                return {'n': n, 'phi': phi_mm, 'As_ef': n * area,
                        'camadas': camadas, 'construtiva': False,
                        'texto': '%d ø%.1f%s' % (n, phi_mm, extra)}
    return None  # não cabe nem em 2 camadas — redimensionar seção


# ---------------------------------------------------------- cortante (ELU)
def dimensionar_estribos(Vk, b, d, fck):
    """Modelo de Cálculo I (NBR 6118, 17.4.2.2). Vk em kN (característico).

    Retorna dict com phi_t, s (cm), Vsd, Vrd2, Vc — ou {'falha_biela': True}.
    """
    Vsd = Vk * GAMMA_F
    fcd_mpa = fck / GAMMA_C
    alfa_v2 = 1.0 - fck / 250.0
    Vrd2 = 0.27 * alfa_v2 * (fcd_mpa / 10.0) * b * d   # kN
    if Vsd > Vrd2:
        return {'falha_biela': True, 'Vsd': Vsd, 'Vrd2': Vrd2}

    fctm = 0.3 * fck ** (2.0 / 3.0)          # MPa
    fctd = 0.7 * fctm / GAMMA_C              # MPa
    Vc = 0.6 * (fctd / 10.0) * b * d         # kN
    Vsw = max(0.0, Vsd - Vc)
    asw_nec = Vsw / (0.9 * d * FYD)                       # cm²/cm (2 ramos)
    asw_min = 0.2 * (fctm / 10.0) / FYWK * b              # 17.4.1.1.1 c/ fywk
    asw = max(asw_nec, asw_min)

    # Espaçamento máximo — 18.3.3.2
    if Vsd <= 0.67 * Vrd2:
        s_max = min(0.6 * d, 30.0)
    else:
        s_max = min(0.3 * d, 20.0)

    aviso = None
    escolhido = None
    for phi_t in BITOLAS_ESTRIBO:
        s = min(2.0 * AREA_BITOLA[phi_t] / asw, s_max)
        s = math.floor(s * 2.0) / 2.0  # arredonda p/ baixo em 0,5 cm
        if s >= 7.0:
            escolhido = (phi_t, s)
            break
    if escolhido is None:  # nem ø8.0 c/7 atende — usa ø8 e avisa
        phi_t = BITOLAS_ESTRIBO[-1]
        s = math.floor(min(2.0 * AREA_BITOLA[phi_t] / asw, s_max) * 2.0) / 2.0
        escolhido = (phi_t, max(s, 3.0))
        aviso = ("Espaçamento menor que 7 cm — de difícil execução. "
                 "Considere aumentar a seção ou usar estribos de 4 ramos.")
    phi_t, s = escolhido
    return {'falha_biela': False, 'phi_t': phi_t, 's': s,
            'Vsd': Vsd, 'Vrd2': Vrd2, 'Vc': Vc,
            'asw_cm2_m': asw * 100.0, 'aviso': aviso,
            'texto': 'ø%.1f c/%.0f cm' % (phi_t, s)}


# ----------------------------------------------------------- ancoragem / lb
def comprimento_ancoragem(phi_mm, fck, boa_aderencia=True):
    """lb reto (m) — NBR 6118, 9.4.2.4 (barra nervurada, sem redução)."""
    fctm = 0.3 * fck ** (2.0 / 3.0)                       # MPa
    fctd = 0.7 * fctm / GAMMA_C                           # MPa
    eta2 = 1.0 if boa_aderencia else 0.7
    fbd = 2.25 * eta2 * fctd                              # MPa
    fbd_kncm2 = fbd / 10.0
    lb_cm = (phi_mm / 10.0) / 4.0 * (FYD / fbd_kncm2)
    return lb_cm / 100.0                                  # m


# --------------------------------------------------------- flecha (ELS)
def modulo_secante(fck, alfa_e_agreg=1.0):
    """Módulo de elasticidade secante Ecs (kN/cm²) — NBR 6118, item 8.2.8.

    alfa_e_agreg: 1,2 basalto · 1,0 granito/gnaisse (padrão) · 0,9 calcário
    · 0,7 arenito.
    """
    eci = alfa_e_agreg * 5600.0 * math.sqrt(fck)     # MPa
    alfa_i = min(0.8 + 0.2 * fck / 80.0, 1.0)
    ecs = alfa_i * eci                               # MPa
    return ecs / 10.0                                # kN/cm²


def _cumint(f, x):
    """Integral cumulativa por trapézios (F[0] = 0)."""
    incr = (f[:-1] + f[1:]) / 2.0 * np.diff(x)
    return np.concatenate(([0.0], np.cumsum(incr)))


def inercia_estadio2(b, d, As, alfa_e):
    """Inércia da seção fissurada (Estádio II), retangular armadura simples."""
    ae_as = alfa_e * As
    x2 = (-ae_as + math.sqrt(ae_as ** 2 + 2.0 * b * ae_as * d)) / b
    i2 = b * x2 ** 3 / 3.0 + ae_as * (d - x2) ** 2
    return i2, x2


def verificar_flecha(res, alfa_f=1.32, alfa_e_agreg=1.0):
    """Verificação de flecha (ELS-DEF) — NBR 6118, item 17.3.2.

    - Rigidez equivalente pela fórmula de Branson (17.3.2.1.1).
    - Flecha imediata por integração do diagrama M(x) (relativa à corda do
      vão); balanços pela flecha da ponta (base engastada, estimativa).
    - Flecha diferida pelo fator alfa_f (padrão 1,32, sem armadura de
      compressão, carga aos ~30 dias).
    - Limite L/250 (aceitabilidade visual, Tabela 13.3); contra-flecha
      limitada a L/350.
    Carga de serviço = carga total característica (conservador — trata tudo
    como quase-permanente, pois o app não separa g de q).
    Retorna dict com resultados por vão e por balanço.
    """
    d = res['dados']
    b, h, fck, dd = d['b'], d['h'], d['fck'], d['d']
    est = res['estatica']

    Ecs = modulo_secante(fck, alfa_e_agreg)          # kN/cm²
    alfa_e = ES / Ecs
    Ic = b * h ** 3 / 12.0                            # cm⁴
    yt = h / 2.0
    fctm = 0.3 * fck ** (2.0 / 3.0)                   # MPa
    Mr = 1.5 * (fctm / 10.0) * Ic / yt               # kN·cm (α=1,5; fct=fctm)
    EIc = Ecs * Ic

    def ei_equivalente(Ma_kNcm, As):
        """(EI)eq (kN·cm²) e estádio, dado o momento de serviço e As."""
        if Ma_kNcm <= Mr or As <= 0:
            return EIc, 'I (não fissura)'
        i2, _ = inercia_estadio2(b, dd, As, alfa_e)
        r = (Mr / Ma_kNcm) ** 3
        ieq = min(r * Ic + (1.0 - r) * i2, Ic)
        return Ecs * ieq, 'II (fissurado)'

    def resultado(nome, L_m, Lref_m, fi_cm, EI, estadio, Ma_kNcm):
        fi = fi_cm * 10.0                            # mm (imediata)
        ft = fi * (1.0 + alfa_f)                     # mm (total c/ fluência)
        lim = Lref_m * 1000.0 / 250.0               # mm (L/250 — visual)
        # limite p/ alvenaria (Tab. 13.3): L/500 ≤ 10 mm (conservador: usa ft)
        lim_alv = min(Lref_m * 1000.0 / 500.0, 10.0)
        ok = ft <= lim
        cf = 0.0
        residual = ft
        resolve = True
        if not ok:
            cf_max = Lref_m * 1000.0 / 350.0
            cf = min(ft, cf_max)
            residual = ft - cf
            resolve = residual <= lim
        return {'nome': nome, 'L': L_m, 'estadio': estadio,
                'Ma': Ma_kNcm / 100.0, 'Mr': Mr / 100.0,
                'flecha_imediata_mm': fi, 'flecha_total_mm': ft,
                'limite_mm': lim, 'ok': ok,
                'limite_alv_mm': lim_alv, 'ok_alv': ft <= lim_alv,
                'contra_flecha_mm': cf, 'residual_mm': residual,
                'resolve_com_cf': resolve}

    vaos_out = []
    for i, v in enumerate(est['vaos']):
        sel = res['flex_vaos'][i].get('sel')
        As = sel['As_ef'] if sel else 0.0
        Ma = v['M_pos'] * 100.0                      # kN·cm
        EI, estadio = ei_equivalente(Ma, As)
        # flecha imediata: dupla integração de y'' = -M/EI (relativa à corda)
        x = v['xs'] * 100.0                          # cm
        ypp = -(v['Mx'] * 100.0) / EI
        y = _cumint(_cumint(ypp, x), x)
        y = y - (y[-1] / x[-1]) * x                  # impõe y(0)=y(L)=0
        fi_cm = float(max(0.0, y.max()))             # flecha p/ baixo (cm)
        vaos_out.append(resultado(f"Vão {i + 1}", v['L'], v['L'], fi_cm,
                                  EI, estadio, Ma))

    bal_out = []
    for lado, info, ap_idx in (('Balanço esq.', est['bal_esq'], 0),
                               ('Balanço dir.', est['bal_dir'], -1)):
        if not info:
            continue
        sel = res['flex_apoios'][ap_idx].get('sel')
        As = sel['As_ef'] if (sel and not sel.get('construtiva')) else 0.0
        Ma = abs(est['M_apoios'][ap_idx]) * 100.0    # kN·cm (momento no apoio)
        EI, estadio = ei_equivalente(Ma, As)
        # flecha da ponta por trabalho virtual (base engastada no apoio)
        x = info['xs'] * 100.0
        L = info['L'] * 100.0
        # distância de cada seção até a PONTA livre
        if lado == 'Balanço esq.':                   # ponta em x=0
            braco = x
        else:                                        # ponta em x=L
            braco = L - x
        integrando = np.abs(info['Mx'] * 100.0) * braco / EI
        fi_cm = float(np.sum((integrando[:-1] + integrando[1:]) / 2.0
                             * np.diff(x)))          # cm (trabalho virtual)
        bal_out.append(resultado(lado, info['L'], 2.0 * info['L'], fi_cm,
                                 EI, estadio, Ma))

    return {'Ecs_MPa': Ecs * 10.0, 'alfa_e': alfa_e, 'alfa_f': alfa_f,
            'Mr_kNm': Mr / 100.0, 'vaos': vaos_out, 'balancos': bal_out}


# --------------------------------------------------------------- principal
def calcular_viga(dados, tramos):
    """Pipeline completo. dados: {'b','h','fck','cob','peso_proprio'(bool)}.

    Retorna dict com estática, dimensionamento, quantitativo e avisos —
    ou {'erros': [...]} se a entrada for inválida.
    """
    erros = validar(dados, tramos)
    if erros:
        return {'erros': erros}

    b, h, fck = float(dados['b']), float(dados['h']), float(dados['fck'])
    cob = float(dados.get('cob', 2.5))
    avisos = []

    # Peso próprio
    tramos_calc = []
    g_pp = 25.0 * (b * h) / 1e4  # kN/m (NBR 6120)
    incluir_pp = bool(dados.get('peso_proprio', True))
    for t in tramos:
        t2 = dict(t)
        if incluir_pp:
            t2['q'] = t['q'] + g_pp
        tramos_calc.append(t2)
    if incluir_pp:
        avisos.append("Peso próprio incluído automaticamente: "
                      "g = %.2f kN/m somado a cada tramo." % g_pp)
    else:
        avisos.append("Peso próprio NÃO incluído — confira se o q digitado "
                      "já o considera (g = %.2f kN/m)." % g_pp)

    vaos = [t for t in tramos_calc if t['tipo'] == 'Normal']
    bal_e = [t for t in tramos_calc if t['tipo'] == 'Balanço Esquerdo']
    bal_d = [t for t in tramos_calc if t['tipo'] == 'Balanço Direito']
    est = resolver_estatica(vaos, bal_e[0] if bal_e else None,
                            bal_d[0] if bal_d else None)

    # ---- flexão: altura útil com estimativa e refinamento p/ 2 camadas
    d = altura_util(h, cob)
    flex_apoios, flex_vaos = [], []
    falha_flexao = False

    def _dimensionar(Mk):
        nonlocal falha_flexao
        r = as_flexao(Mk, b, d, h, fck)
        if 'falha' in r:
            falha_flexao = True
            return {'falha': True, 'Mk': Mk, 'kmd': r['kmd'], 'sel': None,
                    'As': None}
        sel = escolher_barras(r['As'], b, cob)
        if sel is None:
            falha_flexao = True
            return {'falha': True, 'Mk': Mk, 'kmd': r['kmd'], 'sel': None,
                    'As': r['As'],
                    'motivo': 'barras não cabem na largura da viga'}
        if sel['camadas'] == 2:
            # recalcula com d reduzido pelas 2 camadas
            d2 = altura_util(h, cob, phi_long_mm=sel['phi'], camadas=2)
            r2 = as_flexao(Mk, b, d2, h, fck)
            if 'falha' in r2:
                falha_flexao = True
                return {'falha': True, 'Mk': Mk, 'kmd': r2['kmd'],
                        'sel': None, 'As': None}
            sel2 = escolher_barras(r2['As'], b, cob)
            if sel2 is None:
                falha_flexao = True
                return {'falha': True, 'Mk': Mk, 'kmd': r2['kmd'],
                        'sel': None, 'As': r2['As'],
                        'motivo': 'barras não cabem na largura da viga'}
            return {'falha': False, 'Mk': Mk, 'As': r2['As'], 'sel': sel2,
                    'kmd': r2['kmd'], 'minima': r2['minima']}
        return {'falha': False, 'Mk': Mk, 'As': r['As'], 'sel': sel,
                'kmd': r['kmd'], 'minima': r['minima']}

    for m in est['M_apoios']:
        flex_apoios.append(_dimensionar(m))
    for v in est['vaos']:
        flex_vaos.append(_dimensionar(v['M_pos']))

    # ---- cortante / estribos por tramo (cortante REAL de cada tramo)
    estribos = []          # um por vão normal
    falha_biela = False
    for v in est['vaos']:
        e = dimensionar_estribos(v['V_max'], b, d, fck)
        if e.get('falha_biela'):
            falha_biela = True
        estribos.append(e)
    estribo_be = estribo_bd = None
    if est['bal_esq']:
        estribo_be = dimensionar_estribos(est['bal_esq']['V_max'], b, d, fck)
        if estribo_be.get('falha_biela'):
            falha_biela = True
    if est['bal_dir']:
        estribo_bd = dimensionar_estribos(est['bal_dir']['V_max'], b, d, fck)
        if estribo_bd.get('falha_biela'):
            falha_biela = True

    # ---- armadura de pele (17.3.5.2.3) — 0,10% POR FACE
    pele = None
    if h > 60.0:
        as_face = 0.0010 * b * h
        pele = {'As_face': as_face, 'As_total': 2 * as_face,
                'texto': ("%.2f cm² POR FACE (total %.2f cm²), "
                          "espaçamento ≤ 20 cm e ≤ d/3"
                          % (as_face, 2 * as_face))}

    # ---- avisos de escopo (limitações declaradas)
    avisos.append("Análise com caso ÚNICO de carga — alternância de "
                  "sobrecarga entre vãos (envoltória) não considerada.")
    avisos.append("Flecha (ELS-DEF) verificada na seção 'Flecha'. Abertura "
                  "de fissuras (ELS-W, item 17.3.3) NÃO verificada.")

    resultado = {
        'dados': {'b': b, 'h': h, 'fck': fck, 'cob': cob, 'd': d,
                  'g_pp': g_pp if incluir_pp else 0.0},
        'estatica': est,
        'flex_apoios': flex_apoios, 'flex_vaos': flex_vaos,
        'estribos': estribos, 'estribo_be': estribo_be,
        'estribo_bd': estribo_bd,
        'pele': pele,
        'falha_flexao': falha_flexao, 'falha_biela': falha_biela,
        'avisos': avisos,
        'quantitativo': None,
    }

    # ---- quantitativo — SÓ se nada falhou (nunca listar viga reprovada)
    if not falha_flexao and not falha_biela:
        resultado['quantitativo'] = _quantitativo(
            resultado, vaos, bal_e[0] if bal_e else None,
            bal_d[0] if bal_d else None)
    return resultado


# -------------------------------------------------------------- quantitativo
def _quantitativo(res, vaos, bal_e, bal_d):
    """Lista de posições reais (por vão/apoio/balanço) + lista de compra."""
    b = res['dados']['b']
    h = res['dados']['h']
    fck = res['dados']['fck']
    cob = res['dados']['cob']
    d = res['dados']['d']
    est = res['estatica']

    posicoes = []
    npos = 0

    # N: positivos — uma posição por vão
    for i, (v, fx) in enumerate(zip(est['vaos'], res['flex_vaos'])):
        sel = fx['sel']
        lb = comprimento_ancoragem(sel['phi'], fck, boa_aderencia=True)
        comp = v['L'] + 2 * lb
        npos += 1
        posicoes.append({'pos': 'N%d' % npos,
                         'descr': 'Positivo — Vão %d' % (i + 1),
                         'phi': sel['phi'], 'qtd': sel['n'],
                         'comp_unit': comp, 'vao': i,
                         'peso': sel['n'] * comp * PESO_LINEAR[sel['phi']]})

    # N: negativos — uma posição por apoio com As > 0
    n_ap = len(est['M_apoios'])
    for j in range(n_ap):
        fx = res['flex_apoios'][j]
        sel = fx['sel']
        if sel is None or sel.get('construtiva'):
            continue
        L_esq_v = est['vaos'][j - 1]['L'] if j > 0 else 0.0
        L_dir_v = est['vaos'][j]['L'] if j < len(est['vaos']) else 0.0
        lb = comprimento_ancoragem(sel['phi'], fck, boa_aderencia=False)
        al = 0.5 * d / 100.0  # decalagem (m)
        comp = 0.25 * (L_esq_v + L_dir_v) + 2 * (al + lb)
        # balanço: a barra negativa cobre o balanço inteiro
        if j == 0 and est['bal_esq']:
            comp = est['bal_esq']['L'] + 0.25 * L_dir_v + al + lb
        if j == n_ap - 1 and est['bal_dir']:
            comp = est['bal_dir']['L'] + 0.25 * L_esq_v + al + lb
        npos += 1
        posicoes.append({'pos': 'N%d' % npos,
                         'descr': 'Negativo — Apoio %s' % chr(65 + j),
                         'phi': sel['phi'], 'qtd': sel['n'],
                         'comp_unit': comp, 'apoio': j,
                         'peso': sel['n'] * comp * PESO_LINEAR[sel['phi']]})

    # N: porta-estribos — comprimento total da viga (balanços incluídos)
    L_total = (sum(v['L'] for v in est['vaos'])
               + (est['bal_esq']['L'] if est['bal_esq'] else 0.0)
               + (est['bal_dir']['L'] if est['bal_dir'] else 0.0))
    npos += 1
    comp_pe = L_total + 0.30
    posicoes.append({'pos': 'N%d' % npos, 'descr': 'Porta-estribos',
                     'phi': 8.0, 'qtd': 2, 'comp_unit': comp_pe,
                     'peso': 2 * comp_pe * PESO_LINEAR[8.0]})

    # N: estribos — por tramo (vãos E balanços), corte com cobrimento real
    comp_estribo = (2.0 * ((b - 2 * cob) + (h - 2 * cob))
                    + GANCHO_ESTRIBO) / 100.0  # m
    tramos_est = []
    for i, (v, e) in enumerate(zip(est['vaos'], res['estribos'])):
        tramos_est.append(('Vão %d' % (i + 1), v['L'], e))
    if est['bal_esq'] and res['estribo_be']:
        tramos_est.append(('Balanço esq.', est['bal_esq']['L'],
                           res['estribo_be']))
    if est['bal_dir'] and res['estribo_bd']:
        tramos_est.append(('Balanço dir.', est['bal_dir']['L'],
                           res['estribo_bd']))
    for nome, L, e in tramos_est:
        n_est = int(math.ceil(L * 100.0 / e['s'])) + 1
        npos += 1
        posicoes.append({'pos': 'N%d' % npos,
                         'descr': 'Estribos — %s (%s)' % (nome, e['texto']),
                         'phi': e['phi_t'], 'qtd': n_est,
                         'comp_unit': comp_estribo,
                         'peso': n_est * comp_estribo
                                 * PESO_LINEAR[e['phi_t']]})

    peso_total = sum(p['peso'] for p in posicoes)

    # ---- lista de compra: agrupada por bitola, +10 %, barras de 12 m
    compra = {}
    avisos_compra = []
    for p in posicoes:
        phi = p['phi']
        compra.setdefault(phi, {'comp': 0.0, 'peso': 0.0})
        compra[phi]['comp'] += p['qtd'] * p['comp_unit']
        compra[phi]['peso'] += p['peso']
        if p['comp_unit'] > 12.0:
            avisos_compra.append(
                "%s: comprimento unitário %.2f m excede a barra comercial "
                "de 12 m — prever emenda por traspasse (acrescentar lb)."
                % (p['pos'], p['comp_unit']))
    lista_compra = []
    for phi in sorted(compra):
        c = compra[phi]
        comp_c = c['comp'] * 1.10
        lista_compra.append({'phi': phi,
                             'comp_total': c['comp'],
                             'comp_compra': comp_c,
                             'barras_12m': int(math.ceil(comp_c / 12.0)),
                             'peso_compra': c['peso'] * 1.10})
    peso_compra = sum(x['peso_compra'] for x in lista_compra)

    return {'posicoes': posicoes, 'peso_total': peso_total,
            'lista_compra': lista_compra, 'peso_compra': peso_compra,
            'comp_estribo': comp_estribo, 'avisos': avisos_compra}
