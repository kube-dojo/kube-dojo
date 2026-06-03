# Cross-family review — finalize-to-done (back-catalog, CLOUD/Azure track)

Review the module at: __MODULE_PATH__

This is a back-catalog Azure module being expanded to the 5000-word floor
and reviewed so it can be finalized to `done`. Do a rigorous cross-family R1 review
focused on what the automated verifier CANNOT catch:
- **Azure service-fact correctness (verifier-blind, highest priority)**: SKU/tier
  names and boundaries, Entra ID / managed identity / RBAC semantics, networking
  (VNet, NSG, private endpoint, Application Gateway) mechanics, storage redundancy
  (LRS/ZRS/GRS/GZRS) and access tiers, disk IOPS/throughput limits, failover/HA
  semantics, default values, quotas, `az` flags and API names. These are the
  failure class for cloud content — check them hard.
- **`az` CLI correctness**: `az role assignment create --assignee ... --role ...
  --scope ...`; `az group create` precedes resources; `az identity create` for
  user-assigned MI; flags that actually exist.
- **Version / currency**: anything stated as current Azure behavior that has changed
  (Hyperscale/Serverless billing, redundancy SKU availability, GA vs Preview status
  of a feature, retired SKUs).
- **Runnability**: every runnable `az`/`kubectl`/bash block — correct flags, correct
  resource references, correct order, cleanup completeness.
- **Anti-fabrication**: incidents/anecdotes stated as fact without a citation or a
  `Hypothetical scenario:` label; invented numeric quotas/IOPS/pricing.
- **Citation accuracy**: does each linked learn.microsoft.com source actually support
  the claim; >=10 reachable sources.
- **Pedagogy/structure/density**: 7-dimension rubric; outcomes testable; DYK=4;
  common-mistakes 6-8; quiz 6-8 scenario-weighted with `<details>`; Patterns &
  Anti-Patterns + Decision Framework present.

Output a verdict (APPROVE or NEEDS_CHANGES) with priority-ranked findings
(P1 blocker / P2 / nit), each with a file:line reference and a concrete fix. Score /5.
Output the review report ONLY — do not edit the file.

## GROUND-CHECK — do NOT raise these known FALSE POSITIVES:
1. Within-section sibling links `../module-X-name/` are CORRECT for this slug layout
   (a module page resolves `..` to its own section dir). Only a CROSS-section link
   `../othersection/` from a module page is wrong (needs `../../`). Flag THAT only.
2. Hedged illustrative prices ("~$0.02/GB-month", "representative East US price",
   "verify current pricing") are intentional teaching values — do NOT flag them as
   "outdated/wrong". Only flag a price stated as a hard current fact that is materially
   wrong, or a wrong free-vs-billed claim.
3. learn.microsoft.com URLs sometimes fail an automated reachability probe due to CI
   network blocks — do NOT report a real Azure doc URL as dead unless it is a genuine
   404 / wrong-page.
4. Before calling a code block "won't run", check whether it is ILLUSTRATIVE
   (a `text`/`json`/`yaml` display fence) vs a runnable lab step. Flag only genuinely
   runnable blocks that fail.
5. "Kubernetes 1.35" is the project's current standard version — never flag as
   future/invalid.
6. Your training cutoff may PRE-DATE real recent Azure GA promotions — do NOT delete
   a feature as "doesn't exist" without checking; flag it as "verify" instead.
