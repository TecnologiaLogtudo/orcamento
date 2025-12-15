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
        # 1. O mês com a maior diferença positiva (orçado - realizado).
        # 2. Se não houver mês com diferença positiva, o mês com a menor diferença negativa (mais próximo de zero).
        meses_criticos = []
        
        # Filtrar meses com dados para evitar processar meses vazios
        meses_com_dados = [m for m in dados_por_mes if m['orcado'] > 0 or m['realizado'] > 0]

        if meses_com_dados:
            meses_positivos = [m for m in meses_com_dados if m['dif'] > 0]

            if meses_positivos:
                # Caso 1: Encontrar a maior diferença positiva
                maior_dif_positiva = max(mes['dif'] for mes in meses_positivos)
                
                # Encontrar todos os meses que têm essa maior diferença
                meses_criticos = [{
                    'mes': mes['mes'],
                    'orcado': mes['orcado'],
                    'realizado': mes['realizado'],
                    'desvio': mes['dif'],
                    'percentual': ((mes['realizado'] / mes['orcado'] * 100) - 100) if mes['orcado'] and mes['orcado'] > 0 else 0.0
                } for mes in meses_positivos if mes['dif'] == maior_dif_positiva]
            
            else:
                # Caso 2: Nenhum mês com dif positiva, encontrar o mais próximo de zero (maior valor negativo/zero)
                if meses_com_dados: # Garante que não está vazio
                    mais_proximo_de_zero = max(mes['dif'] for mes in meses_com_dados)
                    
                    # Encontrar todos os meses que têm essa diferença
                    meses_criticos = [{
                        'mes': mes['mes'],
                        'orcado': mes['orcado'],
                        'realizado': mes['realizado'],
                        'desvio': mes['dif'],
                        'percentual': ((mes['realizado'] / mes['orcado'] * 100) - 100) if mes['orcado'] and mes['orcado'] > 0 else 0.0
                    } for mes in meses_com_dados if mes['dif'] == mais_proximo_de_zero]
        
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
        # Período atual (padrão: ano atual)
        ano_atual = request.args.get('ano', type=int)
        if not ano_atual:
            # Detecta o ano mais recente nos dados
            max_ano = db.session.query(func.max(ResumoOrcamento.ano)).scalar()
            ano_atual = max_ano if max_ano else datetime.now().year
        
        ano_anterior = ano_atual - 1
        
        # Função para obter dados de um ano
        def get_dados_ano(ano):
            query = db.session.query(
                func.sum(ResumoOrcamento.total_orcado).label('total_orcado'),
                func.sum(ResumoOrcamento.total_realizado).label('total_realizado'),
                func.sum(ResumoOrcamento.total_dif).label('total_dif')
            ).filter(ResumoOrcamento.ano == ano)
            
            result = query.first()
            return {
                'total_orcado': float(result.total_orcado) if result.total_orcado else 0.0,
                'total_realizado': float(result.total_realizado) if result.total_realizado else 0.0,
                'total_dif': float(result.total_dif) if result.total_dif else 0.0
            }
        
        dados_atual = get_dados_ano(ano_atual)
        dados_anterior = get_dados_ano(ano_anterior)
        
        # Calcular variações percentuais
        def calcular_variacao(atual, anterior):
            if anterior == 0:
                return 100.0 if atual > 0 else 0.0
            return ((atual - anterior) / abs(anterior)) * 100
        
        comparativo = {
            'periodo_atual': {
                'ano': ano_atual,
                'dados': dados_atual
            },
            'periodo_anterior': {
                'ano': ano_anterior,
                'dados': dados_anterior
            },
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
        # Filtros
        ano = request.args.get('ano', type=int)
        categoria = request.args.get('categoria')
        uf = request.args.get('uf')
        centro_custo = request.args.get('centro_custo')
        tipo = request.args.get('tipo', default='categoria')  # 'categoria', 'centro_custo', ou 'grupo' (obsoleto)
        
        # Query base para distribuição
        if tipo == 'categoria':
            query = db.session.query(
                ResumoOrcamento.categoria.label('nome'),
                func.sum(ResumoOrcamento.total_orcado).label('orcado'),
                func.sum(ResumoOrcamento.total_realizado).label('realizado'),
                func.sum(ResumoOrcamento.total_dif).label('dif')
            )
        elif tipo == 'centro_custo':
            query = db.session.query(
                ResumoOrcamento.master.label('nome'),
                func.sum(ResumoOrcamento.total_orcado).label('orcado'),
                func.sum(ResumoOrcamento.total_realizado).label('realizado'),
                func.sum(ResumoOrcamento.total_dif).label('dif')
            )
        else:  # tipo == 'grupo'
            query = db.session.query(
                ResumoOrcamento.grupo.label('nome'),
                func.sum(ResumoOrcamento.total_orcado).label('orcado'),
                func.sum(ResumoOrcamento.total_realizado).label('realizado'),
                func.sum(ResumoOrcamento.total_dif).label('dif')
            )
        
        # Aplicar filtros
        if ano:
            query = query.filter(ResumoOrcamento.ano == ano)
        if categoria:
            query = query.filter(ResumoOrcamento.categoria == categoria)
        if uf:
            query = query.filter(ResumoOrcamento.uf == uf)
        if centro_custo:
            query = query.filter(ResumoOrcamento.master == centro_custo)
        
        # Agrupar
        if tipo == 'categoria':
            query = query.group_by(ResumoOrcamento.categoria)
        elif tipo == 'centro_custo':
            query = query.group_by(ResumoOrcamento.master)
        else:
            query = query.group_by(ResumoOrcamento.grupo)
        
        resultados = query.all()
        
        # Formatar dados para gráfico de pizza
        dados_pizza = []
        for row in resultados:
            dados_pizza.append({
                'nome': row.nome,
                'orcado': float(row.orcado) if row.orcado else 0.0,
                'realizado': float(row.realizado) if row.realizado else 0.0,
                'dif': float(row.dif) if row.dif else 0.0,
                'percentual': 0.0  # Será calculado no frontend
            })
        
        # Calcular percentuais
        total_orcado = sum(item['orcado'] for item in dados_pizza)
        if total_orcado > 0:
            for item in dados_pizza:
                item['percentual'] = (item['orcado'] / total_orcado) * 100
        
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