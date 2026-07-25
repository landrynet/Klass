from django.urls import path
from django.views.generic import TemplateView

app_name = "finance"

urlpatterns = [
    path("", TemplateView.as_view(template_name="finance/dashboard.html"), name="dashboard"),
    path("fees/", TemplateView.as_view(template_name="finance/fees.html"), name="fees"),
    path("payments/", TemplateView.as_view(template_name="finance/payments.html"), name="payments"),
    path("reports/", TemplateView.as_view(template_name="finance/reports.html"), name="reports"),
]
