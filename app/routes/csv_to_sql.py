from flask import Blueprint, render_template, request, jsonify
import csv
import io
import re

csv_bp = Blueprint('csv_to_sql', __name__, url_prefix='')

@csv_bp.route('/csv-to-sql', methods=['GET'])
def csv_page():
    return render_template('csv_sql.html')

@csv_bp.route('/api/csv-to-sql', methods=['POST'])
def csv_to_sql_api():
    data = request.get_json() or {}
    csv_data = (data.get('csv_data') or '').strip()
    table_name = (data.get('table_name') or '').strip()

    if not csv_data or not table_name:
        return jsonify({'error': 'Tabla y datos CSV requeridos.'}), 400

    try:
        reader = csv.reader(io.StringIO(csv_data.strip()))
        rows = [row for row in reader if any(cell.strip() for cell in row)]

        if not rows:
            return jsonify({'error': 'CSV inválido. Debe incluir al menos una fila de datos.'}), 400

        def _looks_like_header(row):
            cleaned = [cell.strip() for cell in row if cell.strip()]
            if not cleaned:
                return False
            return all(re.match(r'^[A-Za-z_][A-Za-z0-9_]*$', cell) for cell in cleaned)

        if len(rows) == 1:
            headers = [f'col{i+1}' for i in range(len(rows[0]))]
            data_rows = rows
        else:
            if _looks_like_header(rows[0]) and not _looks_like_header(rows[1]):
                headers = [h.strip() for h in rows[0]]
                data_rows = rows[1:]
            else:
                headers = [f'col{i+1}' for i in range(len(rows[0]))]
                data_rows = rows

        def _infer_sql_type(header_name, sample_value):
            if header_name.strip().lower() == 'id':
                return 'INT PRIMARY KEY'
            if sample_value.strip().lower() in ('true', 'false'):
                return 'BOOLEAN'
            if sample_value.strip().isdigit():
                return 'INT'
            return 'VARCHAR(100)'

        sample_row = data_rows[0] if data_rows else []
        column_types = []
        for index, header in enumerate(headers):
            sample_value = sample_row[index] if index < len(sample_row) else ''
            column_types.append(_infer_sql_type(header, sample_value))

        create_db_lines = [
            f'CREATE DATABASE IF NOT EXISTS db_{table_name};',
            f'USE db_{table_name};',
        ]

        create_columns = []
        for header, column_type in zip(headers, column_types):
            create_columns.append(f'    {header} {column_type}')

        create_table_lines = [
            f'CREATE TABLE {table_name} (',
            ',\n'.join(create_columns),
            ');',
        ]

        inserts = []
        for row in data_rows:
            values = []
            for value in row:
                value = value.strip()
                if value == '':
                    values.append('NULL')
                elif value.lower() in ('true', 'false'):
                    values.append(value.lower())
                elif value.replace('.', '', 1).isdigit():
                    values.append(value)
                else:
                    safe_value = value.replace("'", "''")
                    values.append(f"'{safe_value}'")

            values_line = ', '.join(values)
            inserts.append(f"INSERT INTO {table_name} ({', '.join(headers)}) VALUES ({values_line});")

        sql = '\n'.join(create_db_lines) + '\n\n' + '\n'.join(create_table_lines) + '\n\n' + '\n'.join(inserts)
        return jsonify({'sql': sql}), 200
    except Exception as exc:
        return jsonify({'error': f'Error al convertir CSV: {str(exc)}'}), 500
