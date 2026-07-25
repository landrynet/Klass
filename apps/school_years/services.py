"""
Services métier pour la gestion des années scolaires.
Logique de transitions d'état avec isolation tenant.
"""
import logging
from django.db import transaction
from django_tenants.utils import schema_context

logger = logging.getLogger(__name__)


def activate_school_year(school, year_pk: int, activated_by=None):
    """
    Active une année scolaire dans le schéma du tenant donné.
    Désactive toutes les autres années actives de l'école.

    Retourne l'année activée.
    Lève ValueError si la transition est invalide.
    """
    from apps.school_years.models import SchoolYear

    with schema_context(school.schema_name):
        with transaction.atomic():
            try:
                year = SchoolYear.objects.select_for_update().get(pk=year_pk)
            except SchoolYear.DoesNotExist:
                raise ValueError("Année scolaire introuvable.")
            year.activate(save=True)
            logger.info(
                "Année '%s' activée pour l'école '%s' par %s.",
                year.name, school.name, activated_by or "système"
            )
            return year


def end_school_year(school, year_pk: int, closed_by=None):
    """
    Clôture l'année scolaire active.

    Retourne l'année clôturée.
    """
    from apps.school_years.models import SchoolYear

    with schema_context(school.schema_name):
        with transaction.atomic():
            try:
                year = SchoolYear.objects.select_for_update().get(pk=year_pk)
            except SchoolYear.DoesNotExist:
                raise ValueError("Année scolaire introuvable.")
            year.end(closed_by=closed_by, save=True)
            logger.info(
                "Année '%s' clôturée pour l'école '%s'.",
                year.name, school.name
            )
            return year


def archive_school_year(school, year_pk: int):
    """
    Archive définitivement une année scolaire terminée.

    Retourne l'année archivée.
    """
    from apps.school_years.models import SchoolYear

    with schema_context(school.schema_name):
        with transaction.atomic():
            try:
                year = SchoolYear.objects.select_for_update().get(pk=year_pk)
            except SchoolYear.DoesNotExist:
                raise ValueError("Année scolaire introuvable.")
            year.archive(save=True)
            logger.info(
                "Année '%s' archivée pour l'école '%s'.",
                year.name, school.name
            )
            return year


def create_school_year(school, name: str, start_date, end_date, activate: bool = False, created_by=None):
    """
    Crée une nouvelle année scolaire dans le schéma du tenant.
    Si activate=True, l'active immédiatement (désactive les autres).

    Retourne l'année créée.
    """
    from apps.school_years.models import SchoolYear

    with schema_context(school.schema_name):
        with transaction.atomic():
            # Vérifier l'unicité du nom
            if SchoolYear.objects.filter(name=name).exists():
                raise ValueError(f"Une année scolaire « {name} » existe déjà.")

            if activate:
                SchoolYear.objects.filter(is_active=True).update(is_active=False)

            year = SchoolYear.objects.create(
                name=name,
                start_date=start_date,
                end_date=end_date,
                is_active=activate,
            )
            logger.info(
                "Année '%s' créée pour l'école '%s' (active=%s).",
                name, school.name, activate
            )
            return year


def update_school_year(school, year_pk: int, name: str, start_date, end_date):
    """
    Met à jour les informations d'une année scolaire non clôturée.
    """
    from apps.school_years.models import SchoolYear

    with schema_context(school.schema_name):
        with transaction.atomic():
            try:
                year = SchoolYear.objects.select_for_update().get(pk=year_pk)
            except SchoolYear.DoesNotExist:
                raise ValueError("Année scolaire introuvable.")
            if not year.is_editable:
                raise ValueError("Cette année scolaire ne peut plus être modifiée.")
            # Vérifier l'unicité du nom (hors soi-même)
            if SchoolYear.objects.filter(name=name).exclude(pk=year_pk).exists():
                raise ValueError(f"Une année scolaire « {name} » existe déjà.")
            year.name = name
            year.start_date = start_date
            year.end_date = end_date
            year.save(update_fields=["name", "start_date", "end_date", "updated_at"])
            return year
