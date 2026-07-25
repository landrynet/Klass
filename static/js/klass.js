/**
 * KLASS — Scripts JavaScript principaux
 * Alpine.js gère l'interactivité déclarative
 * HTMX gère les requêtes partielles
 * Ce fichier contient les utilitaires globaux
 */

'use strict';

// ---- PWA Install prompt ----
let deferredInstallPrompt = null;

window.addEventListener('beforeinstallprompt', (e) => {
  e.preventDefault();
  deferredInstallPrompt = e;
  showInstallBanner();
});

function showInstallBanner() {
  const banner = document.getElementById('pwa-install-banner');
  if (banner) banner.classList.remove('d-none');
}

function installPWA() {
  if (deferredInstallPrompt) {
    deferredInstallPrompt.prompt();
    deferredInstallPrompt.userChoice.then(() => {
      deferredInstallPrompt = null;
      const banner = document.getElementById('pwa-install-banner');
      if (banner) banner.classList.add('d-none');
    });
  }
}

// ---- HTMX loading indicator ----
document.addEventListener('htmx:beforeRequest', () => {
  document.body.classList.add('htmx-loading');
});
document.addEventListener('htmx:afterRequest', () => {
  document.body.classList.remove('htmx-loading');
});

// ---- Auto-dismiss alerts ----
document.addEventListener('DOMContentLoaded', () => {
  const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
  alerts.forEach((alert) => {
    setTimeout(() => {
      const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
      if (bsAlert) bsAlert.close();
    }, 5000);
  });
});
