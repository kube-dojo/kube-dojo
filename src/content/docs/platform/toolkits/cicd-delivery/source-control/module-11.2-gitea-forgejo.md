---
title: "Module 11.2: Gitea & Forgejo - Lightweight Self-Hosted Git"
slug: platform/toolkits/cicd-delivery/source-control/module-11.2-gitea-forgejo
sidebar:
  order: 3
---
## Complexity: [MEDIUM]
## Time to Complete: 45-50 minutes

---

## Prerequisites

Before starting this module, you should have completed:
- [GitOps Discipline](../../../disciplines/delivery-automation/gitops/) - Git-centric workflows
- Basic Git fundamentals (branches, remotes, hooks)
- Container/Kubernetes basics
- Understanding of why self-hosting matters

---

## What You'll Be Able to Do

After completing this module, you will be able to:

- **Deploy Gitea or Forgejo on Kubernetes as a lightweight self-hosted Git platform**
- **Configure Gitea Actions for CI/CD workflows compatible with GitHub Actions syntax**
- **Implement repository mirroring, webhooks, and OAuth2 authentication for team workflows**
- **Compare Gitea and Forgejo resource footprints against GitLab for small-to-medium team requirements**


## Why This Module Matters

**When GitHub Is Too Much and Too Little**

The security officer's face went pale as she reviewed the audit findings. A defense contractor's classified automation scripts had been stored on a developer's personal GitHub account for three years. No malicious intent—the engineer just needed version control and GitHub was what he knew. The resulting security incident cost the company $2.3 million in investigation costs, remediation, and lost contract opportunities. The fix? A Git server that could run inside their air-gapped network.

Three thousand miles away, a semiconductor fab faced a different problem. Their equipment automation team needed version control, but their entire edge compute infrastructure ran on Raspberry Pi 4s with 4GB RAM each. The IT team tried GitLab Omnibus—it demanded 8GB RAM minimum just to start. The licensing quote for GitHub Enterprise Server came back at $180,000 annually. For a Git server. To store shell scripts.

Meanwhile, a startup's platform team was drowning in tool sprawl. GitHub for code, Jenkins for CI, Artifactory for packages, separate LDAP integration for each. Every vendor wanted enterprise pricing. The engineering budget was already stretched thin, and they just needed... a Git server that worked.

Gitea exists because not everyone needs an enterprise platform. Sometimes you need a Git server that's small, fast, self-contained, and just works—a single binary that runs on anything from a $35 Raspberry Pi to a massive Kubernetes cluster. GitHub's features with none of GitHub's baggage.

Forgejo is Gitea's community fork—same codebase, different governance. When Gitea's parent company started making decisions the community disagreed with, Forgejo emerged as the "truly open" alternative. They're 95% identical today, but the philosophical differences matter if you're choosing for the long term.

---

## Did You Know?

- **Gitea runs in ~100MB of RAM** - GitLab requires 4GB minimum. A hobbyist in Germany runs 15 separate Gitea instances on a single 4GB VPS—one per open source project—spending less on hosting than a single GitLab license would cost. The entire setup costs him €5/month.

- **Forgejo was born from a governance crisis** - In October 2022, Gitea's maintainers transferred the project to a for-profit company without community consultation. Within weeks, Forgejo forked under Codeberg e.V., a German non-profit. The split highlighted a fundamental question: who owns open source projects when maintainers commercialize?

- **Codeberg.org runs entirely on Forgejo** - Over 100,000 users and 150,000+ repositories run on Codeberg's Forgejo instance, proving the platform scales far beyond "toy project" status. It's become the de facto home for developers who want a GitHub alternative without corporate ownership.

- **The Gitea/Gogs lineage traces back to GitHub itself** - Gogs (Go Git Service) was created in 2014 as a "self-hosted GitHub clone." When Gogs development slowed, Gitea forked in 2016. When Gitea commercialized, Forgejo forked in 2022. Each fork happened because communities wanted faster, more open development than the parent project offered.

---

## Gitea vs Forgejo: The Fork Story

```
THE GITEA/FORGEJO TIMELINE
─────────────────────────────────────────────────────────────────

2016: Gogs created (Go Git Service)
      │
      └──▶ Community wants more features, faster development

2016: Gitea forks from Gogs
      │ "Community-driven, open governance"
      │
      ├── 2017-2022: Rapid growth, GitHub-like features
      │
      └──▶ 2022: Gitea Ltd formed (for-profit company)
           │
           ├── Some contributors concerned about direction
           │
           └──▶ 2022: Forgejo forks from Gitea
                "Truly community-governed, non-profit"

TODAY:
┌─────────────────────────────────────────────────────────────────┐
│                                                                  │
│  GITEA                          FORGEJO                         │
│  ─────                          ───────                         │
│  Gitea Ltd (company)            Codeberg e.V. (non-profit)     │
│  Faster feature releases        Community-first decisions       │
│  Commercial support available   Volunteer-driven support        │
│  95% same code                  95% same code                   │
│                                                                  │
│  Which to choose?                                               │
│  • Need commercial support? → Gitea                             │
│  • Want community governance? → Forgejo                         │
│  • Air-gapped deployment? → Either works                        │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Architecture Deep Dive

### Gitea's Elegant Simplicity

```
┌─────────────────────────────────────────────────────────────────┐
│                      GITEA ARCHITECTURE                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                    Single Go Binary                        │  │
│  │                                                            │  │
│  │  ┌─────────┬─────────┬─────────┬─────────┬─────────────┐  │  │
│  │  │  Git    │  Web    │  API    │ Webhooks│   Actions   │  │  │
│  │  │ Server  │   UI    │  REST   │ Delivery│   Runner    │  │  │
│  │  └─────────┴─────────┴─────────┴─────────┴─────────────┘  │  │
│  │                          │                                 │  │
│  │                          ▼                                 │  │
│  │  ┌─────────────────────────────────────────────────────┐  │  │
│  │  │                    ORM Layer                         │  │  │
│  │  │        XORM (supports multiple databases)           │  │  │
│  │  └─────────────────────────────────────────────────────┘  │  │
│  └────────────────────────────┬──────────────────────────────┘  │
│                               │                                  │
│  ┌────────────────────────────┼──────────────────────────────┐  │
│  │                            │                               │  │
│  │  ┌──────────┐    ┌────────┴────────┐    ┌──────────────┐ │  │
│  │  │ Database │    │  File Storage   │    │   Git Repos  │ │  │
│  │  │SQLite/PG │    │  (local/S3)     │    │(local/NFS)   │ │  │
│  │  │MySQL/MSSQL    └─────────────────┘    └──────────────┘ │  │
│  │  └──────────┘                                            │  │
│  │                                                           │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                  │
│  Optional Components:                                            │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────────────┐    │
│  │ Redis Cache  │  │ Actions Runner│  │ External Auth     │    │
│  │ (optional)   │  │ (for CI/CD)   │  │ (LDAP/OAuth/SAML) │    │
│  └──────────────┘  └──────────────┘  └────────────────────┘    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘

CONTRAST WITH GITLAB:
─────────────────────────────────────────────────────────────────
Gitea:  1 binary, 1 config file, optional database
GitLab: Rails app, Sidekiq, PostgreSQL, Redis, Gitaly, Praefect...

Resource Requirements:
                Gitea           GitLab
─────────────────────────────────────────────────────────────────
RAM             100MB           4GB minimum
CPU             1 core          2+ cores
Disk            ~50MB binary    5GB+ installation
Startup         Seconds         Minutes
```

### Supported Backends

| Component | Options | Notes |
|-----------|---------|-------|
| **Database** | SQLite, PostgreSQL, MySQL, MSSQL | SQLite fine for small teams (<100 users) |
| **Git Storage** | Local filesystem, NFS | Use fast SSD for best performance |
| **LFS Storage** | Local, S3, MinIO, Azure Blob | Required for large file support |
| **Cache** | Built-in, Redis | Redis optional but helps at scale |
| **Search** | Built-in, Elasticsearch | Elasticsearch for code search at scale |

---

## Deployment Options

### Option 1: Single Binary (Simplest)

```bash
# Download latest release
wget https://dl.gitea.io/gitea/1.21/gitea-1.21.0-linux-amd64
chmod +x gitea-1.21.0-linux-amd64
mv gitea-1.21.0-linux-amd64 /usr/local/bin/gitea

# Create user and directories
useradd --system --shell /bin/bash --comment 'Gitea' \
  --create-home --home-dir /var/lib/gitea gitea

mkdir -p /var/lib/gitea/{custom,data,log}
mkdir -p /etc/gitea
chown -R gitea:gitea /var/lib/gitea /etc/gitea

# Run directly (for testing)
sudo -u gitea gitea web --config /etc/gitea/app.ini

# Or create systemd service
cat > /etc/systemd/system/gitea.service << 'EOF'
[Unit]
Description=Gitea
After=network.target

[Service]
Type=simple
User=gitea
Group=gitea
WorkingDirectory=/var/lib/gitea
ExecStart=/usr/local/bin/gitea web --config /etc/gitea/app.ini
Restart=always
Environment=USER=gitea HOME=/var/lib/gitea

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable --now gitea
```

### Option 2: Docker Compose (Recommended for Production)

```yaml
# docker-compose.yml
version: '3'

services:
  gitea:
    image: gitea/gitea:1.21
    container_name: gitea
    environment:
      - USER_UID=1000
      - USER_GID=1000
      - GITEA__database__DB_TYPE=postgres
      - GITEA__database__HOST=db:5432
      - GITEA__database__NAME=gitea
      - GITEA__database__USER=gitea
      - GITEA__database__PASSWD=gitea
      - GITEA__server__ROOT_URL=https://git.example.com
      - GITEA__server__SSH_DOMAIN=git.example.com
      - GITEA__server__SSH_PORT=2222
      - GITEA__mailer__ENABLED=true
      - GITEA__mailer__SMTP_ADDR=smtp.example.com
      - GITEA__mailer__SMTP_PORT=587
    restart: always
    volumes:
      - ./gitea-data:/data
      - /etc/timezone:/etc/timezone:ro
      - /etc/localtime:/etc/localtime:ro
    ports:
      - "3000:3000"   # Web UI
      - "2222:22"     # SSH
    depends_on:
      - db
    networks:
      - gitea

  db:
    image: postgres:15-alpine
    container_name: gitea-db
    restart: always
    environment:
      - POSTGRES_USER=gitea
      - POSTGRES_PASSWORD=gitea
      - POSTGRES_DB=gitea
    volumes:
      - ./postgres-data:/var/lib/postgresql/data
    networks:
      - gitea

networks:
  gitea:
    driver: bridge
```

### Option 3: Kubernetes with Helm

```bash
# Add Gitea Helm repo
helm repo add gitea https://dl.gitea.io/charts/
helm repo update

# Create namespace
kubectl create namespace gitea

# Create values file
cat > gitea-values.yaml << 'EOF'
replicaCount: 1

image:
  repository: gitea/gitea
  tag: "1.21"
  pullPolicy: IfNotPresent

service:
  http:
    type: ClusterIP
    port: 3000
  ssh:
    type: LoadBalancer
    port: 22

ingress:
  enabled: true
  className: nginx
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
  hosts:
    - host: git.example.com
      paths:
        - path: /
          pathType: Prefix
  tls:
    - secretName: gitea-tls
      hosts:
        - git.example.com

persistence:
  enabled: true
  size: 50Gi
  storageClass: standard

gitea:
  admin:
    username: gitea_admin
    password: changeme
    email: admin@example.com

  config:
    server:
      ROOT_URL: https://git.example.com
      SSH_DOMAIN: git.example.com

    database:
      DB_TYPE: postgres

    security:
      INSTALL_LOCK: true
      SECRET_KEY: ""  # Auto-generated if empty

    oauth2:
      ENABLE: true

    actions:
      ENABLED: true
      DEFAULT_ACTIONS_URL: https://github.com

postgresql:
  enabled: true
  auth:
    username: gitea
    password: gitea
    database: gitea
  primary:
    persistence:
      size: 10Gi

redis:
  enabled: true
  architecture: standalone
EOF

# Install
helm install gitea gitea/gitea -n gitea -f gitea-values.yaml
```

---

## Configuration Deep Dive

### Essential app.ini Settings

```ini
; /etc/gitea/app.ini
APP_NAME = My Company Git
RUN_MODE = prod

[server]
DOMAIN           = git.example.com
ROOT_URL         = https://git.example.com/
HTTP_PORT        = 3000
SSH_DOMAIN       = git.example.com
SSH_PORT         = 22
START_SSH_SERVER = true
OFFLINE_MODE     = false  ; Set true for air-gapped

[database]
DB_TYPE  = postgres
HOST     = localhost:5432
NAME     = gitea
USER     = gitea
PASSWD   = `your-secure-password`
SSL_MODE = require

[security]
SECRET_KEY          = your-secret-key
INTERNAL_TOKEN      = your-internal-token
INSTALL_LOCK        = true
MIN_PASSWORD_LENGTH = 12

[service]
DISABLE_REGISTRATION       = false
REQUIRE_SIGNIN_VIEW        = false
ENABLE_CAPTCHA             = true
DEFAULT_KEEP_EMAIL_PRIVATE = true
NO_REPLY_ADDRESS           = noreply.git.example.com

[mailer]
ENABLED   = true
SMTP_ADDR = smtp.example.com
SMTP_PORT = 587
FROM      = gitea@example.com
USER      = gitea@example.com
PASSWD    = smtp-password

[session]
PROVIDER = redis
PROVIDER_CONFIG = network=tcp,addr=localhost:6379,db=0

[cache]
ADAPTER = redis
HOST    = network=tcp,addr=localhost:6379,db=1

[queue]
TYPE = redis
CONN_STR = redis://localhost:6379/2

[log]
MODE      = console, file
LEVEL     = info
ROOT_PATH = /var/lib/gitea/log

[repository]
ROOT                    = /var/lib/gitea/git/repositories
DEFAULT_BRANCH          = main
DEFAULT_PRIVATE         = private
MAX_CREATION_LIMIT      = -1  ; Unlimited
PREFERRED_LICENSES      = MIT,Apache-2.0,GPL-3.0

[repository.upload]
ENABLED     = true
TEMP_PATH   = /var/lib/gitea/uploads
MAX_FILES   = 10
FILE_MAX_SIZE = 50  ; MB

[lfs]
STORAGE_TYPE = minio
MINIO_ENDPOINT = s3.example.com
MINIO_ACCESS_KEY_ID = access-key
MINIO_SECRET_ACCESS_KEY = secret-key
MINIO_BUCKET = gitea-lfs
MINIO_LOCATION = us-east-1
MINIO_USE_SSL = true

[actions]
ENABLED = true
DEFAULT_ACTIONS_URL = github  ; or self-hosted URL

[oauth2]
ENABLE = true
JWT_SECRET = your-jwt-secret
```

### LDAP/Active Directory Integration

```ini
; Add to app.ini or configure via UI

[authentication]
REQUIRE_EXTERNAL_REGISTRATION_CAPTCHA = false

; Via Admin UI: Site Administration → Authentication Sources → Add
; Or via API:
```

```bash
# Add LDAP authentication via CLI
gitea admin auth add-ldap \
  --name "Corporate AD" \
  --host ldap.example.com \
  --port 636 \
  --security-protocol ldaps \
  --user-search-base "ou=Users,dc=example,dc=com" \
  --user-filter "(&(objectClass=user)(sAMAccountName=%s))" \
  --admin-filter "(memberOf=CN=GitAdmins,OU=Groups,DC=example,DC=com)" \
  --email-attribute mail \
  --username-attribute sAMAccountName \
  --firstname-attribute givenName \
  --surname-attribute sn \
  --bind-dn "CN=git-bind,OU=Service Accounts,DC=example,DC=com" \
  --bind-password "bind-password"
```

### OAuth2/OIDC (Keycloak Example)

```bash
# Add Keycloak OIDC provider
gitea admin auth add-oauth \
  --name "Keycloak SSO" \
  --provider openidConnect \
  --key gitea-client-id \
  --secret gitea-client-secret \
  --auto-discover-url https://keycloak.example.com/realms/company/.well-known/openid-configuration \
  --group-claim-name groups \
  --admin-group gitea-admins
```

---

## Gitea Actions: GitHub-Compatible CI/CD

### How It Works

```
GITEA ACTIONS ARCHITECTURE
─────────────────────────────────────────────────────────────────

┌─────────────────────────────────────────────────────────────────┐
│                         GITEA SERVER                             │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  Actions Scheduler                                         │  │
│  │  - Watches for workflow triggers                          │  │
│  │  - Queues jobs for runners                                │  │
│  │  - Stores logs and artifacts                              │  │
│  └────────────────────────────┬──────────────────────────────┘  │
└───────────────────────────────┼──────────────────────────────────┘
                                │ HTTP/HTTPS
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                      ACT RUNNER (self-hosted)                    │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  Runner Process                                            │  │
│  │  - Polls Gitea for jobs                                   │  │
│  │  - Executes workflows in containers                       │  │
│  │  - Uploads logs and artifacts                             │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                  │
│  Execution Environments:                                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                      │
│  │  Docker  │  │  LXC     │  │  Host    │                      │
│  │Container │  │Container │  │(rootless)│                      │
│  └──────────┘  └──────────┘  └──────────┘                      │
└─────────────────────────────────────────────────────────────────┘

WORKFLOW SYNTAX: 99% compatible with GitHub Actions!
```

### Setting Up Actions

```bash
# 1. Enable Actions in app.ini
cat >> /etc/gitea/app.ini << 'EOF'
[actions]
ENABLED = true
DEFAULT_ACTIONS_URL = github  ; Use GitHub's actions as default

; For air-gapped: host your own action repos
; DEFAULT_ACTIONS_URL = https://git.internal.example.com
EOF

# 2. Deploy Act Runner
# Option A: Binary
wget https://dl.gitea.io/act_runner/0.2.6/act_runner-0.2.6-linux-amd64
chmod +x act_runner-0.2.6-linux-amd64
mv act_runner-0.2.6-linux-amd64 /usr/local/bin/act_runner

# Register runner (get token from Gitea UI: Settings → Actions → Runners)
act_runner register \
  --instance https://git.example.com \
  --token <registration-token> \
  --name prod-runner-01 \
  --labels ubuntu-latest:docker://ubuntu:22.04,self-hosted

# Start runner
act_runner daemon

# Option B: Docker
docker run -d \
  --name act-runner \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v ./runner-data:/data \
  -e CONFIG_FILE=/data/config.yaml \
  gitea/act_runner:latest
```

### Example Workflow (GitHub-Compatible)

```yaml
# .gitea/workflows/ci.yaml
name: CI Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Go
        uses: actions/setup-go@v5
        with:
          go-version: '1.21'

      - name: Run tests
        run: go test -v ./...

      - name: Build
        run: go build -o app ./cmd/main.go

  security-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Run Trivy
        uses: aquasecurity/trivy-action@master
        with:
          scan-type: 'fs'
          scan-ref: '.'
          severity: 'CRITICAL,HIGH'

  build-image:
    needs: [test, security-scan]
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Login to Registry
        uses: docker/login-action@v3
        with:
          registry: registry.example.com
          username: ${{ secrets.REGISTRY_USER }}
          password: ${{ secrets.REGISTRY_PASS }}

      - name: Build and Push
        uses: docker/build-push-action@v5
        with:
          context: .
          push: true
          tags: registry.example.com/myapp:${{ github.sha }}
```

### Actions Compatibility Notes

| Feature | GitHub Actions | Gitea Actions | Notes |
|---------|---------------|---------------|-------|
| Workflow syntax | ✓ | ✓ | Nearly identical |
| Actions from GitHub | ✓ | ✓ | Works by default |
| Matrix builds | ✓ | ✓ | Full support |
| Secrets | ✓ | ✓ | Repo/org/instance level |
| Artifacts | ✓ | ✓ | Upload/download |
| Caching | ✓ | Partial | Cache action works |
| OIDC tokens | ✓ | ✗ | Not yet supported |
| Reusable workflows | ✓ | ✓ | Works |
| GitHub-hosted runners | ✓ | ✗ | Self-hosted only |

---

## Migration Strategies

### From GitHub to Gitea

```bash
# Option 1: Mirror repositories (keeps sync)
# In Gitea UI: New Migration → GitHub → Enter repo URL
# Check "This repository will be a mirror"

# Option 2: One-time import
# Via UI: New Migration → GitHub
# Enter: https://github.com/owner/repo
# Authenticate with token for private repos

# Option 3: Bulk migration script
#!/bin/bash
GITHUB_ORG="my-company"
GITEA_URL="https://git.example.com"
GITEA_TOKEN="your-token"
GITEA_ORG="my-company"

# Get all repos from GitHub
repos=$(gh repo list $GITHUB_ORG --json name -q '.[].name')

for repo in $repos; do
  echo "Migrating $repo..."

  curl -X POST "$GITEA_URL/api/v1/repos/migrate" \
    -H "Authorization: token $GITEA_TOKEN" \
    -H "Content-Type: application/json" \
    -d "{
      \"clone_addr\": \"https://github.com/$GITHUB_ORG/$repo\",
      \"repo_name\": \"$repo\",
      \"repo_owner\": \"$GITEA_ORG\",
      \"mirror\": false,
      \"private\": true,
      \"wiki\": true,
      \"issues\": true,
      \"pull_requests\": true,
      \"releases\": true
    }"
done
```

### Migrating CI from GitHub Actions to Gitea Actions

```yaml
# BEFORE: .github/workflows/ci.yaml (GitHub)
name: CI
on: [push]
jobs:
  build:
    runs-on: ubuntu-latest  # GitHub-hosted
    steps:
      - uses: actions/checkout@v4
      - run: make build

# AFTER: .gitea/workflows/ci.yaml (Gitea)
name: CI
on: [push]
jobs:
  build:
    runs-on: ubuntu-latest  # Your self-hosted runner
    steps:
      - uses: actions/checkout@v4  # Same!
      - run: make build

# Key changes:
# 1. Move file from .github/ to .gitea/
# 2. Ensure runner labels match
# 3. Update any GitHub-specific actions
# 4. Most workflows work unchanged!
```

---

## War Story: The Air-Gapped Factory Floor

*How a $340 million semiconductor expansion almost failed over a Git server*

### The Situation

**Company**: A tier-2 semiconductor manufacturer in Arizona
**Date**: Q3 2023
**Stakes**: $340 million production line expansion

The fab's automation team maintained 2,400 equipment scripts controlling everything from wafer handling to chemical vapor deposition. For years, these scripts lived in shared network folders with names like `etch_recipe_FINAL_v3_REALLY_FINAL.sh`. No version control. No audit trail. No rollback capability.

Then came the audit.

The FDA (semiconductor fabs fall under pharmaceutical-grade regulations) demanded complete traceability for every script modification. Who changed what, when, and why? The answer was "we don't know"—and that answer was about to cost them their expansion approval.

**Requirements for the fix**:
- Completely air-gapped (ITAR compliance—no internet, ever)
- Run on existing Raspberry Pi 4 infrastructure (4GB RAM each)
- Sync between clean rooms that can't be physically connected
- Support 50 engineers across 3 shifts
- Zero recurring licensing costs (capex budget was exhausted)
- Deployed in 6 weeks before the re-audit

### Why Not GitLab?

The IT team's first call was to GitLab sales. The quote came back: $127,000 annually for a self-managed license, plus $45,000 in professional services for the air-gapped deployment.

"We tried GitLab Omnibus on a test VM anyway. It wanted 8GB RAM minimum just to start. Our entire edge compute budget was 16GB across 4 Pis. GitLab was dead before we started."

GitHub Enterprise Server? $21 per user per month, minimum 500 users. That's $126,000/year for a Git server to store shell scripts.

### The Solution

```
FACTORY FLOOR GIT ARCHITECTURE
─────────────────────────────────────────────────────────────────

┌─────────────────────────────────────────────────────────────────┐
│                        CLEAN ROOM A                              │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  Raspberry Pi 4 (4GB)                                      │  │
│  │  ┌─────────────────────────────────────────────────────┐  │  │
│  │  │  Gitea (100MB RAM)                                   │  │  │
│  │  │  SQLite database (local)                             │  │  │
│  │  │  Local Git storage                                   │  │  │
│  │  └─────────────────────────────────────────────────────┘  │  │
│  └───────────────────────────────────────────────────────────┘  │
│                              │                                   │
│                    USB drive sync                                │
│                     (sneakernet)                                 │
│                              │                                   │
└──────────────────────────────┼───────────────────────────────────┘
                               │
┌──────────────────────────────┼───────────────────────────────────┐
│                        CLEAN ROOM B                              │
│                              │                                   │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  Raspberry Pi 4 (4GB)                                      │  │
│  │  ┌─────────────────────────────────────────────────────┐  │  │
│  │  │  Gitea (100MB RAM)                                   │  │  │
│  │  │  Mirror sync from USB                                │  │  │
│  │  └─────────────────────────────────────────────────────┘  │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘

Sync Process:
1. Engineer commits to Room A Gitea
2. Nightly: USB drive syncs Git bundles
3. Room B imports bundles via automation
4. Bidirectional sync handles conflicts with branch prefixes
```

### Implementation

```bash
# Gitea on Raspberry Pi - minimal config
cat > /etc/gitea/app.ini << 'EOF'
APP_NAME = FabGit
RUN_MODE = prod

[server]
DOMAIN       = gitea.local
ROOT_URL     = http://gitea.local:3000/
HTTP_PORT    = 3000
OFFLINE_MODE = true  # Critical for air-gapped

[database]
DB_TYPE = sqlite3
PATH    = /var/lib/gitea/data/gitea.db

[repository]
ROOT = /var/lib/gitea/git/repositories

[security]
INSTALL_LOCK = true

[service]
DISABLE_REGISTRATION = true
REQUIRE_SIGNIN_VIEW  = true

[log]
LEVEL = warn  # Reduce disk writes
EOF

# USB sync script (runs on each Gitea)
#!/bin/bash
# /opt/sync/export-bundles.sh

EXPORT_DIR="/mnt/usb/git-sync"
mkdir -p "$EXPORT_DIR"

for repo in /var/lib/gitea/git/repositories/*/*.git; do
  repo_name=$(basename "$repo" .git)
  cd "$repo"
  git bundle create "$EXPORT_DIR/${repo_name}.bundle" --all
done

# Checksum for integrity
cd "$EXPORT_DIR"
sha256sum *.bundle > checksums.sha256
```

### Results

**Timeline**:
- Week 1: Gitea deployed on 4 Raspberry Pis
- Week 2: LDAP integration, USB sync automation
- Week 3-4: Migration of 2,400 scripts with commit history reconstruction
- Week 5: Training across all three shifts
- Week 6: Re-audit passed with flying colors

**Financial Impact**:

| Metric | Before (No VCS) | After (Gitea) | Savings |
|--------|-----------------|---------------|---------|
| Script rollback time | 2-4 hours | 30 seconds | $45K/year in downtime |
| Cross-shift handoff issues | 5/week | 0 | $78K/year in rework |
| Audit compliance | **Failed** | **Passed** | $340M expansion saved |
| Annual licensing cost | N/A | $0 | $127K vs GitLab quote |
| Hardware cost | N/A | $0 (existing Pis) | $0 additional |
| Memory used | N/A | 98MB average | - |

**Total first-year value**: The $340 million expansion proceeded on schedule. The alternatives—either paying for enterprise Git licensing or failing the re-audit—would have delayed production by 6+ months.

### Lessons Learned

1. **SQLite is fine for small teams** - 50 users, no performance issues, zero maintenance
2. **Offline mode is essential** - Setting `OFFLINE_MODE = true` prevents all external calls, critical for air-gapped compliance
3. **Git bundles solve sync** - Native Git feature that works everywhere, no special tooling needed
4. **Raspberry Pi handles it** - CPU barely touched 10%, RAM comfortable at 98MB
5. **The audit trail saved them** - Every commit signed, every change traceable, every rollback documented

---

## Gitea vs GitHub vs GitLab Comparison

```
FEATURE COMPARISON
─────────────────────────────────────────────────────────────────

                        Gitea      GitHub.com   GitLab CE
─────────────────────────────────────────────────────────────────
Self-hosted             ✓          Enterprise   ✓
Min RAM                 100MB      N/A          4GB
Single binary           ✓          ✗            ✗
Free (all features)     ✓          Limited      Tiered
LDAP/SAML               ✓          Enterprise   ✓
CI/CD built-in          ✓ (Actions) ✓ (Actions) ✓ (CI/CD)
Container registry      ✓          ✓            ✓
Code review             ✓          ✓            ✓
Issue tracking          ✓          ✓            ✓
Project boards          ✓          ✓            ✓
Wiki                    ✓          ✓            ✓
Dependency scanning     ✗          ✓ (GHAS)     ✓ (Ultimate)
Code search             Basic      Advanced     Advanced

BEST FOR:
─────────────────────────────────────────────────────────────────
Gitea:
  • Resource-constrained environments
  • Air-gapped deployments
  • Simple self-hosting needs
  • GitHub Actions compatibility without GitHub

GitHub:
  • Open source projects
  • Integration ecosystem
  • AI features (Copilot)
  • Enterprise with compliance needs

GitLab:
  • Full DevOps platform in one tool
  • Complex CI/CD pipelines
  • Security scanning built-in
  • Regulatory compliance
```

---

## Common Mistakes

| Mistake | Why It's Bad | Better Approach |
|---------|--------------|-----------------|
| SQLite in production with 500+ users | Performance degrades, locking issues | Use PostgreSQL from the start |
| Not setting `INSTALL_LOCK = true` | Anyone can re-run setup | Lock immediately after install |
| Storing secrets in app.ini | Plain text in config file | Use environment variables or secrets manager |
| Skipping backups | Gitea stores more than Git repos | Backup database + repos + LFS |
| Running as root | Security risk | Use dedicated gitea user |
| Exposing to internet without TLS | Credentials sent in plain text | Always use HTTPS, even internal |
| Ignoring `OFFLINE_MODE` for air-gapped | Gitea tries to reach external services | Set `OFFLINE_MODE = true` |
| Not setting up Actions runners | Users expect CI/CD to work | Deploy runners before announcing |

---

## Hands-On Exercise

### Task: Deploy Gitea with CI/CD

**Objective**: Deploy Gitea, configure authentication, set up Actions, and run a pipeline.

**Success Criteria**:
1. Gitea running and accessible
2. LDAP or OAuth authentication working
3. Actions runner registered
4. Sample workflow executes successfully
5. Container image pushed to registry

### Steps

```bash
# 1. Create deployment directory
mkdir -p ~/gitea-lab && cd ~/gitea-lab

# 2. Deploy with Docker Compose
cat > docker-compose.yaml << 'EOF'
version: '3'

services:
  gitea:
    image: gitea/gitea:1.21
    container_name: gitea
    environment:
      - USER_UID=1000
      - USER_GID=1000
      - GITEA__database__DB_TYPE=sqlite3
      - GITEA__server__ROOT_URL=http://localhost:3000
      - GITEA__actions__ENABLED=true
    volumes:
      - ./gitea-data:/data
    ports:
      - "3000:3000"
      - "2222:22"

  runner:
    image: gitea/act_runner:latest
    container_name: gitea-runner
    depends_on:
      - gitea
    environment:
      - GITEA_INSTANCE_URL=http://gitea:3000
      - GITEA_RUNNER_REGISTRATION_TOKEN=  # Get from UI
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
      - ./runner-data:/data
EOF

docker compose up -d gitea

# 3. Complete initial setup at http://localhost:3000
# - Create admin account
# - Note: Keep defaults for this exercise

# 4. Enable Actions and get runner token
# Go to: Site Administration → Actions → Runners → Create new Runner
# Copy the registration token

# 5. Update docker-compose.yaml with token and start runner
# Edit GITEA_RUNNER_REGISTRATION_TOKEN=<your-token>
docker compose up -d runner

# 6. Create a test repository
# In UI: + → New Repository → "test-ci"

# 7. Add workflow file
git clone http://localhost:3000/your-user/test-ci.git
cd test-ci

mkdir -p .gitea/workflows
cat > .gitea/workflows/ci.yaml << 'EOF'
name: Test Pipeline

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Show environment
        run: |
          echo "Hello from Gitea Actions!"
          echo "Repository: ${{ github.repository }}"
          echo "Commit: ${{ github.sha }}"
          uname -a

      - name: Create artifact
        run: echo "Build output" > artifact.txt

      - name: Upload artifact
        uses: actions/upload-artifact@v3
        with:
          name: build-output
          path: artifact.txt
EOF

git add .
git commit -m "Add CI workflow"
git push

# 8. Watch the pipeline run
# Go to: Repository → Actions → Watch the workflow execute
```

### Verification

```bash
# Check Gitea is running
curl -s http://localhost:3000/api/v1/version | jq

# Check runner is registered
# In UI: Site Administration → Actions → Runners
# Should show your runner as "Idle" or "Active"

# Verify workflow executed
# In UI: Repository → Actions → Should show successful run
```

---

## Quiz

### Question 1
What is the minimum RAM required to run Gitea?

<details>
<summary>Show Answer</summary>

**~100MB**

Gitea is written in Go and compiles to a single binary that's extremely resource-efficient. Compare this to GitLab's 4GB minimum requirement.
</details>

### Question 2
What is the relationship between Gitea and Forgejo?

<details>
<summary>Show Answer</summary>

**Forgejo is a community fork of Gitea**

In 2022, when Gitea Ltd was formed as a for-profit company, some community members forked Gitea to create Forgejo under non-profit governance (Codeberg e.V.). They share ~95% of the same codebase but have different organizational structures and philosophies.
</details>

### Question 3
How do Gitea Actions compare to GitHub Actions?

<details>
<summary>Show Answer</summary>

**Nearly 100% syntax compatible**

Gitea Actions uses the same workflow syntax as GitHub Actions. Most workflows can be copied from `.github/workflows/` to `.gitea/workflows/` with minimal changes. The main differences are:
- Self-hosted runners only (no GitHub-hosted)
- Some advanced features like OIDC tokens not yet supported
- Actions from GitHub.com work by default
</details>

### Question 4
What database options does Gitea support?

<details>
<summary>Show Answer</summary>

**SQLite, PostgreSQL, MySQL, MSSQL**

- SQLite: Good for small teams (<100 users), zero setup
- PostgreSQL: Recommended for production
- MySQL/MariaDB: Widely used, fully supported
- MSSQL: For Microsoft shops
</details>

### Question 5
What is `OFFLINE_MODE` in Gitea configuration?

<details>
<summary>Show Answer</summary>

**Disables all external network calls**

When `OFFLINE_MODE = true`, Gitea won't try to:
- Fetch Gravatar avatars
- Load external fonts
- Check for updates
- Fetch action definitions from GitHub

Essential for air-gapped deployments.
</details>

### Question 6
How do you migrate repositories from GitHub to Gitea?

<details>
<summary>Show Answer</summary>

**Via UI migration, API, or mirror sync**

Options:
1. **UI**: New Migration → GitHub → Enter URL
2. **API**: POST to `/api/v1/repos/migrate`
3. **Mirror**: Creates ongoing sync with source
4. **Manual**: Clone from GitHub, push to Gitea

Migrations include issues, PRs, releases, and wiki.
</details>

### Question 7
What runner does Gitea Actions use?

<details>
<summary>Show Answer</summary>

**act_runner**

Gitea's official Actions runner, based on the `act` project. It:
- Executes workflows in Docker containers
- Uses same syntax as GitHub Actions
- Supports labels for runner selection
- Can run on any platform (Linux, macOS, Windows)
</details>

### Question 8
When would you choose Gitea over GitLab?

<details>
<summary>Show Answer</summary>

**Resource constraints, simplicity, or air-gapped environments**

Choose Gitea when:
- Limited RAM/CPU (edge, IoT, small VMs)
- Simple Git hosting without full DevOps platform
- Air-gapped networks needing offline mode
- GitHub Actions compatibility is desired
- Zero licensing cost is required

Choose GitLab when:
- Full DevOps platform in one tool
- Built-in security scanning
- Complex CI/CD requirements
- Enterprise support needed
</details>

---

## Key Takeaways

1. **Gitea = GitHub features, minimal resources** - A full-featured Git server in 100MB RAM
2. **Single binary simplicity** - No complex dependencies, easy deployment
3. **Forgejo is the community fork** - Same features, different governance
4. **Actions are GitHub-compatible** - Move workflows with minimal changes
5. **SQLite works for small teams** - PostgreSQL for anything larger
6. **OFFLINE_MODE for air-gapped** - Critical setting often missed
7. **Migration is straightforward** - Import issues, PRs, wikis, releases
8. **Self-hosted runners only** - Plan your runner infrastructure
9. **Perfect for edge computing** - Runs on Raspberry Pi
10. **Cost: $0** - All features free, forever

---

## Next Steps

- **Next Module**: [Module 11.3: GitHub Advanced](../module-11.3-github-advanced/) - GHAS, Copilot, and enterprise features
- **Related**: [Module 12.1: SonarQube](../../security-quality/code-quality/module-12.1-sonarqube/) - Integrate code quality scanning
- **Related**: [Module 2.1: ArgoCD](../gitops-deployments/module-2.1-argocd/) - GitOps with Gitea

---

## Further Reading

- [Gitea Documentation](https://docs.gitea.io/)
- [Forgejo Documentation](https://forgejo.org/docs/)
- [Gitea Actions Documentation](https://docs.gitea.io/en-us/actions/)
- [act_runner Documentation](https://gitea.com/gitea/act_runner)
- [Gitea vs GitLab comparison](https://docs.gitea.io/en-us/comparison/)

---

*"Sometimes the best tool is the simplest one that solves your problem. Gitea proves that a Git server doesn't need 4GB of RAM to be useful."*
