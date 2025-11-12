from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import db, Usuario, Log
from datetime import datetime, timedelta

bp = Blueprint('logs', __name__)

@bp.route('/logs', methods=['GET'])
@jwt_required()
def list_logs():
    """Lista logs de auditoria (apenas admin)"""
    try:
        user_id = get_jwt_identity()
        current_user = Usuario.query.get(user_id)
        
        if current_user.papel != 'admin':
            return jsonify({'error': 'Acesso negado'}), 403
        
        # Paginação
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        
        # Filtros
        id_usuario = request.args.get('id_usuario', type=int)
        tabela_afetada = request.args.get('tabela_afetada')
        acao = request.args.get('acao')
        data_inicio = request.args.get('data_inicio')  # formato: YYYY-MM-DD
        data_fim = request.args.get('data_fim')  # formato: YYYY-MM-DD
        search = request.args.get('search')
        
        # Query base
        query = Log.query
        
        # Aplicar filtros
        if id_usuario:
            query = query.filter_by(id_usuario=id_usuario)
        
        if tabela_afetada:
            query = query.filter_by(tabela_afetada=tabela_afetada)
        
        if acao:
            query = query.filter(Log.acao.like(f'%{acao}%'))
        
        if data_inicio:
            try:
                dt_inicio = datetime.strptime(data_inicio, '%Y-%m-%d')
                query = query.filter(Log.timestamp >= dt_inicio)
            except ValueError:
                return jsonify({'error': 'Formato de data_inicio inválido. Use YYYY-MM-DD'}), 400
        
        if data_fim:
            try:
                dt_fim = datetime.strptime(data_fim, '%Y-%m-%d')
                # Incluir o dia inteiro (até 23:59:59)
                dt_fim = dt_fim + timedelta(days=1) - timedelta(seconds=1)
                query = query.filter(Log.timestamp <= dt_fim)
            except ValueError:
                return jsonify({'error': 'Formato de data_fim inválido. Use YYYY-MM-DD'}), 400
        
        if search:
            query = query.filter(
                db.or_(
                    Log.acao.like(f'%{search}%'),
                    Log.tabela_afetada.like(f'%{search}%')
                )
            )
        
        # Ordenar por mais recente
        query = query.order_by(Log.timestamp.desc())
        
        # Paginar
        pagination = query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        logs = pagination.items
        
        return jsonify({
            'logs': [log.to_dict() for log in logs],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': pagination.total,
                'pages': pagination.pages,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/logs/<int:id_log>', methods=['GET'])
@jwt_required()
def get_log(id_log):
    """Retorna um log específico (apenas admin)"""
    try:
        user_id = get_jwt_identity()
        current_user = Usuario.query.get(user_id)
        
        if current_user.papel != 'admin':
            return jsonify({'error': 'Acesso negado'}), 403
        
        log = Log.query.get(id_log)
        
        if not log:
            return jsonify({'error': 'Log não encontrado'}), 404
        
        return jsonify(log.to_dict()), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/logs/usuario/<int:id_usuario>', methods=['GET'])
@jwt_required()
def get_logs_usuario(id_usuario):
    """Retorna logs de um usuário específico (apenas admin)"""
    try:
        user_id = get_jwt_identity()
        current_user = Usuario.query.get(user_id)
        
        if current_user.papel != 'admin':
            return jsonify({'error': 'Acesso negado'}), 403
        
        # Verificar se usuário existe
        usuario = Usuario.query.get(id_usuario)
        if not usuario:
            return jsonify({'error': 'Usuário não encontrado'}), 404
        
        # Paginação
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        
        # Query
        query = Log.query.filter_by(id_usuario=id_usuario)\
                         .order_by(Log.timestamp.desc())
        
        # Paginar
        pagination = query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        return jsonify({
            'usuario': usuario.to_dict(),
            'logs': [log.to_dict() for log in pagination.items],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': pagination.total,
                'pages': pagination.pages
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/logs/tabela/<string:tabela>', methods=['GET'])
@jwt_required()
def get_logs_tabela(tabela):
    """Retorna logs de uma tabela específica (apenas admin)"""
    try:
        user_id = get_jwt_identity()
        current_user = Usuario.query.get(user_id)
        
        if current_user.papel != 'admin':
            return jsonify({'error': 'Acesso negado'}), 403
        
        # Validar nome da tabela
        tabelas_validas = ['usuarios', 'categorias', 'orcamentos', 'sistema']
        if tabela not in tabelas_validas:
            return jsonify({'error': 'Tabela inválida'}), 400
        
        # Paginação
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        
        # Query
        query = Log.query.filter_by(tabela_afetada=tabela)\
                         .order_by(Log.timestamp.desc())
        
        # Paginar
        pagination = query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        return jsonify({
            'tabela': tabela,
            'logs': [log.to_dict() for log in pagination.items],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': pagination.total,
                'pages': pagination.pages
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/logs/resumo', methods=['GET'])
@jwt_required()
def get_resumo_logs():
    """Retorna resumo estatístico dos logs (apenas admin)"""
    try:
        user_id = get_jwt_identity()
        current_user = Usuario.query.get(user_id)
        
        if current_user.papel != 'admin':
            return jsonify({'error': 'Acesso negado'}), 403
        
        # Total de logs
        total_logs = Log.query.count()
        
        # Logs por usuário (top 10)
        logs_por_usuario = db.session.query(
            Usuario.nome,
            db.func.count(Log.id_log).label('total')
        ).join(Log, Usuario.id_usuario == Log.id_usuario)\
         .group_by(Usuario.id_usuario)\
         .order_by(db.func.count(Log.id_log).desc())\
         .limit(10)\
         .all()
        
        # Logs por tabela
        logs_por_tabela = db.session.query(
            Log.tabela_afetada,
            db.func.count(Log.id_log).label('total')
        ).group_by(Log.tabela_afetada)\
         .order_by(db.func.count(Log.id_log).desc())\
         .all()
        
        # Logs por ação (top 10)
        logs_por_acao = db.session.query(
            Log.acao,
            db.func.count(Log.id_log).label('total')
        ).group_by(Log.acao)\
         .order_by(db.func.count(Log.id_log).desc())\
         .limit(10)\
         .all()
        
        # Logs por período (últimos 7 dias)
        sete_dias_atras = datetime.now() - timedelta(days=7)
        logs_ultimos_7_dias = db.session.query(
            db.func.date(Log.timestamp).label('data'),
            db.func.count(Log.id_log).label('total')
        ).filter(Log.timestamp >= sete_dias_atras)\
         .group_by(db.func.date(Log.timestamp))\
         .order_by(db.func.date(Log.timestamp))\
         .all()
        
        # Logs mais recentes
        logs_recentes = Log.query.order_by(Log.timestamp.desc()).limit(10).all()
        
        return jsonify({
            'total_logs': total_logs,
            'logs_por_usuario': [
                {'usuario': nome, 'total': total}
                for nome, total in logs_por_usuario
            ],
            'logs_por_tabela': [
                {'tabela': tabela or 'Sistema', 'total': total}
                for tabela, total in logs_por_tabela
            ],
            'logs_por_acao': [
                {'acao': acao, 'total': total}
                for acao, total in logs_por_acao
            ],
            'logs_ultimos_7_dias': [
                {'data': data.isoformat() if data else None, 'total': total}
                for data, total in logs_ultimos_7_dias
            ],
            'logs_recentes': [log.to_dict() for log in logs_recentes]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/logs/exportar', methods=['GET'])
@jwt_required()
def exportar_logs():
    """Exporta logs em formato CSV (apenas admin)"""
    try:
        user_id = get_jwt_identity()
        current_user = Usuario.query.get(user_id)
        
        if current_user.papel != 'admin':
            return jsonify({'error': 'Acesso negado'}), 403
        
        from flask import send_file
        import pandas as pd
        from io import BytesIO
        
        # Filtros (mesmos da listagem)
        id_usuario = request.args.get('id_usuario', type=int)
        tabela_afetada = request.args.get('tabela_afetada')
        data_inicio = request.args.get('data_inicio')
        data_fim = request.args.get('data_fim')
        
        # Query
        query = Log.query
        
        if id_usuario:
            query = query.filter_by(id_usuario=id_usuario)
        
        if tabela_afetada:
            query = query.filter_by(tabela_afetada=tabela_afetada)
        
        if data_inicio:
            dt_inicio = datetime.strptime(data_inicio, '%Y-%m-%d')
            query = query.filter(Log.timestamp >= dt_inicio)
        
        if data_fim:
            dt_fim = datetime.strptime(data_fim, '%Y-%m-%d')
            dt_fim = dt_fim + timedelta(days=1) - timedelta(seconds=1)
            query = query.filter(Log.timestamp <= dt_fim)
        
        logs = query.order_by(Log.timestamp.desc()).all()
        
        # Preparar dados
        dados = []
        for log in logs:
            dados.append({
                'ID': log.id_log,
                'Usuário': log.usuario.nome if log.usuario else 'Sistema',
                'Ação': log.acao,
                'Tabela': log.tabela_afetada or 'N/A',
                'ID Registro': log.id_registro or 'N/A',
                'Data/Hora': log.timestamp.strftime('%d/%m/%Y %H:%M:%S') if log.timestamp else '',
                'Detalhes': str(log.detalhes) if log.detalhes else ''
            })
        
        # Criar DataFrame
        df = pd.DataFrame(dados)
        
        # Criar arquivo CSV em memória
        output = BytesIO()
        df.to_csv(output, index=False, encoding='utf-8-sig')  # utf-8-sig para Excel
        output.seek(0)
        
        # Nome do arquivo
        filename = f'logs_auditoria_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        
        return send_file(
            output,
            mimetype='text/csv',
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/logs/search', methods=['POST'])
@jwt_required()
def search_logs():
    """Busca avançada em logs (apenas admin)"""
    try:
        user_id = get_jwt_identity()
        current_user = Usuario.query.get(user_id)
        
        if current_user.papel != 'admin':
            return jsonify({'error': 'Acesso negado'}), 403
        
        data = request.get_json()
        
        # Query base
        query = Log.query
        
        # Filtros avançados
        if 'usuarios' in data and data['usuarios']:
            query = query.filter(Log.id_usuario.in_(data['usuarios']))
        
        if 'tabelas' in data and data['tabelas']:
            query = query.filter(Log.tabela_afetada.in_(data['tabelas']))
        
        if 'acoes' in data and data['acoes']:
            # Busca parcial em ações
            acao_filters = [Log.acao.like(f'%{acao}%') for acao in data['acoes']]
            query = query.filter(db.or_(*acao_filters))
        
        if 'data_inicio' in data and data['data_inicio']:
            dt_inicio = datetime.strptime(data['data_inicio'], '%Y-%m-%d')
            query = query.filter(Log.timestamp >= dt_inicio)
        
        if 'data_fim' in data and data['data_fim']:
            dt_fim = datetime.strptime(data['data_fim'], '%Y-%m-%d')
            dt_fim = dt_fim + timedelta(days=1) - timedelta(seconds=1)
            query = query.filter(Log.timestamp <= dt_fim)
        
        if 'texto' in data and data['texto']:
            # Busca em ação ou detalhes
            texto = data['texto']
            query = query.filter(
                db.or_(
                    Log.acao.like(f'%{texto}%'),
                    Log.detalhes.cast(db.String).like(f'%{texto}%')
                )
            )
        
        # Paginação
        page = data.get('page', 1)
        per_page = data.get('per_page', 50)
        
        pagination = query.order_by(Log.timestamp.desc()).paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        return jsonify({
            'logs': [log.to_dict() for log in pagination.items],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': pagination.total,
                'pages': pagination.pages
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500