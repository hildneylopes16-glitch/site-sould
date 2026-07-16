from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os
import re

app = Flask(__name__)

# Configurações usando variáveis de ambiente com fallbacks seguros
app.secret_key = os.environ.get('SECRET_KEY', 'chave_secreta_para_sould_banda_2026')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'postgresql://usuario:senha@localhost/sould_db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Credenciais protegidas via variáveis de ambiente
USER_ADMIN = os.environ.get('ADMIN_USER', 'admin')
PASSWORD_ADMIN = os.environ.get('ADMIN_PASSWORD', 'sould2026')

@app.route('/ping', methods=['GET'])
def ping():
    return jsonify({"status": "healthy", "timestamp": datetime.utcnow().isoformat()}), 200

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
    def criterio_ordenacao(show):
        data_match = re.search(r'(\d{2})/(\d{2})/(\d{4})', show.data)
        if data_match:
            dia, mes, ano = map(int, data_match.groups())
        else:
            return (datetime.max, 0, 0)
        
        hora = 0
        minuto = 0
        
        hora_match = re.search(r'(\d{1,2})\s*[hH]', show.data)
        if hora_match:
            hora = int(hora_match.group(1))
        else:
            hora_min_match = re.search(r'(\d{1,2}):(\d{2})', show.data)
            if hora_min_match:
                hora = int(hora_min_match.group(1))
                minuto = int(hora_min_match.group(2))
                
        return (datetime(ano, mes, dia), hora, minuto)

    try:
        return sorted(lista_shows, key=criterio_ordenacao)
    except Exception as e:
        print(f"Erro na ordenação avançada: {e}")
        return sorted(lista_shows, key=lambda x: x.id)

with app.app_context():
    try:
        db.create_all()
    except Exception as e:
        print(f"Aviso na criação de tabelas: {e}")

@app.route('/')
def index():
    shows_query = []
    links_query = []
    try:
        # Sintaxe atualizada de consulta
        shows_query = ordenar_shows(db.session.execute(db.select(Show)).scalars().all())
        links_query = db.session.execute(db.select(LinkTree).order_by(LinkTree.id)).scalars().all()
    except Exception as e:
        print(f"Erro ao ler tabelas na index: {e}")
    return render_template('index.html', shows=shows_query, links=links_query)

@app.route('/links')
def linktree_publico():
    links_query = []
    try:
        links_query = db.session.execute(db.select(LinkTree).order_by(LinkTree.id)).scalars().all()
    except Exception as e:
        print(f"Erro ao ler tabelas de links: {e}")
    return render_template('links.html', links=links_query)

@app.route('/galeria')
def galeria():
    try:
        galeria_path = os.path.join(app.static_folder, 'img', 'galeria')
        albuns = []
        
        if os.path.exists(galeria_path):
            pastas_albuns = sorted(
                [f for f in os.listdir(galeria_path) if os.path.isdir(os.path.join(galeria_path, f))],
                reverse=True
            )
            
            for pasta in pastas_albuns:
                pasta_completa = os.path.join(galeria_path, pasta)
                fotos = sorted([
                    f for f in os.listdir(pasta_completa)
                    if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp', '.gif'))
                ])
                
                if fotos:
                    nome_exibicao = pasta.replace('_', ' ')
                    foto_capa = f"img/galeria/{pasta}/{fotos[0]}"
                    lista_fotos = [f"img/galeria/{pasta}/{foto}" for foto in fotos]
                    
                    albuns.append({
                        'pasta': pasta,
                        'nome': nome_exibicao,
                        'capa': foto_capa,
                        'fotos': lista_fotos,
                        'total_fotos': len(fotos)
                    })
                    
        return render_template('galeria.html', albuns=albuns)
    except Exception as e:
        print(f"Erro crítico na rota galeria: {e}")
        return "<html><body style='background:#121212;color:white;text-align:center;padding-top:100px;'><h1>GALERIA SOULD</h1><p>Erro ao processar mídias.</p></body></html>"

@app.route('/login', methods=['POST'])
def login():
    """Rota isolada para processar a autenticação de forma organizada"""
    username = request.form.get('username')
    password = request.form.get('password')
    if username == USER_ADMIN and password == PASSWORD_ADMIN:
        session['logado'] = True
    return redirect(url_for('admin'))

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    # Se não estiver logado e for GET, renderiza a tela de login (sem dados confidenciais)
    if not session.get('logado'):
        if request.method == 'POST' and request.form.get('form_type') == 'login':
            # Caso tente logar pelo form da própria página
            username = request.form.get('username')
            password = request.form.get('password')
            if username == USER_ADMIN and password == PASSWORD_ADMIN:
                session['logado'] = True
                return redirect(url_for('admin'))
        return render_template('admin_login.html') # Crie um template simples de login, ou renderize o admin normal ocultando o painel.

    # Usuário autenticado: processa cadastros de novos itens (POST)
    if request.method == 'POST':
        form_type = request.form.get('form_type')
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
            print(f"Erro crítico ao salvar no banco: {e}")
        return redirect(url_for('admin'))

    # Se for GET e estiver logado, exibe o painel completo de controle
    shows_query = []
    links_query = []
    try:
        shows_query = ordenar_shows(db.session.execute(db.select(Show)).scalars().all())
        links_query = db.session.execute(db.select(LinkTree).order_by(LinkTree.id)).scalars().all()
    except Exception as e:
        print(f"Erro ao coletar dados para o admin: {e}")
    
    return render_template(
        'admin.html', 
        shows=shows_query, 
        links=links_query,
        total_acessos=0, 
        historico_acessos=[]
    )

@app.route('/admin/editar/<int:id>', methods=['GET', 'POST'])
def editar_show(id):
    if not session.get('logado'):
        return redirect(url_for('admin'))
    
    # Atualizado para compatibilidade moderna com SQLAlchemy
    show = db.get_or_404(Show, id)
    
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
        show = db.get_or_404(Show, id)
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
        link = db.get_or_404(LinkTree, id)
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
