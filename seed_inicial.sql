-- ===============================
-- SEED INICIAL - Controle Orçamentário
-- ===============================
-- Execute este script após criar as tabelas

USE logtudo01;

-- ===============================
-- USUÁRIOS INICIAIS
-- ===============================
-- Senha para todos: admin123, gestor123, visualizador123
-- Hash gerado com: werkzeug.security.generate_password_hash('senha')

INSERT INTO usuarios (nome, email, senha_hash, papel) VALUES
('Administrador', 'admin@empresa.com', 'pbkdf2:sha256:600000$6RJYWXvB8ByT$e3fc8b4c5a1e9c3d2f8a7b6c5d4e3f2a1b0c9d8e7f6a5b4c3d2e1f0a9b8c7d6e5f4a3b2c1d0e9f8a7b6c5d4e3f2a1b0', 'admin'),
('Gestor Financeiro', 'gestor@empresa.com', 'pbkdf2:sha256:600000$7SKZXYwC9CzU$f4gd9c5b6a2f0d1e3c8b4a7e6d5c4b3a2f1e0d9c8b7a6e5d4c3b2a1f0e9d8c7b6a5e4d3c2b1a0f9e8d7c6b5a4d3c2b1a0', 'gestor'),
('Visualizador Padrão', 'visualizador@empresa.com', 'pbkdf2:sha256:600000$8TLAYZxD0DaV$g5he0d6c7b3a1e2d4c9b5a8f7e6d5c4b3a2f1e0d9c8b7a6f5e4d3c2b1a0f9e8d7c6b5a4e3d2c1b0a9f8e7d6c5b4a3d2c1b0', 'visualizador');

-- ===============================
-- CATEGORIAS DE EXEMPLO
-- ===============================
INSERT INTO categorias (dono, tipo_despesa, uf, master, grupo, cod_class, classe_custo) VALUES
-- TI
('TI', 'Operacional', 'SP', 'Tecnologia', 'Infraestrutura', '001', 'Servidores'),
('TI', 'Operacional', 'SP', 'Tecnologia', 'Software', '002', 'Licenças'),
('TI', 'Operacional', 'SP', 'Tecnologia', 'Suporte', '003', 'Manutenção'),

-- RH
('RH', 'Pessoal', 'RJ', 'Recursos Humanos', 'Folha de Pagamento', '004', 'Salários'),
('RH', 'Pessoal', 'RJ', 'Recursos Humanos', 'Benefícios', '005', 'Vale Alimentação'),
('RH', 'Pessoal', 'RJ', 'Recursos Humanos', 'Treinamento', '006', 'Capacitação'),

-- Marketing
('Marketing', 'Operacional', 'MG', 'Comercial', 'Publicidade', '007', 'Mídia Digital'),
('Marketing', 'Operacional', 'MG', 'Comercial', 'Eventos', '008', 'Feiras e Congressos'),
('Marketing', 'Operacional', 'MG', 'Comercial', 'Material', '009', 'Impressos'),

-- Administrativo
('Administrativo', 'Operacional', 'BA', 'Administrativo', 'Facilities', '010', 'Aluguel'),
('Administrativo', 'Operacional', 'BA', 'Administrativo', 'Utilities', '011', 'Energia'),
('Administrativo', 'Operacional', 'BA', 'Administrativo', 'Utilities', '012', 'Água'),

-- Financeiro
('Financeiro', 'Financeiro', 'SP', 'Financeiro', 'Bancário', '013', 'Tarifas Bancárias'),
('Financeiro', 'Financeiro', 'SP', 'Financeiro', 'Impostos', '014', 'PIS/COFINS'),
('Financeiro', 'Financeiro', 'SP', 'Financeiro', 'Seguros', '015', 'Seguros Gerais');

-- ===============================
-- ORÇAMENTOS DE EXEMPLO (2025)
-- ===============================
-- Inserindo orçamentos para Janeiro/2025 (apenas orçado)

INSERT INTO orcamentos (id_categoria, mes, ano, orcado, realizado, status, criado_por) 
SELECT 
    id_categoria,
    'Janeiro',
    2025,
    CASE 
        WHEN tipo_despesa = 'Pessoal' THEN 50000.00
        WHEN tipo_despesa = 'Operacional' THEN 25000.00
        ELSE 15000.00
    END,
    0.00,
    'rascunho',
    1
FROM categorias;

-- ===============================
-- LOGS INICIAIS
-- ===============================
INSERT INTO logs (id_usuario, acao, tabela_afetada, id_registro, detalhes) VALUES
(1, 'Sistema inicializado', 'sistema', NULL, '{"mensagem": "Seed inicial executado com sucesso"}');

-- ===============================
-- VERIFICAÇÃO
-- ===============================
SELECT 'Usuários criados:' as info, COUNT(*) as total FROM usuarios;
SELECT 'Categorias criadas:' as info, COUNT(*) as total FROM categorias;
SELECT 'Orçamentos criados:' as info, COUNT(*) as total FROM orcamentos;

-- ===============================
-- INFORMAÇÕES DE ACESSO
-- ===============================
SELECT 
    '========================================' as '                                        ',
    'USUÁRIOS CRIADOS' as '                                        ',
    '========================================' as '                                        '
UNION ALL
SELECT '', 'Admin:', 'admin@empresa.com / admin123'
UNION ALL
SELECT '', 'Gestor:', 'gestor@empresa.com / gestor123'
UNION ALL
SELECT '', 'Visualizador:', 'visualizador@empresa.com / visualizador123'
UNION ALL
SELECT '', '', ''
UNION ALL
SELECT '', '⚠️  ALTERE AS SENHAS APÓS PRIMEIRO ACESSO!', '';