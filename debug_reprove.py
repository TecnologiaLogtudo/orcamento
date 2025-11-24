import sys
sys.path.insert(0, 'backend')
from app import create_app
from app.models import db, Orcamento, Log

app = create_app()

with app.app_context():
    # Verificar orçamentos em 'rascunho'
    orcs_rascunho = Orcamento.query.filter_by(status='rascunho').all()
    print(f"=== Orçamentos em 'rascunho': {len(orcs_rascunho)} ===")
    for orc in orcs_rascunho:
        print(f"  ID: {orc.id_orcamento}, Data aprovação: {orc.data_aprovacao}")
    
    # Verificar se há logs de reprovação individual
    print(f"\n=== Logs contendo 'Reprovou': ===")
    logs_reprovou = Log.query.filter(Log.acao.contains('Reprovou')).all()
    print(f"Total: {len(logs_reprovou)}")
    for log in logs_reprovou:
        print(f"\nID: {log.id_log}")
        print(f"Ação: {log.acao}")
        print(f"Detalhes: {log.detalhes}")
    
    # Verificar todos os logs de 'rascunho'
    print(f"\n=== Logs contendo 'reprova' ou 'rejeit': ===")
    logs_all = Log.query.filter(
        Log.acao.contains('reprova') | Log.acao.contains('rejeit')
    ).all()
    print(f"Total: {len(logs_all)}")
    for log in logs_all:
        print(f"\nID: {log.id_log}, Ação: {log.acao}, Detalhes: {log.detalhes}")
