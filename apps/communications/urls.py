from django.urls import path
from django.views.generic import TemplateView

app_name = "communications"

urlpatterns = [
    path("", TemplateView.as_view(template_name="communications/list.html"), name="list"),
]
