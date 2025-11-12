#app/routes/dashboard.py
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from app.models import db, ResumoOrcamento, Orcamento, Categoria
from sqlalchemy import func, and_

bp = Blueprint('dashboard', __name__)

@bp.route('/dashboard', methods=['GET'])
@jwt_required()
def get_dashboard():
    """Retorna dados consolidados do dashboard"""
    try:
        # Filtros
        ano = request.args.get('ano', type=int)
        categoria = request.args.get('categoria')
        uf = request.args.get('uf')
        grupo = request.args.get('grupo')
        
        # Query base
        query = db.session.query(
            func.sum(ResumoOrcamento.total_orcado).label('total_orcado'),
            func.sum(ResumoOrcamento.total_realizado).label('total_realizado'),
            func.sum(ResumoOrcamento.total_dif).label('total_dif')
        )
        
        # Aplicar filtros
        if ano:
            query = query.filter(ResumoOrcamento.ano == ano)
        if categoria:
            query = query.filter(ResumoOrcamento.categoria == categoria)
        if uf:
            query = query.filter(ResumoOrcamento.uf == uf)
        if grupo:
            query = query.filter(ResumoOrcamento.grupo == grupo)
        
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
        
        # Dados por mês
        query_mensal = db.session.query(
            ResumoOrcamento.mes,
            func.sum(ResumoOrcamento.total_orcado).label('orcado'),
            func.sum(ResumoOrcamento.total_realizado).label('realizado'),
            func.sum(ResumoOrcamento.total_dif).label('dif')
        )
        
        # Aplicar mesmos filtros
        if ano:
            query_mensal = query_mensal.filter(ResumoOrcamento.ano == ano)
        if categoria:
            query_mensal = query_mensal.filter(ResumoOrcamento.categoria == categoria)
        if uf:
            query_mensal = query_mensal.filter(ResumoOrcamento.uf == uf)
        if grupo:
            query_mensal = query_mensal.filter(ResumoOrcamento.grupo == grupo)
        
        dados_mensais = query_mensal.group_by(ResumoOrcamento.mes).all()
        
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
        
        # Mês mais crítico (maior desvio)
        mes_critico = None
        maior_desvio = 0
        
        for item in dados_por_mes:
            if abs(item['dif']) > abs(maior_desvio):
                maior_desvio = item['dif']
                mes_critico = {
                    'mes': item['mes'],
                    'desvio': item['dif']
                }
        
        # Top 5 grupos por desvio
        query_grupos = db.session.query(
            ResumoOrcamento.grupo,
            func.sum(ResumoOrcamento.total_dif).label('dif_total')
        )
        
        if ano:
            query_grupos = query_grupos.filter(ResumoOrcamento.ano == ano)
        if categoria:
            query_grupos = query_grupos.filter(ResumoOrcamento.categoria == categoria)
        if uf:
            query_grupos = query_grupos.filter(ResumoOrcamento.uf == uf)
        
        top_grupos = query_grupos.group_by(ResumoOrcamento.grupo)\
                                 .order_by(func.abs(func.sum(ResumoOrcamento.total_dif)).desc())\
                                 .limit(5)\
                                 .all()
        
        grupos_criticos = [
            {
                'grupo': g.grupo,
                'desvio': float(g.dif_total) if g.dif_total else 0.0
            }
            for g in top_grupos
        ]
        
        # Dados por centro de custo (categoria)
        query_centros_custo = db.session.query(
            ResumoOrcamento.categoria,
            func.sum(ResumoOrcamento.total_orcado).label('orcado'),
            func.sum(ResumoOrcamento.total_realizado).label('realizado'),
            func.sum(ResumoOrcamento.total_dif).label('dif')
        )
        
        if ano:
            query_centros_custo = query_centros_custo.filter(ResumoOrcamento.ano == ano)
        if uf:
            query_centros_custo = query_centros_custo.filter(ResumoOrcamento.uf == uf)
        if grupo:
            query_centros_custo = query_centros_custo.filter(ResumoOrcamento.grupo == grupo)
        
        dados_por_categoria = query_centros_custo.group_by(ResumoOrcamento.categoria).all()
        
        centros_custo = [
            {
                'categoria': d.categoria,
                'orcado': float(d.orcado) if d.orcado else 0.0,
                'realizado': float(d.realizado) if d.realizado else 0.0,
                'dif': float(d.dif) if d.dif else 0.0
            }
            for d in dados_por_categoria
        ]
        
        return jsonify({
            'totais': totais,
            'dados_mensais': dados_por_mes,
            'mes_critico': mes_critico,
            'grupos_criticos': grupos_criticos,
            'centros_custo': centros_custo
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