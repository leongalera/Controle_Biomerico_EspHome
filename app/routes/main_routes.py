# app/routes/main_routes.py
from flask import Blueprint, render_template
from flask_login import login_required
from app.models import User, Zone, AccessGroup, Password, AccessLog, PasswordLog
from sqlalchemy import func

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
@login_required
def index():
    # --- 1. Contagens Totais para os Cards ---
    user_count = User.query.count()
    zones = Zone.query.order_by(Zone.name).all()
    zone_count = len(zones)
    group_count = AccessGroup.query.count()
    password_count = Password.query.count()

    # --- 2. Dados para o Gráfico de Acessos ---
    # Conta todos os acessos autorizados (de digitais e senhas válidas)
    authorized_bio = AccessLog.query.filter_by(result='Autorizado').count()
    authorized_pass = PasswordLog.query.filter_by(result='Válida').count()
    total_authorized = authorized_bio + authorized_pass

    # Conta todos os acessos negados
    denied_bio = AccessLog.query.filter(AccessLog.result != 'Autorizado').count()
    denied_pass = PasswordLog.query.filter(PasswordLog.result != 'Válida').count()
    total_denied = denied_bio + denied_pass

    # Prepara os dados para o JavaScript do gráfico
    access_chart_data = {
        'labels': ['Autorizados', 'Negados'],
        'data': [total_authorized, total_denied],
    }

    # --- 3. Lista de Logs Recentes ---
    # Busca os 5 logs mais recentes de cada tipo
    recent_bio_logs = AccessLog.query.order_by(AccessLog.timestamp.desc()).limit(5).all()
    recent_pass_logs = PasswordLog.query.order_by(PasswordLog.timestamp.desc()).limit(5).all()

    # Combina as duas listas e as reordena pelo timestamp
    # Adicionamos um atributo 'type' para diferenciá-los no template
    for log in recent_bio_logs: log.type = 'biometria'
    for log in recent_pass_logs: log.type = 'senha'

    recent_logs = sorted(
        recent_bio_logs + recent_pass_logs,
        key=lambda x: x.timestamp,
        reverse=True
    )[:8] # Pega os 8 mais recentes da lista combinada

    # Passa todos os dados para o template
    return render_template(
        'index.html',
        user_count=user_count,
        zone_count=zone_count,
        group_count=group_count,
        password_count=password_count,
        access_chart_data=access_chart_data,
        recent_logs=recent_logs,
        zones=zones
    )