from flask import Blueprint, render_template, request, current_app
import datetime

dashboard_bp = Blueprint("dashboard", __name__)

@dashboard_bp.route("/dashboard", methods=["GET"])
def tela_dashboard():
    conexao = current_app.conectar_banco()
    cursor = conexao.cursor()

    # Recebe o mês do formulário ou define o mês atual por padrão (Formato YYYY-MM)
    mes_selecionado = request.args.get("mes", datetime.date.today().strftime("%Y-%m"))
    mes_busca = mes_selecionado + "%"

    # ==========================================
    # MÉTRICAS DO MÊS SELECIONADO (Cards)
    # ==========================================
    cursor.execute("SELECT COUNT(*) FROM pacientes WHERE data_consulta LIKE ?", (mes_busca,))
    total_mes = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM pacientes WHERE data_consulta LIKE ? AND status = 'Atendido'", (mes_busca,))
    atendidos_mes = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM pacientes WHERE data_consulta LIKE ? AND status = 'Falta'", (mes_busca,))
    faltas_mes = cursor.fetchone()[0]
    
    agendados_mes = total_mes - (atendidos_mes + faltas_mes)

    # ==========================================
    # DADOS PARA GRÁFICOS
    # ==========================================
    cursor.execute("""
        SELECT profissional, COUNT(*) 
        FROM pacientes 
        WHERE data_consulta LIKE ? 
        GROUP BY profissional
    """, (mes_busca,))
    dados_profissionais = cursor.fetchall()

    # ==========================================
    # LISTA DE PACIENTES (Tabela Inferior)
    # ==========================================
    cursor.execute("""
        SELECT nome, data_consulta, status, profissional
        FROM pacientes 
        WHERE data_consulta LIKE ? AND status IN ('Atendido', 'Falta')
        ORDER BY data_consulta DESC
    """, (mes_busca,))
    lista_pacientes = cursor.fetchall()

    conexao.close()

    return render_template(
        "dashboard.html",
        mes_selecionado=mes_selecionado,
        total_mes=total_mes,
        atendidos_mes=atendidos_mes,
        faltas_mes=faltas_mes,
        agendados_mes=agendados_mes,
        dados_profissionais=dados_profissionais,
        lista_pacientes=lista_pacientes
    )