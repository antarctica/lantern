window.sentryOnLoad = function() {
  Sentry.init({
    tracesSampleRate: 0,
    replaysSessionSampleRate: 0,
    replaysOnErrorSampleRate: 0,
  });
  Sentry.lazyLoadIntegration("feedbackIntegration").then(
    (integration) => {
      Sentry.addIntegration(integration({
        autoInject: false,
        showBranding: false,
        colorScheme: "light",
        formTitle: "Send Feedback",
        submitButtonLabel: "Send Feedback",
        messagePlaceholder: "",
        successMessageText: "Thank you for your feedback.",
      }));
      const feedback = Sentry.getFeedback();
      if (feedback) {
        const triggers = document.querySelectorAll(".site-feedback-trigger");
        triggers.forEach(trigger => {
          feedback.attachTo(trigger, {});
        });
      }
    }
  );
};
