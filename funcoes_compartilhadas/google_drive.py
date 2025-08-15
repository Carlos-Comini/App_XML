# -*- coding: utf-8 -*-
# /funcoes_compartilhadas/google_drive.py
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive
import os

CAMINHO_CREDENCIAIS = os.path.join("credenciais", "drive.json")

def autenticar_drive():
    """Autentica no Google Drive usando conta de serviço"""
    gauth = GoogleAuth()
    gauth.ServiceAuth(CAMINHO_CREDENCIAIS)
    return GoogleDrive(gauth)

def buscar_ou_criar_pasta(nome_pasta, pasta_pai_id=None):
    """Busca pasta pelo nome, cria se não existir, e retorna o ID"""
    drive = autenticar_drive()
    query = f"title = '{nome_pasta}' and mimeType = 'application/vnd.google-apps.folder'"
    if pasta_pai_id:
        query += f" and '{pasta_pai_id}' in parents"
    pastas = drive.ListFile({'q': query}).GetList()
    if pastas:
        return pastas[0]['id']  # já existe
    pasta = drive.CreateFile({'title': nome_pasta, 'mimeType': 'application/vnd.google-apps.folder'})
    if pasta_pai_id:
        pasta['parents'] = [{'id': pasta_pai_id}]
    pasta.Upload()
    return pasta['id']

def enviar_para_drive(caminho_arquivo, nome_arquivo, pasta_pai_id=None):
    """Envia arquivo para o Google Drive e retorna link público"""
    drive = autenticar_drive()
    arquivo_drive = drive.CreateFile({'title': nome_arquivo, 'parents': [{'id': pasta_pai_id}] if pasta_pai_id else []})
    arquivo_drive.SetContentFile(caminho_arquivo)
    arquivo_drive.Upload()
    arquivo_drive.InsertPermission({'type': 'anyone', 'value': 'anyone', 'role': 'reader'})
    return f"https://drive.google.com/uc?id={arquivo_drive['id']}"

def enviar_com_subpastas(caminho_arquivo, nome_arquivo, pasta_raiz_id, lista_subpastas):
    """
    Envia arquivo para o Drive criando subpastas conforme lista_subpastas.
    Retorna link público.
    """
    pasta_atual_id = pasta_raiz_id
    for nome_subpasta in lista_subpastas:
        pasta_atual_id = buscar_ou_criar_pasta(nome_subpasta, pasta_atual_id)
    return enviar_para_drive(caminho_arquivo, nome_arquivo, pasta_atual_id)
