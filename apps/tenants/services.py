"""
Services métier pour la gestion des tenants (écoles).
Logique de création d'école, de schéma et de compte Admin.
"""
import logging
from django.db import transaction
from apps.core.utils import slugify_school_name, generate_temp_password
from apps.core.constants import Roles

logger = logging.getLogger(__name__)


def create_school_with_tenant(
    name: str,
    email: str,
    phone: str = "",
    address: str = "",
    city: str = "",
    country: str = "Congo (RDC)",
    admin_first_name: str = "Admin",
    admin_last_name: str = "",
    admin_email: str = "",
    created_by=None,
) -> tuple:
    """
    Crée une nouvelle école et son tenant PostgreSQL.

    Flux :
    1. Génère un slug depuis le nom
    2. Crée le schéma PostgreSQL via School (TenantMixin)
    3. Crée le domaine principal (slug.klass.app)
    4. Crée le compte Admin École dans le schéma public (User est partagé)
    5. Lie l'Admin à son école via la FK school
    6. Génère les identifiants temporaires

    Retourne : (school, admin_user, temp_password)

    En cas d'erreur, la transaction est annulée (pas de données incomplètes).
    """
    from .models import School, Domain

    slug = slugify_school_name(name)
    if not slug:
        raise ValueError(f"Impossible de générer un slug valide depuis le nom : '{name}'")

    schema_name = f"school_{slug.replace('-', '_')}"
    domain_name = f"{slug}.klass.app"
    temp_password = generate_temp_password()

    # Utiliser l'email de l'admin ou celui de l'école par défaut
    effective_admin_email = admin_email or email
    effective_admin_last_name = admin_last_name or name[:50]

    logger.info(
        "Création de l'école '%s' (slug=%s, schema=%s) par %s",
        name, slug, schema_name,
        created_by.email if created_by else "système",
    )

    with transaction.atomic():
        # 1. Créer le tenant (crée automatiquement le schéma PostgreSQL via django-tenants)
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

        # 2. Créer le domaine principal
        Domain.objects.create(
            tenant=school,
            domain=domain_name,
            is_primary=True,
        )

        # 3. Créer le compte Admin École
        # User est dans SHARED_APPS → table dans le schéma public
        from apps.accounts.models import User
        admin_user = User.objects.create_user(
            email=effective_admin_email,
            password=temp_password,
            role=Roles.SCHOOL_ADMIN,
            first_name=admin_first_name,
            last_name=effective_admin_last_name,
            must_change_password=True,
            school=school,  # Lier l'admin à son école
        )

    logger.info(
        "École '%s' créée avec succès. Admin: %s",
        school.name, admin_user.email,
    )

    return school, admin_user, temp_password
