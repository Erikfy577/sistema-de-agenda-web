import sqlite3
import os
import sys

# ==================================================
# CAMINHOS
# ==================================================
def caminho_base():
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

banco = os.path.join(caminho_base(), "banco.db")

# ==================================================
# ATUALIZAR BANCO
# ==================================================
try:
    conexao = sqlite3.connect(banco)
    cursor = conexao.cursor()
    
    # Adiciona a nova coluna com valor padrão 'Nenhum'
    cursor.execute("ALTER TABLE pacientes ADD COLUMN status_aviso TEXT DEFAULT 'Nenhum'")
    
    conexao.commit()
    print("✅ Banco de dados atualizado! Coluna 'status_aviso' adicionada com sucesso.")

except sqlite3.OperationalError as erro:
    # Se você rodar o código duas vezes sem querer, ele avisa em vez de quebrar
    if "duplicate column name" in str(erro).lower():
        print("⚠️ A coluna 'status_aviso' já existe no banco de dados. Tudo certo!")
    else:
        print(f"❌ Erro operacional: {erro}")
except Exception as erro:
    print(f"❌ Erro ao atualizar o banco: {erro}")
finally:
    conexao.close()