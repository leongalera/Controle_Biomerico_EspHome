# app/routes/main_routes.py
from flask import Blueprint, render_template
from flask_login import login_required
from app.models import db, User, Zone, AccessGroup, Password, AccessLog, PasswordLog
from sqlalchemy import func
from datetime import date, timedelta, datetime
from sqlalchemy import func, extract
from collections import Counter

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
@login_required
def index():
    # --- 1. KPIs da Linha Superior (Configuração) ---
    user_count = User.query.count()
    zone_count = Zone.query.count()
    group_count = AccessGroup.query.count()
    password_count = Password.query.count()

    # --- 2. KPIs da Segunda Linha (Atividade Recente) ---
    today_start = date.today()
    now = datetime.utcnow()
    first_day_of_month = now.replace(day=1)

    accesses_today = AccessLog.query.filter(AccessLog.timestamp >= today_start).count()
    failures_today = PasswordLog.query.filter(PasswordLog.timestamp >= today_start, PasswordLog.result != 'Válida').count() + \
                     AccessLog.query.filter(AccessLog.timestamp >= today_start, AccessLog.result != 'Autorizado').count()

    accesses_this_month = AccessLog.query.filter(AccessLog.timestamp >= first_day_of_month).count()
    
    top_user_query = db.session.query(
        User.name, func.count(AccessLog.id).label('access_count')
    ).join(User).filter(AccessLog.timestamp >= first_day_of_month).group_by(User.name).order_by(func.count(AccessLog.id).desc()).first()
    most_active_user = top_user_query[0] if top_user_query else "N/A"

    # --- 3. Dados para o Gráfico de Linha (Últimos 7 Dias) ---
    seven_days_ago = now - timedelta(days=7)
    accesses_last_7_days = db.session.query(
        func.date(AccessLog.timestamp), func.count(AccessLog.id)
    ).filter(AccessLog.timestamp >= seven_days_ago).group_by(func.date(AccessLog.timestamp)).all()
    
    labels = [(now - timedelta(days=i)).strftime('%d/%m') for i in range(6, -1, -1)]
    
    # --- A CORREÇÃO ESTÁ AQUI ---
    data_points = {day: 0 for day in labels} # Usamos 'day' diretamente
    
    for day_str, count in accesses_last_7_days:
        day_formatted = datetime.strptime(day_str, '%Y-%m-%d').strftime('%d/%m')
        if day_formatted in data_points:
            data_points[day_formatted] = count
    line_chart_data = {'labels': labels, 'data': list(data_points.values())}

    # --- 4. Dados para o Gráfico de Pizza (Acessos por Zona) ---
    access_by_zone = db.session.query(
        AccessLog.zone_name, func.count(AccessLog.id)
    ).group_by(AccessLog.zone_name).all()
    pie_chart_data = {
        'labels': [zone for zone, count in access_by_zone],
        'data': [count for zone, count in access_by_zone]
    }
    
    # --- 5. Dados para a Tabela Top 5 Usuários Ativos (Total) ---
    top_5_users = db.session.query(
        User.name, func.count(AccessLog.id).label('total_accesses')
    ).join(User).group_by(User.name).order_by(func.count(AccessLog.id).desc()).limit(5).all()

    # --- 6. Logs de Atividade Recente (Feed) ---
    # Busca os 3 logs mais recentes de cada tipo
    recent_bio_logs = AccessLog.query.order_by(AccessLog.timestamp.desc()).limit(3).all()
    recent_pass_logs = PasswordLog.query.order_by(PasswordLog.timestamp.desc()).limit(3).all()

    # Adiciona um atributo 'type' para que possamos diferenciá-los no template
    for log in recent_bio_logs: log.type = 'biometria'
    for log in recent_pass_logs: log.type = 'senha'

    # Combina as duas listas e as reordena pela data/hora, pegando os 10 mais recentes no total
    recent_logs = sorted(
        recent_bio_logs + recent_pass_logs,
        key=lambda x: x.timestamp,
        reverse=True
    )[:10] # Aumentamos o limite para 10 para ter uma lista mais completa

    return render_template(
        'index.html',
        user_count=user_count,
        zone_count=zone_count,
        group_count=group_count,
        password_count=password_count,
        accesses_today=accesses_today,
        failures_today=failures_today,
        accesses_this_month=accesses_this_month,
        most_active_user=most_active_user,
        line_chart_data=line_chart_data,
        pie_chart_data=pie_chart_data,
        top_5_users=top_5_users,
        recent_logs=recent_logs
    )