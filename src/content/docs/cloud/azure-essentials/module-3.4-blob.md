---
title: "Module 3.4: Azure Blob Storage & Data Lake"
slug: cloud/azure-essentials/module-3.4-blob
sidebar:
  order: 5
---
**Complexity**: [QUICK] | **Time to Complete**: 1.5h | **Prerequisites**: Module 3.1 (Entra ID & RBAC)

## What You'll Be Able to Do

After completing this module, you will be able to:

- **Configure Azure Blob Storage with access tiers (Hot, Cool, Cold, Archive) and lifecycle management policies**
- **Implement storage account security with private endpoints, SAS tokens, and Entra ID-based RBAC access**
- **Deploy blob versioning, soft delete, and immutable storage policies for data protection and compliance**
- **Design Data Lake Storage Gen2 hierarchical namespaces for analytics workloads integrated with Azure services**

---

## Why This Module Matters

In January 2022, a healthcare analytics company discovered that their Azure storage bill had silently grown from $800/month to $14,200/month over six months. The cause was mundane but devastating: an automated pipeline had been writing diagnostic logs and intermediate processing files to a Hot-tier storage account at a rate of approximately 3 TB per week. Nobody had configured lifecycle management policies, so six months of data---roughly 78 TB---sat in Hot storage at $0.018 per GB per month ($1,437/month for the data alone, plus transaction and bandwidth costs that pushed the total to $14,200). Moving 40% of that data to Cool tier (accessed less than once per month) and 50% to Archive tier (never accessed again) would have reduced storage costs by over 80%. The unnecessary spending over those six months was money that could have funded two engineering hires.

Azure Blob Storage is the foundation of data storage in Azure. It handles everything from serving website assets and storing application logs to backing enterprise data lakes and machine learning datasets. It is deceptively simple on the surface---you create a storage account, upload files, and they are stored. But beneath that simplicity lies a system with multiple access tiers, sophisticated access control mechanisms, replication options, and lifecycle management that can mean the difference between a reasonable bill and a financial disaster.

In this module, you will learn how Azure Storage Accounts work, how to choose the right access tier for your data, how SAS tokens and identity-based access control secure your blobs, and how Azure Data Lake Storage Gen2 extends Blob Storage for big data workloads. By the end, you will understand how to design a storage strategy that balances cost, performance, and security.

---

## Storage Accounts: The Container for Everything

A **Storage Account** is the top-level resource for Azure Storage. It provides a unique namespace for your data that is accessible from anywhere in the world over HTTP or HTTPS. A single storage account can hold up to 5 PiB (petabytes) of data.

### Storage Account Types

| Account Type | Supported Services | Performance Tiers | Use Case |
| :--- | :--- | :--- | :--- |
| **Standard general-purpose v2** | Blob, File, Queue, Table | Standard (HDD-backed) | Most workloads---default choice |
| **Premium block blobs** | Blob only (block blobs) | Premium (SSD-backed) | Low-latency, high-transaction workloads |
| **Premium file shares** | Files only | Premium (SSD-backed) | Enterprise file shares, databases on SMB |
| **Premium page blobs** | Page blobs only | Premium (SSD-backed) | VM disk storage (unmanaged disks---legacy) |

For the vast majority of workloads, **Standard general-purpose v2** is the right choice. Premium accounts are for specialized scenarios where you need sub-millisecond latency or extremely high transaction rates.

```bash
# Create a standard storage account with LRS (locally redundant)
az storage account create \
  --name "kubedojostorage$(openssl rand -hex 4)" \
  --resource-group myRG \
  --location eastus2 \
  --sku Standard_LRS \
  --kind StorageV2 \
  --min-tls-version TLS1_2 \
  --allow-blob-public-access false

# Create a premium block blob account for low-latency workloads
az storage account create \
  --name "kubedojopremium$(openssl rand -hex 4)" \
  --resource-group myRG \
  --location eastus2 \
  --sku Premium_LRS \
  --kind BlockBlobStorage
```

### Redundancy Options

Azure replicates your data to protect against failures. The redundancy option you choose affects both durability and cost:

```text
    ┌──────────────────────────────────────────────────────────────────────┐
    │                         Redundancy Options                          │
    ├────────────────┬───────────────────────────┬────────────────────────┤
    │ Option         │ How It Works              │ Durability             │
    ├────────────────┼───────────────────────────┼────────────────────────┤
    │ LRS            │ 3 copies in one           │ 99.999999999% (11 9s) │
    │ (Locally       │ data center               │                        │
    │  Redundant)    │                           │                        │
    ├────────────────┼───────────────────────────┼────────────────────────┤
    │ ZRS            │ 3 copies across 3         │ 99.9999999999% (12 9s)│
    │ (Zone          │ availability zones        │                        │
    │  Redundant)    │                           │                        │
    ├────────────────┼───────────────────────────┼────────────────────────┤
    │ GRS            │ LRS in primary +          │ 99.99999999999999%    │
    │ (Geo           │ LRS in secondary region   │ (16 9s)               │
    │  Redundant)    │ (async, no read access)   │                        │
    ├────────────────┼───────────────────────────┼────────────────────────┤
    │ RA-GRS         │ GRS + read access         │ 99.99999999999999%    │
    │ (Read-Access   │ to secondary region       │ (16 9s)               │
    │  Geo Redundant)│                           │                        │
    ├────────────────┼───────────────────────────┼────────────────────────┤
    │ GZRS           │ ZRS in primary +          │ 99.99999999999999%    │
    │ (Geo-Zone      │ LRS in secondary          │ (16 9s)               │
    │  Redundant)    │                           │                        │
    ├────────────────┼───────────────────────────┼────────────────────────┤
    │ RA-GZRS        │ GZRS + read access        │ 99.99999999999999%    │
    │ (Read-Access   │ to secondary              │ (16 9s)               │
    │  Geo-Zone)     │                           │                        │
    └────────────────┴───────────────────────────┴────────────────────────┘

    Cost comparison (per GB, Hot tier, East US, approximate):
    LRS:     $0.018    (baseline)
    ZRS:     $0.023    (+28%)
    GRS:     $0.036    (+100%)
    RA-GRS:  $0.046    (+156%)
```

**War Story**: A fintech startup chose LRS (cheapest) for their transaction ledger storage. When the data center experienced a power outage, their storage was offline for 3 hours. While no data was lost (LRS maintains 3 copies within the same data center), the unavailability violated their SLA with banking partners. They switched to ZRS, which would have survived the outage because it replicates across three independent data centers in the region. The extra $0.005/GB cost amounted to about $50/month for their 10 TB dataset---trivial compared to the $25,000 SLA penalty they paid.

---

## Blob Storage: Containers and Blobs

Blob (Binary Large Object) storage is organized into **containers** within a storage account. Think of containers as top-level directories (though they are flat---there are no actual subdirectories).

```text
    Storage Account: kubedojostorage
    │
    ├── Container: images
    │   ├── logos/company-logo.png        (block blob)
    │   ├── photos/team-2024.jpg          (block blob)
    │   └── raw/scan-001.tiff             (block blob)
    │
    ├── Container: logs
    │   ├── 2024/01/app-log-001.json.gz   (block blob)
    │   ├── 2024/02/app-log-002.json.gz   (block blob)
    │   └── 2024/03/app-log-003.json.gz   (block blob)
    │
    └── Container: backups
        ├── db-backup-2024-01-15.sql.gz   (block blob)
        └── db-backup-2024-02-15.sql.gz   (block blob)

    Note: The "/" in blob names creates a virtual directory hierarchy
    in the Azure portal, but the underlying storage is flat.
```

### Blob Types

| Type | Max Size | Use Case |
| :--- | :--- | :--- |
| **Block Blob** | 190.7 TiB | Files, images, logs, backups---99% of workloads |
| **Append Blob** | 195 GiB | Append-only scenarios like log files |
| **Page Blob** | 8 TiB | Random read/write---used for VM disks (legacy) |

```bash
STORAGE_NAME="kubedojostorage"  # Replace with your actual name

# Create a container
az storage container create \
  --name "application-data" \
  --account-name "$STORAGE_NAME" \
  --auth-mode login

# Upload a file
echo '{"event": "user_login", "timestamp": "2024-06-15T10:30:00Z"}' > /tmp/event.json
az storage blob upload \
  --container-name "application-data" \
  --file /tmp/event.json \
  --name "events/2024/06/event-001.json" \
  --account-name "$STORAGE_NAME" \
  --auth-mode login

# Upload multiple files
az storage blob upload-batch \
  --destination "application-data" \
  --source /tmp/logs/ \
  --pattern "*.log" \
  --account-name "$STORAGE_NAME" \
  --auth-mode login

# List blobs in a container
az storage blob list \
  --container-name "application-data" \
  --account-name "$STORAGE_NAME" \
  --auth-mode login \
  --query '[].{Name:name, Size:properties.contentLength, Tier:properties.blobTier}' -o table

# Download a blob
az storage blob download \
  --container-name "application-data" \
  --name "events/2024/06/event-001.json" \
  --file /tmp/downloaded-event.json \
  --account-name "$STORAGE_NAME" \
  --auth-mode login
```

---

## Access Tiers: Hot, Cool, Cold, and Archive

Azure Blob Storage offers four access tiers with different cost profiles. The key insight is that **storage cost and access cost are inversely related**: cheaper storage means more expensive reads.

| Tier | Storage Cost (per GB) | Read Cost (per 10K ops) | Min Retention | Access Latency | Best For |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Hot** | $0.018 | $0.004 | None | Milliseconds | Frequently accessed data |
| **Cool** | $0.010 | $0.01 | 30 days | Milliseconds | Infrequently accessed (monthly) |
| **Cold** | $0.0045 | $0.01 | 90 days | Milliseconds | Rarely accessed (quarterly) |
| **Archive** | $0.002 | $5.00 + rehydration | 180 days | Hours (rehydration) | Compliance, long-term backup |

```text
    Cost Visualization (storing 10 TB for 1 year):

    Hot:     $2,160/year storage + low access costs
    Cool:    $1,200/year storage + moderate access costs
    Cold:    $  540/year storage + moderate access costs
    Archive: $  240/year storage + HIGH access costs

    The break-even point between Hot and Cool is roughly:
    If you access data less than once per month → Cool is cheaper
    If you access data less than once per quarter → Cold is cheaper
    If you never access it (compliance retention) → Archive
```

```bash
# Set the default access tier for a storage account
az storage account update \
  --name "$STORAGE_NAME" \
  --resource-group myRG \
  --access-tier Cool

# Set tier for individual blobs
az storage blob set-tier \
  --container-name "application-data" \
  --name "events/2024/01/event-old.json" \
  --tier Archive \
  --account-name "$STORAGE_NAME" \
  --auth-mode login

# Rehydrate a blob from Archive (takes hours)
az storage blob set-tier \
  --container-name "application-data" \
  --name "events/2024/01/event-old.json" \
  --tier Hot \
  --rehydrate-priority High \
  --account-name "$STORAGE_NAME" \
  --auth-mode login
# High priority: typically <1 hour. Standard priority: up to 15 hours.
```

### Lifecycle Management Policies

Manually moving blobs between tiers is impractical at scale. Lifecycle management policies automate tier transitions and deletion based on age.

```bash
# Create a lifecycle management policy
az storage account management-policy create \
  --account-name "$STORAGE_NAME" \
  --resource-group myRG \
  --policy '{
    "rules": [
      {
        "name": "move-to-cool-after-30-days",
        "enabled": true,
        "type": "Lifecycle",
        "definition": {
          "filters": {
            "blobTypes": ["blockBlob"],
            "prefixMatch": ["logs/"]
          },
          "actions": {
            "baseBlob": {
              "tierToCool": {"daysAfterModificationGreaterThan": 30},
              "tierToArchive": {"daysAfterModificationGreaterThan": 180},
              "delete": {"daysAfterModificationGreaterThan": 365}
            }
          }
        }
      }
    ]
  }'
```

This policy automatically moves blobs in the `logs/` prefix to Cool after 30 days, to Archive after 180 days, and deletes them after 365 days. Set it once and forget it---Azure handles the rest.

---

## Securing Blob Storage: SAS Tokens vs Identity-Based Access

There are three ways to authorize access to blob storage. Understanding when to use each is critical for security.

### 1. Account Keys (Avoid in Production)

Every storage account has two 512-bit access keys that grant **full control** over the entire account. Using these keys is like giving someone the master key to your building.

```bash
# List storage account keys
az storage account keys list \
  --account-name "$STORAGE_NAME" \
  --resource-group myRG \
  --query '[].{KeyName:keyName, Value:value}' -o table

# Rotate keys (do this regularly if you must use keys)
az storage account keys renew \
  --account-name "$STORAGE_NAME" \
  --resource-group myRG \
  --key key1
```

### 2. Shared Access Signatures (SAS Tokens)

A SAS token is a URI query string that grants restricted access to storage resources. You define what operations are allowed, which resources can be accessed, and when the access expires.

```bash
# Generate a SAS token for a specific blob (read-only, expires in 1 hour)
END_DATE=$(date -u -v+1H "+%Y-%m-%dT%H:%MZ" 2>/dev/null || date -u -d "+1 hour" "+%Y-%m-%dT%H:%MZ")

az storage blob generate-sas \
  --account-name "$STORAGE_NAME" \
  --container-name "application-data" \
  --name "events/2024/06/event-001.json" \
  --permissions r \
  --expiry "$END_DATE" \
  --auth-mode login \
  --as-user \
  --output tsv

# Generate a SAS for an entire container (list + read, 24 hours)
END_DATE_24H=$(date -u -v+24H "+%Y-%m-%dT%H:%MZ" 2>/dev/null || date -u -d "+24 hours" "+%Y-%m-%dT%H:%MZ")

az storage container generate-sas \
  --account-name "$STORAGE_NAME" \
  --name "application-data" \
  --permissions lr \
  --expiry "$END_DATE_24H" \
  --auth-mode login \
  --as-user \
  --output tsv
```

SAS token permission flags:

| Flag | Permission |
| :--- | :--- |
| `r` | Read |
| `a` | Add |
| `c` | Create |
| `w` | Write |
| `d` | Delete |
| `l` | List |
| `t` | Tags |
| `x` | Execute |

### 3. Identity-Based Access (Recommended)

The best approach is to use Entra ID identities (users, groups, service principals, or managed identities) with Azure RBAC roles. No keys or tokens to manage, rotate, or leak.

```bash
# Grant a user read access to blob data
az role assignment create \
  --assignee "alice@yourcompany.onmicrosoft.com" \
  --role "Storage Blob Data Reader" \
  --scope "/subscriptions/<sub>/resourceGroups/myRG/providers/Microsoft.Storage/storageAccounts/$STORAGE_NAME"

# Grant a managed identity write access to a specific container
az role assignment create \
  --assignee "$MANAGED_IDENTITY_PRINCIPAL_ID" \
  --role "Storage Blob Data Contributor" \
  --scope "/subscriptions/<sub>/resourceGroups/myRG/providers/Microsoft.Storage/storageAccounts/$STORAGE_NAME/blobServices/default/containers/application-data"
```

Key storage RBAC roles:

| Role | What It Grants |
| :--- | :--- |
| **Storage Blob Data Reader** | Read and list blobs |
| **Storage Blob Data Contributor** | Read, write, delete blobs |
| **Storage Blob Data Owner** | Full access + set POSIX ACLs (Data Lake) |
| **Storage Blob Delegator** | Generate user delegation SAS tokens |

```text
    Authorization Method Decision Tree:

    Is the client an Azure resource (VM, Function, Container App)?
    ├── YES → Use Managed Identity + RBAC (no credentials needed)
    │
    └── NO → Is the client a human user?
        ├── YES → Use Entra ID login + RBAC (az login / browser auth)
        │
        └── NO → Is it a one-time or temporary share?
            ├── YES → Use SAS token with short expiry and minimum permissions
            │
            └── NO → Use Service Principal + RBAC (with certificate, not secret)
```

---

## Azure Data Lake Storage Gen2

Azure Data Lake Storage Gen2 (ADLS Gen2) is not a separate service---it is a capability built on top of Blob Storage. When you enable the **hierarchical namespace** on a storage account, you get true directory semantics, POSIX-like access control lists (ACLs), and atomic directory operations. This makes it suitable for big data analytics workloads that tools like Apache Spark, Databricks, and Synapse Analytics expect.

```bash
# Create a storage account with hierarchical namespace (Data Lake)
az storage account create \
  --name "kubedojodatalake$(openssl rand -hex 4)" \
  --resource-group myRG \
  --location eastus2 \
  --sku Standard_LRS \
  --kind StorageV2 \
  --enable-hierarchical-namespace true

# Create a filesystem (equivalent to a container in blob storage)
az storage fs create \
  --name "raw-data" \
  --account-name "$DATALAKE_NAME" \
  --auth-mode login

# Create actual directories (not virtual like in blob storage)
az storage fs directory create \
  --name "2024/06/sales" \
  --file-system "raw-data" \
  --account-name "$DATALAKE_NAME" \
  --auth-mode login
```

The key differences between regular Blob Storage and ADLS Gen2:

| Feature | Blob Storage | ADLS Gen2 |
| :--- | :--- | :--- |
| **Namespace** | Flat (virtual directories via `/`) | Hierarchical (real directories) |
| **Rename directory** | Must copy all blobs, then delete originals | Atomic single operation |
| **ACLs** | RBAC only (container/account level) | RBAC + POSIX ACLs (file/directory level) |
| **Analytics tools** | Limited integration | Native Spark, Databricks, Synapse support |
| **Protocol** | Blob REST API (`blob.core.windows.net`) | Blob + DFS REST API (`dfs.core.windows.net`) |
| **Cost** | Same | Same (no premium for hierarchical namespace) |

---

## Did You Know?

1. **A single Azure Storage Account can handle up to 20,000 requests per second** and store up to 5 PiB of data. However, a single block blob has a throughput limit of about 300 MiB/s for reads. If you need to serve a very popular file to thousands of concurrent clients, put Azure CDN in front of the storage account rather than scaling the storage account itself.

2. **Archive tier rehydration can take up to 15 hours with Standard priority.** A team at a media company needed to restore 2 TB of archived footage for a legal discovery request. They chose Standard priority and quoted their legal team "a few hours." Fifteen hours later, the data was still rehydrating. High-priority rehydration typically completes in under an hour for blobs smaller than 10 GB, but Azure provides no hard SLA on rehydration times.

3. **Deleting a blob in Cool tier before 30 days incurs an early deletion fee.** Similarly, Cold has a 90-day minimum, and Archive has a 180-day minimum. If you upload a 100 GB file to Archive tier and then realize you need to delete it 10 days later, you still pay for 180 days of storage ($0.002 x 100 GB x 6 months = $1.20) plus the rehydration cost. Always confirm you will not need the data before archiving it.

4. **Azure Storage immutability policies (WORM---Write Once, Read Many) are legally recognized** for regulatory compliance in industries like finance and healthcare. Once a time-based retention policy is locked, even the subscription owner and Microsoft support cannot delete the data until the retention period expires. A company accidentally locked a 7-year retention policy on a 50 TB container of test data, costing them approximately $7,200 over the retention period with no way to delete it.

---

## Common Mistakes

| Mistake | Why It Happens | How to Fix It |
| :--- | :--- | :--- |
| Storing all data in Hot tier indefinitely | Hot is the default and "just works" | Implement lifecycle management policies on day one. Most logs and backups should move to Cool after 30 days. |
| Using storage account keys in application code | Keys are the first thing shown in tutorials | Use Managed Identities and RBAC for Azure-hosted apps. Use SAS tokens with short expiry for external access. |
| Creating SAS tokens with long expiry and broad permissions | Developers want tokens that "just work" without renewal | Generate SAS tokens scoped to specific containers/blobs with minimum permissions and short expiry (hours, not months). |
| Not enabling soft delete on blob storage | It seems like an unnecessary precaution until someone deletes production data | Enable soft delete with a 14-30 day retention period. It costs almost nothing but saves you from accidental deletions. |
| Choosing LRS for data that cannot be recreated | LRS is the cheapest option | Use ZRS minimum for any data that has no backup. Use GRS or RA-GRS for business-critical data like customer records. |
| Enabling public anonymous access on containers | Quick demos and testing leave public access enabled | Set `--allow-blob-public-access false` at the account level. Use SAS tokens or RBAC for legitimate sharing needs. |
| Not planning the storage account naming scheme | Storage account names must be globally unique and 3-24 characters | Adopt a naming convention early: `<company><env><region><purpose>`, e.g., `acmeprodeus2data`. |
| Using Blob Storage when Data Lake (hierarchical namespace) is needed | Teams start with blob storage and later discover they need Spark/Databricks compatibility | Decide upfront if you need analytics workloads. Enabling hierarchical namespace later requires creating a new account and migrating data. |

---

## Quiz

<details>
<summary>1. A storage account has 50 TB of log files in Hot tier that are accessed approximately once per quarter. Which tier should they be in, and how much would you save annually?</summary>

They should be in Cold tier. Hot tier costs $0.018/GB/month = $0.018 x 50,000 GB x 12 = $10,800/year. Cold tier costs $0.0045/GB/month = $0.0045 x 50,000 GB x 12 = $2,700/year. The annual savings would be approximately $8,100. Cool tier ($0.010/GB) would also be a significant improvement at $6,000/year, but since the data is accessed only quarterly, Cold tier's 90-day minimum retention is not a problem, and it provides the best cost-performance balance. Archive tier would save even more on storage but the $5/10K read operations cost and hours-long rehydration time make it impractical for data that is still accessed quarterly.
</details>

<details>
<summary>2. What is the difference between a SAS token generated with an account key and one generated with a user delegation key?</summary>

An account-key SAS token is signed using the storage account's access key. If the key is compromised, all SAS tokens generated with that key are valid until they expire. Revoking access requires rotating the account key, which invalidates ALL SAS tokens and any other integrations using that key. A user delegation SAS token is signed using Entra ID credentials (via `--as-user --auth-mode login`). It is tied to the user's identity and the user delegation key (valid for up to 7 days). You can revoke access by revoking the user delegation key without affecting account keys or other integrations. User delegation SAS is always preferred because it provides better auditability and more granular revocation.
</details>

<details>
<summary>3. You need to share a specific blob with an external partner for 48 hours. What is the most secure approach?</summary>

Generate a user delegation SAS token scoped to the specific blob with read-only permission (`r`) and a 48-hour expiry. Use `az storage blob generate-sas --as-user --auth-mode login --permissions r --expiry <48h-from-now>`. This creates a URL that the partner can use without any Azure account. The token automatically expires after 48 hours, is scoped to only that one blob, and is read-only. Do not use account keys to generate the SAS, do not grant access to the entire container, and do not create a SAS with a long expiry "just in case."
</details>

<details>
<summary>4. What happens when you try to read a blob in Archive tier directly?</summary>

You cannot read a blob in Archive tier directly. Attempting to read it returns a 409 Conflict error with the message "This operation is not permitted on an archived blob." You must first rehydrate the blob by changing its tier to Hot or Cool using `az storage blob set-tier`. Rehydration takes up to 15 hours with Standard priority or typically under 1 hour with High priority. During rehydration, the blob's tier shows as "Archive" with a rehydration status of "rehydrate-pending-to-hot" or "rehydrate-pending-to-cool."
</details>

<details>
<summary>5. Why would you enable hierarchical namespace (Data Lake Storage Gen2) on a storage account?</summary>

You enable hierarchical namespace when you need true directory operations for big data analytics workloads. Without it, renaming a "directory" of 10,000 blobs requires 10,000 individual copy-and-delete operations. With hierarchical namespace, renaming a directory is a single atomic operation. You also get POSIX-like ACLs for fine-grained access control at the file and directory level, which is essential for multi-tenant data lake architectures. Tools like Apache Spark, Azure Databricks, and Azure Synapse Analytics work best with the DFS endpoint that hierarchical namespace provides. The cost is the same as regular blob storage, so the only downside is that some blob features are not supported with hierarchical namespace.
</details>

<details>
<summary>6. An application running on an Azure VM needs to write files to a storage container. Compare using account keys vs. Managed Identity for authentication.</summary>

Account keys: You store the key in the application's configuration (environment variable or config file). The key grants full access to the entire storage account (not just the specific container). If the VM is compromised, the attacker gets the key and can access or delete any data in the account. Key rotation requires updating every application that uses the key. Managed Identity: You enable managed identity on the VM and assign "Storage Blob Data Contributor" role scoped to the specific container. The application uses `DefaultAzureCredential()` which automatically acquires tokens from the IMDS endpoint. No credentials are stored anywhere. If the VM is compromised, the attacker can only access the specific container. Credential rotation is handled automatically by Azure. Managed Identity is superior in every dimension---security, operations, and auditability.
</details>

---

## Hands-On Exercise: Storage Account with Lifecycle Policies and SAS Tokens

In this exercise, you will create a storage account, configure lifecycle management, upload blobs to different tiers, and practice generating scoped SAS tokens.

**Prerequisites**: Azure CLI installed and authenticated, "Storage Blob Data Contributor" role on your subscription.

### Task 1: Create a Storage Account

```bash
RG="kubedojo-storage-lab"
LOCATION="eastus2"
STORAGE_NAME="kubedojolab$(openssl rand -hex 4)"

az group create --name "$RG" --location "$LOCATION"

az storage account create \
  --name "$STORAGE_NAME" \
  --resource-group "$RG" \
  --location "$LOCATION" \
  --sku Standard_LRS \
  --kind StorageV2 \
  --min-tls-version TLS1_2 \
  --allow-blob-public-access false \
  --default-action Allow

# Assign yourself Storage Blob Data Contributor
USER_ID=$(az ad signed-in-user show --query id -o tsv)
STORAGE_ID=$(az storage account show -n "$STORAGE_NAME" -g "$RG" --query id -o tsv)
az role assignment create --assignee "$USER_ID" --role "Storage Blob Data Contributor" --scope "$STORAGE_ID"
```

<details>
<summary>Verify Task 1</summary>

```bash
az storage account show -n "$STORAGE_NAME" -g "$RG" \
  --query '{Name:name, SKU:sku.name, TLS:minimumTlsVersion, PublicAccess:allowBlobPublicAccess}' -o table
```
</details>

### Task 2: Create Containers and Upload Test Data

```bash
# Create containers for different purposes
az storage container create --name "hot-data" --account-name "$STORAGE_NAME" --auth-mode login
az storage container create --name "archive-data" --account-name "$STORAGE_NAME" --auth-mode login
az storage container create --name "logs" --account-name "$STORAGE_NAME" --auth-mode login

# Generate some test files
for i in $(seq 1 5); do
  echo "{\"event\": \"test_$i\", \"timestamp\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\"}" > "/tmp/event-$i.json"
done

# Upload to hot-data container
for i in $(seq 1 5); do
  az storage blob upload \
    --container-name "hot-data" \
    --file "/tmp/event-$i.json" \
    --name "events/event-$i.json" \
    --account-name "$STORAGE_NAME" \
    --auth-mode login
done
```

<details>
<summary>Verify Task 2</summary>

```bash
az storage blob list --container-name "hot-data" --account-name "$STORAGE_NAME" \
  --auth-mode login --query '[].{Name:name, Tier:properties.blobTier}' -o table
```

You should see 5 blobs in Hot tier.
</details>

### Task 3: Configure Lifecycle Management Policy

```bash
az storage account management-policy create \
  --account-name "$STORAGE_NAME" \
  --resource-group "$RG" \
  --policy '{
    "rules": [
      {
        "name": "logs-lifecycle",
        "enabled": true,
        "type": "Lifecycle",
        "definition": {
          "filters": {
            "blobTypes": ["blockBlob"],
            "prefixMatch": ["logs/"]
          },
          "actions": {
            "baseBlob": {
              "tierToCool": {"daysAfterModificationGreaterThan": 30},
              "tierToCold": {"daysAfterModificationGreaterThan": 90},
              "tierToArchive": {"daysAfterModificationGreaterThan": 180},
              "delete": {"daysAfterModificationGreaterThan": 365}
            }
          }
        }
      }
    ]
  }'
```

<details>
<summary>Verify Task 3</summary>

```bash
az storage account management-policy show \
  --account-name "$STORAGE_NAME" \
  --resource-group "$RG" \
  --query 'policy.rules[0].{Name:name, CoolAfter:definition.actions.baseBlob.tierToCool.daysAfterModificationGreaterThan, ArchiveAfter:definition.actions.baseBlob.tierToArchive.daysAfterModificationGreaterThan, DeleteAfter:definition.actions.baseBlob.delete.daysAfterModificationGreaterThan}' -o table
```
</details>

### Task 4: Generate a Scoped SAS Token

```bash
# Generate a read-only SAS token for a specific blob, valid for 1 hour
EXPIRY=$(date -u -v+1H "+%Y-%m-%dT%H:%MZ" 2>/dev/null || date -u -d "+1 hour" "+%Y-%m-%dT%H:%MZ")

SAS_TOKEN=$(az storage blob generate-sas \
  --account-name "$STORAGE_NAME" \
  --container-name "hot-data" \
  --name "events/event-1.json" \
  --permissions r \
  --expiry "$EXPIRY" \
  --auth-mode login \
  --as-user \
  --output tsv)

# Construct the full URL
BLOB_URL="https://${STORAGE_NAME}.blob.core.windows.net/hot-data/events/event-1.json?${SAS_TOKEN}"
echo "SAS URL: $BLOB_URL"

# Test the SAS URL (should return the blob content)
curl -s "$BLOB_URL"
```

<details>
<summary>Verify Task 4</summary>

The curl command should return the JSON content of event-1.json. If you try to upload or delete using this SAS URL, it should fail because the token only has read (`r`) permission.
</details>

### Task 5: Enable Soft Delete

```bash
# Enable soft delete for blobs (14 day retention)
az storage account blob-service-properties update \
  --account-name "$STORAGE_NAME" \
  --resource-group "$RG" \
  --enable-delete-retention true \
  --delete-retention-days 14

# Enable soft delete for containers (7 day retention)
az storage account blob-service-properties update \
  --account-name "$STORAGE_NAME" \
  --resource-group "$RG" \
  --enable-container-delete-retention true \
  --container-delete-retention-days 7

# Test: delete a blob, then verify it is soft-deleted
az storage blob delete \
  --container-name "hot-data" \
  --name "events/event-1.json" \
  --account-name "$STORAGE_NAME" \
  --auth-mode login

# List soft-deleted blobs
az storage blob list \
  --container-name "hot-data" \
  --account-name "$STORAGE_NAME" \
  --auth-mode login \
  --include d \
  --query '[?deleted].{Name:name, Deleted:deleted}' -o table
```

<details>
<summary>Verify Task 5</summary>

You should see the deleted blob listed with `Deleted: true`. To restore it:

```bash
az storage blob undelete \
  --container-name "hot-data" \
  --name "events/event-1.json" \
  --account-name "$STORAGE_NAME" \
  --auth-mode login
```
</details>

### Cleanup

```bash
az group delete --name "$RG" --yes --no-wait
```

### Success Criteria

- [ ] Storage account created with TLS 1.2 minimum and public access disabled
- [ ] Three containers created with test blobs uploaded
- [ ] Lifecycle management policy configured for logs container
- [ ] Scoped SAS token generated and tested with curl
- [ ] Soft delete enabled and tested (delete + verify soft-deleted blob)

---

## Next Module

[Module 3.5: Azure DNS & Traffic Manager](../module-3.5-dns/) --- Learn how Azure handles DNS resolution for both public and private zones, and how Traffic Manager and Front Door route traffic across regions for high availability.
