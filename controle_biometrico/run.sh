#!/usr/bin/with-contenv bashio

# ==============================================================================
# Iniciação do Add-on
# ==============================================================================
bashio::log.info "Iniciando o Add-on Controle Biométrico..."

# Lê as configurações do config.yaml e as exporta como variáveis de ambiente
export DATABASE_URL=$(bashio::config 'database_url')
export HA_URL=$(bashio::config 'ha_url')
export HA_TOKEN=$(bashio::config 'ha_token')
export INITIAL_ADMIN_USER=$(bashio::config 'initial_admin_user')
export INITIAL_ADMIN_PASSWORD=$(bashio::config 'initial_admin_password')

if [[ -z "$INITIAL_ADMIN_PASSWORD" ]]; then
    bashio::log.warning "A senha inicial do administrador não foi definida."
    bashio::log.warning "Se nenhum administrador existir, o sistema não será acessível."
    bashio::log.warning "Por favor, defina a senha na aba 'Configuração' e reinicie o add-on."
fi

bashio::log.info "URL do Banco de Dados: ${DATABASE_URL}"
bashio::log.info "URL do Home Assistant: ${HA_URL}"

# Garante que o diretório do banco de dados exista
DATA_PATH=/data/
if ! bashio::fs.directory_exists "${DATA_PATH}"; then
    mkdir -p "${DATA_PATH}"
fi

# ==============================================================================
# Aplica as Migrações do Banco de Dados
# ==============================================================================
bashio::log.info "Verificando e aplicando migrações do banco de dados..."
flask db upgrade

# ==============================================================================
# Cria o Usuário Administrador Inicial (se necessário)
# ==============================================================================
bashio::log.info "Verificando o usuário administrador inicial..."
python3 /app/create_initial_admin.py

# ==============================================================================
# Inicia a Aplicação Principal
# ==============================================================================
# bashio::log.info "Iniciando o servidor web..."
# python3 -u serve.py

# ==============================================================================
# Inicia a Aplicação Principal com Gunicorn
# ==============================================================================
bashio::log.info "Iniciando o servidor web com Gunicorn..."
exec gunicorn --bind "0.0.0.0:5000" --workers 4 --forwarded-allow-ips="*" "run:app"
