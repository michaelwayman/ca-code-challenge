import os
from unittest import mock

from ca_auth_lib import verify_token
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from django.test import TestCase

from .models import User

_KEY = rsa.generate_private_key(public_exponent=65537, key_size=2048)
PRIVATE = _KEY.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8,
                             serialization.NoEncryption()).decode()
PUBLIC = _KEY.public_key().public_bytes(serialization.Encoding.PEM,
                                        serialization.PublicFormat.SubjectPublicKeyInfo).decode()


class LoginTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("ed", password="pw", role=User.EDITOR)

    def post(self, **body):
        return self.client.post("/api/auth/login", body, content_type="application/json")

    def test_valid_login_returns_verifiable_token(self):
        with mock.patch.dict(os.environ, {"AUTH_JWT_PRIVATE_KEY": PRIVATE}):
            r = self.post(username="ed", password="pw")
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertEqual(data["token_type"], "Bearer")
        self.assertEqual(data["expires_in"], 900)
        claims = verify_token(data["access_token"], PUBLIC)
        self.assertEqual(claims["sub"], str(self.user.pk))
        self.assertEqual(claims["role"], "editor")

    def test_invalid_credentials_401_without_token(self):
        with mock.patch.dict(os.environ, {"AUTH_JWT_PRIVATE_KEY": PRIVATE}):
            r = self.post(username="ed", password="wrong")
        self.assertEqual(r.status_code, 401)
        self.assertNotIn("access_token", r.json())

    def test_missing_key_refuses_to_issue(self):
        with mock.patch.dict(os.environ, {"AUTH_JWT_PRIVATE_KEY": ""}):
            r = self.post(username="ed", password="pw")
        self.assertEqual(r.status_code, 503)
        self.assertNotIn("access_token", r.json())
