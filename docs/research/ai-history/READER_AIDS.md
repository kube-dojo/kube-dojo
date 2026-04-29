# Reader Aids — Layout for AI History Chapters

This document defines the canonical reader-aid layout for the AI History book, established by the Chapter 1 prototype (Issue #561). Chapters 2–72 follow this template.

## Hard rule — prose body is bit-identical to the verified draft

Reader aids are **additions**, never edits. They sit before the first prose paragraph and after the last. They never replace, abridge, or reword the existing prose body. After landing aids on a chapter, run:

```bash
git diff main -- src/content/docs/ai-history/ch-XX-*.md | grep '^-[^-]'
```

If anything returns, a prose line was deleted or modified — revert and try again.

## Layout

### Tier 1 — every chapter

These four aids land on every chapter. They serve readers who want a fast on-ramp, a roster, a calendar, or a plain-words door into specialised vocabulary.

1. **TL;DR callout** — `:::tip[In one paragraph]` Starlight aside, **≤80 words**. Visible by default. Sits immediately after the frontmatter close. Summarises the chapter's load-bearing claim, names the central figure(s) and date, and points to the historiographical correction the chapter carries (if any).
2. **Cast of characters** — `<details><summary><strong>Cast of characters</strong></summary>` collapsible. **6 rows max**. Columns: Name | Lifespan | Role. Sourced strictly from the chapter's `people.md`. Use `—` in the Lifespan column when the contract does not give dates; do not invent.
3. **Timeline** — `<details><summary><strong>Timeline (year-range)</strong></summary>` collapsible. Mermaid `timeline` directive (Mermaid 11.14, in production use across the site). Include only events listed under "In scope" in the chapter's `timeline.md`. Do **not** include excluded or forward-pointing events; those exist as boundary markers in the contract, not narrative beats.
4. **Plain-words glossary** — `<details><summary><strong>Plain-words glossary</strong></summary>` collapsible. **5–7 terms**, each with a 1–2 sentence plain-English definition. Pick terms a non-specialist would stumble on while reading the prose. Definitions must trace to the contract or to the chapter's primary sources.

### "Why this still matters today" — every chapter

Sits after the last prose paragraph.

5. **Why this still matters today** — `:::note[Why this still matters today]` Starlight aside, **≤120 words**. Bridges the chapter's content to today's practitioner-visible technology. Keep claims high-level and verifiable ("every digital circuit descends from Boolean algebra"); do **not** name specific named systems with claimed citations. This is the single place forward-pointing language is permitted.

### Tier 2 — selected chapters only

These aids apply only when the topic genuinely benefits from them. Don't add them to chapters where they would be filler.

6. **The math, on demand** — `<details><summary><strong>The math, on demand</strong></summary>` collapsible. Mathematical notation, equations, derivations relevant to the chapter, listed as bullets with brief commentary. Use `$…$` inline math (the renderer accepts dollar-delimited LaTeX as a stylistic convention; see `grep '\$' <chapter>` for in-prose usage). Apply to: **Ch01, Ch04, Ch15, Ch24, Ch25, Ch27, Ch29, Ch44, Ch50, Ch55, Ch58.**
7. **Architecture sketch** — A diagram (Mermaid `flowchart`, `sequenceDiagram`, or block diagram) of the system the chapter describes. Apply to: **Ch41, Ch42, Ch49, Ch50, Ch52, Ch58.** Form to be finalised in those chapters; not part of the Ch01 prototype.

## Source discipline

Every claim in every aid must trace to one of:

- the chapter's `brief.md`
- the chapter's `people.md`
- the chapter's `timeline.md`
- the chapter's `sources.md`

If a fact is not in the contract, it does not appear in the aids. The single exception is the closing "Why this still matters today" aside, where the chapter is permitted high-level forward-pointing language at the level of "every digital circuit descends from Boolean algebra" — not at the level of "this maps directly to Postgres planner B" with a claimed citation. Keep the bridge honest.

When the contract conflicts (e.g. two sources disagree on a date), use the locution the chapter prose uses, or the resolution in `brief.md → Conflict Notes`. Do not promote a single-source ("Yellow") fact to a confident-sounding aid.

## Caps and constraints

| Aid | Cap |
|---|---|
| TL;DR (`:::tip[]`) | ≤80 words |
| Cast of characters | 6 rows max |
| Timeline | in-scope events only; no excluded events |
| Plain-words glossary | 5–7 terms |
| "The math, on demand" | bullets only; one-sentence commentary per equation |
| "Why this still matters today" (`:::note[]`) | ≤120 words |

## Markdown syntax reference

```markdown
:::tip[In one paragraph]
…content…
:::

<details>
<summary><strong>Cast of characters</strong></summary>

| Name | Lifespan | Role |
|---|---|---|
| … | … | … |

</details>

<details>
<summary><strong>Timeline (1815–1864)</strong></summary>

\`\`\`mermaid
timeline
    title …
    1815 : Born …
\`\`\`

</details>

:::note[Why this still matters today]
…content…
:::
```

Inline math uses `$x^2 = x$`. The renderer treats `$…$` as a stylistic convention; see existing chapter prose (`grep '\$' src/content/docs/ai-history/ch-XX-*.md`) for live examples.

## Default visibility

- `:::tip[]` and `:::note[]` asides are **visible by default**. They are the first and last things a casual reader sees; they must work as a standalone summary.
- `<details>` blocks are **collapsed by default**. Readers expand them on demand. The chapter prose stands on its own without the aids — the aids are aids, not load-bearing content.

## Verification before commit

1. `npm run build` runs clean (0 errors, ~56s).
2. `.venv/bin/python scripts/check_site_health.py` returns 0 errors.
3. `git diff main -- src/content/docs/ai-history/ch-XX-*.md | grep '^-[^-]'` returns empty.

## Prototype reference

The Ch01 prototype (`src/content/docs/ai-history/ch-01-the-laws-of-thought.md`) is the canonical reference implementation. When in doubt about formatting, syntax, or tone, copy from there.
