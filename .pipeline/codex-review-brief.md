# Codex Review Brief: v1_pipeline.py

## Goal

Full architectural review of `scripts/v1_pipeline.py` (4077 lines). The pipeline processes 816 curriculum modules through: WRITE → REVIEW → CHECK → SCORE. It's churning — modules get rebuilt 3-4 times without converging, 124 modules were stuck in dead-end states, and the whole system is fragile.

## Critical Questions for Codex

1. **Convergence**: Why don't modules settle? The write→review→check loop can cycle indefinitely. Is the architecture fundamentally sound or does it need restructuring?
2. **Dead ends**: CHECK failures had no recovery path (just patched today — review that patch). Are there other dead ends?
3. **State machine**: The phase transitions (pending→write→review→check→score→done) have many edge cases and resume paths. Is the state machine correct? Are there unreachable states or missing transitions?
4. **Error accumulation**: Errors append forever, modules carry baggage from 10+ runs ago. Should errors reset on each run?
5. **Retry logic**: Multiple retry mechanisms (max_retries loop, check_failures counter, review fallback chain). Are they coherent or fighting each other?
6. **Code quality**: 4077 lines in one file. Dead code, unused variables, copy-paste patterns, functions that should be extracted.

## File Structure (line ranges for chunked review)

| Chunk | Lines | Section | Key functions |
|-------|-------|---------|---------------|
| 1 | 1-200 | Config, logging, state management | `dispatch_auto`, `load_state`, `save_state`, `get_module_state` |
| 2 | 200-580 | Knowledge cards & fact ledgers | `ensure_knowledge_card`, `step_fact_ledger`, `ensure_fact_ledger`, `step_content_aware_fact_ledger` |
| 3 | 580-970 | Fact merging, knowledge packets, writing | `_merge_fact_ledgers`, `extract_knowledge_packet`, `count_assets`, `step_write` |
| 4 | 970-1400 | Review parsing, severity, index updates | `compute_severity`, `step_update_index`, `_extract_review_json` |
| 5 | 1400-1730 | Edit application & step_review | `apply_review_edits`, `step_review`, `_find_anchor`, `_atomic_write_text` |
| 6 | 1730-2060 | Link checking & integrity checks | `_probe_url`, `step_check_integrity`, URL caching |
| 7 | 2060-2130 | Deterministic checks | `step_check` |
| 8 | 2130-2500 | run_module (first half) | Initial write, fact ledger, write→review loop start, integrity gate |
| 9 | 2500-2880 | run_module (second half) | Review fallback chain, edit application, CHECK/SCORE, **the new retry patch** |
| 10 | 2880-3560 | CLI commands (part 1) | `cmd_audit_all`, `cmd_run`, `cmd_run_section`, `cmd_status`, `_render_status_dashboard_html` |
| 11 | 3560-4077 | CLI commands (part 2) | `cmd_resume`, **`cmd_reset_stuck` (new)**, `cmd_e2e`, `main()` |

## How to Review

For each chunk, Codex should:
1. Read the specified line range
2. Identify bugs, dead ends, logic errors, unreachable code
3. Flag architectural issues (not style nits)
4. Suggest concrete fixes with line numbers
5. Rate severity: CRITICAL (breaks convergence), HIGH (causes stuck states), MEDIUM (inefficiency), LOW (cleanup)

## Today's Changes (review these carefully)

1. **Lines 2757-2787**: CHECK retry logic — routes failures back to write phase instead of dead-ending. New `check_failures` counter, max 2 retries.
2. **Lines 3587-3634**: `cmd_reset_stuck` — resets modules stuck in dead-end states.

## Supporting Files

- `scripts/checks/structural.py` — deterministic structural checks (CheckResult dataclass, section/quiz/frontmatter validation)
- `scripts/checks/ukrainian.py` — Ukrainian language checks
- `scripts/dispatch.py` — LLM dispatch (Gemini CLI, Claude API)
- `.pipeline/state.yaml` — module state (phase, errors, scores, fact_ledger per module)

## Commands to Run the Review

```bash
# Chunk 1: Config & state
codex -q "Review scripts/v1_pipeline.py lines 1-200. Focus on: state management correctness, race conditions in save_state, logging setup. See .pipeline/codex-review-brief.md for full context."

# Chunk 2: Knowledge cards & fact ledgers  
codex -q "Review scripts/v1_pipeline.py lines 200-580. Focus on: cache invalidation, fact ledger reliability, error handling. See .pipeline/codex-review-brief.md for context."

# ... etc for each chunk (see line ranges in table above)

# Final: Architecture review
codex -q "Read .pipeline/codex-review-brief.md and scripts/v1_pipeline.py function list (grep '^def'). Give an architectural assessment: state machine correctness, convergence guarantees, dead-end analysis. Don't read the whole file — use the brief and function signatures."
```
