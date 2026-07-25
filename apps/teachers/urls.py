from django.urls import path
from . import views

app_name = "teachers"

urlpatterns = [
    path("", views.TeacherListView.as_view(), name="list"),
    path("personnel/", views.PersonnelListView.as_view(), name="personnel_list"),
    path("personnel/create/", views.PersonnelCreateView.as_view(), name="personnel_create"),
    path("personnel/<int:pk>/", views.PersonnelDetailView.as_view(), name="personnel_detail"),
    path("personnel/<int:pk>/edit/", views.PersonnelEditView.as_view(), name="personnel_edit"),
    path("personnel/<int:pk>/status/", views.PersonnelStatusView.as_view(), name="personnel_status"),
    path("create/", views.TeacherCreateView.as_view(), name="create"),
    path("<int:pk>/", views.TeacherDetailView.as_view(), name="teacher_detail"),
    path("<int:pk>/edit/", views.PersonnelEditView.as_view(), name="teacher_edit"),
]
