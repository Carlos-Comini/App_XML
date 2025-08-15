import sqlite3

conn = sqlite3.connect('usuarios.db')
c = conn.cursor()
c.execute("UPDATE usuarios SET Permitir_Cadastros = 'Sim', Ver_Arquivos = 'Sim', Ver_XML = 'Sim' WHERE email = 'admin@app.com'")
conn.commit()
conn.close()
print('Permissões do admin atualizadas com sucesso!')
