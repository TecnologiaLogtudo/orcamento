# 📋 Guia Completo: Implantação de Aplicação Python no King Host

**Versão:** 1.0  
**Data:** Dezembro 2025  
**Domínio:** logtudo.com.br  
**Hospedeiro:** King Host  

---

## 📑 Índice

1. [Preparação Inicial](#preparação-inicial)
2. [Criar Aplicação no Painel](#criar-aplicação-no-painel)
3. [Estrutura de Diretórios](#estrutura-de-diretórios)
4. [Configuração de Acesso FTP/SSH](#configuração-de-acesso-ftpssh)
5. [Envio de Arquivos](#envio-de-arquivos)
6. [Arquivo WSGI](#arquivo-wsgi)
7. [Dependências Python](#dependências-python)
8. [Configuração do .htaccess](#configuração-do-htaccess)
9. [Testes e Diagnostico](#testes-e-diagnostico)
10. [Gerenciamento no Painel](#gerenciamento-no-painel)
11. [Checklist Final](#checklist-final)

---

## 🚀 Preparação Inicial

Antes de fazer qualquer coisa no painel do King Host, prepare sua aplicação no seu computador local.

### Estrutura de Pastas Recomendada

meu_projeto/
├── app.py # Arquivo principal WSGI
├── passenger_wsgi.py # Alternativa ao app.py
├── requirements.txt # Dependências Python
├── config/
│ └── settings.py
├── static/
│ ├── css/
│ ├── js/
│ └── img/
├── templates/ # HTML (se usar Framework)
├── utils/
├── .htaccess # Configurações Apache
├── .gitignore
└── README.md

text

### Aplicação WSGI Simples (app.py)

Se não usar framework, crie um arquivo `app.py` básico:

def application(environ, start_response):
"""
Função WSGI padrão do King Host
"""
status = '200 OK'
response_headers = [('Content-type', 'text/plain; charset=utf-8')]
start_response(status, response_headers)
return [b'Hello World! Aplicacao rodando no King Host']

text

### Aplicação Flask (Recomendado)

Se usar Flask, estruture assim:

app.py
from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/')
def home():
"""Rota principal"""
return jsonify({
'status': 'ok',
'mensagem': 'API Flask rodando no King Host',
'versao': '1.0'
})

@app.route('/api/dados')
def dados():
"""Rota de exemplo"""
return jsonify({
'dados': 'seu conteúdo aqui'
})

IMPORTANTE: Exportar a variável application para WSGI
application = app

if __name__ == '__main__':
app.run(debug=False)

text

### Aplicação Django (Alternativa)

Se usar Django, use o `wsgi.py` gerado automaticamente:

wsgi.py (já vem com Django)
import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
application = get_wsgi_application()

text

---

## 🎯 Criar Aplicação no Painel

### Passo 1: Acessar o Painel KingHost

1. Acesse: https://painel.kinghost.com.br
2. Faça login com suas credenciais
3. Clique em **"Gerenciar logtudo.com.br"**
4. No menu lateral, procure por **"Frameworks Python - WSGI"**

### Passo 2: Preencher o Formulário "CRIAR UMA NOVA APLICAÇÃO"

Você verá um formulário com os seguintes campos:

#### **Nome da Aplicação**
- Exemplo: `minha_api`, `sistema_vendas`, `orcamento`
- Este será o subdiretório da URL
- A aplicação será acessível em: `www.logtudo.com.br/nome_aplicacao`
- Não use caracteres especiais, apenas letras, números e underscore

#### **Framework**
Selecione uma das opções:

| Framework | Quando Usar |
|-----------|-----------|
| **Django** | Projetos grandes e complexos |
| **Flask** | APIs leves e aplicações simples |
| **Pylons** | Frameworks clássicos |
| **TurboGears** | Desenvolvimento web avançado |
| **Webpy** | Aplicações minimalistas |
| **Web2py** | Desenvolvimento rápido |
| **Outros** | Frameworks customizados ou WSGI puro |

> **Dica:** Se usar **Flask**, selecione **"Outros"** e configure manualmente

#### **Tipo de Aplicação**
- Mantenha a opção **"Uma ou mais aplicações"** selecionada
- Isso permite criar múltiplas aplicações em subdiretórios
- Número máximo: 10 aplicações

### Passo 3: Clicar em "Criar Aplicação"

Após preencher todos os campos, clique no botão **"Criar Aplicação"**.

O sistema criará automaticamente a estrutura de pastas no servidor.

---

## 📁 Estrutura de Diretórios

Após criar a aplicação, o King Host gera esta estrutura no servidor:

public_html/
└── nome_aplicacao/
├── public/ # Pasta publica (opcional)
├── tmp/ # Pasta temporaria
├── app.py # SEU ARQUIVO PRINCIPAL (OBRIGATÓRIO)
├── passenger_wsgi.py # Alternativa ao app.py
├── requirements.txt # Dependências Python
├── .htaccess # Configurações Apache
└── logs/ # Logs da aplicação

text

**Arquivo obrigatório:**
- `app.py` com função `application()` ou variável `app` do Flask
- O King Host busca automaticamente por este arquivo

---

## 🔐 Configuração de Acesso FTP/SSH

### Dados de Acesso FTP

No painel do King Host, você encontra:

Host FTP: ftp.logtudo.com.br
Usuário FTP: logtudo
Caminho físico: /home/logtudo
Host FTP alternativo: ftp.web10f36.kinghost.net
Acesso WebFTP: http://webftp.kinghost.com.br/

text

### Dados de Acesso SSH

Host SSH: ssh.logtudo.com.br (ou ftp.logtudo.com.br)
Usuário: logtudo
Porta: 22 (padrão) ou porta customizada

text

### Obter a Senha

1. Acesse o painel KingHost
2. Vá para **"Gerenciar FTP"**
3. Clique na aba **"MEUS DADOS"**
4. Copie os dados conforme acima

---

## 📤 Envio de Arquivos

### Opção 1: Usar SSH (Terminal/CMD)

#### No Linux/Mac:
Conectar via SSH
ssh logtudo@ftp.logtudo.com.br

Navegar para a pasta da aplicação
cd ~/public_html/nome_aplicacao/

Se tiver Git configurado (RECOMENDADO)
git clone seu-repositorio .

Ou fazer upload via SCP
scp -r ./meu_projeto/* logtudo@ftp.logtudo.com.br:~/public_html/nome_aplicacao/

text

#### No Windows (PowerShell ou Git Bash):
Conectar via SSH
ssh logtudo@ftp.logtudo.com.br

Ou usar SCP
scp -r "C:\meu_projeto*" logtudo@ftp.logtudo.com.br:~/public_html/nome_aplicacao/

text

### Opção 2: Usar FTP/SFTP (GUI)

#### Software Recomendado:
- **FileZilla** (Grátis e multiplataforma)
- **WinSCP** (Windows)
- **Cyberduck** (Mac)
- **WebFTP do King Host** (Navegador)

#### Passo a Passo FileZilla:
1. Abra FileZilla
2. Vá em **File > Site Manager**
3. Crie um novo site com:
   - **Host:** ftp.logtudo.com.br
   - **Usuário:** logtudo
   - **Senha:** [sua senha]
   - **Protocolo:** SFTP (recomendado) ou FTP
4. Clique em **Connect**
5. Navegue até `public_html/nome_aplicacao/`
6. Faça o upload dos seus arquivos

#### Arquivos para fazer upload:
✅ app.py
✅ requirements.txt
✅ .htaccess
✅ static/ (pasta inteira)
✅ templates/ (pasta inteira, se tiver)
✅ config/ (pasta inteira, se tiver)

text

> **Importante:** NÃO faça upload da pasta `.git`, `venv`, `__pycache__`, `.env`

---

## 🐍 Arquivo WSGI

O arquivo WSGI é o ponto de entrada da sua aplicação. O King Host o executará automaticamente.

### Arquivo Obrigatório: `app.py`

O arquivo **DEVE** estar na raiz de `nome_aplicacao/` e deve conter:

#### Para Framework WSGI Puro:
app.py
def application(environ, start_response):
"""
Função WSGI padrão
environ: dicionário com variáveis de ambiente
start_response: função para enviar headers HTTP
"""
status = '200 OK'
response_headers = [('Content-Type', 'text/html; charset=utf-8')]
start_response(status, response_headers)

text
html = """
<!DOCTYPE html>
<html>
<head>
    <title>Aplicação Python no King Host</title>
</head>
<body>
    <h1>✅ Aplicação rodando com sucesso!</h1>
    <p>Parabéns! Sua aplicação Python está funcionando.</p>
</body>
</html>
"""
return [html.encode('utf-8')]
text

#### Para Flask:
app.py
from flask import Flask, render_template, jsonify

app = Flask(name)

Middleware (se necessário)
@app.before_request
def before_request():
"""Executado antes de cada requisição"""
pass

@app.after_request
def after_request(response):
"""Executado após cada requisição"""
response.headers['X-Powered-By'] = 'Flask/KingHost'
return response

Rotas
@app.route('/')
def index():
"""Página inicial"""
return render_template('index.html', title='Home')

@app.route('/api/status')
def status():
"""Endpoint de status"""
return jsonify({
'status': 'ok',
'aplicacao': 'orcamento',
'versao': '1.0.0'
})

@app.route('/api/dados/<int:id>')
def get_dados(id):
"""Buscar dados por ID"""
return jsonify({
'id': id,
'dados': 'exemplo'
})

@app.errorhandler(404)
def not_found(error):
"""Erro 404"""
return jsonify({'erro': 'Página não encontrada'}), 404

@app.errorhandler(500)
def internal_error(error):
"""Erro 500"""
return jsonify({'erro': 'Erro interno do servidor'}), 500

EXPORTAR A VARIÁVEL PRINCIPAL
application = app

if __name__ == '__main__':
app.run(debug=False, host='0.0.0.0', port=5000)

text

#### Para Django:
wsgi.py (já vem pronto no Django)
import os
import sys

Adicionar o projeto ao PATH
sys.path.insert(0, os.path.dirname(file))

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

application = get_wsgi_application()

text

### Arquivo Alternativo: `passenger_wsgi.py`

Alguns servidores usam este nome:

passenger_wsgi.py (alternativa)
import sys
sys.path.insert(0, '/home/logtudo/public_html/nome_aplicacao')

from app import application # Importar de app.py

text

---

## 📦 Dependências Python

### Criar `requirements.txt`

Liste TODAS as dependências da sua aplicação:

requirements.txt
Framework
Flask==2.3.0
Werkzeug==2.3.0
Jinja2==3.1.2
click==8.1.3

API e HTTP
requests==2.31.0
httpx==0.24.0

Database
SQLAlchemy==2.0.0
psycopg2-binary==2.9.6
mysql-connector-python==8.0.32

Validação e Segurança
python-dotenv==1.0.0
pydantic==1.10.2
PyJWT==2.6.0

Utilitários
python-dateutil==2.8.2
pytz==2023.3

Logs e Monitoramento
python-logging==1.0.0

ORM
alembic==1.11.1

text

> **Importante:** O King Host instalará automaticamente as dependências do `requirements.txt`

### Gerar requirements.txt Automaticamente

Se estiver usando `venv`:

Ativar ambiente virtual
source venv/bin/activate # Linux/Mac
venv\Scripts\activate # Windows

Gerar lista de dependências
pip freeze > requirements.txt

text

---

## ⚙️ Configuração do .htaccess

Se precisar de configurações especiais de rewrite ou headers, crie um `.htaccess`:

.htaccess
Ativar mod_rewrite
<IfModule mod_rewrite.c>
    # Habilita o motor de reescrita de URL
    RewriteEngine On

    # Força o uso de HTTPS para maior segurança (Recomendado)
    # Descomente as duas linhas abaixo se você tiver um certificado SSL ativo.
    # RewriteCond %{HTTPS} off
    # RewriteRule ^(.*)$ https://%{HTTP_HOST}%{REQUEST_URI} [L,R=301]

    # Phusion Passenger (servidor do King Host) precisa de uma regra para saber
    # que este diretório é uma aplicação Python.
    # Esta diretiva habilita o Passenger para a aplicação.
    PassengerEnabled On
    PassengerAppRoot /home/logtudo/public_html/orcamento

</IfModule>