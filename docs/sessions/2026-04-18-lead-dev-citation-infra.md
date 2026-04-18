# Session Handoff — 2026-04-18 — Lead Dev / Citation-First Infra

## Role & Mandate

Claude = lead developer. Codex = senior engineer (demoted — can't handle big projects; suited for execution + review + heavy-command running). Gemini = translation + adversary review.

Top-level goal: rewrite every module with citations via an automated pipeline (**Gemini 3.1 Pro writes → GPT-5.3 Codex reviews / fact-checks / applies fixes**). User orchestrates from shell to save Claude tokens.

## Decisions Locked This Session

1. **Independent-review loop**: role-swap per PR (Codex adversarially reviews Claude's fixes) OR Gemini stays as adversary on every PR. Either satisfies the "never merge without independent adversarial review" rule.
2. **Quality target**: aim **5/5**, gate at **4.5/5**. Do NOT calibrate down to "aim 4.5."
3. **Codex task size budget**: ≤400 LOC diff, ≤3 files, one coherent change. Sometimes one AC at a time. Claude splits anything bigger before delegating.
4. **V3 pipeline proposal** = GH issue **#217** ("drop audit, independent fallback, web grounding, per-track rubric"). Not yet read in detail.
5. **Citation project** = issues **#273** (design, Claude lane), **#274** (reset + re-review), **#275** (AI finish to 4/5).
6. **#273 design direction**: 3-tab module page (**Theory / Practice / Citations**) using Starlight's built-in `<Tabs syncKey>` — NOT custom routing. Four modifications from a naive split:
   - Inline active-learning prompts, Did You Know, Common Mistakes, and citation markers (`[^1]`) STAY in Theory. Practice tab = Quiz + Hands-On only.
   - Citations tab holds full bibliography; inline markers jump to it.
   - Deep-link via `?tab=citations`.
   - Evaluated and rejected the single-page sticky-TOC alternative (fails the "citations are first-class" goal).
7. **Codex as heavy-command executor** — when user is away. Scope: `npm run build` (56s), pipeline runs, audits, anything >100 lines of output. Claude runs `pytest`, `ruff`, `curl`, `git log` inline (cheaper). Command format: `exec: <cmd> / report: pass|fail + last 30 lines + new warnings`.
8. **Long-term**: extend local API with `/api/build/run` + `/api/build/status` (Codex implements) — removes the Codex hop for build reports. Bundle into the GH-reporting API issue.
9. **Gap analysis timing**: AFTER pipeline wiring (task #5 blocked by #3). Reason: gap output is a to-write list; pipeline is the thing that writes.
10. **Session etiquette**: no auto-compact. Claude alerts + hands off before context dies.

## Work Completed

### 4 Commits to `main` (local — NOT pushed yet)

```
5cfa70b0 Seed citations for AI foundations rebuild
9cc52d9d Add /api/citations/status endpoint
49161266 Add deterministic citation checker
b249f710 Add citation-first quality gate policy
```

Touches:
- `docs/citation-upgrade-plan.md` (new) — governing policy doc
- `docs/quality-rubric.md`, `docs/pipeline.md` — citation gate added
- `scripts/check_citations.py` + `tests/test_check_citations.py` — deterministic checker (4 tests passing, lint clean)
- `scripts/local_api.py` + `tests/test_local_api_citations.py` — `/api/citations/status` endpoint
- `docs/citation-seeds-ai-foundations.md` — 13 pre-vetted citations for AI modules 1.1/1.2/1.3

### Rollback

Codex had manually rewritten AI modules 1.1/1.2/1.3 offline. Claude reviewed the diffs and found **structural regression** (stripped Did You Know, quiz reduced below 6–8 floor, worked examples removed, inline active-learning prompts removed). Modules were `git restore`d. The 13 valid citations Codex found were preserved in `docs/citation-seeds-ai-foundations.md` as seed data for the automated pipeline rebuild.

## Open Decisions (Waiting On User)

1. **Push the 4 commits?** User wants to run `npm run build` himself before push. Waiting on green light.
2. **Role-swap vs Gemini adversary** — pick one (both work). Decision needed before drafting pipeline issue.

## Unblocked Tasks (Next Session Picks These Up First)

- **#2** — Read V3 proposal #217 in full. Draft a quick risk note.
- **#3** — Draft GH issues for infra work with ACs as quality gates. Includes:
  - Extend local API with GH reporting (`/api/gh/issues`, `/api/gh/prs`) — Codex task
  - Extend local API with `/api/build/run` + `/api/build/status` — Codex task
  - Pipeline v3 breakdown (from #217) — split into ≤400-LOC pieces
  - Automated citation pipeline wiring (Gemini 3.1 Pro → Codex)
- **#8** — Write #273 design proposal (3-tab module page) as PR. Starlight `<Tabs syncKey>`, migration script outline for ~600 modules.

## Blocked Tasks

- **#5** gap analysis — blocked on #3 (need pipeline before gap output is actionable)
- **#6** automated pipeline — blocked on #3 (wiring needs issue breakdown)
- **#7** write-missing-then-upgrade — blocked on #5 + #6

## Pointers

- **Memory index**: `/Users/krisztiankoos/.claude/projects/-Users-krisztiankoos-projects-kubedojo/memory/MEMORY.md`
- **Policy doc**: `docs/citation-upgrade-plan.md`
- **Checker**: `scripts/check_citations.py`
- **API endpoint added**: `/api/citations/status` (cached 30s by docs mtime)
- **Seeds**: `docs/citation-seeds-ai-foundations.md`
- **Agent bridge**: `scripts/ab` (per memory `reference_agent_bridge.md`)
- **Dispatch**: `scripts/dispatch.py` (per memory `reference_gemini_model.md`)

## Notes for Resuming

- Use `/continue` to resume this conversation with full memory. Do NOT start cold.
- First call on resume: `curl -s http://127.0.0.1:8768/api/briefing/session?compact=1` (standard orientation).
- If user says "go," start with reading #217 in full (task #2) before drafting issues.
- User may push commits 1–4 himself while away; check `git log origin/main..main` on resume.
