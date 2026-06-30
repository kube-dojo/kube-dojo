#!/usr/bin/env bash
# Regression test for `agents_extensions/deploy.sh --check` — the drift detector
# behind the extensions-sync CI gate. Guards that --check (a) is read-only,
# (b) exits 0 when a deployed copy matches its source, and (c) exits 1 when it
# diverges. Self-contained: builds a throwaway agents_extensions/.claude tree in
# a temp dir (deploy.sh derives its root from BASH_SOURCE), never touches the
# real repo.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REAL_DEPLOY="$SCRIPT_DIR/../../agents_extensions/deploy.sh"
TMP=$(mktemp -d)
cleanup() { rm -rf "$TMP"; }
trap cleanup EXIT

mkdir -p "$TMP/agents_extensions/claude/skills/demo" "$TMP/.claude/skills/demo"
cp "$REAL_DEPLOY" "$TMP/agents_extensions/deploy.sh"
printf 'hello\n' > "$TMP/agents_extensions/claude/skills/demo/SKILL.md"
printf 'hello\n' > "$TMP/.claude/skills/demo/SKILL.md"

fail=0
run_check() { bash "$TMP/agents_extensions/deploy.sh" --check --target claude --quiet >/dev/null 2>&1; }

# 1. in sync → exit 0
if run_check; then echo "  ok   in-sync → exit 0"; else echo "  FAIL in-sync should exit 0"; fail=1; fi

# 2. read-only: --check must not have created/modified anything
before=$(find "$TMP/.claude" -type f | sort | xargs cksum 2>/dev/null)
run_check || true
after=$(find "$TMP/.claude" -type f | sort | xargs cksum 2>/dev/null)
if [ "$before" = "$after" ]; then echo "  ok   --check is read-only"; else echo "  FAIL --check mutated the tree"; fail=1; fi

# 3. drifted (deployed differs from source) → exit 1
printf 'drift\n' >> "$TMP/.claude/skills/demo/SKILL.md"
if run_check; then echo "  FAIL drift should exit 1"; fail=1; else echo "  ok   drift → exit 1"; fi

# 4. missing deployed copy → exit 1
rm -f "$TMP/.claude/skills/demo/SKILL.md"
if run_check; then echo "  FAIL missing deployed should exit 1"; fail=1; else echo "  ok   missing deployed → exit 1"; fi

# 5. real deploy (no --check) re-syncs → --check passes again
bash "$TMP/agents_extensions/deploy.sh" --target claude --quiet >/dev/null 2>&1
if run_check; then echo "  ok   deploy re-syncs → exit 0"; else echo "  FAIL deploy did not re-sync"; fail=1; fi

if [ "$fail" -ne 0 ]; then echo "[deploy-check-test] FAIL"; exit 1; fi
echo "[deploy-check-test] PASS"
