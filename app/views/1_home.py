import streamlit as st
import time
import numpy as np
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Dashboard de Vacinação",
    page_icon="💉",
    layout="wide",
)
st.logo('https://ic.ufrj.br/svg/logo-ic.svg')

st.title('💉 Vacinações no Rio de Janeiro')
st.divider()

st.markdown('## Sobre o trabalho')
paragraph1 = """
Este dashboard foi feito como parte do trabalho final da disciplina de **Banco de Dados (ICP489)** do semestre 2025.2 
do curso de Ciência da Computação da Universidade Federal do Rio de Janeiro.    
   
Este trabalho utiliza dados do Open Data SUS, especificamente, dados do [Programa Nacional de Imunizações (PNI) de 2024](https://opendatasus.saude.gov.br/dataset/doses-aplicadas-pelo-programa-de-nacional-de-imunizacoes-pni-2024).
Tendo em vista o seu grande volume, este projeto restringe-se apenas a uma amostra (cerca de 130 mil) de aplicações feitas no Estado do Rio de Janeiro.
"""
st.markdown(paragraph1)

st.markdown("""
## Sistema Único de Saúde e Vacinações

**A vacinação é reconhecida como uma das mais eficazes estratégias** para preservar 
a saúde da população e fortalecer uma sociedade saudável e resistente. Além de 
prevenir doenças graves, a imunização contribui para reduzir a disseminação desses 
agentes infecciosos na comunidade, protegendo aqueles que não podem ser vacinados 
por motivos de saúde.

""")

# Centralizando a imagem
col1, col2, col3 = st.columns([1,2,1])

with col2:
    st.image('assets/vacina.jpg', 
            caption='📷️: Edu Kapps - Secretaria Municipal de Saúde do Rio de Janeiro',
            width=500)

st.markdown("""
**A política de vacinação é responsabilidade do Programa Nacional de Imunizações (PNI)**
do Ministério da Saúde. Estabelecido em 1973, o PNI desempenha um papel fundamental 
na promoção da saúde da população brasileira. Por meio do programa, o governo federal 
disponibiliza gratuitamente no Sistema Único de Saúde - SUS 47 imunobiológicos: 30 vacinas, 
13 soros e 4 imunoglobulinas. Essas vacinas incluem tanto as presentes no calendário nacional 
de vacinação quanto as indicadas para grupos em condições clínicas especiais, como pessoas com 
HIV ou indivíduos em tratamento de algumas doenças (câncer, insuficiência renal, entre outras), 
aplicadas nos Centros de Referência para Imunobiológicos Especiais (CRIE), e inclui também as 
vacinas COVID-19 e outras administradas em situações específicas.
""")






