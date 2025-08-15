import streamlit as st
import pandas as pd
from funcoes_compartilhadas.usuarios_sql import inserir_usuario, listar_usuarios
from funcoes_compartilhadas.estilos import aplicar_estilo_padrao, set_page_title

aplicar_estilo_padrao()
set_page_title("Cadastro de Usuários")
st.markdown("""
    <style>
    .topbar {position: fixed;top: 0;left: 0;width: 100vw;height: 64px;background: #263a53;display: flex;align-items: center;z-index: 100;box-shadow: 0 2px 8px #0002;}
    .topbar-logo {height: 40px;margin-left: 32px;margin-right: 24px;}
    .topbar-menu {display: flex;gap: 32px;}
    .topbar-menu a {color: #fff;font-size: 1.1rem;text-decoration: none;font-weight: 500;padding: 8px 0;transition: color 0.2s;}
    .topbar-menu a:hover {color: #42a5f5;}
    .topbar-account {margin-left: auto;margin-right: 32px;background: #42a5f5;color: #fff;border-radius: 8px;padding: 8px 18px;font-weight: 600;font-size: 1rem;box-shadow: 0 2px 8px #0002;}
    .stApp {padding-top: 72px !important;}
    </style>
    <div class="topbar">
        <img src="https://raw.githubusercontent.com/Notalize/brand-assets/main/logo-notalize.png" class="topbar-logo" alt="Logo" />
        <div class="topbar-menu">
            <a href="#">Cadastros</a>
            <a href="#">Administrativo</a>
            <a href="#">Busca de Documentos</a>
            <a href="#">NF-e | NFC-e | CF-e</a>
            <a href="#">CT-e</a>
            <a href="#">NFC-e</a>
            <a href="#">MDF-e</a>
            <a href="#">Relatórios</a>
        </div>
        <div class="topbar-account">Minha Conta</div>
    </div>
""", unsafe_allow_html=True)

def exibir():
    # Mostra o caminho absoluto do banco de dados para diagnóstico
    import os
    from funcoes_compartilhadas.usuarios_sql import DB_PATH
    st.info(f"Banco de dados em uso: {os.path.abspath(DB_PATH)}")
    st.header("Cadastro de Usuários")
    st.markdown("---")
    escolha = st.radio("Selecione a opção:", ["Cadastro de Usuário", "Usuários cadastrados"], horizontal=True)

    if escolha == "Cadastro de Usuário":
        tipo = st.radio("Tipo de Usuário", ["Escritório", "Cliente"], horizontal=True)
        with st.form("form_usuario"):
            nome = st.text_input("Nome")
            email = st.text_input("Email")
            senha = st.text_input("Senha", type="password")
            from funcoes_compartilhadas.conversa_banco import hash_senha
            # Validação básica
            erro = None
            if tipo == "Escritório":
                permitir_cadastros = st.checkbox("Permitir Cadastros")
                permitir_ver_arquivo = st.checkbox("Permitir Ver Arquivo")
                permitir_ver_xml = st.checkbox("Permitir Ver XML")
            else:
                from funcoes_compartilhadas.empresas_sql import listar_empresas
                empresas_df = pd.DataFrame(listar_empresas())
                if not empresas_df.empty:
                    if "nome_empresa" in empresas_df.columns:
                        empresas = empresas_df["nome_empresa"].tolist()
                    elif "razao_social" in empresas_df.columns:
                        empresas = empresas_df["razao_social"].tolist()
                    else:
                        empresas = empresas_df.iloc[:,0].astype(str).tolist()
                else:
                    empresas = []
                if not empresas:
                    st.warning("Nenhuma empresa cadastrada. Cadastre empresas antes de criar usuários do tipo Cliente.")
                empresas_selecionadas = st.multiselect("Empresas", empresas, disabled=not empresas)
                permitir_ver_arquivo = st.checkbox("Permitir Ver Arquivo")
                permitir_ver_xml = st.checkbox("Permitir Ver XML")
            submit = st.form_submit_button("Salvar")
            if submit:
                if not nome or not email or not senha:
                    st.error("Preencha todos os campos obrigatórios!")
                elif len(senha) < 6:
                    st.error("A senha deve ter pelo menos 6 caracteres.")
                else:
                    if tipo == "Escritório":
                        permissoes = {
                            "cadastrar": permitir_cadastros,
                            "ver_arquivo": permitir_ver_arquivo,
                            "ver_xml": permitir_ver_xml
                        }
                        senha_hash = hash_senha(senha)
                        sucesso = inserir_usuario(nome, email, senha_hash, "Escritorio", permissoes=permissoes)
                        if not sucesso:
                            st.error("Já existe um usuário cadastrado com este e-mail.")
                        else:
                            st.success("Usuário do escritório cadastrado.")
                    else:
                        permissoes = {
                            "ver_arquivo": permitir_ver_arquivo,
                            "ver_xml": permitir_ver_xml
                        }
                        senha_hash = hash_senha(senha)
                        sucesso = inserir_usuario(nome, email, senha_hash, "Cliente", empresa=None, permissoes=permissoes)
                        if not sucesso:
                            st.error("Já existe um usuário cadastrado com este e-mail.")
                        else:
                            # Salva associações usuário-empresa
                            from funcoes_compartilhadas.usuarios_sql import criar_tabela_usuarios_empresas
                            criar_tabela_usuarios_empresas()
                            usuarios = listar_usuarios()
                            usuario_id = None
                            for u in usuarios:
                                if u["email"] == email:
                                    usuario_id = u["id"]
                                    break
                            if usuario_id and empresas_selecionadas:
                                from funcoes_compartilhadas.empresas_sql import listar_empresas
                                empresas_db = listar_empresas()
                                for emp_nome in empresas_selecionadas:
                                    for emp in empresas_db:
                                        if emp_nome in (emp.get("nome_empresa"), emp.get("razao_social")):
                                            emp_id = emp["id"]
                                            # Salva associação
                                            import sqlite3, os
                                            BASE_DIR = os.path.dirname(os.path.abspath(__file__))
                                            DB_PATH = os.path.join(BASE_DIR, '..', 'usuarios.db')
                                            conn = sqlite3.connect(DB_PATH)
                                            cursor = conn.cursor()
                                            cursor.execute('INSERT OR IGNORE INTO usuarios_empresas (id_usuario, id_empresa) VALUES (?, ?)', (usuario_id, emp_id))
                                            conn.commit()
                                            conn.close()
                            st.success("Usuário de cliente cadastrado e empresas associadas.")

    elif escolha == "Usuários cadastrados":
        st.subheader("Usuários cadastrados")
        opcao_tabela = st.radio("Visualizar usuários do tipo:", ["Escritório", "Cliente"], horizontal=True)
        usuarios = listar_usuarios()
        if usuarios:
            from funcoes_compartilhadas.usuarios_empresas_sql import get_empresas_usuario
            df_usuarios = pd.DataFrame(usuarios)
            if opcao_tabela == "Escritório":
                df_filtrados = df_usuarios[df_usuarios["tipo"].str.lower() == "escritorio"]
            else:
                df_filtrados = df_usuarios[df_usuarios["tipo"].str.lower() == "cliente"]
                # Adiciona coluna com empresas associadas
                empresas_col = []
                for idx, row in df_filtrados.iterrows():
                    empresas = get_empresas_usuario(row['id'])
                    empresas_col.append(", ".join(empresas) if empresas else "-")
                df_filtrados = df_filtrados.copy()
                df_filtrados["empresas_associadas"] = empresas_col
            if not df_filtrados.empty:
                colunas_ocultas = [col for col in ['id', 'senha', 'empresa'] if col in df_filtrados.columns]
                st.dataframe(df_filtrados.drop(columns=colunas_ocultas), use_container_width=True)
            else:
                st.info(f"Nenhum usuário do tipo {opcao_tabela} cadastrado ainda.")
        else:
            st.info("Nenhum usuário cadastrado ainda.")
