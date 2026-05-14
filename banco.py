import sqlite3

def conectar():
    return sqlite3.connect('sould_banda.db')

def criar_tabelas():
    conn = conectar()
    c = conn.cursor()
    # Tabela para agenda de shows
    c.execute('''CREATE TABLE IF NOT EXISTS shows (
                 id INTEGER PRIMARY KEY AUTOINCREMENT, 
                 data TEXT, 
                 local TEXT, 
                 cidade TEXT)''')
    conn.commit()
    conn.close()

if __name__ == "__main__":
    criar_tabelas()
    print("✅ Banco da banda criado com sucesso!")

# Adicione isso ao final do seu banco.py

def salvar_show(data, local, cidade):
    conn = conectar()
    c = conn.cursor()
    c.execute("INSERT INTO shows (data, local, cidade) VALUES (?, ?, ?)", (data, local, cidade))
    conn.commit()
    conn.close()

def listar_shows():
    conn = conectar()
    c = conn.cursor()
    c.execute("SELECT data, local, cidade FROM shows ORDER BY data ASC")
    shows = c.fetchall()
    conn.close()
    return shows
