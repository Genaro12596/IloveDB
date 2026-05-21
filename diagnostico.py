"""
Script de diagnóstico de estabilidad para iLoveDB
Verifica:
1. Dependencias instaladas
2. Sintaxis de archivos Python
3. Rutas disponibles
4. Importaciones correctas
"""

import sys
import os

print("=" * 70)
print("DIAGNÓSTICO DE ESTABILIDAD - iLoveDB v0.9")
print("=" * 70)
print()

# 1. VERIFICAR DEPENDENCIAS
print("[1/5] Verificando dependencias...")
print("-" * 70)

required_packages = ['flask', 'sqlparse', 'python-dotenv']
missing = []

for package in required_packages:
    try:
        __import__(package)
        print(f"  OK: {package}")
    except ImportError:
        print(f"  ERROR: {package} NO INSTALADO")
        missing.append(package)

if missing:
    print(f"\nFalta instalar: {', '.join(missing)}")
    print("Ejecuta: pip install " + " ".join(missing))
else:
    print("\n  Todas las dependencias OK")

print()

# 2. VERIFICAR ESTRUCTURA DE ARCHIVOS
print("[2/5] Verificando estructura de archivos...")
print("-" * 70)

required_files = {
    'app/__init__.py': 'Inicializador Flask',
    'app/routes/sql_formatter.py': 'Ruta Formateador',
    'app/routes/optimizer.py': 'Ruta Optimizer',
    'app/services/optimizer_service.py': 'Servicio Optimizer',
    'app/templates/base.html': 'Template base',
    'app/templates/optimizer.html': 'Template optimizer',
    'app/static/js/utils.js': 'Utilidades JavaScript',
    'run.py': 'Punto de entrada'
}

base_path = os.path.dirname(os.path.abspath(__file__))

for file_path, description in required_files.items():
    full_path = os.path.join(base_path, file_path)
    if os.path.exists(full_path):
        print(f"  OK: {file_path}")
    else:
        print(f"  ERROR: {file_path} - {description} FALTA")

print()

# 3. VERIFICAR IMPORTACIONES
print("[3/5] Verificando importaciones críticas...")
print("-" * 70)

try:
    from app import create_app
    print("  OK: Flask app inicializa correctamente")
except Exception as e:
    print(f"  ERROR en importación: {str(e)[:100]}")

try:
    from app.services.optimizer_service import optimize_sql
    print("  OK: Servicio Optimizer importa correctamente")
except Exception as e:
    print(f"  ERROR en Optimizer: {str(e)[:100]}")

print()

# 4. VERIFICAR CONFIGURACIÓN
print("[4/5] Verificando configuración...")
print("-" * 70)

env_file = os.path.join(base_path, '.env')
if os.path.exists(env_file):
    print("  OK: Archivo .env existe")
else:
    print("  INFO: No hay archivo .env (OK para desarrollo)")

print()

# 5. VERIFICAR RUTAS
print("[5/5] Verificando rutas disponibles...")
print("-" * 70)

try:
    from app import create_app
    app = create_app()
    
    routes = []
    for rule in app.url_map.iter_rules():
        if rule.endpoint != 'static':
            routes.append(f"{rule.rule:40} {rule.methods}")
    
    print("\nRutas disponibles:")
    for route in sorted(routes):
        print(f"  {route}")
        
except Exception as e:
    print(f"  ERROR: {str(e)}")

print()
print("=" * 70)
print("DIAGNÓSTICO COMPLETADO")
print("=" * 70)
print()
print("PRÓXIMOS PASOS:")
print("1. Si ves errores, verifica las dependencias")
print("2. Ejecuta: python run.py")
print("3. Abre: http://localhost:5000")
print()
