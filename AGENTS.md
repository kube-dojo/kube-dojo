# AGENTS.md — Rules for AI Coding Agents

> This file is read by Codex, Jules, and other AI coding agents working on this repository.
> For Claude-specific instructions see `CLAUDE.md`. For Gemini-specific, see `.claude/rules/gemini-workflow.md`.

---

## Cold start (first call on a fresh session)

**Do not start with `git log` or a grep sweep.** Run:

```bash
bash scripts/cold-start.sh          # services-up + compact briefing in one call
```

The briefing returns `actions.{active, blocked, next}` + `top_modules[]` — answers "what should I touch" in the same call as "what is the global state". Responses carry a weak ETag; send `If-None-Match` for 304 on repeat polls.

Before claiming work: `GET /api/pipeline/leases`. Before fixing a module: `GET /api/module/{key}/state` (structured `diagnostics[]`). Before re-reviewing: `GET /api/reviews?module={key}`. Situational awareness: `GET /api/tracks/readiness` + `GET /api/activity`.

If the API is down, fall back to `STATUS.md` + `CLAUDE.md`.

---

## MANDATORY PRE-SUBMIT CHECKLIST

**Before opening a PR, verify EVERY item. If ANY check fails, fix it BEFORE submitting.**

- [ ] `.venv/bin/ruff check` clean on every Python file you changed
- [ ] `.venv/bin/python scripts/test_pipeline.py` — 0 new failures (2 pre-existing `check_failures` tests + 1 `TestStatusFourStage` order flake are acceptable until their dedicated cleanup lands)
- [ ] `npm run build` passes if you touched content under `src/content/docs/` or Astro config (skip for pure-Python-script changes)
- [ ] No `sys.executable` anywhere — always `.venv/bin/python` explicitly
- [ ] No `@pytest.mark.skip` with empty `pass` bodies, no double-skip decorators
- [ ] Assertions not weakened (no `is True` → `isinstance(..., bool)`)
- [ ] Every changed file is directly related to the task
- [ ] Total files changed < 20 (if more, you likely included artifacts)
- [ ] Diff budget respected (tasks specify a LOC ceiling; if you can't fit, split)
- [ ] Primary repo is NOT on detached HEAD after your work

**If you cannot check every box, your PR will be rejected.**

### Book-only AI History PR exception

For PRs that only touch AI History book/research material and do not affect executable code, generated state, or the published Astro site, do **not** run the expensive curriculum pipeline gate. These PRs include changes strictly limited to:

- `docs/research/ai-history/**` (including all narrative drafts, workflow, and coordination docs within this path)

Required checks for these book-only PRs are:

- [ ] `git diff --check` clean on the changed files
- [ ] cross-family review posted as a PR comment
- [ ] no generated artifacts included
- [ ] primary repo remains on `main`

Skip `.venv/bin/python scripts/test_pipeline.py` for this category. That test suite validates the curriculum pipeline and has low signal for unpublished book research while consuming substantial local and model resources. If a book PR also changes Python, scripts, pipeline behavior, `src/content/docs/`, Astro config, or shared tooling, this exception does not apply and the full checklist above is required.

---

## Non-Negotiable Rules

These rules are ABSOLUTE. Violating any one of them results in immediate PR rejection.

### 1. NEVER push or work directly on `main`

Use git worktrees under `.worktrees/<short-name>` on a new branch. Create with:
```bash
git worktree add .worktrees/<name> -b <branch-name> main
```

The primary checkout (`/Users/krisztiankoos/projects/kubedojo`) must always stay on `main`, never detached, never dirty with uncommitted work-in-progress.

### 2. ALWAYS build from the primary main checkout — NOT a worktree

`npm run build` fails inside `.worktrees/*` because Astro's `node_modules` symlink resolution walks `../../node_modules` one level too shallow. When you need to verify the build:
1. Commit your worktree changes
2. Fetch the branch from the primary checkout
3. Run `npm run build` there

This regression bit PR #282. Don't repeat it.

### 3. ALWAYS use `.venv/bin/python`, not `sys.executable` or `python3`

```bash
# CORRECT
.venv/bin/python scripts/test_pipeline.py
subprocess.run(['.venv/bin/python', 'scripts/uk_sync.py', 'status'])

# WRONG — misses venv deps
python3 scripts/test_pipeline.py
subprocess.run([sys.executable, ...])
```

### 4. NEVER weaken linters or tests to make CI pass

- Fix the source files, not the linter config
- Do not disable rules (`ruff: disable`, `eslint-disable-next-line`, etc.) without an incident-level reason
- Do not comment out assertions
- Do not stub imports with `try/except` that silently return empty results
- Do not skip tests with `@pytest.mark.skip` + `pass`

If a test fails, fix the code or rewrite the test properly.

### 5. NEVER use container or hard-coded absolute paths

This project runs **locally**, not in Docker. Do not use:
- `/app/src/...` — use relative paths from repo root
- `localhost:4321`, `localhost:3000` — Astro dev port; prefer `127.0.0.1:4321`
- Hard-coded machine paths — derive from `Path(__file__).resolve().parent`

Production API binds to `127.0.0.1:8768` per `scripts/services-up`.

### 6. NEVER delete files without explicit instructions

Scripts, docs, and worktrees exist for reasons that aren't always in the current task's scope. If you think something is dead code, flag it in the PR description and leave it alone.

### 7. Scope your PRs — one concern per PR

Do NOT:
- Change `.python-version` in a "fix tests" PR
- Regenerate `.pipeline/state.yaml` or review audit files in a "code change" PR
- Modify `.claude/settings.json` in a "new endpoint" PR
- Touch content under `src/content/docs/` unrelated to the task

If you find something unrelated that needs fixing, create a separate GitHub issue.

### 8. NEVER include auto-generated artifacts in code PRs

These are auto-written by runtime services — they MUST NOT appear in a code PR:

- `.pipeline/state.yaml` (pipeline state machine)
- `.pipeline/reviews/**/*.md` (per-module review logs)
- `.pipeline/logs/**` (timestamped run logs)
- `.bridge/messages.db` (agent bridge DB)
- `.cache/**` (endpoint caches)
- `.pids/**` (service PIDs)
- `dist/**` (Astro build output)
- `node_modules/**`
- Any file matching `*.staging.md`, `*.bak`

If your diff includes these, you staged too aggressively. Re-stage with explicit file names.

### 9. ALWAYS use `scripts/ab` for Codex-from-bridge invocations

The wrapper at `scripts/ab` defaults `CODEX_BRIDGE_MODE=workspace-write` (guarded by `scripts/ops/smoketest_ab_workspace_write.sh`). Override only when you know you need it:

- `CODEX_BRIDGE_MODE=safe scripts/ab ...` — read-only
- `CODEX_BRIDGE_MODE=danger scripts/ab ...` — full network + FS (for `gh`, pip installs, opening PRs)

For a task that requires opening a PR, **you need `danger` mode** — `workspace-write` blocks network.

### 10. NEVER merge a PR without an independent-family review

Hard rule from session 2026-04-11: 4 PRs landed on tests-passing alone and broke pipeline logic. The reviewer must be from a DIFFERENT model family than the writer (Codex writes → Claude or Gemini reviews; Claude writes → Gemini or Codex reviews; etc.). A tests-passing CI run is NOT a review.

Post the review as a PR comment (not `gh pr review --approve` — fails when the same GH identity owns both author and reviewer).

---

## Economical Multi-Agent Delegation

When Codex multi-agent support is enabled, the user explicitly authorizes the main Codex agent to use lower-cost routine subagents for bounded work that can run in parallel without lowering quality. The main agent stays responsible for planning, integration, final review, PR creation, Gemini review routing, and merge decisions.

Prefer `explorer` subagents for read-only investigation and validation. Use `worker` subagents only for mechanical edits with a clearly owned file set and no ambiguity.

Routine subagent model routing:

- Use `gpt-5.4-mini` for general repo search, small summaries, docs/index checks, simple validation, and straightforward documentation edits.
- Use `gpt-5.3-codex-spark` for narrow code-heavy routine tasks where code fluency matters: mechanical Python/TypeScript edits, focused test-failure triage, small refactors with clear ownership, diff review, and targeted validation. This model has a separate usage/limit counter, so prefer it over the main model for bounded coding chores when it can run independently.

Use routine subagents for:

- finding where a feature, config, route, test, or workflow is defined
- summarizing a small file set before the main agent edits it
- checking whether docs, indexes, tests, or scripts reference a changed file
- running simple validation such as `bash -n`, YAML/JSON parsing, `git diff --check`, or targeted tests
- making mechanical edits in a clearly owned file set
- updating straightforward documentation or generated indexes when explicitly in scope
- verifying a narrow behavior while the main agent keeps implementing elsewhere

Do not use routine subagents for architecture decisions, security-sensitive judgment, ambiguous debugging, broad refactors, PR creation, Gemini review routing, merges, destructive actions, or work that blocks the main agent's next immediate step. Give each subagent a narrow task, a clear file ownership boundary when edits are allowed, and instructions not to revert unrelated changes. The main agent must review every routine-subagent diff before finalizing or presenting the work as complete.

Cost controls:

- Use local deterministic tools before model calls: `rg`, `git diff --check`, `bash -n`, `.venv/bin/ruff`, targeted tests, JSON/YAML parsers, and local API endpoints.
- Escalate routine model work in this order when quality allows: `gpt-5.4-mini` for general routine work, `gpt-5.3-codex-spark` for bounded code-heavy routine work, then the main model for judgment/integration.
- Do not spawn a subagent for work the main agent can finish faster than delegation overhead.
- Keep routine delegation to one to three subagents at a time unless the user explicitly asks for a larger sweep.
- Do not let subagents read secrets, source `.envrc`, call `gh`, request reviews, or merge PRs.
- Do not delegate the independent-family review requirement. Gemini review is still mandatory before merge.

---

## Project Architecture

KubeDojo is a cloud-native curriculum site built with **Astro/Starlight**. It is NOT an MkDocs project (the migration happened weeks ago — any AGENTS.md/CLAUDE.md guidance mentioning MkDocs is historical).

```
src/content/docs/              # All content (this is the source of truth)
├── prerequisites/             # Fundamentals tab
├── linux/                     # Linux Deep Dive + Everyday Use
├── cloud/                     # Cloud tab (85 modules)
├── k8s/                       # Certifications tab (CKA/CKAD/CKS/KCNA/KCSA + specialty)
├── platform/                  # Platform Engineering tab (220 modules)
└── uk/                        # Ukrainian translations (~40% coverage)

scripts/
├── cold-start.sh              # Session entry point
├── services-up                # Idempotent bring-up for API + pipeline workers
├── ab                         # Agent bridge CLI (defaults CODEX_BRIDGE_MODE=workspace-write)
├── ai_agent_bridge/           # Bridge internals (_cli.py, _codex.py, _gemini.py, ...)
├── agent_runtime/             # Model adapters (codex.py, claude.py, gemini.py)
├── dispatch.py                # Direct Gemini/Claude CLI dispatch
├── local_api.py               # :8768 briefing + module state API
├── v1_pipeline.py             # Quality pipeline v1 (serial)
├── pipeline_v2/               # Quality pipeline v2 (queue + workers)
├── uk_sync.py                 # Ukrainian translation pipeline
├── check_site_health.py       # Health gate
├── check_links.py             # Link gate
├── check_citations.py         # Citation gate (2026-04-18)
├── ops/                       # Smoketests (executable, exit-coded)
└── prompts/module-writer.md   # Standard prompt for content writing

.pipeline/
├── state.yaml                 # Pipeline state (auto-generated — never in PRs)
├── reviews/**/*.md            # Per-module review logs (auto-generated — never in PRs)
└── logs/**                    # Timestamped run logs (auto-generated)

.bridge/messages.db            # Agent bridge message store (auto-generated)

docs/                          # Internal project docs (pedagogy, rubrics, sessions)
├── quality-rubric.md          # 8-dim rubric (reviewer's source of truth)
├── quality-audit-results.md   # STALE as of 2026-04-03 — live scores via /api/quality/scores
├── pedagogical-framework.md
├── rubric-profiles/*.yaml     # Per-track rubric overrides
└── sessions/**                # Session handoffs

.claude/
├── rules/*.md                 # Scoped rules (auto-loaded by Claude Code)
├── settings.json              # Shared permissions (committed)
└── settings.local.json        # Personal overrides (gitignored)
```

**Key facts:**
- Python: `.venv/` at repo root, Python 3.12+, use `.venv/bin/python` explicitly
- Build: `npm run build` → `dist/` (~56s for ~1,800 pages)
- Dev: `npx astro dev` (default port 4321)
- Local API: `http://127.0.0.1:8768` (started by `scripts/services-up`)
- K8s version target for content: **1.35**
- Agent bridge DB: `.bridge/messages.db`
- Pipeline v2 is the current default; v1 is maintained for backward compatibility
- Frontmatter requires `title:` and `sidebar.order:` — see `.claude/rules/new-content-checklist.md`
- Ukrainian content lives under `src/content/docs/uk/` mirroring the EN tree

---

## Common Anti-Patterns

| Anti-Pattern | What to Do Instead |
|---|---|
| Running `python3` or `python` without venv prefix | `.venv/bin/python` every time |
| Building from a `.worktrees/` directory | Switch to primary main, run build there |
| Skipping `scripts/ab` and calling `codex exec` directly | Always use `scripts/ab` — it sets the default sandbox mode we rely on |
| Using `workspace-write` (default) for PR-opening tasks | `CODEX_BRIDGE_MODE=danger` when task needs `gh` or network |
| Parsing `docs/quality-audit-results.md` for current scores | Use `/api/quality/scores` (once #303 lands) — static audit is frozen at 2026-04-03 |
| Committing `.pipeline/state.yaml` or `.bridge/messages.db` | These are runtime state; add-by-glob will pull them in — stage explicit files only |
| Editing `mkdocs.yml` (file doesn't exist) | Navigation is handled by Starlight; edit `astro.config.mjs` and frontmatter `sidebar.order` |
| Running `mkdocs build` or `mkdocs serve` | `npm run build` / `npx astro dev` |
| Closing issues without adversarial review | Dispatch review to a cross-family model first, post review as comment, THEN close |
| Parallelizing multiple Gemini calls from pipeline code | Gemini workloads must stay sequential — user runs concurrent workloads elsewhere |
| Leaving the primary on detached HEAD | After worktree ops or merges, confirm primary is on `main` |
| Creating a PR without an issue reference | Tag the issue in commit title `feat(foo): bar (#N)` and PR body |

---

## When delegated a GitHub issue via the agent bridge

The expected workflow is:

1. Read the issue: `gh issue view <N> --repo kube-dojo/kube-dojo.github.io`
2. Create a worktree: `git worktree add .worktrees/<short-name> -b <branch-name> main`
3. Implement inside the worktree (never on primary `main`)
4. Run the quality gates listed in the pre-submit checklist
5. Open a PR: `gh pr create --title "<type>(scope): <summary> (#N)" --body "<summary + test results + LOC diff>"`
6. Do NOT merge — Claude (or another cross-family reviewer) reviews first per rule 10
7. Post back via the bridge with the PR URL and a one-line summary of the design choice

If the task exceeds the stated LOC budget (usually ≤200 LOC), **stop and post a split plan as a comment on the issue** instead of shipping a mega-PR. Splitting is a first-class outcome, not a failure.

Don't decline full PR workflows as "too large for bridge" — the bridge handles this exact pattern 20+ times per session. If you genuinely cannot proceed (env constraints, missing context), post a bridge response explaining WHY, with the specific command that failed. Don't improvise around rules.

---

## Human and Agent Teamwork

When collaborating on complex or open-ended tasks (such as writing narrative history or designing curriculum), both AI agents and human contributors must adhere to a strict standard of **Honesty Over Output**:

- **No Fabrication:** If you cannot reach a requested length (e.g., a 4,000-word chapter constraint) or fulfill a specific structural requirement based *only* on the verified data you have gathered, **you must not hallucinate or pad the content**.
- **Admit Limitations:** It is always better to be honest and explicitly state that you have exhausted the available verified research than to invent historical dialogue, fictionalize events, or fabricate data to meet an arbitrary target.
- **Team Collaboration:** We operate as a team. If an agent lacks the data or context to fulfill a requirement safely, they flag it for the human operator (or a cross-family agent) to help source the missing information. Conversely, agents help human operators identify where narrative ambitions have outpaced the underlying research contracts. Honesty and rigorous adherence to the truth are rewarded more highly than blindly satisfying a metric.
- **Pedagogical Approach to Math:** When explaining complex mathematical concepts or algorithms, ensure the explanations are accessible and engaging. Avoid dry recitations of equations; instead, focus on the historical context, explain the "why", and use clear, relatable demonstrations or analogies to make the math easy to digest for non-mathematicians.
