import { coreServices, createBackendModule } from '@backstage/backend-plugin-api';
import { scaffolderActionsExtensionPoint } from '@backstage/plugin-scaffolder-node';
import { createAgentBlueprintV2Action } from './actions/createAgentBlueprintV2Action';

/**
 * Registra la accion agent-blueprint-v2:create. La ruta del CLI v2 se toma de
 * `agentBlueprintV2.command` (por ejemplo, el binario de su virtualenv en app-config.local.yaml).
 */
export const agentBlueprintV2Module = createBackendModule({
  pluginId: 'scaffolder',
  moduleId: 'agent-blueprint-v2-action',
  register(reg) {
    reg.registerInit({
      deps: { scaffolder: scaffolderActionsExtensionPoint, config: coreServices.rootConfig },
      async init({ scaffolder, config }) {
        const command = config.getOptionalString('agentBlueprintV2.command') ?? 'agent-blueprint-v2';
        scaffolder.addActions(createAgentBlueprintV2Action({ command }));
      },
    });
  },
});

export default agentBlueprintV2Module;
