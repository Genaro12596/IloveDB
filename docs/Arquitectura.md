# Arquitectura de iLoveDB

Este documento describe la estructura arquitectónica, los patrones de diseño y el flujo de datos que rigen a **iLoveDB**.

---

## 1. Patrón Arquitectónico General

La aplicación sigue una **Arquitectura en Capas** combinada con el patrón **Fábrica de Aplicaciones** de Flask, garantizando la separación de responsabilidades, modularidad y escalabilidad del sistema.

El sistema se divide en tres capas fundamentales:
1. **Capa de Presentación (Frontend):** Plantillas HTML5, estilos mediante módulos CSS modernos y lógica del lado del cliente con JavaScript (`Prism.js` para resaltado).
2. **Capa de Enrutamiento y Control (Blueprints):** Controladores de Flask encargados de gestionar las peticiones HTTP (GET/POST) y validar los datos de entrada.
3. **Capa de Lógica de Negocio (Services):** Scripts puros de Python encargados del procesamiento algorítmico pesado (formateo sintáctico, análisis de rendimiento, validaciones de normalización).

![Diagrama](../assets/Diagrama/Diagrama%20Dentro%20de%20la%20APP.png)

---

## 2. Estructura de Módulos (Flask Blueprints)

Para evitar un archivo monolithic y cumplir con las buenas prácticas de desarrollo modular, cada una de las **6 herramientas** está aislada en su propio componente independiente:

* **home**: Gestiona el índice principal de la aplicación web.
* **sql_formatter**: Controla el embellecimiento y reestructuración de sentencias SQL.
* **sql_optimizer**: Ejecuta el motor de optimización heurística analizando 9 patrones comunes de ineficiencia.
* **csv_to_sql**: Parsea archivos planos estructurados para mapear esquemas relacionales.
* **sql_generator**: Constructor dinámico de consultas DML.
* **table_size**: Realiza cálculos matemáticos y métricos del almacenamiento físico estimado.
* **normalization**: Validador lógico de dependencias funcionales y formas normales.

---

## 3. Flujo de Datos (Ciclo de Vida de una Petición)

Cuando un usuario interactúa con la interfaz (por ejemplo, al solicitar la optimización de una consulta en el módulo `SQL Optimizer`):

1. **Disparo del Evento (Client):** El usuario ingresa código SQL en `optimizer.html` y presiona "Analizar". JavaScript (`utils.js`) captura el evento, bloquea el botón con un *loading state* y realiza una petición asíncrona vía `fetch()` al endpoint `POST /api/optimize-sql`.
2. **Recepción y Enrutamiento (Blueprint):** El servidor Flask recibe la solicitud en `app/routes/optimizer.py`. El controlador desempaqueta el JSON recibido, valida la integridad elemental de la cadena y delega la responsabilidad algorítmica a la capa lógica.
3. **Procesamiento Técnico (Service):** El archivo `app/services/optimizer_service.py` recibe la consulta. Utiliza funciones internas o librerías del entorno como `sqlparse` para descomponer la estructura de la consulta, verificar reglas sintácticas y generar una lista de problemas clasificados por severidad (Error, Warning, Info).
4. **Retorno de Respuesta:** El servicio devuelve un diccionario con los resultados al controlador de la ruta, el cual responde al cliente con un código `200 OK` y un cuerpo JSON.
5. **Renderizado en Interfaz:** JavaScript recibe la respuesta, procesa la lista de recomendaciones y actualiza dinámicamente el DOM inyectando badges de severidad, disparando notificaciones interactivas emergentes (Toasts).

---

## 4. Inicialización del Sistema (App Factory)

El archivo `app/__init__.py` implementa la función rectora `create_app()`. Este enfoque previene las importaciones circulares en Python y centraliza de manera ordenada:
* La configuración de límites del sistema (ej. `MAX_CONTENT_LENGTH` restringido a 5MB).
* El mapeo absoluto dinámico de recursos estáticos y vistas para asegurar la portabilidad multiplataforma.
* El registro unificado de todos los Blueprints activos en la plataforma.

Regresar a Readme: [Aqui](../README.md)