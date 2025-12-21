import os
import logging
from flask import Flask, send_from_directory
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
    
    # O frontend (React) é construído na pasta 'dist'.
    # Flask servirá os arquivos estáticos dessa pasta.
    app = Flask(__name__, static_folder='dist', static_url_path='')
    
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
    
    # Em desenvolvimento, o frontend roda em um servidor separado (Vite)
    # e precisa de CORS. Em produção, ambos são servidos juntos, mas
    # manter o CORS não prejudica.
    cors_origins = app.config.get('CORS_ORIGINS', '*')
    CORS(
        app,
        resources={r"/api/*": {"origins": cors_origins}},
        supports_credentials=True,
    )
    jwt = JWTManager(app)

    @jwt.token_in_blocklist_loader
    def check_if_token_revoked(_, payload):
        from models import TokenBlacklist
        jti = payload['jti']
        token = TokenBlacklist.query.filter_by(jti=jti).first()
        return token is not None
    
    # Criar diretórios necessários para uploads (se aplicável)
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['EXPORT_FOLDER'], exist_ok=True)
    
    # Registrar blueprints da API
    from routes import auth, categorias, orcamentos, dashboard, relatorios, logs
    
    api_prefix = '/api'
    app.register_blueprint(auth.bp, url_prefix=api_prefix)
    app.register_blueprint(categorias.bp, url_prefix=api_prefix)
    app.register_blueprint(orcamentos.bp, url_prefix=api_prefix)
    app.register_blueprint(dashboard.bp, url_prefix=api_prefix)
    app.register_blueprint(relatorios.bp, url_prefix=api_prefix)
    app.register_blueprint(logs.bp, url_prefix=api_prefix)

    # Rota de health check da API
    @app.route('/api/health')
    def health():
        return {'status': 'ok', 'message': 'API funcionando'}

    # Handler de erro 404 para servir o app React
    # Qualquer rota não encontrada pela API será tratada aqui, servindo o index.html
    @app.errorhandler(404)
    def not_found(e):
        return send_from_directory(app.static_folder, 'index.html')


    # Handlers de erro JWT (devem vir depois do registro de rotas)
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

    return app

# Determinar ambiente
config_name = os.getenv('FLASK_ENV', 'production')

# Criar aplicação
application = create_app(config_name)

# CLI para criar tabelas
@application.cli.command()
def create_db_command():
    """Cria as tabelas no banco de dados"""
    with application.app_context():
        db.create_all()
        print('✅ Tabelas criadas com sucesso!')

@application.cli.command()
def create_admin():
    """Cria usuário admin padrão"""
    from models import Usuario
    
    with application.app_context():
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

@application.cli.command()
def seed_db():
    """Popula banco com dados de exemplo"""
    # Implementação do seed...
    pass
        
if __name__ == '__main__':
    # Rodar servidor de desenvolvimento
    application.run(
        host='0.0.0.0',
        port=5000,
        debug=(config_name == 'development')
    )
