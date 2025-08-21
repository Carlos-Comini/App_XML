

import os
import time
import threading
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import pystray
from PIL import Image

# Configurações
PASTA_LOCAL = Path(os.path.dirname(os.path.abspath(__file__)))
PASTA_DRIVE_ID = '1QrgORE3rm2d_CusD7cqT12wN5wQoeurj'  # Pasta "Xml" no Drive
CAMINHO_CRED = os.path.join(os.path.dirname(__file__), 'credenciais', 'drive.json')
TIPO_ARQUIVO = 'application/xml'
INTERVALO = 30  # segundos entre varreduras

# Função para extrair Razão Social, Ano e Mês do XML
def extrair_info_xml(xml_path):
    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()
        ns = {'nfe': 'http://www.portalfiscal.inf.br/nfe'}
        emit = root.find('.//nfe:emit', ns)
        razao_social = emit.find('nfe:xNome', ns).text if emit is not None else 'Desconhecida'
        ide = root.find('.//nfe:ide', ns)
        data_emissao = None
        if ide is not None:
            dhEmi = ide.find('nfe:dhEmi', ns)
            if dhEmi is not None and dhEmi.text:
                data_emissao = dhEmi.text[:10]
        if not data_emissao:
            data_emissao = datetime.now().strftime('%Y-%m-%d')
        ano = data_emissao[:4]
        mes = data_emissao[5:7]
        return razao_social, ano, mes
    except Exception as e:
        return 'Desconhecida', datetime.now().strftime('%Y'), datetime.now().strftime('%m')

# Função para autenticar no Google Drive
def get_drive_service():
    creds = service_account.Credentials.from_service_account_file(CAMINHO_CRED, scopes=['https://www.googleapis.com/auth/drive'])
    return build('drive', 'v3', credentials=creds)

def criar_pasta_drive(service, nome, parent_id):
    query = f"name='{nome}' and mimeType='application/vnd.google-apps.folder' and '{parent_id}' in parents and trashed=false"
    results = service.files().list(q=query, fields="files(id, name)").execute()
    items = results.get('files', [])
    if items:
        return items[0]['id']
    file_metadata = {
        'name': nome,
        'mimeType': 'application/vnd.google-apps.folder',
        'parents': [parent_id]
    }
    folder = service.files().create(body=file_metadata, fields='id').execute()
    return folder.get('id')

def upload_xml(service, file_path, razao_social, ano, mes):
    # Cria hierarquia de pastas se necessário
    id_razao = criar_pasta_drive(service, razao_social, PASTA_DRIVE_ID)
    id_ano = criar_pasta_drive(service, ano, id_razao)
    id_mes = criar_pasta_drive(service, mes, id_ano)
    file_metadata = {
        'name': os.path.basename(file_path),
        'parents': [id_mes]
    }
    media = MediaFileUpload(file_path, mimetype=TIPO_ARQUIVO)
    service.files().create(body=file_metadata, media_body=media, fields='id').execute()

def mover_para_enviados(xml_path):
    enviados = PASTA_LOCAL / 'enviados'
    enviados.mkdir(exist_ok=True)
    xml_path.rename(enviados / xml_path.name)


def monitorar_xmls(stop_event):
    print('Monitorando a pasta por novos XMLs...')
    service = get_drive_service()
    while not stop_event.is_set():
        xmls = list(PASTA_LOCAL.glob('*.xml'))
        for xml in xmls:
            print(f'Processando {xml.name}...')
            razao, ano, mes = extrair_info_xml(xml)
            try:
                upload_xml(service, str(xml), razao, ano, mes)
                mover_para_enviados(xml)
                print(f'Enviado: {xml.name} -> {razao}/{ano}/{mes}')
            except Exception as e:
                print(f'Erro ao enviar {xml.name}: {e}')
        time.sleep(INTERVALO)

def on_exit(icon, item, stop_event):
    stop_event.set()
    icon.stop()

def run_tray():
    stop_event = threading.Event()
    t = threading.Thread(target=monitorar_xmls, args=(stop_event,), daemon=True)
    t.start()
    # Carrega o ícone
    icon_path = os.path.join(os.path.dirname(__file__), 'imagens', 'CONTABELINA.ico')
    image = Image.open(icon_path)
    menu = pystray.Menu(pystray.MenuItem('Sair', lambda icon, item: on_exit(icon, item, stop_event)))
    tray_icon = pystray.Icon("Contabelina", image, "Contabelina - Monitor de XMLs", menu)
    tray_icon.run()

if __name__ == '__main__':
    run_tray()
