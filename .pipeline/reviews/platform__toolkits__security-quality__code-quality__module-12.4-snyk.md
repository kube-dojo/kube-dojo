## 2026-06-15T21:18:30Z — `REVIEW` — `CHANGES_REQUESTED` → fixed → `APPROVE`

**Reviewer:** opus-inline cross-family R1 (≠ author cursor/Kimi; no gemini) + ground-check + web-verify. **#1996 (Toolkits).**

Author: cursor `--model auto`. 334→5117 prose-w, 5→22 sources. Teaches Software Composition Analysis as a CAPABILITY (transitive deps, reachability, SBOM, prioritization via CVSS/EPSS) with Snyk as the commercial worked example + a Rosetta; honestly labels Snyk commercial/proprietary/non-CNCF ("neither choice is universally correct"). T0; all gates pass; Hypothetical scenario labeled; no fabrication.

**Finding (FIXED by orchestrator):** the Rosetta labeled **Trivy as a "CNCF sandbox project"** — inaccurate. Web-verified vs cncf.io/projects: **Trivy is NOT a CNCF project** (does not appear at any maturity level); it is open-source by **Aqua Security** and is the default scanner *in* CNCF **Harbor** (Graduated). Corrected the cell. Post-fix re-verified T0. **APPROVE.**
