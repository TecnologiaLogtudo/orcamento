# Controle de Orçamento

Este é um projeto de controle orçamentário com frontend em React e backend em Flask.

## Visão Geral

O projeto permite o gerenciamento de orçamentos, com as seguintes funcionalidades:

- **Autenticação de Usuários**: Sistema de login com JWT.
- **Gerenciamento de Usuários**: Criação, edição e exclusão de usuários com diferentes papéis (admin, gestor, visualizador).
- **Gerenciamento de Categorias**: Criação, edição e exclusão de categorias de orçamento.
- **Lançamentos Orçamentários**: Criação e atualização de lançamentos orçamentários.
- **Fluxo de Aprovação**: Submissão, aprovação e reprovação de orçamentos.
- **Dashboard**: Visualização de dados com gráficos e KPIs.
- **Relatórios**: Exportação de dados em Excel e PDF.
- **Logs**: Rastreamento de atividades no sistema.
- **Upload de Arquivos**: Funcionalidade para upload de arquivos.

## Tecnologias Utilizadas

### Frontend

- **React**: Biblioteca para construção de interfaces de usuário.
- **Vite**: Ferramenta de build para o frontend.
- **Axios**: Cliente HTTP para requisições à API.
- **Chart.js**: Biblioteca para criação de gráficos.
- **Tailwind CSS**: Framework de CSS para estilização.

### Backend

- **Flask**: Framework web para o backend.
- **SQLAlchemy**: ORM para interação com o banco de dados.
- **Flask-JWT-Extended**: Para gerenciamento de tokens de autenticação JWT.
- **MySQL**: Banco de dados relacional.

## Como Executar o Projeto

### Pré-requisitos

- Node.js e npm (ou yarn)
- Python e pip
- MySQL

### Backend

1.  **Navegue até a pasta do backend**:
    ```bash
    cd backend
    ```

2.  **Crie e ative um ambiente virtual**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # No Windows, use `venv\Scripts\activate`
    ```

3.  **Instale as dependências**:
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure as variáveis de ambiente**:
    Crie um arquivo `.env` na pasta `backend` com as seguintes variáveis:
    ```
    FLASK_ENV=development
    SECRET_KEY=sua_chave_secreta
    JWT_SECRET_KEY=sua_chave_jwt_secreta
    MYSQL_HOST=seu_host_mysql
    MYSQL_USER=seu_usuario_mysql
    MYSQL_PASSWORD=sua_senha_mysql
    MYSQL_DB=seu_banco_de_dados_mysql
    ```

5.  **Crie as tabelas do banco de dados**:
    ```bash
    flask create_db_command
    ```

6.  **Inicie o servidor de desenvolvimento**:
    ```bash
un run
    ```
    O servidor estará disponível em `http://localhost:5000`.

### Frontend

1.  **Navegue até a pasta do frontend**:
    ```bash
    cd frontend
    ```

2.  **Instale as dependências**:
    ```bash
    npm install
    ```

3.  **Configure as variáveis de ambiente**:
    Crie um arquivo `.env.local` na pasta `frontend` com a seguinte variável:
    ```
    VITE_API_URL=http://localhost:5000/api
    ```

4.  **Inicie o servidor de desenvolvimento**:
    ```bash
    npm run dev
    ```
    A aplicação estará disponível em `http://localhost:5173`.

## Endpoints da API

A documentação dos endpoints da API pode ser encontrada no arquivo `backend/openapi.yaml`.

### Dashboard

- `GET /api/dashboard`: Retorna os dados principais do dashboard.
- `GET /api/dashboard/filtros`: Retorna os filtros disponíveis para o dashboard.
- `GET /api/dashboard/kpis`: Retorna os KPIs do sistema.
- `GET /api/dashboard/comparativo`: Retorna uma comparação com o período anterior.
- `GET /api/dashboard/distribuicao`: Retorna a distribuição de dados para gráficos.

## Estrutura do Projeto

```
.
├── backend
│   ├── app.py
│   ├── config.py
│   ├── models.py
│   ├── requirements.txt
│   ├── routes
│   │   ├── auth.py
│   │   ├── dashboard.py
│   │   └── ...
│   └── ...
├── frontend
│   ├── public
│   ├── src
│   │   ├── components
│   │   │   ├── Dashboard.jsx
│   │   │   └── ...
│   │   ├── services
│   │   │   └── api.js
│   │   ├── App.jsx
│   │   └── main.jsx
│   └── ...
└── README.md
```
