# Controle Biométrico com ESPHome e Flask

![Python](https://img.shields.io/badge/Python-3.9%2B-blue.svg)
![Flask](https://img.shields.io/badge/Flask-2.x-black.svg)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-1.4%2B-orange.svg)
![ESPHome](https://img.shields.io/badge/ESPHome-blueviolet.svg)

Este projeto é um sistema de backend para gerenciamento de controle de acesso biométrico, projetado para se integrar com dispositivos IoT que utilizam o firmware ESPHome. A aplicação é construída com Flask e utiliza SQLAlchemy para persistência de dados.

## Visão Geral

O sistema consiste em uma API RESTful que permite:

- Cadastrar, visualizar, editar e remover usuários.
- Registrar e gerenciar dados biométricos (ex: impressões digitais) para cada usuário.
- Sincronizar a lista de usuários autorizados com dispositivos ESPHome.
- Receber e registrar logs de acesso (bem-sucedidos ou falhos) dos dispositivos.

## Arquitetura Conceitual

```
┌──────────────────┐      ┌──────────────────┐      ┌────────────────┐
│ Dispositivo      │      │ Servidor Flask   │      │ Banco de Dados │
│ (ESPHome)        │◄─────► (API REST)       │◄─────► (PostgreSQL/   │
│ - Leitor Biomét. │      │ - Lógica de Neg. │      │  SQLite)       │
└──────────────────┘      └──────────────────┘      └────────────────┘
```

1.  **Dispositivo ESPHome:** Responsável pela captura da biometria. Ele consulta a API do servidor Flask para validar um acesso e envia logs.
2.  **Servidor Flask:** O cérebro do sistema. Expõe endpoints para gerenciar usuários e recebe dados dos dispositivos.
3.  **Banco de Dados:** Armazena todas as informações, como usuários, permissões e logs de acesso.

## Tecnologias Utilizadas

- **Backend:** Python, Flask
- **ORM:** SQLAlchemy
- **Migrations:** Flask-Migrate, Alembic
- **Firmware IoT:** ESPHome

## Configuração do Ambiente de Desenvolvimento

Siga os passos abaixo para configurar e executar o projeto localmente.

### 1. Pré-requisitos

- Python 3.9 ou superior
- Git

### 2. Clonar o Repositório

```bash
git clone <URL_DO_SEU_REPOSITORIO>
cd Controle_Biomerico_EspHome
```

### 3. Criar e Ativar o Ambiente Virtual

```bash
# Para Windows
python -m venv venv
.\venv\Scripts\activate

# Para Linux/macOS
python3 -m venv venv
source venv/bin/activate
```

### 4. Instalar as Dependências

Crie um arquivo `requirements.txt` com as bibliotecas do seu projeto (ex: `Flask`, `Flask-SQLAlchemy`, `Flask-Migrate`, `psycopg2-binary`, etc.) e execute:

```bash
pip install -r requirements.txt
```

### 5. Configurar o Banco de Dados

A aplicação utiliza Flask-Migrate para gerenciar o esquema do banco de dados.

Primeiro, configure a variável de ambiente com a URI do seu banco de dados. Por exemplo, para SQLite:

```bash
# No Windows (PowerShell)
$env:DATABASE_URL="sqlite:///app.db"

# No Linux/macOS
export DATABASE_URL="sqlite:///app.db"
```

Em seguida, aplique as migrations:

```bash
flask db upgrade
```

### 6. Executar a Aplicação

```bash
flask run
```

A aplicação estará disponível em `http://127.0.0.1:5000`.