from flask import Blueprint, render_template, request, jsonify
from app.services.table_size_service import calculate_table_size

size_bp = Blueprint('table_size', __name__, url_prefix='')

@size_bp.route('/table-size', methods=['GET'])
def table_size_page():
    return render_template('table_size.html')

@size_bp.route('/api/table-size', methods=['POST'])
def table_size_api():
    data = request.get_json(force=True, silent=True) or {}
    rows = data.get('rows')
    create_table_sql = (data.get('create_table_sql') or '').strip()

    try:
        row_count = int(rows)
        if row_count < 1: raise ValueError
    except Exception:
        return jsonify({'error': 'La cantidad de filas debe ser un número mayor a 0.'}), 400

    if not create_table_sql:
        return jsonify({'error': 'Debe proporcionar un script CREATE TABLE válido.'}), 400

    try:
        result = calculate_table_size(row_count, create_table_sql)
        return jsonify({'result': result}), 200
        
    except ValueError as ve:
        return jsonify({'error': str(ve)}), 400
    except Exception as exc:
        print(f"❌ [Error Backend] DB Sizer: {str(exc)}")
        return jsonify({'error': 'Error interno al procesar la sintaxis de la tabla.'}), 500