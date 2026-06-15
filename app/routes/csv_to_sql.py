from flask import Blueprint, render_template, request, jsonify
from app.services.csv_sql_service import process_csv_to_sql

csv_bp = Blueprint('csv_to_sql', __name__, url_prefix='')

@csv_bp.route('/csv-to-sql', methods=['GET'])
def csv_page():
    return render_template('csv_sql.html')

@csv_bp.route('/api/csv-to-sql', methods=['POST'])
def csv_to_sql_api():
    data = request.get_json(force=True, silent=True) or {}
    csv_data = (data.get('csv_data') or '').strip()
    table_name = (data.get('table_name') or '').strip()

    if not csv_data or not table_name:
        return jsonify({'error': 'Faltan parámetros: Se requiere el nombre de la tabla y los datos CSV.'}), 400

    try:
        # La lógica de conversión se mantiene en el servicio para separar
        # responsabilidades y facilitar las pruebas del controlador.
        result = process_csv_to_sql(table_name, csv_data)
        
        return jsonify({
            'sql': result['sql'],
            'stats': result['stats'],
            'schema': result['schema']
        }), 200
        
    except ValueError as value_error:
        return jsonify({'error': str(value_error)}), 400
    except Exception as processing_error:
        print(f"❌ [Error Backend] CSV to SQL: {str(processing_error)}")
        return jsonify({'error': 'Error interno al procesar el archivo CSV.'}), 500