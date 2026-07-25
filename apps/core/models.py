"""
Modèles abstraits de base pour KLASS.
Tous les modèles tenant héritent de TenantAwareModel.
"""
from django.db import models
from django.utils import timezone


class TimeStampedModel(models.Model):
    """Modèle abstrait avec timestamps automatiques."""
    created_at = models.DateTimeField(default=timezone.now, editable=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class TenantAwareModel(TimeStampedModel):
    """
    Modèle abstrait pour toutes les entités tenant-spécifiques.
    Ces modèles ont leurs tables dans le schéma de l'école (tenant).
    La séparation multi-tenant est assurée au niveau PostgreSQL par django-tenants.
    """
    class Meta:
        abstract = True


class SoftDeleteModel(models.Model):
    """Modèle abstrait avec suppression logique (soft delete)."""
    deleted_at = models.DateTimeField(null=True, blank=True)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        abstract = True

    def soft_delete(self):
        self.deleted_at = timezone.now()
        self.is_deleted = True
        self.save(update_fields=["deleted_at", "is_deleted"])

    def restore(self):
        self.deleted_at = None
        self.is_deleted = False
        self.save(update_fields=["deleted_at", "is_deleted"])
