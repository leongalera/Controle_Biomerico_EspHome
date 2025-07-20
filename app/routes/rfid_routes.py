# app/routes/rfid_routes.py
from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required
from app.models import db, RFIDTag, User, Zone
from app.forms import RFIDTagForm

rfid_bp = Blueprint('rfid', __name__)

@rfid_bp.route('/rfid_tags')
@login_required
def list_tags():
    tags = RFIDTag.query.all()
    return render_template('rfid/list.html', tags=tags)

@rfid_bp.route('/rfid_tags/add', methods=['GET', 'POST'])
@login_required
def add_tag():
    form = RFIDTagForm()
    if form.validate_on_submit():
        new_tag = RFIDTag(
            uid=form.uid.data,
            description=form.description.data,
            user=form.user.data,
            zones=form.zones.data
        )
        db.session.add(new_tag)
        db.session.commit()
        flash('Tag RFID adicionada com sucesso!', 'success')
        return redirect(url_for('rfid.list_tags'))
    return render_template('rfid/form.html', form=form, title='Adicionar Nova Tag RFID')

@rfid_bp.route('/rfid_tags/<int:tag_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_tag(tag_id):
    tag = RFIDTag.query.get_or_404(tag_id)
    form = RFIDTagForm(obj=tag)
    if form.validate_on_submit():
        form.populate_obj(tag)
        db.session.commit()
        flash('Tag RFID atualizada com sucesso!', 'success')
        return redirect(url_for('rfid.list_tags'))
    return render_template('rfid/form.html', form=form, title='Editar Tag RFID')

@rfid_bp.route('/rfid_tags/<int:tag_id>/delete', methods=['POST'])
@login_required
def delete_tag(tag_id):
    tag = RFIDTag.query.get_or_404(tag_id)
    db.session.delete(tag)
    db.session.commit()
    flash('Tag RFID excluída com sucesso!', 'danger')
    return redirect(url_for('rfid.list_tags'))