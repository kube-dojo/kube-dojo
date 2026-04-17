# Repository Guidelines

## Agent Orientation (first call on a cold start)

**Do not start with `git log` or a grep sweep.** Hit the local API first:

```bash
curl -s http://127.0.0.1:8768/api/briefing/session?compact=1   # ~0.7K tokens
curl -s http://127.0.0.1:8768/api/schema                       # endpoint index
```

The briefing returns `actions.{active, blocked, next}` + `top_modules[]` — answers "what should I touch" in the same call as "what is the global state". Responses carry a weak ETag; send `If-None-Match` for 304 on repeat polls.

Before claiming work: `GET /api/pipeline/leases`. Before fixing a module: `GET /api/module/{key}/state` (structured `diagnostics[]`). Before re-reviewing: `GET /api/reviews?module={key}`. Situational awareness: `GET /api/tracks/readiness` + `GET /api/activity`.

Full recipe: [`scripts/agent_onboarding.md`](scripts/agent_onboarding.md). If the API is down, fall back to `STATUS.md` + `CLAUDE.md`.

Everything below this block is historical MkDocs-era guidance; for current site structure see the Curriculum Structure section in `CLAUDE.md`.

## Project Structure & Module Organization
- Course content lives under `docs/` and is grouped by track: `docs/prerequisites/`, `docs/linux/`, `docs/k8s/`, and `docs/platform/`. Each track contains numbered `module-X.Y-name.md` files plus local `README.md` overviews.
- Navigation is defined in `mkdocs.yml`; add new pages there to surface them in the site.
- Built output is written to `site/` by MkDocs—do not edit it manually. `exercises/` is reserved for future hands-on labs.

## Build, Test, and Development Commands
- Install tooling: `pip install -r requirements.txt`.
- Live preview with reload: `mkdocs serve -a 0.0.0.0:8000` (serves the docs locally).
- Static build check: `mkdocs build` (writes the generated site to `site/` and fails on syntax errors).
- Optional publish: `mkdocs gh-deploy` if you have repo permissions.

## Coding Style & Naming Conventions
- Markdown-first; keep headings concise (`## Topic`) and prefer unordered lists for checklists or summaries.
- File naming: lowercase, hyphen-separated, and numbered (`module-2.3-storage.md`) to match the learning path.
- Keep sections short (2–6 bullets or paragraphs). Use fenced code blocks with language tags for commands and YAML.
- Avoid external images when possible; inline examples and text explanations are preferred for portability.

## Testing Guidelines
- Run `mkdocs build` before submitting to catch broken links, malformed Markdown, or navigation errors.
- For new commands or YAML snippets, validate them locally (e.g., `kubectl explain`, `kind create cluster`) and note assumptions inline.
- When adding exercises, include expected outcomes and cleanup steps so readers can reset their environment.

## Exercises & Practice Environments
- Align with Issue #15: prefer lightweight clusters (kind/minikube) by default; only introduce multi-node or topic-specific clusters when required and state why.
- Exercise layout lives under `exercises/cka/partN-*/N.N-topic/` with `README.md`, optional `setup.sh`, and `verify.sh` that reports granular checks (✓/✗ plus hints). Include complexity tags `[QUICK]`, `[MEDIUM]`, or `[COMPLEX]`.
- For verification scripts, aim for helpful feedback (what passed, what failed, and a short hint) rather than simple pass/fail.

## Curriculum Monitoring
- Follow Issue #14 for certification source tracking. Before adding/updating CKA/CKAD/CKS/KCNA/KCSA modules, confirm the CNCF/LF curriculum version and note the check date in the PR description.
- If a curriculum change impacts navigation, update `mkdocs.yml` and summarize the delta (what changed and where) in the PR body.

## Commit & Pull Request Guidelines
- Commit messages: short, imperative, and scoped (e.g., `Add kcna scheduling module outline`).
- Pull requests should state the goal, summarize notable changes, and link any related issue. If altering navigation or moving files, call that out explicitly.
- Include screenshots only when they meaningfully demonstrate rendered formatting; otherwise rely on `mkdocs build` output.
- Ensure contributions keep the text authoritative and vendor-neutral; avoid promotional links or tool bias unless clearly marked as opinionated.
