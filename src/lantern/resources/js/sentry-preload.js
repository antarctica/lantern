window.sentryOnLoad = function() {
  Sentry.init({
    tracesSampleRate: 0,
    replaysSessionSampleRate: 0,
    replaysOnErrorSampleRate: 0,
  });
  Sentry.lazyLoadIntegration("feedbackIntegration").then(
    (integration) => {
      Sentry.addIntegration(integration({autoInject: false}));
    }
  );
};
