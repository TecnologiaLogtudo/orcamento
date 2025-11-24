#!/usr/bin/env python
import sys
sys.path.insert(0, '/home/users/felip/OneDrive/Logtudo/Controle_orcamento/backend')

from app import create_app
from app.models import db, Log, Orcamento, Usuario

app = create_app()

with app.app_context():
    # Verificar logs com 'Submissão em lote'
    logs = Log.query.filter(Log.acao.contains('Submissão em lote')).all()
    print(f"\n=== Logs com 'Submissão em lote': {len(logs)} ===")
    for log in logs:
        print(f"\nID: {log.id_log}")
        print(f"Ação: {log.acao}")
        print(f"Tabela: {log.tabela_afetada}")
        print(f"Timestamp: {log.timestamp}")
        print(f"Detalhes: {log.detalhes}")
    
    # Verificar orçamentos em 'aguardando_aprovacao'
    print(f"\n=== Orçamentos em 'aguardando_aprovacao': ===")
    orc_pendentes = Orcamento.query.filter_by(status='aguardando_aprovacao').all()
    print(f"Total: {len(orc_pendentes)}")
    for orc in orc_pendentes[:5]:  # Mostrar apenas os 5 primeiros
        print(f"  - ID: {orc.id_orcamento}, Categoria: {orc.id_categoria}, Status: {orc.status}")
    
    # Verificar usuários com papel 'gestor'
    print(f"\n=== Usuários com papel 'gestor': ===")
    gestores = Usuario.query.filter_by(papel='gestor').all()
    print(f"Total: {len(gestores)}")
    for gestor in gestores:
        print(f"  - {gestor.id_usuario}: {gestor.nome}")
