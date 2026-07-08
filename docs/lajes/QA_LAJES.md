# QA / Validação — Módulo de Lajes

Evidências de validação do motor `motor_laje.py`. Todos os cenários rodados
sem travamento, sem resultado absurdo, com reações conservando a carga total
(Σ forças = p·A).

## 1. Solver de placa (diferenças finitas) × Timoshenko (solução exata)

| Caso | Grandeza | Motor | Timoshenko | Erro |
|---|---|---|---|---|
| SS quadrada (ν=0,2) | flecha w·D/(p·lx⁴) | 0,00406 | 0,00406 | ~0 |
| SS quadrada (ν=0,2) | μ (M=μ·p·lx²/100) | 4,42 | 4,4 (Bares) | <1% |
| SS retângulo 1×2 (ν=0,3) | μx / μy | 10,16 / 4,66 | 10,17 / 4,64 | <1% |
| SS retângulo 1×2 (ν=0,3) | flecha | 0,01013 | 0,01013 | ~0 |
| Engastada 4 lados (ν=0,3) | M_vão | 0,0229 | 0,0231 | ~1% |
| Engastada 4 lados (ν=0,3) | M_engaste | −0,0511 | −0,0513 | <1% |

## 2. Seis casos de referência (conferidos à mão)

| Caso | Verificação manual | Motor | OK |
|---|---|---|---|
| A) Maciça 4×4 4-apoiada h10 | p=5,0; M≈3,54; q_borda=5,0; ΣF=80 | p=5,0; Mx=3,53; q=5,0; ΣF=80 | ✅ |
| B) Maciça 4×6 4-apoiada h12 | λ=1,5; Mx>My; ΣF=132 | Mx=6,88>My=3,74; ΣF=132 | ✅ |
| C) Maciça 4×4 inf-engastada | engaste puxa mais carga | q_inf=8,85 > q_sup=5,09 | ✅ |
| D) Maciça 5×5 2 engastes opostos | — | Mx_eng=9,52; verde | ✅ |
| E) Treliçada 4×4 h16 EPS | g=1,70; p=4,2; M=8,4; V=8,4; reação=8,4 | idem | ✅ |
| F) Treliçada 5×4 h20 cerâmico | lx=4 (menor); g=2,9; p=5,4; M=10,8 | idem | ✅ |

## 3. Cobertura ampla (0 falhas)

- **12 vãos padrão × 2 tipos** (2×1 … 7×7): reações conservam em todos;
  alertas de flecha coerentes (verde nos vãos pequenos → amarelo/vermelho nos
  grandes/finos). Tempo médio 0,08 s/laje.
- **9 padrões de apoio** (maciça 4×5 h12): 1 a 4 engastes, adjacentes e
  opostos. Momentos coerentes (mais engaste → menos M⁺, flecha menor);
  reações conservam. 0 falhas.
- **Extremos**: 1×1 h6 (alerta espessura mínima), 12×6 h20 (amarelo), 8×2
  λ=4 (uma direção), treliçada 7×7 h12 (vermelho + "exige laje mais alta"),
  treliçada 3×3 h25 contínua (verde). Sem exceção/absurdo.

## 4. Integração (ponta a ponta, navegador real — Playwright)

- **Enviar para Vigas**: cria o tramo `L=4,00 m · q=214 kgf/m` na página de
  Vigas e a viga calcula (veredito exibido). ✅
- **Enviar para Pilares**: abre a página de Pilares com o `Nk` do pilar de
  canto. ✅
- **Regressão**: páginas de Vigas, Pilares e Pilares Prévios renderizam com
  0 exceções após a inclusão do módulo. ✅

Total: **32+ cenários de cálculo + integração + regressão, 0 falhas.**
