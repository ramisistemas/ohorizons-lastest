# Dockerfile multietapa optimizado para MCP Enterprise Template

# Stage 1: Builder
FROM python:3.11-slim as builder

WORKDIR /app

# Instalar dependencias del sistema necesarias para compilar
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copiar archivos de especificación
COPY pyproject.toml .

# Crear wheels para todas las dependencias
RUN pip install --upgrade pip setuptools wheel && \
    pip wheel --no-cache-dir --no-deps --wheel-dir /app/wheels -e .

# Stage 2: Runtime
FROM python:3.11-slim

WORKDIR /app

# Metadata
LABEL maintainer="${{ values.owner }}"
LABEL version="1.0.0"
LABEL description="${{ values.description }}"

# Instalar solo dependencias de runtime necesarias
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Crear usuario no-root para seguridad
RUN useradd -m -u 1000 appuser

# Copiar wheels desde builder
COPY --from=builder /app/wheels /wheels

# Instalar dependencias desde wheels
RUN pip install --no-cache /wheels/* && rm -rf /wheels

# Copiar código de aplicación
COPY --chown=appuser:appuser . .

# Cambiar a usuario no-root
USER appuser

# Establecer variables de entorno predeterminadas
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    LOG_LEVEL=INFO \
    DEBUG=false

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)"

# Comando de ejecucion: modo HTTP/SSE por defecto (requerido para exponerse
# como Service de Kubernetes; el modo stdio solo aplica a clientes locales)
ENTRYPOINT ["python", "main.py"]
CMD ["--mode", "http", "--http-host", "0.0.0.0", "--http-port", "8000"]
