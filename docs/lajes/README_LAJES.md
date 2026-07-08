# Módulo de Lajes — README

Cálculo de **lajes maciças** (1 e 2 direções) e **pré-moldadas treliçadas**,
com transferência das cargas para os módulos de **Vigas** e **Pilares**.
NBR 6118 / 6120 / 14859. Ferramenta de **pré-dimensionamento** — não substitui
projeto assinado.

## Arquivos
- `motor_laje.py` — motor de cálculo puro (sem Streamlit), testável.
- `pagina_lajes.py` — interface Streamlit (usa `ui_comum.py`).
- `docs/lajes/ENGENHARIA_LAJES.md` — formulação de engenharia.
- `docs/lajes/ENGENHARIA_VERIF.md` — verificação independente de coeficientes.
- `docs/lajes/AUDITORIA_LAJES.md` — mapa de integração com vigas/pilares.

## Como usar (fluxo)
1. Escolha **tipo** (treliçada ou maciça) e os **vãos** (botões rápidos ou
   digitados). `lx` = menor vão.
2. Treliçada: **altura** (12/16/20/25), **enchimento** (EPS/cerâmico),
   **vinculação** (biapoiada/contínua). Maciça: **espessura** e **condições
   das 4 bordas** (Apoiada/Engastada).
3. **Cargas**: uso (NBR 6120), revestimento, parede, fck.
4. Leia o **veredito de flecha** (🟢/🟡/🔴), o **desenho do pano**, os
   esforços/armadura, as **reações nas vigas** e **cargas nos pilares**.
5. **Integração**: "Enviar para Vigas" (cria a viga da borda com a reação) e
   "Enviar para Pilares" (envia o Nk de um pilar de canto).
6. Baixe a **memória em PDF**.

## Métodos (resumo)
| Item | Método | Validação |
|---|---|---|
| Momentos/flecha da laje maciça (9 casos, qualquer λ) | Placa de Kirchhoff por **diferenças finitas** (13 pontos, nós-fantasma), ν=0,2 | vs Timoshenko: w=0,00406·p·lx⁴/D; μ, M_engaste (<2%) |
| Reações nas vigas | **Charneiras plásticas** (NBR 6118 14.7.6.1) por grade ponderada (45°/60°) | soma das forças = p·A (conservação) |
| Treliçada (1 direção) | Faixa de 1 m: M=p·lx²/8, V=p·lx/2; reações p·lx/2 (principal) e p·lx/8 (marginal) | catálogo NBR 14859 |
| Armadura | Flexão simples, **Md = 1,4·Mk**, As_mín (Tab. 17.3), x/d ≤ 0,45 | — |
| Flecha (ELS) | Estádio I (Ecs, seção bruta) na **combinação quase-permanente** (g+ψ₂·q, ψ₂=0,3) × fluência **(1+αf)=3** | limites Tab. 13.3: L/250, L/500≤10mm |
| Reações → pilar | Carga de canto = ½ reação de cada viga adjacente + PP da viga | pré-dimensionamento |

## Integração (chaves de session_state)
- **Vigas**: `viga_b/h/fck/cob` + `lista_vaos=[{tipo,L,q,P,a}]` (q em **kN
  interno**) → `st.switch_page("pagina_vigas.py")`.
- **Pilares**: `pilar_Nk = Nk_kN * fu` (**unidade de exibição**) + seção →
  `st.switch_page("pagina_pilar.py")`.
- Não altera as páginas de Vigas/Pilares (apenas pré-preenche o estado que
  elas já leem).

## Limites / avisos
- Um pano por vez (múltiplos panos = roadmap).
- Flecha por estádio I (bruta) — simplificação de pré-dim (pode subestimar em
  laje muito fissurada; o alerta é conservador).
- Peso próprio da treliçada por catálogo (varia entre fabricantes — editável
  em versões futuras).
- Não considera vento, cargas concentradas móveis, balanços (roadmap).
