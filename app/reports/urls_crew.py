from django.urls import path

from . import views

app_name = "crew"

urlpatterns = [path("my-shifts/", views.my_shifts, name="my_shifts")]
