---
name: devsecops-expert
description: DevSecOps discipline knowledge. Use for security integration, shift-left, supply chain security, SBOM, vulnerability scanning, policy as code. Triggers on "DevSecOps", "shift-left", "supply chain security", "SBOM", "vulnerability scanning".
---

# DevSecOps Expert Skill

Authoritative knowledge source for DevSecOps principles, security integration into CI/CD, supply chain security, and cloud native security practices. Combines development velocity with security requirements.

## When to Use
- Writing or reviewing DevSecOps curriculum content
- Designing secure CI/CD pipelines
- Implementing supply chain security
- Policy as code implementation
- Container and Kubernetes security scanning

## Core DevSecOps Principles

### What is DevSecOps?

DevSecOps integrates security practices into the DevOps workflow. Instead of security being a gate at the end, it's embedded throughout the software development lifecycle.

### The Shift-Left Philosophy

```
TRADITIONAL SECURITY
────────────────────────────────────────────────────────────▶
Code ──▶ Build ──▶ Test ──▶ Deploy ──▶ [SECURITY GATE] ──▶ Prod
                                              │
                                      Expensive fixes
                                      Late discoveries

SHIFT-LEFT SECURITY
────────────────────────────────────────────────────────────▶
[SEC]    [SEC]    [SEC]    [SEC]         [SEC]
  │        │        │        │             │
Code ──▶ Build ──▶ Test ──▶ Deploy ──▶ Runtime ──▶ Prod
  │        │        │        │             │
IDE      SAST    DAST     Image        Runtime
checks   scans   scans    scanning     detection
```

### DevSecOps Principles

| Principle | Description |
|-----------|-------------|
| **Shift Left** | Find issues early when cheaper to fix |
| **Automate Everything** | Security checks in CI/CD, not manual gates |
| **Security as Code** | Policies, configs, tests are versioned |
| **Shared Responsibility** | Everyone owns security, not just sec team |
| **Continuous Compliance** | Compliance verified automatically |
| **Feedback Loops** | Fast feedback to developers on security issues |

## The Security Pipeline

### Pipeline Stages

```
┌─────────────────────────────────────────────────────────────────┐
│                     DEVSECOPS PIPELINE                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  PRE-COMMIT          BUILD              TEST                    │
│  ┌──────────┐       ┌──────────┐       ┌──────────┐            │
│  │ Secrets  │       │  SAST    │       │  DAST    │            │
│  │ scanning │       │ scanning │       │ scanning │            │
│  ├──────────┤       ├──────────┤       ├──────────┤            │
│  │ Linting  │       │   SCA    │       │   IAST   │            │
│  │ (security│       │ (deps)   │       │          │            │
│  │  rules)  │       ├──────────┤       └──────────┘            │
│  └──────────┘       │  Image   │                               │
│                     │ scanning │                               │
│                     └──────────┘                               │
│                                                                 │
│  DEPLOY              RUNTIME            CONTINUOUS              │
│  ┌──────────┐       ┌──────────┐       ┌──────────┐            │
│  │ Config   │       │ Runtime  │       │Compliance│            │
│  │ scanning │       │ security │       │ scanning │            │
│  ├──────────┤       ├──────────┤       ├──────────┤            │
│  │ Policy   │       │  Threat  │       │ Audit    │            │
│  │ checks   │       │ detection│       │ logging  │            │
│  └──────────┘       └──────────┘       └──────────┘            │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Security Testing Types

| Type | What It Does | When | Tools |
|------|--------------|------|-------|
| **SAST** | Static code analysis | Build | Semgrep, SonarQube, CodeQL |
| **SCA** | Dependency vulnerabilities | Build | Snyk, Dependabot, Trivy |
| **DAST** | Dynamic app testing | Test | OWASP ZAP, Burp Suite |
| **IAST** | Runtime instrumentation | Test | Contrast, Hdiv |
| **Container Scan** | Image vulnerabilities | Build | Trivy, Grype, Clair |
| **IaC Scan** | Infrastructure misconfig | Build | Checkov, tfsec, Kubesec |

## Supply Chain Security

### The Software Supply Chain

```
┌─────────────────────────────────────────────────────────────┐
│                    SOFTWARE SUPPLY CHAIN                     │
│                                                              │
│  SOURCE CODE        DEPENDENCIES        BUILD                │
│  ┌──────────┐      ┌──────────┐       ┌──────────┐          │
│  │   Your   │      │  Direct  │       │  Build   │          │
│  │   code   │◀─────│   deps   │◀──────│ process  │          │
│  └──────────┘      └────┬─────┘       └────┬─────┘          │
│                         │                   │                │
│                    ┌────▼─────┐       ┌────▼─────┐          │
│                    │Transitive│       │  Build   │          │
│                    │   deps   │       │  tools   │          │
│                    └──────────┘       └──────────┘          │
│                                                              │
│  ARTIFACTS          DEPLOYMENT         RUNTIME               │
│  ┌──────────┐      ┌──────────┐       ┌──────────┐          │
│  │  Images  │─────▶│ Registry │──────▶│  K8s     │          │
│  │  SBOMs   │      │          │       │ cluster  │          │
│  └──────────┘      └──────────┘       └──────────┘          │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### SLSA Framework (Supply chain Levels for Software Artifacts)

| Level | Requirements |
|-------|--------------|
| SLSA 1 | Build process documented |
| SLSA 2 | Tamper-resistant build service |
| SLSA 3 | Hardened build platform |
| SLSA 4 | Two-person review, hermetic builds |

### SBOM (Software Bill of Materials)

An SBOM lists all components in your software:

```json
{
  "bomFormat": "CycloneDX",
  "specVersion": "1.4",
  "components": [
    {
      "type": "library",
      "name": "lodash",
      "version": "4.17.21",
      "purl": "pkg:npm/lodash@4.17.21"
    }
  ]
}
```

**SBOM Formats:**
- **SPDX** - Linux Foundation standard
- **CycloneDX** - OWASP standard
- **SWID** - ISO standard

**SBOM Tools:**
- Syft (generate)
- Grype (scan SBOM for vulns)
- Trivy (generate + scan)

### Image Signing & Verification

```
BUILD PIPELINE
┌──────────────────────────────────────────────────────┐
│                                                      │
│  Build ──▶ Scan ──▶ Sign ──▶ Push to Registry       │
│                       │                              │
│                 ┌─────▼─────┐                        │
│                 │  Cosign   │                        │
│                 │ (Sigstore)│                        │
│                 └───────────┘                        │
└──────────────────────────────────────────────────────┘

DEPLOYMENT
┌──────────────────────────────────────────────────────┐
│                                                      │
│  Admission ──▶ Verify Signature ──▶ Allow/Deny      │
│  Controller          │                               │
│              ┌───────▼───────┐                       │
│              │ Kyverno/OPA   │                       │
│              │ (policy check)│                       │
│              └───────────────┘                       │
└──────────────────────────────────────────────────────┘
```

**Sigstore Ecosystem:**
- **Cosign** - Sign and verify containers
- **Fulcio** - Certificate authority
- **Rekor** - Transparency log

## Policy as Code

### What is Policy as Code?

Codifying security, compliance, and operational policies as version-controlled code that can be automatically enforced.

### Policy Enforcement Points

| Layer | What to Enforce | Tools |
|-------|-----------------|-------|
| CI/CD | Build policies | OPA Conftest |
| Admission | K8s resource policies | OPA/Gatekeeper, Kyverno |
| Runtime | Network, process policies | NetworkPolicy, Falco |
| Cloud | Cloud resource policies | Cloud Custodian, Sentinel |

### OPA (Open Policy Agent)

```rego
# Deny containers running as root
package kubernetes.admission

deny[msg] {
    input.request.kind.kind == "Pod"
    container := input.request.object.spec.containers[_]
    container.securityContext.runAsUser == 0
    msg := sprintf("Container %v runs as root", [container.name])
}
```

### Kyverno

```yaml
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata:
  name: require-labels
spec:
  validationFailureAction: Enforce
  rules:
    - name: require-team-label
      match:
        resources:
          kinds:
            - Pod
      validate:
        message: "Label 'team' is required"
        pattern:
          metadata:
            labels:
              team: "?*"
```

### OPA vs Kyverno

| Aspect | OPA/Gatekeeper | Kyverno |
|--------|----------------|---------|
| Language | Rego | YAML/JMESPath |
| Learning curve | Steeper | Easier |
| Capabilities | More powerful | Simpler use cases |
| Mutation | Supported | Native |
| Generation | Limited | Strong |
| CNCF Status | Graduated | Incubating |

## Vulnerability Management

### Vulnerability Lifecycle

```
DISCOVER ──▶ TRIAGE ──▶ REMEDIATE ──▶ VERIFY ──▶ CLOSE
    │           │            │           │          │
 Scanning   Severity     Fix/mitigate  Rescan   Document
            assessment   or accept               lessons
```

### Severity Ratings

| CVSS Score | Severity | Response Time |
|------------|----------|---------------|
| 9.0-10.0 | Critical | Immediate |
| 7.0-8.9 | High | Days |
| 4.0-6.9 | Medium | Weeks |
| 0.1-3.9 | Low | Backlog |

### Vulnerability Scanning Tools

| Tool | Scans | Strengths |
|------|-------|-----------|
| Trivy | Images, IaC, SBOM, K8s | All-in-one, fast |
| Grype | Images, SBOM | Accurate, Anchore |
| Snyk | Code, deps, containers | Developer-friendly |
| Clair | Images | CoreOS/Quay integration |
| Checkov | IaC | Bridgecrew, comprehensive |

### Trivy Example

```bash
# Scan image
trivy image nginx:latest

# Scan K8s cluster
trivy k8s --report summary cluster

# Generate SBOM
trivy image --format spdx nginx:latest > sbom.json

# Scan IaC
trivy config ./terraform/
```

## Secrets Management

### The Secrets Problem

- Secrets in code → breach
- Secrets in env vars → leaked in logs
- Secrets in config maps → no encryption at rest

### Secrets Management Approaches

| Approach | Security | Complexity |
|----------|----------|------------|
| K8s Secrets (encrypted) | Low-Medium | Low |
| Sealed Secrets | Medium | Low |
| External Secrets | High | Medium |
| HashiCorp Vault | High | High |

### HashiCorp Vault Integration

```yaml
# External Secrets Operator
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: app-secrets
spec:
  refreshInterval: 1h
  secretStoreRef:
    name: vault
    kind: ClusterSecretStore
  target:
    name: app-secrets
  data:
    - secretKey: db-password
      remoteRef:
        key: secret/data/myapp
        property: db_password
```

## Container Security

### Image Security Best Practices

1. **Use minimal base images** (distroless, Alpine)
2. **Don't run as root**
3. **Multi-stage builds** (no build tools in prod)
4. **Pin versions** (no `latest` tag)
5. **Scan in CI** (fail on critical/high)
6. **Sign images** (Cosign/Sigstore)

### Dockerfile Security

```dockerfile
# Good practices
FROM cgr.dev/chainguard/python:latest-dev AS builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM cgr.dev/chainguard/python:latest
WORKDIR /app
COPY --from=builder /app /app
COPY . .
USER nonroot
ENTRYPOINT ["python", "app.py"]
```

### Pod Security Standards

| Level | Description |
|-------|-------------|
| Privileged | Unrestricted (legacy) |
| Baseline | Minimally restrictive |
| Restricted | Hardened (recommended) |

```yaml
# Namespace label for PSS
apiVersion: v1
kind: Namespace
metadata:
  name: production
  labels:
    pod-security.kubernetes.io/enforce: restricted
    pod-security.kubernetes.io/warn: restricted
```

## Compliance Automation

### Common Frameworks

| Framework | Focus |
|-----------|-------|
| SOC 2 | Service organizations |
| PCI DSS | Payment card data |
| HIPAA | Healthcare data |
| GDPR | EU personal data |
| CIS Benchmarks | Infrastructure hardening |
| NIST | Government security |

### Continuous Compliance

```
┌─────────────────────────────────────────────────────────┐
│              CONTINUOUS COMPLIANCE                       │
│                                                          │
│  DEFINE        IMPLEMENT       MONITOR        REPORT    │
│  ┌─────┐       ┌─────┐        ┌─────┐        ┌─────┐   │
│  │Policy│ ───▶ │ IaC │ ───▶   │Scan │ ───▶   │Audit│   │
│  │as    │      │     │        │     │        │trail│   │
│  │Code  │      │     │        │     │        │     │   │
│  └─────┘       └─────┘        └─────┘        └─────┘   │
│     │             │              │               │       │
│     └─────────────┴──────────────┴───────────────┘       │
│                         │                                │
│                    Git (versioned)                       │
└─────────────────────────────────────────────────────────┘
```

### kube-bench (CIS Kubernetes Benchmark)

```bash
# Run CIS benchmark
kube-bench run --targets master,node

# Output
[PASS] 1.1.1 Ensure API server pod file permissions are 644
[FAIL] 1.1.2 Ensure API server pod file ownership is root:root
```

## Common DevSecOps Anti-Patterns

| Anti-Pattern | Problem | Solution |
|--------------|---------|----------|
| Security as blocker | Friction, bypass | Security as enabler |
| Manual security reviews | Slow, inconsistent | Automate in CI |
| Vulnerability backlogs | Technical debt | SLOs for remediation |
| Alert fatigue | Ignored alerts | Tune, prioritize |
| Secrets in repos | Breaches | Secrets management |
| No SBOM | Unknown components | Generate & track |

## Key Resources

- **OWASP** - owasp.org (Top 10, guides)
- **CNCF Security TAG** - github.com/cncf/tag-security
- **SLSA** - slsa.dev (supply chain)
- **Sigstore** - sigstore.dev (signing)
- **OpenSSF** - openssf.org (scorecards)

*"Security is not a feature. It's a property of the system."*
