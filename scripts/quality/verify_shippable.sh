#!/usr/bin/env bash
# verify_shippable — the codified local Definition-of-Done for content (#1961).
#
# A module is NOT shippable on density/tier alone. The learn-ukrainian autopsy
# (2026-06-14) and KubeDojo's own CKS-5.2 break (an out-of-enum `lab.difficulty`
# that passed every build-time gate and broke `main`'s deploy) show the same
# lesson: Definition-of-Done must include RENDER. This wraps both axes into one
# green/red:
#
#   1. verify_module.py  — density / tier gates (per file given)
#   2. npm run build     — full astro render + content-collection Zod schema
#                          validation (the gate CI defers to deploy and that
#                          verify_module.py does NOT do)
#
# Run it before declaring any content wave done. Mirrors the PR gate in
# .github/workflows/build-check.yml so "green locally" == "green in CI".
#
# Usage:
#   scripts/quality/verify_shippable.sh [FILE ...]   # density-gate each FILE, then build
#   scripts/quality/verify_shippable.sh --no-density  # build only (schema/render)
#   scripts/quality/verify_shippable.sh               # build only (no files given)
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$REPO_ROOT"

RUN_DENSITY=1
FILES=()
for arg in "$@"; do
  case "$arg" in
    --no-density) RUN_DENSITY=0 ;;
    -h|--help)
      grep '^#' "$0" | sed 's/^# \{0,1\}//'
      exit 0
      ;;
    *) FILES+=("$arg") ;;
  esac
done

fail=0

if [[ "$RUN_DENSITY" -eq 1 && "${#FILES[@]}" -gt 0 ]]; then
  echo "==> [1/2] density / tier gates (verify_module.py)"
  for f in "${FILES[@]}"; do
    echo "    --- $f"
    if ! python scripts/quality/verify_module.py "$f"; then
      echo "    DENSITY/TIER FAIL: $f" >&2
      fail=1
    fi
  done
else
  echo "==> [1/2] density / tier gates SKIPPED (no files / --no-density)"
fi

echo "==> [2/2] astro build (render + Zod schema) — the render gate"
# Surface the first schema/render error without dumping the ~5,600-line route
# manifest (per feedback_never_read_build_logs).
BUILD_LOG="$(mktemp)"
trap 'rm -f "$BUILD_LOG"' EXIT
if npm run build >"$BUILD_LOG" 2>&1; then
  grep -E "built in|[0-9]+ page" "$BUILD_LOG" | tail -1 || true
else
  echo "    BUILD FAILED — first schema/render error:" >&2
  grep -nE "InvalidContentEntryDataError|does not match|Error|error:" "$BUILD_LOG" | head -10 >&2 || tail -20 "$BUILD_LOG" >&2
  fail=1
fi

if [[ "$fail" -ne 0 ]]; then
  echo "RESULT: NOT SHIPPABLE ❌" >&2
  exit 1
fi
echo "RESULT: SHIPPABLE ✅"
