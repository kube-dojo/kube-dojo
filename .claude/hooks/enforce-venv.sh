#!/bin/bash
# Hook: PreToolUse (Bash) — Enforce .venv/bin/python usage
# Rewrites bare `python3` or `python` commands to `.venv/bin/python`
# Prevents accidentally using system Python instead of project venv.

# Read tool input from stdin
INPUT=$(cat)

# Extract the command from JSON
COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // empty')

if [ -z "$COMMAND" ]; then
  exit 0
fi

# Check if command starts with bare python3 or python (not already using .venv)
if echo "$COMMAND" | grep -qE '^python3?\s'; then
  # Already using venv? Skip.
  if echo "$COMMAND" | grep -qE '^\./\.venv/|^\.venv/|^/.*\.venv/'; then
    exit 0
  fi

  # Rewrite python3/python to .venv/bin/python
  FIXED=$(printf '%s' "$COMMAND" | sed -E 's/^python3?\s/.venv\/bin\/python /')

  # Return modified input
  printf '{"modifiedInput": {"command": %s}}' "$(printf '%s' "$FIXED" | jq -Rs '.')"
  exit 0
fi

# No modification needed
exit 0
