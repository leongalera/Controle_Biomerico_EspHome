# app/__init__.py
from flask import Flask
from config import Config
from .models import db, AdminUser
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_apscheduler import APScheduler
from datetime import datetime
import pytz

def create_app():
    app = Flask(__name__)

    @app.template_filter('localtime')
    def localtime_filter(utc_dt):
        # Define o fuso horário de origem (UTC) e o de destino (seu local)
        utc_zone = pytz.timezone('UTC')
        local_zone = pytz.timezone('America/Sao_Paulo') # Ajuste se o seu fuso for diferente

        if utc_dt is None:
            return ""

        # Converte o horário do banco de dados (que é 'naive') para um horário 'aware' em UTC
        aware_utc_dt = utc_zone.localize(utc_dt)

        # Converte para o fuso horário local
        local_dt = aware_utc_dt.astimezone(local_zone)
        return local_dt

    app.jinja_env.add_extension('jinja2.ext.do')
    app.config.from_object(Config)

    # Inicializa o agendador
    scheduler = APScheduler()
    scheduler.init_app(app)
    scheduler.start()

    db.init_app(app)
    Migrate(app, db)

    login_manager = LoginManager()
    login_manager.login_view = 'auth.login' # Rota para a qual será redirecionado se não estiver logado
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return AdminUser.query.get(int(user_id))
    
    # Registrar comandos personalizados
    from . import commands
    app.cli.add_command(commands.create_admin)

    # Registrar Blueprints (rotas)
    from .routes.main_routes import main_bp
    from .routes.auth_routes import auth_bp
    from .routes.zone_routes import zone_bp
    from .routes.group_routes import group_bp
    from .routes.user_routes import user_bp
    from .routes.fingerprint_routes import fingerprint_bp
    from .routes.api_routes import api_bp
    from .routes.monitoring_routes import monitoring_bp
    from .routes.password_routes import password_bp

    # Registra a tarefa para rodar a cada 60 segundos
    from . import scheduler_jobs
    app.apscheduler.add_job(func=scheduler_jobs.check_schedules_and_update_ha, trigger='interval', seconds=60, id='job1')

    # Adicionaremos mais rotas aqui
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(zone_bp)
    app.register_blueprint(group_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(fingerprint_bp)
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(monitoring_bp)
    app.register_blueprint(password_bp)
    
    return app