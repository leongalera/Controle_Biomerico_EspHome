# app/routes.py
import asyncio
from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from .models import db, Pessoa, Dispositivo, Digital, LogAcesso
from .esphome_api import call_esphome_service, get_esphome_entity_state

bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    # Dashboard com os últimos 10 logs
    logs = LogAcesso.query.order_by(LogAcesso.timestamp.desc()).limit(10).all()
    return render_template('index.html', logs=logs)

# --- ROTAS CRUD PARA PESSOAS ---
@bp.route('/pessoas')
def listar_pessoas():
    pessoas = Pessoa.query.all()
    return render_template('pessoas.html', pessoas=pessoas)

@bp.route('/pessoas/nova', methods=['POST'])
def nova_pessoa():
    nome = request.form.get('nome')
    if nome:
        # Verifica se a pessoa já existe
        if not Pessoa.query.filter_by(nome=nome).first():
            db.session.add(Pessoa(nome=nome))
            db.session.commit()
            flash('Pessoa adicionada com sucesso!', 'success')
        else:
            flash('Uma pessoa com este nome já existe.', 'warning')
    return redirect(url_for('main.listar_pessoas'))

@bp.route('/pessoas/<int:id>')
def detalhe_pessoa(id):
    pessoa = Pessoa.query.get_or_404(id)
    dispositivos = Dispositivo.query.all()
    # Pega as digitais da pessoa e agrupa por dispositivo
    digitais_por_dispositivo = {}
    for digital in pessoa.digitais:
        if digital.dispositivo.nome not in digitais_por_dispositivo:
            digitais_por_dispositivo[digital.dispositivo.nome] = []
        digitais_por_dispositivo[digital.dispositivo.nome].append(digital)
    return render_template('pessoa_detalhe.html', pessoa=pessoa, dispositivos=dispositivos, digitais_agrupadas=digitais_por_dispositivo)

# --- ROTAS CRUD PARA DISPOSITIVOS ---
@bp.route('/dispositivos')
def listar_dispositivos():
    dispositivos = Dispositivo.query.all()
    return render_template('dispositivos.html', dispositivos=dispositivos)

@bp.route('/dispositivos/novo', methods=['POST'])
def novo_dispositivo():
    # Extrai os dados do formulário
    nome = request.form.get('nome')
    hostname = request.form.get('hostname')
    ip_address = request.form.get('ip_address')
    api_key = request.form.get('api_key')
    # Adiciona ao banco de dados...
    if nome and hostname and ip_address and api_key:
        if not Dispositivo.query.filter_by(hostname=hostname).first():
            novo_disp = Dispositivo(nome=nome, hostname=hostname, ip_address=ip_address, api_key=api_key)
            db.session.add(novo_disp)
            db.session.commit()
            flash('Dispositivo adicionado com sucesso!', 'success')
        else:
            flash('Um dispositivo com este hostname já existe.', 'warning')
    return redirect(url_for('main.listar_dispositivos'))

# --- ROTAS DE CADASTRO E STATUS DA BIOMETRIA ---

@bp.route('/digital/cadastrar', methods=['POST'])
def cadastrar_digital():
    pessoa_id = request.form.get('pessoa_id')
    dispositivo_id = request.form.get('dispositivo_id')
    nome_dedo = request.form.get('nome_dedo')

    dispositivo = Dispositivo.query.get(dispositivo_id)
    if not dispositivo:
        flash('Dispositivo inválido.', 'danger')
        return redirect(url_for('main.detalhe_pessoa', id=pessoa_id))
    
    nova_digital = Digital(pessoa_id=pessoa_id, dispositivo_id=dispositivo_id, nome_dedo=nome_dedo)
    db.session.add(nova_digital)
    db.session.commit() # Salva para obter o ID

    finger_id_para_usar = nova_digital.id
    
    resultado_api = asyncio.run(call_esphome_service(
        ip=dispositivo.ip_address,
        key=dispositivo.api_key,
        service_name='gravar',
        service_data={'finger_id': finger_id_para_usar, 'num_scans': 2}
    ))

    if resultado_api['success']:
        flash(f'Comando de cadastro enviado para "{dispositivo.nome}". Acompanhe o status abaixo.', 'info')
    else:
        flash(f'Erro ao contatar {dispositivo.nome}: {resultado_api["message"]}', 'danger')
        db.session.delete(nova_digital)
        db.session.commit()

    return redirect(url_for('main.detalhe_pessoa', id=pessoa_id))

@bp.route('/digital/<int:digital_id>/status')
def status_digital(digital_id):
    digital = Digital.query.get_or_404(digital_id)
    
    if digital.status_cadastro != 'Pendente':
        return jsonify({'status': digital.status_cadastro, 'completed': True})
    
    dispositivo = digital.dispositivo
    # Nome do text_sensor como definido no YAML: ${PrefixoNome} Status Cadastro Web
    # Substituímos o ${PrefixoNome} pelo valor real, ex: 'accp - Status Cadastro Web'
    prefixo_nome = f"accp - " # Você pode tornar isso dinâmico se tiver múltiplos prefixos
    entity_name_to_find = f"{prefixo_nome}Status Cadastro Web"

    resultado_api = asyncio.run(get_esphome_entity_state(
        ip=dispositivo.ip_address,
        key=dispositivo.api_key,
        entity_name=entity_name_to_find
    ))

    if resultado_api.get('success'):
        status_atual_esp = resultado_api['state']
        if status_atual_esp == 'SUCESSO':
            digital.status_cadastro = 'Sucesso'
            db.session.commit()
            return jsonify({'status': 'Sucesso', 'completed': True})
        elif status_atual_esp == 'FALHA':
            digital.status_cadastro = 'Falha'
            db.session.commit()
            return jsonify({'status': 'Falha', 'completed': True})
        
        return jsonify({'status': status_atual_esp, 'completed': False})
    
    return jsonify({'status': f"Erro: {resultado_api.get('message', 'desconhecido')}", 'completed': True})

@bp.route('/digital/<int:digital_id>/excluir', methods=['POST'])
def excluir_digital(digital_id):
    digital = Digital.query.get_or_404(digital_id)
    pessoa_id = digital.pessoa_id
    dispositivo = digital.dispositivo
    
    resultado_api = asyncio.run(call_esphome_service(
        ip=dispositivo.ip_address,
        key=dispositivo.api_key,
        service_name='excluir',
        service_data={'finger_id': digital.id}
    ))
    
    if resultado_api['success']:
        flash(f'Digital "{digital.nome_dedo}" em "{dispositivo.nome}" excluída com sucesso.', 'success')
        db.session.delete(digital)
        db.session.commit()
    else:
        flash(f'Erro ao excluir digital em {dispositivo.nome}: {resultado_api["message"]}', 'danger')
        
    return redirect(url_for('main.detalhe_pessoa', id=pessoa_id))