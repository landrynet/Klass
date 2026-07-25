"""Tests Phase 3.2 — personnel, enseignants, matricules et permissions."""
import datetime

import pytest
from django.core.exceptions import ValidationError
from django.test import TestCase
from django_tenants.utils import schema_context

from apps.core.constants import StaffStatus, StaffType


class Phase32DataMixin:
    def setup_school(self, suffix):
        from apps.tenants.services import create_school_with_tenant

        return create_school_with_tenant(
            name=f"École Test Phase 3.2 {suffix}",
            email=f"phase32-{suffix}@test.app",
            phone="+243000000032",
            address="Test",
            city="Lubumbashi",
            country="Congo (RDC)",
            admin_first_name="Admin",
            admin_last_name=suffix,
            admin_email=f"admin-phase32-{suffix}@test.app",
        )


class TestPersonnelModel(Phase32DataMixin, TestCase):
    def test_staff_matricule_is_generated_and_stable(self):
        from apps.teachers.models import Personnel

        school, _, _ = self.setup_school("matricule")
        with schema_context(school.schema_name):
            person = Personnel.objects.create(
                first_name="Aline",
                last_name="Test",
                staff_type=StaffType.TEACHER,
            )
            first_id = person.employee_id
            self.assertTrue(first_id.startswith("ENS-"))
            person.phone = "+243000000032"
            person.save()
            person.refresh_from_db()
            self.assertEqual(person.employee_id, first_id)

    def test_staff_types_and_statuses_are_supported(self):
        from apps.teachers.models import Personnel

        school, _, _ = self.setup_school("statuses")
        with schema_context(school.schema_name):
            person = Personnel.objects.create(
                first_name="David",
                last_name="Test",
                staff_type=StaffType.TECHNICAL,
                status=StaffStatus.ARCHIVED,
            )
            self.assertTrue(person.is_archived)
            self.assertEqual(person.get_staff_type_display(), "Personnel technique")

    def test_teacher_profile_does_not_require_login_account(self):
        from apps.teachers.models import Personnel, Teacher

        school, _, _ = self.setup_school("profile")
        with schema_context(school.schema_name):
            person = Personnel.objects.create(
                first_name="Samuel",
                last_name="Test",
                staff_type=StaffType.TEACHER,
                specialization="Français",
            )
            teacher = Teacher.objects.create(personnel=person)
            self.assertIsNone(teacher.user)
            self.assertEqual(teacher.full_name, person.full_name)
            self.assertEqual(teacher.email, "")

    def test_employee_ids_are_unique_within_tenant(self):
        from apps.teachers.models import Personnel

        school, _, _ = self.setup_school("unique")
        with schema_context(school.schema_name):
            first = Personnel.objects.create(first_name="A", last_name="Test", staff_type=StaffType.OTHER)
            second = Personnel.objects.create(first_name="B", last_name="Test", staff_type=StaffType.OTHER)
            self.assertNotEqual(first.employee_id, second.employee_id)


class TestPersonnelViews(Phase32DataMixin, TestCase):
    def test_direct_detail_is_limited_to_current_tenant_schema(self):
        from apps.teachers.models import Personnel
        from django.http import Http404
        from django.test import RequestFactory
        from apps.teachers.views import PersonnelDetailView

        school, admin, _ = self.setup_school("scope")
        with schema_context(school.schema_name):
            person = Personnel.objects.create(first_name="A", last_name="OnlyA")
        request = RequestFactory().get(f"/teachers/personnel/{person.pk}/")
        request.user = admin
        with self.assertRaises(Http404):
            PersonnelDetailView().get(request, person.pk + 999999)