# Session Handoff — 2026-03-25

## What Was Done This Session

### Fixes (3 modules)
- CKS 0.2: audit volume config fix
- CKS 0.3: Falco persistence fix (exec → Helm/ConfigMap)
- KCSA 4.5: full rewrite from 49-line outline to 500+ line module

### Ukrainian Translations (91 modules)
- Prerequisites: K8s Basics (8) + Modern DevOps (6) — all prerequisites 100% translated
- CKA: All 47 modules translated (Parts 0-5)
- CKAD: All 30 modules translated (Parts 0-5)
- Still untranslated: CKS, KCNA, KCSA, Platform, Linux, Cloud

### Site Restructure
- Merged Prerequisites + Linux tabs → **Fundamentals** tab
- Added **Cloud** tab
- Moved Linux Everyday Use after Zero to Terminal (before Philosophy & Design)
- Enabled `navigation.prune` for sidebar performance
- Added Learning Paths to homepage
- Fixed 450+ broken links across 171 files
- Created 18 missing README index files
- Pinned mkdocs<2.0.0 (MkDocs 2.0 breaks everything — watch Zensical)
- Removed deprecated i18n `default_language` config
- Build is now **0 warnings**

### New Content Written (159 modules, ~133,000 lines)

| Track | Modules | Lines | Issue |
|-------|---------|-------|-------|
| Linux Everyday Use | 5 | 3,841 | #128 closed |
| Engineering Leadership | 6 | 5,773 | #116 closed |
| Release Engineering | 5 | 5,482 | #113 closed |
| Chaos Engineering | 5 | 4,600 | #114 closed |
| FinOps | 6 | 5,625 | #115 closed |
| Data Engineering | 6 | 6,131 | #118 closed |
| Advanced Networking | 6 | 8,406 | #117 closed |
| AI/GPU Infrastructure | 6 | 6,678 | #120 closed |
| Extending Kubernetes | 8 | 8,841 | #119 closed |
| Rosetta Stone | 1 | 947 | #127 closed |
| AWS Essentials | 12 | 11,545 | #124 closed |
| GCP Essentials | 12 | 9,689 | #125 closed |
| Azure Essentials | 12 | 8,988 | #126 closed |
| Cloud Deep Dive Phase 1 | 18 | 16,990 | #112 closed |
| Cloud Deep Dive Phase 2 | 10 | 10,058 | #121 closed |
| Cloud Deep Dive Phase 3 | 10 | 9,432 | #122 closed |
| Cloud Deep Dive Phase 4 | 10 | 10,461 | #123 closed |

### Config Restructure
- CLAUDE.md trimmed 247→106 lines (under 200 guideline)
- Created `.claude/settings.json` (clean team permissions)
- Created `.claude/rules/` with 4 scoped rules (quality, translation, checklist, Gemini)
- Cleaned bloated `settings.local.json`
- Updated `.gitignore` to commit `.claude/` team config
- Created `scripts/prompts/module-writer.md` (reusable writer prompt)

## Open Issues
- #105 — Ukrainian translation (ongoing, ~40% done)
- #14 — Curriculum monitoring (ongoing)

## Not Yet Done
- **Gemini review** of most new expansion modules (only Engineering Leadership and Release Engineering were reviewed)
- **Ukrainian translations** for CKS (30), KCNA (21), KCSA (25) — plus all new content
- **STATUS.md** needs updating with this session's work
- **Push** — nothing has been pushed to remote yet

## Key Decisions Made
- Gemini drafts → Claude expands workflow tested and proven (Rosetta Stone: 386→947 lines)
- Gemini is good at: translations, reviews, planning. Not at: writing full-depth modules
- Cloud track organized by provider (not by topic) — students work in provider silos
- Linux Everyday Use placed after Zero to Terminal, before Philosophy & Design
- MkDocs 2.0 blocked — pinned to <2.0.0, future migration to Zensical

## TODO Next Session
- **#130 Migrate to Starlight (Astro)** — MkDocs is dead, migration planned. Write conversion script, scaffold Starlight, run migration.
- **#131 Give Gemini proper tools** — replace blind bridge with MCP/function-calling so Gemini can read files, search web, check glossary, run linters
- **#129 Review .claude/skills/** — 12 skills unused, need enrichment or consolidation
- Run Gemini adversary review on 100+ new modules that skipped review
- Update STATUS.md with this session's massive output
- Continue Ukrainian translations (CKS, KCNA, KCSA)
- Push all commits to remote

## Unpushed Commits
All work is committed locally but NOT pushed. Run `git push` when ready.
