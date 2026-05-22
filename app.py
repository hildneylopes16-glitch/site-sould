from flask import Flask, render_template, request, jsonify
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
    # Busca todos os shows ordenados por id
    shows_query = Show.query.order_by(Show.id).all()
    return render_template('index.html', shows=shows_query)

# Rota do Painel Administrativo
@app.route('/admin')
def admin():
    # Busca os shows para listar no painel caso o admin.html precise deles via Jinja2
    shows_query = Show.query.order_by(Show.id).all()
    return render_template('admin.html', shows=shows_query)

# Rota de Galeria (Se houver)
@app.route('/galeria')
def galeria():
    return "<h1>Galeria de Fotos da SOULD - Em breve</h1>"

# --- API ENDPOINTS PARA GERENCIAR A AGENDA ---

@app.route('/api/shows', methods=['GET'])
def get_shows():
    shows = Show.query.all()
    return jsonify([show.to_dict() for show in shows])

@app.route('/api/shows', methods=['POST'])
def add_show():
    data = request.json
    if not data or not all(k in data for k in ('data', 'local', 'cidade')):
        return jsonify({"error": "Dados incompletos"}), 400
    
    novo_show = Show(
        data=data['data'],
        local=data['local'],
        cidade=data['cidade'],
        link_maps=data.get('link_maps')
    )
    db.session.add(novo_show)
    db.session.commit()
    return jsonify({"success": True, "show": novo_show.to_dict()}), 201

@app.route('/api/shows/<int:id>', methods=['DELETE'])
def delete_show(id):
    show = Show.query.get_or_404(id)
    db.session.delete(show)
    db.session.commit()
    return jsonify({"success": True, "message": "Show removido com sucesso"})

if __name__ == '__main__':
    app.run(debug=True)
