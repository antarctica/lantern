/* show-js */
document.addEventListener('DOMContentLoaded', function() {
  document.querySelectorAll('.show-js').forEach(el => el.classList.remove('hidden'));
});
/* sticky-tabs */
/* Based on jQuery Plugin Sticky Tabs by Aidan Lister <aidan@php.net> */
(function () {
  const selectTab = (tabId) => {
    const input = document.getElementById(tabId);
    if (input && input.type === "radio") {
      input.checked = true;
      window.history.pushState(null, null, `#${tabId}`);
    }
  };
  const handleHashChange = () => {
    const hash = window.location.hash;
    if (hash) {
      selectTab(hash.substring(1)); // Remove '#' from hash
    }
  };
  document.addEventListener("DOMContentLoaded", function () {
    handleHashChange(); // Handle initial hash on page load
    const tabLabels = document.querySelectorAll('label[for^="tab-"]');
    tabLabels.forEach((label) => {
      label.addEventListener("click", () => {
        const tabId = label.getAttribute("for");
        selectTab(tabId);
      });
    });
    // Listen for hash changes
    window.addEventListener("hashchange", handleHashChange);
  });
})();
/* collapsible */
document.addEventListener('DOMContentLoaded', () => {
  // Find all elements with the `data-target` attribute and add click event listeners to hide/show a target element
  const toggles = document.querySelectorAll('[data-target]');
  toggles.forEach(toggle => {
    toggle.addEventListener('click', () => {
      const targetSelector = toggle.getAttribute('data-target');
      const targetElement = document.querySelector(targetSelector);
      if (targetElement) {
        targetElement.classList.toggle('hidden');
      }
    });
  });
});
/* clipboard-copy */
document.addEventListener('DOMContentLoaded', () => {
  const writeToClipboard = async (text) => {
    if (navigator.clipboard && navigator.clipboard.writeText) {
      await navigator.clipboard.writeText(text);
    }
  };
  document.addEventListener('click', async (event) => {
    const trigger = event.target.closest('[data-copy]');
    if (!trigger) {
      return;
    }
    event.preventDefault();
    const value = trigger.getAttribute('data-copy');
    if (!value) {
      return;
    }
    try {
      await writeToClipboard(value);
      trigger.dispatchEvent(new CustomEvent('copy:success', { bubbles: true }));
    } catch (error) {
      trigger.dispatchEvent(new CustomEvent('copy:error', { bubbles: true, detail: error }));
    }
  });
});
/* feedback-processing */
document.addEventListener('DOMContentLoaded', () => {
  const form = document.getElementById('site-feedback');
  if (!form) return;
  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const submitBtn = form.querySelector('button[type="submit"], [type="submit"]');
    const contentEl = document.getElementById('feedback-content');
    const emailEl = document.getElementById('feedback-email');
    const successEl = document.getElementById('feedback-success');
    const errorEl = document.getElementById('feedback-error');
    const feedback = {
      message: contentEl ? contentEl.value.trim() : '',
      email: emailEl ? (emailEl.value.trim() || undefined) : undefined,
    };
    try {
      if (typeof Sentry === 'undefined' || typeof Sentry.captureFeedback !== 'function') {
        throw new Error('Sentry.captureFeedback is not available');
      }
      const res = Sentry.captureFeedback(feedback);
      if (res && typeof res.then === 'function') {
        await res;
      } else {
        throw new Error('Sentry.captureFeedback did not return a submission promise');
      }
      submitBtn.classList.add('hidden');
      successEl.classList.remove('hidden');
    } catch (err) {
      submitBtn.classList.add('hidden');
      errorEl.classList.remove('hidden');
    }
  });
});
