C1 [constraint] Whole stack runs through docker compose, Docker is the only host prerequisite
C2 [constraint] Migration must be re-runnable without producing duplicates
C3 [constraint] Server-rendered URL slugs must match WP permalinks
C4 [constraint] Main app stores no passwords or roles
C5 [constraint] Auth service is a separate Django project in its own container with its own database
C6 [constraint] GET /api/brands/ and the server-rendered pages stay public
C7 [constraint] Shared library has its own pyproject.toml, is versioned, has tests that run without either Django project, and holds only code both services use
C8 [preference] Shared library lives in its own directory of this repo
C9 [constraint] All six pillars are required, prioritise within them rather than cutting one
C10 [constraint] Call date is the cutoff, no fixed deadline, the date itself is not yet known
C11 [constraint] reference/theme.css is not edited, SCSS must compile to structurally equivalent CSS
C12 [constraint] Every submitted piece must be explainable and defensible by the candidate
C13 [constraint] Built for dev and demo as a take-home, not for production deployment
A1 [unvalidated] db/dump.sql loads cleanly through docker compose and exposes brands, reviews, industries and users
A2 [validated] Every review links to exactly one existing brand
A3 [validated] Each brand has at most one industry term
A4 [validated] WP user roles can be read from wp_usermeta wp_capabilities
A5 [unvalidated] One import flow can populate both services without a separate auth-side importer being specified
A6 [invalid] Reviews do not need a link from the main app to an auth account
A7 [unvalidated] Both services can reach the WP database on the compose network
A8 [unvalidated] Framework defaults for ordering are enough, no explicit default order, tie-break or null placement is needed
A9 [unvalidated] The serializer defaults for row field types and rounding are acceptable and a published schema is not needed
A10 [unvalidated] The behaviour of multiple industry slugs and of an unknown slug can stay undefined
A11 [unvalidated] An uncapped page_size and the framework default beyond the last page are acceptable
A12 [unvalidated] The brand listing will not issue a query per row
A13 [unvalidated] Filter and sort state in the component without URL sync is acceptable
A14 [unvalidated] Framework default error bodies and 401 headers are consistent enough
A15 [unvalidated] The cut order in T20 is enough without changing priorities, R9 and R11 can stay P0
A16 [unvalidated] A headless browser container for visual checks fits the Docker-only constraint at demo scale
A17 [unvalidated] An injectable clock in the library core is cheap to add and test
A18 [unvalidated] Logging in every imported user is cheap to test
R1 [P0] Whole stack boots from a clean clone
R2 [P0] Clean relational domain model for brands, reviews, industries and reviewer users
R3 [P0] Re-runnable WP content migration command in the main app
R4 [P0] Server-rendered homepage, brand detail and review detail pages
R5 [P0] Brand listing endpoint returns card-ready rows
R6 [P0] Brand listing is filterable, sortable and paginated
R7 [P0] Top review snippet is defined and documented
R8 [P0] BrandList consumes the API with industry filter and sort control
R9 [P0] BrandList handles loading, empty and error states
R10 [P0] BrandList is keyboard accessible and semantic
R11 [P0] BrandList is responsive
R12 [P0] SCSS source tree compiles to equivalent CSS
R13 [P0] Auth service owns users and its own re-runnable import creates them from wp_users
R14 [P0] Login exchanges credentials for a token
R15 [P0] Auth service is the source of truth for at least two roles
R16 [P0] Editor-only brand write endpoint in the main app
R17 [P0] Token verification approach and auth outage behaviour are decided and documented
R18 [P0] Shared library is an installable package used by both services
R19 [P0] Library has a framework-free core, tests run without Django and the library stays small
R20 [P1] Tests cover migration idempotency, API behaviour and auth protection
R21 [P0] README documents how to run, authenticate, test the library and migrate
R22 [P0] README records modeling decisions, what to do differently and AI defaults accepted
O1 [active] Migrating the WP admin and editor experience
O2 [active] Yoast SEO frontend output
O3 [active] WP plugin parity beyond data structure
O4 [active] User-facing review submission and search
O5 [active] Registration, password reset, social login, MFA
O6 [active] A login UI
O7 [active] Image uploads and real logos
O8 [active] Pixel-matching the WP theme
O9 [active] Archive pages and industry taxonomy pages
Q1 [answered] Where is BrandList rendered?
Q2 [answered] Is Yoast SEO data carried across?
Q3 [answered] Which tests are in scope beyond the library tests?
Q4 [answered] Are archive and taxonomy pages built?
Q5 [answered] What happens to wp_users passwords in the auth service?
Q6 [answered] Which Python and Django versions and which API stack (DRF, Django Ninja or plain views)?
Q7 [answered] Which database engine for the main app and for the auth service?
Q8 [answered] Which token format and signing, and does the main app verify locally or call the auth service, and what happens when it is down?
Q9 [answered] Which React build tooling, language (TypeScript or JavaScript), CSS approach and way of serving the bundle, and where does filter and sort state live including URL sync?
Q10 [answered] Which migration source (dump.sql, WP REST, MariaDB direct), which idempotency key, and how would it scale to 100x?
Q11 [answered] Which source becomes a brand's short description? Research: all 5 brands in db/dump.sql have an empty excerpt and no short_description postmeta, content is three HTML paragraphs. Candidates: first paragraph of content, or first N characters of stripped content. To confirm with user.
Q12 [answered] Is the average rating stored, derived or both, and are reviewers Django users, a Reviewer model or denormalized strings?
Q13 [answered] Which postmeta fields become model fields, JSON or are dropped?
Q14 [answered] What does top review mean (highest rating, most recent, longest, other)?
Q15 [answered] Which pagination shape and which filter and sort parameter names, and is the industry filter single or multi select?
Q16 [answered] Which role names exist, which WP users become editors, and how are tokens revoked or roles changed before expiry?
Q17 [answered] How is the shared library installed into both images, how is it pinned, and how is a breaking change released without a simultaneous deploy?
Q18 [answered] Which SCSS toolchain, partial layout and token naming, and how does a second engineer add a component?
Q19 [answered] How does the main app obtain the RS256 public key (mounted file or JWKS endpoint) and how are keys rotated?
Q20 [answered] What is the call date, and which requirements drop first if time runs short?
Q21 [answered] Where does the code that reads the WP database live: each service owns its own queries and only the upsert-by-WP-ID pattern is shared, or the shared library holds a WP reader?
T1 [active] WordPress source
T2 [active] Main Django app
T3 [active] Auth service
T4 [active] Shared Python library
T5 [active] BrandList component in the browser
T6 [active] Backend framework
T7 [active] Databases
T8 [active] Token and verification
T9 [active] Frontend stack
T10 [active] Migration
T11 [active] Rating and reviewer modelling
T12 [active] Postmeta mapping
T13 [active] Top review definition
T14 [active] API contract
T15 [active] Roles and revocation
T16 [active] Library distribution
T17 [active] SCSS toolchain
T18 [active] Short description source
T19 [active] Public key distribution
T20 [active] Cut order
T21 [removed] WP reader location
T22 [active] WP reader location
