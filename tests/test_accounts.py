"""
Tests du module Comptes utilisateurs KLASS.
Vérifie l'authentification, les rôles et les permissions.
Tests purement unitaires (pas de connexion DB requise).
"""
from django.test import SimpleTestCase
from apps.core.constants import Roles


class TestUserModel(SimpleTestCase):
    """Tests du modèle User personnalisé — sans accès DB."""

    def setUp(self):
        """Crée une instance User non sauvegardée."""
        from apps.accounts.models import User
        self.user = User(
            email="test@klass.app",
            first_name="Alice",
            last_name="Dupont",
            role=Roles.SCHOOL_ADMIN,
        )

    def test_user_full_name(self):
        """get_full_name retourne Prénom Nom."""
        self.assertEqual(self.user.get_full_name(), "Alice Dupont")

    def test_user_short_name(self):
        """get_short_name retourne le prénom."""
        self.assertEqual(self.user.get_short_name(), "Alice")

    def test_user_str(self):
        """__str__ retourne nom complet + rôle."""
        self.assertIn("Alice Dupont", str(self.user))
        self.assertIn("Admin École", str(self.user))

    def test_is_school_admin_property(self):
        """is_school_admin est True pour le rôle school_admin."""
        self.assertTrue(self.user.is_school_admin)
        self.assertFalse(self.user.is_super_admin)
        self.assertFalse(self.user.is_teacher)

    def test_is_school_staff_property(self):
        """is_school_staff est True pour les rôles du personnel."""
        self.assertTrue(self.user.is_school_staff)
        self.assertFalse(self.user.is_portal_user)

    def test_portal_user_property(self):
        """is_portal_user est True pour parent et student."""
        from apps.accounts.models import User
        parent = User(role=Roles.PARENT)
        student = User(role=Roles.STUDENT)
        admin = User(role=Roles.SCHOOL_ADMIN)

        self.assertTrue(parent.is_portal_user)
        self.assertTrue(student.is_portal_user)
        self.assertFalse(admin.is_portal_user)

    def test_all_roles_defined(self):
        """Tous les 7 rôles du projet sont définis."""
        expected_roles = {
            Roles.SUPER_ADMIN,
            Roles.SCHOOL_ADMIN,
            Roles.SECRETARY,
            Roles.ACCOUNTANT,
            Roles.TEACHER,
            Roles.PARENT,
            Roles.STUDENT,
        }
        actual_roles = set(Roles.all_values())
        self.assertEqual(expected_roles, actual_roles)

    def test_auth_user_model_configured(self):
        """AUTH_USER_MODEL est correctement configuré."""
        from django.conf import settings
        self.assertEqual(settings.AUTH_USER_MODEL, "accounts.User")

    def test_user_username_field_is_email(self):
        """Le champ d'identification est l'email (pas username)."""
        from apps.accounts.models import User
        self.assertEqual(User.USERNAME_FIELD, "email")


class TestRolesConstants(SimpleTestCase):
    """Tests des constantes de rôles."""

    def test_school_staff_roles(self):
        """Les rôles du personnel scolaire sont corrects."""
        expected = {Roles.SCHOOL_ADMIN, Roles.SECRETARY, Roles.ACCOUNTANT, Roles.TEACHER}
        actual = set(Roles.SCHOOL_STAFF_ROLES)
        self.assertEqual(expected, actual)

    def test_portal_roles(self):
        """Les rôles du portail sont corrects."""
        expected = {Roles.PARENT, Roles.STUDENT}
        actual = set(Roles.PORTAL_ROLES)
        self.assertEqual(expected, actual)

    def test_super_admin_not_in_school_staff(self):
        """Le super_admin n'est pas dans les rôles école."""
        self.assertNotIn(Roles.SUPER_ADMIN, Roles.SCHOOL_STAFF_ROLES)

    def test_super_admin_not_in_portal(self):
        """Le super_admin n'est pas dans les rôles portail."""
        self.assertNotIn(Roles.SUPER_ADMIN, Roles.PORTAL_ROLES)

    def test_seven_roles_total(self):
        """Il y a exactement 7 rôles définis."""
        self.assertEqual(len(Roles.CHOICES), 7)

    def test_write_roles_subset_of_staff(self):
        """Les rôles avec droits d'écriture sont un sous-ensemble du personnel."""
        for role in Roles.WRITE_ROLES:
            self.assertIn(role, Roles.SCHOOL_STAFF_ROLES)
