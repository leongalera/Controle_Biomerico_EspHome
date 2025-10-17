# Controle Biométrico com ESPHome e Flask

![Python](https://img.shields.io/badge/Python-3.11-blue.svg)
![Flask](https://img.shields.io/badge/Flask-black.svg)
![ESPHome](https://img.shields.io/badge/ESPHome-blueviolet.svg)
![Home Assistant](https://img.shields.io/badge/Home%20Assistant-41B883.svg)

Este projeto é um sistema completo para gerenciamento de controle de acesso biométrico (sensor de digitais R503) e RFID, projetado para se integrar com múltiplos dispositivos ESP32.

A aplicação roda como um **Add-on do Home Assistant**, fornecendo uma interface web amigável para gerenciar zonas de acesso, usuários, grupos de permissão, logs de acesso e muito mais.

## Visão Geral da Arquitetura

```
┌──────────────────┐      ┌──────────────────┐      ┌──────────────────────────┐
│ Dispositivo      │      │ Home Assistant   │      │ Add-on (Este Projeto)    │
│ (ESPHome)        │◄─────► (Automações)     │◄─────► (Interface Web & API)    │
│ - Leitor R503    │      │                  │      │ - Gerencia Usuários/Zonas│
│ - Leitor RFID    │      └──────────────────┘      │ - Banco de Dados (SQLite)│
└──────────────────┘                              └──────────────────────────┘
```

1.  **Dispositivo ESPHome:** Responsável pela leitura da digital ou tag RFID. Ele se comunica diretamente com o Home Assistant.
2.  **Home Assistant:** Atua como o intermediário. Recebe os sinais do ESPHome e, através de automações, chama a API do Add-on para registrar os acessos. Também recebe do Add-on a lista de digitais que devem ser desativadas.
3.  **Add-on (Controle Biométrico):** O cérebro do sistema. Fornece a interface para todo o gerenciamento e armazena os dados. A comunicação com o ESP32 para o cadastro de novas digitais é feita diretamente do Add-on para o dispositivo.

## Funcionalidades

- **Interface Web Completa:** Gerencie Zonas, Grupos de Acesso, Usuários, Senhas e Tags RFID.
- **Cadastro de Digitais Interativo:** Um guia passo a passo na interface web se comunica em tempo real com o sensor R503 para o cadastro de novas digitais.
- **Grupos de Acesso Flexíveis:** Crie regras de acesso por dias da semana e horários específicos, ou libere o acesso 24h.
- **Múltiplas Zonas:** Gerencie diversos dispositivos ESP32 em locais diferentes a partir de um único painel.
- **Monitoramento Detalhado:** Visualize logs de acesso por digital, senha e RFID, com filtros por data, usuário e zona.
- **Ativação/Desativação de Usuários:** Ative ou desative o acesso de um usuário instantaneamente. A alteração é sincronizada com todos os ESPs via Home Assistant.
- **Painel de Administração:** Ferramentas para gerenciar os administradores do sistema e realizar manutenções, como limpeza de digitais e reset de fábrica.

## 1. Instalação como Add-on no Home Assistant

Este projeto é desenhado para rodar como um **Add-on Local**.

1.  **Pré-requisito:** Você precisa ter o Add-on **"Samba share"** ou **"Visual Studio Code"** instalado no seu Home Assistant para poder acessar o sistema de arquivos.

2.  **Copiar os Arquivos:**
    * Acesse o diretório raiz do seu Home Assistant (geralmente `config/`).
    * Navegue até a pasta `addons/`. Se ela não existir, crie-a.
    * Copie a pasta `controle_biometrico` (a pasta que contém o `config.yaml`, `Dockerfile`, etc.) para dentro da pasta `addons/`.

    A estrutura final deve ser: `.../addons/controle_biometrico/config.yaml`.

3.  **Instalar o Add-on:**
    * No Home Assistant, vá para **Configurações > Add-ons > Loja de Add-ons**.
    * Clique no menu de três pontos no canto superior direito e selecione **"Verificar por atualizações"**.
    * Role até o final da página. Uma nova seção chamada **"Add-ons Locais"** aparecerá com o "Controle Biométrico ESPHome".
    * Clique nele e depois em **"Instalar"**. Aguarde o processo terminar.

## 2. Configuração do Add-on

Após a instalação, vá para a aba **"Configuração"** do add-on e preencha os seguintes campos:

-   **`ha_url`**: A URL interna do seu Home Assistant (ex: `http://192.168.0.100:8123` ou `http://homeassistant.local:8123`).
-   **`ha_token`**: Um Token de Acesso de Longa Duração. Para criar um, vá no seu Perfil (clique no seu nome no canto inferior esquerdo) > `Tokens de Acesso de Longa Duração` > `CRIAR TOKEN`.
-   **`initial_admin_user`**: O nome de usuário para o primeiro administrador do painel web (o padrão é `admin`).
-   **`initial_admin_password`**: A senha para o primeiro administrador. **Este campo é obrigatório na primeira inicialização.**

Após preencher, clique em **"SALVAR"** e inicie o add-on.

## 3. Configuração do Dispositivo ESPHome

Abaixo está um exemplo completo e funcional do código `esphome.yaml` para o seu ESP32. Adapte os pinos (`tx_pin`, `rx_pin`, etc.) para a sua placa.

```yaml
esphome:
  name: acesso-principal # Mude para o nome do seu dispositivo
  friendly_name: Acesso Principal

esp32:
  board: esp32dev
  framework:
    type: arduino

# Habilita a API Nativa para comunicação com o Home Assistant e o Add-on
api:
  # Adicione uma chave de criptografia para segurança
  encryption:
    key: "SUA_CHAVE_DE_ENCRIPTACAO_DE_32_BYTES"
  
  # Serviços personalizados para o cadastro/exclusão de digitais
  services:
    - service: gravar
      variables:
        finger_id: int
        num_scans: int
      then:
        - fingerprint_grow.enroll:
            finger_id: !lambda "return finger_id;"
            num_scans: !lambda "return num_scans;"
    - service: excluir
      variables:
        finger_id: int
      then:
        - fingerprint_grow.delete:
            finger_id: !lambda "return finger_id;"
    - service: excluir_todos
      then:
        - fingerprint_grow.clear_database
    - service: cancelar
      then:
        - fingerprint_grow.cancel_enroll

# Sensor de impressão digital
fingerprint_grow:
  id: r503
  sensing_pin: GPIO4
  uart_id: uart_bus
  password: 0x0
  new_password: 0x0
  on_finger_scan_matched:
    then:
      - logger.log:
          format: "Digital correspondente encontrada! ID: %d"
          args: [ 'finger_id' ]
      # Publica o ID no sensor para o HA capturar
      - text_sensor.template.publish:
          id: last_finger_id_matched
          state: !lambda 'return std::to_string(finger_id);'
      # Sua lógica de liberação (ex: acionar um relé)
      - switch.turn_on: rele_porta
  on_finger_scan_unmatched:
    then:
      - logger.log: "Digital não encontrada."
      # Publica um sinal para o HA capturar a falha
      - text_sensor.template.publish:
          id: last_finger_unmatched
          state: "unmatched"

# Comunicação Serial para o sensor R503
uart:
  - id: uart_bus
    tx_pin: GPIO17
    rx_pin: GPIO16
    baud_rate: 57600

# Sensores de texto para comunicação com o Home Assistant
text_sensor:
  # Reporta o ID da última digital válida
  - platform: template
    id: last_finger_id_matched
    name: "Último ID de Digital Válida"
    internal: true
  
  # Reporta uma tentativa de leitura inválida
  - platform: template
    id: last_finger_unmatched
    name: "Última Digital Desconhecida"
    internal: true
    
  # Guarda o status do processo de cadastro para a interface web
  - platform: template
    id: status_cadastro_web
    name: "Status Cadastro Web"
    internal: false # Precisa ser visível para o Add-on

# Exemplo de um relé para abrir uma porta
switch:
  - platform: gpio
    name: "Relé Porta Principal"
    pin: GPIO23
    id: rele_porta
```

## 4. Configuração no Home Assistant

Para que o Home Assistant possa se comunicar com seu Add-on, você precisa adicionar o seguinte ao seu arquivo `configuration.yaml`.

1.  **Abra o arquivo `configuration.yaml`**.
2.  Adicione o bloco de código abaixo:

```yaml
# configuration.yaml

rest_command:
  log_biometria_sucesso:
    url: "http://a0d7b954-controle_biometrico/api/log_access"
    method: POST
    content_type: "application/json"
    payload: '{"zona": "{{ zona }}", "finger_id": {{ finger_id }} }'

  log_biometria_falha:
    url: "http://a0d7b954-controle_biometrico/api/log_unmatched_access"
    method: POST
    content_type: "application/json"
    payload: '{"zona": "{{ zona }}"}'
```
* **Importante:** O `controle_biometrico` na URL corresponde ao `slug` do seu add-on. Se você o alterou, atualize a URL aqui também.

3.  **Reinicie o Home Assistant** após salvar o arquivo.

## 5. Criação das Automações

Finalmente, crie as automações que conectam tudo.

1.  Vá para **Configurações > Automações e Cenas > + CRIAR AUTOMAÇÃO**.
2.  Crie as duas automações abaixo.

---

**Automação 1: Registrar Acesso com Sucesso**

Esta automação é acionada quando o ESPHome envia um ID de digital válida.

-   **Gatilho (Quando):**
    -   **Tipo de Gatilho:** Estado
    -   **Entidade:** `text_sensor.acesso_principal_ultimo_id_de_digital_valida` (substitua `acesso-principal` pelo nome do seu dispositivo).
-   **Ação (Então fazer):**
    -   **Tipo de Ação:** Chamar um serviço
    -   **Serviço:** `rest_command.log_biometria_sucesso`
    -   **Dados (em modo YAML):**
        ```yaml
        zona: "accp" # Use o prefixo de 4 letras que você cadastrou para esta Zona no Add-on
        finger_id: "{{ trigger.to_state.state }}"
        ```

---

**Automação 2: Registrar Tentativa Falha**

Esta automação é acionada quando o ESPHome reporta uma leitura de digital desconhecida.

-   **Gatilho (Quando):**
    -   **Tipo de Gatilho:** Estado
    -   **Entidade:** `text_sensor.acesso_principal_ultima_digital_desconhecida`
-   **Ação (Então fazer):**
    -   **Tipo de Ação:** Chamar um serviço
    -   **Serviço:** `rest_command.log_biometria_falha`
    -   **Dados (em modo YAML):**
        ```yaml
        zona: "accp" # Use o mesmo prefixo de 4 letras da Zona
        ```

Com tudo configurado, seu sistema estará 100% operacional!