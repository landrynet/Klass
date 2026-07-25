"""
Modèle utilisateur personnalisé pour KLASS.
Remplace le modèle Django par défaut (AUTH_USER_MODEL = 'accounts.User').

Le modèle User est dans SHARED_APPS (schéma public) pour permettre :
- au Super-Admin d'exister globalement
- l'authentification avant le routing tenant
"""
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils import timezone
from apps.core.constants import Roles
from .managers import UserManager


class User(AbstractBaseUser, PermissionsMixin):
    """
    Utilisateur KLASS avec système de rôles.

    Rôles:
    - super_admin : accès global, gère les écoles (schéma public)
    - school_admin : directeur, accès complet à son école
    - secretary   : secrétariat, gestion des inscriptions
    - accountant  : comptabilité, module paiement
    - teacher     : enseignant, emploi du temps + ressources
    - parent      : portail, accès en lecture à ses enfants
    - student     : portail, accès en lecture à ses données
    """
    # Identifiant principal — email au lieu du username
    email = models.EmailField(unique=True, verbose_name="Adresse email")

    # Informations personnelles
    first_name = models.CharField(max_length=100, verbose_name="Prénom")
    last_name = models.CharField(max_length=100, verbose_name="Nom")
    phone = models.CharField(max_length=20, blank=True, verbose_name="Téléphone")
    photo = models.ImageField(
        upload_to="users/photos/",
        null=True,
        blank=True,
        verbose_name="Photo"
    )

    # Rôle
    role = models.CharField(
        max_length=20,
        choices=Roles.CHOICES,
        default=Roles.STUDENT,
        verbose_name="Rôle"
    )

    # Statut
    is_active = models.BooleanField(default=True, verbose_name="Actif")
    is_staff = models.BooleanField(
        default=False,
        verbose_name="Accès admin",
        help_text="Autorise l'accès à l'interface d'administration Django."
    )

    # Sécurité — première connexion
    must_change_password = models.BooleanField(
        default=False,
        verbose_name="Doit changer son mot de passe",
        help_text="Si True, l'utilisateur est redirigé vers le changement de mot de passe à la connexion."
    )

    # Timestamps
    date_joined = models.DateTimeField(default=timezone.now, verbose_name="Date d'inscription")
    last_login_ip = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name="Dernière IP de connexion"
    )

    # École associée (null pour super_admin)
    school = models.ForeignKey(
        "tenants.School",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="staff",
        verbose_name="École",
        help_text="L'école à laquelle appartient cet utilisateur (null pour le Super Admin)."
    )

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name", "role"]

    class Meta:
        verbose_name = "Utilisateur"
        verbose_name_plural = "Utilisateurs"
        ordering = ["last_name", "first_name"]

    def __str__(self):
        return f"{self.get_full_name()} ({self.get_role_display()})"

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    def get_short_name(self):
        return self.first_name

    # ---------------------------------------------------------------------------
    # Propriétés de rôle (raccourcis pour les templates et vues)
    # ---------------------------------------------------------------------------
    @property
    def is_super_admin(self):
        return self.role == Roles.SUPER_ADMIN

    @property
    def is_school_admin(self):
        return self.role == Roles.SCHOOL_ADMIN

    @property
    def is_secretary(self):
        return self.role == Roles.SECRETARY

    @property
    def is_accountant(self):
        return self.role == Roles.ACCOUNTANT

    @property
    def is_teacher(self):
        return self.role == Roles.TEACHER

    @property
    def is_parent(self):
        return self.role == Roles.PARENT

    @property
    def is_student(self):
        return self.role == Roles.STUDENT

    @property
    def is_school_staff(self):
        return self.role in Roles.SCHOOL_STAFF_ROLES

    @property
    def is_portal_user(self):
        return self.role in Roles.PORTAL_ROLES
