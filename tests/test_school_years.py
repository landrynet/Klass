"""
Tests — Phase 2.0 : Années scolaires.
Vérifie le cycle de vie, les transitions d'état, et l'isolation tenant.

Utilise SimpleTestCase pour les tests de logique pure (sans DB).
Les tests d'intégration complète nécessiteraient une configuration
multi-tenant avec vrai PostgreSQL (hors scope tests unitaires).
"""
from django.test import SimpleTestCase


class TestSchoolYearModel(SimpleTestCase):
    """Tests du modèle SchoolYear — logique de statut et transitions."""

    def _make_year(self, is_active=False, is_closed=False, is_archived=False):
        from apps.school_years.models import SchoolYear
        import datetime
        year = SchoolYear(
            name="2025-2026",
            start_date=datetime.date(2025, 9, 1),
            end_date=datetime.date(2026, 6, 30),
            is_active=is_active,
            is_closed=is_closed,
            is_archived=is_archived,
        )
        return year

    # ------------------------------------------------------------------
    # Statut dérivé
    # ------------------------------------------------------------------

    def test_status_planned(self):
        """Un year non actif, non clôturé, non archivé est Planifié."""
        year = self._make_year()
        self.assertEqual(year.status, "planned")
        self.assertEqual(year.status_display, "Planifiée")

    def test_status_active(self):
        """Un year actif est en statut Active."""
        year = self._make_year(is_active=True)
        self.assertEqual(year.status, "active")
        self.assertEqual(year.status_display, "Active")

    def test_status_ended(self):
        """Un year clôturé (non archivé) est en statut Terminé."""
        year = self._make_year(is_closed=True)
        self.assertEqual(year.status, "ended")
        self.assertEqual(year.status_display, "Terminée")

    def test_status_archived(self):
        """Un year clôturé et archivé est en statut Archivé."""
        year = self._make_year(is_closed=True, is_archived=True)
        self.assertEqual(year.status, "archived")
        self.assertEqual(year.status_display, "Archivée")

    # ------------------------------------------------------------------
    # Propriétés de permission
    # ------------------------------------------------------------------

    def test_is_editable_planned(self):
        """Un year planifié est modifiable."""
        year = self._make_year()
        self.assertTrue(year.is_editable)

    def test_is_editable_active(self):
        """Un year actif est modifiable."""
        year = self._make_year(is_active=True)
        self.assertTrue(year.is_editable)

    def test_is_editable_closed(self):
        """Un year clôturé n'est plus modifiable."""
        year = self._make_year(is_closed=True)
        self.assertFalse(year.is_editable)

    def test_is_editable_archived(self):
        """Un year archivé n'est plus modifiable."""
        year = self._make_year(is_closed=True, is_archived=True)
        self.assertFalse(year.is_editable)

    def test_can_activate_planned(self):
        """Seul un year planifié peut être activé."""
        year = self._make_year()
        self.assertTrue(year.can_activate)

    def test_can_activate_active(self):
        """Un year déjà actif ne peut pas être réactivé."""
        year = self._make_year(is_active=True)
        self.assertFalse(year.can_activate)

    def test_can_end_active(self):
        """Seul un year actif peut être clôturé."""
        year = self._make_year(is_active=True)
        self.assertTrue(year.can_end)

    def test_can_end_planned(self):
        """Un year planifié ne peut pas être clôturé."""
        year = self._make_year()
        self.assertFalse(year.can_end)

    def test_can_archive_ended(self):
        """Un year terminé peut être archivé."""
        year = self._make_year(is_closed=True)
        self.assertTrue(year.can_archive)

    def test_can_archive_planned(self):
        """Un year planifié ne peut pas être archivé directement."""
        year = self._make_year()
        self.assertFalse(year.can_archive)

    # ------------------------------------------------------------------
    # Validation des dates
    # ------------------------------------------------------------------

    def test_clean_invalid_dates(self):
        """start_date >= end_date déclenche une ValidationError."""
        from django.core.exceptions import ValidationError
        import datetime
        from apps.school_years.models import SchoolYear
        year = SchoolYear(
            name="2025-2026",
            start_date=datetime.date(2026, 6, 1),
            end_date=datetime.date(2025, 9, 1),
        )
        with self.assertRaises(ValidationError):
            year.clean()

    def test_clean_valid_dates(self):
        """Dates valides ne déclenchent pas d'erreur."""
        import datetime
        from apps.school_years.models import SchoolYear
        year = SchoolYear(
            name="2025-2026",
            start_date=datetime.date(2025, 9, 1),
            end_date=datetime.date(2026, 6, 30),
        )
        year.clean()  # ne doit pas lever

    # ------------------------------------------------------------------
    # Badges CSS
    # ------------------------------------------------------------------

    def test_status_badge_class_active(self):
        """L'année active a une classe badge verte."""
        year = self._make_year(is_active=True)
        self.assertIn("success", year.status_badge_class)

    def test_status_badge_class_archived(self):
        """L'année archivée a une classe badge sombre."""
        year = self._make_year(is_closed=True, is_archived=True)
        self.assertIn("dark", year.status_badge_class)


class TestSchoolYearModelFields(SimpleTestCase):
    """Tests des champs du modèle SchoolYear."""

    def test_model_has_is_archived_field(self):
        """Le modèle SchoolYear possède le champ is_archived."""
        from apps.school_years.models import SchoolYear
        field = SchoolYear._meta.get_field("is_archived")
        self.assertFalse(field.default)

    def test_model_ordering(self):
        """Les années scolaires sont triées par date de début décroissante."""
        from apps.school_years.models import SchoolYear
        self.assertEqual(SchoolYear._meta.ordering, ["-start_date"])


class TestSchoolYearForms(SimpleTestCase):
    """Tests des formulaires d'années scolaires."""

    def test_form_valid_data(self):
        """Formulaire valide avec des données correctes."""
        from apps.school_years.forms import SchoolYearForm
        form = SchoolYearForm(data={
            "name": "2025-2026",
            "start_date": "2025-09-01",
            "end_date": "2026-06-30",
            "activate": False,
        })
        self.assertTrue(form.is_valid(), form.errors)

    def test_form_invalid_dates(self):
        """Formulaire invalide si end_date <= start_date."""
        from apps.school_years.forms import SchoolYearForm
        form = SchoolYearForm(data={
            "name": "2025-2026",
            "start_date": "2026-06-01",
            "end_date": "2025-09-01",
            "activate": False,
        })
        self.assertFalse(form.is_valid())

    def test_form_missing_name(self):
        """Formulaire invalide sans nom."""
        from apps.school_years.forms import SchoolYearForm
        form = SchoolYearForm(data={
            "start_date": "2025-09-01",
            "end_date": "2026-06-30",
        })
        self.assertFalse(form.is_valid())
        self.assertIn("name", form.errors)
