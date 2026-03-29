---
title: "Module 5.2: Image Scanning with Trivy"
slug: k8s/cks/part5-supply-chain-security/module-5.2-image-scanning
sidebar:
  order: 2
---
> **Complexity**: `[MEDIUM]` - Critical CKS skill
>
> **Time to Complete**: 45-50 minutes
>
> **Prerequisites**: Module 5.1 (Image Security), Docker basics

---

## Why This Module Matters

Container images often contain vulnerable packages that attackers can exploit. Image scanning detects known vulnerabilities (CVEs) before images reach production. Trivy is the de-facto standard for container security scanning.

CKS tests your ability to scan images and interpret vulnerability reports.

---

## What is Trivy?

```
┌─────────────────────────────────────────────────────────────┐
│              TRIVY OVERVIEW                                 │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Trivy = All-in-one security scanner                       │
│  ─────────────────────────────────────────────────────────  │
│  • Open source (Aqua Security)                             │
│  • Fast and accurate                                       │
│  • Easy to use                                             │
│  • Works offline (after initial DB download)              │
│                                                             │
│  What Trivy scans:                                         │
│  ├── Container images                                      │
│  ├── Kubernetes manifests                                  │
│  ├── Terraform/CloudFormation                              │
│  ├── Git repositories                                      │
│  └── File systems                                          │
│                                                             │
│  What Trivy finds:                                         │
│  ├── OS package vulnerabilities (CVEs)                    │
│  ├── Language dependencies (npm, pip, gem)                │
│  ├── IaC misconfigurations                                │
│  ├── Secrets in code                                       │
│  └── License compliance issues                             │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Installing Trivy

```bash
# Debian/Ubuntu
sudo apt-get install wget apt-transport-https gnupg lsb-release
wget -qO - https://aquasecurity.github.io/trivy-repo/deb/public.key | sudo gpg --dearmor -o /usr/share/keyrings/trivy.gpg
echo "deb [signed-by=/usr/share/keyrings/trivy.gpg] https://aquasecurity.github.io/trivy-repo/deb $(lsb_release -sc) main" | sudo tee -a /etc/apt/sources.list.d/trivy.list
sudo apt-get update && sudo apt-get install trivy

# macOS
brew install trivy

# Binary download
curl -sfL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh | sh -s -- -b /usr/local/bin

# Verify installation
trivy --version
```

---

## Basic Image Scanning

### Scan a Container Image

```bash
# Basic scan
trivy image nginx:1.25

# Scan with specific severity filter
trivy image --severity HIGH,CRITICAL nginx:1.25

# Scan and exit with error if vulnerabilities found
trivy image --exit-code 1 --severity CRITICAL nginx:1.25

# Scan local image (not from registry)
trivy image --input myimage.tar
```

### Understanding Output

```
nginx:1.25 (debian 12.2)
=========================
Total: 142 (UNKNOWN: 0, LOW: 85, MEDIUM: 42, HIGH: 12, CRITICAL: 3)

┌──────────────────┬────────────────┬──────────┬─────────────────────┬──────────────────┬─────────────────────────────────────┐
│     Library      │ Vulnerability  │ Severity │  Installed Version  │  Fixed Version   │                Title                │
├──────────────────┼────────────────┼──────────┼─────────────────────┼──────────────────┼─────────────────────────────────────┤
│ libssl3          │ CVE-2024-1234  │ CRITICAL │ 3.0.9-1             │ 3.0.9-2          │ OpenSSL: Remote code execution      │
│ curl             │ CVE-2024-5678  │ HIGH     │ 7.88.1-10           │ 7.88.1-11        │ curl: Buffer overflow in...         │
│ zlib1g           │ CVE-2024-9012  │ MEDIUM   │ 1:1.2.13-1          │                  │ zlib: Memory corruption             │
└──────────────────┴────────────────┴──────────┴─────────────────────┴──────────────────┴─────────────────────────────────────┘
```

---

## Severity Levels

```
┌─────────────────────────────────────────────────────────────┐
│              CVE SEVERITY LEVELS                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  CRITICAL (CVSS 9.0-10.0)                                 │
│  ─────────────────────────────────────────────────────────  │
│  • Remote code execution                                   │
│  • No authentication required                              │
│  • Requires immediate action                               │
│                                                             │
│  HIGH (CVSS 7.0-8.9)                                       │
│  ─────────────────────────────────────────────────────────  │
│  • Significant impact                                      │
│  • May require some user interaction                       │
│  • Should be patched soon                                  │
│                                                             │
│  MEDIUM (CVSS 4.0-6.9)                                     │
│  ─────────────────────────────────────────────────────────  │
│  • Limited impact                                          │
│  • Requires specific conditions                            │
│  • Plan to patch                                           │
│                                                             │
│  LOW (CVSS 0.1-3.9)                                        │
│  ─────────────────────────────────────────────────────────  │
│  • Minor impact                                            │
│  • Difficult to exploit                                    │
│  • Patch when convenient                                   │
│                                                             │
│  UNKNOWN                                                   │
│  ─────────────────────────────────────────────────────────  │
│  • CVSS score not assigned yet                            │
│  • Evaluate manually                                       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Advanced Scanning Options

### Output Formats

```bash
# Table format (default)
trivy image nginx:1.25

# JSON format (for CI/CD parsing)
trivy image --format json nginx:1.25 > results.json

# SARIF format (for GitHub Security)
trivy image --format sarif nginx:1.25 > results.sarif

# Template format
trivy image --format template --template "@contrib/html.tpl" nginx:1.25 > report.html
```

### Filtering Results

```bash
# Only show vulnerabilities with fixes available
trivy image --ignore-unfixed nginx:1.25

# Ignore specific CVEs
trivy image --ignore-cve CVE-2024-1234,CVE-2024-5678 nginx:1.25

# Use .trivyignore file
echo "CVE-2024-1234" >> .trivyignore
trivy image nginx:1.25

# Only scan OS packages (skip language dependencies)
trivy image --vuln-type os nginx:1.25

# Only scan language dependencies
trivy image --vuln-type library node:20
```

### Scanning Options

```bash
# Skip database update (use cached)
trivy image --skip-db-update nginx:1.25

# Download database only (for air-gapped setup)
trivy image --download-db-only

# Scan from specific registry
trivy image --username user --password pass registry.example.com/myimage:1.0

# Scan with timeout
trivy image --timeout 10m large-image:1.0
```

---

## Scanning Kubernetes Clusters

### Scan Running Workloads

```bash
# Scan all images in cluster
trivy k8s --report summary cluster

# Scan specific namespace
trivy k8s --namespace production --report summary

# Scan and show all vulnerabilities
trivy k8s --report all --namespace default

# Output as JSON
trivy k8s --format json --output results.json cluster
```

### Scan Kubernetes Manifests

```bash
# Scan YAML files for misconfigurations
trivy config deployment.yaml

# Scan entire directory
trivy config ./manifests/

# Scan for both vulnerabilities and misconfigs
trivy fs --security-checks vuln,config ./
```

---

## Scanning for Misconfigurations

```bash
# Scan Kubernetes manifests
trivy config pod.yaml

# Example misconfiguration output:
# pod.yaml
# ========
# Tests: 23 (SUCCESSES: 18, FAILURES: 5)
# Failures: 5 (UNKNOWN: 0, LOW: 1, MEDIUM: 2, HIGH: 2, CRITICAL: 0)
#
# HIGH: Container 'nginx' of Pod 'web' should set 'securityContext.runAsNonRoot' to true
# HIGH: Container 'nginx' of Pod 'web' should set 'securityContext.allowPrivilegeEscalation' to false
```

### What Trivy Checks in Kubernetes

```
┌─────────────────────────────────────────────────────────────┐
│              KUBERNETES MISCONFIGURATION CHECKS             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Container Security:                                       │
│  ├── Running as root                                       │
│  ├── Privilege escalation allowed                         │
│  ├── Privileged containers                                │
│  ├── Missing securityContext                              │
│  └── Capabilities not dropped                              │
│                                                             │
│  Resource Management:                                      │
│  ├── Missing resource limits                              │
│  ├── Missing resource requests                            │
│  └── Unbounded resource usage                             │
│                                                             │
│  Network Security:                                         │
│  ├── hostNetwork enabled                                  │
│  ├── hostPID enabled                                      │
│  └── hostIPC enabled                                      │
│                                                             │
│  RBAC Security:                                            │
│  ├── Overly permissive roles                              │
│  ├── Wildcard permissions                                 │
│  └── Cluster-admin bindings                               │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## CI/CD Integration

### GitHub Actions

```yaml
name: Security Scan
on: push

jobs:
  scan:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3

    - name: Build image
      run: docker build -t myapp:${{ github.sha }} .

    - name: Run Trivy vulnerability scanner
      uses: aquasecurity/trivy-action@master
      with:
        image-ref: 'myapp:${{ github.sha }}'
        format: 'table'
        exit-code: '1'
        severity: 'CRITICAL,HIGH'
```

### Jenkins Pipeline

```groovy
pipeline {
    agent any
    stages {
        stage('Build') {
            steps {
                sh 'docker build -t myapp:${BUILD_NUMBER} .'
            }
        }
        stage('Scan') {
            steps {
                sh '''
                    trivy image \
                        --exit-code 1 \
                        --severity CRITICAL,HIGH \
                        myapp:${BUILD_NUMBER}
                '''
            }
        }
    }
}
```

---

## Real Exam Scenarios

### Scenario 1: Scan Image and Report Critical CVEs

```bash
# Scan image for critical vulnerabilities
trivy image --severity CRITICAL nginx:1.25

# Save report
trivy image --severity CRITICAL,HIGH --format json nginx:1.25 > report.json

# Count critical vulnerabilities
trivy image --severity CRITICAL --format json nginx:1.25 | \
  jq '.Results[].Vulnerabilities | length'
```

### Scenario 2: Find Images Without Critical Vulnerabilities

```bash
# Scan multiple images, find one without criticals
for img in nginx:1.25 nginx:1.24 nginx:1.23-alpine; do
  echo "Scanning $img..."
  CRITICALS=$(trivy image --severity CRITICAL --format json --quiet "$img" | \
    jq '[.Results[]?.Vulnerabilities // [] | length] | add')
  echo "$img: $CRITICALS critical vulnerabilities"
done
```

### Scenario 3: Scan Kubernetes Deployment

```bash
# Create test deployment
cat <<EOF > deployment.yaml
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
      - name: nginx
        image: nginx:1.25
EOF

# Scan for misconfigurations
trivy config deployment.yaml

# Scan image used in deployment
IMG=$(grep "image:" deployment.yaml | awk '{print $2}')
trivy image "$IMG"
```

### Scenario 4: Generate Report with Only Fixable Vulnerabilities

```bash
# Show only vulnerabilities with available fixes
trivy image --ignore-unfixed --severity HIGH,CRITICAL nginx:1.25

# This helps prioritize what can actually be patched
```

---

## Trivy Database

```bash
# Trivy vulnerability database location
ls ~/.cache/trivy/

# Update database
trivy image --download-db-only

# Check database freshness
trivy image --skip-db-update nginx:1.25  # Uses cached DB

# For air-gapped environments
# 1. Download on internet-connected machine
trivy image --download-db-only
# 2. Copy ~/.cache/trivy/db to air-gapped machine
# 3. Run with --skip-db-update
```

---

## Did You Know?

- **Trivy can scan container images without Docker** using containerd or by analyzing image tarballs directly.

- **The vulnerability database updates daily**. For production CI/CD, consider caching the database to avoid rate limits.

- **Trivy uses multiple vulnerability databases**: NVD, Red Hat OVAL, Debian Security Tracker, Alpine SecDB, and more.

- **Trivy can detect secrets** like API keys, passwords, and certificates accidentally included in images or code.

---

## Common Mistakes

| Mistake | Why It Hurts | Solution |
|---------|--------------|----------|
| Ignoring HIGH severity | Can be exploited | Set threshold to HIGH,CRITICAL |
| Old vulnerability database | Miss recent CVEs | Update DB in CI/CD |
| Only scanning at build | Drift over time | Regular scheduled scans |
| Not fixing fixable CVEs | Easy wins missed | Use --ignore-unfixed first |
| Scanning with :latest | Results change | Use specific tags |

---

## Quiz

1. **What command scans an image for only CRITICAL and HIGH vulnerabilities?**
   <details>
   <summary>Answer</summary>
   `trivy image --severity CRITICAL,HIGH <image>`. The --severity flag filters results to only show specified severity levels.
   </details>

2. **How do you make a CI/CD pipeline fail if critical vulnerabilities are found?**
   <details>
   <summary>Answer</summary>
   Use `trivy image --exit-code 1 --severity CRITICAL <image>`. The --exit-code 1 flag causes trivy to return exit code 1 if vulnerabilities matching the criteria are found.
   </details>

3. **How do you scan only for vulnerabilities that have fixes available?**
   <details>
   <summary>Answer</summary>
   Use `trivy image --ignore-unfixed <image>`. This filters out vulnerabilities where no patched version is available.
   </details>

4. **What does trivy config do?**
   <details>
   <summary>Answer</summary>
   `trivy config` scans configuration files (Kubernetes manifests, Terraform, Dockerfile, etc.) for security misconfigurations, not CVEs.
   </details>

---

## Hands-On Exercise

**Task**: Scan images and identify security issues.

```bash
# Step 1: Update Trivy database
trivy image --download-db-only

# Step 2: Scan nginx:latest for all vulnerabilities
echo "=== Full Scan of nginx:latest ==="
trivy image nginx:latest 2>/dev/null | head -30

# Step 3: Count vulnerabilities by severity
echo "=== Vulnerability Count ==="
trivy image --format json nginx:latest 2>/dev/null | \
  jq -r '.Results[].Vulnerabilities[]?.Severity' | sort | uniq -c

# Step 4: Find only CRITICAL with fixes
echo "=== Critical Vulnerabilities with Fixes ==="
trivy image --severity CRITICAL --ignore-unfixed nginx:latest

# Step 5: Compare with Alpine version
echo "=== Alpine Version Comparison ==="
trivy image --severity CRITICAL,HIGH nginx:alpine 2>/dev/null | head -20

# Step 6: Scan a Kubernetes manifest
cat <<EOF > test-pod.yaml
apiVersion: v1
kind: Pod
metadata:
  name: insecure
spec:
  containers:
  - name: app
    image: nginx
    securityContext:
      privileged: true
EOF

echo "=== Kubernetes Manifest Scan ==="
trivy config test-pod.yaml

# Step 7: Generate JSON report
trivy image --format json --output scan-report.json nginx:latest
echo "Report saved to scan-report.json"

# Cleanup
rm -f test-pod.yaml scan-report.json
```

**Success criteria**: Understand how to scan images and interpret results.

---

## Summary

**Trivy Basics**:
- `trivy image <name>` - Scan container image
- `trivy config <file>` - Scan configurations
- `trivy k8s cluster` - Scan Kubernetes

**Key Flags**:
- `--severity CRITICAL,HIGH` - Filter by severity
- `--exit-code 1` - Fail CI/CD if found
- `--ignore-unfixed` - Only fixable CVEs
- `--format json` - Machine-readable output

**Severity Priority**:
1. CRITICAL - Immediate action
2. HIGH - Patch soon
3. MEDIUM - Plan to fix
4. LOW - When convenient

**Exam Tips**:
- Know basic trivy commands
- Understand severity filtering
- Be able to parse scan output
- Know how to scan Kubernetes manifests

---

## Next Module

[Module 5.3: Static Analysis](../module-5.3-static-analysis/) - Analyzing Kubernetes manifests for security issues.
