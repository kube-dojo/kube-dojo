# CI has no full astro-build gate → frontmatter schema breaks reach main

**Date:** 2026-06-04 (session 103) · **Category:** ci/build

## What broke
`npm run build` exited 1 on `k8s/cks/part5-supply-chain-security/module-5.2-image-scanning.md`:
`InvalidContentEntryDataError — lab.difficulty: Invalid option: expected one of "beginner"|"intermediate"|"advanced"`. The file carried `lab.difficulty: medium`. This broke the entire site build (and any deploy), because Astro validates every content-collection entry's frontmatter against a Zod schema at build time and aborts on the first violation.

## Why (root cause)
1. **CI never runs a full `astro build`.** PR checks are: site-health link check, CodeQL, incident-dedup gate, and the gemini cross-family review. None of them load the Astro content-collection schema, so an invalid frontmatter enum (`lab.difficulty`, `lab.environment`, …) passes CI and merges.
2. **`verify_module.py` validates the #388 content contract** (density, structure, sources, anti-fab) **but not the Astro Zod schema** — so the per-module gate the waves rely on is also blind to it.
3. **The cloud waves (sessions 96–102) treated "PR CI green" as "build green"** and skipped the local `npm run build` (STATUS.md even called PR CI "the de-facto build/link gate"). The invalid value was introduced by an earlier commit (`b52f9fce`) and sat broken on main until session 103 ran a local build after merging PR #1788.

## Prevention
- **Run `npm run build` in the PRIMARY dir before declaring any content wave done** (pipe to a file + grep `InvalidContentEntryDataError|does not match|Build failed`; never Read the full log; the em/en-dash "LaTeX-incompatible … strict mode 'warn'" lines are warnings, not failures; the build halts at the FIRST schema error so fix-and-rebuild to find any behind it).
- **Add a build/schema gate to CI** on `src/content/docs/**` changes: either a full `astro build`, or a lightweight content-collection validate step, or an explicit `lab.difficulty` enum check inside `check_site_health.py` / `verify_module.py`. (Follow-up — see STATUS.md TODO.)
- Valid `lab.difficulty` values are `beginner | intermediate | advanced` ONLY. Map medium→intermediate, easy→beginner, hard→advanced.

Memory: `feedback_pr_ci_has_no_full_astro_build`.
