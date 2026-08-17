import os
from flask import Flask

app = Flask(__name__)

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

app.register_blueprint(inicio_bp)
app.register_blueprint(cadastro_bp)
app.register_blueprint(espera_bp)
app.register_blueprint(agenda_bp)
app.register_blueprint(dashboard_bp)
app.register_blueprint(routes_laudo)


# ==============================================================================
# INICIALIZAÇÃO DO SERVIDOR (Waitress)
# ==============================================================================
if __name__ == '__main__':
    from waitress import serve
    
    print("=" * 60)
    print("✅ SISTEMA MODULAR WEB INICIADO COM SUCESSO")
    print("🖥️  Acesse localmente: http://localhost:5000")
    print("=" * 60)
    
    serve(app, host='0.0.0.0', port=5000)