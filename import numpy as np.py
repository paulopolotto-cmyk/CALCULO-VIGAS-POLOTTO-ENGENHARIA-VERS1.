import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

# Configuração da página para o celular
st.set_page_config(page_title="Polotto Engenharia", layout="centered")

# ESTILIZAÇÃO AGRESSIVA REINSTALADA + CONTORNO SEGURO PARA TABELAS (IMPRESSÃO)
st.markdown("""
    <style>
    .titulo { text-align: center; color: white; background-color: #1E3A8A; padding: 12px; font-weight: bold; font-size: 20px; border-radius: 5px; }
    .tramo-header { text-align: center; background-color: #FFDE4D; color: #000000; padding: 8px; font-weight: bold; border-radius: 5px; margin-bottom: 10px; border: 1px solid #E6B905; }
    
    /* TARJA AMARELA COM LETRAS EM VERMELHO NEGRITO - MÁXIMO CONTRASTE */
    .label-blindado {
        background-color: #FFDE4D !important;
        color: #CC0000 !important;
        font-weight: bold !important;
        font-size: 15px !important;
        padding: 4px 8px !important;
        border-radius: 4px !important;
        display: inline-block !important;
        margin-bottom: 4px !important;
        margin-top: 10px !important;
        border: 1px solid #E6B905 !important;
    }
    
    /* FORÇANDO FUNDO AMARELO CLARO E TEXTO PRETO EM TODAS AS CAIXAS DE ENTRADA */
    div[data-testid="stNumberInput"] input, 
    div[data-testid="stTextInput"] input,
    div[data-testid="stSelectbox"] div[data-baseweb="select"],
    div[data-testid="stSelectbox"] div[data-baseweb="select"] > div,
    div[data-testid="stSelectbox"] select {
        background-color: #FFF9C4 !important;
        color: #000000 !important;
        -webkit-text-fill-color: #000000 !important;
        font-weight: bold !important;
        font-size: 16px !important;
        border: 2px solid #E6B905 !important;
        border-radius: 4px !important;
    }
    
    /* CONTORNO E BORDAS DA TABELA DE FERROS (PERFEITO PARA IMPRESSÃO) */
    div[data-testid="stTable"] table {
        border-collapse: collapse !important;
        width: 100% !important;
        border: 2px solid #94A3B8 !important;
    }
    div[data-testid="stTable"] th {
        background-color: #F1F5F9 !important;
        color: #000000 !important;
        border: 1px solid #CBD5E1 !important;
        padding: 8px !important;
        font-weight: bold !important;
    }
    div[data-testid="stTable"] td {
        border: 1px solid #CBD5E1 !important;
        color: #000000 !important;
        padding: 8px !important;
    }
    
    /* ESTILIZAÇÃO DO TEXTO FANTASMA (PLACEHOLDER) */
    input::placeholder {
        color: #555555 !important;
        opacity: 1 !important;
        font-style: italic !important;
        font-size: 14px !important;
    }
    
    /* CORREÇÃO DO CELULAR: Texto selecionado legível */
    div[data-testid="stSelectbox"] div[data-baseweb="select"] span,
    div[data-testid="stSelectbox"] [data-testid="stMarkdownContainer"] p {
        color: #000000 !important;
        font-weight: bold !important;
        -webkit-text-fill-color: #000000 !important;
    }
    
    /* MENU EXPANDIDO */
    ul[role="listbox"] li, div[role="option"] {
        color: #000000 !important;
        font-weight: bold !important;
        background-color: #FFF9C4 !important;
    }
    
    /* ESCONDE OS LABELS PADRÕES DO STREAMLIT */
    div[data-testid="stNumberInput"] label,
    div[data-testid="stTextInput"] label,
    div[data-testid="stSelectbox"] label {
        display: none !important;
    }
    
    /* FORÇANDO O BOTÃO DO FORMULÁRIO */
    div[data-testid="stForm"] button, div.stButton > button:not([type="primary"]) {
        background-color: #FFDE4D !important;
        color: #000000 !important;
        font-size: 16px !important;
        font-weight: bold !important;
        height: 48px !important;
        width: 100% !important;
        border: 2px solid #E6B905 !important;
        border-radius: 6px !important;
        box-shadow: 0px 3px 5px rgba(0,0,0,0.1) !important;
    }
    
    /* Botão de Calcular em Vermelho */
    div.stButton > button[type="primary"] {
        width: 100% !important;
        height: 50px !important;
        font-weight: bold !important;
        background-color: #FF4B4B !important;
        color: white !important;
        font-size: 16px !important;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="titulo">PROGRAMA DE CÁLCULOS DE VIGAS DA POLOTTO ENGENHARIA</div>', unsafe_allow_html=True)
st.write("")

# --- FUNÇÃO AUXILIAR PARA CONVERTER TEXTO DO CELULAR PARA NÚMERO ---
def converter_valor(texto, padrao=0.0):
    if not texto or str(texto).strip() == "":
        return padrao
    try:
        txt_limpo = str(texto).replace(",", ".").strip()
        if txt_limpo in [".", "-", "-."]:
            return padrao
        return float(txt_limpo)
    except:
        return padrao

# --- DECLARAÇÃO DA FUNÇÃO DE SUGESTÃO DE BARRAS ---
def sugerir_barras(as_req):
    if as_req == -1: return "Redim.!"
    if as_req <= 0: return "2 ø 8.0mm (Porta-Estribo)"
    bitolas = [("ø10mm", 0.79), ("ø12.5mm", 1.23), ("ø16mm", 2.01)]
    for nome, area in bitolas:
        qtd = int(np.ceil(as_req / area))
        if qtd >= 2: return f"{qtd} {nome}"
    return f"2 ø 10mm"

# --- MOTOR MATEMÁTICO ADAPTADO NBR 6118 ---
def calcular_viga_dinamica(dados_gerais, lista_vaos):
    try:
        b = float(dados_gerais['b'])
        h = float(dados_gerais['h'])
        fck = float(dados_gerais['fck'])
        
        gamma_f, gamma_c, gamma_s = 1.4, 1.4, 1.15
        fcd = (fck / 10) / gamma_c 
        fyd = (500 / 10) / gamma_s 
        d = h - 4.0 
        
        vaos_internos = [v for v in lista_vaos if v['tipo'] == 'Normal']
        bal_esq = [v for v in lista_vaos if v['tipo'] == 'Balanço Esquerdo']
        bal_dir = [v for v in lista_vaos if v['tipo'] == 'Balanço Direito']
        
        num_vaos = len(vaos_internos)
        num_apoios = num_vaos + 1
        
        if num_vaos < 1:
            return {"erro": "A viga precisa ter pelo menos 1 vão normal entre apoios para calcular."}
            
        MA = - (bal_esq[0]['q'] * bal_esq[0]['L']**2 / 2 + bal_esq[0]['P'] * bal_esq[0]['a']) if bal_esq else 0.0
        MZ = - (bal_dir[0]['q'] * bal_dir[0]['L']**2 / 2 + bal_dir[0]['P'] * (bal_dir[0]['L'] - bal_dir[0]['a'])) if bal_dir else 0.0
        
        if num_vaos == 1:
            L1 = vaos_internos[0]['L']
            q1 = vaos_internos[0]['q']
            P1 = vaos_internos[0]['P']
            a1 = vaos_internos[0]['a']
            b1 = L1 - a1
            
            MB = MZ 
            VA_iso = q1 * L1 / 2 + (P1 * b1 / L1 if L1 > 0 else 0)
            VB_iso = q1 * L1 / 2 + (P1 * a1 / L1 if L1 > 0 else 0)
            VA = VA_iso + (MB - MA)/L1 if L1 > 0 else VA_iso
            VB = VB_iso + (MA - MB)/L1 if L1 > 0 else VB_iso
            
            M_pos = max(0, ((q1 * L1**2)/8 + (P1 * a1 * b1 / L1 if L1 > 0 else 0)) + (MA + MB)/2)
            
            V_max = max(abs(VA), abs(VB))
            if bal_esq: V_max = max(V_max, bal_esq[0]['q']*bal_esq[0]['L'] + bal_esq[0]['P'])
            if bal_dir: V_max = max(V_max, bal_dir[0]['q']*bal_dir[0]['L'] + bal_dir[0]['P'])
            
            M_apoios = [MA, MB]
            M_positivos = [M_pos]
            Reacoes = [VA + (bal_esq[0]['q']*bal_esq[0]['L'] + bal_esq[0]['P'] if bal_esq else 0), VB + (bal_dir[0]['q']*bal_dir[0]['L'] + bal_dir[0]['P'] if bal_dir else 0)]
            V_por_vao = [max(abs(VA), abs(VB))]
        else:
            num_incog = num_apoios - 2
            A_mat = np.zeros((num_incog, num_incog))
            B_mat = np.zeros(num_incog)
            
            W = []
            for v in vaos_internos:
                L_v = v['L']
                a_v = v['a']
                b_v = L_v - a_v
                term_q = (v['q'] * L_v**3) / 24
                term_p = (v['P'] * a_v * b_v * (L_v + b_v)) / (6 * L_v) if L_v > 0 else 0
                W.append(term_q + term_p)
                
            for i in range(num_incog):
                L_esq = vaos_internos[i]['L']
                L_dir = vaos_internos[i+1]['L']
                A_mat[i, i] = 2 * (L_esq + L_dir)
                if i > 0: A_mat[i, i-1] = L_esq
                if i < num_incog - 1: A_mat[i, i+1] = L_dir
                B_mat[i] = -6 * (W[i] + W[i+1])
                
            B_mat[0] -= vaos_internos[0]['L'] * MA
            B_mat[-1] -= vaos_internos[-1]['L'] * MZ
            
            M_sol = np.linalg.solve(A_mat, B_mat)
            M_apoios = [MA] + list(M_sol) + [MZ]
            
            Reacoes_apoio = np.zeros(num_apoios)
            M_positivos = []
            V_max = 0.0
            V_por_vao = []
            
            for i in range(num_vaos):
                L = vaos_internos[i]['L']
                q = vaos_internos[i]['q']
                P = vaos_internos[i]['P']
                a_v = vaos_internos[i]['a']
                b_v = L - a_v
                M_esq = M_apoios[i]
                M_dir = M_apoios[i+1]
                
                V_iso_esq = q * L / 2 + (P * b_v / L if L > 0 else 0)
                V_iso_dir = q * L / 2 + (P * a_v / L if L > 0 else 0)
                
                V_esq_total = V_iso_esq + (M_dir - M_esq) / L if L > 0 else V_iso_esq
                V_dir_total = V_iso_dir + (M_esq - M_dir) / L if L > 0 else V_iso_dir
                
                Reacoes_apoio[i] += V_esq_total
                Reacoes_apoio[i+1] += V_dir_total
                
                M_pos = max(0, ((q * L**2)/8 + (P * a_v * b_v / L if L > 0 else 0)) + (M_esq + M_dir)/2)
                M_positivos.append(M_pos)
                
                V_max_vao = max(abs(V_esq_total), abs(V_dir_total))
                V_por_vao.append(V_max_vao)
                V_max = max(V_max, V_max_vao)
                
            if bal_esq:
                Reacoes_apoio[0] += bal_esq[0]['q'] * bal_esq[0]['L'] + bal_esq[0]['P']
                V_max = max(V_max, bal_esq[0]['q'] * bal_esq[0]['L'] + bal_esq[0]['P'])
            if bal_dir:
                Reacoes_apoio[-1] += bal_dir[0]['q'] * bal_dir[0]['L'] + bal_dir[0]['P']
                V_max = max(V_max, bal_dir[0]['q'] * bal_dir[0]['L'] + bal_dir[0]['P'])
                
            Reacoes = list(Reacoes_apoio)

        xi_vaos, x_vaos = [], []
        def calcular_as_e_ln(M_k):
            if abs(M_k) <= 0.05: 
                xi_vaos.append(0.0)
                x_vaos.append(0.0)
                return 0.0
            M_d = abs(M_k) * 100 * gamma_f 
            k_md = M_d / (b * (d**2) * fcd)
            if k_md > 0.295: 
                xi_vaos.append(0.45)
                x_vaos.append(0.45 * d)
                return -1 
            xi = 1.25 * (1 - np.sqrt(1 - 2 * k_md))
            x_cm = xi * d
            xi_vaos.append(xi)
            x_vaos.append(x_cm)
            return M_d / ((d * (1 - 0.4 * xi)) * fyd)

        As_min = 0.0015 * b * h
        def ajustar_as(as_calc):
            if as_calc == -1: return -1
            if as_calc == 0: return 0
            return max(as_calc, As_min)

        As_apoios = [ajustar_as(calcular_as_e_ln(m)) for m in M_apoios]
        xi_pos, x_pos = [], []
        for m in M_positivos:
            M_d = abs(m) * 100 * gamma_f
            k_md = M_d / (b * (d**2) * fcd)
            if k_md > 0.295 or abs(m) <= 0.05:
                xi_pos.append(0.0 if abs(m) <= 0.05 else 0.45)
                x_pos.append(0.0 if abs(m) <= 0.05 else 0.45 * d)
            else:
                xi = 1.25 * (1 - np.sqrt(1 - 2 * k_md))
                xi_pos.append(xi)
                x_pos.append(xi * d)
        As_positivos = [ajustar_as(calcular_as_e_ln(m)) for m in M_positivos]

        tem_pele = h > 60.0
        if tem_pele:
            as_pele_total = 0.0010 * b * h 
            pele_msg = f"OBRIGATÓRIA: {as_pele_total:.2f} cm² total (Usar 2x2 ø6.3mm nas laterais)"
        else:
            pele_msg = "DISPENSADA POR NORMA (h <= 60cm)"

        fcd_mpa = fck / 1.4
        v1 = 0.6 * (1 - fck / 250)
        Vrd2 = 0.27 * v1 * fcd_mpa * (b / 10) * (d / 10) * 10 
        falha_cortante = (V_max * gamma_f) > Vrd2
        
        estribos_vaos_texto = []
        num_estribos_total = 0
        if falha_cortante:
            estribo_msg = "REDIRECIONAR SEÇÃO!"
            for _ in range(num_vaos): estribos_vaos_texto.append("Seção Insuficiente")
        else:
            fctm = 0.3 * (fck ** (2/3))
            Vc = 0.6 * (((0.7 * fctm) / 1.4) / 10) * b * d 
            for v_curr in vaos_internos:
                Vsw = max(0, (v_curr['q'] * v_curr['L'] * gamma_f) - Vc)
                Asw_s = max((Vsw / (0.9 * d * fyd)) * 100, 0.2 * (fctm / 10) * b / 43.5 * 100)
                esp = min((2 * 0.196 / Asw_s) * 100, min(0.6 * d, 30.0))
                estribos_vaos_texto.append(f"ø5.0 c/{esp:.1f}cm")
                num_estribos_total += int(np.ceil((v_curr['L'] * 100) / esp)) + 1
            estribo_msg = estribos_vaos_texto[0]

        return {
            "M_apoios": M_apoios, "M_positivos": M_positivos, "Reacoes": Reacoes,
            "As_apoios": As_apoios, "As_positivos": As_positivos,
            "V_max": V_max, "Vrd2": Vrd2, "estribos": estribo_msg, "estribos_lista": estribos_vaos_texto,
            "falha_cortante": falha_cortante, "vaos_internos": vaos_internos, 
            "bal_esq": bal_esq, "bal_dir": bal_dir, "pele": pele_msg, "tem_pele": tem_pele,
            "xi_pos": xi_pos, "x_pos": x_pos, "num_estribos": num_estribos_total
        }
    except Exception as e:
        return {"erro": str(e)}

# --- GERENCIAMENTO DE ESTADO SÉRIO ---
if 'lista_vaos' not in st.session_state: st.session_state.lista_vaos = []
if 'contador' not in st.session_state: st.session_state.contador = 1
if 'edit_index' not in st.session_state: st.session_state.edit_index = None
if 'res_calculo' not in st.session_state: st.session_state.res_calculo = None

# --- ENTRADA DE DADOS ---
st.header("1. Seção, Concreto e Aço")
st.markdown('<span class="label-blindado">Base (bw) [cm]</span>', unsafe_allow_html=True)
b_raw = st.text_input("Base (bw) [cm]", value="15", key="main_b")
b_val = converter_valor(b_raw, 15.0)

st.markdown('<span class="label-blindado">Altura (h) [cm]</span>', unsafe_allow_html=True)
h_raw = st.text_input("Altura (h) [cm]", value="50", key="main_h")
h_val = converter_valor(h_raw, 50.0)

st.markdown('<span class="label-blindado">Concreto fck [MPa]</span>', unsafe_allow_html=True)
fck_raw = st.text_input("Concreto fck [MPa]", value="25", key="main_fck")
fck_val = converter_valor(fck_raw, 25.0)

st.markdown('<span class="label-blindado">Aço de Projeto</span>', unsafe_allow_html=True)
tipo_aco = st.text_input("Aço de Projeto", value="CA-50A", disabled=True, key="main_aco")

dados_g = {'b': b_val, 'h': h_val, 'fck': fck_val}

st.header("2. Inserir Elementos da Viga")
num_normais = sum(1 for v in st.session_state.lista_vaos if v['tipo'] == 'Normal')

if st.session_state.edit_index is not None:
    idx = st.session_state.edit_index
    st.markdown(f'<div class="tramo-header">✏️ MODIFICANDO TRAMO: {st.session_state.lista_vaos[idx]["nome"]}</div>', unsafe_allow_html=True)
    st.markdown('<span class="label-blindado">Tipo do Tramo</span>', unsafe_allow_html=True)
    tipo_ed = st.selectbox("Tipo do Tramo", ["Normal", "Balanço Esquerdo", "Balanço Direito"], index=["Normal", "Balanço Esquerdo", "Balanço Direito"].index(st.session_state.lista_vaos[idx]['tipo']), key="ed_tipo")
    
    colL, colQ, colP, colA = st.columns(4)
    with colL:
        st.markdown('<span class="label-blindado">Comprimento [m]</span>', unsafe_allow_html=True)
        L_ed = st.text_input("Comprimento [m]", value=str(st.session_state.lista_vaos[idx]['L']), key="ed_L")
    with colQ:
        st.markdown('<span class="label-blindado">Carga Distr. [kN/m]</span>', unsafe_allow_html=True)
        q_ed = st.text_input("Carga Distr. [kN/m]", value=str(st.session_state.lista_vaos[idx]['q']), key="ed_q")
    with colP:
        st.markdown('<span class="label-blindado">Carga Conc. [kN]</span>', unsafe_allow_html=True)
        P_ed = st.text_input("Carga Conc. [kN]", value=str(st.session_state.lista_vaos[idx]['P']), key="ed_p")
    with colA:
        st.markdown('<span class="label-blindado">Dist. Carga (a) [m]</span>', unsafe_allow_html=True)
        a_ed = st.text_input("Dist. Carga (a) [m]", value=str(st.session_state.lista_vaos[idx]['a']), key="ed_a")
    
    col_b1, col_b2 = st.columns(2)
    if col_b1.button("💾 SALVAR ALTERAÇÃO", key="btn_salvar_ed"):
        st.session_state.lista_vaos[idx] = {'nome': st.session_state.lista_vaos[idx]['nome'], 'tipo': tipo_ed, 'L': converter_valor(L_ed), 'q': converter_valor(q_ed), 'P': converter_valor(P_ed), 'a': converter_valor(a_ed)}
        st.session_state.edit_index = None
        st.session_state.res_calculo = None 
        st.rerun()
    if col_b2.button("❌ CANCELAR", key="btn_cancelar_ed"):
        st.session_state.edit_index = None
        st.rerun()
else:
    st.markdown(f'<div class="tramo-header">Tramo {len(st.session_state.lista_vaos) + 1} - Vão {num_normais + 1}</div>', unsafe_allow_html=True)
    with st.form(key="form_insercao_limpo", clear_on_submit=True):
        st.markdown('<span class="label-blindado">Tipo do Tramo</span>', unsafe_allow_html=True)
        tipo = st.selectbox("Tipo do Tramo", ["Normal", "Balanço Esquerdo", "Balanço Direito"], key="form_tipo")
        
        colL, colQ, colP, colA = st.columns(4)
        L = colL.text_input("Comprimento [m]", placeholder="Digitar...", value="", key="inp_L")
        q = colQ.text_input("Carga Distr. [kN/m]", placeholder="Digitar...", value="", key="inp_q")
        P = colP.text_input("Carga Conc. [kN]", placeholder="Digitar...", value="", key="inp_P")
        a = colA.text_input("Dist. Carga (a) [m]", placeholder="Digitar...", value="", key="inp_a")
        
        btn_inserir = st.form_submit_button("➕ INSERIR TRAMO NA VIGA")

    if btn_inserir:
        v_L, v_q, v_P, v_a = converter_valor(L), converter_valor(q), converter_valor(P), converter_valor(a)
        if v_L <= 0.0: st.error("O comprimento do vão precisa ser maior que zero!")
        else:
            nome_tramo = f"Vão {st.session_state.contador}" if tipo == "Normal" else tipo
            if tipo == "Normal": st.session_state.contador += 1
            st.session_state.lista_vaos.append({'nome': nome_tramo, 'tipo': tipo, 'L': v_L, 'q': v_q, 'P': v_P, 'a': v_a})
            st.session_state.res_calculo = None 
            st.rerun()

if len(st.session_state.lista_vaos) > 0:
    st.write("### 📋 Tramos Inseridos no Projeto:")
    for i, v in enumerate(st.session_state.lista_vaos):
        col_text, col_edit, col_del = st.columns([3, 0.6, 0.6])
        col_text.markdown(f"**{v['nome']}** | L = **{v['L']}m** | q = **{v['q']} kN/m**")
        if col_edit.button("✏️", key=f"edit_{i}"): st.session_state.edit_index = i; st.rerun()
        if col_del.button("❌", key=f"del_{i}"):
            if v['tipo'] == "Normal": st.session_state.contador -= 1
            st.session_state.lista_vaos.pop(i)
            st.session_state.res_calculo = None
            st.rerun()

    st.write("")
    if st.button("⚡ FINALIZAR E CALCULAR VIGA", type="primary", key="btn_calcular_final"):
        st.session_state.res_calculo = calcular_viga_dinamica(dados_g, st.session_state.lista_vaos)
        st.rerun()
    st.write("")

    if st.session_state.res_calculo is not None:
        res = st.session_state.res_calculo
        
        if "erro" in res: st.error(res["erro"])
        else:
            st.write("---")
            st.header("🏁 Layout de Detalhamento Estrutural")
            
            if res['falha_cortante']:
                st.markdown(f'<div style="background-color:#DC2626; color:white; padding:25px; border-radius:10px; font-weight:bold; font-size:22px; text-align:center;">⚠️ AS DIMENSÕES DA VIGA ({b_val}x{h_val} cm) SÃO INSUFICIENTES!</div>', unsafe_allow_html=True)
                
            fig, ax = plt.subplots(figsize=(8, 4.5))
            ax.set_xlim(-1, len(res['Reacoes']) + 0.5)
            ax.set_ylim(-2.8, 2.2)
            ax.axis('off')
            
            # Desenho da viga
            ax.fill_between([-0.5, len(res['Reacoes'])-0.5], 0.4, -0.4, color='#E5E7EB')
            
            # Pilares e reações
            for idx, r in enumerate(res['Reacoes']):
                ax.plot(idx, -0.4, '^', color='#1E3A8A', markersize=15)
                ax.text(idx, -0.7, f"Pilar {chr(65+idx)}\n{r:.1f} kN", ha='center', va='top', color='#1E3A8A', fontsize=10, fontweight='bold')
            
            # Linhas de armaduras longitudinais
            ax.plot([-0.4, len(res['Reacoes'])-0.6], [0.25, 0.25], color='#DC2626', linewidth=3.5)
            ax.plot([-0.4, len(res['Reacoes'])-0.6], [-0.25, -0.25], color='#16A34A', linewidth=3.5)
            
            # Armaduras nos apoios
            if res['bal_esq']:
                ax.text(-0.3, 0.55, f"{sugerir_barras(res['As_apoios'][0])}\n(C1)", color='#DC2626', fontsize=9, ha='center', fontweight='bold')
            for i in range(len(res['M_apoios'])-2):
                ax.text(i+1, 0.55, f"{sugerir_barras(res['As_apoios'][i+1])}\n(C1)", color='#DC2626', fontsize=9, ha='center', fontweight='bold')
            if res['bal_dir']:
                ax.text(len(res['Reacoes'])-0.7, 0.55, f"{sugerir_barras(res['As_apoios'][-1])}\n(C1)", color='#DC2626', fontsize=9, ha='center', fontweight='bold')
                
            for i in range(len(res['vaos_internos'])):
                ax.text(i + 0.5, -0.18, f"{sugerir_barras(res['As_positivos'][i])} (C1)", color='#16A34A', fontsize=9, ha='center', fontweight='bold')
                texto_estribo_vao = res['estribos_lista'][i] if not res['falha_cortante'] else "Incompatível"
                ax.text(i + 0.5, -1.30, f"Estribos:\n{texto_estribo_vao}", color='#78350F', fontsize=9, ha='center', va='top', fontweight='bold', style='italic')
            
            # Caixa indicadora de seção transversal no gráfico
            posX_corte = len(res['Reacoes']) - 0.1
            caixa_corte = plt.Rectangle((posX_corte, -0.4), 0.4, 0.8, edgecolor='black', facecolor='#F3F4F6', hatch='//', linewidth=2.0)
            ax.add_patch(caixa_corte)
            ax.text(posX_corte + 0.2, -0.65, f"{int(b_val)}", ha='center', va='top', fontsize=10, fontweight='bold')
            ax.text(posX_corte + 0.5, 0.0, f"{int(h_val)}", ha='left', va='center', fontsize=10, fontweight='bold')
            st.pyplot(fig)

            # --- NOVO BLOCO 1: VISÃO LONGITUDINAL DA LINHA NEUTRA (ESTUDO PARA FUROS) ---
            st.subheader("🚧 Zoneamento Seguro para Furos e Passagens (Linha Neutra)")
            fig_ln, ax_ln = plt.subplots(figsize=(8, 3.5))
            L_total = sum(v['L'] for v in res['vaos_internos'])
            ax_ln.set_xlim(0, L_total)
            ax_ln.set_ylim(-h_val, 0)
            ax_ln.set_ylabel("Altura da Viga (cm)", fontweight='bold')
            ax_ln.set_xlabel("Comprimento da Viga (m)", fontweight='bold')
            ax_ln.fill_between([0, L_total], 0, -h_val, color='#F3F4F6')
            
            curr_x = 0
            for i, v in enumerate(res['vaos_internos']):
                ln_v = res['x_pos'][i] if (res['x_pos'][i] > 0 and res['x_pos'][i] < h_val) else 0.35 * h_val
                ax_ln.fill_between([curr_x, curr_x + v['L']], 0, -ln_v, color='#FCA5A5', alpha=0.6, label="ZONA COMPRIMIDA (PROIBIDO FURAR)" if i==0 else "")
                ax_ln.fill_between([curr_x, curr_x + v['L']], -ln_v, -h_val, color='#BBF7D0', alpha=0.6, label="ZONA TRACIONADA (PERMITIDO FURAR)" if i==0 else "")
                ax_ln.plot([curr_x, curr_x + v['L']], [-ln_v, -ln_v], 'r--', linewidth=2)
                ax_ln.text(curr_x + v['L']/2, -ln_v - 3, f"LN = {ln_v:.1f}cm", color='red', ha='center', fontsize=10, fontweight='bold')
                curr_x += v['L']
            ax_ln.legend(loc="lower left", fontsize=9)
            st.pyplot(fig_ln)

            # --- NOVO BLOCO 2: CORTE TRANSVERSAL ULTRA MINIATURA (AFASTADO E AUMENTADO) ---
            st.subheader("📐 Corte Transversal da Seção")
            
            col_esq, col_centro, col_dir = st.columns([1.4, 1.0, 1.4])
            
            with col_centro:
                fig_ct, ax_ct = plt.subplots(figsize=(0.7, 1.1))
                ax_ct.set_xlim(-9, b_val + 9)  # Expandido para acomodar os textos sem trombar
                ax_ct.set_ylim(-9, h_val + 9)
                ax_ct.set_aspect('equal')
                
                ax_ct.add_patch(plt.Rectangle((0, 0), b_val, h_val, edgecolor='#1E3A8A', facecolor='#E5E7EB', linewidth=1.5))
                ax_ct.add_patch(plt.Rectangle((2, 2), b_val-4, h_val-4, edgecolor='#78350F', facecolor='none', linewidth=0.8))
                
                # Barras superiores (Porta-Estribos)
                ax_ct.plot(3.5, h_val-3.5, 'o', color='black', markersize=4) 
                ax_ct.plot(b_val-3.5, h_val-3.5, 'o', color='black', markersize=4) 
                
                # Barras inferiores (Reforço positivo)
                ax_ct.plot(3.5, 3.5, 'o', color='red', markersize=4.5)
                ax_ct.plot(b_val/2, 3.5, 'o', color='red', markersize=4.5)
                ax_ct.plot(b_val-3.5, 3.5, 'o', color='red', markersize=4.5)
                
                if res['tem_pele']:
                    ax_ct.plot(3.5, h_val/2, 'o', color='green', markersize=3)
                    ax_ct.plot(b_val-3.5, h_val/2, 'o', color='green', markersize=3)
                    ax_ct.text(b_val/2, h_val/2 + 2.5, "Pele", color='green', ha='center', fontsize=6, fontweight='bold')

                # Afastamento seguro das dimensões para evitar qualquer sobreposição e aumento do tamanho
                ax_ct.text(b_val/2, -5.5, f"bw={int(b_val)}", ha='center', fontsize=7.5, fontweight='bold', color='#1E3A8A')
                ax_ct.text(-6.5, h_val/2, f"h={int(h_val)}", va='center', rotation=90, fontsize=7.5, fontweight='bold', color='#1E3A8A')
                ax_ct.axis('off')
                st.pyplot(fig_ct)

            # --- NOVO BLOCO 3: QUANTITATIVO / TABELA DE FERROS ENVELOPADA ---
            st.subheader("📊 Quantitativo e Listagem de Aço")
            comp_padrao = res['vaos_internos'][0]['L'] + 0.60
            data_tabela = [
                {"Pos": "N1", "Tipo": "Positivo (Fundo)", "Bitola": "ø10.0 mm", "Qtd": "3", "Comp. Unit (m)": f"{comp_padrao:.2f}", "Função": "Flexão Positiva"},
                {"Pos": "N2", "Tipo": "Porta-Estribo", "Bitola": "ø8.0 mm", "Qtd": "2", "Comp. Unit (m)": f"{comp_padrao:.2f}", "Função": "Montagem da Viga"},
                {"Pos": "N3", "Tipo": "Estribos", "Bitola": "ø5.0 mm", "Qtd": str(res['num_estribos']), "Comp. Unit (m)": f"{(2*b_val + 2*h_val - 8)/100:.2f}", "Função": "Força Cortante"}
            ]
            if res['tem_pele']:
                data_tabela.append({"Pos": "N4", "Tipo": "Armadura Pele", "Bitola": "ø6.3 mm", "Qtd": "4", "Comp. Unit (m)": f"{comp_padrao:.2f}", "Função": "Pele Lateral"})
            st.table(data_tabela)

            # Relatório Técnico Original em Texto
            st.subheader("Relação de Especificações Técnicas")
            status_norma = "⚠️ REPROVADO (Seção Insuficiente!)" if res['falha_cortante'] else "✅ APROVADO CONFORME NBR 6118"
            
            linhas_relatorio = [
                f"SEÇÃO TRANSVERSAL: {b_val}x{h_val} cm  |  CONCRETO: fck = {fck_val} MPa  |  AÇO: {tipo_aco}",
                "--------------------------------------------------------------------------------",
                f"STATUS DA FORÇA CORTANTE: {status_norma}",
                f"ARMADURA TRANSVERSAL (ESTRIBOS GERAIS): {res['estribos']}",
                f"ARMADURA DE PELE TRANSVERSAL: {res['pele']}",
                "--------------------------------------------------------------------------------"
            ]
            for idx, r in enumerate(res['Reacoes']):
                linhas_relatorio.append(f"PILAR {chr(65+idx)}: Reação Atuante = {r:.1f} kN")
            
            linhas_relatorio.append("--------------------------------------------------------------------------------")
            linhas_relatorio.append("📊 PARÂMETROS DE CONTROLE DE DUCTILIDADE DA LINHA NEUTRA:")
            for i, v in enumerate(res['vaos_internos']):
                linhas_relatorio.append(f"  Vão {i+1}: Posição LN (x) = {res['x_pos'][i]:.2f} cm | Relação LN (x/d) = {res['xi_pos'][i]:.3f} (Limite NBR = 0.450)")
                
            st.code("\n".join(linhas_relatorio), language="text")

st.write("")
if st.button("🔄 Limpar Tudo e Reiniciar", key="btn_reiniciar_viga"):
    st.session_state.lista_vaos = []
    st.session_state.contador = 1
    st.session_state.edit_index = None
    st.session_state.res_calculo = None
    st.rerun()
