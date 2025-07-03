import asyncio
import os
from dotenv import load_dotenv
from py_ha_ws_client import HomeAssistantWsClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models import Dispositivo, Digital, LogAcesso, Pessoa

# Carrega as variáveis do .env
load_dotenv()

# Configurações
DATABASE_URL = "sqlite:///instance/controle_acesso.db"
HA_URL = os.getenv("HA_URL")
HA_TOKEN = os.getenv("HA_TOKEN")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

async def main():
    async with HomeAssistantWsClient(HA_URL, HA_TOKEN) as client:
        print("Conectado ao Home Assistant. Aguardando eventos de biometria...")
        
        event_types_to_listen = [
            "esphome.acc_finger_scan_matched",
            "esphome.acc_finger_scan_unmatched"
        ]

        @client.on_event
        async def on_new_event(event):
            if event["event_type"] in event_types_to_listen:
                data = event["data"]
                print(f"Evento de acesso recebido: {data}")
                
                db_session = SessionLocal()
                try:
                    # 'zona' no seu YAML é o PrefixoNome. Assumindo que o hostname é o codename.
                    # Vamos usar o 'codename' (ex: 'acesso-principal') como identificador único.
                    hostname = data.get("zona") # Seu YAML manda o Prefixo, ex: 'accp - '
                    # Precisamos encontrar o dispositivo pelo hostname. Ex: 'acesso_principal'
                    dispositivo = db_session.query(Dispositivo).filter(Dispositivo.hostname.like(f"%{hostname}%")).first()
                    if not dispositivo:
                        print(f"Alerta: Dispositivo com hostname/zona '{hostname}' não foi encontrado no banco de dados.")
                        return

                    finger_id = data.get("finger_id")
                    status = "Autorizado" if event["event_type"] == "esphome.acc_finger_scan_matched" else "Negado"
                    
                    digital = db_session.query(Digital).filter_by(id=finger_id, dispositivo_id=dispositivo.id).first()
                    
                    log = LogAcesso(
                        dispositivo_id=dispositivo.id,
                        finger_id=finger_id,
                        nome_dispositivo=dispositivo.nome,
                        nome_pessoa=digital.pessoa.nome if digital else "Desconhecido",
                        nome_dedo=digital.nome_dedo if digital else "N/A",
                        status=status
                    )
                    db_session.add(log)
                    db_session.commit()
                    print(f"Log salvo: {log.nome_pessoa} - {log.status} em {log.nome_dispositivo}")
                except Exception as e:
                    print(f"Erro ao processar e salvar o log: {e}")
                finally:
                    db_session.close()

        await client.subscribe_events(event_types_to_listen)
        await client.wait() # Mantém a conexão ativa

if __name__ == "__main__":
    if not HA_URL or not HA_TOKEN:
        print("Erro: Variáveis de ambiente HA_URL ou HA_TOKEN não definidas no arquivo .env")
    else:
        try:
            asyncio.run(main())
        except KeyboardInterrupt:
            print("\nListener de eventos encerrado pelo usuário.")