# app/routes/api_routes.py
from flask import Blueprint, request, jsonify
from app.models import db, AccessLog, Fingerprint, User, Zone
from datetime import datetime

api_bp = Blueprint('api', __name__)

@api_bp.route('/log_access', methods=['POST'])
def log_access():
    data = request.json
    if not data:
        return jsonify({"status": "error", "message": "Request must be JSON"}), 400

    finger_id_on_sensor = data.get('finger_id')
    zone_prefix = data.get('zona') # <-- Usando o prefixo da zona enviado pelo HA

    if not zone_prefix:
        return jsonify({"status": "error", "message": "Payload must include 'zona' prefix"}), 400

    # --- LÓGICA DE BUSCA CORRIGIDA ---
    # Procura a zona pelo prefixo único, que é o correto
    zone = Zone.query.filter_by(prefix=zone_prefix).first()
    
    if not zone:
        return jsonify({"status": "error", "message": f"Zone with prefix '{zone_prefix}' not found in DB"}), 404

    fingerprint = Fingerprint.query.filter_by(
        finger_id_on_sensor=finger_id_on_sensor,
        zone_id=zone.id
    ).first()

    if not fingerprint:
        # Registra que uma digital válida no sensor não foi encontrada no nosso banco de dados
        unmatched_log = AccessLog(
            zone_name=zone.name,
            result="Autorizado (ID não associado)",
            matched_finger_id=finger_id_on_sensor
        )
        db.session.add(unmatched_log)
        db.session.commit()
        return jsonify({"status": "success", "info": "Fingerprint ID matched on sensor but not found in webapp DB"}), 200

    # Se tudo for encontrado, registra o log de sucesso completo
    log = AccessLog(
        user_id=fingerprint.user_id,
        zone_name=zone.name,
        finger_used=fingerprint.finger_name,
        matched_finger_id=finger_id_on_sensor,
        result="Autorizado"
    )
    db.session.add(log)
    db.session.commit()

    return jsonify({"status": "success"}), 200

@api_bp.route('/log_unmatched_access', methods=['POST'])
def log_unmatched_access():
    data = request.json
    if not data:
        return jsonify({"status": "error", "message": "Request must be JSON"}), 400
    
    zone_prefix = data.get('zona')
    if not zone_prefix:
        return jsonify({"status": "error", "message": "Payload must include 'zona' prefix"}), 400
        
    zone = Zone.query.filter_by(prefix=zone_prefix).first()
    zone_name = zone.name if zone else f"Zona Desconhecida (prefixo: {zone_prefix})"

    log = AccessLog(
        zone_name=zone_name,
        result="Não Reconhecido"
    )
    db.session.add(log)
    db.session.commit()
    return jsonify({"status": "success"}), 200

@api_bp.route('/log_inactive_access', methods=['POST'])
def log_inactive_access():
    data = request.json
    if not data:
        return jsonify({"status": "error", "message": "Request must be JSON"}), 400

    finger_id_on_sensor = data.get('finger_id')
    zone_prefix = data.get('zona')

    if not all([finger_id_on_sensor, zone_prefix]):
        return jsonify({"status": "error", "message": "Payload must include 'finger_id' and 'zona'"}), 400

    zone = Zone.query.filter_by(prefix=zone_prefix).first()
    if not zone:
        return jsonify({"status": "error", "message": f"Zone with prefix '{zone_prefix}' not found"}), 404

    # Encontra a digital para descobrir quem é o usuário inativo
    fingerprint = Fingerprint.query.filter_by(
        finger_id_on_sensor=finger_id_on_sensor,
        zone_id=zone.id
    ).first()

    if not fingerprint:
        # Se a digital não está no nosso BD, tratamos como um log "não reconhecido"
        log = AccessLog(zone_name=zone.name, result="Não Reconhecido")
    else:
        # Se encontramos a digital, registramos o log com os dados do usuário inativo
        log = AccessLog(
            user_id=fingerprint.user_id,
            zone_name=zone.name,
            finger_used=fingerprint.finger_name,
            matched_finger_id=finger_id_on_sensor,
            result="Negado (Inativo)" # <-- O novo status
        )

    db.session.add(log)
    db.session.commit()
    return jsonify({"status": "success"}), 200