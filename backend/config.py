# backend/app/config.py
import os
from datetime import timedelta

class Config:
    """Configurações base do aplicativo"""

    # Chaves de segurança - DEVEM ser configuradas no ambiente
    SECRET_KEY = os.environ.get('SECRET_KEY')
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY')

    # Configuração do banco de dados - Prioriza DATABASE_URL (padrão do Render)
    DATABASE_URL = os.environ.get('DATABASE_URL')
    if DATABASE_URL and DATABASE_URL.startswith("mysql://"):
        DATABASE_URL = DATABASE_URL.replace("mysql://", "mysql+pymysql://", 1)

    SQLALCHEMY_DATABASE_URI = DATABASE_URL or \
        f"mysql+pymysql://{os.environ.get('MYSQL_USER')}:{os.environ.get('MYSQL_PASSWORD')}@" \
        f"{os.environ.get('MYSQL_HOST')}/{os.environ.get('MYSQL_DB')}?charset=utf8mb4"

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
        'pool_size': 10,
        'max_overflow': 5,
    }

    # Configuração de tokens JWT
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=8)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=7)

    # CORS
    CORS_ORIGINS = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]
    
    # ATENÇÃO: O sistema de arquivos em plataformas como Render/Heroku é efêmero.
    # Arquivos salvos aqui serão PERDIDOS em reinicializações ou deploys.
    # Para armazenamento persistente, use um serviço de storage como AWS S3, Google Cloud Storage, etc.
    UPLOAD_FOLDER = '/tmp/uploads'
    EXPORT_FOLDER = '/tmp/exports'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max
    
    # Paginação
    ITEMS_PER_PAGE = 50

class DevelopmentConfig(Config):
    """Configurações de desenvolvimento"""
    DEBUG = True
    TESTING = False
    
    # Em desenvolvimento, podemos usar valores padrão se não estiverem no .env
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-for-testing'
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'dev-jwt-secret-key-for-testing'

class ProductionConfig(Config):
    """Configurações de produção"""
    DEBUG = False
    TESTING = False

    # Em produção, estas variáveis DEVEM vir do ambiente
    if not Config.SECRET_KEY or not Config.JWT_SECRET_KEY:
        raise ValueError("SECRET_KEY e JWT_SECRET_KEY devem ser configuradas no ambiente de produção.")
    
    if not Config.SQLALCHEMY_DATABASE_URI:
        raise ValueError("DATABASE_URL ou variáveis MYSQL_* devem ser configuradas no ambiente de produção.")

    # Configurações específicas de produção
    CORS_ORIGINS = [
        "https://orcamento.logtudo.com.br",
        "https://www.orcamento.logtudo.com.br",
        "https://orcamento-coral.vercel.app"
    ]
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
        'pool_size': 20,
        'max_overflow': 10,
        'pool_timeout': 30,  # Timeout ao obter conexão
    }

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}