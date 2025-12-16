#app/routes/dashboard.py
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from app.models import db, ResumoOrcamento, Orcamento, Categoria
from sqlalchemy import func, and_
from functools import lru_cache
from datetime import datetime, timedelta

bp = Blueprint('dashboard', __name__)

# Cache para filtros disponíveis (atualiza a cada 30 minutos)
_filtros_cache = None
_filtros_cache_time = None
CACHE_DURATION = 1800  # 30 minutos em segundos

def _get_filtros_from_db():
    """Busca filtros do banco de dados"""
    try:
        # Anos: buscar de Orcamento (tabela primária de dados)
        anos_result = db.session.query(Orcamento.ano).distinct().order_by(Orcamento.ano.desc()).all()
        anos = [int(row[0]) for row in anos_result if row[0] is not None]
        
        # UFs: buscar de Categoria (relacionada a Orcamento via id_categoria)
        ufs_result = db.session.query(Categoria.uf).distinct().filter(Categoria.uf != None).order_by(Categoria.uf).all()
        ufs = [row[0] for row in ufs_result if row[0]]
        
        # Centros de Custo (master): buscar de Categoria
        centros_custo_result = db.session.query(Categoria.master).distinct().filter(Categoria.master != None).order_by(Categoria.master).all()
        centros_de_custo = [row[0] for row in centros_custo_result if row[0]]
        
        # Categorias: buscar de Categoria
        categorias_result = db.session.query(Categoria.categoria).distinct().filter(Categoria.categoria != None).order_by(Categoria.categoria).all()
        categorias = [row[0] for row in categorias_result if row[0]]
        
        return {
            'anos': anos,
            'ufs': ufs,
            'centros_de_custo': centros_de_custo,
            'categorias': categorias
        }
    except Exception as e:
        return {'anos': [], 'ufs': [], 'centros_de_custo': [], 'categorias': []}

def _get_filtros_cached():
    """Retorna filtros do cache ou do banco de dados"""
    global _filtros_cache, _filtros_cache_time
    
    now = datetime.now()
    
    # Se não há cache ou expirou, busca do banco
    if _filtros_cache is None or _filtros_cache_time is None or \
       (now - _filtros_cache_time).total_seconds() > CACHE_DURATION:
        _filtros_cache = _get_filtros_from_db()
        _filtros_cache_time = now
    
    return _filtros_cache

def limpar_cache_filtros():
    """Limpa o cache de filtros (chamar quando houver novos dados)"""
    global _filtros_cache, _filtros_cache_time
    _filtros_cache = None
    _filtros_cache_time = None

@bp.route('/dashboard', methods=['GET'])
@jwt_required()
def get_dashboard():
    """Retorna dados consolidados do dashboard"""
    try:
        # Filtros
        ano = request.args.get('ano', type=int)
        categoria = request.args.get('categoria')
        uf = request.args.get('uf')
        centro_custo = request.args.get('centro_custo')
        
        # Query base para totais, agora direto nas tabelas Orcamento e Categoria
        query = db.session.query(
            func.sum(Orcamento.orcado).label('total_orcado'),
            func.sum(Orcamento.realizado).label('total_realizado'),
            func.sum(Orcamento.dif).label('total_dif')
        ).join(Categoria, Categoria.id_categoria == Orcamento.id_categoria).filter(Orcamento.status == 'aprovado')

        # Aplicar filtros
        if ano:
            query = query.filter(Orcamento.ano == ano)
        if categoria:
            query = query.filter(Categoria.categoria == categoria)
        if uf:
            query = query.filter(Categoria.uf == uf)
        if centro_custo:
            query = query.filter(Categoria.master == centro_custo)
        
        result = query.first()
        
        # Totais gerais
        totais = {
            'total_orcado': float(result.total_orcado) if result.total_orcado else 0.0,
            'total_realizado': float(result.total_realizado) if result.total_realizado else 0.0,
            'total_dif': float(result.total_dif) if result.total_dif else 0.0
        }
        
        # Calcular percentual de execução
        if totais['total_orcado'] > 0:
            totais['percentual_execucao'] = (totais['total_realizado'] / totais['total_orcado']) * 100
        else:
            totais['percentual_execucao'] = 0.0
        
        # Dados por mês, agora direto nas tabelas Orcamento e Categoria
        query_mensal = db.session.query(
            Orcamento.mes,
            func.sum(Orcamento.orcado).label('orcado'),
            func.sum(Orcamento.realizado).label('realizado'),
            func.sum(Orcamento.dif).label('dif')
        ).join(Categoria, Categoria.id_categoria == Orcamento.id_categoria).filter(Orcamento.status == 'aprovado')
        
        # Aplicar mesmos filtros
        if ano:
            query_mensal = query_mensal.filter(Orcamento.ano == ano)
        if categoria:
            query_mensal = query_mensal.filter(Categoria.categoria == categoria)
        if uf:
            query_mensal = query_mensal.filter(Categoria.uf == uf)
        if centro_custo:
            query_mensal = query_mensal.filter(Categoria.master == centro_custo)
        
        dados_mensais = query_mensal.group_by(Orcamento.mes).all()
        
        meses_ordenados = ['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
                          'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro']
        
        dados_por_mes = []
        for mes in meses_ordenados:
            item = next((m for m in dados_mensais if m.mes == mes), None)
            dados_por_mes.append({
                'mes': mes,
                'orcado': float(item.orcado) if item and item.orcado else 0.0,
                'realizado': float(item.realizado) if item and item.realizado else 0.0,
                'dif': float(item.dif) if item and item.dif else 0.0
            })
        
        # Mês crítico
        # - Mês de maior economia: maior desvio positivo (orçado - realizado)
        # - Mês de maior gasto: maior desvio negativo (menor valor de dif)
        # - Mês de maior precisão: menor desvio absoluto (mais próximo de zero)
        meses_criticos = []
        
        # Filtrar meses com dados para evitar processar meses vazios
        meses_com_dados = [m for m in dados_por_mes if m['orcado'] > 0 or m['realizado'] > 0]

        if meses_com_dados:
            # Dicionário para guardar os meses únicos, usando o nome do mês como chave
            candidatos = {}

            # 1. Mês de maior economia (maior desvio positivo)
            maior_economia = max(meses_com_dados, key=lambda m: m['dif'])
            if maior_economia['dif'] > 0:
                candidatos[maior_economia['mes']] = {
                    'mes': maior_economia['mes'],
                    'orcado': maior_economia['orcado'],
                    'realizado': maior_economia['realizado'],
                    'desvio': maior_economia['dif'],
                    'percentual': ((maior_economia['realizado'] / maior_economia['orcado'] * 100) - 100) if maior_economia['orcado'] > 0 else 0.0,
                    'tipo': 'economia'
                }

            # 2. Mês de maior gasto (maior desvio negativo)
            maior_gasto = min(meses_com_dados, key=lambda m: m['dif'])
            if maior_gasto['dif'] < 0:
                candidatos[maior_gasto['mes']] = {
                    'mes': maior_gasto['mes'],
                    'orcado': maior_gasto['orcado'],
                    'realizado': maior_gasto['realizado'],
                    'desvio': maior_gasto['dif'],
                    'percentual': ((maior_gasto['realizado'] / maior_gasto['orcado'] * 100) - 100) if maior_gasto['orcado'] > 0 else 0.0,
                    'tipo': 'gasto'
                }
            
            # 3. Mês de maior precisão (menor desvio absoluto)
            maior_precisao = min(meses_com_dados, key=lambda m: abs(m['dif']))
            # Adiciona apenas se o mês ainda não foi selecionado
            if maior_precisao['mes'] not in candidatos:
                candidatos[maior_precisao['mes']] = {
                    'mes': maior_precisao['mes'],
                    'orcado': maior_precisao['orcado'],
                    'realizado': maior_precisao['realizado'],
                    'desvio': maior_precisao['dif'],
                    'percentual': ((maior_precisao['realizado'] / maior_precisao['orcado'] * 100) - 100) if maior_precisao['orcado'] > 0 else 0.0,
                    'tipo': 'precisao'
                }

            meses_criticos = list(candidatos.values())
            
            # Fallback para o caso de todos os desvios serem zero
            if not meses_criticos and meses_com_dados:
                mes_neutro = meses_com_dados[0] # Pega o primeiro mês com dados
                meses_criticos.append({
                    'mes': mes_neutro['mes'],
                    'orcado': mes_neutro['orcado'],
                    'realizado': mes_neutro['realizado'],
                    'desvio': mes_neutro['dif'],
                    'percentual': 0.0,
                    'tipo': 'neutro'
                })
        
        # Top 5 centros de custo por desvio
        query_centros_custo = db.session.query(
            Categoria.master,
            func.sum(Orcamento.orcado).label('orcado_total'),
            func.sum(Orcamento.realizado).label('realizado_total'),
            func.sum(Orcamento.dif).label('dif_total')
        ).join(Categoria, Categoria.id_categoria == Orcamento.id_categoria).filter(Orcamento.status == 'aprovado')

        if ano:
            query_centros_custo = query_centros_custo.filter(Orcamento.ano == ano)
        if categoria:
            query_centros_custo = query_centros_custo.filter(Categoria.categoria == categoria)
        if uf:
            query_centros_custo = query_centros_custo.filter(Categoria.uf == uf)
        
        top_centros_custo = query_centros_custo.group_by(Categoria.master)\
                                 .order_by(func.abs(func.sum(Orcamento.dif)).desc())\
                                 .limit(5)\
                                 .all()
        
        centros_custo_criticos = [
            {
                'centro_custo': g.master,
                'orcado': float(g.orcado_total) if g.orcado_total else 0.0,
                'realizado': float(g.realizado_total) if g.realizado_total else 0.0,
                'desvio': float(g.dif_total) if g.dif_total else 0.0,
                'percentual': ((g.realizado_total / g.orcado_total * 100) - 100) if g.orcado_total and g.orcado_total > 0 else 0.0
            }
            for g in top_centros_custo
        ]
        
        # Dados por categoria
        query_categoria = db.session.query(
            Categoria.categoria,
            func.sum(Orcamento.orcado).label('orcado'),
            func.sum(Orcamento.realizado).label('realizado'),
            func.sum(Orcamento.dif).label('dif')
        ).join(Categoria, Categoria.id_categoria == Orcamento.id_categoria).filter(Orcamento.status == 'aprovado')
        
        if ano:
            query_categoria = query_categoria.filter(Orcamento.ano == ano)
        if uf:
            query_categoria = query_categoria.filter(Categoria.uf == uf)
        if centro_custo:
            query_categoria = query_categoria.filter(Categoria.master == centro_custo)
        
        dados_por_categoria_result = query_categoria.group_by(Categoria.categoria).all()
        
        dados_categoria = [
            {
                'categoria': d.categoria,
                'orcado': float(d.orcado) if d.orcado else 0.0,
                'realizado': float(d.realizado) if d.realizado else 0.0,
                'dif': float(d.dif) if d.dif else 0.0
            }
            for d in dados_por_categoria_result
        ]
        
        return jsonify({
            'totais': totais,
            'dados_mensais': dados_por_mes,
            'mes_critico': meses_criticos,
            'centros_custo_criticos': centros_custo_criticos,
            'centros_custo': dados_categoria
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/dashboard/filtros', methods=['GET'])
@jwt_required()
def get_dashboard_filtros():
    """Retorna valores disponíveis para filtros do dashboard (com cache)"""
    try:
        filtros = _get_filtros_cached()
        return jsonify(filtros), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/dashboard/comparativo', methods=['GET'])
@jwt_required()
def get_dashboard_comparativo():
    """Retorna dados comparativos entre período atual e período anterior"""
    try:
        ano_atual = request.args.get('ano', type=int)
        if not ano_atual:
            max_ano = db.session.query(func.max(Orcamento.ano)).scalar()
            ano_atual = max_ano if max_ano else datetime.now().year
        
        ano_anterior = ano_atual - 1
        
        def get_dados_ano(ano):
            """Obtém dados agregados para um ano específico diretamente de Orçamentos."""
            query = db.session.query(
                func.sum(Orcamento.orcado).label('total_orcado'),
                func.sum(Orcamento.realizado).label('total_realizado'),
                func.sum(Orcamento.dif).label('total_dif')
            ).filter(Orcamento.ano == ano, Orcamento.status == 'aprovado')
            
            result = query.first()
            return {
                'total_orcado': float(result.total_orcado) if result.total_orcado else 0.0,
                'total_realizado': float(result.total_realizado) if result.total_realizado else 0.0,
                'total_dif': float(result.total_dif) if result.total_dif else 0.0
            }
        
        dados_atual = get_dados_ano(ano_atual)
        dados_anterior = get_dados_ano(ano_anterior)
        
        def calcular_variacao(atual, anterior):
            if anterior == 0:
                return 100.0 if atual > 0 else 0.0
            return ((atual - anterior) / abs(anterior)) * 100
        
        comparativo = {
            'periodo_atual': {'ano': ano_atual, 'dados': dados_atual},
            'periodo_anterior': {'ano': ano_anterior, 'dados': dados_anterior},
            'variacoes': {
                'total_orcado_pct': calcular_variacao(dados_atual['total_orcado'], dados_anterior['total_orcado']),
                'total_realizado_pct': calcular_variacao(dados_atual['total_realizado'], dados_anterior['total_realizado']),
                'total_dif_pct': calcular_variacao(dados_atual['total_dif'], dados_anterior['total_dif'])
            }
        }
        
        return jsonify(comparativo), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/dashboard/distribuicao', methods=['GET'])
@jwt_required()
def get_dashboard_distribuicao():
    """Retorna dados de distribuição para gráficos de pizza"""
    try:
        ano = request.args.get('ano', type=int)
        categoria_filtro = request.args.get('categoria')
        uf = request.args.get('uf')
        centro_custo = request.args.get('centro_custo')
        tipo = request.args.get('tipo', default='categoria')

        if tipo not in ['categoria', 'centro_custo', 'grupo']:
            return jsonify({'error': 'Tipo de distribuição inválido'}), 400

        group_by_col = {
            'categoria': Categoria.categoria,
            'centro_custo': Categoria.master,
            'grupo': Categoria.grupo
        }[tipo]

        query = db.session.query(
            group_by_col.label('nome'),
            func.sum(Orcamento.orcado).label('orcado'),
            func.sum(Orcamento.realizado).label('realizado')
        ).join(Categoria, Orcamento.id_categoria == Categoria.id_categoria)\
         .filter(Orcamento.status == 'aprovado')

        if ano:
            query = query.filter(Orcamento.ano == ano)
        if categoria_filtro:
            query = query.filter(Categoria.categoria == categoria_filtro)
        if uf:
            query = query.filter(Categoria.uf == uf)
        if centro_custo:
            query = query.filter(Categoria.master == centro_custo)

        resultados = query.group_by('nome').all()

        dados_pizza = [
            {'nome': row.nome, 'orcado': float(row.orcado or 0), 'realizado': float(row.realizado or 0)}
            for row in resultados if row.nome
        ]

        total_orcado = sum(item['orcado'] for item in dados_pizza)
        if total_orcado > 0:
            for item in dados_pizza:
                item['percentual'] = (item['orcado'] / total_orcado) * 100
        else:
            for item in dados_pizza:
                item['percentual'] = 0.0

        return jsonify({
            'tipo': tipo,
            'dados': dados_pizza,
            'total_orcado': total_orcado
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/dashboard/kpis', methods=['GET'])
@jwt_required()
def get_kpis():
    """Retorna KPIs principais"""
    try:
        ano_atual = request.args.get('ano', type=int)
        
        # Total de categorias
        total_categorias = Categoria.query.count()
        
        # Total de orçamentos lançados
        query = Orcamento.query
        if ano_atual:
            query = query.filter_by(ano=ano_atual)
        
        total_orcamentos = query.count()
        
        # Orçamentos aguardando aprovação
        aguardando_aprovacao = query.filter_by(status='aguardando_aprovacao').count()
        
        # Orçamentos aprovados
        aprovados = query.filter_by(status='aprovado').count()
        
        return jsonify({
            'total_categorias': total_categorias,
            'total_orcamentos': total_orcamentos,
            'aguardando_aprovacao': aguardando_aprovacao,
            'aprovados': aprovados
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500