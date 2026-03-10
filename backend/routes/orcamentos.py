from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, Usuario, Categoria, Orcamento, Log
from datetime import datetime

import pandas as pd
import re
import json
from difflib import SequenceMatcher
from decimal import Decimal, InvalidOperation

bp = Blueprint('orcamentos', __name__)

MESES = ['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
         'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro']

MONTH_MAP = {
    'jan': 'Janeiro', 'janeiro': 'Janeiro',
    'fev': 'Fevereiro', 'fevereiro': 'Fevereiro',
    'mar': 'Março', 'março': 'Março',
    'abr': 'Abril', 'abril': 'Abril',
    'mai': 'Maio', 'maio': 'Maio',
    'jun': 'Junho', 'junho': 'Junho',
    'jul': 'Julho', 'julho': 'Julho',
    'ago': 'Agosto', 'agosto': 'Agosto',
    'set': 'Setembro', 'setembro': 'Setembro',
    'out': 'Outubro', 'outubro': 'Outubro',
    'nov': 'Novembro', 'novembro': 'Novembro',
    'dez': 'Dezembro', 'dezembro': 'Dezembro'
}

def build_category_key(master, grupo, uf):
    """Cria uma chave única para combinações de Centro de Custo / Grupo / UF."""
    return f"{(master or '').strip()}|{(grupo or '').strip()}|{(uf or '').strip()}"

def compute_similarity(a, b):
    return SequenceMatcher(None, (a or '').lower(), (b or '').lower()).ratio()

def find_best_category_suggestion(master, grupo, uf, categorias):
    if not categorias:
        return None

    best = None
    best_score = 0.0
    base_master = (master or '').strip()
    base_grupo = (grupo or '').strip()
    base_uf = (uf or '').strip().lower()

    for categoria in categorias:
        master_score = compute_similarity(base_master, categoria.master)
        grupo_score = compute_similarity(base_grupo, categoria.grupo)
        uf_score = 1.0 if categoria.uf and categoria.uf.strip().lower() == base_uf and base_uf else 0.0
        total_score = (master_score + grupo_score + uf_score) / 3.0
        if total_score > best_score:
            best_score = total_score
            best = categoria

    if best and best_score >= 0.45:
        return {
            'id_categoria': best.id_categoria,
            'categoria': best.categoria,
            'master': best.master,
            'grupo': best.grupo,
            'uf': best.uf,
            'score': round(best_score, 3)
        }

    return None

def to_decimal(value):
    if value is None:
        return Decimal('0')
    if isinstance(value, Decimal):
        return value
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        return Decimal('0')


def normalize_months(mes_str):
    """Converte strings de meses (jan, fev, janeiro/fevereiro) em lista de nomes de meses válidos"""
    if pd.isna(mes_str):
        return []
    
    # Substituir delimitadores comuns por espaços
    normalized = re.sub(r'[,/;]', ' ', str(mes_str).lower())
    parts = normalized.split()
    
    result = []
    for part in parts:
        # Remover pontos (ex: jan.)
        clean_part = part.strip('.')
        if clean_part in MONTH_MAP:
            result.append(MONTH_MAP[clean_part])
    
    return list(set(result)) # Remover duplicatas

@bp.route('/orcamentos/import', methods=['POST'])
@jwt_required()
def import_orcamentos():
    """Importa orçamentos de arquivo Excel"""
    try:
        user_id = get_jwt_identity()
        current_user = Usuario.query.get(user_id)
        
        if current_user.papel != 'admin':
            return jsonify({'error': 'Acesso negado'}), 403
            
        if 'file' not in request.files:
            return jsonify({'error': 'Nenhum arquivo enviado'}), 400
            
        file = request.files['file']
        create_missing = request.form.get('create_missing') == 'true'
        skip_missing = request.form.get('skip_missing') == 'true'
        missing_actions_payload = request.form.get('missing_actions')
        missing_actions = {}
        if missing_actions_payload:
            try:
                parsed_actions = json.loads(missing_actions_payload)
                if isinstance(parsed_actions, dict):
                    for key, value in parsed_actions.items():
                        raw_value = str(value or '').strip()
                        if raw_value.startswith('use_suggestion:'):
                            missing_actions[key] = raw_value
                        else:
                            normalized = raw_value.lower()
                            if normalized not in ['create', 'skip']:
                                normalized = 'skip'
                            missing_actions[key] = normalized
            except (json.JSONDecodeError, TypeError):
                missing_actions = {}
        
        if file.filename == '':
            return jsonify({'error': 'Nenhum arquivo selecionado'}), 400
            
        df = pd.read_excel(file)
        
        # Mapeamento de colunas (case-insensitive e flexível)
        col_map = {col.lower(): col for col in df.columns}
        
        def get_col(names):
            for name in names:
                if name.lower() in col_map:
                    return col_map[name.lower()]
            return None

        cc_col = get_col(['Centro de Custo', 'CC', 'Master'])
        grupo_col = get_col(['Grupo'])
        uf_col = get_col(['UF'])
        ano_col = get_col(['Ano'])
        mes_col = get_col(['Mes(es)', 'Mes', 'Mês', 'Meses'])
        valor_col = get_col(['Valor', 'Orçado'])

        if not all([cc_col, grupo_col, uf_col, ano_col, mes_col, valor_col]):
            return jsonify({
                'error': 'Colunas obrigatórias ausentes. Certifique-se de que o Excel possui: Centro de Custo, Grupo, UF, Ano, Mes(es), Valor'
            }), 400

        all_categories = Categoria.query.all()
        categoria_by_key = {}
        categoria_by_id = {}
        for categoria in all_categories:
            candidate_key = build_category_key(categoria.master, categoria.grupo, categoria.uf)
            if candidate_key not in categoria_by_key:
                categoria_by_key[candidate_key] = categoria
            categoria_by_id[categoria.id_categoria] = categoria

        missing_categories = []
        missing_category_keys = set()
        valid_items = []
        
        # Primeira passada: Validar categorias
        for index, row in df.iterrows():
            master = str(row[cc_col]).strip() if pd.notna(row[cc_col]) else None
            grupo = str(row[grupo_col]).strip() if pd.notna(row[grupo_col]) else None
            uf = str(row[uf_col]).strip() if pd.notna(row[uf_col]) else None
            key = build_category_key(master, grupo, uf)
            
            # Buscar categoria
            categoria = categoria_by_key.get(key)
            suggestion = None
            if not categoria and key not in missing_category_keys:
                missing_category_keys.add(key)
                suggestion = find_best_category_suggestion(master, grupo, uf, all_categories)
                missing_categories.append({
                    'master': master,
                    'grupo': grupo,
                    'uf': uf,
                    'key': key,
                    'suggestion': suggestion
                })
            
            valid_items.append({
                'index': index,
                'master': master,
                'grupo': grupo,
                'uf': uf,
                'key': key,
                'ano': int(row[ano_col]) if pd.notna(row[ano_col]) else None,
                'meses': normalize_months(row[mes_col]),
                'valor': to_decimal(row[valor_col]) if pd.notna(row[valor_col]) else Decimal('0'),
                'categoria_id': categoria.id_categoria if categoria else None
            })

        # Se houver categorias faltando e o usuário ainda não decidiu o que fazer
        if missing_categories and not (create_missing or skip_missing or missing_actions):
            return jsonify({
                'status': 'missing_categories',
                'missing': missing_categories,
                'message': 'Algumas categorias (Centro de Custo/Grupo) não existem.'
            }), 200

        # Processar importação
        created_count = 0
        updated_count = 0
        categories_created = 0
        created_category_ids = {}
        
        for item in valid_items:
            cat_id = item['categoria_id']
            
            if not cat_id:
                action = None
                if missing_actions:
                    action = missing_actions.get(item['key'])
                if not action:
                    if create_missing:
                        action = 'create'
                    elif skip_missing:
                        action = 'skip'
                if action and action.startswith('use_suggestion:'):
                    try:
                        suggestion_id = int(action.split(':', 1)[1])
                    except (ValueError, IndexError):
                        continue
                    suggested = categoria_by_id.get(suggestion_id)
                    if not suggested:
                        continue
                    cat_id = suggested.id_categoria
                elif action == 'create':
                    if item['key'] in created_category_ids:
                        cat_id = created_category_ids[item['key']]
                    else:
                        new_cat = Categoria(
                            categoria=item['grupo'],  # Usando grupo como nome da categoria por padrão
                            master=item['master'],
                            grupo=item['grupo'],
                            uf=item['uf']
                        )
                        db.session.add(new_cat)
                        db.session.flush()  # Para pegar o ID
                        cat_id = new_cat.id_categoria
                        created_category_ids[item['key']] = cat_id
                        categories_created += 1
                elif action == 'skip' or action is None:
                    continue
                else:
                    continue  # Segurança

            for mes in item['meses']:
                orcamento = Orcamento.query.filter_by(
                    id_categoria=cat_id,
                    mes=mes,
                    ano=item['ano']
                ).first()
                
                if orcamento:
                    if orcamento.status != 'aprovado':
                        orcamento.orcado = item['valor']
                        orcamento.atualizado_por = user_id
                        updated_count += 1
                else:
                    orcamento = Orcamento(
                        id_categoria=cat_id,
                        mes=mes,
                        ano=item['ano'],
                        orcado=item['valor'],
                        criado_por=user_id,
                        status='aguardando_aprovacao'
                    )
                    db.session.add(orcamento)
                    created_count += 1

        db.session.commit()
        
        # Log
        log = Log(
            id_usuario=current_user.id_usuario,
            acao=f'Importação Excel: {created_count} criados, {updated_count} atualizados, {categories_created} categorias criadas',
            tabela_afetada='orcamentos',
            detalhes={
                'criados': created_count,
                'atualizados': updated_count,
                'categorias_criadas': categories_created,
                'arquivo': file.filename
            }
        )
        db.session.add(log)
        db.session.commit()

        return jsonify({
            'message': 'Importação concluída com sucesso',
            'created': created_count,
            'updated': updated_count,
            'categories_created': categories_created
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

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
            try:
                # Check if mes is a number string (e.g., '1', '12')
                mes_num = int(mes)
                if 1 <= mes_num <= 12:
                    # Convert number to month name
                    mes = MESES[mes_num - 1]
            except (ValueError, TypeError):
                # It's already a name or something else, use as is
                pass
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
    """Reprova (marca como reprovado) múltiplos orçamentos em lote (gestor/admin)"""
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
        reprovados_detalhes = []

        for orc_id in orcamento_ids:
            orcamento = Orcamento.query.get(orc_id)
            if not orcamento:
                errors.append(f'Orçamento com ID {orc_id} não encontrado.')
                continue

            orcamento.status = 'reprovado'
            orcamento.aprovado_por = None
            orcamento.data_aprovacao = None
            orcamento.atualizado_por = user_id
            updated_count += 1
            
            # Coletar informações para o log
            categoria = Categoria.query.get(orcamento.id_categoria)
            if categoria:
                reprovados_detalhes.append({
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

        # Registrar reprovação no log com detalhes para rastreamento pelo admin
        if reprovados_detalhes:
            log = Log(
                id_usuario=current_user.id_usuario,
                acao=f'Reprovação em lote: {updated_count} orçamentos rejeitados',
                tabela_afetada='orcamentos',
                id_registro=None,
                detalhes={
                    'orcamentos_reprovados': reprovados_detalhes,
                    'total_reprovados': updated_count,
                    'motivo': motivo,
                    'gestor_usuario': current_user.nome,
                    'erros': len(errors),
                    'timestamp': datetime.utcnow().isoformat()
                }
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
    """Atualiza múltiplos orçamentos de uma vez, com permissões granulares."""
    try:
        user_id = get_jwt_identity()
        current_user = Usuario.query.get(user_id)
        
        # Permitir acesso para admin e gestor
        if current_user.papel not in ['admin', 'gestor']:
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
                # Validar dados mínimos para busca ou criação
                if 'id_categoria' not in orc_data or 'mes' not in orc_data or 'ano' not in orc_data:
                    errors.append(f'Dados incompletos para um orçamento: {orc_data}')
                    continue
                
                # Garante que o mês seja o nome, não o número
                mes_valor = orc_data['mes']
                mes_nome = MESES[mes_valor - 1] if isinstance(mes_valor, int) and 1 <= mes_valor <= 12 else mes_valor

                # Buscar ou criar
                orcamento = Orcamento.query.filter_by(
                    id_categoria=orc_data['id_categoria'],
                    mes=mes_nome,
                    ano=orc_data['ano']
                ).first()
                
                if orcamento: # Orçamento existente
                    if orcamento.status == 'aprovado':
                        if 'realizado' in orc_data:
                            orcamento.realizado = orc_data['realizado']
                            orcamento.atualizado_por = user_id
                            updated += 1
                        # Outras alterações em orçamentos aprovados são ignoradas
                    elif current_user.papel == 'admin': # Não aprovado, apenas admin pode editar
                        orcamento.atualizado_por = user_id
                        if 'orcado' in orc_data:
                            orcamento.orcado = orc_data['orcado']
                        if 'realizado' in orc_data:
                            orcamento.realizado = orc_data['realizado']
                        if 'status' in orc_data and orc_data['status']:
                            orcamento.status = orc_data['status']
                        updated += 1
                    else:
                        errors.append(f'Apenas administradores podem editar orçamentos com status "{orcamento.status}".')

                else: # Novo orçamento
                    if current_user.papel == 'admin':
                        orcamento = Orcamento(
                            id_categoria=orc_data['id_categoria'],
                            mes=mes_nome,
                            ano=orc_data['ano'],
                            criado_por=user_id,
                            status='rascunho'
                        )
                        db.session.add(orcamento)
                        if 'orcado' in orc_data:
                            orcamento.orcado = orc_data['orcado']
                        if 'realizado' in orc_data:
                            orcamento.realizado = orc_data['realizado']
                        if 'status' in orc_data and orc_data['status']:
                            orcamento.status = orc_data['status']
                        created += 1
                    else:
                        errors.append('Apenas administradores podem criar novos orçamentos.')

            except Exception as e:
                errors.append(f'Erro processando {orc_data.get("id_categoria", "N/A")}: {str(e)}')

        db.session.flush()
        for orc_data in data['orcamentos']:
            try:
                mes_nome = MESES[orc_data['mes'] - 1] if isinstance(orc_data['mes'], int) else orc_data['mes']
                orc = Orcamento.query.filter_by(id_categoria=orc_data['id_categoria'], mes=mes_nome, ano=orc_data['ano']).first()
                if orc:
                    processed_orcamentos.append({'id_orcamento': orc.id_orcamento})
            except (KeyError, TypeError): # Lida com orc_data malformado que já foi logado
                pass

        db.session.commit()
        
        # Registrar no log
        log = Log(
            id_usuario=current_user.id_usuario,
            acao=f'Atualização em lote: {created} criados, {updated} atualizados',
            tabela_afetada='orcamentos',
            id_registro=None,
            detalhes={'criados': created, 'atualizados': updated, 'erros': errors}
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
            
            if orcamento.status in ['rascunho', 'reprovado']:
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
                        'ano': orcamento.ano,
                        'orcado': float(orcamento.orcado),
                        'realizado': float(orcamento.realizado)
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
    """Reprova um orçamento (apenas gestor ou admin) — marca como 'reprovado'"""
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
        
        orcamento.status = 'reprovado'
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
            acao=f'Deletou orçamento {orcamento_data["mes"]}/{orcamento_data["ano"]} ({orcamento_data.get("status", "N/A")})',
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
                orc_id = orc.get('id_orcamento')
                orcamento_ids_em_logs.add(orc_id)
                
                # Buscar objeto atual do banco para hidratação
                db_orc = Orcamento.query.get(orc_id)
                
                # Hidratar com valor atual do banco se não estiver no log (logs antigos)
                # ou para garantir valor atualizado
                if 'orcado' not in orc:
                    if db_orc:
                        orc['orcado'] = float(db_orc.orcado)
                        orc['realizado'] = float(db_orc.realizado)
                    else:
                        orc['orcado'] = 0.0
                        orc['realizado'] = 0.0
                
                # Hidratar detalhes da categoria se não estiverem no log
                if 'categoria_nome' not in orc or 'master' not in orc:
                    if db_orc:
                        categoria = Categoria.query.get(db_orc.id_categoria)
                        if categoria:
                            orc['categoria_nome'] = categoria.categoria
                            orc['master'] = categoria.master
                            orc['uf'] = categoria.uf
                            orc['grupo'] = categoria.grupo
                            # Garantir mes/ano também
                            if 'mes' not in orc: orc['mes'] = db_orc.mes
                            if 'ano' not in orc: orc['ano'] = db_orc.ano
            
            # Agrupar por master, uf, categoria para exibição
            primeiro_orcamento = orcamentos_submetidos[0] if orcamentos_submetidos else {}
            submission = {
                'id_log': log.id_log,
                'data': log.timestamp.isoformat() if log.timestamp else None,
                'admin_usuario': log.usuario.nome if log.usuario else 'Desconhecido',
                'total_submetidos': detalhes.get('total_submetidos', 0),
                'ano': primeiro_orcamento.get('ano'),
                'mes': primeiro_orcamento.get('mes'),
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
                        'ano': orc.ano,
                        'orcado': float(orc.orcado),
                        'realizado': float(orc.realizado)
                    })
        
        # Se houver orçamentos sem log, criar uma submissão virtual
        if orcamentos_sem_log:
            primeiro_orcamento_virtual = orcamentos_sem_log[0] if orcamentos_sem_log else {}
            virtual_submission = {
                'id_log': None,  # Sem log real
                'data': None,
                'admin_usuario': 'Importado',
                'total_submetidos': len(orcamentos_sem_log),
                'ano': primeiro_orcamento_virtual.get('ano'),
                'mes': primeiro_orcamento_virtual.get('mes'),
                'orcamentos': orcamentos_sem_log,
                'masters': list(set([o.get('master') for o in orcamentos_sem_log if o.get('master')])),
                'ufs': list(set([o.get('uf') for o in orcamentos_sem_log if o.get('uf')])),
                'categorias': list(set([o.get('categoria_nome') for o in orcamentos_sem_log if o.get('categoria_nome')])),
            }
            resultado.insert(0, virtual_submission)  # Adicionar no início

        return jsonify(resultado), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/orcamentos/rejections', methods=['GET'])
@jwt_required()
def get_rejections():
    """Retorna rejeições de orçamentos para o admin (logs com detalhes de reprovações em lote e individuais)"""
    try:
        user_id = get_jwt_identity()
        current_user = Usuario.query.get(user_id)

        if current_user.papel != 'admin':
            return jsonify({'error': 'Acesso negado'}), 403

        resultado = []

        # 1. Buscar logs de reprovação em lote (ação contém 'Reprovação em lote')
        logs_lote = db.session.query(Log).filter(
            Log.acao.contains('Reprovação em lote'),
            Log.tabela_afetada == 'orcamentos'
        ).order_by(Log.timestamp.desc()).all()

        for log in logs_lote:
            detalhes = log.detalhes or {}
            orcamentos_reprovados = detalhes.get('orcamentos_reprovados', [])
            
            primeiro_orcamento_reprovado = orcamentos_reprovados[0] if orcamentos_reprovados else {}
            rejection = {
                'id_log': log.id_log,
                'data': log.timestamp.isoformat() if log.timestamp else None,
                'gestor_usuario': detalhes.get('gestor_usuario', log.usuario.nome if log.usuario else 'Desconhecido'),
                'total_reprovados': detalhes.get('total_reprovados', 0),
                'motivo': detalhes.get('motivo', 'Sem motivo especificado'),
                'tipo': 'lote',
                'ano': primeiro_orcamento_reprovado.get('ano'),
                'mes': primeiro_orcamento_reprovado.get('mes'),
                'orcamentos': orcamentos_reprovados,
                'masters': list(set([o.get('master') for o in orcamentos_reprovados if o.get('master')])),
                'ufs': list(set([o.get('uf') for o in orcamentos_reprovados if o.get('uf')])),
                'categorias': list(set([o.get('categoria_nome') for o in orcamentos_reprovados if o.get('categoria_nome')])),
            }
            resultado.append(rejection)

        # 2. Buscar logs de reprovações individuais (ação contém 'Reprovou')
        logs_individuais = db.session.query(Log).filter(
            Log.acao.contains('Reprovou'),
            Log.tabela_afetada == 'orcamentos'
        ).order_by(Log.timestamp.desc()).all()

        # Agrupar reprovações individuais por data/gestor
        reprovacoes_por_gestor = {}
        for log in logs_individuais:
            detalhes = log.detalhes or {}
            orcamento = detalhes.get('orcamento', {})
            motivo = detalhes.get('motivo', 'Sem motivo especificado')
            
            # Chave para agrupar: data do log + id do usuário + motivo
            key = (log.timestamp, log.id_usuario, motivo)
            
            if key not in reprovacoes_por_gestor:
                reprovacoes_por_gestor[key] = {
                    'id_log': log.id_log,
                    'data': log.timestamp.isoformat() if log.timestamp else None,
                    'gestor_usuario': log.usuario.nome if log.usuario else 'Desconhecido',
                    'motivo': motivo,
                    'tipo': 'individual',
                    'orcamentos': [],
                    'masters': set(),
                    'ufs': set(),
                    'categorias': set(),
                    'ano': None, # Será preenchido abaixo
                    'mes': None, # Será preenchido abaixo
                }
            
            if orcamento:
                categoria = Categoria.query.get(orcamento.get('id_categoria'))
                orc_detail = {
                    'id_orcamento': orcamento.get('id_orcamento'),
                    'id_categoria': orcamento.get('id_categoria'),
                    'categoria_nome': categoria.categoria if categoria else 'Desconhecida',
                    'master': categoria.master if categoria else '-',
                    'uf': categoria.uf if categoria else '-',
                    'grupo': categoria.grupo if categoria else '-',
                    'mes': orcamento.get('mes'),
                    'ano': orcamento.get('ano'),
                }
                reprovacoes_por_gestor[key]['orcamentos'].append(orc_detail)
                if categoria:
                    reprovacoes_por_gestor[key]['masters'].add(categoria.master)
                    reprovacoes_por_gestor[key]['ufs'].add(categoria.uf)
                    reprovacoes_por_gestor[key]['categorias'].add(categoria.categoria)
                
                # Preencher ano e mês do grupo com o primeiro orçamento encontrado
                if not reprovacoes_por_gestor[key]['ano'] and orc_detail.get('ano'):
                    reprovacoes_por_gestor[key]['ano'] = orc_detail.get('ano')
                if not reprovacoes_por_gestor[key]['mes'] and orc_detail.get('mes'):
                    reprovacoes_por_gestor[key]['mes'] = orc_detail.get('mes')

        # Converter sets para lists e calcular total
        for rejection_group in reprovacoes_por_gestor.values():
            rejection_group['total_reprovados'] = len(rejection_group['orcamentos'])
            rejection_group['masters'] = list(rejection_group['masters'])
            rejection_group['ufs'] = list(rejection_group['ufs'])
            rejection_group['categorias'] = list(rejection_group['categorias'])
            resultado.append(rejection_group)

        # Ordenar por data decrescente
        resultado.sort(key=lambda x: x['data'] if x['data'] else '', reverse=True)

        return jsonify(resultado), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
