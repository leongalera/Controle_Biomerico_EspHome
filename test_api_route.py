# test_api_route.py
import requests
import json

# URL base da nossa API. Altere se necessário.
BASE_URL = "http://127.0.0.1:5000/api"
HEADERS = {"Content-Type": "application/json"}

def test_matched_scan(zone_prefix, finger_id):
    """
    Testa o endpoint para um acesso autorizado por digital.
    """
    url = f"{BASE_URL}/log_access"
    payload = { "zona": zone_prefix, "finger_id": finger_id }
    print(f"\n--- INICIANDO TESTE: Log de Acesso por Digital ---")
    print(f"URL: {url}")
    print(f"Payload: {json.dumps(payload)}")
    _make_request(url, payload)

def test_unmatched_scan(zone_prefix):
    """
    Testa o endpoint para um acesso não reconhecido por digital.
    """
    url = f"{BASE_URL}/log_unmatched_access"
    payload = { "zona": zone_prefix }
    print(f"\n--- INICIANDO TESTE: Log de Digital Não Reconhecida ---")
    print(f"URL: {url}")
    print(f"Payload: {json.dumps(payload)}")
    _make_request(url, payload)

# --- FUNÇÃO NOVA ---
def test_password_verification(zone_prefix, password):
    """
    Testa o endpoint de verificação de senha.
    """
    url = f"{BASE_URL}/verify_password"
    payload = {
        "zona": zone_prefix,
        "password": password
    }
    print(f"\n--- INICIANDO TESTE: Verificação de Senha ---")
    print(f"URL: {url}")
    print(f"Payload: {json.dumps(payload)}")
    _make_request(url, payload)

def _make_request(url, payload):
    """Função auxiliar para fazer a requisição e imprimir o resultado."""
    try:
        response = requests.post(url, data=json.dumps(payload), headers=HEADERS)
        print("--- RESPOSTA DO SERVIDOR ---")
        print(f"Status Code: {response.status_code}")
        try:
            print(f"Resposta (JSON): {response.json()}")
        except json.JSONDecodeError:
            print(f"Resposta (Texto): {response.text}")
    except requests.exceptions.ConnectionError:
        print("--- ERRO: Não foi possível conectar ao servidor. ---")


if __name__ == "__main__":
    # --- CONFIGURE SEU TESTE AQUI ---
    # Coloque o prefixo de uma zona que você já cadastrou no painel web.
    PREFIXO_DA_ZONA_PARA_TESTAR = "accp" 
    
    # Coloque o ID de uma digital que você já cadastrou para essa zona.
    ID_DA_DIGITAL_PARA_TESTAR = 1

    # Coloque uma senha que você cadastrou e associou à zona acima.
    SENHA_VALIDA_PARA_A_ZONA = "1234"

    # Coloque uma senha que não existe.
    SENHA_INVALIDA = "9999"
    
    # --- Executa os testes ---
    # test_matched_scan(PREFIXO_DA_ZONA_PARA_TESTAR, ID_DA_DIGITAL_PARA_TESTAR)
    # test_unmatched_scan(PREFIXO_DA_ZONA_PARA_TESTAR)
    
    print("\n=================================================")
    print("Teste 1: Verificando uma senha válida para a zona...")
    test_password_verification(PREFIXO_DA_ZONA_PARA_TESTAR, SENHA_VALIDA_PARA_A_ZONA)
    
    print("\n=================================================")
    print("Teste 2: Verificando uma senha que não existe...")
    test_password_verification(PREFIXO_DA_ZONA_PARA_TESTAR, SENHA_INVALIDA)
    print("=================================================")