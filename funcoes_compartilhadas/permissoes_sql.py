import sqlite3
from typing import Optional, Dict, List

DB_PATH = 'usuarios.db'

def conectar():
    return sqlite3.connect(DB_PATH)

def buscar_permissoes_usuario(id_usuario: int) -> List[Dict]:
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM permissoes WHERE id_usuario=?", (id_usuario,))
    rows = cursor.fetchall()
    colunas = [desc[0] for desc in cursor.description]
    conn.close()
    return [dict(zip(colunas, row)) for row in rows]

def adicionar_permissao(id_usuario: int, id_funcionalidade: int):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO permissoes (id_usuario, id_funcionalidade) VALUES (?, ?)", (id_usuario, id_funcionalidade))
    conn.commit()
    conn.close()
