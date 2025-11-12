from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import event, text, TypeDecorator
from sqlalchemy.orm import attributes
from werkzeug.security import generate_password_hash, check_password_hash
import json

db = SQLAlchemy()

class JsonEncodedDict(TypeDecorator):
    """Enables JSON storage by encoding and decoding on the fly."""
    impl = db.Text

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        return json.dumps(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        return json.loads(value)



class Usuario(db.Model):
    __tablename__ = 'usuarios'
    
    id_usuario = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    senha_hash = db.Column(db.String(255), nullable=False)
    papel = db.Column(db.Enum('admin', 'gestor', 'visualizador'), nullable=False, default='visualizador')
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relacionamentos
    logs = db.relationship('Log', back_populates='usuario', lazy='dynamic')
    orcamentos_criados = db.relationship('Orcamento', foreign_keys='Orcamento.criado_por', back_populates='criador', lazy='dynamic')
    orcamentos_atualizados = db.relationship('Orcamento', foreign_keys='Orcamento.atualizado_por', back_populates='atualizador', lazy='dynamic')
    orcamentos_aprovados = db.relationship('Orcamento', foreign_keys='Orcamento.aprovado_por', back_populates='aprovador', lazy='dynamic')
    
    def set_password(self, password):
        """Define senha com hash"""
        self.senha_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Verifica senha"""
        return check_password_hash(self.senha_hash, password)
    
    def to_dict(self):
        """Converte para dicionário"""
        return {
            'id_usuario': self.id_usuario,
            'nome': self.nome,
            'email': self.email,
            'papel': self.papel,
            'criado_em': self.criado_em.isoformat() if self.criado_em else None
        }

class Categoria(db.Model):
    __tablename__ = 'categorias'
    
    id_categoria = db.Column(db.Integer, primary_key=True)
    categoria = db.Column(db.String(100), nullable=False)
    uf = db.Column(db.String(20))
    master = db.Column(db.String(100))
    grupo = db.Column(db.String(100))
    cod_class = db.Column(db.String(20))
    classe_custo = db.Column(db.String(100))
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relacionamentos
    orcamentos = db.relationship('Orcamento', back_populates='categoria', lazy='dynamic', cascade='all, delete-orphan')
    
    __table_args__ = (
        db.UniqueConstraint('categoria', 'grupo', 'cod_class', name='unique_categoria'),
    )
    
    def to_dict(self):
        """Converte para dicionário"""
        return {
            'id_categoria': self.id_categoria,
            'categoria': self.categoria,
            'uf': self.uf,
            'master': self.master,
            'grupo': self.grupo,
            'cod_class': self.cod_class,
            'classe_custo': self.classe_custo,
            'criado_em': self.criado_em.isoformat() if self.criado_em else None
        }

class Orcamento(db.Model):
    __tablename__ = 'orcamentos'
    
    id_orcamento = db.Column(db.Integer, primary_key=True)
    id_categoria = db.Column(db.Integer, db.ForeignKey('categorias.id_categoria', ondelete='CASCADE'), nullable=False)
    mes = db.Column(db.Enum('Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
                            'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'),
                   nullable=False)
    ano = db.Column(db.Integer, nullable=False)
    orcado = db.Column(db.Numeric(15, 2), default=0.00)
    realizado = db.Column(db.Numeric(15, 2), default=0.00)
    dif = db.Column(db.Numeric(15, 2), default=0.00)
    
    status = db.Column(db.Enum('rascunho', 'aguardando_aprovacao', 'aprovado'), default='rascunho')
    aprovado_por = db.Column(db.Integer, db.ForeignKey('usuarios.id_usuario', ondelete='SET NULL'))
    data_aprovacao = db.Column(db.DateTime)
    
    criado_por = db.Column(db.Integer, db.ForeignKey('usuarios.id_usuario', ondelete='SET NULL'))
    atualizado_por = db.Column(db.Integer, db.ForeignKey('usuarios.id_usuario', ondelete='SET NULL'))
    
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    atualizado_em = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamentos
    categoria = db.relationship('Categoria', back_populates='orcamentos')
    aprovador = db.relationship('Usuario', foreign_keys=[aprovado_por], back_populates='orcamentos_aprovados')
    criador = db.relationship('Usuario', foreign_keys=[criado_por], back_populates='orcamentos_criados')
    atualizador = db.relationship('Usuario', foreign_keys=[atualizado_por], back_populates='orcamentos_atualizados')
    
    __table_args__ = (
        db.UniqueConstraint('id_categoria', 'mes', 'ano', name='unique_orcamento'),
    )
    
    def to_dict(self, include_categoria=False):
        """Converte para dicionário"""
        data = {
            'id_orcamento': self.id_orcamento,
            'id_categoria': self.id_categoria,
            'mes': self.mes,
            'ano': self.ano,
            'orcado': float(self.orcado) if self.orcado else 0.0,
            'realizado': float(self.realizado) if self.realizado else 0.0,
            'dif': float(self.dif) if self.dif else 0.0,
            'status': self.status,
            'aprovado_por': self.aprovado_por,
            'data_aprovacao': self.data_aprovacao.isoformat() if self.data_aprovacao else None,
            'criado_em': self.criado_em.isoformat() if self.criado_em else None,
            'atualizado_em': self.atualizado_em.isoformat() if self.atualizado_em else None
        }
        
        if include_categoria and self.categoria:
            data['categoria'] = self.categoria.to_dict()
        
        return data

class Log(db.Model):
    __tablename__ = 'logs'
    
    id_log = db.Column(db.Integer, primary_key=True)
    id_usuario = db.Column(db.Integer, db.ForeignKey('usuarios.id_usuario', ondelete='SET NULL'))
    acao = db.Column(db.String(255))
    tabela_afetada = db.Column(db.String(50))
    id_registro = db.Column(db.Integer)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    detalhes = db.Column(JsonEncodedDict)
    
    # Relacionamentos
    usuario = db.relationship('Usuario', back_populates='logs')
    
    def to_dict(self):
        """Converte para dicionário"""
        return {
            'id_log': self.id_log,
            'id_usuario': self.id_usuario,
            'usuario_nome': self.usuario.nome if self.usuario else None,
            'acao': self.acao,
            'tabela_afetada': self.tabela_afetada,
            'id_registro': self.id_registro,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'detalhes': self.detalhes
        }

# View para relatórios (somente leitura)
class ResumoOrcamento(db.Model):
    __tablename__ = 'resumo_orcamento'
    __table_args__ = {'info': {'is_view': True}}
    
    # Como é uma view, precisamos definir uma primary key artificial
    categoria = db.Column(db.String(100), primary_key=True)
    uf = db.Column(db.String(20))
    master = db.Column(db.String(100))
    grupo = db.Column(db.String(100), primary_key=True)
    cod_class = db.Column(db.String(20), primary_key=True)
    classe_custo = db.Column(db.String(100))
    ano = db.Column(db.Integer, primary_key=True)
    mes = db.Column(db.String(20), primary_key=True)
    total_orcado = db.Column(db.Numeric(15, 2))
    total_realizado = db.Column(db.Numeric(15, 2))
    total_dif = db.Column(db.Numeric(15, 2))
    
    def to_dict(self):
        """Converte para dicionário"""
        return {
            'categoria': self.categoria,
            'uf': self.uf,
            'master': self.master,
            'grupo': self.grupo,
            'cod_class': self.cod_class,
            'classe_custo': self.classe_custo,
            'ano': self.ano,
            'mes': self.mes,
            'total_orcado': float(self.total_orcado) if self.total_orcado else 0.0,
            'total_realizado': float(self.total_realizado) if self.total_realizado else 0.0,
            'total_dif': float(self.total_dif) if self.total_dif else 0.0
        }

class TokenBlacklist(db.Model):
    __tablename__ = 'token_blacklist'

    id = db.Column(db.Integer, primary_key=True)
    jti = db.Column(db.String(36), nullable=False, unique=True)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f'<TokenBlacklist {self.jti}>'

@event.listens_for(Orcamento, 'before_insert')
@event.listens_for(Orcamento, 'before_update')
def calculate_dif(mapper, connection, target):
    if target.realizado is not None and target.orcado is not None:
        target.dif = target.realizado - target.orcado
    else:
        target.dif = 0