CONSOLIDATED FIX — Azure Essentials PR-2 (modules 3.3, 3.6, 3.7).

Apply EVERY fix below. For each pattern, **find and fix ALL occurrences in the file,
not just the listed line(s) — line numbers are approximate and listings are sampled,
not exhaustive.** Do NOT lower body_words below 5000 and keep each module T0
(`scripts/quality/verify_module.py` → passed:true). Preserve all other content. Edit in
place. After all edits, run verify_module.py on each touched file and report
body_words + tier + passed. Commit once at the end:
`chore(content): apply cross-family review fixes — Azure 3.3/3.6/3.7 (cloud Azure wave)`.

============================================================================
## module-3.3-vms.md
============================================================================
P1 — Disk Types table (≈L259-265) has WRONG max IOPS/throughput (the columns are labeled
"max"). Correct them to the real per-disk maximums:
  - Premium SSD (P80): `20,000` IOPS / `900` MB/s  (it currently says 7,500 / 250 — and
    250 is even LOWER than the Standard SSD row, which is impossible).
  - Ultra Disk: `400,000` IOPS / `10,000` MB/s  (currently 160,000 / 4,000 — and this
    contradicts the body at ≈L322 which already says 400,000 / 10,000).
  Leave Premium SSD v2 (80,000 / 1,200) and Standard SSD/HDD rows as-is.

P2 — Two HA Mermaid diagrams (≈L144-155 and ≈L161-176) have invalid syntax and won't
render. Fix BOTH:
  - Remove every `note over ...` line (it's sequence-diagram syntax, invalid in a
    `graph`/flowchart) — move the caption text into prose or a node label. Affected
    ≈L153 and ≈L174.
  - Quote node labels that contain parentheses: `FD0 --- VM1(VM-1 (UD0))` →
    `FD0 --- VM1["VM-1 (UD0)"]` (the inner `(UD0)` closes the node early). Affects
    VM1-VM5 (≈L168-172).

P2 — Ultra Disk throughput cost (≈L678) is internally inconsistent by 50×: it says
"~$0.01 per MB/s of throughput per month" then "500 MB/s adds ~$250/month". 500 × $0.01 =
$5, not $250. Fix so rate and total agree — change the total to ~$5/month (keep the IOPS
half: 10,000 × $0.06 = $600, which is consistent). Keep prices illustrative.

P2 — Azure Advisor lookback (≈L72) says "rolling 14-day window"; the DEFAULT is 7 days
(configurable 7/14/21/30/60/90). Change to "rolling 7-day window (configurable up to 90
days)".

P2 — VMSS-definition inline citation (≈L441) points to `/azure/virtual-machines/availability`
(the availability-options page, wrong). Repoint to `/azure/virtual-machine-scale-sets/overview`.

P2 — Hands-On lab (≈L927-1056): the VMSS lab never creates a port-80 load-balancing rule,
so Task 6's `curl http://$LB_IP` has no data path. (a) Add an LB rule before Task 6:
`az network lb rule create -g <rg> --lb-name <lb> -n http --frontend-port 80 --backend-port 80 --protocol Tcp --probe-name <probe> --backend-pool-name <pool>`.
(b) Replace the `probe update` (≈L979-985) — which assumes a probe already exists — with a
`az network lb probe create` (idempotent intent). Make sure `$LB_PROBE`/pool/LB names used
in the rule match what `az vmss create` provisioned (inspect with `az network lb show`).

Nits (apply): L84 drop "or Basic" (Basic-tier A-series VMs retired); L96 reword
"i = Isolated (dedicated host)" → "(isolated to dedicated hardware)" (NOT Azure Dedicated
Host); L102 prefer `az vm list-skus` over soft-deprecated `az vm list-sizes`; L682 P20 is
~4× P10 not 5×.

============================================================================
## module-3.6-acr.md
============================================================================
P1 — Docker Content Trust (DCT) is DEPRECATED and can no longer be ENABLED — the module
teaches it as a current best practice. WEB-VERIFIED (learn.microsoft.com
container-registry-content-trust-deprecation): DCT deprecation started 2025-03-31, DCT is
fully removed 2028-03-31, and Microsoft's replacement is the **Notary Project**
(`notation` CLI) + **Azure Key Vault**. Affected ≈L46 (SKU table), L84, L203, L472, L592
(anti-pattern remediation), L606 (decision matrix). FIX: add a deprecation note wherever
content trust appears; pivot the supply-chain-signing recommendation to Notary Project +
AKV (notation sign/verify; verify on AKS via Ratify + Azure Policy). The anti-pattern
remediation (L592) and decision-matrix row (L606) MUST point to Notary/notation, not DCT.
Relabel the SKU-table "Content Trust" row (L46) to "Image signing (Notary Project)".

P1 — FALSE claim (≈L182-188) that "Microsoft Entra managed identities cannot receive
repository-scoped ABAC today". WEB-VERIFIED (learn.microsoft.com
container-registry-rbac-abac-repository-permissions + Nov-2025 GA): ACR repository
permissions with Entra ABAC are **GA**. A registry set to the "RBAC Registry + ABAC
Repository Permissions" mode supports ABAC-enabled built-in roles **Container Registry
Repository Reader / Writer / Contributor**, and ABAC conditions **CAN** be assigned to
managed identities — including AKS kubelet/workload identities, ACA, and ACI. (Also: on an
ABAC-enabled registry, broad roles Owner/Contributor/Reader grant CONTROL-plane only, no
data-plane pull/push.) FIX L188: state that Entra managed identities CAN now receive
repository-scoped permissions via ABAC (GA Nov 2025) using the ABAC built-in roles; keep
tokens/scope-maps as the path for NON-Entra consumers (IoT, partners); mention the
per-registry role-assignment-mode toggle.

P2 — `az acr build --platform linux/amd64,linux/arm64` (≈L266-271) does NOT build a
multi-arch image (`--platform` takes a single OS/arch). Replace with
`docker buildx build --platform linux/amd64,linux/arm64 --tag <login-server>/myapp:v1.0.0 --push .`
(or relabel and drop the multi-arch claim).

P2 — `az acr repository show-manifests` is deprecated (≈L235 and the runnable lab Task 4
≈L839). Switch both to `az acr manifest list-metadata --name <repo> --registry <acr>
--detail`, with a one-line note that it lists only TAGGED manifests (fine for Task 4).

P2 — Anti-fabrication: the "Why This Module Matters" opener (≈L22-24) is an UNLABELED
hypothetical presented as a real anecdote ("they … learned the hard way"). Prefix with
`Hypothetical scenario:` and give it a generic subject. KEEP the cited real Docker Hub
pull-limit numbers (100/6h anon, 200/6h authenticated) — only the framing is the problem.

Nits (apply): L399 strip `?view=azureml-api-2` from the Private Link citation URL; L397
rename "Azure Active Directory" → "Microsoft Entra ID"; L54 trim `?source=recommendations`.

============================================================================
## module-3.7-aci-aca.md
============================================================================
P1 — Hands-On lab Task 5 (≈L840-844) uses `az storage queue show`, which does NOT exist.
The approximate message count comes from `metadata show`. FIX:
`az storage queue metadata show --name "work-items" --account-name "$STORAGE_NAME" --connection-string "$STORAGE_CONN" --query approximateMessageCount -o tsv`.

P2 — ACI worked example vCPU-seconds (≈L258) is off by 2×: a 2-vCPU group for 30 days is
2 × 2,592,000 ≈ **5.18 million** vCPU-seconds, not 2.59M (2.59M is the 1-vCPU value). The
memory figure (10.4M GB-s) is correct. Change "2.59 million vCPU-seconds" → "≈5.18 million
vCPU-seconds".

P2 — Container Apps revision split (≈L335-381): the initial `az containerapp create`
(`web-api`, ≈L335) has no `--revision-suffix`, so its revision is auto-named `web-api--<hash>`,
but the traffic split (≈L381) references `web-api--v1` which never exists → the split
command fails. FIX: add `--revision-suffix v1` to the initial create so `web-api--v1` exists.

P2 — Dapr component example (≈L491-505) uses `az containerapp env dapr-component set --yaml
'{ ... }'`, but `--yaml` expects a FILE PATH, not an inline string. FIX: show the component
as a standalone `pubsub.yaml` file, then `--yaml pubsub.yaml` (and remove the trailing comma
after the metadata entry). Or move the inline block to a ```yaml fence and drop the `az
--yaml '{...}'` framing.

Nits (apply where quick): L663 Quiz Q4 — in MULTIPLE revision mode, weighting v1 to 0 does
NOT auto-deactivate it (only single-revision mode does); reword to "v1 stops receiving new
requests; deactivate/scale it down once drained". L675 soften "5-10 second cold start" to
"a brief cold start (seconds, depending on image size)".
