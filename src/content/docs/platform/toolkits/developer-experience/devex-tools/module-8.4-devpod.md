---
title: "Module 8.4: DevPod - Open Source Dev Environments"
slug: platform/toolkits/developer-experience/devex-tools/module-8.4-devpod
sidebar:
  order: 5
---
## Complexity: [MEDIUM]
## Time to Complete: 40-45 minutes

---

## Prerequisites

Before starting this module, you should have completed:
- [Module 8.3: Local Kubernetes](module-8.3-local-kubernetes/)
- Container fundamentals (Docker)
- Basic understanding of Dev Containers specification
- SSH basics

---

## Why This Module Matters

**Your Laptop Is a Liability**

The new hire stared at her screen in frustration. Day three. Still no working development environment.

The Slack thread had 47 messages: "Try brew install again." "Did you set GOPATH?" "Oh wait, you need version 1.20, not 1.21." "Have you checked your Node version?" "That error means your Docker isn't running." Her mentor had already spent 6 hours pair-debugging her laptop. Other engineers kept chiming in with contradictory advice. Meanwhile, the sprint was moving forward without her.

Two buildings away, another team had a different problem. Their security team had just mandated that no customer data—not even anonymized test data—could touch developer laptops. Every engineer's local database was now a compliance violation. The solution? Move development to cloud VMs. But GitHub Codespaces quoted them $28,000/month for 40 developers. Microsoft's infrastructure, Microsoft's prices.

GitHub Codespaces showed the world that "development environment as a service" was possible. But Codespaces only works with GitHub, costs $0.18/core/hour, and runs on Microsoft's infrastructure. What if you want the same experience but:
- Self-hosted on your infrastructure
- Works with GitLab, Bitbucket, or any Git provider
- Runs on AWS, GCP, Azure, or your own Kubernetes cluster
- Free and open source

That's DevPod. Created by Loft Labs (the same team behind vcluster), it's an open source alternative to Codespaces that runs dev environments anywhere. Same dev containers spec, your choice of infrastructure.

---

## Did You Know?

- **Loft Labs created DevPod after their own frustration** - The team behind vcluster (virtual Kubernetes clusters) kept losing days to environment setup when onboarding engineers. They built DevPod because they needed it themselves—then open-sourced it. Their internal "time to first commit" dropped from 2 days to 15 minutes.

- **The Dev Containers spec came from VS Code, but Microsoft doesn't control it** - In 2022, Microsoft moved the Dev Containers specification to an open governance model. Now DevPod, Codespaces, VS Code, JetBrains, and others all implement the same standard. Your `.devcontainer.json` works everywhere.

- **DevPod's "no server" architecture was controversial** - When DevPod launched, competitors argued teams needed centralized management. Loft Labs bet that developers would prefer simplicity over control planes. They were right: DevPod reached 10,000 GitHub stars faster than Gitpod's self-hosted offering.

- **GPU support enables ML development without $3,000 laptops** - A startup in Berlin runs DevPod on AWS g4dn instances. Their ML engineers get NVIDIA T4 GPUs for $0.53/hour instead of buying expensive workstations. When training finishes, they stop the instance. Annual hardware budget dropped from $180,000 to $12,000.

---

## How DevPod Works

```
DEVPOD ARCHITECTURE
─────────────────────────────────────────────────────────────────

┌─────────────────────────────────────────────────────────────────┐
│                     DEVELOPER'S LAPTOP                           │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  DevPod CLI / Desktop App                                  │  │
│  │  ┌─────────────────────────────────────────────────────┐  │  │
│  │  │  • Reads devcontainer.json                          │  │  │
│  │  │  • Provisions infrastructure via provider           │  │  │
│  │  │  • Starts dev container                             │  │  │
│  │  │  • Connects IDE via SSH                             │  │  │
│  │  └─────────────────────────────────────────────────────┘  │  │
│  └───────────────────────────────────────────────────────────┘  │
└────────────────────────────┬────────────────────────────────────┘
                             │ SSH
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                     PROVIDER (Your Choice)                       │
│                                                                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐ │
│  │   Docker    │  │  Kubernetes │  │   Cloud VM              │ │
│  │   (local)   │  │  (any)      │  │   (AWS/GCP/Azure)       │ │
│  └──────┬──────┘  └──────┬──────┘  └───────────┬─────────────┘ │
│         │                │                      │               │
│         └────────────────┼──────────────────────┘               │
│                          │                                      │
│                          ▼                                      │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │              DEV CONTAINER                                 │ │
│  │  ┌─────────────────────────────────────────────────────┐ │ │
│  │  │  • Your source code (cloned or mounted)             │ │ │
│  │  │  • All dependencies installed                       │ │ │
│  │  │  • Tools and extensions configured                  │ │ │
│  │  │  • SSH server for IDE connection                    │ │ │
│  │  └─────────────────────────────────────────────────────┘ │ │
│  └───────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘

COMPARISON:
─────────────────────────────────────────────────────────────────
                 Codespaces      Gitpod         DevPod
─────────────────────────────────────────────────────────────────
Server needed    Yes (GitHub)    Yes (Gitpod)   No
Self-hosted      Enterprise      Yes            Yes
Provider choice  GitHub only     AWS/GCP/own    Any
Cost             $0.18/hour      $0-36/month    Infrastructure
Open source      No              Partial        Yes
```

---

## Installation

### Desktop App (Recommended)

```bash
# macOS
brew install --cask devpod

# Windows
winget install loft-sh.devpod

# Linux (AppImage)
curl -L -o devpod.AppImage https://github.com/loft-sh/devpod/releases/latest/download/DevPod-linux-x86_64.AppImage
chmod +x devpod.AppImage
./devpod.AppImage
```

### CLI Only

```bash
# macOS/Linux
curl -L -o devpod https://github.com/loft-sh/devpod/releases/latest/download/devpod-darwin-amd64
chmod +x devpod
sudo mv devpod /usr/local/bin/

# Verify installation
devpod version
```

---

## Providers

### Setting Up Providers

```bash
# Docker (local) - usually default
devpod provider add docker

# Kubernetes
devpod provider add kubernetes
devpod provider set-options kubernetes \
  --option KUBERNETES_NAMESPACE=devpod \
  --option KUBERNETES_CONTEXT=my-cluster

# AWS
devpod provider add aws
devpod provider set-options aws \
  --option AWS_REGION=us-west-2 \
  --option AWS_INSTANCE_TYPE=t3.large

# GCP
devpod provider add gcp
devpod provider set-options gcp \
  --option GCP_PROJECT=my-project \
  --option GCP_ZONE=us-central1-a \
  --option GCP_MACHINE_TYPE=e2-standard-4

# Azure
devpod provider add azure
devpod provider set-options azure \
  --option AZURE_RESOURCE_GROUP=devpod-rg \
  --option AZURE_LOCATION=eastus

# SSH (any existing server)
devpod provider add ssh
devpod provider set-options ssh \
  --option SSH_HOST=dev-server.example.com \
  --option SSH_USER=devuser
```

### Provider Options

| Provider | Use Case | Notes |
|----------|----------|-------|
| **Docker** | Quick local dev | Default, no cloud costs |
| **Kubernetes** | Team standardization | Use existing cluster |
| **AWS** | Power users, GPU | EC2 instances |
| **GCP** | GKE users | Compute Engine |
| **Azure** | Azure shops | Azure VMs |
| **SSH** | Existing servers | Any SSH-accessible machine |
| **DigitalOcean** | Cost-effective | Good for small teams |

---

## Creating Dev Environments

### From a Repository

```bash
# Clone and open in VS Code
devpod up github.com/myorg/myrepo --ide vscode

# Use different IDE
devpod up github.com/myorg/myrepo --ide goland
devpod up github.com/myorg/myrepo --ide openvscode  # Browser-based

# Use specific provider
devpod up github.com/myorg/myrepo --provider aws

# Use specific branch
devpod up github.com/myorg/myrepo@develop

# Private repository (uses git credentials)
devpod up github.com/myorg/private-repo
```

### From Local Directory

```bash
# Open current directory
devpod up . --ide vscode

# Specify directory
devpod up /path/to/project --ide vscode
```

### Managing Workspaces

```bash
# List all workspaces
devpod list

# Stop a workspace (keeps state)
devpod stop myrepo

# Start stopped workspace
devpod up myrepo

# Delete workspace
devpod delete myrepo

# SSH into workspace
devpod ssh myrepo
```

---

## Dev Container Configuration

### Basic devcontainer.json

```json
// .devcontainer/devcontainer.json
{
  "name": "Node.js Development",
  "image": "mcr.microsoft.com/devcontainers/javascript-node:20",

  "features": {
    "ghcr.io/devcontainers/features/docker-in-docker:2": {},
    "ghcr.io/devcontainers/features/kubectl-helm-minikube:1": {}
  },

  "customizations": {
    "vscode": {
      "extensions": [
        "dbaeumer.vscode-eslint",
        "esbenp.prettier-vscode",
        "bradlc.vscode-tailwindcss"
      ],
      "settings": {
        "editor.formatOnSave": true,
        "editor.defaultFormatter": "esbenp.prettier-vscode"
      }
    }
  },

  "forwardPorts": [3000, 5432],

  "postCreateCommand": "npm install",

  "remoteUser": "node"
}
```

### Full-Featured Example

```json
// .devcontainer/devcontainer.json
{
  "name": "Full Stack Development",

  "build": {
    "dockerfile": "Dockerfile",
    "context": "..",
    "args": {
      "NODE_VERSION": "20",
      "GO_VERSION": "1.21"
    }
  },

  "features": {
    "ghcr.io/devcontainers/features/docker-in-docker:2": {
      "dockerDashComposeVersion": "v2"
    },
    "ghcr.io/devcontainers/features/kubectl-helm-minikube:1": {
      "minikube": "none"
    },
    "ghcr.io/devcontainers/features/aws-cli:1": {},
    "ghcr.io/devcontainers/features/terraform:1": {}
  },

  "customizations": {
    "vscode": {
      "extensions": [
        "golang.go",
        "dbaeumer.vscode-eslint",
        "hashicorp.terraform",
        "ms-azuretools.vscode-docker"
      ]
    }
  },

  "forwardPorts": [3000, 8080, 5432, 6379],

  "portsAttributes": {
    "3000": {"label": "Frontend", "onAutoForward": "notify"},
    "8080": {"label": "API", "onAutoForward": "openPreview"}
  },

  "postCreateCommand": ".devcontainer/setup.sh",
  "postStartCommand": "docker compose up -d db redis",

  "mounts": [
    "source=${localEnv:HOME}/.aws,target=/home/vscode/.aws,type=bind,consistency=cached",
    "source=devpod-go-cache,target=/go/pkg,type=volume"
  ],

  "remoteEnv": {
    "DATABASE_URL": "postgres://localhost:5432/dev",
    "REDIS_URL": "redis://localhost:6379"
  },

  "hostRequirements": {
    "cpus": 4,
    "memory": "8gb",
    "storage": "32gb"
  }
}
```

### Custom Dockerfile

```dockerfile
# .devcontainer/Dockerfile
FROM mcr.microsoft.com/devcontainers/base:ubuntu-22.04

ARG NODE_VERSION=20
ARG GO_VERSION=1.21

# Install Node.js
RUN curl -fsSL https://deb.nodesource.com/setup_${NODE_VERSION}.x | bash - \
    && apt-get install -y nodejs

# Install Go
RUN curl -fsSL https://go.dev/dl/go${GO_VERSION}.linux-amd64.tar.gz | tar -C /usr/local -xzf - \
    && echo 'export PATH=$PATH:/usr/local/go/bin' >> /etc/profile.d/go.sh

# Install additional tools
RUN apt-get update && apt-get install -y \
    postgresql-client \
    redis-tools \
    jq \
    && rm -rf /var/lib/apt/lists/*

# Pre-install global npm packages
RUN npm install -g pnpm typescript ts-node

# Set up non-root user
USER vscode
WORKDIR /workspace
```

---

## IDE Integration

### Supported IDEs

```
IDE SUPPORT MATRIX
─────────────────────────────────────────────────────────────────

┌─────────────────────┬──────────────┬────────────────────────────┐
│ IDE                 │ Connection   │ Notes                      │
├─────────────────────┼──────────────┼────────────────────────────┤
│ VS Code             │ Native SSH   │ Best experience, default   │
│ VS Code (Browser)   │ code-server  │ No local install needed    │
│ JetBrains IDEs      │ Gateway      │ IntelliJ, GoLand, PyCharm │
│ Cursor              │ Native SSH   │ AI-first fork of VS Code   │
│ Neovim              │ SSH          │ For terminal warriors      │
│ Zed                 │ SSH          │ High-performance editor    │
│ Fleet               │ SSH          │ JetBrains' new editor      │
└─────────────────────┴──────────────┴────────────────────────────┘
```

### VS Code Configuration

```bash
# Open with VS Code (default)
devpod up myrepo --ide vscode

# VS Code opens automatically via Remote-SSH extension
# No additional configuration needed
```

### JetBrains Configuration

```bash
# Open with GoLand
devpod up myrepo --ide goland

# Open with IntelliJ
devpod up myrepo --ide intellij

# Open with PyCharm
devpod up myrepo --ide pycharm

# Uses JetBrains Gateway automatically
```

### Browser-Based (OpenVSCode)

```bash
# Open in browser
devpod up myrepo --ide openvscode

# Opens http://localhost:10800 with full VS Code in browser
# Great for:
# - Chromebooks
# - Tablets
# - Quick edits without IDE
```

---

## Enterprise Setup

### Kubernetes Provider for Teams

```yaml
# devpod-kubernetes-provider.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: devpod
---
apiVersion: v1
kind: ServiceAccount
metadata:
  name: devpod-sa
  namespace: devpod
---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: devpod-role
  namespace: devpod
rules:
  - apiGroups: [""]
    resources: ["pods", "pods/exec", "services", "persistentvolumeclaims"]
    verbs: ["*"]
  - apiGroups: ["apps"]
    resources: ["deployments"]
    verbs: ["*"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: devpod-binding
  namespace: devpod
subjects:
  - kind: ServiceAccount
    name: devpod-sa
    namespace: devpod
roleRef:
  kind: Role
  name: devpod-role
  apiGroup: rbac.authorization.k8s.io
```

```bash
# Apply and configure
kubectl apply -f devpod-kubernetes-provider.yaml

devpod provider add kubernetes
devpod provider set-options kubernetes \
  --option KUBERNETES_NAMESPACE=devpod \
  --option KUBERNETES_SERVICE_ACCOUNT=devpod-sa
```

### Resource Limits

```json
// .devcontainer/devcontainer.json
{
  "hostRequirements": {
    "cpus": 4,
    "memory": "8gb",
    "storage": "32gb",
    "gpu": true  // For ML workloads
  }
}
```

---

## War Story: The 2-Day Onboarding Problem

*How a fintech's $320,000 annual onboarding cost became a competitive advantage*

**Company**: Series B fintech, 80 developers, 40 hires/year
**Date**: Q1 2024
**Stakes**: $8M annual engineering budget under scrutiny from new CFO

### The Before

The engineering VP got the numbers from HR and nearly choked on her coffee: **2.1 days average** to first productive commit. For 40 new hires per year, that was 84 person-days—over four months of engineering capacity—spent watching progress bars and debugging PATH variables.

But that was just the visible cost. The hidden tax was worse: every new hire consumed an average of **6 hours of senior developer time** in pair-debugging sessions. At a $150/hour fully-loaded cost, that was another $36,000/year in opportunity cost.

The fintech with 80 developers had the following onboarding process:

```
TRADITIONAL ONBOARDING (2 DAYS)
─────────────────────────────────────────────────────────────────

Day 1 (8 hours):
─────────────────────────────────────────────────────────────────
□ Install Homebrew
□ Install Docker Desktop (and wait for license approval)
□ Install Node.js (but which version? Check with team)
□ Install Go (wait, we need 1.20 AND 1.21 for different services)
□ Install PostgreSQL (local, because "it's easier to debug")
□ Install Redis
□ Clone 12 repositories
□ Run "npm install" on 8 of them (and debug node-gyp failures)
□ Configure AWS credentials
□ Set up VPN
□ Debug why service A can't connect to service B

Day 2 (6 hours):
─────────────────────────────────────────────────────────────────
□ Finish debugging environment issues
□ Discover everyone uses different versions
□ Ask senior developer for help (interrupt their work)
□ Finally run the app
□ Realize the database schema is outdated
□ Run migrations (break something)
□ Ask for help again
□ MAYBE write first line of code

Problems:
• Every laptop different
• Senior devs interrupted
• New devs feel incompetent
• Hidden costs: 2 days × 80 hires/year × $500/day = $80,000/year
```

### The DevPod Solution

```
DEVPOD ONBOARDING (15 MINUTES)
─────────────────────────────────────────────────────────────────

Step 1: Install DevPod (2 min)
─────────────────────────────────────────────────────────────────
brew install --cask devpod

Step 2: Open workspace (10 min)
─────────────────────────────────────────────────────────────────
devpod up github.com/fintech/platform --ide vscode

This automatically:
• Provisions 8-core, 16GB VM on company Kubernetes
• Clones all 12 repositories
• Installs correct Node.js, Go, Python versions
• Starts PostgreSQL, Redis, Kafka in containers
• Runs database migrations
• Pre-installs all VS Code extensions
• Configures AWS credentials (via IAM role)

Step 3: Start coding (3 min)
─────────────────────────────────────────────────────────────────
• VS Code opens with everything ready
• Run tests: npm test (all pass)
• Start dev server: npm run dev (works immediately)
• Open http://localhost:3000 (app running)

Total time: 15 minutes
First PR: Same day
```

### The Implementation

```json
// .devcontainer/devcontainer.json
{
  "name": "Fintech Platform",

  "image": "ghcr.io/fintech/devcontainer:latest",

  "features": {
    "ghcr.io/devcontainers/features/docker-in-docker:2": {},
    "ghcr.io/devcontainers/features/aws-cli:1": {}
  },

  "postCreateCommand": "/workspace/.devcontainer/setup.sh",

  "forwardPorts": [3000, 3001, 5432, 6379, 9092],

  "customizations": {
    "vscode": {
      "extensions": [
        "golang.go",
        "dbaeumer.vscode-eslint",
        "ms-azuretools.vscode-docker",
        "redhat.vscode-yaml"
      ],
      "settings": {
        "go.toolsManagement.autoUpdate": true,
        "editor.formatOnSave": true
      }
    }
  },

  "hostRequirements": {
    "cpus": 8,
    "memory": "16gb"
  }
}
```

```bash
#!/bin/bash
# .devcontainer/setup.sh

set -e

echo "Setting up development environment..."

# Clone all required repositories
repos=(
  "platform-api"
  "platform-web"
  "shared-libraries"
  "infrastructure"
)

for repo in "${repos[@]}"; do
  if [ ! -d "/workspace/$repo" ]; then
    git clone "git@github.com:fintech/$repo.git" "/workspace/$repo"
  fi
done

# Start infrastructure
docker compose -f /workspace/.devcontainer/infra.yaml up -d

# Wait for PostgreSQL
until pg_isready -h localhost -p 5432; do
  sleep 1
done

# Run migrations
cd /workspace/platform-api
npm run db:migrate

# Install dependencies
for repo in "${repos[@]}"; do
  if [ -f "/workspace/$repo/package.json" ]; then
    cd "/workspace/$repo"
    npm ci
  fi
done

echo "✅ Development environment ready!"
```

### Results

**Six-Month Review**:

| Metric | Before | After | Impact |
|--------|--------|-------|--------|
| Onboarding time | 2.1 days | 15 minutes | -99% |
| "Works on my machine" bugs | 5/week | 0 | -100% |
| Senior dev interruptions | 6 hours/new hire | 15 min/new hire | -96% |
| Developer satisfaction | 60% | 94% | +57% |
| Time to first PR | 3 days | 2 hours | -97% |
| Environment-related Slack messages | 120/month | 8/month | -93% |

**Financial Impact**:

| Cost Category | Before | After | Annual Savings |
|---------------|--------|-------|----------------|
| New hire lost productivity | $168,000 | $4,000 | **$164,000** |
| Senior dev support time | $36,000 | $3,000 | **$33,000** |
| "Works on my machine" bugs | $62,000 | $0 | **$62,000** |
| Infrastructure (DevPod on K8s) | $0 | $18,000 | **-$18,000** |
| **Total** | $266,000 | $25,000 | **$241,000** |

The CFO who'd questioned the engineering budget became DevPod's biggest advocate. "You turned a cost center into a recruiting advantage," she told the VP. In interviews, the 15-minute onboarding demo became their closer—three candidates accepted offers specifically because of it.

---

## Common Mistakes

| Mistake | Why It's Bad | Better Approach |
|---------|--------------|-----------------|
| No devcontainer.json | Every dev configures differently | Create and maintain devcontainer |
| Giant custom image | Slow to build, hard to update | Use features for tooling |
| Missing forwardPorts | Can't access dev servers | Define all needed ports |
| No postCreateCommand | Manual setup still needed | Automate all setup steps |
| Local Docker only | Misses remote dev benefits | Use Kubernetes for teams |
| No hostRequirements | Underpowered environments | Specify resource needs |
| Skipping volume mounts | Slow filesystem, lost caches | Mount package caches |
| Not versioning devcontainer | Config drift over time | Commit to repository |

---

## Hands-On Exercise

### Task: Create a DevPod-Ready Project

**Objective**: Configure a project for DevPod development with full tooling.

**Success Criteria**:
1. .devcontainer/devcontainer.json created
2. DevPod workspace starts successfully
3. IDE connects automatically
4. Development server runs without manual setup

### Steps

```bash
# 1. Create sample project
mkdir devpod-lab && cd devpod-lab
git init

# 2. Create simple Node.js app
cat > package.json << 'EOF'
{
  "name": "devpod-lab",
  "version": "1.0.0",
  "scripts": {
    "dev": "node server.js",
    "test": "echo 'Tests pass!'"
  },
  "dependencies": {
    "express": "^4.18.0"
  }
}
EOF

cat > server.js << 'EOF'
const express = require('express');
const app = express();

app.get('/', (req, res) => {
  res.json({ message: 'Hello from DevPod!' });
});

app.listen(3000, () => {
  console.log('Server running on http://localhost:3000');
});
EOF

# 3. Create devcontainer configuration
mkdir .devcontainer

cat > .devcontainer/devcontainer.json << 'EOF'
{
  "name": "DevPod Lab",
  "image": "mcr.microsoft.com/devcontainers/javascript-node:20",

  "features": {
    "ghcr.io/devcontainers/features/docker-in-docker:2": {}
  },

  "customizations": {
    "vscode": {
      "extensions": [
        "dbaeumer.vscode-eslint",
        "esbenp.prettier-vscode"
      ],
      "settings": {
        "editor.formatOnSave": true
      }
    }
  },

  "forwardPorts": [3000],

  "postCreateCommand": "npm install",

  "postStartCommand": "npm run dev",

  "remoteUser": "node"
}
EOF

# 4. Commit the configuration
git add .
git commit -m "Add devcontainer configuration"

# 5. Test with DevPod
devpod up . --ide vscode

# 6. Verify server is running
curl http://localhost:3000
# Should return: {"message":"Hello from DevPod!"}
```

### Verification

```bash
# Check workspace is running
devpod list

# SSH into workspace
devpod ssh devpod-lab

# Inside workspace, verify:
node --version  # Should be 20.x
npm --version
curl localhost:3000  # Should return JSON
```

---

## Quiz

### Question 1
What is DevPod?

<details>
<summary>Show Answer</summary>

**An open source tool for running dev environments anywhere, using the Dev Containers spec**

DevPod:
- Reads devcontainer.json configuration
- Provisions infrastructure via providers (Docker, K8s, cloud)
- Starts containerized dev environments
- Connects IDEs via SSH

It's like GitHub Codespaces but self-hosted, provider-agnostic, and free.
</details>

### Question 2
What's the difference between DevPod and Gitpod?

<details>
<summary>Show Answer</summary>

**DevPod is client-only; Gitpod requires a server component**

- **DevPod**: CLI/desktop app that manages providers directly, no central server
- **Gitpod**: SaaS or self-hosted server that manages workspaces

DevPod is simpler to set up but Gitpod offers more centralized management for large organizations.
</details>

### Question 3
What providers does DevPod support?

<details>
<summary>Show Answer</summary>

**Docker (local), Kubernetes, AWS, GCP, Azure, DigitalOcean, SSH, and more**

Providers determine WHERE the dev environment runs:
- Local Docker for quick development
- Kubernetes for team standardization
- Cloud VMs for powerful machines or GPU
- SSH for existing infrastructure

You can use different providers for different projects.
</details>

### Question 4
What is devcontainer.json?

<details>
<summary>Show Answer</summary>

**A standardized configuration file for development containers**

The Dev Containers specification (also used by VS Code and Codespaces) defines:
- Base image or Dockerfile
- Features (tools to install)
- IDE extensions and settings
- Port forwarding
- Post-create/start commands
- Host requirements

This ensures consistent environments across tools and teams.
</details>

### Question 5
How does DevPod connect to IDEs?

<details>
<summary>Show Answer</summary>

**Via SSH into the dev container**

DevPod:
1. Starts a container with SSH server
2. Configures SSH credentials automatically
3. Opens IDE with remote SSH connection
4. VS Code uses Remote-SSH extension
5. JetBrains uses Gateway

The developer experience is seamless—the IDE "just opens."
</details>

### Question 6
What are DevPod features?

<details>
<summary>Show Answer</summary>

**Pre-packaged tool installations for dev containers**

Features are reusable components that add tools:
```json
"features": {
  "ghcr.io/devcontainers/features/docker-in-docker:2": {},
  "ghcr.io/devcontainers/features/kubectl-helm-minikube:1": {}
}
```

They're better than installing tools in Dockerfile because:
- Maintained by the community
- Versioned and tested
- Layer-cached efficiently
</details>

### Question 7
How do you persist data across workspace restarts?

<details>
<summary>Show Answer</summary>

**Use volume mounts in devcontainer.json**

```json
"mounts": [
  "source=devpod-go-cache,target=/go/pkg,type=volume",
  "source=${localEnv:HOME}/.npm,target=/home/node/.npm,type=bind"
]
```

Named volumes persist even when workspaces are deleted. Bind mounts sync with local directories.
</details>

### Question 8
When should you use Kubernetes provider vs Docker provider?

<details>
<summary>Show Answer</summary>

**Kubernetes for teams, Docker for individual developers**

Use Docker when:
- Quick local development
- Offline work
- Simple projects
- Testing devcontainer changes

Use Kubernetes when:
- Team standardization needed
- Powerful machines required
- Consistent environments across team
- Enterprise resource management
</details>

---

## Key Takeaways

1. **Open source Codespaces alternative** - Same experience, your infrastructure
2. **Provider-agnostic** - Docker, Kubernetes, AWS, GCP, Azure, SSH
3. **Uses Dev Containers spec** - Compatible with VS Code, Codespaces
4. **Client-only architecture** - No server to manage
5. **IDE-agnostic** - VS Code, JetBrains, browser, Neovim
6. **Free forever** - Only pay for infrastructure
7. **Features for tooling** - Pre-packaged tool installations
8. **Automate everything** - postCreateCommand, postStartCommand
9. **Perfect for onboarding** - New devs productive in minutes
10. **Kubernetes for teams** - Centralized, consistent environments

---

## Next Steps

- **Next Module**: [Module 8.5: Gitpod & Codespaces](module-8.5-gitpod-codespaces/) - Cloud alternatives
- **Related**: [Module 8.3: Local Kubernetes](module-8.3-local-kubernetes/) - Local K8s for DevPod
- **Related**: [Platform Engineering](../../disciplines/core-platform/platform-engineering/) - Building developer platforms

---

## Further Reading

- [DevPod Documentation](https://devpod.sh/docs)
- [DevPod GitHub Repository](https://github.com/loft-sh/devpod)
- [Dev Containers Specification](https://containers.dev/)
- [Dev Container Features](https://containers.dev/features)
- [VS Code Dev Containers](https://code.visualstudio.com/docs/devcontainers/containers)

---

*"The best development environment is one you don't have to think about. DevPod makes 'it just works' the default."*
