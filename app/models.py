from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Dispositivo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), unique=True, nullable=False, comment="Ex: Porta da Frente")
    hostname = db.Column(db.String(100), unique=True, nullable=False, comment="Ex: acesso-principal")
    ip_address = db.Column(db.String(50), nullable=False)
    api_key = db.Column(db.String(255), nullable=False, comment="Chave de criptografia da API Nativa")
    digitais = db.relationship('Digital', backref='dispositivo', lazy='dynamic', cascade="all, delete-orphan")
    logs = db.relationship('LogAcesso', backref='dispositivo', lazy='dynamic', cascade="all, delete-orphan")

    def __repr__(self):
        return f'<Dispositivo {self.nome}>'

class Pessoa(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(150), nullable=False, unique=True)
    digitais = db.relationship('Digital', backref='pessoa', lazy='dynamic', cascade="all, delete-orphan")

    def __repr__(self):
        return f'<Pessoa {self.nome}>'

class Digital(db.Model):
    id = db.Column(db.Integer, primary_key=True, comment="Este é o 'finger_id' usado no ESP")
    nome_dedo = db.Column(db.String(50), nullable=False, comment="Ex: Polegar Direito")
    pessoa_id = db.Column(db.Integer, db.ForeignKey('pessoa.id'), nullable=False)
    dispositivo_id = db.Column(db.Integer, db.ForeignKey('dispositivo.id'), nullable=False)
    status_cadastro = db.Column(db.String(20), default='Pendente', nullable=False)

    def __repr__(self):
        return f'<Digital id={self.id} pessoa={self.pessoa.nome} dedo={self.nome_dedo}>'

class LogAcesso(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    dispositivo_id = db.Column(db.Integer, db.ForeignKey('dispositivo.id'), nullable=False)
    finger_id = db.Column(db.Integer, nullable=True)
    nome_pessoa = db.Column(db.String(150), nullable=True, comment="Nome da pessoa no momento do acesso")
    nome_dedo = db.Column(db.String(50), nullable=True)
    nome_dispositivo = db.Column(db.String(100), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    status = db.Column(db.String(50), nullable=False, comment="Ex: Autorizado, Negado")

    def __repr__(self):
        return f'<Log {self.timestamp} - {self.nome_pessoa} em {self.nome_dispositivo}>'