# ${{ values.name }}

${{ values.description }}

Servidor **MCP (Model Context Protocol)** construido con Clean Architecture / DDD
(`domain` → `application` → `infrastructure` → `delivery`), usando el SDK oficial `mcp`.

## Arquitectura

Ver [docs/architecture.md](docs/architecture.md) para el detalle completo de capas, patrones
de diseño y cómo agregar nuevas tools/resources.

## Dominio de ejemplo incluido

Este proyecto se genera con un caso de uso de referencia (pólizas de seguro:
`get_policy_info`, `get_customer_policies`) para mostrar el patrón completo end-to-end.
**Renombrar/reemplazar** los archivos en `src/domain/`, `src/application/use_cases.py`,
`src/infrastructure/repositories.py` y `src/delivery/mcp_server.py` con las tools reales
de tu caso de uso.

## Ejecutar localmente

```bash
pip install -e ".[dev]"
cp .env.example .env
# modo stdio (clientes locales, ej. Claude Desktop)
python main.py --mode mcp
# modo HTTP/SSE (el que corre en Kubernetes)
python main.py --mode http --http-port 8000
```

## Backend externo configurado

- URL: `${{ values.backendApiUrl }}`
- API Key: se inyecta en runtime vía `ExternalSecret` desde Key Vault (secreto `${{ values.backendApiKeySecretKey }}`)

## Tests

```bash
pytest tests/unit/ -v
pytest tests/integration/ -v
pytest --cov=src --cov-report=html
```

## Despliegue

CI/CD en `.github/workflows/deploy.yml` construye la imagen y la publica en
`${{ values.registry }}`; los manifiestos en `deploy/` despliegan en el namespace
`${{ values.namespace }}` vía ArgoCD.
