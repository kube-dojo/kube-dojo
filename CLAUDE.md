# CLAUDE.md

KubeDojo — free, open-source cloud native curriculum.

## Project Overview

**Website**: https://kube-dojo.github.io/ (MkDocs Material, pinned mkdocs<2.0.0)

**Site tabs**: Home | What's New | Fundamentals | Cloud | Certifications | Platform Engineering

**Tracks**:
- **Fundamentals** — Zero to Terminal, Linux Everyday Use, Philosophy, Cloud Native 101, K8s Basics, Modern DevOps, Linux Deep Dive
- **Cloud** — Rosetta Stone, AWS/GCP/Azure Essentials (12 each), Architecture Patterns, EKS/GKE/AKS Deep Dives, Advanced Ops, Managed Services, Enterprise & Hybrid
- **Certifications** — CKA, CKAD, CKS, KCNA, KCSA, Extending K8s, 10+ tool certs
- **Platform Engineering** — Foundations (7 sections), Disciplines (12 sections), Toolkits (17 categories)

**Ukrainian translation**: ~40% (Prerequisites, CKA, CKAD). `.uk.md` suffix files, `docs/uk-glossary.md`.

## Session Workflow

1. **READ `STATUS.md` FIRST** — instant context
2. Use `scripts/prompts/module-writer.md` for new modules
3. Send to Gemini for review before closing issues
4. **UPDATE `STATUS.md`** before ending session

## Build & Serve

```bash
source .venv/bin/activate
NO_MKDOCS_2_WARNING=1 mkdocs build                    # 0 warnings expected
NO_MKDOCS_2_WARNING=1 mkdocs serve --dev-addr 127.0.0.1:8001 --no-livereload --clean
```

## Key Files

| File | Purpose |
|------|---------|
| `STATUS.md` | Current work, progress, blockers |
| `CLAUDE.md` | This file — project overview |
| `.claude/rules/` | Scoped rules (quality, translation, checklist, Gemini) |
| `.claude/settings.json` | Shared permissions (committed) |
| `.claude/settings.local.json` | Personal overrides (gitignored) |
| `scripts/prompts/module-writer.md` | Standard prompt for module creation |
| `scripts/ai_agent_bridge/` | Gemini integration |
| `docs/uk-glossary.md` | Ukrainian translation glossary |
| `requirements.txt` | Pinned deps (mkdocs<2.0.0) |

## Curriculum Structure

```
docs/
├── prerequisites/         # Fundamentals tab (33 modules)
├── linux/                 # Also Fundamentals (33 modules)
├── cloud/                 # Cloud tab (85 modules)
│   ├── hyperscaler-rosetta-stone.md
│   ├── aws-essentials/    # 12 modules
│   ├── gcp-essentials/    # 12 modules
│   ├── azure-essentials/  # 12 modules
│   ├── architecture-patterns/  # 4 modules
│   ├── eks-deep-dive/     # 5 modules
│   ├── gke-deep-dive/     # 5 modules
│   ├── aks-deep-dive/     # 4 modules
│   ├── advanced-operations/    # 10 modules
│   ├── managed-services/  # 10 modules
│   └── enterprise-hybrid/ # 10 modules
├── k8s/                   # Certifications tab (150+ modules)
│   ├── extending/         # 8 modules (controllers, operators)
│   ├── cka/ ckad/ cks/ kcna/ kcsa/
│   └── ...tool certs
└── platform/              # Platform Engineering tab (170+ modules)
    ├── foundations/        # 7 sections (32 modules)
    ├── disciplines/        # 12 sections (75 modules)
    └── toolkits/           # 17 categories (75+ modules)
```

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
- **Gemini Bridge**: `scripts/ai_agent_bridge/`
