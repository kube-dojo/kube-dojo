# Review Audit: on-premises/provisioning/module-2.3-immutable-os

**Path**: `src/content/docs/on-premises/provisioning/module-2.3-immutable-os.md`

---

## 2026-06-11T01:12:19Z — `REVIEW` — `APPROVE`
On-premises wave 3 (#1881, PR #1886). Back-catalog review→flip, dense T0/score 5.0. Reviewer: cursor (R1, cross-family, NO gemini). 2 P1 (Talos apiserver/cm/scheduler are static pods not machined services; talosctl upgrade has NO --dry-run → use upgrade-k8s --dry-run) + 8 P2 (FCOS ostree not A/B; Flatcar CNCF Incubating web-verified 2024; TUF Targets-vs-Root; CoreOS EOL 2020; Flatcar CABPK+Ignition CAPI; ChromeOS 300M softened) + 2 nits. 1 FP rejected (apiclient prefix-get valid). Orchestrator ground-checked EVERY finding vs the live file + web-verified currency both directions; consolidated cursor fix-pass diff-audited (1 cursor error caught+fixed); build green PRIMARY 2171p; merged → main (PR #1886). APPROVE.
