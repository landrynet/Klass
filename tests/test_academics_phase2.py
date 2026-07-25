"""
Tests — Phase 2.0 : Niveaux et Options.
Vérifie les modèles, formulaires et isolation tenant.
"""
from django.test import SimpleTestCase


class TestLevelModel(SimpleTestCase):
    """Tests du modèle Level."""

    def test_level_has_is_active_field(self):
        """Le modèle Level possède le champ is_active."""
        from apps.academics.models import Level
        field = Level._meta.get_field("is_active")
        self.assertTrue(field.default)  # défaut = True

    def test_level_has_order_field(self):
        """Le modèle Level possède le champ order."""
        from apps.academics.models import Level
        field = Level._meta.get_field("order")
        self.assertEqual(field.default, 0)

    def test_level_ordering(self):
        """Les niveaux sont triés par ordre puis par nom."""
        from apps.academics.models import Level
        self.assertEqual(Level._meta.ordering, ["order", "name"])

    def test_level_unique_together(self):
        """Un niveau est unique par (school_year, name)."""
        from apps.academics.models import Level
        unique = [list(c) for c in Level._meta.unique_together]
        self.assertIn(["school_year", "name"], unique)

    def test_level_str_representation(self):
        """Le __str__ du niveau inclut l'année scolaire."""
        from apps.academics.models import Level
        from apps.school_years.models import SchoolYear
        import datetime
        year = SchoolYear(name="2025-2026",
                          start_date=datetime.date(2025, 9, 1),
                          end_date=datetime.date(2026, 6, 30))
        level = Level(name="1ère secondaire", school_year=year)
        self.assertIn("1ère secondaire", str(level))
        self.assertIn("2025-2026", str(level))


class TestOptionModel(SimpleTestCase):
    """Tests du modèle Option."""

    def test_option_has_is_active_field(self):
        """Le modèle Option possède le champ is_active."""
        from apps.academics.models import Option
        field = Option._meta.get_field("is_active")
        self.assertTrue(field.default)  # défaut = True

    def test_option_unique_together(self):
        """Une option est unique par (level, name)."""
        from apps.academics.models import Option
        unique = [list(c) for c in Option._meta.unique_together]
        self.assertIn(["level", "name"], unique)

    def test_option_has_description_field(self):
        """Le modèle Option possède le champ description (nullable)."""
        from apps.academics.models import Option
        field = Option._meta.get_field("description")
        self.assertTrue(field.blank)

    def test_option_str_representation(self):
        """Le __str__ de l'option inclut le niveau."""
        from apps.academics.models import Level, Option
        from apps.school_years.models import SchoolYear
        import datetime
        year = SchoolYear(name="2025-2026",
                          start_date=datetime.date(2025, 9, 1),
                          end_date=datetime.date(2026, 6, 30))
        level = Level(name="4ème secondaire", school_year=year)
        option = Option(name="Scientifique", level=level)
        self.assertIn("Scientifique", str(option))
        self.assertIn("4ème secondaire", str(option))


class TestAcademicsForms(SimpleTestCase):
    """Tests des formulaires academics (sans DB)."""

    def test_level_form_requires_school_year_queryset(self):
        """LevelForm initialisé sans queryset a le champ school_year."""
        from apps.academics.forms import LevelForm
        # Sans queryset, le champ existe mais queryset est None
        form = LevelForm(school_year_queryset=None)
        self.assertIn("school_year", form.fields)
        self.assertIn("name", form.fields)
        self.assertIn("code", form.fields)
        self.assertIn("order", form.fields)
        self.assertIn("is_active", form.fields)

    def test_option_form_fields_present(self):
        """OptionForm contient les champs attendus."""
        from apps.academics.forms import OptionForm
        form = OptionForm(level_queryset=None)
        self.assertIn("level", form.fields)
        self.assertIn("name", form.fields)
        self.assertIn("code", form.fields)
        self.assertIn("description", form.fields)
        self.assertIn("is_active", form.fields)

    def test_level_form_code_cleaned_uppercase(self):
        """Le code est normalisé en majuscules."""
        from apps.academics.forms import LevelForm
        form = LevelForm.__new__(LevelForm)
        form.cleaned_data = {"code": "sec1"}
        result = form.clean_code()
        self.assertEqual(result, "SEC1")

    def test_option_form_name_stripped(self):
        """Le nom est trimé des espaces."""
        from apps.academics.forms import OptionForm
        form = OptionForm.__new__(OptionForm)
        form.cleaned_data = {"name": "  Scientifique  "}
        result = form.clean_name()
        self.assertEqual(result, "Scientifique")


class TestAcademicsTenantIsolation(SimpleTestCase):
    """Tests de configuration de l'isolation tenant pour les academics."""

    def test_academics_in_tenant_apps(self):
        """L'app academics est dans les apps tenant (isolation par schéma)."""
        from config.tenant_config import TENANT_APPS
        self.assertIn("apps.academics", TENANT_APPS)

    def test_school_years_in_tenant_apps(self):
        """L'app school_years est dans les apps tenant."""
        from config.tenant_config import TENANT_APPS
        self.assertIn("apps.school_years", TENANT_APPS)

    def test_level_model_is_tenant_aware(self):
        """Level hérite de TenantAwareModel."""
        from apps.academics.models import Level
        from apps.core.models import TenantAwareModel
        self.assertTrue(issubclass(Level, TenantAwareModel))

    def test_option_model_is_tenant_aware(self):
        """Option hérite de TenantAwareModel."""
        from apps.academics.models import Option
        from apps.core.models import TenantAwareModel
        self.assertTrue(issubclass(Option, TenantAwareModel))

    def test_school_year_model_is_tenant_aware(self):
        """SchoolYear hérite de TenantAwareModel."""
        from apps.school_years.models import SchoolYear
        from apps.core.models import TenantAwareModel
        self.assertTrue(issubclass(SchoolYear, TenantAwareModel))

    def test_academics_not_in_shared_apps(self):
        """Les données académiques ne sont pas dans SHARED_APPS."""
        from config.tenant_config import SHARED_APPS
        self.assertNotIn("apps.academics", SHARED_APPS)
        self.assertNotIn("apps.school_years", SHARED_APPS)
