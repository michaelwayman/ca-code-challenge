import os
from unittest import mock

from ca_auth_lib import InvalidToken, verify_token
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


class RoleTests(TestCase):
    """R15: the auth service is the source of truth for roles."""

    def login(self, username):
        with mock.patch.dict(os.environ, {"AUTH_JWT_PRIVATE_KEY": PRIVATE}):
            r = self.client.post("/api/auth/login", {"username": username, "password": "pw"},
                                 content_type="application/json")
        self.assertEqual(r.status_code, 200)
        return r.json()["access_token"]

    def test_reader_and_editor_tokens_carry_their_roles(self):
        User.objects.create_user("rita", password="pw", role=User.READER)
        User.objects.create_user("ed", password="pw", role=User.EDITOR)
        self.assertEqual(verify_token(self.login("rita"), PUBLIC)["role"], "reader")
        self.assertEqual(verify_token(self.login("ed"), PUBLIC)["role"], "editor")

    def test_imported_role_mapping(self):
        from .management.commands.import_wp_users import role_from_capabilities
        self.assertEqual(role_from_capabilities('a:1:{s:13:"administrator";b:1;}'), User.EDITOR)
        self.assertEqual(role_from_capabilities('a:1:{s:6:"editor";b:1;}'), User.EDITOR)
        self.assertEqual(role_from_capabilities('a:1:{s:10:"subscriber";b:1;}'), User.READER)
        self.assertEqual(role_from_capabilities(None), User.READER)

    def test_role_change_applies_at_next_login_not_to_old_token(self):
        from .tokens import issue_token
        user = User.objects.create_user("rita", password="pw", role=User.READER)
        clock = {"t": 1_000_000.0}
        with mock.patch.dict(os.environ, {"AUTH_JWT_PRIVATE_KEY": PRIVATE}):
            old = issue_token(user, now=lambda: clock["t"])["access_token"]

        user.role = User.EDITOR
        user.save()

        # Old token keeps its old role until it expires.
        clock["t"] += 899
        self.assertEqual(verify_token(old, PUBLIC, now=lambda: clock["t"])["role"], "reader")
        clock["t"] += 2
        with self.assertRaises(InvalidToken):
            verify_token(old, PUBLIC, now=lambda: clock["t"])

        # A fresh login carries the new role.
        self.assertEqual(verify_token(self.login("rita"), PUBLIC)["role"], "editor")
