# test_api_route.py
import requests
import json

# URL base da nossa API. Altere se necessário.
BASE_URL = "http://127.0.0.1:5000/api"
HEADERS = {"Content-Type": "application/json"}

def test_matched_scan(zone_prefix, finger_id):
    """
    Testa o endpoint para um acesso autorizado (digital encontrada).
    """
    url = f"{BASE_URL}/log_access"
    payload = {
        "zona": zone_prefix,
        "finger_id": finger_id
    }
    
    print(f"\n--- INICIANDO TESTE: Acesso Autorizado ---")
    print(f"URL: {url}")
    print(f"Payload: {json.dumps(payload)}")
    
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

def test_unmatched_scan(zone_prefix):
    """
    Testa o endpoint para um acesso não reconhecido.
    """
    url = f"{BASE_URL}/log_unmatched_access"
    payload = {
        "zona": zone_prefix
    }

    print(f"\n--- INICIANDO TESTE: Acesso Não Reconhecido ---")
    print(f"URL: {url}")
    print(f"Payload: {json.dumps(payload)}")
    
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
    PREFIXO_DA_ZONA_PARA_TESTAR = "accg" 
    
    # Coloque o ID de uma digital que você já cadastrou para essa zona.
    ID_DA_DIGITAL_PARA_TESTAR = 1
    
    # Executa os dois testes
    test_matched_scan(PREFIXO_DA_ZONA_PARA_TESTAR, ID_DA_DIGITAL_PARA_TESTAR)
    test_unmatched_scan(PREFIXO_DA_ZONA_PARA_TESTAR)