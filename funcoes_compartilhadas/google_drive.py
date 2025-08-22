# -*- coding: utf-8 -*-
# /funcoes_compartilhadas/google_drive.py
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive
import io
import json
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive
import tempfile

# Cole o conteúdo do seu credenciais.json aqui como string (apenas o JSON, sem código extra)
CREDENCIAIS_JSON = """
{
  "type": "service_account",
  "project_id": "SUA_PROJECT_ID",
  "private_key_id": "SUA_PRIVATE_KEY_ID",
  "private_key": "-----BEGIN PRIVATE KEY-----\\nSUA_CHAVE_AQUI\\n-----END PRIVATE KEY-----\\n",
  "client_email": "SUA_EMAIL@SUA_PROJECT_ID.iam.gserviceaccount.com",
  "client_id": "SUA_CLIENT_ID",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/SUA_EMAIL@SUA_PROJECT_ID.iam.gserviceaccount.com"
}
"""

def autenticar_drive():
    """
    Autentica no Google Drive usando credenciais embutidas.
    """
    import tempfile
    gauth = GoogleAuth()
    with tempfile.NamedTemporaryFile('w+', delete=False, suffix='.json') as tmp:
        tmp.write(CREDENCIAIS_JSON)
        tmp.flush()
        gauth.client_json_file_path = tmp.name
        gauth.ServiceAuth()
    return GoogleDrive(gauth)

def buscar_ou_criar_pasta(nome_pasta, pasta_pai_id=None):
    """
    Busca uma pasta pelo nome e ID da pasta pai.
    Se não encontrar, cria uma nova pasta com o nome na pasta pai especificada.
    Retorna o ID da pasta encontrada ou criada.
    """
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
