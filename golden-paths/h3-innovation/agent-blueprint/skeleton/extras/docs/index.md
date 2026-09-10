# ${{ values.name }}

Agente IA generado con [`agent-blueprint-cli`](https://github.com/SuraOhorizons/agent-blueprint-cli-archetype)
(perfil `${{ values.profile }}`, dominio `${{ values.domain }}`).

## Overview

El código del agente (arquitectura hexagonal: `domain/`, `application/`, `adapters/`,
`bootstrap/`) fue generado automaticamente por el CLI segun el perfil seleccionado —
no se edito a mano en este golden path. Este repo agrega, ademas del proyecto del
agente en si:

- `catalog-info.yaml` — registro en el catalogo de Backstage
- `.github/workflows/deploy.yml` — build + push de la imagen a ACR
- `deploy/` — manifiestos de Kubernetes (`Deployment`, `Service`, `ConfigMap`,
  `ExternalSecret`) y la `Application` de ArgoCD para despliegue GitOps

## Getting Started

1. `make install` — instala dependencias del proyecto generado
2. `make test` — corre los tests generados
3. `make run` — levanta el agente localmente (puerto 8080 por defecto)
4. Cargar en Key Vault el secreto declarado en `deploy/external-secret.yaml`
   (API key del LLM Gateway)
5. Confirmar `AGENT_LLM_GATEWAY_URL`, `AGENT_PROMPT_MANAGEMENT_URL` y
   `AGENT_MCP_GATEWAY_URL` en `deploy/configmap.yaml` antes de desplegar

## Endpoints

| Endpoint | Metodo | Que hace |
|---|---|---|
| `/health` | GET | Health check |
| `/invoke` | POST | Invoca al agente (`input`, `session_id`) |

## Perfiles disponibles en el golden path

- `single-agent-conversational`
- `transactional-tools`
- `orchestrator-worker`
- `planner-executor-reviewer`
- `async-event-driven`

Cada perfil trae componentes obligatorios distintos (ver `.agent-archetype.yaml`
en la raiz del repo generado para la composicion exacta).
