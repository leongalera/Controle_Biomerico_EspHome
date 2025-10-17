# app/routes/user_routes.py
from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required
from app.models import db, User, AccessGroup
from app.forms import UserForm
from app.models import db, User, AccessGroup, Fingerprint, Zone # Adicione Fingerprint e Zone
from app.services.ha_service import update_disabled_ids_in_ha
from app.scheduler_jobs import get_all_blocked_user_ids

user_bp = Blueprint('user', __name__)

@user_bp.route('/users')
@login_required
def list_users():
    users = User.query.order_by(User.name).all()
    return render_template('users/list.html', users=users)

@user_bp.route('/users/add', methods=['GET', 'POST'])
@login_required
def add_user():
    form = UserForm()
    if form.validate_on_submit():
        new_user = User(
            name=form.name.data,
            phone=form.phone.data,
            access_group_id=form.access_group.data.id
        )
        db.session.add(new_user)
        db.session.commit()
        flash('Usuário adicionado com sucesso!', 'success')
        return redirect(url_for('user.list_users'))
    return render_template('users/form.html', form=form, title='Adicionar Novo Usuário')

@user_bp.route('/users/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_user(user_id):
    user = User.query.get_or_404(user_id)
    form = UserForm(obj=user)
    form.access_group.data = user.access_group # Seta o valor do dropdown
    if form.validate_on_submit():
        user.name = form.name.data
        user.phone = form.phone.data
        user.access_group_id = form.access_group.data.id
        db.session.commit()
        flash('Usuário atualizado com sucesso!', 'success')
        return redirect(url_for('user.list_users'))
    return render_template('users/form.html', form=form, title='Editar Usuário')

@user_bp.route('/users/<int:user_id>/delete', methods=['POST'])
@login_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    # A configuração 'cascade' no modelo vai excluir as digitais e logs automaticamente
    db.session.delete(user)
    db.session.commit()
    # AQUI, no futuro, também precisaremos chamar a função para atualizar o HA
    flash('Usuário excluído permanentemente!', 'danger')
    return redirect(url_for('user.list_users'))


# ROTA IMPORTANTE PARA ATIVAR E DESATIVAR - VERSÃO FINAL
@user_bp.route('/users/<int:user_id>/toggle_active', methods=['POST'])
@login_required
def toggle_active(user_id):
    user = User.query.get_or_404(user_id)
    user.is_active = not user.is_active
    db.session.commit()

    # ---- LÓGICA CORRIGIDA ----
    all_blocked_ids = get_all_blocked_user_ids()
    zones_to_update = {fp.zone for fp in user.fingerprints}
    
    for zone in zones_to_update:
        # Passa a lista de IDs calculada para a função de serviço
        update_disabled_ids_in_ha(zone, all_blocked_ids)
    
    status = "ativado" if user.is_active else "desativado"
    flash(f'Usuário {user.name} foi {status}. Status sincronizado com as zonas de acesso.', 'success')
    
    return redirect(url_for('user.list_users'))