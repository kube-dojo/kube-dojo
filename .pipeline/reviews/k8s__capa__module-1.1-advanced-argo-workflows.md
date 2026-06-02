# Review Audit: k8s/capa/module-1.1-advanced-argo-workflows

**Path**: `src/content/docs/k8s/capa/module-1.1-advanced-argo-workflows.md`
**First pass**: 2026-04-14T11:19:07Z
**Last pass**: 2026-04-14T11:19:07Z
**Total passes**: 1
**Current phase**: review
**Current reviewer**: -
**Current severity**: None

---

## 2026-04-14T11:19:07Z — `WRITE`

**Writer**: gemini-3.1-pro-preview
**Mode**: write
**Plan**: Draft or improve the module at k8s/capa/module-1.1-advanced-argo-workflows per the topic spec in the module frontmatter and any TODO comments in the existing stub.
**Output**: 33722 chars
**Duration**: 3m 26s

## 2026-06-02T16:56:05Z — `REVIEW` — `APPROVE`
Tool-certs wave-2 CAPA cross-family R1 (session 94). Reviewer: claude opus-4.8 (4/5, NEEDS_CHANGES). 3 verifier-blind config-correctness P1/P2 ground-checked vs upstream Argo Workflows docs and fixed: lifecycle `running` hook now carries its required `expression`; indefinite suspend uses `suspend: {}` (duration:"0" auto-resumes immediately); ConfigMap Resource-template successCondition/failureCondition removed (ConfigMap has no .status). CEL wording softened; latest-stable v4.0.4->v4.0.5; revision_pending removed. The module's many v4.0 facts (v4.0.0=2026-02-04, singular->plural field removals, argo convert, 9 template types/no data) independently WEB-VERIFIED correct. Fixed via PR #1757. Verifier T0/PASS bw5063.
