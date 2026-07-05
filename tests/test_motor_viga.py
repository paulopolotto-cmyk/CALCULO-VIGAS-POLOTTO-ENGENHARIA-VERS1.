# -*- coding: utf-8 -*-
"""Testes do motor_viga contra os casos exatos provados na auditoria."""
import sys
import os; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import motor_viga as mv

OK = True
def check(nome, obtido, esperado, tol=1e-3):
    global OK
    ok = abs(obtido - esperado) <= tol
    if not ok:
        OK = False
    print(("PASS" if ok else "FAIL"), nome, "-> obtido=%.5f esperado=%.5f" % (obtido, esperado))

V = lambda L, q=0.0, P=0.0, a=0.0: {'L': L, 'q': q, 'P': P, 'a': a}

# ---- 1. Caso clássico: 2 vãos L=4, q=10 → M_B = -qL²/8 = -20; R=[15,50,15]
r = mv.resolver_estatica([V(4, q=10), V(4, q=10)])
check("1a M_B (2 vãos q=10)", r['M_apoios'][1], -20.0)
check("1b R_A", r['Reacoes'][0], 15.0)
check("1c R_B", r['Reacoes'][1], 50.0)
check("1d R_C", r['Reacoes'][2], 15.0)

# ---- 2. CRÍTICO corrigido: 2 vãos L=4, P=10 em a=3.0 no vão 1
#         exato: M_B = -P·a·b·(L+a)/(4L²) = -3.28125; R=[1.680, 9.141, -0.820]
r = mv.resolver_estatica([V(4, P=10, a=3.0), V(4)])
check("2a M_B (P no vão esq., a=3)", r['M_apoios'][1], -3.28125)
check("2b R_A", r['Reacoes'][0], 1.6797, tol=1e-3)
check("2c R_B", r['Reacoes'][1], 9.1406, tol=1e-3)
check("2d R_C", r['Reacoes'][2], -0.8203, tol=1e-3)

# ---- 3. Mesmo P no vão 2 (a=3 do apoio central) → M_B = -2.34375
r = mv.resolver_estatica([V(4), V(4, P=10, a=3.0)])
check("3  M_B (P no vão dir., a=3)", r['M_apoios'][1], -2.34375)

# ---- 4. Balanço esquerdo L=2, P=10 em a=0.5 (braço 1.5) → MA = -15
r = mv.resolver_estatica([V(4)], bal_esq=V(2, P=10, a=0.5))
check("4  MA balanço esq. (braço L-a)", r['M_apoios'][0], -15.0)

# ---- 5. Balanço direito L=2, P=100 na ponta (a=2) → MZ = -200
r = mv.resolver_estatica([V(4)], bal_dir=V(2, P=100, a=2.0))
check("5  MZ balanço dir. carga na ponta", r['M_apoios'][-1], -200.0)

# ---- 6. M_pos máximo REAL: 2 vãos L=4 q=10 → 9qL²/128 = 11.25 em x=1.5
r = mv.resolver_estatica([V(4, q=10), V(4, q=10)])
check("6a M_pos máximo real (não meio do vão)", r['vaos'][0]['M_pos'], 11.25, tol=2e-3)
check("6b posição x do máximo", r['vaos'][0]['x_pos'], 1.5, tol=0.02)

# ---- 7. Flexão com 0.85·fcd: b=15,d=46,h=50,fck=25
#         Mk=101.0: Md=14140; mu=0.29350; xi=0.44669; As=14140/(37.781*43.478)=8.608
f = mv.as_flexao(101.0, 15, 46, 50, 25)
check("7a As flexão perto do limite", f['As'], 8.608, tol=0.02)
# claramente acima do limite deve falhar (Mk=103 → mu=0.2993 > 0.2952)
f2 = mv.as_flexao(103.0, 15, 46, 50, 25)
check("7b kmd>0.2952 falha", 1.0 if 'falha' in f2 else 0.0, 1.0)

# ---- 8. Vrd2 sem o 0.6 espúrio: 15x50 d=46 C25 → 299.4 kN
e = mv.dimensionar_estribos(100, 15, 46, 25)
check("8  Vrd2 NBR (Modelo I)", e['Vrd2'], 299.4, tol=0.5)

# ---- 9. Taxa mínima de estribo com fywk=50: C25 b=15 → 1.539 cm²/m
#         (cortante baixo, Vsd < Vc, para a MÍNIMA governar)
e_min = mv.dimensionar_estribos(30, 15, 46, 25)
check("9  asw_min", e_min['asw_cm2_m'], 1.539, tol=5e-3)

# ---- 10. Pesos lineares corretos (o bug do ø12.5)
check("10a peso ø12.5", mv.PESO_LINEAR[12.5], 0.963)
check("10b peso ø5.0", mv.PESO_LINEAR[5.0], 0.154)

# ---- 11. As_min pela Tabela 17.3: b=15 h=50 fck=40 → 0.179% = 1.3425 cm²
check("11 As_min fck40", mv.rho_min_flexao(40) / 100 * 15 * 50, 1.3425, tol=1e-3)

# ---- 12. Validações: a > L deve dar erro
errs = mv.validar({'b': 15, 'h': 50, 'fck': 25, 'cob': 2.5},
                  [{'nome': 'Vão 1', 'tipo': 'Normal', 'L': 4, 'q': 10, 'P': 100, 'a': 6}])
check("12 valida a>L", 1.0 if errs else 0.0, 1.0)

# ---- 13. Dois balanços do mesmo lado deve dar erro
errs = mv.validar({'b': 15, 'h': 50, 'fck': 25, 'cob': 2.5},
                  [{'nome': 'V1', 'tipo': 'Normal', 'L': 4, 'q': 10, 'P': 0, 'a': 0},
                   {'nome': 'B1', 'tipo': 'Balanço Esquerdo', 'L': 2, 'q': 10, 'P': 0, 'a': 0},
                   {'nome': 'B2', 'tipo': 'Balanço Esquerdo', 'L': 1, 'q': 50, 'P': 0, 'a': 0}])
check("13 valida 2 balanços esq.", 1.0 if errs else 0.0, 1.0)

# ---- 14. Pipeline completo com quantitativo (sem falha)
res = mv.calcular_viga({'b': 15, 'h': 50, 'fck': 25, 'cob': 2.5, 'peso_proprio': False},
                       [{'nome': 'V1', 'tipo': 'Normal', 'L': 5, 'q': 20, 'P': 0, 'a': 0},
                        {'nome': 'V2', 'tipo': 'Normal', 'L': 3, 'q': 10, 'P': 0, 'a': 0}])
assert 'erros' not in res, res.get('erros')
check("14a M apoio central (5m/20 + 3m/10)", res['estatica']['M_apoios'][1], -43.28125, tol=0.01)
q = res['quantitativo']
check("14b quantitativo existe", 1.0 if q else 0.0, 1.0)
print("    posições:", [(p['pos'], p['descr'], p['phi'], p['qtd'], round(p['comp_unit'],2)) for p in q['posicoes']])
print("    peso total: %.2f kg | compra: %.2f kg" % (q['peso_total'], q['peso_compra']))

# ---- 15. Viga reprovada NÃO gera quantitativo
res = mv.calcular_viga({'b': 15, 'h': 50, 'fck': 25, 'cob': 2.5, 'peso_proprio': False},
                       [{'nome': 'V1', 'tipo': 'Normal', 'L': 8, 'q': 80, 'P': 0, 'a': 0}])
check("15 reprovada sem quantitativo", 0.0 if res['quantitativo'] is None else 1.0, 0.0)
check("15b flag falha", 1.0 if (res['falha_flexao'] or res['falha_biela']) else 0.0, 1.0)

# ---- 16. Estribo usa cortante real: vão 4m q=2 P=150 no meio (b=15 h=50 C25)
#          Vsd real ≈ 110.6 kN → deve dar ~c/12 cm, não taxa mínima (c/22)
res = mv.calcular_viga({'b': 15, 'h': 50, 'fck': 25, 'cob': 2.5, 'peso_proprio': False},
                       [{'nome': 'V1', 'tipo': 'Normal', 'L': 4, 'q': 2, 'P': 150, 'a': 2}])
e = res['estribos'][0]
print("    estribo vão P=150:", e['texto'], "(Vsd=%.1f)" % e['Vsd'])
check("16 Vsd com P incluído", e['Vsd'], 110.6, tol=1.0)

print()
print("RESULTADO GERAL:", "TODOS OS TESTES PASSARAM ✔" if OK else "*** HÁ FALHAS ***")
