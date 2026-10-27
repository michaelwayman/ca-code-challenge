from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("brand/<slug:slug>/", views.brand_detail, name="brand-detail"),
    path("review/<slug:slug>/", views.review_detail, name="review-detail"),
]
