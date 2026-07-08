# DECISÕES — Módulo de Lajes (Polotto Engenharia)

Registro cronológico das decisões técnicas tomadas de forma autônoma durante a
implementação do Módulo de Cálculo de Lajes (pré-moldada treliçada + maciça),
integrado aos módulos existentes de Vigas e Pilares.

> Ferramenta de **pré-dimensionamento e estudo**; não substitui projeto
> estrutural assinado por profissional habilitado (disclaimer fixo na UI).

---

## D0 — Estratégia geral e ambiente (início)

- **Trabalhar em `main`**, com commits incrementais e mensagens claras.
  *Motivo:* é o fluxo que o usuário já usa (deploy automático no Streamlit
  Cloud a partir do `main`); o usuário não é técnico e quer o resultado já
  publicado. Segurança garantida por **git tag de restauração
  `v-antes-lajes` (= a2e07fa)** criada antes de começar.
- **Arquitetura** (segue o padrão já validado do projeto):
  - `motor_laje.py` — motor PURO de cálculo (sem Streamlit), testável, no
    estilo de `motor_viga.py`/`motor_pilar.py`.
  - `pagina_lajes.py` — interface Streamlit, no estilo de
    `pagina_vigas.py`/`pagina_pilar.py`, usando os helpers de `ui_comum.py`.
  - Integração via `st.session_state` (mesmo mecanismo dos exemplos que já
    pré-preenchem vigas/pilares).
- **Navegação:** adicionar 4ª opção "Lajes" ao seletor
  (`ui_comum.seletor_pagina`) e registrar a página nos dois pontos de entrada
  (`import numpy as np.py` e `app_polotto.py`), **sem alterar** os cálculos de
  Vigas/Pilares/Pilares Prévios.
- **Documentação:** `docs/lajes/` guarda a formulação de engenharia
  (`ENGENHARIA_LAJES.md`), auditoria de integração (`AUDITORIA_LAJES.md`) e
  verificação independente de coeficientes (`ENGENHARIA_VERIF.md`).
  `ROADMAP.md` (raiz) lista o top 5 de melhorias futuras. `README` do módulo
  em `docs/lajes/README_LAJES.md`.

## D1 — Equipe de agentes (fase de fundamentos)

Disparada em paralelo (workflow `lajes-research`):
- **Auditor de código** → mapa exato de integração (chaves de session_state
  de vigas/pilares, estrutura do dict de tramo, helpers de `ui_comum`, estilo).
- **Engenheiro estrutural sênior** → formulação NBR completa (cargas NBR 6120
  Tab. 10; peso próprio de laje treliçada por altura/enchimento; espessura
  mínima 13.2.4.1; momentos maciça 2 direções por tabelas de Bares/Czerny —
  coef. de Pinheiro, 9 casos; charneiras plásticas 14.7.6.1 p/ reações;
  flechas + limites Tab. 13.3; αf).
- **Verificador independente** → reproduz de forma independente os
  coeficientes/valores numéricos críticos, para cruzar com o engenheiro e
  eliminar valores alucinados.
- **Pesquisa de features/roadmap** → top 5 de utilidade para engenheiros e
  arquitetos.

*Regra:* qualquer coeficiente numérico só entra no motor se **confirmado por
QA / verificação cruzada**; divergências são documentadas aqui e resolvidas
pelo valor mais defensável (ou conservador).

## D2 — Reações por charneiras plásticas (método robusto, sem tabela)

**Decisão:** calcular as reações da laje nas vigas (NBR 6118 14.7.6.1) por um
método de **grade ponderada** (weighted nearest-edge), que reproduz EXATAMENTE
a regra normativa das inclinações sem depender de tabela de coeficientes:
- cada ponto da laje pertence à borda de menor "distância efetiva" =
  (distância perpendicular à borda) × peso;
- peso = **1,0** para borda apoiada e **1/√3 ≈ 0,577** para borda engastada;
- consequência geométrica exata: 45° entre bordas de mesmo tipo, **60° a
  partir da borda engastada** quando a vizinha é apoiada (borda livre → peso
  ∞, não recebe carga → laje arma na direção oposta).
- Reação de cada viga = p × (área tributária da borda); **carga uniforme
  equivalente** q_eq = p·A_borda / L_borda (kN/m).

*Motivo:* elimina o risco de coeficientes de tabela alucinados; funciona para
os 9 casos de apoio e qualquer λ; a integração laje→viga→pilar (o diferencial
do módulo) fica ancorada em geometria exata, não em tabela frágil.
**Validado numericamente** (prototipo): quadrada 4 apoiadas → q=p·L/4;
retângulo 4×6 → áreas exatas (curtas lx²/4, longas trapézio); soma das forças
= p·A_total (conservação) em todos os casos; borda engastada atrai mais carga.

## D3 — Integração laje → vigas / pilares SEM alterar as páginas existentes

**Decisão:** o botão "Enviar para Vigas" seta diretamente as chaves de estado
já existentes e navega com `st.switch_page`:
- Vigas: `ss.viga_b/h/fck/cob` (seção) e `ss.lista_vaos` = lista de tramos
  `{'tipo','L','q','P','a'}` com **q e P em kN internos** (confirmado:
  `pagina_vigas` divide a entrada por `fu`, guarda em kN). `ss.res=None`.
- Pilares: `ss.pilar_Nk` = Nk_kN × fu (unidade de exibição — o seletor de
  unidade é COMPARTILHADO via mesma chave de session_state entre páginas),
  e opcionalmente `ss.pilar_b/h/l0/fck/caa` do pré-dimensionamento.
  `ss.res_pilar=None`.
- O init de estado das páginas é protegido por `if <chave> not in ss`, então
  o pré-preenchimento NÃO é sobrescrito. **Zero alteração** em
  `pagina_vigas.py` / `pagina_pilar.py` (só leitura de estado que elas já
  fazem). **Confirmado pelo auditor**: `pilar_Nk` em unidade de exibição
  (×fu), `unidade_forca` compartilhada, tramo = `{'tipo','L','q','P','a'}`
  com q/P em kN internos.

## D4 — Momentos e flechas da laje maciça: solver de placa por diferenças finitas

**Decisão:** em vez de reproduzir tabelas de Bares/Czerny "de memória" (risco
de alucinação — os DOIS engenheiros recomendaram NÃO fazer isso), resolver a
**equação de placa de Kirchhoff** `D·∇⁴w = p` por **diferenças finitas**
(estêncil bi-harmônico de 13 pontos), com condições de contorno por nós-
fantasma: borda apoiada → w=0, w_nn=0 (reflexão ímpar); borda engastada →
w=0, w_n=0 (reflexão par). Cobre os **9 casos** de apoio e **qualquer λ**,
dá momentos positivos de vão (Mx, My), momentos negativos de engaste
(fórmula do nó-fantasma) e a flecha elástica, tudo determinístico.
- ν = 0,2 (NBR 6118 8.2.9, concreto).
- **Validado contra Timoshenko** (prototipo): SS quadrada w=0,00406·p·lx⁴/D
  e μ=4,42 (≈ Bares ν=0,2); retângulo 1×2 (ν=0,3) μx=10,16 / μy=4,66 /
  w=0,01013 (exatos); engastada 4 lados M_vão=0,0229 e **M_engaste=−0,0511**
  (Timoshenko 0,0231 e −0,0513). Erros < 2%.

## D5 — Flechas (ELS): estádio I + fluência (simplificação de pré-dim)

- Flecha imediata δ_i = solução elástica da placa com rigidez D usando **E_cs**
  (NBR 6118 8.2.8: Eci=5600√fck, αi=0,8+0,2·fck/80, Ecs=αi·Eci) e seção
  BRUTA (estádio I). *Motivo:* sem As não há como aplicar Branson; é
  simplificação usual de pré-dimensionamento — documentada e com alerta
  conservador.
- Flecha diferida por fluência: αf = Δξ/(1+50ρ'), ξ(∞)=2 (17.3.2.1.2);
  caso usual ρ'=0 → αf=2 → **δ_total = 3·δ_i**.
- Limites (Tab. 13.3): **visual δ_total ≤ L/250**; **após alvenaria**
  δ_pós ≈ 2·δ_i ≤ min(L/500, 10 mm). Contra-flecha ≤ L/350 quando aplicável.
- Alerta 🟢/🟡/🔴: verde se folga > 20%, amarelo até o limite, vermelho acima.

## D6 — Laje treliçada (unidirecional) e pesos próprios

- Arma na direção do MENOR vão (automático, editável). g_pp por altura/
  enchimento: **EPS por fórmula geométrica** (capa + nervuras a intereixo
  42 cm, verificável) e **cerâmico por faixa de catálogo** (editável por
  fabricante — marcado como valor de catálogo, não normativo).
- Esforços: biapoiada M=p·lx²/8, V=p·lx/2; contínua por coeficientes.
- Vão-limite (pré-dim): h recomendada ≈ lx/30 (biapoiada); alerta se a laje
  escolhida é insuficiente (sugere altura maior ou vigota protendida).
- Reações: as 2 vigas PERPENDICULARES às vigotas recebem p·lx/2 (kN/m); as
  vigas PARALELAS recebem faixa marginal (default: faixa lx/4 com p·lx/8) —
  critério documentado (sem regra normativa única; a favor da segurança na
  viga principal).

## D7 — Cargas (NBR 6120:2019 Tab. 10) — valores confirmados por 2 agentes

Dormitório/sala/cozinha/banheiro 1,5 · área de serviço/despensa 2,0 · forro
sem acesso 0,5 · corredor privativo 1,5 / comum 3,0 · garagem leve 3,0 ·
varanda/terraço com acesso ~2,5 (marcado a confirmar). Concreto 25 kN/m³.
