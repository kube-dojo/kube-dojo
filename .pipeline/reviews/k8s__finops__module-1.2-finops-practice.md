# Review Audit: k8s/finops/module-1.2-finops-practice

**Path**: `src/content/docs/k8s/finops/module-1.2-finops-practice.md`
**Current phase**: review

---

## 2026-06-02T22:59:27Z — `REVIEW` — `APPROVE`
Tool-certs wave-2 FinOps/FOCP cross-family R1 (session 95). Reviewer: opus-4.8 (4/5, NEEDS_CHANGES; all 6 keys correct). Fixed 1 verifier-blind P1 (opus web-verified): OpenCost lab wired prometheus.internal.port=9090 but the prometheus-community/prometheus chart's prometheus-server Service exposes port 80 -> connection-refused -> no allocation rows while all 4 acceptance checks still pass (silent break). Set to 80 (chart default). No quiz Q/answer changed. Fixed via PR #1761. Verifier T0/PASS.
