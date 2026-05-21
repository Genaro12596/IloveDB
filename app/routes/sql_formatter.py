from flask import Blueprint, render_template, request, jsonify

from app.services.sql_formatter_service import format_sql_query

formatter_bp = Blueprint('formatter', __name__, url_prefix='')

@formatter_bp.route('/formatter', methods=['GET'])
def formatter_page():
    return render_template('formatter.html')

@formatter_bp.route('/api/format-sql', methods=['POST'])
def format_sql_api():
    data = request.get_json() or {}
    sql = (data.get('sql') or '').strip()
    if not sql:
        return jsonify({'error': 'Por favor ingresa una consulta SQL.'}), 400

    try:
        formatted_sql = format_sql_query(sql)
        return jsonify({'formatted_sql': formatted_sql}), 200
    except Exception as exc:
        return jsonify({'error': f'Error al formatear SQL: {str(exc)}'}), 500
