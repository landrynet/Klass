from django.urls import path
from django.views.generic import TemplateView

app_name = "students"

urlpatterns = [
    path("", TemplateView.as_view(template_name="students/list.html"), name="list"),
    path("enroll/", TemplateView.as_view(template_name="students/enroll.html"), name="enroll"),
]
