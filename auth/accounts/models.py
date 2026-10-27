import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Auth service user. Owns credentials and role (C4).

    The primary key is a UUID. Imported users get a UUIDv5 derived from their WP
    user ID by the importer, so the WP ID itself is never stored here.
    """

    READER = "reader"
    EDITOR = "editor"
    ROLES = [(READER, "Reader"), (EDITOR, "Editor")]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    role = models.CharField(max_length=16, choices=ROLES, default=READER)
