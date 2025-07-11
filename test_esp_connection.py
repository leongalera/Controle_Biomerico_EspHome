# test_esp_connection.py
import asyncio
import logging
from aioesphomeapi import APIClient

# --- CONFIGURE AQUI ---
ESP_HOST = "acesso-garagem.local"
ESP_API_KEY = "DtbXdqwkbbV9P7m3vadxMvvaAwrDZCAbKRBzO8LLDYU="
# --------------------

# Configuração de logging para vermos todas as mensagens
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

async def main():
    """Função principal para conectar e testar o ESP32."""
    logging.info(f"Iniciando conexão ao host: {ESP_HOST}")
    logging.info(f"ESP_API_KEY: {ESP_API_KEY}")

    cli = APIClient(ESP_HOST, 6053, password=None,  noise_psk=ESP_API_KEY)

    try:
        logging.info(f"Tentando conectar ao host: {ESP_HOST}")
        await cli.connect(login=True)
        logging.info("Conexão bem-sucedida!")

        # Passo extra: Tenta listar as entidades para confirmar a comunicação
        logging.info("Listando entidades e serviços...")
        entities = await cli.list_entities_services()
        print("\n--- ENTIDADES ENCONTRADAS ---")
        for entity in entities[0]:
            print(f"- {entity.name} (key: {entity.key}, type: {entity.object_id})")
        print("---------------------------\n")

    except Exception as e:
        logging.error(f"Ocorreu um erro durante a conexão ou comunicação: {e}", exc_info=True)

    finally:
        logging.info("Desconectando do host.")
        await cli.disconnect()

if __name__ == "__main__":
    # Roda a função assíncrona
    asyncio.run(main())