import csv
import io
import re

def _infer_column_type(column_name: str, values: list) -> str:
    """Infiere el tipo de dato SQL analizando una muestra de valores de la columna."""
    if column_name.strip().lower() == 'id':
        return 'INT PRIMARY KEY'

    vals = [v.strip() for v in values if v.strip()]
    if not vals:
        return 'VARCHAR(255)'

    is_int = True
    is_float = True
    is_bool = True
    is_date = True
    max_len = 0

    for v in vals:
        max_len = max(max_len, len(v))
        # Comprobar si es entero
        if is_int and not (v.isdigit() or (v.startswith('-') and v[1:].isdigit())):
            is_int = False
        # Comprobar si es decimal
        if is_float:
            try: 
                float(v)
            except ValueError: 
                is_float = False
        # Comprobar si es booleano
        if is_bool and v.lower() not in ('true', 'false', '1', '0', 'verdadero', 'falso'):
            is_bool = False
        # Comprobar si es fecha (YYYY-MM-DD o YYYY-MM-DD HH:MM:SS)
        if is_date and not re.match(r'^\d{4}-\d{2}-\d{2}( \d{2}:\d{2}:\d{2})?$', v):
            is_date = False

    if is_bool: return 'BOOLEAN'
    if is_int: return 'INT'
    if is_float: return 'DECIMAL(10, 2)'
    if is_date: return 'TIMESTAMP' if ':' in vals[0] else 'DATE'
    
    # Asignar un VARCHAR dinámico basado en la longitud máxima encontrada
    varchar_length = max(255, ((max_len // 50) + 1) * 50) 
    return f'VARCHAR({varchar_length})'

def process_csv_to_sql(table_name: str, csv_data: str) -> dict:
    reader = csv.reader(io.StringIO(csv_data.strip()))
    rows = [row for row in reader if any(cell.strip() for cell in row)]

    if not rows:
        raise ValueError("El CSV está vacío o no contiene datos válidos.")

    # Detección de cabeceras
    def _looks_like_header(row):
        cleaned = [cell.strip() for cell in row if cell.strip()]
        return bool(cleaned) and all(re.match(r'^[A-Za-z_][A-Za-z0-9_]*$', cell) for cell in cleaned)

    if len(rows) == 1 or not _looks_like_header(rows[0]):
        headers = [f'col_{i+1}' for i in range(len(rows[0]))]
        data_rows = rows
    else:
        headers = [h.strip().replace(" ", "_").lower() for h in rows[0]]
        data_rows = rows[1:]

    # Extraer columnas completas para inferir tipos correctamente
    column_types = []
    schema_info = []
    
    for col_idx, header in enumerate(headers):
        column_values = [row[col_idx] for row in data_rows if col_idx < len(row)]
        sql_type = _infer_column_type(header, column_values)
        column_types.append(sql_type)
        schema_info.append({"column": header, "type": sql_type})

    # Generación de SQL
    lines = [f"-- Script autogenerado para la tabla: {table_name}", 
             f"-- Total de registros: {len(data_rows)}", ""]
    
    lines.append(f"CREATE TABLE IF NOT EXISTS {table_name} (")
    col_defs = [f"    {h} {t}" for h, t in zip(headers, column_types)]
    lines.append(",\n".join(col_defs))
    lines.append(");\n")

    for row in data_rows:
        values = []
        for i, value in enumerate(row):
            value = value.strip()
            col_type = column_types[i] if i < len(column_types) else 'VARCHAR(255)'
            
            if value == '' or value.lower() == 'null':
                values.append('NULL')
            elif 'INT' in col_type or 'DECIMAL' in col_type or 'BOOLEAN' in col_type:
                values.append(value)
            else:
                safe_value = value.replace("'", "''")
                values.append(f"'{safe_value}'")

        values_line = ', '.join(values)
        lines.append(f"INSERT INTO {table_name} ({', '.join(headers)}) VALUES ({values_line});")

    return {
        "sql": '\n'.join(lines),
        "stats": {"rows": len(data_rows), "columns": len(headers)},
        "schema": schema_info
    }