"""
Permissions et décorateurs pour KLASS.
Contrôle d'accès par rôle et par tenant.
"""
from functools import wraps
from django.core.exceptions import PermissionDenied
from django.contrib.auth.decorators import login_required
from apps.core.constants import Roles


def role_required(*roles):
    """
    Décorateur qui vérifie que l'utilisateur possède l'un des rôles spécifiés.
    Usage: @role_required(Roles.SCHOOL_ADMIN, Roles.SECRETARY)
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def wrapper(request, *args, **kwargs):
            if request.user.role not in roles:
                raise PermissionDenied(
                    f"Accès refusé. Rôles requis : {', '.join(roles)}"
                )
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def super_admin_required(view_func):
    """Décorateur pour les vues réservées au Super-Admin."""
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if request.user.role != Roles.SUPER_ADMIN:
            raise PermissionDenied("Accès réservé au Super-Admin.")
        return view_func(request, *args, **kwargs)
    return wrapper


def school_staff_required(view_func):
    """Décorateur pour les vues réservées au personnel scolaire."""
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if request.user.role not in Roles.SCHOOL_STAFF_ROLES:
            raise PermissionDenied("Accès réservé au personnel scolaire.")
        return view_func(request, *args, **kwargs)
    return wrapper


class RolePermissionMixin:
    """
    Mixin pour les class-based views avec vérification de rôle.
    Usage: class MyView(RolePermissionMixin, View):
               allowed_roles = [Roles.SCHOOL_ADMIN]
    """
    allowed_roles = []

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            from django.contrib.auth.views import redirect_to_login
            return redirect_to_login(request.get_full_path())

        if self.allowed_roles and request.user.role not in self.allowed_roles:
            raise PermissionDenied(
                f"Accès refusé. Rôles requis : {', '.join(self.allowed_roles)}"
            )
        return super().dispatch(request, *args, **kwargs)
