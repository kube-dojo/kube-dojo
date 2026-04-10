#!/usr/bin/env bash
#
# Phase 5 — full deduplication audit (#199)
#
# Compares every ai-ml-engineering module against existing tracks
# (k8s, cloud, linux, prerequisites, platform) using Gemini Pro to judge
# overlap. Output: docs/migration-decisions.md
#
# Sequential. Safe to re-run — overwrites the report each time.
#

source "$(dirname "$0")/_lib.sh"

log "Running full dedupe audit (this can take a while — sequential Gemini calls)"
"$PY" scripts/dedupe_audit.py \
  --source ai-ml-engineering \
  --against k8s,cloud,linux,prerequisites,platform \
  --output docs/migration-decisions.md

log "Done. Review docs/migration-decisions.md for merge / cross-link recommendations."
