CONSOLIDATED FIX — Azure Essentials PR-4 (modules 3.11, 3.12). NOTE: module 3.13 is also
in this branch but is ALREADY fixed (do not touch module-3.13-application-gateway.md).

Apply EVERY fix below. For each pattern, **find and fix ALL occurrences in the file, not
just the listed line(s).** Do NOT lower body_words below 5000; keep each module T0
(verify_module.py passed:true). Preserve all other content. Edit in place. After edits,
run verify_module.py on module-3.11-cicd.md and module-3.12-bicep.md and report
body_words+tier+passed. Commit once:
`chore(content): apply cross-family review fixes — Azure 3.11/3.12 (cloud Azure wave)`.

============================================================================
## module-3.11-cicd.md
============================================================================
P1 — The hands-on lab (≈L991-1019, L1158-1163) never grants the Container App permission
to pull the private ACR image, so the Task 4 deploy fails end-to-end (the troubleshooting
note at ≈L985-987 even references a pull-permission step "configured earlier" that doesn't
exist). FIX (managed-identity path — consistent with the module's own best-practice that
teaches AGAINST admin creds): add to Task 1 (after the Container App is created), computing
ACR_ID here:
```bash
# Give the Container App a system-assigned identity and let it pull from ACR
az containerapp identity assign -g "$RG" -n "$APP_NAME" --system-assigned
APP_MI_PRINCIPAL=$(az containerapp identity show -g "$RG" -n "$APP_NAME" --query principalId -o tsv)
ACR_ID=$(az acr show -n "$ACR_NAME" --query id -o tsv)
az role assignment create --assignee-object-id "$APP_MI_PRINCIPAL" \
  --assignee-principal-type ServicePrincipal --role AcrPull --scope "$ACR_ID"
az containerapp registry set -g "$RG" -n "$APP_NAME" \
  --server "$ACR_NAME.azurecr.io" --identity system
```
This also makes the troubleshooting note at ≈L985-987 accurate.

P2 — Role assignments created right after `az ad sp create` (≈L1040, L1055, L1059, and the
example blocks ≈L183-187, L431-441) use `--assignee <objectId>`, which races Entra
replication (intermittent PrincipalNotFound). Switch ALL of them to
`--assignee-object-id "$SP_OBJECT_ID" --assignee-principal-type ServicePrincipal`.

Nits (apply where quick): standardize `az ad app federated-credential create --id` to use
the object id everywhere (≈L175 uses appId; L407/L1046 use object id); add a one-line
`az containerapp` extension prerequisite note (≈L981).

============================================================================
## module-3.12-bicep.md
============================================================================
P1 — `utcNow()` inside a `var` (≈L1336) is a Bicep COMPILE error (utcNow() is only valid
in a parameter default). This breaks the whole lab (Verify Task 3 `az bicep build` fails,
Tasks 4-6 never run). FIX: promote to a parameter default and reference it:
```bicep
param deployedAt string = utcNow('yyyy-MM-dd')
var tags = { environment: environment, project: baseName, managedBy: 'bicep', deployedAt: deployedAt }
```

P1 — Lab resource names (≈L1359 storage, L1371 web app) use a FIXED `kubedojo` prefix with
no `uniqueString()` → globally-unique-name collisions (StorageAccountAlreadyTaken /
web-app name-in-use), and it contradicts the module's own Common Mistakes guidance (≈L1116
"Use uniqueString() for globally unique names") and body examples (≈L48, L129, L1009). FIX:
add `${uniqueString(resourceGroup().id)}` to the storage name (truncate to ≤24 chars,
e.g. `'${replace(prefix, '-', '')}st${uniqueString(resourceGroup().id)}'`) and the web app
name, mirroring the body examples.

P2 — `az stack group create` (≈L730-734) is missing the REQUIRED `--action-on-unmanage`
(both `--action-on-unmanage/--aou {deleteAll,deleteResources,detachAll}` AND
`--deny-settings-mode` are required). FIX: add `--action-on-unmanage detachAll` (safest for
a teaching example) and optionally `--yes`.

P2 — what-if symbol legend (≈L786-792, L814-820) is inaccurate (`! Ignore` / `* No change`
are not the documented symbols). WEB-VERIFY against learn.microsoft.com bicep deploy-what-if
and correct the legend to the real change-type symbols (Create `+`, Delete `-`, Modify `~`,
Deploy `!`, NoChange `=`, Ignore `*` — but CONFIRM each against the doc before writing).
