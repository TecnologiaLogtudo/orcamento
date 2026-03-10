import os
import click
from dotenv import load_dotenv
from app import create_app
from models import db, Orcamento

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

@click.command()
@click.option('--yes', is_flag=True, help='Pular o pedido de confirmação.')
def delete_all_lancamentos(yes):
    """
    Script para deletar todos os lançamentos (orçamentos).
    Exige confirmação do usuário antes de executar.
    """
    # Determina o ambiente e cria a aplicação para ter o contexto correto
    config_name = os.getenv('FLASK_ENV', 'development')
    app = create_app(config_name)

    with app.app_context():
        if not yes:
            if not click.confirm(
                click.style(
                    'ATENÇÃO: Você está prestes a deletar TODOS os lançamentos (orçamentos) do banco de dados.\n'
                    'Esta ação NÃO PODE ser desfeita.\n\n'
                    'Deseja realmente continuar?',
                    fg='red', bold=True
                )
            ):
                click.echo('Operação cancelada pelo usuário.')
                return

        click.echo('🔍 Processando... Deletando todos os lançamentos...')
        
        try:
            num_deleted = db.session.query(Orcamento).delete()
            db.session.commit()
            click.echo(click.style(f'\n✅ Operação concluída: {num_deleted} lançamentos foram deletados com sucesso.', fg='green'))
        except Exception as e:
            db.session.rollback()
            click.echo(click.style(f'❌ Erro ao deletar os lançamentos: {e}', fg='red'))


if __name__ == '__main__':
    delete_all_lancamentos()
