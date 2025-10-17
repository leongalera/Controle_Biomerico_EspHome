# app/routes/group_routes.py
from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required
from app.models import db, AccessGroup
from app.forms import AccessGroupForm

group_bp = Blueprint('group', __name__)

@group_bp.route('/groups')
@login_required
def list_groups():
    groups = AccessGroup.query.order_by(AccessGroup.name).all()
    return render_template('groups/list.html', groups=groups)

@group_bp.route('/groups/add', methods=['GET', 'POST'])
@login_required
def add_group():
    form = AccessGroupForm()
    if form.validate_on_submit():
        new_group = AccessGroup(
            name=form.name.data,
            is_24h=form.is_24h.data,
            start_time=form.start_time.data if not form.is_24h.data else None,
            end_time=form.end_time.data if not form.is_24h.data else None,
            day_sun=form.day_sun.data,
            day_mon=form.day_mon.data,
            day_tue=form.day_tue.data,
            day_wed=form.day_wed.data,
            day_thu=form.day_thu.data,
            day_fri=form.day_fri.data,
            day_sat=form.day_sat.data
        )
        db.session.add(new_group)
        db.session.commit()
        flash('Grupo de acesso adicionado com sucesso!', 'success')
        return redirect(url_for('group.list_groups'))
    return render_template('groups/form.html', form=form, title='Adicionar Novo Grupo')

@group_bp.route('/groups/<int:group_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_group(group_id):
    group = AccessGroup.query.get_or_404(group_id)
    form = AccessGroupForm(obj=group)
    if form.validate_on_submit():
        group.name = form.name.data
        group.is_24h = form.is_24h.data
        group.start_time = form.start_time.data if not form.is_24h.data else None
        group.end_time = form.end_time.data if not form.is_24h.data else None
        group.day_sun=form.day_sun.data
        group.day_mon=form.day_mon.data
        group.day_tue=form.day_tue.data
        group.day_wed=form.day_wed.data
        group.day_thu=form.day_thu.data
        group.day_fri=form.day_fri.data
        group.day_sat=form.day_sat.data
        db.session.commit()
        flash('Grupo de acesso atualizado com sucesso!', 'success')
        return redirect(url_for('group.list_groups'))
    return render_template('groups/form.html', form=form, title='Editar Grupo de Acesso')

@group_bp.route('/groups/<int:group_id>/delete', methods=['POST'])
@login_required
def delete_group(group_id):
    group = AccessGroup.query.get_or_404(group_id)
    # Verifica se existem usuários associados antes de excluir
    if group.users:
        flash('Não é possível excluir este grupo, pois existem usuários associados a ele.', 'danger')
        return redirect(url_for('group.list_groups'))
    
    db.session.delete(group)
    db.session.commit()
    flash('Grupo de acesso excluído com sucesso!', 'success')
    return redirect(url_for('group.list_groups'))