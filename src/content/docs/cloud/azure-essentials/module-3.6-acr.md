---
title: "Module 3.6: Azure Container Registry (ACR)"
slug: cloud/azure-essentials/module-3.6-acr
sidebar:
  order: 7
---
**Complexity**: [MEDIUM] | **Time to Complete**: 1h | **Prerequisites**: Module 3.1 (Entra ID & RBAC), Docker basics

## Why This Module Matters

In September 2022, a DevOps team at a mid-size fintech company pushed a new container image to their shared Docker Hub account. The image contained a critical fix for a payment processing bug. Twenty minutes later, their entire CI/CD pipeline ground to a halt. Docker Hub had rate-limited their pulls: the free tier allows only 100 pulls per 6 hours for anonymous users and 200 for authenticated users. With 40 microservices, 3 environments, and frequent deployments, they were blowing past the limit every day. Developers sat idle for hours waiting for rate limits to reset. The team estimated the productivity loss at roughly $8,000 per incident, and it happened three times that month before they migrated to Azure Container Registry.

Container images are the atoms of modern application deployment. Every container you run---whether on AKS, Container Apps, or ACI---starts with pulling an image from a registry. If your registry is slow, unreliable, or insecure, your entire deployment pipeline suffers. Azure Container Registry is a managed, private Docker registry that integrates deeply with Azure's identity system. It eliminates rate limits, keeps your images close to your compute (same Azure region), and provides features like automated builds, vulnerability scanning, and geo-replication that Docker Hub's free tier cannot match.

In this module, you will learn how to set up ACR, authenticate using different methods (admin, service principal, managed identity), build images directly in the cloud with ACR Tasks, replicate your registry across regions, and secure access using Private Link. By the end, you will have a production-ready container registry strategy.

---

## ACR SKUs: Choosing the Right Tier

ACR comes in three SKUs with dramatically different capabilities and costs:

| Feature | Basic | Standard | Premium |
| :--- | :--- | :--- | :--- |
| **Storage** | 10 GiB | 100 GiB | 500 GiB (expandable to 50 TiB) |
| **Read throughput** | 1,000 ReadOps/min | 3,000 ReadOps/min | 10,000 ReadOps/min |
| **Write throughput** | 100 WriteOps/min | 500 WriteOps/min | 2,000 WriteOps/min |
| **Webhooks** | 2 | 10 | 500 |
| **Geo-replication** | No | No | Yes |
| **Private Link** | No | No | Yes |
| **Content Trust** | No | No | Yes (image signing) |
| **Customer-managed keys** | No | No | Yes |
| **Approximate cost** | ~$5/month | ~$20/month | ~$50/month + replicas |

For most teams, **Standard** is the right starting point. Premium is needed when you require geo-replication (multi-region pulls), Private Link (no public endpoint), or content trust (signed images).

```bash
# Create a Basic ACR (for dev/test)
az acr create \
  --resource-group myRG \
  --name kubedojoacr \
  --sku Basic \
  --location eastus2

# Upgrade to Standard (no downtime, no data loss)
az acr update --name kubedojoacr --sku Standard

# View ACR details
az acr show --name kubedojoacr \
  --query '{Name:name, SKU:sku.name, LoginServer:loginServer, Location:location}' -o table
```

The **login server** is the URL you use to push and pull images: `kubedojoacr.azurecr.io`. This is globally unique.

---

## Authentication: Three Methods, One Recommendation

ACR supports three authentication methods. Understanding the trade-offs is essential for security.

### 1. Admin Account (Avoid in Production)

The admin account provides a username/password pair. It is convenient for quick testing but terrible for production.

```bash
# Enable admin (NOT recommended for production)
az acr update --name kubedojoacr --admin-enabled true

# Get credentials
az acr credential show --name kubedojoacr -o table

# Login with admin credentials
az acr login --name kubedojoacr
```

Problems with admin accounts: the credentials are shared (no auditability), they have full push/pull access (no least privilege), and rotating the password requires updating every system that uses it.

### 2. Service Principal

A service principal provides scoped, auditable access. You can grant different service principals different roles.

```bash
# Create a service principal with AcrPull role (read-only)
ACR_ID=$(az acr show --name kubedojoacr --query id -o tsv)

az ad sp create-for-rbac \
  --name "acr-pull-sp" \
  --role AcrPull \
  --scopes "$ACR_ID"

# Available ACR roles:
# AcrPull   - Pull images only
# AcrPush   - Push and pull images
# AcrDelete - Delete images
# Owner     - Full access including role assignments
```

### 3. Managed Identity (Recommended)

For Azure-hosted workloads, Managed Identity is the best option. No credentials to manage, rotate, or leak.

```bash
# Grant a VM's managed identity access to pull from ACR
VM_PRINCIPAL_ID=$(az vm identity show -g myRG -n myVM --query principalId -o tsv)
ACR_ID=$(az acr show --name kubedojoacr --query id -o tsv)

az role assignment create \
  --assignee "$VM_PRINCIPAL_ID" \
  --role AcrPull \
  --scope "$ACR_ID"

# For AKS, attach ACR directly (creates role assignment automatically)
az aks update \
  --resource-group myRG \
  --name myAKSCluster \
  --attach-acr kubedojoacr
```

```text
    Authentication Decision Tree:

    Is the consumer an Azure resource (AKS, ACI, Container Apps, VM)?
    ├── YES → Managed Identity + AcrPull role
    │
    └── NO → Is it a CI/CD pipeline?
        ├── GitHub Actions → OIDC federated credential (no secrets)
        ├── Azure DevOps → Service Connection (Workload Identity)
        │
        └── Other → Service Principal with certificate (not secret)
                     Set minimum role (AcrPull for pull, AcrPush for push)
```

```bash
# Login to ACR using the Azure CLI (uses your current az login identity)
az acr login --name kubedojoacr

# Push an image
docker tag myapp:latest kubedojoacr.azurecr.io/myapp:v1.0.0
docker push kubedojoacr.azurecr.io/myapp:v1.0.0

# Pull an image
docker pull kubedojoacr.azurecr.io/myapp:v1.0.0

# List repositories in ACR
az acr repository list --name kubedojoacr -o table

# List tags for a repository
az acr repository show-tags --name kubedojoacr --repository myapp -o table

# Show image manifest details
az acr repository show-manifests --name kubedojoacr --repository myapp --detail -o table
```

---

## ACR Tasks: Building Images in the Cloud

ACR Tasks lets you build container images directly in Azure without needing a local Docker daemon or a dedicated build server. This is particularly useful for CI/CD pipelines and for building multi-architecture images.

### Quick Build

The simplest use case: send your Dockerfile and source code to ACR, and it builds the image for you.

```bash
# Build an image from a local Dockerfile (uploads context to ACR)
az acr build \
  --registry kubedojoacr \
  --image myapp:v1.0.0 \
  --file Dockerfile \
  .

# Build from a Git repository
az acr build \
  --registry kubedojoacr \
  --image myapp:v2.0.0 \
  https://github.com/myorg/myrepo.git#main

# Build a multi-architecture image
az acr build \
  --registry kubedojoacr \
  --image myapp:v1.0.0 \
  --platform linux/amd64,linux/arm64 \
  .
```

### Automated Tasks (Trigger-Based Builds)

ACR Tasks can automatically rebuild images when:
- Source code changes (Git commit trigger)
- Base image is updated (e.g., `node:18` gets a security patch)
- On a schedule (daily vulnerability rebuilds)

```bash
# Create a task that rebuilds when the base image updates
az acr task create \
  --registry kubedojoacr \
  --name rebuild-on-base-update \
  --image myapp:{{.Run.ID}} \
  --context https://github.com/myorg/myrepo.git#main \
  --file Dockerfile \
  --git-access-token "$GITHUB_PAT" \
  --base-image-trigger-enabled true \
  --base-image-trigger-type All

# Create a scheduled task (rebuild every day at 3 AM UTC)
az acr task create \
  --registry kubedojoacr \
  --name nightly-rebuild \
  --image myapp:nightly \
  --context https://github.com/myorg/myrepo.git#main \
  --file Dockerfile \
  --git-access-token "$GITHUB_PAT" \
  --schedule "0 3 * * *"

# Manually trigger a task run
az acr task run --registry kubedojoacr --name rebuild-on-base-update

# View task run logs
az acr task logs --registry kubedojoacr --run-id cf1
```

**War Story**: A team discovered a critical vulnerability in the `node:18-alpine` base image at 2 PM on a Friday. They had 23 microservices built on that base image. Without ACR Tasks, rebuilding and pushing all 23 images would have taken their CI pipeline 2 hours (sequential builds on a shared build agent). With ACR Tasks and base image triggers, all 23 images were automatically rebuilt and pushed within 8 minutes of the base image update being published. The team just had to trigger the rollout.

---

## Geo-Replication (Premium SKU)

Geo-replication creates read-only replicas of your registry in multiple Azure regions. When a client in West Europe pulls an image, they pull from the local replica---not from East US across the Atlantic.

```text
    ┌─────────────────────────────────────────────────────┐
    │             ACR: kubedojoacr (Premium)               │
    │                                                     │
    │  ┌──────────────┐  ┌──────────────┐  ┌────────────┐│
    │  │  East US 2   │  │  West Europe │  │  SE Asia   ││
    │  │  (primary)   │  │  (replica)   │  │  (replica) ││
    │  │              │  │              │  │            ││
    │  │  Push here   │──│─ Sync ──────►│──│─ Sync ───►││
    │  │  Pull here   │  │  Pull here   │  │  Pull here││
    │  └──────────────┘  └──────────────┘  └────────────┘│
    │                                                     │
    │  Push: Write to primary, replicated automatically   │
    │  Pull: Read from nearest replica                    │
    └─────────────────────────────────────────────────────┘
```

```bash
# Enable geo-replication (requires Premium SKU)
az acr replication create \
  --registry kubedojoacr \
  --location westeurope

az acr replication create \
  --registry kubedojoacr \
  --location southeastasia

# List replications
az acr replication list --registry kubedojoacr \
  --query '[].{Location:location, Status:provisioningState}' -o table
```

The cost is approximately $50/month per additional replica region, plus storage costs for the replicated data.

---

## Private Link: Eliminating Public Access

For organizations with strict security requirements, ACR Premium supports Private Link. This places the ACR endpoint on a private IP within your VNet, making the registry inaccessible from the public internet.

```bash
# Disable public access
az acr update --name kubedojoacr --public-network-enabled false

# Create a private endpoint for ACR
az network private-endpoint create \
  --resource-group myRG \
  --name acr-private-endpoint \
  --vnet-name hub-vnet \
  --subnet private-endpoints \
  --private-connection-resource-id "$ACR_ID" \
  --group-id registry \
  --connection-name acr-connection

# Create Private DNS Zone for ACR
az network private-dns zone create \
  --resource-group myRG \
  --name privatelink.azurecr.io

# Link DNS zone to VNet
az network private-dns link vnet create \
  --resource-group myRG \
  --zone-name privatelink.azurecr.io \
  --name acr-dns-link \
  --virtual-network hub-vnet \
  --registration-enabled false

# Create DNS zone group for automatic record management
az network private-endpoint dns-zone-group create \
  --resource-group myRG \
  --endpoint-name acr-private-endpoint \
  --name default \
  --private-dns-zone "privatelink.azurecr.io" \
  --zone-name acr
```

After this, `kubedojoacr.azurecr.io` resolves to a private IP (e.g., 10.0.5.10) when queried from within the linked VNet, and is unreachable from the public internet.

---

## Image Management Best Practices

### Tagging Strategy

```bash
# Use semantic versioning for release images
docker tag myapp kubedojoacr.azurecr.io/myapp:1.3.2
docker tag myapp kubedojoacr.azurecr.io/myapp:1.3
docker tag myapp kubedojoacr.azurecr.io/myapp:1
docker tag myapp kubedojoacr.azurecr.io/myapp:latest

# Use Git SHA for traceability
docker tag myapp kubedojoacr.azurecr.io/myapp:sha-a1b2c3d

# Use build number for CI/CD
docker tag myapp kubedojoacr.azurecr.io/myapp:build-1234
```

### Cleanup and Retention

Images accumulate quickly. Without cleanup, your registry storage grows indefinitely.

```bash
# Delete a specific tag
az acr repository delete --name kubedojoacr --image myapp:old-tag --yes

# Delete untagged manifests (orphaned layers)
az acr run --registry kubedojoacr \
  --cmd "acr purge --filter 'myapp:.*' --ago 30d --untagged" \
  /dev/null

# Set up automatic purge (run daily, delete untagged images older than 7 days)
az acr task create \
  --registry kubedojoacr \
  --name purge-untagged \
  --cmd "acr purge --filter '.*:.*' --ago 7d --untagged" \
  --context /dev/null \
  --schedule "0 4 * * *"

# Lock an image to prevent deletion (immutable tag)
az acr repository update \
  --name kubedojoacr \
  --image myapp:v1.0.0 \
  --write-enabled false
```

---

## Did You Know?

1. **ACR Tasks can build images without a Dockerfile** using Buildpacks. By specifying `--pack` in the build command, ACR automatically detects the language runtime and creates an OCI-compliant image. This is useful for teams that want to avoid writing and maintaining Dockerfiles for standard application frameworks like Node.js, Python, Java, and .NET.

2. **Azure Container Registry stores images as OCI artifacts**, which means you can store more than just container images. Helm charts, WASM modules, Singularity containers, and arbitrary files can all be pushed to ACR using the ORAS (OCI Registry as Storage) CLI. This makes ACR a universal artifact repository, not just a Docker registry.

3. **Pulling a 1 GB image from ACR in the same Azure region takes approximately 3-6 seconds** thanks to direct backbone connectivity. Pulling the same image from Docker Hub (which serves from Cloudflare's CDN) typically takes 15-30 seconds due to the additional network hops. For a VMSS with 50 instances scaling out simultaneously, this difference means the fleet is ready in 6 seconds with ACR versus 30 seconds with Docker Hub.

4. **ACR supports anonymous pull** (since 2021) on any SKU. When enabled, anyone can pull images without authentication. This is useful for open-source projects that want to distribute images publicly while still using ACR for push authentication and management. However, anonymous pull is disabled by default and should only be enabled intentionally.

---

## Common Mistakes

| Mistake | Why It Happens | How to Fix It |
| :--- | :--- | :--- |
| Using the admin account for CI/CD pipelines | It is the first authentication method shown in quickstarts | Use service principals with AcrPush role for CI/CD, or OIDC federation for GitHub Actions. |
| Not cleaning up old images | There is no built-in retention policy enabled by default | Create an ACR Task with `acr purge` on a schedule. Delete untagged manifests weekly and old tagged images monthly. |
| Using `:latest` tag in production deployments | It seems like "latest" means "newest and best" | `:latest` is mutable---it can point to different images at different times. Use immutable tags (semantic version or Git SHA) for production. |
| Running Premium SKU for dev/test registries | Teams copy production configuration | Use Basic ($5/month) for dev/test. Premium ($50+/month) is only needed for geo-replication, Private Link, or content trust. |
| Pulling images from a different region than compute | The registry is in East US but compute is in West Europe | Use geo-replication (Premium) or create separate registries per region. Cross-region pull adds latency and egress costs. |
| Not enabling vulnerability scanning | Teams assume images are secure because they built them | Enable Microsoft Defender for Containers, which automatically scans images pushed to ACR and reports vulnerabilities. |
| Hardcoding registry URLs in Kubernetes manifests | It works today, so why abstract it? | Use a variable or Helm value for the registry URL. This lets you switch registries (e.g., from dev ACR to prod ACR) without modifying manifests. |
| Granting AcrPush when only AcrPull is needed | AcrPull seems "incomplete" | Follow least privilege. Build agents need AcrPush. Runtime workloads (AKS, ACI, Container Apps) only need AcrPull. |

---

## Quiz

<details>
<summary>1. What is the difference between an ACR admin account and a service principal for ACR authentication?</summary>

The admin account provides a single shared username/password with full push/pull/delete access to the entire registry. There is no granularity---anyone with the password has the same access. There is no audit trail of who did what. A service principal is a dedicated identity with an RBAC role assignment. You can grant AcrPull (read-only), AcrPush (read/write), or AcrDelete (delete) access. Each service principal has its own credentials and can be independently audited and revoked. Service principals support certificate-based authentication, which is more secure than passwords.
</details>

<details>
<summary>2. How does ACR geo-replication reduce image pull latency for global deployments?</summary>

When you enable geo-replication, ACR creates read-only replicas of your registry in additional Azure regions. Images pushed to the primary region are automatically replicated to all secondary regions. When a client (like an AKS cluster in West Europe) pulls an image, ACR routes the pull to the nearest replica, which is the West Europe replica in this case. The image data travels within the Azure backbone from the local replica instead of crossing the ocean from the primary region. This reduces pull time from 15-30 seconds to 3-6 seconds for large images.
</details>

<details>
<summary>3. You have an AKS cluster that needs to pull images from ACR. What is the most secure authentication method?</summary>

Use `az aks update --attach-acr` which creates a Managed Identity-based role assignment. This grants the AKS kubelet identity the AcrPull role on the ACR. No credentials are stored in Kubernetes secrets, no passwords to rotate, and the access is scoped to pull-only. The AKS nodes automatically authenticate using the managed identity when pulling images. This is a single command and is the recommended approach by Microsoft. Avoid creating Kubernetes imagePullSecrets with admin credentials or service principal secrets.
</details>

<details>
<summary>4. What is the purpose of ACR Tasks base image triggers?</summary>

Base image triggers automatically rebuild your application images when the base image they depend on is updated. For example, if your Dockerfile starts with `FROM node:18-alpine` and the `node:18-alpine` image receives a security patch, ACR Tasks detects the base image change and triggers a rebuild of your application image using the updated base. This ensures your application images always include the latest security patches from the base image without manual intervention. Without this, your images would contain the vulnerable base image until someone manually triggers a rebuild.
</details>

<details>
<summary>5. Why should you avoid using the `:latest` tag in production Kubernetes deployments?</summary>

The `:latest` tag is mutable---it is a floating pointer that gets reassigned to whichever image was most recently pushed without an explicit tag. In production, this causes three problems: (1) Non-reproducibility: you cannot determine exactly which image version is running. (2) Unpredictable updates: if Kubernetes re-pulls the image (node restart, scaling event), it might get a different version than what was originally deployed. (3) Rollback difficulty: you cannot roll back to `:latest` because it now points to the version you are trying to roll back from. Use immutable tags like semantic versions (v1.2.3) or Git SHAs (sha-a1b2c3d) instead.
</details>

<details>
<summary>6. What additional capabilities does ACR Premium provide over Standard, and when are they worth the extra cost?</summary>

Premium adds geo-replication, Private Link, content trust (image signing), customer-managed encryption keys, and higher throughput limits. Geo-replication is worth it when you run workloads in multiple Azure regions and want fast local pulls. Private Link is essential when your security policy requires no public endpoints. Content trust is needed when you must cryptographically verify image integrity (common in regulated industries). The extra cost ($50/month vs $20/month, plus per-replica costs) is justified when you have multi-region production deployments or strict security/compliance requirements. For single-region or dev/test, Standard is sufficient.
</details>

---

## Hands-On Exercise: ACR Setup, Build, and Image Management

In this exercise, you will create an ACR, build an image using ACR Tasks (no local Docker needed), manage tags, and set up an automated purge.

**Prerequisites**: Azure CLI installed and authenticated.

### Task 1: Create an ACR

```bash
RG="kubedojo-acr-lab"
LOCATION="eastus2"
ACR_NAME="kubedojolab$(openssl rand -hex 4)"

az group create --name "$RG" --location "$LOCATION"

az acr create \
  --resource-group "$RG" \
  --name "$ACR_NAME" \
  --sku Standard \
  --location "$LOCATION"

echo "ACR Login Server: ${ACR_NAME}.azurecr.io"
```

<details>
<summary>Verify Task 1</summary>

```bash
az acr show -n "$ACR_NAME" --query '{Name:name, SKU:sku.name, LoginServer:loginServer}' -o table
```
</details>

### Task 2: Build an Image with ACR Tasks (No Local Docker)

```bash
# Create a simple app
mkdir -p /tmp/acr-lab && cd /tmp/acr-lab

cat > Dockerfile << 'EOF'
FROM nginx:alpine
COPY index.html /usr/share/nginx/html/index.html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
EOF

cat > index.html << 'EOF'
<!DOCTYPE html>
<html><body>
<h1>Built by ACR Tasks</h1>
<p>No local Docker daemon needed.</p>
</body></html>
EOF

# Build the image in the cloud
az acr build \
  --registry "$ACR_NAME" \
  --image webapp:v1.0.0 \
  --file Dockerfile \
  /tmp/acr-lab
```

<details>
<summary>Verify Task 2</summary>

```bash
az acr repository show-tags -n "$ACR_NAME" --repository webapp -o table
```

You should see the `v1.0.0` tag.
</details>

### Task 3: Push Multiple Tagged Versions

```bash
# Modify the app and build v1.1.0
cat > /tmp/acr-lab/index.html << 'EOF'
<!DOCTYPE html>
<html><body>
<h1>Version 1.1.0</h1>
<p>New feature: improved layout</p>
</body></html>
EOF

az acr build --registry "$ACR_NAME" --image webapp:v1.1.0 /tmp/acr-lab

# Build a third version
cat > /tmp/acr-lab/index.html << 'EOF'
<!DOCTYPE html>
<html><body>
<h1>Version 1.2.0</h1>
<p>Bug fix release</p>
</body></html>
EOF

az acr build --registry "$ACR_NAME" --image webapp:v1.2.0 /tmp/acr-lab
az acr build --registry "$ACR_NAME" --image webapp:latest /tmp/acr-lab

# List all tags
az acr repository show-tags -n "$ACR_NAME" --repository webapp --orderby time_desc -o table
```

<details>
<summary>Verify Task 3</summary>

You should see four tags: v1.0.0, v1.1.0, v1.2.0, and latest.
</details>

### Task 4: Inspect Image Metadata

```bash
# Show detailed manifest information
az acr repository show-manifests \
  --name "$ACR_NAME" \
  --repository webapp \
  --detail \
  --query '[].{Digest:digest, Tags:tags, Created:createdTime, Size:imageSize}' -o table

# Show repository metadata
az acr repository show --name "$ACR_NAME" --repository webapp -o json
```

<details>
<summary>Verify Task 4</summary>

You should see manifest digests, tags, creation timestamps, and image sizes for all pushed versions.
</details>

### Task 5: Create an Automated Purge Task

```bash
# Create a purge task that removes untagged images older than 7 days
az acr task create \
  --registry "$ACR_NAME" \
  --name purge-untagged \
  --cmd "acr purge --filter 'webapp:.*' --ago 0d --untagged --dry-run" \
  --context /dev/null \
  --schedule "0 4 * * *"

# Run it manually to see what would be purged (dry run)
az acr task run --registry "$ACR_NAME" --name purge-untagged
```

<details>
<summary>Verify Task 5</summary>

```bash
az acr task list --registry "$ACR_NAME" \
  --query '[].{Name:name, Status:provisioningState, Schedule:trigger.timerTriggers[0].schedule}' -o table
```

You should see the purge-untagged task with its cron schedule.
</details>

### Cleanup

```bash
az group delete --name "$RG" --yes --no-wait
rm -rf /tmp/acr-lab
```

### Success Criteria

- [ ] ACR created with Standard SKU
- [ ] Image built using ACR Tasks (no local Docker)
- [ ] Multiple image versions pushed with semantic version tags
- [ ] Image manifests inspected for metadata
- [ ] Automated purge task created and tested with dry-run

---

## Next Module

[Module 3.7: ACI & Container Apps](module-3.7-aci-aca/) --- Learn the serverless container options in Azure, from quick-and-simple Azure Container Instances to the fully-featured Azure Container Apps with KEDA auto-scaling and Dapr integration.
