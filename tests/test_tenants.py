"""
Tests du socle multi-tenant KLASS.
Vérifie que les tenants sont correctement configurés (tests sans DB).
"""
from django.test import SimpleTestCase


class TestSchoolModel(SimpleTestCase):
    """Tests du modèle School (tenant) — sans accès DB."""

    def test_school_str_representation(self):
        """Le __str__ du School retourne son nom."""
        from apps.tenants.models import School
        school = School(name="École de Lubumbashi", slug="ecole-lubs")
        self.assertEqual(str(school), "École de Lubumbashi")

    def test_school_is_trial_property(self):
        """Une école en essai est correctement identifiée."""
        from apps.tenants.models import School
        from apps.core.constants import SubscriptionStatus
        school = School(
            name="Test",
            slug="test",
            subscription_status=SubscriptionStatus.TRIAL
        )
        self.assertTrue(school.is_trial)

    def test_school_is_operational_requires_setup(self):
        """Une école n'est opérationnelle que si is_active ET setup_completed."""
        from apps.tenants.models import School
        school = School(name="Test", slug="test", is_active=True, setup_completed=False)
        self.assertFalse(school.is_operational)
        school.setup_completed = True
        self.assertTrue(school.is_operational)

    def test_school_inactive_not_operational(self):
        """Une école inactive n'est pas opérationnelle même si configurée."""
        from apps.tenants.models import School
        school = School(name="Test", slug="test", is_active=False, setup_completed=True)
        self.assertFalse(school.is_operational)


class TestTenantIsolation(SimpleTestCase):
    """
    Tests de la configuration multi-tenant.
    Tests d'architecture/logique sans connexion DB.
    """

    def test_school_slug_unique(self):
        """Deux écoles ne peuvent pas avoir le même slug."""
        from apps.tenants.models import School
        slug_field = School._meta.get_field("slug")
        self.assertTrue(slug_field.unique)

    def test_tenant_model_registered(self):
        """Le modèle tenant est correctement déclaré dans settings."""
        from django.conf import settings
        self.assertEqual(settings.TENANT_MODEL, "tenants.School")
        self.assertEqual(settings.TENANT_DOMAIN_MODEL, "tenants.Domain")

    def test_tenant_router_configured(self):
        """Le router multi-tenant est configuré."""
        from django.conf import settings
        self.assertIn(
            "django_tenants.routers.TenantSyncRouter",
            settings.DATABASE_ROUTERS
        )

    def test_tenant_backend_configured(self):
        """Le backend PostgreSQL multi-tenant est configuré."""
        from django.conf import settings
        self.assertEqual(
            settings.DATABASES["default"]["ENGINE"],
            "django_tenants.postgresql_backend"
        )

    def test_shared_apps_contains_tenants(self):
        """SHARED_APPS contient les apps de gestion des tenants."""
        from django.conf import settings
        self.assertIn("apps.tenants", settings.INSTALLED_APPS)
        self.assertIn("django_tenants", settings.INSTALLED_APPS)

    def test_tenant_apps_not_in_shared(self):
        """Les apps tenant ne gèrent pas de données globales."""
        from config.tenant_config import SHARED_APPS, TENANT_APPS
        # Les apps tenant ne doivent pas inclure des données globales
        # (elles doivent rester isolées par schéma)
        self.assertNotIn("apps.finance", SHARED_APPS)
        self.assertNotIn("apps.students", SHARED_APPS)
        self.assertNotIn("apps.scheduling", SHARED_APPS)

    def test_school_model_has_auto_create_schema(self):
        """School.auto_create_schema est activé (création automatique du schéma)."""
        from apps.tenants.models import School
        self.assertTrue(School.auto_create_schema)
