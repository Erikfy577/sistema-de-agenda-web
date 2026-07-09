from flask import Blueprint, render_template, request, current_app, Response
import csv
import io
import datetime

cadastro_bp = Blueprint('cadastro', __name__)

@cadastro_bp.route('/cadastro', methods=['GET', 'POST'])
def tela_cadastro():
    mensagem = None
    
    if request.method == 'POST':
        nome = request.form.get('nome')
        telefone = request.form.get('telefone')
        profissional = request.form.get('profissional')
        prioridade = request.form.get('prioridade')
        tipo = request.form.get('atendimento_tipo')
        
        try:
            conexao = current_app.conectar_banco()
            cursor = conexao.cursor()
            
            cursor.execute("""
                INSERT INTO pacientes (nome, telefone, profissional, prioridade, atendimento_tipo, status, status_aviso) 
                VALUES (?, ?, ?, ?, ?, 'Aguardando', 'Nenhum')
            """, (nome, telefone, profissional, prioridade, tipo))
            
            conexao.commit()
            conexao.close()
            mensagem = "Paciente cadastrado na Fila de Espera com sucesso!"
            
        except Exception as erro:
            mensagem = f"Ocorreu um erro ao salvar no banco: {erro}"
            
    return render_template('cadastro.html', mensagem=mensagem)

# NOVA ROTA: Exportar Planilha
@cadastro_bp.route('/exportar_pacientes')
def exportar_pacientes():
    conexao = current_app.conectar_banco()
    cursor = conexao.cursor()
    # Puxa o histórico completo de todos os pacientes e seus status
    cursor.execute("SELECT id, nome, telefone, profissional, prioridade, atendimento_tipo, status, data_consulta FROM pacientes")
    pacientes = cursor.fetchall()
    conexao.close()

    # Cria o arquivo na memória
    si = io.StringIO()
    # Usa ponto e vírgula para abrir certinho no Excel em português
    writer = csv.writer(si, delimiter=';') 
    
    # Cabeçalho da planilha
    writer.writerow(['ID', 'Nome', 'Telefone', 'Profissional', 'Prioridade', 'Tipo', 'Status', 'Data da Consulta'])
    writer.writerows(pacientes)

    # Prepara o download com codificação correta para acentos (utf-8-sig)
    output = si.getvalue().encode('utf-8-sig')
    
    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment;filename=relatorio_telessaude_{datetime.date.today()}.csv"}
    )