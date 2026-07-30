from flask import Blueprint, render_template, request, current_app, redirect, url_for
from urllib.parse import quote
import datetime
import requests
import os
import time
import random

agenda_bp = Blueprint("agenda", __name__)

# ==========================================================
# MOSTRAR AGENDA
# ==========================================================

@agenda_bp.route("/agenda", methods=["GET"])
def tela_agenda():
    prof_selecionado = request.args.get("profissional", "Dra. Jamile")
    data_selecionada = request.args.get("data", datetime.date.today().strftime("%Y-%m-%d"))

    conexao = current_app.conectar_banco()
    cursor = conexao.cursor()

    cursor.execute("""
        SELECT id, nome, telefone, prioridade, atendimento_tipo, status_aviso
        FROM pacientes
        WHERE profissional = ? AND status = 'Agendado' AND data_consulta = ?
        ORDER BY CASE prioridade WHEN 'Urgente' THEN 1 WHEN 'Prioritário' THEN 2 ELSE 3 END, id ASC
    """, (prof_selecionado, data_selecionada))

    pacientes = cursor.fetchall()
    conexao.close()

    return render_template(
        "agenda.html",
        pacientes=pacientes,
        prof_atual=prof_selecionado,
        data_atual=data_selecionada
    )

# ==========================================================
# AÇÕES DA AGENDA
# ==========================================================

@agenda_bp.route("/acoes_agenda", methods=["POST"])
def acoes_agenda():
    acao = request.form.get("acao")
    ids_selecionados = request.form.getlist("pacientes_ids")
    data_consulta = request.form.get("data_consulta")
    prof_atual = request.form.get("prof_atual")

    # --- TRAVA DE SEGURANÇA NO BACKEND ---
    if prof_atual == "Dra. Jamile":
        periodo = "Manhã"
    elif prof_atual in ["Dra. Laurice", "Dr. Gerlando"]:
        periodo = "Noite"
    else:
        # Jadson atende Manhã e Tarde, então pegamos o que vier da tela
        periodo = request.form.get("periodo", "Manhã")

    if not ids_selecionados:
        return redirect(url_for("agenda.tela_agenda", profissional=prof_atual, data=data_consulta))

    conexao = current_app.conectar_banco()
    cursor = conexao.cursor()

    # --- AÇÕES CRUD ---
    if acao in ["atendido", "falta", "excluir"]:
        placeholders = ",".join("?" for _ in ids_selecionados)
        if acao == "atendido":
            cursor.execute(f"UPDATE pacientes SET status = 'Atendido' WHERE id IN ({placeholders})", ids_selecionados)
        elif acao == "falta":
            cursor.execute(f"UPDATE pacientes SET status = 'Falta' WHERE id IN ({placeholders})", ids_selecionados)
        elif acao == "excluir":
            cursor.execute(f"DELETE FROM pacientes WHERE id IN ({placeholders})", ids_selecionados)
        
        conexao.commit()
        conexao.close()
        return redirect(url_for("agenda.tela_agenda", profissional=prof_atual, data=data_consulta))

    # --- INTEGRAÇÃO EVOLUTION API ---
    if acao == "notificar_whatsapp":
        mensagem_tipo = "normal"
    elif acao == "notificar_amanha":
        mensagem_tipo = "amanha"
    else:
        mensagem_tipo = None

    if mensagem_tipo:
        evo_url = os.getenv("EVO_INSTANCE_URL")
        evo_api_key = os.getenv("EVO_API_KEY")
        nome_instancia = "erik-teste" 
        url_envio = f"{evo_url}/message/sendText/{nome_instancia}"
        
        evo_headers = {
            "apikey": evo_api_key,
            "Content-Type": "application/json"
        }

        placeholders = ",".join("?" for _ in ids_selecionados)
        cursor.execute(f"""
            SELECT id, nome, telefone
            FROM pacientes
            WHERE id IN ({placeholders})
        """, ids_selecionados)
        
        pacientes_selecionados = cursor.fetchall()

        for paciente in pacientes_selecionados:
            id_paciente, nome, telefone = paciente
            telefone = "".join(filter(str.isdigit, str(telefone)))
            if not telefone.startswith("55"):
                telefone = "55" + telefone

            if periodo == "Manhã":
                horario = "das 07:00 às 09:30"
            elif periodo == "Tarde":
                horario = "das 13:00 às 16:00"
            else:
                horario = "das 17:00 às 19:00"

            data_formatada = datetime.datetime.strptime(data_consulta, "%Y-%m-%d")

            if mensagem_tipo == "amanha":
                data_formatada = data_formatada + datetime.timedelta(days=1)
                data_br = data_formatada.strftime("%d/%m/%Y")
                mensagem = f"""Olá *{nome}*, tudo bem?\n\nEstamos entrando em contato para confirmar sua consulta de amanhã.\n\n👨‍⚕️ *Profissional:* {prof_atual}\n🌤️ *Período:* {periodo}\n🕛 *Horário:* {horario}\n\n📍 *Local:*\nUnidade Básica de Saúde Maria Divina Monteiro\n\nPodemos confirmar sua presença?\nObrigado pela atenção. 💙"""
            else:
                data_br = data_formatada.strftime("%d/%m/%Y")
                mensagem = f"""Aviso Importante para você *{nome}*\n\nDando continuidade ao cuidado com a saúde, estamos entrando em contato para confirmar seu agendamento com *{prof_atual}*.\n\n📅 *Data:* {data_br}\n🌤️ *Período:* {periodo}\n🕛 *Horário:* {horario}\n\n📍 *Local:*\nUnidade Básica de Saúde Maria Divina Monteiro\n\nPodemos confirmar sua presença?\nCaso não possa comparecer, pedimos que entre em contato:\n📞 (64) 98131-1988\n\nCuidar da saúde hoje é um passo importante para o seu bem-estar. 💛"""

            
            payload = {
                "number": telefone,
                "textMessage": {
                    "text": mensagem
                }
            }

            try:
                if evo_url and evo_api_key:
                    resposta = requests.post(url_envio, json=payload, headers=evo_headers)
                    if resposta.status_code in [200, 201]:
                        cursor.execute("UPDATE pacientes SET status_aviso = 'Enviado' WHERE id = ?", (id_paciente,))

                        time.sleep(random.randint(2, 4))
                        
                    else:
                        print(f"Erro na Evolution API - Status {resposta.status_code}: {resposta.text}")
            except Exception as e:
                print(f"Erro ao enviar mensagem para {nome}: {e}")

        conexao.commit()
        conexao.close()
        return redirect(url_for("agenda.tela_agenda", profissional=prof_atual, data=data_consulta))

    conexao.commit()
    conexao.close()
    return redirect(url_for("agenda.tela_agenda", profissional=prof_atual, data=data_consulta))