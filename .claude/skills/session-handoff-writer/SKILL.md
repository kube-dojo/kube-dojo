---
name: session-handoff-writer
description: End-of-session handoff convention for KubeDojo. HTML-first, served via local API. Live-index (.agent/STATUS.md) update protocol — handoffs are LOCAL agent state, never committed. Triggers on "session handoff", "end of session", "wrap up session", "write handoff".
last_calibrated: 2026-05-24
---

# Session Handoff Writer Skill

End-of-session ritual for KubeDojo. The handoff is a durable narrative that lets the next agent pick up cold without paging the previous session's context. The LIVE index `.agent/STATUS.md` (machine-local, gitignored) points to it; the tracked `STATUS.md` is the seed/fallback and changes via PR only.

## The two-file pattern

```
docs/session-state/2026-05-24-session-52-<slug>.html   ← full handoff (this skill writes it; gitignored)
.agent/STATUS.md                                         ← LIVE index that points at it (this skill updates it; gitignored)
```

**Do NOT inline the full handoff into the index.** `.agent/STATUS.md` is an INDEX. The briefing API parses `## TODO` (unchecked `- [ ]`) and `## Blockers` (`- `) from it (`_live_status_path` prefers the live copy), so those headings stay populated — but the narrative belongs in the dated file.

## When to write a handoff

- End of a working session (you're about to disconnect or hand off).
- After landing 3+ PRs.
- After a meaningful policy/routing change (Decision Card move, agent retirement, threshold freeze).
- Before a long break where session context would otherwise be lost to compaction.

## Format choice — HTML default (HTML-first artifact policy)

Per [[feedback_html_over_markdown_for_artifacts]]:
- **AI → Human consumption** (handoffs, audits, batch reports, PR explainers, autopsies) → **HTML**.
- **Human → AI or AI → AI** (dispatch briefs, agent prompts) → **MD**.

Handoffs are AI → Human (you, the orchestrator, telling the user + next orchestrator what happened) → **HTML**.

Brief / dense handoffs may stay `.md` if the narrative is short and a sidecar (`.notes.md`) is not warranted. Default: `.html`.

## Naming

```
docs/session-state/YYYY-MM-DD-session-NN-<topic-slug>.html
```

Examples:
- `2026-05-24-session-52-cursor-as-author-pr-pipeline-6-merged.html`
- `2026-05-23-session-48-parallel-rewrite-cap-three.html`

## HTML template

Use this skeleton (matches sessions 50-52 conventions):

```html
<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Session NN — <one-line topic></title>
<style>
body { font: 14px/1.55 -apple-system, sans-serif; max-width: 1000px; margin: 2rem auto; padding: 0 1rem; }
h1 { margin-bottom: 0.2rem }
.meta { color: #555; margin-bottom: 1.5rem }
h2 { border-bottom: 1px solid #ddd; padding-bottom: 4px; margin-top: 2rem }
h3 { margin-top: 1.4rem }
code { background: #f4f4f4; padding: 1px 5px; border-radius: 3px; font-size: 90% }
table { border-collapse: collapse; margin: 0.5rem 0; width: 100% }
td, th { padding: 4px 10px; border-bottom: 1px solid #eee; vertical-align: top; text-align: left }
th { background: #f8f8f8 }
.pill { display: inline-block; padding: 1px 8px; border-radius: 10px; font-size: 80%; font-weight: bold; }
.merged { background: #d4edda; color: #155724 }
.inflight { background: #cce5ff; color: #004085 }
blockquote { border-left: 3px solid #ccc; padding-left: 1rem; color: #555 }
</style></head><body>

<h1>Session NN — <one-line topic></h1>
<p class="meta"><date + 2-3 sentence TLDR. Who was active, what shifted, what landed.></p>

<h2>Headline</h2>
<table>
<tr><th>PR</th><th>State</th><th>Title</th><th>Cycle</th></tr>
<tr><td>#NNNN</td><td><span class="pill merged">MERGED</span></td><td>...</td><td>R1 ... → R2 ... → merged</td></tr>
<tr><td>#NNNN</td><td><span class="pill inflight">IN-FLIGHT</span></td><td>...</td><td>...</td></tr>
</table>

<h2>Policy moves locked this session</h2>
<h3>1. <name></h3>
<p>What changed, why, who triggered it. Quote the user verbatim where load-bearing.</p>

<h2>Headline data</h2>
<p>Numbers from the briefing API at session end. Quality boards, readiness, in-flight PRs.</p>

<h2>Dispatch ledger</h2>
<table>
<tr><th>Dispatch</th><th>Agent</th><th>Class</th><th>Outcome</th></tr>
<tr><td>PR #NNNN R1</td><td>codex gpt-5.5</td><td>review</td><td>...</td></tr>
</table>

<h2>What's next</h2>
<ul>
<li>Top priority for next session: ...</li>
<li>Date-bound: ...</li>
<li>Long-running epics: ...</li>
</ul>

<h2>Files touched</h2>
<ul>
<li><code>path/to/file.py</code> — what changed</li>
</ul>

</body></html>
```

## Required sections

1. **Headline / TLDR** — 2-3 sentences. The next agent should be able to read just this and know what happened.
2. **PRs** — table of PRs (merged + in-flight) with cycle annotations.
3. **Policy moves** — what conventions changed. Quote the user where load-bearing.
4. **Headline data** — numbers from `/api/briefing/session`, `/api/quality/scores`, etc.
5. **Dispatch ledger** — every dispatch fired, agent, outcome. This is the audit trail.
6. **What's next** — top priorities for the next session.

Optional but recommended:
- **Files touched** — list with one-line "what changed" each.
- **Decisions made / Decision Cards moved** — link to `docs/decisions/`.
- **Memory entries added/updated** — list with one-line "why".

## STATUS.md update protocol

After writing the handoff HTML, update the **LIVE index: `.agent/STATUS.md`**
(machine-local, gitignored — the briefing API + `cold-start.sh` prefer it when
present; seed it from the tracked `STATUS.md` if missing). Do NOT edit the
tracked `STATUS.md` at session end — it holds the durable sections and changes
via PR only:

1. **Promote previous "Latest handoff" row to "Predecessor chain"** (move the row down a section).
2. **Insert new row** at the top of "## Latest handoff":
   ```
   | YYYY-MM-DD | **NN** | <one-line summary> | [session-NN](./docs/session-state/<file>.html) |
   ```
3. **Refresh "## Current state"** — module counts, readiness, in-flight PRs.
4. **Refresh "## TODO"** — unchecked `- [ ]` items the next session should pick up. The briefing API parses these.
5. **Refresh "## Blockers"** — `- ` prefix items. Briefing API parses these too. Leave empty if none.
6. **Refresh "## Active policies"** — add new Decision Cards / policy locks.
7. **Date-bound items** — add expiry-bound TODOs (claude-throttle window, agentic-pool flip, agent retirements).

Cap `.agent/STATUS.md` at ~100 lines (the compression target — commit `dcd86360`). Anything narrative-y belongs in the handoff HTML, not here.

## Serving the handoff

Per [[feedback_html_artifacts_via_local_api]]: HTML artifacts MUST be served via the local API, never `open <file>` or `file://`. **Port map** — `8768` = local API (briefing, pipeline state, JSON endpoints); `8910` = session-state HTML renderer (`render_url` for dated handoffs).

The render URL pattern is `http://127.0.0.1:8910/docs/session-state/<file>.html`. Briefing API (`8768`) surfaces it as `kubedojo:session` → `render_url`.

## Do NOT commit the handoff (user directive s190b)

Handoffs + the live STATUS index are **LOCAL agent state** — the briefing API and
cold-start read them **from disk**, not from git. New files in `docs/session-state/`
are gitignored; `.agent/STATUS.md` is gitignored. Ending a session = a couple of
file Writes. **No `git add`, no commit, no PR, no CI wait** — see
[[feedback_handoff_commit_direct_no_worktree]]. (Durable shared records — decision
docs, curriculum, code — still go through git + PR as normal.)

<!-- Historical (pre-s190b) commit ritual removed. Old form for reference:
git add docs/session-state/<file>.html STATUS.md
git commit -m "$(cat <<'EOF'
docs: session NN handoff — <topic>

- <key thing 1>
- <key thing 2>
- <key thing 3>

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
-->

## What NOT to put in a handoff

- Curriculum content (modules live in `src/content/docs/`).
- Pipeline code (lives in `scripts/`).
- Decision Card pending content (lives in `docs/decisions/pending/`).
- Memory updates (live in `~/.claude/projects/...kubedojo/memory/`).

The handoff cites/links to these; it does not duplicate them.

## Anti-patterns

- Inlining the full handoff into the index — `.agent/STATUS.md` is the index, dated handoff HTML is the log (see commit `dcd86360` compression).
- Skipping the dispatch ledger — that's the audit trail, not optional.
- Writing the handoff in Markdown when the HTML rendering matters (tables, pill labels) — use HTML.
- Forgetting to refresh `## TODO` / `## Blockers` — the briefing API will surface stale data.
- Writing a handoff before merging the in-flight PRs — better: write the handoff WITH `IN-FLIGHT` pills, then let the next session merge.

## References

- [[curriculum-orchestrator]] — the parent role that calls this skill.
- [[feedback_html_over_markdown_for_artifacts]] — format-choice rule.
- [[feedback_html_artifacts_via_local_api]] — serving rule.
- [`STATUS.md`](../../../STATUS.md) — the tracked seed/fallback (durable sections; PR-only). The LIVE index this skill updates is `.agent/STATUS.md`.
- [`docs/session-state/`](../../../docs/session-state/) — all prior handoffs (49+ files).
- [`docs/migrations/html-first/plan.html`](../../../docs/migrations/html-first/plan.html) — HTML-first artifact policy spec.
- [`scripts/local_api.py`](../../../scripts/local_api.py) `_parse_status_md` — the briefing parser.
