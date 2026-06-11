# Review Audit: on-premises/storage/module-4.4-object-storage-bare-metal

**Path**: `src/content/docs/on-premises/storage/module-4.4-object-storage-bare-metal.md`

---

## 2026-06-11T12:00:47Z — `REVIEW` — `APPROVE`
On-premises storage (#1881, PR #1892). T3→T0 expand 1619→5159w. Author: cursor. Reviewer: codex (R1, cross-family) NEEDS_CHANGES 3P1+4P2+nit — ALL ground-checked+web-verified: invalid Tenant CRD shape→pools[].volumeClaimTemplate; operator replicaCount 2+anti-affinity wouldn't deploy on single-node kind→1 replica; quiz 800GiB-vs-5TiB single-PUT contradiction; MinIO/AIStor edition+drive-limit+mc-quota currency dated (CE archived 2026-04, AIStor Free/Lite/Enterprise tiers); heading casing; typo. Fix dispatched to codex, diff-audited; bitnami-clean (quay.io/minio). re-verified T0/5159w. APPROVE.
