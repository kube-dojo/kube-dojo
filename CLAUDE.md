# CLAUDE.md

KubeDojo — free, open-source cloud native curriculum.

## Agent Usage

- Don't spawn agents for work a single Grep/Read/Glob can do — it's slower and wasteful.
- Agents ARE worth it for genuinely parallel work and context isolation (large refactors, independent research).
- Batch direct tool calls in one message when possible (3 Greps > 3 agents).
- Keep sessions long (`/continue`) — cache hits are ~95% within a session.

## Project Overview

**Website**: https://kube-dojo.github.io/ (Starlight/Astro)

**Site tabs**: Home | What's New | Fundamentals | Cloud | Certifications | Platform Engineering

**Tracks**:
- **Fundamentals** — Zero to Terminal, Everyday Linux, Cloud Native 101, K8s Basics, Philosophy & Design, Modern DevOps
- **Cloud** — Rosetta Stone, AWS/GCP/Azure Essentials (12 each), Architecture Patterns, EKS/GKE/AKS Deep Dives, Advanced Ops, Managed Services, Enterprise & Hybrid
- **Certifications** — CKA, CKAD, CKS, KCNA, KCSA, Extending K8s, 10+ tool certs
- **Platform Engineering** — Foundations (7 sections), Disciplines (12 sections), Toolkits (17 categories)

**Ukrainian translation**: ~40% (Prerequisites, CKA, CKAD). Files in `src/content/docs/uk/`.

## Session Workflow

1. **READ `STATUS.md` FIRST** — instant context
2. Use `scripts/prompts/module-writer.md` for new modules
3. Send to Gemini for review before closing issues
4. **UPDATE `STATUS.md`** before ending session

## Build & Serve

```bash
npm run build              # builds to dist/, ~56s for 1,297 pages
npx astro dev              # dev server with hot reload
npx astro preview          # preview built site
```

## Key Files

| File | Purpose |
|------|---------|
| `STATUS.md` | Current work, progress, blockers |
| `CLAUDE.md` | This file — project overview |
| `.claude/rules/` | Scoped rules (quality, translation, checklist, Gemini) |
| `.claude/settings.json` | Shared permissions (committed) |
| `.claude/settings.local.json` | Personal overrides (gitignored) |
| `docs/pedagogical-framework.md` | Educational research & guidelines |
| `docs/quality-rubric.md` | 1-5 rubric for module/lab quality |
| `docs/quality-audit-results.md` | Audit of 31 modules (2026-04-03) |
| `scripts/prompts/module-writer.md` | Standard prompt for module creation |
| `scripts/dispatch.py` | Direct CLI dispatch for Gemini/Claude |
| `astro.config.mjs` | Starlight config (sidebar, i18n, theme) |
| `package.json` | Node.js dependencies |

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

## Commands Available

- `/review-module [path]` — Review single module quality
- `/review-part [dir]` — Review entire part for consistency
- `/verify-technical [path]` — Verify commands and YAML accuracy

## Practice Environment Approach

- **Lightweight**: kind/minikube for most exercises
- **Multi-node**: kubeadm only when topic requires
- **Mock exams**: Questions + self-assessment, not simulation
- **Recommend killer.sh** for realistic exam simulation

## Three-Pass Exam Strategy

1. **Pass 1**: Quick wins (1-3 min) first
2. **Pass 2**: Medium tasks (4-6 min)
3. **Pass 3**: Complex with remaining time

## Git Workflow

- Branch: `main`
- Commits: `feat:`, `docs:`, `fix:` prefixes with `#N` issue refs
- Build before push (0 warnings)
- Never push without verifying

## Links

- **Repo**: https://github.com/kube-dojo/kube-dojo.github.io
- **Writer Prompt**: `scripts/prompts/module-writer.md`
- **Gemini Dispatch**: `scripts/dispatch.py`
