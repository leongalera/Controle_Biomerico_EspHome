# app/routes/main_routes.py
from flask import Blueprint, render_template
from flask_login import login_required

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
@login_required
def index():
    # Por enquanto, apenas renderiza uma página de boas-vindas.
    # Usaremos a que foi criada no passo 1.2
    return render_template('index.html')