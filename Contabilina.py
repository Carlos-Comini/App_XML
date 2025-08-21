import sqlite3


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

# Configurações
PASTA_LOCAL = Path(os.path.dirname(os.path.abspath(__file__)))
PASTA_GOOGLE_DRIVE = Path(r'C:\Users\carlos.santos\Desktop\Xml')
INTERVALO = 30  # segundos entre varreduras

def extrair_info_xml(xml_path):
    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()
        ns_nfe = {'nfe': 'http://www.portalfiscal.inf.br/nfe'}
        ns_cte = {'cte': 'http://www.portalfiscal.inf.br/cte'}
        ns_nfse = {'nfse': 'http://www.abrasf.org.br/nfse.xsd'}
        ns = ns_nfe  # default
        root_tag = root.tag.split('}')[-1] if '}' in root.tag else root.tag
        tipo_doc = 'NF-e'
        cnpj_emit = cnpj_dest = razao_emit = razao_dest = None
        if root_tag.lower() in ['nfeproc', 'nfe']:
            ns = ns_nfe
            tipo_doc = 'NF-e'
            emit = root.find('.//nfe:emit', ns)
            dest = root.find('.//nfe:dest', ns)
            cnpj_emit = emit.find('nfe:CNPJ', ns).text if emit is not None and emit.find('nfe:CNPJ', ns) is not None else None
            cnpj_dest = dest.find('nfe:CNPJ', ns).text if dest is not None and dest.find('nfe:CNPJ', ns) is not None else None
        elif root_tag.lower() in ['cteproc', 'cte']:
            ns = ns_cte
            tipo_doc = 'CT-e'
            emit = root.find('.//cte:emit', ns)
            dest = root.find('.//cte:dest', ns)
            receb = root.find('.//cte:receb', ns)
            # CNPJ do emitente
            cnpj_emit = emit.find('cte:CNPJ', ns).text if emit is not None and emit.find('cte:CNPJ', ns) is not None else None
            # CNPJ do destinatário
            cnpj_dest = dest.find('cte:CNPJ', ns).text if dest is not None and dest.find('cte:CNPJ', ns) is not None else None
            # Se não achar no dest, tenta no receb (recebedor)
            if not cnpj_dest and receb is not None and receb.find('cte:CNPJ', ns) is not None:
                cnpj_dest = receb.find('cte:CNPJ', ns).text
            # Razão social
            razao_emit = emit.find('cte:xNome', ns).text if emit is not None and emit.find('cte:xNome', ns) is not None else None
            razao_dest = dest.find('cte:xNome', ns).text if dest is not None and dest.find('cte:xNome', ns) is not None else None
            if not razao_dest and receb is not None and receb.find('cte:xNome', ns) is not None:
                razao_dest = receb.find('cte:xNome', ns).text
        elif root_tag.lower() in ['compnfse', 'nfse']:
            ns = ns_nfse
            tipo_doc = 'NFS-e'
            prestador = root.find('.//nfse:PrestadorServico', ns)
            tomador = root.find('.//nfse:Tomador', ns)
            if prestador is None:
                # padrão ABRASF: pode estar em InfDeclaracaoPrestacaoServico/Prestador
                prestador = root.find('.//nfse:Prestador', ns)
            if tomador is None:
                tomador = root.find('.//nfse:TomadorServico', ns)
            # CNPJ do prestador
            cnpj_emit = None
            if prestador is not None:
                cnpj_tag = prestador.find('.//nfse:Cnpj', ns)
                if cnpj_tag is None:
                    cnpj_tag = prestador.find('.//nfse:CNPJ', ns)
                if cnpj_tag is not None:
                    cnpj_emit = cnpj_tag.text
                razao_emit = prestador.findtext('.//nfse:RazaoSocial', default='', namespaces=ns)
            # CNPJ do tomador
            cnpj_dest = None
            if tomador is not None:
                cnpj_tag = tomador.find('.//nfse:Cnpj', ns)
                if cnpj_tag is None:
                    cnpj_tag = tomador.find('.//nfse:CNPJ', ns)
                if cnpj_tag is not None:
                    cnpj_dest = cnpj_tag.text
                razao_dest = tomador.findtext('.//nfse:RazaoSocial', default='', namespaces=ns)
        elif root_tag.lower() in ['nfce', 'nfcproc']:
            ns = ns_nfe
            tipo_doc = 'NFC-e'
            emit = root.find('.//nfe:emit', ns)
            dest = root.find('.//nfe:dest', ns)
            cnpj_emit = emit.find('nfe:CNPJ', ns).text if emit is not None and emit.find('nfe:CNPJ', ns) is not None else None
            cnpj_dest = dest.find('nfe:CNPJ', ns).text if dest is not None and dest.find('nfe:CNPJ', ns) is not None else None
        else:
            # fallback genérico
            emit = root.find('.//emit')
            dest = root.find('.//dest')
            cnpj_emit = emit.find('CNPJ').text if emit is not None and emit.find('CNPJ') is not None else None
            cnpj_dest = dest.find('CNPJ').text if dest is not None and dest.find('CNPJ') is not None else None
        cnpj_emit = ''.join(filter(str.isdigit, cnpj_emit)) if cnpj_emit else None
        cnpj_dest = ''.join(filter(str.isdigit, cnpj_dest)) if cnpj_dest else None
        razao_social = 'Desconhecida'
        tipo_nota = 'Desconhecida'
        db_path = os.path.join(os.path.dirname(__file__), 'empresas.db')
        try:
            conn = sqlite3.connect(db_path)
            cur = conn.cursor()
            # Tenta buscar razão social para emitente
            razao_emit = None
            razao_dest = None
            if cnpj_emit:
                cur.execute("SELECT razao_social FROM empresas WHERE cnpj=?", (cnpj_emit,))
                row = cur.fetchone()
                if row:
                    razao_emit = row[0]
            if cnpj_dest:
                cur.execute("SELECT razao_social FROM empresas WHERE cnpj=?", (cnpj_dest,))
                row = cur.fetchone()
                if row:
                    razao_dest = row[0]
            conn.close()
        except Exception as e:
            print(f"[ERRO] Falha ao consultar empresas.db: {e}")
        # Lógica: se encontrou razão social no emitente, é Saída; se no destinatário, é Entrada
        if razao_emit:
            razao_social = razao_emit
            tipo_nota = 'Saída'
        elif razao_dest:
            razao_social = razao_dest
            tipo_nota = 'Entrada'
        else:
            print("[ERRO] Nenhum CNPJ do XML encontrado no banco de empresas.")
        # Determina tipo de documento
    # tipo_doc já definido acima
        ide = root.find('.//nfe:ide', ns)
        data_emissao = None
        if ide is not None:
            dhEmi = ide.find('nfe:dhEmi', ns)
            dEmi = ide.find('nfe:dEmi', ns)
            if dhEmi is not None and dhEmi.text:
                data_emissao = dhEmi.text[:10]
            elif dEmi is not None and dEmi.text:
                data_emissao = dEmi.text[:10]
        if not data_emissao:
            for tag in ['dhEmi', 'dEmi', 'dataEmissao', 'DataEmissao', 'dtEmi']:
                for elem in root.iter():
                    localname = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag
                    if localname == tag and elem.text:
                        data_emissao = elem.text[:10]
                        break
                if data_emissao:
                    break
        if not data_emissao:
            data_emissao = datetime.now().strftime('%Y-%m-%d')
        ano = data_emissao[:4]
        mes = data_emissao[5:7]
        return razao_social, tipo_nota, tipo_doc, ano, mes
    except Exception as e:
        print(f"[ERRO] Falha ao extrair info do XML: {e}")
        return 'Desconhecida', 'Desconhecida', 'Desconhecida', datetime.now().strftime('%Y'), datetime.now().strftime('%m')

def mover_para_google_drive_local(file_path, razao_social, tipo_nota, tipo_doc, ano, mes):
    destino = PASTA_GOOGLE_DRIVE / razao_social / tipo_nota / tipo_doc / ano / mes
    destino.mkdir(parents=True, exist_ok=True)
    destino_arquivo = destino / Path(file_path).name
    print(f"[GOOGLE DRIVE LOCAL] Movendo {file_path} para {destino_arquivo}")
    Path(file_path).rename(destino_arquivo)
    print(f"[GOOGLE DRIVE LOCAL] Arquivo movido com sucesso!")

def monitorar_xmls(stop_event):
    print('[MONITOR] Monitorando a pasta por novos XMLs...')
    print(f'[MONITOR] Pasta monitorada: {PASTA_LOCAL}')
    while not stop_event.is_set():
        xmls = list(PASTA_LOCAL.glob('*.xml'))
        print(f'[MONITOR] Arquivos XML encontrados: {[x.name for x in xmls]}')
        if not xmls:
            print('[MONITOR] Nenhum XML novo encontrado.')
        for xml in xmls:
            print(f'[MONITOR] Processando {xml.name}...')
            razao, tipo_nota, tipo_doc, ano, mes = extrair_info_xml(xml)
            print(f'[MONITOR] Extraído: Razão Social={razao}, Tipo={tipo_nota}, Doc={tipo_doc}, Ano={ano}, Mês={mes}')
            try:
                mover_para_google_drive_local(str(xml), razao, tipo_nota, tipo_doc, ano, mes)
                print(f'[MONITOR] Movido para Google Drive local: {xml.name} -> {razao}/{tipo_nota}/{tipo_doc}/{ano}/{mes}')
            except Exception as e:
                print(f'[ERRO] Falha ao mover {xml.name} para Google Drive local: {e}')
        time.sleep(INTERVALO)

def on_exit(icon, item, stop_event):
    stop_event.set()
    icon.stop()

def run_tray():
    print('[INICIO] Serviço Contabelina iniciado!')
    stop_event = threading.Event()
    t = threading.Thread(target=monitorar_xmls, args=(stop_event,), daemon=True)
    t.start()
    icon_path = os.path.join(os.path.dirname(__file__), 'imagens', 'CONTABELINA.ico')
    print(f'[INICIO] Carregando ícone: {icon_path}')
    image = Image.open(icon_path)
    menu = pystray.Menu(pystray.MenuItem('Sair', lambda icon, item: on_exit(icon, item, stop_event)))
    tray_icon = pystray.Icon("Contabelina", image, "Contabelina - Monitor de XMLs", menu)
    tray_icon.run()

if __name__ == '__main__':
    run_tray()
    # service = get_drive_service()
    while not stop_event.is_set():
        xmls = list(PASTA_LOCAL.glob('*.xml'))
        print(f'[MONITOR] Arquivos XML encontrados: {[x.name for x in xmls]}')
        if not xmls:
            print('[MONITOR] Nenhum XML novo encontrado.')
        for xml in xmls:
            print(f'[MONITOR] Processando {xml.name}...')
            razao, tipo_nota, tipo_doc, ano, mes = extrair_info_xml(xml)
            print(f'[MONITOR] Extraído: Razão Social={razao}, Tipo={tipo_nota}, Doc={tipo_doc}, Ano={ano}, Mês={mes}')
            try:
                mover_para_google_drive_local(str(xml), razao, tipo_nota, tipo_doc, ano, mes)
                print(f'[MONITOR] Movido para Google Drive local: {xml.name} -> {razao}/{tipo_nota}/{tipo_doc}/{ano}/{mes}')
            except Exception as e:
                print(f'[ERRO] Falha ao mover {xml.name} para Google Drive local: {e}')
        time.sleep(INTERVALO)

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
