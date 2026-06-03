Expand the module at: src/content/docs/cloud/azure-essentials/module-3.7-aci-aca.md

Current body_words ≈ 637 (the THINNEST in the track) — needs to reach >= 5000.
Also fails `sources_min_10`, `density_mean_wpp_30`, `density_short_rate_20pct`.
This module needs the most new teaching content — write full deep paragraphs, not
bullet fragments. Follow ALL rules in
logs/remediation/briefs/session98/_shared-expand-rules.md (read it first).

Work inside the worktree you were given; edit the file IN PLACE; commit at the end.

### DEEPEN / BUILD OUT these core sections (genuine NEW depth, WHY before HOW):
1. **Azure Container Instances (ACI)** — the serverless single-container/-container-
   group primitive: container groups (multi-container, shared lifecycle/network/
   storage), per-second billing, restart policies, the lack of autoscaling/L7
   routing (why ACI is for burst/jobs/sidecars, NOT a web platform), virtual-node /
   ACI-backed AKS burst, confidential containers, and Azure Files volume mounts.
2. **Azure Container Apps (ACA)** — the managed serverless container platform on
   Kubernetes+KEDA+Dapr+Envoy (without exposing the cluster): **revisions** (single
   vs multiple, traffic splitting / blue-green / canary), **KEDA-based autoscaling**
   (HTTP concurrency, queue length, scale-to-zero), **Dapr** integration (pub/sub,
   state, service invocation), ingress (external/internal, custom domains), and the
   Consumption vs Dedicated workload profiles.
3. **Choosing ACI vs ACA vs AKS** — make the boundary crisp: ACI for short-lived
   tasks/CI agents/burst; ACA for event-driven microservices and HTTP apps that want
   scale-to-zero without cluster ops; AKS when you need full Kubernetes control,
   custom operators, or node-level access. Map each to operational burden.

### COST LENS: ACI per-second vCPU+memory billing (and the GB-s/vCPU-s model); ACA
Consumption (active + idle pricing, the free monthly grant, scale-to-zero savings)
vs Dedicated plan; how always-on min-replicas defeats scale-to-zero savings.

### ADD (currently missing): Patterns & Anti-Patterns + Decision Framework
(decision flowchart: task vs event-driven service vs full-control → ACI / ACA / AKS).

Web-verify every new fact against learn.microsoft.com. Report final body_words.
