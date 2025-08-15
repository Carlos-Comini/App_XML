import streamlit as st
import hashlib
import os

XML_BASE = os.path.join(os.getcwd(), "xmls")


def hash_senha(senha: str) -> str:
    return hashlib.sha256(senha.encode()).hexdigest()


def autenticar_usuario(email, senha):
    from funcoes_compartilhadas.usuarios_sql import autenticar
    senha_hash = hash_senha(senha)
    usuario = autenticar(email, senha_hash)
    if usuario:
        return True, usuario.get("tipo", ""), usuario
    return False, None, None


## Funções salvar_empresa e salvar_usuario removidas. Reescreva usando SQL.


## Função listar_empresas removida. Reescreva usando SQL.

# Exemplos de integração SQL
from funcoes_compartilhadas.usuarios_sql import inserir_usuario, listar_usuarios, autenticar
from funcoes_compartilhadas.empresas_sql import inserir_empresa, listar_empresas, buscar_empresa_por_cnpj

# Exemplo: salvar novo usuário
# inserir_usuario(nome, email, senha, tipo, empresa, permissoes)

# Exemplo: autenticar usuário
# usuario = autenticar(email, senha)

# Exemplo: listar todos os usuários
# usuarios = listar_usuarios()

# Exemplo: salvar nova empresa
# inserir_empresa(cnpj, razao_social, endereco, telefone, email)

# Exemplo: listar todas as empresas
# empresas = listar_empresas()

# Exemplo: buscar empresa por CNPJ
# empresa = buscar_empresa_por_cnpj(cnpj)

