import sqlite3

# NOME DO BANCO: Deve ser EXATAMENTE igual ao definido no app.py
DATABASE = 'sould.db'

def conectar():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row  # Permite acessar colunas pelo nome
    return conn

def criar_tabelas():
    conn = conectar()
    c = conn.cursor()
    # Tabela atualizada com a coluna link_maps necessária para o index.html
    c.execute('''CREATE TABLE IF NOT EXISTS shows (
                 id INTEGER PRIMARY KEY AUTOINCREMENT, 
                 data TEXT NOT NULL, 
                 local TEXT NOT NULL, 
                 cidade TEXT NOT NULL,
                 link_maps TEXT)''')
    conn.commit()
    conn.close()

def salvar_show(data, local, cidade, link_maps=None):
    """Insere um novo show no banco de dados."""
    conn = conectar()
    c = conn.cursor()
    c.execute("INSERT INTO shows (data, local, cidade, link_maps) VALUES (?, ?, ?, ?)", 
              (data, local, cidade, link_maps))
    conn.commit()
    conn.close()

def listar_shows():
    """Retorna todos os shows ordenados por data."""
    conn = conectar()
    c = conn.cursor()
    # Retornamos todas as colunas (*) para garantir compatibilidade com Admin e Index
    c.execute("SELECT * FROM shows ORDER BY data ASC")
    shows = c.fetchall()
    conn.close()
    return shows

if __name__ == "__main__":
    criar_tabelas()
    print(f"✅ Banco de dados '{DATABASE}' alinhado e criado com sucesso!")
    
    # Exemplo de teste opcional (pode ser removido)
    # salvar_show("25/12/2026", "Rock Arena", "São José dos Campos", "https://maps.google.com")
