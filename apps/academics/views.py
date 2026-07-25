"""
Vues pour le module Académique de KLASS.
"""
import logging
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views import View

logger = logging.getLogger(__name__)


@method_decorator(login_required, name="dispatch")
class DashboardView(View):
    """
    Tableau de bord de l'école pour le personnel (Admin, Secrétariat, Comptable, Enseignant).
    Affiche un résumé de l'état de l'école et des raccourcis vers les modules.
    """
    template_name = "academics/dashboard.html"

    def get(self, request):
        school = getattr(request.user, "school", None) or getattr(request, "current_school", None)
        active_year = None

        if school and school.schema_name:
            try:
                from django_tenants.utils import schema_context
                from apps.school_years.models import SchoolYear
                with schema_context(school.schema_name):
                    active_year = SchoolYear.get_active()
            except Exception as exc:
                logger.warning("Impossible de récupérer l'année active : %s", exc)

        return render(request, self.template_name, {
            "school": school,
            "active_year": active_year,
        })
