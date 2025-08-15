# Cria tabela de associação N para N entre usuários e empresas
def criar_tabela_usuarios_empresas():
    import os
    import sqlite3
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DB_PATH = os.path.join(BASE_DIR, '..', 'usuarios.db')
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios_empresas (
            id_usuario INTEGER,
            id_empresa INTEGER,
            PRIMARY KEY (id_usuario, id_empresa)
        )
    ''')
    conn.commit()
    conn.close()
import sqlite3
import os
from typing import Optional, Dict

# Caminho absoluto do banco na raiz do projeto
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, '..', 'usuarios.db')

def conectar():
    conn = sqlite3.connect(DB_PATH)
    conn.execute('''CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        email TEXT NOT NULL,
        senha TEXT NOT NULL,
        tipo TEXT NOT NULL,
        empresa TEXT,
        cadastrar TEXT,
        ver_arquivo TEXT,
        ver_xml TEXT
    )''')
    return conn
def inserir_usuario(nome, email, senha, tipo, empresa=None, permissoes=None):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute('SELECT 1 FROM usuarios WHERE email=?', (email,))
    if cursor.fetchone():
        conn.close()
        return False  # Usuário já existe
    cadastrar = 'Sim' if permissoes and permissoes.get('cadastrar') else 'Não'
    ver_arquivo = 'Sim' if permissoes and permissoes.get('ver_arquivo') else 'Não'
    ver_xml = 'Sim' if permissoes and permissoes.get('ver_xml') else 'Não'
    cursor.execute('''INSERT INTO usuarios (nome, email, senha, tipo, empresa, cadastrar, ver_arquivo, ver_xml)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
        (nome, email, senha, tipo, empresa, cadastrar, ver_arquivo, ver_xml)
    )
    conn.commit()
    conn.close()
    return True

def autenticar(email: str, senha: str) -> Optional[Dict]:
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM usuarios WHERE email=? AND senha=?
    """, (email, senha))
    row = cursor.fetchone()
    conn.close()
    if row:
        colunas = [desc[0] for desc in cursor.description]
        return dict(zip(colunas, row))
    return None

def buscar_por_id(user_id: int) -> Optional[Dict]:
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM usuarios WHERE id=?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        colunas = [desc[0] for desc in cursor.description]
        return dict(zip(colunas, row))
    return None

def listar_usuarios() -> list:
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM usuarios")
    rows = cursor.fetchall()
    colunas = [desc[0] for desc in cursor.description]
    conn.close()
    return [dict(zip(colunas, row)) for row in rows]

def registrar_usuario_padrao():
    # Registra o usuário ELIANE se não existir
    conn = conectar()
    cursor = conn.cursor()
    email = "eliane@alencarassociados.com.br"
    cursor.execute('SELECT 1 FROM usuarios WHERE email=?', (email,))
    if not cursor.fetchone():
        cursor.execute('''INSERT INTO usuarios (nome, email, senha, tipo, empresa, cadastrar, ver_arquivo, ver_xml)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
            ("ELIANE", email, "8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92", "Escritorio", None, "Sim", "Sim", "Sim")
        )
        conn.commit()
    conn.close()
