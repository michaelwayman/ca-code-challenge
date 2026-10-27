## Deterministic UUIDs for the WordPress user ID (2026-10-27)
**Answer:** Yes, it works: a UUIDv5 over a fixed namespace and the WP user ID gives the same UUID in both services with no shared database or lookup. It is optional here, because registration is out of scope (O5) so no non-WP users will ever need a different ID scheme, and only 9 users exist. **Serves/costs:** serves C4 and C5 (no cross-database key), costs C7 (the shared namespace constant must live in the library or be duplicated).
**Open:** (1) Should the token `sub` claim be an opaque UUID or the WP integer ID? (2) If UUIDs are used, does the namespace constant live in the shared library's claims module? (3) Is an opaque identifier worth explaining on the call for 9 users?

### Decision this informs
How a main-app reviewer (R2, `wp_user_id`) and an auth-service user (R13) refer to the same person, and what identifier goes in the token `sub` claim (R14, T8). Steered by C4 (main app stores no accounts), C5 (separate auth database, so no foreign key), C7 (library holds only shared code), C13 (dev/demo).

### Findings
- UUIDv5 hashes namespace plus name with SHA-1 and the same inputs always give the same UUID (RFC 9562, https://www.rfc-editor.org/rfc/rfc9562.html, read 2026-10-27).
- Python provides it as `uuid.uuid5(namespace, name)`, with name as bytes or a UTF-8 string (https://docs.python.org/3/library/uuid.html, read 2026-10-27).
- Verified locally with Python 3 on this machine: for WP user IDs 2, 3 and 9 two independent calls returned identical UUIDs, user IDs 1 to 9 produced 9 distinct UUIDs, and the version is 5.
- RFC 9562 says a UUID is not a security capability and implementations should not assume it is hard to guess. A name-based UUID can be recomputed by anyone who knows the namespace and name, so it is an identifier, not a secret.
- RFC 9562 advises against name-based UUIDs as primary keys because names may change. WP user IDs are integers that do not change, and the dump has users 1 to 9 (db/dump.sql), so this does not bite here.
- RFC 9562 notes SHA-1 may be disallowed by some policies and then points to UUIDv8 with SHA-256. This identifier protects nothing, so the SHA-1 concern is not material at this scale. Not checked: any policy of the interviewers.
- The reviewers in the dump are `wp_users` 2 to 9 (A6 invalid), and admin (user 1) wrote no reviews.

### Options
| Option | Cross-service key | Pros | Cons |
|---|---|---|---|
| A. Keep the WP integer (current R2 and R13) | `wp_user_id` int | Simplest, readable in SQL, matches the dump, no shared constant | Sequential and guessable, ties the token `sub` to WordPress |
| B. UUIDv5 from the WP ID | uuid computed in each service | Opaque `sub`, no shared database, importers are idempotent by key | Namespace constant must be shared (fits the library claims module), one more concept to defend, cannot be reversed to the WP ID |
| C. Both: auth PK is the UUID, keep nullable `wp_user_id` for audit | uuid plus int | Opaque `sub` and traceability to WP | Two identifiers per user |

### Not verified
- Storing the UUIDs in Postgres `uuid` columns through Django `UUIDField` and Ninja schemas was not tried. It is standard Django behaviour, but it was not run here.
