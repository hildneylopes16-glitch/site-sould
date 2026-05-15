from flask import Flask, render_template, request, redirect, url_for, session, flash
from datetime import datetime
import os
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'sould_secret_key_2026'

# Configurações de Admin
USUARIO_ADMIN = "sould_admin"
# O hash deve ser gerado uma vez. Em produção, você usaria o hash fixo aqui.
SENHA_HASH = generate_password_hash("sould2026")
DATABASE = 'sould.db'

def obter_conexao_db():
    # Caminho absoluto para garantir que o arquivo .db não mude de lugar
    caminho_db = os.path.join(os.path.abspath(os.path.dirname(__file__)), DATABASE)
    conexao = sqlite3.connect(caminho_db)
    conexao.row_factory = sqlite3.Row
    return conexao

def inicializar_db():
    try:
        conexao = obter_conexao_db()
        cursor = conexao.cursor()
        # Cria a tabela se não existir
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS shows (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                data TEXT NOT NULL,
                local TEXT NOT NULL,
                cidade TEXT NOT NULL,
                link_maps TEXT
            )
        ''')
        conexao.commit()
        
        # Verifica se já existem shows para não inserir duplicados ou resetar a agenda
        cursor.execute('SELECT COUNT(*) FROM shows')
        if cursor.fetchone()[0] == 0:
            cursor.execute(
                'INSERT INTO shows (data, local, cidade, link_maps) VALUES (?, ?, ?, ?)',
                ("23/05/2026", "GEORGE'S SEVEN", "SÃO JOSÉ DOS CAMPOS", "https://maps.google.com")
            )
            conexao.commit()
        conexao.close()
    except Exception as e:
        print(f"Erro ao inicializar banco: {e}")

# Inicializa o banco ao rodar o app
inicializar_db()

def ordenar_shows(lista_rows):
    try:
        # Mantém a lógica de ordenação por data que você já criou
        return sorted(lista_rows, key=lambda x: datetime.strptime(x['data'], '%d/%m/%Y'))
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

@app.route('/galeria')
def galeria():
    caminho_galeria = os.path.join('static', 'img', 'galeria')
    if not os.path.exists(caminho_galeria): os.makedirs(caminho_galeria)
    fotos = [f for f in os.listdir(caminho_galeria) if f.lower().endswith(('.jpg', '.png', '.jpeg', '.webp'))]
    return render_template('galeria.html', fotos=fotos)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if usuario_esta_logado(): return redirect(url_for('admin'))
    if request.method == 'POST':
        usuario = request.form.get('usuario')
        senha = request.form.get('senha')
        if usuario == USUARIO_ADMIN and check_password_hash(SENHA_HASH, senha):
            session['logado'] = True
            session['usuario'] = usuario
            return redirect(url_for('admin'))
        flash('Usuário ou senha incorretos!', 'danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if not usuario_esta_logado(): return redirect(url_for('login'))
    conexao = obter_conexao_db()
    if request.method == 'POST':
        data = request.form.get('data')
        local = request.form.get('local')
        cidade = request.form.get('cidade')
        link_maps = request.form.get('link_maps') or ""
        
        if data and local and cidade:
            conexao.execute(
                'INSERT INTO shows (data, local, cidade, link_maps) VALUES (?, ?, ?, ?)', 
                (data, local, cidade, link_maps)
            )
            conexao.commit()
            conexao.close()
            return redirect(url_for('admin'))
    
    shows_db = conexao.execute('SELECT * FROM shows').fetchall()
    conexao.close()
    return render_template('admin.html', shows=ordenar_shows(shows_db), show_edit=None)

@app.route('/editar/<int:id>')
def editar_show(id):
    if not usuario_esta_logado(): return redirect(url_for('login'))
    conexao = obter_conexao_db()
    show_para_editar = conexao.execute('SELECT * FROM shows WHERE id = ?', (id,)).fetchone()
    shows_db = conexao.execute('SELECT * FROM shows').fetchall()
    conexao.close()
    return render_template('admin.html', shows=ordenar_shows(shows_db), edit_id=id, show_edit=show_para_editar)

@app.route('/atualizar/<int:id>', methods=['POST'])
def atualizar_show(id):
    if not usuario_esta_logado(): return redirect(url_for('login'))
    data = request.form.get('data')
    local = request.form.get('local')
    cidade = request.form.get('cidade')
    link_maps = request.form.get('link_maps') or ""
    
    if data and local and cidade:
        conexao = obter_conexao_db()
        conexao.execute(
            'UPDATE shows SET data = ?, local = ?, cidade = ?, link_maps = ? WHERE id = ?', 
            (data, local, cidade, link_maps, id)
        )
        conexao.commit()
        conexao.close()
    return redirect(url_for('admin'))

@app.route('/excluir/<int:id>')
def excluir(id):
    if not usuario_esta_logado(): return redirect(url_for('login'))
    conexao = obter_conexao_db()
    conexao.execute('DELETE FROM shows WHERE id = ?', (id,))
    conexao.commit()
    conexao.close()
    return redirect(url_for('admin'))

if __name__ == '__main__':
    # O uso de use_reloader=False pode ajudar em alguns ambientes a não duplicar a execução
    app.run(debug=True)
