# app/services/ha_service.py
import requests
import json
from flask import current_app
from app.models import User, Fingerprint

# A função agora recebe a lista de IDs de usuários bloqueados como um parâmetro
def update_disabled_ids_in_ha(zone, blocked_user_ids):
    """
    Recebe uma lista de IDs de usuários bloqueados e atualiza o Home Assistant
    para uma zona específica.
    """
    try:
        # print(f"HA_SERVICE: Iniciando atualização para a zona: '{zone.name}'")

        # Encontra os fingerprints que pertencem aos usuários bloqueados NESSA ZONA
        fingerprints_to_disable = Fingerprint.query.filter(
            Fingerprint.user_id.in_(blocked_user_ids),
            Fingerprint.zone_id == zone.id
        ).all()
        
        disabled_ids_list = [str(f.finger_id_on_sensor) for f in fingerprints_to_disable]
        disabled_ids_str = f",{','.join(disabled_ids_list)}," if disabled_ids_list else ""
        
        # print(f"HA_SERVICE: Lista de IDs de digitais a serem desabilitados para a zona '{zone.name}': '{disabled_ids_str}'")

        # O resto da função de envio para o HA continua igual
        clean_hostname = zone.esphome_hostname.split('.')[0]
        object_id = clean_hostname.replace('-', '_')
        entity_id = f"input_text.{object_id}_disabled_ids"
        
        ha_url = current_app.config['HA_URL']
        ha_token = current_app.config['HA_TOKEN']
        
        if not ha_url or not ha_token:
            print("HA_SERVICE: ERRO - URL ou Token do Home Assistant não configurados.")
            return False

        url = f"{ha_url}/api/services/input_text/set_value"
        headers = {"Authorization": f"Bearer {ha_token}", "Content-Type": "application/json"}
        payload = {"entity_id": entity_id, "value": disabled_ids_str}

        response = requests.post(url, headers=headers, data=json.dumps(payload), timeout=10)
        response.raise_for_status()
        
        # print(f"HA_SERVICE: Resposta do Home Assistant: {response.status_code}")
        return True
    except Exception as e:
        current_app.logger.error(f"Erro inesperado ao atualizar o HA para a zona {zone.name}: {e}", exc_info=True)
        return False