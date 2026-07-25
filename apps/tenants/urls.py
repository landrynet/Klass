"""
URLs pour la gestion des tenants (écoles) dans KLASS.

Deux groupes :
  1. Super Admin (/super-admin/) — gestion globale des écoles
  2. Setup wizard (/setup/) — assistant de configuration initiale pour l'Admin École
"""
from django.urls import path
from . import views

app_name = "tenants"

urlpatterns = [
    # --- Super Admin ---
    path("", views.SuperAdminDashboardView.as_view(), name="super_admin_dashboard"),
    path("schools/create/", views.SchoolCreateView.as_view(), name="school_create"),
    path("schools/<int:pk>/", views.SchoolDetailView.as_view(), name="school_detail"),

    # --- Assistant de configuration initiale (Admin École) ---
    path("setup/school-info/", views.SetupSchoolInfoView.as_view(), name="setup_school_info"),
    path("setup/school-year/", views.SetupSchoolYearView.as_view(), name="setup_school_year"),
    path("setup/confirm/", views.SetupConfirmView.as_view(), name="setup_confirm"),
]
