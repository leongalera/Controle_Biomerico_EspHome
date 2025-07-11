# app/models.py
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_login import UserMixin
from bcrypt import hashpw, gensalt, checkpw

db = SQLAlchemy()

class AdminUser(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)

    def set_password(self, password):
        self.password_hash = hashpw(password.encode('utf-8'), gensalt()).decode('utf-8')

    def check_password(self, password):
        return checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))

class AccessGroup(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    is_24h = db.Column(db.Boolean, default=True)
    start_time = db.Column(db.Time, nullable=True)
    end_time = db.Column(db.Time, nullable=True)
    day_sun = db.Column(db.Boolean, default=True)
    day_mon = db.Column(db.Boolean, default=True)
    day_tue = db.Column(db.Boolean, default=True)
    day_wed = db.Column(db.Boolean, default=True)
    day_thu = db.Column(db.Boolean, default=True)
    day_fri = db.Column(db.Boolean, default=True)
    day_sat = db.Column(db.Boolean, default=True)
    users = db.relationship('User', backref='access_group', lazy=True)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    access_group_id = db.Column(db.Integer, db.ForeignKey('access_group.id'), nullable=False)
    fingerprints = db.relationship('Fingerprint', backref='user', lazy=True, cascade="all, delete-orphan")
    access_logs = db.relationship('AccessLog', backref='user', lazy=True)

class Zone(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.String(255), nullable=True)
    esphome_hostname = db.Column(db.String(100), nullable=False, unique=True)
    esphome_api_key = db.Column(db.String(255), nullable=False)
    fingerprints = db.relationship('Fingerprint', backref='zone', lazy=True)
    prefix = db.Column(db.String(10), unique=True, nullable=False)
    # Define a zona de acesso, que pode ter múltiplas digitais
    fingerprints = db.relationship('Fingerprint', backref='zone', lazy=True)

class Fingerprint(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    # Este é o ID (1-1000) no próprio sensor R503
    finger_id_on_sensor = db.Column(db.Integer, nullable=False)
    finger_name = db.Column(db.String(50), nullable=False) # Ex: "Polegar Direito"
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    valid_until = db.Column(db.DateTime, nullable=True) # Para expiração
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    zone_id = db.Column(db.Integer, db.ForeignKey('zone.id'), nullable=False)
    # Garante que um ID de digital seja único por zona
    __table_args__ = (db.UniqueConstraint('finger_id_on_sensor', 'zone_id', name='_finger_id_zone_uc'),)

class AccessLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    zone_name = db.Column(db.String(100), nullable=False)
    result = db.Column(db.String(50), nullable=False)  # Ex: "Autorizado", "Não Reconhecido"

    # Estes campos podem ser nulos para logs de acesso não reconhecido
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    finger_used = db.Column(db.String(50), nullable=True)
    matched_finger_id = db.Column(db.Integer, nullable=True) # ID da digital no sensor