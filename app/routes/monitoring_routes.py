# app/routes/monitoring_routes.py
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from app.models import db, AccessLog, Zone, User, PasswordLog
from app.forms import LogFilterForm, PasswordLogFilterForm
from datetime import datetime, time
import pytz

monitoring_bp = Blueprint('monitoring', __name__)

@monitoring_bp.route('/monitoring', methods=['GET'])
@login_required
def view_logs():
    form = LogFilterForm(request.args)
    form.zone.choices = [('', '-- Todas as Zonas --')] + [(z.name, z.name) for z in Zone.query.order_by(Zone.name).all()]

    query = AccessLog.query

    # Define o fuso horário local para a conversão
    local_tz = pytz.timezone('America/Sao_Paulo') 

    # Aplica os filtros condicionalmente
    if form.start_date.data:
        # Pega a data selecionada e a considera como o início do dia no fuso local
        local_start_dt_naive = datetime.combine(form.start_date.data, time.min)
        # Torna o datetime 'aware' (consciente do fuso horário)
        local_start_dt_aware = local_tz.localize(local_start_dt_naive)
        # Converte para UTC para a consulta no banco de dados
        utc_start_dt = local_start_dt_aware.astimezone(pytz.utc)
        query = query.filter(AccessLog.timestamp >= utc_start_dt)
    
    if form.end_date.data:
        # Faz o mesmo para a data final, usando o final do dia
        local_end_dt_naive = datetime.combine(form.end_date.data, time.max)
        local_end_dt_aware = local_tz.localize(local_end_dt_naive)
        utc_end_dt = local_end_dt_aware.astimezone(pytz.utc)
        query = query.filter(AccessLog.timestamp <= utc_end_dt)

    # Os filtros de usuário e zona não precisam de conversão de fuso horário
    if form.user.data:
        query = query.filter(AccessLog.user_id == form.user.data.id)
    
    if form.zone.data:
        query = query.filter(AccessLog.zone_name == form.zone.data)
    # --- FIM DA CORREÇÃO ---

    page = request.args.get('page', 1, type=int)
    
    pagination = query.order_by(AccessLog.timestamp.desc()).paginate(
        page=page, per_page=50, error_out=False
    )
    
    logs = pagination.items

    return render_template('monitoring/view.html', logs=logs, pagination=pagination, form=form)


# Rota para limpar o histórico
@monitoring_bp.route('/monitoring/clear', methods=['POST'])
@login_required
def clear_logs():
    try:
        # Apaga todos os registros da tabela AccessLog
        num_deleted = db.session.query(AccessLog).delete()
        db.session.commit()
        flash(f'Sucesso! {num_deleted} registro(s) do histórico foram apagados.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao limpar o histórico: {e}', 'danger')

    return redirect(url_for('monitoring.view_logs'))


@monitoring_bp.route('/monitoring/passwords', methods=['GET'])
@login_required
def view_password_logs():
    # Usa o novo formulário de filtro
    form = PasswordLogFilterForm(request.args)
    form.zone.choices = [('', '-- Todas as Zonas --')] + [(z.name, z.name) for z in Zone.query.order_by(Zone.name).all()]

    # Começa com a query base para os logs de senha
    query = PasswordLog.query
    local_tz = pytz.timezone('America/Sao_Paulo')

    # Aplica os filtros de data e zona, se presentes
    if form.start_date.data:
        local_start_dt_naive = datetime.combine(form.start_date.data, time.min)
        local_start_dt_aware = local_tz.localize(local_start_dt_naive)
        utc_start_dt = local_start_dt_aware.astimezone(pytz.utc)
        query = query.filter(PasswordLog.timestamp >= utc_start_dt)

    if form.end_date.data:
        local_end_dt_naive = datetime.combine(form.end_date.data, time.max)
        local_end_dt_aware = local_tz.localize(local_end_dt_naive)
        utc_end_dt = local_end_dt_aware.astimezone(pytz.utc)
        query = query.filter(PasswordLog.timestamp <= utc_end_dt)

    if form.zone.data:
        query = query.filter(PasswordLog.zone_name == form.zone.data)

    page = request.args.get('page', 1, type=int)

    # Pagina os resultados com o limite de 50 por página
    pagination = query.order_by(PasswordLog.timestamp.desc()).paginate(
        page=page, per_page=50, error_out=False
    )

    logs = pagination.items

    return render_template('monitoring/passwords_view.html', logs=logs, pagination=pagination, form=form)