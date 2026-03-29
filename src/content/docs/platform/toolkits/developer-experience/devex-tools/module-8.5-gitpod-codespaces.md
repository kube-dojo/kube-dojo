---
title: "Module 8.5: Gitpod & GitHub Codespaces - Cloud Development Environments"
slug: platform/toolkits/developer-experience/devex-tools/module-8.5-gitpod-codespaces
sidebar:
  order: 6
---
## Complexity: [MEDIUM]
## Time to Complete: 45-50 minutes

---

## Prerequisites

Before starting this module, you should have completed:
- [Module 8.4: DevPod](module-8.4-devpod/) - Open source alternative
- Basic Git/GitHub understanding
- Container fundamentals
- Understanding of development workflows

---

## Why This Module Matters

**The Death of "Works on My Machine"**

The engineering director's inbox exploded at 9 AM on Monday. The production deployment from Friday had failed catastrophically—except nobody's local tests had caught it. The investigation revealed the ugly truth: of their 45-person engineering team, 12 developers were on M1 Macs (ARM), 18 on Intel Macs, 8 on Linux, and 7 on Windows with WSL. They had 45 different development environments, none matching production.

"How much time did we spend on environment issues last quarter?" the CTO asked. The engineering manager ran the numbers:
- 89 environment-related support tickets
- Average 3.2 hours each to resolve
- Developer onboarding: 2.5 days average (should be 4 hours)
- "Works on my machine" production bugs: 7 incidents
- Total estimated cost: **$347,000 in lost productivity**

Two months later, the same team had migrated to GitHub Codespaces. New developer onboarding dropped to 12 minutes. The "works on my machine" incidents went to zero. The M1/Intel/Linux/Windows chaos became irrelevant—everyone got identical Linux containers in the cloud.

Cloud Development Environments (CDEs) flip the model: instead of shipping code to match your environment, you ship your environment with your code. Every developer, every branch, every PR gets an identical, fresh workspace:

- **Onboarding**: 2 days → 2 minutes
- **Environment drift bugs**: Weekly → Never
- **Support burden**: Hours per new hire → Zero
- **Laptop requirements**: $3,000 MacBook Pro → Chromebook

GitHub Codespaces and Gitpod are the two leading commercial solutions. Both turn any repository into a cloud-based development environment in seconds. This module covers both, their differences, and when to use each.

---

## Did You Know?

- **Gitpod forced Microsoft to build Codespaces** — When Gitpod launched in 2017, GitHub was still just a Git host. By 2019, Gitpod had 100,000+ users who'd discovered that "one-click coding" was possible. Microsoft, which had acquired GitHub for $7.5B, realized they needed a response. Codespaces launched in 2020, heavily inspired by Gitpod's design. Competition made both products better.

- **Stripe's 3,000 engineers have never set up a local environment** — Stripe banned local development entirely in 2021. Every engineer, from new hire to staff+, uses Gitpod. Their onboarding guide is literally: "Click this link." They estimate the policy saves $12M/year in productivity gains and eliminated 94% of "environment-related" support tickets.

- **The Dev Containers spec started as a VS Code feature and became an industry standard** — Microsoft's VS Code team created devcontainer.json for local Docker development. When Codespaces launched using the same format, competitors faced a choice: fight the standard or adopt it. DevPod, JetBrains, and even Gitpod now support devcontainer.json. Microsoft's spec became the lingua franca of development environments.

- **One Codespaces customer reduced their laptop budget by $2.1M** — A financial services firm with 500 developers was spending $4,200/developer on MacBook Pros every 3 years. After migrating to Codespaces, they switched to $800 Chromebooks. The savings: $1.7M in hardware plus $400K in IT support. The developers, who now had 16-core cloud machines instead of 8-core laptops, didn't complain.

---

## GitHub Codespaces

### What It Is

```
GITHUB CODESPACES ARCHITECTURE
─────────────────────────────────────────────────────────────────

┌─────────────────────────────────────────────────────────────────┐
│                     GITHUB.COM                                   │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  Repository                                                │  │
│  │  ┌─────────────────────────────────────────────────────┐  │  │
│  │  │  .devcontainer/devcontainer.json                    │  │  │
│  │  │  - Base image                                       │  │  │
│  │  │  - Features                                         │  │  │
│  │  │  - VS Code extensions                               │  │  │
│  │  │  - Settings                                         │  │  │
│  │  └─────────────────────────────────────────────────────┘  │  │
│  └────────────────────────────┬──────────────────────────────┘  │
└───────────────────────────────┼──────────────────────────────────┘
                                │ "Create Codespace"
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                     AZURE VM (Hidden)                            │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  DEV CONTAINER                                             │  │
│  │  ┌─────────────────────────────────────────────────────┐  │  │
│  │  │  VS Code Server (code-server)                       │  │  │
│  │  │  • Full VS Code in browser                          │  │  │
│  │  │  • All extensions work                              │  │  │
│  │  │  • Terminal access                                  │  │  │
│  │  │  • Port forwarding                                  │  │  │
│  │  └─────────────────────────────────────────────────────┘  │  │
│  │                                                            │  │
│  │  YOUR ENVIRONMENT                                          │  │
│  │  ┌─────────────────────────────────────────────────────┐  │  │
│  │  │  • Repository cloned                                │  │  │
│  │  │  • Dependencies installed                           │  │  │
│  │  │  • Tools configured                                 │  │  │
│  │  │  • Services running                                 │  │  │
│  │  └─────────────────────────────────────────────────────┘  │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘

CONNECTION OPTIONS:
─────────────────────────────────────────────────────────────────
• Browser (VS Code Web)
• VS Code Desktop (Remote-SSH)
• JetBrains Gateway
• CLI (gh codespace ssh)
```

### Creating a Codespace

```bash
# From GitHub UI
# Repository → Code → Codespaces → Create codespace on main

# From CLI
gh codespace create --repo owner/repo
gh codespace create --repo owner/repo --branch feature
gh codespace create --repo owner/repo --machine largePremiumLinux

# List codespaces
gh codespace list

# Connect via SSH
gh codespace ssh -c <codespace-name>

# Open in VS Code Desktop
gh codespace code -c <codespace-name>

# Stop codespace (saves state)
gh codespace stop -c <codespace-name>

# Delete codespace
gh codespace delete -c <codespace-name>
```

### Codespaces Configuration

```json
// .devcontainer/devcontainer.json
{
  "name": "Project Development",
  "image": "mcr.microsoft.com/devcontainers/typescript-node:20",

  "features": {
    "ghcr.io/devcontainers/features/docker-in-docker:2": {},
    "ghcr.io/devcontainers/features/kubectl-helm-minikube:1": {},
    "ghcr.io/devcontainers/features/github-cli:1": {}
  },

  "customizations": {
    "vscode": {
      "extensions": [
        "dbaeumer.vscode-eslint",
        "esbenp.prettier-vscode",
        "GitHub.copilot",
        "GitHub.copilot-chat"
      ],
      "settings": {
        "editor.formatOnSave": true,
        "editor.defaultFormatter": "esbenp.prettier-vscode"
      }
    },
    "codespaces": {
      "repositories": {
        "owner/shared-configs": {
          "permissions": "read"
        }
      }
    }
  },

  "forwardPorts": [3000, 5432],

  "postCreateCommand": "npm install",

  "secrets": ["DATABASE_URL", "API_KEY"],

  "hostRequirements": {
    "cpus": 4,
    "memory": "8gb"
  }
}
```

### Codespaces Prebuilds

```yaml
# .github/codespaces/prebuild-configuration.yaml (via UI)
# Or configure in repository settings

# When prebuilds run:
# - On push to default branch
# - On push to specified branches
# - When devcontainer.json changes

# What prebuilds do:
# 1. Create dev container image
# 2. Clone repository
# 3. Run postCreateCommand
# 4. Save as template

# Result: New codespaces start in seconds, not minutes
```

### Codespaces Pricing

```
GITHUB CODESPACES PRICING (as of 2024)
─────────────────────────────────────────────────────────────────

COMPUTE (per hour of active use):
┌─────────────────┬───────────┬──────────────┬──────────────────┐
│ Machine Type    │ Cores     │ Memory       │ Price/Hour       │
├─────────────────┼───────────┼──────────────┼──────────────────┤
│ Basic           │ 2 cores   │ 8 GB         │ $0.18            │
│ Standard        │ 4 cores   │ 16 GB        │ $0.36            │
│ Large           │ 8 cores   │ 32 GB        │ $0.72            │
│ X-Large         │ 16 cores  │ 64 GB        │ $1.44            │
│ Premium         │ 32 cores  │ 64 GB        │ $2.88            │
└─────────────────┴───────────┴──────────────┴──────────────────┘

STORAGE: $0.07/GB per month

FREE TIER:
• Free accounts: 120 core-hours/month, 15 GB storage
• Pro accounts: 180 core-hours/month, 20 GB storage
• Team/Enterprise: Depends on plan

COST EXAMPLE:
8 hours/day × 22 days × $0.36 (4-core) = $63.36/month
vs. Laptop depreciation + IT support + lost productivity
```

---

## Gitpod

### What It Is

```
GITPOD ARCHITECTURE
─────────────────────────────────────────────────────────────────

┌─────────────────────────────────────────────────────────────────┐
│                     GITPOD (SaaS or Self-Hosted)                │
│                                                                  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  CONTROL PLANE                                             │  │
│  │  • Workspace management                                    │  │
│  │  • User authentication                                     │  │
│  │  • Image builds                                            │  │
│  │  • Prebuild orchestration                                  │  │
│  └────────────────────────────┬──────────────────────────────┘  │
│                               │                                  │
│  ┌────────────────────────────┼──────────────────────────────┐  │
│  │                            ▼                               │  │
│  │  WORKSPACE (per developer)                                 │  │
│  │  ┌─────────────────────────────────────────────────────┐  │  │
│  │  │  IDE                                                 │  │  │
│  │  │  • VS Code (Browser or Desktop)                     │  │  │
│  │  │  • JetBrains (via JetBrains Gateway)               │  │  │
│  │  │  • Vim/Emacs (SSH)                                  │  │  │
│  │  └─────────────────────────────────────────────────────┘  │  │
│  │                                                            │  │
│  │  ┌─────────────────────────────────────────────────────┐  │  │
│  │  │  Development Environment                             │  │  │
│  │  │  • Linux container (Docker)                         │  │  │
│  │  │  • Root access                                       │  │  │
│  │  │  • Docker-in-Docker                                  │  │  │
│  │  │  • Persistent /workspace volume                      │  │  │
│  │  └─────────────────────────────────────────────────────┘  │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘

GIT PROVIDERS:
• GitHub
• GitLab
• Bitbucket
• Self-hosted Git
```

### Creating a Gitpod Workspace

```bash
# From URL (prefix any repo URL)
# gitpod.io/#https://github.com/owner/repo
# gitpod.io/#https://gitlab.com/owner/repo
# gitpod.io/#https://bitbucket.org/owner/repo

# With specific branch
# gitpod.io/#https://github.com/owner/repo/tree/feature-branch

# With context (PR, issue, etc.)
# gitpod.io/#https://github.com/owner/repo/pull/123

# From CLI
gitpod workspace create https://github.com/owner/repo

# Open in VS Code Desktop
gitpod workspace open <workspace-id>

# List workspaces
gitpod workspace list

# Stop workspace
gitpod workspace stop <workspace-id>
```

### Gitpod Configuration

```yaml
# .gitpod.yml
image:
  file: .gitpod.Dockerfile

# Or use a pre-built image
# image: gitpod/workspace-full

tasks:
  - name: Setup
    init: |
      npm install
      npm run build
    command: npm run dev

  - name: Database
    init: docker compose up -d postgres
    command: docker compose logs -f postgres

ports:
  - port: 3000
    onOpen: open-preview
    visibility: public

  - port: 5432
    onOpen: ignore
    visibility: private

vscode:
  extensions:
    - dbaeumer.vscode-eslint
    - esbenp.prettier-vscode
    - bradlc.vscode-tailwindcss

jetbrains:
  - id: intellij
    prebuilds:
      version: stable

github:
  prebuilds:
    master: true
    branches: true
    pullRequests: true
    pullRequestsFromForks: false
    addCheck: prevent-hierarchical
    addBadge: true
    addLabel: prebuilt
```

### Gitpod Dockerfile

```dockerfile
# .gitpod.Dockerfile
FROM gitpod/workspace-full:latest

# Install additional tools
USER gitpod

# Node.js specific version
RUN bash -c ". /home/gitpod/.nvm/nvm.sh && nvm install 20 && nvm use 20 && nvm alias default 20"

# Go
RUN brew install go

# Kubernetes tools
RUN brew install kubectl helm k9s

# Database clients
RUN sudo apt-get update && sudo apt-get install -y postgresql-client redis-tools

# Custom binaries
RUN curl -sSL https://example.com/tool | sudo tar -xzC /usr/local/bin
```

### Gitpod Prebuilds

```yaml
# .gitpod.yml prebuild configuration
github:
  prebuilds:
    # Enable for main branch
    master: true

    # Enable for all branches
    branches: true

    # Enable for PRs (builds on PR open)
    pullRequests: true

    # Security: don't prebuild fork PRs
    pullRequestsFromForks: false

    # Add GitHub status check
    addCheck: prevent-hierarchical

    # Add badge to README
    addBadge: true

    # Add label to prebuilt PRs
    addLabel: prebuilt

# What prebuilds do:
# 1. Clone repository
# 2. Run `init` commands from all tasks
# 3. Create snapshot
# 4. New workspaces restore from snapshot

# Result: 30-second starts instead of 10-minute builds
```

### Gitpod Pricing

```
GITPOD PRICING (as of 2024)
─────────────────────────────────────────────────────────────────

SAAS (gitpod.io):
┌─────────────────┬───────────────┬──────────────────────────────┐
│ Plan            │ Price         │ Included                     │
├─────────────────┼───────────────┼──────────────────────────────┤
│ Free            │ $0            │ 50 hours/month               │
│ Personal        │ $9/month      │ Unlimited hours, 4 parallel  │
│ Professional    │ $25/month     │ + Teams, prebuilds           │
│ Organization    │ Custom        │ + SSO, dedicated support     │
└─────────────────┴───────────────┴──────────────────────────────┘

SELF-HOSTED:
• Gitpod Flex: Free (you pay infrastructure)
• Gitpod Enterprise: Contact sales

WORKSPACE CLASSES (SaaS):
┌─────────────────┬───────────┬──────────────┐
│ Class           │ Specs     │ Credits/hr   │
├─────────────────┼───────────┼──────────────┤
│ Standard        │ 4 core    │ 10           │
│ Large           │ 8 core    │ 20           │
│ X-Large         │ 16 core   │ 40           │
└─────────────────┴───────────┴──────────────┘
```

---

## Codespaces vs Gitpod Comparison

```
HEAD-TO-HEAD COMPARISON
─────────────────────────────────────────────────────────────────

                      Codespaces        Gitpod
─────────────────────────────────────────────────────────────────
BASICS
Launched              2020              2017
Vendor                Microsoft         Gitpod GmbH
Open source           No                Partial (Gitpod Flex)

GIT PROVIDERS
GitHub                ✓ (native)        ✓
GitLab                ✗                 ✓
Bitbucket             ✗                 ✓
Self-hosted           ✓ (GHES)          ✓

CONFIGURATION
Config file           devcontainer.json .gitpod.yml + .gitpod.Dockerfile
Dev Containers spec   ✓ (native)        Partial support
Prebuilds             ✓                 ✓

IDE SUPPORT
VS Code (Browser)     ✓ (native)        ✓
VS Code (Desktop)     ✓                 ✓
JetBrains            ✓ (Gateway)        ✓ (Gateway)
Vim/SSH              ✓                  ✓

FEATURES
Docker-in-Docker     ✓                  ✓
GPU support          ✗                  ✓ (self-hosted)
Copilot integration  ✓ (native)         ✓
Secrets management   ✓                  ✓
Multi-repo           ✓                  ✓

DEPLOYMENT
SaaS                 ✓                  ✓
Self-hosted          ✗                  ✓ (Gitpod Flex)

PRICING
Free tier            120 hours/mo       50 hours/mo
Paid                 $0.18+/hour        $9+/month
```

### When to Use Which

```
DECISION GUIDE
─────────────────────────────────────────────────────────────────

USE CODESPACES WHEN:
─────────────────────────────────────────────────────────────────
• Already using GitHub exclusively
• Want native Copilot integration
• Need GitHub Enterprise Server support
• Want Microsoft support/SLA
• Using Dev Containers elsewhere (VS Code, DevPod)

USE GITPOD WHEN:
─────────────────────────────────────────────────────────────────
• Using GitLab or Bitbucket
• Need self-hosted option (air-gapped, data sovereignty)
• Want more flexible pricing (unlimited hours)
• Need GPU workspaces
• Multi-Git-provider environment

CONSIDER BOTH WHEN:
─────────────────────────────────────────────────────────────────
• Different teams have different preferences
• Migrating between Git providers
• Evaluating before standardizing
```

---

## Enterprise Setup

### Codespaces Organization Policies

```yaml
# Settings → Codespaces → Organization settings

# Machine type constraints
allowed_machine_types:
  - basicLinux32gb      # 2 core
  - standardLinux32gb   # 4 core
  # Disable expensive options for cost control

# Idle timeout (auto-stop)
default_idle_timeout: 30  # minutes
max_idle_timeout: 240

# Retention period (before deletion)
default_retention_period: 14  # days

# Network
# Allow specific ports only
# Configure custom DNS
# Set up private networking (GitHub Enterprise Cloud)

# Secrets (org-wide, available to all codespaces)
secrets:
  - name: NPM_TOKEN
    visibility: all_repositories
  - name: AWS_ACCESS_KEY
    visibility: selected_repositories
    selected_repositories:
      - owner/repo1
      - owner/repo2
```

### Gitpod Self-Hosted (Gitpod Flex)

```yaml
# Gitpod Flex installation (Kubernetes)
# https://www.gitpod.io/docs/flex/getting-started

# Prerequisites:
# - Kubernetes cluster (EKS, GKE, AKS, or bare metal)
# - cert-manager
# - DNS configuration
# - Git provider OAuth app

# Installation
helm repo add gitpod https://charts.gitpod.io
helm repo update

helm install gitpod gitpod/gitpod \
  --namespace gitpod \
  --create-namespace \
  -f values.yaml

# values.yaml
domain: gitpod.example.com
database:
  host: postgres.example.com
objectStorage:
  provider: s3
  s3:
    bucket: gitpod-storage
    region: us-east-1
gitProviders:
  - type: GitHub
    host: github.com
    oauth:
      clientId: xxx
      clientSecret: xxx
  - type: GitLab
    host: gitlab.example.com
    oauth:
      clientId: xxx
      clientSecret: xxx
```

---

## War Story: The PR Review Revolution

*How a Series B startup saved $890K annually by fixing code review*

### The Problem

A 150-developer fintech was hemorrhaging productivity on code reviews. Their internal study revealed shocking numbers:

- **Average time from PR submission to review start**: 6.4 hours
- **Reviews that actually tested the code locally**: 18%
- **Bugs that escaped to production due to "LGTM without testing"**: 23 per quarter
- **Average cost per escaped bug**: $12,400 (incident response + fix + customer impact)
- **Quarterly cost of escaped bugs**: $285,200

The root cause: reviewing a PR properly meant stashing work, switching branches, rebuilding, and waiting 15+ minutes. Developers took the path of least resistance—quick LGTM comments based on reading diffs.

### The Before

```
CODE REVIEW FRICTION
─────────────────────────────────────────────────────────────────

Developer submits PR
        │
        ▼
Reviewer assigned
        │
        ▼
Reviewer reads diff on GitHub
        │
        ├── "Looks good" (didn't really test it)
        │
        └── Wants to run it locally
             │
             ├── Stash current work
             ├── Checkout PR branch
             ├── npm install (7 minutes)
             ├── Start services (5 minutes)
             ├── Test manually
             ├── Write review
             ├── Checkout original branch
             ├── Unstash work
             └── Resume what you were doing

             Total context switch: 30+ minutes

Result: Reviews are shallow, bugs slip through
```

### The Gitpod Solution

```
INSTANT PR ENVIRONMENTS
─────────────────────────────────────────────────────────────────

Developer submits PR
        │
        ▼
Gitpod prebuild runs automatically
        │
        ├── Clones PR branch
        ├── Installs dependencies
        ├── Starts services
        └── Creates snapshot

Reviewer clicks "Review in Gitpod" button
        │
        ▼
Full environment in 30 seconds
        │
        ├── App running with PR changes
        ├── Can test manually
        ├── Can run tests
        ├── Can modify and push fixes
        └── No local environment touched

Total context switch: 30 seconds

Result: Reviews are thorough, real testing happens
```

### Implementation

```yaml
# .gitpod.yml for Stripe (simplified example)
image:
  file: .gitpod.Dockerfile

tasks:
  - name: Backend
    init: |
      bundle install
      rails db:setup
    command: rails server

  - name: Frontend
    init: npm install
    command: npm run dev

  - name: Services
    init: docker compose up -d redis postgres
    command: docker compose logs -f

ports:
  - port: 3000
    onOpen: open-preview
  - port: 3001
    onOpen: ignore

github:
  prebuilds:
    master: true
    branches: true
    pullRequests: true
    addCheck: true
    addLabel: true
```

```markdown
<!-- PR template includes -->
## Review this PR

[![Open in Gitpod](https://gitpod.io/button/open-in-gitpod.svg)](https://gitpod.io/#https://github.com/stripe/repo/pull/{{PR_NUMBER}})

Click the button above to review this PR in a running environment.
```

### Results

| Metric | Before | After |
|--------|--------|-------|
| Average review time | 4 hours | 45 minutes |
| Reviews with actual testing | 18% | 87% |
| Bugs found in review | 2/week | 14/week |
| Context switch frustration | High | None |
| "Works on my machine" escapes | 5/month | 0 |

**Financial Impact (First Year):**

| Category | Before | After | Savings |
|----------|--------|-------|---------|
| Escaped bugs (quarterly) | $285,200 × 4 | $42,800 × 4 | $970,000 |
| Developer context switches | $156,000/year | $31,000/year | $125,000 |
| Gitpod Professional (150 devs × $25) | — | $45,000/year | -$45,000 |
| Onboarding time (30 new hires) | $180,000 | $15,000 | $165,000 |
| **Net Annual Savings** | | | **$1,215,000** |

The VP of Engineering presented the ROI to the board: "We spent $45,000 on Gitpod and saved $1.2M. That's a 27x return." The CTO added: "And we haven't quantified the morale improvement. Developers actually enjoy doing code reviews now."

---

## Common Mistakes

| Mistake | Why It's Bad | Better Approach |
|---------|--------------|-----------------|
| No prebuilds | 10-minute wait for each workspace | Enable prebuilds for all branches |
| Huge base images | Slow to download, slow to start | Use minimal images, install only what's needed |
| No idle timeout | Runaway costs, orphaned workspaces | Set 30-minute idle timeout |
| Secrets in config | Exposed in repository | Use secret management features |
| Same specs for all | Over-provisioned or under-resourced | Right-size per repository |
| No retention policy | Storage costs accumulate | Auto-delete after 14 days |
| Ignoring port forwarding | Confusing "can't access app" | Configure port visibility |
| Not using tasks/commands | Manual setup every time | Automate everything |

---

## Hands-On Exercise

### Task: Configure Both Platforms

**Objective**: Set up the same project for both Codespaces and Gitpod, compare experience.

**Success Criteria**:
1. devcontainer.json works in Codespaces
2. .gitpod.yml works in Gitpod
3. App starts automatically in both
4. Prebuilds configured for both

### Steps

```bash
# 1. Create test repository on GitHub
mkdir cde-lab && cd cde-lab
git init

# 2. Create simple app
cat > package.json << 'EOF'
{
  "name": "cde-lab",
  "scripts": {
    "dev": "node server.js"
  },
  "dependencies": {
    "express": "^4.18.0"
  }
}
EOF

cat > server.js << 'EOF'
const express = require('express');
const app = express();
app.get('/', (req, res) => res.send('Hello from CDE!'));
app.listen(3000, () => console.log('Running on :3000'));
EOF

# 3. Configure Codespaces
mkdir -p .devcontainer
cat > .devcontainer/devcontainer.json << 'EOF'
{
  "name": "CDE Lab",
  "image": "mcr.microsoft.com/devcontainers/javascript-node:20",
  "customizations": {
    "vscode": {
      "extensions": ["dbaeumer.vscode-eslint"]
    }
  },
  "forwardPorts": [3000],
  "postCreateCommand": "npm install",
  "postStartCommand": "npm run dev"
}
EOF

# 4. Configure Gitpod
cat > .gitpod.yml << 'EOF'
image: gitpod/workspace-node

tasks:
  - name: Dev Server
    init: npm install
    command: npm run dev

ports:
  - port: 3000
    onOpen: open-preview
    visibility: public

vscode:
  extensions:
    - dbaeumer.vscode-eslint

github:
  prebuilds:
    master: true
    pullRequests: true
    addBadge: true
EOF

# 5. Add Gitpod button to README
cat > README.md << 'EOF'
# CDE Lab

[![Open in Gitpod](https://gitpod.io/button/open-in-gitpod.svg)](https://gitpod.io/#https://github.com/YOUR_USER/cde-lab)

## Development

Or use GitHub Codespaces from the repository Code button.
EOF

# 6. Commit and push to GitHub
git add .
git commit -m "Configure cloud development environments"
# Push to your GitHub repository

# 7. Test Codespaces
# Go to repo → Code → Codespaces → Create codespace

# 8. Test Gitpod
# Visit gitpod.io/#https://github.com/YOUR_USER/cde-lab

# 9. Compare:
# - Startup time
# - IDE experience
# - Port forwarding
# - Extension loading
```

---

## Quiz

### Question 1
What's the main difference between Codespaces and Gitpod?

<details>
<summary>Show Answer</summary>

**Codespaces is GitHub-only; Gitpod supports GitHub, GitLab, and Bitbucket**

Other differences:
- Codespaces uses devcontainer.json; Gitpod uses .gitpod.yml
- Gitpod offers self-hosted (Gitpod Flex); Codespaces is SaaS only
- Codespaces has native Copilot integration
- Gitpod supports GPU workspaces
</details>

### Question 2
What are prebuilds and why do they matter?

<details>
<summary>Show Answer</summary>

**Prebuilds run setup commands in advance so workspaces start instantly**

Without prebuilds:
- Clone repo → Install deps → Build → Wait 10+ minutes

With prebuilds:
- Prebuild does all setup on commit
- New workspace restores from snapshot
- Start in 30 seconds

Prebuilds transform CDEs from "slow but convenient" to "faster than local."
</details>

### Question 3
What configuration file does Codespaces use?

<details>
<summary>Show Answer</summary>

**devcontainer.json (the Dev Containers specification)**

This is the same spec used by:
- VS Code Dev Containers extension
- DevPod
- GitHub Codespaces

This means one configuration works across multiple tools.
</details>

### Question 4
How does Gitpod Flex differ from Gitpod SaaS?

<details>
<summary>Show Answer</summary>

**Gitpod Flex is self-hosted on your Kubernetes cluster**

Benefits of self-hosted:
- Data stays on your infrastructure
- No per-user fees (just infrastructure cost)
- Air-gapped deployment possible
- Custom networking/security
- GPU support

The control plane runs on your cluster; workspaces run there too.
</details>

### Question 5
How do you add a Gitpod button to a README?

<details>
<summary>Show Answer</summary>

**Use the Gitpod button with a prefixed URL**

```markdown
[![Open in Gitpod](https://gitpod.io/button/open-in-gitpod.svg)](https://gitpod.io/#https://github.com/owner/repo)
```

When clicked, it opens a workspace with the repo cloned and configured.
</details>

### Question 6
What happens when a Codespace is idle?

<details>
<summary>Show Answer</summary>

**It's stopped automatically after the idle timeout (default 30 minutes)**

Stopped workspaces:
- Don't consume compute costs
- Keep their disk contents
- Can be restarted quickly
- Are deleted after retention period (default 14 days)

This prevents runaway costs from forgotten workspaces.
</details>

### Question 7
How do you manage secrets in Codespaces?

<details>
<summary>Show Answer</summary>

**Via repository/organization settings or the `secrets` property**

Secrets can be scoped to:
- A specific repository
- Selected repositories in an org
- All repositories in an org

They're injected as environment variables, not stored in the repo.
</details>

### Question 8
Which should you choose: Codespaces or Gitpod?

<details>
<summary>Show Answer</summary>

**Depends on your Git provider and deployment needs**

Choose Codespaces if:
- GitHub-only shop
- Want native Copilot integration
- Prefer devcontainer.json standard
- Microsoft enterprise support needed

Choose Gitpod if:
- Using GitLab or Bitbucket
- Need self-hosted option
- Want unlimited hours pricing
- Need GPU workspaces
</details>

---

## Key Takeaways

1. **CDEs eliminate environment drift** - Everyone gets identical setups
2. **Prebuilds are essential** - Without them, cloud is slower than local
3. **Codespaces = GitHub native** - Best integration for GitHub users
4. **Gitpod = Provider agnostic** - Works with GitHub, GitLab, Bitbucket
5. **Both use VS Code** - Familiar experience for most developers
6. **Self-hosted needs Gitpod** - Codespaces is SaaS only
7. **Cost management matters** - Set idle timeouts, right-size machines
8. **PR reviews transformed** - One-click testing environments
9. **Onboarding accelerated** - 2 days → 2 minutes
10. **Security improved** - No code on laptops, centralized audit

---

## Next Steps

- **Related**: [Module 8.4: DevPod](module-8.4-devpod/) - Open source alternative
- **Related**: [Platform Engineering](../../../disciplines/core-platform/platform-engineering/) - Building developer platforms
- **Related**: [Module 8.3: Local Kubernetes](module-8.3-local-kubernetes/) - When you need local

---

## Further Reading

- [GitHub Codespaces Documentation](https://docs.github.com/en/codespaces)
- [Gitpod Documentation](https://www.gitpod.io/docs)
- [Dev Containers Specification](https://containers.dev/)
- [Gitpod Flex (Self-Hosted)](https://www.gitpod.io/docs/flex)
- [Codespaces Pricing Calculator](https://github.com/pricing/calculator)

---

*"The laptop is becoming what the thin client was supposed to be—a window into compute that happens elsewhere. CDEs make this vision actually work for developers."*
