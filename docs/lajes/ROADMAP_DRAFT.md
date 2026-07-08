# Roadmap — Módulo de Lajes (Polotto)

> Rascunho de produto. Público: engenheiros civis e arquitetos (Brasil). Norma base: NBR 6118 (+ NBR 6120 para cargas, NBR 14859 para pré-fabricadas/vigotas treliçadas).
> Objetivo do módulo: calcular a laje (pré-moldada treliçada e maciça) e **transferir as cargas para vigas e pilares**, integrando com os módulos existentes.

Data: 2026-07-07 · Status: draft para priorização

---

## (a) Lista ampla de features candidatas

Cada item com uma linha de valor para o dia a dia do projetista.

### Cálculo / dimensionamento
- **Cálculo de laje maciça (armada 1 e 2 direções)** — o básico universal; toda casa/sobrado tem pelo menos uma.
- **Cálculo de laje pré-moldada treliçada (vigota + EPS/cerâmico)** — sistema dominante em residências no Brasil; alta demanda real.
- **Detecção automática da direção de armação** — a partir da relação de vãos (λ = ly/lx) decide armada em 1 ou 2 direções e o sentido das vigotas; evita erro comum de iniciante.
- **Comparativo pré-moldada × maciça** — lado a lado (custo, peso próprio, altura, prazo) para decisão rápida com o cliente.
- **Pré-dimensionamento automático da altura da laje** — sugere h (ou tipo de treliça/enchimento) a partir do vão; ponto de partida instantâneo.
- **Verificação de flecha com alerta (ELS)** — flecha imediata + diferida (φ), comparada ao limite NBR (l/250, l/350); alerta visual verde/amarelo/vermelho.
- **Verificação de cortante em lajes** (dispensa de armadura transversal) — fecha o ELU que muita planilha ignora.
- **Cálculo de laje em balanço (marquises/varandas)** — caso recorrente e crítico (momento negativo, ancoragem).
- **Cargas concentradas e de parede sobre laje** — parede divisória apoiada na laje é dúvida diária.

### Cargas e integração (núcleo do diferencial)
- **Integração laje → viga → pilar** *(já no escopo)* — reação da laje vira carga distribuída na viga e desce ao pilar, sem redigitar.
- **Múltiplos panos em grelha com acúmulo nas vigas/pilares comuns** — casa inteira em um modelo; pilar comum soma contribuições de todos os panos.
- **Mapa de cargas da casa inteira** — planta com todas as reações de laje/viga e o carregamento acumulado em cada pilar; visão de conjunto.
- **Pré-dimensionamento automático de pilar a partir da carga acumulada** — sugere seção do pilar já com o N que desceu das lajes/vigas.
- **Área de influência automática por pano** — distribui a carga da laje às vigas de apoio (charneiras 45°/regras de área) sem cálculo manual.
- **Combinações de carga automáticas (NBR 6120 + 8681)** — permanente/acidental por tipo de ambiente (dormitório, cozinha, área técnica, telhado).

### Quantitativos / orçamento
- **Quantitativo de materiais** — volume de concreto (m³), área de forma (m²), taxa e kg de aço, nº de vigotas e nº de blocos/EPS por pano e total.
- **Resumo consolidado de materiais da obra** — soma de todos os panos → lista de compra do concreto/aço/lajota.
- **Estimativa de custo (R$)** — aplica preços unitários (editáveis) aos quantitativos; orçamento rápido para o cliente.

### Produtividade / entrega
- **Exportação PDF da memória de cálculo** — memória assinável (dados, verificações, croqui) para prefeitura/ART; item de maior pedido em software de eng.
- **Biblioteca de exemplos de casas** — modelos prontos (casa térrea, sobrado, kitnet) para começar em 1 clique e aprender a ferramenta.
- **Croqui/planta esquemática do pano** — desenho com vãos, direção da armadura e apoios; comunica visualmente o que foi calculado.
- **Detalhamento de armadura (posições, bitolas, comprimentos)** — ponte para o executor; reduz retrabalho.

---

## (b) TOP 5 priorizado

Critério: **demanda (frequência de uso real) × utilidade (resolve dor) × esforço (custo de implementação)**. Priorizamos o que é usado em quase todo projeto residencial e/ou é o diferencial competitivo do app, favorecendo alto valor com esforço moderado que aproveita os módulos de viga/pilar já prontos.

### 1. Cálculo de laje pré-moldada treliçada + maciça com detecção automática de direção
**Por quê:** é a razão de existir do módulo. A treliçada é o sistema dominante em residências no Brasil e a maciça é o caso universal. A detecção automática de direção (1 vs 2 direções pelo λ = ly/lx) remove o erro conceitual mais comum. Sem isso, nada mais tem valor. Demanda máxima, utilidade máxima, esforço médio.

### 2. Integração laje → viga → pilar com acúmulo em múltiplos panos *(diferencial competitivo)*
**Por quê:** é o que planilha e concorrentes baratos não fazem bem. Distribuir a reação da laje às vigas por área de influência e acumular nos pilares comuns elimina redigitação e erros de transporte de carga. Já está no escopo e reaproveita os módulos existentes — esforço médio, valor altíssimo. Sustenta o item 4.

### 3. Verificação de flecha (ELS) com alerta visual
**Por quê:** flecha é o que **governa** o dimensionamento de laje residencial (mais que o ELU). O alerta verde/amarelo/vermelho traduz a norma para quem tem pouca familiaridade e evita o defeito de obra nº 1 (piso/forro fissurado, porta que trava). Baixo/médio esforço sobre o cálculo do item 1, utilidade percebida enorme.

### 4. Pré-dimensionamento automático de pilar a partir da carga acumulada + mapa de cargas da casa
**Por quê:** fecha o ciclo "desenhei as lajes → sei o pilar". A carga que desce das lajes/vigas alimenta a seção sugerida do pilar, e o mapa de cargas dá a visão de conjunto da casa inteira. Depende do item 2, mas entrega o "momento mágico" que vende o produto. Esforço médio (aproveita módulo de pilar), alta utilidade.

### 5. Exportação PDF da memória de cálculo + quantitativos de material
**Por quê:** é o **entregável**. O engenheiro precisa da memória para ART/prefeitura e do quantitativo (concreto m³, forma m², kg de aço, nº de vigotas/blocos) para orçar e comprar. Sem PDF, o cálculo "não sai do app". Alta demanda, utilidade direta no bolso do usuário, esforço médio (geração de relatório sobre dados já calculados).

**Fora do TOP 5, mas fortes candidatos ao futuro próximo:** comparativo pré-moldada × maciça (marketing/decisão), estimativa de custo em R$, biblioteca de exemplos de casas, laje em balanço.

---

## (c) MVP desta entrega × Futuro

### MVP (esta entrega)
Foco: calcular um pano corretamente, mostrar que passa, transferir a carga e gerar o documento.

- **Cálculo de 1 pano** — maciça e treliçada, armada em 1 e 2 direções, com detecção automática de direção (TOP 1).
- **Verificação de flecha ELS com alerta** verde/amarelo/vermelho e ELU de flexão (TOP 3).
- **Integração laje → viga → pilar para o pano** — reação vira carga na viga de apoio via área de influência (base do TOP 2).
- **Quantitativos do pano** — concreto, forma, aço, nº de vigotas/blocos (parte do TOP 5).
- **Exportação PDF da memória** do pano com croqui simples (parte do TOP 5).
- **Pré-dimensionamento da altura da laje** (sugestão de h/tipo) como auxílio de entrada.

### Futuro (próximas entregas)
- **Grelha multi-panos com acúmulo nos pilares comuns** + **mapa de cargas da casa inteira** (completa o TOP 2).
- **Pré-dimensionamento automático de pilar** pela carga acumulada (completa o TOP 4).
- **Resumo consolidado de materiais da obra** + **estimativa de custo em R$**.
- **Comparativo pré-moldada × maciça** lado a lado.
- **Biblioteca de exemplos de casas** (onboarding).
- **Casos especiais:** laje em balanço, cargas de parede/concentradas, verificação de cortante, detalhamento de armadura.

### Fora de escopo (por ora)
- Análise não-linear/elementos finitos completos, protensão, lajes nervuradas industriais, CAD/BIM bidirecional.

---

### Racional de sequenciamento
1 (calcular) → 3 (verificar/alertar) → 2 (transferir carga) → 5 (documentar/quantificar) formam o **fluxo mínimo vendável** de um pano. O item 4 (pilar + mapa) e a grelha multi-panos são a **expansão** que multiplica o valor assim que o pano único estiver sólido.
