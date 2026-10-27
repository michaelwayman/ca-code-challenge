import jwt
import pytest

from ca_auth_lib import (InsufficientRole, InvalidToken, has_role, require_role,
                         verify_token)
from ca_auth_lib import claims as c

NOW = 1_800_000_000


def sign(private, **over):
    payload = {c.CLAIM_ISS: c.ISSUER, c.CLAIM_SUB: "7", c.CLAIM_ROLE: c.ROLE_EDITOR,
               c.CLAIM_IAT: NOW, c.CLAIM_EXP: NOW + 900}
    payload.update(over)
    payload = {k: v for k, v in payload.items() if v is not None}
    return jwt.encode(payload, private, algorithm="RS256")


def test_claim_names_and_constants():
    assert (c.CLAIM_ISS, c.CLAIM_SUB, c.CLAIM_ROLE, c.CLAIM_IAT, c.CLAIM_EXP) == ("iss", "sub", "role", "iat", "exp")
    assert c.ISSUER == "ca-auth" and c.ALGORITHM == "RS256" and c.TOKEN_TTL_SECONDS == 900
    assert c.ROLES == ("reader", "editor")


def test_valid_token(keys):
    claims = verify_token(sign(keys[0]), keys[1], now=lambda: NOW + 10)
    assert claims["sub"] == "7" and claims["role"] == "editor"


def test_expired_boundary(keys):
    token = sign(keys[0])
    assert verify_token(token, keys[1], now=lambda: NOW + 899)
    with pytest.raises(InvalidToken):
        verify_token(token, keys[1], now=lambda: NOW + 900)


def test_wrong_key(keys, other_keys):
    with pytest.raises(InvalidToken):
        verify_token(sign(other_keys[0]), keys[1], now=lambda: NOW)


def test_garbage_and_empty(keys):
    for bad in ("", "not.a.jwt", "a.b.c"):
        with pytest.raises(InvalidToken):
            verify_token(bad, keys[1], now=lambda: NOW)


def test_bad_public_key(keys):
    with pytest.raises(InvalidToken):
        verify_token(sign(keys[0]), "not a key", now=lambda: NOW)


def test_hs256_and_none_rejected(keys):
    payload = {"iss": "ca-auth", "sub": "7", "role": "editor", "iat": NOW, "exp": NOW + 900}
    hs = jwt.encode(payload, "x" * 32, algorithm="HS256")
    with pytest.raises(InvalidToken):
        verify_token(hs, keys[1], now=lambda: NOW)
    none = jwt.encode(payload, None, algorithm="none")
    with pytest.raises(InvalidToken):
        verify_token(none, keys[1], now=lambda: NOW)


@pytest.mark.parametrize("over", [
    {c.CLAIM_ISS: "someone-else"}, {c.CLAIM_ISS: None}, {c.CLAIM_SUB: None},
    {c.CLAIM_SUB: 7}, {c.CLAIM_ROLE: None}, {c.CLAIM_ROLE: "admin"},
    {c.CLAIM_IAT: None}, {c.CLAIM_EXP: None}, {c.CLAIM_EXP: NOW + 901},
    {c.CLAIM_IAT: float(NOW), c.CLAIM_EXP: float(NOW + 900)},
])
def test_bad_claims(keys, over):
    with pytest.raises(InvalidToken):
        verify_token(sign(keys[0], **over), keys[1], now=lambda: NOW)


def test_roles():
    editor, reader = {"role": "editor"}, {"role": "reader"}
    assert has_role(editor, "reader") and has_role(editor, "editor")
    assert has_role(reader, "reader") and not has_role(reader, "editor")
    assert require_role(editor, "editor") is editor
    with pytest.raises(InsufficientRole):
        require_role(reader, "editor")
    with pytest.raises(InsufficientRole):
        require_role({}, "reader")
    with pytest.raises(ValueError):
        has_role(editor, "root")


def test_core_is_framework_free():
    import sys
    import ca_auth_lib  # noqa: F401
    assert "django" not in sys.modules and "ninja" not in sys.modules
