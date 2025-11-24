import streamlit as st
import pandas as pd

st.set_page_config(layout='wide', initial_sidebar_state='collapsed')

homepage = st.Page(page='views/1_home.py', 
                title='Página Inicial', 
                icon=':material/home:',
                default=True
)
page2 = st.Page(page='views/2_painel.py', 
                 title='Painel',
                 icon=':material/analytics:'
)
page3 = st.Page(page='views/3_estatisticas.py',
                title='Estatísticas 2024',
                icon=':material/calculate:')

page4 = st.Page(page='views/4_debug.py',
                title='Debug',
                icon='🪲')

pages = {
    "Páginas":[homepage, page2, page3, page4]
}
    
st.navigation(pages).run()
