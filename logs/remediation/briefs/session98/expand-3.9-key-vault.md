Expand the module at: src/content/docs/cloud/azure-essentials/module-3.9-key-vault.md

Current body_words ≈ 1230 — needs to reach >= 5000. Follow ALL rules in
logs/remediation/briefs/session98/_shared-expand-rules.md (read it first).

Work inside the worktree you were given; edit the file IN PLACE; commit at the end.

### DEEPEN these core sections (add genuine NEW Azure Key Vault depth):
1. **Object types & operations** — secrets, keys (RSA/EC, software vs HSM-backed),
   and certificates (issuance, auto-rotation, integration with CAs). Versioning,
   enable/disable, expiry/activation dates, and the difference between Key Vault
   (Standard/Premium) and **Managed HSM** (single-tenant FIPS 140-2 Level 3, when you
   actually need it).
2. **Access control & data protection** — the two authorization models: legacy
   **vault access policies** vs **Azure RBAC** (the recommended model; data-plane
   roles like Key Vault Secrets User/Officer), and why mixing them is an anti-pattern.
   **Soft-delete + purge protection** (retention window, the irreversibility of purge
   protection), network restrictions (private endpoint / firewall / trusted services),
   and the per-vault transaction throttling limits.
3. **Workload integration** — how apps/AKS consume secrets WITHOUT embedding them:
   managed identity + SDK, the **Secrets Store CSI driver** with the Azure Key Vault
   provider (mounting secrets as files, sync to K8s Secret), and rotation. Contrast
   with hardcoded connection strings (the thing this module prevents).

### COST LENS: per-operation (transaction) pricing for Standard vs Premium, HSM-key
premium, certificate-operation cost, Managed HSM per-hour pool cost; how a hot path
that fetches a secret per request (instead of caching) drives transaction cost.

### ADD (currently missing): Patterns & Anti-Patterns + Decision Framework
(decision matrix: vault access policy vs RBAC; Standard vs Premium vs Managed HSM;
CSI driver vs SDK fetch).

Web-verify every new fact against learn.microsoft.com. Report final body_words.
