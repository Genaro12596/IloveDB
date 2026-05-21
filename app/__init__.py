from flask import Flask
from app.routes.sql_formatter import formatter_bp
from app.routes.csv_to_sql import csv_bp
from app.routes.sql_generator import generator_bp
from app.routes.table_size import size_bp
from app.routes.normalization import normalization_bp
from app.routes.optimizer import optimizer_bp


def create_app() -> Flask:
    app = Flask(__name__)

    app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024

    app.register_blueprint(formatter_bp)
    app.register_blueprint(csv_bp)
    app.register_blueprint(generator_bp)
    app.register_blueprint(size_bp)
    app.register_blueprint(normalization_bp)
    app.register_blueprint(optimizer_bp)

    return app