import os
import pymysql
import logging
from dotenv import load_dotenv

# --- Configuração do Logging ---
# Cria um logger
logger = logging.getLogger('db_test')
logger.setLevel(logging.INFO)

# Formato do log
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

# Handler para o console
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

# Handler para o arquivo
file_handler = logging.FileHandler('db_test.log', encoding='utf-8')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# --- Teste de Conexão ---
def test_db_connection():
    """
    Tenta conectar ao banco de dados MySQL usando as credenciais do .env
    e registra o resultado.
    """
    logger.info("Iniciando teste de conexão com o banco de dados...")
    
    # Carrega as variáveis do arquivo .env
    load_dotenv()
    
    # Pega as credenciais do ambiente
    host = os.getenv('MYSQL_HOST')
    user = os.getenv('MYSQL_USER')
    password = os.getenv('MYSQL_PASSWORD')
    db_name = os.getenv('MYSQL_DB')
    
    logger.info(f"Tentando conectar em: host={host}, user={user}, db={db_name}")
    
    try:
        # Tenta estabelecer a conexão
        connection = pymysql.connect(host=host, user=user, password=password, database=db_name, connect_timeout=10)
        logger.info("✅ Conexão com o banco de dados estabelecida com sucesso!")
        connection.close()
        logger.info("Conexão fechada.")
    except pymysql.MySQLError as e:
        logger.error(f"❌ Falha ao conectar ao banco de dados: {e}")

if __name__ == '__main__':
    test_db_connection()