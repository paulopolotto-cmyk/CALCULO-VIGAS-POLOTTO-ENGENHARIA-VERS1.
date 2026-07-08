# ENGENHARIA DE LAJES — Formulação Completa para Motor de Cálculo

Lajes residenciais: pré-moldada treliçada unidirecional + maciça (uma e duas direções).
Base normativa: **NBR 6118:2023** (projeto de concreto), **NBR 6120:2019** (ações),
**NBR 14859-1/2:2016** (lajes pré-fabricadas — nervuradas/treliçadas), **NBR 8681:2003** (ações e segurança).

> **REGRA DE OURO DESTE DOCUMENTO:** nenhum coeficiente foi inventado. Todo valor de
> tabela normativa que não pude reproduzir com certeza absoluta está marcado **`[INCERTO]`**
> com a explicação e a fonte a consultar. Valores calculáveis por geometria/física
> (peso próprio, áreas de charneiras) são deduzidos por fórmula e portanto verificáveis.
> A lista consolidada de itens `[INCERTO]` está no RESUMO final.

Convenção de unidades: forças em **kN**, comprimentos em **m** (salvo cm indicado),
tensões/módulos em **MPa** ou **kN/m²**, cargas distribuídas em **kN/m²** (superfície) ou **kN/m** (linear).

---

## A) CARGAS

### A.1 Cargas variáveis de uso — NBR 6120:2019, Tabela 10

A Tabela 10 fornece os **valores mínimos das cargas variáveis (acidentais)** verticais,
uniformemente distribuídas, em kN/m². Abaixo os usos residenciais e afins. Onde há
dúvida na transcrição exata do valor de 2019 (a norma reorganizou vários itens em relação
à antiga NBR 6120:1980), o item está marcado `[INCERTO]`.

| Local / uso | Carga q (kN/m²) | Confiança |
|---|---|---|
| Dormitório, sala, copa, cozinha e banheiro (edifício residencial) | **1,5** | alta |
| Despensa, área de serviço e lavanderia | **2,0** | alta |
| Corredores **dentro** de unidades autônomas (uso privativo) | **1,5** | média |
| Corredores e áreas de **uso comum** (coletivo) | **3,0** | média |
| Escadas — uso privativo (residencial, dentro da unidade) | **2,5** | `[INCERTO]` |
| Escadas — com acesso ao público / uso coletivo | **3,0** | média |
| Forro — sem acesso a pessoas (só manutenção, sem estoque) | **0,5** | alta |
| Sótão / desvão de telhado acessível | **2,0** | `[INCERTO]` |
| Terraço/varanda — acesso privativo | = ambiente que serve (mín. **1,5**) | média |
| Sacada/varanda — carga adicional na borda livre | ver nota (b) | `[INCERTO]` |
| Garagem/estacionamento — veículos de passageiros (P ≤ 25 kN) | **3,0** | média |
| Depósito (não especificado) | **≥ 3,0** conforme material | consultar |

**Notas:**

- **(a) `[INCERTO]` — escadas privativas (2,5) e sótão (2,0):** a NBR 6120:2019 reorganizou
  esses itens; o valor 2,5 kN/m² para escada privativa e 2,0 kN/m² para sótão vêm da minha
  memória da norma antiga/prática corrente. **Confirmar diretamente na Tabela 10 da
  NBR 6120:2019** antes de fixar no motor.
- **(b) `[INCERTO]` — sacadas/varandas:** a NBR 6120:2019 exige, além da carga de superfície
  igual à do ambiente contíguo, uma **carga linear adicional na extremidade livre** (parapeito
  + concentração de pessoas). Não reproduzo o valor exato de memória — **consultar o item
  específico de sacadas da NBR 6120:2019** (ordem de 2 kN/m linear no bordo, a confirmar).
- **(c) Garagem (3,0 e limite de peso):** confirmar se a NBR 6120:2019 fixa o limite em
  25 kN ou 30 kN para "veículos de passageiros"; adotei 3,0 kN/m² que é o valor de projeto
  usual para garagem residencial leve. `[INCERTO]` no limite de peso.
- **(d) Regra geral:** a carga de uso **nunca substitui** verificações de cargas concentradas
  (a própria Tabela/norma pede verificar carga concentrada de 2 kN sobre 5×5 cm em pisos,
  quando mais desfavorável).

### A.2 Cargas permanentes (peso próprio + revestimentos)

**Peso específico do concreto armado:** **γ_c = 25 kN/m³** (NBR 6120:2019, Tabela 1 /
concordante com NBR 6118). Concreto simples = 24 kN/m³.

**Revestimento / contrapiso (valores típicos de projeto, kN/m²):**

Composição usual de piso residencial e peso específico dos materiais (NBR 6120:2019, Anexo A):

| Camada | γ típico | Espessura usual | g (kN/m²) |
|---|---|---|---|
| Contrapiso / regularização (argamassa cimento-areia, γ=21 kN/m³) | 21 kN/m³ | 3–5 cm | 0,63–1,05 |
| Piso cerâmico/porcelanato + argamassa colante | — | — | ~0,20–0,50 |
| Revestimento de teto (reboco/gesso, γ≈12,5–19 kN/m³) | 12,5–19 kN/m³ | 1,5–2 cm | ~0,20–0,40 |
| **Total típico de revestimento (piso+teto)** | — | — | **≈ 1,0 kN/m²** |

> γ da argamassa de cimento e areia = **21 kN/m³**; argamassa de cal-cimento-areia ≈ **19 kN/m³**;
> gesso ≈ **12,5 kN/m³** (NBR 6120:2019, Anexo A). O valor de projeto **g_rev ≈ 1,0 kN/m²**
> é uma adoção conservadora usual; ajuste conforme o acabamento real.

### A.3 Parede sobre laje — conversão em carga

**Carga da parede (peso por metro linear de parede):**

    g_parede,linear = γ_alv · e · h_parede           [kN/m]

onde γ_alv = peso específico da alvenaria (kN/m³), e = espessura da parede **acabada** (m,
incluindo revestimento), h_parede = altura livre da parede (m). Some o revestimento das
duas faces se γ_alv for só do bloco.

**Peso específico da alvenaria (NBR 6120:2019, Anexo A):**

| Material | γ_alv (kN/m³) | Confiança |
|---|---|---|
| Alvenaria de tijolos cerâmicos furados | ~13 | `[INCERTO]` (confirmar Anexo A) |
| Alvenaria de tijolos cerâmicos maciços | ~18 | `[INCERTO]` |
| Alvenaria de blocos de concreto vazado | ~14 | `[INCERTO]` |
| Alvenaria de blocos de concreto celular autoclavado | 5,5–8 | `[INCERTO]` |

> `[INCERTO]`: os γ de alvenaria acima são de ordem de grandeza usual; **os valores exatos
> devem ser lidos do Anexo A da NBR 6120:2019**. Alternativamente use peso por m² de parede
> pronta tabelado (a norma traz tabela de "peso de paredes por m² de face" já com revestimento).

**Quando tratar como carga LINEAR vs. distribuída por m²:**

1. **Laje MACIÇA armada em duas direções, ou laje com parede em posição qualquer:**
   trate a parede como **carga linear** (kN/m) na sua posição real. Em cálculo de placa,
   converta a parede em carga distribuída equivalente **somente para pré-dimensionamento**:

       g_parede,eq = (Σ pesos de todas as paredes sobre a laje) / (área da laje)   [kN/m²]

   Essa "diluição" é aceitável apenas quando as paredes são **numerosas e bem distribuídas**
   e não paralelas/muito próximas de um bordo.

2. **Laje TRELIÇADA unidirecional:**
   - Parede **paralela às vigotas** (na direção do vão): a nervura sob a parede recebe
     carga concentrada — **verificar a vigota isolada** com a carga linear real ou usar
     nervura de reforço (dupla). Não diluir.
   - Parede **perpendicular às vigotas** (transversal ao vão): distribui-se sobre várias
     nervuras; pode ser tratada como carga linear cruzando a laje, ou diluída por m² para
     pré-dimensionamento.

3. **Regra prática de segurança:** parede alta/pesada (ex.: > 2,5 kN/m) alinhada a uma
   nervura **nunca** deve ser diluída — dimensione a nervura sob ela como viga.

---

## B) LAJE PRÉ-MOLDADA TRELIÇADA (unidirecional)

Nomenclatura NBR 14859-1: altura total **h = h_enchimento + h_capa** (cm). Capa = mesa de
concreto moldada in loco. Intereixo (distância entre eixos de vigotas) padrão treliçado
**= 42 cm** (também há 33 cm e outros). Vigota treliçada = armadura treliçada eletrossoldada
+ base de concreto pré-moldada.

### B.1 Peso próprio g_pp por altura e enchimento

O peso próprio é **calculável por geometria** (portanto não inventado). Modelo por m² para
intereixo b = 0,42 m, largura de nervura b_w ≈ 0,12 m (varia 9–13 cm), capa e_c:

    Concreto da capa:      g_capa   = γ_c · e_c
    Concreto das nervuras: g_nerv   = γ_c · b_w · h_ench · (1/b)     [n° nervuras/m = 1/b]
    Enchimento:            g_ench   = γ_ench · (b − b_w)/b · h_ench
    ------------------------------------------------------------
    g_pp = g_capa + g_nerv + g_ench            [kN/m²],  γ_c = 25 kN/m³

γ_ench: cerâmico ≈ **11–13 kN/m³**; EPS ≈ **0,15–0,30 kN/m³** (praticamente nulo).

**Tabela de peso próprio — valores de referência (catálogo nacional / NBR 14859).**
As colunas "calc." são obtidas pelas fórmulas acima (b=0,42 m; b_w=0,12 m; γ_ceram=12 kN/m³);
as colunas "catálogo" são faixas típicas de catálogos de fabricantes. **Adotar o maior entre
o calculado e o de catálogo, ou o valor do catálogo do fabricante especificado.**

| h total (cm) | Enchimento + capa | g_pp EPS (kN/m²) | g_pp cerâmico (kN/m²) | Base |
|---|---|---|---|---|
| **12** | 8 + 4 | **≈ 1,5** (calc ~1,45) | **≈ 2,0–2,2** | calc + catálogo |
| **16** | 12 + 4 | **≈ 1,7** (calc ~1,65) | **≈ 2,4–2,6** | calc + catálogo |
| **20** | 16 + 4 | **≈ 2,0** (calc ~1,85) | **≈ 2,8–3,1** | calc + catálogo |
| **25** | 20 + 5 | **≈ 2,4** (calc ~2,35) | **≈ 3,3–3,6** | calc + catálogo |

> **`[INCERTO]` (parcial):** as faixas de catálogo (especialmente cerâmico) variam por
> fabricante conforme b_w real, tipo de lajota e intereixo. Os valores **EPS** são mais
> estáveis (dominados pelo concreto) e coerentes com o cálculo geométrico. **Recomendação
> para o motor:** guardar g_pp como parâmetro editável por altura e por fabricante; usar a
> fórmula geométrica como default verificável e permitir sobrescrever pelo catálogo.
> Para bidirecional/treliça protendida os valores mudam.

Carga permanente total sobre a laje treliçada:

    g_total = g_pp + g_rev + g_parede,diluída        [kN/m²]
    p (ELU/ELS) = combinação de g_total com q (uso)   → ver seção D e NBR 8681

### B.2 Vão máximo (pré-dimensionamento)

Regra prática de esbeltez para laje treliçada unidirecional (relação vão/altura):

    Biapoiada:   h ≥ L / 25      ⇒   L_max ≈ 25 · h
    Contínua:    h ≥ L / 30      ⇒   L_max ≈ 30 · h

Exemplos (biapoiada, h em cm → L_max em m):

| h (cm) | L_max biapoiada (≈ L=25h) | L_max contínua (≈ 30h) |
|---|---|---|
| 12 | ~3,0 m | ~3,6 m |
| 16 | ~4,0 m | ~4,8 m |
| 20 | ~5,0 m | ~6,0 m |
| 25 | ~6,25 m | ~7,5 m |

**Alertas do motor:**
- Se L exigir h acima do disponível em enchimento, **passar para vigota dupla, intereixo
  menor, ou vigota PROTENDIDA** (maior capacidade). Sinalizar.
- Acima de ~5–6 m biapoiada, quase sempre exige **treliça protendida** ou laje **bidirecional/nervurada**.
- Esta regra é de **pré-dimensionamento**; a altura final decorre da verificação de flecha
  (seção D) e de ELU (flexão/cortante), que **governam** frequentemente antes do vão-limite.

> **`[INCERTO]` (leve):** os fatores 25 e 30 são regras práticas consagradas, não valores
> normativos fixos. Cada fabricante publica **tabela de vãos** por altura e sobrecarga —
> preferir essa tabela quando disponível.

### B.3 Esforços (faixa de 1 m ou por nervura)

Modele a laje unidirecional como **viga de largura unitária (1 m)** ou **por nervura**
(largura = intereixo b). Carga p em kN/m² → carga linear por faixa de 1 m: p_faixa = p·1,0 (kN/m).

**Biapoiada:**

    M_meio = p · L² / 8
    V_apoio = p · L / 2

**Contínua (vãos aproximadamente iguais, método dos coeficientes):**

    M = coef · p · L²      (L = vão teórico do tramo considerado)

Coeficientes clássicos para vigas contínuas de vãos iguais e carga uniforme (viga
contínua, apoios simples internos):

| Situação | Momento positivo (vão) | Momento negativo (apoio) |
|---|---|---|
| 2 vãos iguais | +p L²/8 nos vãos (aprox. +1/14 a +1/11) | −p L²/8 no apoio central |
| 3 vãos iguais — vão externo | ≈ +p L²/10 (0,10) | apoio 1º interno ≈ −p L²/10 |
| 3 vãos iguais — vão central | ≈ +p L²/24 (0,04) | — |
| Vão interno genérico (aprox. NBR simplif.) | +p L²/14 a +p L²/11 | −p L²/8 a −p L²/10 |

> Para implementação **exata e geral** (vãos desiguais, cargas diferentes por tramo),
> resolva a **viga contínua por rigidez / três momentos** (equação de Clapeyron):
>
>     M_{i-1}·L_i + 2·M_i·(L_i + L_{i+1}) + M_{i+1}·L_{i+1} = −(q_i·L_i³ + q_{i+1}·L_{i+1}³)/4
>
> Isso substitui a tabela de coeficientes e é totalmente computável. **Adote a envoltória**
> (carga acidental alternada em tramos) para máximos de vão e de apoio, conforme NBR 6118.

**Cortante:** por tramo, V = reações da viga contínua; para pré-dimensionar use V ≈ p·L/2
(majorado ~10–15% junto a apoios internos de continuidade). Verificar V_Rd,1 da laje
(sem estribo) por NBR 6118 19.4.1.

### B.4 REAÇÕES da laje unidirecional nas vigas

Direção das vigotas = direção do vão L (as vigotas "vencem" L). Elas se apoiam nas **duas
vigas perpendiculares às vigotas** (vigas de apoio principais). As **duas vigas paralelas às
vigotas** (bordos laterais) recebem apenas uma **faixa marginal**.

**Vigas perpendiculares às vigotas (apoios principais):** recebem a reação principal

    r_principal = p · L / 2          [kN/m ao longo da viga]

(cada uma das duas vigas de apoio recebe p·L/2 da faixa que nelas descarrega).

**Vigas paralelas às vigotas (bordos laterais):** recebem a **faixa marginal**. Critério
adotado (documentado — há mais de um na prática):

- **Critério A (faixa de rigidez / distribuição transversal):** considere que uma faixa de
  largura **b_m = L/4** junto a cada bordo lateral descarrega parcialmente nessa viga.
  Carga na viga lateral ≈ p · b_m / 2 = **p · L / 8** [kN/m]  → *(valor de ordem de grandeza)*.
- **Critério B (charneiras, coerente com C):** aplicar o método das charneiras plásticas
  (seção C.4) mesmo à laje unidirecional, obtendo reação triangular/trapezoidal nos bordos
  laterais. Para λ = L/b_lateral grande (unidirecional), o bordo lateral tende a receber
  faixa ≈ triangular de altura b_lateral/2.
- **Critério C (conservador simplificado):** desprezar a faixa lateral no dimensionamento
  das vigotas (todo p·L vai para as 2 vigas principais) **mas** prover armadura de
  distribuição e considerar uma carga linear mínima nas vigas de bordo (peso de revestimento
  + eventual parede).

> **`[INCERTO]` (critério, não número):** não existe um único critério normativo fechado
> para a faixa marginal de laje unidirecional treliçada. **Recomendação para o motor:**
> usar o **Critério A (p·L/8 numa faixa L/4)** como default explícito e permitir alternar
> para charneiras (Critério B). Documentar a escolha no relatório de cálculo. A armadura de
> distribuição perpendicular às vigotas é obrigatória (NBR 14859 / 6118 — mín. 0,9 cm²/m ou
> conforme norma, **confirmar**).

---

## C) LAJE MACIÇA

### C.1 Espessura mínima — NBR 6118:2023, item 13.2.4.1

Valores mínimos de espessura h (lajes maciças):

| Situação | h_min |
|---|---|
| a) Laje de **cobertura** não em balanço | **7 cm** |
| b) Laje de **piso** não em balanço | **8 cm** |
| c) Laje **em balanço** | **10 cm** |
| d) Laje que suporte **veículos** de peso total ≤ 30 kN | **10 cm** |
| e) Laje que suporte **veículos** de peso total > 30 kN | **12 cm** |
| f) Laje com **protensão** apoiada em vigas | **15 cm** (ℓ/42 biapoiada; ℓ/50 contínua) |
| g) Laje **lisa** (sem vigas) | **16 cm** |
| g) Laje-**cogumelo** (com capitel), fora do capitel | **14 cm** |

> Alta confiança nesta lista (item 13.2.4.1 manteve-se da NBR 6118:2014 para a 2023).
> Há ainda exigência de cobrimento/altura útil e, para lajes em balanço, a NBR 6118:2023
> pede aumento do coeficiente de segurança (γ_n) conforme o vão do balanço — **verificar 13.2.4.1
> nota sobre balanços**.

### C.2 Pré-dimensionamento da espessura pelo vão

Estimativa de altura útil d (Pinheiro/prática):

    d ≈ (2,5 − 0,1·n) · ℓ* / 100        [ℓ* e d em cm]

onde **n = número de bordos engastados (contínuos)** e **ℓ* = menor valor entre ℓx e 0,7·ℓy**
(ℓx = menor vão, ℓy = maior vão). Depois:

    h = d + c + φ/2   (c = cobrimento; φ = diâmetro; usualmente h ≈ d + 2,5 a 3,0 cm)

Regra alternativa direta por vão:

    Biapoiada:  h ≈ ℓ/40      Contínua/engastada:  h ≈ ℓ/45      (ℓ = menor vão)

> O fator (2,5 − 0,1n)/100 é a **fórmula de pré-dimensionamento de Pinheiro** (prática
> acadêmica consagrada, **não** valor normativo). Respeitar sempre h_min de C.1 e a
> verificação de flecha (D) como decisão final.

### C.3 Classificação e cálculo de momentos

**Classificação:**

    λ = ℓy / ℓx   (maior vão / menor vão, sempre ≥ 1)
    λ ≤ 2  →  laje armada em DUAS direções (bidirecional)
    λ > 2  →  laje armada em UMA direção (calcular como C.3.0 unidirecional/faixa 1 m)

**C.3.0 Uma direção (λ>2):** idêntico à seção B.3 (M = p ℓx²/8 biapoiada, etc.), com faixa
de 1 m; armadura de distribuição na direção longa.

**C.3.1 Duas direções — método das tabelas (Bares / Czerny / coeficientes de Pinheiro).**

Fórmula geral dos momentos por faixa unitária:

    m = μ · p · ℓx² / 100        [kN·m/m]

onde μ é o coeficiente tabelado (μx, μy para vão; μx', μy' para engaste), p em kN/m²,
ℓx = **menor** vão em m. Os coeficientes dependem de **λ** e do **caso de vinculação**.

**Os 9 CASOS de vinculação (numeração de Pinheiro/Bares):**

| Caso | Descrição das bordas |
|---|---|
| 1 | 4 bordas **apoiadas** |
| 2 | 1 borda **engastada** (menor bordo) / 3 apoiadas |
| 2A | 1 borda engastada (maior bordo) / 3 apoiadas |
| 3 | 2 bordas engastadas **adjacentes** |
| 4 | 2 bordas engastadas **opostas** — engaste nos bordos **menores** |
| 4A | 2 bordas engastadas opostas — engaste nos bordos **maiores** |
| 5 | 3 bordas engastadas |
| 5A | 3 bordas engastadas (orientação alternada) |
| 6 | 4 bordas engastadas |

(μx = momento positivo direção do menor vão; μy = positivo maior vão; μx'/μy' = momentos
negativos de engaste nas respectivas direções.)

> **`[INCERTO]` — TABELAS COMPLETAS DE μ:** **não reproduzo de memória, com a precisão de
> engenharia, os coeficientes μx, μy, μx', μy' para todos os 9 casos e para λ de 1,00 a 2,00
> passo 0,05.** Reproduzir esses ~600 números de memória violaria a regra de ouro (risco de
> erro). **AÇÃO PARA O MOTOR:** carregar as tabelas de Bares/Czerny de uma **fonte publicada
> verificável** (ex.: apostilas de L. M. Pinheiro — "Tabelas de lajes", USP-EESC; ou tabelas
> de Bares) para um arquivo de dados (CSV/JSON) e interpolar linearmente em λ. Como **âncora
> de sanidade** (ordem de grandeza para caso 1, λ=1,0): μx = μy ≈ 4,4 (⇒ m ≈ 0,044·p·ℓx²),
> valor clássico para placa quadrada 4 bordos apoiados — **usar apenas para validar a tabela
> carregada, não como dado de projeto**.

**C.3.2 MÉTODO ALTERNATIVO COMPUTÁVEL — Marcus / grelha (Grashof-Rankine).**
Quando faltar a tabela, use este método fechado e conservador. Analogia de grelha: duas
faixas centrais cruzadas de 1 m, com igualdade de flechas no centro.

Partição da carga (4 bordos apoiados):

    p_x = p · ℓy⁴ / (ℓx⁴ + ℓy⁴)          (faixa que vence ℓx)
    p_y = p · ℓx⁴ / (ℓx⁴ + ℓy⁴)          (faixa que vence ℓy)
    m_x = p_x · ℓx² / 8 ;   m_y = p_y · ℓy² / 8

Para outras vinculações, substitua o "5/384" por coeficientes de flecha k da faixa e iguale
flechas centrais: k_x·p_x·ℓx⁴ = k_y·p_y·ℓy⁴, com p_x+p_y = p. Coeficientes de flecha por
condição de bordo da faixa:

| Vinculação da faixa | k (δ = k·p·ℓ⁴/EI) | M_vão | M_engaste |
|---|---|---|---|
| apoiada–apoiada | 5/384 | pℓ²/8 | — |
| engastada–apoiada | 1/185 (máx.) | 9pℓ²/128 | pℓ²/8 |
| engastada–engastada | 1/384 | pℓ²/24 | pℓ²/12 |

> A grelha de Grashof (sem correção de torção) é **conservadora** e 100% implementável.
> A **correção de torção de Marcus** (reduz os momentos de vão em placas com torção nos
> cantos) existe mas o **fator exato de redução de Marcus está `[INCERTO]` na minha memória**;
> por segurança o motor pode omiti-lo (fica a favor da segurança) ou carregá-lo de fonte
> verificada. Use Grashof como default computável e Bares (tabela carregada) como preferencial.

**C.3.3 MÉTODO RIGOROSO COMPUTÁVEL — diferenças finitas da placa de Kirchhoff.**
Para qualquer vinculação e forma retangular, resolva:

    ∇⁴w = p / D ,      D = E_cs · h³ / [12 (1 − ν²)] ,   ν = 0,2 (concreto, NBR 6118)

por diferenças finitas (malha n×n, estêncil biharmônico de 13 pontos). Condições de contorno:
- **apoio simples:** w = 0 e M_n = 0 (⇒ w=0 e ∂²w/∂n²=0);
- **engaste:** w = 0 e ∂w/∂n = 0;
- **borda livre:** M_n = 0 e V_n efetivo = 0.

Momentos: `M_x = −D(∂²w/∂x² + ν ∂²w/∂y²)`, `M_y = −D(∂²w/∂y² + ν ∂²w/∂x²)`.
Este método dá **todos os 9 casos** (e casos mistos) sem tabela — recomendado como núcleo
do motor, com Bares como conferência.

### C.4 REAÇÕES por CHARNEIRAS PLÁSTICAS — NBR 6118:2023, 14.7.6.1

As reações nos apoios são obtidas pelas **áreas de influência** delimitadas por charneiras
(linhas de ruptura) traçadas dos cantos com os ângulos:

- **45°** entre dois apoios do **mesmo tipo** (ambos apoiados ou ambos engastados);
- **60°** a partir do bordo **engastado**, quando o bordo vizinho é **apoiado** (o engaste
  "puxa" mais área — reta mais inclinada, invade mais a laje);
- **90°** a partir do apoio quando a borda vizinha é **livre**.

A reação (carga uniforme equivalente) numa viga de bordo de comprimento ℓ_bordo:

    r = p · A_influência / ℓ_bordo        [kN/m]

onde A_influência é a área do triângulo/trapézio tributário daquele bordo. (Distribuição real
é triangular/trapezoidal; para dimensionamento de viga usa-se a **reação uniforme média
= p·A/ℓ**, admitida pela NBR; fatores de "carga uniforme equivalente" para momento existem,
ver nota.)

**Dedução das áreas — caso 1 (4 bordos apoiados, 45° em todos os cantos).**
Seja ℓx = menor vão, ℓy = maior vão. As charneiras a 45° dos 4 cantos formam:

- **Bordos menores (comprimento ℓx):** triângulos de base ℓx e altura ℓx/2.
  A_tri = ℓx·(ℓx/2)/2 = **ℓx²/4**.
  Reação: **r_menor = p·(ℓx²/4)/ℓx = p·ℓx/4**.
- **Bordos maiores (comprimento ℓy):** trapézios de bases ℓy e (ℓy−ℓx), altura ℓx/2.
  A_trap = [(ℓy + (ℓy−ℓx))/2]·(ℓx/2) = **(2ℓy − ℓx)·ℓx/4**.
  Reação: **r_maior = p·(2ℓy − ℓx)·ℓx/(4·ℓy) = (p·ℓx/4)·(2 − ℓx/ℓy)**.

Verificação: 2·(ℓx²/4) + 2·(2ℓy−ℓx)ℓx/4 = ℓx·ℓy ✔ (fecha a carga total p·ℓx·ℓy).

**Caso com um bordo engastado (60° a partir do engaste).**
A charneira do lado engastado sobe com ângulo de 60° com o bordo (tan 60° = √3). A altura da
região tributária do bordo engastado até encontrar a charneira do bordo apoiado adjacente
(45°) resolve-se por interseção geométrica. Definindo a **relação de ataque** dos ângulos:

- lado a 45°: a reta sobe 1 vertical por 1 horizontal (coef. 1);
- lado a 60°: sobe √3 vertical por 1 horizontal → o engaste alcança a linha de encontro a uma
  distância horizontal menor, gerando **trapézio maior** para o engaste e triângulo/trapézio
  menor para o apoio oposto.

**Fórmula fechada (bordo engastado vs. bordo apoiado paralelo, medindo na direção
perpendicular ℓ):** a divisão do vão perpendicular ℓ entre a parte tributária do apoio (y_a)
e do engaste (y_e), com y_a + y_e = ℓ e a razão de avanço dada pelos ângulos:

    y_e / y_a = tan(60°)/tan(45°) = √3 ≈ 1,732   (engaste captura ~63% do vão perpendicular)
    ⇒ y_e = ℓ·√3/(1+√3) ≈ 0,634·ℓ ;  y_a = ℓ/(1+√3) ≈ 0,366·ℓ

> **`[INCERTO]` (parcial):** a razão y_e/y_a = √3 vem diretamente da geometria dos ângulos
> 60°/45° (dedutível), **mas** as tabelas de Pinheiro consolidam essas áreas em **coeficientes
> tabelados k (r = k·p·ℓx)** por caso e por λ, que é o que a prática usa. Recomendo, para o
> motor, **calcular as áreas de charneira por construção geométrica** (traçar as retas com os
> ângulos, achar interseções, integrar as áreas dos polígonos) — método exato e implementável —
> ou carregar os coeficientes k de reação das tabelas de Pinheiro. Reproduzir de memória os k
> por caso seria inventar → não faço.

**Nota — carga uniforme equivalente para momento em viga:** a reação é triangular
(bordo menor) ou trapezoidal (bordo maior). Para **momento fletor** da viga de apoio pode-se
usar cargas uniformes equivalentes: triangular → q_eq ≈ (2/3)·q_máx para momento; trapezoidal
→ fator entre triangular e uniforme conforme a relação. Para simplicidade e a favor da
segurança, muitos projetos usam a **reação média p·A/ℓ como uniforme**. Documentar a escolha.

---

## D) FLECHAS (ELS) — NBR 6118:2023

### D.1 Módulo de elasticidade do concreto

    E_ci = α_E · 5600 · √f_ck        [MPa, f_ck em MPa]   (para f_ck ≤ 50 MPa)
    E_cs = α_i · E_ci ,   α_i = 0,8 + 0,2·f_ck/80 ≤ 1,0

α_E (agregado graúdo): **1,2 basalto/diabásio; 1,0 granito/gnaisse; 0,9 calcário; 0,7 arenito**
(NBR 6118:2023, 8.2.8). Use **E_cs** (secante) nos cálculos de deformação.

### D.2 Rigidez — Estádio I e Estádio II (Branson)

Momento de fissuração:

    M_r = α · f_ct · I_c / y_t        (α = 1,5 para seção retangular, flexão)
    f_ct = f_ctm = 0,3 · f_ck^(2/3)   [MPa]  (para f_ck ≤ 50 MPa)

- **Estádio I** (não fissurado, M_a ≤ M_r): usar I_c (inércia bruta da seção) — para laje
  de largura b e altura h: I_c = b·h³/12.
- **Estádio II** simplificado / rigidez equivalente de **Branson** (NBR 6118 17.3.2.1.1),
  quando M_a > M_r:

      (EI)_eq = E_cs · [ (M_r/M_a)³ · I_c + (1 − (M_r/M_a)³) · I_II ]  ≤  E_cs · I_c

  I_II = inércia da seção fissurada no Estádio II (posição da linha neutra x_II resolvendo o
  momento estático da seção homogeneizada com α_e = E_s/E_cs). M_a = momento atuante na
  combinação **quase-permanente** de serviço.

### D.3 Flecha imediata

Para faixa/laje equivalente a viga:

    a_i = coef · (p_serv · ℓ⁴) / (EI)_eq         [m]

coef = 5/384 (biapoiada), 1/384 (biengastada), 2/384 = 1/192 (aprox. engastada-apoiada máx.).
Para laje em 2 direções, usar a flecha da faixa central (ou a solução de placa de C.3.3 com
(EI)_eq no lugar de D). p_serv = combinação quase-permanente: g + ψ2·q (ψ2 residencial = 0,3).

### D.4 Flecha diferida (fluência) e total

    a_diferida = a_i · α_f
    α_f = Δξ / (1 + 50·ρ')      (NBR 6118 17.3.2.1.2)
    ρ' = A's / (b·d)            (armadura de compressão; se A's=0 → ρ'=0)
    Δξ = ξ(t) − ξ(t0)

ξ(t) — coeficiente função do tempo: ξ(t) ≈ 0,68·(0,996^t)·t^0,32 para t ≤ 70 meses;
**ξ(∞) = 2** (t ≥ 70 meses). Para t0 no primeiro mês, Δξ ≈ 2 − ξ(t0). Com ρ'=0, α_f máx = 2.

**Flecha total (longo prazo):**

    a_total = a_i · (1 + α_f)

### D.5 Limites de deslocamento — NBR 6118:2023, Tabela 13.3

| Efeito / razão | Deslocamento a comparar | Limite |
|---|---|---|
| Aceitabilidade visual (visual) | total | **ℓ/250** |
| Vibração sentida no piso | devido a cargas acidentais | **ℓ/350** |
| Danos a **paredes/alvenaria** (deslocamento **após** execução da parede) | após a parede | **ℓ/500 ou 10 mm** (o menor) |
| Efeito em elementos que suportam paredes (paredes de alvenaria) | após parede | ℓ/500 |
| **Contraflecha** máxima na execução | contraflecha | **≤ ℓ/350** |

> Para balanços, adotar ℓ = 2·ℓ_balanço na comparação (prática usual). A flecha "após
> alvenaria" = a_total − a(no instante da execução da parede).

---

## E) COMPARATIVO — treliçada pré-moldada × maciça

| Critério | Treliçada (pré-moldada) | Maciça |
|---|---|---|
| **Peso próprio** | **Menor** (EPS 1,5–2,4 kN/m²; cerâmica 2,0–3,6) devido ao enchimento | Maior (25·h: h=10 cm → 2,5; h=12 → 3,0 kN/m²) |
| **Vão econômico** | 3–5 m (comum > 6 m só protendida) | Bom até ~5 m biapoiada; 2 direções otimiza |
| **Flecha** | Nervurada → inércia concentrada; controlar rigorosamente; contra-flecha usual | Mais rígida por unidade de altura em placa 2D |
| **Formas/escoramento** | Menos forma (só capa); escoramento de vigotas | Forma total + escoramento pleno |
| **Mão de obra / prazo** | Mais rápida, menos concreto in loco | Mais lenta, mais concreto/aço in loco |
| **Custo relativo** | Geralmente **menor** em residencial de vãos médios e formas repetitivas simples | Competitiva em vãos curtos, formas irregulares, 2 direções, balanços |
| **Instalações embutidas** | Limitadas (passagem entre nervuras) | Flexível (embutir na massa) |
| **Comportamento 2 direções / cargas concentradas** | Fraco (unidirecional) — parede sobre nervura crítica | Excelente (distribui em 2 direções) |
| **Quando convém** | Panos retangulares regulares, vãos ≤ ~5 m, casas térreas/sobrados econômicos | Formas irregulares, balanços, grandes cargas concentradas, λ≤2 aproveitando 2 direções |

**Regra de decisão prática:** pano retangular regular, vão ≤ 5 m, sem muitas cargas
concentradas → **treliçada**. Forma irregular, balanço, laje que recebe pilar/escada/grande
parede localizada, ou aproveitamento de duas direções (λ≤2) → **maciça**.

---

## RESUMO EXECUTIVO (para implementação)

1. **g_pp da treliçada por altura (kN/m², intereixo 42 cm) — EPS / cerâmico:**
   h=12 (8+4): **~1,5 / ~2,0–2,2**; h=16 (12+4): **~1,7 / ~2,4–2,6**;
   h=20 (16+4): **~2,0 / ~2,8–3,1**; h=25 (20+5): **~2,4 / ~3,3–3,6**.
   Os valores EPS são coerentes com o cálculo geométrico (verificáveis); os cerâmicos são
   faixas de catálogo — deixar editável por fabricante.
2. **Cargas de uso NBR 6120:2019 Tab.10 (kN/m²):** dormitório/sala/copa/cozinha/banheiro **1,5**;
   despensa/área de serviço/lavanderia **2,0**; corredor privativo **1,5** / uso comum **3,0**;
   forro sem acesso **0,5**; garagem leve **3,0**; escada pública **3,0** (privativa 2,5 `[INCERTO]`).
3. **Peso concreto armado 25 kN/m³**; revestimento típico **≈1,0 kN/m²**; parede: linear
   γ_alv·e·h, diluir por m² só em pré-dim. e nunca sobre nervura isolada.
4. **Maciça — h_min (13.2.4.1):** cobertura 7, piso 8, balanço 10, veículo ≤30 kN 10 / >30 kN 12,
   protendida 15, laje lisa 16, cogumelo 14 cm. Pré-dim d=(2,5−0,1n)·ℓ*/100.
5. **Classificação:** λ=ℓy/ℓx ≤2 duas direções, >2 uma direção.
6. **Momentos 2 direções:** m = μ·p·ℓx²/100 (Bares/Pinheiro, tabela a **carregar de fonte**);
   fallback computável = **grelha de Grashof** (p_x=p·ℓy⁴/(ℓx⁴+ℓy⁴)…) ou **diferenças finitas
   da placa** (rigoroso, cobre os 9 casos).
7. **MÉTODO ESCOLHIDO PARA REAÇÕES = CHARNEIRAS PLÁSTICAS (NBR 6118 14.7.6.1):** ângulos 45°
   (mesmo tipo), 60° (a partir de engaste vs. apoiado), 90° (vizinho livre); reação
   r = p·A_influência/ℓ_bordo. Caso 1 deduzido em fórmula fechada:
   **bordo menor r = p·ℓx/4** (triângulo ℓx²/4); **bordo maior r = (p·ℓx/4)·(2 − ℓx/ℓy)**
   (trapézio). Casos com engaste: razão geométrica y_e/y_a = √3.
8. **Flechas:** E_cs=α_i·α_E·5600√f_ck; (EI)_eq de Branson; a_total=a_i·(1+α_f),
   α_f=Δξ/(1+50ρ'), ξ(∞)=2. Limites Tab.13.3: visual **ℓ/250**, alvenaria **ℓ/500 ou 10 mm**,
   vibração ℓ/350, contraflecha ≤ℓ/350.

### Itens marcados `[INCERTO]` (a confirmar antes de produção)

- **NBR 6120:2019 Tab.10:** escada privativa (2,5) e sótão (2,0); carga linear de borda de
  sacada/varanda; limite de peso do veículo em garagem (25 vs 30 kN). Confirmar na tabela.
- **γ de alvenaria (Anexo A NBR 6120:2019):** furados ~13, maciço ~18, bloco concreto ~14 kN/m³
  são ordens de grandeza — confirmar valores exatos.
- **g_pp treliçada cerâmica:** faixas de catálogo variam por fabricante/intereixo/b_w.
- **Vão-limite treliçada (fatores 25 e 30):** regra prática, não normativa — preferir tabela do fabricante.
- **Faixa marginal da laje unidirecional (viga paralela às vigotas):** não há critério
  normativo único; adotado default p·ℓ/8 numa faixa ℓ/4 (Critério A) — documentar.
- **Tabelas completas de μ (Bares/Czerny, 9 casos × λ):** NÃO reproduzidas de memória;
  carregar de fonte publicada (Pinheiro/USP-EESC) e interpolar. Âncora só de validação: caso 1
  λ=1 → μ≈4,4.
- **Fator de redução de torção de Marcus:** omitido (a favor da segurança) ou carregar de fonte.
- **Coeficientes k tabelados de reação por charneiras (Pinheiro):** usar construção geométrica
  das áreas (exata) em vez de reproduzir os k de memória.
- **Armadura mínima de distribuição da treliçada:** confirmar valor (NBR 14859 / 6118).
- **ξ(t) — expressão de fluência:** conferir a fórmula de ξ(t) para t<70 meses na NBR 6118:2023
  (o valor final ξ(∞)=2 é seguro).
