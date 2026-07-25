"""URLs Phase 3.0 & 3.1 — Élèves, parents, matricules et inscriptions."""
from django.urls import path
from . import views

app_name = "students"

urlpatterns = [
    # ---------------------------------------------------------------------------
    # Phase 3.0 — Élèves
    # ---------------------------------------------------------------------------
    path("", views.StudentListView.as_view(), name="list"),
    path("create/", views.StudentCreateView.as_view(), name="create"),
    path("<int:pk>/", views.StudentDetailView.as_view(), name="detail"),
    path("<int:pk>/edit/", views.StudentEditView.as_view(), name="edit"),

    # ---------------------------------------------------------------------------
    # Phase 3.0 — Parents
    # ---------------------------------------------------------------------------
    path("parents/", views.ParentListView.as_view(), name="parents"),
    path("parents/create/", views.ParentCreateView.as_view(), name="parent_create"),
    path("parents/<int:pk>/", views.ParentDetailView.as_view(), name="parent_detail"),
    path("parents/<int:pk>/edit/", views.ParentEditView.as_view(), name="parent_edit"),

    # ---------------------------------------------------------------------------
    # Phase 3.0 — Matricules
    # ---------------------------------------------------------------------------
    path("matricules/configuration/", views.MatriculeConfigurationView.as_view(), name="matricule_config"),

    # ---------------------------------------------------------------------------
    # Phase 3.1 — Inscriptions
    # ---------------------------------------------------------------------------
    path("enrollments/", views.EnrollmentListView.as_view(), name="enrollment_list"),
    path("enrollments/create/", views.EnrollmentCreateView.as_view(), name="enrollment_create"),
    path("enrollments/<int:pk>/", views.EnrollmentDetailView.as_view(), name="enrollment_detail"),
    path("enrollments/<int:pk>/edit/", views.EnrollmentEditView.as_view(), name="enrollment_edit"),
    path("enrollments/<int:pk>/change-class/", views.EnrollmentChangeClassView.as_view(), name="enrollment_change_class"),
    path("enrollments/<int:pk>/status/", views.EnrollmentStatusChangeView.as_view(), name="enrollment_status"),

    # ---------------------------------------------------------------------------
    # Phase 3.1 — Vue par classe
    # ---------------------------------------------------------------------------
    path("classrooms/<int:classroom_pk>/enrollments/", views.ClassroomEnrollmentsView.as_view(), name="classroom_enrollments"),

    # ---------------------------------------------------------------------------
    # Phase 3.1 — API HTMX / JSON
    # ---------------------------------------------------------------------------
    path("api/classrooms-for-year/", views.ClassroomsForYearView.as_view(), name="api_classrooms_for_year"),
    path("api/search/", views.StudentSearchView.as_view(), name="api_search"),
]
