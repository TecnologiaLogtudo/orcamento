"""
Módulo de rotas da aplicação
Centraliza os imports de todos os blueprints
"""

from app.routes import auth
from app.routes import categorias
from app.routes import orcamentos
from app.routes import dashboard
from app.routes import relatorios
from app.routes import logs

__all__ = [
    'auth',
    'categorias',
    'orcamentos',
    'dashboard',
    'relatorios',
    'logs'
]