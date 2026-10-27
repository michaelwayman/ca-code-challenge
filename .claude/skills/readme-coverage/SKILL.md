---
name: readme-coverage
description: Use when checking that README.md answers everything CHALLENGE.md asks of the candidate, before submitting, or after editing either file. Builds a one-to-one table of challenge item to README answer.
---

# readme-coverage

Maps every README obligation and every live-defence question in `CHALLENGE.md` to an answer in `README.md`, one row per item, and keeps that table in the README under `## Challenge coverage`.

## Steps

1. **Read `CHALLENGE.md` in full** and number every item in three groups:
   - **D** README deliverables: each bullet under "What to deliver" > "A `README.md` with". Split the last bullet into its sub-asks (modeling decisions, what to do differently, AI defaults chosen over own preference).
   - **Q** Each numbered question under "Decisions you will defend live". Split a question into one item per distinct sub-question (`Q1a`, `Q1b`, ...).
   - **P** Documentation asks stated inside a pillar (e.g. define "top review", how to compile the SCSS, local vs remote token verification and why).
2. **Read `README.md` and `written-answers.md`** (modeling, hindsight, AI defaults live there) and find the one section that answers each item. Links to it use `written-answers.md#anchor`.
3. **Write the answer** in 12 words or fewer, from the README, the code, or `mkit show <ID>`. Say the decision, not the reasoning: the linked section holds the detail. No commands longer than one short line, no restating the question. Never invent a decision. Design decisions are the user's: if the answer is not on record, mark the row `GAP` and ask.
4. **Check one-to-one** before writing: every item has exactly one row; every row cites an existing heading (`grep -n '^#' README.md written-answers.md`); no row without a challenge item. Report gaps and missing sections to the user first.
5. **Group and sort** the rows before writing (each item in exactly one group, groups in this order):
   1. **Run and operate**: the D items about running things, ordered by the reader's workflow (start the stack, migrate, authenticate, test).
   2. **Data and migration**: Pillar 1 items and the schema, postmeta and migration questions.
   3. **API and component**: Pillars 2 and 3 items and the API contract and component questions.
   4. **Styling**: Pillar 4 items and the SCSS question.
   5. **Auth and shared library**: Pillars 5 and 6 items and the service boundary and library questions.
   6. **Write-up**: the modeling decisions, hindsight and AI defaults sub-asks.
   Within a group, put P rows first (what must be documented), then Q rows, each in challenge order. If CHALLENGE.md changes its pillars, keep the same idea: reader workflow first, then one group per pillar area, write-up last. Never create a group for a single row unless no existing group fits.
6. **Write the tables** under `## Challenge coverage` in README.md, one `###` heading and one table per group, replacing the existing section if present (everything up to the next `## `), so reruns never duplicate it. The only text under the heading is one line: `D` deliverable, `P` pillar doc ask, `Q` live question. Do not edit SPEC.md or CHALLENGE.md.

## Table format

```
### Data and migration

| # | Challenge asks | Answer | Where |
|---|---|---|---|
| Q1a | Store, derive or both: average rating? | Derived: aggregate over reviews, 1 decimal. | [Modeling decisions](#modeling-decisions) |
```

The `#` column keeps the IDs from step 1, so the one-to-one check still works across all tables. The asks column is the challenge wording cut to 8 words or fewer. The Where column is one link, the single best section. The whole `## Challenge coverage` section must stay under 600 words (`wc -w` of the section); if it does not, shorten answers before anything else, and never add prose to the README to support a row.
