#!/usr/bin/env bash
#
# Phase 7 — cross-linking from existing tracks into AI/ML Engineering (#199)
#
# Delegates to Gemini Pro: read docs/migration-decisions.md and the AI/ML
# hub, then add "See also" links from existing modules to the new track.
#
# Gemini edits files directly via dispatch.py with no extra wrapper —
# review with `git diff` before committing.
#

source "$(dirname "$0")/_lib.sh"

PROMPT='You are doing cross-linking work for the KubeDojo curriculum.

Read these files first:
  - docs/migration-decisions.md (overlap audit results)
  - src/content/docs/ai-ml-engineering/index.md (AI/ML Engineering hub with phase list)

For every existing kubedojo module that should reference an AI/ML Engineering
module, add a single "See also" bullet at the bottom of the relevant section.

Strong cross-link candidates (look for these patterns):
  - CKA / CKAD storage modules → ai-ml-engineering/mlops/module-5.7-data-pipelines/
  - CKA networking → ai-ml-engineering/mlops/module-5.4-kubernetes-for-ml/
  - cloud GPU / accelerator content → ai-ml-engineering/ai-infrastructure/
  - platform/disciplines/mlops/* → ai-ml-engineering/mlops/ (full phase)
  - on-premises GPU / bare metal → ai-ml-engineering/ai-infrastructure/
  - platform/toolkits/observability → ai-ml-engineering/mlops/module-5.10-ml-monitoring/
  - container/Docker fundamentals → ai-ml-engineering/mlops/module-5.2-docker-for-ml/

Rules:
  - Use slug links (no .md extension), trailing slash.
  - Add at most ONE see-also bullet per file. Do not flood.
  - Skip files that already reference ai-ml-engineering.
  - Edit files directly. Do NOT create new files.
  - Output a final list of every file you modified.
'

log "Dispatching cross-linking task to Gemini Pro"
"$PY" scripts/dispatch.py gemini "$PROMPT" --review

log "Done. Review with: git diff --stat"
log "Commit when satisfied."
