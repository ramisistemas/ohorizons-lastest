.PHONY: help install install-dev test test-unit test-integration test-cov clean lint format type-check run run-debug docker-build docker-run docker-stop

.DEFAULT_GOAL := help

PYTHON := python
PIP := pip
PYTEST := pytest
BLACK := black
RUFF := ruff
MYPY := mypy

help: ## Mostrar esta ayuda
	@echo "MCP Enterprise Template - Comandos disponibles"
	@echo "=============================================="
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Instalar dependencias
	$(PIP) install -e .

install-dev: ## Instalar dependencias de desarrollo
	$(PIP) install -e ".[dev]"

test: ## Ejecutar todas las pruebas
	$(PYTEST) -v

test-unit: ## Ejecutar solo pruebas unitarias
	$(PYTEST) tests/unit/ -v

test-integration: ## Ejecutar solo pruebas de integración
	$(PYTEST) tests/integration/ -v

test-cov: ## Ejecutar pruebas con reporte de cobertura
	$(PYTEST) --cov=src --cov-report=html --cov-report=term-missing -v

clean: ## Limpiar archivos generados
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .mypy_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name htmlcov -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name ".DS_Store" -delete
	rm -rf build/ dist/ *.egg-info/ .coverage

lint: ## Ejecutar linter (ruff)
	$(RUFF) check src tests

format: ## Formatear código con black
	$(BLACK) src tests

format-check: ## Verificar formato sin cambiar archivos
	$(BLACK) --check src tests

type-check: ## Verificar tipos con mypy
	$(MYPY) src

run: ## Ejecutar el servidor
	$(PYTHON) main.py

run-debug: ## Ejecutar el servidor en modo debug
	DEBUG=true LOG_LEVEL=DEBUG $(PYTHON) main.py

docker-build: ## Construir imagen Docker
	docker build -t mcp-enterprise-template:latest .

docker-run: ## Ejecutar contenedor Docker
	docker run -e INSURANCE_API_KEY=${INSURANCE_API_KEY} \
	           -e DEBUG=false \
	           --rm \
	           mcp-enterprise-template:latest

docker-stop: ## Detener contenedor Docker
	docker stop mcp-enterprise-template || true

docker-compose-up: ## Iniciar servicios con docker-compose
	docker-compose up -d

docker-compose-down: ## Detener servicios con docker-compose
	docker-compose down

docker-compose-logs: ## Ver logs de docker-compose
	docker-compose logs -f

dev-env: ## Configurar entorno de desarrollo
	cp .env.example .env
	$(PYTHON) -m venv venv || true
	$(MAKE) install-dev

all: clean install-dev lint type-check test ## Ejecutar todos los checks (lint, type-check, test)

# Alias útiles
check: lint type-check ## Ejecutar lint y type-check
dev: dev-env run-debug ## Configurar dev-env y ejecutar en debug
prod: docker-build docker-run ## Construir imagen y ejecutar
