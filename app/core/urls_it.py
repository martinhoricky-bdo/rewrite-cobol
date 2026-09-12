from django.urls import include, path

app_name = "it"

urlpatterns = [
    path("", include("accounts.urls_it")),
    path("", include("fleet.urls")),
]
