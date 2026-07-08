# AUDITORIA DE INTEGRAÇÃO — Módulo de Lajes → Vigas / Pilares

Polotto Engenharia · App Streamlit NBR 6118
Objetivo: mapear com precisão os pontos de integração para um NOVO módulo de
Lajes que precisa **pré-preencher** os módulos existentes de Vigas e de
Pilares (botões "Enviar para Vigas" / "Enviar para Pilares").

Arquivos auditados: `pagina_vigas.py`, `pagina_pilar.py`,
`pagina_pilar_previo.py`, `ui_comum.py`, `motor_viga.py`, `motor_pilar.py`,
`import numpy as np.py`, `app_polotto.py`.

---

## 1. `pagina_vigas.py` — chaves de `st.session_state`

`ss = st.session_state`. Inicialização (linhas 42-58):

```python
if 'lista_vaos' not in ss:      ss.lista_vaos = []        # lista de tramos
if 'edit_index' not in ss:      ss.edit_index = None      # índice em edição
if 'res' not in ss:             ss.res = None             # resultado do motor
if 'res_fp' not in ss:          ss.res_fp = None          # "fingerprint" (json)
if 'confirmar_limpar' not in ss: ss.confirmar_limpar = False
if 'q_sugerido' not in ss:      ss.q_sugerido = None      # carga do assistente (kN/m INTERNO)
for _k, _v in (('viga_b', 15.0), ('viga_h', 50.0), ('viga_fck', 25),
               ('viga_cob', 2.5)):
    if _k not in ss: ss[_k] = _v
```

### Seção (concreto/aço) — chaves de widget `number_input(key=...)`
| chave | tipo | unidade | default | widget |
|-------|------|---------|---------|--------|
| `viga_b`   | float | cm  | 15.0 | Base bw [cm] (min 10, max 100) |
| `viga_h`   | float | cm  | 50.0 | Altura h [cm] (min 15, max 200) |
| `viga_fck` | int   | MPa | 25   | Concreto fck [MPa] (20–50, step 5) |
| `viga_cob` | float | cm  | 2.5  | Cobrimento c [cm] (2.0–5.0, step 0.5) |

Peso próprio: checkbox local `pp` (não é chave de estado persistente); entra
em `dados_g = {'b','h','fck','cob','peso_proprio': pp}`.

### Lista de tramos — `ss.lista_vaos`
É uma **lista de dicts**. Cada tramo tem EXATAMENTE estas 5 chaves
(inserção linha 205-206; edição linha 254-255):

```python
{'tipo': tipo, 'L': L_in, 'q': q_in, 'P': P_in, 'a': a_val}
```

| campo | tipo | unidade | significado |
|-------|------|---------|-------------|
| `tipo` | str   | —   | "Normal" \| "Balanço Esquerdo" \| "Balanço Direito" |
| `L`    | float | m   | comprimento do vão / balanço (>0) |
| `q`    | float | **kN/m INTERNO** | carga distribuída (NÃO em kgf) |
| `P`    | float | **kN INTERNO**   | carga concentrada (0.0 se não houver) |
| `a`    | float | m   | posição de P medida da esquerda do tramo (0.0 se não houver) |

**IMPORTANTE — unidades:** o app converte a exibição para kgf via `fu`, mas
`q` e `P` são **sempre armazenados em kN internamente**. Na UI:
`q_in = (q_disp or 0.0) / fu` e `P_in = (P_disp or 0.0) / fu` (linhas 182-183).
Quem preencher `lista_vaos` por código deve gravar **kN**, não kgf.

Valores de `tipo` aceitos: `["Normal", "Balanço Esquerdo", "Balanço Direito"]`
(selectbox, linhas 150 e 214). Regras: no máximo **um** "Balanço Esquerdo" e
**um** "Balanço Direito"; deve existir pelo menos 1 "Normal" para calcular.
Os nomes exibidos ("Vão 1", "Vão 2"...) são derivados da posição pela função
`nomes_tramos(lista)` (linha 73) — não são armazenados.

### `carregar_exemplo_viga(ex)` — como preenche o estado (linha 61)
```python
def carregar_exemplo_viga(ex):
    ss.viga_b   = float(ex['secao']['b'])
    ss.viga_h   = float(ex['secao']['h'])
    ss.viga_fck = int(ex['secao']['fck'])
    ss.viga_cob = float(ex['secao']['cob'])
    ss.lista_vaos = [dict(t) for t in ex['tramos']]   # COPIA cada dict
    ss.res = None
    ss.edit_index = None
    ss.q_sugerido = None
    ss.confirmar_limpar = False
```
Estrutura do dict `ex` (ver `EXEMPLOS_VIGA` em `ui_comum.py`):
```python
{"nome": "...", "descr": "...",
 "secao": {"b": 15.0, "h": 45.0, "fck": 25, "cob": 2.5},
 "tramos": [{"tipo": "Normal", "L": 4.5, "q": 18.0, "P": 0.0, "a": 0.0}, ...]}
```
Observação: nos exemplos `q` já está em **kN/m** (ex.: 18.0), confirmando que
`lista_vaos` guarda kN internos.

### Flags de resultado / invalidação
- `ss.res` — dict retornado por `mv.calcular_viga(...)` ou `{'erros':[...]}`; `None` = sem resultado.
- `ss.res_fp` — `json.dumps([dados_g, ss.lista_vaos], sort_keys=True)`; se mudar, o resultado é invalidado (linha 297-311).
- Pré-preencher/alterar `lista_vaos` ou `viga_*` deve zerar `ss.res = None` para evitar mostrar resultado velho.

### Chamada do motor (contrato)
```python
mv.calcular_viga(dados_g, [{'nome': n, **t} for n, t in zip(nomes, ss.lista_vaos)])
# dados_g = {'b','h','fck','cob','peso_proprio'(bool)}
```

---

## 2. `pagina_pilar.py` — chaves de `st.session_state`

Inicialização (linhas 29-39):
```python
if 'res_pilar' not in ss:    ss.res_pilar = None
if 'res_pilar_fp' not in ss: ss.res_pilar_fp = None
for _k, _v in (('pilar_b', 20.0), ('pilar_h', 30.0), ('pilar_l0', 2.8),
               ('pilar_fck', 25), ('pilar_caa', 'I')):
    if _k not in ss: ss[_k] = _v
if 'pilar_Nk' not in ss: ss.pilar_Nk = None
```

| chave | tipo | unidade | default | widget |
|-------|------|---------|---------|--------|
| `pilar_b`   | float | cm  | 20.0 | Base b [cm] (menor dim.) min 14, max 120 |
| `pilar_h`   | float | cm  | 30.0 | Altura h [cm] (maior dim.) min 14, max 300 |
| `pilar_l0`  | float | m   | 2.8  | Altura livre l0 [m] (0.5–10) |
| `pilar_fck` | int   | MPa | 25   | Concreto fck [MPa] (20–50, step 5) |
| `pilar_caa` | str   | —   | 'I'  | selectbox ["I","II","III","IV"] |
| `pilar_Nk`  | float | **UNIDADE DE EXIBIÇÃO (kN·fu)** | None | Força normal característica Nk |

### ⚠️ Unidade de `pilar_Nk` — DIFERENTE de vigas
Diferente de `viga q/P` (que são kN internos), o widget `pilar_Nk` guarda o
valor **na unidade de exibição** (kN se `fu=1`, kgf se `fu≈101,97`). Conversão
para kN interno acontece na leitura (linha 102):
```python
Nk = (Nk_disp or 0.0) / fu          # -> kN (interno)
```
E `carregar_exemplo_pilar` grava **já multiplicado por `fu`** (linha 49):
```python
ss.pilar_Nk = float(dd['Nk']) * fu          # em unidade de exibição
```
Portanto, ao enviar da Laje uma carga em **kN**, faça:
`ss.pilar_Nk = Nk_kN * fu` (usando o `fu` corrente da página de Lajes).
Como o seletor de unidade compartilha a chave `unidade_forca` no session_state
(ver §4), o `fu` é consistente entre as páginas.

### `carregar_exemplo_pilar(ex)` (linha 42)
```python
def carregar_exemplo_pilar(ex):
    dd = ex['dados']
    ss.pilar_b   = float(dd['b'])
    ss.pilar_h   = float(dd['h'])
    ss.pilar_l0  = float(dd['l0'])
    ss.pilar_fck = int(dd['fck'])
    ss.pilar_caa = dd['caa']
    ss.pilar_Nk  = float(dd['Nk']) * fu          # exibição
    ss.res_pilar = None
```
Estrutura de `ex['dados']`: `{"b","h","l0","fck","Nk","caa"}` (Nk em kN).

### Flags de resultado
- `ss.res_pilar` — dict de `mp.calcular_pilar(dados)` ou `{'erros':[...]}`.
- `ss.res_pilar_fp` — `json.dumps(dados, sort_keys=True)` com
  `dados = {'b','h','l0','fck','Nk','caa'}` (Nk em kN interno). Invalidação igual à viga.
- Botão calcular fica desabilitado enquanto `ss.pilar_Nk is None`.

### Contrato do motor
```python
mp.calcular_pilar({'b','h','l0'(m),'fck','Nk'(kN interno),'caa'})
```

---

## 3. Helpers de `ui_comum.py` reutilizáveis

Imports típicos de uma página:
```python
from ui_comum import (NAVY, AMBAR, VERMELHO, VERDE, CINZA_TXT, CONCRETO,
                      aplicar_estilo, header, sec, seletor_unidade, tabela,
                      mostrar_figura, seletor_pagina, assistente_carga,
                      EXEMPLOS_VIGA)
```

### Assinaturas
- `aplicar_estilo()` — injeta o CSS `_CSS` (classes `pol-*`) e o JS de zoom. Chamar **uma vez no topo** de cada página, antes de tudo.
- `header(titulo, subtitulo)` — renderiza o cabeçalho de marca (logo/data-URI + título + subtítulo).
- `sec(num, titulo, destaque=False)` — título de seção numerado; `destaque=True` desenha a barra azul/âmbar. `num` pode ser int ou str (ex.: `"!"`).
- `seletor_pagina(atual)` — navegação (ver detalhe abaixo). `atual` ∈ {'vigas','pilar','previo'}.
- `seletor_unidade(key="unidade_forca")` → retorna `(fu, un_f, un_fm)`. `fu`=fator kN→exibição, `un_f`∈{'kN','kgf'}, `un_fm`∈{'kN/m','kgf/m'}. Padrão `index=1` (kgf). Cálculo interno sempre kN.
- `tabela(rows)` — `rows` = lista de dicts `{coluna: valor}`; renderiza tabela HTML `pol-tab` com rolagem horizontal.
- `mostrar_figura(fig, dpi=170)` — mostra figura matplotlib em contêiner rolável; **retorna os bytes PNG** (para download). Fecha a figura (`plt.close`).
- `assistente_carga(fu, un_fm, key="asst")` → retorna `q` em **kN/m** (float) se o usuário confirmar, senão `None`. Usa `SOBRECARGAS_USO`, `PAREDES`, `TIPOS_LAJE`. **Muito relevante para Lajes**: já contém toda a lógica laje+revest+uso×largura+parede.
- `rodape(texto)` — `st.caption`.

### Constantes
```python
NAVY="#1E3A8A"; NAVY_ESC="#16265B"; AMBAR="#B45309"; VERMELHO="#B91C1C";
VERDE="#15803D"; CINZA_TXT="#334155"; CONCRETO="#CBD5E1"
KGF_POR_KN = 101.9716                      # 1 kN = 101,9716 kgf

SOBRECARGAS_USO = {   # NBR 6120:2019 [kN/m²]
  "Residência — dormitório/sala":1.5, "Residência — cozinha/área de serviço":2.0,
  "Escritório":2.5, "Corredor/escada":3.0, "Loja/comércio":4.0,
  "Garagem — veículos leves":3.0, "Cobertura — só manutenção/acesso":1.0 }

PAREDES = {   # peso por m² de parede [kN/m²]
  "Sem parede":0.0, "Bloco cerâmico furado 15 cm":1.8,
  "Bloco de concreto 14 cm":2.8, "Tijolo maciço (1 vez)":3.6,
  "Divisória leve / drywall":1.0 }

TIPOS_LAJE = {   # 'macica'->25·esp ; 'direto'->pede valor ; número->peso kN/m²
  "Maciça (informar espessura)":"macica", "Nervurada / treliçada com EPS":2.0,
  "Lajota cerâmica pré-fabricada":2.5, "Pré-moldada comum":2.2,
  "Informar o peso direto":"direto" }
```
Também exportadas: `EXEMPLOS_VIGA`, `EXEMPLOS_PILAR`.

### `seletor_pagina` e `_botao_pagina` — como adicionar 4º botão "Lajes"
```python
def _botao_pagina(alvo, atual, path, label, icon):
    if atual == alvo:
        st.markdown(f'<div class="pol-pg-ativo">{icon} {label}</div>',
                    unsafe_allow_html=True)          # botão ativo (âmbar)
        return
    try:
        st.page_link(path, label=label, icon=icon)   # link real (st.navigation)
    except Exception:
        st.markdown(f'<div class="pol-pg-inativo">{icon} {label}</div>',
                    unsafe_allow_html=True)           # fallback execução direta

def seletor_pagina(atual):
    st.markdown('<div class="pol-calc-label">Calcular — clique na opção '
                'abaixo:</div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1: _botao_pagina("vigas", atual, "pagina_vigas.py", "Vigas", "🏗️")
    with c2: _botao_pagina("pilar", atual, "pagina_pilar.py", "Pilares", "🏛️")
    _botao_pagina("previo", atual, "pagina_pilar_previo.py",
                  "Pilares Prévios — casas térreas", "🏠")
```
**Para adicionar "Lajes" sem quebrar os existentes**, editar SOMENTE
`seletor_pagina` — acrescentar uma linha (largura total, como o botão "previo"):
```python
    _botao_pagina("lajes", atual, "pagina_lajes.py", "Lajes", "🧱")
```
E em cada página passar seu identificador em `seletor_pagina("lajes")` etc.
O CSS que mantém "Vigas | Pilares" lado a lado é escopado a
`[data-testid="stHorizontalBlock"]:has([data-testid="stPageLink"])` — botões
de largura total (fora de `st.columns`) não são afetados.

### Registro das páginas (`import numpy as np.py` e `app_polotto.py`)
Os DOIS arquivos são idênticos (um p/ web, outro p/ .exe). Registro via
`st.navigation` (linhas 22-32 / 29-33):
```python
_paginas = [
    st.Page("pagina_vigas.py", title="Vigas", icon="🏗️", default=True),
    st.Page("pagina_pilar.py", title="Pilares", icon="🏛️"),
    st.Page("pagina_pilar_previo.py", title="Pilares Prévios", icon="🏠"),
]
nav = st.navigation(_paginas, position="top"); nav.run()
```
**Para registrar Lajes**, adicionar em AMBOS os arquivos:
```python
    st.Page("pagina_lajes.py", title="Lajes", icon="🧱"),
```
(A barra nativa do st.navigation é escondida por CSS `[data-testid="stNavLink"]{display:none}`; a navegação visível é o `seletor_pagina`.)

---

## 4. Convenções de estilo / formatação / unidades

- **CSS classes `pol-*`**: `pol-header`, `pol-sec`(+`.destaque`), `pol-tramo`,
  `pol-tab`/`pol-tab-wrap`, `pol-fig-wrap`(+`.wide`), `pol-pg-ativo`/`pol-pg-inativo`,
  `pol-calc-label`, `pol-pergunta`, `pol-logo-card`. Reusar em vez de estilos novos.
- **Matplotlib**: sempre `import matplotlib; matplotlib.use("Agg")` **antes** de
  `import matplotlib.pyplot as plt`. Figuras com `fig.patch.set_facecolor('white')`,
  `dpi=150`, cores das constantes. Exibir com `mostrar_figura(fig)`.
- **Padrão de unidade kN/kgf**: `fu, un_f, un_fm = seletor_unidade()` no topo.
  `_cf`/`ca`: casas decimais = `0 if fu>1 else 1/2`. Exibição = `valor_kN * fu`.
  Rótulos via `un_f` (força) e `un_fm` (carga linear). Área: `"kgf/m²" if fu>1 else "kN/m²"`.
- **Formatação PT-BR**: separador de milhar por replace, ex.
  `f"{v:,.0f}".replace(",", ".")` (ver `_fN` em pagina_pilar_previo). Decimais com
  vírgula quando exibido ao usuário.
- **Fingerprint / invalidação**: `json.dumps(..., sort_keys=True)`; comparar com `*_fp`
  e zerar `res`/`res_pilar` ao mudar dados.

---

## 5. Recomendação CONCRETA — botões "Enviar para Vigas" / "Enviar para Pilares"

O padrão já validado no app é o de `carregar_exemplo_*`: escrever direto nas
chaves de widget do session_state e depois navegar. Como o widget usa
`key=`, ao carregar a página destino o `number_input` lê o valor de
`ss[key]`. **Setar de outra página funciona** (é exatamente o que os exemplos
fazem, só que na mesma página + `st.rerun`). Para trocar de página use
`st.switch_page(...)`.

### Enviar para VIGAS (carga distribuída da laje → q de um tramo)
A carga da laje sobre a viga já sai em **kN/m** (o `assistente_carga` retorna
kN/m). Gravar em kN interno:
```python
def enviar_para_vigas(q_kNm, L_m, b=15.0, h=50.0, fck=25, cob=2.5):
    ss = st.session_state
    ss.viga_b, ss.viga_h = float(b), float(h)
    ss.viga_fck, ss.viga_cob = int(fck), float(cob)
    ss.lista_vaos = [{'tipo': 'Normal', 'L': float(L_m),
                      'q': float(q_kNm),    # kN/m INTERNO (NÃO multiplicar por fu)
                      'P': 0.0, 'a': 0.0}]
    ss.res = None                            # invalida resultado antigo
    ss.edit_index = None
    ss.q_sugerido = float(q_kNm)             # opcional: mostra "sugerido"
    st.switch_page("pagina_vigas.py")
```
Se quiser apenas sugerir a carga sem criar tramo, basta
`ss.q_sugerido = q_kNm` (aparece pré-preenchido no formulário de tramo).

### Enviar para PILARES (reação da laje/viga → Nk)
`pilar_Nk` está em **unidade de exibição**, então multiplicar por `fu`:
```python
def enviar_para_pilares(Nk_kN, l0=2.8, b=20.0, h=30.0, fck=25, caa='I'):
    ss = st.session_state
    fu = ss_fu()          # fu corrente = KGF_POR_KN se kgf, senão 1.0
    ss.pilar_b, ss.pilar_h = float(b), float(h)
    ss.pilar_l0 = float(l0)
    ss.pilar_fck, ss.pilar_caa = int(fck), caa
    ss.pilar_Nk = float(Nk_kN) * fu          # EXIBIÇÃO (igual carregar_exemplo_pilar)
    ss.res_pilar = None
    st.switch_page("pagina_pilar.py")
```
`fu` é obtido do mesmo `seletor_unidade()` da página de Lajes (a chave
`unidade_forca` é compartilhada no session_state, então o valor é consistente
quando o usuário chega na página de Pilares).

### Notas de robustez
- Se a página destino ainda não instanciou o widget, setar `ss[key]` antes de
  `st.switch_page` é seguro (não há conflito "widget já criado").
- Sempre zerar `ss.res` / `ss.res_pilar` ao pré-preencher.
- `st.switch_page` requer que a página esteja registrada em `st.navigation`
  (nos dois entrypoints). Em execução fora do `st.navigation`, `switch_page`
  pode lançar — envolver em `try/except` como `_botao_pagina` faz com `page_link`.
- Alternativa a `switch_page`: apenas setar o estado e instruir o usuário a
  clicar no botão do `seletor_pagina` (menos automático, mas à prova de versão).

---

## Resumo do mapa de chaves

**VIGAS** (kN internos): `viga_b, viga_h, viga_fck, viga_cob` +
`lista_vaos = [{'tipo','L','q'(kN/m),'P'(kN),'a'(m)}]` (tipo ∈ Normal /
Balanço Esquerdo / Balanço Direito) + `q_sugerido`(kN/m) + zerar `res`.

**PILARES**: `pilar_b, pilar_h, pilar_l0, pilar_fck, pilar_caa` +
`pilar_Nk = Nk_kN * fu` (UNIDADE DE EXIBIÇÃO) + zerar `res_pilar`.

Navegação: `st.switch_page("pagina_vigas.py" / "pagina_pilar.py")`.
</content>
</invoke>
