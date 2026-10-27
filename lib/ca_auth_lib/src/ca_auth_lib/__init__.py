"""Shared auth core: claim names, token verification, role checks. No web framework imports."""

from .claims import ALGORITHM, CLAIM_IAT, CLAIM_EXP, CLAIM_ISS, CLAIM_ROLE, CLAIM_SUB, ISSUER, ROLE_EDITOR, ROLE_READER, ROLES, TOKEN_TTL_SECONDS
from .roles import has_role, require_role
from .tokens import AuthError, InvalidToken, InsufficientRole, verify_token

__version__ = "0.1.0"

__all__ = [
    "ALGORITHM", "CLAIM_EXP", "CLAIM_IAT", "CLAIM_ISS", "CLAIM_ROLE", "CLAIM_SUB",
    "ISSUER", "ROLE_EDITOR", "ROLE_READER", "ROLES", "TOKEN_TTL_SECONDS",
    "AuthError", "InsufficientRole", "InvalidToken", "has_role", "require_role", "verify_token",
]
