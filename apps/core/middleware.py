"""
Middleware personnalisé pour KLASS.
"""
from django.http import HttpRequest


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
