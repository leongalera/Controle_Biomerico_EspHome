# app/routes/monitoring_routes.py
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from app.models import db, AccessLog, Zone, User
from app.forms import LogFilterForm
from datetime import datetime, time

monitoring_bp = Blueprint('monitoring', __name__)

@monitoring_bp.route('/monitoring', methods=['GET'])
@login_required
def view_logs():
    form = LogFilterForm(request.args)
    form.zone.choices = [('', '-- Todas as Zonas --')] + [(z.name, z.name) for z in Zone.query.order_by(Zone.name).all()]

    query = AccessLog.query

    # --- INÍCIO DA CORREÇÃO ---
    # Removemos o 'if form.validate():' e processamos os filtros diretamente.
    # O formulário já foi populado com 'request.args', então podemos checar seus dados.
    if form.start_date.data:
        start_datetime = datetime.combine(form.start_date.data, time.min)
        query = query.filter(AccessLog.timestamp >= start_datetime)
    
    if form.end_date.data:
        end_datetime = datetime.combine(form.end_date.data, time.max)
        query = query.filter(AccessLog.timestamp <= end_datetime)

    if form.user.data:
        query = query.filter(AccessLog.user_id == form.user.data.id)
    
    if form.zone.data:
        query = query.filter(AccessLog.zone_name == form.zone.data)
    # --- FIM DA CORREÇÃO ---

    # Lógica de paginação e renderização continua a mesma
    page = request.args.get('page', 1, type=int)
    
    pagination = query.order_by(AccessLog.timestamp.desc()).paginate(
        page=page, per_page=100, error_out=False
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