# app/services/esphome_service.py

import asyncio
from flask import current_app
from aioesphomeapi import APIClient, TextSensorState
from app.models import db, Fingerprint

# Variável para armazenar a 'key' interna do nosso sensor alvo
TARGET_ENTITY_KEY = None

# Dicionário para guardar os sinais de cancelamento
CANCEL_ENROLLMENT_FLAGS = {}

async def enroll_fingerprint(hostname, api_key, finger_id_on_sensor, q, user_id, zone_id, finger_name, num_scans=3):
    cli = APIClient(hostname, 6053, password=None, noise_psk=api_key)
    enrollment_done_event = asyncio.Event()
    final_status = "ERRO"

    # Garante que a "bandeira" de cancelamento para este usuário comece como falsa
    CANCEL_ENROLLMENT_FLAGS[user_id] = False

    async def _check_for_cancel_request():
        nonlocal final_status
        """Esta tarefa roda em paralelo, verificando a bandeira de cancelamento."""
        while not enrollment_done_event.is_set():
            if CANCEL_ENROLLMENT_FLAGS.get(user_id):
                q.put("INFO: Cancelamento solicitado pelo usuário.")
                try:
                    # Encontra e executa o serviço 'cancelar' do esphome
                    entities, services = await cli.list_entities_services()
                    cancel_service = next((s for s in services if s.name == 'cancelar'), None)
                    if cancel_service:
                        cli.execute_service(cancel_service, {})
                    else:
                        q.put("AVISO: Serviço 'cancelar' não encontrado no YAML do ESPHome.")
                except Exception as e:
                    q.put(f"ERRO ao tentar enviar comando de cancelar: {e}")

                final_status = "CANCELADO"
                enrollment_done_event.set() # Força o término do processo principal
                break
            await asyncio.sleep(0.5)

    try:
        await cli.connect(login=True)
        q.put("INFO: Conexão bem-sucedida.")
        
        # Inicia a tarefa que fica vigiando o pedido de cancelamento
        cancel_checker_task = asyncio.create_task(_check_for_cancel_request())

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
        
        await asyncio.wait_for(enrollment_done_event.wait(), timeout=120.0)
   
        cancel_checker_task.cancel()

        # A função agora apenas retorna o status final
        return final_status

    except asyncio.TimeoutError:
        q.put("INFO: O processo de cadastro demorou demais e foi encerrado (timeout).")
        current_app.logger.error("O processo de cadastro demorou demais e foi encerrado (timeout).")

        # Se deu timeout, tenta enviar o comando de cancelar para o ESP32
        try:
            q.put("INFO: Cancelamento solicitado.")
            current_app.logger.warning("Timeout! Tentando cancelar o cadastro no ESP32...")
            entities, services = await cli.list_entities_services()
            cancel_service = next((s for s in services if s.name == 'cancelar'), None)
            if cancel_service:
                cli.execute_service(cancel_service, {})
                current_app.logger.info("Comando de cancelar enviado ao ESP32 após o timeout.")
                q.put("INFO: Cadastro cancelado.")
        except Exception as cancel_exc:
            current_app.logger.error(f"Falha ao tentar cancelar no ESP32 após o timeout: {cancel_exc}")

    except Exception as e:
        q.put(f"ERRO: {e}")
    finally:
        await cli.disconnect()



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