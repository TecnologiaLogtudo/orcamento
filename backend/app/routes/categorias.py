from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import db, Usuario, Categoria, Log
from sqlalchemy import or_
import pandas as pd

bp = Blueprint('categorias', __name__)

@bp.route('/categorias', methods=['GET'])
@jwt_required()
def list_categorias():
    """Lista categorias com filtros opcionais"""
    try:
        # Filtros
        categoria = request.args.get('categoria')
        uf = request.args.get('uf')
        grupo = request.args.get('grupo')
        search = request.args.get('search')
        
        query = Categoria.query
        
        if categoria:
            query = query.filter_by(categoria=categoria)
        if uf:
            query = query.filter_by(uf=uf)
        if grupo:
            query = query.filter_by(grupo=grupo)
        if search:
            query = query.filter(
                or_(
                    Categoria.categoria.like(f'%{search}%'),
                    Categoria.grupo.like(f'%{search}%'),
                    Categoria.classe_custo.like(f'%{search}%')
                )
            )
        
        categorias = query.order_by(Categoria.categoria, Categoria.grupo).all()
        
        return jsonify([c.to_dict() for c in categorias]), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/categorias/<int:id_categoria>', methods=['GET'])
@jwt_required()
def get_categoria(id_categoria):
    """Retorna uma categoria específica"""
    try:
        categoria = Categoria.query.get(id_categoria)
        
        if not categoria:
            return jsonify({'error': 'Categoria não encontrada'}), 404
        
        return jsonify(categoria.to_dict()), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/categorias', methods=['POST'])
@jwt_required()
def create_categoria():
    """Cria nova categoria (apenas admin)"""
    try:
        user_id = get_jwt_identity()
        current_user = Usuario.query.get(user_id)
        
        if current_user.papel != 'admin':
            return jsonify({'error': 'Acesso negado'}), 403
        
        data = request.get_json()
        
        # Validações
        required_fields = ['categoria']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Campo {field} é obrigatório'}), 400
        
        # Verificar duplicidade
        existing = Categoria.query.filter_by(
            categoria=data['categoria'],
            grupo=data.get('grupo'),
            cod_class=data.get('cod_class')
        ).first()
        
        if existing:
            return jsonify({'error': 'Categoria já existe'}), 400
        
        # Criar categoria
        categoria = Categoria(
            categoria=data['categoria'],
            uf=data.get('uf'),
            master=data.get('master'),
            grupo=data.get('grupo'),
            cod_class=data.get('cod_class'),
            classe_custo=data.get('classe_custo')
        )
        
        db.session.add(categoria)
        db.session.commit()
        
        # Registrar no log
        log = Log(
            id_usuario=current_user.id_usuario,
            acao=f'Criou categoria {categoria.grupo}',
            tabela_afetada='categorias',
            id_registro=categoria.id_categoria,
            detalhes={'categoria': categoria.to_dict()}
        )
        db.session.add(log)
        db.session.commit()
        
        return jsonify(categoria.to_dict()), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@bp.route('/categorias/<int:id_categoria>', methods=['PUT'])
@jwt_required()
def update_categoria(id_categoria):
    """Atualiza categoria (apenas admin)"""
    try:
        user_id = get_jwt_identity()
        current_user = Usuario.query.get(user_id)
        
        if current_user.papel != 'admin':
            return jsonify({'error': 'Acesso negado'}), 403
        
        categoria = Categoria.query.get(id_categoria)
        if not categoria:
            return jsonify({'error': 'Categoria não encontrada'}), 404
        
        data = request.get_json()
        dados_antigos = categoria.to_dict()
        
        # Atualizar campos
        if 'categoria' in data:
            categoria.categoria = data['categoria']
        if 'uf' in data:
            categoria.uf = data['uf']
        if 'master' in data:
            categoria.master = data['master']
        if 'grupo' in data:
            categoria.grupo = data['grupo']
        if 'cod_class' in data:
            categoria.cod_class = data['cod_class']
        if 'classe_custo' in data:
            categoria.classe_custo = data['classe_custo']
        
        db.session.commit()
        
        # Registrar no log
        log = Log(
            id_usuario=current_user.id_usuario,
            acao=f'Atualizou categoria {categoria.grupo}',
            tabela_afetada='categorias',
            id_registro=categoria.id_categoria,
            detalhes={
                'antes': dados_antigos,
                'depois': categoria.to_dict()
            }
        )
        db.session.add(log)
        db.session.commit()
        
        return jsonify(categoria.to_dict()), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@bp.route('/categorias/<int:id_categoria>', methods=['DELETE'])
@jwt_required()
def delete_categoria(id_categoria):
    """Deleta categoria (apenas admin)"""
    try:
        user_id = get_jwt_identity()
        current_user = Usuario.query.get(user_id)
        
        if current_user.papel != 'admin':
            return jsonify({'error': 'Acesso negado'}), 403
        
        categoria = Categoria.query.get(id_categoria)
        if not categoria:
            return jsonify({'error': 'Categoria não encontrada'}), 404
        
        # Verificar se tem orçamentos vinculados
        if categoria.orcamentos.count() > 0:
            return jsonify({
                'error': 'Não é possível deletar categoria com orçamentos vinculados'
            }), 400
        
        categoria_data = categoria.to_dict()
        
        db.session.delete(categoria)
        db.session.commit()
        
        # Registrar no log
        log = Log(
            id_usuario=current_user.id_usuario,
            acao=f'Deletou categoria {categoria_data["grupo"]}',
            tabela_afetada='categorias',
            id_registro=id_categoria,
            detalhes={'categoria_deletada': categoria_data}
        )
        db.session.add(log)
        db.session.commit()
        
        return jsonify({'message': 'Categoria deletada com sucesso'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@bp.route('/categorias/import', methods=['POST'])
@jwt_required()
def import_categorias():
    """Importa categorias de arquivo Excel (apenas admin)"""
    try:
        user_id = get_jwt_identity()
        current_user = Usuario.query.get(user_id)
        
        if current_user.papel != 'admin':
            return jsonify({'error': 'Acesso negado'}), 403
        
        if 'file' not in request.files:
            return jsonify({'error': 'Nenhum arquivo enviado'}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'error': 'Nenhum arquivo selecionado'}), 400
        
        if not file.filename.endswith(('.xlsx', '.xls')):
            return jsonify({'error': 'Formato de arquivo inválido. Use Excel (.xlsx ou .xls)'}), 400
        
        # Ler Excel
        df = pd.read_excel(file)
        
        # Validar colunas obrigatórias
        required_columns = ['categoria']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            return jsonify({
                'error': f'Colunas obrigatórias ausentes: {", ".join(missing_columns)}'
            }), 400
        
        # Processar cada linha
        imported = 0
        errors = []
        
        for index, row in df.iterrows():
            try:
                # Verificar se já existe
                existing = Categoria.query.filter_by(
                    categoria=row['categoria'],
                    grupo=row.get('grupo'),
                    cod_class=row.get('cod_class')
                ).first()
                
                if existing:
                    errors.append(f'Linha {index + 2}: Categoria já existe')
                    continue
                
                categoria = Categoria(
                    categoria=row['categoria'],
                    uf=row.get('uf'),
                    master=row.get('master'),
                    grupo=row.get('grupo'),
                    cod_class=row.get('cod_class'),
                    classe_custo=row.get('classe_custo')
                )
                
                db.session.add(categoria)
                imported += 1
                
            except Exception as e:
                errors.append(f'Linha {index + 2}: {str(e)}')
        
        db.session.commit()
        
        # Registrar no log
        log = Log(
            id_usuario=current_user.id_usuario,
            acao=f'Importou {imported} categorias',
            tabela_afetada='categorias',
            id_registro=None,
            detalhes={
                'importadas': imported,
                'erros': len(errors),
                'arquivo': file.filename
            }
        )
        db.session.add(log)
        db.session.commit()
        
        return jsonify({
            'message': f'{imported} categorias importadas com sucesso',
            'imported': imported,
            'errors': errors
        }), 200 if not errors else 207
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@bp.route('/categorias/filtros', methods=['GET'])
@jwt_required()
def get_filtros():
    """Retorna valores únicos para filtros"""
    try:
        categorias = db.session.query(Categoria.categoria).distinct().order_by(Categoria.categoria).all()
        ufs = db.session.query(Categoria.uf).distinct().order_by(Categoria.uf).all()
        grupos = db.session.query(Categoria.grupo).distinct().order_by(Categoria.grupo).all()
        
        return jsonify({
            'categorias': [c[0] for c in categorias if c[0]],
            'ufs': [u[0] for u in ufs if u[0]],
            'grupos': [g[0] for g in grupos if g[0]]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500