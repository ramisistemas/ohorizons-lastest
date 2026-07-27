# angular-crud-spa

SPA básica en Angular 19 (standalone components) con CRUD completo (crear, listar, editar, marcar y eliminar) contra una API [PostgREST](https://postgrest.org/) — es decir, sin backend propio: PostgREST expone la tabla `tasks` de Postgres directamente como API REST.

Este proyecto es el punto de partida para convertirse en una golden path template de Backstage (scaffolder). Por ahora vive aquí, en la raíz, para probarlo antes de moverlo a su ubicación definitiva.

## Estructura

```
angular-crud-spa/
├── src/app/
│   ├── core/
│   │   ├── models/task.model.ts       # forma de la fila de la tabla `tasks`
│   │   └── services/task.service.ts   # cliente HTTP genérico contra PostgREST
│   └── features/
│       ├── task-list/                 # listado + eliminar + marcar completada
│       └── task-form/                 # crear / editar
├── database/init.sql                  # tabla `tasks` + rol `web_anon` para PostgREST
├── docker-compose.yml                 # Postgres + PostgREST + app, listo para levantar
├── Dockerfile / nginx.conf            # build de producción servido con nginx
└── .github/workflows/ci.yaml          # build + lint en cada push/PR
```

## Levantar todo el stack (Postgres + PostgREST + Angular)

```bash
docker compose up --build
```

- App: http://localhost:8080
- PostgREST: http://localhost:3000
- Postgres: localhost:5432 (`appuser` / `apppass`)

## Desarrollo local (solo frontend, contra PostgREST en :3000)

```bash
docker compose up postgres postgrest   # levanta solo la base + API
npm install
npm start                              # ng serve, con proxy /api -> localhost:3000
```

## Apuntar a otra base de datos / recurso

Edita `src/environments/environment.ts` (producción) o `environment.development.ts` (desarrollo):

```ts
export const environment = {
  apiUrl: '/api',      // o la URL absoluta de tu PostgREST
  resource: 'tasks',   // nombre de la tabla/vista PostgREST a exponer
};
```

Para usar otra entidad además de `tasks`, crea su tabla en `database/init.sql` con los mismos `grant` que usa `web_anon`, y ajusta `Task`/`TaskService` (o duplica esos dos archivos) para el nuevo modelo.

## Próximo paso

Una vez validado, este proyecto se convierte en golden path de Backstage: se traslada a `golden-paths/h1-foundation/angular-crud-spa/skeleton/`, se agrega `template.yaml` con los parámetros (`appName`, `owner`, `entityName`, `postgrestUrl`, `repoUrl`) y se reemplazan los valores fijos por marcadores de la forma `{{ values.NOMBRE }}`.
