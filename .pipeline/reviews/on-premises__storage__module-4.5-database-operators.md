# Review Audit: on-premises/storage/module-4.5-database-operators

**Path**: `src/content/docs/on-premises/storage/module-4.5-database-operators.md`

---

## 2026-06-11T12:00:47Z — `REVIEW` — `APPROVE`
On-premises storage (#1881, PR #1892). T3→T0 expand 1878→5809w (heuristic score was 1.5). Author: codex. Reviewer: cursor (R1, cross-family) APPROVE_WITH_NITS 0P1+4P2 — verified bitnami-clean (CNPG ghcr.io/cloudnative-pg/postgresql, MinIO quay.io) + CNCF maturity (CNPG Sandbox, Vitess Graduated); 4 P2 ground-checked+applied: Kubernetes Leases≠DB primary fencing (→readiness+fencing annotation+BMC/IPMI bare-metal split-brain); walStorage mounts dedicated WAL PVC at /var/lib/postgresql/wal; attribute K8s support to 1.29 supported-releases matrix; lab secret lands in default ns. orchestrator inline-fixed; re-verified T0/5809w. APPROVE.
