# Review Audit: prerequisites/zero-to-terminal/module-0.4-files-and-directories

**Path**: `src/content/docs/prerequisites/zero-to-terminal/module-0.4-files-and-directories.md`
**Reviewer (cross-family)**: codex
**Session**: 74 — Phase 1 back-catalog review (one cross-family review per module)

---

## 2026-05-30T08:41:14Z — `REVIEW` — `REJECT`

**Reviewer**: codex
**Rubric**: 4.4
**Must-fix**: (1) Unsafe runnable `head -n 10 ~/.kube/config` (dumps real tokens/certs) shown before its own warning. (2) Non-runnable `bash` blocks with placeholder paths/assumed cwd.

---

## 2026-05-30T08:41:14Z — `REVIEW` — `APPROVE`

**Reviewer**: orchestrator-verified (mechanical fix confirmed against the codex must-fix list)
**Note**: Fix applied (cursor; PR pending). kubeconfig inspection now non-secret; placeholder examples marked illustrative. Must-fixes resolved (orchestrator-verified mechanical).
