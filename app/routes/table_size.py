from flask import Blueprint, render_template, request, jsonify
import re # <-- Esta es la línea crucial que falta o está mal ubicada

size_bp = Blueprint('table_size', __name__, url_prefix='')

TYPE_SIZES = {
    'INT': 4,
    'BIGINT': 8,
    'SMALLINT': 2,
    'VARCHAR': 50,
    'CHAR': 1,
    'TEXT': 100,
    'DATE': 3,
    'DATETIME': 8,
    'BOOLEAN': 1,
    'FLOAT': 4,
    'DOUBLE': 8,
}

@size_bp.route('/table-size', methods=['GET'])
def table_size_page():
    return render_template('table_size.html')

@size_bp.route('/api/table-size', methods=['POST'])
def table_size_api():
    data = request.get_json() or {}
    rows = data.get('rows')
    create_table_sql = (data.get('create_table_sql') or '').strip()

    try:
        row_count = int(rows)
        if row_count < 1:
            raise ValueError
    except Exception:
        return jsonify({'error': 'Cantidad de filas inválida.'}), 400

    if not create_table_sql:
        return jsonify({'error': 'Debe proporcionar un script CREATE TABLE válido.'}), 400

    def _format_size(bytes_value):
        if bytes_value < 1024:
            return f"{bytes_value} Bytes"
        if bytes_value < 1024 ** 2:
            return f"{bytes_value / 1024:.2f} KB"
        if bytes_value < 1024 ** 3:
            return f"{bytes_value / (1024 ** 2):.2f} MB"
        return f"{bytes_value / (1024 ** 3):.2f} GB"

    def _clean_sql(sql_text):
        sql_text = re.sub(r'/\*.*?\*/', '', sql_text, flags=re.S)
        sql_text = re.sub(r'--.*?$', '', sql_text, flags=re.M)
        return sql_text.strip()

    def _split_column_definitions(columns_text):
        parts = []
        buffer = []
        depth = 0
        in_single = False
        in_double = False
        escape = False

        for char in columns_text:
            if escape:
                buffer.append(char)
                escape = False
                continue

            if char == '\\':
                buffer.append(char)
                escape = True
                continue

            if char == "'" and not in_double:
                in_single = not in_single
            elif char == '"' and not in_single:
                in_double = not in_double
            elif not in_single and not in_double:
                if char == '(':
                    depth += 1
                elif char == ')':
                    depth = max(depth - 1, 0)
                elif char == ',' and depth == 0:
                    parts.append(''.join(buffer).strip())
                    buffer = []
                    continue

            buffer.append(char)

        if buffer:
            parts.append(''.join(buffer).strip())

        return [part for part in parts if part]

    def _infer_column_type(column_name, sample_value, column_type_token):
        if column_name.strip().lower() == 'id':
            return 'INT PRIMARY KEY', 4

        token = column_type_token.strip().upper()
        varchar_match = re.match(r'VARCHAR\s*\(\s*(\d+)\s*\)', token, flags=re.I)
        char_match = re.match(r'CHAR\s*\(\s*(\d+)\s*\)', token, flags=re.I)
        if varchar_match:
            length = int(varchar_match.group(1))
            return f'VARCHAR({length})', length + 2
        if char_match:
            length = int(char_match.group(1))
            return f'CHAR({length})', length + 2

        if token in ('INT', 'INTEGER'):
            return 'INT', 4
        if token == 'BIGINT':
            return 'BIGINT', 8
        if token == 'SMALLINT':
            return 'SMALLINT', 2
        if token == 'BOOLEAN':
            return 'BOOLEAN', 1
        if token == 'DATE':
            return 'DATE', 3
        if token in ('DATETIME', 'TIMESTAMP'):
            return 'DATETIME', 8
        if token == 'FLOAT':
            return 'FLOAT', 4
        if token == 'DOUBLE':
            return 'DOUBLE', 8
        if token == 'TEXT':
            return 'TEXT', 100

        if str(sample_value).strip().lower() in ('true', 'false'):
            return 'BOOLEAN', 1
        if str(sample_value).strip().isdigit():
            return 'INT', 4

        return 'VARCHAR(100)', 102

    try:
        cleaned_sql = _clean_sql(create_table_sql)
        match = re.search(r'CREATE\s+TABLE\s+[^(]+\((.*)\)\s*;', cleaned_sql, flags=re.IGNORECASE | re.DOTALL)
        if not match:
            return jsonify({'error': 'No se encontró un bloque CREATE TABLE válido.'}), 400

        columns_text = match.group(1)
        column_lines = _split_column_definitions(columns_text)
        if not column_lines:
            return jsonify({'error': 'No se pudieron extraer columnas del CREATE TABLE.'}), 400

        parsed_columns = []
        for line in column_lines:
            clean_line = line.rstrip(',').strip()
            if not clean_line:
                continue
            if re.match(r'^(PRIMARY|FOREIGN|UNIQUE|CHECK|CONSTRAINT|KEY|INDEX)\b', clean_line, flags=re.IGNORECASE):
                continue

            parts = clean_line.split()
            if len(parts) < 2:
                continue

            name = parts[0].strip('`"[]')
            type_token = parts[1]
            if len(parts) > 2 and re.match(r'[A-Za-z]+\s*\(', ' '.join(parts[1:3]), flags=re.I):
                type_token = ' '.join(parts[1:3])

            sample_value = ''
            if len(column_lines) > 1:
                sample_value = ''

            column_type, size_bytes = _infer_column_type(name, sample_value, type_token)
            parsed_columns.append({
                'name': name,
                'type': column_type,
                'bytes': size_bytes,
            })

        if not parsed_columns:
            return jsonify({'error': 'No se encontraron columnas válidas en el CREATE TABLE.'}), 400

        row_bytes = sum(col['bytes'] for col in parsed_columns) + 20
        total_bytes = int((row_bytes * row_count) * 1.15)

        result_columns = [
            {
                'name': col['name'],
                'type': col['type'],
                'formatted_size': _format_size(col['bytes']),
            }
            for col in parsed_columns
        ]

        result = {
            'rows': row_count,
            'row_size': {
                'bytes': row_bytes,
                'formatted': _format_size(row_bytes),
            },
            'total_size': {
                'bytes': total_bytes,
                'formatted': _format_size(total_bytes),
            },
            'columns': result_columns,
        }

        return jsonify({'result': result}), 200
    except Exception as exc:
        return jsonify({'error': f'Error al calcular tamaño: {str(exc)}'}), 500
