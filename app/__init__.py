import os
from flask import Flask
from dotenv import load_dotenv
from .models import db

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

def create_app():
    app = Flask(__name__)
    
    # Configurações da aplicação
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'default-secret-key')
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///../instance/controle_acesso.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Inicializa o banco de dados
    db.init_app(app)

    # Importa e registra as rotas
    from . import routes
    app.register_blueprint(routes.bp)

    with app.app_context():
        db.create_all() # Cria as tabelas do banco de dados se não existirem

    return app