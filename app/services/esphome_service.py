# app/services/esphome_service.py

import asyncio
from flask import current_app
from aioesphomeapi import APIClient, TextSensorState
from app.models import db, Fingerprint

# Variável para armazenar a 'key' interna do nosso sensor alvo
TARGET_ENTITY_KEY = None

async def enroll_fingerprint(hostname, api_key, finger_id_on_sensor, q, user_id, zone_id, finger_name, num_scans=3):
    """
    Versão final e corrigida.
    """
    cli = APIClient(hostname, 6053, password=None, noise_psk=api_key)
    enrollment_done_event = asyncio.Event()
    final_status = "ERRO"

    try:
        await cli.connect(login=True)
        q.put("INFO: Conexão bem-sucedida.")
        
        # Função de callback que será chamada pela biblioteca
        def on_state(state):
            nonlocal final_status

            if isinstance(state, TextSensorState) and state.key == TARGET_ENTITY_KEY:
                status_msg = state.state
                q.put(f"STATUS: {status_msg}")
                # Se o processo terminou, aciona nosso sinalizador
                if "SUCESSO" in status_msg:
                    final_status = "SUCESSO"
                    enrollment_done_event.set()
                elif "FALHA" in status_msg:
                    final_status = "FALHA"
                    enrollment_done_event.set()


        entity_list, _ = await cli.list_entities_services()
        # O loop agora itera sobre a variável correta: 'entity_list'
        for entity in entity_list:
            if "Status Cadastro Web" in entity.name:
                TARGET_ENTITY_KEY = entity.key
                q.put(f"Entidade encontrada! Nome: '{entity.name}', Key interna: {TARGET_ENTITY_KEY}")
                break

        cli.subscribe_states(on_state)

        entities, services = await cli.list_entities_services()
        gravar_service = next((s for s in services if s.name == 'gravar'), None)

        if not gravar_service:
            raise ValueError("O serviço 'gravar' não foi encontrado no dispositivo.")

        q.put("INFO: Comando de gravação enviado. Siga as instruções no sensor.")
        cli.execute_service(gravar_service, {"finger_id": finger_id_on_sensor, "num_scans": num_scans})
        
        await asyncio.wait_for(enrollment_done_event.wait(), timeout=60.0)
        
        # print("status final:", final_status)
        if final_status == "SUCESSO":
            q.put(f"STATUS: {final_status}")
            current_app.logger.info("Salvando digital no banco de dados...")
            try:
                new_fingerprint = Fingerprint(
                    user_id=user_id,
                    zone_id=zone_id,
                    finger_id_on_sensor=finger_id_on_sensor,
                    finger_name=finger_name
                )
                db.session.add(new_fingerprint)
                db.session.commit()
                q.put("INFO: Digital salva com sucesso no banco de dados!")

            except Exception as db_exc:
                db.session.rollback()
                q.put(f"ERRO FATAL: Falha ao salvar no banco de dados: {db_exc}")
                current_app.logger.error(f"Falha ao salvar no BD: {db_exc}", exc_info=True)

    except asyncio.TimeoutError:
        q.put("ERRO: O processo de cadastro demorou demais (timeout).")
    except Exception as e:
        q.put(f"ERRO: {e}")
    finally:
        await cli.disconnect()
        current_app.logger.info("AIOESPHOMEAPI: Cliente desconectado.")
        q.put(None)


async def delete_fingerprint_from_sensor(hostname, api_key, finger_id_to_delete):
    # A assinatura da função não tem mais o 'loop'
    cli = APIClient(hostname, 6053, password=None, noise_psk=api_key)
    try:
        await cli.connect(login=True)
        entities, services = await cli.list_entities_services()
        excluir_service = next((s for s in services if s.name == 'excluir'), None)
        if not excluir_service:
            raise ValueError("O serviço 'excluir' não foi encontrado.")
        cli.execute_service(excluir_service, {"finger_id": finger_id_to_delete})
        return {"success": True}
    except Exception as e:
        return {"success": False, "message": str(e)}
    finally:
        await cli.disconnect()


async def delete_all_fingerprints_from_sensor(hostname, api_key):
    """
    Usa aioesphomeapi para apagar TODAS as digitais de um sensor.
    Versão corrigida com a sintaxe correta da API.
    """
    cli = APIClient(hostname, 6053, password=None, noise_psk=api_key)
    try:
        await cli.connect(login=True)
        
        # Encontra o serviço 'excluir_todos' definido no seu YAML
        entities, services = await cli.list_entities_services()
        service_to_run = next((s for s in services if s.name == 'excluir_todos'), None)
        
        if not service_to_run:
            raise ValueError("O serviço 'excluir_todos' não foi encontrado no dispositivo ESP32.")

        # Executa o serviço sem dados, e sem 'await'
        cli.execute_service(service_to_run, {})
        
        await asyncio.sleep(1) # Delay para garantir que o comando seja processado
        
        return {"success": True, "message": "Comando para apagar todas as digitais foi enviado com sucesso."}
    except Exception as e:
        return {"success": False, "message": f"Falha ao enviar comando para apagar todas as digitais: {e}"}
    finally:
        # Garante que a desconexão sempre ocorra
        await cli.disconnect()