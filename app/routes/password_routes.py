# app/routes/password_routes.py
from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required
from app.models import db, Password, Zone
from app.forms import PasswordForm

password_bp = Blueprint('password', __name__)

@password_bp.route('/passwords')
@login_required
def list_passwords():
    passwords = Password.query.all()
    return render_template('passwords/list.html', passwords=passwords)

@password_bp.route('/passwords/add', methods=['GET', 'POST'])
@login_required
def add_password():
    form = PasswordForm()
    if form.validate_on_submit():
        new_password = Password(
            description=form.description.data,
            value=form.value.data,
            zones=form.zones.data # SQLAlchemy lida com a associação automaticamente
        )
        db.session.add(new_password)
        db.session.commit()
        flash('Senha criada com sucesso!', 'success')
        return redirect(url_for('password.list_passwords'))
    return render_template('passwords/form.html', form=form, title='Adicionar Nova Senha')

@password_bp.route('/passwords/<int:password_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_password(password_id):
    password = Password.query.get_or_404(password_id)
    form = PasswordForm(obj=password)
    if form.validate_on_submit():
        password.description = form.description.data
        password.value = form.value.data
        password.zones = form.zones.data # Atualiza as associações
        db.session.commit()
        flash('Senha atualizada com sucesso!', 'success')
        return redirect(url_for('password.list_passwords'))
    return render_template('passwords/form.html', form=form, title='Editar Senha')

@password_bp.route('/passwords/<int:password_id>/delete', methods=['POST'])
@login_required
def delete_password(password_id):
    password = Password.query.get_or_404(password_id)
    db.session.delete(password)
    db.session.commit()
    flash('Senha excluída com sucesso!', 'danger')
    return redirect(url_for('password.list_passwords'))