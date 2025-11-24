import requests
import json

# Fazer login como admin (para ter um token válido)
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

# Tentar fazer login como gestor
response = requests.post('http://localhost:5000/api/login', json={
    'email': 'gestor@empresa.com',
    'senha': 'gestor123'
})

if response.status_code == 200:
    gestor_token = response.json()['access_token']
    print('✓ Gestor logado com sucesso\n')
    
    # Chamar endpoint de submissões como gestor
    response = requests.get('http://localhost:5000/api/orcamentos/submissions', headers={
        'Authorization': f'Bearer {gestor_token}'
    })
    
    print(f'Status code: {response.status_code}')
    data = response.json()
    print(f'\nTotal de submissões: {len(data)}')
    for i, submission in enumerate(data, 1):
        print(f"\n{i}. Submissão:")
        print(f"   Admin: {submission['admin_usuario']}")
        print(f"   Data: {submission['data']}")
        print(f"   Total: {submission['total_submetidos']}")
        print(f"   Masters: {submission['masters']}")
        print(f"   UFs: {submission['ufs']}")
        print(f"   Categorias: {submission['categorias']}")
else:
    print(f'Erro ao fazer login como gestor: {response.status_code}')
    print(response.text)
