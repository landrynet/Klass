"""
Middleware personnalisé pour KLASS.
"""
from django.http import HttpRequest
from django.shortcuts import redirect


# ---------------------------------------------------------------------------
# Préfixes URL exemptés du contrôle de changement de mot de passe obligatoire
# ---------------------------------------------------------------------------
_PASSWORD_CHANGE_EXEMPT_PREFIXES = (
    "/auth/",
    "/static/",
    "/media/",
    "/__debug__/",
    "/favicon.ico",
)

# ---------------------------------------------------------------------------
# Préfixes URL exemptés du contrôle de configuration obligatoire
# ---------------------------------------------------------------------------
_SETUP_EXEMPT_PREFIXES = (
    "/auth/",
    "/super-admin/setup/",   # Assistant de configuration initiale
    "/static/",
    "/media/",
    "/__debug__/",
    "/favicon.ico",
)


class TenantContextMiddleware:
    """
    Middleware qui injecte des informations sur le tenant courant
    dans la requête pour un accès facile dans les vues et templates.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request: HttpRequest):
        # Injecter le tenant courant dans la requête
        # django-tenants l'a déjà mis dans request.tenant via TenantMainMiddleware
        if hasattr(request, "tenant"):
            request.current_school = request.tenant
        else:
            request.current_school = None

        response = self.get_response(request)
        return response


class MustChangePasswordMiddleware:
    """
    Middleware qui force TOUS les utilisateurs connectés dont
    must_change_password=True à changer leur mot de passe avant d'accéder
    à n'importe quelle autre page du système.

    Ce contrôle est global et ne peut pas être contourné par URL.
    Seules les URLs d'authentification (/auth/…) et les ressources
    statiques sont exemptées.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request: HttpRequest):
        if self._should_redirect_to_password_change(request):
            return redirect("accounts:change_password_required")
        return self.get_response(request)

    def _should_redirect_to_password_change(self, request: HttpRequest) -> bool:
        if not hasattr(request, "user") or not request.user.is_authenticated:
            return False
        if not getattr(request.user, "must_change_password", False):
            return False
        path = request.path_info
        if any(path.startswith(prefix) for prefix in _PASSWORD_CHANGE_EXEMPT_PREFIXES):
            return False
        return True


class SetupRequiredMiddleware:
    """
    Middleware qui force l'Admin École à compléter la configuration initiale
    avant d'accéder aux autres modules du système.

    Conditions de déclenchement :
    - Utilisateur authentifié
    - Rôle school_admin
    - Mot de passe déjà changé (must_change_password = False)
    - École non encore configurée (setup_completed = False)
    - URL non exemptée

    En cas de déclenchement : redirection vers l'assistant de configuration.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request: HttpRequest):
        if self._should_redirect_to_setup(request):
            return redirect("tenants:setup_school_info")
        return self.get_response(request)

    def _should_redirect_to_setup(self, request: HttpRequest) -> bool:
        """Détermine si l'utilisateur doit être redirigé vers l'assistant."""
        if not hasattr(request, "user") or not request.user.is_authenticated:
            return False

        from apps.core.constants import Roles
        if request.user.role != Roles.SCHOOL_ADMIN:
            return False

        # Si le mot de passe doit encore être changé, MustChangePasswordMiddleware
        # s'en charge — ne pas interférer ici.
        if getattr(request.user, "must_change_password", False):
            return False

        school = getattr(request.user, "school", None)
        if not school or school.setup_completed:
            return False

        path = request.path_info
        if any(path.startswith(prefix) for prefix in _SETUP_EXEMPT_PREFIXES):
            return False

        return True
