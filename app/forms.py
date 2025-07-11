# app/forms.py
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired
from wtforms import StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Length
from wtforms import StringField, SubmitField, BooleanField, TimeField
from wtforms.validators import DataRequired, Length, Optional, NumberRange
from wtforms_sqlalchemy.fields import QuerySelectField
from wtforms import StringField, SubmitField, IntegerField, SelectField
from app.models import AccessGroup
from app.models import Zone
from wtforms.fields import DateField
from .models import User # Adicionar User

class LoginForm(FlaskForm):
    username = StringField('Usuário', validators=[DataRequired()])
    password = PasswordField('Senha', validators=[DataRequired()])
    submit = SubmitField('Entrar')

class ZoneForm(FlaskForm):
    name = StringField('Nome da Zona', validators=[DataRequired(), Length(min=3, max=100)])
    prefix = StringField('Prefixo da Zona', 
                         description='Prefixo de 4 caracteres usado no YAML do ESPHome (ex: accp, accg).',
                         validators=[DataRequired(), Length(min=4, max=4)])
    description = TextAreaField('Descrição', validators=[Length(max=255)])
    esphome_hostname = StringField('Hostname do ESP32', 
                                   description='Ex: acesso-principal.local',
                                   validators=[DataRequired(), Length(max=100)])
    esphome_api_key = StringField('Chave da API Nativa', 
                                  description='A chave de criptografia definida no YAML do ESPHome.',
                                  validators=[DataRequired(), Length(max=255)])
    submit = SubmitField('Salvar')

class AccessGroupForm(FlaskForm):
    name = StringField('Nome do Grupo', validators=[DataRequired(), Length(max=100)])
    is_24h = BooleanField('Acesso Permitido 24 Horas')
    
    # Horários só são obrigatórios se o acesso não for 24h
    start_time = TimeField('Horário de Início', validators=[Optional()])
    end_time = TimeField('Horário de Fim', validators=[Optional()])

    # Dias da semana
    day_sun = BooleanField('Domingo')
    day_mon = BooleanField('Segunda-feira')
    day_tue = BooleanField('Terça-feira')
    day_wed = BooleanField('Quarta-feira')
    day_thu = BooleanField('Quinta-feira')
    day_fri = BooleanField('Sexta-feira')
    day_sat = BooleanField('Sábado')
    
    submit = SubmitField('Salvar')

# Esta função é necessária para que o QuerySelectField saiba o que buscar no banco de dados.
def group_query():
    return AccessGroup.query.order_by(AccessGroup.name)

class UserForm(FlaskForm):
    name = StringField('Nome Completo', validators=[DataRequired(), Length(max=150)])
    phone = StringField('Telefone', validators=[Optional(), Length(max=20)])
    
    # Este campo especial cria um dropdown com os Grupos de Acesso
    access_group = QuerySelectField(
        'Grupo de Acesso',
        query_factory=group_query,
        get_label='name',
        allow_blank=False,
        validators=[DataRequired()]
    )
    
    submit = SubmitField('Salvar')

FINGER_CHOICES = [
    ('Polegar Direito', 'Polegar Direito'),
    ('Indicador Direito', 'Indicador Direito'),
    ('Dedo Médio Direito', 'Dedo Médio Direito'),
    ('Anelar Direito', 'Anelar Direito'),
    ('Mínimo Direito', 'Dedo Mínimo Direito'),
    ('Polegar Esquerdo', 'Polegar Esquerdo'),
    ('Indicador Esquerdo', 'Indicador Esquerdo'),
    ('Dedo Médio Esquerdo', 'Dedo Médio Esquerdo'),
    ('Anelar Esquerdo', 'Anelar Esquerdo'),
    ('Mínimo Esquerdo', 'Dedo Mínimo Esquerdo'),
]

# Função para buscar as Zonas, similar à que fizemos para os Grupos
def zone_query():
    return Zone.query.order_by(Zone.name)

class FingerprintEnrollForm(FlaskForm):
    zone = QuerySelectField(
        'Selecione a Zona (ESP32)',
        query_factory=zone_query,
        get_label='name',
        allow_blank=False,
        validators=[DataRequired()]
    )
    finger_id_on_sensor = IntegerField(
        'ID para a Digital no Sensor',
        validators=[DataRequired(), NumberRange(min=1, max=1000)],
        description='Este ID é gerado automaticamente com base na zona selecionada.',
        render_kw={'readonly': True} # <-- Adicionado aqui
    )
    finger_name = SelectField(
        'Nome de Identificação do Dedo',
        choices=FINGER_CHOICES,
        validators=[DataRequired()]
    )
    submit = SubmitField('Iniciar Cadastro')

# Função para buscar os usuários para o filtro
def user_query():
    return User.query.order_by(User.name)

class LogFilterForm(FlaskForm):
    start_date = DateField('Data Início', format='%Y-%m-%d', validators=[Optional()])
    end_date = DateField('Data Fim', format='%Y-%m-%d', validators=[Optional()])

    # Usamos QuerySelectField para popular o dropdown com usuários do banco
    user = QuerySelectField(
        'Usuário',
        query_factory=user_query,
        get_label='name',
        allow_blank=True, # Permite a opção "Todos"
        blank_text='-- Todos os Usuários --',
        validators=[Optional()]
    )

    # Para as zonas, vamos popular as opções diretamente na rota
    zone = SelectField('Zona', choices=[], validators=[Optional()])

    submit = SubmitField('Filtrar')
    clear = SubmitField('Limpar Filtros')