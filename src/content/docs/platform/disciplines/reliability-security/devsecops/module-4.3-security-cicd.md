---
title: "Module 4.3: Security in CI/CD Pipelines"
slug: platform/disciplines/reliability-security/devsecops/module-4.3-security-cicd
sidebar:
  order: 4
---
> **Discipline Module** | Complexity: `[COMPLEX]` | Time: 40-45 min

## Prerequisites

Before starting this module:
- **Required**: [Module 4.2: Shift-Left Security](../module-4.2-shift-left-security/) — Pre-commit checks
- **Required**: CI/CD experience (GitHub Actions, GitLab CI, Jenkins, etc.)
- **Recommended**: Container basics (Docker, image registries)
- **Helpful**: YAML configuration experience

---

## Why This Module Matters

Pre-commit hooks catch a lot. But developers can bypass them. And some checks are too slow for pre-commit.

**CI/CD is your guaranteed checkpoint.**

Every commit, every PR, every merge goes through CI. It's the enforced gate that can't be skipped (unless you change the rules).

This module teaches you how to build security deeply into your CI/CD pipelines—not as an afterthought, but as a first-class citizen alongside build and test.

After this module, you'll understand:
- How to structure security stages in CI/CD
- SAST, SCA, and container scanning implementation
- Dependency vulnerability management
- Security gates: what to block, what to warn

---

## The Security Pipeline Architecture

### Pipeline Stages Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    DEVSECOPS PIPELINE STAGES                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  SOURCE         BUILD            TEST           DEPLOY          │
│  ┌─────────┐   ┌─────────┐     ┌─────────┐    ┌─────────┐      │
│  │ Lint    │   │ SAST    │     │ DAST    │    │ Policy  │      │
│  │ Secrets │   │ SCA     │     │ IAST    │    │ Verify  │      │
│  │ Commit  │   │ Image   │     │ API     │    │ Sign    │      │
│  │ signing │   │ scan    │     │ security│    │ Admit   │      │
│  └────┬────┘   └────┬────┘     └────┬────┘    └────┬────┘      │
│       │             │               │              │            │
│       ▼             ▼               ▼              ▼            │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │                    SECURITY GATES                            ││
│  │  Critical/High → Block    Medium → Warn    Low → Log        ││
│  └─────────────────────────────────────────────────────────────┘│
│                              │                                   │
│                              ▼                                   │
│                    ┌─────────────────┐                          │
│                    │    REPORTS &    │                          │
│                    │    DASHBOARDS   │                          │
│                    └─────────────────┘                          │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### What Happens at Each Stage

| Stage | Security Activities | Blocks On |
|-------|---------------------|-----------|
| **Source** | Secrets detection, commit signing, license check | High-entropy secrets |
| **Build** | SAST, SCA, IaC scanning, image scanning | Critical vulns |
| **Test** | DAST, API security, integration security tests | Auth bypass, injection |
| **Deploy** | Policy verification, signature check, admission | Policy violations |

---

## Static Application Security Testing (SAST)

### What SAST Does

SAST analyzes source code without running it:

```
┌─────────────────────────────────────────────────────────────┐
│                     SAST ANALYSIS                            │
│                                                              │
│  SOURCE CODE                    SAST ENGINE                  │
│  ┌──────────┐                  ┌──────────┐                 │
│  │ def login│      Parse       │ AST      │                 │
│  │   query =│ ────────────────▶│ Analysis │                 │
│  │   "SELECT│                  │ Data flow│                 │
│  │   ..." + │                  │ Patterns │                 │
│  │   user_id│                  └────┬─────┘                 │
│  └──────────┘                       │                        │
│                                     ▼                        │
│                              ┌──────────┐                    │
│                              │ FINDINGS │                    │
│                              │ SQL Inj  │                    │
│                              │ Line 42  │                    │
│                              └──────────┘                    │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Popular SAST Tools

| Tool | Languages | Open Source | Best For |
|------|-----------|-------------|----------|
| **Semgrep** | 30+ | Yes | Fast, custom rules |
| **CodeQL** | 10+ | Yes (analysis) | Deep analysis, GitHub |
| **SonarQube** | 25+ | Community | Enterprise, quality |
| **Bandit** | Python | Yes | Python-specific |
| **Gosec** | Go | Yes | Go-specific |
| **Brakeman** | Ruby | Yes | Rails-specific |

### GitHub Actions: Semgrep

```yaml
name: Security Scan
on: [push, pull_request]

jobs:
  semgrep:
    runs-on: ubuntu-latest
    container:
      image: returntocorp/semgrep
    steps:
      - uses: actions/checkout@v4

      - name: Run Semgrep
        run: |
          semgrep ci \
            --config p/security-audit \
            --config p/secrets \
            --config p/owasp-top-ten \
            --sarif --output semgrep.sarif

      - name: Upload SARIF
        uses: github/codeql-action/upload-sarif@v2
        with:
          sarif_file: semgrep.sarif
        if: always()
```

### GitHub Actions: CodeQL

```yaml
name: CodeQL Analysis
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]
  schedule:
    - cron: '0 6 * * 1'  # Weekly deep scan

jobs:
  analyze:
    runs-on: ubuntu-latest
    permissions:
      security-events: write

    steps:
      - uses: actions/checkout@v4

      - name: Initialize CodeQL
        uses: github/codeql-action/init@v2
        with:
          languages: javascript, python
          queries: security-extended

      - name: Build (if needed)
        run: |
          # Add build commands for compiled languages

      - name: Perform CodeQL Analysis
        uses: github/codeql-action/analyze@v2
```

### GitLab CI: SAST

```yaml
# .gitlab-ci.yml
include:
  - template: Security/SAST.gitlab-ci.yml

variables:
  SAST_EXCLUDED_PATHS: "spec, test, tests, tmp"
  SECURE_LOG_LEVEL: "debug"

sast:
  stage: test
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH
```

---

## Did You Know?

1. **CodeQL was originally created by a company called Semmle**, which GitHub acquired in 2019 for $25 million. CodeQL is now free for open source and powers GitHub's security features.

2. **The term "SARIF" (Static Analysis Results Interchange Format)** was standardized by OASIS in 2020. It allows different security tools to output results in a common format, making tool comparison and migration possible.

3. **The first SCA tool was created in 2002** by Black Duck Software. Before that, developers had no automated way to know what open source components were in their software or if they were vulnerable.

4. **Log4Shell (CVE-2021-44228) affected an estimated 93% of enterprise cloud environments**. SCA tools that tracked transitive dependencies found it in minutes; organizations without SCA spent weeks manually auditing.

---

## Software Composition Analysis (SCA)

### Why SCA Matters

Modern applications are 80-90% dependencies:

```
┌─────────────────────────────────────────────────────────────┐
│                YOUR APPLICATION                              │
│                                                              │
│  ┌───────────────────────────────────────────────────────┐  │
│  │                                                        │  │
│  │    Your Code                                           │  │
│  │    (10-20%)                                            │  │
│  │                                                        │  │
│  ├────────────────────────────────────────────────────────┤  │
│  │                                                        │  │
│  │    Direct Dependencies                                 │  │
│  │    (30-40%)                                            │  │
│  │                                                        │  │
│  ├────────────────────────────────────────────────────────┤  │
│  │                                                        │  │
│  │    Transitive Dependencies                             │  │
│  │    (Dependencies of your dependencies)                 │  │
│  │    (40-60%)                                            │  │
│  │                                                        │  │
│  └────────────────────────────────────────────────────────┘  │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

SAST doesn't see dependency vulnerabilities. SCA does.

### SCA Tools

| Tool | Ecosystems | Open Source | Best For |
|------|------------|-------------|----------|
| **Trivy** | All | Yes | All-in-one |
| **Snyk** | All | Freemium | Developer UX |
| **Dependabot** | Major | Free (GitHub) | Auto-PRs |
| **OWASP Dependency-Check** | Java, .NET | Yes | OWASP compliance |
| **Grype** | Containers, SBOM | Yes | Anchore ecosystem |
| **npm audit** | Node.js | Built-in | Quick checks |

### GitHub Actions: Trivy SCA

```yaml
name: Dependency Scan
on: [push, pull_request]

jobs:
  dependency-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Run Trivy vulnerability scanner
        uses: aquasecurity/trivy-action@master
        with:
          scan-type: 'fs'
          scan-ref: '.'
          format: 'sarif'
          output: 'trivy-results.sarif'
          severity: 'CRITICAL,HIGH'

      - name: Upload Trivy scan results
        uses: github/codeql-action/upload-sarif@v2
        with:
          sarif_file: 'trivy-results.sarif'
```

### GitHub Actions: Snyk

```yaml
name: Snyk Security
on: [push, pull_request]

jobs:
  snyk:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Run Snyk to check for vulnerabilities
        uses: snyk/actions/node@master
        env:
          SNYK_TOKEN: ${{ secrets.SNYK_TOKEN }}
        with:
          args: --severity-threshold=high

      - name: Upload result to Snyk
        uses: snyk/actions/node@master
        env:
          SNYK_TOKEN: ${{ secrets.SNYK_TOKEN }}
        with:
          command: monitor
```

### Dependabot Configuration

```yaml
# .github/dependabot.yml
version: 2
updates:
  - package-ecosystem: "npm"
    directory: "/"
    schedule:
      interval: "weekly"
    open-pull-requests-limit: 10
    labels:
      - "dependencies"
      - "security"
    reviewers:
      - "security-team"

  - package-ecosystem: "docker"
    directory: "/"
    schedule:
      interval: "weekly"

  - package-ecosystem: "github-actions"
    directory: "/"
    schedule:
      interval: "weekly"
```

---

## Container Image Scanning

### What Container Scanning Finds

```
┌─────────────────────────────────────────────────────────────┐
│                  CONTAINER IMAGE LAYERS                      │
│                                                              │
│  ┌─────────────────────────────────────────────────────────┐│
│  │ Your Application Code                                    ││
│  │ - App vulnerabilities (covered by SAST)                  ││
│  └─────────────────────────────────────────────────────────┘│
│  ┌─────────────────────────────────────────────────────────┐│
│  │ Application Dependencies                                 ││
│  │ - Library CVEs (covered by SCA)                          ││
│  └─────────────────────────────────────────────────────────┘│
│  ┌─────────────────────────────────────────────────────────┐│
│  │ OS Packages (apt, apk, yum)           ◀── Container     ││
│  │ - OpenSSL, curl, libc vulnerabilities     Scanning      ││
│  └─────────────────────────────────────────────────────────┘│
│  ┌─────────────────────────────────────────────────────────┐│
│  │ Base Image (ubuntu, alpine, distroless)◀── Container    ││
│  │ - Kernel, system library vulnerabilities   Scanning     ││
│  └─────────────────────────────────────────────────────────┘│
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Container Scanning Tools

| Tool | Registry Integration | CI Integration | Best For |
|------|---------------------|----------------|----------|
| **Trivy** | All | All | All-in-one |
| **Grype** | All | All | SBOM integration |
| **Clair** | Quay | Limited | CoreOS users |
| **Snyk Container** | All | All | Developer UX |
| **Docker Scout** | Docker Hub | Docker | Docker users |

### GitHub Actions: Trivy Container Scan

```yaml
name: Container Security
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  build-and-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Build image
        run: docker build -t myapp:${{ github.sha }} .

      - name: Run Trivy vulnerability scanner
        uses: aquasecurity/trivy-action@master
        with:
          image-ref: 'myapp:${{ github.sha }}'
          format: 'sarif'
          output: 'trivy-results.sarif'
          severity: 'CRITICAL,HIGH'
          exit-code: '1'  # Fail on critical/high

      - name: Upload Trivy scan results
        uses: github/codeql-action/upload-sarif@v2
        with:
          sarif_file: 'trivy-results.sarif'
        if: always()

      - name: Push to registry (if scan passes)
        if: github.ref == 'refs/heads/main'
        run: |
          docker tag myapp:${{ github.sha }} registry.example.com/myapp:${{ github.sha }}
          docker push registry.example.com/myapp:${{ github.sha }}
```

### GitLab CI: Container Scanning

```yaml
include:
  - template: Security/Container-Scanning.gitlab-ci.yml

container_scanning:
  variables:
    CS_IMAGE: $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA
    CS_SEVERITY_THRESHOLD: HIGH
```

---

## Infrastructure as Code Scanning

### IaC Security Issues

```yaml
# Terraform - Multiple Issues
resource "aws_s3_bucket" "bad" {
  bucket = "my-bucket"
  acl    = "public-read"  # Issue: Public bucket
  # Missing: encryption
  # Missing: versioning
  # Missing: logging
}

# Kubernetes - Multiple Issues
apiVersion: v1
kind: Pod
spec:
  containers:
  - name: app
    image: nginx:latest           # Issue: No version pinning
    securityContext:
      privileged: true            # Issue: Privileged container
      runAsRoot: true             # Issue: Running as root
    resources: {}                 # Issue: No resource limits
```

### IaC Scanning Tools

| Tool | Targets | Open Source |
|------|---------|-------------|
| **Checkov** | Terraform, K8s, CloudFormation, Docker | Yes |
| **tfsec** | Terraform | Yes |
| **Trivy** | Terraform, K8s, Docker, CloudFormation | Yes |
| **kube-linter** | Kubernetes, Helm | Yes |
| **Kubesec** | Kubernetes | Yes |
| **Terrascan** | Terraform, K8s, Docker | Yes |

### GitHub Actions: Checkov

```yaml
name: IaC Security
on: [push, pull_request]

jobs:
  checkov:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Run Checkov
        uses: bridgecrewio/checkov-action@master
        with:
          directory: .
          framework: terraform,kubernetes,dockerfile
          output_format: sarif
          output_file_path: checkov.sarif
          soft_fail: false  # Fail on issues

      - name: Upload SARIF
        uses: github/codeql-action/upload-sarif@v2
        with:
          sarif_file: checkov.sarif
        if: always()
```

### GitHub Actions: Trivy IaC

```yaml
name: IaC Scan
on: [push, pull_request]

jobs:
  trivy-iac:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Run Trivy IaC scanner
        uses: aquasecurity/trivy-action@master
        with:
          scan-type: 'config'
          scan-ref: '.'
          format: 'sarif'
          output: 'trivy-iac.sarif'
          severity: 'CRITICAL,HIGH,MEDIUM'

      - name: Upload SARIF
        uses: github/codeql-action/upload-sarif@v2
        with:
          sarif_file: 'trivy-iac.sarif'
```

---

## War Story: The Pipeline That Saved Black Friday

An e-commerce company was pushing a major update three days before Black Friday.

**The Setup:**
- 200+ microservices
- Daily deployments
- Basic security: SAST in some repos, no SCA, no container scanning

**The Discovery:**

Two days before Black Friday, they added Trivy to scan container images. First scan:

```
Total: 847 vulnerabilities
  Critical: 12
  High: 89
  Medium: 412
  Low: 334

Critical vulnerabilities:
- CVE-2021-44228 (Log4Shell) in 8 services
- CVE-2022-22965 (Spring4Shell) in 3 services
- CVE-2021-3711 (OpenSSL) in base image
```

**The Response:**

1. **Immediate triage**: Log4Shell and Spring4Shell in internet-facing services
2. **Mitigation**: WAF rules to block exploit patterns
3. **Fix**: Emergency patches for critical services
4. **Base image update**: New base image for all services

**The Timeline:**
- Day 1: Discovery, triage, WAF rules deployed
- Day 2: Critical services patched, tested, deployed
- Black Friday: Zero incidents

**The After:**

They implemented:
```yaml
# All container builds now require:
- Image scanning (Trivy)
- Block on Critical
- Warn on High (fix within 7 days SLA)
- Base image weekly updates
- SBOM generation for every image
```

**The lesson:** If they'd had container scanning for six months, they wouldn't have had a Black Friday crisis. The vulnerabilities accumulated silently.

### The CI/CD Tool That Became the Attack Vector (March 2026)

The Trivy/LiteLLM incident of March 2026 is a cautionary tale for every CI/CD pipeline. Threat actor TeamPCP compromised the `trivy-action` GitHub Action by rewriting Git tags to point to a malicious release. When LiteLLM's pipeline ran Trivy **without pinning the action to a commit SHA**, the compromised scanner exfiltrated their `PYPI_PUBLISH` token from the GitHub Actions runner environment. The attacker then published backdoored versions of LiteLLM (3.4M daily downloads) that deployed persistent backdoor pods into victim Kubernetes clusters.

Two CI/CD lessons from this incident:

**1. Pin GitHub Actions to commit SHAs, not tags:**
```yaml
# VULNERABLE — tags are mutable, can be rewritten:
- uses: aquasecurity/trivy-action@latest
- uses: aquasecurity/trivy-action@v0.69

# SECURE — commit SHAs are immutable:
- uses: aquasecurity/trivy-action@a7a829a0ece790ca07e16ed53ba6daba6e7e4e04
```

**2. Scope secrets to the jobs that need them:**
```yaml
jobs:
  scan:
    # This job has NO access to publish tokens
    permissions:
      contents: read
    steps:
      - uses: aquasecurity/trivy-action@a7a829...  # pinned

  publish:
    needs: scan
    # Only THIS job can publish
    permissions:
      id-token: write  # OIDC for Trusted Publishers
    steps:
      - uses: pypa/gh-action-pypi-publish@release/v1
```

For the full attack chain, payload analysis, and postmortem, see [Module 4.4: Supply Chain Security](../module-4.4-supply-chain-security/#war-story-when-the-security-scanner-became-the-weapon-march-2026).

---

## Security Gates and Policies

### Defining Security Gates

Not all findings are equal. Define what blocks vs warns:

```
┌─────────────────────────────────────────────────────────────┐
│                    SECURITY GATE POLICY                      │
│                                                              │
│  Finding Severity    Action        SLA                       │
│  ─────────────────   ─────────     ───                       │
│  Critical            BLOCK         Fix before merge          │
│  High                BLOCK/WARN*   Fix within 7 days         │
│  Medium              WARN          Fix within 30 days        │
│  Low                 LOG           Backlog, best effort      │
│                                                              │
│  * High = Block for new code, Warn for existing              │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Implementing Gates in GitHub Actions

```yaml
name: Security Gate
on: [pull_request]

jobs:
  security-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      # SAST
      - name: Run Semgrep
        id: semgrep
        uses: returntocorp/semgrep-action@v1
        with:
          config: p/security-audit

      # SCA
      - name: Run Trivy (dependencies)
        id: trivy-deps
        uses: aquasecurity/trivy-action@master
        with:
          scan-type: 'fs'
          severity: 'CRITICAL,HIGH'
          exit-code: '1'
        continue-on-error: true

      # Container
      - name: Build and scan image
        id: trivy-image
        run: |
          docker build -t test:${{ github.sha }} .
          trivy image --exit-code 1 --severity CRITICAL test:${{ github.sha }}
        continue-on-error: true

      # Gate decision
      - name: Security Gate
        run: |
          if [[ "${{ steps.trivy-deps.outcome }}" == "failure" ]]; then
            echo "::error::Critical dependency vulnerabilities found"
            exit 1
          fi
          if [[ "${{ steps.trivy-image.outcome }}" == "failure" ]]; then
            echo "::error::Critical container vulnerabilities found"
            exit 1
          fi
          echo "Security gate passed"
```

### Branch Protection Rules

Enforce security jobs in GitHub:

```
Repository Settings → Branches → Branch protection rules

☑ Require status checks to pass before merging
  ☑ security-scan
  ☑ sast
  ☑ container-scan

☑ Require branches to be up to date before merging
☑ Do not allow bypassing the above settings
```

---

## Complete Pipeline Example

### Full GitHub Actions Workflow

```yaml
name: Secure CI/CD Pipeline
on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

jobs:
  # Stage 1: Source Security
  secrets-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Detect secrets
        uses: gitleaks/gitleaks-action@v2
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}

  # Stage 2: SAST
  sast:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Semgrep
        uses: returntocorp/semgrep-action@v1
        with:
          config: >-
            p/security-audit
            p/secrets
            p/owasp-top-ten

  # Stage 3: SCA
  dependency-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Trivy filesystem scan
        uses: aquasecurity/trivy-action@master
        with:
          scan-type: 'fs'
          severity: 'CRITICAL,HIGH'
          exit-code: '1'
          format: 'sarif'
          output: 'trivy-fs.sarif'

      - name: Upload SARIF
        uses: github/codeql-action/upload-sarif@v2
        with:
          sarif_file: 'trivy-fs.sarif'
        if: always()

  # Stage 4: Build & Container Scan
  build-and-scan:
    runs-on: ubuntu-latest
    needs: [secrets-scan, sast, dependency-scan]
    outputs:
      image-digest: ${{ steps.build.outputs.digest }}
    steps:
      - uses: actions/checkout@v4

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Build image
        id: build
        uses: docker/build-push-action@v5
        with:
          context: .
          load: true
          tags: ${{ env.IMAGE_NAME }}:${{ github.sha }}

      - name: Trivy image scan
        uses: aquasecurity/trivy-action@master
        with:
          image-ref: ${{ env.IMAGE_NAME }}:${{ github.sha }}
          severity: 'CRITICAL,HIGH'
          exit-code: '1'
          format: 'sarif'
          output: 'trivy-image.sarif'

      - name: Upload SARIF
        uses: github/codeql-action/upload-sarif@v2
        with:
          sarif_file: 'trivy-image.sarif'
        if: always()

  # Stage 5: IaC Scan
  iac-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Checkov
        uses: bridgecrewio/checkov-action@master
        with:
          directory: ./kubernetes/
          framework: kubernetes
          soft_fail: false

  # Stage 6: Push (only on main, after all checks)
  push:
    runs-on: ubuntu-latest
    needs: [build-and-scan, iac-scan]
    if: github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v4

      - name: Login to registry
        uses: docker/login-action@v3
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Build and push
        uses: docker/build-push-action@v5
        with:
          context: .
          push: true
          tags: |
            ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:${{ github.sha }}
            ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:latest
```

---

## Common Mistakes

| Mistake | Problem | Solution |
|---------|---------|----------|
| Scanning after push | Vulnerable images in registry | Scan before push, gate deployment |
| No severity filtering | Alert fatigue, everything blocked | Critical = block, High = warn, tune |
| Caching old scans | New CVEs not caught | Scan on every build, schedule deep scans |
| No SARIF integration | Findings not visible in PR | Upload to GitHub Security tab |
| Scanning only main branch | Issues merge without review | Scan all PRs |
| No baseline for legacy | 1000 findings = chaos | Baseline existing, focus on new |

---

## Quiz: Check Your Understanding

### Question 1
Your container scan shows 50 vulnerabilities in the base image (ubuntu:20.04), but your application code has no vulnerabilities. The vulnerabilities are in packages your app doesn't use. Should you block the build?

<details>
<summary>Show Answer</summary>

**It depends, but probably yes for Critical/High:**

**Why you should care (even for unused packages):**
1. Attackers can exploit any vulnerability if they get code execution
2. "Unused" packages might be used by other packages
3. Compliance frameworks require patching all known vulnerabilities
4. It's easy for attackers to check for vulnerable packages

**Recommended approach:**

1. **Switch to minimal base images:**
   ```dockerfile
   # Instead of:
   FROM ubuntu:20.04

   # Use:
   FROM gcr.io/distroless/base
   # Or:
   FROM alpine:3.18
   # Or:
   FROM cgr.dev/chainguard/static
   ```

2. **If you must use ubuntu:**
   - Update regularly: `apt-get update && apt-get upgrade`
   - Remove unused packages: `apt-get autoremove`
   - Use multi-stage builds to exclude build dependencies

3. **For gating:**
   - Block on Critical (exploitable RCE)
   - Warn on High (require fix within SLA)
   - Track Medium/Low as technical debt

The best solution is minimizing the attack surface with smaller images.

</details>

### Question 2
Your SCA tool reports a Critical vulnerability in a transitive dependency (a dependency of a dependency). You don't directly use the vulnerable function. What should you do?

<details>
<summary>Show Answer</summary>

**Still treat it seriously, but investigate first:**

**Step 1: Understand the exposure**
```bash
# Check dependency tree
npm ls vulnerable-package
pip show --files vulnerable-package
```

**Step 2: Check if vulnerable function is reachable**
- Read the CVE description
- Check if your code path can reach the vulnerable function
- Use tools like Snyk's reachability analysis

**Step 3: Determine action**

If reachable:
- High priority fix
- Update the direct dependency that pulls it in
- Or override the transitive version if possible

If NOT reachable:
- Lower priority, but still fix
- Attackers can change your code path
- New code might use the vulnerable path
- Track as tech debt with SLA

**Step 4: Fix options**

```json
// npm: Override transitive dependency
{
  "overrides": {
    "vulnerable-package": "2.0.0"
  }
}
```

```python
# pip: Pin in requirements.txt
vulnerable-package>=2.0.0  # Fixed version
```

**Never ignore Critical CVEs** even in transitive dependencies. The Log4Shell vulnerability was a transitive dependency in most affected applications.

</details>

### Question 3
Your pipeline now takes 15 minutes due to all the security scans. Developers are complaining. How do you optimize?

<details>
<summary>Show Answer</summary>

**Optimize for speed without sacrificing security:**

**1. Parallelize scans:**
```yaml
jobs:
  sast:
    runs-on: ubuntu-latest
  sca:
    runs-on: ubuntu-latest  # Runs in parallel
  container-scan:
    runs-on: ubuntu-latest  # Runs in parallel
    needs: [build]          # Only after build
```

**2. Incremental scanning:**
- Only scan changed files for SAST
- Only rescan if dependencies changed for SCA
```yaml
- name: Get changed files
  id: changes
  uses: dorny/paths-filter@v2
  with:
    filters: |
      src: 'src/**'
      deps: 'package*.json'
```

**3. Cache vulnerability databases:**
```yaml
- name: Cache Trivy DB
  uses: actions/cache@v3
  with:
    path: ~/.cache/trivy
    key: trivy-db-${{ github.run_id }}
    restore-keys: trivy-db-
```

**4. Quick PR scans, deep scheduled scans:**
- PR: Fast scan, current code only
- Nightly: Deep scan, full history

**5. Use faster tools:**
- Semgrep is faster than SonarQube for SAST
- Trivy is faster than Clair for containers

**6. Right-size runners:**
```yaml
runs-on: ubuntu-latest-4-cores  # Faster for parallel tasks
```

**Target: < 10 minutes for PR checks.** Deep scans can run longer on schedules.

</details>

### Question 4
A new zero-day is announced (like Log4Shell). How should your pipeline help you respond?

<details>
<summary>Show Answer</summary>

**A good pipeline enables rapid response:**

**Immediate actions:**

1. **Update vulnerability database:**
   ```bash
   # Trivy
   trivy image --download-db-only

   # Most tools auto-update, but force refresh
   ```

2. **Trigger scans on all repos:**
   ```bash
   # GitHub Actions: workflow_dispatch
   gh workflow run security-scan.yml -R org/repo
   ```

3. **Check existing images:**
   ```bash
   # Scan all images in registry
   trivy image --severity CRITICAL registry.example.com/myapp:latest
   ```

**Pipeline design for emergencies:**

```yaml
# Schedule frequent rescans
on:
  schedule:
    - cron: '0 */4 * * *'  # Every 4 hours during incidents

# Manual trigger for emergency scans
on:
  workflow_dispatch:
    inputs:
      severity:
        description: 'Minimum severity to report'
        default: 'CRITICAL'
```

**Pre-build response capabilities:**

1. **SBOM for every image** — Know what's deployed
2. **Centralized vulnerability dashboard** — See all findings
3. **Automated PR creation** — Fix dependencies automatically
4. **Slack/PagerDuty integration** — Alert immediately

**Post-incident:**

- Add specific pattern detection if generic rules missed it
- Review why existing scans didn't catch it sooner
- Update runbook for next zero-day

</details>

---

## Hands-On Exercise: Build a Security Pipeline

Create a complete security pipeline for a sample project.

### Part 1: Create Sample Project

```bash
mkdir devsecops-pipeline-demo && cd devsecops-pipeline-demo
git init

# Create a simple app with intentional issues
cat > app.py << 'EOF'
import os
import sqlite3

def get_user(user_id):
    # Intentional SQL injection vulnerability
    conn = sqlite3.connect('users.db')
    query = f"SELECT * FROM users WHERE id = {user_id}"
    return conn.execute(query).fetchone()

def run_command(cmd):
    # Intentional command injection
    os.system(cmd)

# Intentional hardcoded secret
API_KEY = "sk_live_1234567890abcdef"
EOF

cat > requirements.txt << 'EOF'
requests==2.25.0
pyyaml==5.3
EOF

cat > Dockerfile << 'EOF'
FROM python:3.9
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
USER root
CMD ["python", "app.py"]
EOF
```

### Part 2: Create Security Pipeline

```yaml
# .github/workflows/security.yml
name: Security Pipeline
on: [push, pull_request]

jobs:
  secrets:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Detect secrets
        uses: gitleaks/gitleaks-action@v2
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}

  sast:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Semgrep
        uses: returntocorp/semgrep-action@v1
        with:
          config: p/python

  sca:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Trivy FS scan
        uses: aquasecurity/trivy-action@master
        with:
          scan-type: 'fs'
          severity: 'CRITICAL,HIGH'

  container:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Build image
        run: docker build -t test:latest .
      - name: Trivy image scan
        uses: aquasecurity/trivy-action@master
        with:
          image-ref: 'test:latest'
          severity: 'CRITICAL,HIGH'
```

### Part 3: Run and Fix

Push to GitHub and observe:
1. Secrets scan should find the API key
2. SAST should find SQL injection and command injection
3. SCA should find vulnerabilities in old dependencies
4. Container scan should find issues in base image and Dockerfile

Fix each issue and push again until pipeline passes.

### Success Criteria

- [ ] All four scan types implemented
- [ ] Pipeline catches all intentional vulnerabilities
- [ ] Able to fix issues and pass the pipeline
- [ ] SARIF results uploaded to GitHub Security tab

---

## Key Takeaways

1. **CI/CD is the enforced checkpoint** — Pre-commit can be bypassed, CI/CD cannot
2. **Layer your defenses** — SAST + SCA + Container + IaC each catch different issues
3. **Gate on severity** — Block Critical, warn on High, log Medium/Low
4. **Scan before push** — Don't put vulnerable images in registries
5. **Automate remediation** — Dependabot PRs, automated upgrades reduce friction

---

## Further Reading

**Tools Documentation:**
- **Trivy** — aquasecurity.github.io/trivy
- **Semgrep** — semgrep.dev/docs
- **CodeQL** — codeql.github.com
- **Checkov** — checkov.io

**Standards:**
- **SARIF** — sarifweb.azurewebsites.net
- **OWASP ASVS** — owasp.org/asvs

**Guides:**
- **GitHub Security Guides** — docs.github.com/security
- **GitLab Secure** — docs.gitlab.com/ee/user/application_security

---

## Summary

Security in CI/CD is about embedding security checks at every stage:

- **Source**: Secrets detection, license compliance
- **Build**: SAST (code), SCA (dependencies), container scanning
- **Test**: DAST, API security testing
- **Deploy**: IaC scanning, policy enforcement

The key is balancing security with developer velocity:
- Block on Critical/High
- Warn on Medium
- Track Low as tech debt
- Optimize for speed (parallel scans, caching)
- Upload results to dashboards for visibility

A well-designed security pipeline catches vulnerabilities automatically, before they reach production.

---

## Next Module

Continue to [Module 4.4: Supply Chain Security](../module-4.4-supply-chain-security/) to learn about securing the entire software supply chain from source to deployment.

---

*"Your pipeline is your last line of defense before production. Make it count."*
