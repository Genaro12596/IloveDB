import re
from flask import Blueprint, render_template, request, jsonify

generator_bp = Blueprint('generator', __name__, url_prefix='')

@generator_bp.route('/generator', methods=['GET'])
def generator_page():
    return render_template('generator.html')

def parse_create_table(sql):
    sql = sql.strip()
    table_match = re.search(r'CREATE\s+TABLE\s+(\w+)\s*\((.*)\)', sql, re.IGNORECASE | re.DOTALL)
    
    if not table_match:
        raise ValueError('CREATE TABLE no válido')
    
    table_name = table_match.group(1)
    columns_raw = table_match.group(2)
    
    columns = []
    pk_col = None
    paren_depth = 0
    current_col = []
    
    for char in columns_raw:
        if char == '(':
            paren_depth += 1
            current_col.append(char)
        elif char == ')':
            paren_depth -= 1
            current_col.append(char)
        elif char == ',' and paren_depth == 0:
            col_def = ''.join(current_col).strip()
            if col_def:
                parts = col_def.split()
                col_name = parts[0] if parts else None
                if col_name:
                    if 'PRIMARY' in col_def.upper() or 'KEY' in col_def.upper():
                        pk_col = col_name
                    columns.append(col_name)
            current_col = []
        else:
            current_col.append(char)
    
    if current_col:
        col_def = ''.join(current_col).strip()
        if col_def:
            parts = col_def.split()
            col_name = parts[0] if parts else None
            if col_name:
                if 'PRIMARY' in col_def.upper() or 'KEY' in col_def.upper():
                    pk_col = col_name
                columns.append(col_name)
    
    if not pk_col and columns:
        pk_col = columns[0]
    
    if not columns:
        raise ValueError('No se encontraron columnas')
    
    return table_name, columns, pk_col

def generate_crud(table_name, columns, pk_col):
    non_pk_cols = [c for c in columns if c != pk_col]
    cols_str = ', '.join(columns)
    non_pk_str = ', '.join(non_pk_cols)
    
    placeholders = ', '.join([f"'{c}'" for c in columns])
    set_clause = ', '.join([f"{c} = '{c}_value'" for c in non_pk_cols])
    
    create_sql = f"INSERT INTO {table_name} ({cols_str}) VALUES ({placeholders});"
    read_sql = f"SELECT {cols_str} FROM {table_name} WHERE {pk_col} = [valor];"
    update_sql = f"UPDATE {table_name} SET {set_clause} WHERE {pk_col} = [valor];"
    delete_sql = f"DELETE FROM {table_name} WHERE {pk_col} = [valor];"
    
    explanations = {
        'create': 'INSERT añade nuevos registros a la tabla. Especifica todas las columnas y sus valores correspondientes. Es la operación que crea nuevos datos.',
        'read': 'SELECT recupera datos existentes. Usa WHERE para filtrar. Sin WHERE devolverá todos los registros. Es la operación que lee datos.',
        'update': 'UPDATE modifica registros existentes. CRÍTICO: siempre incluye WHERE, sino modificarás todos los registros. SET define qué columnas cambiar.',
        'delete': 'DELETE elimina registros. CRÍTICO: siempre incluye WHERE para no borrar toda la tabla. Sin WHERE, se eliminan TODOS los datos.'
    }
    
    return {
        'create': {'sql': create_sql, 'explanation': explanations['create']},
        'read': {'sql': read_sql, 'explanation': explanations['read']},
        'update': {'sql': update_sql, 'explanation': explanations['update']},
        'delete': {'sql': delete_sql, 'explanation': explanations['delete']}
    }

@generator_bp.route('/api/generate-crud', methods=['POST'])
def generate_crud_api():
    data = request.get_json() or {}
    sql_input = (data.get('create_table_sql') or '').strip()
    
    if not sql_input:
        return jsonify({'error': 'Proporciona un CREATE TABLE válido'}), 400
    
    try:
        table_name, columns, pk_col = parse_create_table(sql_input)
        crud_result = generate_crud(table_name, columns, pk_col)
        return jsonify(crud_result), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 400

