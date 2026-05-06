#!/bin/bash
# Hook: SessionStart — validates environment and reports project state.
# Skips in headless/pipeline mode.

# Skip in non-interactive mode
if [ -n "$CLAUDE_NON_INTERACTIVE" ] || [ -n "$KUBEDOJO_PIPELINE" ] || [ -n "$GEMINI_SESSION" ]; then
  exit 0
fi

REPO_HINT="${CLAUDE_PROJECT_DIR:-$(cd "$(dirname "$0")/../.." && pwd)}"
REPO_ROOT=$(git -C "$REPO_HINT" rev-parse --show-toplevel)
PRIMARY_WORKTREE=$(git -C "$REPO_ROOT" worktree list --porcelain | awk '/^worktree / {print $2; exit}')
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

# 2. Check MCP RAG server (for Ukrainian translations)
RAG_STATUS=$(curl -s -o /dev/null -w '%{http_code}' --max-time 2 "http://127.0.0.1:8766/sse" 2>/dev/null)
if [ "$RAG_STATUS" = "000" ]; then
  INFO+=("MCP RAG server not running (127.0.0.1:8766) — Ukrainian translation tools unavailable")
fi

# 3. Check gemini-cli
if ! command -v gemini >/dev/null 2>&1; then
  INFO+=("gemini-cli not found — pipeline WRITE step unavailable")
fi

# 4. Pipeline status
if [ -f "$PROJECT_DIR/.pipeline/state.yaml" ]; then
  DONE=$(.venv/bin/python -c "
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

# 5. Open GH issues (top 5)
if command -v gh >/dev/null 2>&1; then
  ISSUES_LIST=$(gh issue list --state open --limit 5 --json number,title 2>/dev/null | jq -r '.[] | "  #\(.number): \(.title)"' 2>/dev/null)
  if [ -n "$ISSUES_LIST" ]; then
    ISSUE_COUNT=$(gh issue list --state open --json number 2>/dev/null | jq 'length' 2>/dev/null)
    INFO+=("$ISSUE_COUNT open issue(s):
$ISSUES_LIST")
  fi
fi

# 6. Check MEMORY.md size
MEMORY_FILE="$HOME/.claude/projects/-Users-krisztiankoos-projects-kubedojo/memory/MEMORY.md"
if [ -f "$MEMORY_FILE" ]; then
  MEMORY_LINES=$(wc -l < "$MEMORY_FILE" | tr -d ' ')
  if [ "$MEMORY_LINES" -gt 150 ]; then
    ISSUES+=("MEMORY.md is $MEMORY_LINES lines (limit: 200). Trim before it gets truncated.")
  fi
fi

# Build output
if [ ${#ISSUES[@]} -eq 0 ] && [ ${#INFO[@]} -eq 0 ]; then
  exit 0
fi

CONTEXT="SESSION SETUP CHECK:"

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

printf '{"additionalContext": %s}' "$(printf '%s' "$CONTEXT" | jq -Rs '.')"
exit 0
