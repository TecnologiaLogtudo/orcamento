import os
import click
from dotenv import load_dotenv
from app import create_app
from models import db, Categoria

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

def delete_all_categories():
    """
    Script para deletar todas as categorias que não possuem orçamentos vinculados.
    Exige confirmação do usuário antes de executar.
    """
    # Determina o ambiente e cria a aplicação para ter o contexto correto
    config_name = os.getenv('FLASK_ENV', 'development')
    app = create_app(config_name)

    with app.app_context():
        if not click.confirm(
            click.style(
                'ATENÇÃO: Você está prestes a deletar categorias do banco de dados.\n'
                'Esta ação NÃO PODE ser desfeita.\n'
                '--> Categorias com orçamentos vinculados NÃO serão deletadas para manter a integridade dos dados.\n\n'
                'Deseja realmente continuar?',
                fg='yellow', bold=True
            )
        ):
            click.echo('Operação cancelada pelo usuário.')
            return

        click.echo('🔍 Processando... Verificando categorias para deletar...')
        
        # Query para deletar categorias que não têm nenhum orçamento associado.
        # O método .delete() é mais performático para operações em massa.
        num_deleted = Categoria.query.filter(~Categoria.orcamentos.any()).delete(synchronize_session=False)
        
        # Contar as categorias que sobraram (com orçamentos)
        num_skipped = Categoria.query.count()

        # Efetivar a transação
        db.session.commit()

        click.echo(click.style(f'\n✅ Operação concluída: {num_deleted} categorias foram deletadas com sucesso.', fg='green'))
        
        if num_skipped > 0:
            click.echo(click.style(f'⚠️  {num_skipped} categorias foram mantidas pois já possuem orçamentos vinculados.', fg='yellow'))
        else:
            click.echo('Nenhuma categoria foi mantida.')

if __name__ == '__main__':
    delete_all_categories()