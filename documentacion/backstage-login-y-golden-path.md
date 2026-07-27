# Backstage local: login con GitHub y golden path Angular+Postgres

Documento de trabajo en curso. Registra lo hecho hasta el 2026-07-27 en dos frentes relacionados pero independientes sobre el mismo Backstage local: (1) reproducir un bug de login de producción, y (2) construir un golden path de scaffolder con despliegue a Kubernetes.

---

## Parte 1 — Login con GitHub

### Objetivo
Replicar en local un bug de login (GitHub OAuth) que ocurre en el despliegue real de Open Horizons en Azure AKS, para llevar evidencia concreta al departamento de arquitectura de la empresa. No es una prueba exploratoria: es el caso de sospecha para escalar internamente.

### Dónde vive el Backstage local
- Repo: `~/projects/ohorizons-lastest/backstage` (fork `ramisistemas/ohorizons-lastest` de `github.com/Ohorizons/ohorizons-lastest`)
- Frontend: puerto **3001** · Backend: puerto **7007**
- Requiere **Node 22** vía `nvm` (el Node global del sistema es v25, no soportado por Backstage)
- Credenciales OAuth y demás variables de entorno están en `~/projects/ohorizons-lastest/backstage/.env` (gitignored, no se documentan valores acá)

### Cómo levantarlo
```bash
cd ~/projects/ohorizons-lastest/backstage
source ~/.nvm/nvm.sh && nvm use 22
set -a && source .env && set +a
yarn start
```

### Cómo reiniciarlo (necesario tras tocar `app-config.yaml` / `app-config.local.yaml`)
El backend **no** recarga la configuración en caliente — hay que matar los procesos y volver a levantar:
```bash
pkill -f "backstage-cli repo start"
pkill -f "node /home/ramisistemas/.local/bin/yarn start"
# esperar a que liberen los puertos 3001/7007, luego repetir el bloque de arriba
```
Para confirmar que el backend ya respondió antes de seguir probando:
```bash
curl -s -o /dev/null -w "%{http_code}" http://localhost:7007/api/catalog/entities
```

### OAuth App de GitHub (pruebas locales)
- Client ID: `Ov23liED5cfCV2iKaSTU`
- Homepage: `http://localhost:3001`
- Callback: `http://localhost:7007/api/auth/github/handler/frame`
- Client Secret: **solo en `.env`**, no se repite acá
- Cuenta GitHub del usuario: `ramisistemas`
- Organización: `rami-engineer` (con `magom2024-blip` invitado como Member)
- Fork del repo: `github.com/ramisistemas/ohorizons-lastest`

### Resultado de la prueba
Login con GitHub probado y funcionando (frontend `:3001`, backend `:7007`).

### Hallazgo de seguridad — CONFIRMADO
`app-config.yaml` trae `dangerouslyAllowSignInWithoutUserInCatalog: true` en el resolver de GitHub. Se probó loguearse con una cuenta de GitHub que **no** es miembro de `rami-engineer` y **entró sin problema**. Pendiente decidir si se restringe el acceso solo a miembros de la organización.

### Diagnóstico del bug en producción (Azure AKS) — BLOQUEADO
El despliegue real en AKS tiene el login roto. Causa hipotetizada (casi confirmada por la reproducción local): se creó la organización de GitHub e invitó gente, pero **nunca se creó una OAuth App de GitHub** ni se cargaron `GITHUB_APP_CLIENT_ID` / `GITHUB_APP_CLIENT_SECRET` como secret en el cluster. Son pasos independientes — invitar gente a la org no genera credenciales de OAuth.

**Pendiente para destrabar producción:**
1. Crear la OAuth App en GitHub con el callback real: `https://<dominio-de-producción>/api/auth/github/handler/frame`
2. Cargar esas credenciales como secret en AKS: `kubectl create secret generic backstage-secrets --from-env-file=.env` (según el README del repo)

### Otras carpetas relacionadas (no confundir)
- `~/ohorizons/backstage` — copia distinta y anterior (~15-21 julio), sin `node_modules`. Parece el intento original que no llegó a levantar. No se investigó por qué falló.
- El repo completo `~/projects/ohorizons-lastest` incluye mucho más que Backstage: Terraform (16 módulos), ArgoCD, Golden Paths (36 templates), agent APIs en Python — pensado para Azure AKS.

---

## Parte 2 — Golden path `angular-crud-postgres`

### Objetivo
Construir un golden path real de Backstage que además de generar el código (Angular + Postgres/PostgREST) también arme y publique los manifiestos de despliegue a Kubernetes, siguiendo el mismo patrón que ya usa `golden-paths/h2-enhancement/gitops-deployment` en este repo (Kustomize base/overlays + ArgoCD Application + repo `-gitops` separado + registro en catálogo).

### Historia
1. Se armó primero como prototipo suelto en `~/backstage-templates/angular-crud-postgres/` (carpeta simple, **nunca fue un repositorio git**).
2. Se generó una instancia de prueba y se publicó en GitHub: `github.com/ramisistemas/mi-proyecto-angular` (esto es un producto del template, no el template en sí).
3. Se migró el template a su ubicación definitiva: `~/projects/ohorizons-lastest/golden-paths/h1-foundation/angular-crud-postgres/`.
4. Se borró la carpeta original `~/backstage-templates/` (ya no se usa).

### Registro en el catálogo de Backstage
Se agregó la entrada en `backstage/app-config.yaml` (junto a los otros templates H1):
```yaml
- type: file
  target: ../../../golden-paths/h1-foundation/angular-crud-postgres/template.yaml
  rules:
    - allow: [Template]
```

**Bug preexistente encontrado y corregido:** `app-config.local.yaml` tenía su propio bloque `catalog.locations` que **reemplazaba por completo** (no fusionaba) la lista de `app-config.yaml`, dejando ocultos los otros 35 golden paths y las locations de `org.yaml`/`entities.yaml` — solo se veía 1 template en todo el catálogo. Se quitó ese bloque de `app-config.local.yaml`. Si en el futuro el catálogo muestra muy pocos templates, revisar ese archivo primero.

### Templates vs Catalog — aclaración conceptual
- **Templates** (menú "Create") = el catálogo de moldes disponibles para generar cosas nuevas.
- **Catalog** (menú "Catalog") = el inventario de lo que ya existe/está desplegado (Components, APIs, Resources, etc.).

Un Template es técnicamente también una entidad de catálogo, pero la UI los separa. Para que un proyecto generado por este golden path aparezca en "Catalog" como Component, el `template.yaml` necesita un step `catalog:register` al final — **hoy no lo tiene**, por eso `mi-proyecto-angular` existe como repo en GitHub pero no aparece en el Catalog de Backstage.

### Estructura actual del skeleton (reordenada el 2026-07-27)
```
golden-paths/h1-foundation/angular-crud-postgres/
├── template.yaml
└── skeleton/
    ├── app/          código Angular + Postgres + PostgREST (Dockerfile, angular.json,
    │                 catalog-info.yaml, database/, docker-compose.yml, nginx.conf,
    │                 package.json, proxy.conf.json, src/, tsconfig*.json, README.md)
    ├── base/         deployment.yaml, service.yaml, kustomization.yaml
    ├── overlays/
    │   ├── dev/      patch.yaml (1 réplica) + kustomization.yaml
    │   └── prod/     patch.yaml (2 réplicas) + kustomization.yaml
    └── argocd/       application.yaml (Application de ArgoCD completa, con
                      syncPolicy automatizado)
```

Motivo de la carpeta `app/`: el step `fetch` original hacía `url: ./skeleton` (barría todo). Al sumar `base/`, `overlays/` y `argocd/` como hermanos directos, ese mismo step arrastraría los manifiestos de Kubernetes hacia el repo de la app por error. Por eso el código se movió a `skeleton/app/` y el step se actualizó a `url: ./skeleton/app`.

### `template.yaml` — estado actual

**Parámetros:**
| Parámetro | Default | Uso |
|---|---|---|
| `name` | `mi-proyecto-angular` | `package.json`, `angular.json`, `catalog-info.yaml`, nombre del repo en GitHub |
| `dbName` | `appdb` | Nombre de la base Postgres |
| `owner` | `user:default/ramisistemas` | Owner del componente en `catalog-info.yaml` |

**Steps actuales:**
1. `fetch` (`fetch:template`) → copia `./skeleton/app` con los valores de `name`, `dbName`, `owner`
2. `publish` (`publish:github`) → crea el repo nuevo `github.com/ramisistemas/<name>` (privado, rama `main`)

**Nota sobre el nombre del proyecto:** el campo `name` se controla desde el formulario del front de Backstage al ejecutar el template (`http://localhost:3001/create`) — el `default:` en el YAML es solo el valor pre-cargado, no un valor fijo. Volver a correr el template con otro `name` crea un **repo nuevo**, no renombra el existente. Para renombrar un repo ya creado hay que hacerlo aparte: `gh repo rename <nuevo-nombre> --repo ramisistemas/<nombre-actual>`.

### Pendiente — 3 decisiones bloqueantes (sin responder al 2026-07-27)
1. **Dónde se publica la imagen del contenedor** (Docker Hub / GHCR / ACR de Azure) — el `base/deployment.yaml` ya tiene el placeholder `${{ values.image }}` esperando este dato, que todavía no es un parámetro real del template.
2. **Repo GitOps separado** (`angular-crud-postgres-gitops`, mismo patrón que `gitops-deployment`) **o mezclado** con el repo de la app.
3. **Cluster/namespace destino real** — `argocd/application.yaml` hoy asume el cluster donde corre ArgoCD (`https://kubernetes.default.svc`) y namespace `${{ values.name }}`, pero no está confirmado si es el AKS de producción (ver Parte 1, todavía bloqueado por el tema de login) o un cluster de pruebas distinto.

### Falta además, más allá de las 3 decisiones
- **CI/CD para build+push de la imagen**: no existe ningún workflow todavía. Falta un step `fetch:template` que genere `.github/workflows/build-push.yaml` dentro de `skeleton/app/`.
- **Steps de despliegue en `template.yaml`**: agregar 3 `fetch:template` (uno por `base/`, `overlays/`, `argocd/`), el `publish:github` del repo GitOps (si se separa) y el `catalog:register` final.

### Estado de git
Los cambios en `~/projects/ohorizons-lastest` (nuevo golden path completo + la línea agregada en `app-config.yaml`) están **sin commitear** — decisión explícita del usuario de no commitear todavía. No hacer commit/push sin confirmación.

### Verificación rápida del catálogo (para usar después de cualquier cambio)
```bash
# Template específico
curl -s http://localhost:7007/api/catalog/entities/by-name/template/default/angular-crud-postgres

# Total de templates (debería dar 36, o más si se agregan otros)
curl -s "http://localhost:7007/api/catalog/entities?filter=kind=template" | python3 -c "import json,sys; print(len(json.load(sys.stdin)))"

# Componentes registrados (para confirmar si mi-proyecto-angular ya aparece)
curl -s "http://localhost:7007/api/catalog/entities?filter=kind=component" | python3 -c "import json,sys; [print(e['metadata']['name']) for e in json.load(sys.stdin)]"
```
