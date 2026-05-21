# 2026-05-21 — Quality Hooks: Conservative Scope for Auto-Format and Log-Filter

**Status**: ACCEPTED
**Decided by**: Claude (sonnet-4-6), worktree infra-1380
**Scope**: `.claude/hooks/` quality hooks for issue #1380

## Context

Issue #1380 asked for two quality hooks inspired by the zodchii post:

1. **Post-write auto-format** — automatically run `ruff format` after Python file edits so Claude never leaves formatting debt in scripts.
2. **Pre-read log-filter** — warn Claude before it reads a large dispatch log file cold, to avoid context bloat.

Both hooks interact with an active dispatch pipeline where agents write files, read logs, and run automated batches. Any over-broad scope risks: (a) mangling content modules that contain frontmatter and code blocks, (b) corrupting JSONL log entries that pipeline readers rely on, or (c) causing noisy reruns in dispatch chains.

## Decision

### Hook 1 — Post-write auto-format

**Scope: `.py` files only, in the primary tree, outside excluded directories.**

**Why `.py` only:**
- Python files have no frontmatter, no fenced-code-block nesting, and ruff has no destructive edge cases on valid Python.
- Markdown auto-format is excluded: markdownlint and prettier both modify frontmatter patterns that Astro/Starlight parses for sidebar config. One bad reformat can break 1,999 pages.
- YAML auto-format is excluded: Astro frontmatter is embedded YAML. yamlfix and prettier both strip or reorder keys in ways that break `title:`, `sidebar.order:`, and `slug:` fields.
- TypeScript auto-format is excluded: it requires a separate node toolchain; `npx prettier` has different installation guarantees than `.venv/bin/ruff`.

**Why excluded directories:**
- `logs/`, `dist/`, `node_modules/`, `.venv/` — not human-authored Python; formatting changes corrupt binary data or pollute venv contents.
- `.worktrees/` — dispatch agents write into worktrees; formatting their in-progress files adds unrequested diff noise to PRs.
- `src/content/docs/` — content modules are Markdown, not Python; this guard is belt-and-suspenders.

**Skip conditions:**
- `KUBEDOJO_DISPATCHED=1` — dispatch pipelines set this env var; the hook skips to avoid double-formatting and noisy pipeline logs.
- Ruff not installed at `.venv/bin/ruff` — fail-open; never error in a missing-venv environment.

### Hook 2 — Pre-read log-filter

**Scope: `logs/smart_dispatch.jsonl` and `logs/dispatch_responses/*.txt` only, when file > 100 KB.**

**Why log-warn-only (never block):**
- Blocking a Read on a log file could prevent Claude from debugging a stuck pipeline.
- The value is in flagging the pattern (read whole log = context flood) and offering targeted `jq` alternatives, not in enforcement.
- Exit code is always 0; `hookSpecificOutput.additionalContext` injects the advisory into Claude's next turn.

**Why 100 KB threshold:**
- Smart dispatch JSONL files grow at ~2 KB/entry. 100 KB ≈ 50 entries — large enough to be a real log, small enough that a cold-read is still reasonable.
- Response text files in `dispatch_responses/` are typically 5-50 KB; only multi-agent batches exceed 100 KB.

## Deferred (follow-up issue)

The following were explicitly deferred to avoid blast radius:
- **Markdown auto-format** — requires a frontmatter-aware formatter and isolated testing against Astro builds.
- **YAML auto-format** — needs agreement on which YAML files are safe (pure config vs embedded frontmatter).
- **TypeScript auto-format** — requires node toolchain coordination and ESLint/Prettier version pinning.

## References

- Issue: #1380
- Hook files: `.claude/hooks/post-write-py-autoformat.sh`, `.claude/hooks/pre-read-warn-large-log.sh`
- Tests: `tests/test_quality_hooks.py`
- Similar pattern: `.claude/hooks/block-orchestrator-content-edits.sh` (KUBEDOJO_DISPATCHED guard)
