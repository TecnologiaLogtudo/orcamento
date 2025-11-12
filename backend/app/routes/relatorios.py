from flask import Blueprint, request, jsonify, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import db, Usuario, ResumoOrcamento, Orcamento, Categoria
from sqlalchemy import and_, or_
import pandas as pd
from io import BytesIO
from datetime import datetime
import os

bp = Blueprint('relatorios', __name__)

@bp.route('/relatorios', methods=['GET'])
@jwt_required()
def get_relatorios():
    """Retorna dados para relatórios com filtros"""
    try:
        # Filtros
        ano = request.args.get('ano', type=int)
        dono = request.args.get('dono')
        tipo_despesa = request.args.get('tipo_despesa')
        uf = request.args.get('uf')
        grupo = request.args.get('grupo')
        mes = request.args.get('mes')
        
        # Query base na view
        query = ResumoOrcamento.query
        
        # Aplicar filtros
        if ano:
            query = query.filter(ResumoOrcamento.ano == ano)
        if dono:
            query = query.filter(ResumoOrcamento.dono == dono)
        if tipo_despesa:
            query = query.filter(ResumoOrcamento.tipo_despesa == tipo_despesa)
        if uf:
            query = query.filter(ResumoOrcamento.uf == uf)
        if grupo:
            query = query.filter(ResumoOrcamento.grupo == grupo)
        if mes:
            query = query.filter(ResumoOrcamento.mes == mes)
        
        # Ordenar
        resultados = query.order_by(
            ResumoOrcamento.ano.desc(),
            ResumoOrcamento.dono,
            ResumoOrcamento.grupo
        ).all()
        
        return jsonify([r.to_dict() for r in resultados]), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/relatorios/detalhado', methods=['GET'])
@jwt_required()
def get_relatorio_detalhado():
    """Retorna relatório detalhado com dados de orçamentos e categorias"""
    try:
        # Filtros
        ano = request.args.get('ano', type=int)
        id_categoria = request.args.get('id_categoria', type=int)
        status = request.args.get('status')
        
        # Query com join
        query = db.session.query(Orcamento, Categoria)\
            .join(Categoria, Orcamento.id_categoria == Categoria.id_categoria)
        
        # Aplicar filtros
        if ano:
            query = query.filter(Orcamento.ano == ano)
        if id_categoria:
            query = query.filter(Orcamento.id_categoria == id_categoria)
        if status:
            query = query.filter(Orcamento.status == status)
        
        resultados = query.order_by(
            Orcamento.ano.desc(),
            Categoria.dono,
            Orcamento.mes
        ).all()
        
        # Formatar dados
        dados = []
        for orcamento, categoria in resultados:
            dados.append({
                **orcamento.to_dict(),
                'categoria_info': categoria.to_dict()
            })
        
        return jsonify(dados), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/relatorios/excel', methods=['GET'])
@jwt_required()
def export_excel():
    """Exporta relatório em formato Excel"""
    try:
        # Obter filtros
        ano = request.args.get('ano', type=int)
        dono = request.args.get('dono')
        tipo_despesa = request.args.get('tipo_despesa')
        uf = request.args.get('uf')
        grupo = request.args.get('grupo')
        
        # Query
        query = ResumoOrcamento.query
        
        if ano:
            query = query.filter(ResumoOrcamento.ano == ano)
        if dono:
            query = query.filter(ResumoOrcamento.dono == dono)
        if tipo_despesa:
            query = query.filter(ResumoOrcamento.tipo_despesa == tipo_despesa)
        if uf:
            query = query.filter(ResumoOrcamento.uf == uf)
        if grupo:
            query = query.filter(ResumoOrcamento.grupo == grupo)
        
        resultados = query.all()
        
        # Converter para DataFrame
        dados = [{
            'Dono': r.dono,
            'Tipo Despesa': r.tipo_despesa,
            'UF': r.uf,
            'Master': r.master,
            'Grupo': r.grupo,
            'Cod. Classe': r.cod_class,
            'Classe Custo': r.classe_custo,
            'Ano': r.ano,
            'Mês': r.mes,
            'Total Orçado': float(r.total_orcado) if r.total_orcado else 0.0,
            'Total Realizado': float(r.total_realizado) if r.total_realizado else 0.0,
            'Diferença': float(r.total_dif) if r.total_dif else 0.0
        } for r in resultados]
        
        df = pd.DataFrame(dados)
        
        # Criar arquivo Excel em memória
        output = BytesIO()
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # Aba principal com dados
            df.to_excel(writer, sheet_name='Relatório', index=False)
            
            # Aba com resumo
            if len(df) > 0:
                resumo = pd.DataFrame({
                    'Métrica': [
                        'Total Orçado',
                        'Total Realizado',
                        'Diferença Total',
                        'Percentual Execução'
                    ],
                    'Valor': [
                        df['Total Orçado'].sum(),
                        df['Total Realizado'].sum(),
                        df['Diferença'].sum(),
                        f"{(df['Total Realizado'].sum() / df['Total Orçado'].sum() * 100):.2f}%" if df['Total Orçado'].sum() > 0 else '0%'
                    ]
                })
                resumo.to_excel(writer, sheet_name='Resumo', index=False)
            
            # Formatar colunas
            worksheet = writer.sheets['Relatório']
            for column in worksheet.columns:
                max_length = 0
                column = [cell for cell in column]
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = (max_length + 2)
                worksheet.column_dimensions[column[0].column_letter].width = adjusted_width
        
        output.seek(0)
        
        # Nome do arquivo
        filename = f'relatorio_orcamento_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
        
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/relatorios/pdf', methods=['GET'])
@jwt_required()
def export_pdf():
    """Exporta relatório em formato PDF"""
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4, landscape
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.lib.enums import TA_CENTER, TA_RIGHT
        
        # Obter filtros
        ano = request.args.get('ano', type=int)
        dono = request.args.get('dono')
        tipo_despesa = request.args.get('tipo_despesa')
        uf = request.args.get('uf')
        grupo = request.args.get('grupo')
        
        # Query
        query = ResumoOrcamento.query
        
        if ano:
            query = query.filter(ResumoOrcamento.ano == ano)
        if dono:
            query = query.filter(ResumoOrcamento.dono == dono)
        if tipo_despesa:
            query = query.filter(ResumoOrcamento.tipo_despesa == tipo_despesa)
        if uf:
            query = query.filter(ResumoOrcamento.uf == uf)
        if grupo:
            query = query.filter(ResumoOrcamento.grupo == grupo)
        
        resultados = query.limit(100).all()  # Limitar para não sobrecarregar PDF
        
        # Criar PDF em memória
        output = BytesIO()
        doc = SimpleDocTemplate(
            output,
            pagesize=landscape(A4),
            rightMargin=30,
            leftMargin=30,
            topMargin=30,
            bottomMargin=18,
        )
        
        # Container para elementos
        elements = []
        
        # Estilos
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            textColor=colors.HexColor('#1e40af'),
            spaceAfter=30,
            alignment=TA_CENTER
        )
        
        # Título
        title = Paragraph("Relatório Orçamentário", title_style)
        elements.append(title)
        
        # Informações do relatório
        info_style = ParagraphStyle(
            'Info',
            parent=styles['Normal'],
            fontSize=10,
            spaceAfter=20
        )
        
        filtros_aplicados = []
        if ano:
            filtros_aplicados.append(f"Ano: {ano}")
        if dono:
            filtros_aplicados.append(f"Dono: {dono}")
        if tipo_despesa:
            filtros_aplicados.append(f"Tipo: {tipo_despesa}")
        if uf:
            filtros_aplicados.append(f"UF: {uf}")
        if grupo:
            filtros_aplicados.append(f"Grupo: {grupo}")
        
        if filtros_aplicados:
            filtros_text = f"Filtros: {' | '.join(filtros_aplicados)}"
        else:
            filtros_text = "Sem filtros aplicados"
        
        info = Paragraph(
            f"{filtros_text}<br/>Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}",
            info_style
        )
        elements.append(info)
        elements.append(Spacer(1, 0.2*inch))
        
        # Tabela de dados
        data = [['Dono', 'Grupo', 'Mês', 'Ano', 'Orçado', 'Realizado', 'Diferença']]
        
        total_orcado = 0
        total_realizado = 0
        total_dif = 0
        
        for r in resultados:
            orcado = float(r.total_orcado) if r.total_orcado else 0.0
            realizado = float(r.total_realizado) if r.total_realizado else 0.0
            dif = float(r.total_dif) if r.total_dif else 0.0
            
            total_orcado += orcado
            total_realizado += realizado
            total_dif += dif
            
            data.append([
                r.dono or '',
                r.grupo or '',
                r.mes or '',
                str(r.ano) or '',
                f'R$ {orcado:,.2f}',
                f'R$ {realizado:,.2f}',
                f'R$ {dif:,.2f}'
            ])
        
        # Linha de total
        data.append([
            'TOTAL',
            '',
            '',
            '',
            f'R$ {total_orcado:,.2f}',
            f'R$ {total_realizado:,.2f}',
            f'R$ {total_dif:,.2f}'
        ])
        
        # Criar tabela
        table = Table(data, colWidths=[1.2*inch, 1.5*inch, 0.8*inch, 0.6*inch, 1*inch, 1*inch, 1*inch])
        
        # Estilo da tabela
        table.setStyle(TableStyle([
            # Cabeçalho
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e40af')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            
            # Dados
            ('BACKGROUND', (0, 1), (-1, -2), colors.beige),
            ('TEXTCOLOR', (0, 1), (-1, -2), colors.black),
            ('ALIGN', (0, 1), (3, -2), 'LEFT'),
            ('ALIGN', (4, 1), (-1, -2), 'RIGHT'),
            ('FONTNAME', (0, 1), (-1, -2), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -2), 9),
            ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, colors.lightgrey]),
            
            # Total
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#1e40af')),
            ('TEXTCOLOR', (0, -1), (-1, -1), colors.whitesmoke),
            ('ALIGN', (0, -1), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, -1), (-1, -1), 10),
            
            # Bordas
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        
        elements.append(table)
        
        # Adicionar resumo
        elements.append(Spacer(1, 0.3*inch))
        
        percentual = (total_realizado / total_orcado * 100) if total_orcado > 0 else 0
        
        resumo_text = f"""
        <b>Resumo Executivo:</b><br/>
        • Total Orçado: R$ {total_orcado:,.2f}<br/>
        • Total Realizado: R$ {total_realizado:,.2f}<br/>
        • Diferença: R$ {total_dif:,.2f}<br/>
        • Percentual de Execução: {percentual:.2f}%
        """
        
        resumo = Paragraph(resumo_text, info_style)
        elements.append(resumo)
        
        # Gerar PDF
        doc.build(elements)
        output.seek(0)
        
        # Nome do arquivo
        filename = f'relatorio_orcamento_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf'
        
        return send_file(
            output,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/relatorios/comparativo', methods=['GET'])
@jwt_required()
def get_comparativo():
    """Retorna comparativo entre dois períodos"""
    try:
        ano1 = request.args.get('ano1', type=int)
        ano2 = request.args.get('ano2', type=int)
        
        if not ano1 or not ano2:
            return jsonify({'error': 'Anos são obrigatórios'}), 400
        
        # Dados ano 1
        dados_ano1 = ResumoOrcamento.query.filter_by(ano=ano1).all()
        
        # Dados ano 2
        dados_ano2 = ResumoOrcamento.query.filter_by(ano=ano2).all()
        
        return jsonify({
            'ano1': {
                'ano': ano1,
                'dados': [d.to_dict() for d in dados_ano1]
            },
            'ano2': {
                'ano': ano2,
                'dados': [d.to_dict() for d in dados_ano2]
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500