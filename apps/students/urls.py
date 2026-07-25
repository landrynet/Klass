from django.urls import path
from . import views

app_name = "students"

urlpatterns = [
    path("", views.StudentListView.as_view(), name="list"),
    path("create/", views.StudentCreateView.as_view(), name="create"),
    path("<int:pk>/", views.StudentDetailView.as_view(), name="detail"),
    path("<int:pk>/edit/", views.StudentEditView.as_view(), name="edit"),
    path("parents/", views.ParentListView.as_view(), name="parents"),
    path("parents/create/", views.ParentCreateView.as_view(), name="parent_create"),
    path("parents/<int:pk>/", views.ParentDetailView.as_view(), name="parent_detail"),
    path("parents/<int:pk>/edit/", views.ParentEditView.as_view(), name="parent_edit"),
    path("matricules/configuration/", views.MatriculeConfigurationView.as_view(), name="matricule_config"),
    path("enroll/", views.StudentCreateView.as_view(), name="enroll"),
]
