import os
import logging
from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from dotenv import load_dotenv

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

# Late initialization for db and config
from models import db
from config import config

def create_app(config_name='default'):
    """Factory para criar a aplicação Flask"""
    
    app = Flask(__name__)
    
    # Carregar configurações
    app.config.from_object(config[config_name])
    
    # Configurar logging
    if not app.debug and not app.testing:
        app.logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter(
            '[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
        ))
        app.logger.addHandler(handler)
        app.logger.info("Iniciando aplicação em modo de produção")
    
    # Inicializar extensões
    db.init_app(app)
    
    CORS(
        app,
        resources={r"/api/*": {"origins": ["http://localhost:5173", "https://orcamento-silk.vercel.app"]}},
        supports_credentials=True,
        methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization", "X-Requested-With"],
    )
    jwt = JWTManager(app)

    @jwt.token_in_blocklist_loader
    def check_if_token_revoked(_, payload):
        from models import TokenBlacklist
        jti = payload['jti']
        token = TokenBlacklist.query.filter_by(jti=jti).first()
        return token is not None
    
    # Criar diretórios necessários
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['EXPORT_FOLDER'], exist_ok=True)
    
    # Registrar blueprints
    from routes import auth, categorias, orcamentos, dashboard, relatorios, logs
    
    # Registrar blueprints sob o prefixo /api para coincidir com o frontend
    api_prefix = '/api'
    app.register_blueprint(auth.bp, url_prefix=api_prefix)
    app.register_blueprint(categorias.bp, url_prefix=api_prefix)
    app.register_blueprint(orcamentos.bp, url_prefix=api_prefix)
    app.register_blueprint(dashboard.bp, url_prefix=api_prefix)
    app.register_blueprint(relatorios.bp, url_prefix=api_prefix)
    app.register_blueprint(logs.bp, url_prefix=api_prefix)

    # Handlers de erro JWT
    @jwt.expired_token_loader
    def expired_token_loader(jwt_header, jwt_payload):
        app.logger.warning("Token expirado")
        return {'error': 'Token de autenticação expirado'}, 401

    @jwt.invalid_token_loader
    def invalid_token_loader(error):
        app.logger.warning("Token inválido")
        return {'error': 'Token de autenticação inválido'}, 401

    @jwt.unauthorized_loader
    def unauthorized_callback(error):
        app.logger.warning("Token não fornecido")
        return {'error': 'Token de autenticação não fornecido'}, 401

    # Rota de health check
    @app.route('/api/health')
    def health():
        return {'status': 'ok', 'message': 'API funcionando'}

    # Remover print statements em produção
    if app.debug:
        print("JWT SECRET ATIVO:", app.config.get('JWT_SECRET_KEY'))

    return app

# Determinar ambiente
config_name = os.getenv('FLASK_ENV', 'production')

# Criar aplicação
app = create_app(config_name)

# CLI para criar tabelas
@app.cli.command()
def create_db_command():
    """Cria as tabelas no banco de dados"""
    with app.app_context():
        db.create_all()
        print('✅ Tabelas criadas com sucesso!')

@app.cli.command()
def create_admin():
    """Cria usuário admin padrão"""
    from models import Usuario
    
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
    from models import Usuario, Categoria, Orcamento
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
        
if __name__ == '__main__':
    # Rodar servidor de desenvolvimento
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=(config_name == 'development')
    )
