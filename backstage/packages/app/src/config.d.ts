export interface Config {
  app: {
    features?: {
      /**
       * Muestra u oculta la sección "Intelligence" (AI Chat / AI Impact) del
       * sidebar. Se controla vía la env var AI_CHAT_ENABLED (ver app-config.yaml
       * / app-config.production.yaml).
       * @visibility frontend
       */
      aiChat?: string;
    };
  };
}
