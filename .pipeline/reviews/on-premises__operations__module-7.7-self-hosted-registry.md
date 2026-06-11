# Review Audit: on-premises/operations/module-7.7-self-hosted-registry

**Path**: `src/content/docs/on-premises/operations/module-7.7-self-hosted-registry.md`

---

## 2026-06-11T10:52:13Z — `REVIEW` — `APPROVE`
On-premises wave 4 batch 3 (#1881, PR #1891). T3→T0 expand-to-floor + structural rebuild. Author: codex gpt-5.5 (2098→5159w, 33 sources, added Why-Matters/DYK/Common-Mistakes-table/details-quiz/lab-checkboxes/Next-link). Reviewer: cursor composer-2.5 (R1, cross-family, NO gemini) NEEDS_CHANGES 1P1+3P2+4nit — ALL ground-checked + web-verified: P1 cosign sign/verify missing --allow-http-registry for plain-HTTP Harbor lab (Step 5 break); chartmuseum/notary chart stanzas obsolete (ChartMuseum removed Harbor v2.8.0, Notary deprecated v2.8); signature storage reframed onto OCI 1.1 referrers; Compose host-reqs scoped; 1.26 in-tree cred-provider precision; version-dependent UI badge. Orchestrator inline-fixed + re-verified T0/5159w. Build green PRIMARY 2171p. APPROVE.
