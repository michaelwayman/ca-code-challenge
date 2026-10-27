import html
import re
from typing import Literal, Optional
from urllib.parse import urlencode

from django.db.models import Avg, Count, OuterRef, Subquery
from django.db.models import F
from ninja import Field, NinjaAPI, Query, Schema

from .models import Brand, Review

SNIPPET_LENGTH = 140
TAG_RE = re.compile(r"<[^>]+>")

DEFAULT_PAGE_SIZE = 10

ORDERINGS = {
    "average_rating": F("avg_rating").asc(nulls_last=True),
    "-average_rating": F("avg_rating").desc(nulls_last=True),
    "review_count": F("n_reviews").asc(),
    "-review_count": F("n_reviews").desc(),
    "name": F("name").asc(),
}

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


class BrandPage(Schema):
    count: int
    next: Optional[str]
    previous: Optional[str]
    results: list[BrandRow]


class BrandFilters(Schema):
    industry: list[str] = []  # repeatable industry slug; unknown slugs match nothing
    ordering: Literal[tuple(ORDERINGS)] = "name"
    page: int = Field(1, ge=1)
    page_size: int = Field(DEFAULT_PAGE_SIZE, ge=1)


def page_url(request, filters, page):
    params = [("industry", slug) for slug in filters.industry]
    params += [("ordering", filters.ordering), ("page_size", filters.page_size), ("page", page)]
    return request.build_absolute_uri(request.path) + "?" + urlencode(params)


@api.get("/brands/", response=BrandPage, auth=None)
def list_brands(request, filters: BrandFilters = Query(...)):
    """Brand cards. Several `industry` slugs are OR-ed. A page past the end returns
    200 with empty `results` and the real `count`."""
    qs = brand_queryset()
    if filters.industry:
        qs = qs.filter(industry__slug__in=filters.industry)
    # name then id as tie-breakers keep pages stable; ratings sort nulls last.
    qs = qs.order_by(ORDERINGS[filters.ordering], "name", "id")
    count = qs.count()
    start = (filters.page - 1) * filters.page_size
    last_page = max(1, -(-count // filters.page_size))
    results = list(qs[start : start + filters.page_size])
    return {
        "count": count,
        "next": page_url(request, filters, filters.page + 1) if start + filters.page_size < count else None,
        "previous": page_url(request, filters, min(filters.page - 1, last_page)) if filters.page > 1 else None,
        "results": results,
    }
