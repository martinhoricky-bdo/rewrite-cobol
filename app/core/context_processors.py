from django.utils import timezone


def header(request):
    return {
        "now_local": timezone.localtime(),
        "app_title": "COBOL AIRLINES",
        "app_subtitle": "Programming at heights",
    }
