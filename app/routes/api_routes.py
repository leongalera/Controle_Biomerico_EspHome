# app/routes/api_routes.py
from flask import Blueprint, request, jsonify
from flask_login import login_required
from app.models import db, AccessLog, Fingerprint, User, Zone, Password, PasswordLog
from datetime import datetime
from sqlalchemy import func

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


@api_bp.route('/verify_password', methods=['POST'])
def verify_password():
    data = request.json
    password_value = data.get('password')
    zone_prefix = data.get('zona')

    if not all([password_value, zone_prefix]):
        return jsonify({'valid': False, 'reason': 'Payload incompleto'}), 400

    zone_name_for_log = f"Prefixo: {zone_prefix}"
    zone = Zone.query.filter_by(prefix=zone_prefix).first()
    if zone:
        zone_name_for_log = zone.name

    password_entry = Password.query.filter_by(value=password_value).first()

    # Caso 1: Senha não existe no banco de dados
    if not password_entry:
        log = PasswordLog(zone_name=zone_name_for_log, password_submitted=password_value, result="Inválida")
        db.session.add(log)
        db.session.commit()
        return jsonify({'valid': False, 'reason': 'Senha inválida'})

    # Caso 2: Senha existe, mas não está associada a esta zona
    is_zone_allowed = any(z.prefix == zone_prefix for z in password_entry.zones)
    if not is_zone_allowed:
        log = PasswordLog(zone_name=zone_name_for_log, password_submitted=password_value, result="Não Permitida", notes=f"Senha válida, mas não para a zona {zone_name_for_log}")
        db.session.add(log)
        db.session.commit()
        return jsonify({'valid': False, 'reason': 'Senha não permitida para esta zona'})

    # Caso 3: Sucesso! Senha válida e permitida para a zona
    log = PasswordLog(zone_name=zone_name_for_log, password_submitted=password_value, result="Válida")
    db.session.add(log)
    db.session.commit()
    return jsonify({'valid': True})


@api_bp.route('/chart_data')
@login_required
def get_chart_data():
    # Pega o nome da zona dos parâmetros da URL (ex: /chart_data?zone=Porta%20Principal)
    zone_name = request.args.get('zone')

    # Constrói a query base
    query_bio = AccessLog.query
    query_pass = PasswordLog.query

    # Se uma zona específica foi selecionada, adiciona o filtro
    if zone_name and zone_name != 'all':
        query_bio = query_bio.filter_by(zone_name=zone_name)
        query_pass = query_pass.filter_by(zone_name=zone_name)

    # Calcula os totais com base na query (filtrada ou não)
    authorized_bio = query_bio.filter(AccessLog.result == 'Autorizado').count()
    authorized_pass = query_pass.filter(PasswordLog.result == 'Válida').count()
    total_authorized = authorized_bio + authorized_pass

    denied_bio = query_bio.filter(AccessLog.result != 'Autorizado').count()
    denied_pass = query_pass.filter(PasswordLog.result != 'Válida').count()
    total_denied = denied_bio + denied_pass

    # Retorna os dados em formato JSON
    return jsonify({
        'labels': ['Autorizados', 'Negados'],
        'data': [total_authorized, total_denied],
    })

