@echo off
REM iLoveDB v0.9 - Servidor de inicio
REM Script para Windows

echo.
echo ======================================================================
echo     iLoveDB v0.9 - SQL Tools Platform
echo ======================================================================
echo.

REM Verificar Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python no esta instalado
    echo Descarga Python desde: https://www.python.org
    pause
    exit /b 1
)

REM Mostrar version
echo Verificando Python...
python --version
echo.

REM Verificar dependencias
echo Verificando dependencias...
python verificar.py
if errorlevel 1 (
    echo.
    echo ERROR: La verificacion fallo
    pause
    exit /b 1
)

echo.
echo Iniciando servidor...
echo.
echo ======================================================================
echo   URL: http://127.0.0.1:5000
echo   Presiona Ctrl+C para detener el servidor
echo ======================================================================
echo.

python run.py

pause
