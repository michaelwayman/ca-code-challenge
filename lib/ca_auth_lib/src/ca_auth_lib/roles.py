"""Role checks. editor satisfies a reader requirement; reader does not satisfy editor."""

from .claims import CLAIM_ROLE, ROLE_EDITOR, ROLE_READER, ROLES
from .tokens import InsufficientRole

_RANK = {ROLE_READER: 0, ROLE_EDITOR: 1}


def has_role(claims: dict, required: str) -> bool:
    if required not in ROLES:
        raise ValueError(f"unknown role: {required}")
    return _RANK.get(claims.get(CLAIM_ROLE), -1) >= _RANK[required]


def require_role(claims: dict, required: str) -> dict:
    """Return claims if they satisfy `required`, else raise InsufficientRole."""
    if not has_role(claims, required):
        raise InsufficientRole(f"{required} role required")
    return claims
