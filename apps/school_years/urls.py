from django.urls import path
from django.views.generic import TemplateView

app_name = "school_years"

urlpatterns = [
    path("", TemplateView.as_view(template_name="school_years/list.html"), name="list"),
]
