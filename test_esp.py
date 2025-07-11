import asyncio
from aioesphomeapi import APIClient

# --- Suas Configurações ---
ESP_HOST = "acesso-garagem.local"
ESP_API_KEY = "DtbXdqwkbbV9P7m3vadxMvvaAwrDZCAbKRBzO8LLDYU="

# Defina aqui a PARTE do nome que você quer buscar.
# O código irá encontrar qualquer sensor cujo nome contenha este texto.
# É case-sensitive (diferencia maiúsculas de minúsculas).
SUBSTRING_A_BUSCAR = "Status Cadastro Web" 
# -------------------------

def on_state_change(state):
    """
    Função de callback que agora filtra se o NOME do sensor CONTÉM a substring.
    """
    # A verificação principal acontece aqui com o operador 'in'
    if hasattr(state, 'name') and SUBSTRING_A_BUSCAR in state.name:
        # Imprimimos o nome completo do sensor para saber qual foi encontrado
        # e também o seu estado.
        print(f"Match encontrado em '{state.name}'. Novo estado: '{state.state}'")


async def main():
    """Função principal para conectar e se inscrever."""
    cli = APIClient(ESP_HOST, 6053, password=None, noise_psk=ESP_API_KEY)
    
    try:
        await cli.connect(login=True)
        print("Conexão bem-sucedida!")

        # Inscreve nossa função de callback para receber todas as atualizações
        cli.subscribe_states(on_state_change)
        print(f"Inscrito com sucesso! Aguardando atualizações de sensores cujo nome contenha '{SUBSTRING_A_BUSCAR}'...")
        
        # Mantém o script rodando para escutar
        await asyncio.sleep(300)

    except Exception as e:
        print(f"Ocorreu um erro: {e}")
    finally:
        if cli.is_connected:
            await cli.disconnect()
            print("Desconectado.")

# Inicia o programa
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Programa interrompido pelo usuário.")