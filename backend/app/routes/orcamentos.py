from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import db, Usuario, Categoria, Orcamento, Log
from datetime import datetime

bp = Blueprint('orcamentos', __name__)

MESES = ['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
         'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro']

@bp.route('/orcamentos', methods=['GET'])
@jwt_required()
def list_orcamentos():
    """Lista orçamentos com filtros"""
    try:
        # Filtros
        id_categoria = request.args.get('id_categoria', type=int)
        ano = request.args.get('ano', type=int)
        mes = request.args.get('mes')
        status = request.args.get('status')
        
        query = Orcamento.query
        
        if id_categoria:
            query = query.filter_by(id_categoria=id_categoria)
        if ano:
            query = query.filter_by(ano=ano)
        if mes:
            query = query.filter_by(mes=mes)
        if status:
            query = query.filter_by(status=status)
        
        orcamentos = query.order_by(Orcamento.ano.desc(), 
                                    Orcamento.mes).all()
        
        return jsonify([o.to_dict(include_categoria=True) for o in orcamentos]), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/orcamentos/categoria/<int:id_categoria>/ano/<int:ano>', methods=['GET'])
@jwt_required()
def get_orcamentos_categoria_ano(id_categoria, ano):
    """Retorna todos os meses de uma categoria/ano"""
    try:
        categoria = Categoria.query.get(id_categoria)
        if not categoria:
            return jsonify({'error': 'Categoria não encontrada'}), 404
        
        # Buscar orçamentos existentes
        orcamentos_existentes = Orcamento.query.filter_by(
            id_categoria=id_categoria,
            ano=ano
        ).all()
        
        # Criar dicionário indexado por mês
        orcamentos_dict = {o.mes: o for o in orcamentos_existentes}
        
        # Criar lista completa com todos os meses
        resultado = []
        for mes in MESES:
            if mes in orcamentos_dict:
                resultado.append(orcamentos_dict[mes].to_dict())
            else:
                resultado.append({
                    'id_orcamento': None,
                    'id_categoria': id_categoria,
                    'mes': mes,
                    'ano': ano,
                    'orcado': 0.0,
                    'realizado': 0.0,
                    'dif': 0.0,
                    'status': 'rascunho'
                })
        
        return jsonify({
            'categoria': categoria.to_dict(),
            'orcamentos': resultado
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/orcamentos', methods=['POST'])
@jwt_required()
def create_or_update_orcamento():
    """Cria ou atualiza orçamento (admin)"""
    try:
        user_id = get_jwt_identity()
        current_user = Usuario.query.get(user_id)
        
        if current_user.papel not in ['admin', 'gestor']:
            return jsonify({'error': 'Acesso negado'}), 403
        
        data = request.get_json()
        
        # Validações
        required_fields = ['id_categoria', 'mes', 'ano']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Campo {field} é obrigatório'}), 400
        
        if data['mes'] not in MESES:
            return jsonify({'error': 'Mês inválido'}), 400
        
        # Verificar se categoria existe
        categoria = Categoria.query.get(data['id_categoria'])
        if not categoria:
            return jsonify({'error': 'Categoria não encontrada'}), 404
        
        # Buscar orçamento existente
        orcamento = Orcamento.query.filter_by(
            id_categoria=data['id_categoria'],
            mes=data['mes'],
            ano=data['ano']
        ).first()
        
        is_new = orcamento is None
        
        if is_new:
            # Criar novo
            orcamento = Orcamento(
                id_categoria=data['id_categoria'],
                mes=data['mes'],
                ano=data['ano'],
                criado_por=user_id
            )
            acao = 'Criou orçamento'
        else:
            # Verificar se pode editar (não pode editar se aprovado)
            if orcamento.status == 'aprovado' and current_user.papel != 'admin':
                return jsonify({'error': 'Orçamento aprovado não pode ser editado'}), 403
            
            acao = 'Atualizou orçamento'
            orcamento.atualizado_por = user_id
        
        # Atualizar valores
        if 'orcado' in data:
            orcamento.orcado = data['orcado']
        if 'realizado' in data:
            orcamento.realizado = data['realizado']
        if 'status' in data and data['status'] in ['rascunho', 'aguardando_aprovacao', 'aprovado']:
            orcamento.status = data['status']
        
        if is_new:
            db.session.add(orcamento)
        
        db.session.commit()
        
        # Registrar no log
        log = Log(
            id_usuario=current_user.id_usuario,
            acao=f'{acao} {data["mes"]}/{data["ano"]}',
            tabela_afetada='orcamentos',
            id_registro=orcamento.id_orcamento,
            detalhes={
                'categoria': categoria.grupo,
                'mes': data['mes'],
                'ano': data['ano'],
                'orcado': float(orcamento.orcado) if orcamento.orcado else 0.0,
                'realizado': float(orcamento.realizado) if orcamento.realizado else 0.0
            }
        )
        db.session.add(log)
        db.session.commit()
        
        return jsonify(orcamento.to_dict(include_categoria=True)), 201 if is_new else 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@bp.route('/orcamentos/batch', methods=['POST'])
@jwt_required()
def batch_update_orcamentos():
    """Atualiza múltiplos orçamentos de uma vez"""
    try:
        user_id = get_jwt_identity()
        current_user = Usuario.query.get(user_id)
        
        if current_user.papel != 'admin':
            return jsonify({'error': 'Acesso negado'}), 403
        
        data = request.get_json()
        
        if 'orcamentos' not in data or not isinstance(data['orcamentos'], list):
            return jsonify({'error': 'Lista de orçamentos inválida'}), 400
        
        updated = 0
        created = 0
        errors = []
        
        for orc_data in data['orcamentos']:
            try:
                # Validar dados mínimos
                if 'id_categoria' not in orc_data or 'mes' not in orc_data or 'ano' not in orc_data:
                    errors.append(f'Dados incompletos: {orc_data}')
                    continue
                
                # Buscar ou criar
                orcamento = Orcamento.query.filter_by(
                    id_categoria=orc_data['id_categoria'],
                    mes=orc_data['mes'],
                    ano=orc_data['ano']
                ).first()
                
                if orcamento:
                    orcamento.atualizado_por = user_id
                    updated += 1
                else:
                    orcamento = Orcamento(
                        id_categoria=orc_data['id_categoria'],
                        mes=orc_data['mes'],
                        ano=orc_data['ano'],
                        criado_por=user_id
                    )
                    db.session.add(orcamento)
                    created += 1
                
                if 'orcado' in orc_data:
                    orcamento.orcado = orc_data['orcado']
                if 'realizado' in orc_data:
                    orcamento.realizado = orc_data['realizado']
                if 'status' in orc_data:
                    orcamento.status = orc_data['status']
                
            except Exception as e:
                errors.append(f'Erro em {orc_data}: {str(e)}')
        
        db.session.commit()
        
        # Registrar no log
        log = Log(
            id_usuario=current_user.id_usuario,
            acao=f'Atualização em lote: {created} criados, {updated} atualizados',
            tabela_afetada='orcamentos',
            id_registro=None,
            detalhes={
                'criados': created,
                'atualizados': updated,
                'erros': len(errors)
            }
        )
        db.session.add(log)
        db.session.commit()
        
        return jsonify({
            'message': 'Atualização concluída',
            'created': created,
            'updated': updated,
            'errors': errors
        }), 200 if not errors else 207
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@bp.route('/orcamentos/<int:id_orcamento>/aprovar', methods=['POST'])
@jwt_required()
def aprovar_orcamento(id_orcamento):
    """Aprova um orçamento (apenas gestor ou admin)"""
    try:
        user_id = get_jwt_identity()
        current_user = Usuario.query.get(user_id)
        
        if current_user.papel != 'gestor':
            return jsonify({'error': 'Acesso negado'}), 403
        
        orcamento = Orcamento.query.get(id_orcamento)
        if not orcamento:
            return jsonify({'error': 'Orçamento não encontrado'}), 404
        
        if orcamento.status == 'aprovado':
            return jsonify({'error': 'Orçamento já está aprovado'}), 400
        
        orcamento.status = 'aprovado'
        orcamento.aprovado_por = user_id
        orcamento.data_aprovacao = datetime.utcnow()
        
        db.session.commit()
        
        # Registrar no log
        log = Log(
            id_usuario=current_user.id_usuario,
            acao=f'Aprovou orçamento {orcamento.mes}/{orcamento.ano}',
            tabela_afetada='orcamentos',
            id_registro=orcamento.id_orcamento,
            detalhes={'orcamento': orcamento.to_dict()}
        )
        db.session.add(log)
        db.session.commit()
        
        return jsonify(orcamento.to_dict(include_categoria=True)), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@bp.route('/orcamentos/<int:id_orcamento>/reprovar', methods=['POST'])
@jwt_required()
def reprovar_orcamento(id_orcamento):
    """Reprova um orçamento (apenas gestor ou admin)"""
    try:
        user_id = get_jwt_identity()
        current_user = Usuario.query.get(user_id)
        
        if current_user.papel not in ['gestor', 'admin']:
            return jsonify({'error': 'Acesso negado'}), 403
        
        orcamento = Orcamento.query.get(id_orcamento)
        if not orcamento:
            return jsonify({'error': 'Orçamento não encontrado'}), 404
        
        data = request.get_json()
        motivo = data.get('motivo', 'Sem motivo especificado')
        
        orcamento.status = 'rascunho'
        orcamento.aprovado_por = None
        orcamento.data_aprovacao = None
        
        db.session.commit()
        
        # Registrar no log
        log = Log(
            id_usuario=current_user.id_usuario,
            acao=f'Reprovou orçamento {orcamento.mes}/{orcamento.ano}',
            tabela_afetada='orcamentos',
            id_registro=orcamento.id_orcamento,
            detalhes={
                'orcamento': orcamento.to_dict(),
                'motivo': motivo
            }
        )
        db.session.add(log)
        db.session.commit()
        
        return jsonify(orcamento.to_dict(include_categoria=True)), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@bp.route('/orcamentos/<int:id_orcamento>', methods=['DELETE'])
@jwt_required()
def delete_orcamento(id_orcamento):
    """Deleta orçamento (apenas admin)"""
    try:
        user_id = get_jwt_identity()
        current_user = Usuario.query.get(user_id)
        
        if current_user.papel != 'admin':
            return jsonify({'error': 'Acesso negado'}), 403
        
        orcamento = Orcamento.query.get(id_orcamento)
        if not orcamento:
            return jsonify({'error': 'Orçamento não encontrado'}), 404
        
        orcamento_data = orcamento.to_dict(include_categoria=True)
        
        db.session.delete(orcamento)
        db.session.commit()
        
        # Registrar no log
        log = Log(
            id_usuario=current_user.id_usuario,
            acao=f'Deletou orçamento {orcamento_data["mes"]}/{orcamento_data["ano"]}',
            tabela_afetada='orcamentos',
            id_registro=id_orcamento,
            detalhes={'orcamento_deletado': orcamento_data}
        )
        db.session.add(log)
        db.session.commit()
        
        return jsonify({'message': 'Orçamento deletado com sucesso'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500