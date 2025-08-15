import tkinter as tk
from tkinter import messagebox
from pathlib import Path
import shutil
import xml.etree.ElementTree as ET
import sys
from datetime import datetime

# Caminho da pasta centralizada dos XMLs (ajuste conforme necessário)
XML_BASE = Path(r"C:\Users\carlos.santos\Desktop\App_XML\xmls")

if getattr(sys, 'frozen', False):
    # Executando como .exe
    PASTA_CLIENTE = Path(sys.executable).parent
else:
    # Executando como script Python
    PASTA_CLIENTE = Path(__file__).parent

def extrair_cnpj(xml_path):
    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()
        ns = {'nfe': 'http://www.portalfiscal.inf.br/nfe'}
        dest = root.find(".//nfe:dest", ns)
        emit = root.find(".//nfe:emit", ns)
        cnpj_dest = dest.find("nfe:CNPJ", ns).text if dest is not None else None
        cnpj_emit = emit.find("nfe:CNPJ", ns).text if emit is not None else None
        return cnpj_dest or cnpj_emit or "geral"
    except:
        return "geral"

def enviar_xml():
    arquivos = list(PASTA_CLIENTE.glob("*.xml"))
    if not arquivos:
        messagebox.showinfo("Aviso", "Nenhum arquivo XML encontrado na pasta do cliente.")
        return 0
    hoje = datetime.now().strftime("%Y_%m_%d")
    for arquivo in arquivos:
        cnpj = extrair_cnpj(arquivo)
        pasta_destino = XML_BASE / cnpj / hoje
        pasta_destino.mkdir(parents=True, exist_ok=True)
        novo_nome = f"exe_{arquivo.name}"
        destino = pasta_destino / novo_nome
        shutil.copy2(arquivo, destino)
    messagebox.showinfo("Sucesso", f"{len(arquivos)} arquivo(s) enviado(s) para a contabilidade!")
    return len(arquivos)

if __name__ == "__main__":
    root = tk.Tk()
    root.title("Uploader de XML")
    root.geometry("300x150")
    btn = tk.Button(root, text="Enviar XMLs da pasta do cliente", command=enviar_xml, height=2, width=30)
    btn.pack(pady=40)
    root.mainloop()
