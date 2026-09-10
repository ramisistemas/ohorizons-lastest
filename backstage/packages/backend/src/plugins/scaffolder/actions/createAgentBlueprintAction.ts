import { createTemplateAction, executeShellCommand } from '@backstage/plugin-scaffolder-node';
import { mkdtemp, writeFile, rm } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import yaml from 'js-yaml';

/**
 * Invokes the `agent-blueprint` CLI (agent-blueprint-cli-archetype) to
 * generate an AI agent runtime project into the scaffolder workspace,
 * reusing its own profile/capability composition rules instead of
 * reimplementing them as Nunjucks templates.
 */
export function createAgentBlueprintAction() {
  return createTemplateAction({
    id: 'agent-blueprint:create',
    description:
      'Genera un proyecto de agente IA (LangGraph + arquitectura hexagonal) usando agent-blueprint-cli, segun el perfil y las capacidades seleccionadas.',
    schema: {
      input: {
        name: z => z.string().describe('Nombre del proyecto del agente'),
        domain: z => z.string().describe('Dominio de negocio'),
        owner: z => z.string().describe('Equipo dueno'),
        profile: z =>
          z
            .string()
            .describe(
              'Perfil de arquitectura: single-agent-conversational | transactional-tools | orchestrator-worker | planner-executor-reviewer | async-event-driven',
            ),
        tools: z => z.string().optional().describe('none | mcp (si se omite, usa el default del perfil)'),
        inbound: z => z.string().optional().describe('http | event (si se omite, usa el default del perfil)'),
        memory: z => z.string().optional().describe('session | episodic (si se omite, usa el default del perfil)'),
        a2a: z => z.boolean().optional().describe('Habilitar A2A/AgentCard'),
        internalMcpServer: z => z.boolean().optional().describe('Generar servidor MCP interno'),
      },
    },
    async handler(ctx) {
      const { name, domain, owner, profile, tools, inbound, memory, a2a, internalMcpServer } = ctx.input;

      const features: Record<string, unknown> = {};
      if (tools) features.tools = tools;
      if (inbound) features.inbound = inbound;
      if (memory) features.memory = memory;
      if (a2a !== undefined) features.a2a = a2a;
      if (internalMcpServer !== undefined) features.internal_mcp_server = internalMcpServer;

      const configDir = await mkdtemp(join(tmpdir(), 'agent-blueprint-'));
      const configPath = join(configDir, 'definition.yaml');
      const definition = {
        name,
        domain,
        owner,
        profile,
        output: ctx.workspacePath,
        features,
      };
      await writeFile(configPath, yaml.dump(definition), 'utf8');

      ctx.logger.info(`Generando proyecto con agent-blueprint (perfil: ${profile})`);
      ctx.logger.info(yaml.dump(definition));

      try {
        await executeShellCommand({
          command: 'agent-blueprint',
          args: ['create', '--config', configPath],
          logger: ctx.logger,
        });
      } finally {
        await rm(configDir, { recursive: true, force: true });
      }
    },
  });
}
