import os
from funcoes_compartilhadas.documentos_sql import listar_documentos, atualizar_data_documento
from paginas.arquivos_xml import parse_xml

def atualizar_datas():
    documentos = listar_documentos()
    atualizados = 0
    for doc in documentos:
        caminho = doc.get('caminho')
        if not caminho or not os.path.exists(caminho):
            continue
        dados_xml = parse_xml(caminho)
        data_documento = dados_xml.get('Data', None)
        if data_documento and data_documento not in [None, '', '—', 'Erro']:
            atualizar_data_documento(doc['id'], data_documento)
            atualizados += 1
    print(f"Datas atualizadas em {atualizados} documentos.")

if __name__ == "__main__":
    atualizar_datas()
    print("Processo concluído!")
