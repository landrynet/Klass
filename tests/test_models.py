"""
Tests des modèles métier de KLASS.
Tests unitaires sans connexion DB (SimpleTestCase).
"""
from django.test import SimpleTestCase


class TestSchoolYearModel(SimpleTestCase):
    """Tests du modèle SchoolYear."""

    def test_str_with_active(self):
        """__str__ inclut le statut 'Active' si l'année est active."""
        from apps.school_years.models import SchoolYear
        sy = SchoolYear(name="2025-2026", is_active=True, is_closed=False)
        self.assertIn("Active", str(sy))

    def test_str_with_closed(self):
        """__str__ inclut le statut 'Terminée' si l'année est clôturée."""
        from apps.school_years.models import SchoolYear
        sy = SchoolYear(name="2024-2025", is_active=False, is_closed=True)
        self.assertIn("Terminée", str(sy))

    def test_str_with_regular(self):
        """__str__ d'une année normale n'a pas de tag."""
        from apps.school_years.models import SchoolYear
        sy = SchoolYear(name="2023-2024", is_active=False, is_closed=False)
        self.assertNotIn("ACTIVE", str(sy))
        self.assertNotIn("CLÔTURÉE", str(sy))

    def test_is_editable_when_not_closed(self):
        """Une année non clôturée est modifiable."""
        from apps.school_years.models import SchoolYear
        sy = SchoolYear(is_closed=False)
        self.assertTrue(sy.is_editable)

    def test_is_not_editable_when_closed(self):
        """Une année clôturée n'est pas modifiable."""
        from apps.school_years.models import SchoolYear
        sy = SchoolYear(is_closed=True)
        self.assertFalse(sy.is_editable)


class TestStudentMatricule(SimpleTestCase):
    """Tests de la génération de matricule."""

    def test_generate_matricule_format(self):
        """Le matricule respecte le format KLS-YYYY-XXXXXX."""
        import re
        from apps.core.utils import generate_matricule
        matricule = generate_matricule()
        pattern = r"KLS-\d{4}-[A-Z0-9]{6}"
        self.assertRegex(matricule, pattern)

    def test_generate_multiple_matricules_unique(self):
        """Plusieurs appels génèrent des matricules différents (très probablement)."""
        from apps.core.utils import generate_matricule
        matricules = {generate_matricule() for _ in range(100)}
        self.assertGreater(len(matricules), 90)

    def test_generate_temp_password_length(self):
        """Le mot de passe temporaire a la longueur requise."""
        from apps.core.utils import generate_temp_password
        pwd = generate_temp_password(12)
        self.assertEqual(len(pwd), 12)

    def test_generate_temp_password_contains_uppercase(self):
        """Le mot de passe temporaire contient des majuscules."""
        import string
        from apps.core.utils import generate_temp_password
        pwd = generate_temp_password(12)
        self.assertTrue(any(c in string.ascii_uppercase for c in pwd))

    def test_generate_temp_password_contains_digits(self):
        """Le mot de passe temporaire contient des chiffres."""
        import string
        from apps.core.utils import generate_temp_password
        pwd = generate_temp_password(12)
        self.assertTrue(any(c in string.digits for c in pwd))

    def test_slugify_school_name(self):
        """slugify_school_name produit un slug valide."""
        from apps.core.utils import slugify_school_name
        slug = slugify_school_name("École Primaire de Lubumbashi")
        self.assertRegex(slug, r"^[a-z0-9-]+$")
        self.assertNotIn(" ", slug)
        self.assertLessEqual(len(slug), 30)


class TestScheduleConflict(SimpleTestCase):
    """Tests de logique de conflit d'emploi du temps (sans DB)."""

    def test_schedule_constraints_defined(self):
        """Les contraintes d'unicité sont définies sur le modèle Schedule."""
        from apps.scheduling.models import Schedule
        constraint_names = [c.name for c in Schedule._meta.constraints]
        self.assertIn("unique_teacher_per_timeslot", constraint_names)
        self.assertIn("unique_classroom_per_timeslot", constraint_names)

    def test_schedule_has_room_field(self):
        """Schedule a bien un champ room (nécessaire pour conflits de salle)."""
        from apps.scheduling.models import Schedule
        fields = [f.name for f in Schedule._meta.get_fields()]
        self.assertIn("room", fields)


class TestCeleryConfiguration(SimpleTestCase):
    """Tests de configuration Celery."""

    def test_celery_broker_configured(self):
        """Le broker Celery (Redis) est configuré."""
        from django.conf import settings
        self.assertTrue(hasattr(settings, "CELERY_BROKER_URL"))
        self.assertTrue(settings.CELERY_BROKER_URL)

    def test_celery_beat_scheduler(self):
        """Celery Beat utilise le scheduler Django."""
        from django.conf import settings
        self.assertEqual(
            settings.CELERY_BEAT_SCHEDULER,
            "django_celery_beat.schedulers:DatabaseScheduler"
        )

    def test_finance_task_defined(self):
        """La tâche de génération de reçu PDF est définie."""
        from apps.finance.tasks import generate_receipt_pdf
        self.assertTrue(callable(generate_receipt_pdf))

    def test_notification_task_defined(self):
        """La tâche d'envoi de notification est définie."""
        from apps.notifications.tasks import send_notification
        self.assertTrue(callable(send_notification))

    def test_debug_task_defined(self):
        """La tâche de test Celery est définie."""
        from config.celery import debug_task
        self.assertTrue(callable(debug_task))


class TestModelStructure(SimpleTestCase):
    """Tests de la structure des modèles (champs, Meta, relations)."""

    def test_user_required_fields(self):
        """User a les champs requis email, first_name, last_name, role."""
        from apps.accounts.models import User
        field_names = [f.name for f in User._meta.get_fields()]
        for field in ["email", "first_name", "last_name", "role", "must_change_password"]:
            self.assertIn(field, field_names, f"Champ manquant: {field}")

    def test_student_has_matricule_field(self):
        """Student a un champ matricule unique."""
        from apps.students.models import Student
        matricule_field = Student._meta.get_field("matricule")
        self.assertTrue(matricule_field.unique)

    def test_payment_has_reference_field(self):
        """Payment a un champ reference unique."""
        from apps.finance.models import Payment
        ref_field = Payment._meta.get_field("reference")
        self.assertTrue(ref_field.unique)

    def test_school_model_is_tenant_mixin(self):
        """School hérite de TenantMixin."""
        from apps.tenants.models import School
        from django_tenants.models import TenantMixin
        self.assertTrue(issubclass(School, TenantMixin))

    def test_domain_model_is_domain_mixin(self):
        """Domain hérite de DomainMixin."""
        from apps.tenants.models import Domain
        from django_tenants.models import DomainMixin
        self.assertTrue(issubclass(Domain, DomainMixin))

    def test_all_apps_have_appconfig(self):
        """Toutes les apps KLASS ont une AppConfig configurée."""
        from django.apps import apps
        klass_app_names = [
            "apps.core", "apps.tenants", "apps.accounts",
            "apps.school_years", "apps.academics", "apps.students",
            "apps.teachers", "apps.finance", "apps.scheduling",
            "apps.resources", "apps.portal", "apps.communications",
            "apps.notifications",
        ]
        installed = [app.name for app in apps.get_app_configs()]
        for app_name in klass_app_names:
            self.assertIn(app_name, installed, f"App non installée: {app_name}")
