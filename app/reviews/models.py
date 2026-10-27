from django.db import models
from django.db.models import Avg


class Industry(models.Model):
    wp_term_id = models.PositiveBigIntegerField(unique=True)
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "industries"

    def __str__(self):
        return self.name


class Reviewer(models.Model):
    # Plain integer, not a FK: the WP user lives in another database (R2).
    wp_user_id = models.PositiveBigIntegerField(null=True, blank=True, unique=True)
    display_name = models.CharField(max_length=200)

    class Meta:
        ordering = ["display_name"]

    def __str__(self):
        return self.display_name


class Brand(models.Model):
    wp_post_id = models.PositiveBigIntegerField(unique=True)
    slug = models.SlugField(max_length=200, unique=True)
    name = models.CharField(max_length=200)
    content = models.TextField(blank=True)
    short_description = models.CharField(max_length=255, blank=True)
    website_url = models.URLField(blank=True)
    founded_year = models.PositiveSmallIntegerField(null=True, blank=True)
    headquarters = models.CharField(max_length=200, blank=True)
    industry = models.ForeignKey(
        Industry, null=True, blank=True, on_delete=models.SET_NULL, related_name="brands"
    )
    seo = models.JSONField(default=dict, blank=True)  # Yoast keys, carried but not rendered
    published_at = models.DateTimeField()

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    @property
    def average_rating(self):
        """Derived from reviews, never stored."""
        value = self.reviews.aggregate(v=Avg("rating"))["v"]
        return None if value is None else round(value, 1)


class Review(models.Model):
    wp_post_id = models.PositiveBigIntegerField(unique=True)
    slug = models.SlugField(max_length=200, unique=True)
    title = models.CharField(max_length=300)
    body = models.TextField(blank=True)
    rating = models.PositiveSmallIntegerField()
    reviewer = models.ForeignKey(
        Reviewer, null=True, blank=True, on_delete=models.SET_NULL, related_name="reviews"
    )
    reviewer_location = models.CharField(max_length=200, blank=True)
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE, related_name="reviews")
    published_at = models.DateTimeField()

    class Meta:
        ordering = ["-published_at", "-id"]

    def __str__(self):
        return self.title
