# ${{ values.name }}

Agente IA generado con el **Agent Blueprint CLI v2** corporativo (perfil `${{ values.profile }}`,
dominio `${{ values.domain }}`). La definición exacta usada para generarlo está en
`.agent-archetype.yaml`.

## Qué trae el proyecto

| Pieza | Dónde |
|---|---|
| Código del agente (hexagonal: `domain/`, `application/`, `adapters/`, `bootstrap/`; LangGraph) | `src/` |
| Pruebas | `tests/` |
| Prompts de desarrollo y skills | `agent_assets/` |
| Catálogo de tools MCP (si aplica) | `config/mcp-tools.yaml` |
| Pipeline corporativo de Azure DevOps (ruff, mypy, pruebas, Sonar, dllo/labo/pdn) | `azure-pipeline.yaml` |
| Manifiestos AKS (formato del repo `-conf`, Key Vault, AppGW) | `deploy/conf/${{ values.name }}/` |
| Confianza TLS en la PKI de SURA | `certs/`, `docs/TLS.md` |
| Registro en Backstage y esta documentación | `catalog-info.yaml`, `mkdocs.yml`, `docs/` |

## Empezar

```bash
make install    # dependencias
make test       # pytest
make lint       # ruff + mypy (mismo gate que el pipeline)
make run-stub   # arranca sin LLM Gateway ni Langfuse
```

El detalle de configuración (variables `AGENT_*`, LLM Gateway, Langfuse, MCP Gateway) está en el
`README.md` del repositorio.
