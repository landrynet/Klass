"""
Services métier pour la gestion des tenants (écoles).
Logique de création d'école, de schéma et de compte Admin.
"""
from django.db import transaction
from apps.core.utils import slugify_school_name, generate_temp_password
from apps.core.constants import Roles


def create_school_with_tenant(
    name: str,
    email: str,
    phone: str = "",
    address: str = "",
    city: str = "",
    country: str = "Congo (RDC)",
    created_by=None,
) -> tuple:
    """
    Crée une nouvelle école et son tenant PostgreSQL.

    Flux:
    1. Génère un slug depuis le nom
    2. Crée le schéma PostgreSQL via School (TenantMixin)
    3. Crée le domaine principal
    4. Dans le schéma de l'école, crée le compte Admin école
    5. Génère les identifiants temporaires

    Retourne: (school, admin_user, temp_password)
    """
    from .models import School, Domain

    slug = slugify_school_name(name)
    schema_name = f"school_{slug.replace('-', '_')}"
    domain = f"{slug}.klass.app"
    temp_password = generate_temp_password()

    with transaction.atomic():
        # Créer le tenant (crée automatiquement le schéma PostgreSQL)
        school = School.objects.create(
            name=name,
            slug=slug,
            schema_name=schema_name,
            email=email,
            phone=phone,
            address=address,
            city=city,
            country=country,
        )

        # Créer le domaine principal
        Domain.objects.create(
            tenant=school,
            domain=domain,
            is_primary=True,
        )

        # Créer le compte Admin école dans le schéma de l'école
        from django_tenants.utils import schema_context
        with schema_context(schema_name):
            from apps.accounts.models import User
            admin_user = User.objects.create_user(
                email=email,
                password=temp_password,
                role=Roles.SCHOOL_ADMIN,
                first_name="Admin",
                last_name=name[:50],
                must_change_password=True,  # Changement obligatoire à la première connexion
            )

    return school, admin_user, temp_password
