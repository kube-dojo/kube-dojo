---
title: "DevSecOps Discipline"
sidebar:
  order: 1
  label: "DevSecOps"
---
> **Discipline Track** | 6 Modules | ~3.5 hours total

## Overview

DevSecOps integrates security into the DevOps workflow. Instead of security as a gate at the end, it's embedded throughout the software development lifecycle.

This track covers the complete DevSecOps journey—from shift-left practices and CI/CD security to supply chain protection and runtime defense—culminating in building a security-first culture.

## Prerequisites

Before starting this track:
- [Security Principles Track](../../foundations/security-principles/) — Defense in depth, least privilege
- [GitOps Track](../gitops/) — Modern deployment practices
- Basic CI/CD concepts (pipelines, builds, deployments)
- Container basics (Docker, registries)

## Modules

| # | Module | Complexity | Time |
|---|--------|------------|------|
| 4.1 | [DevSecOps Fundamentals](module-4.1-devsecops-fundamentals/) | `[MEDIUM]` | 30-35 min |
| 4.2 | [Shift-Left Security](module-4.2-shift-left-security/) | `[MEDIUM]` | 35-40 min |
| 4.3 | [Security in CI/CD Pipelines](module-4.3-security-cicd/) | `[COMPLEX]` | 40-45 min |
| 4.4 | [Supply Chain Security](module-4.4-supply-chain-security/) | `[COMPLEX]` | 40-45 min |
| -- | [Supply Chain Defense Guide](supply-chain-defense-guide/) | Reference | 20-25 min |
| 4.5 | [Runtime Security](module-4.5-runtime-security/) | `[COMPLEX]` | 40-45 min |
| 4.6 | [Security Culture & Automation](module-4.6-security-culture/) | `[MEDIUM]` | 30-35 min |

## Learning Outcomes

After completing this track, you will be able to:

1. **Implement shift-left security** — Pre-commit hooks, IDE plugins, secrets detection
2. **Build secure pipelines** — SAST, SCA, DAST, container scanning in CI/CD
3. **Protect the supply chain** — SBOMs, image signing, SLSA provenance
4. **Defend at runtime** — Falco, network policies, Pod Security Standards
5. **Build security culture** — Champions programs, metrics, automation

## Key Concepts

### The Security Pipeline

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
│  │ Linting  │       │   SCA    │       │   API    │            │
│  │          │       │ (deps)   │       │ security │            │
│  └──────────┘       ├──────────┤       └──────────┘            │
│                     │  Image   │                               │
│                     │ scanning │                               │
│                     └──────────┘                               │
│                                                                 │
│  DEPLOY              RUNTIME            CONTINUOUS              │
│  ┌──────────┐       ┌──────────┐       ┌──────────┐            │
│  │ Policy   │       │ Falco    │       │Compliance│            │
│  │ checks   │       │ detection│       │ scanning │            │
│  ├──────────┤       ├──────────┤       ├──────────┤            │
│  │ Image    │       │ Network  │       │ SBOM     │            │
│  │ signing  │       │ policies │       │ tracking │            │
│  └──────────┘       └──────────┘       └──────────┘            │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Core Principles

1. **Shift Left** — Find issues early when they're cheap to fix
2. **Automate Everything** — Security checks in CI/CD, not manual gates
3. **Security as Code** — Policies, configs, tests are versioned
4. **Shared Responsibility** — Everyone owns security
5. **Continuous Compliance** — Compliance verified automatically

## Tools Covered

| Category | Tools |
|----------|-------|
| **Secrets Detection** | detect-secrets, gitleaks, TruffleHog |
| **SAST** | Semgrep, CodeQL, Bandit, SonarQube |
| **SCA** | Trivy, Snyk, Dependabot, Grype |
| **Container Scanning** | Trivy, Grype, Docker Scout |
| **IaC Scanning** | Checkov, tfsec, Kubesec (see [IaC Security](../iac/module-6.3-iac-security/)) |
| **Supply Chain** | Cosign, Sigstore, Syft |
| **Runtime** | Falco, Kyverno, OPA/Gatekeeper |

## Study Path

```
Module 4.1: DevSecOps Fundamentals
     │
     ▼
Module 4.2: Shift-Left Security
     │
     ▼
Module 4.3: Security in CI/CD Pipelines
     │
     ▼
Module 4.4: Supply Chain Security
     │
     ▼
Module 4.5: Runtime Security
     │
     ▼
Module 4.6: Security Culture & Automation
     │
     ▼
[Track Complete] → Security Tools Toolkit
```

## Related Tracks

- **Before**: [Security Principles](../../foundations/security-principles/) — Foundational theory
- **Related**: [GitOps](../gitops/) — Deployment practices that support DevSecOps
- **Related**: [IaC Discipline](../iac/) — Infrastructure as Code security and testing
- **After**: [Security Tools Toolkit](../../toolkits/security-quality/security-tools/) — Hands-on implementations
- **After**: [IaC Tools](../../toolkits/infrastructure-networking/iac-tools/) — Terraform, OpenTofu, Pulumi hands-on

---

*"Security is not a feature. It's a property of the system—and building it in is cheaper than bolting it on."*
