Expand the module at: src/content/docs/cloud/azure-essentials/module-3.11-cicd.md

Current body_words ≈ 1402 — needs to reach >= 5000. Also fails `sources_min_10` and
`sentence_length_12_28` (keep mean sentence length in the 12-28 word band; break long
sentences). Follow ALL rules in
logs/remediation/briefs/session98/_shared-expand-rules.md (read it first).

Work inside the worktree you were given; edit the file IN PLACE; commit at the end.

### DEEPEN these core sections (add genuine NEW Azure CI/CD depth). Cover BOTH
GitHub Actions for Azure AND Azure Pipelines (do not add Jenkins):
1. **Secure auth from CI to Azure (the highest-value topic)** — **OIDC / workload
   identity federation** for GitHub Actions (`azure/login` with a federated credential,
   no stored secret) and Azure Pipelines **service connections** (workload-identity
   federation vs service-principal secret). Explain WHY OIDC beats long-lived secrets,
   and least-privilege scoping of the deployment identity.
2. **Pipeline structure & environments** — GitHub Actions (workflows, jobs, reusable
   workflows, environments + required reviewers/approvals) and Azure Pipelines (stages,
   jobs, templates, environments, approvals/checks). Deployment strategies: blue-green,
   canary, ring-based, and **gated promotion** between environments.
3. **Deploying to Azure targets** — concrete flows for App Service, Container Apps,
   AKS (build → push to ACR → deploy manifest/helm), and infra (Bicep/Terraform what-if
   then apply). Artifact handling, environment-specific config, and rollback. Include a
   minimal GitHub Actions YAML using `azure/login` with OIDC.

### COST LENS: GitHub Actions minutes (free tier + per-minute by runner OS) vs
self-hosted runners; Azure DevOps parallel-job (Microsoft-hosted vs self-hosted)
pricing; how matrix builds and chatty triggers inflate minutes.

### ADD (currently missing): Patterns & Anti-Patterns + Decision Framework
(decision matrix: GitHub Actions vs Azure Pipelines; OIDC vs secret; hosted vs
self-hosted runners).

Web-verify every new fact against learn.microsoft.com / docs.github.com. Report final
body_words.
