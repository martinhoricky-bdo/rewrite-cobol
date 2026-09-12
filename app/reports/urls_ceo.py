"""Design: CEO reporting routes expose the UC-E01 operational overview."""

from django.urls import path

from . import views

app_name = "ceo"

urlpatterns = [path("dashboard/", views.DashboardView.as_view(), name="dashboard")]
