FIX — Azure Essentials 3.2 vnet (at-floor module, review fixes only — no expansion).

Module: src/content/docs/cloud/azure-essentials/module-3.2-vnet.md (already at floor,
T0 PASS — apply ONLY the review fixes below; do not pad). For each pattern, find and fix
ALL occurrences. Keep T0 (verify_module.py passed:true); do NOT drop below 5000 body_words.
Edit in place. Commit:
`chore(content): apply cross-family review fixes — Azure 3.2-vnet (cloud Azure wave)`.

P1 — ≈L478: the VPN/ExpressRoute SLA table cell says ExpressRoute "99.95% (standard) /
99.99% (premium)". WRONG — ExpressRoute SLA is **99.95%**, full stop; the Premium add-on
does NOT raise the SLA (it extends global reach + route prefixes). FIX the ExpressRoute SLA
cell to `99.95%` (optionally `99.95% (Premium extends global reach, not the SLA)`). The VPN
side (99.9% single / 99.95% active-active) is correct — leave it.

P1 — ≈L561 (DYK #2): "This is more than AWS reserves (which takes only the first 4 and the
last 1)" is FALSE — AWS reserves first 4 + last 1 = **5 IPs**, identical to Azure's 5 (the
sentence even self-contradicts). FIX: "This matches AWS, which also reserves 5 (the first
four addresses and the last); the positions differ slightly, so don't assume an Azure
subnet has more usable space than the same-sized AWS subnet."

P2 — ≈L444-455: the illustrative Azure Firewall application rule mixes `--fqdn-tags
"AzureKubernetesService"` AND `--target-fqdns "*.ubuntu.com" "packages.microsoft.com"` in
one rule — unsupported. FIX: split into two rules — one with `--fqdn-tags
"AzureKubernetesService"` (protocol https), and a separate `allow-os-updates` rule with
`--target-fqdns "*.ubuntu.com" "packages.microsoft.com"` (protocol `Https=443`).

P2 — ≈L875-883: lab Task 6 runs `traceroute` but the Ubuntu2204 image doesn't include it.
FIX: prefix the run-command with `sudo apt-get update -qq && sudo apt-get install -y
traceroute && ...`. (ping at ≈L872 is fine — iputils-ping is preinstalled.)

P2 — ≈L582: the last "Common Mistakes" row (DNS) has only 2 cells in a 3-column
(Mistake | Why It Happens | How to Fix It) table. FIX by splitting Why and How:
Why = "Cross-VNet name resolution isn't automatic — VNets default to Azure-provided DNS
scoped to themselves"; How = "Link a Private DNS Zone to each VNet that must resolve the
names, or run a central DNS resolver in the hub".
