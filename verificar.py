#!/usr/bin/env python
"""Verificación completa de iLoveDB v0.9"""
import sys
import os

print("\n" + "="*70)
print("VERIFICACIÓN - iLoveDB v0.9")
print("="*70 + "\n")

errors = []
warnings = []

# 1. Verificar dependencias
print("[1/4] Verificando dependencias...")
required = ['flask', 'sqlparse', 'dotenv']
installed = {}
for pkg in required:
    try:
        __import__(pkg)
        print(f"  ✅ {pkg}")
        installed[pkg] = True
    except ImportError:
        print(f"  ❌ {pkg} - NO INSTALADO")
        installed[pkg] = False
        errors.append(f"Falta: {pkg}")

print()

# 2. Verificar estructura
print("[2/4] Verificando estructura de archivos...")
required_files = [
    'app/__init__.py',
    'app/routes/sql_formatter.py',
    'app/routes/csv_to_sql.py',
    'app/routes/sql_generator.py',
    'app/routes/table_size.py',
    'app/routes/normalization.py',
    'app/routes/optimizer.py',
    'app/services/optimizer_service.py',
    'app/templates/base.html',
    'app/templates/formatter.html',
    'app/templates/optimizer.html',
    'app/static/css/styles.css',
    'app/static/js/utils.js',
    'run.py',
]

for file in required_files:
    if os.path.exists(file):
        print(f"  ✅ {file}")
    else:
        print(f"  ❌ {file} - NO ENCONTRADO")
        errors.append(f"Archivo faltante: {file}")

print()

# 3. Verificar importaciones
print("[3/4] Verificando importaciones...")
try:
    from app import create_app
    print("  ✅ from app import create_app")
except Exception as e:
    print(f"  ❌ Error importando app: {e}")
    errors.append(f"Error en __init__.py: {str(e)}")

try:
    from app.services.optimizer_service import SQLOptimizer
    print("  ✅ from app.services.optimizer_service import SQLOptimizer")
except Exception as e:
    print(f"  ❌ Error importando optimizer_service: {e}")
    errors.append(f"Error en optimizer_service: {str(e)}")

print()

# 4. Crear app y verificar rutas
print("[4/4] Verificando Flask app...")
try:
    from app import create_app
    app = create_app()
    print("  ✅ Flask app creada correctamente")
    
    # Contar rutas
    routes = [str(r.rule) for r in app.url_map.iter_rules()]
    web_routes = [r for r in routes if not r.startswith('/static')]
    
    print(f"  ✅ {len(web_routes)} rutas disponibles:")
    for route in sorted(web_routes):
        print(f"     - {route}")
    
except Exception as e:
    print(f"  ❌ Error creando Flask app: {e}")
    errors.append(f"Error en Flask app: {str(e)}")
    sys.exit(1)

print()

# Resumen
print("="*70)
if not errors:
    print("✅ VERIFICACIÓN COMPLETADA - TODO OK")
    print()
    print("Para ejecutar la app:")
    print("  python run.py")
    print()
    print("URL: http://127.0.0.1:5000")
else:
    print("❌ ERRORES ENCONTRADOS:")
    for error in errors:
        print(f"  - {error}")
    if warnings:
        print("\n⚠️  ADVERTENCIAS:")
        for warning in warnings:
            print(f"  - {warning}")
    sys.exit(1)

print("="*70 + "\n")
