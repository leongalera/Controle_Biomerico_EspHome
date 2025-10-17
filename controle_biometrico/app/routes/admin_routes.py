# app/routes/admin_routes.py
import asyncio
from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from app.models import db, AdminUser, User, Fingerprint, Zone, AccessGroup, AccessLog, Password, PasswordLog, RFIDTag, RFIDLog
from app.forms import AdminUserForm, EditAdminUserForm
from app.services.esphome_service import delete_all_fingerprints_from_sensor

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/')
@login_required
def index():
    """Página principal da área de administração."""
    zones = Zone.query.order_by(Zone.name).all()
    return render_template('admin/index.html', zones=zones)

# --- Gerenciamento de Administradores ---
@admin_bp.route('/admins')
@login_required
def list_admins():
    admins = AdminUser.query.order_by(AdminUser.username).all()
    return render_template('admin/list_admins.html', admins=admins)

@admin_bp.route('/admins/add', methods=['GET', 'POST'])
@login_required
def add_admin():
    form = AdminUserForm()
    if form.validate_on_submit():
        if AdminUser.query.filter_by(username=form.username.data).first():
            flash('Este nome de usuário já existe.', 'danger')
        else:
            new_admin = AdminUser(username=form.username.data)
            new_admin.set_password(form.password.data)
            db.session.add(new_admin)
            db.session.commit()
            flash('Administrador adicionado com sucesso!', 'success')
            return redirect(url_for('admin.list_admins'))
    return render_template('admin/admin_form.html', form=form, title='Adicionar Administrador')

@admin_bp.route('/admins/<int:admin_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_admin(admin_id):
    admin = AdminUser.query.get_or_404(admin_id)
    form = EditAdminUserForm(obj=admin)
    if form.validate_on_submit():
        # Verifica se a senha atual está correta
        if not admin.check_password(form.current_password.data):
            flash('A senha atual está incorreta.', 'danger')
            return render_template('admin/admin_form.html', form=form, title='Editar Administrador')

        admin.username = form.username.data
        # Altera a senha apenas se uma nova foi fornecida
        if form.new_password.data:
            admin.set_password(form.new_password.data)

        db.session.commit()
        flash('Administrador atualizado com sucesso!', 'success')
        return redirect(url_for('admin.list_admins'))
    return render_template('admin/admin_form.html', form=form, title='Editar Administrador')

@admin_bp.route('/admins/<int:admin_id>/delete', methods=['POST'])
@login_required
def delete_admin(admin_id):
    # Impede que o usuário se auto-exclua
    if current_user.id == admin_id:
        flash('Você não pode excluir a si mesmo.', 'danger')
        return redirect(url_for('admin.list_admins'))
    
    admin_to_delete = AdminUser.query.get_or_404(admin_id)
    db.session.delete(admin_to_delete)
    db.session.commit()
    flash('Administrador excluído com sucesso.', 'success')
    return redirect(url_for('admin.list_admins'))

# --- Ação Perigosa: Zerar Ferramenta ---
@admin_bp.route('/factory_reset', methods=['POST'])
@login_required
def factory_reset():
    """Apaga TODOS os dados de configuração e logs, incluindo administradores."""
    try:
        # Apaga em uma ordem que respeita as chaves estrangeiras
        Fingerprint.query.delete()
        AccessLog.query.delete()
        PasswordLog.query.delete()
        RFIDLog.query.delete()
        
        # Tabelas de associação
        db.session.execute(db.text('DELETE FROM password_zone_association'))
        db.session.execute(db.text('DELETE FROM rfid_zone_association'))

        RFIDTag.query.delete()
        Password.query.delete()
        User.query.delete()
        AccessGroup.query.delete()
        Zone.query.delete()
        AdminUser.query.delete()

        db.session.commit()
        flash('FERRAMENTA ZERADA! Todos os dados foram apagados. Você precisará recriar um administrador na configuração do Add-on.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao tentar zerar a ferramenta: {e}', 'danger')
    
    return redirect(url_for('admin.index'))