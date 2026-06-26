import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

# Configuração da página para o celular
st.set_page_config(page_title="Polotto Engenharia", layout="centered")

# ESTILIZAÇÃO AGRESSIVA: Garante legibilidade total no celular (Modo Escuro/Claro)
st.markdown("""
    <style>
    .titulo { text-align: center; color: white; background-color: #1E3A8A; padding: 12px; font-weight: bold; font-size: 20px; border-radius: 5px; }
    .tramo-header { text-align: center; background-color: #FFDE4D; color: #000000; padding: 8px; font-weight: bold; border-radius: 5px; margin-bottom: 10px; border: 1px solid #E6B905; }
    
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
    
    /* GARANTE QUE O TEXTO SELECIONADO DENTRO DA CAIXA FIQUE PRETO NO CELULAR */
    div[data-testid="stSelectbox"] [data-testid="stMarkdownContainer"] p {
        color: #000000 !important;
        font-weight: bold !important;
    }
    
    /* MODIFICANDO O MENU EXPANDIDO (OPÇÕES) DO SELECTBOX PARA MANTER O TEXTO PRETO E LEGÍVEL */
    ul[role="listbox"] li, div[role="option"] {
        color: #000000 !important;
        font-weight: bold !important;
        background-color: #FFF9C4 !important;
    }
    
    /* LABELS (TEXTOS DOS CAMPOS) SEMPRE VISÍVEIS EM NEGRITO */
    div[data-testid="stNumberInput"] label,
    div[data-testid="stTextInput"] label,
    div[data-testid="stSelectbox"] label {
        color: #000000 !important;
        font-weight: bold !important;
        font-size: 14px !important;
    }
    
    /* FORÇANDO O BOTÃO DO FORMULÁRIO A FICAR AMARELO E EM DESTAQUE */
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
    
    /* Mantendo o Botão de Calcular em Vermelho Marcante */
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

        def calcular_as(M_k):
            if abs(M_k) <= 0.05: return 0.0
            M_d = abs(M_k) * 100 * gamma_f 
            k_md = M_d / (b * (d**2) * fcd)
            if k_md > 0.295: return -1 
            xi = 1.25 * (1 - np.sqrt(1 - 2 * k_md))
            return M_d / ((d * (1 - 0.4 * xi)) * fyd)

        As_min = 0.0015 * b * h
        def ajustar_as(as_calc):
            if as_calc == -1: return -1
            if as_calc == 0: return 0
            return max(as_calc, As_min)

        As_apoios = [ajustar_as(calcular_as(m)) for m in M_apoios]
        As_positivos = [ajustar_as(calcular_as(m)) for m in M_positivos]

        fcd_mpa = fck / 1.4
        v1 = 0.6 * (1 - fck / 250)
        Vrd2 = 0.27 * v1 * fcd_mpa * (b / 10) * (d / 10) * 10 
        falha_cortante = (V_max * gamma_f) > Vrd2
        
        estribos_vaos_texto = []
        if falha_cortante:
            estribo_msg = "REDIRECIONAR SEÇÃO!"
            for _ in range(num_vaos):
                estribos_vaos_texto.append("Seção Insuficiente")
        else:
            fctm = 0.3 * (fck ** (2/3))
            Vc = 0.6 * (((0.7 * fctm) / 1.4) / 10) * b * d 
            for v_curr in V_por_vao:
                Vsw = max(0, (v_curr * gamma_f) - Vc)
                Asw_s = max((Vsw / (0.9 * d * fyd)) * 100, 0.2 * (fctm / 10) * b / 43.5 * 100)
                esp = min((2 * 0.196 / Asw_s) * 100, min(0.6 * d, 30.0))
                estribos_vaos_texto.append(f"ø5.0 c/{esp:.1f}cm")
            Vsw_max = max(0, (V_max * gamma_f) - Vc)
            Asw_s_max = max((Vsw_max / (0.9 * d * fyd)) * 100, 0.2 * (fctm / 10) * b / 43.5 * 100)
            esp_max = min((2 * 0.196 / Asw_s_max) * 100, min(0.6 * d, 30.0))
            estribo_msg = f"ø5.0 c/{esp_max:.1f}cm"

        return {
            "M_apoios": M_apoios, "M_positivos": M_positivos, "Reacoes": Reacoes,
            "As_apoios": As_apoios, "As_positivos": As_positivos,
            "V_max": V_max, "Vrd2": Vrd2, "estribos": estribo_msg, "estribos_lista": estribos_vaos_texto,
            "falha_cortante": falha_cortante, "vaos_internos": vaos_internos, 
            "bal_esq": bal_esq, "bal_dir": bal_dir
        }
    except Exception as e:
        return {"erro": str(e)}

def sugerir_barras(as_req):
    if as_req == -1: return "Redim.!"
    if as_req <= 0: return "2 ø 8.0mm"
    bitolas = [("ø10mm", 0.79), ("ø12.5mm", 1.23), ("ø16mm", 2.01)]
    for nome, area in bitolas:
        qtd = int(np.ceil(as_req / area))
        if qtd >= 2: return f"{qtd} {nome}"
    return f"{as_req:.2f} cm²"

# --- GERENCIAMENTO DE ESTADO ---
if 'lista_vaos' not in st.session_state:
    st.session_state.lista_vaos = []
if 'contador' not in st.session_state:
    st.session_state.contador = 1
if 'edit_index' not in st.session_state:
    st.session_state.edit_index = None

# --- INTERFACE DE ENTRADA DE DADOS ---
st.header("1. Seção, Concreto e Aço")
col1, col2, col3, col4 = st.columns(4)
b = col1.number_input("Base (bw) [cm]", value=20)
h = col2.number_input("Altura (h) [cm]", value=45)
fck = col3.number_input("Concreto fck [MPa]", value=30)
tipo_aco = col4.text_input("Aço de Projeto", value="CA-50A", disabled=True)
dados_g = {'b': b, 'h': h, 'fck': fck}

st.header("2. Inserir Elementos da Viga")

num_normais = sum(1 for v in st.session_state.lista_vaos if v['tipo'] == 'Normal')

# MODO DE EDIÇÃO: Alinhado verticalmente para o celular
if st.session_state.edit_index is not None:
    idx = st.session_state.edit_index
    st.markdown(f'<div class="tramo-header">✏️ MODIFICANDO TRAMO: {st.session_state.lista_vaos[idx]["nome"]}</div>', unsafe_allow_html=True)
    
    tipo_ed = st.selectbox("Tipo do Tramo", ["Normal", "Balanço Esquerdo", "Balanço Direito"], index=["Normal", "Balanço Esquerdo", "Balanço Direito"].index(st.session_state.lista_vaos[idx]['tipo']), key="ed_tipo")
    L_ed = st.number_input("Comprimento [m]", value=float(st.session_state.lista_vaos[idx]['L']), step=0.1, key="ed_L")
    q_ed = st.number_input("Carga Distr. [kN/m]", value=float(st.session_state.lista_vaos[idx]['q']), step=0.5, key="ed_q")
    P_ed = st.number_input("Carga Conc. [kN]", value=float(st.session_state.lista_vaos[idx]['P']), step=0.5, key="ed_p")
    a_ed = st.number_
