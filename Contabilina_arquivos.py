
import os
import sys
import time
import threading
from datetime import datetime
from pathlib import Path
import pystray
from PIL import Image
import logging
import shutil
# Google Drive
from funcoes_compartilhadas.google_drive import enviar_com_subpastas

# Configuração do logging para arquivo
LOG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'contabilina_arquivos.log')
logging.basicConfig(
    filename=LOG_PATH,
    filemode='a',
    format='%(asctime)s [%(levelname)s] %(message)s',
    level=logging.INFO
)

# Configurações
# Cliente específico
CNPJ_CLIENTE = '06220643000127'
RAZAO_CLIENTE = 'ALENCAR CONTABILIDADE LTDA'
PASTA_LOCAL = Path(os.getcwd())
# ID da pasta raiz do Google Drive (ajuste para o seu ambiente)
PASTA_RAIZ_ID = 'COLOQUE_AQUI_O_ID_DA_PASTA_RAIZ_DO_DRIVE'
INTERVALO = 30  # segundos entre varreduras

# Função para copiar qualquer arquivo (exceto pastas e Enviados)
def processar_arquivo(file_path):
    hoje = datetime.now()
    ano = str(hoje.year)
    mes = f"{hoje.month:02d}"
    tipo_arquivo = Path(file_path).suffix.lower().replace('.', '') or 'outros'
    subpastas = [RAZAO_CLIENTE, 'ARQUIVOS', tipo_arquivo, ano, mes]
    logging.info(f"Enviando {file_path} para o Google Drive: {subpastas}")
    try:
        link_drive = enviar_com_subpastas(str(file_path), Path(file_path).name, PASTA_RAIZ_ID, subpastas)
        logging.info(f"Arquivo enviado para o Drive! Link: {link_drive}")
        # Move o original para a subpasta 'Enviados'
        enviados_dir = PASTA_LOCAL / 'Enviados'
        enviados_dir.mkdir(exist_ok=True)
        destino_enviado = enviados_dir / Path(file_path).name
        shutil.move(file_path, destino_enviado)
        logging.info(f"Arquivo original movido para {destino_enviado}")
    except Exception as e:
        logging.error(f"Erro ao enviar/mover arquivo: {e}")

def monitorar_arquivos(stop_event):
    logging.info('[MONITOR] Monitorando a pasta por novos arquivos...')
    logging.info(f'[MONITOR] Pasta monitorada: {PASTA_LOCAL}')
    # Nome do script/executável
    nome_script = Path(sys.argv[0]).name.lower()
    while not stop_event.is_set():
        arquivos = [
            x for x in PASTA_LOCAL.iterdir()
            if x.is_file()
            and x.suffix.lower() != '.log'
            and x.suffix.lower() != '.xml'
            and x.parent.name != 'Enviados'
            and x.name.lower() != nome_script
        ]
        logging.info(f'[MONITOR] Arquivos encontrados: {[x.name for x in arquivos]}')
        if not arquivos:
            logging.info('[MONITOR] Nenhum arquivo novo encontrado.')
        for arq in arquivos:
            logging.info(f'[MONITOR] Processando {arq.name}...')
            processar_arquivo(str(arq))
        time.sleep(INTERVALO)

def on_exit(icon, item, stop_event):
    stop_event.set()
    icon.stop()

def run_tray():
    logging.info('[INICIO] Serviço Contabilina_arquivos iniciado!')
    stop_event = threading.Event()
    t = threading.Thread(target=monitorar_arquivos, args=(stop_event,), daemon=True)
    t.start()
    if hasattr(sys, '_MEIPASS'):
        icon_path = os.path.join(sys._MEIPASS, 'imagens', 'CONTABELINA.ico')
    else:
        icon_path = os.path.join(os.path.dirname(__file__), 'imagens', 'CONTABELINA.ico')
    logging.info(f'[INICIO] Carregando ícone: {icon_path}')
    try:
        image = Image.open(icon_path)
        menu = pystray.Menu(pystray.MenuItem('Sair', lambda icon, item: on_exit(icon, item, stop_event)))
        tray_icon = pystray.Icon("Contabilina_arquivos", image, "Contabilina - Monitor de Arquivos", menu)
        tray_icon.run()
    except Exception as e:
        logging.error(f'Erro ao carregar ícone ou iniciar tray: {e}')

if __name__ == '__main__':
    run_tray()
