from django.http import JsonResponse
from django.urls import include, path


def health(request):
    return JsonResponse({"status": "ok", "service": "main-app"})


from reviews.api import api  # noqa: E402

urlpatterns = [path("health/", health), path("api/", api.urls),path("", include("reviews.urls"))]
