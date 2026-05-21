@echo off
REM Script para ejecutar iLoveDB en Windows
REM Navega al directorio y ejecuta el servidor

cd /d "c:\Users\ANDYN\OneDrive\Documentos\Cuarto semestre\Ingenieria de software\soft2\IloveBD"

echo ===============================================
echo  Iniciando iLoveDB...
echo ===============================================
echo.

REM Verificar si existe venv
if exist "venv\Scripts\python.exe" (
    echo ✓ Entorno virtual encontrado
    echo.
    echo Ejecutando: .\venv\Scripts\python.exe run.py
    echo.
    echo Accede a: http://localhost:5000
    echo.
    .\venv\Scripts\python.exe run.py
) else (
    echo.
    echo ⚠ Entorno virtual no encontrado
    echo Intentando con python del sistema...
    echo.
    python run.py
)

pause
