from flask import Blueprint, render_template
import os

routes_laudo = Blueprint('routes_laudo', __name__)

@routes_laudo.route('/laudo')
def laudo():
    # Coleta os dados estritamente do .env. Nenhuma informação de lote fica no código.
    dados_testes = {
        'hiv_fab': os.getenv('HIV_FABRICANTE'),
        'hiv_lote': os.getenv('HIV_LOTE'),
        'hiv_val': os.getenv('HIV_VALIDADE'),
        
        'sifilis_fab': os.getenv('SIFILIS_FABRICANTE'),
        'sifilis_lote': os.getenv('SIFILIS_LOTE'),
        'sifilis_val': os.getenv('SIFILIS_VALIDADE'),
        
        'hcv_fab': os.getenv('HCV_FABRICANTE'),
        'hcv_lote': os.getenv('HCV_LOTE'),
        'hcv_val': os.getenv('HCV_VALIDADE'),
        
        'hbsag_fab': os.getenv('HBSAG_FABRICANTE'),
        'hbsag_lote': os.getenv('HBSAG_LOTE'),
        'hbsag_val': os.getenv('HBSAG_VALIDADE')
    }
    
    return render_template('laudo.html', **dados_testes)