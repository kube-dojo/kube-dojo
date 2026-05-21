# CLAUDE.md

KubeDojo — free, open-source cloud native curriculum.

## Agent Orientation (first call on a cold start)

The orientation sequence is API-first to reduce token use and get a complete cold-start picture (`actions`, blockers, leases, and top modules) before reading local handoff files.

1. Pull compact briefing:
```bash
curl -s --max-time 2 "http://127.0.0.1:8768/api/briefing/session?compact=1"
```
If 200, parse the payload and proceed. If timeout or non-200, record `API down` — still run steps 2 and 3 (local filesystem state is independent of the API), then fall back to step 6 instead of step 4.

2. Run local working-tree awareness:
```bash
git status --short
```

3. Scan for blocking decisions:
```bash
ls docs/decisions/pending/
```
Respect `.claude/rules/decision-card.md` and only process what is declared blocking.

4. Pull the latest handoff via API (preferred) or fall back to the file:
```bash
curl -s --max-time 2 "http://127.0.0.1:8768/api/session/current"
```
Returns the most recent handoff path plus predecessor chain. Only read the underlying `docs/session-state/<date>-*.{md,html}` file when the briefing leaves a real narrative-why gap; use the path from the API response or from STATUS.md's `Latest handoff` row.

5. Optional situational check for recent orchestration context:
```bash
curl -s --max-time 2 "http://127.0.0.1:8768/api/activity?limit=30"
```

6. Fallback path if API is down:
`STATUS.md` → latest handoff → `MEMORY.md` → `CLAUDE.md`.

**Before you claim/fix/re-review work**:
- `GET /api/pipeline/leases`
- `GET /api/module/{key}/state`
- `GET /api/reviews?module={key}`

**Self-discovery**: `curl -s http://127.0.0.1:8768/api/state/manifest` returns the categorized route inventory (cold_start / dashboards / pipeline / etc.) — use this when uncertain which endpoint serves a given concern.

**Orientation punch-line**: `curl -s --max-time 2 http://127.0.0.1:8768/api/orient` returns the single primary action + up to 3 alternatives + blockers/alerts in ~1.3 KB. Use this when the briefing is overkill.

Standalone session = main orchestrator. Drive the queue; ask only on irreversible or ambiguous actions.

Full agent recipe: [`scripts/agent_onboarding.md`](scripts/agent_onboarding.md).

## Agent Usage

- Don't spawn agents for work a single Grep/Read/Glob can do — it's slower and wasteful.
- Agents ARE worth it for genuinely parallel work and context isolation (large refactors, independent research).
- Batch direct tool calls in one message when possible (3 Greps > 3 agents).
- Keep sessions long (`/continue`) — cache hits are ~95% within a session.

## Multi-agent deliberation (`ab discuss`)

For high-leverage decisions only (architecture, threshold freezes, contested NEEDS CHANGES, bets affecting 100+ modules). Use `scripts/ab discuss <channel> --with claude,codex,gemini --max-rounds 3`. See `.claude/rules/decision-card.md` for the full protocol (deliberation not quorum; emit a Decision Card on disagreement only). Scan `docs/decisions/pending/` at cold start.

## Project Overview

**Website**: https://kube-dojo.github.io/ (Starlight/Astro)

**Site tabs**: Home | What's New | Fundamentals | Cloud | Certifications | Platform Engineering

**Tracks**:
- **Fundamentals** — Zero to Terminal, Everyday Linux, Cloud Native 101, K8s Basics, Philosophy & Design, Modern DevOps
- **Cloud** — Rosetta Stone, AWS/GCP/Azure Essentials (12 each), Architecture Patterns, EKS/GKE/AKS Deep Dives, Advanced Ops, Managed Services, Enterprise & Hybrid
- **Certifications** — CKA, CKAD, CKS, KCNA, KCSA, Extending K8s, 10+ tool certs
- **Platform Engineering** — Foundations (7 sections), Disciplines (12 sections), Toolkits (17 categories)

**Ukrainian translation**: ~40% (Prerequisites, CKA, CKAD). Files in `src/content/docs/uk/`.

> **HTML-first artifact policy:** see [`docs/migrations/html-first/plan.html`](docs/migrations/html-first/plan.html) — orchestrator artifacts (audit reports, dispatch briefs, bug autopsies, batch summaries, PR review explainers, session handoffs) default to HTML; STATUS.md / CLAUDE.md / `.claude/rules/` / memory stay Markdown.

## Session Workflow

1. **Orient via `/api/briefing/session`** (see *Agent Orientation* above). `STATUS.md` is the fallback when the API is down.
2. Use `scripts/prompts/module-writer.md` for new modules
3. Send completed work to the designated cross-family reviewer (see `docs/review-protocol.md`) before closing issues
4. **At session end**: write the full handoff to a new `docs/session-state/YYYY-MM-DD-<topic>.{md,html}` file. Prefer `.html` per the HTML-first artifact policy (see `docs/migrations/html-first/plan.html`); use `.md` only if the handoff is brief and a markdown sidecar (`.notes.md`) is not warranted. Then update `STATUS.md` (the index) — promote the new file to "Latest handoff", shift the previous Latest into "Predecessor chain", refresh "Cross-thread notes" / `## TODO` / `## Blockers`. **Do NOT inline the full handoff into STATUS.md** — it is an index, not a log. The briefing API (`scripts/local_api.py:_parse_status_md`) parses `## TODO` (unchecked `- [ ]`) and `## Blockers` (`- `) from STATUS.md, so keep those headings populated.

## Build & Serve

```bash
npm run build              # builds to dist/, ~38s for 1,999 pages
npx astro dev              # dev server with hot reload
npx astro preview          # preview built site
```

## Key Files

| File | Purpose |
|------|---------|
| `STATUS.md` | Current work, progress, blockers |
| `.claude/rules/` | Scoped rules (quality, translation, decision-card, etc.) |
| `.claude/settings.json` | Shared permissions (committed) |
| `.claude/settings.local.json` | Personal overrides (gitignored) |
| `docs/pedagogical-framework.md` | Educational research & guidelines |
| `docs/quality-rubric.md` | 1-5 rubric for module/lab quality |
| `scripts/prompts/module-writer.md` | Standard prompt for module creation |
| `scripts/dispatch.py` / `scripts/dispatch_smart.py` | CLI dispatchers |
| `astro.config.mjs` | Starlight config (sidebar, i18n, theme) |

## Curriculum Structure

```
src/content/docs/          # English content (648 files)
├── prerequisites/         # Fundamentals tab
├── linux/                 # Linux Deep Dive + Everyday Use
├── cloud/                 # Cloud tab (85 modules)
├── k8s/                   # Certifications tab (169 modules)
├── platform/              # Platform Engineering tab (199 modules)
└── uk/                    # Ukrainian translations (115 files)
    ├── prerequisites/
    ├── k8s/cka/
    └── k8s/ckad/
```

## Practice Environment Approach

- **Lightweight**: kind/minikube for most exercises
- **Multi-node**: kubeadm only when topic requires
- **Mock exams**: Questions + self-assessment, not simulation
- **Recommend killer.sh** for realistic exam simulation

## Git Workflow

- Branch: `main`
- Commits: `feat:`, `docs:`, `fix:` prefixes with `#N` issue refs
- Build before push (0 warnings)
- Never push without verifying

## Links

- **Repo**: https://github.com/kube-dojo/kube-dojo.github.io
