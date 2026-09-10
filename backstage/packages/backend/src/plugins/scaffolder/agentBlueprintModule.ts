import { createBackendModule } from '@backstage/backend-plugin-api';
import { scaffolderActionsExtensionPoint } from '@backstage/plugin-scaffolder-node';
import { createAgentBlueprintAction } from './actions/createAgentBlueprintAction';

export const agentBlueprintModule = createBackendModule({
  pluginId: 'scaffolder',
  moduleId: 'agent-blueprint-action',
  register(reg) {
    reg.registerInit({
      deps: { scaffolder: scaffolderActionsExtensionPoint },
      async init({ scaffolder }) {
        scaffolder.addActions(createAgentBlueprintAction());
      },
    });
  },
});

export default agentBlueprintModule;
