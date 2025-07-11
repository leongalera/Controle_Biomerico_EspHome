# Sistema de Controle de Acesso Biométrico com ESPHome e Flask

![Python](https://img.shields.io/badge/python-3.12-blue.svg)
![Flask](https://img.shields.io/badge/flask-%23000.svg?style=for-the-badge&logo=flask&logoColor=white)
![Home Assistant](https://img.shields.io/badge/home%20assistant-%2341B8F1.svg?style=for-the-badge&logo=home-assistant&logoColor=white)
![ESPHome](https://img.shields.io/badge/esphome-%2300A9D4.svg?style=for-the-badge&logo=esphome&logoColor=white)

Este projeto é uma solução completa e de código aberto para controle de acesso, utilizando módulos ESP32 com sensores biométricos (R503), integrados ao Home Assistant e gerenciados por um painel de controle web robusto desenvolvido em Python com o framework Flask.

## ✨ Funcionalidades Principais

* **Painel de Gerenciamento Web:** Interface completa para gerenciar todas as facetas do sistema.
* **Gestão de Entidades:** CRUD completo para Usuários, Grupos de Acesso e Zonas (módulos ESP32).
* **Controle de Acesso por Horário:** Crie grupos com permissões de acesso baseadas em dias da semana e horários específicos.
* **Cadastro Remoto de Digitais:** Inicie e acompanhe o processo de cadastro de digitais diretamente pela interface web, com feedback em tempo real.
* **Monitoramento e Auditoria:** Registre e visualize todos os eventos de acesso, incluindo tentativas autorizadas, não reconhecidas e negadas (por inatividade ou fora de horário).
* **Integração com Home Assistant:** Utilize o Home Assistant como uma ponte de comunicação robusta e para orquestrar regras complexas.
* **Autonomia do Dispositivo:** A decisão de abrir a porta é feita instantaneamente no ESP32, garantindo velocidade e funcionamento mesmo que o painel web esteja offline.

## 🏗️ Arquitetura do Sistema

O sistema opera com três componentes principais que se comunicam de forma orquestrada:

1.  **Módulo ESP32 (ESPHome):** O "músculo" do sistema. Ele é responsável por ler a digital e tomar a decisão final de abrir a porta. Ele mantém uma lista local de IDs de digitais bloqueadas.
2.  **Home Assistant:** O "mensageiro" e cérebro das regras. Ele recebe eventos do ESP32 (acesso autorizado, negado, etc.) e os encaminha para o Painel Web. Ele também serve como um "quadro de avisos" (`input_text`) onde o Painel Web publica a lista de digitais bloqueadas.
3.  **Painel Web (Flask):** A "inteligência central" e a interface de gerenciamento. É a fonte da verdade sobre usuários, grupos e regras de horário. Ele atualiza o Home Assistant com as regras de bloqueio e recebe os logs de acesso.

## 🚀 Guia de Instalação e Configuração

Siga os passos abaixo para configurar o ambiente de desenvolvimento e produção.

### 1. Pré-requisitos
* **Git:** Para clonar o repositório.
* **Python:** Versão **3.11** ou **3.12**.

### 2. Configuração do Ambiente Local (Painel Web)

**a. Clone o Repositório:**

```bash
git clone https://github.com/leongalera/Controle_Biomerico_EspHome.git
cd Controle_Biomerico_EspHome
```

**b. Crie e Ative o Ambiente Virtual (`venv`):**

```bash
# No Windows
py -3.12 -m venv venv
.\venv\Scripts\activate

# No macOS/Linux
python3.12 -m venv venv
source venv/bin/activate
```

**c. Instale as Dependências:**
Crie um arquivo `requirements.txt` com o conteúdo abaixo e depois execute `pip install -r requirements.txt`.

```
# requirements.txt
Flask
Flask-SQLAlchemy
Flask-Migrate
Flask-Login
python-dotenv
requests
bcrypt
wtforms-sqlalchemy
Flask-APScheduler
pytz
aioesphomeapi
waitress
```

```bash
pip install -r requirements.txt
```

**d. Crie o Arquivo de Configuração `.env`:**
Crie o arquivo `.env` na raiz do projeto e preencha com suas informações.

```ini
# .env
SECRET_KEY='sua-chave-secreta-muito-forte-e-aleatoria'
DATABASE_URI='sqlite:///access_control.db'
HA_URL='http://IP_DO_SEU_HOME_ASSISTANT:8123'
HA_TOKEN='SEU_TOKEN_DE_ACESSO_DE_LONGA_DURAÇÃO_DO_HA'
SCHEDULER_API_ENABLED=True
```

**e. Configure o Banco de Dados:**

```bash
# No Windows CMD: set FLASK_APP=run.py
# No PowerShell: $env:FLASK_APP="run.py"
# No macOS/Linux: export FLASK_APP=run.py

flask db init
flask db migrate -m "Initial database creation"
flask db upgrade
```

**f. Crie o Usuário Administrador:**

```bash
flask create-admin
```

### 3\. Configuração do ESPHome e Home Assistant

Para o funcionamento completo, siga o **Manual de Configuração do Home Assistant** gerado anteriormente. Ele detalha os passos para criar:

1.  Os auxiliares `input_text` para cada zona.
2.  Os `rest_command` no `configuration.yaml` para se comunicar com a API do painel.
3.  As `automations` no `automations.yaml` para reagir aos eventos do ESP32.

-----

## 💻 Executando a Aplicação

Para iniciar o servidor para desenvolvimento ou produção local:

```bash
# Garanta que seu venv está ativo
python serve.py
```

A aplicação estará acessível em `http://127.0.0.1:5000`.

-----

## 🏭 Colocando em Produção

Para um ambiente de produção 24/7, considere os seguintes pontos:

### **Banco de Dados**

Migre do SQLite para um servidor de banco de dados mais robusto como **PostgreSQL** ou **MySQL**. Isso envolve instalar o servidor, o driver Python correspondente (ex: `psycopg2-binary`) e alterar a `DATABASE_URI` no seu arquivo de configuração.

### **Rodando como um Add-on do Home Assistant (Método Recomendado)**

A maneira mais integrada e robusta de rodar esta aplicação é como um Add-on local dentro do próprio Home Assistant OS. Isso envolve:

1.  **Alterar a `DATABASE_URI`** no `.env` para `sqlite:////share/access_control.db` para persistência.
2.  **Criar um `Dockerfile`** para empacotar a aplicação.
3.  **Criar um `config.yaml`** para descrever o Add-on para o Supervisor do HA.
4.  **Copiar a pasta inteira do projeto** para a pasta `/addons` da sua instalação do Home Assistant (via Samba ou SSH).
5.  **Instalar e iniciar** o Add-on local através da loja de Add-ons do Home Assistant.

### **Rodando em um Servidor Dedicado**

Se preferir um servidor separado (Linux, por exemplo):

  * **Servidor WSGI:** O `waitress` já é pronto para produção. Uma alternativa comum no Linux é o `Gunicorn` combinado com um proxy reverso como o `Nginx`.
  * **Rodar como Serviço:** Configure a aplicação para rodar como um serviço de sistema (`systemd` no Linux) para que ela inicie automaticamente com o servidor e reinicie em caso de falhas.
  * **IP Estático:** Garanta que o servidor tenha um endereço IP estático na sua rede para que o Home Assistant e os ESP32 possam sempre encontrá-lo.

-----

## 📜 Licença

Este projeto é distribuído sob a licença MIT.