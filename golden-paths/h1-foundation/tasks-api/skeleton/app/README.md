# ${{values.name}}

API CRUD de tareas para demo Open Horizons

## Overview

Microservicio CRUD de tareas generado con el Golden Path H1 - Foundation de Open Horizons.
Reemplaza a PostgREST: expone la misma forma de contrato REST que ya usa la SPA `ohorizons_ms`
(`GET/POST /tasks`, `GET/PATCH/DELETE /tasks/:id`), pero con código propio sobre Postgres.

| Property | Value |
|----------|-------|
| Owner | ${{values.owner}} |

## Getting Started

### Prerequisites

- Node.js 20+
- Docker
- Un Postgres accesible (local o el `tasksdb` de la plataforma)

### Local Development

```bash
# Instalar dependencias
npm install

# Correr localmente (crea la tabla tasks si no existe)
DATABASE_URL=postgres://appuser:apppass@localhost:5432/tasksdb npm run dev

# Correr tests (requiere un Postgres en localhost:5432)
DATABASE_URL=postgres://appuser:apppass@localhost:5432/tasksdb npm test

# Construir imagen Docker
docker build -t ${{values.name}}:local .
```

## API Endpoints

| Method | Path | Description |
|--------|------|--------------|
| GET | /health | Health check |
| GET | /ready | Readiness (verifica conexión a Postgres) |
| GET | /metrics | Métricas Prometheus |
| GET | /tasks | Lista tareas |
| POST | /tasks | Crea una tarea |
| GET | /tasks/:id | Obtiene una tarea |
| PATCH | /tasks/:id | Actualiza una tarea |
| DELETE | /tasks/:id | Elimina una tarea |

## Architecture

```
src/
├── index.js          # Entry point: middlewares, health/ready/metrics, arranque
├── routes/            # Rutas Express (tasks.js)
├── services/          # Lógica de negocio y validación (tasks.service.js)
├── db/                # Pool de conexión y queries SQL
├── middleware/         # error-handler, request-metrics
└── config/            # Variables de entorno (env.js)
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| PORT | Puerto del servidor | 3000 |
| NODE_ENV | Entorno | development |
| LOG_LEVEL | Nivel de logging | info |
| DATABASE_URL | Connection string de Postgres (requerido) | - |
| ALLOWED_ORIGIN | Origen permitido para CORS | * |

## Base de datos

Al arrancar, el servicio ejecuta `ensureSchema()` (`src/db/queries.js`), que crea la tabla
`tasks` si no existe.

## Monitoring

- Métricas: disponibles en `/metrics` en formato Prometheus
- Logs: JSON estructurado a stdout
- Readiness: `/ready` valida conexión real a Postgres (`select 1`)
