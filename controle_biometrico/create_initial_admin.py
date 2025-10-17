# /addons/controle_biometrico/create_initial_admin.py
import os
from run import app
from app.models import db, AdminUser

# Esta função será executada pelo run.sh
def setup_admin():
    with app.app_context():
        initial_user = os.environ.get('INITIAL_ADMIN_USER')
        initial_pass = os.environ.get('INITIAL_ADMIN_PASSWORD')

        if initial_user and initial_pass:
            if not db.session.query(AdminUser).first():
                print(f"Banco de dados de administradores vazio. Criando usuário inicial '{initial_user}'...")
                admin = AdminUser(username=initial_user)
                admin.set_password(initial_pass)
                db.session.add(admin)
                db.session.commit()
                print(f"Usuário administrador inicial '{initial_user}' criado com sucesso!")
            else:
                print("Um ou mais administradores já existem. Nenhuma ação necessária.")

if __name__ == "__main__":
    setup_admin()