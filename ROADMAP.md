# ROADMAP — Polotto Engenharia (Cálculo Estrutural)

App Streamlit de cálculo estrutural em concreto armado (NBR 6118 / 6120 /
14859). Módulos atuais: **Vigas**, **Pilares**, **Pilares Prévios (casas
térreas)** e **Lajes (maciça + treliçada)**.

> Priorização (demanda × utilidade × esforço) feita na fase de pesquisa do
> módulo de Lajes. Detalhe em `docs/lajes/ROADMAP_DRAFT.md`.

---

## TOP 5 de melhorias futuras (mapeado nesta entrega)

### 1. Múltiplos panos de laje em grelha (casa inteira)
Modelar todos os panos de uma casa em uma malha, com **acúmulo automático das
cargas nos pilares comuns** (um pilar de canto de vários panos soma as
contribuições). Completa o diferencial "laje → viga → pilar" para a obra toda.
*Estado:* MVP entrega **um pano** com integração completa; a grelha é o próximo
passo.

### 2. Mapa de cargas da casa + pré-dimensionamento automático de pilar
Planta com todas as reações de laje/viga e o **N acumulado em cada pilar**,
alimentando a seção sugerida do pilar automaticamente (liga com o módulo
"Pilares Prévios"). Fecha o ciclo "desenhei as lajes → sei o pilar".

### 3. Quantitativo consolidado da obra + estimativa de custo (R$)
Somar os quantitativos de todos os panos (concreto m³, fôrma m², kg de aço,
nº de vigotas/blocos) e aplicar **preços unitários editáveis** → orçamento
rápido. Hoje o quantitativo é **por pano**.

### 4. Casos especiais de laje
**Laje em balanço** (marquises/varandas — momento negativo, ancoragem),
**cargas concentradas** e **de parede** com posição sobre a laje,
**verificação de cortante** em laje (dispensa de armadura transversal).

### 5. Detalhamento e biblioteca de exemplos
**Detalhamento de armadura** (posições, bitolas, comprimentos, dobras) e uma
**biblioteca de exemplos de casas** (térrea, sobrado, kitnet) para começar em
1 clique. Onboarding + ponte para o executor.

---

## O que ENTROU nesta entrega (módulo de Lajes — MVP)

- ✅ Laje **maciça** (1 e 2 direções, 9 casos de apoio) e **pré-moldada
  treliçada** (EPS/cerâmico), com **detecção automática de direção** (λ).
- ✅ Cargas NBR 6120 (Tabela 10), materiais e coeficientes editáveis.
- ✅ **Verificação de flecha** (ELS) imediata + diferida, com **alerta
  🟢/🟡/🔴** e sugestão de contra-flecha.
- ✅ Momentos (positivos e de engaste) e **armadura** (As, As_mín).
- ✅ **Reações da laje nas vigas** (charneiras plásticas) e **cargas nos
  pilares** (cantos), com nomeação V1–V4 / P1–P4.
- ✅ **Integração** "Enviar para Vigas" e "Enviar para Pilares"
  (pré-preenche os módulos existentes — validado ponta a ponta).
- ✅ **Desenho esquemático** do pano (vigas, pilares, áreas de influência,
  direção das vigotas).
- ✅ **Comparativo** treliçada × maciça do mesmo pano.
- ✅ **Quantitativos** do pano e **memória de cálculo em PDF**.
- ✅ Vãos padrão de seleção rápida (12) + vão personalizado.

## Fora de escopo (por ora)
Análise não-linear / elementos finitos completos, protensão, lajes nervuradas
industriais, CAD/BIM. Grelha multi-panos e mapa de cargas da casa são o
próximo grande passo (itens 1–2 acima).
