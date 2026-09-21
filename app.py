import os
from flask import Flask
from flask_socketio import SocketIO, emit

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins='*', async_mode='threading')

# Filas do painel: cada senha chamada na triagem fica disponível no consultório
# correspondente até ser chamada pelo médico.
filas_painel = {'A': [], 'B': []}
sequencias_painel = {'A': 0, 'B': 0}

from dotenv import load_dotenv

load_dotenv()

# ==============================================================================
# CONEXÃO COM O BANCO DE DADOS (Disponível para as rotas)
# ==============================================================================
def conectar_banco():
    caminho_banco = os.path.join('database', 'banco.db')
    import sqlite3
    return sqlite3.connect(caminho_banco)

# Registra a função de conexão no objeto da aplicação para os outros arquivos usarem
app.conectar_banco = conectar_banco

# ==============================================================================
# REGISTRO DOS BLUEPRINTS (Conectando os arquivos de rotas)
# ==============================================================================
from routes_inicio import inicio_bp
from routes_cadastro import cadastro_bp
from routes_espera import espera_bp
from routes_agenda import agenda_bp
from routes_dashboard import dashboard_bp
from routes_laudo import routes_laudo
from routes_painel import painel_bp


app.register_blueprint(inicio_bp)
app.register_blueprint(cadastro_bp)
app.register_blueprint(espera_bp)
app.register_blueprint(agenda_bp)
app.register_blueprint(dashboard_bp)
app.register_blueprint(routes_laudo)
app.register_blueprint(painel_bp)


@socketio.on('pedir_listas')
def enviar_listas():
    emit('atualizar_listas', filas_painel)


@socketio.on('chamar_nova_triagem')
def chamar_nova_triagem(dados):
    fila = dados.get('fila')
    fila = {'H': 'A', 'T': 'B'}.get(fila, fila)
    if fila not in ('A', 'B'):
        return

    sequencias_painel[fila] += 1
    numero = f'{sequencias_painel[fila]:02d}'
    senha = numero if fila == 'A' else f'B{numero}'
    sala = fila
    filas_painel[sala].append(senha)

    emit('nova_chamada', {'senha': senha, 'sala_origem': 'triagem'}, broadcast=True)
    emit('atualizar_listas', filas_painel, broadcast=True)


@socketio.on('chamar_proxima_medico')
def chamar_proxima_medico(dados):
    sala = dados.get('sala')
    if sala not in ('A', 'B'):
        return

    sequencias_painel[sala] += 1
    numero = f'{sequencias_painel[sala]:02d}'
    senha = numero if sala == 'A' else f'B{numero}'

    emit('nova_chamada', {'senha': senha, 'sala_origem': sala}, broadcast=True)


@socketio.on('chamar_manual')
def chamar_manual(dados):
    fila = dados.get('fila')
    nome_sala = str(dados.get('nome_sala', '')).strip()[:80]
    if fila not in ('A', 'B') or not nome_sala:
        return

    sequencias_painel[fila] += 1
    numero = f'{sequencias_painel[fila]:02d}'
    senha = numero if fila == 'A' else f'B{numero}'

    emit('nova_chamada', {
        'senha': senha,
        'sala_origem': 'manual',
        'sala_nome': nome_sala,
    }, broadcast=True)


@socketio.on('chamar_senha_manual')
def chamar_senha_manual(dados):
    senha = dados.get('senha')
    nome_sala = str(dados.get('nome_sala', '')).strip()[:80]
    fila = 'B' if str(senha).startswith('B') else 'A'
    if not nome_sala or senha not in filas_painel[fila]:
        return

    filas_painel[fila].remove(senha)
    emit('nova_chamada', {
        'senha': senha,
        'sala_origem': 'manual',
        'sala_nome': nome_sala,
    }, broadcast=True)
    emit('atualizar_listas', filas_painel, broadcast=True)


@socketio.on('chamar_medico')
def chamar_medico(dados):
    senha = dados.get('senha')
    sala = dados.get('sala')
    if sala not in filas_painel or senha not in filas_painel[sala]:
        return

    filas_painel[sala].remove(senha)
    emit('nova_chamada', {'senha': senha, 'sala_origem': sala}, broadcast=True)
    emit('atualizar_listas', filas_painel, broadcast=True)


@socketio.on('rechamar_senha')
def rechamar_senha(dados):
    senha = dados.get('senha')
    sala = dados.get('sala')
    sala_evento = sala
    if sala == 'triagem':
        sala = 'B' if str(senha).startswith('B') else 'A'
    if sala not in ('A', 'B') or senha not in filas_painel[sala]:
        return

    emit('nova_chamada', {'senha': senha, 'sala_origem': sala_evento}, broadcast=True)

# ==============================================================================
# INICIALIZAÇÃO DO SERVIDOR (Waitress)
# ==============================================================================
if __name__ == '__main__':
    print("=" * 60)
    print("✅ SISTEMA MODULAR WEB INICIADO COM SUCESSO")
    print("🖥️  Acesse localmente: http://localhost:5000")
    print("=" * 60)

    socketio.run(app, host='0.0.0.0', port=5000, allow_unsafe_werkzeug=True)