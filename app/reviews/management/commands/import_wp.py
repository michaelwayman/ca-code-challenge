"""Import brands, reviews, industries and reviewers from the WordPress MariaDB.

Usage: docker compose run --rm app python manage.py import_wp

Re-runnable: every row is upserted on its WP ID (post, term or user), so a second
run creates nothing and reports created / updated / unchanged per model. The
command never creates accounts, passwords or roles (C4).
"""
import html
import os
import re
from collections import Counter
from datetime import timezone

import pymysql
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils.html import strip_tags

from reviews.models import Brand, Industry, Review, Reviewer

SHORT_DESCRIPTION_LENGTH = 200
YOAST_PREFIX = "_yoast_wpseo_"


def short_description(content, limit=SHORT_DESCRIPTION_LENGTH):
    """First `limit` characters of the stripped content, cut at a word boundary."""
    text = " ".join(html.unescape(strip_tags(content)).split())
    if len(text) <= limit:
        return text
    cut = text[:limit]
    if text[limit] != " ":
        cut = cut.rsplit(" ", 1)[0]
    return cut.rstrip(" ,;:.-") + "…"


def _int_or_none(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


class Command(BaseCommand):
    help = "Import WP brands, reviews, industries and reviewers (idempotent, keyed on WP IDs)."

    def handle(self, *args, **options):
        self.stats = {}
        prefix = os.environ.get("WORDPRESS_TABLE_PREFIX", "wp_")
        if not re.fullmatch(r"[A-Za-z0-9_]+", prefix):
            raise CommandError("Invalid WORDPRESS_TABLE_PREFIX")
        self.p = prefix
        try:
            conn = pymysql.connect(
                host=os.environ.get("WP_DB_HOST", "db"),
                port=int(os.environ.get("WP_DB_PORT", "3306")),
                user=os.environ.get("WP_DB_USER", "wp"),
                password=os.environ.get("WP_DB_PASSWORD", "wp"),
                database=os.environ.get("WP_DB_NAME", "wp"),
                charset="utf8mb4",
                cursorclass=pymysql.cursors.DictCursor,
            )
        except pymysql.MySQLError as exc:
            raise CommandError(f"Cannot reach the WordPress database: {exc}")

        with conn, transaction.atomic():
            self.cur = conn.cursor()
            self.import_industries()
            self.import_brands()
            self.import_reviewers()
            self.import_reviews()

        for model, counts in self.stats.items():
            self.stdout.write(
                f"{model:<9} created={counts['created']} updated={counts['updated']} "
                f"unchanged={counts['unchanged']}"
            )

    # -- helpers -----------------------------------------------------------

    def q(self, sql, args=()):
        self.cur.execute(sql.replace("{p}", self.p), args)
        return self.cur.fetchall()

    def upsert(self, model, key, values):
        """Create or update the row identified by `key`; record what happened."""
        counts = self.stats.setdefault(model.__name__, Counter(created=0, updated=0, unchanged=0))
        obj = model.objects.filter(**key).first()
        if obj is None:
            obj = model.objects.create(**key, **values)
            counts["created"] += 1
            return obj
        changed = [f for f, v in values.items() if getattr(obj, f) != v]
        if changed:
            for f in changed:
                setattr(obj, f, values[f])
            obj.save(update_fields=changed)
            counts["updated"] += 1
        else:
            counts["unchanged"] += 1
        return obj

    def meta(self, post_ids):
        by_post = {}
        if not post_ids:
            return by_post
        marks = ",".join(["%s"] * len(post_ids))
        for row in self.q(
            f"SELECT post_id, meta_key, meta_value FROM {{p}}postmeta WHERE post_id IN ({marks})",
            post_ids,
        ):
            by_post.setdefault(row["post_id"], {})[row["meta_key"]] = row["meta_value"]
        return by_post

    def posts(self, post_type):
        return self.q(
            "SELECT ID, post_author, post_date_gmt, post_title, post_name, post_content "
            "FROM {p}posts WHERE post_type=%s AND post_status='publish' ORDER BY ID",
            (post_type,),
        )

    # -- importers ---------------------------------------------------------

    def import_industries(self):
        self.industry_by_post = {}
        for row in self.q(
            "SELECT t.term_id, t.name, t.slug FROM {p}terms t "
            "JOIN {p}term_taxonomy tt ON tt.term_id=t.term_id WHERE tt.taxonomy='industry' "
            "ORDER BY t.term_id"
        ):
            self.upsert(
                Industry,
                {"wp_term_id": row["term_id"]},
                {"name": row["name"], "slug": row["slug"]},
            )
        for row in self.q(
            "SELECT tr.object_id, tt.term_id FROM {p}term_relationships tr "
            "JOIN {p}term_taxonomy tt ON tt.term_taxonomy_id=tr.term_taxonomy_id "
            "WHERE tt.taxonomy='industry' ORDER BY tr.object_id, tt.term_id"
        ):
            # A3: at most one industry per brand
            self.industry_by_post[row["object_id"]] = row["term_id"]

    def import_brands(self):
        posts = self.posts("brand")
        meta = self.meta([p["ID"] for p in posts])
        industries = {i.wp_term_id: i for i in Industry.objects.all()}
        for post in posts:
            m = meta.get(post["ID"], {})
            self.upsert(
                Brand,
                {"wp_post_id": post["ID"]},
                {
                    "slug": post["post_name"],
                    "name": post["post_title"],
                    "content": post["post_content"],
                    "short_description": short_description(post["post_content"]),
                    "website_url": m.get("website_url", ""),
                    "founded_year": _int_or_none(m.get("founded_year")),
                    "headquarters": m.get("headquarters", ""),
                    "industry": industries.get(self.industry_by_post.get(post["ID"])),
                    "seo": {k: v for k, v in sorted(m.items()) if k.startswith(YOAST_PREFIX)},
                    "published_at": post["post_date_gmt"].replace(tzinfo=timezone.utc),
                },
            )

    def import_reviewers(self):
        # Reviewers are the WP authors of published reviews (users with no reviews
        # are not reviewers). Only name data is read, never credentials.
        author_ids = sorted({p["post_author"] for p in self.posts("review") if p["post_author"]})
        self.reviewer_by_wp = {}
        if not author_ids:
            return
        marks = ",".join(["%s"] * len(author_ids))
        for row in self.q(
            f"SELECT ID, display_name FROM {{p}}users WHERE ID IN ({marks}) ORDER BY ID",
            author_ids,
        ):
            self.upsert(
                Reviewer, {"wp_user_id": row["ID"]}, {"display_name": row["display_name"]}
            )
        self.reviewer_by_wp = {r.wp_user_id: r for r in Reviewer.objects.all()}

    def import_reviews(self):
        posts = self.posts("review")
        meta = self.meta([p["ID"] for p in posts])
        brands = {b.wp_post_id: b for b in Brand.objects.all()}
        skipped = 0
        for post in posts:
            m = meta.get(post["ID"], {})
            brand = brands.get(_int_or_none(m.get("brand")))
            rating = _int_or_none(m.get("rating"))
            if brand is None or rating is None:
                skipped += 1
                self.stderr.write(f"skipped review {post['ID']}: missing brand or rating")
                continue
            self.upsert(
                Review,
                {"wp_post_id": post["ID"]},
                {
                    "slug": post["post_name"],
                    "title": post["post_title"],
                    "body": post["post_content"],
                    "rating": rating,
                    "reviewer": self.reviewer_by_wp.get(post["post_author"]),
                    "reviewer_location": m.get("reviewer_location", ""),
                    "brand": brand,
                    "published_at": post["post_date_gmt"].replace(tzinfo=timezone.utc),
                },
            )
        if skipped:
            self.stdout.write(f"Review    skipped={skipped}")
