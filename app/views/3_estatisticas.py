import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import mysql.connector
from mysql.connector import Error
from datetime import datetime
from utils.db_functions import *

st.logo('https://ic.ufrj.br/svg/logo-ic.svg')

# Configurações da página
st.set_page_config(
    page_title="Dashboard Vacinação",
    page_icon="💉",
    layout="wide",
    initial_sidebar_state="expanded"
)

with st.sidebar:
    on = st.toggle('Mostrar consultas', value=True)

# Título
st.title("📊 Estatísticas de Vacinação do Rio de Janeiro em 2024")
st.divider()


st.subheader("Indicadores Principais")
kpi_cols = st.columns(4)

with kpi_cols[0]:
    total_doses = execute_query('SELECT COUNT(*) as total_doses FROM AplicacaoDose')['total_doses'][0]
    st.metric(
        "Total de Doses Aplicadas",
        formatar_numero(total_doses)
    )

with kpi_cols[1]:
    unique_patients = execute_query('SELECT COUNT(DISTINCT id_paciente) as unique_patients FROM AplicacaoDose')['unique_patients'][0]
    st.metric(
        "Pacientes Vacinados",
        formatar_numero(unique_patients)
    )

with kpi_cols[2]:
    average_age = execute_query('SELECT AVG(idade) as average_age FROM Paciente')['average_age'][0]
    st.metric(
        "Idade Média",
        f"{average_age:.1f} anos" if average_age > 0 else "N/A"
    )

with kpi_cols[3]:
    unique_doses = execute_query('SELECT COUNT(id_aplicacao) as unique_doses FROM AplicacaoDose WHERE dose_vacina LIKE "%Única%"')['unique_doses'][0]
    st.metric(
        "Doses únicas",
        formatar_numero(unique_doses)
    )
st.divider()
st.subheader("Vacinas com mais aplicações")

query1 = """
    SELECT
        V.nome AS Nome_Vacina,
        COUNT(A.id_aplicacao) AS Vezes_Utilizada
    FROM
        vacinacao.Vacina V
    LEFT JOIN
        vacinacao.AplicacaoDose A ON V.id = A.id_vacina
    GROUP BY
        V.nome
    ORDER BY
        Vezes_Utilizada DESC
    LIMIT 10;
"""

df1 = execute_query(query1)
col1, col2 = st.columns([1,1])
with col1:
    st.markdown("""
                No topo do ranking, temos a **Penta (DTP/HepB/Hib)**, que atua como um verdadeiro "canivete suíço" da saúde pública. 
                O fato de ser a mais aplicada não é surpresa: ela é uma vacina combinada que, em uma única dose, **protege bebês contra 
                cinco doenças graves (difteria, tétano, coqueluche, hepatite B e infecções por Haemophilus influenzae b)**. Logo em seguida, 
                a **Hepatite B** e a **Meningo C** reforçam essa blindagem na primeira infância.
                
                Outro destaque interessante é a presença dupla da proteção contra a paralisia infantil. Vemos tanto a **Pólio Oral** (a famosa gotinha) 
                quanto a **Pólio Injetável** no top 5. Isso reflete o esquema vacinal atual, que mistura a eficácia da versão injetável nas primeiras 
                doses com a facilidade do reforço oral, mantendo o país protegido contra a reintrodução do vírus.            
                """)
    if on:
        st.code(query1, language='sql')

with col2:
    if df1 is not None:
        fig, ax = plt.subplots(figsize=(15, 6))
        ax.bar(range(len(df1)), df1['Vezes_Utilizada'], color='steelblue')
        ax.set_xticks(range(len(df1)))
        ax.set_xticklabels(df1['Nome_Vacina'], rotation=45, ha='right')
        ax.set_ylabel('Aplicações')
        plt.tight_layout()
        st.pyplot(fig, width='stretch')

st.divider()
st.subheader("Estabelecimentos com Aplicações Acima da Média")
col1, col2 = st.columns(2)

query3 = """
    SELECT
        E.nome_fantasia,
        COUNT(A.id_aplicacao) AS Total_Aplicacoes
    FROM
        vacinacao.Estabelecimento E
    JOIN
        vacinacao.AplicacaoDose A ON E.id_cnes = A.cnes
    GROUP BY
        E.nome_fantasia
    HAVING
        COUNT(A.id_aplicacao) > (
            SELECT COUNT(*) / COUNT(DISTINCT cnes)
            FROM vacinacao.AplicacaoDose ad
        )
    ORDER BY
        Total_Aplicacoes DESC
    LIMIT 10;
"""
df_q3 = execute_query(query3)


query7 = """
        SELECT 
            e.id_cnes,
            e.latitude,
            e.longitude,
            COUNT(A.id_aplicacao) AS total
        FROM vacinacao.AplicacaoDose A
        INNER JOIN vacinacao.Estabelecimento e ON A.cnes = e.id_cnes
        GROUP BY e.id_cnes, e.latitude, e.longitude
        """
df_q7 = execute_query(query7)

with col2:
    st.map(df_q7.dropna(), zoom=7, width=1000, height=400, size='total', color="#0084ffdd")
    if on:
        st.code(query7, language='sql')
    
    
with col1:
    st.table(df_q3.rename(columns={'nome_fantasia': 'Estabelecimento', 'Total_Aplicacoes': 'Total de Aplicações'})) 

    if on:
        st.markdown('#### Consulta utilizada')
        st.code(query3, language='sql')

st.divider()
st.markdown('## Vacinação em Idosos')

col1, col2 = st.columns(2)
with col1:
    st.markdown("### Municípios - Aplicações em Idosos (>60 anos)")

    query4 = """
        SELECT
            E.municipio AS Municipio,
            COUNT(A.id_aplicacao) AS Total_Idosos_Vacinados
        FROM vacinacao.AplicacaoDose A
        INNER JOIN
            vacinacao.Estabelecimento E ON A.cnes = E.id_cnes
        WHERE
            A.id_paciente IN (
                SELECT id_paciente
                FROM vacinacao.Paciente
                WHERE idade > 60
            )
        GROUP BY
            E.municipio
        ORDER BY
            Total_Idosos_Vacinados DESC
        LIMIT 10;
    """

    df_q4 = execute_query(query4)
    if df_q4 is not None:
        fig, ax = plt.subplots(figsize=(10, 7))
        ax.bar(range(len(df_q4)), df_q4['Total_Idosos_Vacinados'], color='skyblue')
        ax.set_xticks(range(len(df_q4)))
        ax.set_xticklabels(df_q4['Municipio'], rotation=30, ha='right')
        ax.set_ylabel('Idosos Vacinados')
        plt.tight_layout()
        st.pyplot(fig, width='content')
    
    if on:
        st.markdown('#### Consulta utilizada')
        st.code(query4, language='sql')


with col2:
    st.subheader("Vacinas Mais Aplicadas em Idosos (60+)")

    query5 = """
        SELECT
            V.nome AS Nome_Vacina,
            COUNT(A.id_aplicacao) AS Total_Doses
        FROM
            vacinacao.AplicacaoDose A
        INNER JOIN
            vacinacao.Vacina V ON A.id_vacina = V.id
        WHERE
            A.id_paciente IN (
                SELECT id_paciente
                FROM vacinacao.Paciente
                WHERE idade > 60
            )
            AND V.nome <> 'SEM INFORMAÇÃO'
        GROUP BY
            V.nome
        ORDER BY
            Total_Doses DESC
        LIMIT 5;
    """

    df_q5 = execute_query(query5)
    if df_q5 is not None:
        fig, ax = plt.subplots(figsize=(10, 6.5))
        ax.barh(df_q5['Nome_Vacina'], df_q5['Total_Doses'], color='lightcoral')
        ax.set_xlabel('Doses Aplicadas')
        ax.tick_params(axis='y', labelsize=8)
        plt.tight_layout()
        st.pyplot(fig, width='content')
    
    if on:
        st.markdown('#### Consulta utilizada')
        st.code(query5, language='sql')
        
        
st.divider()
st.markdown('## Aplicação do Paciente Mais Velho')

query6 = """
    SELECT 
        P.id_paciente,
        P.idade,
        P.municipio AS Municipio_Residencia,
        A.data_vacina,
        A.dose_vacina,
        V.nome AS Vacina_Aplicada,
        E.nome_fantasia AS Local_Aplicacao
    FROM 
        vacinacao.AplicacaoDose  A
    INNER JOIN 
        vacinacao.Paciente P ON A.id_paciente = P.id_paciente
    INNER JOIN 
        vacinacao.Vacina V ON A.id_vacina = V.id
    INNER JOIN 
        vacinacao.Estabelecimento E ON A.cnes = E.id_cnes
    WHERE 
        P.idade = (SELECT MAX(idade) FROM vacinacao.Paciente);
"""
col1, col2 = st.columns([1,1])

with col1:
    patient_id, idade, municipio, data, dose, vacina, unidade = execute_query(query6).loc[0].to_list()
    st.markdown(f"""
    No dia **{pd.to_datetime(data).strftime('%d/%m/%Y')}**, o paciente de ID `{patient_id}` com **{idade} anos** recebeu a **{dose}** da 
    **{vacina}** na **{unidade}** no município de **{municipio}**""")
    if on:
        st.markdown('#### Consulta utilizada')
        st.code(query6, language='sql')
with col2:

    st.image('assets/unidade.png',
            caption='📷️: Google Maps',
            width='stretch')
    
    
st.divider()
st.subheader("Vacinas Fabricadas no Brasil")
    
query7 = """
SELECT 
    V.nome AS Nome_Vacina,
    F.nome AS Nome_Fabricante
FROM 
    vacinacao.Vacina V
INNER JOIN 
    vacinacao.fabrica FAB ON V.id = FAB.id_vacina
INNER JOIN 
    vacinacao.Fabricante F ON FAB.id_fabricante = F.id
WHERE 
    (F.nome LIKE '%OSWALDO CRUZ%' OR F.nome LIKE '%BUTANTAN%')
    AND V.nome NOT LIKE '%SEM INFORMAÇÃO%'
ORDER BY F.nome, V.nome;
"""
df_q7 = execute_query(query7)


col1, col2 = st.columns([1, 1])
with col2:
    st.markdown("""
    As vacinas fabricadas no Brasil, como as do **Instituto Oswaldo Cruz** e do **Instituto Butantan**, são fundamentais para a 
    imunização da população. Elas garantem acesso a vacinas de qualidade, muitas vezes adaptadas às necessidades locais, e ajudam 
    a reduzir a dependência de importações.
    """)
    if on:
        st.markdown('#### Consulta utilizada')
        st.code(query7, language='sql')
with col1:
    selected_fabricante = st.selectbox('Filtrar por Fabricante', options=['FUNDACAO OSWALDO CRUZ', 'FUNDACAO BUTANTAN', 'Todos'], )
    if df_q7 is not None:
        if selected_fabricante == 'Todos':
            st.table(df_q7.rename(columns={'Nome_Vacina': 'Vacina', 'Nome_Fabricante': 'Fabricante'}))
        else:
            st.table(df_q7.rename(columns={'Nome_Vacina': 'Vacina', 'Nome_Fabricante': 'Fabricante'}).loc[df_q7['Nome_Fabricante'] == selected_fabricante])
            
st.caption(f"Última atualização: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")