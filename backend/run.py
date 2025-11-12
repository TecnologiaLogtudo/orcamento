import os
from app import create_app
from app.models import db
from dotenv import load_dotenv

# Carrega as variáveis de ambiente do arquivo .env
# Esta linha é crucial para que a aplicação leia as credenciais corretas
load_dotenv()
 
# Determinar ambiente
config_name = os.getenv('FLASK_ENV', 'development')

# Criar aplicação
app = create_app(config_name)

# CLI para criar tabelas
@app.cli.command()
def create_db():
    """Cria as tabelas no banco de dados"""
    with app.app_context():
        db.create_all()
        print('✅ Tabelas criadas com sucesso!')

@app.cli.command()
def create_admin():
    """Cria usuário admin padrão"""
    from app.models import Usuario
    
    with app.app_context():
        # Verificar se já existe admin
        admin_exists = Usuario.query.filter_by(email='admin@empresa.com').first()
        
        if admin_exists:
            print('⚠️  Usuário admin já existe!')
            return
        
        admin = Usuario(
            nome='Administrador',
            email='admin@empresa.com',
            papel='admin'
        )
        admin.set_password('admin123')
        
        db.session.add(admin)
        db.session.commit()
        
        print('✅ Usuário admin criado!')
        print('   Email: admin@empresa.com')
        print('   Senha: admin123')
        print('   ⚠️  ALTERE A SENHA APÓS PRIMEIRO LOGIN!')

@app.cli.command()
def seed_db():
    """Popula banco com dados de exemplo"""
    from app.models import Usuario, Categoria, Orcamento
    from datetime import datetime
    
    with app.app_context():
        print('🌱 Populando banco de dados...')
        
        # Criar usuários de teste
        if not Usuario.query.filter_by(email='gestor@empresa.com').first():
            gestor = Usuario(nome='Gestor Teste', email='gestor@empresa.com', papel='gestor')
            gestor.set_password('gestor123')
            db.session.add(gestor)
            print('✅ Gestor criado')
        
        if not Usuario.query.filter_by(email='visualizador@empresa.com').first():
            visualizador = Usuario(nome='Visualizador Teste', email='visualizador@empresa.com', papel='visualizador')
            visualizador.set_password('visualizador123')
            db.session.add(visualizador)
            print('✅ Visualizador criado')
        
        db.session.commit()
        
        # Criar categorias de exemplo
        categorias_exemplo = [
            {
                'dono': 'TI',
                'tipo_despesa': 'Operacional',
                'uf': 'SP',
                'master': 'Tecnologia',
                'grupo': 'Infraestrutura',
                'cod_class': '001',
                'classe_custo': 'Servidores'
            },
            {
                'dono': 'RH',
                'tipo_despesa': 'Pessoal',
                'uf': 'RJ',
                'master': 'Recursos Humanos',
                'grupo': 'Folha de Pagamento',
                'cod_class': '002',
                'classe_custo': 'Salários'
            },
            {
                'dono': 'Marketing',
                'tipo_despesa': 'Operacional',
                'uf': 'MG',
                'master': 'Comercial',
                'grupo': 'Publicidade',
                'cod_class': '003',
                'classe_custo': 'Mídia Digital'
            }
        ]
        
        for cat_data in categorias_exemplo:
            if not Categoria.query.filter_by(
                dono=cat_data['dono'],
                grupo=cat_data['grupo'],
                cod_class=cat_data['cod_class'],
                tipo_despesa=cat_data['tipo_despesa']
            ).first():
                categoria = Categoria(**cat_data)
                db.session.add(categoria)
                print(f'✅ Categoria criada: {cat_data["grupo"]}')
        
        db.session.commit()
        
        print('✅ Banco populado com sucesso!')
        print('\n📋 Usuários criados:')
        print('   Admin: admin@empresa.com / admin123')
        print('   Gestor: gestor@empresa.com / gestor123')
        print('   Visualizador: visualizador@empresa.com / visualizador123')

if __name__ == '__main__':
    # Rodar servidor de desenvolvimento
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=(config_name == 'development')
    )