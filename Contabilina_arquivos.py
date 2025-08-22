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
CNPJ_CLIENTE = '13891705000198'
RAZAO_CLIENTE = 'GM MOTOS LTDA'
PASTA_LOCAL = Path(os.getcwd())
PASTA_GOOGLE_DRIVE = Path(r'C:\Users\carlos.santos\Desktop\Arquivo')
INTERVALO = 30  # segundos entre varreduras

# Função para copiar qualquer arquivo (exceto pastas e Enviados)
def processar_arquivo(file_path):
    hoje = datetime.now()
    ano = str(hoje.year)
    mes = f"{hoje.month:02d}"
    tipo_arquivo = Path(file_path).suffix.lower().replace('.', '') or 'outros'
    destino = PASTA_GOOGLE_DRIVE / RAZAO_CLIENTE / 'ARQUIVOS' / tipo_arquivo / ano / mes
    destino.mkdir(parents=True, exist_ok=True)
    destino_arquivo = destino / Path(file_path).name
    logging.info(f"Copiando {file_path} para {destino_arquivo}")
    try:
        shutil.copy2(file_path, destino_arquivo)
        logging.info(f"Arquivo copiado com sucesso!")
        # Move o original para a subpasta 'Enviados'
        enviados_dir = PASTA_LOCAL / 'Enviados'
        enviados_dir.mkdir(exist_ok=True)
        destino_enviado = enviados_dir / Path(file_path).name
        shutil.move(file_path, destino_enviado)
        logging.info(f"Arquivo original movido para {destino_enviado}")
    except Exception as e:
        logging.error(f"Erro ao copiar/mover arquivo: {e}")

def monitorar_arquivos(stop_event):
    logging.info('[MONITOR] Monitorando a pasta por novos arquivos...')
    logging.info(f'[MONITOR] Pasta monitorada: {PASTA_LOCAL}')
    while not stop_event.is_set():
        arquivos = [
            x for x in PASTA_LOCAL.iterdir()
            if x.is_file()
            and x.suffix.lower() != '.log'
            and x.suffix.lower() != '.xml'
            and x.parent.name != 'Enviados'
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
