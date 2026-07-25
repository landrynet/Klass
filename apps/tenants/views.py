"""
Vues pour la gestion des tenants (écoles) dans KLASS.

Super Admin :
  - Dashboard super-admin (liste des écoles, stats)
  - Création d'une école
  - Détail d'une école

Assistant de configuration initiale (Admin École) :
  - Étape 1 : Informations de l'école
  - Étape 2 : Année scolaire initiale
  - Étape 3 : Confirmation et activation
"""
import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.decorators import method_decorator
from django.views import View

from apps.core.constants import Roles
from .forms import CreateSchoolForm, SchoolInfoSetupForm, SchoolYearSetupForm
from .models import School
from .services import create_school_with_tenant

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Décorateurs / mixins de permissions
# ---------------------------------------------------------------------------

def super_admin_required(view_func=None):
    """Décorateur : accès réservé au Super Admin."""
    def decorator(func):
        @login_required
        def wrapper(request, *args, **kwargs):
            if request.user.role != Roles.SUPER_ADMIN:
                raise PermissionDenied
            return func(request, *args, **kwargs)
        return wrapper
    if view_func:
        return decorator(view_func)
    return decorator


def school_admin_required(view_func=None):
    """Décorateur : accès réservé à l'Admin École."""
    def decorator(func):
        @login_required
        def wrapper(request, *args, **kwargs):
            if request.user.role != Roles.SCHOOL_ADMIN:
                raise PermissionDenied
            return func(request, *args, **kwargs)
        return wrapper
    if view_func:
        return decorator(view_func)
    return decorator


# ---------------------------------------------------------------------------
# Super Admin — Dashboard et gestion des écoles
# ---------------------------------------------------------------------------

@method_decorator([login_required], name="dispatch")
class SuperAdminDashboardView(View):
    """
    Tableau de bord principal du Super Admin.
    Affiche la liste des écoles, les statistiques et les actions disponibles.
    """
    template_name = "tenants/super_admin_dashboard.html"

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect("accounts:login")
        if request.user.role != Roles.SUPER_ADMIN:
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def get(self, request):
        schools = School.objects.all().order_by("-created_at")
        stats = {
            "total": schools.count(),
            "active": schools.filter(is_active=True).count(),
            "setup_done": schools.filter(setup_completed=True).count(),
            "trial": schools.filter(subscription_status="trial").count(),
        }
        return render(request, self.template_name, {
            "schools": schools,
            "stats": stats,
        })


@method_decorator([login_required], name="dispatch")
class SchoolCreateView(View):
    """
    Création d'une école par le Super Admin.
    Crée le tenant PostgreSQL, le domaine et l'Admin École en une seule opération.
    """
    template_name = "tenants/schools/create.html"

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect("accounts:login")
        if request.user.role != Roles.SUPER_ADMIN:
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def get(self, request):
        form = CreateSchoolForm()
        return render(request, self.template_name, {"form": form})

    def post(self, request):
        form = CreateSchoolForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            try:
                school, admin_user, temp_password = create_school_with_tenant(
                    name=data["name"],
                    email=data["email"],
                    phone=data.get("phone", ""),
                    address=data.get("address", ""),
                    city=data.get("city", ""),
                    country=data.get("country", "Congo (RDC)"),
                    admin_first_name=data["admin_first_name"],
                    admin_last_name=data["admin_last_name"],
                    admin_email=data["admin_email"],
                    created_by=request.user,
                )
                logger.info(
                    "École créée : %s (slug=%s)",
                    school.name, school.slug,
                )
                # Stocker les identifiants en session pour affichage unique.
                # Le mot de passe n'est jamais re-affiché après cette étape.
                request.session["school_creation_credentials"] = {
                    "school_name": school.name,
                    "school_pk": school.pk,
                    "school_slug": school.slug,
                    "admin_email": admin_user.email,
                    "admin_full_name": admin_user.get_full_name(),
                    "temp_password": temp_password,
                    "login_url": f"https://{school.slug}.klass.app/auth/login/",
                }
                return redirect("tenants:school_creation_success")

            except Exception as exc:
                logger.exception("Erreur lors de la création de l'école : %s", exc)
                messages.error(
                    request,
                    f"Erreur lors de la création de l'école : {exc}. "
                    "Aucune donnée incomplète n'a été enregistrée."
                )

        return render(request, self.template_name, {"form": form})


@method_decorator([login_required], name="dispatch")
class SchoolCreationSuccessView(View):
    """
    Page de confirmation après création d'une école.
    Affiche une seule fois les informations d'accès de l'Admin École,
    lues depuis la session puis immédiatement effacées.
    """
    template_name = "tenants/schools/creation_success.html"

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect("accounts:login")
        if request.user.role != Roles.SUPER_ADMIN:
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def get(self, request):
        # Lire et supprimer immédiatement les identifiants de la session (affichage unique)
        credentials = request.session.pop("school_creation_credentials", None)
        if not credentials:
            messages.info(
                request,
                "Les informations d'accès ne sont disponibles qu'une seule fois, "
                "immédiatement après la création. Consultez la fiche de l'école si nécessaire."
            )
            return redirect("tenants:super_admin_dashboard")
        return render(request, self.template_name, {"credentials": credentials})


@method_decorator([login_required], name="dispatch")
class SchoolDetailView(View):
    """
    Détail d'une école (Super Admin).
    Affiche les informations de l'école, son Admin et son statut.
    """
    template_name = "tenants/schools/detail.html"

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect("accounts:login")
        if request.user.role != Roles.SUPER_ADMIN:
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, pk):
        school = get_object_or_404(School, pk=pk)
        # Récupérer le personnel de l'école (via FK school sur User)
        from apps.accounts.models import User
        staff = User.objects.filter(school=school).order_by("role", "last_name")
        return render(request, self.template_name, {
            "school": school,
            "staff": staff,
        })


# ---------------------------------------------------------------------------
# Assistant de configuration initiale — Admin École
# ---------------------------------------------------------------------------

@method_decorator([login_required], name="dispatch")
class SetupSchoolInfoView(View):
    """
    Étape 1 de l'assistant : informations de l'école.
    Permet à l'Admin École de compléter les données de son établissement.
    """
    template_name = "tenants/setup/step_school_info.html"
    STEP = 1

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect("accounts:login")
        if request.user.role != Roles.SCHOOL_ADMIN:
            raise PermissionDenied
        if not hasattr(request.user, "school") or not request.user.school:
            messages.error(request, "Votre compte n'est associé à aucune école.")
            return redirect("accounts:logout")
        return super().dispatch(request, *args, **kwargs)

    def get(self, request):
        school = request.user.school
        form = SchoolInfoSetupForm(instance=school)
        return render(request, self.template_name, {
            "form": form,
            "school": school,
            "step": self.STEP,
            "total_steps": 3,
        })

    def post(self, request):
        school = request.user.school
        form = SchoolInfoSetupForm(request.POST, request.FILES, instance=school)
        if form.is_valid():
            form.save()
            request.session["setup_step_1_done"] = True
            messages.success(request, "Informations de l'école enregistrées.")
            return redirect("tenants:setup_school_year")
        return render(request, self.template_name, {
            "form": form,
            "school": school,
            "step": self.STEP,
            "total_steps": 3,
        })


@method_decorator([login_required], name="dispatch")
class SetupSchoolYearView(View):
    """
    Étape 2 de l'assistant : année scolaire initiale.
    Crée la première année scolaire active de l'établissement.
    """
    template_name = "tenants/setup/step_school_year.html"
    STEP = 2

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect("accounts:login")
        if request.user.role != Roles.SCHOOL_ADMIN:
            raise PermissionDenied
        if not hasattr(request.user, "school") or not request.user.school:
            messages.error(request, "Votre compte n'est associé à aucune école.")
            return redirect("accounts:logout")
        return super().dispatch(request, *args, **kwargs)

    def get(self, request):
        school = request.user.school
        existing_year = self._get_active_year(school)
        form = SchoolYearSetupForm()
        return render(request, self.template_name, {
            "form": form,
            "school": school,
            "existing_year": existing_year,
            "step": self.STEP,
            "total_steps": 3,
        })

    def post(self, request):
        school = request.user.school
        form = SchoolYearSetupForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            try:
                self._create_school_year(school, data)
                request.session["setup_step_2_done"] = True
                messages.success(request, f"Année scolaire « {data['name']} » créée et activée.")
                return redirect("tenants:setup_confirm")
            except Exception as exc:
                logger.exception("Erreur lors de la création de l'année scolaire : %s", exc)
                messages.error(request, f"Erreur : {exc}")

        existing_year = self._get_active_year(school)
        return render(request, self.template_name, {
            "form": form,
            "school": school,
            "existing_year": existing_year,
            "step": self.STEP,
            "total_steps": 3,
        })

    def _get_active_year(self, school):
        from django_tenants.utils import schema_context
        from apps.school_years.models import SchoolYear
        try:
            with schema_context(school.schema_name):
                return SchoolYear.get_active()
        except Exception:
            return None

    def _create_school_year(self, school, data):
        from django.db import transaction
        from django_tenants.utils import schema_context
        from apps.school_years.models import SchoolYear

        with schema_context(school.schema_name):
            with transaction.atomic():
                # Désactiver les années précédentes
                SchoolYear.objects.filter(is_active=True).update(is_active=False)
                # Créer la nouvelle année active
                SchoolYear.objects.create(
                    name=data["name"],
                    start_date=data["start_date"],
                    end_date=data["end_date"],
                    is_active=True,
                )


@method_decorator([login_required], name="dispatch")
class SetupConfirmView(View):
    """
    Étape 3 de l'assistant : confirmation et activation.
    Valide la configuration initiale et active l'école.
    """
    template_name = "tenants/setup/confirm.html"
    STEP = 3

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect("accounts:login")
        if request.user.role != Roles.SCHOOL_ADMIN:
            raise PermissionDenied
        if not hasattr(request.user, "school") or not request.user.school:
            messages.error(request, "Votre compte n'est associé à aucune école.")
            return redirect("accounts:logout")
        return super().dispatch(request, *args, **kwargs)

    def get(self, request):
        school = request.user.school
        active_year = self._get_active_year(school)
        return render(request, self.template_name, {
            "school": school,
            "active_year": active_year,
            "step": self.STEP,
            "total_steps": 3,
        })

    def post(self, request):
        school = request.user.school

        # --- Vérification des prérequis côté serveur ---
        active_year = self._get_active_year(school)
        if not active_year:
            messages.error(
                request,
                "Impossible de valider la configuration : aucune année scolaire active n'a été créée. "
                "Veuillez créer une année scolaire avant de continuer."
            )
            return redirect("tenants:setup_school_year")

        # --- Validation : les informations de base de l'école sont présentes ---
        school.refresh_from_db()
        if not school.name or not school.email:
            messages.error(
                request,
                "Les informations de base de l'école sont incomplètes. "
                "Veuillez compléter l'étape 1."
            )
            return redirect("tenants:setup_school_info")

        # --- Tous les prérequis sont remplis : activer l'école ---
        school.setup_completed = True
        school.save(update_fields=["setup_completed"])

        # Nettoyer les variables de session de l'assistant
        request.session.pop("setup_step_1_done", None)
        request.session.pop("setup_step_2_done", None)

        messages.success(
            request,
            f"Configuration terminée ! L'école « {school.name} » est maintenant opérationnelle."
        )
        logger.info("Configuration initiale terminée pour l'école : %s", school.name)
        return redirect("academics:dashboard")

    def _get_active_year(self, school):
        from django_tenants.utils import schema_context
        from apps.school_years.models import SchoolYear
        try:
            with schema_context(school.schema_name):
                return SchoolYear.get_active()
        except Exception:
            return None
