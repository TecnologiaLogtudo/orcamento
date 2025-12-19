"""
Módulo de rotas da aplicação
Centraliza os imports de todos os blueprints
"""

from routes import auth
from routes import categorias
from routes import orcamentos
from routes import dashboard
from routes import relatorios
from routes import logs

__all__ = [
    'auth',
    'categorias',
    'orcamentos',
    'dashboard',
    'relatorios',
    'logs'
]