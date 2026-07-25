"""
Vues pour le module Académique de KLASS — Phase 2.0 & 2.1.

Dashboard + Niveaux + Options / Filières + Classes + Salles.
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
from .forms import LevelForm, OptionForm, ClassroomForm, RoomForm

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
        dashboard = {
            "student_count": 0,
            "enrollment_count": 0,
            "classroom_count": 0,
            "staff_count": 0,
            "recent_students": [],
            "recent_enrollments": [],
        }

        if school and school.schema_name:
            try:
                from apps.school_years.models import SchoolYear
                from apps.students.models import Student, StudentEnrollment
                from apps.teachers.models import Personnel
                from apps.academics.models import Classroom
                from apps.core.constants import EnrollmentStatus, StaffStatus

                with schema_context(school.schema_name):
                    active_year = SchoolYear.get_active()
                    active_students = Student.objects.filter(status="active")
                    dashboard["student_count"] = active_students.count()
                    dashboard["recent_students"] = list(
                        active_students.order_by("-created_at")[:5]
                    )
                    if active_year:
                        active_enrollments = StudentEnrollment.objects.filter(
                            school_year=active_year,
                            status__in=EnrollmentStatus.ACTIVE_STATUSES,
                        )
                        dashboard["enrollment_count"] = active_enrollments.count()
                        dashboard["recent_enrollments"] = list(
                            active_enrollments.select_related("student", "classroom")
                            .order_by("-created_at")[:5]
                        )
                        dashboard["classroom_count"] = Classroom.objects.filter(
                            school_year=active_year,
                            is_active=True,
                            is_archived=False,
                        ).count()
                    dashboard["staff_count"] = Personnel.objects.filter(
                        status=StaffStatus.ACTIVE
                    ).count()
            except Exception as exc:
                logger.warning("Impossible de récupérer l'année active : %s", exc)

        return render(request, self.template_name, {
            "school": school,
            "active_year": active_year,
            "dashboard": dashboard,
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


# ---------------------------------------------------------------------------
# Salles — CRUD (Phase 2.1)
# ---------------------------------------------------------------------------

@method_decorator(login_required, name="dispatch")
class RoomListView(SchoolStaffRequiredMixin, View):
    """Liste les salles de l'école, avec filtres par type et statut."""
    template_name = "academics/rooms/list.html"

    def get(self, request):
        school = request.user.school
        from .models import Room

        with schema_context(school.schema_name):
            qs = Room.objects.all()

            # Filtre par type
            type_filter = request.GET.get("type", "")
            if type_filter:
                qs = qs.filter(room_type=type_filter)

            # Filtre par statut
            status_filter = request.GET.get("status", "active")
            if status_filter == "archived":
                qs = qs.filter(is_archived=True)
            elif status_filter == "unavailable":
                qs = qs.filter(is_archived=False, is_available=False)
            else:
                qs = qs.filter(is_archived=False, is_available=True)

            # Recherche par nom / code
            q = request.GET.get("q", "").strip()
            if q:
                qs = qs.filter(name__icontains=q) | Room.objects.filter(code__icontains=q, is_archived=False)

            rooms = list(qs.order_by("name"))
            total_count = Room.objects.filter(is_archived=False).count()

        return render(request, self.template_name, {
            "rooms": rooms,
            "total_count": total_count,
            "type_filter": type_filter,
            "status_filter": status_filter,
            "q": q,
            "room_types": Room.ROOM_TYPES,
            "school": school,
        })


@method_decorator(login_required, name="dispatch")
class RoomCreateView(SchoolAdminRequiredMixin, View):
    """Création d'une nouvelle salle."""
    template_name = "academics/rooms/create.html"

    def get(self, request):
        form = RoomForm(initial={"is_available": True, "capacity": 40, "room_type": "classroom"})
        return render(request, self.template_name, {"form": form})

    def post(self, request):
        school = request.user.school
        from .models import Room

        with schema_context(school.schema_name):
            form = RoomForm(request.POST)
            if form.is_valid():
                data = form.cleaned_data
                # Vérifier l'unicité du nom dans l'école
                if Room.objects.filter(name=data["name"], is_archived=False).exists():
                    form.add_error("name", f"Une salle « {data['name']} » existe déjà.")
                else:
                    room = Room.objects.create(
                        name=data["name"],
                        code=data.get("code", ""),
                        room_type=data["room_type"],
                        capacity=data["capacity"],
                        floor=data.get("floor", ""),
                        notes=data.get("notes", ""),
                        is_available=data.get("is_available", True),
                    )
                    messages.success(request, f"Salle « {room.name} » créée avec succès.")
                    return redirect("academics:rooms")

        return render(request, self.template_name, {"form": form})


@method_decorator(login_required, name="dispatch")
class RoomEditView(SchoolAdminRequiredMixin, View):
    """Modification d'une salle."""
    template_name = "academics/rooms/edit.html"

    def get(self, request, pk):
        school = request.user.school
        from .models import Room

        with schema_context(school.schema_name):
            room = get_object_or_404(Room, pk=pk)
            if room.is_archived:
                messages.warning(request, "Cette salle est archivée et ne peut plus être modifiée.")
                return redirect("academics:rooms")
            form = RoomForm(initial={
                "name": room.name,
                "code": room.code,
                "room_type": room.room_type,
                "capacity": room.capacity,
                "floor": room.floor,
                "notes": room.notes,
                "is_available": room.is_available,
            })

        return render(request, self.template_name, {"form": form, "room": room})

    def post(self, request, pk):
        school = request.user.school
        from .models import Room

        with schema_context(school.schema_name):
            room = get_object_or_404(Room, pk=pk)
            if room.is_archived:
                messages.error(request, "Cette salle est archivée et ne peut plus être modifiée.")
                return redirect("academics:rooms")

            form = RoomForm(request.POST)
            if form.is_valid():
                data = form.cleaned_data
                # Unicité du nom, hors soi-même
                if Room.objects.filter(name=data["name"], is_archived=False).exclude(pk=pk).exists():
                    form.add_error("name", f"Une salle « {data['name']} » existe déjà.")
                else:
                    room.name = data["name"]
                    room.code = data.get("code", "")
                    room.room_type = data["room_type"]
                    room.capacity = data["capacity"]
                    room.floor = data.get("floor", "")
                    room.notes = data.get("notes", "")
                    room.is_available = data.get("is_available", True)
                    room.save()
                    messages.success(request, f"Salle « {room.name} » mise à jour.")
                    return redirect("academics:rooms")

        return render(request, self.template_name, {"form": form, "room": room})


@method_decorator(login_required, name="dispatch")
class RoomToggleView(SchoolAdminRequiredMixin, View):
    """Active ou désactive une salle (POST uniquement)."""

    def post(self, request, pk):
        school = request.user.school
        from .models import Room

        with schema_context(school.schema_name):
            room = get_object_or_404(Room, pk=pk)
            if room.is_archived:
                messages.error(request, "Cette salle est archivée.")
                return redirect("academics:rooms")
            room.is_available = not room.is_available
            room.save(update_fields=["is_available", "updated_at"])
            action = "disponible" if room.is_available else "marquée indisponible"
            messages.success(request, f"Salle « {room.name} » {action}.")

        return redirect("academics:rooms")


@method_decorator(login_required, name="dispatch")
class RoomArchiveView(SchoolAdminRequiredMixin, View):
    """Archive ou désarchive une salle (POST uniquement)."""

    def post(self, request, pk):
        school = request.user.school
        from .models import Room

        with schema_context(school.schema_name):
            room = get_object_or_404(Room, pk=pk)
            room.is_archived = not room.is_archived
            room.save(update_fields=["is_archived", "updated_at"])
            action = "archivée" if room.is_archived else "désarchivée"
            messages.success(request, f"Salle « {room.name} » {action}.")

        return redirect("academics:rooms")


# ---------------------------------------------------------------------------
# Classes — CRUD (Phase 2.1)
# ---------------------------------------------------------------------------

@method_decorator(login_required, name="dispatch")
class ClassroomListView(SchoolStaffRequiredMixin, View):
    """Liste les classes de l'école, filtrées par année / niveau / option / statut."""
    template_name = "academics/classrooms/list.html"

    def get(self, request):
        school = request.user.school
        from apps.school_years.models import SchoolYear
        from .models import Level, Option, Classroom

        with schema_context(school.schema_name):
            years = list(SchoolYear.objects.filter(is_archived=False).order_by("-start_date"))
            active_year = SchoolYear.get_active()

            # Sélection de l'année
            year_id = request.GET.get("year_id")
            selected_year = None
            if year_id:
                selected_year = next((y for y in years if str(y.pk) == year_id), None)
            if selected_year is None:
                selected_year = active_year

            levels = []
            selected_level = None
            options = []
            selected_option = None
            classrooms = []

            if selected_year:
                levels = list(Level.objects.filter(school_year=selected_year).order_by("order", "name"))

                level_id = request.GET.get("level_id")
                if level_id:
                    selected_level = next((l for l in levels if str(l.pk) == level_id), None)

                if selected_level:
                    options = list(Option.objects.filter(level=selected_level).order_by("name"))
                    option_id = request.GET.get("option_id")
                    if option_id:
                        selected_option = next((o for o in options if str(o.pk) == option_id), None)

                # Filtres de statut
                status_filter = request.GET.get("status", "active")
                q = request.GET.get("q", "").strip()

                qs = Classroom.objects.filter(school_year=selected_year)
                if selected_option:
                    qs = qs.filter(option=selected_option)
                elif selected_level:
                    qs = qs.filter(option__level=selected_level)

                if status_filter == "archived":
                    qs = qs.filter(is_archived=True)
                elif status_filter == "inactive":
                    qs = qs.filter(is_archived=False, is_active=False)
                else:
                    qs = qs.filter(is_archived=False, is_active=True)

                if q:
                    qs = qs.filter(name__icontains=q)

                classrooms = list(qs.select_related("option", "option__level", "main_room")
                                   .order_by("option__level__order", "option__name", "name"))

        return render(request, self.template_name, {
            "classrooms": classrooms,
            "years": years,
            "selected_year": selected_year,
            "active_year": active_year,
            "levels": levels,
            "selected_level": selected_level,
            "options": options,
            "selected_option": selected_option,
            "status_filter": request.GET.get("status", "active"),
            "q": request.GET.get("q", "").strip(),
            "school": school,
        })


@method_decorator(login_required, name="dispatch")
class ClassroomCreateView(SchoolAdminRequiredMixin, View):
    """Création d'une nouvelle classe."""
    template_name = "academics/classrooms/create.html"

    def _build_context(self, school, request_year_id=None, request_level_id=None):
        """Construit le contexte commun (années, niveaux, options, salles)."""
        from apps.school_years.models import SchoolYear
        from .models import Level, Option, Room

        with schema_context(school.schema_name):
            years = list(SchoolYear.objects.filter(is_archived=False).order_by("-start_date"))
            active_year = SchoolYear.get_active()

            selected_year = None
            if request_year_id:
                selected_year = next((y for y in years if str(y.pk) == request_year_id), None)
            if not selected_year:
                selected_year = active_year

            if selected_year:
                levels = list(Level.objects.filter(school_year=selected_year, is_active=True).order_by("order", "name"))
            else:
                levels = []

            selected_level = None
            if request_level_id:
                selected_level = next((l for l in levels if str(l.pk) == request_level_id), None)

            if selected_level:
                option_qs = Option.objects.filter(level=selected_level, is_active=True).order_by("name")
            elif selected_year:
                option_qs = Option.objects.filter(level__school_year=selected_year, is_active=True).order_by("level__order", "name")
            else:
                option_qs = Option.objects.none()

            room_qs = Room.objects.filter(is_archived=False, is_available=True).order_by("name")
            # Populate the queryset cache while the tenant schema is active.
            # Django ModelChoiceFields are rendered later, outside this block.
            list(option_qs)
            list(room_qs)

        return {
            "years": years,
            "selected_year": selected_year,
            "levels": levels,
            "selected_level": selected_level,
            "option_qs": option_qs,
            "room_qs": room_qs,
        }

    def get(self, request):
        school = request.user.school
        year_id = request.GET.get("year_id")
        level_id = request.GET.get("level_id")

        with schema_context(school.schema_name):
            ctx = self._build_context(school, year_id, level_id)
            form = ClassroomForm(
                option_queryset=ctx["option_qs"],
                room_queryset=ctx["room_qs"],
                initial={"is_active": True, "capacity": 40},
            )

        return render(request, self.template_name, {**ctx, "form": form})

    def post(self, request):
        school = request.user.school
        from .models import Classroom

        year_id = request.POST.get("year_id")
        level_id = request.POST.get("level_id")

        with schema_context(school.schema_name):
            ctx = self._build_context(school, year_id, level_id)
            form = ClassroomForm(
                request.POST,
                option_queryset=ctx["option_qs"],
                room_queryset=ctx["room_qs"],
            )
            if form.is_valid():
                data = form.cleaned_data
                option = data["option"]
                school_year = option.level.school_year

                # Vérifier l'unicité (school_year, option, name)
                if Classroom.objects.filter(
                    school_year=school_year, option=option, name=data["name"]
                ).exists():
                    form.add_error("name", f"Une classe « {data['name']} » existe déjà pour cette option.")
                else:
                    classroom = Classroom.objects.create(
                        school_year=school_year,
                        option=option,
                        name=data["name"],
                        capacity=data["capacity"],
                        main_room=data.get("main_room"),
                        is_active=data.get("is_active", True),
                    )
                    messages.success(request, f"Classe « {classroom.full_name} » créée avec succès.")
                    return redirect("academics:classrooms")

        return render(request, self.template_name, {**ctx, "form": form})


@method_decorator(login_required, name="dispatch")
class ClassroomEditView(SchoolAdminRequiredMixin, View):
    """Modification d'une classe."""
    template_name = "academics/classrooms/edit.html"

    def get(self, request, pk):
        school = request.user.school
        from apps.school_years.models import SchoolYear
        from .models import Level, Option, Classroom, Room

        with schema_context(school.schema_name):
            classroom = get_object_or_404(Classroom, pk=pk)
            if classroom.is_archived:
                messages.warning(request, "Cette classe est archivée et ne peut plus être modifiée.")
                return redirect("academics:classrooms")

            option_qs = Option.objects.filter(
                level__school_year=classroom.school_year, is_active=True
            ).order_by("level__order", "name")
            room_qs = Room.objects.filter(is_archived=False, is_available=True).order_by("name")

            form = ClassroomForm(
                option_queryset=option_qs,
                room_queryset=room_qs,
                initial={
                    "option": classroom.option,
                    "name": classroom.name,
                    "capacity": classroom.capacity,
                    "main_room": classroom.main_room,
                    "is_active": classroom.is_active,
                },
            )

        return render(request, self.template_name, {"form": form, "classroom": classroom})

    def post(self, request, pk):
        school = request.user.school
        from .models import Option, Classroom, Room

        with schema_context(school.schema_name):
            classroom = get_object_or_404(Classroom, pk=pk)
            if classroom.is_archived:
                messages.error(request, "Cette classe est archivée et ne peut plus être modifiée.")
                return redirect("academics:classrooms")

            option_qs = Option.objects.filter(
                level__school_year=classroom.school_year, is_active=True
            ).order_by("level__order", "name")
            room_qs = Room.objects.filter(is_archived=False, is_available=True).order_by("name")

            form = ClassroomForm(
                request.POST,
                option_queryset=option_qs,
                room_queryset=room_qs,
            )
            if form.is_valid():
                data = form.cleaned_data
                option = data["option"]

                # Unicité (school_year, option, name) hors soi-même
                if Classroom.objects.filter(
                    school_year=classroom.school_year, option=option, name=data["name"]
                ).exclude(pk=pk).exists():
                    form.add_error("name", f"Une classe « {data['name']} » existe déjà pour cette option.")
                else:
                    classroom.option = option
                    classroom.name = data["name"]
                    classroom.capacity = data["capacity"]
                    classroom.main_room = data.get("main_room")
                    classroom.is_active = data.get("is_active", True)
                    classroom.save()
                    messages.success(request, f"Classe « {classroom.full_name} » mise à jour.")
                    return redirect("academics:classrooms")

        return render(request, self.template_name, {"form": form, "classroom": classroom})


@method_decorator(login_required, name="dispatch")
class ClassroomToggleView(SchoolAdminRequiredMixin, View):
    """Active ou désactive une classe (POST uniquement)."""

    def post(self, request, pk):
        school = request.user.school
        from .models import Classroom

        with schema_context(school.schema_name):
            classroom = get_object_or_404(Classroom, pk=pk)
            if classroom.is_archived:
                messages.error(request, "Cette classe est archivée.")
                return redirect("academics:classrooms")
            classroom.is_active = not classroom.is_active
            classroom.save(update_fields=["is_active", "updated_at"])
            action = "activée" if classroom.is_active else "désactivée"
            messages.success(request, f"Classe « {classroom.full_name} » {action}.")

        return redirect("academics:classrooms")


@method_decorator(login_required, name="dispatch")
class ClassroomArchiveView(SchoolAdminRequiredMixin, View):
    """Archive ou désarchive une classe (POST uniquement)."""

    def post(self, request, pk):
        school = request.user.school
        from .models import Classroom

        with schema_context(school.schema_name):
            classroom = get_object_or_404(Classroom, pk=pk)
            classroom.is_archived = not classroom.is_archived
            if classroom.is_archived:
                classroom.is_active = False
            classroom.save(update_fields=["is_archived", "is_active", "updated_at"])
            action = "archivée" if classroom.is_archived else "désarchivée"
            messages.success(request, f"Classe « {classroom.full_name} » {action}.")

        return redirect("academics:classrooms")
