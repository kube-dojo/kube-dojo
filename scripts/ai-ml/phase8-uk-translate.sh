#!/usr/bin/env bash
#
# Phase 8 — Ukrainian translation of the AI/ML Engineering track (#199)
#
# Translates every phase one section at a time. uk_sync handles:
#   - skipping already-translated files (resume-friendly)
#   - chunked translation for modules > 40K chars
#   - index.md discovery (after the #195 fix)
#
# This is the heaviest phase by far. Each phase script call below is one
# `translate-section` invocation — sequential, fail-fast.
#
# Usage:
#   bash scripts/ai-ml/phase8-uk-translate.sh                # all phases
#   bash scripts/ai-ml/phase8-uk-translate.sh prerequisites  # one phase only
#

source "$(dirname "$0")/_lib.sh"

PHASES=(
  "ai-ml-engineering/prerequisites"
  "ai-ml-engineering/ai-native-development"
  "ai-ml-engineering/generative-ai"
  "ai-ml-engineering/vector-rag"
  "ai-ml-engineering/frameworks-agents"
  "ai-ml-engineering/mlops"
  "ai-ml-engineering/ai-infrastructure"
  "ai-ml-engineering/advanced-genai"
  "ai-ml-engineering/multimodal-ai"
  "ai-ml-engineering/deep-learning"
  "ai-ml-engineering/classical-ml"
  "ai-ml-engineering/history"
)

translate_phase() {
  local section="$1"
  local logf="$LOG_DIR/uk_$(echo "$section" | tr '/' '_').log"
  log "translating $section → $logf"
  if "$PY" scripts/uk_sync.py translate-section "$section" 2>&1 | tee "$logf"; then
    log "✓ $section"
  else
    log "✗ $section — see $logf"
    return 1
  fi
}

if (( $# > 0 )); then
  for arg in "$@"; do
    translate_phase "ai-ml-engineering/$arg"
  done
else
  for p in "${PHASES[@]}"; do
    translate_phase "$p"
  done
fi

log "Phase 8 complete. Run 'npm run build' and 'python scripts/uk_sync.py status' to verify."
