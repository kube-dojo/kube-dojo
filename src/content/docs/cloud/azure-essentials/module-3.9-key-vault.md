---
title: "Module 3.9: Azure Key Vault"
slug: cloud/azure-essentials/module-3.9-key-vault
sidebar:
  order: 10
---
**Complexity**: [MEDIUM] | **Time to Complete**: 1.5h | **Prerequisites**: Module 3.1 (Entra ID & RBAC)

## Why This Module Matters

In December 2022, a widely-used password management company disclosed a major breach. Attackers had stolen encrypted vault data and the encryption keys needed to decrypt it. The root cause was traced back to a developer's home computer that had an old, vulnerable version of a media player installed. The attacker exploited the vulnerability, captured the developer's master credentials, and used them to access the company's cloud storage containing encrypted customer data. The breach affected 25 million users and resulted in an estimated $100 million in damages.

This incident drives home a fundamental point: **secrets management is not optional, and it is not a problem you solve with environment variables.** Every application has secrets---database passwords, API keys, encryption keys, TLS certificates. How you store and access these secrets determines whether a single compromised developer laptop leads to a minor inconvenience or a company-ending breach.

Azure Key Vault is a cloud service for securely storing and managing secrets, encryption keys, and certificates. It is backed by FIPS 140-2 Level 2 validated hardware security modules (HSMs), and integrates natively with virtually every Azure service. In this module, you will learn the three object types Key Vault manages, the two access control models (Access Policies vs RBAC), how soft delete and purge protection safeguard against accidental deletion, and how to integrate Key Vault with your applications using Managed Identities. By the end, you will store a database connection string in Key Vault and retrieve it from a Container App without any credentials in your code.

---

## Key Vault Fundamentals

### The Three Object Types

Key Vault manages three distinct categories of cryptographic and sensitive material:

| Object Type | What It Stores | Use Cases | API Endpoint |
| :--- | :--- | :--- | :--- |
| **Secrets** | Any string up to 25 KB | DB passwords, API keys, connection strings, config values | `https://myvault.vault.azure.net/secrets/` |
| **Keys** | RSA or EC cryptographic keys | Data encryption, signing, wrapping other keys | `https://myvault.vault.azure.net/keys/` |
| **Certificates** | X.509 certificates + private keys | TLS/SSL for web apps, code signing, mTLS | `https://myvault.vault.azure.net/certificates/` |

```text
    ┌──────────────────────────────────────────────────────────┐
    │                  Azure Key Vault                         │
    │                  "myvault"                               │
    │                                                         │
    │  ┌─────────────────┐  ┌────────────────┐  ┌───────────┐│
    │  │    Secrets       │  │     Keys        │  │   Certs    ││
    │  │                 │  │                │  │           ││
    │  │ db-password     │  │ data-encrypt   │  │ api-tls   ││
    │  │ api-key-stripe  │  │ signing-key    │  │ mtls-cert ││
    │  │ cosmos-conn-str │  │ wrapping-key   │  │ code-sign ││
    │  │ redis-password  │  │                │  │           ││
    │  └─────────────────┘  └────────────────┘  └───────────┘│
    │                                                         │
    │  Features:                                              │
    │  - HSM-backed (FIPS 140-2 Level 2)                     │
    │  - Versioned (every update creates new version)         │
    │  - Audit logged (every access is recorded)              │
    │  - Soft delete + purge protection                      │
    │  - Private endpoint support                            │
    └──────────────────────────────────────────────────────────┘
```

```bash
# Create a Key Vault
az keyvault create \
  --resource-group myRG \
  --name kubedojo-vault \
  --location eastus2 \
  --sku standard \
  --retention-days 90 \
  --enable-purge-protection true \
  --enable-rbac-authorization true

# Store a secret
az keyvault secret set \
  --vault-name kubedojo-vault \
  --name "db-password" \
  --value "SuperSecretP@ss123!"

# Retrieve a secret
az keyvault secret show \
  --vault-name kubedojo-vault \
  --name "db-password" \
  --query value -o tsv

# Store a multi-line secret (like a connection string)
az keyvault secret set \
  --vault-name kubedojo-vault \
  --name "cosmos-connection" \
  --value "AccountEndpoint=https://mydb.documents.azure.com:443/;AccountKey=abc123..."

# List all secrets (names only, not values)
az keyvault secret list \
  --vault-name kubedojo-vault \
  --query '[].{Name:name, Enabled:attributes.enabled, Created:attributes.created}' -o table
```

### Secret Versioning

Every time you update a secret, Key Vault creates a new version. The "current" version is always the latest, but you can access any previous version by its version identifier.

```bash
# Update a secret (creates a new version)
az keyvault secret set \
  --vault-name kubedojo-vault \
  --name "db-password" \
  --value "NewRotatedP@ss456!"

# List all versions of a secret
az keyvault secret list-versions \
  --vault-name kubedojo-vault \
  --name "db-password" \
  --query '[].{Version:id, Created:attributes.created, Enabled:attributes.enabled}' -o table

# Get a specific version
az keyvault secret show \
  --vault-name kubedojo-vault \
  --name "db-password" \
  --version "abc123def456..."
```

### Keys: Encryption Without Exposing Key Material

Key Vault keys are special: the key material never leaves the HSM. When you need to encrypt data, you send the data to Key Vault, and it returns the ciphertext. You never see the raw key.

```bash
# Create an RSA key
az keyvault key create \
  --vault-name kubedojo-vault \
  --name "data-encryption-key" \
  --kty RSA \
  --size 2048

# Encrypt data (the key never leaves Key Vault)
echo -n "sensitive data" | base64 > /tmp/plaintext.b64
az keyvault key encrypt \
  --vault-name kubedojo-vault \
  --name "data-encryption-key" \
  --algorithm RSA-OAEP \
  --value "$(cat /tmp/plaintext.b64)"

# Decrypt data
az keyvault key decrypt \
  --vault-name kubedojo-vault \
  --name "data-encryption-key" \
  --algorithm RSA-OAEP \
  --value "$CIPHERTEXT"
```

### Certificates: Automated TLS Management

Key Vault can issue certificates from integrated Certificate Authorities (DigiCert, GlobalSign) or manage self-signed certificates. It handles renewal automatically.

```bash
# Create a self-signed certificate
az keyvault certificate create \
  --vault-name kubedojo-vault \
  --name "api-tls-cert" \
  --policy "$(az keyvault certificate get-default-policy)"

# Import an existing PFX certificate
az keyvault certificate import \
  --vault-name kubedojo-vault \
  --name "imported-cert" \
  --file mycert.pfx \
  --password "pfx-password"

# Download the certificate (public portion)
az keyvault certificate download \
  --vault-name kubedojo-vault \
  --name "api-tls-cert" \
  --file /tmp/api-cert.pem \
  --encoding PEM
```

---

## Access Control: Access Policies vs Azure RBAC

Key Vault supports two access control models. You must choose one at creation time (though you can switch later).

### Access Policies (Legacy)

Access Policies are vault-level permissions granted to specific identities. Each policy specifies what operations (get, set, delete, list, etc.) an identity can perform on secrets, keys, and certificates.

```bash
# Create a vault with access policies (not recommended for new vaults)
az keyvault create \
  --name old-style-vault \
  --resource-group myRG \
  --enable-rbac-authorization false

# Grant a user access to secrets
az keyvault set-policy \
  --name old-style-vault \
  --upn "alice@company.com" \
  --secret-permissions get list set

# Grant a managed identity access to keys
az keyvault set-policy \
  --name old-style-vault \
  --object-id "$MANAGED_IDENTITY_PRINCIPAL_ID" \
  --key-permissions get unwrapKey wrapKey
```

### Azure RBAC (Recommended)

RBAC uses the standard Azure role assignment model with fine-grained built-in roles:

| Role | Scope | Permissions |
| :--- | :--- | :--- |
| **Key Vault Administrator** | Vault | Full management of all objects |
| **Key Vault Secrets Officer** | Vault or secret | Manage secrets (set, delete, rotate) |
| **Key Vault Secrets User** | Vault or secret | Read secrets only |
| **Key Vault Crypto Officer** | Vault or key | Manage keys (create, delete, sign, encrypt) |
| **Key Vault Crypto User** | Vault or key | Use keys (sign, encrypt) but not manage |
| **Key Vault Certificates Officer** | Vault or cert | Manage certificates |
| **Key Vault Reader** | Vault | Read metadata (not secret values) |

```bash
# Create a vault with RBAC (recommended)
az keyvault create \
  --name kubedojo-vault \
  --resource-group myRG \
  --enable-rbac-authorization true

# Grant read-only access to secrets for a managed identity
VAULT_ID=$(az keyvault show -n kubedojo-vault --query id -o tsv)
az role assignment create \
  --assignee "$MANAGED_IDENTITY_PRINCIPAL_ID" \
  --role "Key Vault Secrets User" \
  --scope "$VAULT_ID"

# Grant secret management access to a specific secret
az role assignment create \
  --assignee "alice@company.com" \
  --role "Key Vault Secrets Officer" \
  --scope "$VAULT_ID/secrets/db-password"
```

```text
    Access Policies vs RBAC:

    Access Policies (legacy):
    ┌────────────────────────────────────┐
    │ Vault: kubedojo-vault              │
    │                                    │
    │ Policy 1: alice@company.com        │
    │   Secrets: get, list, set          │
    │   Keys: (none)                     │
    │   Certs: (none)                    │
    │                                    │
    │ Policy 2: app-managed-identity     │
    │   Secrets: get                     │
    │   Keys: get, wrapKey, unwrapKey    │
    │   Certs: (none)                    │
    │                                    │
    │ Limitation: Cannot scope to        │
    │ individual secrets/keys            │
    └────────────────────────────────────┘

    RBAC (recommended):
    ┌────────────────────────────────────┐
    │ Vault: kubedojo-vault              │
    │                                    │
    │ alice@company.com                  │
    │   Role: Key Vault Secrets Officer  │
    │   Scope: /secrets/db-password      │  ← Per-secret scope!
    │                                    │
    │ app-managed-identity               │
    │   Role: Key Vault Secrets User     │
    │   Scope: / (entire vault)          │
    │                                    │
    │ Advantage: Standard Azure RBAC,    │
    │ Conditional Access, PIM support    │
    └────────────────────────────────────┘
```

**War Story**: A company using Access Policies had 150 identities with vault-level secret access. When an audit asked "who can read the production database password specifically?", the answer was "all 150 identities." They could not scope Access Policies to individual secrets. After migrating to RBAC, they granted `Key Vault Secrets User` at the individual secret scope, reducing the blast radius of each identity to only the secrets it needed.

---

## Soft Delete and Purge Protection

Key Vault has two safety nets against accidental or malicious deletion:

**Soft Delete**: When you delete a secret, key, or certificate, it is not immediately destroyed. Instead, it enters a "soft-deleted" state and can be recovered during the retention period (7-90 days). Soft delete is mandatory for all vaults created after 2020.

**Purge Protection**: When enabled, even a soft-deleted object cannot be permanently destroyed (purged) until the retention period expires. Not even the vault owner or a Global Administrator can purge it early. This protects against a compromised admin account deliberately destroying secrets.

```bash
# Delete a secret (soft delete)
az keyvault secret delete --vault-name kubedojo-vault --name "db-password"

# List soft-deleted secrets
az keyvault secret list-deleted --vault-name kubedojo-vault \
  --query '[].{Name:name, DeletedDate:deletedDate, ScheduledPurge:scheduledPurgeDate}' -o table

# Recover a soft-deleted secret
az keyvault secret recover --vault-name kubedojo-vault --name "db-password"

# With purge protection disabled, you COULD permanently purge:
# az keyvault secret purge --vault-name kubedojo-vault --name "db-password"
# With purge protection enabled, this command fails until retention expires.
```

```text
    Secret Lifecycle with Soft Delete + Purge Protection:

    Active ──► Deleted (soft) ──► Purged (permanent)
                    │                    ▲
                    │                    │ (only after retention
                    │                    │  period expires)
                    ▼                    │
                 Recovered ──────────────┘
                 (back to Active)

    With purge protection: No shortcut to Purged state.
    Must wait for retention period (7-90 days) to expire.
```

---

## Integrating Key Vault with Applications

### Pattern 1: Direct SDK Access (Application Code)

```python
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

# No credentials in code! DefaultAzureCredential uses Managed Identity.
credential = DefaultAzureCredential()
client = SecretClient(vault_url="https://kubedojo-vault.vault.azure.net/", credential=credential)

# Get a secret
db_password = client.get_secret("db-password")
print(f"Connected to DB with password: {db_password.value[:3]}***")

# Set a secret
client.set_secret("api-key-new", "my-new-api-key")

# List secrets (metadata only, not values)
for secret in client.list_properties_of_secrets():
    print(f"Secret: {secret.name}, Enabled: {secret.enabled}")
```

### Pattern 2: Key Vault References in App Configuration

Azure App Service, Functions, and Container Apps can reference Key Vault secrets directly in application settings, without any SDK code:

```bash
# Set a Key Vault reference in a Function App
az functionapp config appsettings set \
  --resource-group myRG \
  --name my-function-app \
  --settings "DB_PASSWORD=@Microsoft.KeyVault(SecretUri=https://kubedojo-vault.vault.azure.net/secrets/db-password/)"

# The application reads DB_PASSWORD as a normal environment variable.
# Azure resolves the Key Vault reference automatically.
```

### Pattern 3: Container Apps with Key Vault

```bash
# Create a Container App that reads secrets from Key Vault via Managed Identity
az containerapp create \
  --resource-group myRG \
  --name my-app \
  --environment my-env \
  --image myregistry.azurecr.io/app:v1 \
  --secrets "db-pass=keyvaultref:https://kubedojo-vault.vault.azure.net/secrets/db-password,identityref:/subscriptions/.../userAssignedIdentities/my-identity" \
  --env-vars "DB_PASSWORD=secretref:db-pass"
```

### Pattern 4: Kubernetes Integration (CSI Driver)

For AKS, the Azure Key Vault Provider for Secrets Store CSI Driver mounts secrets as files in the pod:

```yaml
# SecretProviderClass for AKS
apiVersion: secrets-store.csi.x-k8s.io/v1
kind: SecretProviderClass
metadata:
  name: kv-secrets
spec:
  provider: azure
  parameters:
    usePodIdentity: "false"
    useVMManagedIdentity: "true"
    userAssignedIdentityID: "<managed-identity-client-id>"
    keyvaultName: "kubedojo-vault"
    objects: |
      array:
        - |
          objectName: db-password
          objectType: secret
        - |
          objectName: api-key-stripe
          objectType: secret
    tenantId: "<tenant-id>"
  secretObjects:
    - secretName: app-secrets
      type: Opaque
      data:
        - objectName: db-password
          key: DB_PASSWORD
        - objectName: api-key-stripe
          key: STRIPE_KEY
```

---

## Key Vault Networking: Private and Secure

By default, Key Vault is accessible from the public internet (with authentication required). For production, restrict network access:

```bash
# Restrict to specific VNets and IPs
az keyvault update \
  --name kubedojo-vault \
  --default-action Deny

# Allow access from a specific subnet
az keyvault network-rule add \
  --name kubedojo-vault \
  --subnet "/subscriptions/.../subnets/app-subnet"

# Allow access from a specific IP
az keyvault network-rule add \
  --name kubedojo-vault \
  --ip-address "203.0.113.0/24"

# Or use Private Endpoint for full private access
az network private-endpoint create \
  --resource-group myRG \
  --name kv-private-endpoint \
  --vnet-name hub-vnet \
  --subnet private-endpoints \
  --private-connection-resource-id "$VAULT_ID" \
  --group-id vault \
  --connection-name kv-connection
```

---

## Did You Know?

1. **Azure Key Vault processes over 200 billion transactions per month** across all Azure customers as of 2024. It is one of the most heavily used services in Azure because virtually every Azure service that needs secrets, keys, or certificates uses Key Vault under the hood. Azure Disk Encryption, App Service certificates, SQL Transparent Data Encryption---they all store their keys in Key Vault.

2. **Key Vault Premium SKU uses FIPS 140-2 Level 3 validated HSMs** (Marvell LiquidSecurity), while Standard uses Level 2. The difference: Level 3 HSMs have physical tamper-evidence mechanisms and identity-based authentication. Level 3 is required for certain compliance frameworks like PCI-DSS in some interpretations. Premium costs approximately $1 per key per month, while Standard key operations are billed per 10,000 operations ($0.03).

3. **Key Vault has a throttling limit of 4,000 transactions per vault per 10 seconds** for secret read operations. A team running 500 microservices that each fetched 3 secrets at startup experienced throttling when deploying all services simultaneously. The fix: cache secrets locally with a reasonable refresh interval (every 5 minutes instead of every request) and stagger deployments.

4. **Once purge protection is enabled on a vault, it cannot be disabled.** This is by design---it prevents an attacker who gains admin access from disabling the protection and then purging secrets. A team accidentally enabled purge protection on a test vault with a 90-day retention period, meaning they cannot fully clean up deleted test secrets for 3 months. Always use a shorter retention period (7 days) for non-production vaults.

---

## Common Mistakes

| Mistake | Why It Happens | How to Fix It |
| :--- | :--- | :--- |
| Storing secrets in environment variables, config files, or code | It is "faster" during development | Use Key Vault from day one. Local dev uses `DefaultAzureCredential` which falls back to Azure CLI login---no secret management needed locally. |
| Creating one vault per secret | Misunderstanding of vault purpose | A vault is a logical grouping of related secrets. Use one vault per application/environment (e.g., `app-prod-vault`, `app-dev-vault`). |
| Using Access Policies instead of RBAC on new vaults | Access Policies are the older default | Always create vaults with `--enable-rbac-authorization true`. RBAC provides per-secret scoping, Conditional Access integration, and PIM support. |
| Not enabling purge protection on production vaults | It seems overly cautious | A compromised admin could delete and purge all secrets. Purge protection ensures deleted secrets can be recovered. Enable it on all production vaults. |
| Reading secrets from Key Vault on every request | It seems like the "most secure" approach | Cache secrets in memory and refresh periodically (every 5-15 minutes). Key Vault has throttling limits, and each call adds 5-10ms latency. |
| Granting Key Vault Administrator when Key Vault Secrets User is sufficient | "Administrator" sounds like the right role for an admin | Key Vault Administrator can create, delete, and manage ALL objects. Most applications only need Key Vault Secrets User (read secrets). |
| Not rotating secrets | The initial secret "works fine" | Implement secret rotation. Use Key Vault's built-in rotation policies (preview), or use Event Grid notifications to trigger rotation logic. |
| Forgetting to configure firewall rules on production vaults | The vault works from everywhere by default | Set `--default-action Deny` and add only the necessary VNet subnets and IPs. Use Private Endpoint for the strongest isolation. |

---

## Quiz

<details>
<summary>1. What are the three types of objects that Azure Key Vault can store, and when would you use each?</summary>

Secrets store any sensitive string value (up to 25 KB): database passwords, API keys, connection strings, and configuration values. Use secrets when you need to store and retrieve a raw value. Keys store RSA or EC cryptographic keys that never leave the HSM. Use keys when you need to encrypt/decrypt data or sign/verify signatures without exposing the raw key material. Certificates store X.509 certificates with their private keys and can handle automated renewal. Use certificates for TLS/SSL endpoints, mTLS between services, and code signing. The key distinction is that keys and certificates have cryptographic operations that happen inside Key Vault, while secrets are just stored and retrieved.
</details>

<details>
<summary>2. Why is Azure RBAC recommended over Access Policies for Key Vault?</summary>

RBAC provides several advantages: (1) Per-object scoping---you can grant access to a specific secret, not the entire vault. (2) Conditional Access integration---you can require MFA or compliant devices for Key Vault access. (3) PIM (Privileged Identity Management) support---you can make access time-limited and require approval. (4) Consistency with the rest of Azure---the same role assignment model used everywhere else. (5) Azure Policy compliance---RBAC assignments can be audited and enforced by Azure Policy. Access Policies lack all of these capabilities and operate only at the vault level.
</details>

<details>
<summary>3. What happens when you delete a secret from a vault with soft delete enabled and purge protection enabled?</summary>

The secret enters a "soft-deleted" state. It no longer appears in the active secrets list, and applications that reference it will get a 404 error. However, it can be recovered (restored to active state) at any time during the retention period. With purge protection enabled, nobody---not even a Global Administrator---can permanently destroy (purge) the secret before the retention period expires. After the retention period ends (7-90 days, depending on configuration), the secret is automatically and permanently deleted. This two-layer protection ensures that both accidental deletions and malicious purge attempts are prevented.
</details>

<details>
<summary>4. How does the DefaultAzureCredential pattern work for Key Vault access across development and production environments?</summary>

DefaultAzureCredential tries multiple authentication methods in a priority order. On a developer's laptop, it finds Azure CLI credentials (from `az login`) and uses those to authenticate with Key Vault. On an Azure VM or Container App with a Managed Identity, it finds the Managed Identity token endpoint and uses that. On a CI/CD pipeline with environment variables, it uses those credentials. The application code is identical in all environments---`DefaultAzureCredential()` with no parameters. This eliminates environment-specific authentication code and prevents developers from hardcoding credentials for "just this environment."
</details>

<details>
<summary>5. A team reads 3 secrets from Key Vault on every HTTP request. Their API handles 500 requests per second. What problem will they encounter, and how should they fix it?</summary>

They will hit Key Vault's throttling limit. At 500 RPS with 3 secret reads each, that is 1,500 Key Vault transactions per second, or 15,000 per 10 seconds. Key Vault throttles at roughly 4,000 transactions per vault per 10 seconds for secret operations. They will start getting 429 (Too Many Requests) responses. The fix is to cache secrets in memory with a periodic refresh. Read secrets from Key Vault once at application startup and refresh every 5-15 minutes. The Azure SDK provides `SecretClient` which can be combined with a simple in-memory cache. For .NET, the `Azure.Extensions.AspNetCore.Configuration.Secrets` package handles caching automatically.
</details>

<details>
<summary>6. Compare storing a database password in an environment variable vs. Azure Key Vault. What are the security implications of each?</summary>

Environment variable: The password is visible in process listings (`/proc/<pid>/environ` on Linux), in crash dumps, in application settings in the Azure portal, in deployment scripts, and in CI/CD pipeline logs if accidentally echoed. Anyone with read access to the App Service configuration can see it. There is no audit trail of who read the password and when. Rotating requires redeploying the application. Key Vault: The password is stored encrypted in an HSM. Access requires authentication (Managed Identity or Entra ID credential). Every read is logged in Key Vault diagnostic logs (who, when, what, from where). RBAC controls who can read vs. manage the secret. Rotating the secret in Key Vault does not require redeploying the application (if using Key Vault references with version rotation). Soft delete and purge protection prevent accidental or malicious deletion.
</details>

---

## Hands-On Exercise: DB Connection String in Key Vault, Retrieved by Container App via Managed Identity

In this exercise, you will store a secret in Key Vault, create a Container App with a Managed Identity, grant the identity access to read the secret, and verify the integration.

**Prerequisites**: Azure CLI installed and authenticated.

### Task 1: Create Key Vault with RBAC Authorization

```bash
RG="kubedojo-keyvault-lab"
LOCATION="eastus2"
VAULT_NAME="kubedojokv$(openssl rand -hex 4)"

az group create --name "$RG" --location "$LOCATION"

az keyvault create \
  --resource-group "$RG" \
  --name "$VAULT_NAME" \
  --location "$LOCATION" \
  --enable-rbac-authorization true \
  --retention-days 7 \
  --enable-purge-protection false  # false for lab (easy cleanup)

# Grant yourself Key Vault Secrets Officer so you can create secrets
USER_ID=$(az ad signed-in-user show --query id -o tsv)
VAULT_ID=$(az keyvault show -n "$VAULT_NAME" --query id -o tsv)
az role assignment create \
  --assignee "$USER_ID" \
  --role "Key Vault Secrets Officer" \
  --scope "$VAULT_ID"
```

<details>
<summary>Verify Task 1</summary>

```bash
az keyvault show -n "$VAULT_NAME" \
  --query '{Name:name, RBAC:properties.enableRbacAuthorization, SoftDelete:properties.enableSoftDelete}' -o table
```
</details>

### Task 2: Store Secrets in Key Vault

```bash
# Store a simulated database connection string
az keyvault secret set \
  --vault-name "$VAULT_NAME" \
  --name "db-connection-string" \
  --value "Server=tcp:myserver.database.windows.net,1433;Database=mydb;User=admin;Password=S3cureP@ss!;"

# Store an API key
az keyvault secret set \
  --vault-name "$VAULT_NAME" \
  --name "api-key" \
  --value "sk-live-abc123def456ghi789"

# Verify secrets exist
az keyvault secret list --vault-name "$VAULT_NAME" \
  --query '[].{Name:name, Enabled:attributes.enabled}' -o table
```

<details>
<summary>Verify Task 2</summary>

```bash
az keyvault secret show --vault-name "$VAULT_NAME" --name "db-connection-string" \
  --query '{Name:name, Created:attributes.created}' -o table
```
</details>

### Task 3: Create a User-Assigned Managed Identity

```bash
IDENTITY_NAME="keyvault-reader-identity"

az identity create \
  --resource-group "$RG" \
  --name "$IDENTITY_NAME"

IDENTITY_ID=$(az identity show -g "$RG" -n "$IDENTITY_NAME" --query id -o tsv)
IDENTITY_PRINCIPAL=$(az identity show -g "$RG" -n "$IDENTITY_NAME" --query principalId -o tsv)
IDENTITY_CLIENT=$(az identity show -g "$RG" -n "$IDENTITY_NAME" --query clientId -o tsv)

# Grant the managed identity Key Vault Secrets User role
az role assignment create \
  --assignee "$IDENTITY_PRINCIPAL" \
  --role "Key Vault Secrets User" \
  --scope "$VAULT_ID"

echo "Identity Principal ID: $IDENTITY_PRINCIPAL"
echo "Identity Client ID: $IDENTITY_CLIENT"
```

<details>
<summary>Verify Task 3</summary>

```bash
az role assignment list --assignee "$IDENTITY_PRINCIPAL" --scope "$VAULT_ID" \
  --query '[].{Role:roleDefinitionName, Scope:scope}' -o table
```

You should see `Key Vault Secrets User` assigned.
</details>

### Task 4: Create Container Apps Environment and App

```bash
# Create Log Analytics workspace
az monitor log-analytics workspace create \
  --resource-group "$RG" --workspace-name kv-lab-logs
LOG_ID=$(az monitor log-analytics workspace show -g "$RG" -n kv-lab-logs --query customerId -o tsv)
LOG_KEY=$(az monitor log-analytics workspace get-shared-keys -g "$RG" -n kv-lab-logs --query primarySharedKey -o tsv)

# Create Container Apps environment
az containerapp env create \
  --resource-group "$RG" \
  --name kv-lab-env \
  --location "$LOCATION" \
  --logs-workspace-id "$LOG_ID" \
  --logs-workspace-key "$LOG_KEY"

# Deploy a Container App with the managed identity
az containerapp create \
  --resource-group "$RG" \
  --name secret-reader-app \
  --environment kv-lab-env \
  --image mcr.microsoft.com/k8se/quickstart:latest \
  --target-port 80 \
  --ingress external \
  --user-assigned "$IDENTITY_ID" \
  --min-replicas 1 \
  --max-replicas 1 \
  --env-vars "VAULT_URL=https://${VAULT_NAME}.vault.azure.net/" "AZURE_CLIENT_ID=$IDENTITY_CLIENT"
```

<details>
<summary>Verify Task 4</summary>

```bash
az containerapp show -g "$RG" -n secret-reader-app \
  --query '{Name:name, Identities:identity.userAssignedIdentities}' -o json | head -10
```

You should see the user-assigned identity attached to the Container App.
</details>

### Task 5: Verify Secret Access from the Container App

```bash
# Get the Container App's FQDN
APP_FQDN=$(az containerapp show -g "$RG" -n secret-reader-app \
  --query properties.configuration.ingress.fqdn -o tsv)
echo "App URL: https://$APP_FQDN"

# Test that the managed identity can read secrets using az CLI inside the container
# (In a real app, you'd use the Azure SDK with DefaultAzureCredential)
az containerapp exec \
  --resource-group "$RG" \
  --name secret-reader-app \
  --command "curl -s -H 'Metadata: true' 'http://169.254.169.254/metadata/identity/oauth2/token?api-version=2019-08-01&resource=https://vault.azure.net&client_id=$IDENTITY_CLIENT'" 2>/dev/null | head -1 || \
echo "Note: exec may not be available on quickstart image. Testing via CLI instead."

# Verify from outside: use Azure CLI to confirm the identity has access
az keyvault secret show \
  --vault-name "$VAULT_NAME" \
  --name "db-connection-string" \
  --query '{Name:name, Value:value}' -o table
```

<details>
<summary>Verify Task 5</summary>

The secret should be readable. In a production scenario, your application code would use the Azure SDK:

```python
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

credential = DefaultAzureCredential()
client = SecretClient(vault_url="https://VAULT_NAME.vault.azure.net/", credential=credential)
secret = client.get_secret("db-connection-string")
# Use secret.value to configure your database connection
```

The `AZURE_CLIENT_ID` environment variable tells `DefaultAzureCredential` which user-assigned managed identity to use.
</details>

### Task 6: Test Soft Delete and Recovery

```bash
# Delete a secret
az keyvault secret delete --vault-name "$VAULT_NAME" --name "api-key"

# Verify it is gone from active list
az keyvault secret list --vault-name "$VAULT_NAME" \
  --query '[].name' -o tsv

# Find it in deleted secrets
az keyvault secret list-deleted --vault-name "$VAULT_NAME" \
  --query '[].{Name:name, DeletedDate:deletedDate}' -o table

# Recover it
az keyvault secret recover --vault-name "$VAULT_NAME" --name "api-key"

# Verify it is back
az keyvault secret show --vault-name "$VAULT_NAME" --name "api-key" \
  --query '{Name:name, Value:value}' -o table
```

<details>
<summary>Verify Task 6</summary>

The api-key secret should be restored to its original value after recovery. This demonstrates that soft delete protects against accidental deletions.
</details>

### Cleanup

```bash
az group delete --name "$RG" --yes --no-wait
```

### Success Criteria

- [ ] Key Vault created with RBAC authorization
- [ ] Two secrets stored (db-connection-string and api-key)
- [ ] User-assigned Managed Identity created and granted Key Vault Secrets User role
- [ ] Container App deployed with the managed identity attached
- [ ] Verified that the identity can read secrets from Key Vault
- [ ] Soft delete tested: secret deleted, found in deleted list, and recovered

---

## Next Module

[Module 3.10: Azure Monitor & Log Analytics](module-3.10-monitor/) --- Learn how to observe your Azure infrastructure and applications with metrics, logs, KQL queries, and alerts that notify you before your customers notice problems.
