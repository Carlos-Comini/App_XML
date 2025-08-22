


import sqlite3

import os
import sys
import time
import threading
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
import pystray
from PIL import Image
import logging
import shutil

# Configuração do logging para arquivo
LOG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'contabelina.log')
logging.basicConfig(
    filename=LOG_PATH,
    filemode='a',
    format='%(asctime)s [%(levelname)s] %(message)s',
    level=logging.INFO
)

# Configurações
# PASTA_LOCAL agora é a pasta onde o .exe/.py está sendo executado
PASTA_LOCAL = Path(os.getcwd())
PASTA_GOOGLE_DRIVE = Path(r'C:\Users\carlos.santos\Desktop\Xml')
INTERVALO = 30  # segundos entre varreduras

def extrair_info_xml(xml_path):
    # CNPJ e razão social fixos do cliente
    CNPJ_CLIENTE = '06220643000127'
    RAZAO_CLIENTE = 'ALENCAR CONTABILIDADE LTDA'
    razao_social = 'Desconhecida'
    tipo_nota = 'Desconhecida'
    tipo_doc = 'Desconhecida'
    ano = datetime.now().strftime('%Y')
    mes = datetime.now().strftime('%m')
    try:
        logging.info(f"Lendo XML: {xml_path}")
        tree = ET.parse(xml_path)
        root = tree.getroot()
        ns = root.tag[root.tag.find('{'):root.tag.find('}')+1] if '{' in root.tag else ''
        tag_root = root.tag.replace(ns, '')
        # --- NF-e ---
        if tag_root in ['nfeProc', 'NFe'] or ns == '{http://www.portalfiscal.inf.br/nfe}':
            tipo_doc = 'NF-e'
            infNFe = root.find(f'.//{ns}infNFe')
            emit = infNFe.find(f'{ns}emit') if infNFe is not None else None
            dest = infNFe.find(f'{ns}dest') if infNFe is not None else None
            cnpj_emit = emit.find(f'{ns}CNPJ').text if emit is not None and emit.find(f'{ns}CNPJ') is not None else None
            cnpj_dest = dest.find(f'{ns}CNPJ').text if dest is not None and dest.find(f'{ns}CNPJ') is not None else None
            ide = infNFe.find(f'{ns}ide') if infNFe is not None else None
            data_emissao = ide.find(f'{ns}dhEmi').text if ide is not None and ide.find(f'{ns}dhEmi') is not None else None
            if data_emissao:
                ano = data_emissao[:4]
                mes = data_emissao[5:7]
            logging.info(f"NF-e: cnpj_emit={cnpj_emit}, cnpj_dest={cnpj_dest}, data_emissao={data_emissao}")
            if cnpj_emit == CNPJ_CLIENTE:
                razao_social = RAZAO_CLIENTE
                tipo_nota = 'Saída'
            elif cnpj_dest == CNPJ_CLIENTE:
                razao_social = RAZAO_CLIENTE
                tipo_nota = 'Entrada'
        # --- NFS-e ---
        elif tag_root in ['CompNfse'] or ns == '{http://www.abrasf.org.br/nfse.xsd}':
            tipo_doc = 'NFS-e'
            prestador = root.find(f'.//{ns}PrestadorServico')
            tomador = root.find(f'.//{ns}Tomador')
            cnpj_prest = prestador.find(f'.//{ns}Cnpj').text if prestador is not None and prestador.find(f'.//{ns}Cnpj') is not None else None
            cnpj_tomador = tomador.find(f'.//{ns}Cnpj').text if tomador is not None and tomador.find(f'.//{ns}Cnpj') is not None else None
            data_emissao = root.find(f'.//{ns}DataEmissao')
            if data_emissao is not None and data_emissao.text:
                ano = data_emissao.text[:4]
                mes = data_emissao.text[5:7]
            logging.info(f"NFS-e: cnpj_prest={cnpj_prest}, cnpj_tomador={cnpj_tomador}, data_emissao={getattr(data_emissao, 'text', None)}")
            if cnpj_prest == CNPJ_CLIENTE:
                razao_social = RAZAO_CLIENTE
                tipo_nota = 'Saída'
            elif cnpj_tomador == CNPJ_CLIENTE:
                razao_social = RAZAO_CLIENTE
                tipo_nota = 'Entrada'
        # --- CT-e ---
        elif tag_root in ['cteProc', 'CTe'] or ns == '{http://www.portalfiscal.inf.br/cte}':
            tipo_doc = 'CT-e'
            infCte = root.find(f'.//{ns}infCte')
            emit = infCte.find(f'{ns}emit') if infCte is not None else None
            dest = infCte.find(f'{ns}dest') if infCte is not None else None
            receb = infCte.find(f'{ns}receb') if infCte is not None else None
            cnpj_emit = emit.find(f'{ns}CNPJ').text if emit is not None and emit.find(f'{ns}CNPJ') is not None else None
            cnpj_dest = dest.find(f'{ns}CNPJ').text if dest is not None and dest.find(f'{ns}CNPJ') is not None else None
            cnpj_receb = receb.find(f'{ns}CNPJ').text if receb is not None and receb.find(f'{ns}CNPJ') is not None else None
            ide = infCte.find(f'{ns}ide') if infCte is not None else None
            data_emissao = ide.find(f'{ns}dhEmi').text if ide is not None and ide.find(f'{ns}dhEmi') is not None else None
            if data_emissao:
                ano = data_emissao[:4]
                mes = data_emissao[5:7]
            logging.info(f"CT-e: cnpj_emit={cnpj_emit}, cnpj_dest={cnpj_dest}, cnpj_receb={cnpj_receb}, data_emissao={data_emissao}")
            if cnpj_emit == CNPJ_CLIENTE:
                razao_social = RAZAO_CLIENTE
                tipo_nota = 'Saída'
            elif cnpj_dest == CNPJ_CLIENTE or cnpj_receb == CNPJ_CLIENTE:
                razao_social = RAZAO_CLIENTE
                tipo_nota = 'Entrada'
        logging.info(f"Extraído: razao_social={razao_social}, tipo_nota={tipo_nota}, tipo_doc={tipo_doc}, ano={ano}, mes={mes}")
        return razao_social, tipo_nota, tipo_doc, ano, mes
    except Exception as e:
        logging.error(f"[ERRO] Falha ao extrair informações do XML: {e}")
        return 'Desconhecida', 'Desconhecida', 'Desconhecida', datetime.now().strftime('%Y'), datetime.now().strftime('%m')

def mover_para_google_drive(file_path, razao_social, tipo_nota, tipo_doc, ano, mes):
    """
    Envia o arquivo para o Google Drive na estrutura correta e move o original para 'Enviados'.
    """
    try:
        from funcoes_compartilhadas.google_drive import enviar_com_subpastas
        # ID da pasta raiz do Drive (ajuste conforme seu ambiente)
        PASTA_RAIZ_ID = 'COLOQUE_AQUI_O_ID_DA_PASTA_RAIZ_DO_DRIVE'
        lista_subpastas = [razao_social, tipo_nota, tipo_doc, ano, mes]
        logging.info(f"Enviando {file_path} para o Google Drive: {lista_subpastas}")
        link_drive = enviar_com_subpastas(str(file_path), Path(file_path).name, PASTA_RAIZ_ID, lista_subpastas)
        logging.info(f"Arquivo enviado para o Drive! Link: {link_drive}")
        # Move o original para a subpasta 'Enviados'
        enviados_dir = PASTA_LOCAL / 'Enviados'
        enviados_dir.mkdir(exist_ok=True)
        destino_enviado = enviados_dir / Path(file_path).name
        shutil.move(file_path, destino_enviado)
        logging.info(f"Arquivo original movido para {destino_enviado}")
    except Exception as e:
        logging.error(f"Erro ao enviar/mover arquivo: {e}")

def monitorar_xmls(stop_event):
    logging.info('[MONITOR] Monitorando a pasta por novos XMLs...')
    logging.info(f'[MONITOR] Pasta monitorada: {PASTA_LOCAL}')
    while not stop_event.is_set():
        xmls = list(PASTA_LOCAL.glob('*.xml'))
        logging.info(f'[MONITOR] Arquivos XML encontrados: {[x.name for x in xmls]}')
        if not xmls:
            logging.info('[MONITOR] Nenhum XML novo encontrado.')
        for xml in xmls:
            logging.info(f'[MONITOR] Processando {xml.name}...')
            razao, tipo_nota, tipo_doc, ano, mes = extrair_info_xml(xml)
            logging.info(f'[MONITOR] Extraído: Razão Social={razao}, Tipo={tipo_nota}, Doc={tipo_doc}, Ano={ano}, Mês={mes}')
            try:
                mover_para_google_drive(str(xml), razao, tipo_nota, tipo_doc, ano, mes)
                logging.info(f'[MONITOR] Enviado para Google Drive: {xml.name} -> {razao}/{tipo_nota}/{tipo_doc}/{ano}/{mes}')
            except Exception as e:
                logging.error(f'[ERRO] Falha ao enviar {xml.name} para Google Drive: {e}')
        time.sleep(INTERVALO)

def on_exit(icon, item, stop_event):
    stop_event.set()
    icon.stop()

def run_tray():
    logging.info('[INICIO] Serviço Contabelina iniciado!')
    stop_event = threading.Event()
    t = threading.Thread(target=monitorar_xmls, args=(stop_event,), daemon=True)
    t.start()
    import sys
    if hasattr(sys, '_MEIPASS'):
        # Executando via PyInstaller
        icon_path = os.path.join(sys._MEIPASS, 'imagens', 'CONTABELINA.ico')
    else:
        icon_path = os.path.join(os.path.dirname(__file__), 'imagens', 'CONTABELINA.ico')
    logging.info(f'[INICIO] Carregando ícone: {icon_path}')
    try:
        image = Image.open(icon_path)
        menu = pystray.Menu(pystray.MenuItem('Sair', lambda icon, item: on_exit(icon, item, stop_event)))
        tray_icon = pystray.Icon("Contabelina", image, "Contabelina - Monitor de XMLs", menu)
        tray_icon.run()
    except Exception as e:
        logging.error(f'Erro ao carregar ícone ou iniciar tray: {e}')

if __name__ == '__main__':
    run_tray()

def on_exit(icon, item, stop_event):
    stop_event.set()
    icon.stop()

def run_tray():
    print('[INICIO] Serviço Contabelina iniciado!')
    stop_event = threading.Event()
    t = threading.Thread(target=monitorar_xmls, args=(stop_event,), daemon=True)
    t.start()
    # Carrega o ícone
    icon_path = os.path.join(os.path.dirname(__file__), 'imagens', 'CONTABELINA.ico')
    print(f'[INICIO] Carregando ícone: {icon_path}')
    image = Image.open(icon_path)
    menu = pystray.Menu(pystray.MenuItem('Sair', lambda icon, item: on_exit(icon, item, stop_event)))
    tray_icon = pystray.Icon("Contabelina", image, "Contabelina - Monitor de XMLs", menu)
    tray_icon.run()

if __name__ == '__main__':
    run_tray()
