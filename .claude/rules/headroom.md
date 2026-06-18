# Headroom — Shared Compression + Memory Layer

Convention for using Headroom, the shared compression and memory layer for local
agents. Ported from learn-ukrainian (#3534, 2026-06-18) — KubeDojo imports rather
than reinvents. Tracking issue: #2024.

## Runtime

- Proxy health: `http://127.0.0.1:8787/health` · Stats: `http://127.0.0.1:8787/stats`
- MCP server name: `headroom` (stdio via `headroom mcp serve`); tools: `headroom_compress`, `headroom_retrieve`, `headroom_stats`.
- Start: `headroom install start --profile default`.
- `start-claude.sh` already loads the routing env and ensures the proxy (the "headroom routing guard" block). The session **and every `dispatch_smart` agent** route through `127.0.0.1:8787` (≈22% token savings observed, s164).

## Usage rule — compress big context

If content is roughly over **200 lines or 20 KB**, call `headroom_compress` FIRST,
reason over the returned **hash + a one-line summary**, and `headroom_retrieve`
only the exact detail you need. This is the single biggest context-saver on a long
orchestration session — **default to it instead of letting big outputs truncate.**
Targets:

- `npm run build` output (pipe to file anyway per [[feedback_never_read_build_logs]], then compress if you must reason over it)
- codex / cursor / deepseek review verdicts and dispatch responses
- search / grep result bundles, validation output, large diffs

Do **not** treat Headroom memory as factual authority for curriculum content —
retrieve the original or inspect the repo/source when exact claims matter (same as
the anti-fabrication conventions). Never run `headroom learn --apply` unless the
user explicitly asks — it can rewrite `CLAUDE.md` / `AGENTS.md` / `GEMINI.md`.

## Handoffs — git stays SSOT for now

KubeDojo session handoffs (`docs/session-state/YYYY-MM-DD-<topic>.html`, indexed in
`STATUS.md`, parsed by the briefing API at cold-start) **remain the durable
cross-session source of truth.** The proxy's memory store is local-only with no MCP
write tool yet (`native_tool`/`bridge` off) — it auto-injects context but cannot
carry the handoff across sessions. So keep git as the backstop and push bulky
evidence behind Headroom hashes rather than pasting it. **Migrate the handoff body
to Headroom (and cut git to a thin pointer) only once the durable memory-write tool
lands** — tracked in #2024. Do not drop the git handoff before the cold-start
read-path is proven across sessions, or every future cold-start goes blind.

## Git-tracked source of truth

- `.mcp.json` — the repo-level `headroom` stdio entry (portable; don't rely on user-level `~/.claude.json`).
- `.claude/rules/headroom.md` — this rule.
- the `## Headroom` section in `agents_extensions/claude/skills/curriculum-orchestrator/SKILL.md` (deployed to `.claude/skills/` via `agents_extensions/deploy.sh`).
- `start-claude.sh` headroom routing guard.

Machine-local runtime dirs (`.claude/` runtime state, `.codex/`, `.gemini/`) are not the source of truth.
