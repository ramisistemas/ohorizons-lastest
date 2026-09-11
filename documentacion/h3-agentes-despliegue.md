# H3 Innovation — cómo se despliegan los agentes de IA en `ohorizons-mvp`

> Investigación de implementación (2026-07-31), hecha directamente sobre el repo cloud
> `SuraOhorizons/ohorizons-mvp` (copia local en `~/ohorizons-mvp`), no sobre el fork de
> desarrollo `ramisistemas/ohorizons-lastest`. Los dos repos difieren en un punto importante
> para este análisis — ver sección 3.

## TL;DR

- Lo único que hoy se **despliega de verdad** como "agente de IA" en `ohorizons-mvp` es un
  **único servicio de plataforma**, `foundry-agents` (el gateway L6), desplegado **una sola vez**
  vía Terraform + ArgoCD — no algo que se genera por instancia.
- **No es igual al flujo de `tasks-api`.** `tasks-api` es un golden path de Backstage: cada vez
  que alguien lo usa, se genera un repo nuevo, independiente, self-service. `foundry-agents` no
  se "crea" así — es infraestructura compartida, como el propio Backstage.
- **`ohorizons-mvp` no tiene ningún golden path de H3** (ni `h2-enhancement`). Solo existen los
  6 templates de `h1-foundation`. Los golden paths de H3 (`foundry-agent`, `multi-agent-system`,
  `rag-application`, etc. — el equivalente conceptual a "tasks-api pero para agentes") solo
  existen en el fork personal `ramisistemas/ohorizons-lastest`, y ahí son en su mayoría
  plantillas incompletas (stubs), no algo funcional.
- El ambiente `dev` de este repo (`terraform/environments/dev.tfvars`) ya tiene
  `enable_ai_foundry = true` y `enable_foundry_agents = true` — es decir, H3 está pensado para
  desplegarse en este entorno, no es solo teoría de ADR.
- Encontré dos inconsistencias operativas concretas en los manifiestos de `foundry/k8s/` que
  conviene tener en cuenta antes de asumir que el "deploy vía ArgoCD" corre limpio hoy — secciones 4.2 y 4.3.
- **"Desplegar H3" no es un solo paso.** El script orquestador separa provisión de infra
  (Terraform) del registro en ArgoCD (fase aparte), y deja al menos 3 pasos manuales sin
  automatizar (secret de credenciales, conflicto de manifiestos, wireo de Backstage) — sección 5.

---

## 1. Infraestructura de H3 (breve)

`terraform/modules/ai-foundry` (`main.tf`, 406 líneas) provisiona, todo opt-in vía flags:

| Recurso | Gate |
|---|---|
| Azure OpenAI + model deployments (gpt-5.1, gpt-4o, gpt-4o-mini, text-embedding-3-large) | `openai_config.enabled` |
| Azure AI Search | `ai_search_config.enabled` |
| Azure AI Content Safety | `content_safety_config.enabled` |
| Cosmos DB "enterprise memory" (AAD-only, `local_authentication_disabled = true`) | `foundry_agents_config.enabled && foundry_agents_config.cosmos_memory.enabled` |

Activación real, dos capas:
- **Terraform** (`terraform/variables.tf`): `enable_ai_foundry` (default `false`), `enable_foundry_agents` (default `false`, requiere `enable_ai_foundry`). En `terraform/environments/dev.tfvars` **ambos están en `true`**.
- **Sizing profile** (`config/sizing-profiles.yaml`): perfil `small` trae todo H3 apagado; desde `medium` se activa (`foundry_agents.enabled: true`, `replicas: 2`, `prompt_cache.backend: redis`, `cosmos_memory.enabled: true`).

Justificación formal en `docs/architecture/adr/0005-foundry-resources-gated-to-h3.md` (costo/FinOps: H1/H2 corren sin pagar runtime de IA) y `docs/architecture/adr/0004-memory-and-cache-backends.md` (por qué Cosmos para memoria durable vs. Redis para caché semántico son backends separados).

**No hay golden paths H2 ni H3 en este repo** — `golden-paths/` solo tiene `h1-foundation/` (6 templates: `web-application`, `new-microservice`, `tasks-api` [agregado por vos], `basic-cicd`, `documentation-site`, `infrastructure-provisioning`) y `common/`. Esto es relevante para la sección 3.

---

## 2. El agente real: `foundry-agents` (gateway L6)

### 2.1 Qué es

`foundry/agents-service/` — servicio Python/FastAPI. Componentes (`app/`):

| Archivo | Rol |
|---|---|
| `main.py` | API OpenAI-compatible (`/v1/chat/completions`, `/v1/models`) + endpoints por agente (`/v1/agents/{id}/chat`) |
| `agents.py` | 4 agentes: **architect, devops, sre, platform** (system prompts fijos en código) |
| `azure_openai.py` | Cliente con auth por API key o AAD client-credentials |
| `cache.py` | Caché jerárquica exacta + semántica (Redis + embeddings) |
| `cosmos_memory.py` | Memoria durable, Cosmos AAD-only |
| `a2a.py` | Protocolo agent-to-agent v1.0 |
| `tool_hooks.py` | Hooks pre/post tool-use (cost gate, aprobación humana) |
| `telemetry.py` | Emite evento de 21 campos a Application Insights |

Los "4 agentes" **no son 4 despliegues distintos** — son 4 configuraciones (system prompt + herramientas) dentro del **mismo proceso/pod**. Agregar un 5º agente significa editar `agents.py` y redeployar el mismo servicio, no crear un repo nuevo.

### 2.2 Cómo se despliega

`foundry/k8s/README.md` lo dice explícito: *"Runs in the `ai-services` namespace on AKS. Two deploy paths: GitOps (recommended) [...] Gated to H3 (`enable_foundry_agents=true`). Manual: apply the manifests in order."*

**GitOps real**: `argocd/apps/foundry-agents.yaml` — `Application` de ArgoCD:
```yaml
metadata:
  labels:
    platform.open-horizons/tier: h3-innovation
    platform.open-horizons/layer: l5-agentic-execution
  annotations:
    argocd.argoproj.io/sync-wave: "6"   # después de plataforma + AI services
spec:
  source:
    repoURL: https://github.com/${GITHUB_ORG}/${GITHUB_REPO}.git   # este mismo repo
    path: foundry/k8s
  destination:
    namespace: ai-services
  syncPolicy:
    automated: { prune: true, selfHeal: true }
```
Sincroniza directo desde este repo (no un repo GitOps separado), namespace `ai-services`, con `selfHeal` automático.

### 2.3 Cómo se conecta Backstage

`foundry/k8s/README.md` documenta el wiring del plugin `ai-chat` de Backstage:
```yaml
aiChat:
  providers:
    - id: openai
      baseUrl: 'http://foundry-agents.ai-services.svc.cluster.local:8080/v1'
      token: ${FOUNDRY_AGENTS_API_KEY}
      model: gpt-5.1
```
(No verifiqué que esto ya esté efectivamente escrito en `app-config.production.yaml` de Backstage — no aparece ahí hoy; es documentación de referencia para cuando se quiera activar.)

---

## 3. ¿Es igual al flujo de `tasks-api`? — No, son dos modelos distintos

| | `tasks-api` (golden path H1) | `foundry-agents` (gateway L6) |
|---|---|---|
| **Qué genera** | Un repo nuevo por cada uso (`ohorizons-tasks-api`, `mi-otro-servicio`, etc.) | Nada — es un servicio único de plataforma |
| **Quién lo dispara** | Cualquier developer, self-service, desde "Create" en Backstage | Platform engineering, una vez, vía Terraform + ArgoCD |
| **Cuántas instancias** | Tantas como repos se generen | Una sola, compartida por todos los agentes/equipos |
| **Cómo se despliega el resultado** | Hoy: solo `fetch` + `publish:github` (repo publicado, sin CI/CD ni K8s automático — ver memoria de tasks-api) | ArgoCD Application dedicada, sync-wave 6, `selfHeal: true` |
| **Analogía correcta** | Como generar un microservicio nuevo | Como el propio Backstage: infraestructura de plataforma, no "un proyecto más" |

**El golden path que sí sería el equivalente conceptual de `tasks-api` para agentes** (un template de Backstage que scaffoldea un agente nuevo como repo propio) es `golden-paths/h3-innovation/foundry-agent` — pero **esa carpeta no existe en `ohorizons-mvp`**, solo en el fork `ramisistemas/ohorizons-lastest`, y ahí (investigado antes) es un scaffold con archivos stub de 1-2 líneas (`kubernetes/deployment.yaml` = `"apiVersion: apps/v1"`, funciones `pass`/`return {}`), sin `argocd/application.yaml` real, con un link de salida a ArgoCD **hardcodeado como ejemplo** (`https://argocd.example.com/applications/...`), no generado de verdad. Es decir: si mañana se sube esa carpeta a `ohorizons-mvp`, el flujo "Create → scaffold → publish" funcionaría igual que `tasks-api`, pero el resultado sería un esqueleto sin backend real conectado al gateway — no llega a producción solo.

**Conclusión de esta sección**: hoy, en `ohorizons-mvp`, no existe un flujo self-service para "crear un agente nuevo" análogo a `tasks-api`. Lo único desplegable es el gateway único `foundry-agents`.

---

## 4. Flujo end-to-end real (lo que sí funciona hoy en este repo)

```
1. Terraform (terraform/environments/dev.tfvars: enable_ai_foundry=true, enable_foundry_agents=true)
   └─> module.ai_foundry provisiona Azure OpenAI + Cosmos DB (enterprise_memory)

2. ArgoCD (ya desplegado como parte de la plataforma, ver deploy order H1→H2→H3)
   └─> Application "foundry-agents" (argocd/apps/foundry-agents.yaml, sync-wave 6)
       sincroniza foundry/k8s/ → namespace ai-services

3. Pod foundry-agents corriendo (imagen ghcr.io/ohorizons/ohorizons-foundry-agents,
   o modo "source-mounted" temporal — ver 4.1) expone /v1/chat/completions, /v1/agents/{id}/chat

4. Backstage (ai-chat plugin) apunta a
   http://foundry-agents.ai-services.svc.cluster.local:8080/v1 (config manual, no automática)
```

### 4.1 Detalle no documentado antes: modo "source-mounted" (bootstrap sin imagen)

`foundry/k8s/` tiene **dos variantes de Deployment**:
- `deployment.yaml` — basado en imagen publicada en GHCR (el camino "normal" de producción).
- `deployment-source.yaml` — **monta el código Python directo desde una ConfigMap** (`foundry-agents-source`) y lo instala en un `initContainer` (`pip install --target=/opt/app/.deps`) al arrancar el pod, sin necesitar imagen propia. Comentario explícito en el archivo: *"Source-mounted Deployment — runs the service from a ConfigMap (no image build). After image is published to GHCR, switch to deployment.yaml."*
- La ConfigMap se genera con `foundry/k8s/render-source-cm.sh`, que empaqueta los `.py` del servicio — **pero el script tiene una ruta rota**: apunta a `.../new-features/foundry/agents-service` (relativa desde `foundry/k8s/`), y esa carpeta `new-features/` **no existe** en este repo (el código real está en `foundry/agents-service/`, no en `new-features/foundry/agents-service/`). Es decir, ese script quedó de un reordenamiento de carpetas y no corre tal cual está.

Este modo "source-mounted" es, en esencia, el mismo espíritu que el flujo de scaffolding de `tasks-api` (arrancar sin necesitar todavía un pipeline de imagen/GHCR), pero aplicado al servicio único de plataforma, no a instancias generadas por developers.

### 4.2 Riesgo operativo: dos Deployments con el mismo nombre en la misma carpeta

`deployment.yaml` y `deployment-source.yaml` **ambos definen `kind: Deployment, name: foundry-agents, namespace: ai-services`**, y **no hay `kustomization.yaml`** en `foundry/k8s/` que excluya uno de los dos. La `Application` de ArgoCD apunta a `path: foundry/k8s` como directorio plano — así que, tal como está el repo hoy, un sync de esa Application intentaría aplicar **ambos manifiestos con la misma identidad de recurso**, lo cual típicamente ArgoCD reporta como error de comparación (recurso duplicado) en vez de desplegar limpiamente. Antes de confiar en "GitOps automático" para este servicio, hay que decidir cuál de los dos Deployment usar y sacar el otro del path (o mover uno a una subcarpeta separada / usar Kustomize con overlays).

### 4.3 Riesgo operativo: `secret-template.yaml` con `selfHeal: true`

`secret-template.yaml` define el Secret `foundry-agents-config` con un campo `SERVICE_API_KEY: "REPLACE_WITH_RANDOM_TOKEN"` (placeholder literal) y valores de Cosmos que sí parecen reales/concretos (`COSMOS_ENDPOINT: "https://cosmos-openhorizons-dev-agents.documents.azure.com:443/"`). El `README.md` de `foundry/k8s/` instruye a reemplazar `SERVICE_API_KEY` manualmente después de aplicar. Pero como la `Application` de ArgoCD tiene `selfHeal: true` y sincroniza todo `foundry/k8s/` (incluido este archivo), **cualquier edición manual del secret en el cluster sería revertida automáticamente** al placeholder en el próximo ciclo de reconciliación — contradice la instrucción manual del propio README. El README marca esto como `EXTENSION_POINT` (reemplazar por External Secrets Operator + Workload Identity en producción), pero mientras eso no se implemente, el secret placeholder puede pisar un valor real cada vez que ArgoCD reconcilia.

### 4.4 Tercer camino paralelo, no relacionado: `agent-api` (chat de Backstage)

Existe además `backstage/server/agent-api` (+ variantes `agent-api-sk`, `agent-api-maf`, `agent-api-impact`) — el motor de los **7 agentes del chat de Backstage** (compass, guardian, sentinel, lighthouse, forge, router, orchestrator), **distinto** de los 4 agentes de `foundry-agents`. Confirmé que también está presente en este repo (`backstage/k8s/templates/agent-api-deployment.yaml.tmpl`), desplegado en el mismo namespace `ai-services` pero **vía script de renderizado + `kubectl apply` manual** (`scripts/render-k8s.sh`), no GitOps continuo. Comparte el Azure OpenAI de fondo con `foundry-agents`, pero es una reimplementación paralela e independiente (memoria y tool-hooks propios).

---

## 5. ¿Alcanza con "desplegar H3" para que todo funcione? — No

Encontré el script orquestador `scripts/platform-bootstrap.sh` (soporta `--horizon [h1|h2|h3|all]`). Aclara exactamente qué automatiza "desplegar H3" y qué no.

### 5.1 Son fases separadas, no un solo paso

```
--horizon h3 (o all)
 ├─ deploy_h3_innovation()   → SOLO corre:
 │                              terraform apply -target=module.ai_foundry
 │                              (provisiona Azure OpenAI + Cosmos; nada de K8s/ArgoCD)
 │
 ├─ configure_gitops()       → fase aparte (Phase 4), se ejecuta solo si HORIZON != h1
 │                              y no se pasó --skip-gitops:
 │                              kubectl apply -f argocd/apps/
 │                              (acá recién se registra la Application foundry-agents.yaml)
 │
 └─ register_golden_paths()  → Phase 5, intenta registrar templates en Backstage
```
`deploy_h3_innovation()` (`scripts/platform-bootstrap.sh:347-368`) por sí sola **no toca ArgoCD para nada** — solo hace `terraform apply -target=module.ai_foundry`. El registro de la `Application` de ArgoCD pasa en una función distinta, `configure_gitops()` (`:372-391`), condicionada a `HORIZON != h1` (`:578-579`). Es decir: si alguien corre el paso de Terraform de H3 aislado (a mano, o con `--skip-gitops`), la `Application` de ArgoCD **nunca se registra** y el gateway no se despliega, aunque la infra Azure ya exista.

Si en cambio se corre el orquestador completo (`--horizon h3` o `--horizon all`, sin `--skip-gitops`), sí encadena Terraform → `kubectl apply -f argocd/apps/` automáticamente.

### 5.2 Incluso con el script completo, quedan 3 huecos sin automatizar

1. **El secret de credenciales Azure OpenAI (`foundry-agents-azure-openai`, namespace `ai-services`) no lo crea ningún script.** El `README.md` de `foundry/k8s/` pide crearlo a mano, mirrorándolo desde el secret `foundry-agents-config` del namespace `backstage`. El comentario en `secret-template.yaml` atribuye la creación de ese secret fuente a un script `bootstrap-aro.sh` — **ese archivo no existe en el repo** (busqué en todo `scripts/`, solo están `platform-bootstrap.sh` y `bootstrap.sh`, ninguno crea ese secret). Sin él, el pod de `foundry-agents` queda en `CrashLoopBackOff`/`CreateContainerConfigError` aunque ArgoCD haya sincronizado bien.

2. **El conflicto de los dos `Deployment`** de la sección 4.2 — `kubectl apply -f argocd/apps/` no lo resuelve; ArgoCD va a intentar sincronizar ambos manifiestos igual.

3. **`register_golden_paths()` (Phase 5) es un stub, no hace nada real.** El cuerpo del loop:
   ```bash
   for template in "${ACCELERATOR_ROOT}/golden-paths/h1-foundation/"*/template.yaml; do
       local name=$(basename $(dirname "$template"))
       log INFO "Registering H1 template: $name"
       # Backstage API call to register template     ← comentario, sin código real
   done
   ```
   Solo imprime logs, nunca llama a la API de Backstage. (Para H3 es además moot: el loop equivalente itera `golden-paths/h3-innovation/`, que no existe en este repo — no encontraría nada que registrar).

4. **Backstage no queda conectado al gateway solo.** El bloque `aiChat.providers` de la sección 2.3 no está hoy en `app-config.production.yaml` — hay que agregarlo a mano y reiniciar Backstage (ningún script lo hace).

### 5.3 Resumen

| Paso | ¿Automatizado hoy? |
|---|---|
| Provisionar Azure OpenAI + Cosmos (Terraform) | Sí, con `--horizon h3` |
| Registrar la `Application` de ArgoCD | Sí, pero solo si se corre el script completo (Phase 4) — no si se aísla el paso de Terraform |
| Resolver conflicto de los 2 `Deployment` (sección 4.2) | **No** — manual, hay que elegir uno |
| Crear secret `foundry-agents-azure-openai` | **No** — manual, y el script que se supone lo hace (`bootstrap-aro.sh`) no existe en el repo |
| Fix del `SERVICE_API_KEY` placeholder (sección 4.3) | **No**, y además `selfHeal: true` revertiría un fix hecho a mano en el cluster — hay que corregirlo en el archivo del repo, no en vivo |
| Wireo de Backstage → gateway (`aiChat`) | **No** — manual |
| Registro de Golden Paths en Backstage (Phase 5) | **No** — la función es un stub sin llamada real a la API |

---

## 6. Recomendación

Si el objetivo es **demostrar/usar un despliegue de agentes de IA funcional en `ohorizons-mvp`**, el camino es:
1. Confirmar que Terraform ya corrió con `dev.tfvars` (`enable_ai_foundry`/`enable_foundry_agents` en `true`) y que Azure OpenAI + Cosmos existen.
2. Correr (o completar a mano) la fase `configure_gitops()` — `kubectl apply -f argocd/apps/` — para que la `Application` `foundry-agents` quede registrada en ArgoCD (sección 5.1).
3. Resolver el conflicto de la sección 4.2 (elegir `deployment.yaml` o `deployment-source.yaml`, sacar el otro del path que sincroniza ArgoCD).
4. Crear a mano el secret `foundry-agents-azure-openai` (sección 5.2, punto 1) — no hay script que lo haga hoy.
5. Resolver el `SERVICE_API_KEY` de la sección 4.3 antes de depender de él en producción (idealmente vía External Secrets, no editando el Secret a mano).
6. Sincronizar la `Application` `foundry-agents` y validar `curl .../v1/agents`.
7. Wirear `app-config.production.yaml` de Backstage con el bloque `aiChat` de la sección 2.3 (hoy no está presente).

Si en cambio el objetivo es tener un **flujo self-service tipo `tasks-api` pero para generar agentes nuevos**, eso no existe hoy en `ohorizons-mvp` — habría que traer `golden-paths/h3-innovation/foundry-agent` desde el fork y completarlo (no es un "ajuste de modelo" como hicimos con `tasks-api`, es escribir la implementación real: hoy son stubs).
