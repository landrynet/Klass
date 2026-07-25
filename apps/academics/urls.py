"""
URLs pour le module académique de KLASS — Phase 2.0.
Dashboard + Niveaux + Options / Filières.
"""
from django.urls import path
from . import views

app_name = "academics"

urlpatterns = [
    # Dashboard principal
    path("", views.DashboardView.as_view(), name="dashboard"),

    # Niveaux scolaires
    path("levels/", views.LevelListView.as_view(), name="levels"),
    path("levels/create/", views.LevelCreateView.as_view(), name="level_create"),
    path("levels/<int:pk>/edit/", views.LevelEditView.as_view(), name="level_edit"),
    path("levels/<int:pk>/toggle/", views.LevelToggleView.as_view(), name="level_toggle"),

    # Options / Filières
    path("options/", views.OptionListView.as_view(), name="options"),
    path("options/create/", views.OptionCreateView.as_view(), name="option_create"),
    path("options/<int:pk>/edit/", views.OptionEditView.as_view(), name="option_edit"),
    path("options/<int:pk>/toggle/", views.OptionToggleView.as_view(), name="option_toggle"),

    # Classrooms et Rooms (Phase 2.1 — placeholders conservés)
    path("classrooms/", views.DashboardView.as_view(), name="classrooms"),
    path("rooms/", views.DashboardView.as_view(), name="rooms"),
    path("subjects/", views.DashboardView.as_view(), name="subjects"),
]
