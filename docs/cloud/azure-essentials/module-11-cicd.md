# CI/CD: Azure DevOps & GitHub Actions
**Complexity**: [MEDIUM] | **Time to Complete**: 2h | **Prerequisites**: Module 6 (ACR), Module 7 (Container Apps), Module 1 (Entra ID)

## Why This Module Matters

In February 2023, a major CI/CD platform disclosed that an attacker had gained access to customer repositories by compromising a shared runner environment. The attacker injected malicious code into the build process, which exfiltrated environment variables---including service principal credentials that customers had stored as pipeline secrets. Over 35,000 repositories were potentially affected. Several Azure production environments were compromised because teams had stored long-lived service principal secrets in their pipeline variables, and those secrets had full Contributor access to production subscriptions.

This incident crystallized a lesson the industry had been learning the hard way: **the CI/CD pipeline is the most privileged part of your infrastructure, and it deserves the strongest security posture.** Your pipeline has the power to deploy code to production, access secrets, and modify infrastructure. If an attacker compromises your pipeline, they own your production environment. Static credentials stored in pipeline variables are a ticking time bomb---they do not expire, they are visible to anyone with pipeline admin access, and they are one SSRF vulnerability away from being exfiltrated.

In this module, you will learn how to build secure CI/CD pipelines targeting Azure using two platforms: Azure DevOps Pipelines and GitHub Actions. You will understand YAML pipeline syntax, how Service Connections and OIDC federation eliminate static credentials, and how to deploy to Azure Container Registry and Container Apps. By the end, you will build a complete GitHub Actions pipeline that authenticates to Azure using OIDC (zero secrets), builds a container image, pushes it to ACR, and deploys it to Container Apps.

---

## Azure DevOps Pipelines

Azure DevOps is Microsoft's integrated DevOps platform providing source control (Azure Repos), CI/CD (Azure Pipelines), project management (Boards), artifact management (Artifacts), and testing (Test Plans).

### Pipeline Basics

Azure Pipelines uses YAML files (typically `azure-pipelines.yml`) to define build and deployment workflows. A pipeline consists of **stages**, **jobs**, and **steps**.

```text
    Pipeline Structure:

    Pipeline
    ├── Stage: Build
    │   └── Job: BuildAndTest
    │       ├── Step: Checkout code
    │       ├── Step: Run tests
    │       ├── Step: Build Docker image
    │       └── Step: Push to ACR
    │
    └── Stage: Deploy
        ├── Job: DeployStaging
        │   ├── Step: Deploy to staging
        │   └── Step: Run smoke tests
        │
        └── Job: DeployProduction
            ├── Step: Manual approval gate
            └── Step: Deploy to production
```

```yaml
# azure-pipelines.yml
trigger:
  branches:
    include:
      - main
  paths:
    exclude:
      - '**/*.md'
      - '.github/**'

pool:
  vmImage: 'ubuntu-latest'

variables:
  acrName: 'myacr'
  imageName: 'myapp'
  tag: '$(Build.BuildId)'

stages:
  - stage: Build
    displayName: 'Build and Push Image'
    jobs:
      - job: BuildJob
        steps:
          - task: Docker@2
            displayName: 'Build and Push to ACR'
            inputs:
              containerRegistry: 'acr-service-connection'
              repository: '$(imageName)'
              command: 'buildAndPush'
              Dockerfile: '**/Dockerfile'
              tags: |
                $(tag)
                latest

  - stage: DeployStaging
    displayName: 'Deploy to Staging'
    dependsOn: Build
    condition: succeeded()
    jobs:
      - deployment: DeployStagingJob
        environment: 'staging'
        strategy:
          runOnce:
            deploy:
              steps:
                - task: AzureContainerApps@1
                  displayName: 'Deploy to Container Apps'
                  inputs:
                    azureSubscription: 'azure-service-connection'
                    containerAppName: 'myapp-staging'
                    resourceGroup: 'myRG'
                    imageToDeploy: '$(acrName).azurecr.io/$(imageName):$(tag)'

  - stage: DeployProduction
    displayName: 'Deploy to Production'
    dependsOn: DeployStaging
    condition: succeeded()
    jobs:
      - deployment: DeployProdJob
        environment: 'production'  # Requires manual approval configured on the environment
        strategy:
          runOnce:
            deploy:
              steps:
                - task: AzureContainerApps@1
                  inputs:
                    azureSubscription: 'azure-service-connection'
                    containerAppName: 'myapp-production'
                    resourceGroup: 'myRG-prod'
                    imageToDeploy: '$(acrName).azurecr.io/$(imageName):$(tag)'
```

### Service Connections (OIDC/Workload Identity Federation)

Service Connections are how Azure DevOps authenticates with Azure. The modern approach uses **Workload Identity Federation** (OIDC), which eliminates client secrets entirely.

```text
    Legacy Approach (Service Principal + Secret):
    ┌──────────────────┐    Client Secret     ┌─────────────┐
    │  Azure DevOps    │ ──────────────────── │  Entra ID   │
    │  Pipeline        │    (stored in ADO)    │             │
    └──────────────────┘                       └──────┬──────┘
                                                      │ Access Token
                                                      ▼
                                               ┌─────────────┐
                                               │  Azure       │
                                               │  Resources   │
                                               └─────────────┘
    Problem: Secret can leak, must be rotated, visible in pipeline settings.

    Modern Approach (Workload Identity Federation / OIDC):
    ┌──────────────────┐    OIDC Token         ┌─────────────┐
    │  Azure DevOps    │ ──────────────────── │  Entra ID   │
    │  Pipeline        │    (short-lived,      │  (trusts ADO │
    │                  │     auto-generated)   │   as issuer) │
    └──────────────────┘                       └──────┬──────┘
                                                      │ Access Token
                                                      ▼
                                               ┌─────────────┐
                                               │  Azure       │
                                               │  Resources   │
                                               └─────────────┘
    No secrets stored anywhere. Token is generated per pipeline run.
```

To create a Workload Identity Federation service connection in Azure DevOps:

1. Go to Project Settings > Service Connections > New service connection
2. Select "Azure Resource Manager"
3. Select "Workload Identity federation (automatic)" (or manual for custom setup)
4. Select your subscription and resource group scope
5. Azure DevOps automatically creates the app registration and federated credential

```bash
# Manual setup: Create app registration with federated credential for Azure DevOps
az ad app create --display-name "azure-devops-cicd"
APP_ID=$(az ad app list --display-name "azure-devops-cicd" --query '[0].appId' -o tsv)

# Create service principal
az ad sp create --id "$APP_ID"

# Add federated credential for Azure DevOps
az ad app federated-credential create --id "$APP_ID" --parameters '{
  "name": "azure-devops-federation",
  "issuer": "https://vstoken.dev.azure.com/YOUR_ORG_ID",
  "subject": "sc://YOUR_ORG/YOUR_PROJECT/YOUR_SERVICE_CONNECTION",
  "audiences": ["api://AzureADTokenExchange"]
}'

# Grant the service principal appropriate RBAC
SP_OBJECT_ID=$(az ad sp show --id "$APP_ID" --query id -o tsv)
az role assignment create \
  --assignee "$SP_OBJECT_ID" \
  --role Contributor \
  --scope "/subscriptions/<sub-id>/resourceGroups/myRG"
```

---

## GitHub Actions Targeting Azure

GitHub Actions is GitHub's built-in CI/CD platform. If your code lives on GitHub, Actions provides tight integration with zero additional tooling.

### Workflow Basics

GitHub Actions workflows live in `.github/workflows/` and are triggered by events (push, pull_request, schedule, manual dispatch).

```yaml
# .github/workflows/deploy.yml
name: Build and Deploy to Azure

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]
  workflow_dispatch:  # Manual trigger

permissions:
  id-token: write   # Required for OIDC
  contents: read

env:
  ACR_NAME: myacr
  IMAGE_NAME: myapp
  RESOURCE_GROUP: myRG
  CONTAINER_APP_NAME: myapp

jobs:
  build:
    runs-on: ubuntu-latest
    outputs:
      image-tag: ${{ steps.meta.outputs.version }}
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Azure Login (OIDC)
        uses: azure/login@v2
        with:
          client-id: ${{ secrets.AZURE_CLIENT_ID }}
          tenant-id: ${{ secrets.AZURE_TENANT_ID }}
          subscription-id: ${{ secrets.AZURE_SUBSCRIPTION_ID }}

      - name: Login to ACR
        run: az acr login --name ${{ env.ACR_NAME }}

      - name: Docker meta (tags and labels)
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: ${{ env.ACR_NAME }}.azurecr.io/${{ env.IMAGE_NAME }}
          tags: |
            type=sha,prefix=
            type=ref,event=branch
            type=semver,pattern={{version}}

      - name: Build and push
        uses: docker/build-push-action@v6
        with:
          context: .
          push: ${{ github.event_name != 'pull_request' }}
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}

  deploy-staging:
    needs: build
    if: github.ref == 'refs/heads/main' && github.event_name != 'pull_request'
    runs-on: ubuntu-latest
    environment: staging
    steps:
      - name: Azure Login (OIDC)
        uses: azure/login@v2
        with:
          client-id: ${{ secrets.AZURE_CLIENT_ID }}
          tenant-id: ${{ secrets.AZURE_TENANT_ID }}
          subscription-id: ${{ secrets.AZURE_SUBSCRIPTION_ID }}

      - name: Deploy to Container Apps
        uses: azure/container-apps-deploy-action@v2
        with:
          resourceGroup: ${{ env.RESOURCE_GROUP }}
          containerAppName: ${{ env.CONTAINER_APP_NAME }}-staging
          imageToDeploy: ${{ env.ACR_NAME }}.azurecr.io/${{ env.IMAGE_NAME }}:${{ needs.build.outputs.image-tag }}

  deploy-production:
    needs: [build, deploy-staging]
    if: github.ref == 'refs/heads/main' && github.event_name != 'pull_request'
    runs-on: ubuntu-latest
    environment: production  # Requires approval reviewers configured in GitHub
    steps:
      - name: Azure Login (OIDC)
        uses: azure/login@v2
        with:
          client-id: ${{ secrets.AZURE_CLIENT_ID }}
          tenant-id: ${{ secrets.AZURE_TENANT_ID }}
          subscription-id: ${{ secrets.AZURE_SUBSCRIPTION_ID }}

      - name: Deploy to Container Apps
        uses: azure/container-apps-deploy-action@v2
        with:
          resourceGroup: ${{ env.RESOURCE_GROUP }}
          containerAppName: ${{ env.CONTAINER_APP_NAME }}
          imageToDeploy: ${{ env.ACR_NAME }}.azurecr.io/${{ env.IMAGE_NAME }}:${{ needs.build.outputs.image-tag }}
```

### OIDC Setup for GitHub Actions

```bash
# Create an app registration for GitHub Actions
az ad app create --display-name "github-actions-deploy"
APP_ID=$(az ad app list --display-name "github-actions-deploy" --query '[0].appId' -o tsv)
APP_OBJECT_ID=$(az ad app list --display-name "github-actions-deploy" --query '[0].id' -o tsv)

# Create service principal
az ad sp create --id "$APP_ID"

# Create federated credentials for different scenarios

# 1. For the main branch
az ad app federated-credential create --id "$APP_OBJECT_ID" --parameters '{
  "name": "github-main-branch",
  "issuer": "https://token.actions.githubusercontent.com",
  "subject": "repo:myorg/myrepo:ref:refs/heads/main",
  "audiences": ["api://AzureADTokenExchange"]
}'

# 2. For pull requests (read-only access for testing)
az ad app federated-credential create --id "$APP_OBJECT_ID" --parameters '{
  "name": "github-pull-requests",
  "issuer": "https://token.actions.githubusercontent.com",
  "subject": "repo:myorg/myrepo:pull_request",
  "audiences": ["api://AzureADTokenExchange"]
}'

# 3. For a specific environment (production)
az ad app federated-credential create --id "$APP_OBJECT_ID" --parameters '{
  "name": "github-production-env",
  "issuer": "https://token.actions.githubusercontent.com",
  "subject": "repo:myorg/myrepo:environment:production",
  "audiences": ["api://AzureADTokenExchange"]
}'

# Grant RBAC roles
SP_OBJECT_ID=$(az ad sp show --id "$APP_ID" --query id -o tsv)

# ACR push access
ACR_ID=$(az acr show -n myacr --query id -o tsv)
az role assignment create --assignee "$SP_OBJECT_ID" --role AcrPush --scope "$ACR_ID"

# Container Apps contributor access
az role assignment create \
  --assignee "$SP_OBJECT_ID" \
  --role Contributor \
  --scope "/subscriptions/<sub-id>/resourceGroups/myRG"
```

Then add to GitHub repository secrets:
- `AZURE_CLIENT_ID`: The application (client) ID
- `AZURE_TENANT_ID`: Your Entra ID tenant ID
- `AZURE_SUBSCRIPTION_ID`: Your Azure subscription ID

No secrets or passwords---OIDC handles authentication using short-lived tokens generated per workflow run.

---

## Self-Hosted Agents and Runners

Both Azure DevOps and GitHub Actions offer hosted runners (Microsoft/GitHub manages the VM), but you may need self-hosted runners for:
- Accessing private VNet resources (private endpoints, internal APIs)
- Using specialized hardware (GPU, high-memory)
- Reducing build times with persistent caches
- Compliance requirements (builds must run in your environment)

### Azure DevOps Self-Hosted Agent

```bash
# Deploy a self-hosted agent as a Container Instance
az container create \
  --resource-group myRG \
  --name ado-agent \
  --image mcr.microsoft.com/azure-pipelines/vsts-agent:ubuntu-22.04 \
  --cpu 2 \
  --memory 4 \
  --environment-variables \
    AZP_URL="https://dev.azure.com/myorg" \
    AZP_POOL="Self-Hosted" \
    AZP_AGENT_NAME="aci-agent-1" \
  --secure-environment-variables \
    AZP_TOKEN="$AZURE_DEVOPS_PAT" \
  --restart-policy Always
```

### GitHub Actions Self-Hosted Runner on Azure

```bash
# Deploy a runner as a VM Scale Set (recommended for auto-scaling)
# First, install the runner on a base VM, create an image, then use VMSS.

# For a single runner (quick setup):
az vm create \
  --resource-group myRG \
  --name github-runner \
  --image Ubuntu2204 \
  --size Standard_D4s_v5 \
  --admin-username azureuser \
  --generate-ssh-keys \
  --custom-data @runner-cloud-init.yaml

# runner-cloud-init.yaml would install the runner package and register it
```

For production, use the official **Actions Runner Controller (ARC)** on AKS, which auto-scales runners based on pending jobs.

---

## Pipeline Security Best Practices

```text
    Security Layers for CI/CD:

    ┌────────────────────────────────────────────────────────────┐
    │  1. Authentication: OIDC (no static credentials)          │
    │  2. Authorization: Least privilege RBAC                    │
    │  3. Secrets: Key Vault references (not pipeline variables) │
    │  4. Approval: Environment protection rules                 │
    │  5. Supply chain: Image signing + SBOM                     │
    │  6. Audit: Pipeline run logs + Azure activity logs         │
    └────────────────────────────────────────────────────────────┘
```

| Practice | Why | Implementation |
| :--- | :--- | :--- |
| **Use OIDC, not client secrets** | Secrets can leak; OIDC tokens are ephemeral | Azure Login action with `id-token: write` permission |
| **Scope RBAC to resource groups** | Contributor on subscription is too broad | `az role assignment create --scope /subscriptions/.../resourceGroups/specific-rg` |
| **Use environments with approvals** | Prevent accidental production deploys | GitHub Environments with required reviewers |
| **Pin action versions by SHA** | Tag-based versions can be overwritten | `uses: actions/checkout@a12a3943b...` instead of `@v4` |
| **Scan images before deployment** | Catch vulnerabilities before they reach production | `trivy image myacr.azurecr.io/myapp:latest` in the pipeline |
| **Use branch protection rules** | Prevent direct pushes to main | Require PRs, status checks, and code review |

**War Story**: A startup used a service principal with Contributor access to their production subscription, stored as a GitHub secret. An attacker submitted a pull request that modified the workflow file to echo the secret to the pipeline logs. Because the repository did not have branch protection requiring approval for workflow changes, the PR was auto-merged by a bot. The secret appeared in the workflow run logs, which were public because the repository was public. Within minutes, the attacker had Contributor access to the production subscription. The fix: OIDC (no secret to leak), environment protection rules (require approval), and branch protection (require review for workflow changes).

---

## Did You Know?

1. **GitHub Actions OIDC tokens are valid for only 10 minutes** and are scoped to the specific workflow run, job, and repository. Even if an attacker intercepts a token, it expires before they can do anything meaningful. Compare this to a client secret with a 1-2 year expiry---the attack window is reduced from years to minutes.

2. **Azure DevOps supports pipeline caching** that persists across runs. A Node.js project with 500 MB of node_modules can restore its cache in 15 seconds instead of running `npm install` for 3 minutes. Over 100 pipeline runs per week, that saves 4.2 hours of build time. Use the `Cache@2` task with a hash of your lock file as the cache key.

3. **GitHub Actions hosted runners are ephemeral and fresh for every job.** Each job gets a brand-new VM with a clean filesystem. This is excellent for security (no contamination between builds) but means every job starts from scratch. Self-hosted runners persist between jobs, enabling persistent caches and pre-installed tools, but require you to manage security (ensuring one job cannot access another job's data).

4. **Azure DevOps Pipelines can deploy to any cloud**, not just Azure. The platform supports service connections for AWS, GCP, Kubernetes (any cluster), SSH targets, and generic REST APIs. A single pipeline can build in Azure DevOps, push images to ACR, and deploy to an EKS cluster on AWS.

---

## Common Mistakes

| Mistake | Why It Happens | How to Fix It |
| :--- | :--- | :--- |
| Storing Azure credentials as pipeline secrets instead of using OIDC | OIDC setup requires more initial configuration | Invest 15 minutes in OIDC setup. It eliminates secret rotation, reduces blast radius, and prevents credential exfiltration. |
| Granting Contributor at subscription scope to the pipeline identity | It is the quickest way to "make it work" | Create a custom role or use Contributor scoped to the specific resource group the pipeline deploys to. |
| Not using environments with approval gates for production | "We trust our team" or "approvals slow us down" | Environment protection rules are the last line of defense against accidental or malicious production deployments. A 30-second approval is cheap insurance. |
| Running `docker build` on the runner instead of using ACR Tasks | Teams are familiar with local Docker builds | ACR Tasks builds images in Azure, reducing build time (no push over internet), leveraging Azure network for base image pulls, and eliminating the need for Docker on the runner. |
| Using `actions/checkout@v4` instead of pinning to a specific SHA | Version tags are readable and convenient | Tags can be moved to point to different commits (supply chain attack). Pin critical actions to their full SHA: `actions/checkout@a12a3943...`. |
| Not scanning images for vulnerabilities in the pipeline | "Scanning slows down the pipeline" | Add Trivy or Microsoft Defender scan as a pipeline step. A 30-second scan catches vulnerabilities before they reach production. Better to delay a deploy than to deploy a vulnerable image. |
| Hardcoding resource names in the workflow file | It works for a single environment | Use workflow inputs, environment variables, or matrix strategies to parameterize resource names. This enables the same workflow to deploy to staging and production. |
| Not testing the deployment rollback process | "We will figure it out when we need to" | Include a rollback step or document the rollback procedure. For Container Apps, this means reactivating a previous revision. Test it before you need it. |

---

## Quiz

<details>
<summary>1. What is OIDC federation, and why is it more secure than using a client secret for CI/CD authentication with Azure?</summary>

OIDC (OpenID Connect) federation allows a CI/CD platform (GitHub Actions or Azure DevOps) to authenticate with Azure without any stored secrets. The CI/CD platform generates a short-lived OIDC token (valid for ~10 minutes) that includes claims about the workflow (repository, branch, environment). Azure Entra ID is configured to trust the CI/CD platform as an OIDC token issuer. When the pipeline presents the token, Entra ID validates it and issues an Azure access token. This is more secure than client secrets because: no secret is stored that can be leaked, tokens are ephemeral (10 minutes vs 1-2 years), tokens are scoped to the specific workflow run, and there is nothing to rotate.
</details>

<details>
<summary>2. In a GitHub Actions workflow, what does the `permissions: id-token: write` setting do?</summary>

This setting grants the workflow permission to request an OIDC token from GitHub's token endpoint. Without this permission, the `azure/login` action cannot generate the JWT needed for OIDC authentication with Azure. By default, GitHub workflows do not have this permission, so you must explicitly request it. This is a security feature: only workflows that explicitly declare they need OIDC token generation can request one. You should set this at the job level (not the workflow level) to follow the principle of least privilege, granting token generation only to the jobs that need Azure access.
</details>

<details>
<summary>3. Why would you use a self-hosted runner instead of a GitHub-hosted runner?</summary>

Use self-hosted runners when you need to: access resources in a private VNet (private endpoints, internal databases) that hosted runners cannot reach; use specialized hardware (GPU, high-memory, ARM architecture); maintain persistent caches for large dependencies (node_modules, Maven cache) to avoid re-downloading every run; comply with regulations that require builds to run in your controlled environment; or reduce build times with pre-installed tools and warm caches. The tradeoffs are: you must manage runner security, patching, and scaling. Self-hosted runners persist between jobs, so you must ensure proper isolation to prevent one job from accessing another's data.
</details>

<details>
<summary>4. Explain the purpose of GitHub Environments and protection rules in a deployment pipeline.</summary>

GitHub Environments define deployment targets (staging, production) with configurable protection rules. Protection rules can require: manual approval from designated reviewers before deployment proceeds, specific branches (only main can deploy to production), a wait timer (delay deployment by N minutes), and environment-specific secrets (production secrets are only available in the production environment). This prevents accidental or unauthorized production deployments. Even if someone pushes malicious code to main, the production deployment requires a human reviewer to approve it. Environment secrets are also scoped: a staging pipeline cannot access production secrets even if the workflow is modified.
</details>

<details>
<summary>5. How does pinning GitHub Actions to a commit SHA prevent supply chain attacks?</summary>

When you reference an action by tag (e.g., `actions/checkout@v4`), the tag is a mutable pointer---it can be moved to point to any commit. An attacker who compromises the action's repository can move the tag to a malicious commit, and all workflows using that tag will execute the malicious code. When you pin to a commit SHA (e.g., `actions/checkout@a12a3943...`), the reference is immutable---it always points to the exact same code. Even if the repository is compromised, the SHA cannot be changed to point to different code. Use tools like Dependabot or Renovate to automatically update pinned SHAs when new versions are released.
</details>

<details>
<summary>6. You need a pipeline that builds a Docker image, pushes it to ACR, and deploys to Container Apps. It must work for both staging and production. How would you design this?</summary>

Use a single GitHub Actions workflow with multiple jobs and environments. The build job runs on every push to main: it logs into Azure via OIDC, builds the image, tags it with the Git SHA, and pushes to ACR. The staging deploy job depends on the build job, runs in the `staging` environment, and deploys the image to the staging Container App. The production deploy job depends on the staging job, runs in the `production` environment (which has required reviewers configured), and deploys the same image tag to the production Container App. Use environment-specific variables for resource names. The OIDC federated credential should have separate `subject` claims for each environment, allowing different RBAC scopes (e.g., staging gets Contributor on staging RG, production gets Contributor on production RG).
</details>

---

## Hands-On Exercise: GitHub Actions OIDC Auth to ACR Build and Container Apps Deploy

In this exercise, you will set up OIDC authentication between GitHub Actions and Azure, build a container image with ACR Tasks, and deploy it to Container Apps.

**Prerequisites**: Azure CLI, a GitHub repository, `gh` CLI (optional).

### Task 1: Create Azure Infrastructure

```bash
RG="kubedojo-cicd-lab"
LOCATION="eastus2"
ACR_NAME="kubedojocicd$(openssl rand -hex 4)"
APP_NAME="cicd-demo-app"
ENV_NAME="cicd-demo-env"

az group create --name "$RG" --location "$LOCATION"

# Create ACR
az acr create -g "$RG" -n "$ACR_NAME" --sku Standard --location "$LOCATION"

# Create Container Apps environment
az containerapp env create -g "$RG" -n "$ENV_NAME" --location "$LOCATION"

# Deploy initial Container App
az containerapp create \
  --resource-group "$RG" \
  --name "$APP_NAME" \
  --environment "$ENV_NAME" \
  --image mcr.microsoft.com/k8se/quickstart:latest \
  --target-port 80 \
  --ingress external \
  --min-replicas 1

APP_URL=$(az containerapp show -g "$RG" -n "$APP_NAME" --query properties.configuration.ingress.fqdn -o tsv)
echo "App URL: https://$APP_URL"
```

<details>
<summary>Verify Task 1</summary>

```bash
curl -s "https://$APP_URL" | head -5
```
</details>

### Task 2: Set Up OIDC Authentication for GitHub Actions

```bash
# Create app registration
az ad app create --display-name "github-cicd-lab"
APP_ID=$(az ad app list --display-name "github-cicd-lab" --query '[0].appId' -o tsv)
APP_OBJECT_ID=$(az ad app list --display-name "github-cicd-lab" --query '[0].id' -o tsv)

# Create service principal
az ad sp create --id "$APP_ID"
SP_OBJECT_ID=$(az ad sp show --id "$APP_ID" --query id -o tsv)

# Create federated credential for your GitHub repo
# Replace YOUR_GITHUB_ORG and YOUR_REPO with your actual values
az ad app federated-credential create --id "$APP_OBJECT_ID" --parameters '{
  "name": "github-main",
  "issuer": "https://token.actions.githubusercontent.com",
  "subject": "repo:YOUR_GITHUB_ORG/YOUR_REPO:ref:refs/heads/main",
  "audiences": ["api://AzureADTokenExchange"]
}'

# Grant RBAC: ACR Push
ACR_ID=$(az acr show -n "$ACR_NAME" --query id -o tsv)
az role assignment create --assignee "$SP_OBJECT_ID" --role AcrPush --scope "$ACR_ID"

# Grant RBAC: Container Apps Contributor
RG_ID=$(az group show -n "$RG" --query id -o tsv)
az role assignment create --assignee "$SP_OBJECT_ID" --role Contributor --scope "$RG_ID"

# Output the values you need for GitHub secrets
TENANT_ID=$(az account show --query tenantId -o tsv)
SUB_ID=$(az account show --query id -o tsv)

echo "================================"
echo "Add these as GitHub repository secrets:"
echo "AZURE_CLIENT_ID: $APP_ID"
echo "AZURE_TENANT_ID: $TENANT_ID"
echo "AZURE_SUBSCRIPTION_ID: $SUB_ID"
echo "ACR_NAME: $ACR_NAME"
echo "RESOURCE_GROUP: $RG"
echo "CONTAINER_APP_NAME: $APP_NAME"
echo "================================"
```

<details>
<summary>Verify Task 2</summary>

```bash
az ad app federated-credential list --id "$APP_OBJECT_ID" \
  --query '[].{Name:name, Subject:subject}' -o table
```

You should see the federated credential for your GitHub repository.
</details>

### Task 3: Create the Application Code

In your GitHub repository, create these files:

```bash
# Dockerfile
cat > Dockerfile << 'EOF'
FROM nginx:alpine
COPY index.html /usr/share/nginx/html/index.html
EXPOSE 80
EOF

# index.html
cat > index.html << 'EOF'
<!DOCTYPE html>
<html><body>
<h1>KubeDojo CI/CD Lab</h1>
<p>Deployed via GitHub Actions with OIDC</p>
<p>Build: BUILD_SHA</p>
</body></html>
EOF
```

<details>
<summary>Verify Task 3</summary>

Ensure both files exist in your repository root.
</details>

### Task 4: Create the GitHub Actions Workflow

```bash
mkdir -p .github/workflows

cat > .github/workflows/deploy.yml << 'WORKFLOW'
name: Build and Deploy

on:
  push:
    branches: [main]
  workflow_dispatch:

permissions:
  id-token: write
  contents: read

jobs:
  build-and-deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Azure Login (OIDC)
        uses: azure/login@v2
        with:
          client-id: ${{ secrets.AZURE_CLIENT_ID }}
          tenant-id: ${{ secrets.AZURE_TENANT_ID }}
          subscription-id: ${{ secrets.AZURE_SUBSCRIPTION_ID }}

      - name: Set build SHA in HTML
        run: sed -i "s/BUILD_SHA/${GITHUB_SHA::8}/" index.html

      - name: Build and push to ACR
        run: |
          az acr build \
            --registry ${{ secrets.ACR_NAME }} \
            --image cicd-demo:${{ github.sha }} \
            --image cicd-demo:latest \
            .

      - name: Deploy to Container Apps
        run: |
          az containerapp update \
            --resource-group ${{ secrets.RESOURCE_GROUP }} \
            --name ${{ secrets.CONTAINER_APP_NAME }} \
            --image ${{ secrets.ACR_NAME }}.azurecr.io/cicd-demo:${{ github.sha }}
WORKFLOW
```

<details>
<summary>Verify Task 4</summary>

The workflow file should be at `.github/workflows/deploy.yml`. After pushing to main, check the Actions tab in your GitHub repository for the workflow run.
</details>

### Task 5: Add GitHub Secrets and Trigger the Pipeline

```bash
# If you have the gh CLI installed:
gh secret set AZURE_CLIENT_ID --body "$APP_ID"
gh secret set AZURE_TENANT_ID --body "$TENANT_ID"
gh secret set AZURE_SUBSCRIPTION_ID --body "$SUB_ID"
gh secret set ACR_NAME --body "$ACR_NAME"
gh secret set RESOURCE_GROUP --body "$RG"
gh secret set CONTAINER_APP_NAME --body "$APP_NAME"

# Commit and push to trigger the pipeline
git add -A
git commit -m "feat: add CI/CD pipeline with OIDC authentication"
git push origin main
```

<details>
<summary>Verify Task 5</summary>

```bash
# Check the GitHub Actions run status
gh run list --limit 1

# Or check the deployed app
curl -s "https://$APP_URL"
```

The page should show the build SHA, confirming the pipeline deployed successfully.
</details>

### Task 6: Make a Change and Verify Automatic Deployment

```bash
# Update the HTML
cat > index.html << 'EOF'
<!DOCTYPE html>
<html><body>
<h1>KubeDojo CI/CD Lab - Updated!</h1>
<p>Automatic deployment via GitHub Actions OIDC</p>
<p>Build: BUILD_SHA</p>
<p>Zero secrets stored in the pipeline.</p>
</body></html>
EOF

git add index.html
git commit -m "feat: update landing page"
git push origin main

# Wait for the pipeline to complete
echo "Waiting for pipeline... Check https://github.com/YOUR_ORG/YOUR_REPO/actions"
```

<details>
<summary>Verify Task 6</summary>

After the pipeline completes, curl the app URL again. The updated content should be visible, confirming the automated deployment pipeline works end to end.
</details>

### Cleanup

```bash
az group delete --name "$RG" --yes --no-wait
az ad app delete --id "$APP_OBJECT_ID"
```

### Success Criteria

- [ ] ACR and Container Apps infrastructure created
- [ ] App registration with OIDC federated credential for GitHub Actions
- [ ] GitHub secrets configured (client ID, tenant ID, subscription ID)
- [ ] GitHub Actions workflow created with OIDC login, ACR build, and Container Apps deploy
- [ ] Initial deployment triggered and verified (app accessible via URL)
- [ ] Code change automatically deployed via pipeline (no manual intervention)

---

## Next Module

[Module 12: ARM & Bicep Basics](module-12-bicep.md) --- Learn infrastructure as code on Azure with ARM templates and Bicep, including modules, deployment scopes, and what-if previews for safe infrastructure changes.
