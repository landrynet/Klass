"""
Managers personnalisés pour le modèle User de KLASS.
"""
from django.contrib.auth.models import BaseUserManager
from apps.core.constants import Roles


class UserManager(BaseUserManager):
    """Manager personnalisé pour le modèle User de KLASS."""

    def create_user(self, email, password=None, **extra_fields):
        """Crée et sauvegarde un utilisateur avec l'email et le mot de passe donnés."""
        if not email:
            raise ValueError("L'adresse email est obligatoire.")
        email = self.normalize_email(email)
        extra_fields.setdefault("is_active", True)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """Crée et sauvegarde un Super-Admin."""
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", Roles.SUPER_ADMIN)
        extra_fields.setdefault("is_active", True)

        if not extra_fields.get("is_staff"):
            raise ValueError("Le Super-Admin doit avoir is_staff=True.")
        if not extra_fields.get("is_superuser"):
            raise ValueError("Le Super-Admin doit avoir is_superuser=True.")

        return self.create_user(email, password, **extra_fields)

    def get_by_role(self, role):
        """Retourne tous les utilisateurs d'un rôle donné."""
        return self.filter(role=role, is_active=True)

    def school_staff(self):
        """Retourne tous les membres du personnel scolaire."""
        return self.filter(role__in=Roles.SCHOOL_STAFF_ROLES, is_active=True)

    def portal_users(self):
        """Retourne tous les utilisateurs du portail (parents + élèves)."""
        return self.filter(role__in=Roles.PORTAL_ROLES, is_active=True)
