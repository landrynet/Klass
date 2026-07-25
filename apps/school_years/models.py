"""
Module 8 — Gestion des Années Scolaires.
Fondation temporelle de tous les autres modules KLASS.

Cycle de vie d'une année scolaire :
    Planifiée → Active → Terminée → Archivée
"""
from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
from apps.core.models import TenantAwareModel


class SchoolYear(TenantAwareModel):
    """
    Représente une année scolaire dans une école.
    Une seule année peut être active (is_active=True) à la fois.

    Cycle de vie :
        Planifiée  : is_active=False, is_closed=False, is_archived=False
        Active     : is_active=True,  is_closed=False, is_archived=False
        Terminée   : is_active=False, is_closed=True,  is_archived=False
        Archivée   : is_active=False, is_closed=True,  is_archived=True
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
    is_archived = models.BooleanField(
        default=False,
        verbose_name="Archivée",
        help_text="Une année archivée est définitivement fermée."
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
        return f"{self.name} [{self.status_display}]"

    def clean(self):
        if self.start_date and self.end_date and self.start_date >= self.end_date:
            raise ValidationError("La date de fin doit être postérieure à la date de début.")

    # ------------------------------------------------------------------
    # Statut dérivé
    # ------------------------------------------------------------------

    STATUS_PLANNED = "planned"
    STATUS_ACTIVE = "active"
    STATUS_ENDED = "ended"
    STATUS_ARCHIVED = "archived"

    @property
    def status(self) -> str:
        """Retourne le statut courant sous forme de code."""
        if self.is_active:
            return self.STATUS_ACTIVE
        if self.is_archived:
            return self.STATUS_ARCHIVED
        if self.is_closed:
            return self.STATUS_ENDED
        return self.STATUS_PLANNED

    @property
    def status_display(self) -> str:
        """Retourne le libellé du statut courant."""
        return {
            self.STATUS_PLANNED: "Planifiée",
            self.STATUS_ACTIVE: "Active",
            self.STATUS_ENDED: "Terminée",
            self.STATUS_ARCHIVED: "Archivée",
        }[self.status]

    @property
    def status_badge_class(self) -> str:
        """Retourne la classe CSS du badge de statut."""
        return {
            self.STATUS_PLANNED: "bg-secondary-subtle text-secondary",
            self.STATUS_ACTIVE: "bg-success-subtle text-success",
            self.STATUS_ENDED: "bg-warning-subtle text-warning",
            self.STATUS_ARCHIVED: "bg-dark-subtle text-secondary",
        }[self.status]

    @property
    def is_editable(self) -> bool:
        """Une année clôturée ou archivée n'est plus modifiable."""
        return not self.is_closed and not self.is_archived

    @property
    def can_activate(self) -> bool:
        return self.status == self.STATUS_PLANNED

    @property
    def can_end(self) -> bool:
        return self.status == self.STATUS_ACTIVE

    @property
    def can_archive(self) -> bool:
        return self.status == self.STATUS_ENDED

    # ------------------------------------------------------------------
    # Transitions d'état
    # ------------------------------------------------------------------

    def activate(self, save: bool = True):
        """
        Active cette année scolaire.
        Désactive automatiquement toute autre année active.
        """
        if self.is_archived:
            raise ValueError("Une année archivée ne peut pas être réactivée.")
        if self.is_closed:
            raise ValueError("Une année terminée ne peut pas être réactivée.")
        # Désactiver les autres années actives
        SchoolYear.objects.filter(is_active=True).exclude(pk=self.pk).update(is_active=False)
        self.is_active = True
        self.is_closed = False
        if save:
            self.save(update_fields=["is_active", "is_closed", "updated_at"])

    def end(self, closed_by=None, save: bool = True):
        """Clôture cette année scolaire."""
        if not self.is_active:
            raise ValueError("Seule l'année active peut être clôturée.")
        self.is_active = False
        self.is_closed = True
        self.closed_at = timezone.now()
        if closed_by:
            self.closed_by = closed_by
        if save:
            fields = ["is_active", "is_closed", "closed_at", "updated_at"]
            if closed_by:
                fields.append("closed_by")
            self.save(update_fields=fields)

    def archive(self, save: bool = True):
        """Archive définitivement cette année scolaire."""
        if self.is_active:
            raise ValueError("Clôturez d'abord l'année avant de l'archiver.")
        if not self.is_closed:
            raise ValueError("Seule une année terminée peut être archivée.")
        self.is_archived = True
        if save:
            self.save(update_fields=["is_archived", "updated_at"])

    # ------------------------------------------------------------------
    # Classmethods
    # ------------------------------------------------------------------

    @classmethod
    def get_active(cls):
        """Retourne l'année scolaire active, None si aucune."""
        return cls.objects.filter(is_active=True).first()
