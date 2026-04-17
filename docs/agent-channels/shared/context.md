# KubeDojo — Shared Agent Context

## First call on a cold start
Hit the local API before reading STATUS.md or grepping:
```
curl -s http://127.0.0.1:8768/api/briefing/session?compact=1  # ~0.7K tokens
curl -s http://127.0.0.1:8768/api/schema                      # endpoint index
```
`/api/briefing/session` returns `actions.now | blocked | next` + `top_modules`
so you know what to touch. `/api/module/{key}/state` is a one-call drill-down
(includes orchestration + lease + structured diagnostics). Fall back to
STATUS.md only when the API is down.

## Project
Free, open-source cloud native curriculum. 670 modules across 7 tracks.
Site: https://kube-dojo.github.io/ (Starlight/Astro)

## Agent Roles
- **Claude (Opus)**: main session, planning, synthesis, merge gates
- **Gemini Pro**: module writing, structural review (7 binary checks), Ukrainian translation
- **gpt-5.3-codex-spark**: fact-grounding (calibration winner 25/25)
- **gpt-5.3-codex**: greenfield code, architecture PRs, fix passes
- **gpt-5.4**: adversarial code review (same-family independence)
- **Claude Sonnet**: targeted fixes (rare), fact-grounding fallback

## Constraints
- Claude family DISQUALIFIED for bulk work (Anthropic 20x Max nerf)
- Never parallelize Gemini calls (user runs concurrent workloads)
- Never merge without cross-family adversarial review
- K8s target version: v1.35+ for all examples

## Key Files
- `scripts/v1_pipeline.py` — module quality pipeline
- `scripts/dispatch.py` — Gemini/Claude CLI dispatch
- `.pipeline/state.yaml` — module state tracking
- `CLAUDE.md` — project instructions
