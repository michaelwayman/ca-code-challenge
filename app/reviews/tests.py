import time

import jwt
from ca_auth_lib import ALGORITHM, ISSUER, TOKEN_TTL_SECONDS
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from django.test import TestCase, override_settings
from django.utils import timezone

from .models import Brand

_KEY = rsa.generate_private_key(public_exponent=65537, key_size=2048)
PRIVATE = _KEY.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8,
                             serialization.NoEncryption()).decode()
PUBLIC = _KEY.public_key().public_bytes(serialization.Encoding.PEM,
                                        serialization.PublicFormat.SubjectPublicKeyInfo).decode()


def token(role, issued=None):
    iat = int(issued or time.time())
    return jwt.encode({"iss": ISSUER, "sub": "1", "role": role, "iat": iat,
                       "exp": iat + TOKEN_TTL_SECONDS}, PRIVATE, algorithm=ALGORITHM)


@override_settings(JWT_PUBLIC_KEY=PUBLIC)
class BrandPatchTests(TestCase):
    def setUp(self):
        self.brand = Brand.objects.create(wp_post_id=1, slug="acme", name="Acme",
                                          short_description="old", published_at=timezone.now())

    def patch(self, body, slug="acme", tok=None):
        headers = {"HTTP_AUTHORIZATION": f"Bearer {tok}"} if tok else {}
        return self.client.patch(f"/api/brands/{slug}/", body, content_type="application/json", **headers)

    def current(self):
        return Brand.objects.get(pk=self.brand.pk)

    def test_no_token_401(self):
        self.assertEqual(self.patch({"short_description": "x"}).status_code, 401)
        self.assertEqual(self.current().short_description, "old")

    def test_reader_403(self):
        self.assertEqual(self.patch({"short_description": "x"}, tok=token("reader")).status_code, 403)
        self.assertEqual(self.current().short_description, "old")

    def test_editor_200_returns_row_and_shows_in_listing_and_page(self):
        r = self.patch({"short_description": "New text"}, tok=token("editor"))
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["short_description"], "New text")
        self.assertEqual(r.json()["slug"], "acme")
        listing = self.client.get("/api/brands/").json()["results"]
        self.assertEqual(listing[0]["short_description"], "New text")
        self.assertContains(self.client.get("/brand/acme/"), "New text")

    def test_invalid_and_expired_token_401(self):
        self.assertEqual(self.patch({"short_description": "x"}, tok="junk").status_code, 401)
        old = token("editor", issued=time.time() - 3600)
        self.assertEqual(self.patch({"short_description": "x"}, tok=old).status_code, 401)

    def test_length_bounds(self):
        ed = token("editor")
        self.assertEqual(self.patch({"short_description": ""}, tok=ed).status_code, 422)
        self.assertEqual(self.patch({"short_description": "a" * 501}, tok=ed).status_code, 422)
        self.assertEqual(self.patch({"short_description": "a" * 500}, tok=ed).status_code, 200)
        self.assertEqual(self.patch({"short_description": "a"}, tok=ed).status_code, 200)

    def test_other_fields_422_and_nothing_changes(self):
        ed = token("editor")
        for extra in ({"slug": "z"}, {"name": "Z"}, {"website_url": "http://x.example"}):
            r = self.patch({"short_description": "new", **extra}, tok=ed)
            self.assertEqual(r.status_code, 422)
        self.assertEqual(self.patch({"name": "Z"}, tok=ed).status_code, 422)
        b = self.current()
        self.assertEqual((b.short_description, b.slug, b.name), ("old", "acme", "Acme"))

    def test_order_401_403_404(self):
        body = {"short_description": "x"}
        self.assertEqual(self.patch(body, slug="nope").status_code, 401)
        self.assertEqual(self.patch(body, slug="nope", tok=token("reader")).status_code, 403)
        self.assertEqual(self.patch(body, slug="nope", tok=token("editor")).status_code, 404)

    def test_get_stays_public(self):
        self.assertEqual(self.client.get("/api/brands/").status_code, 200)
        self.assertEqual(self.client.get("/brand/acme/").status_code, 200)

    @override_settings(JWT_PUBLIC_KEY="")
    def test_no_key_configured_fails_closed(self):
        self.assertEqual(self.patch({"short_description": "x"}, tok=token("editor")).status_code, 401)
