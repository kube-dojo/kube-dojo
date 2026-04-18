#!/usr/bin/env bash
# Smoketest: scripts/ab must default CODEX_BRIDGE_MODE=workspace-write,
# and must respect user overrides.
#
# Regression guard for the session-2 2026-04-18 finding: upstream "safe"
# default silently blocks worktree + gh CLI writes. Loss of this default
# would burn another debugging session before anyone notices.
#
# Exit 0 on pass, non-zero with diagnostic on fail.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
AB="$REPO_ROOT/scripts/ab"
[ -x "$AB" ] || { echo "FAIL: $AB not executable"; exit 1; }

# Extract the env-setup preamble (everything before the final exec) so we can
# source it in isolation and inspect the resulting environment without
# actually invoking the Python bridge.
exec_line="$(grep -n '^exec ' "$AB" | head -1 | cut -d: -f1)"
[ -n "$exec_line" ] || { echo "FAIL: no 'exec' line found in $AB"; exit 1; }

preamble="$(mktemp)"
trap 'rm -f "$preamble"' EXIT
head -n "$((exec_line - 1))" "$AB" > "$preamble"

# Test 1: default is workspace-write when caller has not set the var.
actual_default="$(bash -c "unset CODEX_BRIDGE_MODE; source '$preamble'; printf '%s' \"\$CODEX_BRIDGE_MODE\"")"
if [ "$actual_default" != "workspace-write" ]; then
  echo "FAIL: default CODEX_BRIDGE_MODE is '$actual_default', expected 'workspace-write'"
  echo "HINT: upstream default is 'safe' which silently blocks writes, worktrees, and gh CLI."
  exit 1
fi

# Test 2: caller-supplied value is respected (not clobbered by the default).
actual_override="$(bash -c "export CODEX_BRIDGE_MODE=danger; source '$preamble'; printf '%s' \"\$CODEX_BRIDGE_MODE\"")"
if [ "$actual_override" != "danger" ]; then
  echo "FAIL: override CODEX_BRIDGE_MODE=danger clobbered to '$actual_override'"
  echo "HINT: use ':= default' syntax, not '= default', so callers can override."
  exit 1
fi

echo "PASS: scripts/ab defaults CODEX_BRIDGE_MODE=workspace-write and respects overrides"
