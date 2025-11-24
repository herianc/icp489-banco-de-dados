import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import mysql.connector
from mysql.connector import Error
import os
from functools import lru_cache

# ============= CONFIGURAÇÃO DA PÁGINA =============
st.set_page_config(
    page_title="Dashboard de Vacinação",
    page_icon="💉",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============= CONFIGURAÇÕES DO BANCO DE DADOS =============
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', 'root123'),
    'database': os.getenv('DB_NAME', 'meubanco'),
    'port': int(os.getenv('DB_PORT', 3306))
}

# ============= GERENCIAMENTO DE CONEXÃO =============
@st.cache_resource
def get_db_connection():
    """Cria e retorna conexão com o banco de dados"""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        if conn.is_connected():
            st.sidebar.success("✅ Conectado ao banco de dados")
            return conn
    except Error as e:
        st.error(f"❌ Erro na conexão: {e}")
        return None

# ============= FUNÇÕES DE CONSULTA =============
def executar_consulta(query, params=None):
    """Executa consulta e retorna DataFrame"""
    conn = get_db_connection()
    if conn is None:
        return pd.DataFrame()
    
    try:
        cursor = conn.cursor()
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        
        # Obter nomes das colunas
        columns = [desc[0] for desc in cursor.description]
        data = cursor.fetchall()
        
        df = pd.DataFrame(data, columns=columns)
        cursor.close()
        return df
    except Error as e:
        st.error(f"Erro na consulta: {e}")
        st.error(f"Query: {query}")
        return pd.DataFrame()

@st.cache_data(ttl=300)  # Cache de 5 minutos
def carregar_filtros():
    """Carrega dados para os filtros a partir da view"""
    
    try:
        # Vacinas
        query_vacinas = "SELECT DISTINCT vacina_nome FROM vw_aplicacao_dose_completa WHERE vacina_nome IS NOT NULL ORDER BY vacina_nome"
        df_vacinas = executar_consulta(query_vacinas)
        vacinas = df_vacinas['vacina_nome'].tolist() if not df_vacinas.empty else []
        
        # Doses
        query_doses = "SELECT DISTINCT dose_vacina FROM vw_aplicacao_dose_completa WHERE dose_vacina IS NOT NULL ORDER BY dose_vacina"
        df_doses = executar_consulta(query_doses)
        doses = df_doses['dose_vacina'].tolist() if not df_doses.empty else []
        
        # Estratégias
        query_estrategias = "SELECT DISTINCT estrategia_descricao FROM vw_aplicacao_dose_completa WHERE estrategia_descricao IS NOT NULL ORDER BY estrategia_descricao"
        df_estrategias = executar_consulta(query_estrategias)
        estrategias = df_estrategias['estrategia_descricao'].tolist() if not df_estrategias.empty else []
        
        return vacinas, doses, estrategias
    
    except Exception as e:
        st.error(f"❌ Erro ao carregar filtros: {e}")
        return [], [], []

@st.cache_data(ttl=300)
def carregar_municípios(ufs_selecionadas):
    """Carrega municípios baseado nas UFs selecionadas"""
    if not ufs_selecionadas:
        return []
    
    placeholders = ','.join(['%s'] * len(ufs_selecionadas))
    query = f"SELECT DISTINCT municipio FROM Paciente WHERE uf IN ({placeholders}) AND municipio IS NOT NULL ORDER BY municipio"
    
    df = executar_consulta(query, ufs_selecionadas)
    return df['municipio'].tolist() if not df.empty else []

@st.cache_data(ttl=300)
def carregar_dados_dashboard(data_inicio, data_fim, municipios, doses, vacinas):
    """Carrega dados principais da view com filtros aplicados"""
    
    query = """
    SELECT 
        id_aplicacao,
        data_vacina,
        dose_vacina,
        cnes,
        id_vacina,
        id_paciente,
        id_estrategia_vacinacao,
        sexo,
        paciente_municipio,
        uf,
        idade,
        raca_cor,
        vacina_nome,
        estabelecimento_nome,
        estabelecimento_municipio,
        latitude,
        longitude,
        estrategia_descricao,
        fabricante_nome
    FROM vw_aplicacao_dose_completa
    WHERE data_vacina BETWEEN %s AND %s
    """
    
    params = [data_inicio, data_fim]
    
    if municipios:
        placeholders = ','.join(['%s'] * len(municipios))
        query += f" AND paciente_municipio IN ({placeholders})"
        params.extend(municipios)
    
    if doses:
        placeholders = ','.join(['%s'] * len(doses))
        query += f" AND dose_vacina IN ({placeholders})"
        params.extend(doses)
    
    if vacinas:
        placeholders = ','.join(['%s'] * len(vacinas))
        query += f" AND vacina_nome IN ({placeholders})"
        params.extend(vacinas)
    
    return executar_consulta(query, params)

def formatar_numero(num):
    """Formata números com separadores"""
    return f"{num:,.0f}".replace(',', '.')

# ============= SIDEBAR - FILTROS =============
st.sidebar.header("🔍 Filtros")

# Carregar opções de filtros
with st.spinner("Carregando opções de filtros..."):
    vacinas_lista, doses_lista, estrategias_lista = carregar_filtros()

# Filtro de Período
col_data = st.sidebar.columns(2)
with col_data[0]:
    data_inicio_filtro = st.date_input(
        "Data Início",
        value=datetime(2024, 1, 1),
        key="data_inicio"
    )
with col_data[1]:
    data_fim_filtro = st.date_input(
        "Data Fim",
        value=datetime(2024, 1, 31),
        key="data_fim"
    )

# Filtro de Geografia
@st.cache_data(ttl=300)
def carregar_todos_municipios():
    """Carrega todos os municípios da view"""
    query = "SELECT DISTINCT paciente_municipio FROM vw_aplicacao_dose_completa WHERE paciente_municipio IS NOT NULL ORDER BY paciente_municipio"
    df = executar_consulta(query)
    return df['paciente_municipio'].tolist() if not df.empty else []

municipios_filtrados = carregar_todos_municipios()
municipios_selecionados = st.sidebar.multiselect(
    "Município",
    options=municipios_filtrados,
    default=[]
)

# Filtro de Dose
doses_selecionadas = st.sidebar.multiselect(
    "Tipo de Dose",
    options=doses_lista,
    default=[]
)

# Filtro de Vacina
vacinas_selecionadas = st.sidebar.multiselect(
    "Vacina",
    options=vacinas_lista,
    default=[]
)

# ============= CARREGAMENTO DE DADOS =============
st.title("💉 Dashboard de Vacinação")
st.markdown("---")

# Verificar se o botão foi pressionado
if not aplicar_filtros:
    st.info("👈 Configure os filtros e clique em 'Aplicar Filtros' para visualizar os dados")
else:
    with st.spinner("Carregando dados do banco..."):
        df = carregar_dados_dashboard(
            data_inicio_filtro,
            data_fim_filtro,
            municipios_selecionados,
            doses_selecionadas,
            vacinas_selecionadas
        )

    if df.empty:
        st.warning("❌ Nenhum dado encontrado com os filtros selecionados.")
        st.stop()

    # ============= KPIs PRINCIPAIS =============
    st.subheader("📊 Indicadores Principais")

    kpi_cols = st.columns(4)

    with kpi_cols[0]:
        total_doses = len(df)
        st.metric(
            "Total de Doses Aplicadas",
            formatar_numero(total_doses)
        )

    with kpi_cols[1]:
        pacientes_unicos = df['id_paciente'].nunique()
        st.metric(
            "Pacientes Vacinados",
            formatar_numero(pacientes_unicos)
        )

    with kpi_cols[2]:
        media_idade = df['idade'].mean() if df['idade'].notna().any() else 0
        st.metric(
            "Idade Média",
            f"{media_idade:.1f} anos" if media_idade > 0 else "N/A"
        )

    with kpi_cols[3]:
        dose_reforco = len(df[df['dose_vacina'].str.contains('Reforço', na=False)])
        st.metric(
            "Doses de Reforço",
            formatar_numero(dose_reforco)
        )

    st.markdown("---")

# ============= GRÁFICOS PRINCIPAIS =============
col1, col2 = st.columns(2)

# Gráfico 1: Evolução Temporal
with col1:
    st.subheader("📈 Acompanhamento Temporal da Vacinação")
    
    dados_tempo = df.groupby([df['data_vacina'], 'dose_vacina']).size().reset_index(name='count')
    dados_tempo = dados_tempo.dropna(subset=['data_vacina'])
    
    fig_tempo = px.line(
        dados_tempo,
        x='data_vacina',
        y='count',
        color='dose_vacina',
        markers=True,
        labels={'data_vacina': 'Data', 'count': 'Doses Aplicadas', 'dose_vacina': 'Tipo de Dose'}
    )
    fig_tempo.update_layout(hovermode='x unified', height=400)
    st.plotly_chart(fig_tempo, use_container_width=True)

# Gráfico 2: Doses por Vacina
with col2:
    st.subheader("💊 Doses Aplicadas por Vacina")
    
    dados_vacina = df['vacina_nome'].value_counts().head(10).reset_index()
    dados_vacina.columns = ['vacina_nome', 'count']
    
    fig_vacina = px.bar(
        dados_vacina,
        x='count',
        y='vacina_nome',
        orientation='h',
        labels={'count': 'Total de Doses', 'vacina_nome': 'Vacina'},
        color='count',
        color_continuous_scale='Blues'
    )
    fig_vacina.update_layout(height=400, showlegend=False)
    st.plotly_chart(fig_vacina, use_container_width=True)

# ============= LINHA DE GRÁFICOS 2 =============
col3, col4 = st.columns(2)

# Gráfico 3: Distribuição por Estratégia
with col3:
    st.subheader("🎯 Distribuição por Estratégia de Vacinação")
    
    dados_estrategia = df['estrategia_descricao'].value_counts().reset_index()
    dados_estrategia.columns = ['estrategia', 'count']
    dados_estrategia = dados_estrategia[dados_estrategia['estrategia'].notna()]
    
    if not dados_estrategia.empty:
        fig_estrategia = px.pie(
            dados_estrategia,
            values='count',
            names='estrategia',
            hole=0.3
        )
        fig_estrategia.update_layout(height=400)
        st.plotly_chart(fig_estrategia, use_container_width=True)
    else:
        st.info("Sem dados de estratégia")

# Gráfico 4: Distribuição por Raça/Cor
with col4:
    st.subheader("👥 Distribuição por Raça/Cor")
    
    dados_raca = df['raca_cor'].value_counts().reset_index()
    dados_raca.columns = ['raca_cor', 'count']
    dados_raca = dados_raca[dados_raca['raca_cor'].notna()]
    
    if not dados_raca.empty:
        fig_raca = px.bar(
            dados_raca,
            x='raca_cor',
            y='count',
            labels={'count': 'Total de Doses', 'raca_cor': 'Raça/Cor'},
            color='count',
            color_continuous_scale='Viridis'
        )
        fig_raca.update_layout(height=400, showlegend=False)
        st.plotly_chart(fig_raca, use_container_width=True)
    else:
        st.info("Sem dados de raça/cor")

# ============= LINHA DE GRÁFICOS 3 =============
col5, col6 = st.columns(2)

# Gráfico 5: Pirâmide Etária
with col5:
    st.subheader("📊 Pirâmide Etária")
    
    df_idade = df[df['idade'].notna()].copy()
    
    if not df_idade.empty:
        df_idade['grupo_idade'] = pd.cut(df_idade['idade'], 
                                         bins=[0, 10, 20, 30, 40, 50, 60, 70, 80, 100],
                                         labels=['0-10', '10-20', '20-30', '30-40', '40-50', '50-60', '60-70', '70-80', '80+'])
        
        piramide = df_idade.groupby(['grupo_idade', 'sexo']).size().unstack(fill_value=0)
        
        if 'M' in piramide.columns:
            piramide['M'] = -piramide['M']
        
        fig_piramide = go.Figure()
        
        for col in piramide.columns:
            color = 'steelblue' if col == 'M' else 'lightcoral'
            fig_piramide.add_trace(go.Bar(
                y=piramide.index,
                x=piramide[col],
                name=col,
                orientation='h',
                marker_color=color
            ))
        
        fig_piramide.update_layout(barmode='relative', height=400, xaxis_title='Quantidade')
        st.plotly_chart(fig_piramide, use_container_width=True)
    else:
        st.info("Sem dados de idade")

# Gráfico 6: Ranking de Estabelecimentos
with col6:
    st.subheader("🏥 Ranking de Estabelecimentos")
    
    top_estab = df['estabelecimento_nome'].value_counts().head(10).reset_index()
    top_estab.columns = ['estabelecimento', 'count']
    top_estab = top_estab[top_estab['estabelecimento'].notna()]
    
    if not top_estab.empty:
        fig_estab = px.bar(
            top_estab,
            x='count',
            y='estabelecimento',
            orientation='h',
            labels={'count': 'Total de Doses', 'estabelecimento': 'Estabelecimento'},
            color='count',
            color_continuous_scale='Greens'
        )
        fig_estab.update_layout(height=400, showlegend=False)
        st.plotly_chart(fig_estab, use_container_width=True)
    else:
        st.info("Sem dados de estabelecimento")

# ============= TABELAS DETALHADAS =============
st.markdown("---")
st.subheader("📋 Tabelas de Detalhamento")

tab1, tab2, tab3, tab4 = st.tabs(["Vacinação por Fabricante", "Últimas Aplicações", "Resumo por Município", "Doses por Tipo"])

with tab1:
    st.write("**Distribuição por Fabricante**")
    tabela_fabricante = df.groupby('fabricante_nome').size().reset_index(name='Total de Doses')
    tabela_fabricante = tabela_fabricante[tabela_fabricante['fabricante_nome'].notna()]
    tabela_fabricante = tabela_fabricante.sort_values('Total de Doses', ascending=False)
    st.dataframe(tabela_fabricante, use_container_width=True, hide_index=True)

with tab2:
    st.write("**Últimas 50 Aplicações de Vacina**")
    ultimas = df.sort_values('data_vacina', ascending=False).head(50)[[
        'data_vacina', 'vacina_nome', 'dose_vacina', 'idade', 'sexo', 'paciente_municipio', 'estabelecimento_nome'
    ]].copy()
    ultimas['data_vacina'] = pd.to_datetime(ultimas['data_vacina']).dt.strftime('%d/%m/%Y')
    st.dataframe(ultimas, use_container_width=True, hide_index=True)

with tab3:
    st.write("**Resumo de Vacinação por Município**")
    resumo_municipio = df.groupby('paciente_municipio').agg({
        'id_paciente': 'nunique',
        'id_aplicacao': 'count'
    }).reset_index()
    resumo_municipio.columns = ['Município', 'Pacientes Únicos', 'Total de Doses']
    resumo_municipio = resumo_municipio[resumo_municipio['Município'].notna()]
    resumo_municipio = resumo_municipio.sort_values('Total de Doses', ascending=False)
    st.dataframe(resumo_municipio, use_container_width=True, hide_index=True)

with tab4:
    st.write("**Distribuição de Doses por Tipo**")
    resumo_doses = df.groupby('dose_vacina').agg({
        'id_paciente': 'nunique',
        'id_aplicacao': 'count'
    }).reset_index()
    resumo_doses.columns = ['Tipo de Dose', 'Pacientes', 'Total de Doses']
    resumo_doses = resumo_doses[resumo_doses['Tipo de Dose'].notna()]
    resumo_doses = resumo_doses.sort_values('Total de Doses', ascending=False)
    st.dataframe(resumo_doses, use_container_width=True, hide_index=True)

# ============= RODAPÉ =============
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: gray; font-size: 12px;'>
Dashboard de Vacinação | Dados de 2024 | Atualização: Em Tempo Real
</div>
""", unsafe_allow_html=True)