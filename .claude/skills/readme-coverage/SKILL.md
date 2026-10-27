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
2. **Read `README.md`** and find the one section that answers each item.
3. **Write the answer** in 1-2 sentences taken from the README, the code, or `mkit show <ID>` for recorded decisions. Never invent a decision. Design decisions are the user's: if the answer is not on record, mark the row `GAP` and ask.
4. **Check one-to-one** before writing: every item has exactly one row; every row cites an existing heading (`grep -n '^#' README.md`); no row without a challenge item. Report gaps and missing sections to the user first.
5. **Write the table** under `## Challenge coverage` in README.md, replacing the existing section if present (everything up to the next `## `), so reruns never duplicate it. Do not edit SPEC.md or CHALLENGE.md.

## Table format

```
| # | Challenge asks | Answer | Where |
|---|---|---|---|
| Q1a | Store, derive or both: average rating? | Derived: aggregate over reviews, 1 decimal. | [Modeling decisions](#modeling-decisions) |
```

The `#` column uses the IDs from step 1, in challenge order (D, then P, then Q). Quote or tightly condense the challenge wording so the row can be matched back to it.
