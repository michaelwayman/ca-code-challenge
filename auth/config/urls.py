from django.http import JsonResponse
from django.urls import path

from accounts.api import api


def health(request):
    return JsonResponse({"status": "ok", "service": "auth"})


urlpatterns = [path("health/", health), path("api/", api.urls)]
