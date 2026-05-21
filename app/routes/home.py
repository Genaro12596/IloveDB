from flask import Blueprint, render_template

# Creamos el Blueprint para la ruta de inicio
home_bp = Blueprint('home', __name__)

@home_bp.route('/')
def index():
    # Esto buscará el archivo index.html en tu carpeta de plantillas
    return render_template('index.html')