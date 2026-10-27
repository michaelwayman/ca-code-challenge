from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Auth service user. Owns credentials and role (C4); keyed to WP by wp_user_id."""

    READER = "reader"
    EDITOR = "editor"
    ROLES = [(READER, "Reader"), (EDITOR, "Editor")]

    wp_user_id = models.PositiveBigIntegerField(unique=True, null=True, blank=True)
    role = models.CharField(max_length=16, choices=ROLES, default=READER)
