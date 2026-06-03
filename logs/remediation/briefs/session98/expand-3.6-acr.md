Expand the module at: src/content/docs/cloud/azure-essentials/module-3.6-acr.md

Current body_words ≈ 1619 — needs to reach >= 5000. Also fails `sources_min_10`
(needs >= 10 reachable learn.microsoft.com sources). Follow ALL rules in
logs/remediation/briefs/session98/_shared-expand-rules.md (read it first).

Work inside the worktree you were given; edit the file IN PLACE; commit at the end.

### DEEPEN these core sections (add genuine NEW Azure Container Registry depth):
1. **Service tiers & features** — Basic / Standard / Premium SKUs and what each
   gates: included storage, throughput/ReadOps/WriteOps, **geo-replication**
   (Premium-only, how it serves regional pulls and the single-registry-multi-region
   model), availability zones, and private endpoints. Explain when a team is forced
   up to Premium.
2. **Security & access** — Entra ID RBAC roles (AcrPull/AcrPush/AcrDelete) vs the
   admin account (avoid), **repository-scoped tokens + scope maps**, content trust /
   image signing, **Microsoft Defender for Containers** vulnerability scanning, and
   how AKS authenticates to ACR (kubelet managed identity / `az aks update
   --attach-acr`, NOT image-pull secrets). Anonymous pull and its risks.
3. **Build & lifecycle automation** — **ACR Tasks** (quick tasks, multi-step tasks,
   base-image-update triggers, automatic OS/framework patching), the import command
   (`az acr import`) for promoting images across registries, and **retention /
   purge policies** to control untagged-manifest sprawl.

### COST LENS: per-tier daily/registry cost + storage overage + geo-replication
(per-replica) cost + ACR Tasks build-minute cost; how untagged manifests silently
grow storage cost and how retention policies cap it.

### ADD (currently missing): Patterns & Anti-Patterns + Decision Framework
(decision matrix: Basic vs Standard vs Premium by geo + scale + security needs;
managed-identity attach vs pull secret).

Web-verify every new fact against learn.microsoft.com. Report final body_words.
