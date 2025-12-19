#!/usr/bin/env python
"""
Script para criar ou atualizar a view resumo_orcamento
Agrega dados de orçamentos aprovados com informações das categorias
"""
from app import create_app
from models import db
from sqlalchemy import text

def create_resumo_view():
    """Cria ou recria a view resumo_orcamento"""
    app = create_app()
    
    with app.app_context():
        try:
            # Remover tabela existente se for tabela
            print("Verificando e removendo tabela antiga...")
            db.session.execute(text("DROP VIEW IF EXISTS resumo_orcamento"))
            db.session.commit()
            print("Tabela removida")
            
            # Criar view
            print("Criando view...")
            sql = """
            CREATE VIEW resumo_orcamento AS
            SELECT
                c.categoria,
                c.uf,
                c.master,
                c.grupo,
                c.cod_class,
                c.classe_custo,
                o.ano,
                o.mes,
                SUM(CAST(o.orcado AS DECIMAL(15, 2))) as total_orcado,
                SUM(CAST(o.realizado AS DECIMAL(15, 2))) as total_realizado,
                SUM(CAST(o.dif AS DECIMAL(15, 2))) as total_dif
            FROM orcamentos o
            INNER JOIN categorias c ON o.id_categoria = c.id_categoria
            WHERE o.status = 'aprovado'
            GROUP BY 
                c.id_categoria,
                c.categoria,
                c.uf,
                c.master,
                c.grupo,
                c.cod_class,
                c.classe_custo,
                o.ano,
                o.mes
            ORDER BY o.ano DESC, o.mes DESC
            """
            db.session.execute(text(sql))
            db.session.commit()
            print("View criada com sucesso!")            # Verificar quantos registros foram agregados
            result = db.session.execute(text("SELECT COUNT(*) FROM resumo_orcamento"))
            count = result.scalar()
            print(f"Total de registros na view: {count}")
            
            # Amostra de dados
            sample = db.session.execute(text("""
                SELECT categoria, ano, mes, total_orcado, total_realizado, total_dif 
                FROM resumo_orcamento 
                LIMIT 5
            """))
            print("\nAmostra de dados:")
            for row in sample:
                print(f"  {row[0]}: {row[1]}/{row[2]} - Orcado: {row[3]}, Realizado: {row[4]}, Dif: {row[5]}")
            
        except Exception as e:
            print(f"Erro ao criar view: {e}")
            db.session.rollback()
            raise

if __name__ == '__main__':
    create_resumo_view()
