# Verificação Numérica Independente — Motor de Cálculo de Lajes

**Agente:** Verificador Numérico Independente (NBR 6118 / NBR 6120)
**Objetivo:** Produzir de forma independente os valores críticos, com nível de confiança, para cruzamento posterior.
**Referências:** ABNT NBR 6120:2019 (ações), ABNT NBR 6118:2014 (projeto de concreto), Timoshenko "Theory of Plates and Shells", Tabelas de Bares (Pinheiro/EESC-USP).

> Nota metodológica: onde possível, ancorei os coeficientes de placa nos valores exatos de Timoshenko (solução de Navier), que são independentes de tabela e portanto de ALTA confiança. As tabelas de Bares brasileiras usam ν diferente (≈0,2 ou 0), o que desloca os coeficientes — isso está sinalizado.

---

## 1. NBR 6120:2019 — Tabela 10 — Cargas acidentais (uso residencial)

| Uso | Carga acidental q (kN/m²) | Confiança |
|---|---|---|
| Dormitório | 1,5 | ALTA |
| Sala (estar/jantar) | 1,5 | ALTA |
| Cozinha (residencial) | 1,5 | MÉDIA (alguns projetistas usam 2,0) |
| Área de serviço / lavanderia | 2,0 | ALTA |
| Banheiro | 1,5 | ALTA |
| Corredor (dentro da unidade / uso restrito) | 1,5 | MÉDIA |
| Corredor / hall de uso comum (acesso ao público) | 3,0 | MÉDIA |
| Forro sem acesso a pessoas | 0,5 | ALTA |
| Terraço / varanda com acesso (comunicando c/ ambiente) | 2,5 | BAIXA/MÉDIA (regra: igual ao ambiente + carga linear de borda quando aplicável) |
| Garagem/estacionamento — veículos leves (≤ 25 kN por veículo) | 3,0 | ALTA |

**Observações de confiança:**
- Os 1,5 kN/m² para ambientes residenciais comuns e 2,0 para área de serviço são consolidados. ALTA.
- Varandas/terraços: a NBR 6120:2019 tem regra específica (carga do compartimento com que se comunica, e para bordas livres pode haver carga linear adicional). O valor 2,5 é uma referência conservadora — **marcar como ponto a confirmar na tabela impressa**. BAIXA/MÉDIA.
- Garagem 3,0 kN/m² vale para veículos de passageiros; conferir se há exigência de carga concentrada de roda em paralelo.

---

## 2. Peso próprio — Laje treliçada (kN/m²), valores típicos de catálogo nacional

Convenção: h = altura total (enchimento + capa). Capa típica: 4 cm até h≈16; 5 cm para h≥20.
Peso próprio (g) inclui nervuras + enchimento + capa, SEM revestimento/contrapiso.

| h (cm) | Capa (cm) | Enchimento CERÂMICO g (kN/m²) | Enchimento EPS g (kN/m²) | Confiança |
|---|---|---|---|---|
| 12 | 4 | ~1,8 – 2,0 | ~1,4 – 1,5 | MÉDIA |
| 16 | 4 | ~2,2 – 2,4 | ~1,6 – 1,8 | MÉDIA |
| 20 | 5 | ~2,8 – 3,0 | ~2,0 – 2,2 | MÉDIA |
| 25 | 5 | ~3,3 – 3,5 | ~2,4 – 2,6 | MÉDIA/BAIXA |

**Confiança MÉDIA geral:** variam entre fabricantes (Lajes Patente, Premo, etc.). Ordem de grandeza correta; a diferença EPS × cerâmico (~0,4–0,7 kN/m² a favor do EPS) é robusta. Recomenda-se travar os números pelo catálogo do fornecedor específico do projeto. Valor de referência para peso do concreto armado = 25 kN/m³.

---

## 3. Espessura mínima — Laje maciça (NBR 6118:2014, item 13.2.4.1)

| Situação | Espessura mínima (cm) | Confiança |
|---|---|---|
| Laje de cobertura/forro, não em balanço | 7 | ALTA |
| Laje de piso, não em balanço | 8 | ALTA |
| Laje em balanço | 10 | ALTA |
| Laje que suporta veículos ≤ 30 kN | 10 | ALTA |
| Laje que suporta veículos > 30 kN | 12 | ALTA |
| Laje lisa (sem capitel) | 16 | MÉDIA |
| Laje-cogumelo (com capitel) | 14 | MÉDIA |

Regra do item também exige, para lajes em balanço, que os esforços de cálculo sejam multiplicados por um coeficiente adicional γn (majoração) conforme 13.2.4.1 — verificar γn (função da espessura) à parte.

---

## 4. Laje maciça retangular apoiada nos 4 lados (Caso 1) — coeficientes de momento e flecha

λ = ly/lx (lx = menor vão). Momento: **m = μ · p · lx² / 100**.

### Valores EXATOS (Timoshenko, ν = 0,3) — ALTA confiança
Formato: μx (momento no vão, direção lx) / μy (direção ly) / αw (flecha, na forma w = αw·p·lx⁴/D, com D = E·h³/[12(1−ν²)]).

| λ = ly/lx | μx (Mx) | μy (My) | αw (flecha ×p·lx⁴/D) |
|---|---|---|---|
| 1,00 | 4,79 | 4,79 | 0,00406 |
| 1,25 | ~6,37 | ~5,00 | ~0,00603 |
| 1,50 | 8,12 | 4,98 | 0,00772 |
| 1,75 | ~9,30 | ~4,75 | ~0,00930 |
| 2,00 | 10,17 | 4,64 | 0,01013 |
| ∞ (faixa) | 12,50 | — | 0,01302 |

- Placa quadrada (λ=1): **μx = μy = 4,79** (ν=0,3). Flecha central exata **w = 0,00406·p·lx⁴/D**.
- λ=2: **μx = 10,17**, μy = 4,64.

### Equivalência com as Tabelas de Bares (ν ≈ 0,2) — MÉDIA confiança
As tabelas brasileiras (Bares/Pinheiro) usam Poisson menor, o que reduz o coeficiente de momento para a placa quadrada para a faixa **μ ≈ 4,4** (o "~4,41" citado no enunciado bate com ν≈0,2). Portanto:

- **λ=1, Caso 1: μx = μy ≈ 4,4** (Bares, ν=0,2) — **CONFIRMO a ordem 4,4** (não 4,41 exato; depende do ν adotado). MÉDIA.
- λ=2, Caso 1: μx ≈ 10,2, μy ≈ 3,5–4,6 (a componente μy varia mais entre tabelas). BAIXA/MÉDIA.

Flecha nas tabelas de Bares costuma vir na forma **w = (α/100)·p·lx⁴/(E·h³)**. Convertendo o exato de Timoshenko (λ=1): α = 0,00406·12·(1−0,2²) ≈ **0,0468**, i.e. coeficiente ≈ 4,68 nessa notação. MÉDIA.

**Alerta de cruzamento:** se o outro agente informar μ≈4,4 ele está usando Bares (ν=0,2); se informar μ≈4,79 está usando Timoshenko (ν=0,3). Ambos corretos — divergência é só de Poisson, não erro.

---

## 5. Reações de apoio por charneiras plásticas (laje quadrada, 4 bordas apoiadas)

Charneiras a 45° (bordas de mesmo tipo). Cada borda recebe um triângulo tributário.

**Geometria (ALTA confiança):**
- Triângulo por borda: base = lx, altura = lx/2.
- Área tributária por borda = (1/2)·lx·(lx/2) = **lx²/4**.
- 4 triângulos = lx² = área total da laje. ✔ (fecha)

**Reação total por borda (força):** V = p · lx²/4.
**Reação média distribuída por metro de borda:** **v_méd = p · lx / 4** = 0,25·p·lx. — ALTA.

**Distribuição real:** triangular, com ordenada máxima no meio da borda **v_máx = p · lx / 2** = 0,50·p·lx.

**Cargas uniformes equivalentes (para dimensionar a viga de apoio) — MÉDIA confiança:**
- Equivalente para CORTANTE / reação total (área): **v_eq,V = p·lx/4** (a própria média).
- Equivalente para MOMENTO (mesmo M máx que a carga triangular): para carga triangular simétrica em viga biapoiada, M = v_máx·L²/12 = q_eq·L²/8 ⇒
  **v_eq,M = (2/3)·v_máx = (2/3)·(p·lx/2) = p·lx/3 ≈ 0,333·p·lx.**

Fórmula geral do trapézio/triângulo (laje retangular, borda menor recebe triângulo, borda maior recebe trapézio):
- Triângulo (borda de comprimento lx): carga máx = p·lx/2; equivalente em momento = p·lx/3; equivalente em cortante = p·lx/4.
- Trapézio (borda de comprimento ly, laje retangular λ>1): reação máx = p·lx/2 no patamar; usar os fatores de uniformização de Pinheiro (função de λ) — fora do escopo quadrado, marcar como item a detalhar.

**Resumo laje quadrada:** cada borda → total p·lx²/4; distribuição triangular pico p·lx/2; uniforme equiv. cortante 0,25·p·lx; uniforme equiv. momento ~0,333·p·lx.

---

## 6. Fator de fluência / flecha diferida αf (NBR 6118:2014, item 17.3.2.1.2)

**Fórmula (ALTA confiança):**

  αf = Δξ / (1 + 50·ρ')

- ρ' = As'/(b·d) = taxa de armadura de COMPRESSÃO (se não houver As', ρ'=0).
- Δξ = ξ(t) − ξ(t₀).
- **ξ(t) = 0,68 · (0,996^t) · t^0,32**, para t ≤ 70 meses;
- **ξ(t) = 2,0**, para t ≥ 70 meses (valor final). — **CONFIRMO ξ(∞) = 2**. ALTA.
- t em meses; t₀ = idade (meses) na aplicação da carga de longa duração.

**Valores de ξ(t) (ALTA confiança na tendência):**

| t (meses) | ξ(t) |
|---|---|
| 0 | 0 |
| 1 | ~0,68 |
| 6 | ~1,20 |
| 12 | ~1,43 |
| 24 | ~1,70 |
| 48 | ~1,92 |
| ≥70 | 2,00 |

**Caso usual (ρ' = 0, carga aplicada em t₀→0, t→∞):**
- Δξ = ξ(∞) − ξ(0) = 2 − 0 = 2.
- **αf = 2 / (1 + 0) = 2,0.**
- **Multiplicador da flecha imediata: (1 + αf) = 3,0.** — flecha total diferida = 3× a flecha imediata. ALTA.

Se houver armadura de compressão (ρ'>0), αf < 2 e o multiplicador cai (ex.: ρ'=0,5% ⇒ αf = 2/(1+0,25) = 1,6 ⇒ multiplicador 2,6).

---

## RESUMO NUMÉRICO (itens 1–6)

**1. Cargas acidentais NBR 6120:2019 (kN/m²):** Dormitório 1,5 | Sala 1,5 | Cozinha 1,5 | Área serviço 2,0 | Banheiro 1,5 | Corredor unidade 1,5 (comum/público 3,0) | Forro sem acesso 0,5 | Terraço/varanda c/ acesso ~2,5 | Garagem leve 3,0.

**2. Peso próprio treliçada (kN/m²) [cerâmico / EPS]:** h12 ~1,8–2,0 / 1,4–1,5 (capa 4) | h16 ~2,2–2,4 / 1,6–1,8 (capa 4) | h20 ~2,8–3,0 / 2,0–2,2 (capa 5) | h25 ~3,3–3,5 / 2,4–2,6 (capa 5).

**3. Espessura mínima maciça (cm):** Forro/cobertura 7 | Piso 8 | Balanço 10 | Veículo ≤30 kN 10 | Veículo >30 kN 12 | Lisa 16 | Cogumelo 14.

**4. Placa 4 apoios (Caso 1), m = μ·p·lx²/100:** λ=1 → μ = 4,79 (ν=0,3, exato) ≈ 4,4 (Bares ν=0,2); flecha w=0,00406·p·lx⁴/D. λ=2 → μx = 10,17, μy = 4,64. Tabela λ=1,0/1,25/1,5/1,75/2,0 fornecida acima (Timoshenko).

**5. Charneiras 45° (laje quadrada):** área tributária/borda = lx²/4; reação total/borda = p·lx²/4; distribuição triangular pico p·lx/2; uniforme equiv. cortante 0,25·p·lx; uniforme equiv. momento ~0,333·p·lx (= p·lx/3).

**6. Flecha diferida:** αf = Δξ/(1+50·ρ'); ξ(∞) = 2 (CONFIRMADO); caso usual ρ'=0 ⇒ αf = 2,0 ⇒ multiplicador (1+αf) = 3,0.

**Confianças por item:** (1) ALTA na maioria, BAIXA/MÉDIA em varanda/corredor comum. (2) MÉDIA (varia por fabricante). (3) ALTA. (4) ALTA nos valores exatos Timoshenko; MÉDIA na equivalência com Bares/ν. (5) ALTA na geometria e média; MÉDIA na carga equivalente. (6) ALTA.
