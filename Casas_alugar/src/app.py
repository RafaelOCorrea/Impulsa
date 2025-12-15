import streamlit as st
import pandas as pd
import plotly.express as px
import config as cfg
import etl

# --- CORES ---
CORES = {
    'primary': '#003366', 'secondary': '#E5E5E5', 
    'background': '#0E1117', 'card_bg': '#1A1C24', 'accent': '#FFD700'
}

def formatar_real(valor):
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

st.set_page_config(layout="wide", page_title=cfg.NOME_CLIENTE, page_icon="🏢")

# --- CSS ---
st.markdown(f"""
<style>
    html, body {{ font-family: sans-serif; color: {CORES['secondary']}; }}
    .stApp {{ background-color: {CORES['background']}; }}
    div[data-testid="stMetric"] {{
        background-color: {CORES['card_bg']};
        border-left: 5px solid {CORES['primary']};
        border-radius: 8px;
        padding: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }}
    [data-testid="stMetricValue"] {{ color: {CORES['accent']}; font-size: 26px; }}
    [data-testid="stMetricLabel"] {{ color: #A0A0A0; }}
    section[data-testid="stSidebar"] {{ background-color: #111111; }}
    h1, h2, h3 {{ color: {CORES['secondary']} !important; }}
</style>
""", unsafe_allow_html=True)

# --- UPLOAD ---
st.sidebar.title("🏢 Gestão de Imóveis")
with st.sidebar.expander("Atualizar Inventário", expanded=False):
    up_file = st.file_uploader("Arquivo CSV", type=['csv'])
    if up_file and st.button("Processar Base"):
        with st.spinner("Processando novos dados (Bairros e Tipos)..."):
            ok, msg = etl.processar_dados(up_file)
        if ok:
            st.success(msg)
            st.cache_data.clear()
            if st.button("Recarregar"): st.rerun()
        else:
            st.error(msg)
st.sidebar.divider()

# --- CARGA ---
df = etl.carregar_dados()
if df is None:
    st.info("Aguardando base de imóveis.")
    st.stop()

# --- FILTROS HIERÁRQUICOS ---
st.sidebar.subheader("🎯 Filtros")

# 1. CATEGORIA (Quartil) - O Pai
if 'Categoria_Preco' in df.columns:
    opcoes_cat = sorted(list(df['Categoria_Preco'].unique()))
    sel_cat = st.sidebar.multiselect("Segmento (Quartil)", options=opcoes_cat, default=opcoes_cat)
    
    if not sel_cat:
        df_l1 = df.copy()
    else:
        df_l1 = df[df['Categoria_Preco'].isin(sel_cat)]
else:
    df_l1 = df.copy()

# 2. TIPO DE IMÓVEL (Novo)
if 'Tipo Imóvel' in df_l1.columns:
    tipos = ['Todos'] + sorted(list(df_l1['Tipo Imóvel'].unique()))
    sel_tipo = st.sidebar.selectbox("Tipo de Imóvel", tipos)
    if sel_tipo != 'Todos':
        df_l2 = df_l1[df_l1['Tipo Imóvel'] == sel_tipo]
    else:
        df_l2 = df_l1
else:
    df_l2 = df_l1

# 3. BAIRRO (Novo)
if 'Bairro' in df_l2.columns:
    bairros = sorted(list(df_l2['Bairro'].unique()))
    sel_bairro = st.sidebar.multiselect("Bairro", options=bairros, placeholder="Todos os bairros")
    if sel_bairro:
        df_l3 = df_l2[df_l2['Bairro'].isin(sel_bairro)]
    else:
        df_l3 = df_l2
else:
    df_l3 = df_l2

# 4. FILTROS DINÂMICOS DE VALORES
if not df_l3.empty:
    min_p = float(df_l3['Valor do Aluguel'].min())
    max_p = float(df_l3['Valor do Aluguel'].max())
    # Proteção caso min e max sejam iguais
    if min_p == max_p:
        min_p = 0.0
        max_p = max_p + 1.0
        
    f_preco = st.sidebar.slider("Faixa de Aluguel (R$)", min_p, max_p, (min_p, max_p))
    
    max_q = int(df_l3['Quartos'].max()) if df_l3['Quartos'].max() > 0 else 5
    f_quartos = st.sidebar.slider("Mínimo de Quartos", 0, max_q, 1)
else:
    st.warning("Sem dados para os filtros selecionados.")
    st.stop()

# Aplicação Final
mask = (df_l3['Valor do Aluguel'] >= f_preco[0]) & \
       (df_l3['Valor do Aluguel'] <= f_preco[1]) & \
       (df_l3['Quartos'] >= f_quartos)

df_filt = df_l3[mask]

# --- DASHBOARD ---
st.title(cfg.NOME_CLIENTE)
st.caption(f"{len(df_filt)} imóveis encontrados")
st.divider()

if df_filt.empty:
    st.warning("Nenhum imóvel encontrado.")
    st.stop()

tab1, tab2 = st.tabs(["📊 Inteligência de Mercado", "🔍 Lista Detalhada"])

with tab1:
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Aluguel Médio", formatar_real(df_filt['Valor do Aluguel'].mean()))
    k2.metric("Área Média", f"{int(df_filt['Area'].mean())} m²")
    k3.metric("Custo Médio Total", formatar_real(df_filt['Custo_Mensal'].mean()))
    k4.metric("Preço Médio m²", formatar_real(df_filt['Preco_m2'].mean()))

    st.markdown("###")
    
    # LINHA 1: TIPO E DISTRIBUIÇÃO
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Imóveis por Tipo")
        if 'Tipo Imóvel' in df_filt.columns:
            # Gráfico de Rosca
            tipo_counts = df_filt['Tipo Imóvel'].value_counts().reset_index()
            tipo_counts.columns = ['Tipo', 'Qtd']
            fig_pie = px.pie(tipo_counts, values='Qtd', names='Tipo', hole=0.5, 
                             color_discrete_sequence=px.colors.sequential.RdBu)
            fig_pie.update_layout(paper_bgcolor="rgba(0,0,0,0)", font_color="white")
            st.plotly_chart(fig_pie, use_container_width=True)
            
    with c2:
        st.subheader("Distribuição de Preços")
        color_col = 'Categoria_Preco' if 'Categoria_Preco' in df_filt.columns else None
        fig_hist = px.histogram(df_filt, x="Valor do Aluguel", nbins=30, 
                           color=color_col,
                           color_discrete_sequence=px.colors.sequential.Viridis)
        fig_hist.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="white", yaxis_title="Qtd")
        st.plotly_chart(fig_hist, use_container_width=True)

    # LINHA 2: ANÁLISE DE BAIRROS
    st.markdown("---")
    st.subheader("Top Bairros (Valor Médio do Aluguel)")
    
    if 'Bairro' in df_filt.columns:
        # Agrupa por bairro e calcula a média
        bairro_stats = df_filt.groupby('Bairro')['Valor do Aluguel'].mean().reset_index()
        # Pega os Top 10 mais caros (ou baratos, dependendo da ordenação)
        bairro_stats = bairro_stats.sort_values('Valor do Aluguel', ascending=False).head(10)
        
        fig_bar = px.bar(bairro_stats, x='Valor do Aluguel', y='Bairro', orientation='h', text_auto=True)
        fig_bar.update_traces(marker_color=CORES['accent'], texttemplate='R$ %{x:,.0f}')
        fig_bar.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", 
            font_color="white", yaxis={'categoryorder':'total ascending'}
        )
        st.plotly_chart(fig_bar, use_container_width=True)

with tab2:
    cols_show = ['Bairro', 'Tipo Imóvel', 'Categoria_Preco', 'Area', 'Quartos', 'Valor do Aluguel', 'Custo_Mensal']
    # Garante que as colunas existem antes de mostrar
    cols_final = [c for c in cols_show if c in df_filt.columns]
    
    st.dataframe(
        df_filt[cols_final],
        use_container_width=True,
        height=600
    )