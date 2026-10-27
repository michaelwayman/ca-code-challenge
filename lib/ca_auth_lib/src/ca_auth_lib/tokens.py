"""Verify an RS256 token against a supplied public key. The clock is injectable."""

import time
from typing import Callable

import jwt

from .claims import (ALGORITHM, CLAIM_EXP, CLAIM_IAT, CLAIM_ISS, CLAIM_ROLE,
                     CLAIM_SUB, ISSUER, ROLES, TOKEN_TTL_SECONDS)


class AuthError(Exception):
    """Base class: the request is not authorised."""


class InvalidToken(AuthError):
    """Malformed, badly signed, expired, wrong issuer, or missing/invalid claims."""


class InsufficientRole(AuthError):
    """Token is valid but its role does not satisfy the requirement."""


def verify_token(token: str, public_key: str, now: Callable[[], float] = time.time) -> dict:
    """Return the claims of a valid token, or raise InvalidToken.

    Only RS256 is accepted (an unsigned or HS256 token is rejected). Expiry is
    checked against now() so tests need no sleeping.
    """
    try:
        claims = jwt.decode(
            token,
            public_key,
            algorithms=[ALGORITHM],
            issuer=ISSUER,
            options={"verify_exp": False, "verify_iat": False,
                     "require": [CLAIM_ISS, CLAIM_SUB, CLAIM_ROLE, CLAIM_IAT, CLAIM_EXP]},
        )
    except (jwt.PyJWTError, ValueError, TypeError) as exc:
        raise InvalidToken(str(exc)) from exc

    iat, exp = claims[CLAIM_IAT], claims[CLAIM_EXP]
    if not all(isinstance(v, int) and not isinstance(v, bool) for v in (iat, exp)):
        raise InvalidToken("iat and exp must be integers")
    if not isinstance(claims[CLAIM_SUB], str) or not claims[CLAIM_SUB]:
        raise InvalidToken("sub must be a non-empty string")
    if claims[CLAIM_ROLE] not in ROLES:
        raise InvalidToken("unknown role")
    if exp - iat != TOKEN_TTL_SECONDS:
        raise InvalidToken("unexpected token lifetime")
    if now() >= exp:
        raise InvalidToken("token expired")
    return claims
