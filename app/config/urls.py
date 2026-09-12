from django.contrib import admin
from django.urls import include, path

from core.views import healthz

urlpatterns = [
    path("admin/", admin.site.urls),
    path("healthz/", healthz, name="healthz"),
    path("", include("accounts.urls")),
    path("sales/", include("sales.urls")),
    path("it/", include("core.urls_it", namespace="it")),
    path("hr/", include("hr.urls")),
    path("schedule/", include("operations.urls")),
    path("crew/", include("reports.urls_crew")),
    path("ceo/", include("reports.urls_ceo")),
    path("", include("core.urls")),
]

handler403 = "core.views.permission_denied"
handler404 = "core.views.page_not_found"
