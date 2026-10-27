import html
import re
from typing import Optional

from django.db.models import Avg, Count, OuterRef, Subquery
from ninja import NinjaAPI, Schema

from .models import Brand, Review

SNIPPET_LENGTH = 140
TAG_RE = re.compile(r"<[^>]+>")

api = NinjaAPI(title="Brand reviews", urls_namespace="api")


def top_review_body_subquery():
    """Highest rating, ties broken by newest (see Q14)."""
    return Subquery(
        Review.objects.filter(brand=OuterRef("pk"))
        .order_by("-rating", "-published_at", "-id")
        .values("body")[:1]
    )


def snippet(body):
    if body is None:
        return None
    text = " ".join(html.unescape(TAG_RE.sub(" ", body)).split())
    return text[:SNIPPET_LENGTH]


def brand_queryset():
    """One query for the whole listing: aggregates and top review are annotated."""
    return Brand.objects.select_related("industry").annotate(
        avg_rating=Avg("reviews__rating"),
        n_reviews=Count("reviews"),
        top_body=top_review_body_subquery(),
    )


class BrandRow(Schema):
    name: str
    slug: str
    industry: Optional[str]
    average_rating: Optional[float]
    review_count: int
    short_description: str
    top_review_snippet: Optional[str]

    @staticmethod
    def resolve_industry(obj):
        return obj.industry.name if obj.industry else None

    @staticmethod
    def resolve_average_rating(obj):
        return None if obj.avg_rating is None else round(obj.avg_rating, 1)

    @staticmethod
    def resolve_review_count(obj):
        return obj.n_reviews

    @staticmethod
    def resolve_top_review_snippet(obj):
        return snippet(obj.top_body)


@api.get("/brands/", response=list[BrandRow], auth=None)
def list_brands(request):
    return brand_queryset()
