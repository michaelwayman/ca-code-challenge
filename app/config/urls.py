from django.http import JsonResponse
from django.urls import include, path


def health(request):
    return JsonResponse({"status": "ok", "service": "main-app"})


urlpatterns = [path("health/", health), path("", include("reviews.urls"))]
