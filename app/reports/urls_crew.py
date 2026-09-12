from django.urls import path

from . import views

app_name = "crew"

urlpatterns = [path("my-shifts/", views.MyShiftsView.as_view(), name="my_shifts")]
