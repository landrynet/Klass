"""
Vues du Portail Parents/Élèves pour KLASS.
Agrège les données des autres modules en lecture seule.
"""
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from apps.core.constants import Roles
from apps.core.permissions import role_required


@login_required
def dashboard(request):
    """
    Tableau de bord du portail — vue personnalisée selon le rôle.
    Parent : vue sur tous ses enfants
    Élève : vue sur ses propres données
    """
    context = {}

    if request.user.role == Roles.PARENT:
        try:
            parent = request.user.parent_profile
            context["children"] = parent.students.select_related(
                "current_enrollment__classroom"
            ).all()
        except Exception:
            context["children"] = []

    elif request.user.role == Roles.STUDENT:
        try:
            student = request.user.student_profile
            context["student"] = student
            context["enrollment"] = student.current_enrollment
        except Exception:
            context["student"] = None

    return render(request, "portal/dashboard.html", context)


@require_GET
def manifest(request):
    """
    manifest.json pour l'installation PWA.
    Retourne le manifest de l'application web progressive.
    """
    school = getattr(request, "current_school", None)
    school_name = school.name if school else "KLASS"

    manifest_data = {
        "name": f"{school_name} — KLASS",
        "short_name": school_name[:12],
        "description": "Portail scolaire KLASS — Accès parents et élèves",
        "start_url": "/portal/",
        "display": "standalone",
        "background_color": "#ffffff",
        "theme_color": "#1a56db",
        "orientation": "portrait-primary",
        "icons": [
            {
                "src": "/static/pwa/icons/icon.svg",
                "sizes": "any",
                "type": "image/svg+xml",
                "purpose": "any maskable",
            },
        ],
        "categories": ["education"],
        "lang": "fr",
    }
    return JsonResponse(manifest_data)


@require_GET
def service_worker(request):
    """
    Service Worker JavaScript pour le cache offline PWA.
    Servi depuis la racine / pour avoir le scope maximal.
    """
    from django.http import HttpResponse
    return HttpResponse(
        content_type="application/javascript",
        content="""
// KLASS Service Worker — Cache Offline
const CACHE_NAME = 'klass-portal-v1';
const URLS_TO_CACHE = [
  '/static/css/klass.css',
  '/static/js/klass.js',
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(URLS_TO_CACHE))
  );
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== CACHE_NAME).map((k) => caches.delete(k)))
    )
  );
  self.clients.claim();
});

self.addEventListener('fetch', (event) => {
  // Network first, fallback to cache
  event.respondWith(
    fetch(event.request).catch(() => caches.match(event.request))
  );
});
"""
    )
