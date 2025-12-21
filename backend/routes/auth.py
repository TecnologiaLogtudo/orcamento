#app/routes/auth.py
from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity, get_jwt
from models import db, Usuario, Log
from datetime import datetime
from models import db, TokenBlacklist

bp = Blueprint('auth', __name__)

@bp.route('/login', methods=['POST'])
def login():
    """Autenticação de usuário"""
    try:
        data = request.get_json()
        
        if not data or not data.get('email') or not data.get('senha'):
            return jsonify({'error': 'Email e senha são obrigatórios'}), 400
        
        usuario = Usuario.query.filter_by(email=data['email']).first()
        
        if not usuario or not usuario.check_password(data['senha']):
            return jsonify({'error': 'Credenciais inválidas'}), 401
        
        # Criar token JWT
        access_token = create_access_token(identity=str(usuario.id_usuario))
        
        # Registrar login no log
        log = Log(
            id_usuario=usuario.id_usuario,
            acao='Login realizado',
            tabela_afetada='usuarios',
            id_registro=usuario.id_usuario,
            detalhes={'ip': request.remote_addr}
        )
        db.session.add(log)
        db.session.commit()
        
        return jsonify({
            'access_token': access_token,
            'usuario': usuario.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    """Retorna informações do usuário atual"""
    try:
        user_id = get_jwt_identity()
        usuario = Usuario.query.get(user_id)
        
        if not usuario:
            return jsonify({'error': 'Usuário não encontrado'}), 404
        
        return jsonify(usuario.to_dict()), 200
        
    except Exception as e:
        import traceback
        print("DEBUG JWT ERROR:", traceback.format_exc())
        return jsonify({'error': str(e)}), 500

@bp.route('/usuarios', methods=['GET'])
@jwt_required()
def list_usuarios():
    """Lista todos os usuários (apenas admin)"""
    try:
        user_id = get_jwt_identity()
        current_user = Usuario.query.get(user_id)
        
        if current_user.papel != 'admin':
            return jsonify({'error': 'Acesso negado'}), 403
        
        usuarios = Usuario.query.all()
        return jsonify([u.to_dict() for u in usuarios]), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/usuarios', methods=['POST'])
@jwt_required()
def create_usuario():
    """Cria novo usuário (apenas admin)"""
    try:
        user_id = get_jwt_identity()
        current_user = Usuario.query.get(user_id)
        
        if current_user.papel != 'admin':
            return jsonify({'error': 'Acesso negado'}), 403
        
        data = request.get_json()
        
        # Validações
        required_fields = ['nome', 'email', 'senha', 'papel']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Campo {field} é obrigatório'}), 400
        
        if data['papel'] not in ['admin', 'gestor', 'visualizador']:
            return jsonify({'error': 'Papel inválido'}), 400
        
        # Verificar se email já existe
        if Usuario.query.filter_by(email=data['email']).first():
            return jsonify({'error': 'Email já cadastrado'}), 400
        
        # Criar usuário
        usuario = Usuario(
            nome=data['nome'],
            email=data['email'],
            papel=data['papel']
        )
        usuario.set_password(data['senha'])
        
        db.session.add(usuario)
        db.session.commit()
        
        # Registrar no log
        log = Log(
            id_usuario=current_user.id_usuario,
            acao=f'Criou usuário {usuario.nome}',
            tabela_afetada='usuarios',
            id_registro=usuario.id_usuario,
            detalhes={'usuario_criado': usuario.to_dict()}
        )
        db.session.add(log)
        db.session.commit()
        
        return jsonify(usuario.to_dict()), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@bp.route('/usuarios/<int:id_usuario>', methods=['PUT'])
@jwt_required()
def update_usuario(id_usuario):
    """Atualiza usuário (apenas admin)"""
    try:
        user_id = get_jwt_identity()
        current_user = Usuario.query.get(user_id)
        
        if current_user.papel != 'admin':
            return jsonify({'error': 'Acesso negado'}), 403
        
        usuario = Usuario.query.get(id_usuario)
        if not usuario:
            return jsonify({'error': 'Usuário não encontrado'}), 404
        
        data = request.get_json()
        dados_antigos = usuario.to_dict()
        
        # Atualizar campos
        if 'nome' in data:
            usuario.nome = data['nome']
        if 'email' in data:
            # Verificar se email não está em uso
            email_existente = Usuario.query.filter_by(email=data['email']).first()
            if email_existente and email_existente.id_usuario != id_usuario:
                return jsonify({'error': 'Email já em uso'}), 400
            usuario.email = data['email']
        if 'papel' in data:
            if data['papel'] not in ['admin', 'gestor', 'visualizador']:
                return jsonify({'error': 'Papel inválido'}), 400
            usuario.papel = data['papel']
        if 'senha' in data:
            usuario.set_password(data['senha'])
        
        db.session.commit()
        
        # Registrar no log
        log = Log(
            id_usuario=current_user.id_usuario,
            acao=f'Atualizou usuário {usuario.nome}',
            tabela_afetada='usuarios',
            id_registro=usuario.id_usuario,
            detalhes={
                'antes': dados_antigos,
                'depois': usuario.to_dict()
            }
        )
        db.session.add(log)
        db.session.commit()
        
        return jsonify(usuario.to_dict()), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@bp.route('/usuarios/<int:id_usuario>', methods=['DELETE'])
@jwt_required()
def delete_usuario(id_usuario):
    """Deleta usuário (apenas admin)"""
    try:
        user_id = get_jwt_identity()
        current_user = Usuario.query.get(user_id)
        
        if current_user.papel != 'admin':
            return jsonify({'error': 'Acesso negado'}), 403
        
        # Não pode deletar a si mesmo
        if user_id == id_usuario:
            return jsonify({'error': 'Não é possível deletar seu próprio usuário'}), 400
        
        usuario = Usuario.query.get(id_usuario)
        if not usuario:
            return jsonify({'error': 'Usuário não encontrado'}), 404
        
        usuario_data = usuario.to_dict()
        
        db.session.delete(usuario)
        db.session.commit()
        
        # Registrar no log
        log = Log(
            id_usuario=current_user.id_usuario,
            acao=f'Deletou usuário {usuario_data["nome"]}',
            tabela_afetada='usuarios',
            id_registro=id_usuario,
            detalhes={'usuario_deletado': usuario_data}
        )
        db.session.add(log)
        db.session.commit()
        
        return jsonify({'message': 'Usuário deletado com sucesso'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
    
@bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    jti = get_jwt()["jti"]
    db.session.add(TokenBlacklist(jti=jti))
    db.session.commit()
    return {"msg": "Logout realizado com sucesso"}, 200

@bp.route('/change_password', methods=['PUT'])
@jwt_required()
def change_password():
    """Permite ao usuário logado alterar sua própria senha"""
    try:
        user_id = get_jwt_identity()
        current_user = Usuario.query.get(user_id)

        if not current_user:
            return jsonify({'error': 'Usuário não encontrado'}), 404
        
        data = request.get_json()
        old_password = data.get('old_password')
        new_password = data.get('new_password')

        if not old_password or not new_password:
            return jsonify({'error': 'Senha antiga e nova senha são obrigatórias'}), 400
        
        if not current_user.check_password(old_password):
            return jsonify({'error': 'Senha antiga incorreta'}), 401
        
        current_user.set_password(new_password)
        db.session.commit()

        # Registrar no log
        log = Log(
            id_usuario=current_user.id_usuario,
            acao='Alteração de senha',
            tabela_afetada='usuarios',
            id_registro=current_user.id_usuario,
            detalhes={'usuario': current_user.to_dict()}
        )
        db.session.add(log)
        db.session.commit()
        
        return jsonify({'message': 'Senha alterada com sucesso'}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500