# -*- coding: utf-8 -*-
import os
import sys
import logging

# --------- Ajuste os caminhos do projeto abaixo conforme sua hospedagem ---------
PROJECT_ROOT = '.'
APPS_ROOT = '.'

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
if APPS_ROOT not in sys.path:
    sys.path.insert(0, APPS_ROOT)


# Variáveis de ambiente base
os.environ.setdefault('PYTHON_EGG_CACHE', '/home/logtudo/apps_wsgi/.python-eggs')
os.environ.setdefault('PYTHON_EGG_CACHE', '/home/logtudo/apps_wsgi/.python-eggs')
os.environ.setdefault('FLASK_ENV', 'production')

# Configure logging para capturar erros no error.log do Apache/mod_wsgi
logging.basicConfig(stream=sys.stderr)

# Importar a aplicação WSGI (deve existir `app.py` com `application`)
from app import application


