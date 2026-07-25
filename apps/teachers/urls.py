from django.urls import path
from django.views.generic import TemplateView

app_name = "teachers"

urlpatterns = [
    path("", TemplateView.as_view(template_name="teachers/list.html"), name="list"),
]
