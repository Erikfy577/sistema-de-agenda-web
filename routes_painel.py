import os
import subprocess
import sys

from flask import Blueprint, redirect, render_template, url_for

painel_bp = Blueprint('painel', __name__)
processo_painel_tv = None

# Tela de seleção de perfil
@painel_bp.route('/painel')
def painel_hub():
    return render_template('painel_hub.html')

# Tela da TV
@painel_bp.route('/painel/tv')
def painel_tv():
    global processo_painel_tv

    if processo_painel_tv is None or processo_painel_tv.poll() is not None:
        caminho_painel = os.path.join(os.path.dirname(__file__), 'janela_chamadas.py')
        processo_painel_tv = subprocess.Popen([sys.executable, caminho_painel])

    return redirect(url_for('painel.painel_hub'))


@painel_bp.route('/painel/tv/fechar')
def fechar_painel_tv():
    global processo_painel_tv

    if processo_painel_tv is not None and processo_painel_tv.poll() is None:
        processo_painel_tv.terminate()
        processo_painel_tv = None

    return redirect(url_for('painel.painel_hub'))

# Tela de Controle Dinâmica 
@painel_bp.route('/painel/controle/<sala>')
def painel_controle(sala):
    return render_template('painel_controle.html', sala=sala)