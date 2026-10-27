# Brand Reviews WordPress (Interview Challenge Source)

Self-contained, reproducible WordPress site used as the source for a WP → Django migration challenge.

The site is a small consumer-reviews directory: **brands** with profile pages plus user-submitted **reviews** linked to each brand. Two custom post types, one taxonomy, ACF fields, Yoast SEO metadata.

## Quick start

Docker is the only host prerequisite. From a clean clone:

```bash
cp .env.example .env
make up                                   # build and start every service
make jwt-keys                             # dev RS256 keypair into .env (once)
make up                                   # recreate auth + app so they pick the keys up
docker compose run --rm app python manage.py import_wp          # migrate WP content (see Migration)
docker compose run --rm auth python manage.py import_wp_users   # migrate WP users (see Auth service users)
```

The WordPress database is imported from `db/dump.sql` on first boot, which takes ~20 seconds; the app and auth containers apply their own Django migrations on start. Then:

- Main app:    <http://localhost:8000> (health: `/health/`)
- Auth service: <http://localhost:8001> (health: `/health/`)
- Public WP site: <http://localhost:8080>
- WP admin:    <http://localhost:8080/wp-admin> (`admin` / `admin`)
- phpMyAdmin:  <http://localhost:8081>
- REST root:   <http://localhost:8080/wp-json/wp/v2/>

Host ports are set in `.env` (`WP_PORT`, `PMA_PORT`, `APP_PORT`, `AUTH_PORT`); change them if one clashes, and use your ports in the `curl` commands below, which assume the defaults (8000 for the main app, 8001 for auth). Check status with `docker compose ps`; every service should be running or healthy. This is a dev/demo setup (dev password, dev keys, Django `runserver`), not a production deployment.

### Running the main app

The `app` service (Django 5.2 + Django Ninja, PostgreSQL in `app-db`) serves the server-rendered pages and the API on port 8000:

- `/` homepage with the React `BrandList` component, `/brand/<slug>/`, `/review/<slug>/` (slugs match the WordPress permalinks). Public.
- `GET /api/brands/` public brand listing; `PATCH /api/brands/{slug}/` editor-only (see Login below).

Pages are empty until the migration has run. Source is bind-mounted, so Python edits reload; `docker compose logs -f app` tails it.

`GET /api/brands/` parameters: `industry` (industry slug, repeatable, several are OR-ed, an unknown slug matches nothing), `ordering` (`name` default, `average_rating`, `-average_rating`, `review_count`, `-review_count`), `page` (from 1) and `page_size` (default 10). The response is `{count, next, previous, results}`; each row has `name`, `slug`, `industry`, `average_rating`, `review_count`, `short_description` and `top_review_snippet` (rule below). A page past the end returns 200 with empty `results`.

```
curl -s 'http://localhost:8000/api/brands/?industry=insurance&industry=retail&ordering=-average_rating&page_size=2'
```

### The React component

`BrandList` (filter by industry, sort, paginate; state kept in the URL query string) is a Vite + React 18 JavaScript component in `frontend/src/`, mounted into the homepage and styled with the project SCSS. The built bundle `app/static/dist/brandlist.js` and the compiled `app/static/css/theme.css` are committed, so running the app needs no build step. Rebuild after editing `frontend/src/` or `frontend/scss/` (Node runs in the `node` service, no host Node needed):

```
make node ARGS="npm install"      # first time only
make node ARGS="npm run build"    # writes app/static/dist/brandlist.js
make node ARGS="npm test"         # component tests (Vitest, jsdom)
```

### Compiling the SCSS

The stylesheet source lives in `frontend/scss/`. `main.scss` is the entry file and pulls in partials in `tokens/`, `base/`, `layout/` and `components/`; each commented section of `reference/theme.css` maps to one partial. Compile with Dart Sass in the node container:

```
make node ARGS="npm install"      # first time only
make node ARGS="npm run build:css"
```

This writes `app/static/css/theme.css`, which `base.html` links. Do not edit that file by hand and do not edit `reference/theme.css`. To add a component, create `frontend/scss/components/_name.scss` and add an `@use` line to `main.scss`; use the custom properties from `tokens/_tokens.scss` rather than literal colours.

## Challenge coverage

`D` deliverable, `P` pillar doc ask, `Q` live question.

### Run and operate

| # | Asks | Answer | Where |
|---|---|---|---|
| D1 | Run app, auth, React locally | `make up`, `make jwt-keys`, `make up` | [Quick start](#quick-start) |
| D4 | Run and re-run the migration | `import_wp`; upsert on WP ID, rerun is a no-op | [Migration](#migration-wordpress-to-the-main-app) |
| D2 | Get a token, call protected endpoint | Login, then `PATCH` with Bearer token | [Login](#login-auth-service) |
| D3 | Library tests, how versions reach services | `make lib-test`; bump version and both pins | [Library tests](#tests-and-the-shared-library) |

### Data and migration

| # | Asks | Answer | Where |
|---|---|---|---|
| Q1a | Average rating: store or derive? | Derived by aggregate, 1 decimal | [Modeling](written-answers.md#modeling-decisions) |
| Q1b | Reviewers: users, model or strings? | `Reviewer` model, no users in main app | [Modeling](written-answers.md#modeling-decisions) |
| Q2 | Postmeta: fields, JSON or dropped? | ACF columns, Yoast JSON, rest dropped | [Modeling](written-answers.md#modeling-decisions) |
| Q3a | Why this migration approach? | Read MariaDB directly; skips parsing the dump | [Migration](#migration-wordpress-to-the-main-app) |
| Q3b | Re-run safely? | Upsert on WP ID, one transaction | [Migration](#migration-wordpress-to-the-main-app) |
| Q3c | Scale to 100x? | Chunked bulk upserts, commit per batch | [Differently](written-answers.md#what-i-would-do-differently-with-more-time) |

### API and component

| # | Asks | Answer | Where |
|---|---|---|---|
| P1 | Define "top review" | Highest rating, newest ties; first 24 words | [Top review](#top-review-snippet) |
| Q4a | Why this pagination shape? | `page`/`page_size` plus count envelope; familiar | [Main app](#running-the-main-app) |
| Q4b | Why these filter/sort params? | Repeatable `industry`, one `ordering`; familiar | [Main app](#running-the-main-app) |
| Q4c | What changes for mobile? | Nothing in the contract | [Main app](#running-the-main-app) |
| Q5a | Where does state live? | In the component, `useState` | [React component](#the-react-component) |
| Q5b | URL-synced state? | Query string via `replaceState` | [React component](#the-react-component) |
| Q5c | Loading and error UX? | Status, alert with retry, aborted requests | [React component](#the-react-component) |

### Styling

| # | Asks | Answer | Where |
|---|---|---|---|
| P2 | Compile the SCSS | `npm run build:css` in Docker | [SCSS](#compiling-the-scss) |
| Q6a | Why these partials and tokens? | Mirror `theme.css` sections; themes can swap | [SCSS](#compiling-the-scss) |
| Q6b | How to add a component? | New partial, one `@use`, use tokens | [SCSS](#compiling-the-scss) |

### Auth and shared library

| # | Asks | Answer | Where |
|---|---|---|---|
| P3 | Verify token locally or remotely, why? | Locally; no runtime dependency on auth | [Token verification](#token-verification-and-auth-outage-behaviour) |
| Q7a | What does each service own? | Auth: users, roles, signing. App: data | [Auth users](#auth-service-users) |
| Q7b | Validate a token; auth down? | Local public key; only login fails | [Token verification](#token-verification-and-auth-outage-behaviour) |
| Q7c | Revoke or change role early? | Cannot; 15-minute expiry, next login | [Token verification](#token-verification-and-auth-outage-behaviour) |
| Q8a | Library: what in, what out? | In: claims, verify, roles. Out: signing | [Library tests](#tests-and-the-shared-library) |
| Q8b | Pin and upgrade it? | Exact `ca-auth-lib==` pin per service | [Library tests](#tests-and-the-shared-library) |
| Q8c | Breaking change without joint deploy? | Expand, move each service, contract | [Library tests](#tests-and-the-shared-library) |

### Write-up

| # | Asks | Answer | Where |
|---|---|---|---|
| D5a | Modeling decisions | WP-ID keys, derived rating, `Reviewer` model | [Modeling](written-answers.md#modeling-decisions) |
| D5b | What I would do differently | Re-import edits, deletes, sanitising, login UI | [Differently](written-answers.md#what-i-would-do-differently-with-more-time) |
| D5c | AI defaults chosen over preference | Table of accepted defaults with reasons | [AI defaults](written-answers.md#ai-defaults-i-accepted) |

## Migration (WordPress to the main app)

`import_wp` reads the WordPress MariaDB (`db` service, no WordPress container needed) directly and writes industries, brands, reviewers and reviews into the main app database:

```
docker compose run --rm app python manage.py import_wp
```

It prints one line per model, for example `Brand     created=5 updated=0 unchanged=0`. Only published posts are read. Each row is upserted on its WP ID (post, term or user ID), the whole import runs in one transaction, and it creates no accounts, passwords or roles.

Re-running is safe: a second run prints `created=0 updated=0 unchanged=N` for every model and no duplicates appear (the tests cover this). If WordPress content changed, the rerun updates just those rows (`updated=N`). Rerun it, for example, to restore demo data after PATCH-ing a brand, since the import rewrites `short_description` (the first 200 characters of the stripped brand content, cut at a word boundary). The import never deletes: a post removed in WordPress stays in the app database. If the WP database is unreachable the command exits with an error and writes nothing.

Users are migrated separately into the auth service (`import_wp_users`, see Auth service users) because the main app stores no users.

## Auth service users

The auth service owns users, passwords and roles (the main app stores none). Import them from WordPress (re-runnable: each WP user ID is turned into a UUIDv5 that becomes the auth user's ID):

```
docker compose run --rm auth python manage.py import_wp_users
```

It prints `User created=N updated=N unchanged=N`; a second run creates nothing. The UUID is derived from the WP user ID with a fixed namespace constant in the importer, so the same WP user always gets the same UUID and the auth database stores no WP user ID. There is no integer-to-UUID data migration: after pulling this change, reset the auth database volume and rerun the import. WP password hashes are never read: every user gets the dev password from `AUTH_DEV_PASSWORD` (default `dev-password`, set in `.env` to override). WP administrator and editor become `editor`, all others `reader`.

## Login (auth service)

`POST /api/auth/login` takes JSON `username` and `password` and returns `access_token`, `token_type` (`Bearer`) and `expires_in` (900). Tokens are RS256 JWTs with claims `iss` (`ca-auth`), `sub` (the auth user's UUID), `role` (`reader` or `editor`), `iat` and `exp` (`exp = iat + 900`); claim names come from `ca_auth_lib`. Wrong credentials return 401 with no token. There is no login UI and no refresh token.

The auth service signs with the private key in env var `AUTH_JWT_PRIVATE_KEY` (PEM) and never generates one: if it is unset, login returns 503 with an error. Generate the dev keypair once (this is the `make jwt-keys` step of the quick start; it also writes `APP_JWT_PUBLIC_KEY`, which the main app reads to verify tokens; `.env` is git-ignored and an existing key is never overwritten). Containers read `.env` only when created, so recreate them afterwards with `make up` (or `docker compose up -d`). Then get a token and call the protected endpoint. Seeded logins are `admin` (editor) and e.g. `sarah_k` (reader), all with the dev password:

```
TOKEN=$(curl -s -X POST http://localhost:8001/api/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"username": "admin", "password": "dev-password"}' \
  | sed -E 's/.*"access_token": *"([^"]+)".*/\1/')

curl -s -X PATCH http://localhost:8000/api/brands/acme-insurance/ \
  -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
  -d '{"short_description": "Edited by an editor"}'
```

`PATCH /api/brands/{slug}/` accepts only `short_description` (plain text, 1-500 characters) and returns the updated brand row. No token, a bad token or an expired token gives 401; a valid `reader` token gives 403; an unknown slug gives 404. Re-running `import_wp` resets `short_description` to the value derived from WordPress (see Migration), so that edit does not survive a re-import.

## Tests and the shared library

`make test` runs every suite in Docker: main app (API, auth protection, `import_wp` idempotency), auth service, shared library and frontend. Individually:

```
docker compose exec app python manage.py test     # main app (needs the app container up)
docker compose run --rm auth python manage.py test
make lib-test                                      # shared library
make node ARGS="npm test"                          # frontend
```

The `import_wp` tests read the compose WP database into a throwaway test database; demo data is untouched.

**Shared library** (`lib/ca_auth_lib/`, package `ca-auth-lib`, own `pyproject.toml`): framework-free token claims, RS256 verification and role checks used by both services; see `lib/ca_auth_lib/README.md`. `make lib-test` runs its 19 tests in a plain Python container with no Django or Ninja installed.

How a new version reaches each service: both Dockerfiles `pip install` the library from the repo path `lib/ca_auth_lib`, and each service's `requirements.txt` pins it exactly (`ca-auth-lib==0.1.0`). To release a change: bump `version` in `lib/ca_auth_lib/pyproject.toml`, run `make lib-test`, then change the pin in `app/requirements.txt` and `auth/requirements.txt` and rebuild (`docker compose up -d --build app auth`). If a pin and the library version disagree, the image build fails rather than drifting. A breaking change is released in steps so the services need not deploy together: first a version that supports old and new behaviour, bump each service onto it separately, then remove the old behaviour in a later version.

## Token verification and auth outage behaviour

**The main app verifies tokens locally; it never calls the auth service.** `PATCH /api/brands/{slug}/` checks the RS256 signature, `iss`, `exp` and the `role` claim with `ca_auth_lib` against the public key in env var `APP_JWT_PUBLIC_KEY` (written to `.env` by `make jwt-keys`). Why: the main app needs only the public key, so it has no runtime dependency on the auth service and no per-request network hop, and an auth outage cannot take the main app down. The cost is that the main app cannot see revocations or role changes until a token expires (see below).

Auth outage (auth container stopped): the main app does not depend on it, so nothing changes for it.

- Public endpoints stay up: `GET /api/brands/`, the server-rendered pages (`/`, `/brand/<slug>/`, review pages) and `/health/` return 200.
- `PATCH /api/brands/{slug}/` with an editor token issued before the outage and not yet expired still succeeds (200). With no token, a malformed token or an expired token it returns 401; with a valid reader token it returns 403. These do not change during an outage.
- Only getting a new token fails: `POST /api/auth/login` on the auth service is unreachable, so nobody can log in until it is back. Tokens expire 15 minutes after issue, so after that window an outage means no one can write until auth returns.
- If `APP_JWT_PUBLIC_KEY` is empty in the main app, every `PATCH` returns 401 (fail closed); public endpoints are unaffected.

Revocation and role changes: there is no revocation list and no refresh token. A token cannot be revoked before it expires; the short 15-minute lifetime is the revocation mechanism, so a removed or demoted user keeps their old access for up to 15 minutes. A role change applies at the user's next login (a new token carries the new `role`); until then the old token keeps its old role. Rotating the signing key (redeploy auth with the new private key and the main app with the new public key) invalidates all outstanding tokens at once.

## Written answers

Modeling decisions, what I would do differently with more time, and the AI defaults I accepted are in [written-answers.md](written-answers.md).

## Stack

| Service     | Image                            | Port  | Purpose                                |
|-------------|----------------------------------|-------|----------------------------------------|
| `db`        | `mariadb:11`                     | -     | Database; auto-imports `db/dump.sql`   |
| `wordpress` | `wordpress:6.9-php8.3-apache`    | 8080  | WP + Apache + PHP                      |
| `wpcli`     | `wordpress:cli-php8.3`           | -     | Helper for re-seeding / dumping        |
| `phpmyadmin`| `phpmyadmin:5`                   | 8081  | Optional DB browser                    |
| `app`       | `python:3.12-slim` (Django 5.2)  | 8000  | Main app                               |
| `app-db`    | `postgres:16`                    | -     | Main app database                      |
| `auth`      | `python:3.12-slim` (Django 5.2)  | 8001  | Auth service (separate project)        |
| `auth-db`   | `postgres:16`                    | -     | Auth service database                  |

## What's committed

```
docker-compose.yml          # the stack
.env.example                # config defaults
Makefile                    # make targets
db/dump.sql                 # seeded database snapshot
scripts/seed.sh             # bootstrap script (install + plugins + seed)
wp-content/plugins/         # WP default plugins + ACF + Yoast (committed for offline reproducibility)
wp-content/mu-plugins/
  cpt.php                   # registers `brand` and `review` CPTs and `industry` taxonomy
  acf-fields.php            # registers ACF field groups in code
wp-content/themes/
  consumer-reviews/         # custom theme used by the site
```

WP core files and the default themes (e.g. twentytwentyfour) live inside the `wp_files` named volume and are recreated from the image on first boot. Only the custom `consumer-reviews` theme is committed to the repo.

## Make targets

```
make up         # build and start the whole stack (WP, main app, auth service, databases)
make down       # stop containers (keeps volumes)
make reset      # stop AND wipe volumes (next 'up' re-imports dump.sql)
make logs       # tail wordpress + db
make wp ARGS="plugin list"   # run wp-cli inside the stack
make bootstrap  # full re-seed: WP core install + plugin install + content seed
make dump       # export the current DB to db/dump.sql
make status     # show running services
make jwt-keys   # dev RS256 keypair into .env
make test       # all test suites
make lib-test   # shared library tests only
make node ARGS="npm run build"   # frontend tooling in Docker
```

## Rebuilding the dump from scratch

If you change the schema or seed data:

```bash
make reset
make up
make bootstrap
make dump
git add db/dump.sql wp-content/plugins
git commit -m "Refresh seed data"
```

`make bootstrap` is idempotent enough to re-run, but the cleanest path is reset → up → bootstrap → dump.

## Content model

**`brand` CPT** at `/brand/<slug>/`
- Standard fields: title, content (body), featured image (optional)
- ACF fields: `website_url`, `founded_year`, `headquarters`, `average_rating`
- Taxonomy: `industry`
- Yoast: `_yoast_wpseo_title`, `_yoast_wpseo_metadesc` in postmeta

**`review` CPT** at `/review/<slug>/`
- Standard fields: title, content (review body), post_author (mapped to a real WP user)
- ACF fields: `rating` (1-5), `reviewer_name`, `reviewer_location`, `brand` (post object → brand id)

Seeded volume: 5 brands (one per industry), 60 reviews (12 per brand) authored by 8 reviewer users, 3 static pages (Home/About/Contact), 1 admin user.

## Theme

The active theme is a custom one at `wp-content/themes/consumer-reviews/` (committed to the repo). It renders:

- Homepage with featured brands and recent reviews
- Brand archive (`/brand/`) — card grid
- Single brand page (`/brand/<slug>/`) — hero with industry badge, star rating, website / founded / HQ metadata, body content, and full list of customer reviews
- Review archive (`/review/`) — paginated list
- Single review (`/review/<slug>/`) — back-link to brand, star rating, reviewer name/location, body
- Page template for About / Contact / Home pages

The theme is intentionally small (~10 PHP files + one stylesheet) and is meant to show candidates what the data renders as. They are not expected to clone the theme — just to migrate the underlying data.

## Endpoints worth knowing

- `/wp-json/wp/v2/brands` — list brands (note: `rest_base` is `brands` even though post type is `brand`)
- `/wp-json/wp/v2/brands/<id>` — single brand with ACF fields under `acf`
- `/wp-json/wp/v2/reviews` — list reviews
- `/wp-json/wp/v2/industry` — taxonomy terms
- `/wp-json/wp/v2/users` — reviewer users
- `/wp-json/wp/v2/pages` — static pages

ACF fields are exposed natively via `show_in_rest: true` set in `wp-content/mu-plugins/acf-fields.php`.

## Brand listing API

`GET /api/brands/` is public. Parameters: `industry` (repeatable slug), `ordering`, `page`, `page_size`. The full contract is under Running the main app; the snippet rule is below.

### Top review snippet

The "top" review of a brand is the one with the **highest rating**; ties are broken by the **newest** `published_at` (then highest id). `top_review_snippet` is that review's body with HTML tags removed and whitespace collapsed, cut to the **first 24 whole words**, with an ellipsis (`…`) added only when words were dropped. This is the same rule as `wp_trim_words` on the WordPress theme's review excerpts. A brand with no reviews returns `null` for `top_review_snippet` and `average_rating`, and `0` for `review_count`.

## Notes for the maintainer

- The `wp-content/plugins/advanced-custom-fields/` and `wp-content/plugins/wordpress-seo/` plugin code is GPL and committed to the repo so candidates don't need internet on first boot.
- `wp-content/plugins/akismet/` and `hello.php` are WP defaults — left in place but inactive.
- The site URL is hardcoded as `http://localhost:8080` in the dump (in `wp_options.siteurl` and `home`). Changing the port requires a search/replace in `db/dump.sql` before commit, or just override via `WP_HOME` / `WP_SITEURL` constants.
- `_yoast_wpseo_*` postmeta is seeded for brand posts only.


# AUTOMATIC WRITTEN ANSWERS

## Modeling decisions

- **Rows are keyed on the WP ID.** `Industry`, `Reviewer`, `Brand` and `Review` each carry the WP post, term or user ID, and `import_wp` upserts on it. That is what makes the import re-runnable (C2). Slugs are copied unchanged so URLs match the WP permalinks (C3).
- **Average rating is derived, not stored.** `Brand.average_rating` is an aggregate over reviews, rounded to 1 decimal. WordPress stores `average_rating` as an ACF field. That field is not imported, so the API value can differ from what WP displays.
- **Reviewers are a `Reviewer` model**, not Django users, because the main app stores no users, passwords or roles (C4). Users live only in the auth service.
- **Postmeta:** the ACF fields (`website_url`, `founded_year`, `headquarters`) are columns, the `_yoast_wpseo_*` keys are kept as JSON on `Brand.seo` and not rendered, and other WP-internal keys are dropped.
- **`short_description` is a derived-then-editable field.** All 5 seeded brands have an empty excerpt, so it is the first 200 characters of the stripped content, cut at a word boundary. It is stored so an editor can PATCH it.
- **Top review** is the highest rating, ties broken by newest, shown as the first 24 whole words of the body, with an ellipsis when shortened, like WordPress's `wp_trim_words`.
- **Roles:** `reader` and `editor`. WP administrator and editor become `editor`. Tokens are 15-minute RS256 JWTs verified locally with a public key, with no refresh token and no revocation list.

## What I would do differently with more time

From the record and the code:

- **Make edits survive a re-import.** `import_wp` rewrites `short_description` on every run, so an editor PATCH is lost on the next import. Fixing it needs an "edited by editor" marker or a separate override column. This was found while building R16 and documented, not fixed.
- **Reconcile the rating with WordPress.** Decide whether the imported WP `average_rating` should be kept for comparison, or the difference documented in the API.
- **Handle deletes.** The import never deletes, so content removed in WP stays in the app database.
- **Sanitise HTML.** The templates render WP content with `|safe` (`brand.content`, `review.body`). That is acceptable only because the content is trusted seed data in a dev/demo build (C13). Use an allow-list sanitiser or render only vetted markup before anything real.
- **Add a login UI, refresh tokens and revocation, and a JWKS endpoint** for key rotation. All are out of scope or deferred in the spec (O5, O6; key rotation is by redeploy).
- **Look at the scale of the import.** It is a single transaction reading MariaDB directly. *(inferred: at 100x it would need batching; the record asks the question in Q10 but this README does not measure it)*
- **Cover the framework-default behaviours in tests.** Several assumptions below (A8, A9, A10, A11, A12, A14) are still marked unvalidated in the spec.

## AI defaults I accepted

These are the places where the build agent chose a behaviour the spec did not cover and it was kept. Each is logged in the build inbox. The reason given is the one recorded; where none was recorded it says so. *(The candidate's own preference in each case is not in the record: fill in which of these you would have chosen differently.)*

| Default | Why it was kept |
|---|---|
| Industry returned as its name string (`null` if none); snippet strips HTML tags and collapses whitespace before keeping 24 whole words (WP's `wp_trim_words` rule, chosen by the candidate) | Not recorded beyond the assumption (I1) |
| Listing: `page_size` default 10 and uncapped, default order by name with ties by name then id, nulls last for rating, past-the-end page returns 200 with empty results, several industry slugs OR-ed, unknown slug matches nothing, bad `ordering` or `page` returns Ninja's 422 | Framework defaults accepted as assumptions A8, A10, A11, A14 (I2) |
| `BrandList` sits on the homepage, industry options come from Django via `json_script` (no industries endpoint), pagination is Previous/Next with a "Showing X-Y of N" line, page size fixed at 10 | Keeps the stack small (I3). *(inferred)* |
| URL state uses `history.replaceState`, so changing a filter, sort or page adds no Back-button entry (Back leaves the page); `PAGE_SIZE` 10 is sent explicitly; a shared link past the last page resets to page 1 | `CHALLENGE.md` asks how URL-synced state is handled but says nothing about the Back button, so this is an assumption (I16). *(inferred: `pushState` plus a `popstate` listener would make Back step through filters)* |
| Built bundle `app/static/dist/brandlist.js` is committed | A clean clone then works with no build step (I3) |
| axe test disables colour contrast in jsdom, contrast is checked in the real browser container instead; Playwright 1.49.1 added as a compose `browser` service | jsdom cannot compute contrast (I4) |
| Editor satisfies a reader requirement (role hierarchy) | Not recorded beyond the assumption (I8) |
| `verify_token` also rejects tokens whose `exp - iat` is not 900 and non-integer `iat` or `exp`; signing stays in the auth service, not the library | Not recorded beyond the assumption (I9) |
| A missing signing key returns 503 on login, not 500 or 401 | Not recorded beyond the assumption (I11). The README Login section documents it |
| `Brand.short_description` widened from 255 to 500 (migration `0002`) | So the 500-character PATCH limit is storable (I12) |
| Brand detail page renders `short_description`, which it did not before | Not recorded beyond the assumption (I13) |
| PATCH strips body whitespace before the 1-500 length check and returns the full brand row | Not recorded beyond the assumption (I14) |
| PATCH checks the token before the path, so 401 and 403 come before 404, and request-body validation (422) runs before the handler. A PATCH with an unknown slug and an invalid body therefore returns 422, not 404 *(inferred from Ninja's behaviour, not covered by a test)* | Framework default; the tests cover 401/403/404 with a valid body and 422 with a known slug |

Decisions the candidate made explicitly (the Q-items in the spec, plus I5 to I7: the private key in `AUTH_JWT_PRIVATE_KEY`, library built before the login endpoint, the token claim shapes) are not listed above because they were not AI defaults.
