---
title: "Module 4.4: Supply Chain Security"
slug: platform/toolkits/security-quality/security-tools/module-4.4-supply-chain
sidebar:
  order: 5
---
> **Toolkit Track** | Complexity: `[COMPLEX]` | Time: 45-50 minutes

## Overview

You trust your code. But do you trust your dependencies? Your base images? Your build system? Supply chain attacks target the weakest link—and in software, that's often the build pipeline. This module covers the tools and practices for securing your software supply chain: image signing with Sigstore, SBOMs, vulnerability scanning, and artifact registries.

**What You'll Learn**:
- Container image signing with Cosign/Sigstore
- Generating and consuming SBOMs
- Vulnerability scanning integration
- Secure artifact registries with Harbor

**Prerequisites**:
- [DevSecOps Discipline](../../disciplines/reliability-security/devsecops/)
- Container image basics
- CI/CD pipeline concepts

---

## Why This Module Matters

The SolarWinds attack compromised 18,000 organizations through a single build system. Log4Shell affected millions of applications through one dependency. Supply chain attacks are now the #1 threat vector because defenders focus on their code while attackers target everything else.

> 💡 **Did You Know?** The 2020 SolarWinds attack inserted malicious code into signed updates that were distributed to customers including the US Treasury, Homeland Security, and Fortune 500 companies. The attackers compromised the build system itself—the signed updates were "legitimately" malicious. This attack directly inspired the creation of SLSA (Supply-chain Levels for Software Artifacts) framework.

---

## The Supply Chain Attack Surface

```
SOFTWARE SUPPLY CHAIN ATTACK SURFACE
════════════════════════════════════════════════════════════════════

    Developer      Dependencies      Build         Registry       Runtime
    ─────────      ────────────      ─────         ────────       ───────
        │               │              │               │              │
        ▼               ▼              ▼               ▼              ▼
    ┌───────┐      ┌───────┐      ┌───────┐      ┌───────┐      ┌───────┐
    │Laptop │      │NPM/PyPI│     │CI/CD  │      │Docker │      │ K8s   │
    │compro-│      │package │     │pipeline│     │Hub    │      │cluster│
    │mised  │      │typo-   │     │inject │      │poison │      │config │
    │       │      │squatted│     │code   │      │image  │      │drift  │
    └───────┘      └───────┘      └───────┘      └───────┘      └───────┘

DEFENSES AT EACH STAGE:
────────────────────────────────────────────────────────────────────

Developer:     - Code review, signed commits, MFA
Dependencies:  - Lock files, vulnerability scanning, private mirrors
Build:         - Hermetic builds, build provenance (SLSA)
Registry:      - Image signing, vulnerability scanning, admission control
Runtime:       - Signature verification, SBOM validation, runtime security
```

---

## Sigstore & Cosign

### What is Sigstore?

Sigstore is a collection of tools for signing, verifying, and protecting software artifacts. It's like Let's Encrypt for software signing—free, automated, and widely adopted.

```
SIGSTORE ECOSYSTEM
════════════════════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────────────────┐
│                       SIGSTORE                                   │
│                                                                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │   Cosign    │  │   Fulcio    │  │   Rekor     │             │
│  │  (signing)  │  │ (cert auth) │  │ (trans log) │             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
│                                                                  │
│  • Cosign: Sign and verify containers                           │
│  • Fulcio: Issues short-lived certificates (OIDC)               │
│  • Rekor: Immutable transparency log of signatures              │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Installing Cosign

```bash
# macOS
brew install cosign

# Linux
curl -O -L "https://github.com/sigstore/cosign/releases/latest/download/cosign-linux-amd64"
chmod +x cosign-linux-amd64
sudo mv cosign-linux-amd64 /usr/local/bin/cosign

# Verify installation
cosign version
```

### Keyless Signing (Recommended)

```bash
# Sign an image (keyless - uses OIDC identity)
cosign sign gcr.io/my-project/my-app:v1.0.0

# This opens browser for OIDC auth (GitHub, Google, etc.)
# No key management needed!

# Verify signature
cosign verify gcr.io/my-project/my-app:v1.0.0 \
  --certificate-identity=user@example.com \
  --certificate-oidc-issuer=https://github.com/login/oauth
```

### Key-Based Signing

```bash
# Generate key pair
cosign generate-key-pair

# Sign with private key
cosign sign --key cosign.key gcr.io/my-project/my-app:v1.0.0

# Verify with public key
cosign verify --key cosign.pub gcr.io/my-project/my-app:v1.0.0
```

### CI/CD Integration

```yaml
# GitHub Actions example
name: Sign Container Image
on:
  push:
    tags: ['v*']

jobs:
  sign:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      id-token: write  # Required for keyless signing

    steps:
    - uses: actions/checkout@v4

    - uses: sigstore/cosign-installer@v3

    - name: Log in to registry
      uses: docker/login-action@v3
      with:
        registry: ghcr.io
        username: ${{ github.actor }}
        password: ${{ secrets.GITHUB_TOKEN }}

    - name: Build and push
      run: |
        docker build -t ghcr.io/${{ github.repository }}:${{ github.ref_name }} .
        docker push ghcr.io/${{ github.repository }}:${{ github.ref_name }}

    - name: Sign image
      run: |
        cosign sign --yes ghcr.io/${{ github.repository }}:${{ github.ref_name }}
```

> 💡 **Did You Know?** Keyless signing with Sigstore uses short-lived certificates (10 minutes) tied to your OIDC identity. The certificate is recorded in Rekor's transparency log, providing a permanent, auditable record that you signed the artifact at a specific time. This eliminates the key management nightmare that made traditional signing impractical.

---

## Software Bill of Materials (SBOM)

### Why SBOMs?

An SBOM is a complete inventory of components in your software. When a vulnerability like Log4Shell hits, you can instantly answer: "Are we affected?"

```
SBOM FORMATS
════════════════════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────────────────┐
│                                                                  │
│  SPDX (Software Package Data Exchange)                          │
│  • Linux Foundation standard                                    │
│  • Focus on licensing                                           │
│  • Format: JSON, RDF, tag-value                                 │
│                                                                  │
│  CycloneDX                                                       │
│  • OWASP standard                                               │
│  • Focus on security                                            │
│  • Format: JSON, XML                                            │
│                                                                  │
│  Both work. CycloneDX more common in security tooling.          │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Generating SBOMs

```bash
# Using Syft (recommended)
brew install syft

# Generate SBOM for container image
syft gcr.io/my-project/my-app:v1.0.0 -o cyclonedx-json > sbom.json

# Generate SBOM for directory
syft . -o spdx-json > sbom.spdx.json

# Scan and save with Trivy
trivy image --format cyclonedx gcr.io/my-project/my-app:v1.0.0 > sbom.json
```

### Attaching SBOM to Image

```bash
# Generate SBOM
syft gcr.io/my-project/my-app:v1.0.0 -o cyclonedx-json > sbom.json

# Attach as attestation
cosign attest --predicate sbom.json \
  --type cyclonedx \
  gcr.io/my-project/my-app:v1.0.0

# Verify and retrieve
cosign verify-attestation \
  --type cyclonedx \
  --certificate-identity=user@example.com \
  --certificate-oidc-issuer=https://github.com/login/oauth \
  gcr.io/my-project/my-app:v1.0.0
```

### SBOM-Based Vulnerability Scanning

```bash
# Scan SBOM file with Trivy
trivy sbom sbom.json

# Scan SBOM file with Grype
grype sbom:sbom.json

# Output: List of CVEs affecting components in SBOM
```

---

## Vulnerability Scanning

### Tools Comparison

| Tool | Type | Best For |
|------|------|----------|
| **Trivy** | All-in-one | General purpose, easy to use |
| **Grype** | Image scanner | Fast, Anchore ecosystem |
| **Snyk** | SaaS | Developer experience, fix suggestions |
| **Clair** | Registry scanner | Harbor integration |

### Trivy Deep Dive

```bash
# Scan container image
trivy image nginx:latest

# Scan with specific severity threshold
trivy image --severity HIGH,CRITICAL nginx:latest

# Scan Kubernetes manifest files
trivy config ./kubernetes/

# Scan filesystem
trivy fs .

# Scan in CI (exit 1 on critical vulns)
trivy image --exit-code 1 --severity CRITICAL myapp:latest

# Generate SARIF output (GitHub integration)
trivy image --format sarif -o results.sarif myapp:latest
```

### CI/CD Integration

```yaml
# GitHub Actions with Trivy
name: Security Scan
on: [push, pull_request]

jobs:
  scan:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4

    - name: Build image
      run: docker build -t myapp:${{ github.sha }} .

    - name: Scan image
      uses: aquasecurity/trivy-action@master
      with:
        image-ref: myapp:${{ github.sha }}
        format: 'sarif'
        output: 'trivy-results.sarif'
        severity: 'CRITICAL,HIGH'

    - name: Upload results
      uses: github/codeql-action/upload-sarif@v3
      with:
        sarif_file: 'trivy-results.sarif'
```

> 💡 **Did You Know?** Trivy can scan Infrastructure as Code (Terraform, CloudFormation, Kubernetes manifests) for misconfigurations, not just container images for vulnerabilities. One tool, multiple security checks. It can also detect exposed secrets in code and configuration files.

---

## Harbor Registry

### Why Harbor?

Harbor is a CNCF graduated project that adds enterprise features to container registries:
- Vulnerability scanning
- Image signing
- Replication
- RBAC
- Audit logging

```
HARBOR ARCHITECTURE
════════════════════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────────────────┐
│                          HARBOR                                  │
│                                                                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │   Core      │  │  Registry   │  │   Portal    │             │
│  │  (API/auth) │  │(OCI storage)│  │ (Web UI)    │             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
│                                                                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │   Trivy     │  │  Notary     │  │  Job Service│             │
│  │ (scanning)  │  │ (signing)   │  │(replication)│             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Installation

```bash
# Add Harbor Helm repo
helm repo add harbor https://helm.getharbor.io
helm repo update

# Install Harbor
helm install harbor harbor/harbor \
  --namespace harbor \
  --create-namespace \
  --set expose.type=ingress \
  --set expose.ingress.hosts.core=harbor.example.com \
  --set externalURL=https://harbor.example.com \
  --set persistence.persistentVolumeClaim.registry.size=50Gi \
  --set trivy.enabled=true \
  --set notary.enabled=true
```

### Key Features

```bash
# Push image to Harbor
docker tag myapp:latest harbor.example.com/myproject/myapp:latest
docker push harbor.example.com/myproject/myapp:latest

# Harbor automatically scans on push
# View results in UI or via API

# Configure vulnerability blocking policy
# Project settings → Policy → Prevent vulnerable images from running
# Set: "Prevent images with severity >= High from being pulled"
```

### Replication for Multi-Region

```yaml
# Harbor replication rule
Name: prod-replication
Source Registry: harbor.us-east.example.com
Destination: harbor.eu-west.example.com
Source Filter:
  - Name: library/**
  - Tag: v*
Trigger: On push
Override: true  # Replace existing tags
```

---

## Admission Control for Signed Images

### Kyverno Policy

```yaml
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata:
  name: require-signed-images
spec:
  validationFailureAction: Enforce
  rules:
  - name: verify-signature
    match:
      any:
      - resources:
          kinds:
          - Pod
    verifyImages:
    - imageReferences:
      - "ghcr.io/myorg/*"
      attestors:
      - entries:
        - keyless:
            subject: "https://github.com/myorg/*"
            issuer: "https://token.actions.githubusercontent.com"
            rekor:
              url: https://rekor.sigstore.dev
```

### Gatekeeper/Ratify

```yaml
# Ratify verifies signatures before admission
apiVersion: config.ratify.deislabs.io/v1beta1
kind: Verifier
metadata:
  name: cosign-verifier
spec:
  name: cosign
  artifactTypes: application/vnd.dev.cosign.simplesigning.v1+json
  parameters:
    key: |
      -----BEGIN PUBLIC KEY-----
      MFkwEwYHKoZIzj0CAQYIKoZIzj0DAQcDQgAE...
      -----END PUBLIC KEY-----
---
# Constraint that uses Ratify
apiVersion: constraints.gatekeeper.sh/v1beta1
kind: RatifyVerification
metadata:
  name: require-signature
spec:
  match:
    kinds:
    - apiGroups: [""]
      kinds: ["Pod"]
```

---

## Complete Supply Chain Pipeline

```yaml
# Complete secure pipeline
name: Secure Build and Deploy
on:
  push:
    branches: [main]

jobs:
  build:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write
      id-token: write

    outputs:
      digest: ${{ steps.build.outputs.digest }}

    steps:
    - uses: actions/checkout@v4

    # Build
    - name: Build image
      id: build
      run: |
        docker build -t ghcr.io/${{ github.repository }}:${{ github.sha }} .
        DIGEST=$(docker inspect --format='{{index .RepoDigests 0}}' ghcr.io/${{ github.repository }}:${{ github.sha }} | cut -d@ -f2)
        echo "digest=$DIGEST" >> $GITHUB_OUTPUT
        docker push ghcr.io/${{ github.repository }}:${{ github.sha }}

    # Generate SBOM
    - name: Generate SBOM
      uses: anchore/sbom-action@v0
      with:
        image: ghcr.io/${{ github.repository }}:${{ github.sha }}
        format: cyclonedx-json
        output-file: sbom.json

    # Scan for vulnerabilities
    - name: Vulnerability scan
      uses: aquasecurity/trivy-action@master
      with:
        image-ref: ghcr.io/${{ github.repository }}:${{ github.sha }}
        exit-code: '1'
        severity: 'CRITICAL'

    # Sign image
    - name: Sign image
      uses: sigstore/cosign-installer@v3
    - run: cosign sign --yes ghcr.io/${{ github.repository }}@${{ steps.build.outputs.digest }}

    # Attach SBOM
    - run: |
        cosign attest --yes --predicate sbom.json \
          --type cyclonedx \
          ghcr.io/${{ github.repository }}@${{ steps.build.outputs.digest }}
```

> 💡 **Did You Know?** SLSA (Supply-chain Levels for Software Artifacts, pronounced "salsa") defines 4 levels of supply chain security maturity. Level 1 requires build provenance, Level 2 requires a hosted build platform, Level 3 requires hardened builds, and Level 4 requires two-person review. GitHub Actions can automatically generate SLSA Level 3 provenance attestations.

---

## Common Mistakes

| Mistake | Problem | Solution |
|---------|---------|----------|
| Signing mutable tags | `latest` changes, signature invalid | Sign by digest, not tag |
| Ignoring transitive deps | Vulnerabilities hide in dependencies | Generate full SBOM, scan recursively |
| Blocking all vulnerabilities | Nothing deploys | Set severity thresholds, accept risk for low |
| No key rotation plan | Compromised key = all images suspect | Use keyless signing or rotate regularly |
| Not verifying in prod | Images verified in CI, not at deploy | Add admission controller verification |
| Storing SBOM separately | SBOM gets out of sync with image | Attach SBOM as attestation to image |

---

## War Story: The Phantom Dependency

*A security scan showed zero vulnerabilities in a Node.js app. A week later, they were compromised via a transitive dependency.*

**What went wrong**: The scanner only checked direct dependencies in `package.json`. The attacker exploited `event-stream`, a dependency of a dependency of a dependency—5 levels deep.

**The fix**:
1. Generate SBOM including ALL transitive dependencies
2. Use `npm audit` / `yarn audit` for full tree
3. Pin ALL dependencies (not just direct ones) with lock files
4. Scan the lock file, not just `package.json`

```bash
# Full dependency tree scan
trivy fs --scanners vuln .

# This scans package-lock.json, finding ALL dependencies
```

---

## Quiz

### Question 1
What's the advantage of keyless signing over traditional key-based signing?

<details>
<summary>Show Answer</summary>

**Keyless signing advantages**:
1. **No key management** - No keys to generate, store, rotate, or protect
2. **Identity-based** - Signature tied to OIDC identity (GitHub, Google)
3. **Auditable** - All signatures recorded in transparency log (Rekor)
4. **Short-lived** - Certificates expire in 10 minutes, reducing exposure
5. **Easier adoption** - No security team approval for key storage

**When to use keys**: Air-gapped environments, regulatory requirements for specific key storage.

</details>

### Question 2
Why should you sign images by digest instead of tag?

<details>
<summary>Show Answer</summary>

Tags are mutable pointers. `myapp:latest` points to different images over time.

If you sign `myapp:latest`:
1. Sign image A as `latest` ✓
2. Push image B as `latest`
3. Signature says "latest is verified" but it's now B, not A!

**Digest is immutable**: `myapp@sha256:abc123...` always refers to the same bytes.

```bash
# Good: Sign by digest
cosign sign myapp@sha256:abc123...

# Risky: Sign by tag
cosign sign myapp:latest
```

</details>

### Question 3
An SBOM shows a dependency has a critical CVE but no fix is available. What do you do?

<details>
<summary>Show Answer</summary>

Options (in order of preference):
1. **Replace the dependency** - Find alternative library
2. **Mitigate** - Add WAF rules, network isolation, input validation
3. **Accept risk** - Document decision, set review date, monitor for fix
4. **Patch yourself** - Fork and fix (last resort, maintenance burden)

**Never**: Ignore it and hope for the best

Document in risk register:
```
CVE-2024-XXXX in libfoo 1.2.3
- No fix available
- Mitigated by: NetworkPolicy blocking external access
- Review date: 2024-03-01
- Owner: security-team
```

</details>

---

## Hands-On Exercise

### Objective
Build a secure supply chain with signing, SBOM, and vulnerability scanning.

### Environment Setup

```bash
# Install tools
brew install cosign syft trivy

# Create test Dockerfile
cat > Dockerfile << 'EOF'
FROM python:3.11-slim
RUN pip install flask requests
COPY app.py /app.py
CMD ["python", "/app.py"]
EOF

cat > app.py << 'EOF'
from flask import Flask
app = Flask(__name__)

@app.route('/')
def hello():
    return 'Hello, Secure World!'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
EOF
```

### Tasks

1. **Build and tag image**:
   ```bash
   docker build -t myapp:v1 .
   ```

2. **Generate SBOM**:
   ```bash
   syft myapp:v1 -o cyclonedx-json > sbom.json
   cat sbom.json | head -50
   ```

3. **Scan for vulnerabilities**:
   ```bash
   trivy image myapp:v1
   # Note any HIGH/CRITICAL findings
   ```

4. **Scan SBOM for vulnerabilities**:
   ```bash
   trivy sbom sbom.json
   ```

5. **Sign image** (uses local key for exercise):
   ```bash
   cosign generate-key-pair
   cosign sign --key cosign.key myapp:v1
   ```

6. **Verify signature**:
   ```bash
   cosign verify --key cosign.pub myapp:v1
   ```

### Success Criteria
- [ ] SBOM generated in CycloneDX format
- [ ] SBOM contains Flask and requests dependencies
- [ ] Trivy scan completes (note vulnerability count)
- [ ] Image signed with Cosign
- [ ] Signature verified successfully

### Bonus Challenge
Push the image to a registry and attach the SBOM as an attestation:
```bash
# Tag for registry
docker tag myapp:v1 ghcr.io/youruser/myapp:v1
docker push ghcr.io/youruser/myapp:v1

# Sign (keyless if you have OIDC)
cosign sign ghcr.io/youruser/myapp:v1

# Attach SBOM
cosign attest --predicate sbom.json --type cyclonedx ghcr.io/youruser/myapp:v1
```

---

## Further Reading

- [Sigstore Documentation](https://docs.sigstore.dev/)
- [SLSA Framework](https://slsa.dev/)
- [CycloneDX Specification](https://cyclonedx.org/)
- [Harbor Documentation](https://goharbor.io/docs/)
- [Trivy Documentation](https://aquasecurity.github.io/trivy/)

---

## Next Module

Continue to [Networking Toolkit](../networking/) to learn about Cilium and Service Mesh for Kubernetes networking and security.

---

*"In supply chain security, trust is a vulnerability. Verify everything."*
