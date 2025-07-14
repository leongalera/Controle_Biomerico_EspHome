# app/routes/fingerprint_routes.py

import asyncio
import queue
import threading
from flask import Blueprint, render_template, redirect, url_for, flash, request, Response, jsonify, current_app 
from flask_login import login_required
from sqlalchemy import func
from app.models import db, User, Zone, Fingerprint
from app.forms import FingerprintEnrollForm
from app.services.esphome_service import enroll_fingerprint, delete_fingerprint_from_sensor
from app.services.ha_service import update_disabled_ids_in_ha
from app.scheduler_jobs import get_all_blocked_user_ids
from aioesphomeapi import APIClient, APIConnectionError

# Dicionário para rastrear processos de cadastro ativos
ACTIVE_ENROLLMENTS = {}

fingerprint_bp = Blueprint('fingerprint', __name__)

@fingerprint_bp.route('/user/<int:user_id>/fingerprints')
@login_required
def manage_fingerprints(user_id):
    user = User.query.get_or_404(user_id)
    fingerprints = user.fingerprints
    return render_template('fingerprints/manage.html', user=user, fingerprints=fingerprints)


@fingerprint_bp.route('/user/<int:user_id>/enroll', methods=['GET'])
@login_required
def enroll(user_id):
    user = User.query.get_or_404(user_id)
    form = FingerprintEnrollForm()
    return render_template('fingerprints/enroll.html', user=user, form=form)


@fingerprint_bp.route('/user/<int:user_id>/stream_enroll')
@login_required
def stream_enroll(user_id):
    # ... (leitura dos argumentos continua a mesma) ...
    user = User.query.get_or_404(user_id)
    zone_id = request.args.get('zone', type=int)
    finger_id_on_sensor = request.args.get('finger_id_on_sensor', type=int)
    finger_name = request.args.get('finger_name', type=str)

    if not all([zone_id, finger_id_on_sensor, finger_name]):
        return Response("Erro: Todos os campos são obrigatórios.", mimetype='text/plain')

    zone = Zone.query.get_or_404(zone_id)
    app_instance = current_app._get_current_object()

    def process_stream():
        q = queue.Queue()

        def run_async_enroll(app):
            with app.app_context():
                try:
                    # A chamada agora passa todos os dados necessários para a função de serviço
                    asyncio.run(enroll_fingerprint(
                        zone.esphome_hostname,
                        zone.esphome_api_key,
                        finger_id_on_sensor,
                        q,
                        user_id,
                        zone_id,
                        finger_name
                    ))
                except Exception as e:
                    current_app.logger.error(f"ERRO CRÍTICO NA THREAD: {e}", exc_info=True)
                    q.put(f"ERRO CRÍTICO NA THREAD: {e}")
                finally:
                    q.put(None)

        thread = threading.Thread(target=run_async_enroll, args=(app_instance,))
        thread.start()

        # A rota agora só se preocupa em repassar as mensagens da fila
        while True:
            status = q.get()
            if status is None:
                break
            yield f"data: {status}\n\n"
        
        thread.join()

    return Response(process_stream(), mimetype='text/event-stream')


@fingerprint_bp.route('/fingerprint/<int:fp_id>/delete', methods=['POST'])
@login_required
def delete_fingerprint(fp_id):
    fp_to_delete = Fingerprint.query.get_or_404(fp_id)
    zone = fp_to_delete.zone
    user_id = fp_to_delete.user_id
    
    try:
        # --- A CORREÇÃO ESTÁ AQUI ---
        # Usamos asyncio.run também para a exclusão, simplificando o código
        result = asyncio.run(
            delete_fingerprint_from_sensor(zone.esphome_hostname, zone.esphome_api_key, fp_to_delete.finger_id_on_sensor)
        )
        if not result['success']:
            flash(f"Falha ao deletar a digital do sensor físico: {result['message']}", 'danger')
            return redirect(url_for('fingerprint.manage_fingerprints', user_id=user_id))
    except Exception as e:
        flash(f"Ocorreu um erro de sistema ao comunicar com o sensor: {e}", "danger")
        return redirect(url_for('fingerprint.manage_fingerprints', user_id=user_id))

    db.session.delete(fp_to_delete)
    db.session.commit()
    
    # ... (lógica de atualização do HA) ...
    flash('Digital excluída com sucesso do sensor e do sistema.', 'success')
    return redirect(url_for('fingerprint.manage_fingerprints', user_id=user_id))


@fingerprint_bp.route('/api/zone/<int:zone_id>/next_finger_id')
@login_required
def get_next_finger_id(zone_id):
    max_id = db.session.query(func.max(Fingerprint.finger_id_on_sensor)).filter_by(zone_id=zone_id).scalar()
    next_id = 1 if max_id is None else max_id + 1
    return jsonify({'next_id': next_id})