"""
Context processors pour les templates KLASS.
Injectent automatiquement des variables dans tous les templates.
"""
from apps.core.constants import Roles


def school_context(request):
    """Injecte les informations de l'école courante dans les templates."""
    school = getattr(request, "current_school", None)
    return {
        "current_school": school,
        "school_name": getattr(school, "name", "KLASS"),
        "school_logo": getattr(school, "logo", None),
    }


def user_role_context(request):
    """Injecte le rôle et les permissions de l'utilisateur dans les templates."""
    if not request.user.is_authenticated:
        return {
            "user_role": None,
            "is_super_admin": False,
            "is_school_admin": False,
            "is_school_staff": False,
            "is_portal_user": False,
        }

    role = getattr(request.user, "role", None)
    return {
        "user_role": role,
        "is_super_admin": role == Roles.SUPER_ADMIN,
        "is_school_admin": role == Roles.SCHOOL_ADMIN,
        "is_school_staff": role in Roles.SCHOOL_STAFF_ROLES,
        "is_portal_user": role in Roles.PORTAL_ROLES,
        "Roles": Roles,
    }
