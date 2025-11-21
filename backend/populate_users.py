# c:/Users/felip/OneDrive/Logtudo/Controle_orcamento/backend/populate_users.py

import os
from app import create_app, db
from app.models import Usuario
from dotenv import load_dotenv

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

def populate_users():
    """
    Popula a tabela de usuários com os usuários padrão (Admin, Gestor, Visualizador).
    Verifica se os usuários já existem antes de criá-los.
    """
    # Determina o ambiente e cria a aplicação para ter o contexto correto
    config_name = os.getenv('FLASK_ENV', 'development')
    app = create_app(config_name)

    with app.app_context():
        print("Iniciando a população da tabela de usuários...")

        # Lista de usuários a serem criados
        users_to_create = [
            {
                'nome': 'Administrador',
                'email': 'admin@empresa.com',
                'senha': 'admin123',
                'papel': 'admin'
            },
            {
                'nome': 'Gestor Teste',
                'email': 'gestor@empresa.com',
                'senha': 'gestor123',
                'papel': 'gestor'
            },
            {
                'nome': 'Visualizador Teste',
                'email': 'visualizador@empresa.com',
                'senha': 'visualizador123',
                'papel': 'visualizador'
            }
        ]

        for user_data in users_to_create:
            user_exists = Usuario.query.filter_by(email=user_data['email']).first()
            if user_exists:
                print(f"⚠️  Usuário {user_data['email']} já existe. Pulando.")
            else:
                new_user = Usuario(nome=user_data['nome'], email=user_data['email'], papel=user_data['papel'])
                new_user.set_password(user_data['senha'])
                db.session.add(new_user)
                print(f"✅ Usuário {user_data['email']} criado com sucesso!")
        
        db.session.commit()
        print("\n✨ Processo de população de usuários finalizado.")

if __name__ == '__main__':
    populate_users()