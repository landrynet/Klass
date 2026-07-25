"""Interfaces Phase 3.2 — personnel scolaire et enseignants."""
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django_tenants.utils import schema_context

from apps.core.constants import Roles, StaffStatus, StaffType
from .forms import PersonnelForm, PersonnelStatusForm
from .models import Personnel, Teacher


class SchoolStaffMixin:
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect("accounts:login")
        if request.user.role not in Roles.SCHOOL_STAFF_ROLES:
            raise PermissionDenied("Accès réservé au personnel de l'école.")
        if not getattr(request.user, "school", None):
            raise PermissionDenied("Votre compte n'est associé à aucune école.")
        return super().dispatch(request, *args, **kwargs)


class SchoolAdminMixin:
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect("accounts:login")
        if request.user.role != Roles.SCHOOL_ADMIN:
            raise PermissionDenied("Accès réservé à l'Admin École.")
        if not getattr(request.user, "school", None):
            raise PermissionDenied("Votre compte n'est associé à aucune école.")
        return super().dispatch(request, *args, **kwargs)


def _personnel_form(instance=None, initial=None):
    data = initial or {}
    if instance:
        data = {
            field: getattr(instance, field)
            for field in (
                "first_name", "last_name", "gender", "date_of_birth", "phone", "email", "address",
                "staff_type", "status", "specialization", "education_level", "diploma",
                "experience_years", "hire_date", "contract_type", "notes",
            )
        }
    return PersonnelForm(initial=data)


def _save_personnel(form, instance=None):
    data = form.cleaned_data
    personnel = instance or Personnel()
    for field, value in data.items():
        setattr(personnel, field, value)
    personnel.save()
    if personnel.staff_type == StaffType.TEACHER:
        teacher, _ = Teacher.objects.get_or_create(personnel=personnel)
        teacher.employee_id = personnel.employee_id
        teacher.specialization = personnel.specialization
        teacher.phone = personnel.phone
        teacher.contract_type = personnel.contract_type
        teacher.hire_date = personnel.hire_date
        teacher.save()
    elif hasattr(personnel, "teacher_profile"):
        personnel.teacher_profile.delete()
    return personnel


@method_decorator(login_required, name="dispatch")
class PersonnelListView(SchoolStaffMixin, View):
    template_name = "teachers/personnel_list.html"

    def get(self, request):
        school = request.user.school
        query = request.GET.get("q", "").strip()
        staff_type = request.GET.get("type", "").strip()
        status = request.GET.get("status", "").strip()
        with schema_context(school.schema_name):
            qs = Personnel.objects.all()
            if query:
                qs = qs.filter(
                    Q(first_name__icontains=query) | Q(last_name__icontains=query) |
                    Q(employee_id__icontains=query) | Q(phone__icontains=query)
                )
            if staff_type:
                qs = qs.filter(staff_type=staff_type)
            if status:
                qs = qs.filter(status=status)
            personnel = list(qs.order_by("last_name", "first_name"))
        return render(request, self.template_name, {
            "personnel": personnel, "q": query, "staff_type": staff_type, "status": status,
            "StaffType": StaffType, "StaffStatus": StaffStatus, "school": school,
        })


@method_decorator(login_required, name="dispatch")
class PersonnelCreateView(SchoolAdminMixin, View):
    template_name = "teachers/personnel_form.html"

    def get(self, request):
        return render(request, self.template_name, {
            "form": _personnel_form(initial={"staff_type": request.GET.get("type", StaffType.OTHER), "status": StaffStatus.ACTIVE}),
            "title": "Nouveau membre du personnel", "school": request.user.school,
        })

    def post(self, request):
        form = PersonnelForm(request.POST)
        if form.is_valid():
            with schema_context(request.user.school.schema_name), transaction.atomic():
                personnel = _save_personnel(form)
            messages.success(request, f"Personnel créé avec le matricule {personnel.employee_id}.")
            return redirect("teachers:personnel_detail", pk=personnel.pk)
        return render(request, self.template_name, {
            "form": form, "title": "Nouveau membre du personnel", "school": request.user.school,
        })


@method_decorator(login_required, name="dispatch")
class PersonnelDetailView(SchoolStaffMixin, View):
    def get(self, request, pk):
        school = request.user.school
        with schema_context(school.schema_name):
            personnel = get_object_or_404(Personnel.objects.select_related("user"), pk=pk)
            teacher = getattr(personnel, "teacher_profile", None)
        return render(request, "teachers/personnel_detail.html", {
            "personnel": personnel, "teacher": teacher, "school": school, "StaffStatus": StaffStatus,
        })


@method_decorator(login_required, name="dispatch")
class PersonnelEditView(SchoolAdminMixin, View):
    template_name = "teachers/personnel_form.html"

    def get(self, request, pk):
        school = request.user.school
        with schema_context(school.schema_name):
            personnel = get_object_or_404(Personnel, pk=pk)
            form = _personnel_form(personnel)
        return render(request, self.template_name, {
            "form": form, "title": "Modifier le personnel", "personnel": personnel, "school": school,
        })

    def post(self, request, pk):
        school = request.user.school
        with schema_context(school.schema_name):
            personnel = get_object_or_404(Personnel, pk=pk)
            form = PersonnelForm(request.POST)
            if form.is_valid():
                personnel = _save_personnel(form, personnel)
                messages.success(request, "Membre du personnel mis à jour.")
                return redirect("teachers:personnel_detail", pk=personnel.pk)
        return render(request, self.template_name, {
            "form": form, "title": "Modifier le personnel", "personnel": personnel, "school": school,
        })


@method_decorator(login_required, name="dispatch")
class PersonnelStatusView(SchoolAdminMixin, View):
    def post(self, request, pk):
        school = request.user.school
        with schema_context(school.schema_name):
            personnel = get_object_or_404(Personnel, pk=pk)
            form = PersonnelStatusForm(request.POST)
            if form.is_valid():
                personnel.status = form.cleaned_data["status"]
                personnel.save(update_fields=["status", "updated_at"])
                messages.success(request, f"Statut mis à jour : {personnel.get_status_display()}.")
            else:
                messages.error(request, "Statut invalide.")
        return redirect("teachers:personnel_detail", pk=pk)


@method_decorator(login_required, name="dispatch")
class TeacherListView(SchoolStaffMixin, View):
    def get(self, request):
        school = request.user.school
        query = request.GET.get("q", "").strip()
        status = request.GET.get("status", "").strip()
        specialization = request.GET.get("specialization", "").strip()
        with schema_context(school.schema_name):
            qs = Personnel.objects.filter(staff_type=StaffType.TEACHER)
            if query:
                qs = qs.filter(
                    Q(first_name__icontains=query) | Q(last_name__icontains=query) |
                    Q(employee_id__icontains=query) | Q(specialization__icontains=query)
                )
            if status:
                qs = qs.filter(status=status)
            if specialization:
                qs = qs.filter(specialization__icontains=specialization)
            teachers = list(qs.order_by("last_name", "first_name"))
        return render(request, "teachers/list.html", {
            "teachers": teachers, "q": query, "status": status, "specialization": specialization,
            "StaffStatus": StaffStatus, "school": school,
        })


@method_decorator(login_required, name="dispatch")
class TeacherDetailView(SchoolStaffMixin, View):
    def get(self, request, pk):
        school = request.user.school
        with schema_context(school.schema_name):
            personnel = get_object_or_404(Personnel, pk=pk, staff_type=StaffType.TEACHER)
            teacher = getattr(personnel, "teacher_profile", None)
        return render(request, "teachers/detail.html", {
            "personnel": personnel, "teacher": teacher, "school": school, "StaffStatus": StaffStatus,
        })


@method_decorator(login_required, name="dispatch")
class TeacherCreateView(PersonnelCreateView):
    def get(self, request):
        return render(request, self.template_name, {
            "form": _personnel_form(initial={"staff_type": StaffType.TEACHER, "status": StaffStatus.ACTIVE}),
            "title": "Nouvel enseignant", "teacher_form": True, "school": request.user.school,
        })

    def post(self, request):
        form = PersonnelForm(request.POST)
        if form.is_valid():
            if form.cleaned_data["staff_type"] != StaffType.TEACHER:
                form.add_error("staff_type", "Le profil doit être de type Enseignant.")
            else:
                with schema_context(request.user.school.schema_name), transaction.atomic():
                    personnel = _save_personnel(form)
                messages.success(request, f"Enseignant créé avec le matricule {personnel.employee_id}.")
                return redirect("teachers:teacher_detail", pk=personnel.pk)
        return render(request, self.template_name, {
            "form": form, "title": "Nouvel enseignant", "teacher_form": True, "school": request.user.school,
        })