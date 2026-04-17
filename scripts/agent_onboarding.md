# Agent Onboarding — Local API Recipes

Single source of concrete `curl` recipes for any agent (Claude, Codex, Gemini) spinning up against this repo. The local API runs on `http://127.0.0.1:8768` and is read-only — there is no POST surface.

## 1. Cold-start orientation

```bash
# One call replaces "cat CLAUDE.md + STATUS.md + git log -20 + git status + ls".
# Compact form is the agent path — ~0.7K tokens, 76% reduction vs. the crawl.
curl -s http://127.0.0.1:8768/api/briefing/session?compact=1

# Full briefing (~1.5K) when you also want next_reads + the worktree list.
curl -s http://127.0.0.1:8768/api/briefing/session

# Machine-readable endpoint index — use this instead of reading local_api.py.
curl -s http://127.0.0.1:8768/api/schema
```

The briefing body carries these agent-critical fields:

| field | what it answers |
|-------|-----------------|
| `actions.active` | what's in flight right now (read-only from a deciding agent's view) |
| `actions.blocked` | what the pipeline can't make progress on without human input |
| `actions.next` | what's ready to pick up |
| `top_modules[]` | every row above that names a module, with a drill-down `endpoint` |
| `alerts[]` | one-line warnings (stale pids, critical rubric, zombie workers) |
| `blockers[]` / `focus[]` | pulled from `STATUS.md` |
| `freshness.stale_seconds` | 0 when background-refreshed; if >75 s the data is growing stale |

Every briefing response carries a weak ETag. Send `If-None-Match` with the previous ETag on repeat polls to get a cheap `304 Not Modified`.

## 2. Before claiming work

Avoid cross-agent collisions — check leases before picking a module:

```bash
# All active leases, ordered by expiry.
curl -s http://127.0.0.1:8768/api/pipeline/leases

# Just one module.
curl -s http://127.0.0.1:8768/api/module/k8s/cka/module-2.8-scheduler/lease
```

## 3. Before fixing a module

`diagnostics[]` carries the stable `code` + human `summary` + optional drill-down `next_action`. Switch on `code`, not `summary`.

```bash
curl -s http://127.0.0.1:8768/api/module/k8s/cka/module-2.8-scheduler/state
```

Known diagnostic codes:

- `english_missing`, `frontmatter_missing`, `frontmatter_no_title`
- `no_lab`, `no_fact_ledger`
- `uk_translation_missing`, `uk_state_<status>`
- `rubric_critical`, `rubric_poor`
- `pipeline_rejected`, `pipeline_dead_letter`
- `lease_held`

## 4. Before re-reviewing

```bash
# Index of all review artifacts.
curl -s http://127.0.0.1:8768/api/reviews

# Existing audit log for one module (capped at 200 KB, flags `truncated`).
curl -s "http://127.0.0.1:8768/api/reviews?module=k8s/cka/module-2.8-scheduler"
```

## 5. Situational awareness

```bash
# Per-track, per-section production-readiness grid.
curl -s http://127.0.0.1:8768/api/tracks/readiness

# Merged 24-h feed: commits + pipeline v2 events + bridge messages.
curl -s "http://127.0.0.1:8768/api/activity?limit=30"

# Zombie workers + stuck jobs + unresolved dead-letters in one call.
curl -s http://127.0.0.1:8768/api/pipeline/v2/stuck

# Per-module event timeline (timestamps are Unix-epoch SECONDS, not ms).
curl -s "http://127.0.0.1:8768/api/pipeline/v2/events?module=k8s/cka/module-2.8-scheduler&limit=50"
```

## 6. Human dashboard

The same endpoints feed an HTML dashboard at `http://127.0.0.1:8768/`. The Operator panel at the top renders `actions.*` as Now / Blocked / Next columns, the readiness grid, and the activity feed. Agents don't need it; operators often do.

## 7. Fallback

If the API is down, agents should:

1. `cat STATUS.md` for focus + blockers.
2. `cat CLAUDE.md` for project overview.
3. `git log -20 --oneline` for recent commits.
4. `git status` for worktree state.

The briefing endpoint exists so none of the above is normally necessary.

## 8. Conventions

- **All endpoints are `GET`.** There is no write surface by design.
- **Timestamps are Unix-epoch seconds** for anything sourced from `.pipeline/v2.db` and for the merged activity feed's `items[].at` (bridge-sourced rows are normalized from ISO to epoch inside `/api/activity`). Only the dedicated `/api/bridge/messages` endpoint preserves the bridge's original ISO-8601 strings in its `timestamp` field.
- **Errors are JSON envelopes**: `{"error": "<code>", ...optional context}` with an HTTP status that matches the code.
- **Cache**: cacheable endpoints return a weak ETag; `If-None-Match` yields `304`.
- **Compact**: `/api/briefing/session?compact=1` drops navigation aids (`next_reads`, `links`, worktree list) while keeping the actionable surface.
