"""Interfaces Phase 3.0: élèves, parents et configuration des matricules."""
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.decorators import method_decorator
from django.views import View
from django.contrib.auth.decorators import login_required
from django_tenants.utils import schema_context

from apps.core.constants import Roles
from .forms import MatriculeConfigurationForm, ParentForm, StudentForm, potential_parent_duplicates
from .models import MatriculeConfiguration, Parent, ParentStudent, Student


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


def cached_queryset(queryset):
    """Évalue un queryset dans schema_context et le conserve pour le template."""
    list(queryset)
    return queryset


def parent_queryset(school, query=""):
    with schema_context(school.schema_name):
        qs = Parent.objects.all()
        if query:
            qs = qs.filter(
                Q(first_name__icontains=query) |
                Q(last_name__icontains=query) |
                Q(phone__icontains=query) |
                Q(email__icontains=query)
            )
        return cached_queryset(qs.order_by("last_name", "first_name"))


@method_decorator(login_required, name="dispatch")
class StudentListView(SchoolStaffMixin, View):
    template_name = "students/list.html"

    def get(self, request):
        school = request.user.school
        with schema_context(school.schema_name):
            qs = Student.objects.select_related("primary_parent")
            query = request.GET.get("q", "").strip()
            status = request.GET.get("status", "")
            if query:
                qs = qs.filter(
                    Q(matricule__icontains=query) |
                    Q(first_name__icontains=query) |
                    Q(last_name__icontains=query)
                )
            if status:
                qs = qs.filter(status=status)
            students = list(qs.order_by("last_name", "first_name"))
        return render(request, self.template_name, {"students": students, "q": query, "status": status, "school": school})


@method_decorator(login_required, name="dispatch")
class StudentCreateView(SchoolAdminMixin, View):
    template_name = "students/form.html"

    def get(self, request):
        school = request.user.school
        parents = parent_queryset(school, request.GET.get("parent_q", "").strip())
        form = StudentForm(parent_queryset=parents, initial={"status": "active"})
        return render(request, self.template_name, {"form": form, "title": "Nouvel élève", "parent_q": request.GET.get("parent_q", ""), "school": school})

    def post(self, request):
        school = request.user.school
        parents = parent_queryset(school, request.POST.get("parent_q", "").strip())
        form = StudentForm(request.POST, parent_queryset=parents)
        if form.is_valid():
            data = form.cleaned_data
            with schema_context(school.schema_name), transaction.atomic():
                student = Student.objects.create(**data)
                ParentStudent.objects.get_or_create(parent=data["primary_parent"], student=student)
            messages.success(request, f"Élève créé avec le matricule {student.matricule}.")
            return redirect("students:detail", pk=student.pk)
        return render(request, self.template_name, {"form": form, "title": "Nouvel élève", "parent_q": request.POST.get("parent_q", ""), "school": school})


@method_decorator(login_required, name="dispatch")
class StudentDetailView(SchoolStaffMixin, View):
    def get(self, request, pk):
        school = request.user.school
        with schema_context(school.schema_name):
            student = get_object_or_404(Student.objects.select_related("primary_parent"), pk=pk)
            links = list(student.parent_links.select_related("parent").all())
        return render(request, "students/detail.html", {"student": student, "parent_links": links, "school": school})


@method_decorator(login_required, name="dispatch")
class StudentEditView(SchoolAdminMixin, View):
    template_name = "students/form.html"

    def get(self, request, pk):
        school = request.user.school
        with schema_context(school.schema_name):
            student = get_object_or_404(Student, pk=pk)
            parents = parent_queryset(school)
            form = StudentForm(parent_queryset=parents, initial={
                "first_name": student.first_name, "last_name": student.last_name,
                "date_of_birth": student.date_of_birth, "gender": student.gender,
                "primary_parent": student.primary_parent, "status": student.status,
            })
        return render(request, self.template_name, {"form": form, "title": "Modifier l'élève", "student": student, "school": school})

    def post(self, request, pk):
        school = request.user.school
        with schema_context(school.schema_name):
            student = get_object_or_404(Student, pk=pk)
            parents = parent_queryset(school)
            form = StudentForm(request.POST, parent_queryset=parents)
            if form.is_valid():
                data = form.cleaned_data
                for field, value in data.items():
                    setattr(student, field, value)
                student.save(update_fields=["first_name", "last_name", "date_of_birth", "gender", "primary_parent", "status", "updated_at"])
                ParentStudent.objects.get_or_create(parent=data["primary_parent"], student=student)
                messages.success(request, "Élève mis à jour.")
                return redirect("students:detail", pk=student.pk)
        return render(request, self.template_name, {"form": form, "title": "Modifier l'élève", "student": student, "school": school})


@method_decorator(login_required, name="dispatch")
class ParentListView(SchoolStaffMixin, View):
    def get(self, request):
        school = request.user.school
        with schema_context(school.schema_name):
            query = request.GET.get("q", "").strip()
            qs = Parent.objects.annotate(student_count=Count("students"))
            if query:
                qs = qs.filter(Q(first_name__icontains=query) | Q(last_name__icontains=query) | Q(phone__icontains=query) | Q(email__icontains=query))
            parents = list(qs.order_by("last_name", "first_name"))
        return render(request, "students/parents_list.html", {"parents": parents, "q": query, "school": school})


@method_decorator(login_required, name="dispatch")
class ParentCreateView(SchoolAdminMixin, View):
    template_name = "students/parent_form.html"

    def get(self, request):
        return render(request, self.template_name, {"form": ParentForm(), "title": "Nouveau parent / tuteur", "school": request.user.school})

    def post(self, request):
        school = request.user.school
        form = ParentForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            with schema_context(school.schema_name):
                duplicates = list(potential_parent_duplicates(data))
                if duplicates and request.POST.get("confirm_duplicate") != "1":
                    return render(request, self.template_name, {"form": form, "duplicates": duplicates, "title": "Nouveau parent / tuteur", "school": school})
                parent = Parent.objects.create(**data)
            messages.success(request, "Parent / tuteur créé.")
            return redirect("students:parent_detail", pk=parent.pk)
        return render(request, self.template_name, {"form": form, "title": "Nouveau parent / tuteur", "school": school})


@method_decorator(login_required, name="dispatch")
class ParentDetailView(SchoolStaffMixin, View):
    def get(self, request, pk):
        school = request.user.school
        with schema_context(school.schema_name):
            parent = get_object_or_404(Parent, pk=pk)
            students = list(parent.students.all().order_by("last_name", "first_name"))
        return render(request, "students/parent_detail.html", {"parent": parent, "students": students, "school": school})


@method_decorator(login_required, name="dispatch")
class ParentEditView(SchoolAdminMixin, View):
    template_name = "students/parent_form.html"

    def get(self, request, pk):
        school = request.user.school
        with schema_context(school.schema_name):
            parent = get_object_or_404(Parent, pk=pk)
            form = ParentForm(initial={field: getattr(parent, field) for field in ("first_name", "last_name", "gender", "phone", "phone_secondary", "email", "address", "profession")})
        return render(request, self.template_name, {"form": form, "title": "Modifier le parent / tuteur", "parent": parent, "school": school})

    def post(self, request, pk):
        school = request.user.school
        with schema_context(school.schema_name):
            parent = get_object_or_404(Parent, pk=pk)
            form = ParentForm(request.POST)
            if form.is_valid():
                data = form.cleaned_data
                duplicates = list(potential_parent_duplicates(data, exclude_pk=pk))
                if duplicates and request.POST.get("confirm_duplicate") != "1":
                    return render(request, self.template_name, {"form": form, "duplicates": duplicates, "title": "Modifier le parent / tuteur", "parent": parent, "school": school})
                for field, value in data.items():
                    setattr(parent, field, value)
                parent.save()
                messages.success(request, "Parent / tuteur mis à jour.")
                return redirect("students:parent_detail", pk=parent.pk)
        return render(request, self.template_name, {"form": form, "title": "Modifier le parent / tuteur", "parent": parent, "school": school})


@method_decorator(login_required, name="dispatch")
class MatriculeConfigurationView(SchoolAdminMixin, View):
    template_name = "students/matricule_config.html"

    def get(self, request):
        school = request.user.school
        with schema_context(school.schema_name):
            config, _ = MatriculeConfiguration.objects.get_or_create(pk=1)
            form = MatriculeConfigurationForm(initial={field: getattr(config, field) for field in ("prefix", "include_year", "separator", "number_digits", "next_number")})
            preview = config.preview()
        return render(request, self.template_name, {"form": form, "preview": preview, "school": school})

    def post(self, request):
        school = request.user.school
        with schema_context(school.schema_name):
            config, _ = MatriculeConfiguration.objects.get_or_create(pk=1)
            form = MatriculeConfigurationForm(request.POST)
            if form.is_valid():
                for field, value in form.cleaned_data.items():
                    setattr(config, field, value)
                config.save()
                messages.success(request, "Configuration des matricules enregistrée.")
                return redirect("students:matricule_config")
            preview = config.preview()
        return render(request, self.template_name, {"form": form, "preview": preview, "school": school})