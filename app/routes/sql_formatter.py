from flask import Blueprint, render_template, request, jsonify
from app.services.sql_formatter_service import format_sql_query, analyze_sql_query

formatter_bp = Blueprint('formatter', __name__, url_prefix='')

@formatter_bp.route('/formatter', methods=['GET'])
def formatter_page():
    return render_template('formatter.html')

@formatter_bp.route('/api/format-sql', methods=['POST'])
def format_sql_api():
    data = request.get_json(force=True, silent=True) or {}
    sql = (data.get('sql') or '').strip()

    if not sql:
        return jsonify({'error': 'La consulta SQL está vacía. Por favor, ingresa código para analizar.'}), 400

    try:
        formatted_sql = format_sql_query(sql)
        analysis_data = analyze_sql_query(sql)

        return jsonify({
            'formatted_sql': formatted_sql,
            'analysis': analysis_data['warnings'],
            'score': analysis_data['score'],
            'level': analysis_data['level'],
            'stats': analysis_data['stats']
        }), 200
        
    except Exception as processing_error:
        print(f"❌ [Error Interno] Motor SQL: {str(processing_error)}")
        return jsonify({'error': 'Error interno al procesar la sintaxis SQL.'}), 500