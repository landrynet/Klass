"""
URLs pour le module académique de KLASS — Phase 2.0 & 2.1.
Dashboard + Niveaux + Options / Filières + Classes + Salles.
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

    # Salles (Phase 2.1)
    path("rooms/", views.RoomListView.as_view(), name="rooms"),
    path("rooms/create/", views.RoomCreateView.as_view(), name="room_create"),
    path("rooms/<int:pk>/edit/", views.RoomEditView.as_view(), name="room_edit"),
    path("rooms/<int:pk>/toggle/", views.RoomToggleView.as_view(), name="room_toggle"),
    path("rooms/<int:pk>/archive/", views.RoomArchiveView.as_view(), name="room_archive"),

    # Classes (Phase 2.1)
    path("classrooms/", views.ClassroomListView.as_view(), name="classrooms"),
    path("classrooms/create/", views.ClassroomCreateView.as_view(), name="classroom_create"),
    path("classrooms/<int:pk>/edit/", views.ClassroomEditView.as_view(), name="classroom_edit"),
    path("classrooms/<int:pk>/toggle/", views.ClassroomToggleView.as_view(), name="classroom_toggle"),
    path("classrooms/<int:pk>/archive/", views.ClassroomArchiveView.as_view(), name="classroom_archive"),

    # Matières (Phase future)
    path("subjects/", views.DashboardView.as_view(), name="subjects"),
]
