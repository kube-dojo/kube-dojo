#!/bin/bash
# Hook: SessionStart — validates environment and reports project state.
# Skips in headless/pipeline mode.

# Skip in non-interactive mode
if [ -n "$CLAUDE_NON_INTERACTIVE" ] || [ -n "$KUBEDOJO_PIPELINE" ] || [ -n "$GEMINI_SESSION" ]; then
  exit 0
fi

REPO_HINT="${CLAUDE_PROJECT_DIR:-$(cd "$(dirname "$0")/../.." && pwd)}"
if ! REPO_ROOT=$(git -C "$REPO_HINT" rev-parse --show-toplevel 2>/dev/null); then
  exit 0
fi
PRIMARY_WORKTREE=$(git -C "$REPO_ROOT" worktree list --porcelain | awk '/^worktree / {sub(/^worktree /, ""); print; exit}')
PRIMARY_BRANCH=$(git -C "$PRIMARY_WORKTREE" rev-parse --abbrev-ref HEAD)
if [ "$PRIMARY_BRANCH" != "main" ]; then
  printf '%b\n' "\033[31m[session-setup] PRIMARY TREE NOT ON main (currently '${PRIMARY_BRANCH}') — fix with: git -C ${PRIMARY_WORKTREE} checkout main\033[0m" >&2
  exit 1
fi

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(cd "$(dirname "$0")/../.." && pwd)}"
ISSUES=()
INFO=()

# 1. Check .venv exists
if [ ! -f "$PROJECT_DIR/.venv/bin/python" ]; then
  ISSUES+=("VENV MISSING: .venv/bin/python not found. Create: python3 -m venv .venv && .venv/bin/pip install pyyaml")
fi

# 2. Check KubeDojo local API.
API_STATUS=$(curl -s -o /dev/null -w '%{http_code}' --max-time 2 "http://127.0.0.1:8768/api/runtime/services" 2>/dev/null)
if [ "$API_STATUS" != "200" ]; then
  ISSUES+=("KubeDojo local API not running (127.0.0.1:8768) — run: bash scripts/cold-start.sh")
fi

# 3. Check optional MCP RAG server (for Ukrainian translations).
RAG_STATUS=$(curl -s -o /dev/null -w '%{http_code}' --max-time 2 "http://127.0.0.1:8766/sse" 2>/dev/null)
if [ "$RAG_STATUS" = "000" ]; then
  INFO+=("MCP RAG server not running (127.0.0.1:8766) — Ukrainian translation tools unavailable")
fi

# 4. Check gemini-cli
if ! command -v gemini >/dev/null 2>&1; then
  INFO+=("gemini-cli not found — pipeline WRITE step unavailable")
fi

# 5. Pipeline status
if [ -f "$PROJECT_DIR/.pipeline/state.yaml" ]; then
  DONE=$("$PROJECT_DIR/.venv/bin/python" -c "
import yaml
state = yaml.safe_load(open('$PROJECT_DIR/.pipeline/state.yaml').read()) or {}
modules = state.get('modules', {})
done = sum(1 for m in modules.values() if m.get('phase') == 'done')
total = len(modules)
failed = sum(1 for m in modules.values() if m.get('errors'))
print(f'{done}/{total} done, {failed} with errors')
" 2>/dev/null)
  if [ -n "$DONE" ]; then
    INFO+=("Pipeline: $DONE")
  fi
fi

# 6. Open GH issues (top 5)
if command -v gh >/dev/null 2>&1; then
  ISSUES_LIST=$(gh issue list --state open --limit 5 --json number,title 2>/dev/null | jq -r '.[] | "  #\(.number): \(.title)"' 2>/dev/null)
  if [ -n "$ISSUES_LIST" ]; then
    ISSUE_COUNT=$(gh issue list --state open --json number 2>/dev/null | jq 'length' 2>/dev/null)
    INFO+=("$ISSUE_COUNT open issue(s):
$ISSUES_LIST")
  fi
fi

# 7. Check MEMORY.md size
MEMORY_FILE="$HOME/.claude/projects/-Users-krisztiankoos-projects-kubedojo/memory/MEMORY.md"
if [ -f "$MEMORY_FILE" ]; then
  MEMORY_LINES=$(wc -l < "$MEMORY_FILE" | tr -d ' ')
  if [ "$MEMORY_LINES" -gt 150 ]; then
    ISSUES+=("MEMORY.md is $MEMORY_LINES lines (limit: 200). Trim before it gets truncated.")
  fi
fi

# 8. Stale `astro dev` server check. Vite/Astro dev servers leak memory over
# long uptimes — a forgotten one reached ~5.4 GB after 2.5 days (s182). RSS
# under-reports it (mostly compressed), so flag by UPTIME: any astro dev whose
# elapsed time shows days (etime contains '-') is almost certainly stale.
# start-docs.sh now auto-stops after 12h; this catches servers started manually.
STALE_DEV=$(/bin/ps -axo pid,etime,command 2>/dev/null | grep "astro dev" | grep -v grep | awk '$2 ~ /-/ {print "      PID "$1" (up "$2")"}')
if [ -n "$STALE_DEV" ]; then
  ISSUES+=("STALE astro dev server(s) running 1+ day — Vite leaks memory over long uptimes (can reach multi-GB). Kill, then restart only if needed (\`npx astro preview\` for view-only doesn't leak):
$STALE_DEV")
fi

# Build output. The AUTO-ORIENT directive is always emitted (interactive sessions
# only — headless already exited at line 6). Belt-and-suspenders for CLAUDE.md
# "FIRST ACTION, every session — no exceptions" — the rule still drives, this
# makes a cold restart hands-off so the user does not retype the orientation
# prompt each time (parity with learn-ukrainian's SessionStart hook).
CONTEXT="AUTO-ORIENT — run this ritual BEFORE responding to the user's first message, even if that message is unrelated, trivial, or empty (do NOT skip it; this replaces the orientation prompt the user used to type by hand):
  1. Invoke the curriculum-orchestrator skill via the Skill tool (skip only if already invoked this session).
  2. Run: bash scripts/cold-start.sh — parse the kubedojo:orient / kubedojo:briefing / kubedojo:session / kubedojo:pending-decisions blocks.
  3. Continue from the latest session handoff (docs/session-state/...): state the recommended next action, then proceed with it unless the user's message redirects you.
  4. Hold git/PR discipline throughout: branch in .worktrees/ (never in the primary dir), PR + cross-family review before merge, never push direct to main.

SESSION SETUP CHECK:"

if [ ${#ISSUES[@]} -gt 0 ]; then
  CONTEXT="$CONTEXT
ISSUES:"
  for issue in "${ISSUES[@]}"; do
    CONTEXT="$CONTEXT
  - $issue"
  done
fi

if [ ${#INFO[@]} -gt 0 ]; then
  CONTEXT="$CONTEXT
INFO:"
  for info in "${INFO[@]}"; do
    CONTEXT="$CONTEXT
  - $info"
  done
fi

# Emit via the current SessionStart hook schema (hookSpecificOutput.additionalContext).
# The legacy top-level {"additionalContext": ...} form is silently ignored by newer
# Claude Code builds — which is why this reminder previously never reached the model
# and the user had to retype the orientation prompt each restart.
jq -n --arg msg "$CONTEXT" \
  '{"hookSpecificOutput":{"hookEventName":"SessionStart","additionalContext":$msg}}'
exit 0
