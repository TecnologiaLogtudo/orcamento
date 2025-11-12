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
        dono = request.args.get('dono')
        tipo_despesa = request.args.get('tipo_despesa')
        uf = request.args.get('uf')
        grupo = request.args.get('grupo')
        search = request.args.get('search')
        
        query = Categoria.query
        
        if dono:
            query = query.filter_by(dono=dono)
        if tipo_despesa:
            query = query.filter_by(tipo_despesa=tipo_despesa)
        if uf:
            query = query.filter_by(uf=uf)
        if grupo:
            query = query.filter_by(grupo=grupo)
        if search:
            query = query.filter(
                or_(
                    Categoria.dono.like(f'%{search}%'),
                    Categoria.grupo.like(f'%{search}%'),
                    Categoria.classe_custo.like(f'%{search}%')
                )
            )
        
        categorias = query.order_by(Categoria.dono, Categoria.grupo).all()
        
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
        required_fields = ['dono', 'tipo_despesa']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Campo {field} é obrigatório'}), 400
        
        # Verificar duplicidade
        existing = Categoria.query.filter_by(
            dono=data['dono'],
            grupo=data.get('grupo'),
            cod_class=data.get('cod_class'),
            tipo_despesa=data['tipo_despesa']
        ).first()
        
        if existing:
            return jsonify({'error': 'Categoria já existe'}), 400
        
        # Criar categoria
        categoria = Categoria(
            dono=data['dono'],
            tipo_despesa=data['tipo_despesa'],
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
        if 'dono' in data:
            categoria.dono = data['dono']
        if 'tipo_despesa' in data:
            categoria.tipo_despesa = data['tipo_despesa']
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
        required_columns = ['dono', 'tipo_despesa']
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
                    dono=row['dono'],
                    grupo=row.get('grupo'),
                    cod_class=row.get('cod_class'),
                    tipo_despesa=row['tipo_despesa']
                ).first()
                
                if existing:
                    errors.append(f'Linha {index + 2}: Categoria já existe')
                    continue
                
                categoria = Categoria(
                    dono=row['dono'],
                    tipo_despesa=row['tipo_despesa'],
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
        donos = db.session.query(Categoria.dono).distinct().order_by(Categoria.dono).all()
        tipos = db.session.query(Categoria.tipo_despesa).distinct().order_by(Categoria.tipo_despesa).all()
        ufs = db.session.query(Categoria.uf).distinct().order_by(Categoria.uf).all()
        grupos = db.session.query(Categoria.grupo).distinct().order_by(Categoria.grupo).all()
        
        return jsonify({
            'donos': [d[0] for d in donos if d[0]],
            'tipos_despesa': [t[0] for t in tipos if t[0]],
            'ufs': [u[0] for u in ufs if u[0]],
            'grupos': [g[0] for g in grupos if g[0]]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500