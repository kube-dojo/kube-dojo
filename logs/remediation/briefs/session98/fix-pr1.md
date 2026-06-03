CONSOLIDATED FIX — Azure Essentials PR-1 (modules 3.1, 3.4, 3.5).

You are fixing cross-family review findings on already-expanded Azure modules in this
worktree. Apply EVERY fix below. For each pattern, **find and fix ALL occurrences in
the file, not just the listed line(s) — line numbers are approximate and listings are
sampled, not exhaustive.** Do NOT lower body_words below 5000 and keep each module T0
(`scripts/quality/verify_module.py` → passed:true). Preserve all other content.
Edit in place. After all edits, run verify_module.py on each touched file and report
body_words + tier + passed for each. Commit once at the end:
`chore(content): apply cross-family review fixes — Azure 3.1/3.4/3.5 (cloud Azure wave)`.

============================================================================
## module-3.1-entra-id.md
============================================================================
P1 — Lab Task 3 (~L840-852) uses `--auth-mode login` for container-create + blob-upload,
which FAILS for a subscription Owner (Owner/Contributor do NOT grant blob *data* access
via Entra; you'd get AuthorizationPermissionMismatch). FIX: immediately BEFORE Task 3's
container/upload commands, add a data-plane role self-assignment, and a one-line note
explaining WHY (it reinforces the Actions-vs-DataActions lesson the module teaches):
```bash
# Owner/Contributor grant management-plane rights but NOT blob data access — assign a data role.
ME=$(az ad signed-in-user show --query id -o tsv)
az role assignment create --assignee "$ME" --role "Storage Blob Data Contributor" \
  --scope "$STORAGE_ID"
# wait ~30s for the role assignment to propagate before the data-plane ops below
```
Keep the `--auth-mode login` calls (they now succeed). Ensure `$STORAGE_ID` is defined
(capture it when the storage account is created if not already).

P2 — L99: table says "Max ~500 resource groups per sub (soft limit)". WRONG. The ARM
limit is 980. Change to "Max 980 resource groups per sub".

P2 — L781 & L788: prose says the custom role "can only list … but **not read**, write,
or delete" / "cannot read or modify blob content", but its DataActions include
`.../blobs/read` and Task 6 (~L947-951) tests that read SUCCEEDS. Reword BOTH places to
"can list and **read** blobs but cannot **write or delete**".

P2 — L791: remove `Microsoft.Storage/storageAccounts/listkeys/action` from the custom
role's `Actions` (it lets a holder fetch the account key and bypass the data-plane
restriction the lab demonstrates; it is never exercised). The lab still works after removal.

Nits (apply, cheap): L323 use canonical AKS workload-identity URL
`.../azure/aks/workload-identity-overview` (hyphen, no `/overview`); L231 rename the
"War Story" header (no anecdote in it) to "Security note".

============================================================================
## module-3.4-blob.md
============================================================================
P1 — L1017: `az storage fs directory move --new-directory` takes `{filesystem}/{path}`,
NOT a path relative to `--file-system`. As written ("2024/archived-sales") az treats
"2024" as the destination filesystem and the rename fails. FIX:
`--new-directory "analytics-raw/2024/archived-sales"` (prefix the filesystem name).

P2 — L448: SAS permission table maps `x` → "Execute". WRONG (order is `racwdxltmeop`):
`x` = **Delete version**, Execute = `e`. Relabel the row to `| \`x\` | Delete version |`
and add a row `| \`e\` | Execute (ADLS Gen2) |` if the table lists per-letter meanings.

P2 — L552-570: teaching snippet uses `--account-name "$DATALAKE_NAME"` but never assigns
it (the create line uses an inline `kubedojodatalake$(openssl rand -hex 4)`). FIX: first
line `DATALAKE_NAME="kubedojodatalake$(openssl rand -hex 4)"`, then use
`--name "$DATALAKE_NAME"` on create — mirror the working Task 6 pattern (~L993).

P2 — L306: dangling callback to a "financial disaster war story from the introduction"
that doesn't exist (intro is a generic cost warning). Soften to "…the surprise-bill
scenario described in the introduction."

Nits (apply): L672 remove spurious "vNet" → "geo-replication data transfer (egress
between regions)"; L727 tag the worked Hot/Cool prices as "(illustrative)".

============================================================================
## module-3.5-dns.md
============================================================================
P1 — The Azure DNS Private Resolver block uses a NON-EXISTENT command group
`az network dns-resolver` (≈L255,262,269,275,278,281,289). The correct group is the
`az dns-resolver` CLI extension (NO `network` parent). FIX every occurrence — drop
`network`:
  `az network dns-resolver create` → `az dns-resolver create`
  `az network dns-resolver inbound-endpoint …` → `az dns-resolver inbound-endpoint …`
  `… outbound-endpoint create/show` → `az dns-resolver outbound-endpoint …`
  `… forwarding-ruleset create` → `az dns-resolver forwarding-ruleset create`
  `… forwarding-rule create` → `az dns-resolver forwarding-rule create`
  `… vnet-link create` → `az dns-resolver vnet-link create`
Also: `az dns-resolver create` has no `--virtual-network` flag (≈L257) — the VNet is
passed by resource ID via `--id "/subscriptions/<sub>/resourceGroups/<rg>/providers/Microsoft.Network/virtualNetworks/hub-vnet"`.
Same for `vnet-link create --virtual-network spoke1-vnet` (≈L293) → reference the VNet by
resource ID. (Leave the elided `...` subnet-ID placeholders and the delegation comment.)

P1 — Quiz #2 answer (≈L827) is FACTUALLY WRONG: it says "Azure only allows one VNet to
have auto-registration enabled per Private DNS Zone". Backwards. The real constraint is
**per-VNet**: a VNet can enable auto-registration on only ONE zone, but a single zone
accepts auto-registration from MANY VNets. Keep the design recommendation (spokes =
resolution-only) but change the REASON to the correct one: "a VNet can enable
auto-registration on only one zone, and you don't want stateless spoke app-tier VMs
polluting the shared-services zone with ephemeral names." (This must agree with DYK #4
≈L797 and the body ≈L233.)

P2 — L233: tighten the muddled lead clause to "a VNet can have auto-registration enabled
on **only one** private DNS zone; a single zone can accept auto-registration from many
VNets" (keep the existing rationale).

P2 — L412 and Quiz #4 answer (≈L839): "Layer 7 of DNS, technically" is imprecise — DNS
is an application-layer (OSI L7) protocol. Reword both to "Traffic Manager operates at
the DNS / application layer" — do not teach "Layer 7 of DNS".

Nits (apply): standardize mermaid line breaks to `<br/>` (replace literal `\n` at
≈L214,314,585,590-591); add a "verify current pricing" hedge to the Private Resolver
pricing (≈L693) to match the Front Door/TM rows; soften DYK #3 edge counts to "190+ /
100+".
