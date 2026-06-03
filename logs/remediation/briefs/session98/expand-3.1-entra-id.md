Expand the module at: src/content/docs/cloud/azure-essentials/module-3.1-entra-id.md

Current body_words ≈ 2374 — needs to reach >= 5000. Follow ALL rules in
logs/remediation/briefs/session98/_shared-expand-rules.md (read it first).

Work inside the worktree you were given; edit the file IN PLACE; commit at the end.

### DEEPEN these core sections (add genuine NEW Entra ID depth, WHY before HOW):
1. **Identities & RBAC** — deepen the distinction between Entra ID roles (directory
   roles like Global Admin, User Admin) vs Azure RBAC roles (subscription/resource
   scope). Explain role assignment scope hierarchy (management group → subscription →
   resource group → resource), built-in vs custom roles, and the `az role assignment
   create --assignee --role --scope` mechanics. Cover deny assignments and the
   least-privilege model.
2. **Managed identities & workload identity federation** — system-assigned vs
   user-assigned managed identities (lifecycle, reuse, when to pick which), how a
   managed identity gets an Entra token with no secret, and **Workload Identity
   Federation** for AKS / GitHub Actions / external workloads (federated credential,
   OIDC issuer, no client secret). This is the operator-critical security topic.
3. **Conditional Access & governance** — Conditional Access policy anatomy
   (signals → conditions → grant/session controls), MFA, named locations, and the
   governance tools: Privileged Identity Management (PIM, eligible vs active roles,
   just-in-time activation), Access Reviews, and Entra ID licensing tiers (Free /
   P1 / P2) and which features need which (PIM and risk-based CA need P2).

### COST LENS: Entra ID P1/P2 per-user licensing, what's free vs licensed, how MFA
and Conditional Access and PIM map to license tiers; cost of over-licensing.

### ADD (currently missing): Patterns & Anti-Patterns + Decision Framework
(decision matrix: when to use a service-assigned vs user-assigned MI vs workload
identity federation vs service principal with secret).

Web-verify every new fact against learn.microsoft.com. Report final body_words.
