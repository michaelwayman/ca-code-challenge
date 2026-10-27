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

## Making BrandList look polished in plain SCSS (2026-10-27)
**Answer:** Stay with the project SCSS (Q9, C11) and polish through technique, not a library: a fixed spacing scale, a clear title/meta/body hierarchy on the card, layered shadows, a skeleton loading state, and motion that respects `prefers-reduced-motion`. **Serves/costs:** serves C11 (no new dependency, structure stays in `frontend/scss/`), C12 (every rule is explainable); does not touch O8.
**Open:** (1) Are new design tokens (spacing scale, a second shadow, a focus colour already added) acceptable alongside the `:root` set copied from `theme.css`? (2) Is a skeleton loading state wanted, replacing the plain "Loading brands…" text? (3) Should there be a visual reference (a site or screenshot) you want it to resemble? None was given.

### Decision this informs
How much visual refinement to put into `<BrandList />` (R8 to R11) and its SCSS partial `components/_brand-list.scss`, without changing the stack. Steered by C11, C12, C13 (dev/demo) and O8 (no pixel-matching WP).

### Findings
- Current state: cards use a 1px border, `--radius` 10px, a single small shadow and a 1px hover lift (`frontend/scss/components/_cards.scss`). Stars, badge and the excerpt are already tokenised. Loading is a plain text message (`frontend/src/BrandList.jsx`, status `loading`). There is no skeleton, no `prefers-reduced-motion` rule and no spacing scale; spacing values are literals (16, 20, 22, 24px).
- Secondary summaries of *Refactoring UI* (not the book itself): hierarchy comes from size, weight and colour, and not all three should change on one element; use a fixed spacing scale (one summary suggests 4, 8, 16, 24, 32, 48, 64px); shadows work as a tight dark layer plus a larger soft layer; design in grayscale first and add colour last; card padding 16-24px and gaps 16-32px with one consistent radius (https://cdn.jsdelivr.net/npm/claude-code-skills@0.5.0/data/skills/ux-ui-design-system/references/refactoring-ui.md, read 2026-10-27). The numbers come from community skill files, not the book.
- Motion: `prefers-reduced-motion` is Baseline widely available, supported in all browsers since January 2020 (https://developer.mozilla.org/fr/docs/Web/CSS/Reference/At-rules/%40media/prefers-reduced-motion, read 2026-10-27). Keep focus outlines and colour cues, remove decorative movement, and put the override after the normal motion rules (https://www.simplified.guide/css/motion-respect-reduced-preference). Animating only `transform` and `opacity` is cheaper (secondary tutorial).
- Container queries let a card respond to its own width (`container-type: inline-size`, then `@container`), which suits a card that appears in different column counts (https://frontendchecklist.io/rules/css/container-queries). Not checked against MDN's English page.
- Loading: PatternFly recommends skeletons when the final layout is known and spinners when it is not (https://patternfly.org/components/skeleton/design-guidelines). BrandList's card layout is known, so a skeleton fits. Nielsen Norman Group's own article was not found; only its video page (https://www.nngroup.com/videos/skeleton-screens-vs-progress-bars-vs-spinners/).
- Not verified: which component galleries or design systems look best. I did not research Radix, shadcn, MUI or similar, so I make no ranking claim. They are libraries and would change Q9.

### Options
| Option | What changes | Spec cost |
|---|---|---|
| A. Token and hierarchy polish | Add a spacing scale and a layered shadow token; tune card type sizes and the star and badge placement | None (new tokens in `tokens/_tokens.scss`) |
| B. A plus skeleton and motion | A, plus skeleton cards for loading and a `prefers-reduced-motion` rule; optional container queries on the card | Adds acceptance bullets to R9 and R10 via `/mkit:change` |
| C. UI library | Replace the select and card styles with a library | Changes Q9, strains C11 and C12; not recommended for the call |
