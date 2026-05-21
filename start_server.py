#!/usr/bin/env python
"""
Startup script para iLoveDB v0.9
Verifica todo está bien y ejecuta el servidor
"""

import sys
import os

print("=" * 70)
print("INICIANDO iLoveDB v0.9")
print("=" * 70)
print()

# Verificar dependencias
print("[1/3] Verificando dependencias...")
required = ['flask', 'sqlparse']
for package in required:
    try:
        __import__(package)
        print(f"  OK: {package}")
    except ImportError:
        print(f"  ERROR: {package} no instalado")
        sys.exit(1)

print()

# Crear app
print("[2/3] Inicializando Flask app...")
try:
    from app import create_app
    app = create_app()
    print("  OK: Flask app creada")
except Exception as e:
    print(f"  ERROR: {str(e)}")
    sys.exit(1)

print()

# Ejecutar
print("[3/3] Ejecutando servidor...")
print()
print("=" * 70)
print("URL: http://127.0.0.1:5000")
print("=" * 70)
print()

try:
    app.run(debug=True, host='127.0.0.1', port=5000)
except KeyboardInterrupt:
    print("\n\nServidor detenido")
except Exception as e:
    print(f"\nError: {str(e)}")
    sys.exit(1)
