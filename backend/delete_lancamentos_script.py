import os
import sys
import logging
from dotenv import load_dotenv

# --- HACK to fix fragile imports in the application ---
# The application uses `from models import ...` which is ambiguous and
# relies on the `backend` directory being in the python path. This
# script ensures that `models` always resolves to `backend.models`
# to prevent the module from being loaded twice under different names.

# 1. Ensure project root is in path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# 2. Pre-load `backend.models` and alias it as the top-level `models`
from backend import models
sys.modules['models'] = models
# --- END HACK ---

# Now we can import the rest of the app
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s: %(message)s')
load_dotenv(dotenv_path=os.path.join(project_root, '.env'))
from backend.app import create_app

def delete_specific_lancamentos():
    """
    Deleta lançamentos (orçamentos) específicos que estão com status 'aguardando_aprovacao'.
    """
    # Usar a configuração de produção por padrão, que carrega as variáveis de ambiente
    config_name = os.getenv('FLASK_ENV', 'production')
    app = create_app(config_name)

    with app.app_context():
        logging.info("Iniciando o script de deleção de lançamentos...")

        # Critérios para a deleção
        deletion_criteria = [
            {'master': '10 Aluguéis', 'grupo': 'Alug. Máq. Equitos', 'uf': 'S Filho'}
        ]

        try:
            # Buscar IDs das categorias que correspondem aos critérios
            category_ids_to_delete = []
            for criteria in deletion_criteria:
                categorias = models.Categoria.query.filter_by(
                    master=criteria['master'],
                    grupo=criteria['grupo'],
                    uf=criteria['uf']
                ).all()
                
                if categorias:
                    for cat in categorias:
                        category_ids_to_delete.append(cat.id_categoria)
                        logging.info(f"Categoria encontrada para deleção: ID={cat.id_categoria}, Master='{criteria['master']}', Grupo='{criteria['grupo']}', UF='{criteria['uf']}'")
                else:
                    logging.warning(f"Nenhuma categoria encontrada para Master='{criteria['master']}', Grupo='{criteria['grupo']}', UF='{criteria['uf']}'. Adicionando id_categoria=1451 conforme solicitado.")
                    category_ids_to_delete.append(1451)

            if not category_ids_to_delete:
                logging.info("Nenhuma categoria correspondente aos critérios foi encontrada. Nenhum lançamento será deletado.")
                return

            # Remover IDs duplicados
            unique_category_ids = list(set(category_ids_to_delete))
            
            # Buscar e deletar orçamentos com status 'aguardando_aprovacao' para essas categorias
            logging.info(f"Buscando orçamentos com status 'aguardando_aprovacao' para {len(unique_category_ids)} categorias...")

            orcamentos_to_delete = models.Orcamento.query.filter(
                models.Orcamento.id_categoria.in_(unique_category_ids),
                models.Orcamento.status == 'aguardando_aprovacao'
            ).all()

            if not orcamentos_to_delete:
                logging.info("Nenhum lançamento 'Aguardando Aprovação' encontrado para as categorias especificadas.")
                return

            num_deleted = 0
            for orcamento in orcamentos_to_delete:
                logging.info(f"Deletando lançamento: ID={orcamento.id_orcamento}, Mês={orcamento.mes}, Ano={orcamento.ano}, Categoria ID={orcamento.id_categoria}")
                models.db.session.delete(orcamento)
                num_deleted += 1

            models.db.session.commit()
            logging.info(f"Deleção concluída! {num_deleted} lançamento(s) foram removidos com sucesso.")

        except Exception as e:
            models.db.session.rollback()
            logging.error(f"Ocorreu um erro durante a deleção. Nenhuma alteração foi salva.")
            logging.error(f"Detalhes do erro: {e}", exc_info=True)

if __name__ == '__main__':
    # Verificar se as variáveis de ambiente necessárias estão configuradas
    required_env_vars = ['MYSQL_USER', 'MYSQL_PASSWORD', 'MYSQL_HOST', 'MYSQL_DB', 'SECRET_KEY', 'JWT_SECRET_KEY']
    missing_vars = [var for var in required_env_vars if not os.environ.get(var)]
    
    if missing_vars:
        logging.error("As seguintes variáveis de ambiente obrigatórias não estão definidas: " + ", ".join(missing_vars))
        logging.error("Por favor, configure-as em um arquivo .env no diretório raiz ou no seu ambiente.")
    else:
        delete_specific_lancamentos()
