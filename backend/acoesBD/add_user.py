# backend/add_user.py

import os
from app import create_app
from models import db, Usuario
from dotenv import load_dotenv

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

def add_user(email, password, nome="Admin", papel="admin"):
    """
    Adiciona um novo usuário ao banco de dados.
    Verifica se o usuário já existe antes de criá-lo.
    """
    # Determina o ambiente e cria a aplicação para ter o contexto correto
    config_name = os.getenv('FLASK_ENV', 'development')
    app = create_app(config_name)

    with app.app_context():
        print(f"Tentando adicionar o usuário {email}...")

        user_exists = Usuario.query.filter_by(email=email).first()
        if user_exists:
            print(f"⚠️  Usuário com o email {email} já existe. Nenhuma ação foi tomada.")
        else:
            new_user = Usuario(nome=nome, email=email, papel=papel)
            new_user.set_password(password)
            db.session.add(new_user)
            db.session.commit()
            print(f"✅ Usuário {email} foi criado com sucesso!")

if __name__ == '__main__':
    # Adiciona o usuário especificado
    add_user(email="admin@empresa.com", password="admin123")
