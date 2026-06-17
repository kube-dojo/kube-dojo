## 2026-06-17 — `REVIEW` — `APPROVE`
**Reviewer:** opus-inline cross-family R2 (Anthropic ≠ codex/OpenAI fix author; ≠ cursor/Kimi R1) + independent upstream web-verification before the fix. **#1996, PR (Ansible-arc fix-pass).** Fix author: codex gpt-5.5 (`9c634bdb8`).
Cursor R1 flagged this module NEEDS CHANGES for the densest cluster of fabricated API surface in the arc. All blockers corrected and web-verified.
**Defects fixed (web-verified vs Operator-SDK watches/advanced_options/finalizers/status docs + controller-runtime workqueue metrics):**
- Fabricated watches.yaml fields removed: `maxConcurrentReconciles:` (a Helm-operator field, not Ansible) and `dependentWatches:` (does not exist) → replaced with the real `watchDependentResources: true`; concurrency moved to the `--max-concurrent-reconciles` flag / `MAX_CONCURRENT_RECONCILES_<KIND>_<GROUP>` env var. The learning outcome, prose, tables, lab, and quiz were all reframed to the real mechanism while keeping the scaling pedagogy. 0 residual `maxConcurrentReconciles`.
- Fabricated `ANSIBLE_OPERATOR_PLUGINS_*` env vars removed → `MAX_CONCURRENT_RECONCILES_*` (concurrency), `ANSIBLE_VERBOSITY_<KIND>_<GROUP>` (verbosity); reconcile period via watches.yaml `reconcilePeriod` / `--reconcile-period` / the `ansible.sdk.operatorframework.io/reconcile-period` annotation.
- Finalizer anti-pattern fixed: the deletion role no longer manually patches `finalizers: []`. Prose now correctly states the SDK removes the configured finalizer after the finalizer role/playbook completes successfully; the phantom-deletion and interrupted-reconcile narratives were reframed around SDK-driven removal + idempotent 404 handling.
- Status condition type `AnsibleFailed` → **`Failure`** (reason `Failed`); `Running` retained.
- Metric `controller_runtime_reconcile_queue_length` → **`workqueue_depth`** (the real controller-runtime metric, labeled by controller `name`).
**Ground-checks:** verifier **T0 PASS**, body_words **5238** (floor 5000); 0 residual fabricated tokens; no NEW fabricated API; frontmatter untouched; 17 reachable Sources; `Hypothetical scenario:` labels intact.
**APPROVE.**
