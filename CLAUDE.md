<!-- mkit -->
## mkit
SPEC.md holds scope, constraints and decisions (IDs: R requirement, O out of scope, A assumption, C constraint, Q question, T technology). Never read it whole: `mkit show` = index, `mkit show R3 O1` = just those items.

When to use what:
- Before building anything non-trivial: `mkit brief R<n>`; build only what it lists.
- User reports a bug, idea or tweak: `mkit add "<one line>" --bug|--feature|--adjust`, then carry on. Do not edit SPEC.md.
- A request touches an O item or goes beyond an R's acceptance: stop and ask; suggest `/mkit:change`. Do not build it.
- Scope, a constraint or a tech choice is unclear: ask, or `/mkit:research`. Do not guess.
- Design decisions (schema, API shape, service boundaries, libraries) are the user's: ask with a recommendation, then record it (`mkit apply "ANSWER Q<n> | text | Why: ..."`, By: delegated if they say "you decide").
- A change with merges, migrations or waits between parts: `/mkit:run "<change>"`.
- User corrects you: `/mkit:learn`. Said "triage": `/mkit:triage`. New project or big feature with no SPEC.md: suggest `/mkit:frame`.
- You assumed something the spec doesn't cover: `mkit add "assumed X" --adjust`.

Change SPEC.md only through `mkit apply` or `/mkit:change`, never by hand.
<!-- mkit -->

## Learned rules

- Ask whether the target is dev/demo or production before framing, designing or choosing technology, and record the answer as a constraint. Why: it changes secrets handling, DEBUG, scaling and hosting, and the frame interview skipped it (2026-10-27).
- Whenever SPEC.md changes (via `mkit apply` or `/mkit:change`), run the readme-coverage skill and fix README.md until it matches. Why: the README answers CHALLENGE.md from the spec's decisions and goes stale when they change (2026-10-27).
