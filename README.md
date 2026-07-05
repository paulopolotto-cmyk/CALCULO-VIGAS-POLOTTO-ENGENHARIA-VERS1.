# Polotto Engenharia — Cálculo Estrutural (NBR 6118)

Aplicativo web (Streamlit) de dimensionamento de **vigas contínuas** e
**pilares** de concreto armado, otimizado para uso no celular.

## Como usar

- **Web:** acesse o link do app no Streamlit Cloud (atualiza sozinho a cada
  push neste repositório).
- **Local:**
  ```
  pip install -r requirements.txt
  streamlit run "import numpy as np.py"
  ```
  O app abre com as duas páginas (Vigas e Pilares) na navegação superior.

## Estrutura

| Arquivo | Função |
|---|---|
| `import numpy as np.py` | Ponto de entrada (navegação). Nome histórico — é o arquivo principal do deploy. |
| `pagina_vigas.py` / `pagina_pilar.py` | Interfaces (Streamlit) |
| `motor_viga.py` / `motor_pilar.py` | Motores de cálculo **puros e testáveis** (sem Streamlit) |
| `ui_comum.py` | Identidade visual compartilhada (azul engenharia Polotto) |
| `tests/` | Testes automatizados contra soluções exatas (`python tests/test_motor_viga.py`) |
| `.streamlit/config.toml` | Tema do app |

## O que o programa calcula

**Vigas** (`motor_viga.py`):
- Esforços pela Equação dos Três Momentos (vãos normais + até 1 balanço por
  lado; carga distribuída q e carga concentrada P em posição qualquer `a`)
- Diagramas de momento e cortante; momentos máximos reais (varredura de M(x))
- Flexão ELU com σcd = 0,85·fcd (17.2.2), limite x/d = 0,45 e As,mín pela
  Tabela 17.3; escolha de bitolas que **cabe na largura** (18.3.2.2)
- Cortante pelo Modelo I (17.4.2.2) com o cortante real de cada tramo,
  taxa mínima com fywk, limites de espaçamento (18.3.3.2)
- Armadura de pele por face (17.3.5.2.3), quantitativo por posição real e
  lista de compra em barras de 12 m

**Pilares** (`motor_pilar.py`):
- Nd = γn·γf·Nk (γn pela menor dimensão, Tab. 13.1)
- Esbeltez λ nas duas direções; momento mínimo M1d,min (11.3.3.4.3);
  2ª ordem pelo pilar-padrão com curvatura aproximada (15.8.3.3.2);
  bloqueio para λ > 90
- Verificação em **flexo-compressão** por compatibilidade de deformações
  (pivôs B e C)
- Arranjos que respeitam φ ≤ b/8, espaçamentos mín/máx por face e
  As entre 0,4% e 4% de Ac

## Limitações declaradas (avisadas no app)

- Caso único de carga — **sem envoltória** de alternância de sobrecarga
- **ELS não verificado** (flecha e fissuração) — conferir manualmente
- Sem armadura dupla na flexão (seções que exigem são reprovadas)
- Pilar: sem flexão oblíqua composta nem momentos aplicados (pilar interno
  contraventado); le adotado = l0
- fck limitado ao grupo I (20 a 50 MPa)

> ⚠️ Ferramenta de apoio a projeto. Os resultados devem ser conferidos por
> profissional habilitado.

## Histórico

Em 05/07/2026 o software passou por auditoria técnica completa (74 achados,
10 críticos) e os motores de cálculo foram reescritos e validados contra
soluções exatas — ver `tests/`.
