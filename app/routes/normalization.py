from flask import Blueprint, render_template, request, jsonify
import re

normalization_bp = Blueprint('normalization', __name__, url_prefix='')

@normalization_bp.route('/normalization', methods=['GET'])
def normalization_page():
    return render_template('normalization.html')


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


def _guess_prefix_groups(columns):
    groups = {}
    for col in columns:
        if '_' not in col:
            continue
        prefix = col.split('_', 1)[0].lower()
        if prefix in ('id', ''):
            continue
        groups.setdefault(prefix, []).append(col)
    return groups


def _guess_column_type(column_name):
    if column_name.endswith('_id') or column_name == 'id':
        return 'INT'
    if column_name.startswith('is_') or column_name.startswith('has_'):
        return 'BOOLEAN'
    if any(keyword in column_name for keyword in ('fecha', 'date', 'hora', 'time')):
        return 'DATETIME'
    return 'VARCHAR(255)'


def _build_normalized_sql(table_name, primary_keys, columns):
    groups = _guess_prefix_groups(columns)
    if not groups:
        return None

    pk_column = primary_keys[0] if primary_keys else None
    normalized_sql = []

    normalized_sql.append(f'CREATE TABLE {table_name} (')
    if pk_column:
        normalized_sql.append(f'    {pk_column} INT PRIMARY KEY,')

    main_columns = [col for col in columns if all(not col.startswith(f'{prefix}_') for prefix in groups)]
    for col in main_columns:
        if col == pk_column:
            continue
        normalized_sql.append(f'    {col} {_guess_column_type(col)},')

    for prefix in groups:
        fk_name = f'{prefix}_id'
        if fk_name not in columns:
            normalized_sql.append(f'    {fk_name} INT NOT NULL,')

    if normalized_sql[-1].endswith(','):
        normalized_sql[-1] = normalized_sql[-1].rstrip(',')
    normalized_sql.append(');\n')

    for prefix, prefix_columns in groups.items():
        normalized_sql.append(f'CREATE TABLE {prefix}s (')
        normalized_sql.append(f'    {prefix}_id INT PRIMARY KEY,')
        for col in prefix_columns:
            if col == f'{prefix}_id':
                continue
            normalized_sql.append(f'    {col} {_guess_column_type(col)},')
        if normalized_sql[-1].endswith(','):
            normalized_sql[-1] = normalized_sql[-1].rstrip(',')
        normalized_sql.append(');\n')

    return '\n'.join(normalized_sql)


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

        column_name = parts[0].strip('`"[]').lower()
        columns.append(column_name)

        if re.search(r'PRIMARY\s+KEY\b', clean_line, flags=re.IGNORECASE):
            primary_keys.append(column_name)

    return {
        'table_name': table_name,
        'columns': columns,
        'primary_keys': list(dict.fromkeys(primary_keys)),
    }


@normalization_bp.route('/api/normalization', methods=['POST'])
def normalization_api():
    data = request.get_json() or {}
    create_table_sql = (data.get('create_table_sql') or '').strip()

    if not create_table_sql:
        return jsonify({'error': 'Debe proporcionar un script CREATE TABLE válido.'}), 400

    try:
        parsed = _parse_create_table(create_table_sql)
        if not parsed:
            return jsonify({'error': 'No se encontró un bloque CREATE TABLE válido.'}), 400

        table_name = parsed['table_name'].lower()
        primary_keys = parsed['primary_keys']
        columns = parsed['columns']

        has_primary_key = bool(primary_keys)
        is_1fn = has_primary_key
        is_2fn = len(primary_keys) == 1
        prefix_groups = _guess_prefix_groups(columns)
        repeated_prefixes = sorted(prefix_groups.keys())

        if not is_1fn:
            status_1fn = 'FALLA'
            detail_1fn = 'No se encontró clave primaria. Una tabla normalizada requiere un identificador único.'
        else:
            status_1fn = 'CUMPLE'
            detail_1fn = 'Clave primaria detectada. Se cumple el requerimiento básico de 1FN.'

        if is_2fn:
            status_2fn = 'CUMPLE'
            detail_2fn = 'Clave primaria simple. 2FN se considera válida a nivel de diseño básico.'
        else:
            status_2fn = 'FALLA'
            detail_2fn = 'Clave primaria compuesta o ausente. Esto puede introducir dependencias parciales.'

        if not is_2fn:
            status_3fn = 'FALLA'
            detail_3fn = '2FN no se cumple, por lo que 3FN no puede evaluarse correctamente.'
        elif repeated_prefixes:
            status_3fn = 'ADVERTENCIA'
            detail_3fn = f'Se detectaron entidades relacionadas: {", ".join(repeated_prefixes)}. Revisa posibles dependencias transitivas.'
        else:
            status_3fn = 'CUMPLE'
            detail_3fn = 'No se detectaron dependencias transitivas obvias en los nombres de columna.'

        if status_3fn == 'CUMPLE' and not repeated_prefixes:
            status_bcnf = 'CUMPLE'
            detail_bcnf = 'El diseño parece alineado con BCNF para las dependencias detectadas.'
        elif not is_2fn:
            status_bcnf = 'FALLA'
            detail_bcnf = 'BCNF no es aplicable si no se cumple 2FN.'
        else:
            status_bcnf = 'ADVERTENCIA'
            detail_bcnf = 'Puede haber determinantes que no sean claves candidatas. Revisa las tablas derivadas sugeridas.'

        recommendations = []
        if not has_primary_key:
            recommendations.append('Define una clave primaria clara para esta tabla.')
        if repeated_prefixes:
            recommendations.append('Extrae entidades relacionadas en tablas separadas según los prefijos detectados.')
            recommendations.append('Evita almacenar datos de cliente/producto/dirección en la misma tabla de transacción.')
        else:
            recommendations.append('Verifica que no existan dependencias ocultas entre columnas que no comparten prefijos.')
        recommendations.append('Aplica índices a columnas de búsqueda frecuente y a claves foráneas.')

        dependencies = []
        for prefix, related_columns in prefix_groups.items():
            dependencies.append({
                'entity': prefix,
                'columns': related_columns,
                'recommendation': f'Considere una tabla {prefix}s con clave primaria {prefix}_id.'
            })

        normalized_sql = _build_normalized_sql(table_name, primary_keys, columns)
        if not normalized_sql:
            normalized_sql = '-- No se detectó un patrón claro para generar SQL normalizado automáticamente.'

        return jsonify({
            'result': {
                '1fn': {'status': status_1fn, 'detail': detail_1fn},
                '2fn': {'status': status_2fn, 'detail': detail_2fn},
                '3fn': {'status': status_3fn, 'detail': detail_3fn},
                'bcnf': {'status': status_bcnf, 'detail': detail_bcnf},
                'statistics': {
                    'column_count': len(columns),
                    'primary_key_count': len(primary_keys),
                    'detected_entities': len(prefix_groups),
                    'entity_names': repeated_prefixes,
                },
                'recommendations': recommendations,
                'dependencies': dependencies,
                'normalized_sql': normalized_sql,
            }
        }), 200

    except Exception as processing_error:
        return jsonify({'error': f'Error interno procesando SQL: {str(processing_error)}'}), 500
