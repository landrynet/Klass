"""
Module 8 — Gestion des Années Scolaires.
Fondation temporelle de tous les autres modules KLASS.
"""
from django.db import models
from django.core.exceptions import ValidationError
from apps.core.models import TenantAwareModel


class SchoolYear(TenantAwareModel):
    """
    Représente une année scolaire dans une école.
    Une seule année peut être active (is_active=True) à la fois.

    Cycle de vie:
    - Créée → Active → Clôturée (archivée en lecture seule)

    Le passage d'une année à l'autre est orchestré par le module
    via la commande de bascule (Module 8 complet en Phase 8).
    """
    name = models.CharField(
        max_length=20,
        verbose_name="Nom",
        help_text="Ex: 2025-2026"
    )
    start_date = models.DateField(verbose_name="Date de début")
    end_date = models.DateField(verbose_name="Date de fin")

    is_active = models.BooleanField(
        default=False,
        verbose_name="Année active",
        help_text="Une seule année peut être active à la fois."
    )
    is_closed = models.BooleanField(
        default=False,
        verbose_name="Clôturée",
        help_text="Une année clôturée est en lecture seule."
    )
    closed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Date de clôture"
    )
    closed_by = models.ForeignKey(
        "accounts.User",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="closed_school_years",
        verbose_name="Clôturée par"
    )

    class Meta:
        verbose_name = "Année scolaire"
        verbose_name_plural = "Années scolaires"
        ordering = ["-start_date"]

    def __str__(self):
        status = " [ACTIVE]" if self.is_active else (" [CLÔTURÉE]" if self.is_closed else "")
        return f"{self.name}{status}"

    def clean(self):
        if self.start_date and self.end_date and self.start_date >= self.end_date:
            raise ValidationError("La date de fin doit être postérieure à la date de début.")

    @classmethod
    def get_active(cls):
        """Retourne l'année scolaire active, None si aucune."""
        return cls.objects.filter(is_active=True).first()

    @property
    def is_editable(self):
        """Une année clôturée n'est plus modifiable."""
        return not self.is_closed
