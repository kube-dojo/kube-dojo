Expand the module at: src/content/docs/cloud/azure-essentials/module-3.8-functions.md

Current body_words ≈ 1630 — needs to reach >= 5000. Also fails `sources_min_10`.
Follow ALL rules in logs/remediation/briefs/session98/_shared-expand-rules.md.

Work inside the worktree you were given; edit the file IN PLACE; commit at the end.

### DEEPEN these core sections (add genuine NEW Azure Functions depth):
1. **Triggers & bindings** — the trigger/binding programming model (one trigger,
   N input/output bindings; declarative vs imperative), the common triggers (HTTP,
   Timer, Queue/Service Bus, Blob, Event Hub, Event Grid, Cosmos DB change feed),
   and how bindings remove boilerplate. Cover the isolated-worker vs in-process model
   and supported languages.
2. **Hosting plans & scale** — Consumption (event-driven scale, scale-to-zero, cold
   start), Flex Consumption (the newer per-instance-concurrency + always-ready model),
   Premium (pre-warmed instances, VNet integration, no cold start), and Dedicated/ASP.
   Explain the scale controller, the 200-instance ceiling, and **cold start** causes
   and mitigations. Map each plan to a workload.
3. **Durable Functions & reliability** — orchestrator/activity/entity functions, the
   patterns (function chaining, fan-out/fan-in, async HTTP, human interaction,
   monitor), checkpoint/replay semantics, and idempotency requirements. Retry policies
   and dead-lettering for queue/Service Bus triggers.

### COST LENS: Consumption GB-s + execution-count billing (and the free monthly grant)
vs Premium per-instance hourly (always-ready units) vs Dedicated; why a chatty
Timer/Blob trigger or always-ready Premium instances inflate cost; cold-start vs cost
tradeoff.

### ADD (currently missing): Patterns & Anti-Patterns + Decision Framework
(decision matrix: Consumption vs Flex vs Premium vs Dedicated by cold-start tolerance,
VNet need, scale shape; Functions vs Container Apps vs Logic Apps).

Web-verify every new fact against learn.microsoft.com. Report final body_words.
