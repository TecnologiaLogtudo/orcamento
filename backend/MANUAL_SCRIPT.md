# Scripts Avulsos

Este diretório pode conter scripts para tarefas de manutenção e administração.

## `delete_lancamentos_script.py`

Este script deleta lançamentos (orçamentos) específicos do banco de dados que estão com o status "Aguardando Aprovação".

### Critérios de Deleção

O script foi configurado para deletar orçamentos que atendam **TODOS** os seguintes critérios:

1.  O status do orçamento é `aguardando_aprovacao`.
2.  O orçamento pertence a uma categoria com **UMA** das seguintes combinações de `master`, `grupo` e `uf`:
    *   **Master:** `10 Aluguéis`, **Grupo:** `Alug Prédio/Imóv`, **UF:** `S Filho`
    *   **Master:** `10 Aluguéis`, **Grupo:** `Alug. Máq. Equitos`, **UF:** `S Filho`
    *   **Master:** `10 Aluguéis`, **Grupo:** `Aluguéis Softwares Op.`, **UF:** `S Filho`

### Como Usar

1.  **Configurar Variáveis de Ambiente:**
    *   Crie um arquivo chamado `.env` na raiz do projeto (`Controle_orcamento/.env`).
    *   Adicione as credenciais do banco de dados e as chaves de segurança neste arquivo. Ele deve ter o seguinte formato:
        ```env
        # Credenciais do Banco de Dados
        MYSQL_USER=seu_usuario_mysql
        MYSQL_PASSWORD=sua_senha_mysql
        MYSQL_HOST=seu_host_mysql
        MYSQL_DB=seu_banco_de_dados_mysql

        # Chaves de Segurança da Aplicação (podem ser valores aleatórios)
        SECRET_KEY=uma-chave-secreta-qualquer
        JWT_SECRET_KEY=outra-chave-secreta-qualquer
        ```
    *   Substitua os valores de exemplo pelas suas configurações reais.

2.  **Executar o Script:**
    *   Abra seu terminal na pasta raiz do projeto (`Controle_orcamento`).
    *   Execute o seguinte comando:
        ```bash
        python backend/delete_lancamentos_script.py
        ```

### O que Esperar

*   O script se conectará ao banco de dados e registrará seu progresso no terminal.
*   Ele primeiro identificará as categorias que correspondem aos critérios.
*   Em seguida, buscará e deletará todos os orçamentos com status `aguardando_aprovacao` associados a essas categorias.
*   Uma mensagem final indicará quantos lançamentos foram removidos ou se nenhum lançamento correspondente foi encontrado.
*   Se ocorrer um erro, nenhuma alteração será salva no banco de dados, e os detalhes do erro serão exibidos.