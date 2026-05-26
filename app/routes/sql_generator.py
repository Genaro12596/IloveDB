import io
import re
import zipfile
from typing import List, Dict, Any
from flask import Blueprint, render_template, request, jsonify, send_file

generator_bp = Blueprint('generator', __name__, url_prefix='')

TARGET_LABELS = {
    'sql': 'SQL puro',
    'php': 'PHP',
    'node-express': 'Node.js + Express',
    'flask': 'Python + Flask',
    'java-spring': 'Java + Spring Boot',
}

ARCHITECTURE_LABELS = {
    'rest_api': 'API REST',
    'mvc': 'MVC ligera',
}


@generator_bp.route('/generator', methods=['GET'])
def generator_page():
    return render_template('generator.html')


def _clean_sql(sql_text: str) -> str:
    sql_text = re.sub(r'/\*.*?\*/', '', sql_text, flags=re.S)
    sql_text = re.sub(r'--.*?$', '', sql_text, flags=re.M)
    return sql_text.strip()


def _split_column_definitions(columns_text: str) -> List[str]:
    parts: List[str] = []
    buffer: List[str] = []
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
                part = ''.join(buffer).strip()
                if part:
                    parts.append(part)
                buffer = []
                continue

        buffer.append(char)

    if buffer:
        part = ''.join(buffer).strip()
        if part:
            parts.append(part)

    return parts


def _normalize_type(column_type: str) -> str:
    return re.sub(r'\s+', ' ', column_type.strip())


def _parse_column_definition(line: str) -> Dict[str, Any]:
    line = line.strip().rstrip(',')
    if not line:
        return {}

    fk_match = re.search(r'FOREIGN\s+KEY\s*\(([^)]+)\)\s+REFERENCES\s+([\w`".]+)\s*\(([^)]+)\)', line, flags=re.IGNORECASE)
    pk_match = re.match(r'PRIMARY\s+KEY\s*\(([^)]+)\)', line, flags=re.IGNORECASE)
    if fk_match:
        return {
            'constraint': 'foreign_key',
            'columns': [col.strip(' `"[]') for col in fk_match.group(1).split(',')],
            'references': {
                'table': fk_match.group(2).strip(' `"[]'),
                'columns': [col.strip(' `"[]') for col in fk_match.group(3).split(',')]
            }
        }
    if pk_match:
        return {
            'constraint': 'primary_key',
            'columns': [col.strip(' `"[]') for col in pk_match.group(1).split(',')]
        }

    parts = re.split(r'\s+', line, maxsplit=2)
    column_name = parts[0].strip('`"[]') if parts else ''
    column_type = parts[1] if len(parts) > 1 else 'TEXT'
    raw_constraints = parts[2] if len(parts) > 2 else ''
    nullable = not bool(re.search(r'NOT\s+NULL', raw_constraints, flags=re.IGNORECASE))
    primary_key = bool(re.search(r'PRIMARY\s+KEY', raw_constraints, flags=re.IGNORECASE))
    unique = bool(re.search(r'UNIQUE', raw_constraints, flags=re.IGNORECASE))
    auto_increment = bool(re.search(r'AUTO_INCREMENT|AUTOINCREMENT', raw_constraints, flags=re.IGNORECASE))
    default_match = re.search(r'DEFAULT\s+([^\s,]+)', raw_constraints, flags=re.IGNORECASE)
    default = default_match.group(1) if default_match else None

    reference_match = re.search(r'REFERENCES\s+([\w`".]+)\s*\(([^)]+)\)', raw_constraints, flags=re.IGNORECASE)
    foreign_key = None
    if reference_match:
        foreign_key = {
            'table': reference_match.group(1).strip(' `"[]'),
            'column': reference_match.group(2).strip(' `"[]')
        }

    return {
        'name': column_name,
        'type': _normalize_type(column_type),
        'nullable': nullable,
        'primary_key': primary_key,
        'unique': unique,
        'auto_increment': auto_increment,
        'default': default,
        'foreign_key': foreign_key,
        'raw': line,
    }


def _parse_create_table(sql_text: str) -> Dict[str, Any]:
    cleaned = _clean_sql(sql_text)
    match = re.search(r'CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?[`"]?(\w+)[`"]?\s*\((.*)\)\s*;?$', cleaned, flags=re.IGNORECASE | re.DOTALL)
    if not match:
        raise ValueError('CREATE TABLE no válido')

    table_name = match.group(1)
    columns_text = match.group(2)
    column_lines = _split_column_definitions(columns_text)
    if not column_lines:
        raise ValueError('No se encontraron columnas en la tabla')

    columns: List[Dict[str, Any]] = []
    primary_keys: List[str] = []
    foreign_keys: List[Dict[str, Any]] = []

    for line in column_lines:
        definition = _parse_column_definition(line)
        if not definition:
            continue

        constraint = definition.get('constraint')
        if constraint == 'primary_key':
            primary_keys.extend(definition['columns'])
            continue
        if constraint == 'foreign_key':
            foreign_keys.append({
                'columns': definition['columns'],
                'references': definition['references']
            })
            continue

        if definition.get('primary_key'):
            primary_keys.append(definition['name'])

        if definition.get('foreign_key'):
            foreign_keys.append({
                'columns': [definition['name']],
                'references': definition['foreign_key']
            })

        columns.append(definition)

    if not primary_keys and columns:
        primary_keys.append(columns[0]['name'])
        columns[0]['primary_key'] = True

    return {
        'table_name': table_name,
        'columns': columns,
        'primary_keys': primary_keys,
        'foreign_keys': foreign_keys,
    }


def _build_model_name(table_name: str) -> str:
    singular = table_name.capitalize()
    if singular.endswith('s'):
        singular = singular[:-1]
    return ''.join(part.capitalize() for part in singular.split('_'))


def _build_flask_column_type(column_type: str) -> str:
    lower = column_type.lower()
    if 'int' in lower:
        return 'Integer'
    if 'char' in lower or 'text' in lower:
        return 'String(255)'
    if 'date' in lower or 'time' in lower:
        return 'DateTime'
    if 'bool' in lower:
        return 'Boolean'
    if 'decimal' in lower or 'numeric' in lower or 'float' in lower:
        return 'Float'
    return 'String(255)'


def _build_flask_field(col: Dict[str, Any]) -> str:
    parts = [f"    {col['name']} = db.Column(db.{_build_flask_column_type(col['type'])}" ]
    if col['primary_key']:
        parts.append(', primary_key=True')
    if not col['nullable']:
        parts.append(', nullable=False')
    if col['unique']:
        parts.append(', unique=True')
    if col['default']:
        parts.append(f", default={col['default']}")
    parts.append(')')
    return ''.join(parts)


def _build_java_field(col: Dict[str, Any]) -> str:
    java_type = 'String'
    lower = col['type'].lower()
    if 'int' in lower:
        java_type = 'Long'
    elif 'double' in lower or 'float' in lower or 'decimal' in lower:
        java_type = 'Double'
    elif 'bool' in lower:
        java_type = 'Boolean'
    elif 'date' in lower or 'time' in lower:
        java_type = 'LocalDateTime'

    annotations = []
    if col['primary_key']:
        annotations.append('    @Id')
        annotations.append('    @GeneratedValue(strategy = GenerationType.IDENTITY)')
    annotations.append(f'    @Column(name = "{col["name"]}")')
    field_name = col['name']
    return '\n'.join(annotations) + f'\n    private {java_type} {field_name};\n'


def _build_java_setter_name(column_name: str) -> str:
    words = column_name.split('_')
    if not words:
        return 'setId'
    return 'set' + ''.join(word.capitalize() for word in words)


def _generate_sql_crud(schema: Dict[str, Any]) -> List[Dict[str, str]]:
    table = schema['table_name']
    columns = schema['columns']
    if not columns:
        raise ValueError('No se encontraron columnas válidas')

    pk = schema['primary_keys'][0]
    column_names = [col['name'] for col in columns]
    update_columns = [col for col in column_names if col != pk]
    insert_columns = ', '.join(column_names)
    insert_values = ', '.join([f':{col}' for col in column_names])
    update_assignments = ', '.join([f'{col} = :{col}' for col in update_columns])

    content = f"""-- CRUD profesional para la tabla {table}

-- INSERT
INSERT INTO {table} ({insert_columns})
VALUES ({insert_values});

-- READ (paginación y filtros)
SELECT {insert_columns}
FROM {table}
WHERE 1 = 1
  -- Agrega filtros aquí: AND {column_names[1]} = :{column_names[1]}
ORDER BY {pk} DESC
LIMIT :limit OFFSET :offset;

-- UPDATE
UPDATE {table}
SET {update_assignments}
WHERE {pk} = :{pk};

-- DELETE
DELETE FROM {table}
WHERE {pk} = :{pk};
"""

    return [{'name': 'crud_queries.sql', 'content': content}]


def _generate_php_crud(schema: Dict[str, Any], architecture: str) -> List[Dict[str, str]]:
    table = schema['table_name']
    model_name = _build_model_name(table)
    pk = schema['primary_keys'][0]
    columns = schema['columns']
    insert_columns = ', '.join([col['name'] for col in columns])
    insert_placeholders = ', '.join([f':{col["name"]}' for col in columns])
    update_assignments = ', '.join([f'{col["name"]} = :{col["name"]}' for col in columns if col['name'] != pk])
    select_columns = ', '.join([col['name'] for col in columns])

    db_code = f"""<?php
class Database
{{
    private $pdo;

    public function __construct($dsn, $user, $password)
    {{
        $this->pdo = new PDO($dsn, $user, $password, [
            PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
            PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
        ]);
    }}

    public function getConnection()
    {{
        return $this->pdo;
    }}
}}
"""

    model_code = f"""<?php
require_once 'Database.php';

class {model_name}Model
{{
    private $db;

    public function __construct(Database $database)
    {{
        $this->db = $database->getConnection();
    }}

    public function create(array $data): bool
    {{
        $stmt = $this->db->prepare('INSERT INTO {table} ({insert_columns}) VALUES ({insert_placeholders})');
        return $stmt->execute($data);
    }}

    public function find(int ${pk}): array
    {{
        $stmt = $this->db->prepare('SELECT {select_columns} FROM {table} WHERE {pk} = :{pk}');
        $stmt->execute([':{pk}' => ${pk}]);
        return $stmt->fetch() ?: [];
    }}

    public function update(int ${pk}, array $data): bool
    {{
        $data[':{pk}'] = ${pk};
        $stmt = $this->db->prepare('UPDATE {table} SET {update_assignments} WHERE {pk} = :{pk}');
        return $stmt->execute($data);
    }}

    public function delete(int ${pk}): bool
    {{
        $stmt = $this->db->prepare('DELETE FROM {table} WHERE {pk} = :{pk}');
        return $stmt->execute([':{pk}' => ${pk}]);
    }}

    public function list(int $limit = 20, int $offset = 0): array
    {{
        $stmt = $this->db->prepare('SELECT {select_columns} FROM {table} ORDER BY {pk} DESC LIMIT :limit OFFSET :offset');
        $stmt->bindValue(':limit', $limit, PDO::PARAM_INT);
        $stmt->bindValue(':offset', $offset, PDO::PARAM_INT);
        $stmt->execute();
        return $stmt->fetchAll();
    }}
}}
"""

    controller_code = f"""<?php
require_once 'Database.php';
require_once '{model_name}Model.php';

$database = new Database('mysql:host=localhost;dbname=app_db;charset=utf8mb4', 'user', 'password');
$model = new {model_name}Model($database);
$method = $_SERVER['REQUEST_METHOD'];
$endpoint = $_GET['endpoint'] ?? '';

header('Content-Type: application/json');

try {{
    if ($method === 'GET' && $endpoint === 'list') {{
        echo json_encode(['data' => $model->list((int)($_GET['limit'] ?? 20), (int)($_GET['offset'] ?? 0))]);
        return;
    }}

    if ($method === 'GET' && isset($_GET['{pk}'])) {{
        echo json_encode(['data' => $model->find((int)$_GET['{pk}'])]);
        return;
    }}

    $payload = json_decode(file_get_contents('php://input'), true);

    if ($method === 'POST') {{
        echo json_encode(['success' => $model->create($payload)]);
        return;
    }}

    if ($method === 'PUT' && isset($_GET['{pk}'])) {{
        echo json_encode(['success' => $model->update((int)$_GET['{pk}'], $payload)]);
        return;
    }}

    if ($method === 'DELETE' && isset($_GET['{pk}'])) {{
        echo json_encode(['success' => $model->delete((int)$_GET['{pk}'])]);
        return;
    }}

    http_response_code(400);
    echo json_encode(['error' => 'Solicitud no válida']);
}} catch (PDOException $exception) {{
    http_response_code(500);
    echo json_encode(['error' => $exception->getMessage()]);
}}
"""

    return [
        {'name': 'Database.php', 'content': db_code},
        {'name': f'{model_name}Model.php', 'content': model_code},
        {'name': 'controller.php', 'content': controller_code},
    ]


def _generate_node_express_crud(schema: Dict[str, Any], architecture: str) -> List[Dict[str, str]]:
    table = schema['table_name']
    pk = schema['primary_keys'][0]
    columns = schema['columns']
    column_names = [col['name'] for col in columns]
    select_columns = ', '.join(column_names)
    insert_columns = ', '.join(column_names)
    insert_values = ', '.join(['?' for _ in column_names])
    update_assignments = ', '.join([f"{col} = ?" for col in column_names if col != pk])

    app_code = f"""const express = require('express');
const bodyParser = require('body-parser');
const {table}Router = require('./routes/{table}');

const app = express();
app.use(bodyParser.json());
app.use('/api/{table}', {table}Router);

const port = process.env.PORT || 3000;
app.listen(port, () => {{
  console.log(`API escuchando en http://localhost:${{port}}/api/{table}`);
}});
"""

    route_code = f"""const express = require('express');
const router = express.Router();
const controller = require('../controllers/{table}Controller');

router.get('/', controller.list);
router.get('/:id', controller.find);
router.post('/', controller.create);
router.put('/:id', controller.update);
router.delete('/:id', controller.delete);

module.exports = router;
"""

    controller_code = f"""const model = require('../models/{table}Model');

exports.list = async (req, res) => {{
  const limit = parseInt(req.query.limit, 10) || 20;
  const offset = parseInt(req.query.offset, 10) || 0;
  const result = await model.list(limit, offset);
  res.json({{ data: result }});
}};

exports.find = async (req, res) => {{
  const result = await model.find(req.params.id);
  res.json({{ data: result }});
}};

exports.create = async (req, res) => {{
  const result = await model.create(req.body);
  res.status(201).json({{ success: result }});
}};

exports.update = async (req, res) => {{
  const result = await model.update(req.params.id, req.body);
  res.json({{ success: result }});
}};

exports.delete = async (req, res) => {{
  const result = await model.delete(req.params.id);
  res.json({{ success: result }});
}};
"""

    model_code = f"""const pool = require('../database');

exports.list = async (limit, offset) => {{
  const [rows] = await pool.query(`SELECT {select_columns} FROM {table} ORDER BY {pk} DESC LIMIT ? OFFSET ?`, [limit, offset]);
  return rows;
}};

exports.find = async (id) => {{
  const [rows] = await pool.query(`SELECT {select_columns} FROM {table} WHERE {pk} = ?`, [id]);
  return rows[0] || null;
}};

exports.create = async (data) => {{
  const [result] = await pool.query(
    `INSERT INTO {table} ({insert_columns}) VALUES ({insert_values})`,
    [{', '.join([f'data.{col}' for col in column_names])}]
  );
  return result.affectedRows > 0;
}};

exports.update = async (id, data) => {{
  const [result] = await pool.query(
    `UPDATE {table} SET {update_assignments} WHERE {pk} = ?`,
    [{', '.join([f'data.{col}' for col in column_names if col != pk])}, id]
  );
  return result.affectedRows > 0;
}};

exports.delete = async (id) => {{
  const [result] = await pool.query(`DELETE FROM {table} WHERE {pk} = ?`, [id]);
  return result.affectedRows > 0;
}};
"""

    database_code = """const mysql = require('mysql2/promise');

const pool = mysql.createPool({
  host: 'localhost',
  user: 'root',
  password: 'password',
  database: 'app_db',
});

module.exports = pool;
"""

    return [
        {'name': 'app.js', 'content': app_code},
        {'name': f'routes/{table}.js', 'content': route_code},
        {'name': f'controllers/{table}Controller.js', 'content': controller_code},
        {'name': f'models/{table}Model.js', 'content': model_code},
        {'name': 'database.js', 'content': database_code},
    ]


def _generate_flask_crud(schema: Dict[str, Any], architecture: str) -> List[Dict[str, str]]:
    table = schema['table_name']
    class_name = _build_model_name(table)
    pk = schema['primary_keys'][0]
    columns = schema['columns']
    fields = '\n'.join([_build_flask_field(col) for col in columns])

    model_code = f"""from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class {class_name}(db.Model):
    __tablename__ = '{table}'
{fields}
"""

    routes_code = f"""from flask import Blueprint, request, jsonify
from models import db, {class_name}

bp = Blueprint('{table}', __name__, url_prefix='/{table}')

@bp.route('/', methods=['GET'])
def list_{table}():
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 20))
    query = {class_name}.query.order_by({class_name}.{pk}.desc())
    items = query.paginate(page, per_page, False).items
    return jsonify([item.to_dict() for item in items])

@bp.route('/<int:{pk}>', methods=['GET'])
def get_{table}({pk}):
    item = {class_name}.query.get_or_404({pk})
    return jsonify(item.to_dict())

@bp.route('/', methods=['POST'])
def create_{table}():
    payload = request.json or {{}}
    item = {class_name}(**payload)
    db.session.add(item)
    db.session.commit()
    return jsonify(item.to_dict()), 201

@bp.route('/<int:{pk}>', methods=['PUT'])
def update_{table}({pk}):
    payload = request.json or {{}}
    item = {class_name}.query.get_or_404({pk})
    for key, value in payload.items():
        setattr(item, key, value)
    db.session.commit()
    return jsonify(item.to_dict())

@bp.route('/<int:{pk}>', methods=['DELETE'])
def delete_{table}({pk}):
    item = {class_name}.query.get_or_404({pk})
    db.session.delete(item)
    db.session.commit()
    return jsonify({{'success': True}})
"""

    app_code = f"""from flask import Flask
from models import db
from routes import bp

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
app.register_blueprint(bp)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=5000)
"""

    return [
        {'name': 'models.py', 'content': model_code},
        {'name': 'routes.py', 'content': routes_code},
        {'name': 'app.py', 'content': app_code},
    ]


def _generate_java_spring_crud(schema: Dict[str, Any], architecture: str) -> List[Dict[str, str]]:
    table = schema['table_name']
    entity_name = _build_model_name(table)
    pk = schema['primary_keys'][0]
    fields = '\n'.join([_build_java_field(col) for col in schema['columns']])

    entity_code = f"""package com.example.demo.model;

import javax.persistence.*;

@Entity
@Table(name = \"{table}\")
public class {entity_name} {{
{fields}
}}
"""

    repository_code = f"""package com.example.demo.repository;

import com.example.demo.model.{entity_name};
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

@Repository
public interface {entity_name}Repository extends JpaRepository<{entity_name}, Long> {{
}}
"""

    service_code = f"""package com.example.demo.service;

import com.example.demo.model.{entity_name};
import com.example.demo.repository.{entity_name}Repository;
import org.springframework.stereotype.Service;

import java.util.List;

@Service
public class {entity_name}Service {{

    private final {entity_name}Repository repository;

    public {entity_name}Service({entity_name}Repository repository) {{
        this.repository = repository;
    }}

    public List<{entity_name}> findAll() {{
        return repository.findAll();
    }}

    public {entity_name} findById(Long id) {{
        return repository.findById(id).orElse(null);
    }}

    public {entity_name} save({entity_name} entity) {{
        return repository.save(entity);
    }}

    public void delete(Long id) {{
        repository.deleteById(id);
    }}
}}
"""

    setter_name = _build_java_setter_name(pk)

    controller_code = f"""package com.example.demo.controller;

import com.example.demo.model.{entity_name};
import com.example.demo.service.{entity_name}Service;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping(\"/api/{table}\")
public class {entity_name}Controller {{

    private final {entity_name}Service service;

    public {entity_name}Controller({entity_name}Service service) {{
        this.service = service;
    }}

    @GetMapping
    public List<{entity_name}> list() {{
        return service.findAll();
    }}

    @GetMapping(\"/{id}\")
    public ResponseEntity<{entity_name}> get(@PathVariable Long id) {{
        {entity_name} item = service.findById(id);
        return item != null ? ResponseEntity.ok(item) : ResponseEntity.notFound().build();
    }}

    @PostMapping
    public {entity_name} create(@RequestBody {entity_name} entity) {{
        return service.save(entity);
    }}

    @PutMapping(\"/{id}\")
    public ResponseEntity<{entity_name}> update(@PathVariable Long id, @RequestBody {entity_name} entity) {{
        entity.{setter_name}(id);
        return ResponseEntity.ok(service.save(entity));
    }}

    @DeleteMapping(\"/{id}\")
    public ResponseEntity<Void> delete(@PathVariable Long id) {{
        service.delete(id);
        return ResponseEntity.noContent().build();
    }}
}}
"""

    return [
        {'name': f'model/{entity_name}.java', 'content': entity_code},
        {'name': f'repository/{entity_name}Repository.java', 'content': repository_code},
        {'name': f'service/{entity_name}Service.java', 'content': service_code},
        {'name': f'controller/{entity_name}Controller.java', 'content': controller_code},
    ]


def _generate_code_templates(schema: Dict[str, Any], target: str, architecture: str) -> List[Dict[str, str]]:
    if target == 'php':
        return _generate_php_crud(schema, architecture)
    if target == 'node-express':
        return _generate_node_express_crud(schema, architecture)
    if target == 'flask':
        return _generate_flask_crud(schema, architecture)
    if target == 'java-spring':
        return _generate_java_spring_crud(schema, architecture)
    return _generate_sql_crud(schema)


@generator_bp.route('/api/generate-crud', methods=['POST'])
def generate_crud_api():
    data = request.get_json() or {}
    sql_input = (data.get('create_table_sql') or '').strip()
    target = (data.get('language') or 'sql').strip()
    architecture = (data.get('architecture') or 'rest_api').strip()

    if not sql_input:
        return jsonify({'success': False, 'error': 'Proporciona un CREATE TABLE válido'}), 400

    if target not in TARGET_LABELS:
        target = 'sql'

    if architecture not in ARCHITECTURE_LABELS:
        architecture = 'rest_api'

    try:
        schema = _parse_create_table(sql_input)
        files = _generate_code_templates(schema, target, architecture)
        return jsonify({
            'success': True,
            'target': target,
            'architecture': architecture,
            'target_label': TARGET_LABELS[target],
            'architecture_label': ARCHITECTURE_LABELS[architecture],
            'schema': {
                'table_name': schema['table_name'],
                'primary_keys': schema['primary_keys'],
                'foreign_keys': schema['foreign_keys'],
                'columns': schema['columns'],
            },
            'files': files,
        }), 200
    except ValueError as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    except Exception as exc:
        return jsonify({'success': False, 'error': f'Error interno: {str(exc)}'}), 500


@generator_bp.route('/api/download-crud-zip', methods=['POST'])
def download_crud_zip_api():
    data = request.get_json() or {}
    sql_input = (data.get('create_table_sql') or '').strip()
    target = (data.get('language') or 'sql').strip()
    architecture = (data.get('architecture') or 'rest_api').strip()

    if not sql_input:
        return jsonify({'success': False, 'error': 'Proporciona un CREATE TABLE válido'}), 400

    if target not in TARGET_LABELS:
        target = 'sql'

    if architecture not in ARCHITECTURE_LABELS:
        architecture = 'rest_api'

    try:
        schema = _parse_create_table(sql_input)
        files = _generate_code_templates(schema, target, architecture)

        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
            for file in files:
                zf.writestr(file['name'], file['content'])
        zip_buffer.seek(0)

        return send_file(
            zip_buffer,
            mimetype='application/zip',
            as_attachment=True,
            download_name='crud_generator_package.zip'
        )
    except ValueError as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    except Exception as exc:
        return jsonify({'success': False, 'error': f'Error interno: {str(exc)}'}), 500


def generate_sql(data):
    payload = _build_query_payload(data)

    if not payload['tables']:
        raise ValueError('Selecciona al menos una tabla para la consulta.')

    select_clause = '*'
    if payload['columns']:
        select_clause = ', '.join(payload['columns'])
    if payload['distinct']:
        select_clause = f'DISTINCT {select_clause}'

    base_table = payload['tables'][0]
    join_sql = []
    if payload['joins']:
        for join in payload['joins']:
            join_type = (join.get('type') or 'INNER').upper()
            table = join.get('table') or ''
            condition = join.get('condition') or ''
            if table and condition:
                join_sql.append(f"{join_type} JOIN {table} ON {condition}")

    from_clause = base_table
    if join_sql:
        from_clause += ' ' + ' '.join(join_sql)

    where_clause = ''
    if payload['filters']:
        filters = payload['filters'] if isinstance(payload['filters'], list) else [payload['filters']]
        filters = [item for item in filters if item]
        if filters:
            where_clause = ' WHERE ' + ' AND '.join(filters)

    group_by_clause = f" GROUP BY {payload['group_by']}" if payload['group_by'] else ''
    order_by_clause = f" ORDER BY {payload['order_by']}" if payload['order_by'] else ''
    limit_clause = f" LIMIT {payload['limit']}" if payload['limit'] else ''

    sql = f"SELECT {select_clause} FROM {from_clause}{where_clause}{group_by_clause}{order_by_clause}{limit_clause};"

    explanation_parts = [
        f'Selección de tabla principal: {base_table}.',
        f'Selección de columnas: {select_clause}.',
    ]
    if where_clause:
        explanation_parts.append('Se aplican filtros para limitar los resultados.')
    if payload['joins']:
        explanation_parts.append('Incluye JOINs para combinar datos entre tablas.')
    if group_by_clause:
        explanation_parts.append('Se agrupan resultados con GROUP BY para agregaciones.')
    if order_by_clause:
        explanation_parts.append('Se ordenan los datos con ORDER BY.')
    if limit_clause:
        explanation_parts.append('Se limita el conjunto de resultados con LIMIT.')

    valid = bool(re.search(r'(?i)^SELECT\s+.+\s+FROM\s+.+;', sql))
    if not valid:
        raise ValueError('No se pudo generar una consulta SQL válida con los datos proporcionados.')

    return {
        'success': True,
        'sql': sql,
        'explanation': ' '.join(explanation_parts),
        'valid': valid,
        'metadata': {
            'tables': payload['tables'],
            'columns_selected': payload['columns'],
            'has_filters': bool(payload['filters']),
            'group_by': payload['group_by'],
            'order_by': payload['order_by'],
        }
    }


def _normalize_text_list(value):
    if isinstance(value, str):
        return [item.strip() for item in value.split(',') if item.strip()]
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    return []


def _build_query_payload(data):
    tables = data.get('tables') or data.get('from_tables') or []
    if isinstance(tables, str):
        tables = [t.strip() for t in tables.split(',') if t.strip()]

    columns = _normalize_text_list(data.get('columns', []))
    filters = data.get('filters', [])
    if isinstance(filters, str):
        filters = [f.strip() for f in filters.split(';') if f.strip()]

    joins = data.get('joins', []) or []
    group_by = (data.get('group_by') or '').strip()
    order_by = (data.get('order_by') or '').strip()
    limit = (data.get('limit') or '').strip()
    distinct = bool(data.get('distinct', False))

    return {
        'tables': tables,
        'columns': columns,
        'filters': filters,
        'joins': joins,
        'group_by': group_by,
        'order_by': order_by,
        'limit': limit,
        'distinct': distinct,
    }


@generator_bp.route('/api/generate-sql', methods=['POST'])
def generate_sql_api():
    data = request.get_json() or {}
    try:
        result = generate_sql(data)
        return jsonify(result), 200
    except ValueError as error:
        return jsonify({'success': False, 'error': str(error)}), 400
    except Exception as exc:
        return jsonify({'success': False, 'error': f'Error interno: {str(exc)}'}), 500
