#!/usr/bin/env bash
# #388 Phase 1 #9 — sequential rewrite of AI/ML Tier-1 worst 11 modules
# Continues on failure; each module gets its own log entry.
set -u

cd "$(dirname "$0")/.."

LOG="logs/quality/phase1-tier1-batch.log"
STATUS="logs/quality/phase1-tier1-status.tsv"
mkdir -p logs/quality

slugs=(
  ai-ml-engineering-ai-native-development-module-1.8-ai-assisted-debugging-optimization
  ai-ml-engineering-vector-rag-module-1.6-home-scale-rag-systems
  ai-ml-engineering-generative-ai-module-1.2-tokenization-text-processing
  ai-ml-engineering-deep-learning-module-1.3-training-neural-networks
  ai-ml-engineering-ai-infrastructure-module-1.4-local-inference-stack-for-learners
  ai-ml-engineering-prerequisites-module-1.2-home-ai-workstation-fundamentals
  ai-ml-engineering-mlops-module-1.11-notebooks-to-production-for-ml-llms
  ai-ml-engineering-advanced-genai-module-1.10-single-gpu-local-fine-tuning
  ai-ml-engineering-ai-native-development-module-1.10-anthropic-agent-sdk-and-runtime-patterns
  ai-ml-engineering-prerequisites-module-1.3-reproducible-python-cuda-rocm-environments
  ai-ml-engineering-prerequisites-module-1.4-notebooks-scripts-project-layouts
)

echo "BATCH START: $(date '+%F %T')  total=${#slugs[@]}" | tee -a "$LOG"
echo -e "i\tslug\tstart\tend\twall_s\tresult" >> "$STATUS"

i=0
for slug in "${slugs[@]}"; do
  i=$((i+1))
  start=$(date '+%F %T')
  start_epoch=$(date +%s)
  echo "" | tee -a "$LOG"
  echo "===== [$i/${#slugs[@]}] $slug =====" | tee -a "$LOG"
  echo "start: $start" | tee -a "$LOG"

  # primary clean guard
  if [[ -n "$(git status --porcelain)" ]]; then
    echo "ABORT: primary repo dirty before module $i — bailing" | tee -a "$LOG"
    echo -e "$i\t$slug\t$start\t$(date '+%F %T')\t-\tdirty_pre" >> "$STATUS"
    break
  fi

  set +e
  .venv/bin/python -m scripts.quality.pipeline run-module "$slug" >> "$LOG" 2>&1
  rc=$?
  set -e

  end=$(date '+%F %T')
  wall=$(( $(date +%s) - start_epoch ))
  if [[ $rc -eq 0 ]]; then
    final=$(.venv/bin/python -c "
import json
from pathlib import Path
p = Path('.pipeline/quality-pipeline/$slug.json')
print(json.loads(p.read_text()).get('stage','?'))" 2>/dev/null || echo "unknown")
    echo "end:   $end  wall=${wall}s  stage=$final" | tee -a "$LOG"
    echo -e "$i\t$slug\t$start\t$end\t$wall\t$final" >> "$STATUS"
  else
    echo "end:   $end  wall=${wall}s  rc=$rc FAILED" | tee -a "$LOG"
    echo -e "$i\t$slug\t$start\t$end\t$wall\trc=$rc" >> "$STATUS"
  fi
done

echo "" | tee -a "$LOG"
echo "BATCH END: $(date '+%F %T')" | tee -a "$LOG"
echo "" | tee -a "$LOG"
echo "Summary:" | tee -a "$LOG"
column -t -s $'\t' "$STATUS" | tee -a "$LOG"
