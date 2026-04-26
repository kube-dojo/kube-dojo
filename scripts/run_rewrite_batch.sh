#!/usr/bin/env bash
# #388 — full prioritized rewrite batch.
#   Tier A: ai-ml-engineering         (Phase 1 worst 11 first, rest after)
#   Tier B: ai/ bridge track
#   Tier C: on-premises/ai-ml-infrastructure
#   Tier D: platform/disciplines/data-ai (mlops + aiops)
#   Tier E: everything else
#
# workers=1 per feedback_claude_owns_pipeline.md and feedback_batch_worker_cap.md.
# Continues on per-module failure. Skips slugs already at COMMITTED so kill+restart resumes.
set -u

cd "$(dirname "$0")/.."

QUEUE="${REWRITE_QUEUE:-/tmp/388-rewrite-queue.tsv}"
LOG="logs/quality/phase-rewrite-batch.log"
STATUS="logs/quality/phase-rewrite-status.tsv"
mkdir -p logs/quality

if [[ ! -f "$QUEUE" ]]; then
  echo "ABORT: queue file $QUEUE missing" >&2
  exit 2
fi

total=$(wc -l < "$QUEUE" | tr -d ' ')
echo "BATCH START: $(date '+%F %T')  queue=$QUEUE  total=$total" | tee -a "$LOG"

# header (idempotent)
if [[ ! -f "$STATUS" ]]; then
  echo -e "i\ttier\tslug\tstart\tend\twall_s\tresult" > "$STATUS"
fi

stage_of() {
  local slug="$1"
  .venv/bin/python -c "
import json, sys
from pathlib import Path
p = Path('.pipeline/quality-pipeline/$slug.json')
if not p.exists():
    print('NOSTATE'); sys.exit(0)
try:
    print(json.loads(p.read_text()).get('stage','?'))
except Exception:
    print('READERR')
" 2>/dev/null
}

primary_dirty_tracked() {
  # only TRACKED modifications count; untracked logs/scripts are fine
  [[ -n "$(git diff --name-only && git diff --cached --name-only)" ]]
}

while IFS=$'\t' read -r idx tier wpp words slug; do
  [[ -z "$slug" ]] && continue
  start=$(date '+%F %T')
  start_epoch=$(date +%s)

  pre=$(stage_of "$slug")
  if [[ "$pre" == "COMMITTED" ]]; then
    echo "" | tee -a "$LOG"
    echo "===== [$idx/$total] $tier  $slug =====" | tee -a "$LOG"
    echo "skip:  already COMMITTED" | tee -a "$LOG"
    echo -e "$idx\t$tier\t$slug\t$start\t$start\t0\tskip_committed" >> "$STATUS"
    continue
  fi

  if primary_dirty_tracked; then
    echo "" | tee -a "$LOG"
    echo "ABORT at [$idx/$total] $slug — primary dirty (tracked changes)" | tee -a "$LOG"
    git status -s | head -5 | tee -a "$LOG"
    echo -e "$idx\t$tier\t$slug\t$start\t$(date '+%F %T')\t-\tdirty_pre" >> "$STATUS"
    break
  fi

  echo "" | tee -a "$LOG"
  echo "===== [$idx/$total] $tier  wpp=$wpp  $slug =====" | tee -a "$LOG"
  echo "start: $start" | tee -a "$LOG"

  set +e
  .venv/bin/python -m scripts.quality.pipeline run-module "$slug" >> "$LOG" 2>&1
  rc=$?
  set -e

  end=$(date '+%F %T')
  wall=$(( $(date +%s) - start_epoch ))
  post=$(stage_of "$slug")
  if [[ $rc -eq 0 ]]; then
    echo "end:   $end  wall=${wall}s  stage=$post" | tee -a "$LOG"
    echo -e "$idx\t$tier\t$slug\t$start\t$end\t$wall\t$post" >> "$STATUS"
  else
    echo "end:   $end  wall=${wall}s  rc=$rc  stage=$post  FAILED" | tee -a "$LOG"
    echo -e "$idx\t$tier\t$slug\t$start\t$end\t$wall\trc=$rc/$post" >> "$STATUS"
  fi
done < "$QUEUE"

echo "" | tee -a "$LOG"
echo "BATCH END: $(date '+%F %T')" | tee -a "$LOG"
echo "" | tee -a "$LOG"
column -t -s $'\t' "$STATUS" | tail -50 | tee -a "$LOG"
