# app/commands.py
import click
from flask.cli import with_appcontext
from .models import db, AdminUser

@click.command(name='create-admin')
@with_appcontext
def create_admin():
    """Cria um usuário administrador para o painel web."""
    username = click.prompt('Digite o nome de usuário do administrador')
    password = click.prompt('Digite a senha', hide_input=True, confirmation_prompt=True)
    
    if AdminUser.query.filter_by(username=username).first():
        click.echo('Este usuário já existe.')
        return
        
    admin = AdminUser(username=username)
    admin.set_password(password)
    
    db.session.add(admin)
    db.session.commit()
    
    click.echo(f'Administrador {username} criado com sucesso.')