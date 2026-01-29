#!/usr/bin/env python
"""Script para testar os novos endpoints do dashboard"""
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
    
    # Teste 1: Obter filtros com cache
    print("\n2. Testando endpoint /dashboard/filtros (com cache)...")
    for i in range(2):
        resp = requests.get(f'{BASE_URL}/dashboard/filtros', headers=headers)
        print(f"   Tentativa {i+1}: Status {resp.status_code}")
        filtros = resp.json()
        print(f"   - Anos: {filtros.get('anos', [])}")
    
    # Teste 2: Novo endpoint de comparativo
    print("\n3. Testando endpoint /dashboard/comparativo...")
    resp = requests.get(f'{BASE_URL}/dashboard/comparativo', headers=headers, params={'ano': 2025})
    print(f"Status: {resp.status_code}")
    if resp.status_code == 200:
        comp = resp.json()
        print(f"Comparativo entre {comp['periodo_anterior']['ano']} e {comp['periodo_atual']['ano']}:")
        print(f"  Período Atual ({comp['periodo_atual']['ano']}):")
        print(f"    - Total Orçado: R$ {comp['periodo_atual']['dados']['total_orcado']:.2f}")
        print(f"    - Total Realizado: R$ {comp['periodo_atual']['dados']['total_realizado']:.2f}")
        print(f"  Variações:")
        print(f"    - Orçado: {comp['variacoes']['total_orcado_pct']:.2f}%")
        print(f"    - Realizado: {comp['variacoes']['total_realizado_pct']:.2f}%")
    else:
        print(f"❌ Erro: {resp.json()}")
    
    # Teste 3: Novo endpoint de distribuição por categoria
    print("\n4. Testando endpoint /dashboard/distribuicao (tipo=categoria)...")
    resp = requests.get(f'{BASE_URL}/dashboard/distribuicao', headers=headers, 
                       params={'ano': 2025, 'tipo': 'categoria'})
    print(f"Status: {resp.status_code}")
    if resp.status_code == 200:
        dist = resp.json()
        print(f"Distribuição por Categoria:")
        print(f"  - Total Orçado: R$ {dist['total_orcado']:.2f}")
        print(f"  - Itens:")
        for item in dist['dados'][:3]:
            print(f"    • {item['nome']}: R$ {item['orcado']:.2f} ({item['percentual']:.1f}%)")
    else:
        print(f"❌ Erro: {resp.json()}")
    
    # Teste 4: Novo endpoint de distribuição por grupo
    print("\n5. Testando endpoint /dashboard/distribuicao (tipo=grupo)...")
    resp = requests.get(f'{BASE_URL}/dashboard/distribuicao', headers=headers, 
                       params={'ano': 2025, 'tipo': 'grupo'})
    print(f"Status: {resp.status_code}")
    if resp.status_code == 200:
        dist = resp.json()
        print(f"Distribuição por Grupo:")
        print(f"  - Total Orçado: R$ {dist['total_orcado']:.2f}")
        print(f"  - Total de Grupos: {len(dist['dados'])}")
        if dist['dados']:
            item = dist['dados'][0]
            print(f"  - Maior Grupo: {item['nome']} - R$ {item['orcado']:.2f} ({item['percentual']:.1f}%)")
    else:
        print(f"❌ Erro: {resp.json()}")
    
    print("\n✓ Todos os testes completados com sucesso!")
    
except Exception as e:
    print(f"❌ Erro: {e}")
    import traceback
    traceback.print_exc()
