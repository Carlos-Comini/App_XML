import sqlite3
import os
from typing import List

def get_empresas_usuario(usuario_id: int) -> List[str]:
    # Caminho do banco de empresas
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DB_PATH_USUARIOS = os.path.join(BASE_DIR, '..', 'usuarios.db')
    DB_PATH_EMPRESAS = os.path.join(BASE_DIR, '..', 'empresas.db')
    conn_usuarios = sqlite3.connect(DB_PATH_USUARIOS)
    cursor_usuarios = conn_usuarios.cursor()
    cursor_usuarios.execute('SELECT id_empresa FROM usuarios_empresas WHERE id_usuario=?', (usuario_id,))
    empresas_ids = [row[0] for row in cursor_usuarios.fetchall()]
    conn_usuarios.close()
    if not empresas_ids:
        return []
    # Busca razão social das empresas
    conn_empresas = sqlite3.connect(DB_PATH_EMPRESAS)
    cursor_empresas = conn_empresas.cursor()
    placeholders = ','.join(['?']*len(empresas_ids))
    cursor_empresas.execute(f'SELECT razao_social FROM empresas WHERE id IN ({placeholders})', empresas_ids)
    nomes = [row[0] for row in cursor_empresas.fetchall()]
    conn_empresas.close()
    return nomes
