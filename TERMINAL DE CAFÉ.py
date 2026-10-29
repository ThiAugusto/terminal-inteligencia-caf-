import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
import pydeck as pdk
from datetime import datetime, timedelta
import io

# ==========================================
# 1. ESTADO DE SESSÃO E TEMA DINÂMICO
# ==========================================
st.set_page_config(page_title="Terminal Inteligência | Café", layout="wide", initial_sidebar_state="expanded")

if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = False

with st.sidebar:
    st.markdown("### ⚙️ Configurações do Terminal")
    dark_mode = st.toggle("🌙 Modo Bloomberg (Dark)", value=st.session_state.dark_mode)
    st.session_state.dark_mode = dark_mode

# Variáveis Dinâmicas baseadas no Tema
if dark_mode:
    bg_app = "#050505"
    bg_card = "#111111"
    border_color = "#333333"
    text_main = "#F5F5F5"
    text_muted = "#AAAAAA"
    text_highlight = "#FF9800"
    btn_bg = "#FF9800"
    btn_text = "#000000"
    plot_template = "plotly_dark"
    plot_bg = "rgba(17,17,17,0.8)"
    map_style = "dark"
    line_rapida = "#FFB74D"
    line_lenta = "#FF9800"
    heatmap_color = "solar"
    arc_color = [255, 152, 0, 200]
else:
    bg_app = "#FAF0E6"
    bg_card = "#F5E6D3"
    border_color = "#D7CCC8"
    text_main = "#3E2723"
    text_muted = "#5D4037"
    text_highlight = "#5D4037"
    btn_bg = "#5D4037"
    btn_text = "#FFFFFF"
    plot_template = "none"
    plot_bg = "rgba(245, 230, 211, 0.4)"
    map_style = "light"
    line_rapida = "#8D6E63"
    line_lenta = "#3E2723"
    heatmap_color = "ylorbr"
    arc_color = [93, 64, 55, 200]

# CSS Poderoso
st.markdown(f"""
    <style>
    [data-testid="stHeader"] {{ background-color: transparent !important; }}
    .block-container {{ padding-top: 1rem !important; padding-bottom: 1rem !important; }}
    
    [data-testid="stSidebar"] {{ background-color: {bg_card} !important; border-right: 1px solid {border_color} !important; }}
    
    .stApp, .stMarkdown p, .stMarkdown li, label, .stMarkdown span {{ 
        background-color: transparent; color: {text_main} !important; font-family: 'Segoe UI', sans-serif; 
    }}
    .stApp {{ background-color: {bg_app}; }}
    
    div[data-testid="metric-container"] {{ 
        background-color: {bg_card}; border: 1px solid {border_color}; padding: 20px; 
        border-radius: 10px; box-shadow: 3px 3px 10px rgba(0, 0, 0, 0.2);
    }}
    div[data-testid="metric-container"] label {{ color: {text_highlight} !important; font-weight: bold; font-size: 1.1rem; }}
    
    div[data-testid="stMetricValue"] {{ color: {text_main} !important; }}
    div[data-testid="stMetricValue"] > div {{ color: {text_main} !important; }}
    div[data-testid="stMetricDelta"] > div {{ color: {text_muted} !important; }}
    
    h1, h2, h3, h4 {{ color: {text_main} !important; }}
    hr {{ border-bottom: 1px solid {border_color} !important; margin-top: 5px; margin-bottom: 20px; }}
    
    .stTabs [data-baseweb="tab-list"] {{ gap: 10px; }}
    .stTabs [data-baseweb="tab"] {{ background-color: {bg_card}; border-radius: 6px 6px 0px 0px; padding: 12px 24px; color: {text_highlight}; font-size: 1.1rem; border: 1px solid {border_color}; }}
    .stTabs [aria-selected="true"] {{ background-color: {bg_app}; font-weight: bold; border-bottom: 3px solid {text_highlight} !important; border-top: 2px solid {text_highlight} !important; color: {text_main} !important; }}
    
    .insight-box {{ background-color: {bg_card}; padding: 20px; border-left: 6px solid {text_highlight}; border-radius: 6px; font-size: 1.05em; line-height: 1.6; box-shadow: 2px 2px 8px rgba(0,0,0,0.1); color: {text_main} !important; }}
    .insight-box b, .insight-box h4 {{ color: {text_main} !important; }}
    
    [data-testid="stBaseButton-secondary"], .stDownloadButton button {{
        background-color: {btn_bg} !important; border: none !important; padding: 10px 20px !important; border-radius: 5px !important;
    }}
    [data-testid="stBaseButton-secondary"] p, .stDownloadButton button p {{ color: {btn_text} !important; font-weight: bold !important; font-size: 1.1em !important; }}
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 2. MOTOR DE DADOS E ESTATÍSTICA (À PROVA DE FALHAS)
# ==========================================
@st.cache_data(ttl=300)
def obter_dados():
    hoje = datetime.today()
    inicio = hoje - timedelta(days=180)
    tickers = ['KC=F', 'BRL=X', 'CL=F']
    
    try:
        df_raw = yf.download(tickers, start=inicio, end=hoje, progress=False)
        
        # Ajuste para lidar com diferentes versões do yfinance na nuvem
        if isinstance(df_raw.columns, pd.MultiIndex):
            df_close = df_raw['Close'].copy()
        else:
            df_close = df_raw.copy()
            
        # Mapeando colunas com segurança
        df_macro = pd.DataFrame()
        df_macro['Dolar'] = df_close['BRL=X'] if 'BRL=X' in df_close.columns else pd.Series(dtype=float)
        df_macro['Petroleo'] = df_close['CL=F'] if 'CL=F' in df_close.columns else pd.Series(dtype=float)
        df_macro['Cafe'] = df_close['KC=F'] if 'KC=F' in df_close.columns else pd.Series(dtype=float)
        
        # Corrige feriados antes de remover linhas vazias
        df_macro = df_macro.ffill().bfill().dropna()
        
        cafe_full = yf.download('KC=F', start=inicio, end=hoje, progress=False)
        if isinstance(cafe_full.columns, pd.MultiIndex):
            cafe_full.columns = cafe_full.columns.get_level_values(0)
            
        return cafe_full, df_macro
    except Exception:
        return pd.DataFrame(), pd.DataFrame()

cafe_df, macro_df = obter_dados()

# TRAVA DE SEGURANÇA PROFISSIONAL
if cafe_df.empty or macro_df.empty:
    st.warning("⏳ **Aviso de Conexão (Nuvem):** O servidor do Yahoo Finance bloqueou a nossa requisição temporariamente devido ao alto tráfego no Streamlit Cloud. Por favor, atualize a página em 1 ou 2 minutos.")
    st.stop()

preco_atual = cafe_df['Close'].iloc[-1].item()
dolar_atual = macro_df['Dolar'].iloc[-1].item()

# ==========================================
# 3. CABEÇALHO DO TERMINAL
# ==========================================
st.title("☕ TERMINAL QUANTITATIVO: COMMODITIES AGRÍCOLAS")
st.markdown("**Desk de Arbitragem, Modelagem de Risco e Fluxo Logístico (FOB Santos)**")
st.divider()

col1, col2, col3, col4 = st.columns(4)
col1.metric("Cotação ICE (USc/lb)", f"{preco_atual:.2f}")
col2.metric("Câmbio PTAX (USD/BRL)", f"R$ {dolar_atual:.4f}")
col3.metric("Paridade Exportação (R$/sc)", f"R$ {(preco_atual * 1.32 * dolar_atual):.2f}", "Referência Embarque FOB")
col4.metric("Volatilidade Histórica (30d)", f"{(macro_df['Cafe'].pct_change().std() * np.sqrt(252) * 100):.1f}%", "Risco Anualizado", delta_color="off")
st.markdown("<br>", unsafe_allow_html=True)

# ==========================================
# 4. MÓDULOS DE ANÁLISE (5 ABAS)
# ==========================================
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📈 Análise Técnica", 
    "🌍 Matriz Macro", 
    "🎲 Risco & Cenários", 
    "🗺️ Fluxo Logístico", 
    "🗞️ Relatório Desk"
])

# --- ABA 1: ANÁLISE TÉCNICA ---
with tab1:
    st.markdown("### Ação de Preço e Dinâmica de Curto Prazo")
    fig = go.Figure()
    
    fig.add_trace(go.Candlestick(
        x=cafe_df.index, open=cafe_df['Open'], high=cafe_df['High'], low=cafe_df['Low'], close=cafe_df['Close'], 
        increasing_line_color='#4CAF50' if dark_mode else '#5D4037', 
        decreasing_line_color='#F44336' if dark_mode else '#D84315', name='Café ICE'
    ))
    
    mm9 = cafe_df['Close'].rolling(9).mean()
    mm21 = cafe_df['Close'].rolling(21).mean()
    
    fig.add_trace(go.Scatter(x=cafe_df.index, y=mm9, line=dict(color=line_rapida, width=3), name='Média 9d (Rápida)'))
    fig.add_trace(go.Scatter(x=cafe_df.index, y=mm21, line=dict(color=line_lenta, width=4, dash='dot'), name='Média 21d (Tendência)'))
    
    fig.update_layout(template=plot_template, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor=plot_bg, xaxis_rangeslider_visible=False, height=550, margin=dict(l=0, r=0, t=20, b=0))
    st.plotly_chart(fig, use_container_width=True)

# --- ABA 2: MATRIZ MACRO ---
with tab2:
    st.markdown("### Impacto Cruzado: Café, Dólar e Custos Logísticos (WTI)")
    c1, c2 = st.columns([2, 1])
    
    with c1:
        corr = macro_df.pct_change().dropna().corr()
        fig_corr = px.imshow(corr, text_auto=".2f", color_continuous_scale=heatmap_color, aspect="auto")
        fig_corr.update_layout(template=plot_template, paper_bgcolor='rgba(0,0,0,0)', height=500, margin=dict(l=0, r=0, t=20, b=0))
        st.plotly_chart(fig_corr, use_container_width=True)
        
    with c2:
        st.markdown("""
        <br><br>
        <div class="insight-box">
        <h4 style="margin-top:0px;">Matriz de Correlação</h4>
        A matriz mostra a <b>Força Direcional (de -1 a 1)</b> entre os ativos:<br><br>
        • <b>Próximo de 1.0:</b> Andam juntos.<br>
        • <b>Próximo de -1.0:</b> Andam em direções opostas.<br>
        • <b>Próximo de 0:</b> Movimentos independentes.<br><br>
        <i>Prática na Mesa:</i> Uma correlação negativa forte exige que a trading ajuste o "hedge ratio".
        </div>
        """, unsafe_allow_html=True)

# --- ABA 3: RISCO & CENÁRIOS (MONTE CARLO) ---
with tab3:
    st.markdown("### Modelo de Risco: Projeção Estocástica (Próximos 30 Dias)")
    c1, c2 = st.columns([2, 1])
    
    retornos = np.log(macro_df['Cafe'] / macro_df['Cafe'].shift(1)).dropna()
    mu, sigma = retornos.mean(), retornos.std()
    dias, cenarios = 30, 50 
    simulacoes = np.zeros((dias, cenarios))
    simulacoes[0] = preco_atual
    
    for t in range(1, dias):
        simulacoes[t] = simulacoes[t-1] * np.exp(np.random.normal(loc=mu, scale=sigma, size=cenarios))
    
    df_sim = pd.DataFrame(simulacoes)
    preco_medio_30d = df_sim.iloc[-1].mean()
    pior_cenario_95 = np.percentile(df_sim.iloc[-1], 5) 
    
    with c1:
        fig_mc = go.Figure()
        sim_color = 'rgba(255, 255, 255, 0.1)' if dark_mode else 'rgba(141, 110, 99, 0.15)'
        for col in df_sim.columns:
            fig_mc.add_trace(go.Scatter(y=df_sim[col], mode='lines', line=dict(width=2, color=sim_color)))
            
        fig_mc.add_trace(go.Scatter(y=df_sim.mean(axis=1), mode='lines', name='Tendência Esperada', line=dict(color=line_lenta, width=6)))
        fig_mc.add_trace(go.Scatter(y=df_sim.apply(lambda x: np.percentile(x, 5), axis=1), mode='lines', name='VaR 95% (Pior Cenário)', line=dict(color='#F44336' if dark_mode else '#D84315', width=4, dash='dash')))
        
        fig_mc.update_layout(template=plot_template, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor=plot_bg, showlegend=True, xaxis_title="Dias no Futuro", yaxis_title="Preço (USc/lb)", height=500, margin=dict(l=0, r=0, t=10, b=0))
        st.plotly_chart(fig_mc, use_container_width=True)
        
    with c2:
        st.markdown(f"""
        <br><br>
        <div class="insight-box">
        <h4 style="margin-top:0px;">Estatística de Risco (VaR)</h4>
        O algoritmo simula 50 caminhos baseados na volatilidade real.<br><br>
        • <b>Alvo Médio (30d):</b> {preco_medio_30d:.2f} USc/lb<br>
        • <b>Value at Risk (VaR 95%):</b> {pior_cenario_95:.2f} USc/lb<br><br>
        <i>Decisão Estratégica:</i> A mesa tem 95% de confiança estatística de que o mercado <b>não cairá abaixo de {pior_cenario_95:.2f}</b>.
        </div>
        """, unsafe_allow_html=True)

# --- ABA 4: MAPA DE FLUXO LOGÍSTICO (PYDECK 3D) ---
with tab4:
    st.markdown("### Malha Logística: Rotas de Originação vs Escoamento")
    
    c1_map, c2_map = st.columns([2, 1])
    
    with c1_map:
        df_pontos = pd.DataFrame({
            'Local': ['Porto de Santos (SP)', 'Sul de Minas (MG)', 'Cerrado Mineiro (MG)', 'Alta Mogiana (SP)'],
            'Lat': [-23.9618, -21.2294, -18.9186, -20.5383],
            'Lon': [-46.3322, -45.4947, -48.2772, -47.4008],
            'Cor': [[216, 67, 21, 255], [255, 152, 0, 255], [255, 152, 0, 255], [255, 152, 0, 255]] if dark_mode else [[216, 67, 21, 200], [141, 110, 99, 200], [141, 110, 99, 200], [141, 110, 99, 200]]
        })

        df_rotas = pd.DataFrame({
            'Lat_Origem': [-21.2294, -18.9186, -20.5383],
            'Lon_Origem': [-45.4947, -48.2772, -47.4008],
            'Lat_Destino': [-23.9618, -23.9618, -23.9618],
            'Lon_Destino': [-46.3322, -46.3322, -46.3322]
        })

        layer_pontos = pdk.Layer("ScatterplotLayer", df_pontos, get_position="[Lon, Lat]", get_color="Cor", get_radius=12000, pickable=True)
        layer_rotas = pdk.Layer("ArcLayer", df_rotas, get_source_position="[Lon_Origem, Lat_Origem]", get_target_position="[Lon_Destino, Lat_Destino]", get_source_color=arc_color, get_target_color=[216, 67, 21, 255], get_width=5, pickable=True)

        view_state = pdk.ViewState(latitude=-21.5, longitude=-46.5, zoom=5.5, pitch=45)

        r = pdk.Deck(layers=[layer_rotas, layer_pontos], initial_view_state=view_state, map_style=map_style, tooltip={"text": "{Local}"})
        st.pydeck_chart(r, use_container_width=True)
        
    with c2_map:
        st.markdown("""
        <br><br>
        <div class="insight-box">
        <h4 style="margin-top:0px;">Estratégia de Escoamento</h4>
        O <b>Porto de Santos</b> concentra mais de 70% da exportação de café. <br><br>
        <b>Métricas de Rota (Estimadas):</b><br>
        🚚 <i>Sul de Minas ➔ Santos:</i> ~310 km<br>
        🚚 <i>Alta Mogiana ➔ Santos:</i> ~410 km<br>
        🚚 <i>Cerrado ➔ Santos:</i> ~590 km<br><br>
        <i>Dica: Segure o botão direito do mouse para girar o mapa em 3D.</i>
        </div>
        """, unsafe_allow_html=True)

# --- ABA 5: DOWNLOAD E INSIGHTS (EXCEL RICO) ---
with tab5:
    st.markdown("### Exportação de Relatório Executivo (Excel)")
    
    st.markdown("""
        <div class="insight-box" style="margin-bottom: 20px;">
        Este arquivo <b>.xlsx</b> é gerado automaticamente com formatação corporativa nativa (Data, Moeda) e inclui um dashboard financeiro desenhado em tempo real dentro do Excel. Ideal para enviar à diretoria.
        </div>
    """, unsafe_allow_html=True)
    
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        df_export = macro_df.reset_index()
        df_export.rename(columns={'Date': 'Data Base'}, inplace=True)
        df_export.to_excel(writer, sheet_name='Dashboard_Quant', index=False)
        
        workbook  = writer.book
        worksheet = writer.sheets['Dashboard_Quant']
        
        formato_header = workbook.add_format({'bold': True, 'font_color': 'white', 'bg_color': '#3E2723', 'border': 1, 'align': 'center'})
        formato_data = workbook.add_format({'num_format': 'dd/mm/yyyy', 'align': 'center'})
        formato_moeda = workbook.add_format({'num_format': 'R$ #,##0.00'})
        formato_preco = workbook.add_format({'num_format': '#,##0.00'})
        
        worksheet.set_column('A:A', 15, formato_data)
        worksheet.set_column('B:B', 15, formato_moeda)
        worksheet.set_column('C:C', 15, formato_preco)
        worksheet.set_column('D:D', 15, formato_preco)
        
        for col_num, value in enumerate(df_export.columns.values):
            worksheet.write(0, col_num, value, formato_header)
            
        chart = workbook.add_chart({'type': 'line'})
        max_row = len(df_export)
        
        if max_row > 1:
            chart.add_series({
                'name':       ['Dashboard_Quant', 0, 3],
                'categories': ['Dashboard_Quant', 1, 0, max_row, 0],
                'values':     ['Dashboard_Quant', 1, 3, max_row, 3],
                'line':       {'color': '#5D4037', 'width': 2.25}
            })
            
            chart.set_title ({'name': 'Evolução Cotação ICE (USc/lb)'})
            chart.set_x_axis({'name': 'Período', 'date_axis': True})
            chart.set_y_axis({'name': 'USc/lb', 'major_gridlines': {'visible': True}})
            chart.set_legend({'position': 'bottom'})
            worksheet.insert_chart('F2', chart, {'x_scale': 1.5, 'y_scale': 1.2})
        
    buffer.seek(0)
    st.download_button(
        label="📊 Baixar Relatório Executivo (.xlsx)",
        data=buffer,
        file_name='Desk_Macro_Cafe_Profissional.xlsx',
        mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
