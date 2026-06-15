import re

def _format_size(bytes_value):
    if bytes_value < 1024:
        return f"{bytes_value} B"
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
    parts, buffer = [], []
    depth = 0
    in_single, in_double, escape = False, False, False

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

def _infer_column_type(column_name, type_token):
    if column_name.strip().lower() == 'id':
        return 'INT PRIMARY KEY', 4

    token = type_token.strip().upper()
    varchar_match = re.match(r'VARCHAR\s*\(\s*(\d+)\s*\)', token, flags=re.I)
    char_match = re.match(r'CHAR\s*\(\s*(\d+)\s*\)', token, flags=re.I)
    
    if varchar_match:
        length = int(varchar_match.group(1))
        return f'VARCHAR({length})', length + 2
    if char_match:
        length = int(char_match.group(1))
        return f'CHAR({length})', length + 2

    if token in ('INT', 'INTEGER', 'FLOAT'):
        return token, 4
    if token in ('BIGINT', 'DATETIME', 'TIMESTAMP', 'DOUBLE'):
        return token, 8
    if token == 'SMALLINT':
        return 'SMALLINT', 2
    if token in ('BOOLEAN', 'TINYINT'):
        return 'BOOLEAN', 1
    if token == 'DATE':
        return 'DATE', 3
    if token == 'TEXT':
        return 'TEXT', 100

    return 'VARCHAR(100)', 102 # Default fallback

def calculate_table_size(rows: int, create_table_sql: str) -> dict:
    cleaned_sql = _clean_sql(create_table_sql)
    match = re.search(r'CREATE\s+TABLE\s+[^(]+\((.*)\)\s*;?', cleaned_sql, flags=re.IGNORECASE | re.DOTALL)
    
    if not match:
        raise ValueError("No se encontró un bloque CREATE TABLE válido.")

    columns_text = match.group(1)
    column_lines = _split_column_definitions(columns_text)
    
    if not column_lines:
        raise ValueError("No se pudieron extraer columnas del script.")

    parsed_columns = []
    for line in column_lines:
        clean_line = line.rstrip(',').strip()
        if not clean_line or re.match(r'^(PRIMARY|FOREIGN|UNIQUE|CHECK|CONSTRAINT|KEY|INDEX)\b', clean_line, flags=re.IGNORECASE):
            continue

        parts = clean_line.split()
        if len(parts) < 2:
            continue

        name = parts[0].strip('`"[]')
        type_token = parts[1]
        if len(parts) > 2 and re.match(r'[A-Za-z]+\s*\(', ' '.join(parts[1:3]), flags=re.I):
            type_token = ' '.join(parts[1:3])

        column_type, size_bytes = _infer_column_type(name, type_token)
        parsed_columns.append({
            'name': name,
            'type': column_type,
            'bytes': size_bytes,
            'formatted_size': _format_size(size_bytes)
        })

    if not parsed_columns:
        raise ValueError("No se encontraron columnas válidas para calcular.")

    # 20 bytes de overhead por fila es un estándar aproximado en motores como InnoDB
    row_bytes = sum(col['bytes'] for col in parsed_columns) + 20 
    total_bytes = int((row_bytes * rows) * 1.15) # 15% extra por fragmentación e índices base

    return {
        'rows': rows,
        'row_size': {'bytes': row_bytes, 'formatted': _format_size(row_bytes)},
        'total_size': {'bytes': total_bytes, 'formatted': _format_size(total_bytes)},
        'columns': parsed_columns
    }