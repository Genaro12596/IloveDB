from flask import Blueprint, render_template, request, jsonify
import re

normalization_bp = Blueprint('normalization', __name__, url_prefix='')

@normalization_bp.route('/normalization', methods=['GET'])
def normalization_page():
    return render_template('normalization.html')

@normalization_bp.route('/api/normalization', methods=['POST'])
def normalization_api():
    data = request.get_json() or {}
    create_table_sql = (data.get('create_table_sql') or '').strip()

    if not create_table_sql:
        return jsonify({'error': 'Debe proporcionar un script CREATE TABLE válido.'}), 400

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

    def _normalize_table_name(name):
        lower = name.lower()
        if lower.endswith('es'):
            return lower[:-2]
        if lower.endswith('s'):
            return lower[:-1]
        return lower

    def _parse_create_table(sql_text):
        cleaned = _clean_sql(sql_text)
        match = re.search(r'CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?[`\"]?(\w+)[`\"]?\s*\((.*)\)\s*;?$', cleaned, flags=re.IGNORECASE | re.DOTALL)
        if not match:
            return None

        table_name = match.group(1)
        columns_text = match.group(2)
        column_lines = _split_column_definitions(columns_text)
        if not column_lines:
            return None

        columns = []
        primary_keys = []

        for line in column_lines:
            clean_line = line.rstrip(',').strip()
            if not clean_line:
                continue

            constraint_match = re.match(r'PRIMARY\s+KEY\s*\(([^)]+)\)', clean_line, flags=re.IGNORECASE)
            if constraint_match:
                keys = [k.strip(' `"[]').strip() for k in constraint_match.group(1).split(',') if k.strip()]
                primary_keys.extend([k.lower() for k in keys])
                continue

            if re.match(r'^(FOREIGN|UNIQUE|CHECK|CONSTRAINT|KEY|INDEX)\b', clean_line, flags=re.IGNORECASE):
                continue

            parts = re.split(r'\s+', clean_line, maxsplit=2)
            if not parts:
                continue

            column_name = parts[0].strip('`"[]')
            columns.append(column_name)

            if re.search(r'PRIMARY\s+KEY\b', clean_line, flags=re.IGNORECASE):
                primary_keys.append(column_name.lower())

        return {
            'table_name': table_name,
            'columns': [col.lower() for col in columns],
            'primary_keys': list(dict.fromkeys(primary_keys)),
        }

    try:
        parsed = _parse_create_table(create_table_sql)
        if not parsed:
            return jsonify({'error': 'No se encontró un bloque CREATE TABLE válido.'}), 400

        table_name = parsed['table_name'].lower()
        primary_keys = parsed['primary_keys']
        columns = parsed['columns']

        is_1fn = bool(primary_keys)
        if not is_1fn:
            return jsonify({'result': {
                '1fn': {'status': 'FALLA', 'detail': 'No se encontró una clave primaria en el CREATE TABLE.'},
                '2fn': {'status': 'FALLA', 'detail': 'Sin clave primaria válida no se puede evaluar 2FN.'},
                '3fn': {'status': 'FALLA', 'detail': 'Sin 1FN y 2FN válidas no se puede evaluar 3FN.'}
            }}), 200

        is_2fn = len(primary_keys) == 1
        if is_2fn:
            status_2fn = 'CUMPLE'
            detail_2fn = 'La tabla tiene una clave primaria simple, por lo que se asume una clave atómica para 2FN.'
        else:
            status_2fn = 'FALLA'
            detail_2fn = 'Se detectó una clave primaria compuesta. Esto indica posible dependencia parcial y falla 2FN.'

        table_singular = _normalize_table_name(table_name)
        smell_prefixes = set()
        for col in columns:
            if '_' not in col:
                continue
            prefix = col.split('_', 1)[0].lower()
            if prefix in ('id', table_name, table_singular) or prefix == '':
                continue
            smell_prefixes.add(prefix)

        if not is_2fn:
            status_3fn = 'FALLA'
            detail_3fn = 'No se puede evaluar 3FN porque 2FN no se cumple.'
        elif smell_prefixes:
            status_3fn = 'ADVERTENCIA'
            prefixes = ', '.join(sorted(smell_prefixes))
            detail_3fn = f'Se detectaron prefijos de columna como {prefixes} que pueden corresponder a otras tablas. Revisa si esas columnas pertenecen a entidades separadas.'
        else:
            status_3fn = 'CUMPLE'
            detail_3fn = 'No se detectaron olores de dependencia transitiva en los nombres de columna.'

        return jsonify({'result': {
            '1fn': {'status': 'CUMPLE', 'detail': 'Existe una clave primaria definida en la tabla.'},
            '2fn': {'status': status_2fn, 'detail': detail_2fn},
            '3fn': {'status': status_3fn, 'detail': detail_3fn},
        }}), 200

    except Exception as exc:
        # Esto atrapará el error 500 y te dirá exactamente qué falló
        return jsonify({'error': f'Error interno procesando SQL: {str(exc)}'}), 500
