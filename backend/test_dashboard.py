#!/usr/bin/env python
"""Script para testar os endpoints do dashboard"""
import requests
import json

BASE_URL = 'http://localhost:5000/api'

# Credenciais de teste
credentials = {
    'email': 'admin@empresa.com',
    'senha': 'admin123'
}

try:
    # Login
    print("1. Fazendo login...")
    login_resp = requests.post(f'{BASE_URL}/login', json=credentials)
    if login_resp.status_code != 200:
        print(f"❌ Erro no login: {login_resp.status_code}")
        print(login_resp.text)
        exit(1)
    
    token = login_resp.json()['access_token']
    headers = {'Authorization': f'Bearer {token}'}
    print(f"✓ Login bem-sucedido. Token obtido.")
    
    # Teste 1: Obter filtros disponíveis
    print("\n2. Testando endpoint /dashboard/filtros...")
    resp = requests.get(f'{BASE_URL}/dashboard/filtros', headers=headers)
    print(f"Status: {resp.status_code}")
    filtros = resp.json()
    print(f"Filtros disponíveis:")
    print(f"  - Anos: {filtros.get('anos', [])}")
    print(f"  - UFs: {len(filtros.get('ufs', []))} UFs disponíveis")
    print(f"  - Grupos: {len(filtros.get('grupos', []))} Grupos disponíveis")
    print(f"  - Categorias: {len(filtros.get('categorias', []))} Categorias disponíveis")
    
    # Teste 2: Obter dados do dashboard sem filtros
    print("\n3. Testando endpoint /dashboard (sem filtros)...")
    resp = requests.get(f'{BASE_URL}/dashboard', headers=headers)
    print(f"Status: {resp.status_code}")
    data = resp.json()
    print(f"Dados do dashboard:")
    print(f"  - Total Orçado: R$ {data['totais']['total_orcado']:.2f}")
    print(f"  - Total Realizado: R$ {data['totais']['total_realizado']:.2f}")
    print(f"  - Total Diferença: R$ {data['totais']['total_dif']:.2f}")
    print(f"  - % Execução: {data['totais']['percentual_execucao']:.2f}%")
    print(f"  - Meses com dados: {len(data['dados_mensais'])}")
    
    # Teste 3: Obter dados do dashboard com filtro de ano
    if filtros['anos']:
        ano = filtros['anos'][0]
        print(f"\n4. Testando endpoint /dashboard (filtro: ano={ano})...")
        resp = requests.get(f'{BASE_URL}/dashboard', headers=headers, params={'ano': ano})
        print(f"Status: {resp.status_code}")
        data = resp.json()
        print(f"Dados do dashboard para {ano}:")
        print(f"  - Total Orçado: R$ {data['totais']['total_orcado']:.2f}")
        print(f"  - Total Realizado: R$ {data['totais']['total_realizado']:.2f}")
    
    # Teste 4: Obter KPIs
    print(f"\n5. Testando endpoint /dashboard/kpis...")
    resp = requests.get(f'{BASE_URL}/dashboard/kpis', headers=headers)
    print(f"Status: {resp.status_code}")
    kpis = resp.json()
    print(f"KPIs:")
    print(f"  - Total de Categorias: {kpis['total_categorias']}")
    print(f"  - Total de Orçamentos: {kpis['total_orcamentos']}")
    print(f"  - Aguardando Aprovação: {kpis['aguardando_aprovacao']}")
    print(f"  - Aprovados: {kpis['aprovados']}")
    
    print("\n✓ Todos os testes passaram com sucesso!")
    
except Exception as e:
    print(f"❌ Erro: {e}")
    import traceback
    traceback.print_exc()
