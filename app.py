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

# NOVO: Modelo para Controle Interno de Acessos por Data
class Acesso(db.Model):
    __tablename__ = 'acessos'
    id = db.Column(db.Integer, primary_key=True)
    data = db.Column(db.Date, unique=True, nullable=False, default=datetime.utcnow)
    quantidade = db.Column(db.Integer, nullable=False, default=1)

# Inicializa o Banco de Dados e cria as tabelas se não existirem
with app.app_context():
    db.create_all()

# Rota Principal (Site) - Registra o acesso automaticamente
@app.route('/')
def index():
    # Registrar ou incrementar o acesso do dia atual (Formato Ano-Mês-Dia)
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
        print(f"Erro ao computar acesso: {e}")

    shows_query = Show.query.order_by(Show.id).all()
    return render_template('index.html', shows=shows_query)

# Rota do Painel Administrativo (Exibe Métricas, Lista e Adiciona Shows)
@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        data = request.form.get('data')
        local = request.form.get('local')
        cidade = request.form.get('cidade')
        link_maps = request.form.get('link_maps')
        
        if data and local and cidade:
            novo_show = Show(data=data, local=local, cidade=cidade, link_maps=link_maps)
            db.session.add(novo_show)
            db.session.commit()
        return redirect(url_for('admin'))

    # Coleta de Métricas para o Painel
    todos_acessos = Acesso.query.all()
    total_acessos = sum(a.quantidade for a in todos_acessos)
    
    # Histórico ordenado pelas datas mais recentes
    historico_acessos = Acesso.query.order_by(Acesso.data.desc()).all()
    shows_query = Show.query.order_by(Show.id).all()
    
    return render_template(
        'admin.html', 
        shows=shows_query, 
        total_acessos=total_acessos, 
        historico_acessos=historico_acessos
    )

# Rota para Excluir Show pelo Painel
@app.route('/admin/excluir/<int:id>')
def excluir_show_painel(id):
    show = Show.query.get_or_404(id)
    db.session.delete(show)
    db.session.commit()
    return redirect(url_for('admin'))

# Rota de Logout Temporária
@app.route('/logout')
def logout():
    return redirect(url_for('index'))

# Rota de Galeria
@app.route('/galeria')
def galeria():
    return "<h1>Galeria de Fotos da SOULD - Em breve</h1>"

if __name__ == '__main__':
    app.run(debug=True)
