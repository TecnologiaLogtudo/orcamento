import sys
sys.path.insert(0, '.')
from app import create_app
from app.models import db, Usuario

app = create_app()

with app.app_context():
    users = Usuario.query.all()
    for user in users:
        print(f"ID: {user.id_usuario}, Nome: {user.nome}, Email: {user.email}, Papel: {user.papel}")
