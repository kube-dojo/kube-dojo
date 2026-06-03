CONSOLIDATED FIX — Azure Essentials PR-3 (modules 3.8, 3.9, 3.10).

Apply EVERY fix below. For each pattern, **find and fix ALL occurrences in the file,
not just the listed line(s) — line numbers are approximate and listings are sampled.**
Do NOT lower body_words below 5000; keep each module T0 (verify_module.py passed:true).
Preserve all other content. Edit in place. After edits, run verify_module.py on each
file and report body_words+tier+passed. Commit once:
`chore(content): apply cross-family review fixes — Azure 3.8/3.9/3.10 (cloud Azure wave)`.

============================================================================
## module-3.8-functions.md
============================================================================
P1 — DYK #2 (≈L715): "Durable Functions can run for up to 7 days on the Consumption
plan" is FALSE. There is NO 7-day orchestration cap on any plan — orchestrators
checkpoint to storage and replay, running for arbitrary durations on Consumption too
(only individual ACTIVITY executions are bound by the function timeout: 5 min default /
10 max on Consumption; the nearest real limit is the 6-day durable *timer* for
Python/JS/PowerShell, chainable for longer). It also contradicts the body (≈L469, L531).
FIX: rewrite the DYK to state orchestrations run for days/weeks/months on ANY plan via
checkpoint+replay; the function timeout bounds only a single activity execution.

P1 — Lab Task 5 (≈L1049-1055): `az cosmosdb sql query` is NOT a real command (the
`az cosmosdb sql` group is control-plane only — no `query` subcommand). The verification
can never run. FIX: verify documents via a real path — e.g. the Cosmos DB data-plane
isn't in `az cosmosdb`; use the portal Data Explorer note OR query via the bundled REST
endpoint, OR (simplest for the lab) read items with
`az cosmosdb sql container show`/throughput won't show docs — instead instruct learners
to confirm the two documents in the portal Data Explorer, and make Success Criteria #4/#5
match what the provided commands actually prove. Do NOT leave a dead `cosmosdb sql query`.

P2 — Plan comparison table (≈L38): Flex Consumption "Max execution: 30 min" is wrong →
Default 30 min / Maximum **Unbounded** (no enforced execution timeout; the 230 s ceiling
is only for HTTP-trigger responses). Fix the table cell and any prose that repeats it.

P2 — Premium "Scale to zero: Optional (min 1)" (≈L36, L675) is misleading → Elastic
Premium NEVER scales to zero (keeps ≥1 always-warm instance). Make it consistent with the
cold-start row ("always warm") and cost section ("never scales to zero", ≈L623).

P2 — Premium create example (≈L95-101): `az functionapp plan create` omits `--is-linux
true` (defaults to Windows), but the paired `az functionapp create` passes `--runtime
python` (Linux-only) → deploy fails. Add `--is-linux true` to the plan create (mirror the
Consumption example's `--os-type Linux`).

P2 — "200 instances" Consumption cap (≈L35, L49, L595, L674) is the WINDOWS cap; Linux
Consumption (which Python uses, and the lab deploys Python) is **100**. Change the
relevant ceilings to 100 (note Windows=200 if helpful). KEEP the correct statement that
Linux Consumption is retiring 2028-09-30 / gets no new language versions.

P2 — Anti-fabrication: the War Story (≈L159) and DYK (≈L715 "one retail company … 30
days") are anecdotes stated as fact with no `Hypothetical scenario:` label. Prefix both
with `Hypothetical scenario:` or make them clearly generic.

============================================================================
## module-3.9-key-vault.md
============================================================================
P1 — Lab Task 5 (≈L949, L953-956): the MI-retrieval step uses the VM/VMSS IMDS endpoint
`http://169.254.169.254/...`, which is WRONG for Container Apps. Container Apps exposes
the token endpoint via the `IDENTITY_ENDPOINT` env var with an `X-IDENTITY-HEADER` header
(value from `IDENTITY_HEADER`):
`curl "$IDENTITY_ENDPOINT?resource=https://vault.azure.net&api-version=2019-08-01&client_id=$IDENTITY_CLIENT" -H "X-IDENTITY-HEADER: $IDENTITY_HEADER"`.
Also the `az keyvault secret show` "verification" (≈L953-956) reads with the SIGNED-IN
USER's RBAC, not the MI — so it never proves the MI path. FIX: replace the IMDS curl with
the IDENTITY_ENDPOINT/X-IDENTITY-HEADER pattern (web-verified against
learn.microsoft.com/azure/container-apps/managed-identity), and make the success criterion
(≈L1017) honest about which identity is exercised.

P2 — Throttling arithmetic (≈L629): "200 pods × 50 req/s = 100,000 GETs/second" → 200×50
= **10,000**. Fix to 10,000 (conclusion still holds).
P2 — (≈L635) "$1 per scheduled rotation" is unverified — reframe rotation cost as "you pay
for the new key VERSION each rotation produces" (keep the real "$3 per certificate
renewal" at L633).
P2 — (≈L459) IMDS is NOT "installed via VM extensions" — it's built into every Azure VM.
Reword: "Azure VMs reach MI tokens through the always-present IMDS endpoint; `az vm
identity assign` attaches the identity (no extension required)."
P2 — (≈L65) mermaid features box says HSM = "FIPS 140-2 Level 2" but body (L54/L701)
correctly says Premium reaches FIPS 140-3 Level 3 on HSM Platform 2 (current default).
Update the box to "FIPS 140-2 L2 / 140-3 L3 (HSM Platform 2, current default)".
P2 — (≈L874, and apply to ALL role-assignment-after-create in this file) use
`--assignee-object-id "$PRINCIPAL" --assignee-principal-type ServicePrincipal` to avoid
the Entra replication race.
P2 — (≈L166-178) illustrative encrypt/decrypt: capture the ciphertext
(`CIPHERTEXT=$(az keyvault key encrypt ... -o tsv ...)`) and add `--data-type base64`.

============================================================================
## module-3.10-monitor.md
============================================================================
P1 — `az monitor scheduled-query create` (≈L473-483) is malformed. The `--condition` must
reference a SHORT placeholder name in single quotes, and `--condition-query` binds that
SAME name via `Name="<KQL>"`. FIX to:
  --condition "count 'Failures' > 10 resource id _ResourceId at least 1 violations out of 1 aggregated points" \
  --condition-query Failures="AzureDiagnostics | where Category == 'AuditEvent' | where ResultType == 'Failure'"
(placeholder name `Failures` used in both; current code has no `Name=` prefix and uses the
whole KQL as the placeholder — both wrong).

P2 — Three DEAD citation URLs (opus fetched each, real 404s) — fix:
  - `.../azure-monitor/logs/scoped-configurations` (≈L207) → `.../azure-monitor/logs/manage-access`
  - `.../azure-monitor/platform/policy-reference` (≈L36, L814, L1198, all 3) → `.../azure-monitor/policy-reference` (drop `/platform/`)
  - `.../azure-monitor/metrics/custom-metrics` (≈L182) → `.../azure-monitor/essentials/metrics-custom-overview`
  Do NOT touch `.../platform/diagnostic-settings`, `.../data-collection/data-collection-transformations`,
  `.../metrics/data-platform-metrics` — those are valid.

P2 — NSG flow logs (≈L139, L725, L729) presented as current with no retirement note.
WEB-VERIFIED (learn.microsoft.com nsg-flow-logs-migrate): NSG flow logs retire
**2027-09-30**, and you can **no longer create new ones after 2025-06-30**; successor is
**VNet flow logs**. FIX: name VNet flow logs as the current path and flag NSG flow logs as
on the retirement track (one sentence at L139 + the cost table).

P2 — Lab Task 4 (≈L1047-1053): `stress-ng` is not preinstalled on Ubuntu2204, and `az vm
run-command invoke` returns exit 0 even if the inner script fails, so the alert never
fires. FIX: `sudo apt-get update -qq && sudo apt-get install -y stress-ng && stress-ng ...`
(or run a `yes`-loop as the primary path); don't gate the fallback on run-command exit code.

P2 — Anti-fabrication DYK #4 (≈L828): "A team … reduced 100 GB to 8 GB … with zero loss"
is an unlabeled anecdote and "zero loss" overclaims. FIX: soften to an illustrative range
("often cut 80-90%"), drop "zero loss". KEEP the correct "5 events/sec/server" default.

P2 — (≈L678, L1014) Linux AMA counter `\Memory\Available Bytes` is the WINDOWS name; the
cross-platform counter is `\Memory\Available MBytes Memory`. Swap it (or drop that one
counter).
