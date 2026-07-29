# ${{ values.name }}

${{ values.description }}

## Overview

CRUD REST de tareas (`tasks`) sobre PostgreSQL, listo para desplegarse en AKS vía ArgoCD.
Reemplaza el patrón PostgREST por un backend Express propio con validación, métricas y
readiness real contra la base de datos.

## Getting Started

1. Crear el componente desde el catálogo de software de Backstage.
2. Completar owner, sistema, namespace y el secreto de base de datos (`databaseSecretKey`).
3. Revisar el repositorio generado y el workflow de CI/CD.
4. Verificar que el componente quede registrado en el catálogo.

## Generated Assets

- Metadatos de catálogo de Backstage (`catalog-info.yaml` con Component + API)
- Backend Express + `pg` + `prom-client` con CRUD de `tasks`
- Dockerfile multi-stage con usuario no root
- Manifiestos Kubernetes (`deploy/`) con `ExternalSecret` para `DATABASE_URL`
- CI/CD (lint, test contra Postgres real, escaneo de seguridad, build+push)
- TechDocs
