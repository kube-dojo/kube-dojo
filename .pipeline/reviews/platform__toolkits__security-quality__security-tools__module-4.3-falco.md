## 2026-06-15T20:51:46Z — `REVIEW` — `CHANGES_REQUESTED` → fixed → `APPROVE`

**Reviewer:** opus-inline cross-family R1 (≠ author deepseek; no gemini) + ground-check + web-verify. **#1996 (Toolkits).**

Author: deepseek-v4-pro. 430→5030 prose-w, 4→12 sources. Teaches runtime threat DETECTION as the capability (vs build/deploy controls), with Falco as the worked example (drivers/modern-eBPF, rules, plugins, Falcosidekick, Talon); correctly differentiated from 4.5-tetragon (detection vs enforcement). T0; all gates pass; Hypothetical scenario labeled (round illustrative numbers); no fabricated company stats.

**Finding (FIXED by orchestrator):** the Rosetta CNCF-status row labeled **Tetragon as "Sandbox (as of 2026)"** — inaccurate. Web-verified (cncf.io/projects/cilium + tetragon.io + the OpenSSF/Cilium sources): **Tetragon is a Cilium SUB-PROJECT, not a separately-rated CNCF project**; Cilium is Graduated (2023-10-11). Corrected the cell → "Cilium sub-project (Cilium is Graduated; Tetragon not separately rated)" (consistent with 4.5's correct framing). Verified accurate: **Falco CNCF Graduated Feb 2024**, **KubeArmor CNCF Sandbox**, Sysdig commercial. Post-fix re-verified T0. **APPROVE.**
