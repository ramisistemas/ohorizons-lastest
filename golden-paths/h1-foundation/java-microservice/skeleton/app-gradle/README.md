# ${{ values.name }}

${{ values.description }}

Generado desde el golden path **`h1-java-microservice`** de Backstage — alineado a la LBA (Lista de Bienes Aprobados):

| Clasificación LBA | Valor |
|---|---|
| Lenguaje | Java 21 (Verde) |
| Framework | Spring Boot (Verde) |
| Build Tool | Gradle |
| Cloud | Azure (Verde) |
| Plataforma | AKS |
| Contenedorización | Docker |
| Repositorio | GitHub |
| CI/CD | GitHub Actions |
| Despliegue | Kubernetes + Kustomize |
| Observabilidad | health/readiness (Spring Boot Actuator) |
| Escalamiento | HPA (CPU + memoria) |

## Arquitectura

Clean Architecture / Hexagonal, Gradle multi-proyecto:

```
domain/model/                              -> entidades de dominio puras, sin frameworks
domain/usecase/                            -> casos de uso, orquestan el dominio
infrastructure/driven-adapters/            -> adaptadores de salida (persistencia, etc.)
infrastructure/entry-points/rest/          -> adaptadores de entrada (controllers REST)
applications/app-service/                  -> arranque Spring Boot, conecta todo
```

El módulo `driven-adapters/in-memory-repository` es un ejemplo de referencia (guarda en
memoria, no persiste) — reemplazarlo por un adaptador real (JPA/R2DBC contra la base de
datos que corresponda) es lo primero que hay que hacer al empezar a construir el servicio
de verdad.

## Correr localmente

```bash
gradle :applications-app-service:bootRun
```

## Build

```bash
gradle build
```

## Docker

```bash
docker build -f applications/app-service/Dockerfile -t ${{ values.name }}:local .
docker run -p 8080:8080 ${{ values.name }}:local
```

## Endpoints de ejemplo

- `GET /actuator/health/liveness` / `GET /actuator/health/readiness`
- `GET /api/items` / `POST /api/items` — CRUD de ejemplo (dominio `Item`), a reemplazar por
  el dominio real del servicio.
