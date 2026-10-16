import { createTemplateAction, executeShellCommand } from '@backstage/plugin-scaffolder-node';
import { mkdtemp, writeFile, rm } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import yaml from 'js-yaml';

/**
 * Invokes the corporate Agent Blueprint CLI v2 (agent-blueprint-cli 0.3.x) to generate an AI agent
 * runtime project into the scaffolder workspace. v2 uses the same command name as v1
 * (`agent-blueprint`), so it is installed in its own virtualenv and invoked by path
 * (config `agentBlueprintV2.command`), letting both golden paths coexist.
 */
export function createAgentBlueprintV2Action(options: { command: string }) {
  return createTemplateAction({
    id: 'agent-blueprint-v2:create',
    description:
      'Genera un proyecto de agente IA con el Agent Blueprint CLI v2 corporativo (LangGraph, hexagonal, LLM Gateway, MCP gobernado, A2A, TLS SURA, pipeline Azure DevOps y manifiestos AKS).',
    schema: {
      input: {
        name: z => z.string().describe('Nombre del proyecto del agente'),
        domain: z => z.string().describe('Dominio de negocio'),
        owner: z => z.string().describe('Equipo dueno'),
        profile: z => z.string().describe('Perfil: singular | role-agent | orchestrator | specialist'),
        protocols: z =>
          z.array(z.string()).optional().describe('http | a2a | events (si se omite, usa el default del perfil)'),
        capabilities: z =>
          z.array(z.string()).optional().describe('Capacidades opcionales (si se omite, usa el default del perfil)'),
        executionPattern: z => z.string().optional().describe('synchronous | asynchronous | mixed'),
        promptProvider: z => z.string().optional().describe('local | remote'),
        observability: z => z.string().optional().describe('noop | otel | corporate-sdk'),
      },
    },
    async handler(ctx) {
      const { name, domain, owner, profile, protocols, capabilities, executionPattern, promptProvider, observability } =
        ctx.input;

      // Solo se envian los valores elegidos: lo omitido toma el default del perfil en el CLI.
      const definition: Record<string, unknown> = { name, domain, owner, profile, output: ctx.workspacePath };
      if (protocols && protocols.length > 0) definition.protocols = protocols;
      if (capabilities && capabilities.length > 0) definition.capabilities = capabilities;
      if (executionPattern) definition.execution_pattern = executionPattern;
      if (promptProvider) definition.prompt_provider = promptProvider;
      if (observability) definition.observability_provider = observability;

      const configDir = await mkdtemp(join(tmpdir(), 'agent-blueprint-v2-'));
      const configPath = join(configDir, 'definition.yaml');
      await writeFile(configPath, yaml.dump(definition), 'utf8');

      ctx.logger.info(`Generando proyecto con Agent Blueprint v2 (perfil: ${profile}, comando: ${options.command})`);
      ctx.logger.info(yaml.dump(definition));

      try {
        await executeShellCommand({
          command: options.command,
          args: ['create', '--config', configPath, '--non-interactive'],
          logger: ctx.logger,
        });
        await executeShellCommand({
          command: options.command,
          args: ['validate', '--path', ctx.workspacePath],
          logger: ctx.logger,
        });
      } finally {
        await rm(configDir, { recursive: true, force: true });
      }
    },
  });
}
