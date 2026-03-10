import os
import click
from dotenv import load_dotenv
from sqlalchemy import or_

from app import create_app
from models import db, Log

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

@click.command()
@click.option('--yes', is_flag=True, help='Skip confirmation prompt.')
def delete_submission_rejection_logs(yes):
    """
    Script para deletar todos os logs de submissão e reprovação de orçamentos.
    Exige confirmação do usuário antes de executar.
    """
    # Determina o ambiente e cria a aplicação para ter o contexto correto
    config_name = os.getenv('FLASK_ENV', 'development')
    app = create_app(config_name)

    with app.app_context():
        if not yes:
            if not click.confirm(
                click.style(
                    'ATENÇÃO: Você está prestes a deletar TODOS os registros de Submissões e Reprovações.\n'
                    'Esta ação se aplica apenas aos registros de LOG e não deleta os orçamentos em si.\n'
                    'Esta ação NÃO PODE ser desfeita.\n\n'
                    'Deseja realmente continuar?',
                    fg='red', bold=True
                )
            ):
                click.echo('Operação cancelada pelo usuário.')
                return

        click.echo('Processando... Deletando registros de log de submissões e reprovações...')
        
        try:
            # Filtra os logs que serão deletados
            query = Log.query.filter(
                or_(
                    Log.acao.like('%Submissão em lote%'),
                    Log.acao.like('%Reprovação em lote%'),
                    Log.acao.like('%Reprovou%')
                )
            )
            
            num_deleted = query.delete(synchronize_session=False)
            db.session.commit()
            
            click.echo(click.style(f'\nOperação concluída: {num_deleted} registros de log foram deletados com sucesso.', fg='green'))

        except Exception as e:
            db.session.rollback()
            click.echo(click.style(f'Erro ao deletar os registros de log: {e}', fg='red'))


if __name__ == '__main__':
    delete_submission_rejection_logs()
