from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
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

    def to_dict(self):
        return {
            "id": self.id,
            "data": self.data,
            "local": self.local,
            "cidade": self.cidade,
            "link_maps": self.link_maps
        }

# Inicializa o Banco de Dados
with app.app_context():
    db.create_all()

# Rota Principal (Site)
@app.route('/')
def index():
    shows_query = Show.query.order_by(Show.id).all()
    return render_template('index.html', shows=shows_query)

# Rota do Painel Administrativo (Listar e Adicionar Novo)
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

    shows_query = Show.query.order_by(Show.id).all()
    return render_template('admin.html', shows=shows_query)

# Rota para Excluir Show pelo Painel
@app.route('/admin/excluir/<int:id>')
def excluir_show_painel(id):
    show = Show.query.get_or_404(id)
    db.session.delete(show)
    db.session.commit()
    return redirect(url_for('admin'))

# Rota de Logout Temporária (para não quebrar o botão do HTML)
@app.route('/logout')
def logout():
    return redirect(url_for('index'))

# Rota de Galeria
@app.route('/galeria')
def galeria():
    return "<h1>Galeria de Fotos da SOULD - Em breve</h1>"

# --- API ENDPOINTS (Para integrações futuras se necessário) ---
@app.route('/api/shows', methods=['GET'])
def get_shows():
    shows = Show.query.all()
    return jsonify([show.to_dict() for show in shows])

@app.route('/api/shows/<int:id>', methods=['DELETE'])
def delete_show(id):
    show = Show.query.get_or_404(id)
    db.session.delete(show)
    db.session.commit()
    return jsonify({"success": True, "message": "Show removido"})

if __name__ == '__main__':
    app.run(debug=True)
