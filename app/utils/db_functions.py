import streamlit as st
import mysql.connector
from mysql.connector import Error
import pandas as pd
from utils.constants import DB_CONFIG

def formatar_numero(num):
    """Formata números com separadores"""
    return f"{num:,.0f}".replace(',', '.')

# ============= GERENCIAMENTO DE CONEXÃO =============
@st.cache_resource
def get_db_connection():
    """Cria e retorna conexão com o banco de dados"""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        if conn.is_connected():
            return conn
    except Error as e:
        st.error(f"❌ Erro na conexão: {e}")
        return None

def execute_query(query, params=None):
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

@st.cache_data(ttl=300)
def load_dashboard_data(data_inicio, data_fim, municipios, doses, vacinas):
    """Carrega dados principais da view com filtros aplicados"""
    
    query = """
    SELECT 
        ad.id_aplicacao,
        ad.data_vacina,
        ad.dose_vacina,
        ad.local_aplicacao,
        ad.via_administracao,
        ad.lote_vacina,
        ad.cnes,
        ad.id_vacina,
        ad.id_paciente,
        ad.id_estrategia_vacinacao,
        p.sexo,
        p.municipio AS paciente_municipio,
        p.uf,
        p.idade,
        p.raca_cor,
        v.nome AS vacina_nome,
        e.nome_fantasia AS estabelecimento_nome,
        e.municipio AS estabelecimento_municipio,
        e.tipo AS estabelecimento_tipo,
        e.latitude,
        e.longitude,
        ev.descricao AS estrategia_descricao
    FROM AplicacaoDose ad
    LEFT JOIN Paciente p ON ad.id_paciente = p.id_paciente
    LEFT JOIN Vacina v ON ad.id_vacina = v.id
    LEFT JOIN Estabelecimento e ON ad.cnes = e.id_cnes
    LEFT JOIN EstrategiaVacinacao ev ON ad.id_estrategia_vacinacao = ev.id
    WHERE data_vacina BETWEEN %s AND %s
    """
    
    params = [data_inicio, data_fim]
    
    if municipios:
        placeholders = ','.join(['%s'] * len(municipios))
        query += f" AND e.municipio IN ({placeholders})"
        params.extend(municipios)
    
    if doses:
        placeholders = ','.join(['%s'] * len(doses))
        query += f" AND dose_vacina IN ({placeholders})"
        params.extend(doses)
    
    if vacinas:
        placeholders = ','.join(['%s'] * len(vacinas))
        query += f" AND v.nome IN ({placeholders})"
        params.extend(vacinas)
    
    return execute_query(query, params)

@st.cache_data(ttl=300)
def carregar_municípios(ufs_selecionadas):
    """Carrega municípios baseado nas UFs selecionadas"""
    if not ufs_selecionadas:
        return []
    
    placeholders = ','.join(['%s'] * len(ufs_selecionadas))
    query = f"SELECT DISTINCT municipio FROM Estabelecimento WHERE uf IN ({placeholders}) AND municipio IS NOT NULL ORDER BY municipio"
    
    df = execute_query(query, ufs_selecionadas)
    return df['municipio'].tolist() if not df.empty else []


# Filtro de Geografia
@st.cache_data(ttl=300)
def load_municipalities():
    """Carrega todos os municípios da view"""
    query = "SELECT DISTINCT municipio FROM Estabelecimento WHERE municipio IS NOT NULL ORDER BY municipio"
    df = execute_query(query)
    return df['municipio'].tolist() if not df.empty else []




