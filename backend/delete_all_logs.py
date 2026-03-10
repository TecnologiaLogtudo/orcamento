import os
import click
from dotenv import load_dotenv
from app import create_app
from models import db, Log

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

@click.command()
@click.option('--yes', is_flag=True, help='Pular o pedido de confirmação.')
def delete_all_logs(yes):
    """
    Script para deletar TODOS os logs de auditoria do sistema.
    Exige confirmação do usuário antes de executar.
    """
    # Determina o ambiente e cria a aplicação para ter o contexto correto
    config_name = os.getenv('FLASK_ENV', 'development')
    app = create_app(config_name)

    with app.app_context():
        if not yes:
            if not click.confirm(
                click.style(
                    'ATENÇÃO: Você está prestes a deletar TODOS os registros de LOG de auditoria do sistema.\n'
                    'Esta ação NÃO PODE ser desfeita.\n\n'
                    'Deseja realmente continuar?',
                    fg='red', bold=True
                )
            ):
                click.echo('Operação cancelada pelo usuário.')
                return

        click.echo('Processando... Deletando todos os registros de log de auditoria...')
        
        try:
            # Deleta todos os logs da tabela Log
            num_logs_deleted = db.session.query(Log).delete()
            db.session.commit()
            
            click.echo(click.style(f'\nOperação concluída: {num_logs_deleted} registros de log de auditoria foram deletados com sucesso.', fg='green'))

        except Exception as e:
            db.session.rollback()
            click.echo(click.style(f'Erro ao deletar os registros de log: {e}', fg='red'))


if __name__ == '__main__':
    delete_all_logs()
