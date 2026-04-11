#!/usr/bin/env bash
# Shared helpers for On-Premises expansion phase scripts (#197).
# Source from each phase script: source "$(dirname "$0")/_lib.sh"
# Modeled on scripts/ai-ml/_lib.sh.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PY="$REPO_ROOT/.venv/bin/python"
TRACK_ROOT="$REPO_ROOT/src/content/docs/on-premises"
LOG_DIR="$REPO_ROOT/.pipeline/on-prem-logs"

mkdir -p "$LOG_DIR"

if [[ ! -x "$PY" ]]; then
  echo "ERROR: $PY not found. Activate or create the venv first." >&2
  exit 1
fi

cd "$REPO_ROOT"

log() { printf '\n[%(%H:%M:%S)T] %s\n' -1 "$*"; }

# write_stub <num> <section-dir> <filename-stem> "<title>" "<topic>"
#   num is the dotted module number (e.g. 3.5, 9.1)
write_stub() {
  local num="$1" sec="$2" stem="$3" title="$4" topic="$5"
  local target="$TRACK_ROOT/$sec/module-${num}-${stem}.md"
  # sidebar order: major * 100 + minor (e.g. 3.5 -> 305, 9.1 -> 901)
  local major="${num%.*}"
  local minor="${num#*.}"
  local order=$(( major * 100 + minor ))
  local slug="on-premises/${sec}/module-${num}-${stem}"

  if [[ -f "$target" ]]; then
    log "stub exists, skipping: $target"
    return 0
  fi

  log "creating stub: $target"
  mkdir -p "$(dirname "$target")"
  cat > "$target" <<EOF
---
title: "Module ${num}: ${title}"
slug: ${slug}
sidebar:
  order: ${order}
---
> **On-Premises Track** | NEW 2026 module — pipeline will expand this stub
>
> **Topic**: ${topic}

## Stub

This module is a placeholder. The v1 quality pipeline will rewrite it from
scratch in REWRITE mode (audit score < 28 triggers full rewrite) using the
topic above.
EOF
}

# run_pipeline <module-key> — runs v1 pipeline on a single module, logs to file
run_pipeline() {
  local key="$1"
  local logf="$LOG_DIR/$(echo "$key" | tr '/' '_').log"
  log "PIPELINE: $key  → log: $logf"
  if "$PY" scripts/v1_pipeline.py run "$key" 2>&1 | tee "$logf"; then
    log "✓ pipeline OK: $key"
    return 0
  else
    log "✗ pipeline FAILED: $key — see $logf"
    return 1
  fi
}
