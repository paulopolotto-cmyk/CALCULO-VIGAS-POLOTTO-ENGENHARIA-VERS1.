import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

# Configuração da página para o celular
st.set_page_config(page_title="Polotto Engenharia", layout="centered")

# Estilização CSS Cirúrgica para fixar a Tecla Amarela e Ajustar o Layout
st.markdown("""
    <style>
    .titulo { text-align: center; color: white; background-color: #1E3A8A; padding: 12px; font-weight: bold; font-size: 20px; border-radius: 5px; }
    .tramo-header { text-align: center; background-color: #E0F2FE; color: #0369A1; padding: 6px; font-weight: bold; border-radius: 5px; margin-bottom: 10px; }
    
    /* ESTILO DO BOTÃO DE INSERIR: Amarelo estruturado, grande e destacado */
    div.stButton > button[key="btn_amarelo_inserir"] {
        background-color: #FFDE4D !important;
        color: #000000 !important;
        font-size: 18px !important;
        font-weight: bold !important;
        height: 52px !important;
        width: 100% !important;
        border: 2px solid #E6B905 !important;
        border-radius: 6px !important;
        box-shadow: 0px 4px 6px rgba(0,0,0,0.1) !important;
    }
    div.stButton > button[key="btn_amarelo_inserir"]:hover {
        background-color: #F4CE24 !important;
        border-color: #D4A902 !important;
    }
    
    /* Botão de Calcular em Vermelho Padrão */
    div.stButton > button[type="primary"] {
        width: 100% !important;
        height: 52px !important;
        font-weight: bold !important;
        background-color: #FF4B4B !important;
        color: white !important;
        font-size: 16px !important;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="titulo">PROGRAMA DE CÁLCULOS DE VIGAS DA POLOTTO ENGENHARIA</div>', unsafe_allow_html=True)
st.write("")

# --- MOTOR MATEMÁTICO ---
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
            
        MA = - (bal_esq[0]['q'] * bal_esq[0]['L']**2) / 2 if bal_esq else 0.0
        MZ = - (bal_dir[0]['q'] * bal_dir[0]['L']**2) / 2 if bal_dir else 0.0
        
        if num_vaos == 1:
            L1 = vaos_internos[0]['L']
            q1 = vaos_internos[0]['q']
            P1 = vaos_internos[0]['P']
            
            MB = MZ 
            VA_iso = q1 * L1 / 2 + P1 / 2
            VB_iso = VA_iso
            VA = VA_iso + (MB - MA)/L1
            VB = VB_iso + (MA - MB)/L1
            
            M_pos = max(0, ((q1 * L1**2)/8 + (P1 * L1)/4) + (MA + MB)/2)
            
            q_be = bal_esq[0]['q'] if bal_esq else 0
            q_bd = bal_dir[0]['q'] if bal_dir else 0
            V_max = max(abs(VA), abs(VB), q_be * (bal_esq[0]['L'] if bal_esq else 0), q_bd * (bal_dir[0]['L'] if bal_dir else 0))
            
            M_apoios = [MA, MB]
            M_positivos = [M_pos]
            Reacoes = [VA + q_be * (bal_esq[0]['L'] if bal_esq else 0), VB + q_bd * (bal_dir[0]['L'] if bal_dir else 0)]
            V_por_vao = [max(abs(VA), abs(VB))]
        else:
            num_incog = num_apoios - 2
            A_mat = np.zeros((num_incog, num_incog))
            B_mat = np.zeros(num_incog)
            
            W = []
            for v in vaos_internos:
                W.append((v['q'] * v['L']**3)/24 + (v['P'] * v['L']**2)/16)
                
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
                M_esq = M_apoios[i]
                M_dir = M_apoios[i+1]
                
                V_iso = q * L / 2 + P / 2
                V_hip_esq = (M_dir - M_esq) / L
                V_hip_dir = (M_esq - M_dir) / L
                
                V_esq_total = V_iso + V_hip_esq
                V_dir_total = V_iso + V_hip_dir
                
                Reacoes_apoio[i] += V_esq_total
                Reacoes_apoio[i+1] += V_dir_total
                
                M_pos = max(0, ((q * L**2)/8 + (P * L)/4) + (M_esq + M_dir)/2)
                M_positivos.append(M_pos)
                
                V_max_vao = max(abs(V_esq_total), abs(V_dir_total))
                V_por_vao.append(V_max_vao)
                V_max = max(V_max, V_max_vao)
                
            if bal_esq:
                Reacoes_apoio[0] += bal_esq[0]['q'] * bal_esq[0]['L']
                V_max = max(V_max, bal_esq[0]['q'] * bal_esq[0]['L'])
            if bal_dir:
                Reacoes_apoio[-1] += bal_dir[0]['q'] * bal_dir[0]['L']
                V_max = max(V_max, bal_dir[0]['q'] * bal_dir[0]['L'])
                
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

val_tipo = "Normal"
val_L = 4.0
val_q = 15.0
val_P = 0.0

if st.session_state.edit_index is not None:
    idx = st.session_state.edit_index
    val_tipo = st.session_state.lista_vaos[idx]['tipo']
    val_L = st.session_state.lista_vaos[idx]['L']
    val_q = st.session_state.lista_vaos[idx]['q']
    val_P = st.session_state.lista_vaos[idx]['P']

# --- INTERFACE DE ENTRADA DE DADOS ---
st.header("1. Seção, Concreto e Aço")
col1, col2, col3, col4 = st.columns(4)
b = col1.number_input("Base (bw) [cm]", value=20)
h = col2.number_input("Altura (h) [cm]", value=45)
fck = col3.number_input("Concreto fck [MPa]", value=30)
tipo_aco = col4.text_input("Aço de Projeto", value="CA50A", disabled=True)
dados_g = {'b': b, 'h': h, 'fck': fck}

st.header("2. Inserir Elementos da Viga")

num_normais = sum(1 for v in st.session_state.lista_vaos if v['tipo'] == 'Normal')
texto_tramo_atual = f"Tramo {len(st.session_state.lista_vaos) + 1} - Vão {num_normais + 1}" if st.session_state.edit_index is None else f"Editando: {st.session_state.lista_vaos[st.session_state.edit_index]['nome']}"
st.markdown(f'<div class="tramo-header">{texto_tramo_atual}</div>', unsafe_allow_html=True)

tipo = st.selectbox("Tipo do Tramo", ["Normal", "Balanço Esquerdo", "Balanço Direito"], index=["Normal", "Balanço Esquerdo", "Balanço Direito"].index(val_tipo))
colL, colQ, colP = st.columns(3)
L = colL.number_input("Comprimento [m]", value=val_L, step=0.1, key="input_L")
q = colQ.number_input("Carga Distr. (q) [kN/m]", value=val_q, step=0.5, key="input_q")
P = colP.number_input("Carga Conc. (P) [kN]", value=val_P, step=0.5, key="input_P")

st.write("")

# SOLUÇÃO DEFINITIVA: Botão oficial do Streamlit estilizado perfeitamente como amarelo por ID interno
btn_inserir = st.button("➕ INSERIR TRAMO NA VIGA", key="btn_amarelo_inserir")

if btn_inserir:
    if st.session_state.edit_index is None:
        if tipo == "Balanço Esquerdo" and any(v['tipo'] == "Balanço Esquerdo" for v in st.session_state.lista_vaos):
            st.error("Já existe um Balanço Esquerdo!")
        elif tipo == "Balanço Direito" and any(v['tipo'] == "Balanço Direito" for v in st.session_state.lista_vaos):
            st.error("Já existe um Balanço Direito!")
        else:
            nome_tramo = f"Vão {st.session_state.contador}" if tipo == "Normal" else tipo
            if tipo == "Normal": st.session_state.contador += 1
            st.session_state.lista_vaos.append({'nome': nome_tramo, 'tipo': tipo, 'L': L, 'q': q, 'P': P})
            st.rerun()
    else:
        st.session_state.lista_vaos[st.session_state.edit_index] = {'nome': st.session_state.lista_vaos[st.session_state.edit_index]['nome'], 'tipo': tipo, 'L': L, 'q': q, 'P': P}
        st.session_state.edit_index = None
        st.rerun()

# Exibição dos Tramos Cadastrados
if len(st.session_state.lista_vaos) > 0:
    st.write("### 📋 Tramos Inseridos no Projeto:")
    for i, v in enumerate(st.session_state.lista_vaos):
        col_text, col_edit, col_del = st.columns([3, 0.6, 0.6])
        col_text.markdown(f"**{v['nome']}** | L = **{v['L']}m** | q = **{v['q']} kN/m**")
        
        if col_edit.button("✏️", key=f"edit_{i}"):
            st.session_state.edit_index = i
            st.rerun()
            
        if col_del.button("❌", key=f"del_{i}"):
            if v['tipo'] == "Normal": st.session_state.contador -= 1
            st.session_state.lista_vaos.pop(i)
            st.rerun()

    st.write("")
    btn_calc = st.button("⚡ FINALIZAR E CALCULAR VIGA", type="primary")
    st.write("")

    if btn_calc or 'calcular_ativo' in st.session_state:
        st.session_state.calcular_ativo = True
        res = calcular_viga_dinamica(dados_g, st.session_state.lista_vaos)
        
        if "erro" in res:
            st.error(res["erro"])
        else:
            st.write("---")
            st.header("🏁 Layout de Detalhamento Estrutural")
            
            # TEXTO GRANDE EM VERMELHO DE INSUFICIÊNCIA DA SEÇÃO (NBR 6118)
            if res['falha_cortante']:
                st.markdown(f"""
                <div style="background-color:#DC2626; color:white; padding:25px; border-radius:10px; font-weight:bold; font-size:22px; text-align:center; border: 4px solid #7F1D1D; margin-bottom:25px; line-height: 1.5;">
                ⚠️ AS DIMENSÕES DA VIGA ({b}x{h} cm) SÃO INSUFICIENTES!<br>
                A seção de concreto está FORA DAS NORMAS ATUAIS (NBR 6118) por falha por esmagamento da biela seca.<br>
                O esforço total de projeto ultrapassou o limite máximo resistente de {res['Vrd2']:.2f} kN. As dimensões precisam ser alteradas!
                </div>
                """, unsafe_allow_html=True)
                
            # --- DESENHO TÉCNICO ---
            fig, ax = plt.subplots(figsize=(8, 4.2))
            ax.set_xlim(-1, len(res['Reacoes']) + 0.5)
            ax.set_ylim(-2.2, 2.2)
            ax.axis('off')
            
            # Corpo da viga
            ax.fill_between([-0.5, len(res['Reacoes'])-0.5], 0.4, -0.4, color='#E5E7EB')
            
            # Pilares
            for idx, r in enumerate(res['Reacoes']):
                ax.plot(idx, -0.4, '^', color='#1E3A8A', markersize=15)
                ax.text(idx, -0.7, f"Pilar {chr(65+idx)}\n{r:.1f} kN", ha='center', va='top', color='#1E3A8A', fontsize=9, fontweight='bold')
            
            # Armaduras principais
            ax.plot([-0.4, len(res['Reacoes'])-0.6], [0.25, 0.25], color='#DC2626', linewidth=3.5)
            ax.plot([-0.4, len(res['Reacoes'])-0.6], [-0.25, -0.25], color='#16A34A', linewidth=3.5)
            
            # Negativos nos apoios
            if res['bal_esq']:
                ax.text(-0.3, 0.45, sugerir_barras(res['As_apoios'][0]), color='#DC2626', fontsize=8, ha='center', fontweight='bold')
            for i in range(len(res['M_apoios'])-2):
                ax.text(i+1, 0.45, sugerir_barras(res['As_apoios'][i+1]), color='#DC2626', fontsize=8, ha='center', fontweight='bold')
            if res['bal_dir']:
                ax.text(len(res['Reacoes'])-0.7, 0.45, sugerir_barras(res['As_apoios'][-1]), color='#DC2626', fontsize=8, ha='center', fontweight='bold')
                
            # CORREÇÃO 1: Estribos afastados para baixo (-0.68) para dar leitura perfeita longe da linha verde
            for i in range(len(res['vaos_internos'])):
                ax.text(i + 0.5, -0.18, sugerir_barras(res['As_positivos'][i]), color='#16A34A', fontsize=8, ha='center', fontweight='bold')
                texto_estribo_vao = res['estribos_lista'][i] if not res['falha_cortante'] else "Incompatível"
                ax.text(i + 0.5, -0.68, texto_estribo_vao, color='#78350F', fontsize=8, ha='center', fontweight='bold', style='italic')
            
            # CORREÇÃO 2: Desenho da Seção Transversal com FECHAMENTO TOTAL de bordas explícitas (Z-order forçado para fechar o corte)
            posX_corte = len(res['Reacoes']) - 0.1
            caixa_corte = plt.Rectangle((posX_corte, -0.4), 0.4, 0.8, edgecolor='black', facecolor='#F3F4F6', hatch='//', linewidth=2.0, zorder=5)
            ax.add_patch(caixa_corte)
            ax.text(posX_corte + 0.2, 0.5, f"Corte\n{b}x{h}", ha='center', fontsize=8, fontweight='bold')
            
            st.pyplot(fig)
            
            # --- RELATÓRIO ---
            st.subheader("Relação de Especificações Técnicas")
            status_norma = "⚠️ REPROVADO (Seção Insuficiente!)" if res['falha_cortante'] else "✅ APROVADO CONFORME NBR 6118"
            
            out = [
                f"SEÇÃO TRANSVERSAL: {b}x{h} cm  |  CONCRETO: fck = {fck} MPa  |  AÇO: {tipo_aco}",
                f"STATUS DA FORÇA CORTANTE: {status_norma}",
                f"ARMADURA TRANSVERSAL (ESTRIBOS GERAIS): {res['estribos']}",
                f"CORTANTE MÁXIMO ATUANTE DE PROJETO (Vsd): {res['V_max'] * 1.4:.2f} kN",
                f"RESISTÊNCIA MÁXIMA DA BIELA DE CONCRETO (Vrd2): {res['Vrd2']:.2f} kN"
            ]
            st.code("\n".join(out), language="text")

# Botão para Resetar Projeto
st.write("")
if st.button("🔄 Limpar Tudo e Reiniciar"):
    if 'calcular_ativo' in st.session_state:
        del st.session_state.calcular_ativo
    st.session_state.lista_vaos = []
    st.session_state.contador = 1
    st.session_state.edit_index = None
    st.rerun()
