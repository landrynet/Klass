"""
Modèles multi-tenant pour KLASS.
School est le modèle tenant principal (un schéma PostgreSQL par école).
Domain gère les sous-domaines d'accès (ex: ecoleA.klass.app).
"""
from django.db import models
from django_tenants.models import TenantMixin, DomainMixin
from apps.core.constants import SubscriptionStatus


class School(TenantMixin):
    """
    Représente une école cliente dans la plateforme KLASS.
    Hérite de TenantMixin (django-tenants) qui gère le schéma PostgreSQL dédié.

    Chaque instance de School correspond à :
    - Un schéma PostgreSQL isolé (ex: schema_name = 'ecole_xyz')
    - Un sous-domaine dédié (ex: ecole-xyz.klass.app via le modèle Domain)
    - Des données complètement isolées des autres écoles
    """
    # Informations de base
    name = models.CharField(max_length=200, verbose_name="Nom de l'établissement")
    slug = models.SlugField(max_length=50, unique=True, verbose_name="Identifiant URL")
    email = models.EmailField(verbose_name="Email de contact")
    phone = models.CharField(max_length=20, blank=True, verbose_name="Téléphone")
    address = models.TextField(blank=True, verbose_name="Adresse")
    city = models.CharField(max_length=100, blank=True, verbose_name="Ville")
    country = models.CharField(max_length=100, default="Congo (RDC)", verbose_name="Pays")
    logo = models.ImageField(
        upload_to="schools/logos/",
        null=True,
        blank=True,
        verbose_name="Logo"
    )

    # Statut et abonnement
    is_active = models.BooleanField(default=True, verbose_name="Active")
    subscription_status = models.CharField(
        max_length=20,
        choices=SubscriptionStatus.CHOICES,
        default=SubscriptionStatus.TRIAL,
        verbose_name="Statut abonnement"
    )
    subscription_expires_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Expiration abonnement"
    )

    # Configuration initiale
    setup_completed = models.BooleanField(
        default=False,
        verbose_name="Configuration initiale terminée",
        help_text="Mis à True après que l'Admin école a complété l'assistant de configuration"
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # django-tenants crée automatiquement le schéma PostgreSQL à la sauvegarde
    auto_create_schema = True

    class Meta:
        verbose_name = "École"
        verbose_name_plural = "Écoles"
        ordering = ["name"]

    def __str__(self):
        return self.name

    @property
    def is_trial(self):
        return self.subscription_status == SubscriptionStatus.TRIAL

    @property
    def is_operational(self):
        """Une école est opérationnelle si active et configuration terminée."""
        return self.is_active and self.setup_completed


class Domain(DomainMixin):
    """
    Gestion des sous-domaines pour accéder à une école.
    Ex: ecole-xyz.klass.app → School(slug='ecole-xyz')

    Un même tenant peut avoir plusieurs domaines (domaine principal + alias).
    """
    class Meta:
        verbose_name = "Domaine"
        verbose_name_plural = "Domaines"

    def __str__(self):
        primary = " (principal)" if self.is_primary else ""
        return f"{self.domain}{primary} → {self.tenant.name}"
