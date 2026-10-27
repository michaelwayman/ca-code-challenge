from django.shortcuts import get_object_or_404, render

from .models import Brand, Industry, Review

HOME_REVIEW_COUNT = 10


def home(request):
    reviews = Review.objects.select_related("brand", "reviewer")[:HOME_REVIEW_COUNT]
    industries = list(Industry.objects.values("name", "slug"))
    return render(request, "reviews/home.html", {"reviews": reviews, "industries": industries})


def brand_detail(request, slug):
    brand = get_object_or_404(Brand.objects.select_related("industry"), slug=slug)
    reviews = brand.reviews.select_related("reviewer")
    return render(
        request,
        "reviews/brand_detail.html",
        {"brand": brand, "reviews": reviews, "rating": brand.average_rating},
    )


def review_detail(request, slug):
    review = get_object_or_404(Review.objects.select_related("brand", "reviewer"), slug=slug)
    return render(request, "reviews/review_detail.html", {"review": review})
