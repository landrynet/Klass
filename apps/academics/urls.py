from django.urls import path
from django.views.generic import TemplateView

app_name = "academics"

urlpatterns = [
    path("", TemplateView.as_view(template_name="academics/dashboard.html"), name="dashboard"),
    path("levels/", TemplateView.as_view(template_name="academics/levels.html"), name="levels"),
    path("classrooms/", TemplateView.as_view(template_name="academics/classrooms.html"), name="classrooms"),
    path("rooms/", TemplateView.as_view(template_name="academics/rooms.html"), name="rooms"),
    path("subjects/", TemplateView.as_view(template_name="academics/subjects.html"), name="subjects"),
]
