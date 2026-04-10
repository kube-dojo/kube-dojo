#!/usr/bin/env bash
# Shared helpers for AI/ML migration phase scripts (#199).
# Source from each phase script: source "$(dirname "$0")/_lib.sh"

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PY="$REPO_ROOT/.venv/bin/python"
TRACK_ROOT="$REPO_ROOT/src/content/docs/ai-ml-engineering"
LOG_DIR="$REPO_ROOT/.pipeline/ai-ml-logs"

mkdir -p "$LOG_DIR"

if [[ ! -x "$PY" ]]; then
  echo "ERROR: $PY not found. Activate or create the venv first." >&2
  exit 1
fi

cd "$REPO_ROOT"

log() { printf '\n[%(%H:%M:%S)T] %s\n' -1 "$*"; }

# write_stub <phase> <seq> <dir> <filename-stem> "<title>" "<topic>"
write_stub() {
  local phase="$1" seq="$2" dir="$3" stem="$4" title="$5" topic="$6"
  local target="$TRACK_ROOT/$dir/module-${phase}.${seq}-${stem}.md"
  local order=$(( (phase + 1) * 100 + seq + 1 ))
  local slug="ai-ml-engineering/${dir}/module-${phase}.${seq}-${stem}"

  if [[ -f "$target" ]]; then
    log "stub exists, skipping: $target"
    return 0
  fi

  log "creating stub: $target"
  mkdir -p "$(dirname "$target")"
  cat > "$target" <<EOF
---
title: "${title}"
slug: ${slug}
sidebar:
  order: ${order}
---
> **AI/ML Engineering Track** | NEW 2026 module — pipeline will expand this stub
>
> **Topic**: ${topic}

## Stub

This module is a placeholder. The v1 quality pipeline will rewrite it from scratch
in REWRITE mode (audit score < 28 triggers full rewrite) using the topic above.
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
