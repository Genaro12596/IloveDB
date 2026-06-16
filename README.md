# IloveBD

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
- **Procesador**: Intel Core i3 o equivalente
- **Memoria RAM**: 2 GB mínimo
- **Almacenamiento**: 500 MB de espacio disponible
- **Conexión a Internet**: Recomendado para descargas de dependencias

## Software
Antes de la instalación, asegúrate de contar con los siguientes elementos instalados en tu entorno de ejecución:

* **Python:** Versión 3.10 o superior.
* **Administrador de paquetes:** pip (incluido con Python) o `py` en Windows.
* **Dependencias Core:** Especificadas en el manifiesto del proyecto:
  * `Flask` - Framework de desarrollo backend.
  * `sqlparse` - Motor de análisis sintáctico de SQL.
  * `python-dotenv` - Gestión de variables de entorno.

## Estado de la instalación actual
La sección de instalación actual ofrece los pasos básicos para clonar el repositorio, crear un entorno virtual y ejecutar el proyecto. Esta versión actualizada agrega instrucciones claras para nuevos colaboradores en Windows y en macOS/Linux, usando el intérprete Python adecuado de cada plataforma.

# Procedimiento de instalación

## 1. Clonar el repositorio
```bash
git clone https://github.com/Genaro12596/IloveDB.git
cd IloveDB
```

## 2. Crear y activar el entorno virtual

### En Windows
```powershell
py -3 -m venv venv
venv\Scripts\activate
python -m pip install --upgrade pip
```

### En macOS/Linux
```bash
python3 -m venv venv
source venv/bin/activate
python3 -m pip install --upgrade pip
```

> Nota: Si tu sistema usa `python` en lugar de `python3`, puedes reemplazar `python3` por `python` en los comandos anteriores.

En caso de tener el error 
```bash
venv/bin/activate (línea 40): 'case' builtin usado fuera de un bloque 'switch'
```
Solucion: [Click Aqui](docs/SolucionLinux.md)

## 3. Instalar dependencias
```bash
pip install -r requirements.txt
```

Si el entorno está gestionado por el sistema y no permite instalación directa, usa el entorno virtual creado.

## 4. Ejecutar la aplicación
```bash
python run.py
```

La aplicación estará disponible en `http://localhost:5000`.

## 5. Verificación rápida
- Accede a `http://localhost:5000` en tu navegador.
- Si aparece la página de inicio, la instalación fue exitosa.
- Si no, revisa que el entorno virtual esté activado y que las dependencias hayan sido instaladas correctamente.


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

```text
iLoveDB/
├── .vscode/
│   └── settings.json                  # Config VS Code
├── app/
│   ├── routes/                        # Controladores (Rutas)
│   │   ├── csv_to_sql.py              # Ruta CSV a SQL
│   │   ├── home.py                    # Ruta Inicio
│   │   ├── normalization.py           # Ruta Normalización
│   │   ├── optimizer.py               # Ruta Optimizador
│   │   ├── sql_formatter.py           # Ruta Formateador
│   │   ├── sql_generator.py           # Ruta Generador
│   │   └── table_size.py              # Ruta Calcular Tamaño
│   ├── services/                      
│   │   ├── csv_sql_service.py         # Lógica CSV a SQL
│   │   ├── optimizer_service.py       # Lógica Optimizador
│   │   ├── sql_formatter_service.py   # Lógica Formateador
│   │   └── table_size_service.py      # Lógica Calculadora
│   ├── static/                        # Frontend estático
│   │   ├── css/
│   │   │   └── styles.css             # Estilos
│   │   └── js/
│   │       ├── app.js                 # Scripts JS
│   │       └── utils.js               # Utilidades JS
│   ├── templates/                     # HTML
│   │   ├── base.html                  # Plantilla base
│   │   ├── csv_sql.html               # Vista CSV a SQL
│   │   ├── formatter.html             # Vista Formateador
│   │   ├── generator.html             # Vista Generador
│   │   ├── index.html                 # Vista Inicio
│   │   ├── normalization.html         # Vista Normalización
│   │   ├── optimizer.html             # Vista Optimizador
│   │   └── table_size.html            # Vista Calculadora
│   └── __init__.py                    # Inicializador Flask
├── assets/                            # Recursos extra
│   ├── Diagrama/
│   │   └── [...]                      # Diagramas
│   ├── images/
│   │   └── [...]                      # Capturas de pantalla
│   └── Orientador.md                  # Guía de orientación
├── docs/                              # Documentación Markdown
│   ├── Images/
│   │   └── [...]                      # Imágenes para Docs
│   ├── AnalizadorSQL.md               # Doc Analizador
│   ├── Arquitectura.md                # Doc Arquitectura
│   ├── CSVSQL.md                      # Doc CSV a SQL
│   ├── DBStorage.md                   # Doc Almacenamiento
│   ├── Documentación Clean Code.md    # Estándares de código
│   ├── Ejecucion de programa.md       # Guía de ejecución
│   ├── EngineOptimizer.md             # Doc Optimizador
│   ├── GeneradorSQL                   # Archivo Generador
│   ├── Normalizacion.md               # Doc Normalización
│   ├── SolucionLinux.md               # Guía para Linux
│   └── flujo_de_trabajo.md            # Guía Git/GitHub
├── scripts/                           # Automatización
│   ├── INICIAR.bat                    # Instalador Windows
│   ├── START.bat                      # Lanzador Windows
│   ├── diagnostico.py                 # Script de prueba
│   ├── start_server.py                # Lanzador Python
│   ├── verificar.py                   # Validador de entorno
│   └── verify_ui_changes.py           # Validador de interfaz
├── .gitignore                         # Exclusiones Git
├── README.md                          # Portada del proyecto
├── requirements.txt                   # Dependencias Python
└── run.py                             # Ejecutable principal
```

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
