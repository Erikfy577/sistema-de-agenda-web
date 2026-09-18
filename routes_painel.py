from flask import Blueprint, render_template

painel_bp = Blueprint('painel', __name__)

# Tela de seleção de perfil
@painel_bp.route('/painel')
def painel_hub():
    return render_template('painel_hub.html')

# Tela da TV
@painel_bp.route('/painel/tv')
def painel_tv():
    return render_template('painel_tv.html')

# Tela de Controle Dinâmica 
@painel_bp.route('/painel/controle/<sala>')
def painel_controle(sala):
    return render_template('painel_controle.html', sala=sala)