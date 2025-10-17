# config.py
import os

class Config:
    # A Secret Key continua sendo importante, mas agora a definimos diretamente
    # ou lemos de uma variável de ambiente que o add-on pode fornecer.
    SECRET_KEY = os.environ.get('SECRET_KEY', 'uma-chave-secreta-padrao-muito-segura')

    # Lê a URL do banco de dados da variável de ambiente fornecida pelo Supervisor
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Lê as credenciais do Home Assistant das variáveis de ambiente
    HA_URL = os.environ.get('HA_URL')
    HA_TOKEN = os.environ.get('HA_TOKEN')
    
    SCHEDULER_API_ENABLED = True