"""Punto de entrada principal para iLoveDB."""

import sys
import os
import webbrowser
from threading import Timer
from app import create_app

def open_browser():
    webbrowser.open_new('http://127.0.0.1:5000/')

if __name__ == "__main__":
    # Agregamos el directorio actual al PATH para asegurar que encuentre los módulos
    sys.path.append(os.path.abspath(os.path.dirname(__file__)))

    print("Iniciando iLoveDB v0.9...")
    
    app = create_app()

    # Abre el navegador después de que Flask inicie
    Timer(1.5, open_browser).start()

    try:
        print("Servidor iniciado en http://127.0.0.1:5000")
        app.run(host="127.0.0.1", port=5000, debug=False)
    except Exception as exc:
        print(f"ERROR al iniciar el servidor Flask: {exc}")
        sys.exit(1)