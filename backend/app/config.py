#config.py
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
    }

    # Segurança
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'Logtudo2025PlanoOrçamentario'
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'jLogtudo2025@PlanoOrçamentario'
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=8)
    JWT_REFRESH_TOKEN_EXPIRES = 604800  # 7 dias

    # CORS
    CORS_ORIGINS = ["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000", "http://127.0.0.1:3000"]
    
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

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}