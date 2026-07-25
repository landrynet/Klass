"""
Module 5 — Bibliothèque / Ressources Pédagogiques Numériques.
Upload, organisation et contrôle d'accès des ressources.
Stockage externalisé (Cloudflare R2 / Backblaze B2) via django-storages.
"""
from django.db import models
from apps.core.models import TenantAwareModel
from apps.core.constants import ResourceType


class Resource(TenantAwareModel):
    """
    Ressource pédagogique publiée par un enseignant.
    Stockée en externe (S3-compatible) via django-storages.
    Visible uniquement par les élèves des classes/niveaux ciblés.
    """
    title = models.CharField(max_length=200, verbose_name="Titre")
    description = models.TextField(blank=True, verbose_name="Description")

    resource_type = models.CharField(
        max_length=20,
        choices=ResourceType.CHOICES,
        default=ResourceType.PDF,
        verbose_name="Type"
    )

    # Fichier (stockage externe en production, local en développement)
    file = models.FileField(
        upload_to="resources/%Y/%m/",
        null=True,
        blank=True,
        verbose_name="Fichier"
    )
    external_url = models.URLField(
        blank=True,
        verbose_name="URL externe",
        help_text="Pour les liens YouTube, Drive, etc."
    )
    file_size = models.PositiveBigIntegerField(
        null=True,
        blank=True,
        verbose_name="Taille (octets)"
    )

    # Métadonnées académiques
    subject = models.ForeignKey(
        "academics.Subject",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="resources",
        verbose_name="Matière"
    )
    school_year = models.ForeignKey(
        "school_years.SchoolYear",
        on_delete=models.CASCADE,
        related_name="resources",
        verbose_name="Année scolaire"
    )

    # Publication
    uploaded_by = models.ForeignKey(
        "accounts.User",
        null=True,
        on_delete=models.SET_NULL,
        related_name="resources_uploaded",
        verbose_name="Publié par"
    )
    is_published = models.BooleanField(
        default=True,
        verbose_name="Publié",
        help_text="Décochez pour masquer temporairement aux élèves."
    )

    class Meta:
        verbose_name = "Ressource pédagogique"
        verbose_name_plural = "Ressources pédagogiques"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.title} ({self.get_resource_type_display()})"


class ResourceAccess(TenantAwareModel):
    """
    Contrôle d'accès à une ressource par classe ou niveau.
    Une ressource sans ResourceAccess est visible par tous.
    Une ressource avec ResourceAccess est visible uniquement par les cibles.
    """
    resource = models.ForeignKey(
        Resource,
        on_delete=models.CASCADE,
        related_name="access_rules",
        verbose_name="Ressource"
    )
    classroom = models.ForeignKey(
        "academics.Classroom",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="resource_accesses",
        verbose_name="Classe",
        help_text="Laisser vide si l'accès est par niveau."
    )
    level = models.ForeignKey(
        "academics.Level",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="resource_accesses",
        verbose_name="Niveau",
        help_text="Laisser vide si l'accès est par classe."
    )

    class Meta:
        verbose_name = "Règle d'accès"
        verbose_name_plural = "Règles d'accès"

    def __str__(self):
        target = self.classroom or self.level or "Tous"
        return f"{self.resource.title} → {target}"
