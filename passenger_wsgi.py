# passenger_wsgi.py
import sys
import os

# Adiciona o diretório 'backend' ao path do Python para que os módulos possam ser encontrados.
# O Phusion Passenger (servidor do King Host) executará este arquivo a partir da raiz do projeto.
# '/home/logtudo/public_html/orcamento' é o diretório raiz da aplicação no servidor.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

# Importa a factory 'create_app' do nosso pacote de aplicação.
from app import create_app

# Cria a instância da aplicação Flask.
# É crucial usar a configuração de 'production' para segurança e performance.
# O King Host irá configurar as variáveis de ambiente necessárias.
application = create_app('production')
