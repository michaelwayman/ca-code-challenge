"""Issue RS256 access tokens. Claim names and constants come from ca_auth_lib."""
import os
import time

import jwt
from ca_auth_lib import (ALGORITHM, CLAIM_EXP, CLAIM_IAT, CLAIM_ISS, CLAIM_ROLE,
                         CLAIM_SUB, ISSUER, TOKEN_TTL_SECONDS)


class SigningKeyMissing(Exception):
    """AUTH_JWT_PRIVATE_KEY is not set; the service never generates a key itself."""


def _private_key() -> str:
    pem = os.environ.get("AUTH_JWT_PRIVATE_KEY", "").strip()
    if not pem:
        raise SigningKeyMissing(
            "AUTH_JWT_PRIVATE_KEY is not set; run 'make jwt-keys' and restart the auth service"
        )
    return pem.replace("\\n", "\n")


def issue_token(user, now=time.time) -> dict:
    key = _private_key()
    iat = int(now())
    claims = {
        CLAIM_ISS: ISSUER,
        CLAIM_SUB: str(user.pk),
        CLAIM_ROLE: user.role,
        CLAIM_IAT: iat,
        CLAIM_EXP: iat + TOKEN_TTL_SECONDS,
    }
    token = jwt.encode(claims, key, algorithm=ALGORITHM)
    return {"access_token": token, "token_type": "Bearer", "expires_in": TOKEN_TTL_SECONDS}
