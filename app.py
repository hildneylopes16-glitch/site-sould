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

# --- Seus Modelos permanecem iguais ---
class Show(db.Model):
    __tablename__ = 'shows'
    id = db.Column(db.Integer, primary_key=True)
    data = db.Column(db.String(50), nullable=False)
    local = db.Column(db.String(100), nullable=False)
    cidade = db.Column(db.String(50), nullable=False)
    link_maps = db.Column(db.String(255), nullable=True)

class Acesso(db.Model):
    __tablename__ = 'acessos'
    id = db.Column(db.Integer, primary_key=True)
    data = db.Column(db.Date, unique=True, nullable=False, default=datetime.utcnow)
    quantidade = db.Column(db.Integer, nullable=False, default=1)

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

with app.app_context():
    try:
        db.create_all()
    except Exception as e:
        print(f"Aviso na criação de tabelas: {e}")

# Rota 1: Página Principal
@app.route('/')
def index():
    try:
        hoje_str = datetime.utcnow().strftime('%Y-%m-%d')
        if session.get('ultimo_acesso') != hoje_str:
            hoje = datetime.utcnow().date()
            registro_acesso = Acesso.query.filter_by(data=hoje).first()
            if registro_acesso:
                registro_acesso.quantidade += 1
            else:
                novo_acesso = Acesso(data=hoje, quantity=1)
                db.session.add(novo_acesso)
            db.session.commit()
            session['ultimo_acesso'] = hoje_str
    except Exception as e:
        db.session.rollback()
        print(f"Erro ao registrar acesso: {e}")

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
                    if data and local and city:
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

    total_acessos = 0
    historico_acessos = []
    shows_query = []
    links_query = []
    
    if session.get('logado'):
        try:
            todos_acessos = Acesso.query.all()
            total_acessos = sum(a.quantidade for a in todos_acessos)
            historico_acessos = Acesso.query.order_by(Acesso.data.desc()).all()
            shows_query = ordenar_shows(Show.query.all())
            links_query = LinkTree.query.order_by(LinkTree.id).all()
        except Exception as e:
            print(f"Erro ao coletar dados para o admin: {e}")
    
    return render_template(
        'admin.html', 
        shows=shows_query, 
        links=links_query,
        total_acessos=total_acessos, 
        historico_acessos=historico_acessos
    )

@app.route('/admin/editar/<int:id>', methods=['GET', 'POST'])
def editar_show(id):
    if not session.get('logado'):
        return redirect(url_for('admin'))
    show = Show.query.get_or_404(id)
    if request.method == 'POST':
        try:
            show.data = request.form.get('data')
            show.local = request.form.get('local')
            show.cidade = request.form.get('cidade')
            show.link_maps = request.form.get('link_maps')
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(f"Erro ao editar show: {e}")
        return redirect(url_for('admin'))
    return render_template('editar.html', show=show)

@app.route('/admin/excluir/<int:id>')
def excluir_show_painel(id):
    if not session.get('logado'):
        return redirect(url_for('admin'))
    try:
        show = Show.query.get_or_404(id)
        db.session.delete(show)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Erro ao excluir show: {e}")
    return redirect(url_for('admin'))

@app.route('/admin/excluir-link/<int:id>')
def excluir_link_panel(id):
    if not session.get('logado'):
        return redirect(url_for('admin'))
    try:
        link = LinkTree.query.get_or_404(id)
        db.session.delete(link)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Erro ao excluir link: {e}")
    return redirect(url_for('admin'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('admin'))

if __name__ == '__main__':
    app.run(debug=True)
