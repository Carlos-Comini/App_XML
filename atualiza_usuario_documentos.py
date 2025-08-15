import sqlite3

DB_PATH = 'usuarios.db'
USUARIO_PADRAO = 'Admin'
RAZAO_PADRAO = 'N/A'

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()
cursor.execute("UPDATE documentos SET usuario = ?, razao_social_usuario = ? WHERE usuario IS NULL OR usuario = 'N/A'", (USUARIO_PADRAO, RAZAO_PADRAO))
conn.commit()
conn.close()
print('Registros antigos atualizados com usuário padrão!')
