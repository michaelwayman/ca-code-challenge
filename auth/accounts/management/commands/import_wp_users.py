"""Import WP users and their roles into the auth service.

Usage: docker compose run --rm auth python manage.py import_wp_users

Re-runnable: users are upserted on their WP user ID, so a second run creates
nothing and reports created / updated / unchanged. Every imported user's password
is reset to the dev password from AUTH_DEV_PASSWORD (default "dev-password"; see
README). WP password hashes are never read. Roles: WP administrator and editor
map to "editor", everything else to "reader". Role changes apply at next login.
"""
import os
import re
from collections import Counter

import pymysql
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from accounts.models import User

EDITOR_WP_ROLES = {"administrator", "editor"}


def role_from_capabilities(serialized):
    """Map a serialized PHP wp_capabilities value to a service role."""
    wp_roles = set(re.findall(r's:\d+:"([^"]+)";b:1;', serialized or ""))
    return User.EDITOR if wp_roles & EDITOR_WP_ROLES else User.READER


class Command(BaseCommand):
    help = "Import wp_users and roles into auth users (idempotent, keyed on WP user ID)."

    def handle(self, *args, **options):
        prefix = os.environ.get("WORDPRESS_TABLE_PREFIX", "wp_")
        if not re.fullmatch(r"[A-Za-z0-9_]+", prefix):
            raise CommandError("Invalid WORDPRESS_TABLE_PREFIX")
        password = settings.AUTH_DEV_PASSWORD
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

        with conn, conn.cursor() as cur:
            cur.execute(
                f"SELECT u.ID, u.user_login, u.user_email, u.display_name, m.meta_value AS caps "
                f"FROM {prefix}users u LEFT JOIN {prefix}usermeta m "
                f"ON m.user_id=u.ID AND m.meta_key=%s ORDER BY u.ID",
                (f"{prefix}capabilities",),
            )
            rows = cur.fetchall()

        counts = Counter(created=0, updated=0, unchanged=0)
        with transaction.atomic():
            for row in rows:
                values = {
                    "username": row["user_login"],
                    "email": row["user_email"],
                    "first_name": row["display_name"][:150],
                    "role": role_from_capabilities(row["caps"]),
                }
                user = User.objects.filter(wp_user_id=row["ID"]).first()
                if user is None:
                    user = User(wp_user_id=row["ID"], **values)
                    user.set_password(password)
                    user.save()
                    counts["created"] += 1
                    continue
                changed = [f for f, v in values.items() if getattr(user, f) != v]
                if not user.check_password(password):
                    user.set_password(password)
                    changed.append("password")
                if changed:
                    for f, v in values.items():
                        setattr(user, f, v)
                    user.save()
                    counts["updated"] += 1
                else:
                    counts["unchanged"] += 1

        self.stdout.write(
            f"User      created={counts['created']} updated={counts['updated']} "
            f"unchanged={counts['unchanged']}"
        )
