# serve.py
from waitress import serve
from run import app  # Importa a variável 'app' do nosso arquivo run.py
import logging

logging.basicConfig(level=logging.ERROR, format='%(asctime)s %(levelname)s %(name)s %(message)s')

if __name__ == "__main__":
    print("INFO: Iniciando servidor de produção Waitress em http://0.0.0.0:5000")
    serve(app, host='0.0.0.0', port=5000, threads=8)