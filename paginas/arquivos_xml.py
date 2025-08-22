from funcoes_compartilhadas.empresas_sql import buscar_empresa_por_cnpj
from funcoes_compartilhadas.documentos_sql import criar_tabela_documentos, registrar_documento, listar_documentos
import streamlit as st
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
XML_BASE = Path("xmls")



def parse_xml(file_path):
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
        ns = {'nfe': 'http://www.portalfiscal.inf.br/nfe'}

        ide = root.find(".//nfe:ide", ns)
        emit = root.find(".//nfe:emit", ns)
        dest = root.find(".//nfe:dest", ns)
        total = root.find(".//nfe:ICMSTot", ns)

        numero = "—"
        data_emissao = "—"
        # Detecta layout
        root_tag = root.tag.split('}')[-1] if '}' in root.tag else root.tag
        if root_tag.lower() in ["nfeproc", "nfe"]:
            # NF-e
            if ide is not None:
                numero = ide.find("nfe:nNF", ns).text if ide.find("nfe:nNF", ns) is not None else "—"
                dhEmi = ide.find("nfe:dhEmi", ns)
                if dhEmi is not None and dhEmi.text:
                    data_emissao = dhEmi.text[:10]
        elif root_tag.lower() in ["compnfse", "nfse"]:
            # NFS-e
            numero = "—"
            data_emissao = "—"
            # Busca número e data em qualquer lugar ignorando namespace
            for elem in root.iter():
                localname = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag
                if localname.lower() == "numero" and numero == "—" and elem.text:
                    numero = elem.text
                if localname.lower() == "dataemissao" and data_emissao == "—" and elem.text:
                    data_emissao = elem.text[:10]
        elif root_tag.lower() in ["cteproc", "cte"]:
            # CT-e
            ide_cte = root.find(".//ide")
            if ide_cte is not None:
                numero = ide_cte.find("nCT").text if ide_cte.find("nCT") is not None else "—"
                dhEmi = ide_cte.find("dhEmi")
                if dhEmi is not None and dhEmi.text:
                    data_emissao = dhEmi.text[:10]
        # Fallback para outros layouts
        if data_emissao == "—":
            for tag in ["dhEmi", "dEmi", "dataEmissao", "DataEmissao", "dtEmi"]:
                for elem in root.iter():
                    localname = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag
                    if localname == tag and elem.text:
                        data_emissao = elem.text[:10]
                        break
                if data_emissao != "—":
                    break
        cnpj_emit = emit.find("nfe:CNPJ", ns).text if emit is not None else "—"
        cnpj_dest = dest.find("nfe:CNPJ", ns).text if dest is not None else "—"
        valor = total.find("nfe:vNF", ns).text if total is not None else "—"

        return {
            "Número": numero,
            "Data": data_emissao,
            "CNPJ_Emitente": cnpj_emit,
            "CNPJ_Destinatario": cnpj_dest,
            "Valor": valor
        }
    except:
        return {"Número": "Erro", "Data": "Erro", "CNPJ_Emitente": "Erro", "CNPJ_Destinatario": "Erro", "Valor": "Erro"}

def exibir():
    from funcoes_compartilhadas.empresas_sql import criar_tabela_empresas, listar_empresas
    criar_tabela_empresas()
    criar_tabela_documentos()
    st.title("📂 Gestão de Arquivos XML")
    st.subheader("📤 Enviar XML manualmente")
    uploaded = st.file_uploader("Escolha um ou mais arquivos XML", type=["xml"], accept_multiple_files=True)

    def normaliza_cnpj(cnpj):
        if not cnpj:
            return ''
        return ''.join(filter(str.isdigit, cnpj))
    empresas_cadastradas = [normaliza_cnpj(e["cnpj"]) for e in listar_empresas()]

    if uploaded:
        criar_tabela_documentos()
        for file in uploaded:
            temp_path = XML_BASE / "temp.xml"
            try:
                # Salva o arquivo temporário antes do parse
                with open(temp_path, "wb") as f:
                    f.write(file.read())
                # Busca modelo fiscal por tag raiz, campo <mod>, tags internas ou texto
                tipo_xml = 'Desconhecido'
                cnpj_emit = None
                cnpj_dest = None
                # Busca modelo fiscal (mantém lógica anterior)
                tree = ET.parse(temp_path)
                root = tree.getroot()
                def find_tag(root, tag):
                    for elem in root.iter():
                        localname = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag
                        if localname == tag:
                            return elem.text
                    return None
                root_localname = root.tag.split('}')[-1] if '}' in root.tag else root.tag
                root_ns = root.tag.split('}')[0][1:] if '}' in root.tag else ''
                if root_localname.lower().startswith('compnfse') or 'nfse.xsd' in root_ns:
                    tipo_xml = 'NFS-e'
                elif root_localname.lower().startswith('nfeproc') or root_localname.lower() == 'nfe':
                    tipo_xml = 'NF-e'
                elif root_localname.lower().startswith('cteproc') or root_localname.lower() == 'cte':
                    tipo_xml = 'CT-e'
                elif root_localname.lower().startswith('mdfeproc') or root_localname.lower() == 'mdfe':
                    tipo_xml = 'MDF-e'
                if tipo_xml == 'Desconhecido':
                    mod_val = find_tag(root, 'mod')
                    if mod_val == '55':
                        tipo_xml = 'NF-e'
                    elif mod_val == '65':
                        tipo_xml = 'NFC-e'
                    elif mod_val == '57':
                        tipo_xml = 'CT-e'
                    elif mod_val == '58':
                        tipo_xml = 'MDF-e'
                    elif mod_val:
                        tipo_xml = mod_val
                if tipo_xml == 'Desconhecido':
                    for elem in root.iter():
                        localname = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag
                        if localname.lower() == 'nfe':
                            tipo_xml = 'NF-e'
                            break
                        elif localname.lower() == 'cte':
                            tipo_xml = 'CT-e'
                            break
                        elif localname.lower() == 'nfse':
                            tipo_xml = 'NFS-e'
                            break
                        elif localname.lower() == 'mdfe':
                            tipo_xml = 'MDF-e'
                            break
                if tipo_xml == 'Desconhecido':
                    try:
                        with open(temp_path, 'r', encoding='utf-8') as f:
                            xml_text = f.read().lower()
                        if 'nfce' in xml_text:
                            tipo_xml = 'NFC-e'
                        elif 'nfe' in xml_text:
                            tipo_xml = 'NF-e'
                        elif 'cte' in xml_text:
                            tipo_xml = 'CT-e'
                        elif 'nfse' in xml_text:
                            tipo_xml = 'NFS-e'
                        elif 'mdfe' in xml_text:
                            tipo_xml = 'MDF-e'
                        # Busca CNPJ do emitente e destinatário pelas tags corretas
                        cnpj_emit = None
                        cnpj_dest = None
                        for elem in root.iter():
                            localname = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag
                            if localname.lower() == 'emit':
                                for subelem in elem.iter():
                                    sublocal = subelem.tag.split('}')[-1] if '}' in subelem.tag else subelem.tag
                                    if sublocal.lower() == 'cnpj':
                                        cnpj_emit = normaliza_cnpj(subelem.text)
                                        break
                            if localname.lower() == 'dest':
                                for subelem in elem.iter():
                                    sublocal = subelem.tag.split('}')[-1] if '}' in subelem.tag else subelem.tag
                                    if sublocal.lower() == 'cnpj':
                                        cnpj_dest = normaliza_cnpj(subelem.text)
                                        break
                        tipo_nota = 'Desconhecido'
                        cnpj = None
                        if cnpj_emit and cnpj_emit in empresas_cadastradas:
                            tipo_nota = 'Saída'
                            cnpj = cnpj_emit
                        elif cnpj_dest and cnpj_dest in empresas_cadastradas:
                            tipo_nota = 'Entrada'
                            cnpj = cnpj_dest
                    except Exception:
                        pass
                # Se não encontrou pelo texto, tenta buscar CNPJ por tags (fallback)
                if not cnpj_emit or not cnpj_dest:
                    for elem in root.iter():
                        localname = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag
                        if not cnpj_emit and localname in ['PrestadorServico', 'emit', 'prest']:
                            for subelem in elem.iter():
                                sublocal = subelem.tag.split('}')[-1] if '}' in subelem.tag else subelem.tag
                                if sublocal in ['Cnpj', 'CNPJ']:
                                    cnpj_emit = subelem.text
                                    break
                            if cnpj_emit:
                                break
                        if not cnpj_dest and localname in ['Tomador', 'dest', 'receb', 'toma', 'rem', 'exped']:
                            for subelem in elem.iter():
                                sublocal = subelem.tag.split('}')[-1] if '}' in subelem.tag else subelem.tag
                                if sublocal in ['Cnpj', 'CNPJ']:
                                    cnpj_dest = subelem.text
                                    break
                            if cnpj_dest:
                                break
                        for subelem in elem.iter():
                            sublocal = subelem.tag.split('}')[-1] if '}' in subelem.tag else subelem.tag
                            if sublocal in ['Cnpj', 'CNPJ']:
                                cnpj_emit = subelem.text
                                break
                        if cnpj_emit:
                            break
                # Busca CNPJ do destinatário/tomador em várias tags possíveis
                cnpj_dest = None
                for elem in root.iter():
                    localname = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag
                    if localname in ['Tomador', 'dest', 'receb', 'toma']:
                        for subelem in elem.iter():
                            sublocal = subelem.tag.split('}')[-1] if '}' in subelem.tag else subelem.tag
                            if sublocal in ['Cnpj', 'CNPJ']:
                                cnpj_dest = subelem.text
                                break
                        if cnpj_dest:
                            break
            except Exception:
                tipo_xml = 'Desconhecido'
                cnpj_emit = None
                cnpj_dest = None

            # Aceita qualquer tipo reconhecido e define tipo de nota
            tipo_nota = 'Desconhecido'
            cnpj = None
            cnpj_emit_norm = normaliza_cnpj(cnpj_emit)
            cnpj_dest_norm = normaliza_cnpj(cnpj_dest)
            if cnpj_emit_norm in empresas_cadastradas:
                tipo_nota = 'Saída'
                cnpj = cnpj_emit_norm
            elif cnpj_dest_norm in empresas_cadastradas:
                tipo_nota = 'Entrada'
                cnpj = cnpj_dest_norm
            else:
                st.warning(
                    f"O arquivo '{file.name}' não foi aceito porque o CNPJ do emitente ou destinatário não está cadastrado no sistema. "
                    "Por favor, cadastre a empresa antes de enviar este XML."
                )
                continue

            empresa_info = buscar_empresa_por_cnpj(cnpj)
            nome_empresa = empresa_info["razao_social"] if empresa_info else cnpj
            hoje = datetime.today()
            ano = str(hoje.year)
            mes = f"{hoje.month:02d}"
            # Nova hierarquia: Razão Social / Entrada ou Saída / Ano / Mês
            pasta_destino = XML_BASE / nome_empresa / tipo_nota / ano / mes
            pasta_destino.mkdir(parents=True, exist_ok=True)
            caminho = pasta_destino / file.name
            temp_path.replace(caminho)
            # Extrai dados do XML para salvar a data exata
            dados_xml = parse_xml(str(caminho))
            data_documento = dados_xml.get("Data", "—")
            documentos_existentes = listar_documentos()
            ja_existe = any(
                d["nome"] == file.name and d["caminho"] == str(caminho)
                for d in documentos_existentes
            )
            if ja_existe:
                st.warning(f"O arquivo '{file.name}' já foi registrado para esta empresa e data.")
            else:
                info_doc = {
                    "nome": file.name,
                    "caminho": str(caminho),
                    "empresa": nome_empresa,
                    "cnpj": cnpj,
                    "banco": "XML",
                    "ano": ano,
                    "mes": mes,
                    "tipo_xml": tipo_xml,
                    "tipo_nota": tipo_nota,
                    "tipo": tipo_xml,
                    "data_upload": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "data_documento": data_documento
                }
                sucesso = registrar_documento(info_doc)
                if not sucesso:
                    st.error(f"Já existe um arquivo com este nome para esta empresa!")
                else:
                    st.info(f"Arquivo XML salvo e registrado como {info_doc['tipo_xml']} - {info_doc['tipo_nota']}!")
        st.success(f"{len(uploaded)} arquivo(s) salvo(s) com sucesso!")

    st.subheader("📁 Arquivos Recebidos")
    documentos = listar_documentos()
    empresas = sorted(set(d["empresa"] for d in documentos if d["banco"] == "XML"))
    filtro = st.selectbox("Filtrar por empresa", ["Todas"] + empresas)
    docs_xml = [d for d in documentos if d["banco"] == "XML"]
    if filtro != "Todas":
        docs_xml = [d for d in docs_xml if d["empresa"] == filtro]
    import os
    from funcoes_compartilhadas.documentos_sql import deletar_documento
    if docs_xml:
        for doc in docs_xml:
            with st.expander(f'{doc["nome"]} — {doc["empresa"]} {doc["ano"]}/{doc["mes"]}'):
                st.write(f"📌 Empresa: {doc['empresa']}")
                tipo_xml = doc.get('tipo_xml') or doc.get('tipo') or 'Desconhecido'
                tipo_nota = doc.get('tipo_nota') or 'Desconhecido'
                st.write(f"📄 Tipo de XML: {tipo_xml}")
                st.write(f"📝 Tipo de Nota: {tipo_nota}")
                data_real = doc.get('data_documento')
                if data_real and data_real not in [None, '', '—', 'Erro']:
                    st.write(f"📅 Data do Documento: {data_real}")
                else:
                    st.write(f"📅 Data do Documento: Não disponível")
                if os.path.exists(doc["caminho"]):
                    try:
                        with open(doc["caminho"], "rb") as f:
                            st.download_button("⬇️ Baixar XML", f, file_name=doc["nome"], key=f"download_{doc['id']}")
                    except Exception as e:
                        st.warning(f"Erro ao abrir o arquivo para download: {e}")
                else:
                    st.warning("Arquivo não encontrado no servidor para download.")
                if st.button(f"🗑️ Excluir XML {doc['id']}", key=f"delxml_{doc['id']}"):
                    if st.session_state.get(f"confirm_delxml_{doc['id']}") != True:
                        st.warning("Tem certeza que deseja excluir este XML?")
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button("Sim, excluir", key=f"confirma_xml_{doc['id']}"):
                                st.session_state[f"confirm_delxml_{doc['id']}"] = True
                        with col2:
                            if st.button("Não cancelar", key=f"cancela_xml_{doc['id']}"):
                                st.session_state[f"confirm_delxml_{doc['id']}"] = False
                    elif st.session_state.get(f"confirm_delxml_{doc['id']}") == True:
                        try:
                            deletar_documento(doc['id'])
                            excluiu_arquivo = False
                            if os.path.exists(doc['caminho']):
                                os.remove(doc['caminho'])
                                excluiu_arquivo = True
                            st.success(
                                f"XML excluído com sucesso!\n"
                                f"Caminho do arquivo: {doc['caminho']}\n"
                                f"Arquivo físico removido: {'Sim' if excluiu_arquivo else 'Não'}\n"
                                f"Registro removido do banco: Sim"
                            )
                            st.session_state[f"confirm_delxml_{doc['id']}"] = False
                            # Atualiza a lista de documentos para sumir da tabela
                            st.experimental_rerun()
                        except Exception as e:
                            st.error(f"Erro ao excluir: {e}\nCaminho do arquivo: {doc['caminho']}")
    else:
        st.info("Nenhum arquivo XML encontrado.")

    # NOVA SEÇÃO: Visualizar arquivos XML enviados pela Contabilina
    st.subheader("📑 XMLs enviados pela Contabilina")
    xmls_base = Path("xmls")
    if not xmls_base.exists():
        st.info("Nenhum XML enviado ainda.")
        return
    xmls_encontrados = list(xmls_base.glob("**/*.xml"))
    if not xmls_encontrados:
        st.info("Nenhum XML enviado ainda.")
        return
    agrupados = {}
    for xml in xmls_encontrados:
        partes = xml.parts
        # Esperado: xmls/CNPJ/DATA/arquivo.xml
        if len(partes) >= 4:
            cnpj = partes[1]
            data = partes[2]
            agrupados.setdefault((cnpj, data), []).append(xml)
        else:
            agrupados.setdefault(("geral", "mês"), []).append(xml)
    for (cnpj, data), arquivos in sorted(agrupados.items()):
        with st.expander(f"CNPJ: {cnpj} | Data: {data} ({len(arquivos)} arquivo(s))"):
            for xml in arquivos:
                st.write(f"📄 {xml.name}")
                try:
                    with open(xml, "rb") as f:
                        st.download_button("⬇️ Baixar XML", f, file_name=xml.name, key=f"download_xml_{xml}")
                except Exception as e:
                    st.warning(f"Erro ao abrir o arquivo para download: {e}")

    # NOVA SEÇÃO: Visualização bonita e filtrável dos arquivos do Google Drive
    st.subheader("☁️ Arquivos XML no Google Drive (visualização moderna)")
    import pandas as pd
    from googleapiclient.discovery import build
    from google.oauth2 import service_account
    import datetime

    # Caminho para o arquivo de credenciais do serviço Google
    SERVICE_ACCOUNT_FILE = 'credenciais.json'
    SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
    FOLDER_ID = st.text_input('ID da pasta do Google Drive para listar arquivos:', value='', help='Cole aqui o ID da pasta do Drive que deseja visualizar')
    if FOLDER_ID:
        try:
            creds = service_account.Credentials.from_service_account_file(
                SERVICE_ACCOUNT_FILE, scopes=SCOPES)
            service = build('drive', 'v3', credentials=creds)
            # Busca arquivos na pasta
            query = f"'{FOLDER_ID}' in parents and trashed = false"
            results = service.files().list(q=query,
                                           pageSize=200,
                                           fields="files(id, name, mimeType, createdTime, modifiedTime, size)").execute()
            files = results.get('files', [])
            if not files:
                st.info('Nenhum arquivo encontrado na pasta do Google Drive.')
            else:
                # Monta DataFrame
                df = pd.DataFrame(files)
                if not df.empty:
                    df['createdTime'] = pd.to_datetime(df['createdTime'])
                    df['modifiedTime'] = pd.to_datetime(df['modifiedTime'])
                    df['size'] = df['size'].astype(float) / 1024
                    df['size'] = df['size'].map(lambda x: f"{x:.1f} KB")
                    # Filtros
                    col1, col2 = st.columns(2)
                    with col1:
                        filtro_nome = st.text_input('Filtrar por nome do arquivo')
                    with col2:
                        filtro_tipo = st.selectbox('Filtrar por tipo', ['Todos'] + sorted(df['mimeType'].unique()))
                    df_filtrado = df.copy()
                    if filtro_nome:
                        df_filtrado = df_filtrado[df_filtrado['name'].str.contains(filtro_nome, case=False, na=False)]
                    if filtro_tipo != 'Todos':
                        df_filtrado = df_filtrado[df_filtrado['mimeType'] == filtro_tipo]
                    # Links de download/visualização
                    def make_link(row):
                        url = f"https://drive.google.com/file/d/{row['id']}/view"
                        return f"[🔗 Visualizar]({url})"
                    df_filtrado['Ação'] = df_filtrado.apply(make_link, axis=1)
                    # Exibe tabela
                    st.dataframe(df_filtrado[['name', 'mimeType', 'size', 'createdTime', 'modifiedTime', 'Ação']]
                                 .rename(columns={
                                     'name': 'Nome',
                                     'mimeType': 'Tipo',
                                     'size': 'Tamanho',
                                     'createdTime': 'Criado em',
                                     'modifiedTime': 'Modificado em',
                                 }),
                                 use_container_width=True,
                                 hide_index=True)
        except Exception as e:
            st.error(f'Erro ao acessar o Google Drive: {e}')