#!/bin/bash
# Script de ejecución para MCP Enterprise Template en Unix/Linux/Mac

set -euo pipefail

# Directorio del script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Cargar variables de entorno desde .env
if [ -f .env ]; then
    set -a
    source .env
    set +a
fi

# Establecer valores por defecto
export PYTHONUNBUFFERED=${PYTHONUNBUFFERED:-1}
export PYTHONDONTWRITEBYTECODE=${PYTHONDONTWRITEBYTECODE:-1}
export SERVER_VERSION=${SERVER_VERSION:-1.0.0}
export DEBUG=${DEBUG:-false}
export LOG_LEVEL=${LOG_LEVEL:-INFO}

# Mostrar información
echo "========================================"
echo "MCP Enterprise Template Server"
echo "Version: $SERVER_VERSION"
echo "Debug: $DEBUG"
echo "========================================"
echo ""

# Ejecutar el servidor
python main.py

# Capturar código de salida
EXIT_CODE=$?

if [ $EXIT_CODE -ne 0 ]; then
    echo ""
    echo "Error: El servidor falló con código $EXIT_CODE"
    exit $EXIT_CODE
fi
