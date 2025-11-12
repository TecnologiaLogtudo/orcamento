#app/__init__.py
from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from app.models import db
from app.config import config
from dotenv import load_dotenv
import os

load_dotenv()

def create_app(config_name='default'):
    """Factory para criar a aplicação Flask"""
    
    app = Flask(__name__)
    
    # Carregar configurações
    app.config.from_object(config[config_name])
    
    # Inicializar extensões
    db.init_app(app)
    CORS(app, resources={r"/api/*": {"origins": ["http://localhost:5173"]}}, supports_credentials=True)
    jwt = JWTManager(app)
    
    # Criar diretórios necessários
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['EXPORT_FOLDER'], exist_ok=True)
    
    # Registrar blueprints
    from app.routes import auth, categorias, orcamentos, dashboard, relatorios, logs
    
    app.register_blueprint(auth.bp, url_prefix='/api')
    app.register_blueprint(categorias.bp, url_prefix='/api')
    app.register_blueprint(orcamentos.bp, url_prefix='/api')
    app.register_blueprint(dashboard.bp, url_prefix='/api')
    app.register_blueprint(relatorios.bp, url_prefix='/api')
    app.register_blueprint(logs.bp, url_prefix='/api')

    # Configuração do JWT
    @jwt.token_in_blocklist_loader
    def check_if_token_revoked(_, payload):
        from app.models import TokenBlacklist
        jti = payload['jti']
        token = TokenBlacklist.query.filter_by(jti=jti).first()
        return bool(token)

    # Handlers de erro JWT
    @jwt.expired_token_loader
    def expired_token_loader(jwt_header, jwt_payload):
        print(f"Token expirado: payload={jwt_payload}")
        return {'error': 'Token de autenticação expirado'}, 401

    @jwt.invalid_token_loader
    def invalid_token_loader(error):
        print(f"Token inválido: error={error}")
        return {'error': 'Token de autenticação inválido'}, 401

    @jwt.unauthorized_loader
    def unauthorized_callback(error):
        print(f"Sem token: error={error}")
        return {'error': 'Token de autenticação não fornecido'}, 401

    # Rota de health check
    @app.route('/health')
    def health():
        return {'status': 'ok', 'message': 'API funcionando'}

    print("JWT SECRET ATIVO:", app.config.get('JWT_SECRET_KEY'))

    return app