from flask import Flask, render_template, request, redirect, url_for, session, flash
from datetime import datetime, date
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

# SEGURANÇA: Puxa a chave secreta do Render. Se não achar, usa uma padrão apenas para teste local.
app.secret_key = os.environ.get('SECRET_KEY', 'chave_padrao_local_desenvolvimento')

# SEGURANÇA: Puxa as credenciais administrativas das variáveis de ambiente
USUARIO_ADMIN = os.environ.get('ADMIN_USER', 'sould_admin')
# Se não houver uma senha definida no Render, ele assume o hash da padrão por segurança
SENHA_PADRAO_HASH = generate_password_hash("sould2026")
SENHA_HASH = os.environ.get('ADMIN_PASSWORD_HASH', SENHA_PADRAO_HASH)

# Pega a URL do banco das variáveis de ambiente do Render
DATABASE_URL = os.environ.get('DATABASE_URL')

def obter_conexao_db():
    return psycopg2.connect(DATABASE_URL)

def inicializar_db():
    try:
        with obter_conexao_db() as conexao:
            with conexao.cursor() as cursor:
                # Cria a tabela de shows se não existir
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS shows (
                        id SERIAL PRIMARY KEY,
                        data TEXT NOT NULL,
                        local TEXT NOT NULL,
                        cidade TEXT NOT NULL,
                        link_maps TEXT
                    )
                ''')
                
                # Cria a tabela de acessos diários se não existir
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS acessos (
                        id SERIAL PRIMARY KEY,
                        data DATE UNIQUE NOT NULL,
                        quantidade INT NOT NULL DEFAULT 0
                    )
                ''')
                conexao.commit()
                
                cursor.execute('SELECT COUNT(*) FROM shows')
                if cursor.fetchone()[0] == 0:
                    cursor.execute(
                        'INSERT INTO shows (data, local, cidade, link_maps) VALUES (%s, %s, %s, %s)', 
                        ("23/05/2026", "GEORGE'S SEVEN", "SÃO JOSÉ DOS CAMPOS", "https://maps.google.com")
                    )
                    conexao.commit()
    except Exception as e:
        print(f"Erro crítico ao inicializar banco de dados: {e}")

# Executa a inicialização de tabelas de forma segura
inicializar_db()

def ordenar_shows(lista_rows):
    try:
        return sorted(lista_rows, key=lambda x: datetime.strptime(x['data'], '%d/%m/%Y'))
    except Exception:
        return lista_rows

def usuario_esta_logado():
    return 'logado' in session and session['logado'] is True

@app.route('/')
def index():
    hoje_str = date.today().isoformat()
    
    # CONTAGEM DE ACESSOS (Proteção contra F5/Duplicados usando Session)
    if 'ultimo_acesso' not in session or session['ultimo_acesso'] != hoje_str:
        try:
            with obter_conexao_db() as conexao:
                with conexao.cursor() as cursor_acesso:
                    hoje = date.today()
                    cursor_acesso.execute("""
                        INSERT INTO acessos (data, quantidade) 
                        VALUES (%s, 1) 
                        ON CONFLICT (data) 
                        DO UPDATE SET quantidade = acessos.quantidade + 1
                    """, (hoje,))
                    conexao.commit()
            session['ultimo_acesso'] = hoje_str
        except Exception as e:
            print(f"Erro ao computar acesso diário: {e}")
            
    # Busca os shows para renderizar na página inicial
    try:
        with obter_conexao_db() as conexao:
            with conexao.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute('SELECT * FROM shows')
                shows_db = cursor.fetchall()
        shows_ordenados = ordenar_shows(shows_db)
    except Exception as e:
        print(f"Erro ao buscar shows da index: {e}")
        shows_ordenados = []

    return render_template('index.html', shows=shows_ordenados)

@app.route('/links')
def links():
    hoje_str = date.today().isoformat()
    
    # Também computa acesso vindo pela árvore de links da bio
    if 'ultimo_acesso' not in session or session['ultimo_acesso'] != hoje_str:
        try:
            with obter_conexao_db() as conexao:
                with conexao.cursor() as cursor_acesso:
                    hoje = date.today()
                    cursor_acesso.execute("""
                        INSERT INTO acessos (data, quantidade) 
                        VALUES (%s, 1) 
                        ON CONFLICT (data) 
                        DO UPDATE SET quantidade = acessos.quantidade + 1
                    """, (hoje,))
                    conexao.commit()
            session['ultimo_acesso'] = hoje_str
        except Exception as e:
            print(f"Erro ao computar acesso vindo pelos links: {e}")
            
    return render_template('links.html')

@app.route('/galeria')
def galeria():
    caminho_galeria = os.path.join('static', 'img', 'galeria')
    if not os.path.exists(caminho_galeria): 
        os.makedirs(caminho_galeria)
    fotos = [f for f in os.listdir(caminho_galeria) if f.lower().endswith(('.jpg', '.png', '.jpeg', '.webp'))]
    return render_template('galeria.html', fotos=fotos)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if usuario_esta_logado(): 
        return redirect(url_for('admin'))
        
    if request.method == 'POST':
        usuario = request.form.get('usuario')
        senha = request.form.get('senha')
        
        if usuario == USUARIO_ADMIN and (check_password_hash(SENHA_HASH, senha) or senha == os.environ.get('ADMIN_PASSWORD')):
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
    if not usuario_esta_logado(): 
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        data = request.form.get('data')
        local = request.form.get('local')
        cidade = request.form.get('cidade')
        link_maps = request.form.get('link_maps') or ""
        
        if data and local and cidade:
            try:
                with obter_conexao_db() as conexao:
                    with conexao.cursor() as cursor:
                        cursor.execute(
                            'INSERT INTO shows (data, local, cidade, link_maps) VALUES (%s, %s, %s, %s)', 
                            (data, local, cidade, link_maps)
                        )
                        conexao.commit()
            except Exception as e:
                print(f"Erro ao inserir show: {e}")
            return redirect(url_for('admin'))
    
    try:
        with obter_conexao_db() as conexao:
            with conexao.cursor(cursor_factory=RealDictCursor) as cursor:
                # 1. Recupera a lista de shows
                cursor.execute('SELECT * FROM shows')
                shows_db = cursor.fetchall()
                
                # 2. Recupera a soma total de acessos
                cursor.execute('SELECT SUM(quantidade) as total FROM acessos')
                resultado_acessos = cursor.fetchone()
                total_acessos = resultado_acessos['total'] if resultado_acessos and resultado_acessos['total'] else 0
                
                # 3. Recupera o histórico diário (CORRIGIDO: quantity para quantidade)
                cursor.execute('SELECT data, quantidade FROM acessos ORDER BY data DESC')
                historico_acessos = cursor.fetchall()
    except Exception as e:
        print(f"Erro ao carregar dados do painel admin: {e}")
        shows_db, total_acessos, historico_acessos = [], 0, []

    return render_template('admin.html', shows=ordenar_shows(shows_db), show_edit=None, total_acessos=total_acessos, historico_acessos=historico_acessos)

@app.route('/editar/<int:id>')
def editar_show(id):
    if not usuario_esta_logado(): 
        return redirect(url_for('login'))
        
    try:
        with obter_conexao_db() as conexao:
            with conexao.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute('SELECT * FROM shows WHERE id = %s', (id,))
                show_para_editar = cursor.fetchone()
                
                cursor.execute('SELECT * FROM shows')
                shows_db = cursor.fetchall()
                
                cursor.execute('SELECT SUM(quantidade) as total FROM acessos')
                resultado_acessos = cursor.fetchone()
                total_acessos = resultado_acessos['total'] if resultado_acessos and resultado_acessos['total'] else 0
                
                cursor.execute('SELECT data, quantidade FROM acessos ORDER BY data DESC')
                historico_acessos = cursor.fetchall()
    except Exception as e:
        print(f"Erro ao carregar dados de edição: {e}")
        show_para_editar, shows_db, total_acessos, historico_acessos = None, [], 0, []

    return render_template('admin.html', shows=ordenar_shows(shows_db), edit_id=id, show_edit=show_para_editar, total_acessos=total_acessos, historico_acessos=historico_acessos)

@app.route('/atualizar/<int:id>', methods=['POST'])
def atualizar_show(id):
    if not usuario_esta_logado(): 
        return redirect(url_for('login'))
        
    data = request.form.get('data')
    local = request.form.get('local')
    cidade = request.form.get('cidade')
    link_maps = request.form.get('link_maps') or ""
    
    if data and local and cidade:
        try:
            with obter_conexao_db() as conexao:
                with conexao.cursor() as cursor:
                    cursor.execute(
                        'UPDATE shows SET data = %s, local = %s, cidade = %s, link_maps = %s WHERE id = %s', 
                        (data, local, cidade, link_maps, id)
                    )
                    conexao.commit()
        except Exception as e:
            print(f"Erro ao atualizar show: {e}")
            
    return redirect(url_for('admin'))

@app.route('/excluir/<int:id>')
def excluir(id):
    if not usuario_esta_logado(): 
        return redirect(url_for('login'))
        
    try:
        with obter_conexao_db() as conexao:
            with conexao.cursor() as cursor:
                cursor.execute('DELETE FROM shows WHERE id = %s', (id,))
                conexao.commit()
        flash('Show excluído com sucesso!', 'success')
    except Exception as e:
        print(f"Erro ao excluir show: {e}")
        
    return redirect(url_for('admin'))

if __name__ == '__main__':
    app.run(debug=True)
