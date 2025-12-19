# backend/app/config.py
import os
from datetime import timedelta

class Config:
    """Configurações base do aplicativo"""
    
    # Banco de dados MySQL
    MYSQL_HOST = os.environ.get('MYSQL_HOST', 'mysql.logtudo.com.br')
    MYSQL_USER = os.environ.get('MYSQL_USER', 'logtudo01')
    MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD', 'Banco25orc')
    MYSQL_DB = os.environ.get('MYSQL_DB', 'logtudo01')
    
    SQLALCHEMY_DATABASE_URI = f'mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}/{MYSQL_DB}?charset=utf8mb4'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
        'pool_size': 20,  # Aumentar tamanho do pool em produção
        'max_overflow': 10,  # Permitir conexões extras quando necessário
    }

    # Segurança
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'Logtudo2025PlanoOrcamentario'
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'jLogtudo2025@PlanoOrcamentario'
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=8)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=7)  # 7 dias

    # CORS
    CORS_ORIGINS = [
        "https://orcamento.logtudo.com.br",
        "https://www.orcamento.logtudo.com.br",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]
    
    # Uploads e Exports
    UPLOAD_FOLDER = 'uploads'
    EXPORT_FOLDER = 'exports'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max
    
    # Paginação
    ITEMS_PER_PAGE = 50

class DevelopmentConfig(Config):
    """Configurações de desenvolvimento"""
    DEBUG = True
    TESTING = False

class ProductionConfig(Config):
    """Configurações de produção"""
    DEBUG = False
    TESTING = False
    
    # Em produção, estas variáveis DEVEM vir do ambiente
    @property
    def SECRET_KEY(self):
        key = os.environ.get('SECRET_KEY')
        if not key:
            raise ValueError("SECRET_KEY não configurada em produção!")
        return key

    @property
    def MYSQL_HOST(self):
        host = os.environ.get('MYSQL_HOST')
        if not host:
            raise ValueError("MYSQL_HOST não configurada em produção!")
        return host

    @property
    def MYSQL_USER(self):
        user = os.environ.get('MYSQL_USER')
        if not user:
            raise ValueError("MYSQL_USER não configurada em produção!")
        return user

    @property
    def MYSQL_PASSWORD(self):
        password = os.environ.get('MYSQL_PASSWORD')
        if not password:
            raise ValueError("MYSQL_PASSWORD não configurada em produção!")
        return password

    @property
    def MYSQL_DB(self):
        db = os.environ.get('MYSQL_DB')
        if not db:
            raise ValueError("MYSQL_DB não configurada em produção!")
        return db

    # Configurações específicas de produção
    CORS_ORIGINS = "*"
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