Expand the module at: src/content/docs/cloud/azure-essentials/module-3.12-bicep.md

Current body_words ≈ 1906 — needs to reach >= 5000. Also fails `sentence_length_12_28`
(keep mean sentence length in the 12-28 word band; break long sentences). Follow ALL
rules in logs/remediation/briefs/session98/_shared-expand-rules.md (read it first).

Work inside the worktree you were given; edit the file IN PLACE; commit at the end.

### DEEPEN these core sections (add genuine NEW Bicep depth, WHY before HOW):
1. **Language & authoring model** — Bicep as a transparent abstraction over ARM JSON
   (transpilation, 1:1 resource mapping), the file anatomy (params, vars, resources,
   modules, outputs), **resource dependencies** (implicit via symbolic reference vs
   explicit `dependsOn`), loops (`for`), conditions (`if`), and existing-resource
   references. Show a small but real module example.
2. **Deployment scopes & modularity** — the four scopes (resourceGroup, subscription,
   managementGroup, tenant) and what each can deploy, **modules** (local + registry
   modules, the public/private Bicep registry), and **deployment stacks** for managing
   a resource lifecycle as a unit (deny-settings, what gets cleaned up on delete).
3. **Safe deployment practices** — `az deployment group what-if` (preview changes
   before apply, the change types), incremental vs complete mode (and the danger of
   complete mode deleting unlisted resources), linting/validation, and CI integration.

### COST LENS: Bicep/ARM deployments themselves are free — frame the cost lens as
"IaC prevents cost surprises": what-if catches accidental SKU bumps, complete-mode
mistakes that delete-and-recreate, and tagging-for-cost-allocation enforced in code.

### ADD (currently missing): Patterns & Anti-Patterns + Decision Framework
(decision matrix: Bicep vs ARM JSON vs Terraform; incremental vs complete mode;
module registry vs local modules).

Web-verify every new fact against learn.microsoft.com. Report final body_words.
