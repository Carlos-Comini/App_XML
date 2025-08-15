import sqlite3

DB_PATH = 'usuarios.db'

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()
# Cria a tabela se não existir
cursor.execute('''
	CREATE TABLE IF NOT EXISTS documentos (
		id INTEGER PRIMARY KEY AUTOINCREMENT,
		nome TEXT,
		caminho TEXT,
		empresa TEXT,
		cnpj TEXT,
		banco TEXT,
		ano TEXT,
		mes TEXT,
		tipo TEXT,
		data_upload TEXT
	)
''')
def add_column(colname, coltype, default):
	try:
		cursor.execute(f"ALTER TABLE documentos ADD COLUMN {colname} {coltype} DEFAULT '{default}';")
		print(f'Coluna {colname} adicionada com sucesso!')
	except sqlite3.OperationalError as e:
		if 'duplicate column name' in str(e):
			print(f'Coluna {colname} já existe.')
		else:
			print(f'Erro ao adicionar coluna {colname}:', e)

add_column('tipo_nota', 'TEXT', 'Desconhecido')
add_column('usuario', 'TEXT', 'N/A')
add_column('razao_social_usuario', 'TEXT', 'N/A')
conn.commit()
conn.close()
