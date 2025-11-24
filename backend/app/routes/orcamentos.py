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
        ano = request.args.get('ano', type=int)
        mes = request.args.get('mes')
        status = request.args.get('status')
        uf = request.args.get('uf')
        master = request.args.get('master') # Centro de Custo
        id_categoria = request.args.get('id_categoria', type=int)
        categoria_filter = request.args.get('categoria')
        
        # Query com join para permitir filtros da tabela Categoria
        query = db.session.query(Orcamento).join(Categoria)
        
        if ano:
            query = query.filter(Orcamento.ano == ano)
        if mes:
            query = query.filter(Orcamento.mes == mes)
        if status:
            query = query.filter(Orcamento.status == status)
        
        # Filtros da tabela Categoria
        if uf:
            query = query.filter(Categoria.uf == uf)
        if master and master.strip():
            query = query.filter(Categoria.master == master)
        if id_categoria:
            query = query.filter(Orcamento.id_categoria == id_categoria)
        if categoria_filter and categoria_filter.strip():
            query = query.filter(Categoria.categoria == categoria_filter)
        
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
        
        if current_user.papel != 'admin':
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
            if orcamento.status == 'aprovado':
                return jsonify({'error': 'Orçamento aprovado não pode ser editado por ninguém.'}), 403
            
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


@bp.route('/orcamentos/batch_approve', methods=['POST'])
@jwt_required()
def batch_approve_orcamentos():
    """Aprova múltiplos orçamentos em lote (gestor/admin)"""
    try:
        user_id = get_jwt_identity()
        current_user = Usuario.query.get(user_id)

        if current_user.papel != 'gestor':
            return jsonify({'error': 'Acesso negado'}), 403

        data = request.get_json()
        if 'ids' not in data or not isinstance(data['ids'], list):
            return jsonify({'error': 'Lista de IDs de orçamentos inválida'}), 400

        orcamento_ids = data['ids']
        updated_count = 0
        errors = []

        for orc_id in orcamento_ids:
            orcamento = Orcamento.query.get(orc_id)
            if not orcamento:
                errors.append(f'Orçamento com ID {orc_id} não encontrado.')
                continue

            if orcamento.status == 'aprovado':
                # já aprovado, pular
                continue

            orcamento.status = 'aprovado'
            orcamento.aprovado_por = user_id
            orcamento.data_aprovacao = datetime.utcnow()
            orcamento.atualizado_por = user_id
            updated_count += 1

        db.session.commit()

        # Registrar no log
        log = Log(
            id_usuario=current_user.id_usuario,
            acao=f'Aprovação em lote: {updated_count} aprovados',
            tabela_afetada='orcamentos',
            id_registro=None,
            detalhes={'ids': orcamento_ids, 'atualizados': updated_count, 'erros': len(errors)}
        )
        db.session.add(log)
        db.session.commit()

        return jsonify({'message': f'{updated_count} orçamentos aprovados.', 'errors': errors}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@bp.route('/orcamentos/batch_reprove', methods=['POST'])
@jwt_required()
def batch_reprove_orcamentos():
    """Reprova (volta para rascunho) múltiplos orçamentos em lote (gestor/admin)"""
    try:
        user_id = get_jwt_identity()
        current_user = Usuario.query.get(user_id)

        if current_user.papel not in ['gestor', 'admin']:
            return jsonify({'error': 'Acesso negado'}), 403

        data = request.get_json()
        if 'ids' not in data or not isinstance(data['ids'], list):
            return jsonify({'error': 'Lista de IDs de orçamentos inválida'}), 400

        motivo = data.get('motivo', 'Sem motivo especificado')
        orcamento_ids = data['ids']
        updated_count = 0
        errors = []

        for orc_id in orcamento_ids:
            orcamento = Orcamento.query.get(orc_id)
            if not orcamento:
                errors.append(f'Orçamento com ID {orc_id} não encontrado.')
                continue

            orcamento.status = 'rascunho'
            orcamento.aprovado_por = None
            orcamento.data_aprovacao = None
            orcamento.atualizado_por = user_id
            updated_count += 1

        db.session.commit()

        # Registrar no log
        log = Log(
            id_usuario=current_user.id_usuario,
            acao=f'Reprovação em lote: {updated_count} reprovados',
            tabela_afetada='orcamentos',
            id_registro=None,
            detalhes={'ids': orcamento_ids, 'motivo': motivo, 'atualizados': updated_count, 'erros': len(errors)}
        )
        db.session.add(log)
        db.session.commit()

        return jsonify({'message': f'{updated_count} orçamentos reprovados.', 'errors': errors}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@bp.route('/orcamentos/filtros', methods=['GET'])
@jwt_required()
def get_orcamento_filtros():
    """Retorna valores únicos para os filtros da tela de lançamentos"""
    try:
        anos = db.session.query(Orcamento.ano).distinct().order_by(Orcamento.ano.desc()).all()
        status = db.session.query(Orcamento.status).distinct().order_by(Orcamento.status).all()
        
        # Filtros que vêm da tabela de Categoria
        ufs = db.session.query(Categoria.uf).distinct().order_by(Categoria.uf).all()
        masters = db.session.query(Categoria.master).distinct().order_by(Categoria.master).all()
        
        # Lista de categorias distintas para o novo filtro
        categorias_q = db.session.query(Categoria.categoria).distinct().order_by(Categoria.categoria).all()

        return jsonify({
            'anos': [a[0] for a in anos if a[0]],
            'status': [s[0] for s in status if s[0]],
            'ufs': [u[0] for u in ufs if u[0]],
            'masters': [m[0] for m in masters if m[0]],
            'categorias': [c[0] for c in categorias_q if c[0]]
        }), 200
    except Exception as e:
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
        processed_orcamentos = []
        
        for orc_data in data['orcamentos']:
            try:
                # Validar dados mínimos
                if 'id_categoria' not in orc_data or 'mes' not in orc_data or 'ano' not in orc_data:
                    errors.append(f'Dados incompletos: {orc_data}')
                    continue
                
                # Garante que o mês seja o nome, não o número
                mes_valor = orc_data['mes']
                if isinstance(mes_valor, int) and 1 <= mes_valor <= 12:
                    mes_nome = MESES[mes_valor - 1]
                else:
                    mes_nome = mes_valor


                # Buscar ou criar
                orcamento = Orcamento.query.filter_by(
                    id_categoria=orc_data['id_categoria'],
                    mes=mes_nome,
                    ano=orc_data['ano']
                ).first()
                
                if orcamento:
                    if orcamento.status == 'aprovado':
                        errors.append(f'Orçamento para categoria {orc_data["id_categoria"]} no mês {mes_nome} está aprovado e não pode ser editado.')
                        continue

                    orcamento.atualizado_por = user_id
                    updated += 1
                else:
                    orcamento = Orcamento(
                        id_categoria=orc_data['id_categoria'],
                        mes=mes_nome,
                        ano=orc_data['ano'],
                        criado_por=user_id,
                        status='rascunho' # Default status
                    )
                    db.session.add(orcamento)
                    created += 1
                
                if 'orcado' in orc_data:
                    orcamento.orcado = orc_data['orcado']
                if 'realizado' in orc_data:
                    orcamento.realizado = orc_data['realizado']
                if 'status' in orc_data and orc_data['status']:
                    orcamento.status = orc_data['status']
                
            except Exception as e:
                errors.append(f'Erro em {orc_data}: {str(e)}')
        
        db.session.flush() # Garante que os IDs sejam gerados para novos orçamentos
        for orc_data in data['orcamentos']:
            mes_nome = MESES[orc_data['mes'] - 1] if isinstance(orc_data['mes'], int) else orc_data['mes']
            orc = Orcamento.query.filter_by(id_categoria=orc_data['id_categoria'], mes=mes_nome, ano=orc_data['ano']).first()
            if orc:
                processed_orcamentos.append({'id_orcamento': orc.id_orcamento})
        
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
            'errors': errors,
            'orcamentos': processed_orcamentos
        }), 200 if not errors else 207
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@bp.route('/orcamentos/batch_submit', methods=['POST'])
@jwt_required()
def batch_submit_orcamentos():
    """Submete múltiplos orçamentos para aprovação."""
    try:
        user_id = get_jwt_identity()
        current_user = Usuario.query.get(user_id)

        if current_user.papel != 'admin':
            return jsonify({'error': 'Acesso negado'}), 403

        data = request.get_json()
        if 'ids' not in data or not isinstance(data['ids'], list):
            return jsonify({'error': 'Lista de IDs de orçamentos inválida'}), 400

        orcamento_ids = data['ids']
        updated_count = 0
        errors = []
        submitted_orcamentos = []

        for orc_id in orcamento_ids:
            orcamento = Orcamento.query.get(orc_id)
            if not orcamento:
                errors.append(f'Orçamento com ID {orc_id} não encontrado.')
                continue
            
            if orcamento.status == 'rascunho':
                orcamento.status = 'aguardando_aprovacao'
                orcamento.atualizado_por = user_id
                updated_count += 1
                # Coletar informações para o log
                categoria = Categoria.query.get(orcamento.id_categoria)
                if categoria:
                    submitted_orcamentos.append({
                        'id_orcamento': orcamento.id_orcamento,
                        'id_categoria': orcamento.id_categoria,
                        'categoria_nome': categoria.categoria,
                        'master': categoria.master,
                        'uf': categoria.uf,
                        'grupo': categoria.grupo,
                        'mes': orcamento.mes,
                        'ano': orcamento.ano
                    })

        db.session.commit()

        # Registrar submissão no log com detalhes para rastreamento pelo gestor
        if submitted_orcamentos:
            log = Log(
                id_usuario=current_user.id_usuario,
                acao=f'Submissão em lote: {updated_count} orçamentos enviados para aprovação',
                tabela_afetada='orcamentos',
                id_registro=None,
                detalhes={
                    'orcamentos_submetidos': submitted_orcamentos,
                    'total_submetidos': updated_count,
                    'erros': len(errors),
                    'timestamp': datetime.utcnow().isoformat()
                }
            )
            db.session.add(log)
            db.session.commit()

        return jsonify({
            'message': f'{updated_count} orçamentos enviados para aprovação.',
            'errors': errors
        }), 200
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


@bp.route('/orcamentos/submissions', methods=['GET'])
@jwt_required()
def get_submissions():
    """Retorna submissões de orçamentos para o gestor (logs com detalhes de submissões + orçamentos soltos em aguardando_aprovacao)"""
    try:
        user_id = get_jwt_identity()
        current_user = Usuario.query.get(user_id)

        if current_user.papel != 'gestor':
            return jsonify({'error': 'Acesso negado'}), 403

        # 1. Buscar logs de submissão em lote (ação contém 'Submissão em lote')
        logs = db.session.query(Log).filter(
            Log.acao.contains('Submissão em lote'),
            Log.tabela_afetada == 'orcamentos'
        ).order_by(Log.timestamp.desc()).all()

        resultado = []
        orcamento_ids_em_logs = set()
        
        for log in logs:
            # Extrair detalhes do log
            detalhes = log.detalhes or {}
            orcamentos_submetidos = detalhes.get('orcamentos_submetidos', [])
            
            # Coletar IDs dos orçamentos neste log
            for orc in orcamentos_submetidos:
                orcamento_ids_em_logs.add(orc.get('id_orcamento'))
            
            # Agrupar por master, uf, categoria para exibição
            submission = {
                'id_log': log.id_log,
                'data': log.timestamp.isoformat() if log.timestamp else None,
                'admin_usuario': log.usuario.nome if log.usuario else 'Desconhecido',
                'total_submetidos': detalhes.get('total_submetidos', 0),
                'orcamentos': orcamentos_submetidos,
                # Agrupar únicos para filtro rápido
                'masters': list(set([o.get('master') for o in orcamentos_submetidos if o.get('master')])),
                'ufs': list(set([o.get('uf') for o in orcamentos_submetidos if o.get('uf')])),
                'categorias': list(set([o.get('categoria_nome') for o in orcamentos_submetidos if o.get('categoria_nome')])),
            }
            resultado.append(submission)
        
        # 2. Buscar orçamentos em 'aguardando_aprovacao' que não estão em nenhum log (foram adicionados manualmente)
        orcamentos_soltos = Orcamento.query.filter(
            Orcamento.status == 'aguardando_aprovacao'
        ).all()
        
        # Criar uma "submissão virtual" para os orçamentos sem log
        orcamentos_sem_log = []
        for orc in orcamentos_soltos:
            if orc.id_orcamento not in orcamento_ids_em_logs:
                categoria = Categoria.query.get(orc.id_categoria)
                if categoria:
                    orcamentos_sem_log.append({
                        'id_orcamento': orc.id_orcamento,
                        'id_categoria': orc.id_categoria,
                        'categoria_nome': categoria.categoria,
                        'master': categoria.master,
                        'uf': categoria.uf,
                        'grupo': categoria.grupo,
                        'mes': orc.mes,
                        'ano': orc.ano
                    })
        
        # Se houver orçamentos sem log, criar uma submissão virtual
        if orcamentos_sem_log:
            virtual_submission = {
                'id_log': None,  # Sem log real
                'data': None,
                'admin_usuario': 'Importado',
                'total_submetidos': len(orcamentos_sem_log),
                'orcamentos': orcamentos_sem_log,
                'masters': list(set([o.get('master') for o in orcamentos_sem_log if o.get('master')])),
                'ufs': list(set([o.get('uf') for o in orcamentos_sem_log if o.get('uf')])),
                'categorias': list(set([o.get('categoria_nome') for o in orcamentos_sem_log if o.get('categoria_nome')])),
            }
            resultado.insert(0, virtual_submission)  # Adicionar no início

        return jsonify(resultado), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500