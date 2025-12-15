import streamlit as st
import pandas as pd
import plotly.express as px
import config as cfg
import etl

# --- CORES ---
CORES = {
    'primary': '#003366', 'secondary': '#E5E5E5', 
    'background': '#0E1117', 'card_bg': '#1A1C24', 'accent': '#FFD700',
    'locado': '#FF4B4B', 'disponivel': '#00CC96'
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
    [data-testid="stMetricValue"] {{ color: {CORES['accent']}; font-size: 24px; }}
    [data-testid="stMetricLabel"] {{ color: #A0A0A0; font-size: 14px; }}
    section[data-testid="stSidebar"] {{ background-color: #111111; }}
    h1, h2, h3 {{ color: {CORES['secondary']} !important; }}
</style>
""", unsafe_allow_html=True)

# --- UPLOAD ---
st.sidebar.title("🏢 Gestão de Imóveis")
with st.sidebar.expander("Atualizar Inventário", expanded=False):
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

# --- CARGA ---
df = etl.carregar_dados()
if df is None:
    st.info("Aguardando base de imóveis.")
    st.stop()

# --- FILTROS (Mantendo a lógica hierárquica) ---
st.sidebar.subheader("🎯 Filtros")

df_principal = df.copy()

# 1. CATEGORIA (Quartil)
if 'Categoria_Preco' in df_principal.columns:
    opcoes_cat = sorted(list(df_principal['Categoria_Preco'].unique()))
    sel_cat = st.sidebar.multiselect("Segmento (Quartil)", options=opcoes_cat, default=opcoes_cat)
    df_l1 = df_principal[df_principal['Categoria_Preco'].isin(sel_cat)] if sel_cat else df_principal
else:
    df_l1 = df_principal.copy()

# 2. STATUS
if 'Estado' in df_l1.columns:
    estados = ['Todos'] + sorted(list(df_l1['Estado'].unique()))
    sel_estado = st.sidebar.selectbox("Status do Imóvel", options=estados)
    df_l2 = df_l1[df_l1['Estado'] == sel_estado] if sel_estado != 'Todos' else df_l1
else:
    df_l2 = df_l1

# 3. TIPO
if 'Tipo Imóvel' in df_l2.columns:
    tipos = sorted(list(df_l2['Tipo Imóvel'].unique()))
    sel_tipo = st.sidebar.multiselect("Tipo de Imóvel", options=tipos, placeholder="Todos os tipos")
    df_l3 = df_l2[df_l2['Tipo Imóvel'].isin(sel_tipo)] if sel_tipo else df_l2
else:
    df_l3 = df_l2

# 4. BAIRRO
if 'Bairro' in df_l3.columns:
    bairros = sorted(list(df_l3['Bairro'].unique()))
    sel_bairro = st.sidebar.multiselect("Bairro", options=bairros, placeholder="Todos os bairros")
    df_l4 = df_l3[df_l3['Bairro'].isin(sel_bairro)] if sel_bairro else df_l3
else:
    df_l4 = df_l3

# 5. DINÂMICOS
if not df_l4.empty:
    min_p = float(df_l4['Valor do Aluguel'].min())
    max_p = float(df_l4['Valor do Aluguel'].max())
    if min_p == max_p: max_p += 1 
    f_preco = st.sidebar.slider("Faixa de Aluguel (R$)", min_p, max_p, (min_p, max_p))
    
    max_q = int(df_l4['Quartos'].max()) if df_l4['Quartos'].max() > 0 else 5
    f_quartos = st.sidebar.slider("Mínimo de Quartos", 0, max_q, 1)
else:
    st.stop()

# Aplicação Final
mask = (df_l4['Valor do Aluguel'] >= f_preco[0]) & \
       (df_l4['Valor do Aluguel'] <= f_preco[1]) & \
       (df_l4['Quartos'] >= f_quartos)

df_filt = df_l4[mask]

# --- DASHBOARD ---
st.title(cfg.NOME_CLIENTE)
st.caption(f"{len(df_filt)} imóveis encontrados no filtro atual")
st.divider()

if df_filt.empty:
    st.warning("Nenhum imóvel encontrado.")
    st.stop()

# --- DEFINIÇÃO DAS ABAS ---
tab1, tab2 = st.tabs(["💲 Painel Financeiro", "🏠 Painel Imóveis"])

# ==============================================================================
# ABA 1: PAINEL FINANCEIRO
# ==============================================================================
with tab1:
    # 1. CÁLCULO KPIS
    aluguel_medio = df_filt['Valor do Aluguel'].mean()
    custo_medio = df_filt['Custo_Mensal'].mean()
    preco_m2 = df_filt['Preco_m2'].mean()
    
    # Participação (10% do aluguel)
    # Precisamos filtrar por estado no DF original filtrado para pegar os totais corretos
    soma_disp = df_filt[df_filt['Estado'] == 'Disponível']['Valor do Aluguel'].sum()
    soma_loc = df_filt[df_filt['Estado'] == 'Locado']['Valor do Aluguel'].sum()
    
    part_disp = soma_disp * 0.10
    part_loc = soma_loc * 0.10

    # 2. EXIBIÇÃO KPIS
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Aluguel Médio", formatar_real(aluguel_medio))
    c2.metric("Custo Médio Total", formatar_real(custo_medio))
    c3.metric("Preço Médio m²", formatar_real(preco_m2))
    c4.metric("Part. Disponível (10%)", formatar_real(part_disp))
    c5.metric("Part. Locados (10%)", formatar_real(part_loc))
    
    st.markdown("---")

    # 3. GRÁFICOS FINANCEIROS
    g1, g2 = st.columns(2)
    
    with g1:
        st.subheader("Status da Ocupação")
        if 'Estado' in df_filt.columns:
            status_counts = df_filt['Estado'].value_counts().reset_index()
            status_counts.columns = ['Estado', 'Qtd']
            fig_rosca = px.pie(status_counts, values='Qtd', names='Estado', hole=0.5,
                               color='Estado',
                               color_discrete_map={'Locado': CORES['locado'], 'Disponível': CORES['disponivel']})
            fig_rosca.update_layout(paper_bgcolor="rgba(0,0,0,0)", font_color="white")
            st.plotly_chart(fig_rosca, use_container_width=True)

    with g2:
        st.subheader("Volume Financeiro por Status")
        # Gráfico Colunas: X=Estado, Y=Valor Aluguel (Soma)
        vol_estado = df_filt.groupby('Estado')['Valor do Aluguel'].sum().reset_index()
        fig_col = px.bar(vol_estado, x='Estado', y='Valor do Aluguel', text_auto=True,
                         color='Estado',
                         color_discrete_map={'Locado': CORES['locado'], 'Disponível': CORES['disponivel']})
        fig_col.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="white")
        fig_col.update_traces(texttemplate='R$ %{y:,.2s}')
        st.plotly_chart(fig_col, use_container_width=True)

    st.subheader("Top Bairros (Valor Médio do Aluguel)")
    # Gráfico Barras Empilhadas/Agrupadas: X=Valor Médio, Y=Bairro, Cor=Estado
    # Agrupamos por Bairro e Estado para ter a média
    if 'Bairro' in df_filt.columns:
        bairro_avg = df_filt.groupby(['Bairro', 'Estado'])['Valor do Aluguel'].mean().reset_index()
        
        # Filtra Top 10 bairros gerais para não poluir (ALTERADO AQUI)
        top_bairros = df_filt.groupby('Bairro')['Valor do Aluguel'].mean().sort_values(ascending=False).head(10).index
        bairro_avg = bairro_avg[bairro_avg['Bairro'].isin(top_bairros)]
        
        fig_bar = px.bar(bairro_avg, y='Bairro', x='Valor do Aluguel', color='Estado',
                         orientation='h', barmode='group', # Group facilita comparação de médias
                         color_discrete_map={'Locado': CORES['locado'], 'Disponível': CORES['disponivel']},
                         text_auto=True)
        
        fig_bar.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="white",
            xaxis_title="Valor Médio do Aluguel", yaxis={'categoryorder':'total ascending'},
            height=600
        )
        fig_bar.update_traces(texttemplate='R$ %{x:,.0f}')
        st.plotly_chart(fig_bar, use_container_width=True)


# ==============================================================================
# ABA 2: PAINEL IMÓVEIS
# ==============================================================================
with tab2:
    # 1. CÁLCULO KPIS
    # Contagens específicas
    casas_loc = len(df_filt[(df_filt['Tipo Imóvel'] == 'Casa') & (df_filt['Estado'] == 'Locado')])
    aptos_loc = len(df_filt[(df_filt['Tipo Imóvel'] == 'Apartamento') & (df_filt['Estado'] == 'Locado')])
    
    casas_disp = len(df_filt[(df_filt['Tipo Imóvel'] == 'Casa') & (df_filt['Estado'] == 'Disponível')])
    aptos_disp = len(df_filt[(df_filt['Tipo Imóvel'] == 'Apartamento') & (df_filt['Estado'] == 'Disponível')])

    # 2. EXIBIÇÃO KPIS
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Casas Alugadas", f"{casas_loc}")
    k2.metric("Apartamentos Alugados", f"{aptos_loc}")
    k3.metric("Casas Disponíveis", f"{casas_disp}")
    k4.metric("Apartamentos Disponíveis", f"{aptos_disp}")
    
    st.markdown("---")
    
    # 3. GRÁFICOS OPERACIONAIS
    r1, r2 = st.columns(2)
    
    with r1:
        st.subheader("Proporção Casas vs Apartamentos")
        tipo_counts = df_filt['Tipo Imóvel'].value_counts().reset_index()
        tipo_counts.columns = ['Tipo', 'Qtd']
        fig_tipo = px.pie(tipo_counts, values='Qtd', names='Tipo', hole=0.5,
                          color_discrete_sequence=px.colors.sequential.RdBu)
        fig_tipo.update_layout(paper_bgcolor="rgba(0,0,0,0)", font_color="white")
        st.plotly_chart(fig_tipo, use_container_width=True)
        
    with r2:
        st.subheader("Área Média por Status")
        area_stats = df_filt.groupby('Estado')['Area'].mean().reset_index()
        fig_area = px.bar(area_stats, x='Estado', y='Area', text_auto=True,
                          color='Estado',
                          color_discrete_map={'Locado': CORES['locado'], 'Disponível': CORES['disponivel']})
        fig_area.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="white",
                               yaxis_title="Área Média (m²)")
        fig_area.update_traces(texttemplate='%{y:.0f} m²')
        st.plotly_chart(fig_area, use_container_width=True)

    c_g1, c_g2 = st.columns(2)
    
    with c_g1:
        st.subheader("Contagem de Imóveis")
        # Contagem simples Locado vs Disponível
        fig_count = px.histogram(df_filt, x='Estado', color='Estado',
                                 color_discrete_map={'Locado': CORES['locado'], 'Disponível': CORES['disponivel']},
                                 text_auto=True)
        fig_count.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="white",
                                yaxis_title="Quantidade")
        st.plotly_chart(fig_count, use_container_width=True)
        
    with c_g2:
        st.subheader("Distribuição por Bairro (Top 10)")
        # Empilhadas: X=Bairro, Y=Contagem, Cor=Estado
        if 'Bairro' in df_filt.columns:
            top_bairros_qtd = df_filt['Bairro'].value_counts().head(10).index
            df_bairro_top = df_filt[df_filt['Bairro'].isin(top_bairros_qtd)]
            
            fig_stack = px.histogram(df_bairro_top, y='Bairro', color='Estado',
                                     orientation='h', barmode='stack',
                                     color_discrete_map={'Locado': CORES['locado'], 'Disponível': CORES['disponivel']},
                                     text_auto=True)
            
            fig_stack.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="white",
                                    yaxis={'categoryorder':'total ascending'}, xaxis_title="Quantidade")
            st.plotly_chart(fig_stack, use_container_width=True)