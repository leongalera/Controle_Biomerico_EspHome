# /addons/controle_biometrico/Dockerfile
ARG BUILD_FROM
FROM ${BUILD_FROM}

# Define variáveis de ambiente no formato moderno
ENV LANG="C.UTF-8" \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# Copia todo o código do add-on para dentro do container
WORKDIR /app
COPY . .

# **NOVO**: Garante que o script de inicialização seja executável
RUN chmod +x /app/run.sh

# Instala as dependências Python
RUN pip install --no-cache-dir -r requirements.txt

# Expõe a porta da aplicação
EXPOSE 5000

# **CORRIGIDO**: Aponta para o caminho correto do script
CMD [ "/app/run.sh" ]