

from funcoes_compartilhadas.empresas_sql import listar_empresas
from funcoes_compartilhadas.documentos_sql import criar_tabela_documentos, registrar_documento, listar_documentos
import streamlit as st
from funcoes_compartilhadas.estilos import aplicar_estilo_padrao, set_page_title
aplicar_estilo_padrao()
set_page_title("Arquivo")
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

import streamlit as st
from pathlib import Path
from datetime import datetime
import mimetypes
import re

BASE_DIR = Path("arquivo")

# Lista de bancos conhecidos para identificar o nome mesmo que contenha outras palavras
BANCOS_CONHECIDOS = [
    "SICREDI", "SICOOB", "BRADESCO", "BANCO DO BRASIL", "CAIXA", "ITAU",
    "SANTANDER", "INTER", "NUBANK", "BTG", "C6", "XP"
]

def get_cnpjs_sql():
    empresas = listar_empresas()
    return {e['cnpj']: e['razao_social'] for e in empresas}

def extrair_info(nome_arquivo):
    nome_limpo = nome_arquivo.lower()
    cnpj_match = re.search(r"\d{14}", nome_limpo)
    data_match = re.search(r"(\d{2})_(\d{4})", nome_limpo)

    cnpj = cnpj_match.group() if cnpj_match else "geral"
    mes = data_match.group(1) if data_match else "00"
    ano = data_match.group(2) if data_match else "0000"

    banco = "desconhecido"
    for b in BANCOS_CONHECIDOS:
        if b.lower() in nome_limpo:
            banco = b.upper()
            break

    return cnpj, banco, ano, mes

def exibir():
    from funcoes_compartilhadas.empresas_sql import criar_tabela_empresas
    criar_tabela_empresas()
    criar_tabela_documentos()
    st.title("📁 Arquivos Contábil")

    BASE_DIR.mkdir(parents=True, exist_ok=True)
    criar_tabela_documentos()
    st.subheader("📤 Enviar arquivos")

    tipos_aceitos = [
        "pdf", "jpg", "jpeg", "png",
        "xls", "xlsx",
        "doc", "docx",
        "ppt", "pptx",
        "txt"
    ]

    arquivos = st.file_uploader(
        "Envie arquivos (PDF, Excel, Word, Imagem, TXT...)", 
        type=tipos_aceitos, accept_multiple_files=True
    )

    if arquivos:
        from funcoes_compartilhadas.empresas_sql import buscar_empresa_por_cnpj
        dados_usuario = st.session_state.get("dados_usuario", {})
        usuario_nome = dados_usuario.get("nome", "anonimo")
        usuario_id = dados_usuario.get("id")
        # Se não houver id, tenta buscar pelo e-mail
        if not usuario_id:
            usuario_email = dados_usuario.get("email")
            if usuario_email:
                try:
                    from funcoes_compartilhadas.usuarios_sql import listar_usuarios
                    usuarios = listar_usuarios()
                    for u in usuarios:
                        if u.get("email") == usuario_email:
                            usuario_id = u.get("id")
                            break
                except Exception:
                    usuario_id = None
        # Busca empresas associadas ao usuário logado
        empresas_associadas = []
        if usuario_id:
            try:
                from funcoes_compartilhadas.usuarios_empresas_sql import get_empresas_usuario
                empresas_associadas = get_empresas_usuario(usuario_id)
            except Exception:
                empresas_associadas = []
        empresas_str = ", ".join(empresas_associadas) if empresas_associadas else "desconhecida"
        for arq in arquivos:
            nome = arq.name
            cnpj, banco, ano, mes = extrair_info(nome)
            ext = Path(nome).suffix
            # Se houver empresas associadas, salva em cada diretório
            empresas_para_salvar = empresas_associadas if empresas_associadas else [empresas_str]
            for razao_social in empresas_para_salvar:
                pasta_destino = BASE_DIR / cnpj / banco / ano / mes / razao_social
                pasta_destino.mkdir(parents=True, exist_ok=True)
                nome_final = f"{Path(nome).stem}_{usuario_nome}_{razao_social}{ext}"
                caminho = pasta_destino / nome_final
                with open(caminho, "wb") as f:
                    f.write(arq.read())
                # Registrar no banco
                info_doc = {
                    "nome": nome_final,
                    "caminho": str(caminho),
                    "empresa": razao_social,
                    "cnpj": cnpj,
                    "banco": banco,
                    "ano": ano,
                    "mes": mes,
                    "usuario": usuario_nome,
                    "razao_social_usuario": empresas_str,
                    "tipo": mimetypes.guess_type(caminho)[0] or "desconhecido",
                    "data_upload": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                sucesso = registrar_documento(info_doc)
                if not sucesso:
                    st.error(f"Já existe um arquivo com este nome para a empresa {razao_social}!")
                else:
                    st.info(f"Arquivo salvo e registrado para {razao_social}!")
        st.success(f"{len(arquivos)} arquivo(s) enviado(s) com sucesso!")

    st.subheader("📂 Arquivos Armazenados")
    documentos = [d for d in listar_documentos() if not d["nome"].lower().endswith(".xml")]
    # Pega dados do usuário logado
    dados_usuario = st.session_state.get("dados_usuario", {})
    empresas = sorted(set(d["empresa"] for d in documentos))
    filtro = st.selectbox("Filtrar por empresa", ["Todas"] + empresas)
    if filtro != "Todas":
        documentos = [d for d in documentos if d["empresa"] == filtro]
    import os
    from funcoes_compartilhadas.documentos_sql import deletar_documento
    for doc in documentos:
        nome_usuario = doc.get('usuario', 'N/A')
        # Busca razão social do usuário logado se não encontrar empresa
        razao_empresa = doc.get('empresa', None)
        if not razao_empresa or razao_empresa.lower() == 'desconhecida':
            dados_usuario = st.session_state.get("dados_usuario", {})
            razao_empresa = dados_usuario.get("razao_social", 'Não informado')
        data_importacao = doc.get('data_upload', 'N/A')
        with st.expander(f'{doc["nome"]} — {nome_usuario}'):
            st.markdown(f"""
<div style='display: flex; flex-direction: column; gap: 0.5rem;'>
<span>🏢 <b>Empresa:</b> {razao_empresa}</span>
<span>👤 <b>Usuário:</b> {nome_usuario}</span>
<span>📅 <b>Data da Importação:</b> {data_importacao}</span>
</div>
""", unsafe_allow_html=True)
            with open(doc["caminho"], "rb") as f:
                st.download_button("⬇️ Baixar", f, file_name=doc["nome"], key=f"download_{doc['id']}")
            if st.button(f"🗑️ Excluir documento {doc['id']}", key=f"del_{doc['id']}"):
                if st.session_state.get(f"confirm_del_{doc['id']}") != True:
                    st.warning("Tem certeza que deseja excluir este documento?")
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("Sim, excluir", key=f"confirma_{doc['id']}"):
                            st.session_state[f"confirm_del_{doc['id']}"] = True
                    with col2:
                        if st.button("Não cancelar", key=f"cancela_{doc['id']}"):
                            st.session_state[f"confirm_del_{doc['id']}"] = False
                elif st.session_state.get(f"confirm_del_{doc['id']}") == True:
                    try:
                        deletar_documento(doc['id'])
                        st.write(f"Caminho do arquivo: {doc['caminho']}")
                        st.write(f"Arquivo existe? {os.path.exists(doc['caminho'])}")
                        if os.path.exists(doc['caminho']):
                            os.remove(doc['caminho'])
                            st.success("Documento excluído com sucesso!")
                        else:
                            st.warning("Arquivo não encontrado para exclusão.")
                        st.session_state[f"confirm_del_{doc['id']}"] = False
                    except Exception as e:
                        st.error(f"Erro ao excluir: {e}")


