---
title: "Module 12.5: Trivy - The Swiss Army Knife of Security Scanning"
slug: platform/toolkits/security-quality/code-quality/module-12.5-trivy
sidebar:
  order: 6
---
## Complexity: [MEDIUM]
## Time to Complete: 45-50 minutes

---

## Prerequisites

Before starting this module, you should have completed:
- [DevSecOps Discipline](../../../disciplines/reliability-security/devsecops/) - Security scanning concepts
- Container fundamentals (images, Dockerfiles)
- Basic Kubernetes knowledge
- CI/CD basics

---

## What You'll Be Able to Do

After completing this module, you will be able to:

- **Deploy Trivy for comprehensive vulnerability scanning of container images, filesystems, and Git repositories**
- **Configure Trivy in CI/CD pipelines with severity thresholds and ignore policies for practical scanning**
- **Implement Trivy Operator for continuous Kubernetes cluster scanning with vulnerability and config audit reports**
- **Compare Trivy's open-source scanning against commercial alternatives for enterprise security requirements**


## Why This Module Matters

**The Open Source Security Scanner That Does Everything**

The security architect stared at her spreadsheet in disbelief. After three months of evaluating security tools, she had mapped out what her fintech startup needed to meet SOC2 requirements: Grype for container scanning ($0, but no IaC), Checkov for Terraform ($0, but no containers), Syft for SBOMs ($0, but separate from scanning), Gitleaks for secrets ($0, but another integration), and Snyk for the dashboard ($15,000/year for 30 developers).

"That's five tools, five CI integrations, five different output formats, and $15K," she reported to the CISO. "And we still need someone to correlate all the findings."

"What about that Trivy thing Harbor uses?" the CISO asked.

She hadn't seriously considered it—surely a free tool couldn't do everything. But after a two-hour proof of concept, she deleted her spreadsheet. Trivy did container scanning, IaC scanning, SBOM generation, secret detection, and Kubernetes cluster scanning. One tool. One configuration. One output format.

The fintech passed their SOC2 audit with zero additional tooling costs. The security architect became Trivy's biggest internal advocate—and eventually, an Aqua Security customer success story.

Trivy isn't the deepest scanner in any single category, but it's remarkably good across all of them. It's completely free, backed by Aqua Security, and it's become the default scanner in Harbor, AWS Inspector, and countless CI pipelines.

---

## Did You Know?

- **Trivy started as a weekend project and became a CNCF project in 3 years** — Teppei Fukuda, an Aqua Security engineer, built Trivy in 2019 because existing scanners were too slow and required too much setup. He optimized the vulnerability database download and caching until first scan ran in under 15 seconds. By 2022, Trivy had 15,000+ GitHub stars and joined the CNCF sandbox. Today it's the most-starred container security project on GitHub.

- **AWS built Inspector on Trivy because they couldn't beat it** — When AWS launched the new Inspector in 2021, security researchers noticed something interesting: the vulnerability signatures matched Trivy exactly. AWS confirmed they use Trivy's engine under the hood, adding their own database updates. Even Amazon couldn't build a better scanner—so they adopted the open source one.

- **Harbor chose Trivy after a year-long evaluation that tested 8 scanners** — The Harbor team evaluated Clair, Anchore, Aqua Scanner, and five others before selecting Trivy as the default. The deciding factors: scan speed (10x faster than Clair), accuracy (lowest false positive rate), and operational simplicity (single binary, no database server required).

- **The Log4Shell incident made Trivy famous overnight** — On December 9, 2021, the Log4j vulnerability (CVE-2021-44228) was disclosed. Within 4 hours, Trivy had detection rules. Within 24 hours, thousands of companies had run `trivy fs --scanners vuln .` for the first time. Trivy downloads spiked 400% that week—and many of those emergency users became permanent adopters.

- **In March 2026, Trivy itself was compromised in the TeamPCP supply chain attack** — Threat actor TeamPCP rewrote Git tags in the `trivy-action` GitHub Action repository, pointing tag `v0.69.4` to a malicious release. The compromised action exfiltrated CI/CD secrets from any pipeline that used `trivy-action@latest` or an unpinned tag. The most high-profile victim was LiteLLM (3.4M daily PyPI downloads), whose stolen `PYPI_PUBLISH` token was used to push backdoored packages that deployed persistent pods into victim Kubernetes clusters. The incident proved that even trusted security tools can become attack vectors -- and that pinning GitHub Actions to commit SHAs (not tags) is not optional. See [Module 4.4: Supply Chain Security](../../../disciplines/reliability-security/devsecops/module-4.4-supply-chain-security/) for the full postmortem.

---

## What Trivy Scans

```
TRIVY CAPABILITIES
─────────────────────────────────────────────────────────────────

┌─────────────────────────────────────────────────────────────────┐
│                        TRIVY TARGETS                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  CONTAINER IMAGES                                               │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  • OS packages (Alpine, Debian, Ubuntu, RHEL, etc.)       │  │
│  │  • Language packages (npm, pip, gem, etc.)                │  │
│  │  • Licenses                                                │  │
│  │  • Secrets embedded in images                             │  │
│  │  • Misconfigurations                                      │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                  │
│  FILESYSTEMS & REPOSITORIES                                     │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  • Dependencies (package-lock.json, go.sum, etc.)         │  │
│  │  • Secrets in code                                         │  │
│  │  • IaC misconfigurations                                  │  │
│  │  • License compliance                                      │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                  │
│  KUBERNETES                                                     │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  • Cluster misconfigurations                              │  │
│  │  • Workload vulnerabilities                               │  │
│  │  • RBAC analysis                                          │  │
│  │  • Network policies                                       │  │
│  │  • Secrets in cluster                                     │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                  │
│  INFRASTRUCTURE AS CODE                                         │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  • Terraform                                               │  │
│  │  • CloudFormation                                          │  │
│  │  • Kubernetes YAML                                         │  │
│  │  • Helm charts                                             │  │
│  │  • Docker Compose                                          │  │
│  │  • Ansible                                                 │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                  │
│  SBOM                                                           │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  • Generate CycloneDX                                      │  │
│  │  • Generate SPDX                                           │  │
│  │  • Scan existing SBOMs                                     │  │
│  │  • Attestations                                            │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Installation

```bash
# macOS (Homebrew)
brew install trivy

# Linux (apt)
sudo apt-get install wget apt-transport-https gnupg lsb-release
wget -qO - https://aquasecurity.github.io/trivy-repo/deb/public.key | sudo apt-key add -
echo deb https://aquasecurity.github.io/trivy-repo/deb $(lsb_release -sc) main | sudo tee -a /etc/apt/sources.list.d/trivy.list
sudo apt-get update
sudo apt-get install trivy

# Linux (script)
curl -sfL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh | sh -s -- -b /usr/local/bin

# Docker (no installation)
docker run aquasec/trivy image nginx:latest

# Verify installation
trivy version
```

---

## Container Scanning

### Basic Usage

```bash
# Scan an image
trivy image nginx:latest

# Scan local image (not from registry)
trivy image --input myapp.tar

# Scan with severity filter
trivy image --severity HIGH,CRITICAL nginx:latest

# Scan only OS packages
trivy image --vuln-type os nginx:latest

# Scan only language packages
trivy image --vuln-type library nginx:latest

# Output as JSON
trivy image --format json --output results.json nginx:latest

# Output as SARIF (for GitHub Security)
trivy image --format sarif --output trivy.sarif nginx:latest
```

### Understanding Results

```
TRIVY CONTAINER SCAN OUTPUT
─────────────────────────────────────────────────────────────────

$ trivy image nginx:1.21

nginx:1.21 (debian 11.2)
========================
Total: 142 (UNKNOWN: 0, LOW: 98, MEDIUM: 31, HIGH: 11, CRITICAL: 2)

┌───────────────────┬──────────────────┬──────────┬────────────────┐
│      Library      │  Vulnerability   │ Severity │ Fixed Version  │
├───────────────────┼──────────────────┼──────────┼────────────────┤
│ curl              │ CVE-2023-38545  │ CRITICAL │ 7.74.0-1.3+deb │
│                   │                  │          │ 11u10          │
├───────────────────┼──────────────────┼──────────┼────────────────┤
│ openssl           │ CVE-2023-5678   │ HIGH     │ 1.1.1n-0+deb11 │
│                   │                  │          │ u5             │
├───────────────────┼──────────────────┼──────────┼────────────────┤
│ ...               │ ...              │ ...      │ ...            │
└───────────────────┴──────────────────┴──────────┴────────────────┘

Node.js (package.json)
======================
Total: 5 (HIGH: 3, MEDIUM: 2)

┌───────────────────┬──────────────────┬──────────┬────────────────┐
│      Library      │  Vulnerability   │ Severity │ Fixed Version  │
├───────────────────┼──────────────────┼──────────┼────────────────┤
│ lodash            │ CVE-2021-23337  │ HIGH     │ 4.17.21        │
│ axios             │ CVE-2021-3749   │ HIGH     │ 0.21.2         │
└───────────────────┴──────────────────┴──────────┴────────────────┘
```

### Scanning Configuration

```yaml
# trivy.yaml
scan:
  # Skip update of vulnerability database
  skip-db-update: false

  # Scanners to use
  scanners:
    - vuln
    - secret
    - misconfig

severity:
  - CRITICAL
  - HIGH
  - MEDIUM

# Ignore unfixed vulnerabilities
ignore-unfixed: true

# Timeout
timeout: 10m

# Cache directory
cache-dir: /tmp/trivy-cache

# Exit code when vulnerabilities found
exit-code: 1
```

```bash
# Use config file
trivy image --config trivy.yaml nginx:latest
```

---

## Filesystem Scanning

### Scanning Source Code

```bash
# Scan current directory
trivy fs .

# Scan specific directory
trivy fs /path/to/project

# Include secrets scanning
trivy fs --scanners vuln,secret,misconfig .

# Scan for specific package types
trivy fs --pkg-types npm,pip .
```

### Scanning Git Repositories

```bash
# Scan remote repository
trivy repo https://github.com/aquasecurity/trivy

# Scan specific branch
trivy repo --branch develop https://github.com/myorg/myrepo

# Scan with commit (for reproducibility)
trivy repo --commit abc123 https://github.com/myorg/myrepo
```

---

## Infrastructure as Code Scanning

### Terraform

```bash
# Scan Terraform files
trivy config ./terraform/

# Scan with specific severity
trivy config --severity HIGH,CRITICAL ./terraform/
```

### Example Terraform Findings

```
TRIVY IAC SCAN - TERRAFORM
─────────────────────────────────────────────────────────────────

$ trivy config ./terraform/

main.tf (terraform)
===================
Tests: 45 (SUCCESSES: 38, FAILURES: 7, EXCEPTIONS: 0)
Failures: 7 (HIGH: 3, MEDIUM: 4)

HIGH: S3 bucket does not have encryption enabled
──────────────────────────────────────────────────────────────────
A server-side encryption is not configured for S3 bucket.

File: main.tf
Line: 25-30

 25 │ resource "aws_s3_bucket" "data" {
 26 │   bucket = "my-data-bucket"
 27 │   acl    = "private"
 28 │ }

See: https://avd.aquasec.com/misconfig/avd-aws-0088

──────────────────────────────────────────────────────────────────
HIGH: Security group allows ingress from 0.0.0.0/0
──────────────────────────────────────────────────────────────────
Security group rule allows all traffic from 0.0.0.0/0

File: security.tf
Line: 12-20

 12 │ resource "aws_security_group_rule" "ssh" {
 13 │   type        = "ingress"
 14 │   from_port   = 22
 15 │   to_port     = 22
 16 │   protocol    = "tcp"
 17 │   cidr_blocks = ["0.0.0.0/0"]  # BAD!
 18 │ }
```

### Kubernetes Manifests

```bash
# Scan Kubernetes YAML
trivy config ./k8s/

# Scan Helm chart
trivy config ./helm/mychart/
```

### Example Kubernetes Findings

```
TRIVY K8S CONFIG SCAN
─────────────────────────────────────────────────────────────────

deployment.yaml (kubernetes)
============================
Tests: 23 (SUCCESSES: 18, FAILURES: 5)

HIGH: Container runs as root
──────────────────────────────────────────────────────────────────
Running as root gives the container full access to the host

File: deployment.yaml
Line: 25

 23 │   containers:
 24 │   - name: app
 25 │     securityContext:
 26 │       runAsUser: 0  # BAD!

Recommendation:
  securityContext:
    runAsNonRoot: true
    runAsUser: 1000

──────────────────────────────────────────────────────────────────
MEDIUM: Container has no resource limits
──────────────────────────────────────────────────────────────────
Resource limits prevent container from consuming excess resources

File: deployment.yaml
Line: 24-30

Recommendation:
  resources:
    limits:
      cpu: "500m"
      memory: "512Mi"
    requests:
      cpu: "100m"
      memory: "128Mi"
```

---

## Secret Detection

```bash
# Scan for secrets in filesystem
trivy fs --scanners secret .

# Scan container image for secrets
trivy image --scanners secret nginx:latest

# Scan Git repository history
trivy repo --scanners secret https://github.com/myorg/myrepo
```

### Example Secret Findings

```
SECRET SCAN RESULTS
─────────────────────────────────────────────────────────────────

$ trivy fs --scanners secret .

Secrets Found: 3

─────────────────────────────────────────────────────────────────
HIGH: AWS Access Key ID
Category: AWS
File: config/prod.env
Line: 5

 5 │ AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE

─────────────────────────────────────────────────────────────────
HIGH: Private Key
Category: Asymmetric Private Key
File: certs/server.key
Line: 1

 1 │ -----BEGIN RSA PRIVATE KEY-----

─────────────────────────────────────────────────────────────────
MEDIUM: Generic API Key
Category: Generic
File: src/api.js
Line: 23

 23 │ const API_KEY = "sk_live_abcd1234567890";
```

---

## SBOM Generation

### Creating SBOMs

```bash
# Generate CycloneDX SBOM
trivy image --format cyclonedx --output sbom.json nginx:latest

# Generate SPDX SBOM
trivy image --format spdx-json --output sbom.spdx.json nginx:latest

# Generate SBOM for filesystem
trivy fs --format cyclonedx --output sbom.json .

# Generate SBOM with VEX (Vulnerability Exploitability eXchange)
trivy image --format cyclonedx --output sbom.json --vex vex.json nginx:latest
```

### Scanning Existing SBOMs

```bash
# Scan a CycloneDX SBOM for vulnerabilities
trivy sbom sbom.json

# Scan SPDX SBOM
trivy sbom sbom.spdx.json
```

---

## Kubernetes Cluster Scanning

### Trivy Operator

```bash
# Install Trivy Operator
helm repo add aqua https://aquasecurity.github.io/helm-charts/
helm repo update

helm install trivy-operator aqua/trivy-operator \
  --namespace trivy-system \
  --create-namespace \
  --set trivy.ignoreUnfixed=true

# View vulnerability reports
kubectl get vulnerabilityreports -A
kubectl get configauditreports -A
kubectl get exposedsecretreports -A
```

### Manual Cluster Scanning

```bash
# Scan cluster (requires kubeconfig)
trivy k8s cluster

# Scan specific namespace
trivy k8s --namespace production cluster

# Scan specific resources
trivy k8s --include-namespaces default deployment/nginx

# Generate report
trivy k8s cluster --report summary
```

### Example Cluster Report

```
KUBERNETES CLUSTER SCAN
─────────────────────────────────────────────────────────────────

$ trivy k8s cluster --report summary

Summary Report
==============

Namespace: default
┌────────────────┬───────────┬──────────┬──────────┬──────────┐
│    Resource    │ Critical  │   High   │  Medium  │   Low    │
├────────────────┼───────────┼──────────┼──────────┼──────────┤
│ nginx-deploy   │     0     │    3     │    12    │    45    │
│ redis          │     2     │    5     │    8     │    23    │
│ postgres       │     1     │    7     │    15    │    34    │
└────────────────┴───────────┴──────────┴──────────┴──────────┘

Misconfigurations:
┌────────────────┬───────────┬──────────┬──────────┬──────────┐
│    Resource    │ Critical  │   High   │  Medium  │   Low    │
├────────────────┼───────────┼──────────┼──────────┼──────────┤
│ nginx-deploy   │     0     │    2     │    3     │    1     │
│ redis          │     1     │    1     │    2     │    0     │
└────────────────┴───────────┴──────────┴──────────┴──────────┘
```

---

## CI/CD Integration

### GitHub Actions

```yaml
# .github/workflows/trivy.yml
name: Security Scan

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Trivy filesystem scan
        uses: aquasecurity/trivy-action@master
        with:
          scan-type: 'fs'
          scan-ref: '.'
          severity: 'CRITICAL,HIGH'
          format: 'sarif'
          output: 'trivy-fs.sarif'

      - name: Build image
        run: docker build -t myapp:${{ github.sha }} .

      - name: Trivy image scan
        uses: aquasecurity/trivy-action@master
        with:
          image-ref: 'myapp:${{ github.sha }}'
          format: 'sarif'
          output: 'trivy-image.sarif'
          severity: 'CRITICAL,HIGH'
          exit-code: '1'  # Fail on findings

      - name: Trivy config scan
        uses: aquasecurity/trivy-action@master
        with:
          scan-type: 'config'
          scan-ref: './terraform'
          severity: 'CRITICAL,HIGH'
          format: 'sarif'
          output: 'trivy-config.sarif'

      - name: Upload to GitHub Security
        uses: github/codeql-action/upload-sarif@v2
        with:
          sarif_file: '.'
```

### GitLab CI

```yaml
# .gitlab-ci.yml
stages:
  - scan

trivy-scan:
  stage: scan
  image:
    name: aquasec/trivy:latest
    entrypoint: [""]
  script:
    # Filesystem scan
    - trivy fs --exit-code 0 --severity HIGH,CRITICAL .

    # Image scan
    - trivy image --exit-code 1 --severity CRITICAL $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA

    # Config scan
    - trivy config --exit-code 0 --severity HIGH,CRITICAL ./terraform/
  artifacts:
    reports:
      container_scanning: gl-container-scanning-report.json
```

### Jenkins Pipeline

```groovy
pipeline {
    agent any

    stages {
        stage('Security Scan') {
            steps {
                sh '''
                    # Install Trivy
                    curl -sfL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh | sh -s -- -b /usr/local/bin

                    # Scan filesystem
                    trivy fs --severity HIGH,CRITICAL --exit-code 0 .

                    # Build and scan image
                    docker build -t myapp:${BUILD_NUMBER} .
                    trivy image --severity CRITICAL --exit-code 1 myapp:${BUILD_NUMBER}

                    # Scan IaC
                    trivy config --severity HIGH,CRITICAL ./terraform/
                '''
            }
        }
    }

    post {
        always {
            archiveArtifacts artifacts: '**/trivy-*.json', allowEmptyArchive: true
        }
    }
}
```

---

## Ignoring Findings

### Using .trivyignore

```bash
# .trivyignore

# Ignore specific CVE
CVE-2023-12345

# Ignore with expiration
CVE-2023-67890 exp:2024-12-31

# Ignore by package
pkg:npm/lodash@4.17.20

# Ignore misconfig by ID
AVD-AWS-0088
```

### Using VEX (Vulnerability Exploitability eXchange)

```json
// vex.json
{
  "@context": "https://openvex.dev/ns/v0.2.0",
  "@id": "https://example.com/vex/myapp",
  "author": "Security Team",
  "timestamp": "2024-01-15T00:00:00Z",
  "statements": [
    {
      "vulnerability": {
        "@id": "CVE-2023-12345"
      },
      "products": [
        {
          "@id": "pkg:docker/myapp@1.0.0"
        }
      ],
      "status": "not_affected",
      "justification": "vulnerable_code_not_in_execute_path",
      "impact_statement": "The vulnerable function is not called in our code"
    }
  ]
}
```

```bash
# Use VEX file
trivy image --vex vex.json myapp:latest
```

---

## War Story: The Registry Gate

*How a healthcare company saved $2.1M in compliance costs with a free tool*

### The Situation

A 200-person healthcare company processing $340M in annual claims was facing a crisis. Their HIPAA compliance audit was in 90 days, and the auditor's preliminary report was damning: "No documented evidence that container images are scanned before production deployment. No software bill of materials. No vulnerability tracking."

The estimated cost to fix this with commercial tools:
- Snyk Enterprise: $180K/year (200 developers × $75/month)
- Additional SBOM tooling: $40K/year
- Compliance dashboard: $35K/year
- Integration consulting: $100K one-time

The CISO looked at the $455K first-year estimate and wondered if there was another way.

### The Architecture

```
SECURE IMAGE PIPELINE
─────────────────────────────────────────────────────────────────

┌─────────────────────────────────────────────────────────────────┐
│                     DEVELOPER PUSHES CODE                        │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                     CI PIPELINE (GitHub Actions)                 │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  1. Build image                                            │  │
│  │  2. Trivy scan (fail on CRITICAL)                         │  │
│  │  3. Generate SBOM                                          │  │
│  │  4. Sign with Cosign                                       │  │
│  │  5. Push to staging registry                               │  │
│  └───────────────────────────────────────────────────────────┘  │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                     HARBOR REGISTRY                              │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  • Trivy scanner enabled                                   │  │
│  │  • Block images with CRITICAL vulns                       │  │
│  │  • Verify Cosign signatures                               │  │
│  │  • Store SBOM with image                                  │  │
│  └───────────────────────────────────────────────────────────┘  │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                     KUBERNETES ADMISSION                         │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  Kyverno policy:                                          │  │
│  │  • Only allow images from Harbor                          │  │
│  │  • Require signature verification                         │  │
│  │  • Require scan timestamp < 24h                           │  │
│  └───────────────────────────────────────────────────────────┘  │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                     PRODUCTION CLUSTER                           │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  Trivy Operator:                                          │  │
│  │  • Continuous scanning of running images                  │  │
│  │  • Alert on new vulnerabilities                           │  │
│  │  • Generate compliance reports                            │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### The Implementation

```yaml
# CI: GitHub Actions
name: Secure Build

on: [push]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Build image
        run: docker build -t ${{ env.IMAGE }}:${{ github.sha }} .

      - name: Trivy scan
        uses: aquasecurity/trivy-action@master
        with:
          image-ref: '${{ env.IMAGE }}:${{ github.sha }}'
          exit-code: '1'
          severity: 'CRITICAL'
          format: 'json'
          output: 'trivy-results.json'

      - name: Generate SBOM
        run: |
          trivy image --format cyclonedx \
            --output sbom.json \
            ${{ env.IMAGE }}:${{ github.sha }}

      - name: Sign image
        run: |
          cosign sign --key env://COSIGN_KEY \
            ${{ env.IMAGE }}:${{ github.sha }}

      - name: Attach SBOM
        run: |
          cosign attach sbom --sbom sbom.json \
            ${{ env.IMAGE }}:${{ github.sha }}

      - name: Push to Harbor
        run: |
          docker push ${{ env.IMAGE }}:${{ github.sha }}
```

```yaml
# Kyverno admission policy
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata:
  name: require-scanned-images
spec:
  validationFailureAction: enforce
  rules:
    - name: check-trivy-scan
      match:
        resources:
          kinds:
            - Pod
      verifyImages:
        - imageReferences:
            - "harbor.example.com/*"
          attestations:
            - predicateType: cosign.sigstore.dev/attestation/vuln/v1
              conditions:
                - all:
                  # No critical vulnerabilities
                  - key: "{{ scanner.result.criticalCount }}"
                    operator: Equals
                    value: "0"
                  # Scan within last 24 hours
                  - key: "{{ time_since('', scanner.scanTime, '', 'h') }}"
                    operator: LessThan
                    value: "24"
```

### Results

| Metric | Before | After |
|--------|--------|-------|
| Critical vulns in prod | Unknown | 0 |
| Mean time to patch | 2 weeks | 4 hours |
| Compliance audit prep | 2 weeks | Automated |
| Images blocked/month | 0 | ~50 |
| Developer friction | None | Minimal (clear feedback) |

**Financial Impact (5-Year TCO):**

| Category | Commercial Approach | Trivy Approach |
|----------|---------------------|----------------|
| Year 1 tooling + setup | $455,000 | $25,000 (Harbor + Kyverno setup) |
| Years 2-5 licensing | $1,020,000 ($255K × 4) | $0 |
| Ongoing maintenance | $120,000 | $45,000 |
| **5-Year Total** | **$1,595,000** | **$70,000** |
| **Savings** | | **$1,525,000** |

The HIPAA audit passed with zero findings. The company used the savings to fund a dedicated platform security engineer who expanded the Trivy implementation to their data science infrastructure.

Three years later, the same setup—with zero licensing costs—had processed 2.3 million container scans, generated 890,000 SBOMs, and blocked 4,200 vulnerable images from production.

### Lessons Learned

1. **Shift left, but also shift right** - Scan in CI AND continuously in cluster
2. **Block critical only** - High/Medium in CI would cause too much friction
3. **SBOM enables future scans** - When new CVE drops, scan existing SBOMs
4. **Signatures prevent bypass** - Can't skip CI and push directly
5. **Clear feedback matters** - Developers need actionable results, not just "blocked"

---

## Trivy vs Alternatives

```
SCANNER COMPARISON
─────────────────────────────────────────────────────────────────

                    Trivy       Grype       Clair       Snyk
─────────────────────────────────────────────────────────────────
TARGETS
Container images    ✓✓          ✓✓          ✓           ✓
Filesystems         ✓           ✓           ✗           ✓
Git repos           ✓           ✗           ✗           ✓
IaC scanning        ✓✓          ✗           ✗           ✓
K8s clusters        ✓✓          ✗           ✗           ✗
SBOM generation     ✓✓          ✓ (Syft)    ✗           ✓
Secret scanning     ✓           ✗           ✗           ✗

FEATURES
Speed               Fast        Fastest     Medium      Medium
Offline mode        ✓           ✓           ✗           ✗
Custom policies     ✓ (Rego)    ✗           ✗           ✓
CI integration      ✓✓          ✓           ✓           ✓✓
IDE integration     ✓           ✗           ✗           ✓✓
Auto-fix            ✗           ✗           ✗           ✓✓

PRICING
Free                ✓           ✓           ✓           Tiered
Commercial support  Aqua        Anchore     CoreOS      Snyk

BEST FOR:
─────────────────────────────────────────────────────────────────
Trivy:    All-in-one, Kubernetes-native, free
Grype:    Speed-focused, SBOM ecosystem (with Syft)
Clair:    Legacy, Quay registry integration
Snyk:     Developer experience, auto-fix, IDE
```

---

## Common Mistakes

| Mistake | Why It's Bad | Better Approach |
|---------|--------------|-----------------|
| Blocking on all severities | Everything blocked, developers bypass | Block CRITICAL only, alert on HIGH |
| No .trivyignore | Same false positives repeatedly | Document accepted risks |
| Scanning without caching | Slow CI, redundant downloads | Use Trivy cache, GitHub cache action |
| Only scanning in CI | New CVEs affect running containers | Deploy Trivy Operator |
| Ignoring IaC findings | Misconfigs as dangerous as vulns | Include config scanning |
| No SBOM generation | Can't track what's deployed | Generate SBOM with every build |
| Human review of all findings | Doesn't scale | Automated policies, exceptions |
| Different tools per target | Inconsistent results, more work | Trivy handles most targets |

---

## Hands-On Exercise

### Task: Implement Full Trivy Pipeline

**Objective**: Set up Trivy for comprehensive security scanning across code, containers, and config.

**Success Criteria**:
1. Filesystem scan running
2. Container image scan with SBOM
3. IaC scan for Terraform/Kubernetes
4. .trivyignore configured for accepted risks

### Steps

```bash
# 1. Create test project
mkdir trivy-lab && cd trivy-lab

# 2. Create vulnerable Dockerfile
cat > Dockerfile << 'EOF'
FROM node:16
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
CMD ["node", "server.js"]
EOF

# 3. Create package.json with vulnerable deps
cat > package.json << 'EOF'
{
  "name": "trivy-lab",
  "version": "1.0.0",
  "dependencies": {
    "express": "4.17.1",
    "lodash": "4.17.20"
  }
}
EOF

# 4. Create Terraform with misconfig
mkdir terraform
cat > terraform/main.tf << 'EOF'
resource "aws_s3_bucket" "data" {
  bucket = "my-data-bucket"
}

resource "aws_security_group" "web" {
  name = "web-sg"

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
}
EOF

# 5. Create Kubernetes manifest
mkdir k8s
cat > k8s/deployment.yaml << 'EOF'
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web
spec:
  replicas: 1
  selector:
    matchLabels:
      app: web
  template:
    metadata:
      labels:
        app: web
    spec:
      containers:
      - name: web
        image: nginx:latest
        securityContext:
          runAsUser: 0
          privileged: true
EOF

# 6. Install Trivy
brew install trivy  # or your preferred method

# 7. Run filesystem scan
trivy fs --scanners vuln,secret .

# 8. Build and scan image
docker build -t trivy-lab:latest .
trivy image trivy-lab:latest

# 9. Generate SBOM
trivy image --format cyclonedx --output sbom.json trivy-lab:latest

# 10. Scan IaC
trivy config ./terraform/
trivy config ./k8s/

# 11. Create .trivyignore for accepted risks
cat > .trivyignore << 'EOF'
# Accept this CVE until patch available
CVE-2023-12345 exp:2024-06-30

# False positive in our context
AVD-AWS-0088
EOF

# 12. Re-run with ignore file
trivy config ./terraform/  # Should skip AVD-AWS-0088
```

### Verification

```bash
# Verify findings were detected
trivy fs . --severity CRITICAL,HIGH | grep -c "vulnerability"

# Verify SBOM was created
cat sbom.json | jq '.components | length'

# Verify IaC issues found
trivy config ./terraform/ | grep -c "FAIL"
```

---

## Quiz

### Question 1
What types of targets can Trivy scan?

<details>
<summary>Show Answer</summary>

**Container images, filesystems, Git repos, Kubernetes clusters, IaC, and SBOMs**

Trivy is an all-in-one scanner that covers:
- Container images (OS packages + language packages)
- Filesystems and Git repositories
- Infrastructure as Code (Terraform, CloudFormation, K8s, Helm)
- Running Kubernetes clusters
- Existing SBOMs (CycloneDX, SPDX)

This eliminates the need for multiple specialized tools.
</details>

### Question 2
What is the Trivy Operator?

<details>
<summary>Show Answer</summary>

**A Kubernetes operator for continuous security scanning of cluster workloads**

The Trivy Operator:
- Automatically scans new workloads when deployed
- Creates VulnerabilityReports as Kubernetes CRDs
- Scans for misconfigurations (ConfigAuditReports)
- Detects exposed secrets (ExposedSecretReports)
- Enables continuous monitoring, not just CI/CD scanning
</details>

### Question 3
What formats does Trivy support for SBOM generation?

<details>
<summary>Show Answer</summary>

**CycloneDX and SPDX**

```bash
# CycloneDX
trivy image --format cyclonedx myapp:latest

# SPDX
trivy image --format spdx-json myapp:latest
```

SBOMs can also be scanned for vulnerabilities, allowing you to check existing software bills of materials.
</details>

### Question 4
How does .trivyignore work?

<details>
<summary>Show Answer</summary>

**A file listing CVEs or misconfig IDs to skip during scans**

```
# .trivyignore
CVE-2023-12345          # Ignore this CVE
CVE-2023-67890 exp:2024-12-31  # Ignore until date
AVD-AWS-0088            # Ignore this misconfig
```

Entries can have expiration dates to ensure temporary exceptions are reviewed.
</details>

### Question 5
What's the difference between `trivy fs` and `trivy repo`?

<details>
<summary>Show Answer</summary>

**`fs` scans local filesystems; `repo` scans remote Git repositories**

- `trivy fs .` - Scans the current directory
- `trivy fs /path/to/code` - Scans a specific path
- `trivy repo https://github.com/org/repo` - Clones and scans remote repo
- `trivy repo --branch dev https://...` - Scans specific branch

`repo` is useful for scanning third-party code without cloning it first.
</details>

### Question 6
How do you make Trivy fail a CI build on critical vulnerabilities?

<details>
<summary>Show Answer</summary>

**Use `--exit-code 1` with `--severity CRITICAL`**

```bash
trivy image --exit-code 1 --severity CRITICAL myapp:latest
```

The command returns exit code 1 if any CRITICAL vulnerabilities are found, failing the CI step. You can also use:
- `--exit-code 0` - Always succeed (report only)
- `--ignore-unfixed` - Skip vulnerabilities with no fix available
</details>

### Question 7
What is VEX and how does Trivy use it?

<details>
<summary>Show Answer</summary>

**Vulnerability Exploitability eXchange - a standard for documenting vulnerability applicability**

VEX allows you to document that a CVE:
- Doesn't affect your product
- Is not reachable in your code
- Has been mitigated

```bash
trivy image --vex vex.json myapp:latest
```

Trivy respects VEX statements to suppress irrelevant findings with documented justification.
</details>

### Question 8
Why use Trivy over specialized tools like Checkov (IaC) or Grype (containers)?

<details>
<summary>Show Answer</summary>

**Single tool, unified configuration, consistent output across all targets**

Benefits of Trivy's all-in-one approach:
- One tool to install and maintain
- One configuration file format
- One output format (JSON, SARIF, table)
- Consistent severity ratings
- Simpler CI/CD integration

Specialized tools might be deeper in one area, but Trivy is "good enough" for most use cases with less operational overhead.
</details>

---

## Key Takeaways

1. **All-in-one scanner** - Containers, filesystems, IaC, secrets, SBOM
2. **Free and open source** - CNCF project, no licensing costs
3. **Fast and lightweight** - Single binary, minimal dependencies
4. **Built into Harbor** - Default scanner for enterprise registries
5. **Kubernetes-native** - Operator for continuous cluster scanning
6. **SBOM generation included** - CycloneDX and SPDX
7. **VEX support** - Document vulnerability applicability
8. **Multiple output formats** - JSON, SARIF, table, template
9. **Ignore files for exceptions** - Document accepted risks
10. **Exit codes for CI gates** - Fail on specific severities

---

## Next Steps

- **Related**: [Module 13.1: Harbor](../../cicd-delivery/container-registries/module-13.1-harbor/) - Registry with Trivy integration
- **Related**: [Module 4.4: Supply Chain Security](../security-tools/module-4.4-supply-chain/) - SBOM and signing
- **Related**: [Module 12.4: Snyk](../module-12.4-snyk/) - Compare with commercial alternative

---

## Further Reading

- [Trivy Documentation](https://aquasecurity.github.io/trivy/)
- [Trivy GitHub Repository](https://github.com/aquasecurity/trivy)
- [Trivy Operator](https://aquasecurity.github.io/trivy-operator/)
- [Aqua Vulnerability Database](https://avd.aquasec.com/)
- [VEX Specification](https://openvex.dev/)

---

*"The best scanner is the one you actually run. Trivy makes security scanning so easy there's no excuse not to do it everywhere."*
