# ca-auth-lib

Framework-free auth core shared by the main app and the auth service. Imports no Django or Ninja. Version 0.1.0.

## Modules

- `claims.py` - the one place claim names (`iss`, `sub`, `role`, `iat`, `exp`), roles, issuer, algorithm and the 900 second lifetime are defined, so both services agree.
- `tokens.py` - verifies an RS256 token against a public key passed in by the caller, with an injectable clock, and defines the error types.
- `roles.py` - checks a verified token's role against a requirement (editor satisfies reader).
- `__init__.py` - re-exports the public names and the version.

Signing is not here: only the auth service signs, so it stays in the auth service.

## Tests

From the repo root, in Docker (Django and Ninja are not installed in this container):

    make lib-test

## Consumers

The main app wraps `verify_token`/`require_role` in a thin Ninja auth class (in the main app, not here). The auth service imports the claim names from `claims.py`. Each service pins `ca-auth-lib==0.1.0`.
