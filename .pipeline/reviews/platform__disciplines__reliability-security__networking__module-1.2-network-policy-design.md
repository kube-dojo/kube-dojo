## 2026-06-15T19:50:28Z — `REVIEW` — `CHANGES_REQUESTED` → fixed → `APPROVE`

**Reviewer:** opus-inline cross-family R1 (≠ author deepseek; no gemini) + ground-check + web-verify. **#1953.**

Author: deepseek-v4-pro. ~1016→5173 prose-w, 0→16 sources. Teaches default-deny baseline, the NetworkPolicy API semantics (additive-only, default-allow→first-policy-flips-to-deny), the design patterns (namespace isolation, tiered, DNS-egress gotcha, metadata block), native limitations, AdminNetworkPolicy/CiliumNetworkPolicy/Calico GlobalNetworkPolicy. T0; all gates pass.

**Finding (FIXED by orchestrator):** a "Did You Know" cited "A 2024 survey by Fairwinds found that **83%** of clusters have no network policies... 17%... <3%" — **fabricated figures** (deepseek invented-numbers failure mode). Web-verified vs the real [2024 Fairwinds Kubernetes Benchmark Report](https://www.fairwinds.com/blog/2024-kubernetes-benchmark-report-kubernetes-workload-analysis) (330,000+ workloads): the actual stat is **58% of organizations have workloads missing network policy**. Replaced the fabricated sentence with the verified figure + source link. Ground-checked Cilium "graduated October 2023" — accurate (cncf.io). Post-fix re-verified T0. **APPROVE.**
