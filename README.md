# IloveDB

# Descripcion del proyecto.
ILoveBD es una plataforma orientada a la automatización, análisis y optimización de tareas relacionadas con bases de datos y consultas SQL. El sistema fue desarrollado con el propósito de centralizar herramientas útiles para desarrolladores, analistas de datos y administradores de bases de datos, permitiendo reducir procesos manuales y mejorar la productividad en actividades técnicas relacionadas con SQL. 

La plataforma integra distintos módulos especializados que funcionan de manera independiente bajo una arquitectura modular, permitiendo realizar tareas como análisis y formateo de consultas SQL, conversión de archivos CSV a scripts SQL, estimación de almacenamiento de bases de datos, análisis estructural de normalización, generación de consultas y optimización de rendimiento SQL. 

El sistema cuenta actualmente con **6 herramientas completamente funcionales**:
1. **SQL Formatter:** Formateador automático con resaltado de sintaxis y opciones de exportación.
2. **CSV → SQL Converter:** conversor inteligente con detección automática de tipos de datos, generador de sentencias `CREATE TABLE` e `INSERT`.
3. **SQL Generator:** Constructor interactivo de consultas estándar (`SELECT`, `INSERT`, `UPDATE`, `DELETE`).
4. **Table Size Calculator:** Calculadora métrica para estimar el espacio de almacenamiento físico en disco basándose en tipos de datos, índices y volumen de registros.
5. **Normalization Checker:** Validador teórico y práctico de las primeras tres Formas Normales (1FN, 2FN, 3FN) con sugerencias de resolución.
6. **SQL Optimizer:** Analizador avanzado que detecta 9 patrones de ineficiencia en consultas, clasificándolos por severidad.

# Requisitos de hardware y software.

## Hardware
- **Procesador**: Intel Core i3 o equivalente (intel celeron)
- **Memoria RAM**: 2 GB mínimo
- **Almacenamiento**: 500 MB de espacio disponible
- **Conexión a Internet**: Recomendado para descargas de dependencias

## Software
Antes de la instalación, asegúrate de contar con los siguientes elementos instalados en tu entorno de ejecución:

* **Python:** Versión 3.x o superior.
* **Administrador de paquetes:** pip (incluido por defecto con Python).
* **Dependencias Core:** Especificadas en el manifiesto del proyecto:
  * `Flask` (v3.0.3) - Framework de desarrollo backend.
  * `sqlparse` (v0.5.0) - Motor de análisis sintáctico de SQL.
  * `python-dotenv` (v1.0.1) - Gestión de variables de entorno.

# Procedimiento de instalacion.

1. **Clonar el repositorio**
   ```bash
   git clone https://github.com/Genaro12596/IloveDB.git
   cd IloveDB
   ```

2. **Crear un entorno virtual**
   ```bash
   python -m venv venv
   ```

3. **Activar el entorno virtual**
   - En Windows:
     ```bash
     venv\Scripts\activate
     ```
   - En macOS/Linux:
     ```bash
     source venv/bin/activate
     ```

4. **Instalar las dependencias**
   ```bash
   pip install -r requirements.txt
   ```

5. **Verificar la instalación**
   ```bash
   python run.py
   ```
   
   La aplicación estará disponible en `http://localhost:5000`


# Ejemplos de ejecucion.

En caso de que se requira saber informacion con respecto a las herramientas puede consultar el siguiente archivo en el cual se detallaran algunos ejemplos de como es que deberia de funcionar la aplicacion, adjuntando por supuesto imagenes de su ejecucion para una mejor comprension

Ejecucion: [Aqui](assets/Orientador.md)

# Arquitectura de los archivos

Si se desea entender como funciona este proyecto entonces la siguiente informacion esta dirigida para los nuevos colaboradores o usuarios que quieran entender como es el funcionamiento del software

Arquitectura: [Aqui](docs/Arquitectura.md)

# Estructura de archivos importantes
- `run.py`: Punto de entrada de la aplicación
- `app/__init__.py`: Inicialización de la aplicación Flask
- `app/routes/`: Rutas y controladores
- `app/services/`: Lógica del programa
- `app/templates/`: Plantillas HTML
- `app/static/`: CSS y JavaScript

# Estructura de directorios.

# Licencia y autores.

## Autores
- **Desarrolladores**: 
  - [Anthony Gael Lopez Guerrero](https://github.com/Antonio8624)
  - [Genaro Perez Nuñez](https://github.com/genaro052520-code)
  - [Alexis David Velazquez Garcia](https://github.com/AlexisDVGx)
  - [Moises Valdez Aguilar](https://github.com/ValdezMoises)
  - [Adam Eliseo Lopez Presas](https://github.com/AdamLP33)

## Licencia

Este proyecto fue desarrollado con fines académicos como parte de la experiencia educativa de Tecnologías Computacionales. Su uso está destinado exclusivamente para propósitos educativos y de aprendizaje.