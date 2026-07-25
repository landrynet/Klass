/**
 * KLASS — Scripts JavaScript principaux v2.0
 * Phase 3.5 — Refonte UI/UX
 */

'use strict';

// ============================================================
// PWA Install prompt
// ============================================================
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

// ============================================================
// HTMX loading indicator
// ============================================================
document.addEventListener('htmx:beforeRequest', () => {
  document.body.classList.add('htmx-loading');
});
document.addEventListener('htmx:afterRequest', () => {
  document.body.classList.remove('htmx-loading');
});

// ============================================================
// Auto-dismiss alerts (5s)
// ============================================================
document.addEventListener('DOMContentLoaded', () => {
  const alerts = document.querySelectorAll('.alert:not(.alert-permanent):not(.alert-info)');
  alerts.forEach((alert) => {
    setTimeout(() => {
      const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
      if (bsAlert) bsAlert.close();
    }, 5000);
  });
});

// ============================================================
// Mobile Sidebar Toggle
// ============================================================
document.addEventListener('DOMContentLoaded', () => {
  const toggler  = document.getElementById('sidebar-toggler');
  const sidebar  = document.getElementById('klass-sidebar');
  const overlay  = document.getElementById('sidebar-overlay');

  if (!toggler || !sidebar) return;

  function openSidebar() {
    sidebar.classList.add('sidebar-open');
    overlay.classList.add('show');
    document.body.style.overflow = 'hidden';
  }

  function closeSidebar() {
    sidebar.classList.remove('sidebar-open');
    overlay.classList.remove('show');
    document.body.style.overflow = '';
  }

  toggler.addEventListener('click', () => {
    sidebar.classList.contains('sidebar-open') ? closeSidebar() : openSidebar();
  });

  if (overlay) overlay.addEventListener('click', closeSidebar);

  // Close sidebar on nav-link click (mobile)
  sidebar.querySelectorAll('.nav-link').forEach(link => {
    link.addEventListener('click', () => {
      if (window.innerWidth < 992) closeSidebar();
    });
  });

  // Close on resize to desktop
  window.addEventListener('resize', () => {
    if (window.innerWidth >= 992) closeSidebar();
  });
});

// ============================================================
// Anti double-submit (all forms with data-submit-once)
// ============================================================
document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('form[data-submit-once]').forEach(form => {
    form.addEventListener('submit', function handleSubmit(e) {
      const submitBtn = form.querySelector('[type="submit"]');
      if (!submitBtn) return;

      // Prevent double submit
      if (form.dataset.submitted === 'true') {
        e.preventDefault();
        return;
      }
      form.dataset.submitted = 'true';

      // Show loading state
      const originalText = submitBtn.innerHTML;
      submitBtn.disabled = true;
      submitBtn.innerHTML = '<span class="btn-spinner"></span> Enregistrement…';
      submitBtn.classList.add('btn-loading');

      // Safety reset after 10s
      setTimeout(() => {
        form.dataset.submitted = '';
        submitBtn.disabled = false;
        submitBtn.innerHTML = originalText;
        submitBtn.classList.remove('btn-loading');
      }, 10000);
    });
  });
});

// ============================================================
// Copy to clipboard utility
// ============================================================
function copyToClipboard(text, btn) {
  navigator.clipboard.writeText(text).then(() => {
    const orig = btn.innerHTML;
    btn.innerHTML = '<i class="bi bi-check2"></i>';
    btn.classList.add('copied');
    setTimeout(() => {
      btn.innerHTML = orig;
      btn.classList.remove('copied');
    }, 2000);
  }).catch(() => {
    // Fallback
    const el = document.createElement('textarea');
    el.value = text;
    document.body.appendChild(el);
    el.select();
    document.execCommand('copy');
    document.body.removeChild(el);
  });
}

// ============================================================
// Progress bar (for long operations)
// ============================================================
function showProgressBar() {
  let bar = document.getElementById('klass-progress');
  if (!bar) {
    bar = document.createElement('div');
    bar.id = 'klass-progress';
    bar.className = 'klass-progress-bar active';
    bar.style.width = '0%';
    document.body.appendChild(bar);
  }
  bar.classList.add('active');
  let w = 0;
  const interval = setInterval(() => {
    w = Math.min(w + Math.random() * 15, 85);
    bar.style.width = w + '%';
    if (w >= 85) clearInterval(interval);
  }, 300);
  return interval;
}

function hideProgressBar(intervalId) {
  const bar = document.getElementById('klass-progress');
  if (intervalId) clearInterval(intervalId);
  if (bar) { bar.style.width = '100%'; setTimeout(() => { bar.classList.remove('active'); bar.style.width = '0%'; }, 400); }
}
