"""
Vues pour le module Académique de KLASS — Phase 2.0.

Dashboard + Niveaux + Options / Filières.
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
from .forms import LevelForm, OptionForm

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Mixins de permission
# ---------------------------------------------------------------------------

class SchoolAdminRequiredMixin:
    """Vérifie que l'utilisateur est un Admin École avec une école associée."""

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect("accounts:login")
        if request.user.role != Roles.SCHOOL_ADMIN:
            raise PermissionDenied("Accès réservé à l'Admin École.")
        if not getattr(request.user, "school", None):
            messages.error(request, "Votre compte n'est associé à aucune école.")
            return redirect("accounts:logout")
        return super().dispatch(request, *args, **kwargs)


class SchoolStaffRequiredMixin:
    """Autorise tout le personnel de l'école."""

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
# Dashboard principal
# ---------------------------------------------------------------------------

@method_decorator(login_required, name="dispatch")
class DashboardView(View):
    """
    Tableau de bord de l'école pour le personnel.
    """
    template_name = "academics/dashboard.html"

    def get(self, request):
        school = getattr(request.user, "school", None) or getattr(request, "current_school", None)
        active_year = None

        if school and school.schema_name:
            try:
                from apps.school_years.models import SchoolYear
                with schema_context(school.schema_name):
                    active_year = SchoolYear.get_active()
            except Exception as exc:
                logger.warning("Impossible de récupérer l'année active : %s", exc)

        return render(request, self.template_name, {
            "school": school,
            "active_year": active_year,
        })


# ---------------------------------------------------------------------------
# Niveaux scolaires — CRUD
# ---------------------------------------------------------------------------

@method_decorator(login_required, name="dispatch")
class LevelListView(SchoolStaffRequiredMixin, View):
    """Liste les niveaux scolaires, filtrés par année."""
    template_name = "academics/levels/list.html"

    def get(self, request):
        school = request.user.school
        from apps.school_years.models import SchoolYear
        from .models import Level

        with schema_context(school.schema_name):
            years = list(SchoolYear.objects.filter(is_archived=False).order_by("-start_date"))
            active_year = SchoolYear.get_active()

            # Sélection de l'année depuis l'URL
            year_id = request.GET.get("year_id")
            selected_year = None
            if year_id:
                selected_year = next((y for y in years if str(y.pk) == year_id), None)
            if selected_year is None:
                selected_year = active_year

            if selected_year:
                levels = list(Level.objects.filter(school_year=selected_year).order_by("order", "name"))
            else:
                levels = []

        return render(request, self.template_name, {
            "levels": levels,
            "years": years,
            "selected_year": selected_year,
            "active_year": active_year,
            "school": school,
        })


@method_decorator(login_required, name="dispatch")
class LevelCreateView(SchoolAdminRequiredMixin, View):
    """Création d'un nouveau niveau scolaire."""
    template_name = "academics/levels/create.html"

    def _get_year_queryset(self, school):
        from apps.school_years.models import SchoolYear
        with schema_context(school.schema_name):
            return list(SchoolYear.objects.filter(is_archived=False).order_by("-start_date"))

    def get(self, request):
        school = request.user.school
        from apps.school_years.models import SchoolYear
        with schema_context(school.schema_name):
            year_qs = SchoolYear.objects.filter(is_archived=False).order_by("-start_date")
            active_year = SchoolYear.get_active()
            form = LevelForm(
                school_year_queryset=year_qs,
                initial={"school_year": active_year, "is_active": True, "order": 0},
            )
        return render(request, self.template_name, {"form": form})

    def post(self, request):
        school = request.user.school
        from apps.school_years.models import SchoolYear
        from .models import Level

        with schema_context(school.schema_name):
            year_qs = SchoolYear.objects.filter(is_archived=False).order_by("-start_date")
            form = LevelForm(request.POST, school_year_queryset=year_qs)
            if form.is_valid():
                data = form.cleaned_data
                # Vérifier l'unicité (school_year, name)
                if Level.objects.filter(school_year=data["school_year"], name=data["name"]).exists():
                    form.add_error("name", f"Un niveau « {data['name']} » existe déjà pour cette année scolaire.")
                else:
                    level = Level.objects.create(
                        school_year=data["school_year"],
                        name=data["name"],
                        code=data.get("code", ""),
                        order=data.get("order", 0),
                        is_active=data.get("is_active", True),
                    )
                    messages.success(request, f"Niveau « {level.name} » créé avec succès.")
                    return redirect("academics:levels")

        return render(request, self.template_name, {"form": form})


@method_decorator(login_required, name="dispatch")
class LevelEditView(SchoolAdminRequiredMixin, View):
    """Modification d'un niveau scolaire."""
    template_name = "academics/levels/edit.html"

    def _get_level(self, school, pk):
        from .models import Level
        with schema_context(school.schema_name):
            return get_object_or_404(Level, pk=pk)

    def get(self, request, pk):
        school = request.user.school
        from apps.school_years.models import SchoolYear
        from .models import Level

        with schema_context(school.schema_name):
            level = get_object_or_404(Level, pk=pk)
            year_qs = SchoolYear.objects.filter(is_archived=False).order_by("-start_date")
            form = LevelForm(
                school_year_queryset=year_qs,
                initial={
                    "school_year": level.school_year,
                    "name": level.name,
                    "code": level.code,
                    "order": level.order,
                    "is_active": level.is_active,
                },
            )
        return render(request, self.template_name, {"form": form, "level": level})

    def post(self, request, pk):
        school = request.user.school
        from apps.school_years.models import SchoolYear
        from .models import Level

        with schema_context(school.schema_name):
            level = get_object_or_404(Level, pk=pk)
            year_qs = SchoolYear.objects.filter(is_archived=False).order_by("-start_date")
            form = LevelForm(request.POST, school_year_queryset=year_qs)
            if form.is_valid():
                data = form.cleaned_data
                # Unicité : même année, même nom, hors soi-même
                if Level.objects.filter(
                    school_year=data["school_year"], name=data["name"]
                ).exclude(pk=pk).exists():
                    form.add_error("name", f"Un niveau « {data['name']} » existe déjà pour cette année scolaire.")
                else:
                    level.school_year = data["school_year"]
                    level.name = data["name"]
                    level.code = data.get("code", "")
                    level.order = data.get("order", 0)
                    level.is_active = data.get("is_active", True)
                    level.save()
                    messages.success(request, f"Niveau « {level.name} » mis à jour.")
                    return redirect("academics:levels")

        return render(request, self.template_name, {"form": form, "level": level})


@method_decorator(login_required, name="dispatch")
class LevelToggleView(SchoolAdminRequiredMixin, View):
    """Active ou désactive un niveau (POST uniquement)."""

    def post(self, request, pk):
        school = request.user.school
        from .models import Level

        with schema_context(school.schema_name):
            level = get_object_or_404(Level, pk=pk)
            level.is_active = not level.is_active
            level.save(update_fields=["is_active", "updated_at"])
            action = "activé" if level.is_active else "désactivé"
            messages.success(request, f"Niveau « {level.name} » {action}.")

        return redirect("academics:levels")


# ---------------------------------------------------------------------------
# Options / Filières — CRUD
# ---------------------------------------------------------------------------

@method_decorator(login_required, name="dispatch")
class OptionListView(SchoolStaffRequiredMixin, View):
    """Liste les options / filières, filtrées par niveau."""
    template_name = "academics/options/list.html"

    def get(self, request):
        school = request.user.school
        from apps.school_years.models import SchoolYear
        from .models import Level, Option

        with schema_context(school.schema_name):
            active_year = SchoolYear.get_active()
            years = list(SchoolYear.objects.filter(is_archived=False).order_by("-start_date"))

            # Sélection de l'année
            year_id = request.GET.get("year_id")
            selected_year = None
            if year_id:
                selected_year = next((y for y in years if str(y.pk) == year_id), None)
            if selected_year is None:
                selected_year = active_year

            if selected_year:
                levels = list(Level.objects.filter(school_year=selected_year).order_by("order", "name"))
            else:
                levels = []

            # Sélection du niveau
            level_id = request.GET.get("level_id")
            selected_level = None
            if level_id:
                selected_level = next((l for l in levels if str(l.pk) == level_id), None)
            if selected_level is None and levels:
                selected_level = levels[0]

            if selected_level:
                options = list(Option.objects.filter(level=selected_level).order_by("name"))
            else:
                options = []

        return render(request, self.template_name, {
            "options": options,
            "levels": levels,
            "years": years,
            "selected_year": selected_year,
            "selected_level": selected_level,
            "active_year": active_year,
            "school": school,
        })


@method_decorator(login_required, name="dispatch")
class OptionCreateView(SchoolAdminRequiredMixin, View):
    """Création d'une option / filière."""
    template_name = "academics/options/create.html"

    def get(self, request):
        school = request.user.school
        from apps.school_years.models import SchoolYear
        from .models import Level

        with schema_context(school.schema_name):
            active_year = SchoolYear.get_active()
            if active_year:
                level_qs = Level.objects.filter(school_year=active_year, is_active=True).order_by("order", "name")
            else:
                level_qs = Level.objects.none()
            # Pré-sélection du niveau depuis l'URL
            preselected_level_id = request.GET.get("level_id")
            form = OptionForm(level_queryset=level_qs, initial={"is_active": True})
            if preselected_level_id:
                try:
                    pre_level = Level.objects.get(pk=preselected_level_id, is_active=True)
                    form.initial["level"] = pre_level
                except Level.DoesNotExist:
                    pass
            years = list(SchoolYear.objects.filter(is_archived=False).order_by("-start_date"))
            levels = list(Level.objects.filter(school_year=active_year).order_by("order", "name") if active_year else Level.objects.none())

        return render(request, self.template_name, {
            "form": form,
            "years": years,
            "levels": levels,
            "selected_year": active_year,
        })

    def post(self, request):
        school = request.user.school
        from apps.school_years.models import SchoolYear
        from .models import Level, Option

        with schema_context(school.schema_name):
            active_year = SchoolYear.get_active()
            # Construire le queryset de niveaux basé sur l'année de l'onglet actuel
            year_id = request.POST.get("year_id") or (active_year.pk if active_year else None)
            if year_id:
                try:
                    sel_year = SchoolYear.objects.get(pk=year_id)
                    level_qs = Level.objects.filter(school_year=sel_year, is_active=True).order_by("order", "name")
                except SchoolYear.DoesNotExist:
                    level_qs = Level.objects.none()
                    sel_year = active_year
            else:
                level_qs = Level.objects.none()
                sel_year = None

            form = OptionForm(request.POST, level_queryset=level_qs)
            if form.is_valid():
                data = form.cleaned_data
                # Vérifier l'unicité (level, name)
                if Option.objects.filter(level=data["level"], name=data["name"]).exists():
                    form.add_error("name", f"Une option « {data['name']} » existe déjà pour ce niveau.")
                else:
                    option = Option.objects.create(
                        level=data["level"],
                        name=data["name"],
                        code=data.get("code", ""),
                        description=data.get("description", ""),
                        is_active=data.get("is_active", True),
                    )
                    messages.success(request, f"Option « {option.name} » créée avec succès.")
                    return redirect("academics:options")

            years = list(SchoolYear.objects.filter(is_archived=False).order_by("-start_date"))
            levels = list(level_qs)

        return render(request, self.template_name, {
            "form": form,
            "years": years,
            "levels": levels,
            "selected_year": sel_year if 'sel_year' in locals() else active_year,
        })


@method_decorator(login_required, name="dispatch")
class OptionEditView(SchoolAdminRequiredMixin, View):
    """Modification d'une option / filière."""
    template_name = "academics/options/edit.html"

    def get(self, request, pk):
        school = request.user.school
        from apps.school_years.models import SchoolYear
        from .models import Level, Option

        with schema_context(school.schema_name):
            option = get_object_or_404(Option, pk=pk)
            level_qs = Level.objects.filter(
                school_year=option.level.school_year, is_active=True
            ).order_by("order", "name")
            form = OptionForm(
                level_queryset=level_qs,
                initial={
                    "level": option.level,
                    "name": option.name,
                    "code": option.code,
                    "description": option.description,
                    "is_active": option.is_active,
                },
            )

        return render(request, self.template_name, {"form": form, "option": option})

    def post(self, request, pk):
        school = request.user.school
        from .models import Level, Option

        with schema_context(school.schema_name):
            option = get_object_or_404(Option, pk=pk)
            level_qs = Level.objects.filter(
                school_year=option.level.school_year, is_active=True
            ).order_by("order", "name")
            form = OptionForm(request.POST, level_queryset=level_qs)
            if form.is_valid():
                data = form.cleaned_data
                # Unicité (level, name) hors soi-même
                if Option.objects.filter(level=data["level"], name=data["name"]).exclude(pk=pk).exists():
                    form.add_error("name", f"Une option « {data['name']} » existe déjà pour ce niveau.")
                else:
                    option.level = data["level"]
                    option.name = data["name"]
                    option.code = data.get("code", "")
                    option.description = data.get("description", "")
                    option.is_active = data.get("is_active", True)
                    option.save()
                    messages.success(request, f"Option « {option.name} » mise à jour.")
                    return redirect("academics:options")

        return render(request, self.template_name, {"form": form, "option": option})


@method_decorator(login_required, name="dispatch")
class OptionToggleView(SchoolAdminRequiredMixin, View):
    """Active ou désactive une option (POST uniquement)."""

    def post(self, request, pk):
        school = request.user.school
        from .models import Option

        with schema_context(school.schema_name):
            option = get_object_or_404(Option, pk=pk)
            option.is_active = not option.is_active
            option.save(update_fields=["is_active", "updated_at"])
            action = "activée" if option.is_active else "désactivée"
            messages.success(request, f"Option « {option.name} » {action}.")

        return redirect("academics:options")
