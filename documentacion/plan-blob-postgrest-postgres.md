# Plan: angular-crud-postgres → Blob Storage + PostgREST en AKS + Postgres por proyecto

Documento de planificación, iniciado el 2026-07-28. Extiende el golden path `angular-crud-postgres` (ver también `backstage-login-y-golden-path.md`) para que, además de generar el código Angular, automatice el despliegue completo en el Open Horizons desplegado en Azure (AKS).

**Estado (2026-07-28, actualizado):** el usuario consultó a arquitectura y la base de datos **no debe ser compartida** — cada proyecto necesita un recurso de base de datos nuevo y propio (aislamiento real, no una DB más sobre el servidor de la plataforma). Esto reabre la decisión de estrategia de base de datos — ver la sección dedicada más abajo con las 2 opciones a presentar a arquitectura para que definan. El resto del plan (Blob Storage para la SPA, PostgREST en AKS) sigue vigente sin cambios.

---

## Contexto

El golden path `angular-crud-postgres` (en `golden-paths/h1-foundation/angular-crud-postgres/`) hoy solo genera el código Angular y lo publica en GitHub (`fetch:template` + `publish:github`). No despliega nada. El objetivo es que, además, automatice el despliegue completo:

- La SPA Angular se sirve desde **Azure Blob Storage** (static website hosting) — barato, sin servidor que mantener.
- **PostgREST** (la capa que expone Postgres como API HTTP) corre como contenedor en el **AKS ya desplegado**, vía el mismo patrón ArgoCD/Kustomize que ya funciona en `gitops-deployment` (`golden-paths/h2-enhancement/gitops-deployment`).
- La **base de datos** es un recurso nuevo y propio por proyecto (no compartido) — la estrategia concreta (Azure PaaS dedicado vs. contenedor en AKS) queda pendiente de que arquitectura elija entre las 2 opciones detalladas más abajo.

Decisiones confirmadas con el usuario:
1. PostgREST corre en el AKS existente (no Container Apps, no Functions) — más barato porque el cómputo del cluster ya está pago.
2. ~~La base de datos es compartida~~ — **revertido 2026-07-28 por indicación de arquitectura**: cada proyecto necesita su propio recurso de base de datos, no una DB más en el servidor compartido de la plataforma. Ver sección "Decisión pendiente de Arquitectura" abajo.

Esto resuelve además 2 de los "pendientes" que había en memoria sobre este golden path: no hace falta decidir dónde publicar una imagen de contenedor custom ni construir un pipeline de build+push, porque **ninguna de las dos piezas nuevas requiere una imagen propia** — Blob Storage no corre imágenes, y PostgREST usa la imagen pública oficial `postgrest/postgrest`. Esto no cambia con la revisión de arquitectura.

## Decisión pendiente de Arquitectura: estrategia de base de datos

Arquitectura pidió que cada proyecto tenga un recurso de base de datos **nuevo y aislado**, no una DB más sobre el Postgres compartido de la plataforma. Hay dos formas concretas de lograr ese aislamiento, con trade-offs distintos de costo/velocidad/operación. Falta que arquitectura elija una antes de escribir el step de aprovisionamiento en `template.yaml`.

### Opción A — Azure Database for PostgreSQL Flexible Server dedicado por proyecto
Reutilizar el módulo Terraform que ya existe (`terraform/modules/databases`), instanciándolo **una vez por proyecto** en vez de compartir el servidor de la plataforma.
- Servicio administrado por Azure: backups automáticos, parches, HA opcional, red privada — mismo nivel de garantía que ya tiene el Postgres de Backstage, pero un servidor propio por proyecto.
- Aprovisionamiento vía `terraform apply` (minutos, no segundos): el step de Backstage dispara un workflow de GitHub Actions con su propio Terraform state por proyecto (mismo patrón OIDC que ya usa `common/azure-infrastructure/.github/workflows/azure-infrastructure.yml`), no un script SQL suelto.
- Costo: escala linealmente — cada proyecto paga su propio servidor corriendo 24/7 (mínimo SKU Burstable `B_Standard_B1ms`).
- Es el patrón "servicio administrado" que la plataforma ya usa para todo lo demás (Redis, el Postgres de Backstage) — más alineado con lo que arquitectura probablemente espera si el pedido es por gobierno/compliance.

### Opción B — Postgres como contenedor dedicado dentro del AKS existente
Cada proyecto obtiene su propio Postgres corriendo como `StatefulSet` + PVC + Secret en el cluster — mismo patrón que ya usan en local con el contenedor `postgres-dev`, llevado a Kubernetes.
- Sigue siendo un recurso único y aislado por proyecto (su propio proceso, sus propios datos, su propio namespace) — pero es un contenedor en el cluster que ya pagan, no un servicio PaaS nuevo de Azure.
- Mucho más rápido y barato de aprovisionar: mismo ArgoCD/Kustomize que ya se diseñó para PostgREST en este plan, sin Terraform apply nuevo por proyecto.
- Backups, alta disponibilidad y actualizaciones de versión pasan a ser responsabilidad propia, no de Azure.

**Recomendación:** si el pedido de arquitectura es por gobierno/compliance (aislamiento real, backups garantizados, auditoría por recurso), la Opción A es la esperable. La Opción B tiene sentido si todavía están en modo MVP/demo y priorizan velocidad y costo por sobre HA/backups desde el día uno. Queda a criterio de arquitectura.

## Hallazgos clave de la exploración del repo

- `terraform/modules/databases`: el Flexible Server de la plataforma ya existe con `public_network_access_enabled = false`, en un subnet delegado (`postgres_subnet_id`) dentro de la misma VNet que usa AKS (`aks_nodes`/`aks_pods` subnets, ver `terraform/modules/networking/outputs.tf`). Conclusión: **cualquier Postgres nuevo (compartido o dedicado) solo es alcanzable desde dentro de la VNet** — por eso PostgREST tiene que correr en AKS (o algo en la misma VNet), no en un servicio externo. El módulo ya expone secrets en Key Vault (`postgresql_connection_string`, `postgresql_password`, ver `terraform/modules/databases/outputs.tf`) y es directamente reutilizable para instanciar un servidor dedicado por proyecto (Opción A de la sección de arquitectura).
- Si arquitectura elige la Opción B (contenedor en AKS), el aprovisionamiento sería un **Job de Kubernetes** que corre `psql` contra un Postgres propio del proyecto (StatefulSet) para crear la DB/rol/tabla — mismo patrón que ya usaron en local (`postgres-dev` + script `init.sql`), pero dentro de AKS. Si eligen la Opción A, el aprovisionamiento es un `terraform apply` por proyecto vía GitHub Actions con OIDC, sin Job de Kubernetes.
- `golden-paths/h2-enhancement/gitops-deployment/template.yaml` ya tiene el patrón completo a reutilizar: **External Secrets** (parámetro `secrets`, step `generate-secrets`, fetch de `./skeleton/external-secrets`) para traer secretos de Key Vault a K8s, y **dos repos separados** (repo de app + repo `-gitops`, éste último con `publish:github` + `catalog:register`). Se replica esa misma estructura acá.
- El skeleton de `angular-crud-postgres` ya tiene carpetas `base/`, `overlays/{dev,prod}/`, `argocd/application.yaml` armadas de una sesión anterior, pero **apuntan al patrón viejo** (un solo Deployment con imagen `${{ values.image }}` que corre nginx sirviendo Angular + proxy a PostgREST). Hay que reescribir `base/deployment.yaml` para que sea el Deployment de **PostgREST** (imagen pública `postgrest/postgrest:v12.2.0`), no de la app.
- `common/azure-infrastructure/deploy/azure/main.bicep` ya crea un Storage Account (`StorageV2`, `allowBlobPublicAccess: false`) reutilizable como base — falta habilitarle static website hosting, lo cual **no se hace vía Bicep** (no es una propiedad ARM del recurso storageAccount) sino vía `az storage blob service-properties update --static-website` en el workflow de despliegue, igual que ya hace `common/azure-infrastructure/.github/workflows/azure-infrastructure.yml` con `az login` federado (OIDC).
- `src/environments/environment.ts` del Angular ya tiene el campo `apiUrl` con un comentario anticipando esto ("Base URL of the PostgREST API") pero hoy vale `/api` (relativo, asumía el proxy nginx). Hay que parametrizarlo por template.
- CORS: como la SPA (origen Blob Storage) y PostgREST (origen ingress de AKS) van a ser dominios distintos, ya no existe el proxy nginx que evitaba CORS en local. Se resuelve con la anotación `nginx.ingress.kubernetes.io/enable-cors: "true"` en el Ingress de PostgREST (mismo `ingressClass: nginx` que ya usa `gitops-deployment`) — no hace falta introducir Front Door/CDN para este MVP.

## Arquitectura resultante

```
Usuario → Blob Storage ($web, static website)  →  descarga Angular compilado
Angular (en el navegador) → fetch() → Ingress nginx (AKS, CORS habilitado) → Service → PostgREST (pod en AKS)
PostgREST → Postgres dedicado del proyecto (mismo VNet; Flexible Server propio [Opción A] o StatefulSet en AKS [Opción B])
```

## Cambios a implementar

### 1. Repo de la app (`angular-crud-postgres/skeleton/app`)
- `src/environments/environment.ts`: reemplazar `apiUrl: '/api'` por `apiUrl: '${{ values.apiUrl }}'` (URL pública del Ingress de PostgREST, ej. `https://${{values.name}}-api.<dominio-o-ip-del-ingress>`).
- Dejar `Dockerfile`/`nginx.conf`/`docker-compose.yml` intactos (siguen sirviendo para desarrollo local), aunque ya no se usan en el despliegue cloud.
- Nuevo: `.github/workflows/deploy-blob.yml` — build Angular (`npm ci && npm run build`), login OIDC a Azure (copiar el bloque `az login --service-principal --federated-token` de `common/azure-infrastructure/.github/workflows/azure-infrastructure.yml`), luego:
  ```
  az storage blob service-properties update --account-name <storage> --static-website --index-document index.html --404-document index.html
  az storage blob upload-batch --account-name <storage> --destination '$web' --source dist/<app>/browser --overwrite
  ```
- Nuevo: `infra/main.bicep` — copia mínima de `common/azure-infrastructure/deploy/azure/main.bicep` (Storage Account + App Insights + Log Analytics), reusando su lógica de naming (`storageName`). Se sirve vía `fetch:template` desde `../../common/azure-infrastructure` como ya hace `gitops-deployment` (no reinventar, referenciar el común).

### 2. Repo GitOps (`${{ values.name }}-gitops`, repo nuevo, separado del repo de la app)
- `base/deployment.yaml`: reescribir para Deployment de **PostgREST** — imagen `postgrest/postgrest:v12.2.0`, env vars `PGRST_DB_URI`, `PGRST_DB_SCHEMAS=public`, `PGRST_DB_ANON_ROLE=web_anon`, todas vía `secretKeyRef` a un Secret sincronizado por External Secrets (reusar `golden-paths/h2-enhancement/gitops-deployment/skeleton/external-secrets` como referencia, apuntando al secret `postgresql_connection_string`/`postgresql_password` que ya existe en Key Vault).
- `base/ingress.yaml` (nuevo): Ingress `nginx` con `nginx.ingress.kubernetes.io/enable-cors: "true"`, host `${{ values.name }}-api.<dominio>`.
- Base de datos — **depende de la opción que elija arquitectura** (ver "Decisión pendiente de Arquitectura"):
  - **Si Opción A (Flexible Server dedicado):** no hay manifiesto de DB en el repo gitops — la DB se provisiona antes, vía un workflow de Terraform aparte (nuevo `infra-db/` en el repo de la app o un repo de infra dedicado, con su propio state). El repo gitops solo necesita el `ExternalSecret` apuntando a las credenciales que ese Terraform dejó en Key Vault.
  - **Si Opción B (StatefulSet en AKS):** nuevo `base/postgres-statefulset.yaml` (StatefulSet + PVC + Service, imagen `postgres:16-alpine`) más `base/db-init-job.yaml` — Kubernetes `Job` (`ArgoCD PreSync hook`) que corre un `ConfigMap` con el `init.sql` del proyecto (adaptar `angular-crud-postgres/skeleton/app/database/init.sql`, ya existente) contra ese Postgres propio. Crea la DB `${{ values.dbName }}`, el rol `web_anon` y la tabla `tasks` — mismo script que ya corrieron a mano en local (`postgres-dev`/`appdb`).
- `argocd/application.yaml`: ya está listo (apunta a `${{ values.name }}-gitops`, `overlays/dev`) — no requiere cambios.
- `overlays/{dev,prod}/patch.yaml`: ajustar réplicas/recursos ya existentes para que apliquen al nuevo Deployment de PostgREST en vez de al Deployment viejo de la app.

### 3. `template.yaml` (rewiring completo)
- Agregar parámetro `apiUrl` (o derivarlo de un patrón fijo tipo `https://${{ parameters.name }}-api.<dominio-ingress>` — confirmar dominio/IP del ingress-nginx del cluster antes de fijarlo, ver Preguntas abiertas).
- Mantener el `fetch:template` actual (`./skeleton/app` → repo de la app) y agregar steps:
  - `fetch` de `../../common/azure-infrastructure` → carpeta `infra/` del repo de la app (Storage Account).
  - `publish:github` del repo de la app (ya existe) + **agregar `catalog:register`** (falta hoy, es uno de los pendientes de memoria).
  - `fetch:template` de `./skeleton/base`, `./skeleton/overlays`, `./skeleton/argocd`, `./skeleton/db-init` → carpeta `output/` del repo gitops (mismo patrón multi-fetch que usa `gitops-deployment`).
  - `publish:github` del repo `${{ parameters.name }}-gitops` (repoVisibility `internal`, como en `gitops-deployment`) + `catalog:register`.
- `output.links`: agregar el link al repo gitops y a la URL pública de Blob Storage (`https://<storage>.z*.web.core.windows.net`).

## Preguntas abiertas
- **BLOQUEANTE:** ¿Opción A o B para la base de datos? (ver sección dedicada) — define si el step de aprovisionamiento es un `terraform apply` por proyecto o un manifiesto más en el repo gitops. Sin esto no se puede escribir el step de base de datos en `template.yaml`.
- (no bloquean el resto del plan, pero sí el valor exacto de `apiUrl`/`ingressHost`) ¿Cuál es el hostname o IP pública ya asignada al Ingress Controller nginx del AKS de Open Horizons?
- ¿Nombre/convención para el Storage Account por proyecto? (límite de 24 caracteres alfanuméricos de Azure — reusar la lógica `take('st${safeName}${environment}', 24)` ya existente en el bicep común)

## Verificación
1. `az deployment group what-if` sobre el bicep del Storage Account antes de aplicar (mismo workflow que ya usa `azure-infrastructure.yml` en modo `what-if`).
2. Generar un proyecto de prueba desde Backstage cloud con este template, confirmar:
   - Repo de la app creado con el workflow `deploy-blob.yml` corriendo en verde y el sitio accesible en la URL de static website.
   - Repo `-gitops` creado, ArgoCD sincronizando, pod de PostgREST `Running`, Job `db-init` `Completed`.
   - `curl https://<apiUrl>/tasks` responde JSON (confirma PostgREST conectado a la DB nueva).
   - Angular servido desde Blob Storage puede hacer `fetch` a `/tasks` sin error de CORS en la consola del navegador.
3. Confirmar en el catálogo de Backstage que ambos componentes (app y gitops) aparecen registrados.
