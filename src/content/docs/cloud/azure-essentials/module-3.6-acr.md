---
title: "Module 3.6: Azure Container Registry (ACR)"
slug: cloud/azure-essentials/module-3.6-acr
sidebar:
  order: 7
---

## What You'll Be Able to Do

After completing this module, you will be able to:

- **Design** a scalable Azure Container Registry architecture utilizing geo-replication and Private Link for secure, global deployments.
- **Implement** automated container image builds and patching pipelines using ACR Tasks to ensure base image security.
- **Evaluate** least-privilege authentication mechanisms for ACR access across CI/CD pipelines, virtual machines, and Kubernetes clusters.
- **Diagnose** image bloat and lifecycle issues by configuring automated purge policies and immutable tags.
- **Compare** the Basic, Standard, and Premium SKUs to select the most cost-effective registry tier for specific enterprise workloads.

## Why This Module Matters

Teams that rely on a shared public registry can discover at the worst possible time that pull limits or registry availability are constraining their CI/CD pipeline. Docker Hub had heavily rate-limited their pulls: the free tier allows only [100 pulls per 6 hours for anonymous users and 200 for authenticated users](https://www.docker.com/blog/revisiting-docker-hub-policies-prioritizing-developer-experience/). With 40 microservices, 3 environments, and frequent node scaling events, they were regularly blowing past the limit. 

Registry bottlenecks can delay fixes, slow engineering teams, and create real operational and business costs. They learned the hard way that infrastructure dependencies must be owned and controlled.

Container images are the atoms of modern application deployment. Every container you run—whether on Azure Kubernetes Service (AKS), Azure Container Apps, or Azure Container Instances (ACI)—starts with pulling an image from a registry. If your registry is slow, unreliable, or insecure, your entire deployment pipeline suffers. [Azure Container Registry is a fully managed, highly available, private Docker registry that integrates deeply with Azure's identity system.](https://learn.microsoft.com/en-us/azure/container-registry/container-registry-intro) It removes dependence on third-party public registry limits, can be deployed close to Azure workloads, and integrates with Azure services for builds, optional vulnerability assessment, and geo-replication. In this module, you will build a production-ready container registry strategy from the ground up.

---

## ACR SKUs: Choosing the Right Tier

Azure Container Registry is designed to scale with your organization. To support everything from individual developers to global enterprises, ACR comes in three distinct SKUs (Stock Keeping Units). These SKUs dictate your performance limits, storage capacity, and access to advanced enterprise features.

| Feature | Basic | Standard | Premium |
| :--- | :--- | :--- | :--- |
| **Storage** | 10 GiB | 100 GiB | 500 GiB included (see current Microsoft limits for maximum capacity) |
| **Read throughput** | Lower | Higher | Highest |
| **Write throughput** | Lower | Higher | Highest |
| **Webhooks** | 2 | 10 | 500 |
| **Geo-replication** | No | No | Yes |
| **Private Link** | No | No | Yes |
| **Content Trust** | No | No | Yes (image signing) |
| **Customer-managed keys** | No | No | Yes |
| **Approximate cost** | Varies by region and agreement | Varies by region and agreement | Varies by region, agreement, and replica count |

When designing your architecture, you must balance cost against capability. The **Basic** tier is excellent for individual learning and sandboxed development environments, but its strict rate limits (1,000 ReadOps/min) can easily be overwhelmed by a moderately sized Kubernetes cluster pulling images during a scale-out event. 

[For most production workloads, **Standard** is the recommended baseline. It provides ten times the storage and significantly higher throughput. However, if your security team mandates that all traffic must traverse private networks, or if your application is deployed across multiple global regions, you must adopt the **Premium** tier to unlock Private Link and Geo-replication.](https://learn.microsoft.com/en-us/azure/container-registry/container-registry-skus?source=recommendations)

Microsoft documents that you can change an ACR SKU without registry downtime, subject to the limits and feature constraints of the target tier.

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

Every registry you create is assigned a unique **login server** URL (for example, `kubedojoacr.azurecr.io`). This fully qualified domain name is the address your Docker CLI and Kubernetes clusters will use to communicate with the registry API.

---

## Authentication: Three Methods, One Recommendation

Securing access to your container images is arguably the most critical operational task in this module. Container registries are frequent targets for attackers because a compromised registry allows a malicious actor to inject cryptocurrency miners or backdoors directly into your production workloads. ACR supports three authentication methods, each with vastly different security profiles.

### 1. The Admin Account (Avoid in Production)

When you first create a registry, you have the option to enable an admin account. This generates a static username and a set of passwords. 

```bash
# Enable admin (NOT recommended for production)
az acr update --name kubedojoacr --admin-enabled true

# Get credentials
az acr credential show --name kubedojoacr -o table

# Login with admin credentials
az acr login --name kubedojoacr
```

While convenient for a five-minute proof of concept, the admin account violates almost every principle of modern security. The credentials are shared, meaning you cannot audit which developer or system performed a specific action. The account has full push and pull access across the entire registry, violating the principle of least privilege. Furthermore, rotating the password requires orchestrating an update across every single system that relies on it, often leading to production downtime.

### 2. Service Principals

[A Service Principal is an identity created for use with applications, hosted services, and automated tools to access Azure resources. Unlike the admin account, you can create dozens of service principals and grant each one a highly specific Role-Based Access Control (RBAC) assignment.](https://learn.microsoft.com/en-us/azure/container-registry/container-registry-auth-service-principal)

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

Service principals are ideal for external CI/CD pipelines (like GitLab CI or CircleCI) that need to push images into Azure but live outside of the Azure ecosystem.

### 3. Managed Identity (The Enterprise Standard)

For any workload running inside Azure, Managed Identities represent the gold standard for authentication. [A Managed Identity is effectively a service principal that the Azure platform manages on your behalf. There are no passwords to generate, store, or rotate.](https://learn.microsoft.com/en-us/azure/container-registry/container-registry-authentication-managed-identity) The Azure control plane handles all credential exchanges seamlessly under the hood.

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

> **Stop and think**: If a compromised CI/CD pipeline has an ACR admin password, what is the blast radius? How does that compare to a compromised pipeline with an AcrPush service principal limited to a specific repository?

To help you choose the right authentication model, refer to this architectural decision tree:

```mermaid
graph TD
    A[Is the consumer an Azure resource? <br/> AKS, ACI, Container Apps, VM]
    A -- YES --> B[Managed Identity + AcrPull role]
    A -- NO --> C[Is it a CI/CD pipeline?]
    C -- GitHub Actions --> D[OIDC federated credential <br/> no secrets]
    C -- Azure DevOps --> E[Service Connection <br/> Workload Identity]
    C -- Other --> F[Service Principal with certificate <br/> not secret <br/> Set minimum role]
```

Once authentication is established, interacting with the registry uses standard Docker CLI commands, heavily augmented by the Azure CLI to handle the credential exchange smoothly.

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

## ACR Tasks: Serverless Container Builds

Historically, building container images required a dedicated build server running the Docker daemon. This approach is fraught with maintenance overhead, security risks (privileged containers), and scaling bottlenecks. ACR Tasks completely revolutionizes this by allowing you to offload the build execution directly to Azure's managed compute infrastructure.

### The Quick Build

With a single command, you can [stream your local directory context to Azure, where a managed virtual machine provisions itself, executes your Dockerfile, pushes the resulting image directly into your registry, and then terminates](https://learn.microsoft.com/en-us/azure/container-registry/container-registry-tasks-overview).

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

### Base Image Triggers and Automated Patching

While manual builds are excellent for local development, production systems require automation. [ACR Tasks can monitor upstream base images (like `ubuntu:22.04` or `node:18-alpine`) and automatically trigger a rebuild of your application whenever the base image maintainer pushes a security patch.](https://learn.microsoft.com/en-us/azure/container-registry/container-registry-tasks-overview)

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

**Example**: Base-image triggers can automatically rebuild dependent images when an upstream base image changes, reducing manual patching work during a security event.

---

## Global Distribution with Geo-Replication

When you design distributed systems, physics is your ultimate constraint. The speed of light dictates that transferring gigabytes of image data across oceans will induce significant latency. If your primary registry is in East US, but your AKS cluster is scaling out in West Europe, every pod startup is penalized by transatlantic data transfer speeds.

Furthermore, cross-region bandwidth is not free. Pulling images across regional boundaries incurs heavy egress charges on your monthly Azure bill.

Geo-replication solves this by allowing a single logical registry to exist physically in multiple Azure regions simultaneously. Here is the architectural flow:

```mermaid
flowchart LR
    subgraph Premium_ACR[ACR: kubedojoacr Premium]
        direction LR
        A[East US 2<br/>primary]
        B[West Europe<br/>replica]
        C[SE Asia<br/>replica]

        A -- Sync --> B
        A -- Sync --> C
    end

    Client1[Push Client] -->|Push here| A
    Client2[Pull Client US] -->|Pull here| A
    Client3[Pull Client EU] -->|Pull here| B
    Client4[Pull Client Asia] -->|Pull here| C

    classDef acr fill:#0072C6,stroke:#fff,stroke-width:2px,color:#fff;
    class A,B,C acr;
```

When you push an image to your registry, [Azure automatically replicates the underlying storage blobs asynchronously to all configured regions. When a client requests an image, Azure Traffic Manager intercepts the DNS request and seamlessly routes the client to the closest regional replica.](https://learn.microsoft.com/en-us/azure/container-registry/container-registry-geo-replication)

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

**Example**: Without in-region registry access, cross-region pulls can add startup latency and data-transfer costs; geo-replication reduces both for multi-region deployments.

---

## Network Security and Private Link

By default, Azure Container Registry exposes a public endpoint. While authenticated via Azure Active Directory, the registry is technically reachable from anywhere on the internet. In highly regulated industries like healthcare or finance, data exfiltration policies mandate that Platform-as-a-Service (PaaS) resources must not possess public IP addresses.

[Azure Private Link allows you to project your ACR directly into your Virtual Network (VNet). The registry receives a private IP address (e.g., `10.0.5.10`), and all traffic between your virtual machines or Kubernetes nodes and the registry never leaves the Microsoft backbone network.](https://learn.microsoft.com/en-us/azure/container-registry/container-registry-private-link?view=azureml-api-2)

> **Pause and predict**: If you enable Private Link for an ACR but forget to link the Private DNS Zone to your AKS Virtual Network, what error message will the kubelet throw when trying to pull an image?

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

Once Private Link is established and the DNS zone is correctly linked to your VNet, any request to `kubedojoacr.azurecr.io` from within that VNet will transparently resolve to the private IP address instead of the public endpoint.

---

## Image Management Best Practices

Container registries are notoriously prone to storage bloat. Every time a developer merges a pull request, CI systems typically build and push a new image. Over time, terabytes of outdated, unused images accumulate, driving up storage costs and obscuring the operational state of the registry.

### Tagging Strategy

Implementing a robust tagging strategy is your first line of defense against chaos. You must absolutely [avoid deploying the `:latest` tag into production, as it is a floating pointer that mutates unpredictably](https://learn.microsoft.com/en-us/azure/container-registry/container-registry-image-tag-version).

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

### Automated Cleanup and Retention

When you overwrite an existing tag (like pushing a new build to `myapp:dev`), the old image data isn't deleted. Instead, the tag pointer moves, [leaving behind an "untagged" or orphaned manifest. These orphaned layers consume expensive storage space.](https://learn.microsoft.com/en-us/azure/container-registry/container-registry-concepts) 

You should utilize ACR Tasks to schedule a recurring administrative command that forcefully purges old tags and orphaned manifests.

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

[By scheduling `acr purge`, you ensure that your registry remains lean and cost-effective automatically, without manual intervention from the operations team.](https://learn.microsoft.com/en-us/azure/container-registry/container-registry-auto-purge)

---

## Did You Know?

1. **ACR supports preview Cloud Native Buildpacks builds** via the `az acr pack build` command, which can build some applications from source without a Dockerfile.
2. **Azure Container Registry can store OCI artifacts in addition to container images**, including Helm charts and other artifact types supported by OCI tooling.
3. **In-region ACR pulls are often noticeably faster than pulling the same image from a public registry over the internet**, which becomes more visible during large scale-out events.
4. **ACR supports anonymous pull** on Standard and Premium registries. When enabled, anyone can pull images without authentication, so it should be used intentionally for public artifacts. Anonymous pull is disabled by default.

---

## Common Mistakes

| Mistake | Why It Happens | How to Fix It |
| :--- | :--- | :--- |
| Using the admin account for CI/CD pipelines | It is the first authentication method shown in quickstarts | Use service principals with AcrPush role for CI/CD, or OIDC federation for GitHub Actions. |
| Not cleaning up old images | [There is no built-in retention policy enabled by default](https://learn.microsoft.com/en-us/azure/container-registry/container-registry-retention-policy) | Create an ACR Task with `acr purge` on a schedule. Delete untagged manifests weekly and old tagged images monthly. |
| Using `:latest` tag in production deployments | It seems like "latest" means "newest and best" | `:latest` is mutable---it can point to different images at different times. Use immutable tags (semantic version or Git SHA) for production. |
| Running Premium SKU for dev/test registries | Teams copy production configuration | Use Basic ($5/month) for dev/test. Premium ($50+/month) is only needed for geo-replication, Private Link, or content trust. |
| Pulling images from a different region than compute | The registry is in East US but compute is in West Europe | Use geo-replication (Premium) or create separate registries per region. Cross-region pull adds latency and egress costs. |
| Not enabling vulnerability scanning | Teams assume images are secure because they built them | [Enable Microsoft Defender for Containers, which automatically scans images pushed to ACR and reports vulnerabilities.](https://learn.microsoft.com/en-us/azure/container-registry/scan-images-defender) |
| Hardcoding registry URLs in Kubernetes manifests | It works today, so why abstract it? | Use a variable or Helm value for the registry URL. This lets you switch registries (e.g., from dev ACR to prod ACR) without modifying manifests. |
| Granting AcrPush when only AcrPull is needed | AcrPull seems "incomplete" | Follow least privilege. Build agents need AcrPush. Runtime workloads (AKS, ACI, Container Apps) only need AcrPull. |

---

## Quiz

<details>
<summary>1. You are designing an automated CI/CD pipeline using GitLab that pushes container images to ACR. A junior engineer suggests enabling the ACR admin account for the pipeline to use. Why should you reject this proposal and what should you implement instead?</summary>

You should reject the use of the admin account because it provides unfettered, full administrative access (push, pull, delete) to the entire registry using a single shared credential, which completely violates the principle of least privilege and destroys auditability. If that CI/CD pipeline is compromised, the attacker gains full control over your entire container registry. Instead, you should provision a dedicated Service Principal bound specifically to the `AcrPush` RBAC role. This approach ensures the pipeline only has the exact permissions required to upload images, allows for independent credential rotation, and provides clear audit trails in Azure Monitor without exposing other repositories to risk.
</details>

<details>
<summary>2. Your company just expanded its e-commerce platform to serve users in both North America (East US) and Europe (West Europe). The application teams report that pods in the European AKS cluster are taking over 30 seconds to start during traffic spikes. You discover they are pulling images from a single Standard tier ACR in East US. How do you resolve this architectural bottleneck?</summary>

You must upgrade the Azure Container Registry from the Standard tier to the Premium tier to unlock the geo-replication feature. Once upgraded, you can provision a secondary read-only replica of the registry in the West Europe region. When developers push new images to East US, Azure will automatically and asynchronously sync the blob storage to the West Europe replica over the Microsoft backbone. Consequently, when the European AKS cluster scales out, Azure Traffic Manager will intercept the image pull request and route it locally, dropping pod startup times from 30+ seconds to just a few seconds and eliminating expensive cross-region bandwidth egress costs.
</details>

<details>
<summary>3. You have an AKS cluster that needs to pull images from ACR. What is the most secure authentication method?</summary>

You must utilize Managed Identities by executing `az aks update --attach-acr`. This operational command configures the AKS kubelet identity with a system-managed Service Principal and automatically assigns it the `AcrPull` RBAC role scoped explicitly to your registry. This architectural pattern represents the pinnacle of security because zero static credentials are ever generated, stored in Kubernetes secrets, or transmitted over the network. The Azure platform autonomously handles the lifecycle, secure exchange, and rotation of the underlying tokens, eliminating the risk of credential leakage entirely.
</details>

<details>
<summary>4. Your microservices rely on a public Node.js Alpine base image. A critical zero-day vulnerability is announced in Alpine Linux, and the Node.js maintainers push a patched base image to Docker Hub. How can you ensure your microservices automatically inherit this security patch without relying on your central Jenkins CI pipeline?</summary>

You should implement ACR Tasks and configure base image triggers for your application repositories. When enabled, ACR Tasks acts as a serverless supply chain security mechanism that continuously monitors the upstream base images (like `node:18-alpine`) declared in your Dockerfiles. The moment the patched base image is pushed to Docker Hub, ACR detects the change and instantaneously spins up ephemeral compute to rebuild your application images automatically. This guarantees your deployments are rapidly immunized against zero-day vulnerabilities in underlying layers, drastically reducing your exposure window without requiring any manual engineering intervention or tying up CI/CD build agents.
</details>

<details>
<summary>5. A developer on your team configures their Kubernetes Deployment manifest to use the `webapp:latest` image tag. During a routine node upgrade, several pods are rescheduled, but they suddenly start failing crash loop backoffs. Explain the operational danger of this tagging strategy and how it caused the outage.</summary>

Deploying the `:latest` tag introduces catastrophic non-determinism into production environments because it acts as a highly mutable, floating pointer rather than a fixed artifact. During the node upgrade, when the kubelet rescheduled the pods, it reached out to the registry and blindly pulled whatever newly built image was currently tagged as `:latest`. The team likely pushed a breaking, untested change to `:latest` in the background, meaning the newly scheduled pods received a completely different application version than the pods running on the older nodes. To prevent this split-brain behavior and ensure reliable rollbacks, you should use immutable semantic version tags (e.g., `v1.2.4`) or exact Git SHA commit hashes in your production manifests.
</details>

<details>
<summary>6. Your organization is migrating a highly regulated healthcare workload to Azure. The security compliance team dictates that the container registry must not be accessible via any public IP address and must encrypt all data at rest using keys managed by the organization, not Microsoft. Which ACR SKU must you choose and why?</summary>

You are strictly required to choose the Premium SKU for your Azure Container Registry. While the Standard tier provides adequate storage and throughput for many workloads, it cannot satisfy strict network isolation or cryptographic compliance mandates. Only the Premium tier unlocks the Azure Private Link feature, which completely disables public internet access and projects the registry directly into your Virtual Network using a private IP address. Furthermore, the Premium tier is the only SKU that supports Customer-Managed Encryption Keys (CMK), allowing your security team to retain direct control over the keys used to encrypt the underlying image blob storage.
</details>

<details>
<summary>7. You are designing a multi-region deployment spanning East US and West Europe. Your AKS clusters in West Europe are experiencing elevated image pull latencies when fetching from your Standard SKU ACR located in East US. Diagnose the root cause and implement a solution.</summary>

The root cause of the latency is the physical limitation of transmitting massive gigabyte-scale container layers across the transatlantic network link during pod scaling events. Because the registry is running the Standard SKU, it physically resides only in the East US datacenter. To resolve this, you must upgrade the registry to the Premium SKU dynamically (`az acr update --sku Premium`) and provision a Geo-replication replica in West Europe (`az acr replication create --location westeurope`). This ensures the West Europe AKS nodes pull directly from localized storage, drastically reducing startup latency and eliminating cross-region egress bandwidth costs.
</details>

<details>
<summary>8. A security audit reveals that your development team has been using the `:latest` tag for all production deployments. Evaluate the risks associated with this practice and design a remediation strategy.</summary>

The primary risk is a severe lack of operational determinism. Because `:latest` is continuously overwritten, horizontal pod autoscaling events may inadvertently deploy a mix of different application versions simultaneously, leading to split-brain application behavior and corrupted data schemas. To remediate this, you must implement a strict semantic versioning policy (e.g., `v1.2.4`) or inject the unique Git SHA commit hash directly into the image tag during the CI pipeline build phase. Additionally, you should execute an `az acr repository update --write-enabled false` command against specific production tags to render them cryptographically immutable, preventing any accidental overwrites or malicious tampering by compromised pipelines.
</details>

---

## Hands-On Exercise: ACR Setup, Build, and Image Management

In this comprehensive exercise, you will provision an Azure Container Registry from scratch, utilize the serverless capabilities of ACR Tasks to build an image without relying on a local Docker daemon, manage complex tagging strategies, and implement a sophisticated automated storage purge policy.

**Prerequisites**: Ensure you have the Azure CLI installed locally and are actively authenticated to your Azure subscription.

### Task 1: Create an ACR

We will begin by scaffolding out the resource group and provisioning a Standard tier registry to balance cost and capability.

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

In this task, we will simulate a scenario where a developer lacks local administrative privileges to run the Docker daemon. We will stream the build context directly to Azure's managed compute.

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

You should see the `v1.0.0` tag successfully registered.
</details>

### Task 3: Push Multiple Tagged Versions

Now we will simulate a standard software development lifecycle by patching our HTML application and pushing subsequent semantic versions.

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

You should observe exactly four tags chronologically ordered: v1.0.0, v1.1.0, v1.2.0, and latest.
</details>

### Task 4: Inspect Image Metadata

Understanding how to query the underlying cryptographic signatures and storage metrics of your images is essential for compliance auditing.

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

You should see complex JSON output detailing the manifest digests (SHA-256 hashes), mapping arrays for tags, precise creation timestamps, and aggregated image sizes for all pushed versions.
</details>

### Task 5: Create an Automated Purge Task

To prevent uncontrolled storage bloat, we will provision a serverless cron job inside ACR that executes a deep cleanup operation against orphaned layers.

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

You should see the `purge-untagged` task successfully provisioned with its corresponding cron schedule configuration attached.
</details>

### Cleanup

Always destroy your cloud infrastructure after completing training modules to halt unexpected billing accruals.

```bash
az group delete --name "$RG" --yes --no-wait
rm -rf /tmp/acr-lab
```

### Success Criteria Checklist

- [ ] ACR successfully provisioned leveraging the Standard SKU architecture.
- [ ] Container image cleanly built utilizing the remote compute of ACR Tasks (no local Docker dependency).
- [ ] Multiple progressive image variants pushed and correctly labeled with semantic version tags.
- [ ] Deep image manifests successfully queried and inspected for precise metadata insights.
- [ ] Automated serverless purge task actively deployed, scheduled, and validated via a dry-run execution.

---

## Next Module

[Module 3.7: ACI & Container Apps](../module-3.7-aci-aca/) — Take your newly secured container images and deploy them using the powerful serverless container orchestration options available in Azure. You will transition from quick-and-simple execution environments in Azure Container Instances to building massively scalable microservice fleets in Azure Container Apps, fully integrated with KEDA auto-scaling and Dapr runtime semantics.

## Sources

- [azure.microsoft.com: container registry](https://azure.microsoft.com/en-us/pricing/details/container-registry/) — General lesson point for an illustrative rewrite.
- [learn.microsoft.com: container registry geo replication](https://learn.microsoft.com/en-us/azure/container-registry/container-registry-geo-replication) — General lesson point for an illustrative rewrite.
- [Azure Container Registry Documentation](https://learn.microsoft.com/en-us/azure/container-registry/) — Canonical Microsoft entry point for ACR concepts, tasks, networking, and operations.
- [Authenticate with Azure Container Registry](https://learn.microsoft.com/en-us/azure/container-registry/container-registry-authentication) — Primary overview of admin account, service principal, and managed identity authentication options.
