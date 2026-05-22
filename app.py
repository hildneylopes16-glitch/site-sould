from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os

app = Flask(__name__)

# Configuração do Banco de Dados PostgreSQL (Render)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'postgresql://usuario:senha@localhost/sould_db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Modelo para a Agenda de Shows
class Show(db.Model):
    __tablename__ = 'shows'
    id = db.Column(db.Integer, primary_key=True)
    data = db.Column(db.String(50), nullable=False)
    local = db.Column(db.String(100), nullable=False)
    cidade = db.Column(db.String(50), nullable=False)
    link_maps = db.Column(db.String(255), nullable=True)

# Modelo para Controle Interno de Acessos
class Acesso(db.Model):
    __tablename__ = 'acessos'
    id = db.Column(db.Integer, primary_key=True)
    data = db.Column(db.Date, unique=True, nullable=False, default=datetime.utcnow)
    quantidade = db.Column(db.Integer, nullable=False, default=1)

# Modelo para os Links do estilo Linktree
class LinkTree(db.Model):
    __tablename__ = 'linktree'
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(100), nullable=False)  # Ex: "Instagram Oficial"
    url = db.Column(db.String(255), nullable=False)     # Ex: "https://instagram.com/..."

# Inicializa o Banco de Dados e garante a criação das tabelas
with app.app_context():
    db.create_all()

# Rota Principal (Site)
@app.route('/')
def index():
    # Computar acesso do dia
    hoje = datetime.utcnow().date()
    registro_acesso = Acesso.query.filter_by(data=hoje).first()
    if registro_acesso:
        registro_acesso.quantidade += 1
    else:
        novo_acesso = Acesso(data=hoje, quantidade=1)
        db.session.add(novo_acesso)
    
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()

    shows_query = Show.query.order_by(Show.id).all()
    links_query = LinkTree.query.order_by(LinkTree.id).all()
    return render_template('index.html', shows=shows_query, links=links_query)


# =======================================================
# NOVA ROTA: Página estilo Linktree pública para os fãs
# =======================================================
@app.route('/links')
def linktree_publico():
    # Busca todos os links rápidos cadastrados no banco de dados
    links_query = LinkTree.query.order_by(LinkTree.id).all()
    # Renderiza o template visual dos botões (Certifique-se de ter o links.html ou use este nome)
    return render_template('links.html', links=links_query)


# Rota do Painel Administrativo
@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        form_type = request.form.get('form_type')
        
        if form_type == 'show':
            data = request.form.get('data')
            local = request.form.get('local')
            cidade = request.form.get('cidade')
            link_maps = request.form.get('link_maps')
            # Correção feita aqui: alterado de 'city' para 'cidade'
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
                
        return redirect(url_for('admin'))

    # Coleta de dados para renderizar o painel
    todos_acessos = Acesso.query.all()
    total_acessos = sum(a.quantidade for a in todos_acessos)
    historico_acessos = Acesso.query.order_by(Acesso.data.desc()).all()
    
    shows_query = Show.query.order_by(Show.id).all()
    links_query = LinkTree.query.order_by(LinkTree.id).all()
    
    return render_template(
        'admin.html', 
        shows=shows_query, 
        links=links_query,
        total_acessos=total_acessos, 
        historico_acessos=historico_acessos
    )

# Rota para Excluir Show
@app.route('/admin/excluir/<int:id>')
def excluir_show_painel(id):
    show = Show.query.get_or_404(id)
    db.session.delete(show)
    db.session.commit()
    return redirect(url_for('admin'))

# Rota para Excluir Link do Linktree
@app.route('/admin/excluir-link/<int:id>')
def excluir_link_painel(id):
    link = LinkTree.query.get_or_404(id)
    db.session.delete(link)
    db.session.commit()
    return redirect(url_for('admin'))

@app.route('/logout')
def logout():
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
