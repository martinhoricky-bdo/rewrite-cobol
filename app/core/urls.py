"""Core routes provide Design-based home and health endpoints around the CICS-inspired base
layout.
"""

from django.urls import path

from . import views

app_name = "core"

urlpatterns = [
    path("", views.HomeView.as_view(), name="home"),
    path("healthz/", views.healthz, name="healthz"),
]
