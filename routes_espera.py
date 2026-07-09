from flask import Blueprint, render_template, request, current_app, redirect, url_for
import datetime

espera_bp = Blueprint('espera', __name__)

@espera_bp.route('/espera')
def tela_espera():
    prof_selecionado = request.args.get('profissional', 'Dra. Jamile')
    data_selecionada = request.args.get('data', datetime.date.today().strftime('%Y-%m-%d'))
    
    conexao = current_app.conectar_banco()
    cursor = conexao.cursor()
    
    # Busca fila de espera
    cursor.execute("""
        SELECT id, nome, telefone, prioridade, atendimento_tipo, profissional 
        FROM pacientes WHERE profissional = ? AND status = 'Aguardando'
        ORDER BY CASE prioridade WHEN 'Urgente' THEN 1 WHEN 'Prioritário' THEN 2 ELSE 3 END, id ASC
    """, (prof_selecionado,))
    fila_espera = cursor.fetchall()
    
    # Busca agenda do dia
    cursor.execute("""
        SELECT id, nome, telefone, prioridade, atendimento_tipo, profissional 
        FROM pacientes WHERE profissional = ? AND status = 'Agendado' AND data_consulta = ?
        ORDER BY CASE prioridade WHEN 'Urgente' THEN 1 WHEN 'Prioritário' THEN 2 ELSE 3 END, id ASC
    """, (prof_selecionado, data_selecionada))
    agenda = cursor.fetchall()
    
    conexao.close()
    
    return render_template('espera.html', fila=fila_espera, agenda=agenda, 
                           prof_atual=prof_selecionado, data_atual=data_selecionada)

@espera_bp.route('/acoes_espera', methods=['POST'])
def acoes_espera():
    acao = request.form.get('acao')
    ids_selecionados = request.form.getlist('pacientes_ids')
    data_consulta = request.form.get('data_consulta')
    prof_atual = request.form.get('prof_atual')
    
    if ids_selecionados:
        conexao = current_app.conectar_banco()
        cursor = conexao.cursor()
        placeholders = ','.join('?' for _ in ids_selecionados)
        
        if acao == 'mover_agenda':
            cursor.execute(f"UPDATE pacientes SET status = 'Agendado', data_consulta = ? WHERE id IN ({placeholders})", [data_consulta] + ids_selecionados)
        elif acao == 'voltar_espera':
            cursor.execute(f"UPDATE pacientes SET status = 'Aguardando', data_consulta = NULL WHERE id IN ({placeholders})", ids_selecionados)
        elif acao == 'excluir':
            cursor.execute(f"DELETE FROM pacientes WHERE id IN ({placeholders})", ids_selecionados)
            
        conexao.commit()
        conexao.close()
        
    return redirect(url_for('espera.tela_espera', profissional=prof_atual, data=data_consulta))

@espera_bp.route('/editar_paciente', methods=['POST'])
def editar_paciente():
    id_pac = request.form.get('edit_id')
    nome = request.form.get('edit_nome')
    telefone = request.form.get('edit_telefone')
    profissional = request.form.get('edit_profissional')
    prioridade = request.form.get('edit_prioridade')
    tipo = request.form.get('edit_tipo')
    
    data_consulta = request.form.get('data_consulta')
    prof_atual = request.form.get('prof_atual')
    
    conexao = current_app.conectar_banco()
    cursor = conexao.cursor()
    cursor.execute("""
        UPDATE pacientes 
        SET nome=?, telefone=?, profissional=?, prioridade=?, atendimento_tipo=?
        WHERE id=?
    """, (nome, telefone, profissional, prioridade, tipo, id_pac))
    conexao.commit()
    conexao.close()
    
    return redirect(url_for('espera.tela_espera', profissional=prof_atual, data=data_consulta))