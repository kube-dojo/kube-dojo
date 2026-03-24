# Module 11.1: GitLab - The Complete DevOps Platform

## Complexity: [COMPLEX]
## Time to Complete: 50-60 minutes

---

## Prerequisites

Before starting this module, you should have completed:
- [DevSecOps Discipline](../../disciplines/devsecops/README.md) - CI/CD and security concepts
- [GitOps Discipline](../../disciplines/gitops/README.md) - Git-centric workflows
- Basic Docker/Kubernetes experience
- Git fundamentals (branches, merges, remotes)

---

## Why This Module Matters

**When GitHub Isn't Enough**

Picture this: Your company runs 200 microservices. Each has its own GitHub repo, Actions workflow, and external security scanner. Your Jenkins server runs CI. Your container images live in ECR. Your security team uses Snyk. Your deploy uses ArgoCD watching a separate config repo. Every tool has its own UI, its own permissions model, its own audit trail.

One day, an auditor asks: "Show me the complete path from code change to production for your payment service, including all security checks and approvals."

You spend three days stitching together screenshots from seven different tools.

GitLab exists because fragmented toolchains create operational overhead. It's not just a Git host—it's an integrated platform where source code, CI/CD, container registry, security scanning, and deployment all live together. When everything's in one place, that audit question becomes a single link.

Is GitLab right for everyone? No. It's heavyweight, opinionated, and complex. But if you're tired of managing the integration layer between a dozen tools, GitLab offers a genuinely different approach.

---

## GitLab Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    GITLAB PLATFORM ARCHITECTURE                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                     GitLab Rails App                       │  │
│  │  ┌─────────┬─────────┬─────────┬─────────┬─────────────┐  │  │
│  │  │  Git    │ Issues  │  Merge  │  CI/CD  │   Wiki      │  │  │
│  │  │  Repos  │ Boards  │Requests │ Pipelines│ Pages      │  │  │
│  │  └─────────┴─────────┴─────────┴─────────┴─────────────┘  │  │
│  │                          │                                 │  │
│  │                          ▼                                 │  │
│  │  ┌─────────────────────────────────────────────────────┐  │  │
│  │  │              Sidekiq (Background Jobs)               │  │  │
│  │  │   CI jobs • Webhooks • Email • Imports • Analytics  │  │  │
│  │  └─────────────────────────────────────────────────────┘  │  │
│  └────────────────────────────┬──────────────────────────────┘  │
│                               │                                  │
│  ┌────────────────────────────┼──────────────────────────────┐  │
│  │                            │                               │  │
│  │  ┌──────────┐    ┌────────┴────────┐    ┌──────────────┐ │  │
│  │  │PostgreSQL│    │     Redis       │    │ Gitaly       │ │  │
│  │  │(metadata)│    │ (cache, queue)  │    │(Git storage) │ │  │
│  │  └──────────┘    └─────────────────┘    └──────────────┘ │  │
│  │                                                           │  │
│  │  ┌──────────┐    ┌─────────────────┐    ┌──────────────┐ │  │
│  │  │Container │    │  Object Storage │    │  Runner      │ │  │
│  │  │ Registry │    │   (artifacts)   │    │  (CI exec)   │ │  │
│  │  └──────────┘    └─────────────────┘    └──────────────┘ │  │
│  │                                                           │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Component Deep Dive

| Component | Purpose | Scaling Notes |
|-----------|---------|---------------|
| **Rails App** | Main application, web UI, API | Horizontal scaling behind load balancer |
| **Sidekiq** | Background job processing | Multiple workers, separate queues |
| **PostgreSQL** | Metadata, users, issues, MRs | Primary-replica with Patroni |
| **Redis** | Caching, job queues, sessions | Sentinel for HA |
| **Gitaly** | Git repository storage | Praefect for distributed Git |
| **Registry** | Container image storage | S3-compatible backend |
| **Object Storage** | Artifacts, uploads, LFS | MinIO or cloud (S3/GCS) |
| **Runners** | CI/CD job execution | Auto-scaling on Kubernetes |

---

## GitLab CI/CD: Beyond Basics

### Pipeline Architecture

```yaml
# .gitlab-ci.yml - Production-grade pipeline
stages:
  - validate
  - build
  - test
  - security
  - deploy

variables:
  DOCKER_TLS_CERTDIR: "/certs"
  # Cache configuration
  PIP_CACHE_DIR: "$CI_PROJECT_DIR/.cache/pip"

# Default settings for all jobs
default:
  image: python:3.11-slim
  retry:
    max: 2
    when:
      - runner_system_failure
      - stuck_or_timeout_failure
  interruptible: true  # Cancel on new commits

# Reusable job templates
.docker_build:
  image: docker:24.0
  services:
    - docker:24.0-dind
  before_script:
    - docker login -u $CI_REGISTRY_USER -p $CI_REGISTRY_PASSWORD $CI_REGISTRY

# ─────────────────────────────────────────────────────────────
# VALIDATE STAGE
# ─────────────────────────────────────────────────────────────
lint:
  stage: validate
  script:
    - pip install ruff
    - ruff check .
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH

yaml-lint:
  stage: validate
  image: cytopia/yamllint
  script:
    - yamllint -c .yamllint.yml .
  allow_failure: true

# ─────────────────────────────────────────────────────────────
# BUILD STAGE
# ─────────────────────────────────────────────────────────────
build-image:
  extends: .docker_build
  stage: build
  script:
    - docker build
        --cache-from $CI_REGISTRY_IMAGE:latest
        --tag $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA
        --tag $CI_REGISTRY_IMAGE:latest
        --build-arg BUILDKIT_INLINE_CACHE=1
        .
    - docker push $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA
    - docker push $CI_REGISTRY_IMAGE:latest
  rules:
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
      variables:
        # Don't push :latest on MRs
        PUSH_LATEST: "false"

# ─────────────────────────────────────────────────────────────
# TEST STAGE
# ─────────────────────────────────────────────────────────────
unit-tests:
  stage: test
  script:
    - pip install -r requirements.txt
    - pytest tests/unit --cov=src --cov-report=xml
  coverage: '/TOTAL.*\s+(\d+%)/'
  artifacts:
    reports:
      coverage_report:
        coverage_format: cobertura
        path: coverage.xml
      junit: junit.xml

integration-tests:
  stage: test
  services:
    - postgres:15
    - redis:7
  variables:
    POSTGRES_DB: test
    POSTGRES_USER: test
    POSTGRES_PASSWORD: test
    DATABASE_URL: "postgresql://test:test@postgres:5432/test"
    REDIS_URL: "redis://redis:6379"
  script:
    - pip install -r requirements.txt
    - pytest tests/integration
  rules:
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"

# ─────────────────────────────────────────────────────────────
# SECURITY STAGE
# ─────────────────────────────────────────────────────────────
include:
  - template: Security/SAST.gitlab-ci.yml
  - template: Security/Dependency-Scanning.gitlab-ci.yml
  - template: Security/Secret-Detection.gitlab-ci.yml
  - template: Security/Container-Scanning.gitlab-ci.yml

# Override container scanning to use our image
container_scanning:
  variables:
    CS_IMAGE: $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA

# Custom security gate
security-gate:
  stage: security
  image: alpine
  needs:
    - sast
    - dependency_scanning
    - secret_detection
    - container_scanning
  script:
    - |
      echo "Checking security scan results..."
      # Fail if critical vulnerabilities found
      if [ -f gl-sast-report.json ]; then
        CRITICAL=$(cat gl-sast-report.json | jq '[.vulnerabilities[] | select(.severity=="Critical")] | length')
        if [ "$CRITICAL" -gt 0 ]; then
          echo "Found $CRITICAL critical vulnerabilities!"
          exit 1
        fi
      fi
  allow_failure: false

# ─────────────────────────────────────────────────────────────
# DEPLOY STAGE
# ─────────────────────────────────────────────────────────────
deploy-staging:
  stage: deploy
  image: bitnami/kubectl:latest
  environment:
    name: staging
    url: https://staging.example.com
  script:
    - kubectl set image deployment/app app=$CI_REGISTRY_IMAGE:$CI_COMMIT_SHA
  rules:
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH

deploy-production:
  stage: deploy
  image: bitnami/kubectl:latest
  environment:
    name: production
    url: https://app.example.com
  script:
    - kubectl set image deployment/app app=$CI_REGISTRY_IMAGE:$CI_COMMIT_SHA
  rules:
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH
      when: manual  # Require manual approval
  needs:
    - deploy-staging
    - security-gate
```

### Advanced Pipeline Features

#### Parent-Child Pipelines

```yaml
# .gitlab-ci.yml - Parent pipeline
stages:
  - triggers

trigger-services:
  stage: triggers
  trigger:
    include:
      - local: services/api/.gitlab-ci.yml
      - local: services/web/.gitlab-ci.yml
      - local: services/worker/.gitlab-ci.yml
    strategy: depend  # Wait for child pipelines
  rules:
    - changes:
        - services/**/*
```

```yaml
# services/api/.gitlab-ci.yml - Child pipeline
stages:
  - build
  - test
  - deploy

build-api:
  stage: build
  script:
    - docker build -t api services/api
  rules:
    - changes:
        - services/api/**/*
```

#### Dynamic Pipelines

```yaml
# Generate pipeline configuration dynamically
generate-pipeline:
  stage: .pre
  image: python:3.11
  script:
    - python scripts/generate_pipeline.py > generated-pipeline.yml
  artifacts:
    paths:
      - generated-pipeline.yml

run-generated:
  stage: build
  trigger:
    include:
      - artifact: generated-pipeline.yml
        job: generate-pipeline
    strategy: depend
```

#### Matrix Builds

```yaml
test:
  stage: test
  parallel:
    matrix:
      - PYTHON_VERSION: ["3.9", "3.10", "3.11"]
        DATABASE: ["postgres", "mysql"]
  image: python:${PYTHON_VERSION}
  services:
    - name: ${DATABASE}:latest
      alias: database
  script:
    - pytest tests/
```

---

## GitLab Container Registry

### Built-in Registry Usage

```bash
# Login to GitLab registry
docker login registry.gitlab.com -u $GITLAB_USER -p $GITLAB_TOKEN

# Tag and push
docker build -t registry.gitlab.com/mygroup/myproject:v1.0.0 .
docker push registry.gitlab.com/mygroup/myproject:v1.0.0

# In CI/CD, credentials are automatic:
# $CI_REGISTRY, $CI_REGISTRY_USER, $CI_REGISTRY_PASSWORD
```

### Cleanup Policies

```yaml
# Via API or Settings → Packages & Registries → Container Registry
# Cleanup policy example:
{
  "name_regex_delete": ".*",
  "name_regex_keep": "main|release-.*",
  "keep_n": 10,
  "older_than": "30d",
  "enabled": true
}
```

### Multi-Architecture Builds

```yaml
build-multiarch:
  stage: build
  image: docker:24.0
  services:
    - docker:24.0-dind
  before_script:
    - docker login -u $CI_REGISTRY_USER -p $CI_REGISTRY_PASSWORD $CI_REGISTRY
    - docker run --privileged --rm tonistiigi/binfmt --install all
    - docker buildx create --use
  script:
    - docker buildx build
        --platform linux/amd64,linux/arm64
        --tag $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA
        --push
        .
```

---

## GitLab Security Scanning

### Security Scanning Matrix

```
┌─────────────────────────────────────────────────────────────────┐
│                 GITLAB SECURITY SCANNING                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  STATIC ANALYSIS (Before Runtime)                               │
│  ┌────────────────────────────────────────────────────────────┐│
│  │                                                            ││
│  │  SAST              │ Dependency      │ Secret Detection   ││
│  │  ───────────────   │ Scanning        │ ─────────────────  ││
│  │  Source code       │ ──────────────  │ API keys, tokens   ││
│  │  vulnerabilities   │ CVEs in deps    │ passwords in code  ││
│  │  (SQL injection,   │ (npm, pip,      │ (prevents commits) ││
│  │  XSS, etc.)        │ maven, etc.)    │                    ││
│  │                    │                 │                    ││
│  └────────────────────────────────────────────────────────────┘│
│                                                                  │
│  CONTAINER & INFRASTRUCTURE                                     │
│  ┌────────────────────────────────────────────────────────────┐│
│  │                                                            ││
│  │  Container         │ IaC Scanning    │ License Scanning   ││
│  │  Scanning          │ ──────────────  │ ────────────────   ││
│  │  ──────────────    │ Terraform,      │ Compliance with    ││
│  │  CVEs in images    │ CloudFormation  │ license policies   ││
│  │  (Trivy-based)     │ misconfigs      │ (GPL, MIT, etc.)   ││
│  │                    │                 │                    ││
│  └────────────────────────────────────────────────────────────┘│
│                                                                  │
│  DYNAMIC ANALYSIS (Runtime)                                     │
│  ┌────────────────────────────────────────────────────────────┐│
│  │                                                            ││
│  │  DAST              │ API Fuzzing     │ Coverage Fuzzing   ││
│  │  ───────────────   │ ──────────────  │ ────────────────   ││
│  │  Tests running     │ Malformed API   │ Random input to    ││
│  │  application       │ requests        │ discover crashes   ││
│  │  (OWASP ZAP)       │                 │                    ││
│  │                    │                 │                    ││
│  └────────────────────────────────────────────────────────────┘│
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Enabling All Scanners

```yaml
# .gitlab-ci.yml
include:
  # Static Analysis
  - template: Security/SAST.gitlab-ci.yml
  - template: Security/Dependency-Scanning.gitlab-ci.yml
  - template: Security/Secret-Detection.gitlab-ci.yml
  - template: Security/License-Scanning.gitlab-ci.yml

  # Container & IaC
  - template: Security/Container-Scanning.gitlab-ci.yml
  - template: Jobs/SAST-IaC.gitlab-ci.yml

  # Dynamic Analysis (requires running app)
  - template: Security/DAST.gitlab-ci.yml
  - template: Security/API-Fuzzing.gitlab-ci.yml

# DAST requires a running environment
dast:
  variables:
    DAST_WEBSITE: https://staging.example.com
  rules:
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH
```

### Security Dashboard

```
VULNERABILITY MANAGEMENT WORKFLOW
─────────────────────────────────────────────────────────────────

Pipeline runs → Scanners execute → Findings uploaded
                                          │
                                          ▼
                         ┌────────────────────────────────────┐
                         │       Security Dashboard          │
                         │  ┌────────────────────────────┐  │
                         │  │ Critical: 2  High: 15      │  │
                         │  │ Medium: 47   Low: 123      │  │
                         │  │                            │  │
                         │  │ [Dismiss] [Create Issue]   │  │
                         │  └────────────────────────────┘  │
                         └───────────────┬────────────────────┘
                                         │
              ┌──────────────────────────┼──────────────────────────┐
              │                          │                          │
              ▼                          ▼                          ▼
      ┌─────────────┐           ┌─────────────────┐         ┌─────────────┐
      │ Dismiss     │           │ Create Issue    │         │ MR Approval │
      │ (false pos) │           │ (track fix)     │         │ Blocked     │
      └─────────────┘           └─────────────────┘         └─────────────┘
```

---

## Deploying GitLab on Kubernetes

### Helm Chart Installation

```bash
# Add GitLab Helm repository
helm repo add gitlab https://charts.gitlab.io/
helm repo update

# Create values file
cat > gitlab-values.yaml << 'EOF'
global:
  hosts:
    domain: example.com
    gitlab:
      name: gitlab.example.com
    registry:
      name: registry.example.com

  ingress:
    class: nginx
    configureCertmanager: true

  # External PostgreSQL (recommended for production)
  psql:
    host: postgres.example.com
    port: 5432
    database: gitlabhq_production
    username: gitlab
    password:
      secret: gitlab-postgres-secret
      key: password

  # External Redis (recommended for production)
  redis:
    host: redis.example.com
    password:
      secret: gitlab-redis-secret
      key: password

  # Object storage for artifacts, uploads, etc.
  minio:
    enabled: false
  appConfig:
    object_store:
      enabled: true
      connection:
        secret: gitlab-object-storage
        key: connection
    artifacts:
      bucket: gitlab-artifacts
    uploads:
      bucket: gitlab-uploads
    packages:
      bucket: gitlab-packages
    lfs:
      bucket: gitlab-lfs

# GitLab Rails application
gitlab:
  webservice:
    replicas: 2
    resources:
      requests:
        memory: 2.5Gi
        cpu: 1
      limits:
        memory: 4Gi
        cpu: 2

  sidekiq:
    replicas: 2
    resources:
      requests:
        memory: 2Gi
        cpu: 500m

  gitaly:
    persistence:
      size: 100Gi
      storageClass: fast-ssd

# GitLab Runner
gitlab-runner:
  install: true
  runners:
    config: |
      [[runners]]
        [runners.kubernetes]
          namespace = "gitlab"
          image = "ubuntu:22.04"
          privileged = true
          [[runners.kubernetes.volumes.empty_dir]]
            name = "docker-certs"
            mount_path = "/certs/client"
            medium = "Memory"

# Container Registry
registry:
  enabled: true
  storage:
    secret: gitlab-registry-storage
    key: config

# Disable built-in dependencies for production
postgresql:
  install: false
redis:
  install: false
minio:
  install: false

# Prometheus monitoring
prometheus:
  install: false  # Use existing Prometheus
EOF

# Install GitLab
helm upgrade --install gitlab gitlab/gitlab \
  --namespace gitlab \
  --create-namespace \
  --values gitlab-values.yaml \
  --timeout 600s
```

### Production Considerations

```yaml
# High Availability Configuration
global:
  # Multiple Gitaly nodes with Praefect
  praefect:
    enabled: true
    replicas: 3
    virtualStorages:
      - name: default
        gitalyReplicas: 3
        maxUnavailable: 1

# Pod Disruption Budgets
gitlab:
  webservice:
    podDisruptionBudget:
      minAvailable: 1
  sidekiq:
    podDisruptionBudget:
      minAvailable: 1

# Resource quotas
gitlab:
  webservice:
    hpa:
      minReplicas: 2
      maxReplicas: 10
      targetAverageValue: 400m
```

### GitLab Runner Configuration

```yaml
# runner-values.yaml
gitlabUrl: https://gitlab.example.com
runnerRegistrationToken: "YOUR_REGISTRATION_TOKEN"

runners:
  config: |
    [[runners]]
      name = "kubernetes-runner"
      executor = "kubernetes"
      [runners.kubernetes]
        namespace = "gitlab-runners"
        image = "alpine:latest"
        privileged = false

        # Resource limits per job
        cpu_limit = "2"
        memory_limit = "4Gi"
        cpu_request = "500m"
        memory_request = "1Gi"

        # Service account for RBAC
        service_account = "gitlab-runner"

        # Cache configuration
        [[runners.kubernetes.volumes.pvc]]
          name = "cache"
          mount_path = "/cache"

        # Docker socket for DinD
        [[runners.kubernetes.volumes.host_path]]
          name = "docker-sock"
          mount_path = "/var/run/docker.sock"
          host_path = "/var/run/docker.sock"

rbac:
  create: true
  rules:
    - apiGroups: [""]
      resources: ["pods", "pods/exec", "secrets"]
      verbs: ["get", "list", "watch", "create", "delete"]

# Autoscaling runners
replicas: 2
```

---

## GitLab vs GitHub: Honest Comparison

```
FEATURE COMPARISON
─────────────────────────────────────────────────────────────────

                        GitLab               GitHub
─────────────────────────────────────────────────────────────────
PHILOSOPHY              All-in-one           Best-of-breed
                        integrated           ecosystem

CI/CD                   Built-in, powerful   Actions (flexible,
                        YAML complexity      marketplace)

Security Scanning       Built-in (SAST,      GHAS (extra cost)
                        DAST, container)     CodeQL is excellent

Self-hosted             Easy (Omnibus)       Enterprise only
                        or Kubernetes        (expensive)

Performance             Heavy (4GB+ RAM)     N/A (SaaS)
                        Complex scaling

User Experience         Dense, powerful      Clean, intuitive
                        steeper learning     faster onboarding

Package Registry        Built-in (npm,       Built-in (good)
                        Maven, etc.)

Wiki/Pages              Built-in             Built-in
                        (per-project)        (GitHub Pages)

Issue Tracking          Full-featured        Good, simpler
                        boards, epics        Projects boards

Community               Strong open-source   Massive ecosystem
                        contributor base     most OSS lives here

Enterprise Features     Premium/Ultimate     Enterprise SKU
                        tiers                GHAS separate

Pricing (100 users)     $0 (CE) to          ~$40k/year with
                        $115k (Ultimate)     Enterprise + GHAS
─────────────────────────────────────────────────────────────────

WHEN TO CHOOSE GITLAB:
• You want one platform instead of 5+ tools
• Self-hosted requirement
• Security scanning included in price is important
• Complex CI/CD with parent-child pipelines
• Air-gapped environment

WHEN TO CHOOSE GITHUB:
• Your developers already know it
• Open source community engagement
• GitHub marketplace integrations
• Copilot AI assistance
• Actions marketplace ecosystem
```

---

## War Story: The Great Migration

**Company**: E-commerce platform, 150 engineers
**Challenge**: Migrate from Jenkins + GitHub + Harbor + Snyk to GitLab

**The Situation**:

The team managed:
- 300 repos on GitHub
- Jenkins with 2000 jobs
- Harbor for container images
- Snyk for security scanning
- Separate LDAP groups per tool

Every new service required:
1. Create GitHub repo
2. Add Jenkins job
3. Configure Harbor project
4. Add to Snyk monitoring
5. Set up deployment config

Time to onboard new service: 2-3 days
Audit preparation time: 1 week per audit

**The Migration**:

```
PHASE 1: PARALLEL OPERATION (Month 1-2)
─────────────────────────────────────────────────────────────────
• Deploy GitLab on Kubernetes
• Mirror GitHub repos to GitLab (read-only)
• Pilot: Convert 5 services to GitLab CI
• Document CI/CD translation patterns

PHASE 2: GRADUAL MIGRATION (Month 3-4)
─────────────────────────────────────────────────────────────────
• Team-by-team migration
• Convert Jenkins jobs to GitLab CI
• Enable security scanning on migrated repos
• Disable Jenkins jobs as services move

PHASE 3: CUTOVER (Month 5)
─────────────────────────────────────────────────────────────────
• Stop GitHub mirroring
• Redirect GitHub URLs
• Decommission Jenkins
• Decommission Harbor
• Cancel Snyk subscription
```

**Results**:

| Metric | Before | After |
|--------|--------|-------|
| New service onboarding | 2-3 days | 15 minutes |
| Tools to maintain | 5 | 1 |
| Audit preparation | 1 week | 2 hours |
| Monthly tooling cost | $12,000 | $8,500 |
| Security scan coverage | 60% | 100% |

**Key Lessons**:

1. **Jenkins translation is hardest**: Groovy pipelines don't map cleanly to YAML
2. **Train developers early**: GitLab CI has different mental model
3. **Don't migrate everything**: Some repos were archived instead
4. **Security scanning catches things**: Found 12 critical vulns in first week

---

## Common Mistakes

| Mistake | Problem | Solution |
|---------|---------|----------|
| Under-provisioned runners | Slow CI, job queues | Autoscaling runners on Kubernetes |
| No artifact cleanup | Storage costs explode | Pipeline artifact expiration policies |
| Monolithic pipelines | Slow, hard to debug | Parent-child pipelines, includes |
| Ignoring security dashboard | Vulnerabilities accumulate | Weekly triage, block MRs on critical |
| Single Gitaly node | Data loss risk, bottleneck | Praefect with 3+ Gitaly nodes |
| No backup strategy | Disaster recovery impossible | Automated backups to object storage |
| Everyone is admin | Security nightmare | Group-based RBAC, least privilege |
| No runner tagging | Jobs run on wrong runners | Tag runners by capability |

---

## Quiz

<details>
<summary>1. What is the difference between GitLab CE and EE?</summary>

**Answer**: GitLab CE (Community Edition) is open-source and free, containing core functionality. GitLab EE (Enterprise Edition) includes additional features in tiers:

- **Free**: Same as CE
- **Premium**: Advanced CI/CD, compliance, security (SAST), support
- **Ultimate**: Full security suite (DAST, fuzz testing), portfolio management

The same codebase runs both—EE features are license-gated.
</details>

<details>
<summary>2. Explain the purpose of Gitaly and Praefect.</summary>

**Answer**:
- **Gitaly**: Service that handles all Git operations. Instead of GitLab Rails shelling out to `git`, it talks to Gitaly via gRPC. Improves security and scalability.

- **Praefect**: Cluster manager for multiple Gitaly nodes. Provides:
  - Replication across nodes
  - Automatic failover
  - Read distribution
  - Strong consistency guarantees

For HA, deploy Praefect with 3+ Gitaly nodes.
</details>

<details>
<summary>3. How do parent-child pipelines differ from multi-project pipelines?</summary>

**Answer**:
- **Parent-child**: One repo, pipeline triggers child pipelines from same repo. Useful for monorepos—child pipelines can be generated dynamically.

- **Multi-project**: Pipeline in repo A triggers pipeline in repo B. Useful for deployment orchestration across separate repos.

```yaml
# Parent-child (same repo)
trigger:
  include: services/api/.gitlab-ci.yml

# Multi-project (different repo)
trigger:
  project: mygroup/deploy-repo
  branch: main
```
</details>

<details>
<summary>4. What security scanners are included in GitLab and when do they run?</summary>

**Answer**: GitLab includes:

| Scanner | Runs On | Detects |
|---------|---------|---------|
| SAST | Source code | Code vulnerabilities |
| Dependency Scanning | Package files | CVEs in dependencies |
| Secret Detection | All files | Leaked credentials |
| Container Scanning | Built images | Image CVEs |
| IaC Scanning | Terraform/CF | Infrastructure misconfigs |
| DAST | Running app | Runtime vulnerabilities |
| API Fuzzing | API endpoints | API security issues |
| License Scanning | Dependencies | License compliance |

All run in CI pipeline. SAST/Secrets can also run as pre-receive hooks.
</details>

<details>
<summary>5. How do you configure GitLab runners for Docker-in-Docker builds?</summary>

**Answer**: Two approaches:

**1. Privileged DinD** (simpler, less secure):
```yaml
services:
  - docker:24.0-dind
variables:
  DOCKER_TLS_CERTDIR: "/certs"
```
Runner must have `privileged: true`.

**2. Kaniko** (rootless, more secure):
```yaml
build:
  image:
    name: gcr.io/kaniko-project/executor:latest
    entrypoint: [""]
  script:
    - /kaniko/executor --context $CI_PROJECT_DIR --dockerfile Dockerfile
```
No privileged mode needed.
</details>

<details>
<summary>6. What is the purpose of GitLab's environment and review apps feature?</summary>

**Answer**: Environments track deployments:

```yaml
deploy:
  environment:
    name: review/$CI_COMMIT_REF_SLUG
    url: https://$CI_COMMIT_REF_SLUG.example.com
    on_stop: stop_review
    auto_stop_in: 1 week
```

Benefits:
- Track which commit is deployed where
- Auto-generated environment URLs
- Review apps: per-MR preview environments
- Auto-cleanup stale environments
- Deployment history and rollback
</details>

<details>
<summary>7. How does GitLab's merge request approval workflow function?</summary>

**Answer**: MR approvals can require:

1. **Approval rules**: Minimum approvers, specific users/groups
2. **Code owners**: File-pattern based required approvers (CODEOWNERS file)
3. **Security approvals**: Block on critical vulnerabilities
4. **Pipeline success**: All jobs must pass

```yaml
# .gitlab/CODEOWNERS
*.tf @platform-team
/security/ @security-team
```

Settings allow:
- Prevent self-approval
- Reset approvals on push
- Require re-approval after changes
</details>

<details>
<summary>8. What are GitLab's options for disaster recovery and high availability?</summary>

**Answer**:

**High Availability**:
- Multiple Rails/Sidekiq pods
- PostgreSQL with Patroni (auto-failover)
- Redis Sentinel
- Praefect + Gitaly cluster
- Load balancer for traffic distribution

**Disaster Recovery**:
- Geo replication (EE): Full read-only secondary site
- Backup rake tasks: Full backups to object storage
- Database replication: PostgreSQL streaming replication

**RPO/RTO**:
- Geo: RPO ~minutes, RTO ~minutes (failover)
- Backups: RPO ~hours, RTO ~hours (restore)
</details>

---

## Hands-On Exercise

**Objective**: Deploy GitLab on Kubernetes and create a complete CI/CD pipeline with security scanning.

### Part 1: Deploy GitLab (Using kind for local testing)

```bash
# Create kind cluster with ingress support
cat > kind-config.yaml << 'EOF'
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
nodes:
- role: control-plane
  kubeadmConfigPatches:
  - |
    kind: InitConfiguration
    nodeRegistration:
      kubeletExtraArgs:
        node-labels: "ingress-ready=true"
  extraPortMappings:
  - containerPort: 80
    hostPort: 80
  - containerPort: 443
    hostPort: 443
EOF

kind create cluster --config kind-config.yaml --name gitlab

# Install ingress controller
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/kind/deploy.yaml

# Wait for ingress
kubectl wait --namespace ingress-nginx \
  --for=condition=ready pod \
  --selector=app.kubernetes.io/component=controller \
  --timeout=90s

# Add GitLab Helm repo
helm repo add gitlab https://charts.gitlab.io/
helm repo update

# Minimal GitLab for testing (NOT for production!)
cat > gitlab-minimal.yaml << 'EOF'
global:
  hosts:
    domain: 127.0.0.1.nip.io
    https: false
  ingress:
    configureCertmanager: false
    class: nginx
    tls:
      enabled: false

certmanager:
  install: false

gitlab-runner:
  install: false

nginx-ingress:
  enabled: false

prometheus:
  install: false

# Minimal resources for local testing
gitlab:
  webservice:
    minReplicas: 1
    maxReplicas: 1
  sidekiq:
    minReplicas: 1
    maxReplicas: 1
  gitaly:
    persistence:
      size: 5Gi
EOF

# Install (takes 5-10 minutes)
helm upgrade --install gitlab gitlab/gitlab \
  --namespace gitlab \
  --create-namespace \
  --values gitlab-minimal.yaml \
  --timeout 600s

# Get root password
kubectl get secret gitlab-gitlab-initial-root-password \
  -n gitlab \
  -o jsonpath='{.data.password}' | base64 -d && echo

# Access at: http://gitlab.127.0.0.1.nip.io
# Login: root / <password from above>
```

### Part 2: Create CI/CD Pipeline

```bash
# Create a sample project in GitLab UI, then clone it
git clone http://gitlab.127.0.0.1.nip.io/root/sample-app.git
cd sample-app

# Create application
cat > app.py << 'EOF'
from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/health')
def health():
    return jsonify({"status": "healthy"})

@app.route('/')
def hello():
    return jsonify({"message": "Hello from GitLab CI!"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
EOF

cat > requirements.txt << 'EOF'
flask==3.0.0
pytest==7.4.0
EOF

cat > Dockerfile << 'EOF'
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY app.py .
EXPOSE 5000
CMD ["python", "app.py"]
EOF

# Create tests
mkdir -p tests
cat > tests/test_app.py << 'EOF'
import pytest
from app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_health(client):
    response = client.get('/health')
    assert response.status_code == 200
    assert response.json['status'] == 'healthy'

def test_hello(client):
    response = client.get('/')
    assert response.status_code == 200
    assert 'message' in response.json
EOF

# Create GitLab CI pipeline
cat > .gitlab-ci.yml << 'EOF'
stages:
  - validate
  - build
  - test
  - security
  - deploy

variables:
  PIP_CACHE_DIR: "$CI_PROJECT_DIR/.cache/pip"

default:
  image: python:3.11-slim

cache:
  paths:
    - .cache/pip

# Lint Python code
lint:
  stage: validate
  script:
    - pip install ruff
    - ruff check .
  allow_failure: true

# Build container image
build:
  stage: build
  image: docker:24.0
  services:
    - docker:24.0-dind
  variables:
    DOCKER_TLS_CERTDIR: "/certs"
  before_script:
    - docker login -u $CI_REGISTRY_USER -p $CI_REGISTRY_PASSWORD $CI_REGISTRY
  script:
    - docker build -t $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA .
    - docker push $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA

# Run tests
test:
  stage: test
  script:
    - pip install -r requirements.txt
    - pytest tests/ -v --junitxml=junit.xml
  artifacts:
    reports:
      junit: junit.xml

# Security scanning (included templates)
include:
  - template: Security/SAST.gitlab-ci.yml
  - template: Security/Dependency-Scanning.gitlab-ci.yml
  - template: Security/Secret-Detection.gitlab-ci.yml

# Deploy to staging environment
deploy-staging:
  stage: deploy
  script:
    - echo "Deploying $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA to staging"
    # In real scenario: kubectl set image deployment/app ...
  environment:
    name: staging
    url: https://staging.example.com
  rules:
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH
EOF

# Commit and push
git add .
git commit -m "Initial application with CI/CD pipeline"
git push origin main
```

### Part 3: Verify Pipeline Execution

1. Go to GitLab UI → Your project → CI/CD → Pipelines
2. Watch pipeline execute through stages
3. Check Security tab for scan results
4. Review artifacts and test reports

### Success Criteria

- [ ] GitLab running on Kubernetes
- [ ] Project created with CI/CD pipeline
- [ ] All pipeline stages pass (lint, build, test)
- [ ] Security scans execute (SAST, dependency, secrets)
- [ ] Container image pushed to GitLab Registry
- [ ] Environment created for staging deployment

---

## Key Takeaways

1. **GitLab is a platform, not just Git hosting** — CI/CD, registry, security, all integrated
2. **Self-hosting is an option** — Unlike GitHub, you can run it on-prem or air-gapped
3. **Security scanning is built-in** — SAST, DAST, container scanning without extra tools
4. **Pipelines are powerful but complex** — Parent-child, dynamic generation, DAGs
5. **Resource requirements are significant** — Plan for 4GB+ RAM minimum, more for production
6. **Runners need careful planning** — Autoscaling, tagging, security isolation
7. **Migration from other tools is work** — Jenkins conversion especially painful
8. **Praefect enables HA Git storage** — Required for production high availability
9. **Everything is auditable** — Single platform means single audit trail
10. **Cost model differs from GitHub** — May be cheaper or more expensive depending on usage

---

## Did You Know?

> **GitLab's Origin**: GitLab was started by Dmitriy Zaporozhets in Ukraine in 2011 as an open-source GitHub alternative. The company is now one of the largest all-remote companies in the world with 2000+ employees across 65+ countries.

> **Monthly Releases**: GitLab follows a strict monthly release cadence. Version numbers are year.month (e.g., 16.5 = 2023, month 5). This predictable schedule helps enterprises plan upgrades.

> **Handbook-First**: GitLab's employee handbook is public and over 2000 pages. This "handbook-first" culture means almost everything about how the company operates is documented publicly at handbook.gitlab.com.

> **Meltano Spinoff**: GitLab spun off Meltano, an open-source DataOps platform, as a separate company. It started as an internal GitLab project for data pipeline management.

---

## Next Module

Continue to [Module 11.2: Gitea & Forgejo](module-11.2-gitea-forgejo.md) to learn about lightweight, self-hosted Git alternatives that run in a fraction of GitLab's resources.
