---
name: session-handoff-writer
description: End-of-session handoff convention for KubeDojo. MARKDOWN handoff file (AI→AI local agent state) + live-index (.agent/STATUS.md) update — never committed to git. Triggers on "session handoff", "end of session", "wrap up session", "write handoff".
last_calibrated: 2026-05-24
---

# Session Handoff Writer Skill

End-of-session ritual for KubeDojo. The handoff is a durable narrative that lets the next agent pick up cold without paging the previous session's context. The LIVE index `.agent/STATUS.md` (machine-local, gitignored) points to it; the tracked `STATUS.md` is the seed/fallback and changes via PR only.

## The two-file pattern

```
.agent/session-state/YYYY-MM-DD-session-NN-<slug>.md   ← handoff BRIEF (this skill writes it; agent dir, gitignored)
.agent/STATUS.md                                        ← LIVE index that points at it (this skill updates it; gitignored)
```

(lu parity #3768/#4704, user 2026-07-07: handoffs live in the AGENT DIR and never go
through git/PRs — session end is pure file writes, "much faster". `docs/session-state/`
= tracked pre-s196 history only.)

**Do NOT inline the full handoff into the index.** `.agent/STATUS.md` is an INDEX. The briefing API parses `## TODO` (unchecked `- [ ]`) and `## Blockers` (`- `) from it (`_live_status_path` prefers the live copy), so those headings stay populated — but the narrative belongs in the dated file.

## When to write a handoff

- End of a working session (you're about to disconnect or hand off).
- After landing 3+ PRs.
- After a meaningful policy/routing change (Decision Card move, agent retirement, threshold freeze).
- Before a long break where session context would otherwise be lost to compaction.

## Format — MARKDOWN (re-reclassified AI→AI, 2026-07-07 s196)

Per [[feedback_html_over_markdown_for_artifacts]] the format follows the READER. Since
PR #2247 handoffs are gitignored LOCAL AGENT STATE — the primary reader is the NEXT
AGENT (Read tool) + the briefing parser, not a human in a browser. So handoffs are
**Markdown**: 2–4× cheaper to generate, cheaper to Read, greppable. (User, s196: "do
whichever is more efficient". The 2026-05-09 AI→Human/HTML reclassification is
SUPERSEDED — its premise, "the file's primary reader is the user", no longer holds.)

HTML remains for genuinely human-facing artifacts (batch reports, audits, PR review
explainers, autopsies) — and only there. Do NOT write an HTML handoff unless the user
explicitly asks for a rendered report.

## Naming

```
.agent/session-state/YYYY-MM-DD-session-NN-<topic-slug>.md
```

Examples:
- `2026-07-07-session-196-infra-prompt-refresh-codexbar-openrouter-git-clean.md` (first under the MD convention)
- pre-s196 handoffs are `.html` in `docs/session-state/` (readable history; do not convert or move the tracked ones)

## Markdown template — a lean BRIEF, not a saga (~2–5KB target, lu #4704)

YAML frontmatter + bullet-dense body. Agents AND the human read THIS — the lu measurement
was that heavyweight narrative halves go unread. Cite PRs/issues/decisions instead of
retelling them; the git log and the PR bodies are the archive. Skeleton:

```markdown
---
session: NN
date: YYYY-MM-DD
lane: <curriculum | infra>
prs_merged: ["#NNNN", "#NNNN"]
issues: {filed: ["#N"], closed: ["#N"]}
next: "<the single DO-NEXT for the successor session>"
---

# Session NN — <one-line topic>

<2-3 sentence TLDR: what shifted, what landed.>

## Shipped
- #NNNN <title> — <one-line what/why; review cycle in the PR>

## Decisions / policy moves
- <what changed + who triggered it; quote the user where load-bearing>

## Dispatch ledger
- <dispatch> → <agent> → <outcome>   (one line each; the audit trail)

## What's next
- <top priority>
- <date-bound / watch items>

## Memory / files
- <memory entries added-updated; notable files — one line each>
```

## Required sections (match the lean skeleton above)

1. **YAML frontmatter** — session, date, lane, prs_merged, issues, `next` (the single DO-NEXT).
2. **TLDR** — 2-3 sentences. The next agent should be able to read just this and know what happened.
3. **Shipped** — one bullet per PR/issue (cite; the PR body carries the detail).
4. **Decisions / policy moves** — what changed; quote the user where load-bearing.
5. **Dispatch ledger** — one line per dispatch (agent → outcome). The audit trail.
6. **What's next** — top priorities + watch items.

Optional (one line each, only when non-obvious): memory entries added/updated, notable files.
No "Headline data" dumps — the briefing API serves live numbers; don't snapshot them into the brief.

## STATUS.md update protocol

After writing the handoff `.md`, update the **LIVE index: `.agent/STATUS.md`**
(machine-local, gitignored — the briefing API + `cold-start.sh` prefer it when
present; seed it from the tracked `STATUS.md` if missing). Do NOT edit the
tracked `STATUS.md` at session end — it holds the durable sections and changes
via PR only:

1. **Promote previous "Latest handoff" row to "Predecessor chain"** (move the row down a section).
2. **Insert new row** at the top of "## Latest handoff":
   ```
   | YYYY-MM-DD | **NN** | <one-line summary> | [session-NN](./.agent/session-state/<file>.md) |
   ```
3. **Refresh "## Current state"** — module counts, readiness, in-flight PRs.
4. **Refresh "## TODO"** — unchecked `- [ ]` items the next session should pick up. The briefing API parses these.
5. **Refresh "## Blockers"** — `- ` prefix items. Briefing API parses these too. Leave empty if none.
6. **Refresh "## Active policies"** — add new Decision Cards / policy locks.
7. **Date-bound items** — add expiry-bound TODOs (claude-throttle window, agentic-pool flip, agent retirements).

Cap `.agent/STATUS.md` at ~100 lines (the compression target — commit `dcd86360`). Anything narrative-y belongs in the handoff file, not here.

## Serving the handoff

Markdown handoffs are consumed via the `Read` tool (next agent) and the briefing API's
handoff pointer — no render step needed. If a human wants to view one, serve it via the
local API artifacts route (`http://127.0.0.1:8768/artifacts/.agent/session-state/<file>.md`)
— never `open <file>` / `file://` ([[feedback_html_artifacts_via_local_api]]). Pre-s196
`.html` handoffs render via `8910` (`http://127.0.0.1:8910/docs/session-state/<file>.html`).

## Do NOT commit the handoff (user directive s190b)

Handoffs + the live STATUS index are **LOCAL agent state** — the briefing API and
cold-start read them **from disk**, not from git. Handoffs live in the gitignored
`.agent/session-state/`; `.agent/STATUS.md` is gitignored; `docs/session-state/` new
files are gitignored too (defense in depth). Ending a session = a couple of
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

- Inlining the full handoff into the index — `.agent/STATUS.md` is the index, the dated handoff file is the log (see commit `dcd86360` compression).
- Skipping the dispatch ledger — that's the audit trail, not optional.
- Writing an HTML handoff — handoffs are Markdown since s196 (AI→AI local agent state); HTML is for human-facing reports only.
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
