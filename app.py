from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os

app = Flask(__name__)

# Configuração do Banco de Dados PostgreSQL (Render)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'postgresql://usuario:senha@localhost/sould_db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Modelo 1: Agenda de Shows
class Show(db.Model):
    __tablename__ = 'shows'
    id = db.Column(db.Integer, primary_key=True)
    data = db.Column(db.String(50), nullable=False)
    local = db.Column(db.String(100), nullable=False)
    cidade = db.Column(db.String(50), nullable=False)
    link_maps = db.Column(db.String(255), nullable=True)

# Modelo 2: Controle Interno de Acessos
class Acesso(db.Model):
    __tablename__ = 'acessos'
    id = db.Column(db.Integer, primary_key=True)
    data = db.Column(db.Date, unique=True, nullable=False, default=datetime.utcnow)
    quantidade = db.Column(db.Integer, nullable=False, default=1)

# Modelo 3: Links do Linktree
class LinkTree(db.Model):
    __tablename__ = 'linktree'
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(100), nullable=False)
    url = db.Column(db.String(255), nullable=False)

# Inicialização segura do banco de dados
with app.app_context():
    try:
        db.create_all()
    except Exception as e:
        print(f"Aviso na criação de tabelas: {e}")

# Rota 1: Página Principal do Site (Sould)
@app.route('/')
def index():
    # Bloco do contador de acessos imune a falhas
    try:
        hoje = datetime.utcnow().date()
        registro_acesso = Acesso.query.filter_by(data=hoje).first()
        if registro_acesso:
            registro_acesso.quantidade += 1
        else:
            novo_acesso = Acesso(data=hoje, quantidade=1)
            db.session.add(novo_acesso)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Erro ao registrar acesso: {e}")

    # Carrega dados das tabelas de forma segura
    shows_query = []
    links_query = []
    try:
        shows_query = Show.query.order_by(Show.id).all()
        links_query = LinkTree.query.order_by(LinkTree.id).all()
    except Exception as e:
        print(f"Erro ao ler tabelas na index: {e}")

    return render_template('index.html', shows=shows_query, links=links_query)

# Rota 2: Linktree Público (bandasould.com.br/links)
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
        return render_template('galeria.html')
    except Exception:
        return "<html><body style='background:#121212;color:white;text-align:center;padding-top:100px;font-family:sans-serif;'><h1>GALERIA SOULD</h1><p>Fotos em alta resolução sendo processadas. Em breve!</p><a href='/' style='color:red;'>Voltar ao site</a></body></html>"

# Rota 3: Painel Administrativo
@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        form_type = request.form.get('form_type')
        
        try:
            if form_type == 'show':
                data = request.form.get('data')
                local = request.form.get('local')
                cidade = request.form.get('cidade')
                link_maps = request.form.get('link_maps')
                if data and local and cidade:
                    novo_show = Show(data=data, local=local, city=cidade, link_maps=link_maps)
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

    # Coleta de métricas e listas para renderizar a página
    total_acessos = 0
    historico_acessos = []
    shows_query = []
    links_query = []

    try:
        todos_acessos = Acesso.query.all()
        total_acessos = sum(a.quantidade for a in todos_acessos)
        historico_acessos = Acesso.query.order_by(Acesso.data.desc()).all()
        shows_query = Show.query.order_by(Show.id).all()
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

# Rota 4: Excluir Show
@app.route('/admin/excluir/<int:id>')
def excluir_show_painel(id):
    try:
        show = Show.query.get_or_404(id)
        db.session.delete(show)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Erro ao excluir show: {e}")
    return redirect(url_for('admin'))

# Rota 5: Excluir Link 
@app.route('/admin/excluir-link/<int:id>')
def excluir_link_panel(id):
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
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
