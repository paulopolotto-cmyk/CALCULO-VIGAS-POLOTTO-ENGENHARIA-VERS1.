# -*- coding: utf-8 -*-
"""Testes do motor_pilar contra os números provados na auditoria."""
import sys
import os; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import motor_pilar as mp

OK = True
def check(nome, obtido, esperado, tol=1e-2):
    global OK
    ok = abs(obtido - esperado) <= tol
    if not ok:
        OK = False
    print(("PASS" if ok else "FAIL"), nome, "-> obtido=%.4f esperado=%.4f" % (obtido, esperado))

# ---- 1. Caso da auditoria: 14x40, l0=3.0, fck=30, Nk=400 (kN)
#         γn=1.25, Nd=700, λ=74.1, ν=0.583, e2=2.97cm, M1d,min=13.44 kN·m,
#         Md,tot=34.2 kN·m — e o antigo 4ø10 NÃO pode passar
r = mp.calcular_pilar({'b': 14, 'h': 40, 'l0': 3.0, 'fck': 30, 'Nk': 400, 'caa': 'II'})
assert 'erros' not in r, r.get('erros')
check("1a gamma_n", r['gamma_n'], 1.25)
check("1b Nd", r['Nd'], 700.0)
dx = r['direcoes']['x']  # direção fraca (b=14)
check("1c lambda_x", dx['lambda'], 74.14, tol=0.1)
check("1d ni", r['ni'], 0.5833, tol=1e-3)
check("1e e2_x (cm)", dx['e2'], 2.967, tol=0.02)
check("1f M1d,min_x (kN·cm)", dx['M1d_min'], 1344.0, tol=1.0)
check("1g Md,tot_x (kN·cm)", dx['Md_tot'], 3421.0, tol=10.0)
# A auditoria provou que este pilar exige ~21.7 cm² ≈ limite de 4% (22.4):
# com análise rigorosa NEM o máximo passa → a resposta correta é
# 'seção insuficiente' (o app antigo dava 4ø10, que ROMPERIA)
check("1h seção 14x40/Nk400 corretamente reprovada (sem opções)",
      0.0 if r['opcoes'] else 1.0, 1.0)
# verificação direta: MRd do 4ø10 na direção fraca deve ser < Md_tot
pos410 = mp.posicoes_barras(4, 10.0, 14, 40, 3.0, 5.0)
barras_prof = [14 - p[0] for p in pos410]
MRd_410 = mp.momento_resistente(40, 14, barras_prof, 0.785, 30, 700.0)
print("    MRd 4ø10 direção fraca = %.1f kN·cm (demanda %.0f)" % (MRd_410, dx['Md_tot']))
check("1i 4ø10 reprova", 1.0 if (MRd_410 < dx['Md_tot']) else 0.0, 1.0)

# ---- 2. Caso default antigo: 20x30, l0=2.8, fck=30, Nk=500
r2 = mp.calcular_pilar({'b': 20, 'h': 30, 'l0': 2.8, 'fck': 30, 'Nk': 500, 'caa': 'II'})
assert 'erros' not in r2, r2.get('erros')
check("2a gamma_n=1 (b=20>=19... espera 1.0)", r2['gamma_n'], 1.0)
check("2b lambda_x (le=280,b=20)", r2['direcoes']['x']['lambda'], 48.44, tol=0.1)
assert r2['opcoes'], "20x30 Nk=500 deveria ter opções"
print("    melhor opção 20x30:", r2['opcoes'][0]['texto'],
      "folga_x=%.2f folga_y=%.2f" % (r2['opcoes'][0]['folga_x'], r2['opcoes'][0]['folga_y']))

# ---- 3. γn pela MENOR dimensão (b=30, h=16 → γn = 1.95-0.05·16 = 1.15)
r3 = mp.calcular_pilar({'b': 30, 'h': 16, 'l0': 2.5, 'fck': 30, 'Nk': 300, 'caa': 'II'})
assert 'erros' not in r3, r3.get('erros')
check("3  gamma_n usa min(b,h)", r3['gamma_n'], 1.15)

# ---- 4. φ ≤ b/8: pilar b=15 → ø20 e ø25 proibidos nas opções
r4 = mp.calcular_pilar({'b': 15, 'h': 50, 'l0': 2.8, 'fck': 30, 'Nk': 800, 'caa': 'II'})
if 'erros' not in r4:
    phis = {o['phi'] for o in r4['opcoes']}
    print("    bitolas oferecidas p/ b=15:", sorted(phis))
    check("4  phi<=b/8 (nada acima de 18.75mm)",
          0.0 if any(p > 18.75 for p in phis) else 1.0, 1.0)

# ---- 5. Espaçamento máximo: 20x100 não pode aprovar só 4 barras nos cantos
r5 = mp.calcular_pilar({'b': 20, 'h': 100, 'l0': 2.8, 'fck': 30, 'Nk': 500, 'caa': 'II'})
if 'erros' not in r5:
    ns = {o['n'] for o in r5['opcoes']}
    print("    n de barras oferecidos p/ 20x100:", sorted(ns))
    check("5  20x100 exige mais que 4 barras (face de 92cm > 40cm)",
          0.0 if 4 in ns else 1.0, 1.0)

# ---- 6. λ > 90 bloqueado: 14x40 com l0=4.0 → λ=98.9
r6 = mp.calcular_pilar({'b': 14, 'h': 40, 'l0': 4.0, 'fck': 30, 'Nk': 300, 'caa': 'II'})
check("6  lambda>90 bloqueia", 1.0 if 'erros' in r6 else 0.0, 1.0)

# ---- 7. Pilar-parede bloqueado: 14x120 (h/b=8.6)
r7 = mp.calcular_pilar({'b': 14, 'h': 120, 'l0': 2.8, 'fck': 30, 'Nk': 300, 'caa': 'II'})
check("7  h/b>5 bloqueia", 1.0 if 'erros' in r7 else 0.0, 1.0)

# ---- 8. Sanidade do momento_resistente: flexão simples conhecida
#         b=20,h=50,C25, 3ø16 (6.03cm²) em d=46 → MRd ≈ As·fyd·0.9d ~ 108 kN·m
MRd = mp.momento_resistente(20, 50, [46.0, 46.0, 46.0], 2.011, 25, 0.0)
print("    MRd flexão simples 3ø16: %.0f kN·cm (~z·As·fyd=%.0f)" % (MRd, 6.03*43.48*0.9*46))
check("8  MRd flexão simples plausível", MRd, 6.03*43.48*46*0.9, tol=1200)

print()
print("RESULTADO:", "TODOS OS TESTES DO PILAR PASSARAM" if OK else "*** HÁ FALHAS ***")
