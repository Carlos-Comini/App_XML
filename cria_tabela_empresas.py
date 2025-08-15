from funcoes_compartilhadas.empresas_sql import criar_tabela_empresas

if __name__ == "__main__":
    criar_tabela_empresas()
    print("Tabela 'empresas' criada (ou já existia) em empresas.db na raiz do projeto.")
