import streamlit as st
import sqlite3
import pandas as pd

st.title("Explorar Banco de Dados SQL")

DB_PATH = 'usuarios.db'

# Listar tabelas disponíveis
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tabelas = [row[0] for row in cursor.fetchall()]
conn.close()

selected_table = st.selectbox("Selecione a tabela para visualizar", tabelas)

if selected_table:
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query(f"SELECT * FROM {selected_table}", conn)
    conn.close()
    st.dataframe(df, use_container_width=True)
    st.write(f"Total de registros: {len(df)}")
