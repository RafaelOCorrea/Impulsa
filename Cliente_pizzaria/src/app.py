import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import config as cfg
import etl
from datetime import date

# --- DEFINIÇÃO DE CORES (Tema Dark / Cliente) ---
CORES = {
    'primary': '#E0211B',      # Vermelho Impulsa (Destaques)
    'secondary': '#E5E5E5',    # Texto Claro (para fundo escuro)
    'background': '#000000',   # Fundo Preto solicitado
    'card_bg': '#1A1A1A',      # Fundo dos Cartões (Cinza Escuro)
    'charts': ['#E0211B', '#F47C7C', '#FFB7B2', '#A31612', '#680E0B']
}

# --- FUNÇÃO AUXILIAR DE FORMATAÇÃO (BRL) ---
def formatar_real(valor):
    """Formata float para string BRL (R$ 1.234,56) apenas para exibição"""
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

# --- 1. CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    layout="wide", 
    page_title=cfg.NOME_CLIENTE,
    page_icon="🍕"
)

# --- 2. CSS AVANÇADO (DARK MODE) ---
st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');

    html, body, [class*="css"] {{
        font-family: 'Inter', sans-serif;
        color: {CORES['secondary']};
    }}

    /* Fundo Preto */
    .stApp {{
        background-color: {CORES['background']};
    }}

    /* CARTÕES DE MÉTRICAS (KPIs) - Estilo Dark */
    div[data-testid="stMetric"] {{
        background-color: {CORES['card_bg']};
        border-left: 5px solid {CORES['primary']};
        padding: 15px;
        border-radius: 8px;
        box-shadow: 0 4px 6px rgba(255,255,255,0.05); /* Sombra sutil clara */
    }}
    
    /* Valor da Métrica */
    [data-testid="stMetricValue"] {{ 
        color: {CORES['primary']}; 
        font-size: 28px; 
        font-weight: 700;
    }}
    
    /* Label da Métrica */
    [data-testid="stMetricLabel"] {{
        color: #A0A0A0; /* Cinza médio */
        font-size: 14px;
        font-weight: 600;
    }}

    /* SIDEBAR (Mantendo clean, mas adaptada) */
    section[data-testid="stSidebar"] {{
        background-color: #111111;
        border-right: 1px solid #333333;
    }}
    
    /* Textos Gerais */
    h1, h2, h3, p, span {{
        color: {CORES['secondary']} !important;
    }}
    
    /* Ajuste de cor nos inputs da sidebar para ficarem visíveis */
    .stMultiSelect, .stDateInput {{
        color: white;
    }}

</style>
""", unsafe_allow_html=True)

# --- 3. BARRA LATERAL (CONTROLO) ---
st.sidebar.title("🍕 Painel de Controle")

with st.sidebar.expander("⚙️ Gestão de Dados", expanded=False):
    up_file = st.file_uploader("Arquivo CSV", type=['csv'])
    if up_file and st.button("Processar Base"):
        with st.spinner("Processando..."):
            ok, msg = etl.processar_dados(up_file)
        if ok:
            st.success(msg)
            st.cache_data.clear()
            if st.button("Recarregar"): st.rerun()
        else:
            st.error(msg)

st.sidebar.divider()

# --- 4. CARREGAMENTO ---
df = etl.carregar_dados()

if df is None:
    st.info("👋 Bem-vindo! Faça o upload dos dados para começar.")
    st.stop()

# --- 5. FILTROS ---
st.sidebar.subheader("🎯 Filtros")

# A. Data
try:
    min_date = df['order_date'].min()
    max_date = df['order_date'].max()
    
    if pd.isna(min_date) or pd.isna(max_date):
        min_d, max_d = date.today(), date.today()
    else:
        min_d, max_d = min_date.date(), max_date.date()

    periodo = st.sidebar.date_input("Período", [min_d, max_d], min_value=min_d, max_value=max_d)
except:
    st.error("Erro nos dados de data.")
    st.stop()

# B. Categoria e Tamanho
filtro_cat = st.sidebar.multiselect("Categoria", options=['Todas'] + sorted(list(df['pizza_category'].unique()))[1:], default=['Todas'], placeholder="Filtrar categorias...")
filtro_tam = st.sidebar.multiselect("Tamanho", options=['Todos'] + sorted(list(df['pizza_size'].unique()))[1:], default=['Todos'], placeholder="Filtrar tamanhos...")

# --- 6. APLICAÇÃO DOS FILTROS (CORRIGIDO) ---
if len(periodo) == 2:
    mask_data = (df['order_date'].dt.date >= periodo[0]) & (df['order_date'].dt.date <= periodo[1])
else:
    mask_data = True

# Lógica de Filtro: Se "Todas/os" estiver na lista OU a lista estiver vazia, não filtra nada.
mask_cat = True
if filtro_cat and 'Todas' not in filtro_cat:
    mask_cat = df['pizza_category'].isin(filtro_cat)

mask_tam = True
if filtro_tam and 'Todos' not in filtro_tam:
    mask_tam = df['pizza_size'].isin(filtro_tam)

df_filt = df[mask_data & mask_cat & mask_tam]

# --- 7. DASHBOARD PRINCIPAL ---

col_head1, col_head2 = st.columns([4, 1])
with col_head1:
    st.title(cfg.NOME_CLIENTE)
    if len(periodo) == 2:
        st.caption(f"📅 Dados de **{periodo[0].strftime('%d/%m/%Y')}** a **{periodo[1].strftime('%d/%m/%Y')}**")

st.divider()

if df_filt.empty:
    st.warning("⚠️ Nenhum dado encontrado com os filtros atuais.")
    st.stop()

# --- NOVAS ABAS (MONETÁRIO vs OPERAÇÃO) ---
tab_money, tab_prod = st.tabs(["💰 Setor Monetário", "📦 Produtos e Operação"])

# =========================================================
# ABA 1: SETOR MONETÁRIO
# =========================================================
with tab_money:
    # 1. CÁLCULO DOS KPIS FINANCEIROS
    faturamento = df_filt['total_item_value'].sum()
    qtd_pedidos = df_filt['order_id'].nunique()
    qtd_dias = df_filt['order_date'].nunique()
    
    ticket_medio_pedido = faturamento / qtd_pedidos if qtd_pedidos > 0 else 0
    ticket_medio_dia = faturamento / qtd_dias if qtd_dias > 0 else 0

    # 2. CARTÕES
    col_kpi1, col_kpi2, col_kpi3 = st.columns(3)
    
    col_kpi1.metric("Faturamento Total", formatar_real(faturamento))
    col_kpi2.metric("Ticket Médio (Por Pedido)", formatar_real(ticket_medio_pedido))
    col_kpi3.metric("Ticket Médio (Por Dia)", formatar_real(ticket_medio_dia))

    st.markdown("###") # Espaço

    # 3. GRÁFICOS FINANCEIROS
    c1, c2 = st.columns([2, 1])
    
    with c1:
        st.subheader("Evolução do Faturamento")
        evolucao = df_filt.groupby('order_date')['total_item_value'].sum().reset_index()
        
        fig_line = px.line(evolucao, x='order_date', y='total_item_value', markers=True)
        fig_line.update_traces(line_color=CORES['primary'], line_width=3)
        # Ajuste para Dark Mode
        fig_line.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font_color="white",
            xaxis_title=None, yaxis_title="Vendas (R$)",
            xaxis=dict(showgrid=False), yaxis=dict(showgrid=True, gridcolor='#333333'),
            hovermode="x unified"
        )
        st.plotly_chart(fig_line, use_container_width=True)

    with c2:
        st.subheader("Receita por Categoria")
        mix = df_filt.groupby('pizza_category')['total_item_value'].sum().reset_index()
        
        fig_donut = px.pie(mix, values='total_item_value', names='pizza_category', 
                           hole=0.6, color_discrete_sequence=CORES['charts'])
        fig_donut.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            font_color="white",
            showlegend=True,
            legend=dict(orientation="h", y=-0.1)
        )
        fig_donut.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig_donut, use_container_width=True)

# =========================================================
# ABA 2: PRODUTOS E OPERAÇÃO
# =========================================================
with tab_prod:
    # 1. CÁLCULO DOS KPIS OPERACIONAIS
    total_pedidos = df_filt['order_id'].nunique()
    total_pizzas = df_filt['quantity'].sum()

    # 2. CARTÕES
    col_op1, col_op2, col_vazia = st.columns([1, 1, 2]) # Usando colunas para alinhar à esquerda
    
    col_op1.metric("Pedidos Realizados", f"{total_pedidos}")
    col_op2.metric("Pizzas Vendidas", f"{total_pizzas}")

    st.markdown("###")

    # 3. GRÁFICOS OPERACIONAIS
    c_prod1, c_prod2 = st.columns(2)
    
    with c_prod1:
        st.subheader("Ranking de Pizzas (Volume)")
        top_vol = df_filt.groupby('pizza_name')['quantity'].sum().sort_values().tail(5).reset_index()
        
        fig_bar = px.bar(top_vol, x='quantity', y='pizza_name', orientation='h', text_auto=True)
        fig_bar.update_traces(marker_color=CORES['primary'])
        fig_bar.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font_color="white",
            xaxis_title="Quantidade Vendida", yaxis_title=None,
            xaxis=dict(showgrid=True, gridcolor='#333333')
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    with c_prod2:
        st.subheader("Picos de Horário")
        pico = df_filt.groupby('hour_of_day')['order_id'].nunique().reset_index()
        
        fig_hist = px.bar(pico, x='hour_of_day', y='order_id')
        fig_hist.update_traces(marker_color='#444444') # Cinza médio
        fig_hist.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font_color="white",
            xaxis_title="Hora", yaxis_title="Pedidos",
            bargap=0.2,
            yaxis=dict(gridcolor='#333333')
        )
        st.plotly_chart(fig_hist, use_container_width=True)

    st.markdown("---")
    
    # 4. NOVO GRÁFICO: VOLUME POR TAMANHO (SUBSTITUI O HEATMAP)
    st.subheader("Volume de Vendas por Tamanho")
    
    # Agrupamento por tamanho
    vol_tamanho = df_filt.groupby('pizza_size')['quantity'].sum().reset_index()
    
    # Ordem lógica de tamanho se possível (S, M, L, XL, XXL)
    # Como não temos metadados de ordem, ordenamos por volume ou alfabético. Vamos por volume decrescente.
    vol_tamanho = vol_tamanho.sort_values('quantity', ascending=False)

    fig_col = px.bar(vol_tamanho, x='pizza_size', y='quantity', text_auto=True)
    fig_col.update_traces(marker_color=CORES['primary'])
    fig_col.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font_color="white",
        xaxis_title="Tamanho da Pizza", yaxis_title="Quantidade Vendida",
        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=True, gridcolor='#333333')
    )
    
    st.plotly_chart(fig_col, use_container_width=True)