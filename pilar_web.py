import streamlit as strt
import matplotlib.pyplot as plt
import math
import os

# --- REDIRECIONAMENTO AUTOMÁTICO FORÇADO DO TERMINAL ---
caminho_projeto = r"C:\Users\paulo\OneDrive\Área de Trabalho\CALCULO DE PILAR"
try:
    os.chdir(caminho_projeto)
except Exception:
    pass

# Configuração da página para web/celular
strt.set_page_config(page_title="Pilar NBR 6118", layout="centered")

# --- CUSTOMIZAÇÃO DE CORES PARA MODO ESCURO EXTREMO ---
strt.markdown("""
    <style>
    /* Força os campos de digitação (Inputs) a terem fundo escuro com números BRANCOS bem visíveis */
    input, select, div[data-baseweb="select"] {
        background-color: #1E1E1E !important;
        color: #FFFFFF !important;
        font-weight: bold !important;
        font-size: 16px !important;
        border: 2px solid #00BFFF !important;
    }
    
    /* Força TODA a tabela de ferragens a ter fundo amarelo ouro com letras pretas em negrito */
    .stTable, table, tbody, tr, td, th, div[data-testid="stTable"] {
        background-color: #FFD700 !important;
        color: #000000 !important;
        font-weight: bold !important;
        font-size: 14px !important;
        border: 2px solid #B8860B !important;
        text-align: center !important;
    }
    .stTable th {
        background-color: #B8860B !important;
        color: #FFFFFF !important;
    }
    div.stButton > button:first-child {
        background-color: #FFD700 !important;
        color: #000000 !important;
        font-weight: bold !important;
        border: 2px solid #B8860B !important;
        height: 45px !important;
        width: 100% !important;
        font-size: 16px !important;
    }
    </style>
""", unsafe_allow_html=True)

def bloco_amarelo(texto, tamanho_fonte=14, alinhamento="left"):
    strt.markdown(f'<div style="background-color: #FFD700; padding: 10px; border-radius: 6px; margin-top: 6px; margin-bottom: 6px; text-align: {alinhamento}; border: 2px solid #B8860B;"><span style="color: #000000; font-weight: bold; font-size: {tamanho_fonte}px; font-family: \'Segoe UI\', sans-serif;">{texto}</span></div>', unsafe_allow_html=True)

def bloco_azul(texto, tamanho_fonte=13, alinhamento="left"):
    strt.markdown(f'<div style="background-color: #00BFFF; padding: 8px; border-radius: 6px; margin-top: 5px; margin-bottom: 5px; text-align: {alinhamento}; border: 2px solid #00008B;"><span style="color: #FFFFFF; font-weight: bold; font-size: {tamanho_fonte}px; font-family: \'Segoe UI\', sans-serif;">{texto}</span></div>', unsafe_allow_html=True)

def bloco_vermelho(texto, tamanho_fonte=14, alinhamento="left"):
    strt.markdown(f'<div style="background-color: #FF0000; padding: 12px; border-radius: 6px; margin-top: 8px; margin-bottom: 8px; text-align: {alinhamento}; border: 2px solid #8B0000;"><span style="color: #FFFFFF; font-weight: bold; font-size: {tamanho_fonte}px; font-family: \'Segoe UI\', sans-serif;">⚠️ {texto}</span></div>', unsafe_allow_html=True)

def bloco_verde(texto, tamanho_fonte=14, alinhamento="left"):
    strt.markdown(f'<div style="background-color: #32CD32; padding: 10px; border-radius: 6px; margin-top: 6px; margin-bottom: 6px; text-align: {alinhamento}; border: 2px solid #006400;"><span style="color: #FFFFFF; font-weight: bold; font-size: {tamanho_fonte}px; font-family: \'Segoe UI\', sans-serif;">✅ {texto}</span></div>', unsafe_allow_html=True)

bloco_amarelo("🏢 MOTOR DE CÁLCULO MULTI-BITOLAS (NBR 6118)", tamanho_fonte=18, alinhamento="center")
bloco_amarelo("📋 DADOS DE ENTRADA DO PILAR", tamanho_fonte=14, alinhamento="center")

col1, col2 = strt.columns(2)
with col1:
    bloco_azul("📐 Base b (menor dimensão) [cm]")
    b = strt.number_input("", min_value=14.0, value=20.0, step=1.0, key="b_input", label_visibility="collapsed")
    bloco_azul("📐 Altura h (maior dimensão) [cm]")
    h = strt.number_input("", min_value=14.0, value=30.0, step=1.0, key="h_input", label_visibility="collapsed")

with col2:
    bloco_azul("📏 Altura livre do pilar l0 [m]")
    l0 = strt.number_input("", min_value=0.5, value=2.8, step=0.1, key="l0_input", label_visibility="collapsed")
    bloco_azul("🧱 Fck do Concreto [MPa]")
    fck = strt.number_input("", min_value=20, value=30, step=5, key="fck_input", label_visibility="collapsed")

bloco_azul("💥 Força Normal Carga Fk (Projeto) [kN]")
fk = strt.number_input("", min_value=1.0, value=500.0, step=50.0, key="fk_input", label_visibility="collapsed")

strt.write("")

if "opcao_selecionada" not in strt.session_state:
    strt.session_state.opcao_selecionada = None

if strt.button("🚀 CALCULAR E EXIBIR ARRANJOS PERMITIDOS PELA NORMA"):
    try:
        if b * h < 360:
            bloco_vermelho("ERRO DE NORMA: A área mínima de seção para pilar deve ser 360 cm².", alinhamento="center")
        else:
            gamma_n = 1.95 - 0.05 * b if b < 19 else 1.0
            Nd = fk * 1.4 * gamma_n 
            fcd = (fck / 10) / 1.4 
            fyd = 50 / 1.15 
            Ac = b * h
            N_concreto = 0.85 * fcd * Ac
            
            As_nec_calculo = (Nd - N_concreto) / fyd if Nd > N_concreto else 0.0
            As_min_norma = max(0.15 * Nd / fyd, 0.004 * Ac)
            As_final = max(As_nec_calculo, As_min_norma)
            
            bitolas = [10.0, 12.5, 16.0, 20.0, 25.0]
            opcoes_validas = []
            recob = 3.0
            s_min_livre = 2.5 
            
            for phi in bitolas:
                area_b = (math.pi * (phi / 10)**2) / 4
                n_test = 4
                while n_test <= 20:
                    as_teste = n_test * area_b
                    if as_teste >= As_final and as_teste <= 0.04 * Ac:
                        perimetro_util = 2 * ((b - 2*recob) + (h - 2*recob))
                        espaco_livre = (perimetro_util - (n_test * (phi/10))) / n_test
                        
                        if espaco_livre >= s_min_livre:
                            comp_b = l0 + (40 * (phi / 10) / 100)
                            peso_m = (math.pi * (phi/1000)**2 / 4) * 7850
                            peso_t = comp_b * n_test * peso_m
                            opcoes_validas.append({
                                "texto": f"{n_test} barras de Ø {phi:.1f} mm",
                                "barras": n_test, "phi": phi, "peso": peso_t, "as_ef": as_teste
                            })
                            break 
                    n_test += 2
            
            if not opcoes_validas:
                bloco_vermelho("A SEÇÃO DE CONCRETO É INSUFICIENTE PARA A CARGA APLICADA! Aumente as dimensões ou o Fck.", alinhamento="center")
                strt.session_state.opcoes = []
            else:
                opcoes_validas = sorted(opcoes_validas, key=lambda x: x["peso"])
                strt.session_state.opcoes = opcoes_validas
                strt.session_state.As_final = As_final
                strt.session_state.caiu_na_minima = As_min_norma > As_nec_calculo
                strt.session_state.As_min_norma = As_min_norma
                strt.session_state.b = b
                strt.session_state.h = h
                strt.session_state.l0 = l0
                strt.session_state.Nd = Nd
    except Exception as e:
        strt.error(f"Erro: {str(e)}")

if "opcoes" in strt.session_state and strt.session_state.opcoes:
    bloco_amarelo("🎯 SELEÇÃO DO ENGENHEIRO (Arranjos aprovados pela NBR 6118)", tamanho_fonte=14, alinhamento="center")
    
    if strt.session_state.caiu_na_minima:
        bloco_vermelho(f"Aviso de Norma: Carga baixa. Aplicada armadura mínima de norma: {strt.session_state.As_min_norma:.2f} cm².", tamanho_fonte=12, alinhamento="center")
    
    mais_economica = strt.session_state.opcoes[0]["texto"]
    bloco_verde(f"Sugestão Econômica do Motor (Menor Peso): {mais_economica}", tamanho_fonte=13)
    
    # --- PARTE CORRIGIDA: ENVELOPAMENTO DO SELECTBOX NUMA TARJA AZUL COMPLETA ---
    bloco_azul("👇 CLIQUE ABAIXO PARA SELECIONAR A OPÇÃO DE ARMAÇÃO:")
    lista_textos = [opt["texto"] for opt in strt.session_state.opcoes]
    escolha = strt.selectbox("", lista_textos, label_visibility="collapsed")
    
    selected_opt = next(opt for opt in strt.session_state.opcoes if opt["texto"] == escolha)
    
    b = strt.session_state.b
    h = strt.session_state.h
    l0 = strt.session_state.l0
    num_barras = selected_opt["barras"]
    phi_long = selected_opt["phi"]
    
    phi_estribo = max(5.0, phi_long / 4)
    s_estribo = min(20, b, h, 12 * (phi_long/10))
    comp_barra_long = l0 + (40 * (phi_long / 10) / 100)
    comp_total_long = comp_barra_long * num_barras
    num_estribos = math.ceil((l0 * 100) / s_estribo) + 1
    
    recob = 3.0
    comp_um_est = 2 * ((b - 2*recob) + (h - 2*recob)) + 10
    comp_total_est = (comp_um_est / 100) * num_estribos
    
    peso_tot_long = selected_opt["peso"]
    peso_tot_est = (comp_total_est) * ((math.pi * (phi_estribo/1000)**2 / 4) * 7850)
    
    bloco_amarelo("🎨 CORTE TRANSVERSAL DA OPÇÃO SELECIONADA", tamanho_fonte=14, alinhamento="center")
    col_grafico, col_resumo = strt.columns([4, 6])
    
    with col_grafico:
        fig, ax = plt.subplots(figsize=(2.8, 2.8))
        fig.patch.set_facecolor('#000000')
        ax.set_facecolor('#000000')
        ax.add_patch(plt.Rectangle((0, 0), b, h, edgecolor='#00FF00', facecolor='#2B2B2B', linewidth=3.0))
        ax.add_patch(plt.Rectangle((recob, recob), b-2*recob, h-2*recob, edgecolor='#FF0000', facecolor='none', linewidth=1.5, linestyle='--'))
        
        x_min, x_max = recob + 0.5, b - recob - 0.5
        y_min, y_max = recob + 0.5, h - recob - 0.5
        xs, ys = [], []
        
        if num_barras == 4:
            xs, ys = [x_min, x_max, x_min, x_max], [y_min, y_min, y_max, y_max]
        else:
            cantos = [(x_min, y_min), (x_max, y_min), (x_min, y_max), (x_max, y_max)]
            for cx, cy in cantos: xs.append(cx); ys.append(cy)
            restantes = num_barras - 4
            lados = restantes // 2
            if lados > 0:
                if h >= b:
                    dy = (y_max - y_min) / (lados + 1)
                    for i in range(1, lados + 1): xs.extend([x_min, x_max]); ys.extend([y_min + i*dy, y_min + i*dy])
                else:
                    dx = (x_max - x_min) / (lados + 1)
                    for i in range(1, lados + 1): xs.extend([x_min + i*dx, x_min + i*dx]); ys.extend([y_min, y_max])
                    
        ax.scatter(xs, ys, color='#FFD700', s=80, zorder=5, edgecolor='#FFFFFF', linewidth=0.5)
        ax.set_xlim(-5, b + 5); ax.set_ylim(-5, h + 5); ax.set_aspect('equal'); ax.axis('off')
        ax.text(b/2, -4, f"{b:.0f} cm", ha='center', fontweight='bold', fontsize=11, color='#FFFF00')
        ax.text(-4, h/2, f"{h:.0f} cm", va='center', rotation=90, fontweight='bold', fontsize=11, color='#FFFF00')
        strt.pyplot(fig)
        
    with col_resumo:
        bloco_amarelo(f"Seção: {b:.0f} x {h:.0f} cm", tamanho_fonte=13)
        bloco_amarelo(f"Esforço Nd: {strt.session_state.Nd:.1f} kN", tamanho_fonte=13)
        bloco_amarelo(f"🔴 Ferro Escolhido: {num_barras} x Ø {phi_long:.1f} mm", tamanho_fonte=13)
        bloco_amarelo(f"⚪ Estribos: Ø {phi_estribo:.1f} mm a c/ {s_estribo:.0f} cm", tamanho_fonte=13)

    bloco_amarelo("🛠️ DETALHAMENTO DAS ARMADURAS A SEREM UTILIZADAS", tamanho_fonte=14, alinhamento="center")
    bloco_amarelo(f"📌 Armadura Longitudinal (Otimizada): O algoritmo escolheu a melhor relação peso/segurança: usar {num_barras} barras de ferro com bitola de Ø {phi_long:.1f} mm, com corte individual de {comp_barra_long:.2f} m.")
    bloco_amarelo(f"📌 Armadura Transversal (Estribos): Utilizar {num_estribos} estribos com bitola de Ø {phi_estribo:.1f} mm, espaçados a cada {s_estribo:.0f} cm, com comprimento de corte por estribo de {comp_um_est / 100:.2f} m.")

    bloco_amarelo("📊 TABELA DE FERRAGENS PARA A ESCOLHA", tamanho_fonte=14, alinhamento="center")
    dados_tabela = {
        "Elemento": ["Longitudinal", "Estribos"],
        "Bitola (mm)": [f"{phi_long:.1f}", f"{phi_estribo:.1f}"],
        "Quantidade": [f"{num_barras} un", f"{num_estribos} un"],
        "Comp. Unit (m)": [f"{comp_barra_long:.2f} m", f"{comp_um_est/100:.2f} m"],
        "Comprimento Total (m)": [f"{comp_total_long:.2f} m", f"{comp_total_est:.2f} m"],
        "Peso Total (kg)": [f"{peso_tot_long:.2f} kg", f"{peso_tot_est:.2f} kg"]
    }
    strt.table(dados_tabela)
    bloco_amarelo(f"🏋️ Peso Total de Aço estimado: {peso_tot_long + peso_tot_est:.2f} kg", tamanho_fonte=14, alinhamento="center")
