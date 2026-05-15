import sqlite3
import os

# NOME DO BANCO
DATABASE = 'sould.db'

def conectar():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def criar_tabelas():
    """Cria a estrutura do banco de dados do zero."""
    conn = conectar()
    c = conn.cursor()
    # Criando a tabela com a coluna link_maps para bater com o index.html
    c.execute('''CREATE TABLE IF NOT EXISTS shows (
                 id INTEGER PRIMARY KEY AUTOINCREMENT, 
                 data TEXT NOT NULL, 
                 local TEXT NOT NULL, 
                 cidade TEXT NOT NULL,
                 link_maps TEXT)''')
    conn.commit()
    conn.close()

def salvar_show(data, local, cidade, link_maps=None):
    """Insere um novo show manualmente via script se necessário."""
    conn = conectar()
    c = conn.cursor()
    c.execute("INSERT INTO shows (data, local, cidade, link_maps) VALUES (?, ?, ?, ?)", 
              (data, local, cidade, link_maps))
    conn.commit()
    conn.close()

def listar_shows():
    """Lista todos os shows cadastrados."""
    conn = conectar()
    c = conn.cursor()
    c.execute("SELECT * FROM shows ORDER BY id DESC")
    shows = c.fetchall()
    conn.close()
    return shows

if __name__ == "__main__":
    # Verifica se já existe e avisa sobre a estrutura
    if os.path.exists(DATABASE):
        print(f"Atenção: O arquivo '{DATABASE}' já existe. Se a coluna 'link_maps' estiver faltando, apague o arquivo e rode este script novamente.")
    
    criar_tabelas()
    print(f"✅ Banco de dados '{DATABASE}' alinhado e pronto para uso!")
