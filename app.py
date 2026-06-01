from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os

app = Flask(__name__)

app.secret_key = os.environ.get('SECRET_KEY', 'chave_secreta_para_sould_banda_2026')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'postgresql://usuario:senha@localhost/sould_db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

USER_ADMIN = "admin"
PASSWORD_ADMIN = "sould2026"

# =================================================================
# NOVA ROTA: Rota de Ping para o UptimeRobot ou Scripts Externos
# =================================================================
@app.route('/ping', methods=['GET'])
def ping():
    # Retorna uma resposta rápida sem computar acesso ou tocar no banco
    return jsonify({"status": "healthy", "timestamp": datetime.utcnow().isoformat()}), 200

# --- Seus Modelos permanecem iguais (Tabela Acesso Removida para Economia) ---
class Show(db.Model):
    __tablename__ = 'shows'
    id = db.Column(db.Integer, primary_key=True)
    data = db.Column(db.String(50), nullable=False)
    local = db.Column(db.String(100), nullable=False)
    cidade = db.Column(db.String(50), nullable=False)
    link_maps = db.Column(db.String(255), nullable=True)

class LinkTree(db.Model):
    __tablename__ = 'linktree'
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(100), nullable=False)
    url = db.Column(db.String(255), nullable=False)

def ordenar_shows(lista_shows):
    try:
        return sorted(lista_shows, key=lambda x: datetime.strptime(x.data, '%d/%m/%Y'))
    except Exception:
        return sorted(lista_shows, key=lambda x: x.id)

# =================================================================
# COMANDO FORÇADO DE LIMPEZA INTERNA (Evita bloqueios externos do Render)
# =================================================================
with app.app_context():
    try:
        # Executa o comando de dentro da infraestrutura antes de levantar o site
        db.session.execute(db.text("DROP TABLE IF EXISTS acessos CASCADE;"))
        db.session.commit()
        print("SUCESSO: Tabela de acessos deletada com sucesso!")
        
        # Recria as tabelas oficiais (shows e linktree) se necessário
        db.create_all()
    except Exception as e:
        db.session.rollback()
        print(f"Aviso/Erro na inicialização ou limpeza: {e}")

# Rota 1: Página Principal (ATUALIZADA: SEM GRAVAÇÃO PESADA NO BANCO)
@app.route('/')
def index():
    shows_query = []
    links_query = []
    try:
        shows_query = ordenar_shows(Show.query.all())
        links_query = LinkTree.query.order_by(LinkTree.id).all()
    except Exception as e:
        print(f"Erro ao ler tabelas na index: {e}")

    return render_template('index.html', shows=shows_query, links=links_query)

# Rota 2: Linktree Público
@app.route('/links')
def linktree_publico():
    links_query = []
    try:
        links_query = LinkTree.query.order_by(LinkTree.id).all()
    except Exception as e:
        print(f"Erro ao ler tabelas de links: {e}")
    return render_template('links.html', links=links_query)

# Rota Nova: Galeria de Fotos
@app.route('/galeria')
def galeria():
    try:
        pasta_galeria = os.path.join(app.static_folder, 'img', 'galeria')
        fotos = []
        if os.path.exists(pasta_galeria):
            fotos = [f for f in os.listdir(pasta_galeria) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp', '.gif'))]
            fotos.sort()
        return render_template('galeria.html', fotos=fotos)
    except Exception as e:
        print(f"Erro crítico na rota galeria: {e}")
        return "<html><body style='background:#121212;color:white;text-align:center;padding-top:100px;'><h1>GALERIA SOULD</h1><p>Erro ao processar mídias.</p></body></html>"

# Rota 3: Painel Administrativo
@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        form_type = request.form.get('form_type')
        if form_type == 'login':
            username = request.form.get('username')
            password = request.form.get('password')
            if username == USER_ADMIN and password == PASSWORD_ADMIN:
                session['logado'] = True
            return redirect(url_for('admin'))
            
        if session.get('logado'):
            try:
                if form_type == 'show':
                    data = request.form.get('data')
                    local = request.form.get('local')
                    cidade = request.form.get('cidade')
                    link_maps = request.form.get('link_maps')
                    if data and local and cidade:
                        novo_show = Show(data=data, local=local, cidade=cidade, link_maps=link_maps)
                        db.session.add(novo_show)
                        db.session.commit()
                elif form_type == 'linktree':
                    titulo = request.form.get('titulo')
                    url = request.form.get('url')
                    if titulo and url:
                        novo_link = LinkTree(titulo=titulo, url=url)
                        db.session.add(novo_link)
                        db.session.commit()
            except Exception as e:
                db.session.rollback()
                print(f"Erro ao salvar dados pelo painel: {e}")
        return redirect(url_for('admin'))

    shows_query = []
    links_query = []
    
    if session.get('logado'):
        try:
            shows_query = ordenar_shows(Show.query.all())
            links_query = LinkTree.query.order_by(LinkTree.id).all()
        except Exception as e:
            print(f"Erro ao coletar dados para o admin: {e}")
    
    return render_template(
        'admin.html', 
        shows
