from flask import (
    Blueprint,
    render_template,
    request,
    current_app,
    Response,
    redirect,
    url_for
)

import csv
import io
import os
import datetime


cadastro_bp = Blueprint('cadastro', __name__)


# ==========================================================
# TELA DE CADASTRO
# ==========================================================

@cadastro_bp.route('/cadastro', methods=['GET', 'POST'])
def tela_cadastro():

    mensagem = None

    if request.method == 'POST':

        nome = request.form.get('nome')
        telefone = request.form.get('telefone')
        profissional = request.form.get('profissional')
        prioridade = request.form.get('prioridade')
        tipo = request.form.get('atendimento_tipo')

        conexao = None

        try:

            # --------------------------------------------------
            # CONECTAR AO BANCO
            # --------------------------------------------------

            conexao = current_app.conectar_banco()
            cursor = conexao.cursor()

            # --------------------------------------------------
            # INSERIR PACIENTE
            # --------------------------------------------------

            cursor.execute("""
                INSERT INTO pacientes (
                    nome,
                    telefone,
                    profissional,
                    prioridade,
                    atendimento_tipo,
                    status,
                    status_aviso
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                nome,
                telefone,
                profissional,
                prioridade,
                tipo,
                'Aguardando',
                'Nenhum'
            ))

            conexao.commit()

            mensagem = (
                "Paciente cadastrado na Fila de Espera "
                "com sucesso!"
            )

        except Exception as erro:

            if conexao:
                conexao.rollback()

            mensagem = (
                f"Ocorreu um erro ao salvar no banco: {erro}"
            )

            print("=" * 60)
            print("ERRO AO CADASTRAR PACIENTE")
            print(type(erro).__name__)
            print(str(erro))
            print("=" * 60)

        finally:

            if conexao:
                conexao.close()

    # ==========================================================
    # WEBHOOK DO MAKE
    # ==========================================================

    url_make = os.getenv('WEBHOOK_MAKE', '')

    # ==========================================================
    # ENVIAR DADOS PARA O HTML
    # ==========================================================

    return render_template(
        'cadastro.html',
        mensagem=mensagem,
        webhook_url=url_make
    )


# ==========================================================
# EXPORTAR PACIENTES PARA CSV
# ==========================================================

@cadastro_bp.route('/exportar_pacientes')
def exportar_pacientes():

    conexao = None

    try:

        # --------------------------------------------------
        # CONECTAR AO BANCO
        # --------------------------------------------------

        conexao = current_app.conectar_banco()
        cursor = conexao.cursor()

        # --------------------------------------------------
        # BUSCAR PACIENTES
        # --------------------------------------------------

        cursor.execute("""
            SELECT
                id,
                nome,
                telefone,
                profissional,
                prioridade,
                atendimento_tipo,
                status,
                data_consulta
            FROM pacientes
        """)

        pacientes = cursor.fetchall()

        # --------------------------------------------------
        # CRIAR CSV NA MEMÓRIA
        # --------------------------------------------------

        si = io.StringIO(
            newline='',
            encoding='utf-8'
        )

        # Usa ; para abrir corretamente no Excel em português
        writer = csv.writer(
            si,
            delimiter=';',
            lineterminator='\n'
        )

        # --------------------------------------------------
        # CABEÇALHO
        # --------------------------------------------------

        writer.writerow([
            'ID',
            'Nome',
            'Telefone',
            'Profissional',
            'Prioridade',
            'Tipo',
            'Status',
            'Data da Consulta'
        ])

        # --------------------------------------------------
        # DADOS
        # --------------------------------------------------

        writer.writerows(pacientes)

        # --------------------------------------------------
        # UTF-8 COM BOM
        # --------------------------------------------------

        output = si.getvalue().encode('utf-8-sig')

        # --------------------------------------------------
        # NOME DO ARQUIVO
        # --------------------------------------------------

        data_hoje = datetime.date.today().strftime(
            "%d-%m-%Y"
        )

        nome_arquivo = (
            f"relatorio_telessaude_{data_hoje}.csv"
        )

        return Response(
            output,
            mimetype="text/csv",
            headers={
                "Content-Disposition":
                    f"attachment; filename={nome_arquivo}"
            }
        )

    except Exception as erro:

        print("=" * 60)
        print("ERRO AO EXPORTAR PACIENTES")
        print(type(erro).__name__)
        print(str(erro))
        print("=" * 60)

        return Response(
            f"Erro ao exportar pacientes: {erro}",
            status=500,
            mimetype="text/plain"
        )

    finally:

        if conexao:
            conexao.close()


# ==========================================================
# IMPORTAR PACIENTES VIA CSV
# ==========================================================

@cadastro_bp.route('/injetar_script_bd', methods=['POST'])
def injetar_script_bd():

    # ------------------------------------------------------
    # PEGAR ARQUIVO ENVIADO PELO FORMULÁRIO
    # ------------------------------------------------------

    arquivo = request.files.get('arquivo_csv')

    # ------------------------------------------------------
    # VERIFICAR SE EXISTE ARQUIVO
    # ------------------------------------------------------

    if not arquivo or arquivo.filename == '':

        return redirect(
            url_for('cadastro.tela_cadastro')
        )

    conexao = None

    try:

        # ==================================================
        # CONECTAR AO BANCO
        # ==================================================

        conexao = current_app.conectar_banco()
        cursor = conexao.cursor()

        # ==================================================
        # LER ARQUIVO
        # ==================================================

        conteudo = arquivo.stream.read()

        # --------------------------------------------------
        # TENTAR UTF-8
        # --------------------------------------------------

        try:

            texto = conteudo.decode('utf-8-sig')

        except UnicodeDecodeError:

            # --------------------------------------------------
            # CASO O EXCEL TENHA SALVADO EM OUTRA CODIFICAÇÃO
            # --------------------------------------------------

            texto = conteudo.decode('latin-1')

        # ==================================================
        # CRIAR STREAM
        # ==================================================

        stream = io.StringIO(
            texto,
            newline=''
        )

        # ==================================================
        # DETECTAR SEPARADOR
        # ==================================================

        primeira_linha = stream.readline()

        stream.seek(0)

        if ';' in primeira_linha:

            delimitador = ';'

        else:

            delimitador = ','

        print("=" * 60)
        print("IMPORTAÇÃO DE CSV")
        print(f"Separador detectado: {delimitador}")
        print("=" * 60)

        # ==================================================
        # LEITOR CSV
        # ==================================================

        leitor = csv.reader(
            stream,
            delimiter=delimitador
        )

        # ==================================================
        # PULAR CABEÇALHO
        # ==================================================

        try:

            cabecalho = next(leitor)

            print("Cabeçalho encontrado:")
            print(cabecalho)

        except StopIteration:

            return redirect(
                url_for('cadastro.tela_cadastro')
            )

        # ==================================================
        # CONTADORES
        # ==================================================

        importados = 0
        duplicados = 0
        ignorados = 0

        # ==================================================
        # PERCORRER LINHAS
        # ==================================================

        for numero_linha, linha in enumerate(
            leitor,
            start=2
        ):

            # ------------------------------------------------
            # IGNORAR LINHAS VAZIAS
            # ------------------------------------------------

            if not linha:

                ignorados += 1
                continue

            # ------------------------------------------------
            # VERIFICAR QUANTIDADE DE COLUNAS
            # ------------------------------------------------

            if len(linha) < 6:

                print(
                    f"Linha {numero_linha} ignorada: "
                    f"quantidade de colunas insuficiente."
                )

                ignorados += 1
                continue

            # =================================================
            # PEGAR DADOS
            # =================================================

            nome = linha[0].strip()

            telefone = linha[1].strip()

            profissional = linha[2].strip()
            
            if profissional.lower() == 'dr. jamile':
             profissional = 'Dra. Jamile'

            prioridade_planilha = linha[3].strip()

            status = linha[4].strip()

            retorno_planilha = (
                linha[5]
                .strip()
                .lower()
            )

            # ------------------------------------------------
            # VERIFICAR NOME
            # ------------------------------------------------

            if not nome:

                ignorados += 1
                continue

            # =================================================
            # CONVERTER TIPO DE ATENDIMENTO
            # =================================================

            if retorno_planilha in (
                'sim',
                's',
                'yes',
                'true'
            ):

                atendimento_tipo = 'Retorno'

            else:

                atendimento_tipo = 'Nova Consulta'

            # =================================================
            # CONVERTER PRIORIDADE
            # =================================================

            if prioridade_planilha.lower() == 'normal':

                prioridade = 'Eletivo'

            else:

                prioridade = prioridade_planilha

            # =================================================
            # VERIFICAR DUPLICIDADE
            # =================================================

            cursor.execute(
                """
                SELECT id
                FROM pacientes
                WHERE nome = ?
                """,
                (nome,)
            )

            paciente_existente = cursor.fetchone()

            if paciente_existente:

                print(
                    f"Paciente duplicado: {nome}"
                )

                duplicados += 1
                continue

            # =================================================
            # INSERIR PACIENTE
            # =================================================

            cursor.execute("""
                INSERT INTO pacientes (
                    nome,
                    telefone,
                    profissional,
                    atendimento_tipo,
                    prioridade,
                    status,
                    status_aviso
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                nome,
                telefone,
                profissional,
                atendimento_tipo,
                prioridade,
                status,
                'Nenhum'
            ))

            importados += 1

        # ==================================================
        # SALVAR ALTERAÇÕES
        # ==================================================

        conexao.commit()

        # ==================================================
        # MOSTRAR RESULTADO NO TERMINAL
        # ==================================================

        print("=" * 60)
        print("IMPORTAÇÃO CONCLUÍDA")
        print(f"Importados : {importados}")
        print(f"Duplicados : {duplicados}")
        print(f"Ignorados  : {ignorados}")
        print("=" * 60)

        # ==================================================
        # VOLTAR PARA CADASTRO
        # ==================================================

        return redirect(
            url_for('cadastro.tela_cadastro')
        )

    except Exception as erro:

        # ==================================================
        # DESFAZER ALTERAÇÕES
        # ==================================================

        if conexao:

            conexao.rollback()

        # ==================================================
        # MOSTRAR ERRO NO TERMINAL
        # ==================================================

        print("=" * 60)
        print("ERRO AO IMPORTAR CSV")
        print("=" * 60)
        print(f"Tipo: {type(erro).__name__}")
        print(f"Erro: {erro}")
        print("=" * 60)

        # ==================================================
        # MOSTRAR ERRO NO NAVEGADOR
        # ==================================================

        return f"""
        <!DOCTYPE html>
        <html lang="pt-br">

        <head>
            <meta charset="UTF-8">
            <title>Erro na importação</title>

            <style>
                body {{
                    font-family: Arial, sans-serif;
                    padding: 40px;
                    background: #f5f5f5;
                }}

                .erro {{
                    background: white;
                    padding: 30px;
                    border-radius: 10px;
                    max-width: 800px;
                    margin: auto;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                }}

                h1 {{
                    color: #b00020;
                }}

                pre {{
                    background: #eee;
                    padding: 15px;
                    border-radius: 5px;
                    white-space: pre-wrap;
                }}

                a {{
                    display: inline-block;
                    margin-top: 20px;
                    padding: 10px 20px;
                    background: #007bff;
                    color: white;
                    text-decoration: none;
                    border-radius: 5px;
                }}
            </style>
        </head>

        <body>

            <div class="erro">

                <h1>Erro ao importar pacientes</h1>

                <h3>Tipo do erro:</h3>

                <pre>{type(erro).__name__}</pre>

                <h3>Mensagem:</h3>

                <pre>{erro}</pre>

                <a href="/cadastro">
                    Voltar para o cadastro
                </a>

            </div>

        </body>

        </html>
        """, 500

    finally:

        # ==================================================
        # FECHAR BANCO
        # ==================================================

        if conexao:

            conexao.close()