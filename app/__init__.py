from flask import Flask
from app.routes.sql_formatter import formatter_bp
from app.routes.csv_to_sql import csv_bp
from app.routes.sql_generator import generator_bp
from app.routes.table_size import size_bp
from app.routes.normalization import normalization_bp
from app.routes.optimizer import optimizer_bp
from app.routes.home import home_bp
import os
import sys

def get_resource_path(relative_path):
    """Obtiene la ruta absoluta hacia los archivos, funciona para dev y PyInstaller."""
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

def create_app() -> Flask:
    # Inicializamos Flask usando la función auxiliar
    app = Flask(__name__, 
                template_folder=get_resource_path('templates'),
                static_folder=get_resource_path('static'))

    app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024

    # Registro de Blueprints
    app.register_blueprint(formatter_bp)
    app.register_blueprint(csv_bp)
    app.register_blueprint(generator_bp)
    app.register_blueprint(size_bp)
    app.register_blueprint(normalization_bp)
    app.register_blueprint(optimizer_bp)
    app.register_blueprint(home_bp)

    return app