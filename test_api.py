import requests
import json

# Fazer login como admin
response = requests.post('http://localhost:5000/api/login', json={
    'email': 'admin@empresa.com',
    'senha': 'admin123'
})

if response.status_code != 200:
    print(f'Erro no login: {response.status_code}')
    print(response.text)
    exit(1)

admin_token = response.json()['access_token']
print('✓ Admin logado com sucesso\n')

# Chamar endpoint de rejections
print('=== TESTANDO ENDPOINT /orcamentos/rejections ===')
response = requests.get('http://localhost:5000/api/orcamentos/rejections', headers={
    'Authorization': f'Bearer {admin_token}'
})

print(f'Status code: {response.status_code}')
if response.status_code != 200:
    print(f'Erro: {response.text}')
else:
    data = response.json()
    print(f'Total de reprovações: {len(data)}')
    if data:
        print('\nPrimeira reprovação:')
        print(json.dumps(data[0], indent=2, ensure_ascii=False))

# Verificar logs com "Reprovação" no banco
print('\n=== VERIFICANDO LOGS COM "REPROVAÇÃO" ===')
import sys
sys.path.insert(0, 'backend')
from app import create_app
from app.models import db, Log

app = create_app()

with app.app_context():
    logs = Log.query.filter(Log.acao.contains('Reprovação')).all()
    print(f'Total de logs com "Reprovação": {len(logs)}')
    for log in logs:
        print(f'\nID: {log.id_log}')
        print(f'Ação: {log.acao}')
        print(f'Detalhes: {log.detalhes}')


