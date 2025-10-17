# app/routes/main_routes.py
from flask import Blueprint, render_template
from flask_login import login_required
from app.models import db, User, Zone, AccessGroup, Password, AccessLog, PasswordLog, RFIDTag, RFIDLog
from sqlalchemy import func
from datetime import date, timedelta, datetime
from sqlalchemy import func, extract
from collections import Counter

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
@login_required
def index():
    # --- 1. KPIs de Configuração ---
    user_count = User.query.count()
    zone_count = Zone.query.count()
    group_count = AccessGroup.query.count()
    password_count = Password.query.count()
    rfid_tag_count = RFIDTag.query.count() # <-- NOVO KPI

    # --- 2. KPIs de Atividade Recente (Agora com RFID) ---
    today_start = date.today()
    now = datetime.utcnow()
    first_day_of_month = now.replace(day=1)

    # Acessos hoje (Biometria + Senha + RFID)
    accesses_today_bio = AccessLog.query.filter(AccessLog.timestamp >= today_start, AccessLog.result == 'Autorizado').count()
    accesses_today_pass = PasswordLog.query.filter(PasswordLog.timestamp >= today_start, PasswordLog.result == 'Válida').count()
    accesses_today_rfid = RFIDLog.query.filter(RFIDLog.timestamp >= today_start, RFIDLog.result == 'Autorizado').count()
    accesses_today = accesses_today_bio + accesses_today_pass + accesses_today_rfid

    # Falhas hoje (Biometria + Senha + RFID)
    failures_today_bio = AccessLog.query.filter(AccessLog.timestamp >= today_start, AccessLog.result != 'Autorizado').count()
    failures_today_pass = PasswordLog.query.filter(PasswordLog.timestamp >= today_start, PasswordLog.result != 'Válida').count()
    failures_today_rfid = RFIDLog.query.filter(RFIDLog.timestamp >= today_start, RFIDLog.result != 'Autorizado').count()
    failures_today = failures_today_bio + failures_today_pass + failures_today_rfid

    # Acessos no Mês (Biometria + Senha + RFID)
    accesses_month_bio = AccessLog.query.filter(AccessLog.timestamp >= first_day_of_month, AccessLog.result == 'Autorizado').count()
    accesses_month_pass = PasswordLog.query.filter(PasswordLog.timestamp >= first_day_of_month, PasswordLog.result == 'Válida').count()
    accesses_month_rfid = RFIDLog.query.filter(RFIDLog.timestamp >= first_day_of_month, RFIDLog.result == 'Autorizado').count()
    accesses_this_month = accesses_month_bio + accesses_month_pass + accesses_month_rfid

    # --- 3. Dados para o Gráfico de Linha (Últimos 7 Dias, com RFID) ---
    seven_days_ago = now - timedelta(days=7)
    # Combina logs de biometria e rfid para o gráfico
    all_access_logs = db.session.query(func.date(AccessLog.timestamp).label('day')).filter(AccessLog.timestamp >= seven_days_ago).union_all(
        db.session.query(func.date(RFIDLog.timestamp).label('day')).filter(RFIDLog.timestamp >= seven_days_ago)
    ).subquery()
    accesses_last_7_days = db.session.query(all_access_logs.c.day, func.count()).group_by(all_access_logs.c.day).all()

    labels = [(now.date() - timedelta(days=i)) for i in range(6, -1, -1)]
    data_points = {day.strftime('%d/%m'): 0 for day in labels}
    for day_str, count in accesses_last_7_days:
        # --- A CORREÇÃO ESTÁ AQUI ---
        # 1. Converte a string 'AAAA-MM-DD' em um objeto de data.
        day_obj = datetime.strptime(day_str, '%Y-%m-%d')
        # 2. Formata o objeto de data para 'DD/MM'.
        day_formatted = day_obj.strftime('%d/%m')

        if day_formatted in data_points:
            data_points[day_formatted] = count
    line_chart_data = {'labels': list(data_points.keys()), 'data': list(data_points.values())}

    # --- 4. Dados para o Gráfico de Pizza (Acessos por Zona, com RFID) ---
    access_by_zone_bio = db.session.query(AccessLog.zone_name, func.count(AccessLog.id)).group_by(AccessLog.zone_name).all()
    access_by_zone_rfid = db.session.query(RFIDLog.zone_name, func.count(RFIDLog.id)).group_by(RFIDLog.zone_name).all()
    zone_counter = Counter()
    for zone, count in access_by_zone_bio: zone_counter[zone] += count
    for zone, count in access_by_zone_rfid: zone_counter[zone] += count
    pie_chart_data = {'labels': list(zone_counter.keys()), 'data': list(zone_counter.values())}

    # --- 5. Tabela Top 5 Usuários Ativos (com RFID) ---
    top_users_bio = db.session.query(User.name, func.count(AccessLog.id).label('total')).join(User).group_by(User.name).all()
    top_users_rfid = db.session.query(User.name, func.count(RFIDLog.id).label('total')).join(User).group_by(User.name).all()
    user_counter = Counter()
    for name, count in top_users_bio: user_counter[name] += count
    for name, count in top_users_rfid: user_counter[name] += count
    top_5_users = user_counter.most_common(5)

    # --- 6. Atividades Recentes (com RFID) ---
    recent_bio_logs = AccessLog.query.order_by(AccessLog.timestamp.desc()).limit(2).all()
    recent_pass_logs = PasswordLog.query.order_by(PasswordLog.timestamp.desc()).limit(2).all()
    recent_rfid_logs = RFIDLog.query.order_by(RFIDLog.timestamp.desc()).limit(2).all()
    for log in recent_bio_logs: log.type = 'biometria'
    for log in recent_pass_logs: log.type = 'senha'
    for log in recent_rfid_logs: log.type = 'rfid'

    recent_logs = sorted(recent_bio_logs + recent_pass_logs + recent_rfid_logs, key=lambda x: x.timestamp, reverse=True)[:10]

    return render_template('index.html', # ... (passando todas as variáveis novas e antigas)
        user_count=user_count, zone_count=zone_count, group_count=group_count, password_count=password_count, rfid_tag_count=rfid_tag_count,
        accesses_today=accesses_today, failures_today=failures_today, accesses_this_month=accesses_this_month,
        line_chart_data=line_chart_data, pie_chart_data=pie_chart_data, top_5_users=top_5_users, recent_logs=recent_logs)