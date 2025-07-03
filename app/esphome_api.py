import asyncio
from aioesphomeapi import APIClient

async def call_esphome_service(ip: str, key: str, service_name: str, service_data: dict):
    """Conecta a um ESP específico e chama um serviço."""
    cli = APIClient(ip, 6053, "", encryption_key=key)
    try:
        await asyncio.wait_for(cli.connect(login=True), timeout=5.0)
        await asyncio.wait_for(cli.execute_service(service_name, service_data), timeout=5.0)
        return {"success": True}
    except asyncio.TimeoutError:
        return {"success": False, "message": "Timeout: O dispositivo não respondeu a tempo."}
    except Exception as e:
        return {"success": False, "message": str(e)}
    finally:
        if cli.connected:
            await cli.disconnect()

async def get_esphome_entity_state(ip: str, key: str, entity_name: str):
    """Conecta a um ESP e retorna o estado de uma entidade pelo seu NOME."""
    cli = APIClient(ip, 6053, "", encryption_key=key)
    try:
        await asyncio.wait_for(cli.connect(login=True), timeout=5.0)
        entities = await cli.list_entities_services()
        for entity in entities[0]:
            if entity.name == entity_name:
                return {"success": True, "state": entity.state}
        return {"success": False, "message": f"Entidade '{entity_name}' não encontrada."}
    except asyncio.TimeoutError:
        return {"success": False, "message": "Timeout: O dispositivo não respondeu a tempo."}
    except Exception as e:
        return {"success": False, "message": str(e)}
    finally:
        if cli.connected:
            await cli.disconnect()