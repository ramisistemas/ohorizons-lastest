@echo off
REM Script de ejecución para MCP Enterprise Template en Windows

setlocal enabledelayedexpansion

REM Establecer variables de entorno
set PYTHONUNBUFFERED=1
set PYTHONDONTWRITEBYTECODE=1

REM Cargar .env si existe
if exist .env (
    for /f "tokens=1,2 delims==" %%A in (.env) do (
        if not "%%A"=="" (
            set "%%A=%%B"
        )
    )
)

REM Obtener directorio del script
set SCRIPT_DIR=%~dp0

REM Cambiar al directorio del proyecto
cd /d %SCRIPT_DIR%

REM Mostrar información
echo ========================================
echo MCP Enterprise Template Server
echo Version: %SERVER_VERSION%
echo Debug: %DEBUG%
echo ========================================
echo.

REM Ejecutar el servidor
python main.py

REM Verificar código de salida
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Error: El servidor falló con código %ERRORLEVEL%
    pause
    exit /b %ERRORLEVEL%
)

endlocal
