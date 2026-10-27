# ca-code-challenge: Spec

<!-- Source of truth. Change only with `mkit apply` or /mkit:change. IDs are stable: never renumbered or reused. -->

## Constraints

<!-- C: a limit on the solution. Fields: Kind (constraint|preference), Source, Real (real|inherited|unknown). -->

### C1. Whole stack runs through docker compose, Docker is the only host prerequisite
- Kind: constraint
- Source: brief §Setup
- Real: real

### C2. Migration must be re-runnable without producing duplicates
- Kind: constraint
- Source: brief §Pillar 1
- Real: real

### C3. Server-rendered URL slugs must match WP permalinks
- Kind: constraint
- Source: brief §Pillar 1
- Real: real

### C4. Main app stores no passwords or roles
- Kind: constraint
- Source: brief §Pillar 5
- Real: real

### C5. Auth service is a separate Django project in its own container with its own database
- Kind: constraint
- Source: brief §Pillar 5
- Real: real

### C6. GET /api/brands/ and the server-rendered pages stay public
- Kind: constraint
- Source: brief §Pillar 5
- Real: real

### C7. Shared library has its own pyproject.toml, is versioned, has tests that run without either Django project, and holds only code both services use
- Kind: constraint
- Source: brief §Pillar 6
- Real: real

### C8. Shared library lives in its own directory of this repo
- Kind: preference
- Source: user choice, brief allows own directory or own repository
- Real: real

### C9. All six pillars are required, prioritise within them rather than cutting one
- Kind: constraint
- Source: user, brief §What to deliver
- Real: real

### C10. Call date is the cutoff, no fixed deadline, the date itself is not yet known
- Kind: constraint
- Source: user, brief §How the evaluation works
- Real: unknown

### C11. reference/theme.css is not edited, SCSS must compile to structurally equivalent CSS
- Kind: constraint
- Source: brief §Pillar 4 and theme.css header
- Real: real

### C12. Every submitted piece must be explainable and defensible by the candidate
- Kind: constraint
- Source: brief §How the evaluation works
- Real: real

### C13. Built for dev and demo as a take-home, not for production deployment
- Kind: constraint
- Source: user, answer to the target environment question
- Real: real

## Assumptions

<!-- A: something we believe but have not verified. Fields: Status (unvalidated|validated|invalid), Test (how we'd know we're wrong). -->

### A1. db/dump.sql loads cleanly through docker compose and exposes brands, reviews, industries and users
- Status: unvalidated
- Test: fresh docker compose up then SQL counts on wp_posts by post_type, wp_term_taxonomy and wp_users are non-zero and match the REST API totals

### A2. Every review links to exactly one existing brand
- Status: validated
- Test: SQL check that each review post has a brand postmeta value pointing to an existing brand post, zero orphans and zero duplicates

### A3. Each brand has at most one industry term
- Status: validated
- Test: SQL count of wp_term_relationships per brand, any brand with more than one term proves it wrong and the API industry field must become a list

### A4. WP user roles can be read from wp_usermeta wp_capabilities
- Status: validated
- Test: SQL on wp_usermeta for wp_capabilities shows an administrator or editor row for at least one user and a lower role for another

### A5. One import flow can populate both services without a separate auth-side importer being specified
- Status: unvalidated
- Test: from a clean compose, run the documented migration then compare auth user count to wp_users and confirm the main app has no user table

### A6. Reviews do not need a link from the main app to an auth account
- Status: invalid
- Test: SQL check whether review post_author differs from reviewer_name, if authors are distinct wp_users a wp_user_id link is needed

### A7. Both services can reach the WP database on the compose network
- Status: unvalidated
- Test: docker compose exec from the main app and the auth container connecting to the db service

### A8. Framework defaults for ordering are enough, no explicit default order, tie-break or null placement is needed
- Status: unvalidated
- Test: request every page with ordering by average rating on the seeded brands and assert the pages together contain each brand exactly once, then repeat with a brand that has no reviews

### A9. The serializer defaults for row field types and rounding are acceptable and a published schema is not needed
- Status: unvalidated
- Test: a contract test over GET /api/brands/ asserting each field type, including a brand with no reviews

### A10. The behaviour of multiple industry slugs and of an unknown slug can stay undefined
- Status: unvalidated
- Test: request with two valid slugs and with one unknown slug, and check the result is sensible and documented

### A11. An uncapped page_size and the framework default beyond the last page are acceptable
- Status: unvalidated
- Test: request page_size=100000 and a page past the end and check the response time and status

### A12. The brand listing will not issue a query per row
- Status: validated
- Test: count queries for page_size 5 and 50 and assert they are equal

### A13. Filter and sort state in the component without URL sync is acceptable
- Status: unvalidated
- Test: select a filter, reload and copy the link, then check whether the brief's URL-synced state question can be answered without it

### A14. Framework default error bodies and 401 headers are consistent enough
- Status: unvalidated
- Test: curl a 401, a 403, a 404 and a 422 from the API and compare body shapes and headers

### A15. The cut order in T20 is enough without changing priorities, R9 and R11 can stay P0
- Status: unvalidated
- Test: when behind schedule apply the T20 order and check each pillar's core path still works

### A16. A headless browser container for visual checks fits the Docker-only constraint at demo scale
- Status: unvalidated
- Test: add the container and run the 375px and 1280px checks through docker compose, if it takes more than one service and one script fall back to committed screenshots

### A17. An injectable clock in the library core is cheap to add and test
- Status: unvalidated
- Test: implement token verification with a clock parameter, if it needs more than a few lines switch to a short token lifetime from an env var

### A18. Logging in every imported user is cheap to test
- Status: unvalidated
- Test: loop over all 9 imported users in one test with the dev password and confirm the run stays fast

## Requirements

<!-- R: a capability a user or caller can exercise. Fields: Priority P0-P2, Status, Source, Acceptance (observable bullets). -->

### R1. Whole stack boots from a clean clone
- Priority: P0
- Status: active
- Acceptance:
  - after cp .env.example .env and docker compose up -d every service (WP, db, main app, auth service, auth db) reaches running or healthy in docker compose ps
  - no host tool other than Docker is needed to build the bundle, compile SCSS or run any test suite
  - docs list the service URLs
- Source: brief §Setup, §What to deliver

### R2. Clean relational domain model for brands, reviews, industries and reviewer users
- Priority: P0
- Status: active
- Acceptance:
  - Django migrations create tables for brand, review, industry and reviewer data with foreign keys from review to brand and brand to industry
  - no table stores generic key and value postmeta rows
  - Yoast keys are kept as one JSON field on brand
  - makemigrations --check reports no pending changes
  - a reviewer row carries a nullable wp_user_id with no foreign key across databases
  - after the migration each of the 8 reviewers in the dump has the wp_user_id of its WP author and the review counts per reviewer match the dump
- Source: brief §Pillar 1

### R3. Re-runnable WP content migration command in the main app
- Priority: P0
- Status: active
- Acceptance:
  - one documented main app command imports brands, reviews, industries and reviewers from the WP source and never creates accounts, passwords or roles
  - Django row counts equal the WP published counts after the first run
  - a second consecutive run creates no new rows and reports created, updated and unchanged counts
  - the command works inside docker compose
- Source: brief §Pillar 1

### R4. Server-rendered homepage, brand detail and review detail pages
- Priority: P0
- Status: active
- Acceptance:
  - GET / returns 200 HTML containing a hero and the most recent reviews with JavaScript disabled
  - for every WP brand slug GET /brand/<slug>/ returns 200 and shows name, rating and its reviews
  - for every WP review slug GET /review/<slug>/ returns 200
  - an unknown slug returns 404
  - the set of Django slugs equals the set of WP permalinks
  - Visual: at 375px the pages show one column with no horizontal scroll
  - Visual: at 1280px content is centred within the 1100px container
  - the brand detail page shows short_description
- Source: brief §Pillar 1
- Built: 2026-10-27

### R5. Brand listing endpoint returns card-ready rows
- Priority: P0
- Status: active
- Acceptance:
  - GET /api/brands/ with no token returns 200 JSON
  - every row has name, slug, industry, average rating, review count, short description and top review snippet
  - row values equal what the brand detail page shows
  - if A3 is proven wrong the industry field is returned as a list named industries
  - industry is the name string or null
  - the top review snippet strips tags and collapses whitespace, then keeps the first 24 whole words and appends an ellipsis only when words were dropped, matching wp_trim_words on the WordPress theme
- Source: brief §Pillar 2
- Built: 2026-10-27

### R6. Brand listing is filterable, sortable and paginated
- Priority: P0
- Status: active
- Acceptance:
  - filtering by an industry returns only brands in that industry
  - sorting by average rating and by review count each return rows in the requested order in both directions
  - results are paginated with a documented page size and a request beyond the last page returns a defined response
  - page_size defaults to 10 and is uncapped
  - ties by name then id
  - nulls last for rating
  - a past-end page returns 200 with empty results
  - several industry slugs are OR-ed and an unknown slug matches nothing
  - invalid ordering or page returns 422
  - the listing runs a constant number of queries regardless of how many brands exist, asserted in a test
- Source: brief §Pillar 2
- Built: 2026-10-27

### R7. Top review snippet is defined and documented
- Priority: P0
- Status: active
- Acceptance:
  - the README states what top means
  - for each seeded brand the snippet returned equals the review the definition selects
  - a brand with no reviews returns a defined empty value rather than an error
- Source: brief §Pillar 2

### R8. BrandList consumes the API with industry filter and sort control
- Priority: P0
- Status: active
- Acceptance:
  - <BrandList /> renders on a server-rendered Django page
  - choosing an industry sends a request with the filter and the cards update
  - changing the sort control sends a request with the sort and the card order changes
  - initial render shows the brands returned by GET /api/brands/
  - the card's industry badge uses the same markup as the WordPress brand archive card (wrapped in its own element) and is sized to its text, not stretched across the card
  - the industry and sort controls stay native selects, restyled with project tokens (custom arrow, 44px minimum height, visible labels)
  - the selected industry and ordering are kept in the page URL query string and are restored on reload and when the link is shared
  - the component lets the user reach every brand beyond the first page (pagination controls) and shows how many brands exist
  - the URL query string uses history.replaceState, so URL changes add no Back-button entries
  - the params are industry, ordering and page, named as in the API
  - PAGE_SIZE 10 is sent explicitly
  - a shared link past the last page resets to page 1
  - unknown URL values fall back to defaults
- Source: brief §Pillar 3, user choice mounted on a Django page
- Built: 2026-10-27

### R9. BrandList handles loading, empty and error states
- Priority: P0
- Status: active
- Acceptance:
  - while the request is pending a loading indicator is visible when the network is throttled
  - a filter that matches nothing shows an empty message
  - a 500 response shows an error message with a retry action
  - Visual: loading, empty and error states each render at 375px and 1280px without layout breaks
- Source: brief §Pillar 3

### R10. BrandList is keyboard accessible and semantic
- Priority: P0
- Status: active
- Acceptance:
  - every control is reachable with Tab and operable with Enter, Space or arrows in a logical order
  - focus is visible on every control
  - the list uses list markup and each control has a programmatic label
  - an axe check run in the Node container component test reports zero violations
  - Visual: focus ring visible on filter, sort and cards at 1280px checked from a screenshot taken by a headless browser container
  - cards are li elements
  - focus is a 3px blue outline
  - colour contrast is checked in the browser container, not jsdom
- Source: brief §Pillar 3
- Built: 2026-10-27

### R11. BrandList is responsive
- Priority: P0
- Status: active
- Acceptance:
  - Visual: at 375px cards stack in one column, controls fit the width and there is no horizontal scroll
  - Visual: at 1280px cards use a multi-column layout within the container
  - touch targets for controls are at least 44px at 375px
- Source: brief §Pillar 3

### R12. SCSS source tree compiles to equivalent CSS
- Priority: P0
- Status: active
- Acceptance:
  - SCSS under frontend/scss/ compiles through a documented docker command with no errors
  - every custom property in the :root block of reference/theme.css is defined in a tokens partial
  - each commented section of reference/theme.css maps to a partial
  - the tree has an entry file and partials split by tokens, base, layout and components
  - the README explains how to compile
  - no component CSS outside frontend/scss
  - the temporary brandlist.css is folded into the SCSS tree
- Source: brief §Pillar 4
- Built: 2026-10-27

### R13. Auth service owns users and its own re-runnable import creates them from wp_users
- Priority: P0
- Status: active
- Acceptance:
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
- Source: brief §Pillar 5, user choice reset passwords
- Built: 2026-10-27

### R14. Login exchanges credentials for a token
- Priority: P0
- Status: active
- Acceptance:
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
- Source: brief §Pillar 5
- Built: 2026-10-27

### R15. Auth service is the source of truth for at least two roles
- Priority: P0
- Status: active
- Acceptance:
  - at least two roles exist and each seeded user has one
  - a freshly issued reader token carries the reader role and an editor token carries the editor role
  - after a role is changed in the auth service an old token keeps its old role until it expires, shown in a test with an injectable clock
  - a fresh login after the change carries the new role
  - editor satisfies a reader requirement
- Source: brief §Pillar 5
- Built: 2026-10-27

### R16. Editor-only brand write endpoint in the main app
- Priority: P0
- Status: active
- Acceptance:
  - PATCH /api/brands/<slug>/ with no token returns 401
  - with a reader token returns 403
  - with an editor token returns 200 and the response body is the updated brand row
  - the new short description appears in GET /api/brands/ and /brand/<slug>/
  - the body accepts only short_description as plain text of 1 to 500 characters
  - any other field in the body, including slug and name, returns 422 and changes nothing
  - an invalid or expired token returns 401
  - checks run in the order 401, 403, 404 so an unknown slug does not leak to anonymous callers
  - GET /api/brands/ and the pages still return 200 without a token
  - short_description accepts up to 500 characters
  - whitespace is stripped before the 1-500 length check
  - the response is the full brand row
- Source: brief §Pillar 5
- Built: 2026-10-27

### R17. Token verification approach and auth outage behaviour are decided and documented
- Priority: P0
- Status: active
- Acceptance:
  - the README states whether the main app verifies tokens locally or calls the auth service and why
  - with the auth container stopped, public GET requests still return 200 and PATCH behaves exactly as documented
  - the README states how a token is revoked or a role changed before expiry
  - verification rejects tokens where exp - iat is not 900 or iat or exp is not an integer
- Source: brief §Pillar 5
- Built: 2026-10-27

### R18. Shared library is an installable package used by both services
- Priority: P0
- Status: active
- Acceptance:
  - the package has its own pyproject.toml with a name and version
  - pip show inside the main app container and the auth container lists it with that version
  - the main app protected endpoint imports its auth and permission code from the library with no copy in the app
- Source: brief §Pillar 6
- Built: 2026-10-27

### R19. Library has a framework-free core, tests run without Django and the library stays small
- Priority: P0
- Status: active
- Acceptance:
  - the documented test command passes in an environment where Django and Ninja are not installed
  - the core verifies a token, checks a role and defines the shared claim names
  - the main app imports the core and the auth service imports the claim names from it
  - the Ninja auth class lives in the main app as a thin adapter over the core
  - the README gives a one-line justification for every module
- Source: brief §Pillar 6

### R20. Tests cover migration idempotency, API behaviour and auth protection
- Priority: P1
- Status: active
- Acceptance:
  - the documented docker command runs the suite and it passes
  - a test runs the migration twice and asserts equal row counts
  - API tests cover filter, both sorts and pagination
  - auth tests cover the 401, 403 and 200 cases of the PATCH endpoint
- Source: user choice

### R21. README documents how to run, authenticate, test the library and migrate
- Priority: P0
- Status: active
- Acceptance:
  - README sections exist for running the main app, the auth service and the React component
  - getting a token and calling the protected endpoint with copy-pasteable commands
  - running the library tests and how a new version reaches each service
  - running the migration and re-running it safely
  - following the commands from a clean clone works
- Source: brief §What to deliver

### R22. README records modeling decisions, what to do differently and AI defaults accepted
- Priority: P0
- Status: active
- Acceptance:
  - a README section of about half a page covers modeling decisions
  - the same section lists what would be done differently with more time
  - the same section lists each place the AI default was kept over own preference and why
  - the candidate confirms the README section before submission
- Source: brief §What to deliver

## Out of scope

<!-- O: decided against, with Why and Revisit (what would change our mind). Dropped, not deferred. -->

### O1. Migrating the WP admin and editor experience
- Why: brief excludes it
- Revisit: never for this challenge

### O2. Yoast SEO frontend output
- Why: brief excludes it, the data is kept as JSON on brand only
- Revisit: if the live session asks for SEO meta tags

### O3. WP plugin parity beyond data structure
- Why: brief excludes it
- Revisit: never for this challenge

### O4. User-facing review submission and search
- Why: brief excludes it
- Revisit: if the live session adds it as the new requirement

### O5. Registration, password reset, social login, MFA
- Why: brief says login plus role-based access is enough
- Revisit: if the live session adds it as the new requirement

### O6. A login UI
- Why: brief says curl or the DRF browsable API is fine
- Revisit: if the live session asks for it

### O7. Image uploads and real logos
- Why: brief says placeholder boxes are fine
- Revisit: if the live session asks for it

### O8. Pixel-matching the WP theme
- Why: brief grades structure, not identical output
- Revisit: never for this challenge

### O9. Archive pages and industry taxonomy pages
- Why: user decided to build only the three required pages
- Revisit: if the live session needs a browsable industry page

## Open questions

<!-- Q: unanswered blocks `ready`. Answer with ANSWER; "you decide" is recorded as By: delegated. -->

### Q1. Where is BrandList rendered?
- Answer: Mounted on a Django page
- Decided by: you

### Q2. Is Yoast SEO data carried across?
- Answer: Kept as JSON on the brand model, not rendered
- Decided by: you

### Q3. Which tests are in scope beyond the library tests?
- Answer: Library tests plus migration idempotency, API and auth tests
- Decided by: you

### Q4. Are archive and taxonomy pages built?
- Answer: No, only homepage, brand detail and review detail
- Decided by: you

### Q5. What happens to wp_users passwords in the auth service?
- Answer: Reset to a documented dev password
- Decided by: you

### Q6. Which Python and Django versions and which API stack (DRF, Django Ninja or plain views)?
- Answer: Python 3.12, Django 5.2 LTS, Django Ninja
- Decided by: you

### Q7. Which database engine for the main app and for the auth service?
- Answer: PostgreSQL for both, separate containers
- Decided by: you

### Q8. Which token format and signing, and does the main app verify locally or call the auth service, and what happens when it is down?
- Answer: RS256 JWT, main app verifies locally with the public key, revocation through short expiry
- Decided by: you

### Q9. Which React build tooling, language (TypeScript or JavaScript), CSS approach and way of serving the bundle, and where does filter and sort state live including URL sync?
- Answer: Vite with JavaScript, styled with the project SCSS, filter and sort state in the component
- Decided by: you

### Q10. Which migration source (dump.sql, WP REST, MariaDB direct), which idempotency key, and how would it scale to 100x?
- Answer: manage.py command reading MariaDB directly, upsert keyed on WP post ID; at 100x, chunked bulk upserts committing per batch
- Decided by: you
- Why: By: delegated, the README only said 100x needs batching

### Q11. Which source becomes a brand's short description? Research: all 5 brands in db/dump.sql have an empty excerpt and no short_description postmeta, content is three HTML paragraphs. Candidates: first paragraph of content, or first N characters of stripped content. To confirm with user.
- Answer: First N characters of the stripped content, N set to 200 and cut at a word boundary, stored as an editable field on brand
- Decided by: you

### Q12. Is the average rating stored, derived or both, and are reviewers Django users, a Reviewer model or denormalized strings?
- Answer: Average derived by aggregate, separate Reviewer model
- Decided by: you

### Q13. Which postmeta fields become model fields, JSON or are dropped?
- Answer: ACF fields as columns, Yoast as JSON, WP-internal keys dropped
- Decided by: you

### Q14. What does top review mean (highest rating, most recent, longest, other)?
- Answer: Highest rating, ties broken by newest, snippet is the first 140 characters of the body
- Decided by: you

### Q15. Which pagination shape and which filter and sort parameter names, and is the industry filter single or multi select?
- Answer: page and page_size, envelope count next previous results, repeatable industry slug filter, ordering param
- Decided by: you

### Q16. Which role names exist, which WP users become editors, and how are tokens revoked or roles changed before expiry?
- Answer: reader and editor, WP administrator and editor map to editor, 15-minute tokens, no refresh token, role changes apply at the next login
- Decided by: you

### Q17. How is the shared library installed into both images, how is it pinned, and how is a breaking change released without a simultaneous deploy?
- Answer: Path install from repo root, exact version pin per service, expand and contract releases
- Decided by: you

### Q18. Which SCSS toolchain, partial layout and token naming, and how does a second engineer add a component?
- Answer: Dart Sass with flat partials by page section
- Decided by: you

### Q19. How does the main app obtain the RS256 public key (mounted file or JWKS endpoint) and how are keys rotated?
- Answer: Public key in an environment variable, rotated by redeploying with the new key
- Decided by: you

### Q20. What is the call date, and which requirements drop first if time runs short?
- Answer: Call date unknown, cut order R20 first, then R12 polish, then R11, then R9
- Decided by: you

### Q21. Where does the code that reads the WP database live: each service owns its own queries and only the upsert-by-WP-ID pattern is shared, or the shared library holds a WP reader?
- Answer: Each service owns its own WP queries, only the upsert by WP ID pattern is a shared convention and the library gets no WP reader
- Decided by: you

## Technology

<!-- T: a technology choice. Fields: Choice, Why, Alternative. -->

### T1. WordPress source
- Owns: original content in MariaDB, read-only migration source
- Calls: none
- When down: migration cannot run, the Django site is unaffected

### T2. Main Django app
- Owns: brand, review, industry and reviewer data, server-rendered pages, GET /api/brands/ and the editor-only PATCH
- Calls: token verification through the shared library, remote call to the auth service only if Q8 chooses it
- When down: pages and API are unavailable

### T3. Auth service
- Owns: users, passwords, roles, token issue and its own database
- Calls: none
- When down: login fails, public reads keep working, PATCH behaves as decided in Q8

### T4. Shared Python library
- Owns: token verification, permission checks and shared claim names used by both services
- Calls: none, pure code testable without Django
- When down: not a runtime service

### T5. BrandList component in the browser
- Owns: filter and sort UI state
- Calls: GET /api/brands/
- When down: shows its error state with retry

### T6. Backend framework
- Choice: Python 3.12, Django 5.2 LTS, Django Ninja
- Why: user choice, typed schemas for the brand API
- Alternative: DRF, plain JSON views

### T7. Databases
- Choice: PostgreSQL for the main app and for the auth service in separate containers
- Why: JSON field for Yoast data and unambiguous own database for auth
- Alternative: MariaDB, SQLite for auth

### T8. Token and verification
- Choice: RS256 JWT, main app verifies locally with the public key, short expiry for revocation
- Why: PATCH keeps working when auth is down and the main app cannot forge tokens
- Alternative: opaque token with introspection, HS256 JWT

### T9. Frontend stack
- Choice: Vite, JavaScript, project SCSS, state in the component
- Why: user choice, reuses the SCSS pillar tokens
- Alternative: TypeScript, CSS modules

### T10. Migration
- Choice: manage.py command reading MariaDB directly, upsert on WP post ID
- Why: no dependency on WP running, batched upserts scale to 100x
- Alternative: WP REST API, parse dump.sql

### T11. Rating and reviewer modelling
- Choice: average derived by aggregate, separate Reviewer model
- Why: user choice, never stale and the main app owns no accounts. Dump check: stored average_rating differs from the mean of the reviews for 4 of 5 brands (brand 11 stores 4.4 but its reviews average 3.67) and the sort order differs, so sorting must use the derived value
- Alternative: stored average, denormalised strings

### T12. Postmeta mapping
- Choice: ACF fields as columns, Yoast keys as one JSON field, WP-internal keys dropped
- Why: keeps the schema clean without losing SEO data
- Alternative: all non-ACF meta as JSON

### T13. Top review definition
- Choice: highest rating, ties broken by newest, snippet is the first 140 characters
- Why: deterministic and easy to test
- Alternative: most recent, lowest rating

### T14. API contract
- Choice: page and page_size, envelope count next previous results, repeatable industry slug, ordering param
- Why: mobile clients follow next links
- Alternative: limit and offset, cursor

### T15. Roles and revocation
- Choice: reader and editor, WP administrator and editor become editor, 15-minute tokens, no refresh token and no refresh endpoint, role changes apply at the next login
- Why: local verification with a documented revocation trade-off and no extra endpoint to build
- Alternative: main app denylist, three roles

### T16. Library distribution
- Choice: path install from repo root, exact version pin per service, expand and contract releases
- Why: runs offline in Docker and allows staged upgrades
- Alternative: git URL tags, private index

### T17. SCSS toolchain
- Choice: Dart Sass with flat partials by page section
- Why: user choice, mirrors the sections of theme.css
- Alternative: 7-1 layered partials, custom properties only

### T18. Short description source
- Choice: first 200 characters of HTML-stripped content cut at a word boundary, stored as an editable brand field
- Why: all 5 brands have an empty WP excerpt and no short_description meta
- Alternative: first paragraph of content

### T19. Public key distribution
- Choice: RS256 public key supplied to the main app as an environment variable, rotated by redeploy
- Why: no runtime dependency on the auth service
- Alternative: mounted PEM file, JWKS endpoint

### T20. Cut order
- Choice: R20, then R12 polish, then R11, then R9, core path of every pillar stays
- Why: call date is unknown
- Alternative: drop R20 then R10

### T21. WP reader location
- Choice: a module in the shared library with an injected connection, each service does its own upserts
- Why: user choice, one place for WP schema knowledge
- Alternative: each service owns its queries, separate migration tool
- Status: removed (2026-10-27, Q21 shared WP reader choice undone at user request, being re-asked)

### T22. WP reader location
- Choice: each service owns its own WP queries, main app reads posts, meta and terms, auth service reads wp_users and capabilities
- Why: keeps the library small, Django-free and free of a database driver
- Alternative: WP reader module in the shared library, separate migration tool

## Deliverables trace

| Brief bullet | Covered by |
|---|---|
| Models that mirror the domain: brands, reviews, industries, reviewer users | R2 |
| A data migration step that pulls the WP content into your Django DB | R3 |
| Server-rendered pages at minimum for: homepage (hero + recent reviews), brand detail at /brand/<slug>/, and review detail at /review/<slug>/ | R4 |
| GET /api/brands/ | R5 |
| Filterable by industry. | R6 |
| Sortable by average rating and by review count. | R6 |
| Paginated. | R6 |
| Returns enough data per row to render a card: name, slug, industry, average rating, review count, short description, and the top review snippet | R5, R7 |
| Consumes the endpoint from Pillar 2. | R8 |
| Industry filter (single or multi-select, your call). | R8 |
| Sort control. | R8 |
| Loading, empty, and error states all handled. | R9 |
| Keyboard accessible; semantic markup; meets basic a11y expectations. | R10 |
| Responsive across mobile and desktop. | R11 |
| Place your SCSS under frontend/scss/ and include a brief README note on how to compile it | R12, R21 |
| Users are owned by the auth service. The wp_users accounts must exist there after migration | R13 |
| Login: an endpoint that exchanges credentials for a token | R14 |
| Authorization: at least two roles, the auth service is the source of truth | R15 |
| Protected endpoint in the main app: one write endpoint that only editor can call | R16 |
| Decide whether the main app verifies tokens locally or calls the auth service on every request, and document why | R17 |
| Its own pyproject.toml, versioned, installed into both services | R18 |
| At minimum it holds the token verification and permission-check code the main app uses | R18 |
| Has its own tests that run without either Django project. | R19 |
| Keep it small. Only code that both services actually use belongs there | R19 |
| The Django project. | R2, R4, R5 |
| The migration command/script. | R3 |
| The React BrandList component. | R8 |
| The SCSS source tree under frontend/scss/. | R12 |
| The auth service as a separate Django project, wired into docker-compose.yml. | R13, R1 |
| The shared Python library as a separate package with its tests. | R18, R19 |
| A README.md with: | R21, R22 |
| How to run the Django app, the auth service, and the React component locally. | R21 |
| How to get a token and call the protected endpoint. | R21 |
| How to run the shared library's tests and how a new version reaches each service. | R21 |
| How to run the migration (and how to re-run it safely). | R21 |
| A short section on modeling decisions, what you would do differently, and AI defaults chosen over your preference | R22 |
| Migrating the WP admin / editor experience. | O1 |
| Yoast SEO frontend output | O2 |
| WP plugin parity beyond data structure. | O3 |
| User-facing review submission, search. | O4 |
| Registration, password reset, social login, MFA. | O5 |
| A login UI. | O6 |
| Image uploads | O7 |
| Pixel-matching the WP theme. | O8 |
| Schema modeling: store or derive average_rating, how reviewer users are modeled | Q12 |
| Postmeta strategy: which fields became model fields, JSON, or dropped | Q13 |
| Migration approach: why, safe re-run, scaling to 100x | Q10, R3 |
| API contract: pagination shape, filter/sort param names, mobile client | Q15 |
| Component and state: where BrandList state lives, URL-synced filter/sort, loading/error UX | Q9, R9 |
| SCSS architecture: partials, tokens, how a second engineer adds a component | Q18, R12 |
| Service boundary: ownership, token validation, auth outage, revocation | Q8, Q16, R17 |
| Shared library: what went in and out, pinning and upgrading, breaking change release | Q17, R19 |

## Changelog

| Date | Change | By |
|---|---|---|
| 2026-10-27 | Initial spec | mkit |
| 2026-10-27 | ADD C1: Whole stack runs through docker compose, Docker is the only host prerequisite | mkit |
| 2026-10-27 | ADD C2: Migration must be re-runnable without producing duplicates | mkit |
| 2026-10-27 | ADD C3: Server-rendered URL slugs must match WP permalinks | mkit |
| 2026-10-27 | ADD C4: Main app stores no passwords or roles | mkit |
| 2026-10-27 | ADD C5: Auth service is a separate Django project in its own container with its own database | mkit |
| 2026-10-27 | ADD C6: GET /api/brands/ and the server-rendered pages stay public | mkit |
| 2026-10-27 | ADD C7: Shared library has its own pyproject.toml, is versioned, has tests that run without either Django project, and holds only code both services use | mkit |
| 2026-10-27 | ADD C8: Shared library lives in its own directory of this repo | mkit |
| 2026-10-27 | ADD C9: All six pillars are required, prioritise within them rather than cutting one | mkit |
| 2026-10-27 | ADD C10: Call date is the cutoff, no fixed deadline, the date itself is not yet known | mkit |
| 2026-10-27 | ADD C11: reference/theme.css is not edited, SCSS must compile to structurally equivalent CSS | mkit |
| 2026-10-27 | ADD C12: Every submitted piece must be explainable and defensible by the candidate | mkit |
| 2026-10-27 | ADD A1: db/dump.sql loads cleanly through docker compose and exposes brands, reviews, industries and users | mkit |
| 2026-10-27 | ADD A2: Every review links to exactly one existing brand | mkit |
| 2026-10-27 | ADD A3: Each brand has at most one industry term | mkit |
| 2026-10-27 | ADD R1: Whole stack boots from a clean clone | mkit |
| 2026-10-27 | ADD R2: Clean relational domain model for brands, reviews, industries and reviewer users | mkit |
| 2026-10-27 | ADD R3: Re-runnable WP content migration command | mkit |
| 2026-10-27 | ADD R4: Server-rendered homepage, brand detail and review detail pages | mkit |
| 2026-10-27 | ADD R5: Brand listing endpoint returns card-ready rows | mkit |
| 2026-10-27 | ADD R6: Brand listing is filterable, sortable and paginated | mkit |
| 2026-10-27 | ADD R7: Top review snippet is defined and documented | mkit |
| 2026-10-27 | ADD R8: BrandList consumes the API with industry filter and sort control | mkit |
| 2026-10-27 | ADD R9: BrandList handles loading, empty and error states | mkit |
| 2026-10-27 | ADD R10: BrandList is keyboard accessible and semantic | mkit |
| 2026-10-27 | ADD R11: BrandList is responsive | mkit |
| 2026-10-27 | ADD R12: SCSS source tree compiles to equivalent CSS | mkit |
| 2026-10-27 | ADD R13: Auth service owns users and the WP users exist there | mkit |
| 2026-10-27 | ADD R14: Login exchanges credentials for a token | mkit |
| 2026-10-27 | ADD R15: Auth service is the source of truth for at least two roles | mkit |
| 2026-10-27 | ADD R16: Editor-only brand write endpoint in the main app | mkit |
| 2026-10-27 | ADD R17: Token verification approach and auth outage behaviour are decided and documented | mkit |
| 2026-10-27 | ADD R18: Shared library is an installable package used by both services | mkit |
| 2026-10-27 | ADD R19: Library tests run without Django and the library stays small | mkit |
| 2026-10-27 | ADD R20: Tests cover migration idempotency, API behaviour and auth protection | mkit |
| 2026-10-27 | ADD R21: README documents how to run, authenticate, test the library and migrate | mkit |
| 2026-10-27 | ADD R22: README records modeling decisions, what to do differently and AI defaults accepted | mkit |
| 2026-10-27 | ADD O1: Migrating the WP admin and editor experience | mkit |
| 2026-10-27 | ADD O2: Yoast SEO frontend output | mkit |
| 2026-10-27 | ADD O3: WP plugin parity beyond data structure | mkit |
| 2026-10-27 | ADD O4: User-facing review submission and search | mkit |
| 2026-10-27 | ADD O5: Registration, password reset, social login, MFA | mkit |
| 2026-10-27 | ADD O6: A login UI | mkit |
| 2026-10-27 | ADD O7: Image uploads and real logos | mkit |
| 2026-10-27 | ADD O8: Pixel-matching the WP theme | mkit |
| 2026-10-27 | ADD O9: Archive pages and industry taxonomy pages | mkit |
| 2026-10-27 | ADD Q1: Where is BrandList rendered? | mkit |
| 2026-10-27 | ADD Q2: Is Yoast SEO data carried across? | mkit |
| 2026-10-27 | ADD Q3: Which tests are in scope beyond the library tests? | mkit |
| 2026-10-27 | ADD Q4: Are archive and taxonomy pages built? | mkit |
| 2026-10-27 | ADD Q5: What happens to wp_users passwords in the auth service? | mkit |
| 2026-10-27 | ADD Q6: Which Python and Django versions and which API stack (DRF, Django Ninja or plain views)? | mkit |
| 2026-10-27 | ADD Q7: Which database engine for the main app and for the auth service? | mkit |
| 2026-10-27 | ADD Q8: Which token format and signing, and does the main app verify locally or call the auth service, and what happens when it is down? | mkit |
| 2026-10-27 | ADD Q9: Which React build tooling, language (TypeScript or JavaScript), CSS approach and way of serving the bundle, and where does filter and sort state live including URL sync? | mkit |
| 2026-10-27 | ADD Q10: Which migration source (dump.sql, WP REST, MariaDB direct), which idempotency key, and how would it scale to 100x? | mkit |
| 2026-10-27 | ADD Q11: Which source becomes a brand's short description (excerpt, content or a new field)? | mkit |
| 2026-10-27 | ADD Q12: Is the average rating stored, derived or both, and are reviewers Django users, a Reviewer model or denormalized strings? | mkit |
| 2026-10-27 | ADD Q13: Which postmeta fields become model fields, JSON or are dropped? | mkit |
| 2026-10-27 | ADD Q14: What does top review mean (highest rating, most recent, longest, other)? | mkit |
| 2026-10-27 | ADD Q15: Which pagination shape and which filter and sort parameter names, and is the industry filter single or multi select? | mkit |
| 2026-10-27 | ADD Q16: Which role names exist, which WP users become editors, and how are tokens revoked or roles changed before expiry? | mkit |
| 2026-10-27 | ADD Q17: How is the shared library installed into both images, how is it pinned, and how is a breaking change released without a simultaneous deploy? | mkit |
| 2026-10-27 | ADD Q18: Which SCSS toolchain, partial layout and token naming, and how does a second engineer add a component? | mkit |
| 2026-10-27 | ANSWER Q1 | mkit |
| 2026-10-27 | ANSWER Q2 | mkit |
| 2026-10-27 | ANSWER Q3 | mkit |
| 2026-10-27 | ANSWER Q4 | mkit |
| 2026-10-27 | ANSWER Q5 | mkit |
| 2026-10-27 | ADD T1: WordPress source | mkit |
| 2026-10-27 | ADD T2: Main Django app | mkit |
| 2026-10-27 | ADD T3: Auth service | mkit |
| 2026-10-27 | ADD T4: Shared Python library | mkit |
| 2026-10-27 | ADD T5: BrandList component in the browser | mkit |
| 2026-10-27 | TRACE R2 | mkit |
| 2026-10-27 | TRACE R3 | mkit |
| 2026-10-27 | TRACE R4 | mkit |
| 2026-10-27 | TRACE R5 | mkit |
| 2026-10-27 | TRACE R6 | mkit |
| 2026-10-27 | TRACE R6 | mkit |
| 2026-10-27 | TRACE R6 | mkit |
| 2026-10-27 | TRACE R5, R7 | mkit |
| 2026-10-27 | TRACE R8 | mkit |
| 2026-10-27 | TRACE R8 | mkit |
| 2026-10-27 | TRACE R8 | mkit |
| 2026-10-27 | TRACE R9 | mkit |
| 2026-10-27 | TRACE R10 | mkit |
| 2026-10-27 | TRACE R11 | mkit |
| 2026-10-27 | TRACE R12, R21 | mkit |
| 2026-10-27 | TRACE R13 | mkit |
| 2026-10-27 | TRACE R14 | mkit |
| 2026-10-27 | TRACE R15 | mkit |
| 2026-10-27 | TRACE R16 | mkit |
| 2026-10-27 | TRACE R17 | mkit |
| 2026-10-27 | TRACE R18 | mkit |
| 2026-10-27 | TRACE R18 | mkit |
| 2026-10-27 | TRACE R19 | mkit |
| 2026-10-27 | TRACE R19 | mkit |
| 2026-10-27 | TRACE R2, R4, R5 | mkit |
| 2026-10-27 | TRACE R3 | mkit |
| 2026-10-27 | TRACE R8 | mkit |
| 2026-10-27 | TRACE R12 | mkit |
| 2026-10-27 | TRACE R13, R1 | mkit |
| 2026-10-27 | TRACE R18, R19 | mkit |
| 2026-10-27 | TRACE R21, R22 | mkit |
| 2026-10-27 | TRACE R21 | mkit |
| 2026-10-27 | TRACE R21 | mkit |
| 2026-10-27 | TRACE R21 | mkit |
| 2026-10-27 | TRACE R21 | mkit |
| 2026-10-27 | TRACE R22 | mkit |
| 2026-10-27 | TRACE O1 | mkit |
| 2026-10-27 | TRACE O2 | mkit |
| 2026-10-27 | TRACE O3 | mkit |
| 2026-10-27 | TRACE O4 | mkit |
| 2026-10-27 | TRACE O5 | mkit |
| 2026-10-27 | TRACE O6 | mkit |
| 2026-10-27 | TRACE O7 | mkit |
| 2026-10-27 | TRACE O8 | mkit |
| 2026-10-27 | TRACE Q12 | mkit |
| 2026-10-27 | TRACE Q13 | mkit |
| 2026-10-27 | TRACE Q10, R3 | mkit |
| 2026-10-27 | TRACE Q15 | mkit |
| 2026-10-27 | TRACE Q9, R9 | mkit |
| 2026-10-27 | TRACE Q18, R12 | mkit |
| 2026-10-27 | TRACE Q8, Q16, R17 | mkit |
| 2026-10-27 | TRACE Q17, R19 | mkit |
| 2026-10-27 | ANSWER Q6 | mkit |
| 2026-10-27 | ANSWER Q7 | mkit |
| 2026-10-27 | ANSWER Q8 | mkit |
| 2026-10-27 | ANSWER Q9 | mkit |
| 2026-10-27 | ANSWER Q10 | mkit |
| 2026-10-27 | ANSWER Q12 | mkit |
| 2026-10-27 | ANSWER Q13 | mkit |
| 2026-10-27 | ADD T6: Backend framework | mkit |
| 2026-10-27 | ADD T7: Databases | mkit |
| 2026-10-27 | ADD T8: Token and verification | mkit |
| 2026-10-27 | ADD T9: Frontend stack | mkit |
| 2026-10-27 | ADD T10: Migration | mkit |
| 2026-10-27 | ADD T11: Rating and reviewer modelling | mkit |
| 2026-10-27 | ADD T12: Postmeta mapping | mkit |
| 2026-10-27 | ANSWER Q14 | mkit |
| 2026-10-27 | ANSWER Q15 | mkit |
| 2026-10-27 | ANSWER Q16 | mkit |
| 2026-10-27 | ANSWER Q17 | mkit |
| 2026-10-27 | ANSWER Q18 | mkit |
| 2026-10-27 | ADD T13: Top review definition | mkit |
| 2026-10-27 | ADD T14: API contract | mkit |
| 2026-10-27 | ADD T15: Roles and revocation | mkit |
| 2026-10-27 | ADD T16: Library distribution | mkit |
| 2026-10-27 | ADD T17: SCSS toolchain | mkit |
| 2026-10-27 | ALTER Q11 | mkit |
| 2026-10-27 | ANSWER Q11 | mkit |
| 2026-10-27 | ADD T18: Short description source | mkit |
| 2026-10-27 | ALTER R19 | mkit |
| 2026-10-27 | ALTER R15 | mkit |
| 2026-10-27 | ALTER R5 | mkit |
| 2026-10-27 | ALTER R10 | mkit |
| 2026-10-27 | ALTER R13 | mkit |
| 2026-10-27 | ADD Q19: How does the main app obtain the RS256 public key (mounted file or JWKS endpoint) and how are keys rotated? | mkit |
| 2026-10-27 | ADD Q20: What is the call date, and which requirements drop first if time runs short? | mkit |
| 2026-10-27 | ADD A4: WP user roles can be read from wp_usermeta wp_capabilities | mkit |
| 2026-10-27 | ANSWER Q19 | mkit |
| 2026-10-27 | ANSWER Q20 | mkit |
| 2026-10-27 | ADD T19: Public key distribution | mkit |
| 2026-10-27 | ADD T20: Cut order | mkit |
| 2026-10-27 | ADD Q21: Where does the code that reads the WP database live: each service owns its own queries and only the upsert-by-WP-ID pattern is shared, or the shared library holds a WP reader? | mkit |
| 2026-10-27 | ADD A5: One import flow can populate both services without a separate auth-side importer being specified | mkit |
| 2026-10-27 | ADD A6: Reviews do not need a link from the main app to an auth account | mkit |
| 2026-10-27 | ADD A7: Both services can reach the WP database on the compose network | mkit |
| 2026-10-27 | ANSWER Q21 | mkit |
| 2026-10-27 | ALTER R19 | mkit |
| 2026-10-27 | ALTER T4 | mkit |
| 2026-10-27 | ADD T21: WP reader location | mkit |
| 2026-10-27 | ALTER R19 | mkit |
| 2026-10-27 | ALTER T4 | mkit |
| 2026-10-27 | REMOVE T21: Q21 shared WP reader choice undone at user request, being re-asked | mkit |
| 2026-10-27 | ANSWER Q21 | mkit |
| 2026-10-27 | ADD T22: WP reader location | mkit |
| 2026-10-27 | ALTER R16 | mkit |
| 2026-10-27 | ADD A8: Framework defaults for ordering are enough, no explicit default order, tie-break or null placement is needed | mkit |
| 2026-10-27 | ADD A9: The serializer defaults for row field types and rounding are acceptable and a published schema is not needed | mkit |
| 2026-10-27 | ADD A10: The behaviour of multiple industry slugs and of an unknown slug can stay undefined | mkit |
| 2026-10-27 | ADD A11: An uncapped page_size and the framework default beyond the last page are acceptable | mkit |
| 2026-10-27 | ADD A12: The brand listing will not issue a query per row | mkit |
| 2026-10-27 | ADD A13: Filter and sort state in the component without URL sync is acceptable | mkit |
| 2026-10-27 | ADD A14: Framework default error bodies and 401 headers are consistent enough | mkit |
| 2026-10-27 | ADD C13: Built for dev and demo as a take-home, not for production deployment | mkit |
| 2026-10-27 | ALTER A2 | mkit |
| 2026-10-27 | ALTER A3 | mkit |
| 2026-10-27 | ALTER A4 | mkit |
| 2026-10-27 | ALTER A6 | mkit |
| 2026-10-27 | ALTER R2 | mkit |
| 2026-10-27 | ALTER T11 | mkit |
| 2026-10-27 | ALTER R3 | mkit |
| 2026-10-27 | ALTER R13 | mkit |
| 2026-10-27 | ALTER T15 | mkit |
| 2026-10-27 | ALTER R14 | mkit |
| 2026-10-27 | ALTER R12 | mkit |
| 2026-10-27 | ADD A15: The cut order in T20 is enough without changing priorities, R9 and R11 can stay P0 | mkit |
| 2026-10-27 | ADD A16: A headless browser container for visual checks fits the Docker-only constraint at demo scale | mkit |
| 2026-10-27 | ADD A17: An injectable clock in the library core is cheap to add and test | mkit |
| 2026-10-27 | ADD A18: Logging in every imported user is cheap to test | mkit |
| 2026-10-27 | ANSWER Q16 | mkit |
| 2026-10-27 | ALTER R13 | mkit |
| 2026-10-27 | ALTER R14 | mkit |
| 2026-10-27 | ALTER R5 | mkit |
| 2026-10-27 | ALTER R6 | mkit |
| 2026-10-27 | ALTER R12 | mkit |
| 2026-10-27 | ALTER R10 | mkit |
| 2026-10-27 | ALTER R14 | mkit |
| 2026-10-27 | ALTER R14 | mkit |
| 2026-10-27 | ALTER R15 | mkit |
| 2026-10-27 | ALTER R17 | mkit |
| 2026-10-27 | ALTER R16 | mkit |
| 2026-10-27 | ALTER R4 | mkit |
| 2026-10-27 | ALTER R22 | mkit |
| 2026-10-27 | ALTER R13 | mkit |
| 2026-10-27 | DONE R13 R14 | mkit |
| 2026-10-27 | DONE R12 | mkit |
| 2026-10-27 | DONE R4 R5 R6 R10 R15 R16 R17 R18 | mkit |
| 2026-10-27 | RUN done: UUID auth users and triage follow-ups | mkit |
| 2026-10-27 | ALTER R8 | mkit |
| 2026-10-27 | ALTER R8 | mkit |
| 2026-10-27 | DONE R8 | mkit |
| 2026-10-27 | RUN done: BrandList badge parity and restyled selects | mkit |
| 2026-10-27 | ALTER R5 | mkit |
| 2026-10-27 | DONE R5 | mkit |
| 2026-10-27 | RUN done: Quote cutoff matches WordPress word trimming | mkit |
| 2026-10-27 | ALTER R8 | mkit |
| 2026-10-27 | ALTER R8 | mkit |
| 2026-10-27 | ALTER R6 | mkit |
| 2026-10-27 | ALTER A12 | mkit |
| 2026-10-27 | DONE R8 R6 | mkit |
| 2026-10-27 | RUN done: R8 URL state and pagination, R6 query-count test | mkit |
| 2026-10-27 | ALTER R8 | mkit |
| 2026-10-27 | ANSWER Q10 | mkit |
