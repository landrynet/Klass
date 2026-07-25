"""
URLs pour la gestion des années scolaires — Phase 2.0.
"""
from django.urls import path
from . import views

app_name = "school_years"

urlpatterns = [
    path("", views.SchoolYearListView.as_view(), name="list"),
    path("create/", views.SchoolYearCreateView.as_view(), name="create"),
    path("<int:pk>/edit/", views.SchoolYearEditView.as_view(), name="edit"),
    path("<int:pk>/activate/", views.SchoolYearActivateView.as_view(), name="activate"),
    path("<int:pk>/end/", views.SchoolYearEndView.as_view(), name="end"),
    path("<int:pk>/archive/", views.SchoolYearArchiveView.as_view(), name="archive"),
]
