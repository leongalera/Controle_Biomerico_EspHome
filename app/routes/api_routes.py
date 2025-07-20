# app/routes/api_routes.py
from flask import Blueprint, request, jsonify
from flask_login import login_required
from app.models import db, AccessLog, Fingerprint, User, Zone, Password, PasswordLog, RFIDTag, RFIDLog
from datetime import datetime, time
from sqlalchemy import func
from app.services.esphome_service import CANCEL_ENROLLMENT_FLAGS
import pytz
from app.services.ha_service import update_disabled_ids_in_ha, get_ha_entity_state

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
        return jsonify({'valid': False, 'reason': 'Payload incompleto'}), 400 # Payload incompleto

    # Encontra a senha e a zona
    password_entry = Password.query.filter_by(value=password_value).first()
    zone = Zone.query.filter_by(prefix=zone_prefix).first()
    zone_name_for_log = zone.name if zone else f"Prefixo: {zone_prefix}"

    # Validação 1: A senha existe?
    if not password_entry:
        log = PasswordLog(zone_name=zone_name_for_log, password_submitted=password_value, result="Inválida")
        db.session.add(log); db.session.commit()
        return jsonify({'valid': False, 'reason': 'Erro, Senha inválida'})

    # Validação 2: A senha é permitida para esta zona?
    is_zone_allowed = any(z.prefix == zone_prefix for z in password_entry.zones)
    if not is_zone_allowed:
        log = PasswordLog(zone_name=zone_name_for_log, password_submitted=password_value, result="Não Permitida na Zona")
        db.session.add(log); db.session.commit()
        return jsonify({'valid': False, 'reason': 'Erro, Senha não permitida para esta zona'})

    group = password_entry.group

    # Se o grupo tem acesso 24h, permite
    if group.is_24h:
        log = PasswordLog(zone_name=zone_name_for_log, password_submitted=password_value, result="Válida")
        db.session.add(log); db.session.commit()
        return jsonify({'valid': True, 'reason': 'Senha Válida'})

    # Se não, verifica o dia e a hora
    try:
        tz = pytz.timezone('America/Sao_Paulo')
        now = datetime.now(tz)
        current_time = now.time()
        current_weekday = now.weekday() # Segunda=0, ..., Domingo=6
        weekday_map = {0: group.day_mon, 1: group.day_tue, 2: group.day_wed, 3: group.day_thu, 4: group.day_fri, 5: group.day_sat, 6: group.day_sun}

        is_day_allowed = weekday_map.get(current_weekday, False)
        is_time_allowed = group.start_time <= current_time <= group.end_time

        if is_day_allowed and is_time_allowed:
            log = PasswordLog(zone_name=zone_name_for_log, password_submitted=password_value, result="Válida")
            db.session.add(log); db.session.commit()
            return jsonify({'valid': True, 'reason': 'Senha Válida'})
        else:
            reason = "Fora do dia permitido" if not is_day_allowed else "Fora do horário permitido"
            log = PasswordLog(zone_name=zone_name_for_log, password_submitted=password_value, result="Fora de Horário", notes=reason)
            db.session.add(log); db.session.commit()
            return jsonify({'valid': False, 'reason': 'Erro, Fora do horário permitido'})
    except Exception as e:
        log = PasswordLog(zone_name=zone_name_for_log, password_submitted=password_value, result="Erro de Validação", notes=str(e))
        db.session.add(log); db.session.commit()
        return jsonify({'valid': False, 'reason': 'Erro de Validação'})


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

@api_bp.route('/fingerprint/cancel_enroll', methods=['POST'])
@login_required
def cancel_enroll():
    data = request.json
    user_id = data.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'message': 'ID do Usuário não fornecido'}), 400

    # Apenas levanta a bandeira. A thread de cadastro verá isso e se cancelará.
    if user_id in CANCEL_ENROLLMENT_FLAGS:
        CANCEL_ENROLLMENT_FLAGS[user_id] = True
        return jsonify({'success': True, 'message': 'Sinal de cancelamento enviado.'}), 200
    else:
        return jsonify({'success': False, 'message': 'Nenhum processo de cadastro ativo para cancelar.'}), 404
    

@api_bp.route('/verify_rfid', methods=['POST'])
def verify_rfid():
    data = request.json
    uid = data.get('uid')
    zone_prefix = data.get('zona')

    if not all([uid, zone_prefix]):
        return jsonify({'valid': False}), 400

    zone = Zone.query.filter_by(prefix=zone_prefix).first()
    zone_name_for_log = zone.name if zone else f"Prefixo: {zone_prefix}"
    tag = RFIDTag.query.filter_by(uid=uid).first()

    # Validação 1: Tag não existe
    if not tag:
        log = RFIDLog(zone_name=zone_name_for_log, uid_submitted=uid, result="UID Inválido")
        db.session.add(log); db.session.commit()
        return jsonify({'valid': False})

    # Validação 2: Tag não permitida na zona
    if zone not in tag.zones:
        log = RFIDLog(zone_name=zone_name_for_log, uid_submitted=uid, result="Zona Não Permitida", user_id=tag.user_id)
        db.session.add(log); db.session.commit()
        return jsonify({'valid': False})

    # Validação 3: Usuário e horário
    user = tag.user
    group = user.access_group

    if not user.is_active:
        log = RFIDLog(zone_name=zone_name_for_log, uid_submitted=uid, result="Usuário Inativo", user_id=user.id)
        db.session.add(log); db.session.commit()
        return jsonify({'valid': False})

    if not group.is_24h:
        try:
            tz = pytz.timezone('America/Sao_Paulo')
            now = datetime.now(tz)
            current_time = now.time()
            current_weekday = now.weekday()
            weekday_map = {0: group.day_mon, 1: group.day_tue, 2: group.day_wed, 3: group.day_thu, 4: group.day_fri, 5: group.day_sat, 6: group.day_sun}
            is_day_allowed = weekday_map.get(current_weekday, False)
            is_time_allowed = group.start_time <= current_time <= group.end_time

            if not (is_day_allowed and is_time_allowed):
                reason = "Fora do dia" if not is_day_allowed else "Fora do horário"
                log = RFIDLog(zone_name=zone_name_for_log, uid_submitted=uid, result=f"Negado ({reason})", user_id=user.id)
                db.session.add(log); db.session.commit()
                return jsonify({'valid': False})
        except Exception:
            return jsonify({'valid': False})

    # Sucesso
    log = RFIDLog(zone_name=zone_name_for_log, uid_submitted=uid, result="Autorizado", user_id=user.id)
    db.session.add(log); db.session.commit()
    return jsonify({'valid': True})
    

@api_bp.route('/zone/<int:zone_id>/get_last_rfid')
@login_required
def get_last_rfid(zone_id):
    zone = Zone.query.get_or_404(zone_id)

    # Monta o nome da entidade que o ESPHome cria
    # Ex: "accp -  Last RFID UID" -> "accp_last_rfid_uid"
    # O ideal é padronizar, vamos assumir que o nome do device é o hostname sem .local
    clean_hostname = zone.esphome_hostname.split('.')[0]
    # O ESPHome substitui '-' por '_' e espaços por '_'
    entity_name_slug = f"{zone.prefix.strip()}__last_rfid_uid".replace(' - ', '_').replace(' ', '_').lower()
    entity_zone = zone.prefix.replace(' ', '_').lower()  # Ex: "acesso_principal"

    entity_id = f"sensor.{clean_hostname.replace('-', '_')}_{entity_zone}_last_rfid_uid"
    alternative_entity_id = f"text_sensor.{clean_hostname.replace('-', '_')}_{entity_zone}_last_rfid_uid"

    result = get_ha_entity_state(entity_id)
    if not result['success']:
        result = get_ha_entity_state(alternative_entity_id) # Tenta a alternativa
        if not result['success']:
             return jsonify({'success': False, 'message': f"Não foi possível encontrar a entidade '{entity_id}' ou '{alternative_entity_id}' no Home Assistant."}), 404

    # Retorna o estado (o UID) e o horário da última atualização
    return jsonify({
        'success': True, 
        'uid': result['data']['state'],
        'last_updated': result['data']['last_updated']
    })