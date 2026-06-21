# Review Audit: on-premises/security/module-6.1-air-gapped

**Path**: `src/content/docs/on-premises/security/module-6.1-air-gapped.md`

---

## 2026-06-11T13:48:50Z — `REVIEW` — `APPROVE`
On-premises security chapter (#1881, PR #1893). T3→T0 expand 640→5049w (13 sources). Author: cursor. Reviewer: opus (R1, cross-family) NEEDS_CHANGES → fixed. opus found NO fabrication — web-verified the K8s 1.35 image tags against the real `v1.35.0/constants.go` (etcd 3.6.6-0, coredns v1.13.1, pause 3.10.1 all match). 3×P2 ground-checked + orchestrator inline-fixed: (1) OCIRepository `apiVersion` `v1`→`v1beta2` to match the pinned Flux 2.4.x components (OCIRepository graduated to v1 only in Flux 2.6, web-verified), with a durable version note; (2) dropped the removed Harbor "content trust" (Notary v1, removed ~Harbor 2.8) → reframed to cosign/Notation OCI signature storage + admission policy (Kyverno verifyImages / Sigstore policy-controller / Gatekeeper); (3) repointed a mis-cited Trivy-offline source (was a Clair page) → harbor-scanner-trivy configuration (web-verified it documents SCANNER_TRIVY_SKIP_UPDATE/SKIP_JAVA_DB_UPDATE/OFFLINE_SCAN). Re-verified T0/5049w. Build green PRIMARY 2171p. APPROVE.
