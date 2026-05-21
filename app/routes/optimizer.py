"""
Ruta para SQL Optimizer
"""

from flask import Blueprint, render_template, request, jsonify
from app.services.optimizer_service import optimize_sql

optimizer_bp = Blueprint('optimizer', __name__, url_prefix='')


@optimizer_bp.route('/optimizer', methods=['GET'])
def optimizer_page():
    """Página de SQL Optimizer"""
    return render_template('optimizer.html')


@optimizer_bp.route('/api/optimize-sql', methods=['POST'])
def api_optimize_sql():
    """API endpoint para optimizar SQL"""
    try:
        data = request.get_json()
        sql = (data.get('sql') or '').strip()
        
        if not sql:
            return jsonify({
                'success': False,
                'error': 'Por favor, ingresa una consulta SQL.'
            }), 400
        
        result = optimize_sql(sql)
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error al procesar: {str(e)}'
        }), 500
