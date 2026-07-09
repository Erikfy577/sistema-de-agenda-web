from flask import Blueprint, render_template, request, current_app, redirect, url_for
from urllib.parse import quote
import datetime


agenda_bp = Blueprint("agenda", __name__)


# ==========================================================
# MOSTRAR AGENDA
# ==========================================================

@agenda_bp.route("/agenda", methods=["GET"])
def tela_agenda():

    prof_selecionado = request.args.get(
        "profissional",
        "Dra. Jamile"
    )

    data_selecionada = request.args.get(
        "data",
        datetime.date.today().strftime("%Y-%m-%d")
    )

    wa_url = request.args.get("wa_url")


    conexao = current_app.conectar_banco()
    cursor = conexao.cursor()


    cursor.execute("""
        SELECT
            id,
            nome,
            telefone,
            prioridade,
            atendimento_tipo,
            status_aviso
        FROM pacientes
        WHERE profissional = ?
        AND status = 'Agendado'
        AND data_consulta = ?
        ORDER BY
            CASE prioridade
                WHEN 'Urgente' THEN 1
                WHEN 'Prioritário' THEN 2
                ELSE 3
            END,
            id ASC
    """,
    (
        prof_selecionado,
        data_selecionada
    ))


    pacientes = cursor.fetchall()

    conexao.close()


    return render_template(
        "agenda.html",
        pacientes=pacientes,
        prof_atual=prof_selecionado,
        data_atual=data_selecionada,
        wa_url=wa_url
    )



# ==========================================================
# AÇÕES DA AGENDA
# ==========================================================

@agenda_bp.route("/acoes_agenda", methods=["POST"])
def acoes_agenda():


    acao = request.form.get("acao")

    ids_selecionados = request.form.getlist(
        "pacientes_ids"
    )

    data_consulta = request.form.get(
        "data_consulta"
    )

    prof_atual = request.form.get(
        "prof_atual"
    )

    periodo = request.form.get(
        "periodo",
        "Manhã"
    )


    if not ids_selecionados:

        return redirect(
            url_for(
                "agenda.tela_agenda",
                profissional=prof_atual,
                data=data_consulta
            )
        )



    conexao = current_app.conectar_banco()
    cursor = conexao.cursor()



    # ======================================================
    # MENSAGEM NORMAL
    # ======================================================

    if acao == "notificar_whatsapp":


        mensagem_tipo = "normal"



    # ======================================================
    # CONFIRMAR CONSULTA AMANHÃ
    # ======================================================

    elif acao == "notificar_amanha":


        mensagem_tipo = "amanha"



    else:

        mensagem_tipo = None





    # ======================================================
    # ENVIO WHATSAPP
    # ======================================================

    if mensagem_tipo:



        id_paciente = ids_selecionados[0]


        cursor.execute("""
            SELECT nome, telefone
            FROM pacientes
            WHERE id = ?
        """,
        (id_paciente,))


        paciente = cursor.fetchone()



        if paciente:


            nome, telefone = paciente


            telefone = "".join(
                filter(
                    str.isdigit,
                    str(telefone)
                )
            )


            if not telefone.startswith("55"):

                telefone = "55" + telefone





            if periodo == "Manhã":

                horario = "das 07:00 às 10:00"


            elif periodo == "Tarde":

                horario = "das 13:00 às 16:00"


            else:

                horario = "das 17:00 às 19:30"





            data_formatada = datetime.datetime.strptime(
                data_consulta,
                "%Y-%m-%d"
            )



            if mensagem_tipo == "amanha":


                data_formatada = (
                    data_formatada +
                    datetime.timedelta(days=1)
                )


                data_br = data_formatada.strftime(
                    "%d/%m/%Y"
                )


                mensagem = f"""Olá *{nome}*, tudo bem?

Estamos entrando em contato para confirmar sua consulta de amanhã.

👨‍⚕️ *Profissional:* {prof_atual}

🌤️ *Período:* {periodo}

🕛 *Horário:* {horario}

📍 *Local:*
Unidade Básica de Saúde Maria Divina Monteiro

Podemos confirmar sua presença?

Obrigado pela atenção. 💙"""



            else:



                data_br = data_formatada.strftime(
                    "%d/%m/%Y"
                )


                mensagem = f"""Aviso Importante para você *{nome}*

Dando continuidade ao cuidado com a saúde, estamos entrando em contato para confirmar seu agendamento com *{prof_atual}*.

📅 *Data:* {data_br}

🌤️ *Período:* {periodo}

🕛 *Horário:* {horario}

📍 *Local:*
Unidade Básica de Saúde Maria Divina Monteiro

Podemos confirmar sua presença?

Caso não possa comparecer, pedimos que entre em contato:

📞 (64) 98131-1988

Cuidar da saúde hoje é um passo importante para o seu bem-estar. 💛"""





            whatsapp_url = (
                f"https://wa.me/{telefone}"
                f"?text={quote(mensagem)}"
            )



            placeholders = ",".join(
                "?" for _ in ids_selecionados
            )



            cursor.execute(
                f"""
                UPDATE pacientes
                SET status_aviso = 'Enviado'
                WHERE id IN ({placeholders})
                """,
                ids_selecionados
            )



            conexao.commit()

            conexao.close()



            return redirect(
                url_for(
                    "agenda.tela_agenda",
                    profissional=prof_atual,
                    data=data_consulta,
                    wa_url=whatsapp_url
                )
            )






    conexao.commit()

    conexao.close()



    return redirect(
        url_for(
            "agenda.tela_agenda",
            profissional=prof_atual,
            data=data_consulta
        )
    )