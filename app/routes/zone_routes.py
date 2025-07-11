# app/routes/zone_routes.py
import asyncio
from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required
from app.models import db, Zone, Fingerprint 
from app.forms import ZoneForm
from app.services.esphome_service import delete_all_fingerprints_from_sensor

zone_bp = Blueprint('zone', __name__)

@zone_bp.route('/zones')
@login_required
def list_zones():
    zones = Zone.query.order_by(Zone.name).all()
    return render_template('zones/list.html', zones=zones)

@zone_bp.route('/zones/add', methods=['GET', 'POST'])
@login_required
def add_zone():
    form = ZoneForm()
    if form.validate_on_submit():
        new_zone = Zone(
            name=form.name.data,
            prefix=form.prefix.data,
            description=form.description.data,
            esphome_hostname=form.esphome_hostname.data,
            esphome_api_key=form.esphome_api_key.data
        )
        db.session.add(new_zone)
        db.session.commit()
        flash('Zona adicionada com sucesso!', 'success')
        return redirect(url_for('zone.list_zones'))
    return render_template('zones/form.html', form=form, title='Adicionar Nova Zona')

@zone_bp.route('/zones/<int:zone_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_zone(zone_id):
    zone = Zone.query.get_or_404(zone_id)
    form = ZoneForm(obj=zone) # Preenche o formulário com os dados da zona
    if form.validate_on_submit():
        zone.name = form.name.data
        zone.prefix = form.prefix.data
        zone.description = form.description.data
        zone.esphome_hostname = form.esphome_hostname.data
        zone.esphome_api_key = form.esphome_api_key.data
        db.session.commit()
        flash('Zona atualizada com sucesso!', 'success')
        return redirect(url_for('zone.list_zones'))
    return render_template('zones/form.html', form=form, title='Editar Zona')

@zone_bp.route('/zones/<int:zone_id>/delete', methods=['POST'])
@login_required
def delete_zone(zone_id):
    zone = Zone.query.get_or_404(zone_id)
    db.session.delete(zone)
    db.session.commit()
    flash('Zona excluída com sucesso!', 'danger')
    return redirect(url_for('zone.list_zones'))

@zone_bp.route('/zone/<int:zone_id>/delete_all_fingerprints', methods=['POST'])
@login_required
def delete_all_fingerprints(zone_id):
    zone = Zone.query.get_or_404(zone_id)

    # Etapa 1: Enviar comando para o ESP32 apagar as digitais do sensor
    try:
        result = asyncio.run(delete_all_fingerprints_from_sensor(zone.esphome_hostname, zone.esphome_api_key))
        if not result['success']:
            flash(f"Falha ao comunicar com o módulo: {result['message']}", 'danger')
            return redirect(url_for('zone.list_zones'))
    except Exception as e:
        flash(f"Ocorreu um erro de sistema ao comunicar com o módulo: {e}", 'danger')
        return redirect(url_for('zone.list_zones'))

    # Etapa 2: Se a Etapa 1 foi bem-sucedida, apagar os registros do nosso banco de dados
    try:
        # O método 'delete()' em uma query apaga todos os registros que correspondem ao filtro
        num_deleted = Fingerprint.query.filter_by(zone_id=zone.id).delete()
        db.session.commit()
        flash(f"Sucesso! {num_deleted} registro(s) de digitais foram apagados do banco de dados para a zona '{zone.name}'.", 'success')
    except Exception as e:
        db.session.rollback()
        flash(f"As digitais foram apagadas do módulo, mas ocorreu um erro ao apagar os registros no banco de dados: {e}", 'danger')

    return redirect(url_for('zone.list_zones'))