# CI catches broken links and bad prose, but not valid-but-wrong metadata (+ fork-PR friction)

**Date:** 2026-06-04 · **Category:** ci/build · **Surfaced by:** PR #1742 (our first external contributor, @H3xKatana)

## What broke
`module-1.3-helm.md` shipped with `lab.url: https://killercoda.com/playgrounds/scenario/kubernetes` — the **generic** KillerCoda playground instead of the module-specific scenario `https://killercoda.com/kubedojo/scenario/cka-1.3-helm`. The "Launch Lab" button sent learners to an empty generic playground. It was the **sole outlier** across all 269 lab URLs sitewide (268 already followed the `kubedojo/scenario/` convention), and it sat on `main` unnoticed until an external contributor reported it.

## Why (root cause)
The defect class is **valid-but-wrong metadata**, which fell through every gate:

1. **It's frontmatter, not teaching content.** Cross-family reviewers (human and LLM) are briefed to scrutinize prose, code, exercises, and technical accuracy. The `lab:` block is boilerplate they skim past, and they had no canonical value to compare against.
2. **The bad URL returned HTTP 200.** `killercoda.com/playgrounds/scenario/kubernetes` is a real, live page — just the wrong one. The link checker (`check_site_health.py`) only flags broken/404 links, so a reachable-but-wrong URL passes. The defect is *semantic*, not a dead link.
3. **`verify_module.py` never inspected `lab.url`.** The #388 content contract (density, structure, sources, anti-fab) is blind to frontmatter URL correctness.
4. **The Astro Zod schema only checks `url()`** (`src/content.config.ts`), i.e. "is it a syntactically valid URL" — not "does it match our scenario convention." And per the sibling autopsy [`ci-no-full-build-gate.md`](ci-no-full-build-gate.md), PR CI runs no full `astro build` anyway, so even a tighter schema wouldn't gate PRs.
5. **No convention-conformance gate existed.** 268/269 modules conformed by authoring discipline alone. Nothing *enforced* the pattern, so one straggler (authored before the convention solidified) stayed invisible.

### Two adjacent CI frictions this PR also exposed
6. **Cross-family review can't run on any fork PR.** The job reads `API_KEY: ${{ secrets.GEMINI_API_KEY }}`, but GitHub withholds repo secrets from `pull_request` runs triggered by a fork (anti-exfiltration). So `cross_family_review.sh` aborts with `API_KEY required` and shows a misleading red ❌ on every external contribution — looking like the contributor's change failed review when the job simply couldn't authenticate.
7. **Required CodeQL checks never run on docs-only PRs → permanent BLOCKED.** Branch protection required `Analyze (actions|javascript-typescript|python)`, but CodeQL is path-filtered to code, so a markdown-only PR never triggers them. GitHub then waits forever for required checks that will never report, forcing an admin-merge on **every** content PR (and on external PRs, admin-merge is the only escape — the contributor can't self-merge).

## Prevention
- **`scripts/ci/check_lab_urls.py`** — a deterministic, stdlib-only validator asserting every `lab.url` matches `https://killercoda.com/kubedojo/scenario/<slug>`. Wired into the `link-check` job (runs on every PR, fork-safe, no secrets). Includes a `--selftest`. Confirmed it would have flagged the #1742 URL.
- **Skip the cross-family review job on fork PRs** via `if: github.event.pull_request.head.repo.full_name == github.repository`. Internal-branch PRs still get the review; external contributors stop seeing a false red ❌.
- **Removed the 3 CodeQL `Analyze` contexts from branch protection's required checks.** CodeQL still runs (advisory on code PRs + on push to `main`); it just no longer blocks content/external PRs. `link-check` was de-path-filtered so it always runs and serves as a universal required gate alongside the always-on `Incident dedup gate`.
- **General lesson:** the pipeline was built to catch *content* defects and *broken* (404) links. It had no defense against *valid-but-wrong* metadata. When adding any frontmatter field with a project convention (a URL host, an id prefix, a slug shape), add a conformance check — `url()` / "is reachable" is not "is correct."

Memory: `feedback_fork_pr_ci_behavior`, `feedback_lab_url_convention`.
