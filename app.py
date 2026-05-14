from flask import Flask, render_template, request, redirect, url_for, session, flash
from datetime import datetime
import os
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

# CHAVE SECRETA
app.secret_key = 'sould_secret_key_2026'

# CONFIGURAÇÃO DE LOGIN
USUARIO_ADMIN = "sould_admin"
SENHA_HASH = generate_password_hash("sould2026")

DATABASE = 'sould.db'

def obter_conexao_db():
    conexao = sqlite3.connect(DATABASE)
    conexao.row_factory = sqlite3.Row
    return conexao

def inicializar_db():
    conexao = obter_conexao_db()
    cursor = conexao.cursor()
    
    # Cria a tabela se não existir
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS shows (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data TEXT NOT NULL,
            local TEXT NOT NULL,
            cidade TEXT NOT NULL,
            endereco TEXT
        )
    ''')
    
    # ATUALIZAÇÃO AUTOMÁTICA: Adiciona a coluna endereco se ela não existir em bancos antigos
    try:
        cursor.execute('ALTER TABLE shows ADD COLUMN endereco TEXT')
    except sqlite3.OperationalError:
        pass # A coluna já existe
        
    conexao.commit()
    
    cursor.execute('SELECT COUNT(*) FROM shows')
    if cursor.fetchone()[0] == 0:
        cursor.execute(
            'INSERT INTO shows (data, local, cidade, endereco) VALUES (?, ?, ?, ?)',
            ("23/05/2026", "GEOGER'S SEVEN", "SÃO JOSÉ DOS CAMPOS", "Rua General Osório, 123, Centro, São José dos Campos - SP")
        )
        conexao.commit()
    
    conexao.close()

inicializar_db()

def ordenar_shows(lista_rows):
    try:
        return sorted(
            lista_rows, 
            key=lambda x: datetime.strptime(x['data'], '%d/%m/%Y') if len(x['data']) > 5 else datetime.strptime(x['data'] + '/2026', '%d/%m/%Y')
        )
    except Exception:
        return lista_rows

def usuario_esta_logado():
    return 'logado' in session and session['logado'] == True

@app.route('/')
def index():
    conexao = obter_conexao_db()
    shows_db = conexao.execute('SELECT * FROM shows').fetchall()
    conexao.close()
    shows_ordenados = ordenar_shows(shows_db)
    return render_template('index.html', shows=shows_ordenados)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if usuario_esta_logado():
        return redirect(url_for('admin'))
    if request.method == 'POST':
        usuario = request.form.get('usuario')
        senha = request.form.get('senha')
        if usuario == USUARIO_ADMIN and check_password_hash(SENHA_HASH, senha):
            session['logado'] = True
            session['usuario'] = usuario
            return redirect(url_for('admin'))
        else:
            flash('Usuário ou senha incorretos!', 'danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if not usuario_esta_logado():
        return redirect(url_for('login'))
    conexao = obter_conexao_db()
    if request.method == 'POST':
        data = request.form.get('data')
        local = request.form.get('local')
        cidade = request.form.get('cidade')
        endereco = request.form.get('endereco')
        if data and local and cidade:
            conexao.execute(
                'INSERT INTO shows (data, local, cidade, endereco) VALUES (?, ?, ?, ?)',
                (data, local, cidade, endereco)
            )
            conexao.commit()
        conexao.close()
        return redirect(url_for('admin'))
    shows_db = conexao.execute('SELECT * FROM shows').fetchall()
    conexao.close()
    shows_ordenados = ordenar_shows(shows_db)
    return render_template('admin.html', shows=shows_ordenados, show_edit=None)

@app.route('/editar/<int:id>')
def editar_show(id):
    if not usuario_esta_logado():
        return redirect(url_for('login'))
    conexao = obter_conexao_db()
    show_para_editar = conexao.execute('SELECT * FROM shows WHERE id = ?', (id,)).fetchone()
    shows_db = conexao.execute('SELECT * FROM shows').fetchall()
    conexao.close()
    shows_ordenados = ordenar_shows(shows_db)
    return render_template('admin.html', shows=shows_ordenados, edit_id=id, show_edit=show_para_editar)

@app.route('/atualizar/<int:id>', methods=['POST'])
def atualizar_show(id):
    if not usuario_esta_logado():
        return redirect(url_for('login'))
    data = request.form.get('data')
    local = request.form.get('local')
    cidade = request.form.get('cidade')
    endereco = request.form.get('endereco')
    if data and local and cidade:
        conexao = obter_conexao_db()
        conexao.execute(
            'UPDATE shows SET data = ?, local = ?, cidade = ?, endereco = ? WHERE id = ?',
            (data, local, cidade, endereco, id)
        )
        conexao.commit()
        conexao.close()
    return redirect(url_for('admin'))

@app.route('/excluir/<int:id>')
def excluir(id):
    if not usuario_esta_logado():
        return redirect(url_for('login'))
    conexao = obter_conexao_db()
    conexao.execute('DELETE FROM shows WHERE id = ?', (id,))
    conexao.commit()
    conexao.close()
    return redirect(url_for('admin'))

if __name__ == '__main__':
    app.run(debug=True)
