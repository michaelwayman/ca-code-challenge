# Build brief

Build only what is listed. Out-of-scope items are decisions, not gaps. Anything else is a spec change: stop and ask. Detail: `mkit show <ID>`.

## Constraints
- C1 Whole stack runs through docker compose, Docker is the only host prerequisite
- C2 Migration must be re-runnable without producing duplicates
- C3 Server-rendered URL slugs must match WP permalinks
- C4 Main app stores no passwords or roles
- C5 Auth service is a separate Django project in its own container with its own database
- C6 GET /api/brands/ and the server-rendered pages stay public
- C7 Shared library has its own pyproject.toml, is versioned, has tests that run without either Django project, and holds only code both services use
- C8 Shared library lives in its own directory of this repo
- C9 All six pillars are required, prioritise within them rather than cutting one
- C10 Call date is the cutoff, no fixed deadline, the date itself is not yet known
- C11 reference/theme.css is not edited, SCSS must compile to structurally equivalent CSS
- C12 Every submitted piece must be explainable and defensible by the candidate
- C13 Built for dev and demo as a take-home, not for production deployment

## Build
- **R13** [P0] Auth service owns users and its own re-runnable import creates them from wp_users
  - auth service runs as its own container with its own database service
  - the main app database schema contains no password or role columns
  - one documented auth service command imports wp_users and their roles from the WP source
  - a second consecutive run of that command creates no new users and reports created, updated and unchanged counts
  - after the import the number of auth users equals the number of wp_users
  - each imported user can log in with the dev password read from an environment variable with a documented local default, never hardcoded in source
  - auth user IDs are UUIDs derived deterministically from the WP user ID (UUIDv5 with a fixed namespace constant in the importer)
  - the auth database stores no WP user ID
  - a rerun derives the same UUIDs and creates no duplicates
  - the UUIDv5 namespace is one fixed constant in the importer
  - the auth database is reset and import_wp_users rerun, with no integer-to-UUID data migration
- **R14** [P0] Login exchanges credentials for a token
  - a login request with valid credentials returns a token
  - invalid credentials return 401 with no token
  - the README shows a curl command that obtains a token
  - login is POST /api/auth/login with JSON username and password and returns JSON access_token, token_type and expires_in
  - the token is an RS256 JWT with claims sub, role, iat, exp and iss
  - the library core defines these claim names and the auth service imports them
  - the token claim sub is the auth user's UUID string
  - the signing key is read from AUTH_JWT_PRIVATE_KEY and login returns 503 when it is unset
  - iss is ca-auth
  - role is reader or editor
  - iat and exp are integer epoch seconds with exp = iat + 900

## Do NOT build
- O1 Migrating the WP admin and editor experience
- O2 Yoast SEO frontend output
- O3 WP plugin parity beyond data structure
- O4 User-facing review submission and search
- O5 Registration, password reset, social login, MFA
- O6 A login UI
- O7 Image uploads and real logos
- O8 Pixel-matching the WP theme
- O9 Archive pages and industry taxonomy pages

## Decided
- Where is BrandList rendered? -> Mounted on a Django page
- Is Yoast SEO data carried across? -> Kept as JSON on the brand model, not rendered
- Which tests are in scope beyond the library tests? -> Library tests plus migration idempotency, API and auth tests
- Are archive and taxonomy pages built? -> No, only homepage, brand detail and review detail
- What happens to wp_users passwords in the auth service? -> Reset to a documented dev password
- Which Python and Django versions and which API stack (DRF, Django Ninja or plain views)? -> Python 3.12, Django 5.2 LTS, Django Ninja
- Which database engine for the main app and for the auth service? -> PostgreSQL for both, separate containers
- Which token format and signing, and does the main app verify locally or call the auth service, and what happens when it is down? -> RS256 JWT, main app verifies locally with the public key, revocation through short expiry
- Which React build tooling, language (TypeScript or JavaScript), CSS approach and way of serving the bundle, and where does filter and sort state live including URL sync? -> Vite with JavaScript, styled with the project SCSS, filter and sort state in the component
- Which migration source (dump.sql, WP REST, MariaDB direct), which idempotency key, and how would it scale to 100x? -> manage.py command reading MariaDB directly, upsert keyed on WP post ID
- Which source becomes a brand's short description? Research: all 5 brands in db/dump.sql have an empty excerpt and no short_description postmeta, content is three HTML paragraphs. Candidates: first paragraph of content, or first N characters of stripped content. To confirm with user. -> First N characters of the stripped content, N set to 200 and cut at a word boundary, stored as an editable field on brand
- Is the average rating stored, derived or both, and are reviewers Django users, a Reviewer model or denormalized strings? -> Average derived by aggregate, separate Reviewer model
- Which postmeta fields become model fields, JSON or are dropped? -> ACF fields as columns, Yoast as JSON, WP-internal keys dropped
- What does top review mean (highest rating, most recent, longest, other)? -> Highest rating, ties broken by newest, snippet is the first 140 characters of the body
- Which pagination shape and which filter and sort parameter names, and is the industry filter single or multi select? -> page and page_size, envelope count next previous results, repeatable industry slug filter, ordering param
- Which role names exist, which WP users become editors, and how are tokens revoked or roles changed before expiry? -> reader and editor, WP administrator and editor map to editor, 15-minute tokens, no refresh token, role changes apply at the next login
- How is the shared library installed into both images, how is it pinned, and how is a breaking change released without a simultaneous deploy? -> Path install from repo root, exact version pin per service, expand and contract releases
- Which SCSS toolchain, partial layout and token naming, and how does a second engineer add a component? -> Dart Sass with flat partials by page section
- How does the main app obtain the RS256 public key (mounted file or JWKS endpoint) and how are keys rotated? -> Public key in an environment variable, rotated by redeploying with the new key
- What is the call date, and which requirements drop first if time runs short? -> Call date unknown, cut order R20 first, then R12 polish, then R11, then R9
- Where does the code that reads the WP database live: each service owns its own queries and only the upsert-by-WP-ID pattern is shared, or the shared library holds a WP reader? -> Each service owns its own WP queries, only the upsert by WP ID pattern is a shared convention and the library gets no WP reader

## Unvalidated assumptions (flag if they break)
- A1 db/dump.sql loads cleanly through docker compose and exposes brands, reviews, industries and users
- A5 One import flow can populate both services without a separate auth-side importer being specified
- A7 Both services can reach the WP database on the compose network
- A8 Framework defaults for ordering are enough, no explicit default order, tie-break or null placement is needed
- A9 The serializer defaults for row field types and rounding are acceptable and a published schema is not needed
- A10 The behaviour of multiple industry slugs and of an unknown slug can stay undefined
- A11 An uncapped page_size and the framework default beyond the last page are acceptable
- A12 The brand listing will not issue a query per row
- A13 Filter and sort state in the component without URL sync is acceptable
- A14 Framework default error bodies and 401 headers are consistent enough
- A15 The cut order in T20 is enough without changing priorities, R9 and R11 can stay P0
- A16 A headless browser container for visual checks fits the Docker-only constraint at demo scale
- A17 An injectable clock in the library core is cheap to add and test
- A18 Logging in every imported user is cheap to test
