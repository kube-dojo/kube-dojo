---
title: "Code Quality & Security Scanning Toolkit"
sidebar:
  order: 1
  label: "Code Quality"
---
> **Toolkit Track** | 5 Modules | ~4 hours total

## Overview

The Code Quality & Security Scanning Toolkit covers the shift-left revolution—catching bugs, vulnerabilities, and misconfigurations before they reach production. From SonarQube's technical debt visualization to Semgrep's developer-friendly security rules, these tools transform security from a gate to a guardrail.

This toolkit applies concepts from [DevSecOps Discipline](../../disciplines/reliability-security/devsecops/) and integrates with [CI/CD Pipelines Toolkit](../ci-cd-pipelines/).

## Prerequisites

Before starting this toolkit:
- [DevSecOps Discipline](../../disciplines/reliability-security/devsecops/) - Security integration concepts
- Basic CI/CD understanding
- Programming experience in at least one language
- Understanding of common vulnerability types (OWASP Top 10)

## Modules

| # | Module | Complexity | Time |
|---|--------|------------|------|
| 12.1 | [SonarQube](module-12.1-sonarqube/) | `[COMPLEX]` | 50-60 min |
| 12.2 | [Semgrep](module-12.2-semgrep/) | `[MEDIUM]` | 45-50 min |
| 12.3 | [CodeQL](module-12.3-codeql/) | `[COMPLEX]` | 50-60 min |
| 12.4 | [Snyk](module-12.4-snyk/) | `[MEDIUM]` | 40-45 min |
| 12.5 | [Checkov & Trivy](module-12.5-trivy/) | `[MEDIUM]` | 40-45 min |

## Learning Outcomes

After completing this toolkit, you will be able to:

1. **Deploy SonarQube** — Code quality analysis with technical debt tracking
2. **Write Semgrep rules** — Custom security patterns in minutes
3. **Run CodeQL queries** — GitHub's semantic code analysis
4. **Integrate Snyk** — Dependency and container vulnerability scanning
5. **Scan infrastructure code** — Checkov and Trivy for IaC and images

## Tool Selection Guide

```
WHICH CODE QUALITY TOOL?
─────────────────────────────────────────────────────────────────

"I need code quality metrics, technical debt tracking"
└──▶ SonarQube
     • Bugs, code smells, coverage
     • Quality gates for PRs
     • Historical trends
     • Language: 30+ languages

"I want to write security rules quickly"
└──▶ Semgrep
     • Pattern-matching syntax
     • Write rules in 5 minutes
     • Low false positives
     • Free tier generous

"I need deep semantic analysis"
└──▶ CodeQL
     • Query language for code
     • Finds complex patterns
     • GitHub native integration
     • Best for security research

"I need dependency vulnerability scanning"
└──▶ Snyk
     • SCA (Software Composition Analysis)
     • Container scanning
     • IaC scanning
     • Fix PRs auto-generated

"I need IaC and container scanning"
└──▶ Checkov + Trivy
     • Terraform, CloudFormation, K8s
     • Container image CVEs
     • Open source, free
     • CI/CD native

THE SCANNING MATRIX:
─────────────────────────────────────────────────────────────────
                SonarQube  Semgrep   CodeQL    Snyk      Trivy
─────────────────────────────────────────────────────────────────
Code Quality      ✓✓        ✗         ✗         ✗         ✗
SAST              ✓         ✓✓        ✓✓        ✓         ✗
SCA (deps)        ✗         ✗         ✗         ✓✓        ✓
Container         ✗         ✗         ✗         ✓✓        ✓✓
IaC               ✗         ✓         ✗         ✓         ✓✓
Secrets           ✗         ✓         ✗         ✓         ✓
Custom Rules      ✗         ✓✓        ✓✓        ✗         ✗
Self-hosted       ✓         ✓         ✓         ✗*        ✓
Free tier         Limited   Generous  GitHub    Generous  Free
─────────────────────────────────────────────────────────────────
```

## The Code Quality Landscape

```
┌─────────────────────────────────────────────────────────────────┐
│                  CODE QUALITY & SECURITY                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  CODE QUALITY & SAST                                            │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                                                           │  │
│  │  SonarQube         Semgrep           CodeQL               │  │
│  │  ┌─────────┐      ┌─────────┐       ┌─────────┐          │  │
│  │  │Technical│      │ Pattern │       │ Semantic│          │  │
│  │  │debt +   │      │ matching│       │ analysis│          │  │
│  │  │SAST     │      │ rules   │       │ queries │          │  │
│  │  └─────────┘      └─────────┘       └─────────┘          │  │
│  │                                                           │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                  │
│  SOFTWARE COMPOSITION ANALYSIS (SCA)                            │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                                                           │  │
│  │  Snyk              Dependabot        OWASP Dependency-    │  │
│  │  ┌─────────┐      ┌─────────┐       Check                 │  │
│  │  │Deps +   │      │ GitHub  │       ┌─────────┐          │  │
│  │  │container│      │ native  │       │  Open   │          │  │
│  │  │+ IaC    │      │         │       │ source  │          │  │
│  │  └─────────┘      └─────────┘       └─────────┘          │  │
│  │                                                           │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                  │
│  INFRASTRUCTURE & CONTAINER                                     │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                                                           │  │
│  │  Checkov           Trivy             Grype               │  │
│  │  ┌─────────┐      ┌─────────┐       ┌─────────┐          │  │
│  │  │   IaC   │      │Container│       │Container│          │  │
│  │  │scanning │      │+ IaC +  │       │ vuln    │          │  │
│  │  │         │      │ SBOM    │       │ scanner │          │  │
│  │  └─────────┘      └─────────┘       └─────────┘          │  │
│  │                                                           │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## The Shift-Left Journey

```
SHIFT-LEFT IMPLEMENTATION
─────────────────────────────────────────────────────────────────

LEVEL 1: Reactive (Where most teams start)
├── Security scan in CI (blocks merges)
├── Developers annoyed by false positives
└── Security team overwhelmed triaging

LEVEL 2: Proactive
├── Pre-commit hooks (secrets, formatting)
├── IDE plugins (real-time feedback)
├── Quality gates with thresholds
└── Developers own findings in their code

LEVEL 3: Preventive
├── Custom rules for your codebase patterns
├── Security champions write Semgrep rules
├── Auto-fix PRs for dependency updates
└── Guardrails, not gates

LEVEL 4: Embedded
├── Security guidance in IDE (Copilot-style)
├── Architectural decisions encoded as rules
├── Continuous scanning, not just CI
└── Mean time to fix: hours, not weeks

TOOLS BY LEVEL:
─────────────────────────────────────────────────────────────────
Level 1: Trivy in CI, basic SonarQube
Level 2: Semgrep + Snyk + quality gates
Level 3: Custom Semgrep rules + CodeQL
Level 4: IDE integration + continuous monitoring
```

## Study Path

```
Module 12.1: SonarQube
     │
     │  Code quality foundation
     │  Technical debt tracking
     │  Quality gates
     ▼
Module 12.2: Semgrep
     │
     │  Security pattern matching
     │  Custom rule writing
     │  Low false positives
     ▼
Module 12.3: CodeQL
     │
     │  Semantic code analysis
     │  GitHub Advanced Security
     │  Complex vulnerability patterns
     ▼
Module 12.4: Snyk
     │
     │  Dependency vulnerabilities
     │  Container scanning
     │  Auto-fix PRs
     ▼
Module 12.5: Checkov & Trivy
     │
     │  IaC scanning
     │  Container images
     │  Misconfigurations
     ▼
[Toolkit Complete] → Container Registries Toolkit
```

## Key Concepts

### Finding Categories

| Category | Examples | Tools |
|----------|----------|-------|
| **Bugs** | Null dereference, resource leaks | SonarQube, CodeQL |
| **Vulnerabilities** | SQL injection, XSS | Semgrep, CodeQL, Snyk |
| **Code Smells** | Long methods, duplications | SonarQube |
| **Security Hotspots** | Needs manual review | SonarQube |
| **Dependency CVEs** | Log4Shell, etc. | Snyk, Trivy |
| **Misconfigurations** | S3 public, no encryption | Checkov, Trivy |
| **Secrets** | API keys, passwords | Semgrep, Trivy, Gitleaks |

### Quality Gate Example

```
QUALITY GATE CONFIGURATION
─────────────────────────────────────────────────────────────────

"New Code" Gate (recommended):
┌─────────────────────────────────────────────────────────────┐
│ Condition                    │ Threshold │ Status          │
├─────────────────────────────────────────────────────────────┤
│ New Bugs                     │ = 0       │ ✓ Passed        │
│ New Vulnerabilities          │ = 0       │ ✓ Passed        │
│ New Security Hotspots        │ = 0       │ ✗ Failed (2)    │
│ New Code Coverage            │ >= 80%    │ ✓ Passed (87%)  │
│ New Duplicated Lines         │ <= 3%     │ ✓ Passed (1.2%) │
│ New Maintainability Rating   │ >= A      │ ✓ Passed        │
├─────────────────────────────────────────────────────────────┤
│ Overall                      │           │ ✗ FAILED        │
└─────────────────────────────────────────────────────────────┘

Focus on new code: Don't require fixing all legacy issues
to merge. Gate only on what changed.
```

## Common Workflows

### Multi-Tool Pipeline

```yaml
# .github/actions/workflows/security.yml
name: Security Scanning
on: [push, pull_request]

jobs:
  sast:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      # Semgrep for SAST
      - name: Semgrep
        uses: semgrep/semgrep-action@v1
        with:
          config: >-
            p/security-audit
            p/secrets
            p/owasp-top-ten

      # SonarQube for quality
      - name: SonarQube Scan
        uses: sonarsource/sonarqube-scan-action@master
        env:
          SONAR_TOKEN: ${{ secrets.SONAR_TOKEN }}
          SONAR_HOST_URL: ${{ secrets.SONAR_HOST_URL }}

  sca:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      # Snyk for dependencies
      - name: Snyk
        uses: snyk/actions/node@master
        with:
          args: --severity-threshold=high
        env:
          SNYK_TOKEN: ${{ secrets.SNYK_TOKEN }}

  container:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Build image
        run: docker build -t app:${{ github.sha }} .

      # Trivy for container
      - name: Trivy scan
        uses: aquasecurity/trivy-action@master
        with:
          image-ref: app:${{ github.sha }}
          severity: CRITICAL,HIGH
          exit-code: 1

  iac:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      # Checkov for IaC
      - name: Checkov
        uses: bridgecrewio/checkov-action@master
        with:
          directory: terraform/
          framework: terraform
          soft_fail: false
```

### IDE Integration

```
IDE-FIRST SECURITY
─────────────────────────────────────────────────────────────────

VS Code Extensions:
├── SonarLint (real-time SonarQube rules)
├── Semgrep (real-time pattern matching)
├── Snyk (dependency alerts)
└── Trivy (IaC highlighting)

Developer Experience:
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│  def login(username, password):                             │
│      query = f"SELECT * FROM users WHERE name='{username}'" │
│              ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~        │
│              ⚠ SQL Injection (CWE-89)                       │
│                                                             │
│      [Quick Fix: Use parameterized query]                   │
│                                                             │
└─────────────────────────────────────────────────────────────┘

Fix at write time, not review time.
```

## Hands-On Focus

| Module | Key Exercise |
|--------|--------------|
| SonarQube | Deploy SonarQube, analyze project, configure quality gate |
| Semgrep | Write custom rules, scan codebase, integrate in CI |
| CodeQL | Run queries, understand dataflow, find vulnerabilities |
| Snyk | Scan dependencies, container, create fix PR |
| Checkov/Trivy | Scan Terraform and images, custom policies |

## Tool Comparison

```
DETAILED COMPARISON
─────────────────────────────────────────────────────────────────

                    SonarQube   Semgrep    Snyk       Trivy
─────────────────────────────────────────────────────────────────
Primary Focus       Quality     SAST       SCA        Container
Languages           30+         30+        20+        N/A
Custom Rules        Limited     ✓✓         ✗          ✓ (Rego)
False Positives     Medium      Low        Low        Low
Speed               Slow        Fast       Medium     Fast
Self-hosted         ✓           ✓          ✗*         ✓
SaaS                ✓           ✓          ✓          ✓
Free Tier           Limited     Generous   Generous   Free
Enterprise          $$$$        $$         $$$        Free
CI Integration      ✓           ✓          ✓          ✓
IDE Plugin          SonarLint   ✓          ✓          ✓
─────────────────────────────────────────────────────────────────

* Snyk has snyk-cli but depends on Snyk cloud
```

## Cost Considerations

```
TOTAL COST OF OWNERSHIP (100 developers)
─────────────────────────────────────────────────────────────────

SonarQube:
├── Community: Free (limited)
├── Developer: $30k/year (good for most)
├── Enterprise: $50k+/year (large orgs)
└── Self-hosted: +$10k/year infra

Semgrep:
├── Community: Free (CLI + many rules)
├── Team: $50/dev/month = $60k/year
├── Enterprise: Custom pricing
└── Self-hosted: Free (CLI only)

Snyk:
├── Free: 200 tests/month (hobbyists)
├── Team: $57/dev/month = $68k/year
├── Enterprise: Custom pricing
└── Note: Tests = scans, can add up

Trivy/Checkov:
├── Open source: Free
├── Aqua Platform: Enterprise pricing
├── Prisma Cloud (Checkov): Enterprise
└── Self-hosted: Just compute costs

RECOMMENDED STACK BY BUDGET:
─────────────────────────────────────────────────────────────────
$0: Semgrep CLI + Trivy + SonarQube Community
$10k: Add SonarQube Developer
$50k: Add Snyk Team
$100k+: Full enterprise stack
```

## Related Tracks

- **Before**: [DevSecOps Discipline](../../disciplines/reliability-security/devsecops/) — Security concepts
- **Related**: [CI/CD Pipelines Toolkit](../ci-cd-pipelines/) — Pipeline integration
- **Related**: [Source Control Toolkit](../source-control/) — GitLab/GitHub security features
- **After**: [Container Registries Toolkit](../container-registries/) — Image security

---

*"The best security tool is the one developers actually use. Make it fast, make it accurate, make it actionable."*
