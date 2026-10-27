from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from .models import Brand, Industry, Review


class BrandListTests(TestCase):
    """GET /api/brands/: filter, both sorts (rating, review count) and pagination.

    The 401/403/200 cases of the PATCH endpoint are covered in tests.py (BrandPatchTests).
    """

    @classmethod
    def setUpTestData(cls):
        now = timezone.now()
        cls.tech = Industry.objects.create(wp_term_id=1, name="Tech", slug="tech")
        cls.food = Industry.objects.create(wp_term_id=2, name="Food", slug="food")
        cls.bank = Industry.objects.create(wp_term_id=3, name="Banking", slug="banking")
        # name, industry, ratings
        spec = [
            ("Alpha", cls.tech, [5, 5]),        # avg 5.0, 2 reviews
            ("Bravo", cls.tech, [3]),           # avg 3.0, 1 review
            ("Charlie", cls.food, [4, 4, 4]),   # avg 4.0, 3 reviews
            ("Delta", cls.food, []),            # no reviews: null rating
            ("Echo", cls.bank, [1, 2]),         # avg 1.5, 2 reviews
        ]
        wp = 100
        for i, (name, industry, ratings) in enumerate(spec, start=1):
            brand = Brand.objects.create(
                wp_post_id=i, slug=name.lower(), name=name, industry=industry,
                short_description=f"{name} desc", published_at=now)
            for rating in ratings:
                wp += 1
                Review.objects.create(
                    wp_post_id=wp, slug=f"r{wp}", title="t", body=f"<p>body {rating}</p>",
                    rating=rating, brand=brand, published_at=now - timedelta(days=wp))

    def get(self, query=""):
        response = self.client.get(f"/api/brands/{query}")
        self.assertEqual(response.status_code, 200)
        return response.json()

    def names(self, query=""):
        return [row["name"] for row in self.get(query)["results"]]

    def test_listing_is_public_and_row_shape(self):
        data = self.get()
        self.assertEqual(set(data), {"count", "next", "previous", "results"})
        self.assertEqual(data["count"], 5)
        row = data["results"][0]
        self.assertEqual(set(row), {"name", "slug", "industry", "average_rating", "review_count",
                                    "short_description", "top_review_snippet"})
        self.assertEqual(row["name"], "Alpha")
        self.assertEqual(row["average_rating"], 5.0)
        self.assertEqual(row["review_count"], 2)
        self.assertEqual(row["industry"], "Tech")

    def test_default_order_is_name(self):
        self.assertEqual(self.names(), ["Alpha", "Bravo", "Charlie", "Delta", "Echo"])

    def test_filter_by_industry_slug(self):
        self.assertEqual(self.names("?industry=food"), ["Charlie", "Delta"])

    def test_filter_by_several_industries_is_or(self):
        self.assertEqual(self.names("?industry=food&industry=banking"), ["Charlie", "Delta", "Echo"])

    def test_unknown_industry_matches_nothing(self):
        data = self.get("?industry=nope")
        self.assertEqual((data["count"], data["results"]), (0, []))

    def test_filter_count_reflects_filter_not_page(self):
        data = self.get("?industry=tech&page_size=1")
        self.assertEqual(data["count"], 2)
        self.assertEqual(len(data["results"]), 1)

    def test_sort_by_average_rating_both_directions_nulls_last(self):
        self.assertEqual(self.names("?ordering=-average_rating"),
                         ["Alpha", "Charlie", "Bravo", "Echo", "Delta"])
        self.assertEqual(self.names("?ordering=average_rating"),
                         ["Echo", "Bravo", "Charlie", "Alpha", "Delta"])

    def test_sort_by_review_count_both_directions(self):
        # ties (Alpha/Echo at 2) fall back to name
        self.assertEqual(self.names("?ordering=-review_count"),
                         ["Charlie", "Alpha", "Echo", "Bravo", "Delta"])
        self.assertEqual(self.names("?ordering=review_count"),
                         ["Delta", "Bravo", "Alpha", "Echo", "Charlie"])

    def test_invalid_ordering_is_rejected(self):
        self.assertEqual(self.client.get("/api/brands/?ordering=bogus").status_code, 422)

    def test_filter_and_sort_combine(self):
        self.assertEqual(self.names("?industry=tech&industry=banking&ordering=-average_rating"),
                         ["Alpha", "Bravo", "Echo"])

    def test_pagination_pages_links_and_count(self):
        first = self.get("?page_size=2")
        self.assertEqual([r["name"] for r in first["results"]], ["Alpha", "Bravo"])
        self.assertEqual(first["count"], 5)
        self.assertIsNone(first["previous"])
        self.assertIn("page=2", first["next"])
        self.assertIn("page_size=2", first["next"])

        second = self.client.get(first["next"]).json()
        self.assertEqual([r["name"] for r in second["results"]], ["Charlie", "Delta"])
        self.assertIn("page=1", second["previous"])

        last = self.client.get(second["next"]).json()
        self.assertEqual([r["name"] for r in last["results"]], ["Echo"])
        self.assertIsNone(last["next"])

    def test_pagination_keeps_filter_and_ordering_in_links(self):
        data = self.get("?industry=tech&industry=food&ordering=-review_count&page_size=2")
        self.assertIn("industry=tech", data["next"])
        self.assertIn("industry=food", data["next"])
        self.assertIn("ordering=-review_count", data["next"])

    def test_page_past_the_end_is_empty_with_real_count(self):
        data = self.get("?page=9&page_size=2")
        self.assertEqual((data["count"], data["results"], data["next"]), (5, [], None))
        self.assertIsNotNone(data["previous"])

    def test_invalid_page_params_rejected(self):
        for query in ("page=0", "page_size=0", "page=abc"):
            self.assertEqual(self.client.get(f"/api/brands/?{query}").status_code, 422, query)

    def test_snippet_keeps_24_whole_words_and_adds_ellipsis_only_when_cut(self):
        from .api import snippet
        short = " ".join(f"w{i}" for i in range(24))
        self.assertEqual(snippet(f"<p>{short}</p>"), short)
        longer = short + " extra words"
        self.assertEqual(snippet(f"<p>{longer}</p>"), short + "\u2026")
        self.assertEqual(snippet("<p>a  &amp;\n b</p>"), "a & b")
        self.assertIsNone(snippet(None))

    def test_listing_query_count_does_not_grow_with_brands(self):
        from django.db import connection
        from django.test.utils import CaptureQueriesContext

        def queries():
            with CaptureQueriesContext(connection) as ctx:
                self.get("?page_size=100")
            return len(ctx)

        before = queries()
        now = timezone.now()
        for i in range(20):
            brand = Brand.objects.create(
                wp_post_id=1000 + i, slug=f"extra{i}", name=f"Extra {i}", industry=self.tech,
                short_description="d", published_at=now)
            Review.objects.create(wp_post_id=5000 + i, slug=f"extra-r{i}", title="t",
                                  body="<p>x</p>", rating=3, brand=brand, published_at=now)
        self.assertEqual(queries(), before)

    def test_top_review_snippet_is_highest_rating(self):
        row = next(r for r in self.get()["results"] if r["name"] == "Echo")
        self.assertEqual(row["top_review_snippet"], "body 2")
        delta = next(r for r in self.get()["results"] if r["name"] == "Delta")
        self.assertIsNone(delta["top_review_snippet"])
