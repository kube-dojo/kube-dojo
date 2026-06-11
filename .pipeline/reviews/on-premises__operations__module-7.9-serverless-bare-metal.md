# Review Audit: on-premises/operations/module-7.9-serverless-bare-metal

**Path**: `src/content/docs/on-premises/operations/module-7.9-serverless-bare-metal.md`

---

## 2026-06-11T10:52:13Z — `REVIEW` — `APPROVE`
On-premises wave 4 batch 3 (#1881, PR #1891). T3→T0 expand-to-floor. Author: cursor auto (1764→5053w, de-fab telecom opener→Hypothetical, canonical outcomes heading, +Patterns/Decision-Framework/Day-2, 14 sources). Reviewer: codex gpt-5.5 (R1, cross-family) NEEDS_CHANGES 2P1+5P2 — ALL ground-checked + web-verified TRUE: P1 CRIU checkpoint claimed Stable-1.32 → still BETA as of 1.35 (KEP-2008); P1 electricity $200-800/kW-yr → ~$1,200-1,900 (EIA ~14c/kWh Feb-2026, dated); KEDA RabbitMQ deprecated bare queueLength → mode+value+host; KEDA 2.19→2.20 (k8s 1.33-1.35); Knative lab v1.14.0→v1.22.1 + net-kourier org move (knative→knative-extensions); scale-to-zero-grace-period semantics; CronJob does-not-hold-memory correction. Orchestrator inline-fixed + re-verified T0/5053w. Build green PRIMARY 2171p. APPROVE.
