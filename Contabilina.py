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
    # Inicializa variáveis padrão
    razao_social = 'Desconhecida'
    tipo_nota = 'Desconhecida'
    tipo_doc = 'Desconhecida'
    ano = datetime.now().strftime('%Y')
    mes = datetime.now().strftime('%m')
    try:
        import xml.etree.ElementTree as ET
        tree = ET.parse(xml_path)
        root = tree.getroot()

        # Detecta tipo de XML pelo namespace e tags
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
            # Ano e mês
            ide = infNFe.find(f'{ns}ide') if infNFe is not None else None
            data_emissao = ide.find(f'{ns}dhEmi').text if ide is not None and ide.find(f'{ns}dhEmi') is not None else None
            if data_emissao:
                ano = data_emissao[:4]
                mes = data_emissao[5:7]
            import sqlite3
            conn = sqlite3.connect('empresas.db')
            cursor = conn.cursor()
            razao_social = 'Desconhecida'
            tipo_nota = 'Desconhecida'
            # Verifica emitente (Saída)
            if cnpj_emit:
                cursor.execute("SELECT razao_social FROM empresas WHERE cnpj=?", (cnpj_emit,))
                row = cursor.fetchone()
                if row:
                    razao_social = row[0]
                    tipo_nota = 'Saída'
            # Se não achou, verifica destinatário (Entrada)
            if razao_social == 'Desconhecida' and cnpj_dest:
                cursor.execute("SELECT razao_social FROM empresas WHERE cnpj=?", (cnpj_dest,))
                row = cursor.fetchone()
                if row:
                    razao_social = row[0]
                    tipo_nota = 'Entrada'
            conn.close()
        # --- NFS-e ---
        elif tag_root in ['CompNfse'] or ns == '{http://www.abrasf.org.br/nfse.xsd}':
            tipo_doc = 'NFS-e'
            prestador = root.find(f'.//{ns}PrestadorServico')
            tomador = root.find(f'.//{ns}Tomador')
            cnpj_prest = prestador.find(f'.//{ns}Cnpj').text if prestador is not None and prestador.find(f'.//{ns}Cnpj') is not None else None
            cnpj_tomador = tomador.find(f'.//{ns}Cnpj').text if tomador is not None and tomador.find(f'.//{ns}Cnpj') is not None else None
            # Ano e mês
            data_emissao = root.find(f'.//{ns}DataEmissao')
            if data_emissao is not None and data_emissao.text:
                ano = data_emissao.text[:4]
                mes = data_emissao.text[5:7]
            import sqlite3
            conn = sqlite3.connect('empresas.db')
            cursor = conn.cursor()
            razao_social = 'Desconhecida'
            tipo_nota = 'Desconhecida'
            # Verifica prestador (Saída)
            if cnpj_prest:
                cursor.execute("SELECT razao_social FROM empresas WHERE cnpj=?", (cnpj_prest,))
                row = cursor.fetchone()
                if row:
                    razao_social = row[0]
                    tipo_nota = 'Saída'
            # Se não achou, verifica tomador (Entrada)
            if razao_social == 'Desconhecida' and cnpj_tomador:
                cursor.execute("SELECT razao_social FROM empresas WHERE cnpj=?", (cnpj_tomador,))
                row = cursor.fetchone()
                if row:
                    razao_social = row[0]
                    tipo_nota = 'Entrada'
            conn.close()
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
            # Ano e mês
            ide = infCte.find(f'{ns}ide') if infCte is not None else None
            data_emissao = ide.find(f'{ns}dhEmi').text if ide is not None and ide.find(f'{ns}dhEmi') is not None else None
            if data_emissao:
                ano = data_emissao[:4]
                mes = data_emissao[5:7]
            import sqlite3
            conn = sqlite3.connect('empresas.db')
            cursor = conn.cursor()
            razao_social = 'Desconhecida'
            tipo_nota = 'Desconhecida'
            # Verifica emitente (Saída)
            if cnpj_emit:
                cursor.execute("SELECT razao_social FROM empresas WHERE cnpj=?", (cnpj_emit,))
                row = cursor.fetchone()
                if row:
                    razao_social = row[0]
                    tipo_nota = 'Saída'
            # Se não achou, verifica destinatário (Entrada)
            if razao_social == 'Desconhecida' and cnpj_dest:
                cursor.execute("SELECT razao_social FROM empresas WHERE cnpj=?", (cnpj_dest,))
                row = cursor.fetchone()
                if row:
                    razao_social = row[0]
                    tipo_nota = 'Entrada'
            # Se não achou, verifica recebedor (Entrada)
            if razao_social == 'Desconhecida' and cnpj_receb:
                cursor.execute("SELECT razao_social FROM empresas WHERE cnpj=?", (cnpj_receb,))
                row = cursor.fetchone()
                if row:
                    razao_social = row[0]
                    tipo_nota = 'Entrada'
            conn.close()
        else:
            print(f'[DEBUG] Tipo de XML não reconhecido: {tag_root} {ns}')
        # LOG: mostrar CNPJs extraídos
        print(f"[DEBUG] CNPJ emitente extraído: {locals().get('cnpj_emit', None)}")
        print(f"[DEBUG] CNPJ destinatário extraído: {locals().get('cnpj_dest', None)}")
        print(f"[DEBUG] CNPJ recebedor extraído: {locals().get('cnpj_receb', None)}")
        print(f"[DEBUG] Razão social extraída: {razao_social}")
        print(f"[DEBUG] Tipo de nota: {tipo_nota} | Tipo doc: {tipo_doc} | Ano: {ano} | Mês: {mes}")
        return razao_social, tipo_nota, tipo_doc, ano, mes
    except Exception as e:
        print(f"[ERRO] Falha ao extrair informações do XML: {e}")
        return 'Desconhecida', 'Desconhecida', 'Desconhecida', datetime.now().strftime('%Y'), datetime.now().strftime('%m')
    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()
        # Detecta namespace real
        nsmap = {}
        if root.tag.startswith('{'):
            uri = root.tag.split('}')[0].strip('{')
            nsmap['ns'] = uri
        root_tag = root.tag.split('}')[-1] if '}' in root.tag else root.tag
        tipo_doc = 'NF-e'
        cnpj_emit = cnpj_dest = razao_emit = razao_dest = None
        if root_tag.lower() in ['nfeproc', 'nfe']:
            # NF-e padrão
            emit = root.find('.//ns:emit', nsmap) if nsmap else root.find('.//emit')
            dest = root.find('.//ns:dest', nsmap) if nsmap else root.find('.//dest')
            cnpj_emit = emit.find('ns:CNPJ', nsmap).text if emit is not None and emit.find('ns:CNPJ', nsmap) is not None else (emit.find('CNPJ').text if emit is not None and emit.find('CNPJ') is not None else None)
            cnpj_dest = dest.find('ns:CNPJ', nsmap).text if dest is not None and dest.find('ns:CNPJ', nsmap) is not None else (dest.find('CNPJ').text if dest is not None and dest.find('CNPJ') is not None else None)
        elif root_tag.lower() in ['cteproc', 'cte']:
            tipo_doc = 'CT-e'
            emit = root.find('.//ns:emit', nsmap) if nsmap else root.find('.//emit')
            dest = root.find('.//ns:dest', nsmap) if nsmap else root.find('.//dest')
            receb = root.find('.//ns:receb', nsmap) if nsmap else root.find('.//receb')
            cnpj_emit = emit.find('ns:CNPJ', nsmap).text if emit is not None and emit.find('ns:CNPJ', nsmap) is not None else (emit.find('CNPJ').text if emit is not None and emit.find('CNPJ') is not None else None)
            cnpj_dest = dest.find('ns:CNPJ', nsmap).text if dest is not None and dest.find('ns:CNPJ', nsmap) is not None else (dest.find('CNPJ').text if dest is not None and dest.find('CNPJ') is not None else None)
            if not cnpj_dest and receb is not None:
                cnpj_dest = receb.find('ns:CNPJ', nsmap).text if receb.find('ns:CNPJ', nsmap) is not None else (receb.find('CNPJ').text if receb.find('CNPJ') is not None else None)
            razao_emit = emit.find('ns:xNome', nsmap).text if emit is not None and emit.find('ns:xNome', nsmap) is not None else (emit.find('xNome').text if emit is not None and emit.find('xNome') is not None else None)
            razao_dest = dest.find('ns:xNome', nsmap).text if dest is not None and dest.find('ns:xNome', nsmap) is not None else (dest.find('xNome').text if dest is not None and dest.find('xNome') is not None else None)
            if not razao_dest and receb is not None:
                razao_dest = receb.find('ns:xNome', nsmap).text if receb.find('ns:xNome', nsmap) is not None else (receb.find('xNome').text if receb.find('xNome') is not None else None)
        elif root_tag.lower() in ['compnfse', 'nfse']:
            tipo_doc = 'NFS-e'
            # Busca PrestadorServico e TomadorServico com e sem prefixo
            prestador = root.find('.//ns:PrestadorServico', nsmap) or root.find('.//PrestadorServico')
            if prestador is None:
                prestador = root.find('.//ns:Prestador', nsmap) or root.find('.//Prestador')
            tomador = root.find('.//ns:Tomador', nsmap) or root.find('.//Tomador')
            if tomador is None:
                tomador = root.find('.//ns:TomadorServico', nsmap) or root.find('.//TomadorServico')
            cnpj_emit = None
            if prestador is not None:
                # Busca Cnpj e RazaoSocial com e sem prefixo
                cnpj_tag = prestador.find('.//ns:Cnpj', nsmap) or prestador.find('.//Cnpj')
                if cnpj_tag is None:
                    cnpj_tag = prestador.find('.//ns:CNPJ', nsmap) or prestador.find('.//CNPJ')
                if cnpj_tag is not None:
                    cnpj_emit = cnpj_tag.text
                razao_emit = prestador.findtext('.//ns:RazaoSocial', default='', namespaces=nsmap) or prestador.findtext('.//RazaoSocial', default='')
            cnpj_dest = None
            if tomador is not None:
                cnpj_tag = tomador.find('.//ns:Cnpj', nsmap) or tomador.find('.//Cnpj')
                if cnpj_tag is None:
                    cnpj_tag = tomador.find('.//ns:CNPJ', nsmap) or tomador.find('.//CNPJ')
                if cnpj_tag is not None:
                    cnpj_dest = cnpj_tag.text
                razao_dest = tomador.findtext('.//ns:RazaoSocial', default='', namespaces=nsmap) or tomador.findtext('.//RazaoSocial', default='')
        elif root_tag.lower() in ['nfce', 'nfcproc']:
            emit = root.find('.//ns:emit', nsmap) if nsmap else root.find('.//emit')
            dest = root.find('.//ns:dest', nsmap) if nsmap else root.find('.//dest')
            cnpj_emit = emit.find('ns:CNPJ', nsmap).text if emit is not None and emit.find('ns:CNPJ', nsmap) is not None else (emit.find('CNPJ').text if emit is not None and emit.find('CNPJ') is not None else None)
            cnpj_dest = dest.find('ns:CNPJ', nsmap).text if dest is not None and dest.find('ns:CNPJ', nsmap) is not None else (dest.find('CNPJ').text if dest is not None and dest.find('CNPJ') is not None else None)
        else:
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
                print(f"[DEBUG] Busca no banco para emitente ({cnpj_emit}): {row}")
                if row:
                    razao_emit = row[0]
            if cnpj_dest:
                cur.execute("SELECT razao_social FROM empresas WHERE cnpj=?", (cnpj_dest,))
                row = cur.fetchone()
                print(f"[DEBUG] Busca no banco para destinatário ({cnpj_dest}): {row}")
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
        # Busca data de emissão de forma genérica
        data_emissao = None
        # Procura por tags comuns de data de emissão
        for tag in ['dhEmi', 'dEmi', 'dataEmissao', 'DataEmissao', 'dtEmi', 'DataEmissao']:
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
    import sys
    if hasattr(sys, '_MEIPASS'):
        # Executando via PyInstaller
        icon_path = os.path.join(sys._MEIPASS, 'imagens', 'CONTABELINA.ico')
    else:
        icon_path = os.path.join(os.path.dirname(__file__), 'imagens', 'CONTABELINA.ico')
    print(f'[INICIO] Carregando ícone: {icon_path}')
    image = Image.open(icon_path)
    menu = pystray.Menu(pystray.MenuItem('Sair', lambda icon, item: on_exit(icon, item, stop_event)))
    tray_icon = pystray.Icon("Contabelina", image, "Contabelina - Monitor de XMLs", menu)
    tray_icon.run()

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
