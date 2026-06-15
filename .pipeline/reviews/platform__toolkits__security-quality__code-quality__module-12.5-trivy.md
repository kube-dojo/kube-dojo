## 2026-06-15T21:18:30Z — `REVIEW` — `CHANGES_REQUESTED` → fixed → `APPROVE`

**Reviewer:** opus-inline cross-family R1 (≠ author deepseek; no gemini) + ground-check + web-verify. **#1996 (Toolkits).**

Author: deepseek-v4-pro. 459→5120 prose-w, 5→16 sources. Teaches unified open-source scanning as a CAPABILITY (images/fs/IaC/K8s/SBOM/secrets) with Trivy as the worked example + a Rosetta; correctly frames Trivy as Harbor's (CNCF Graduated) default scanner; SBOM (CycloneDX/SPDX), VEX, Trivy Operator covered. T0; all gates pass.

**Findings (FIXED by orchestrator):** (1) a "Did You Know" origin story carried unsourced embellishment — "single engineer … weekend project," "first-scan time to under 15 seconds," "one of the most widely deployed" — trimmed to the verifiable, durable core (Teppei Fukuda created Trivy at Aqua, first release 2019, the compact self-contained-DB / single-binary design that removes the database-server dependency). (2) A closing **fabricated, promotional unattributed quote** ("The best scanner is the one you actually run. Trivy makes security scanning so easy there is no excuse…") — replaced with a neutral durable takeaway (no advocacy, no quote). Post-fix re-verified T0. **APPROVE.**
