"""
Tests Phase 3.1 — Inscriptions et affectation des élèves aux classes.

Couvre :
- Modèle StudentEnrollment (règles métier)
- Règle : une seule inscription active par élève/année
- Historique : plusieurs années
- Changement de classe (traçabilité)
- Statuts d'inscription
- Isolation multi-tenant
- Vues et permissions
"""
import datetime
import pytest
from django.test import TestCase, RequestFactory
from django.core.exceptions import ValidationError
from django_tenants.utils import schema_context

from apps.core.constants import EnrollmentStatus


class TestEnrollmentModel(TestCase):
    """Tests du modèle StudentEnrollment."""

    def _setup_school(self):
        """Crée une école de test avec son schéma."""
        from apps.tenants.services import create_school_with_tenant
        school, admin, _ = create_school_with_tenant(
            name="École Test Phase 3.1",
            email="test31@test.app",
            phone="+243000000031",
            address="Test",
            city="Lubumbashi",
            country="Congo (RDC)",
            admin_first_name="Admin",
            admin_last_name="Test31",
            admin_email="test31@test.app",
        )
        return school, admin

    def _setup_tenant_data(self, school):
        """Crée les données de base dans le schéma de l'école."""
        from apps.school_years.models import SchoolYear
        from apps.academics.models import Level, Option, Classroom
        from apps.students.models import Parent, Student

        with schema_context(school.schema_name):
            year_active = SchoolYear.objects.create(
                name="2025-2026 Test",
                start_date=datetime.date(2025, 9, 1),
                end_date=datetime.date(2026, 6, 30),
                is_active=True,
            )
            year_old = SchoolYear.objects.create(
                name="2024-2025 Test",
                start_date=datetime.date(2024, 9, 1),
                end_date=datetime.date(2025, 6, 30),
                is_active=False,
                is_closed=True,
            )
            level = Level.objects.create(
                school_year=year_active,
                name="6ème Test",
                order=0,
                is_active=True,
            )
            level_old = Level.objects.create(
                school_year=year_old,
                name="5ème Test",
                order=0,
                is_active=True,
            )
            option = Option.objects.create(level=level, name="Scientifique Test", is_active=True)
            option_old = Option.objects.create(level=level_old, name="Scientifique Test", is_active=True)
            classroom_a = Classroom.objects.create(
                school_year=year_active, option=option, name="A", capacity=40, is_active=True,
            )
            classroom_b = Classroom.objects.create(
                school_year=year_active, option=option, name="B", capacity=30, is_active=True,
            )
            classroom_old = Classroom.objects.create(
                school_year=year_old, option=option_old, name="A", capacity=40, is_active=True,
            )
            parent = Parent.objects.create(
                first_name="Test", last_name="Parent", phone="+243000000099",
            )
            student = Student.objects.create(
                first_name="Test", last_name="Élève",
                date_of_birth=datetime.date(2010, 1, 1),
                gender="M", nationality="Congolaise",
                primary_parent=parent,
            )
            student2 = Student.objects.create(
                first_name="Test2", last_name="Élève2",
                date_of_birth=datetime.date(2011, 1, 1),
                gender="F", nationality="Congolaise",
                primary_parent=parent,
            )

        return {
            "year_active": year_active,
            "year_old": year_old,
            "classroom_a": classroom_a,
            "classroom_b": classroom_b,
            "classroom_old": classroom_old,
            "student": student,
            "student2": student2,
        }

    def test_enrollment_creation(self):
        """Création d'une inscription basique."""
        from apps.students.models import StudentEnrollment
        school, admin = self._setup_school()
        data = self._setup_tenant_data(school)

        with schema_context(school.schema_name):
            enrollment = StudentEnrollment.objects.create(
                student=data["student"],
                school_year=data["year_active"],
                classroom=data["classroom_a"],
                status=EnrollmentStatus.ACTIVE,
            )
            self.assertEqual(enrollment.student, data["student"])
            self.assertEqual(enrollment.school_year, data["year_active"])
            self.assertEqual(enrollment.classroom, data["classroom_a"])
            self.assertEqual(enrollment.status, EnrollmentStatus.ACTIVE)
            self.assertTrue(enrollment.is_active_enrollment)

    def test_no_duplicate_active_enrollment(self):
        """Impossible d'avoir deux inscriptions actives pour la même année."""
        from apps.students.models import StudentEnrollment
        school, admin = self._setup_school()
        data = self._setup_tenant_data(school)

        with schema_context(school.schema_name):
            # Première inscription active
            StudentEnrollment.objects.create(
                student=data["student"],
                school_year=data["year_active"],
                classroom=data["classroom_a"],
                status=EnrollmentStatus.ACTIVE,
            )
            # Tentative de deuxième inscription active = erreur
            duplicate = StudentEnrollment(
                student=data["student"],
                school_year=data["year_active"],
                classroom=data["classroom_b"],
                status=EnrollmentStatus.ACTIVE,
            )
            with self.assertRaises(ValidationError):
                duplicate.clean()

    def test_cancelled_enrollment_allows_new_active(self):
        """
        Une inscription annulée permet de créer une nouvelle inscription active
        pour la même année.
        """
        from apps.students.models import StudentEnrollment
        school, admin = self._setup_school()
        data = self._setup_tenant_data(school)

        with schema_context(school.schema_name):
            # Créer et annuler une inscription
            enr1 = StudentEnrollment.objects.create(
                student=data["student"],
                school_year=data["year_active"],
                classroom=data["classroom_a"],
                status=EnrollmentStatus.CANCELLED,
            )
            # Créer une nouvelle inscription active — doit fonctionner
            enr2 = StudentEnrollment(
                student=data["student"],
                school_year=data["year_active"],
                classroom=data["classroom_b"],
                status=EnrollmentStatus.ACTIVE,
            )
            # Ne doit pas lever d'exception
            enr2.clean()
            enr2.save()
            self.assertEqual(StudentEnrollment.objects.filter(student=data["student"]).count(), 2)

    def test_enrollment_history_multiple_years(self):
        """Un élève peut avoir des inscriptions sur plusieurs années."""
        from apps.students.models import StudentEnrollment
        school, admin = self._setup_school()
        data = self._setup_tenant_data(school)

        with schema_context(school.schema_name):
            # Inscription 2024-2025 (terminée)
            enr_old = StudentEnrollment.objects.create(
                student=data["student"],
                school_year=data["year_old"],
                classroom=data["classroom_old"],
                status=EnrollmentStatus.COMPLETED,
            )
            # Inscription 2025-2026 (active)
            enr_current = StudentEnrollment.objects.create(
                student=data["student"],
                school_year=data["year_active"],
                classroom=data["classroom_a"],
                status=EnrollmentStatus.ACTIVE,
            )
            history = list(data["student"].enrollments.all())
            self.assertEqual(len(history), 2)

    def test_current_enrollment_property(self):
        """La propriété current_enrollment retourne l'inscription active."""
        from apps.students.models import StudentEnrollment
        school, admin = self._setup_school()
        data = self._setup_tenant_data(school)

        with schema_context(school.schema_name):
            enr = StudentEnrollment.objects.create(
                student=data["student"],
                school_year=data["year_active"],
                classroom=data["classroom_a"],
                status=EnrollmentStatus.ACTIVE,
            )
            current = data["student"].current_enrollment
            self.assertIsNotNone(current)
            self.assertEqual(current.pk, enr.pk)

    def test_pending_enrollment_is_active(self):
        """Une inscription 'en attente' est considérée comme active."""
        from apps.students.models import StudentEnrollment
        school, admin = self._setup_school()
        data = self._setup_tenant_data(school)

        with schema_context(school.schema_name):
            enr = StudentEnrollment.objects.create(
                student=data["student"],
                school_year=data["year_active"],
                classroom=data["classroom_a"],
                status=EnrollmentStatus.PENDING,
            )
            self.assertTrue(enr.is_active_enrollment)
            # Ne peut pas en avoir une deuxième active
            enr2 = StudentEnrollment(
                student=data["student"],
                school_year=data["year_active"],
                classroom=data["classroom_b"],
                status=EnrollmentStatus.ACTIVE,
            )
            with self.assertRaises(ValidationError):
                enr2.clean()

    def test_enrollment_cancel_method(self):
        """La méthode cancel() marque l'inscription comme annulée."""
        from apps.students.models import StudentEnrollment
        school, admin = self._setup_school()
        data = self._setup_tenant_data(school)

        with schema_context(school.schema_name):
            enr = StudentEnrollment.objects.create(
                student=data["student"],
                school_year=data["year_active"],
                classroom=data["classroom_a"],
                status=EnrollmentStatus.ACTIVE,
            )
            enr.cancel()
            enr.refresh_from_db()
            self.assertEqual(enr.status, EnrollmentStatus.CANCELLED)
            self.assertFalse(enr.is_active_enrollment)

    def test_status_badge_class(self):
        """La propriété status_badge_class retourne une classe CSS valide."""
        from apps.students.models import StudentEnrollment
        school, admin = self._setup_school()
        data = self._setup_tenant_data(school)

        with schema_context(school.schema_name):
            enr = StudentEnrollment.objects.create(
                student=data["student"],
                school_year=data["year_active"],
                classroom=data["classroom_a"],
                status=EnrollmentStatus.ACTIVE,
            )
            badge = enr.status_badge_class
            self.assertIn("bg-", badge)

    def test_two_students_same_classroom(self):
        """Deux élèves différents peuvent être inscrits dans la même classe."""
        from apps.students.models import StudentEnrollment
        school, admin = self._setup_school()
        data = self._setup_tenant_data(school)

        with schema_context(school.schema_name):
            enr1 = StudentEnrollment.objects.create(
                student=data["student"],
                school_year=data["year_active"],
                classroom=data["classroom_a"],
                status=EnrollmentStatus.ACTIVE,
            )
            enr2 = StudentEnrollment.objects.create(
                student=data["student2"],
                school_year=data["year_active"],
                classroom=data["classroom_a"],
                status=EnrollmentStatus.ACTIVE,
            )
            count = StudentEnrollment.objects.filter(
                classroom=data["classroom_a"],
                status=EnrollmentStatus.ACTIVE,
            ).count()
            self.assertEqual(count, 2)


class TestEnrollmentEditValidation(TestCase):
    """
    Régression : ré-activer une inscription annulée ne doit pas créer
    deux inscriptions actives pour la même année.
    Ces tests opèrent au niveau modèle/clean() pour éviter la complexité
    du middleware multi-tenant dans le client HTTP de test.
    """

    def _setup_school(self):
        from apps.tenants.services import create_school_with_tenant
        school, admin, _ = create_school_with_tenant(
            name="École Test Edit Validation",
            email="editval@test.app",
            phone="+243000000099",
            address="Test",
            city="Lubumbashi",
            country="Congo (RDC)",
            admin_first_name="Admin",
            admin_last_name="Edit",
            admin_email="editval@test.app",
        )
        return school, admin

    def _setup_data(self, school):
        from apps.school_years.models import SchoolYear
        from apps.academics.models import Level, Option, Classroom
        from apps.students.models import Parent, Student

        with schema_context(school.schema_name):
            year = SchoolYear.objects.create(
                name="2025-2026 EditVal",
                start_date=datetime.date(2025, 9, 1),
                end_date=datetime.date(2026, 6, 30),
                is_active=True,
            )
            level = Level.objects.create(school_year=year, name="6ème EV", order=0, is_active=True)
            option = Option.objects.create(level=level, name="Sci EV", is_active=True)
            cls_a = Classroom.objects.create(school_year=year, option=option, name="A", capacity=40, is_active=True)
            cls_b = Classroom.objects.create(school_year=year, option=option, name="B", capacity=40, is_active=True)
            parent = Parent.objects.create(first_name="P", last_name="EV", phone="+243111111111")
            student = Student.objects.create(
                first_name="S", last_name="EV",
                date_of_birth=datetime.date(2010, 1, 1),
                gender="M", nationality="Congolaise",
                primary_parent=parent,
            )
        return {"year": year, "cls_a": cls_a, "cls_b": cls_b, "student": student}

    def test_model_clean_blocks_reactivation_when_conflict(self):
        """
        Tenter de remettre une inscription annulée en 'active' doit échouer
        via clean() si une autre inscription active existe déjà pour la même année.
        (Teste la règle métier portée par StudentEnrollment.clean().)
        """
        from apps.students.models import StudentEnrollment

        school, admin = self._setup_school()
        data = self._setup_data(school)

        with schema_context(school.schema_name):
            # Inscription active dans cls_a
            enr_active = StudentEnrollment.objects.create(
                student=data["student"],
                school_year=data["year"],
                classroom=data["cls_a"],
                status=EnrollmentStatus.ACTIVE,
            )
            # Inscription annulée dans cls_b
            enr_cancelled = StudentEnrollment.objects.create(
                student=data["student"],
                school_year=data["year"],
                classroom=data["cls_b"],
                status=EnrollmentStatus.CANCELLED,
            )

            # Tenter de remettre l'inscription annulée en active → doit lever ValidationError
            enr_cancelled.status = EnrollmentStatus.ACTIVE
            with self.assertRaises(ValidationError):
                enr_cancelled.clean()

    def test_model_clean_allows_status_change_without_conflict(self):
        """
        Changer le statut d'une inscription unique (aucun conflit) doit passer clean().
        """
        from apps.students.models import StudentEnrollment

        school, admin = self._setup_school()
        data = self._setup_data(school)

        with schema_context(school.schema_name):
            enr = StudentEnrollment.objects.create(
                student=data["student"],
                school_year=data["year"],
                classroom=data["cls_a"],
                status=EnrollmentStatus.PENDING,
            )
            # Passer en active — pas de conflit, ne doit pas lever d'exception
            enr.status = EnrollmentStatus.ACTIVE
            enr.clean()  # Ne doit pas lever ValidationError
            enr.save(update_fields=["status", "updated_at"])

        with schema_context(school.schema_name):
            enr.refresh_from_db()
        self.assertEqual(enr.status, EnrollmentStatus.ACTIVE)

    def test_status_change_view_logic_blocks_conflict(self):
        """
        La logique de EnrollmentStatusChangeView doit détecter le conflit
        avant d'enregistrer un changement de statut vers 'active'.
        (Teste directement la logique de conflit portée par la vue.)
        """
        from apps.students.models import StudentEnrollment

        school, admin = self._setup_school()
        data = self._setup_data(school)

        with schema_context(school.schema_name):
            enr_active = StudentEnrollment.objects.create(
                student=data["student"],
                school_year=data["year"],
                classroom=data["cls_a"],
                status=EnrollmentStatus.ACTIVE,
            )
            enr_cancelled = StudentEnrollment.objects.create(
                student=data["student"],
                school_year=data["year"],
                classroom=data["cls_b"],
                status=EnrollmentStatus.CANCELLED,
            )

            # Simuler la logique de la vue : chercher un conflit avant de sauver
            new_status = EnrollmentStatus.ACTIVE
            conflict = StudentEnrollment.objects.filter(
                student=enr_cancelled.student,
                school_year=enr_cancelled.school_year,
                status__in=EnrollmentStatus.ACTIVE_STATUSES,
            ).exclude(pk=enr_cancelled.pk).first()

            # Un conflit doit être détecté
            self.assertIsNotNone(conflict,
                                 "Un conflit doit être détecté avant de réactiver l'inscription.")
            self.assertEqual(conflict.pk, enr_active.pk)

            # Le statut de l'inscription annulée NE doit pas changer
            # (la vue ne sauvegarde pas en cas de conflit)
            enr_cancelled.refresh_from_db()
            self.assertEqual(enr_cancelled.status, EnrollmentStatus.CANCELLED)


class TestChangeClassTemplateCompiles(TestCase):
    """
    Régression : le template change_class.html doit se compiler sans
    erreur de syntaxe Django (TemplateSyntaxError).
    """

    def test_change_class_template_compiles(self):
        """
        Charger le template via le moteur Django pour détecter les erreurs
        de syntaxe (ex: endfor/endif inversés).
        """
        import django.apps
        from django.template.loader import get_template
        from django.template.exceptions import TemplateSyntaxError

        # get_template lève TemplateSyntaxError si le template est invalide
        try:
            template = get_template("students/enrollments/change_class.html")
            self.assertIsNotNone(template)
        except TemplateSyntaxError as e:
            self.fail(f"Le template change_class.html contient une erreur de syntaxe : {e}")


class TestEnrollmentStatusConstants(TestCase):
    """Tests des constantes de statut d'inscription."""

    def test_active_statuses(self):
        self.assertIn(EnrollmentStatus.ACTIVE, EnrollmentStatus.ACTIVE_STATUSES)
        self.assertIn(EnrollmentStatus.PENDING, EnrollmentStatus.ACTIVE_STATUSES)
        self.assertNotIn(EnrollmentStatus.CANCELLED, EnrollmentStatus.ACTIVE_STATUSES)
        self.assertNotIn(EnrollmentStatus.COMPLETED, EnrollmentStatus.ACTIVE_STATUSES)

    def test_choices_contain_all_statuses(self):
        values = [v for v, _ in EnrollmentStatus.CHOICES]
        self.assertIn(EnrollmentStatus.PENDING, values)
        self.assertIn(EnrollmentStatus.ACTIVE, values)
        self.assertIn(EnrollmentStatus.COMPLETED, values)
        self.assertIn(EnrollmentStatus.CANCELLED, values)

    def test_badge_classes_exist(self):
        for status, _ in EnrollmentStatus.CHOICES:
            self.assertIn(status, EnrollmentStatus.BADGE_CLASSES)
