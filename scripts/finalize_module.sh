#!/usr/bin/env bash
# scripts/finalize_module.sh — canonical per-module finalize for curriculum waves.
#
# Bundles the deterministic finalize steps for ONE module so /telemetry is
# auto-populated on EVERY wave. Before #1978, record-build was a manual CLI call
# separate from the finalize flow and got forgotten → the dashboard went stale.
#
# This helper runs, in order:
#   1. GUARD  — assert the .pipeline/reviews APPROVE record exists (latest verdict
#               is APPROVE). Prevents flipping a module to COMMITTED with no review
#               — a real past gotcha.
#   2. git add -f <review-record>           (track the review record)
#   3. reset-stage <stage-slug> COMMITTED   (board flip — scripts.quality.pipeline)
#   4. record-build <passthrough args>      (telemetry — scripts.agent_telemetry)
#
# The bespoke APPROVE prose is written by the CALLER before invoking this (it
# varies per module); the helper only verifies + tracks it, then flips + records.
#
# Usage:
#   scripts/finalize_module.sh [--dry-run] <stage-slug> <review-record-path> \
#       -- <record-build args…>
#
# Example:
#   scripts/finalize_module.sh \
#     platform-disciplines-core-platform-platform-engineering-module-2.3-internal-developer-platforms \
#     .pipeline/reviews/platform__disciplines__core-platform__platform-engineering__module-2.3-internal-developer-platforms.md \
#     -- --track platform/disciplines/core-platform/platform-engineering \
#        --slug module-2.3-internal-developer-platforms \
#        --module-title "Internal Developer Platforms (IDPs)" \
#        --source orchestrator --no-swarm --swarm-note "solo expand" --pr 1980 \
#        --participant "role=author,agent=cursor,model=auto,total_tokens=240000,token_source=est" \
#        --participant "role=reviewer,agent=codex,model=gpt-5.5,total_tokens=60000,token_source=est"
#
# Run from anywhere inside the repo (resolves the repo root via git). Review-record
# paths are interpreted relative to the repo root.
set -euo pipefail

usage() { sed -n '2,40p' "$0"; }

DRY_RUN=0
while [ $# -gt 0 ]; do
  case "$1" in
    -h|--help) usage; exit 0 ;;
    -n|--dry-run) DRY_RUN=1; shift ;;
    --) break ;;            # no positionals supplied before --
    -*) echo "finalize_module: unknown flag '$1'" >&2; usage >&2; exit 2 ;;
    *) break ;;             # first positional (stage-slug)
  esac
done

STAGE_SLUG="${1:-}"
REVIEW_PATH="${2:-}"
if [ -z "$STAGE_SLUG" ] || [ -z "$REVIEW_PATH" ]; then
  echo "finalize_module: missing <stage-slug> and/or <review-record-path>" >&2
  usage >&2; exit 2
fi
shift 2 || true

if [ "${1:-}" != "--" ]; then
  echo "finalize_module: expected '--' before the record-build args" >&2
  usage >&2; exit 2
fi
shift  # drop the --
if [ $# -eq 0 ]; then
  echo "finalize_module: no record-build args after '--'" >&2
  usage >&2; exit 2
fi

REPO_ROOT="$(git rev-parse --show-toplevel)"
cd "$REPO_ROOT"

# Resolve the review record relative to the repo root.
case "$REVIEW_PATH" in
  /*) REVIEW_ABS="$REVIEW_PATH" ;;
  *)  REVIEW_ABS="$REPO_ROOT/$REVIEW_PATH" ;;
esac

# --- Step 1: GUARD — the APPROVE review record must exist and be APPROVE'd ---
if [ ! -s "$REVIEW_ABS" ]; then
  echo "finalize_module: review record missing or empty: $REVIEW_PATH" >&2
  echo "  Write the .pipeline/reviews APPROVE record BEFORE finalizing." >&2
  exit 3
fi
LAST_HEADER="$(grep -E '^##[[:space:]].*REVIEW' "$REVIEW_ABS" | tail -1 || true)"
if [ -z "$LAST_HEADER" ]; then
  echo "finalize_module: no '## … REVIEW …' verdict header in $REVIEW_PATH" >&2
  exit 3
fi
if ! printf '%s' "$LAST_HEADER" | grep -q 'APPROVE'; then
  echo "finalize_module: latest review verdict is not APPROVE — refusing to flip." >&2
  echo "  latest header: $LAST_HEADER" >&2
  exit 3
fi

# Pick the project interpreter (.venv preferred).
PY="$REPO_ROOT/.venv/bin/python"
[ -x "$PY" ] || PY="python3"

run() {
  if [ "$DRY_RUN" -eq 1 ]; then
    printf '[dry-run] '; printf '%q ' "$@"; printf '\n'
  else
    "$@"
  fi
}

echo "finalize_module: $STAGE_SLUG (guard OK — latest verdict APPROVE)"
# --- Step 2: track the review record ---
run git add -f "$REVIEW_ABS"
# --- Step 3: board flip ---
run "$PY" -m scripts.quality.pipeline reset-stage "$STAGE_SLUG" COMMITTED
# --- Step 4: telemetry (record-build) ---
# Run as a SCRIPT, not `-m scripts.agent_telemetry`: agent_telemetry.py uses flat
# sibling imports (`from telemetry_store import …`), which need scripts/ on sys.path.
# The `-m` form puts repo-root on the path instead → ModuleNotFoundError (#1978 dogfood).
run "$PY" "$REPO_ROOT/scripts/agent_telemetry.py" record-build "$@"

echo "finalize_module: done ($([ "$DRY_RUN" -eq 1 ] && echo dry-run || echo committed)) — $STAGE_SLUG"
