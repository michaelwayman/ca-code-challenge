"""Claim names and constants both services must agree on."""

ALGORITHM = "RS256"
ISSUER = "ca-auth"
TOKEN_TTL_SECONDS = 900  # exp = iat + 900

CLAIM_ISS = "iss"
CLAIM_SUB = "sub"  # auth user id, as a string
CLAIM_ROLE = "role"
CLAIM_IAT = "iat"  # integer epoch seconds
CLAIM_EXP = "exp"  # integer epoch seconds

ROLE_READER = "reader"
ROLE_EDITOR = "editor"
ROLES = (ROLE_READER, ROLE_EDITOR)
