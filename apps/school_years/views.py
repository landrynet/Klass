"""
Vues pour la gestion des années scolaires — Phase 2.0.

Accès réservé au School Admin.
Toutes les requêtes tenant sont isolées via schema_context.
"""
import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.decorators import method_decorator
from django.views import View
from django_tenants.utils import schema_context

from apps.core.constants import Roles
from .forms import SchoolYearForm, SchoolYearEditForm
from . import services

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Mixin commun
# ---------------------------------------------------------------------------

class SchoolAdminRequiredMixin:
    """Vérifie que l'utilisateur est un Admin École avec une école associée."""

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect("accounts:login")
        if request.user.role not in [Roles.SCHOOL_ADMIN]:
            raise PermissionDenied("Accès réservé à l'Admin École.")
        if not getattr(request.user, "school", None):
            messages.error(request, "Votre compte n'est associé à aucune école.")
            return redirect("accounts:logout")
        return super().dispatch(request, *args, **kwargs)


class SchoolStaffRequiredMixin:
    """Autorise tout le personnel de l'école (lecture seule dans certains modules)."""

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect("accounts:login")
        if request.user.role not in Roles.SCHOOL_STAFF_ROLES:
            raise PermissionDenied("Accès réservé au personnel de l'école.")
        if not getattr(request.user, "school", None):
            messages.error(request, "Votre compte n'est associé à aucune école.")
            return redirect("accounts:logout")
        return super().dispatch(request, *args, **kwargs)


# ---------------------------------------------------------------------------
# Années scolaires — CRUD
# ---------------------------------------------------------------------------

@method_decorator(login_required, name="dispatch")
class SchoolYearListView(SchoolStaffRequiredMixin, View):
    """Liste toutes les années scolaires de l'école."""
    template_name = "school_years/list.html"

    def get(self, request):
        school = request.user.school
        from .models import SchoolYear
        with schema_context(school.schema_name):
            years = list(SchoolYear.objects.all().order_by("-start_date"))
        return render(request, self.template_name, {
            "years": years,
            "school": school,
        })


@method_decorator(login_required, name="dispatch")
class SchoolYearCreateView(SchoolAdminRequiredMixin, View):
    """Création d'une nouvelle année scolaire."""
    template_name = "school_years/create.html"

    def get(self, request):
        form = SchoolYearForm()
        return render(request, self.template_name, {"form": form})

    def post(self, request):
        school = request.user.school
        form = SchoolYearForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            try:
                year = services.create_school_year(
                    school=school,
                    name=data["name"],
                    start_date=data["start_date"],
                    end_date=data["end_date"],
                    activate=data.get("activate", False),
                    created_by=request.user,
                )
                messages.success(
                    request,
                    f"Année scolaire « {year.name} » créée avec succès."
                )
                return redirect("school_years:list")
            except ValueError as exc:
                messages.error(request, str(exc))

        return render(request, self.template_name, {"form": form})


@method_decorator(login_required, name="dispatch")
class SchoolYearEditView(SchoolAdminRequiredMixin, View):
    """Modification d'une année scolaire non clôturée."""
    template_name = "school_years/edit.html"

    def _get_year(self, school, pk):
        from .models import SchoolYear
        with schema_context(school.schema_name):
            return get_object_or_404(SchoolYear, pk=pk)

    def get(self, request, pk):
        school = request.user.school
        year = self._get_year(school, pk)
        if not year.is_editable:
            messages.error(request, "Cette année scolaire ne peut plus être modifiée.")
            return redirect("school_years:list")
        form = SchoolYearEditForm(initial={
            "name": year.name,
            "start_date": year.start_date,
            "end_date": year.end_date,
        })
        return render(request, self.template_name, {"form": form, "year": year})

    def post(self, request, pk):
        school = request.user.school
        year = self._get_year(school, pk)
        if not year.is_editable:
            messages.error(request, "Cette année scolaire ne peut plus être modifiée.")
            return redirect("school_years:list")
        form = SchoolYearEditForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            try:
                year = services.update_school_year(
                    school=school,
                    year_pk=pk,
                    name=data["name"],
                    start_date=data["start_date"],
                    end_date=data["end_date"],
                )
                messages.success(
                    request,
                    f"Année scolaire « {year.name} » mise à jour."
                )
                return redirect("school_years:list")
            except ValueError as exc:
                messages.error(request, str(exc))

        return render(request, self.template_name, {"form": form, "year": year})


# ---------------------------------------------------------------------------
# Actions d'état (POST uniquement)
# ---------------------------------------------------------------------------

@method_decorator(login_required, name="dispatch")
class SchoolYearActivateView(SchoolAdminRequiredMixin, View):
    """Active une année scolaire planifiée."""

    def post(self, request, pk):
        school = request.user.school
        try:
            year = services.activate_school_year(
                school=school,
                year_pk=pk,
                activated_by=request.user,
            )
            messages.success(
                request,
                f"Année scolaire « {year.name} » activée avec succès."
            )
        except ValueError as exc:
            messages.error(request, str(exc))
        return redirect("school_years:list")


@method_decorator(login_required, name="dispatch")
class SchoolYearEndView(SchoolAdminRequiredMixin, View):
    """Clôture l'année scolaire active."""

    def post(self, request, pk):
        school = request.user.school
        try:
            year = services.end_school_year(
                school=school,
                year_pk=pk,
                closed_by=request.user,
            )
            messages.success(
                request,
                f"Année scolaire « {year.name} » clôturée."
            )
        except ValueError as exc:
            messages.error(request, str(exc))
        return redirect("school_years:list")


@method_decorator(login_required, name="dispatch")
class SchoolYearArchiveView(SchoolAdminRequiredMixin, View):
    """Archive définitivement une année scolaire terminée."""

    def post(self, request, pk):
        school = request.user.school
        try:
            year = services.archive_school_year(
                school=school,
                year_pk=pk,
            )
            messages.success(
                request,
                f"Année scolaire « {year.name} » archivée."
            )
        except ValueError as exc:
            messages.error(request, str(exc))
        return redirect("school_years:list")
