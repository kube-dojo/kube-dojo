---
title: "Source Control & Collaboration Toolkit"
sidebar:
  order: 1
  label: "Source Control"
---
> **Toolkit Track** | 3 Modules | ~2.5 hours total

## Overview

The Source Control & Collaboration Toolkit goes beyond "just use GitHub." Modern platform engineering requires understanding the full landscape: GitLab's integrated DevOps platform, self-hosted alternatives for data sovereignty, and GitHub's advanced security features that most teams never enable.

This toolkit applies concepts from [DevSecOps Discipline](../../disciplines/reliability-security/devsecops/) and [GitOps Discipline](../../disciplines/delivery-automation/gitops/).

## Prerequisites

Before starting this toolkit:
- Basic Git proficiency (commits, branches, merges)
- Understanding of CI/CD concepts
- [DevSecOps Discipline](../../disciplines/reliability-security/devsecops/) - Security integration
- [GitOps Discipline](../../disciplines/delivery-automation/gitops/) - Git-centric workflows

## Modules

| # | Module | Complexity | Time |
|---|--------|------------|------|
| 11.1 | [GitLab](module-11.1-gitlab/) | `[COMPLEX]` | 50-60 min |
| 11.2 | [Gitea & Forgejo](module-11.2-gitea-forgejo/) | `[MEDIUM]` | 40-45 min |
| 11.3 | [GitHub Advanced](module-11.3-github-advanced/) | `[MEDIUM]` | 40-45 min |

## Learning Outcomes

After completing this toolkit, you will be able to:

1. **Deploy GitLab** — Full DevOps platform with integrated CI/CD, registry, security
2. **Run self-hosted Git** — Gitea/Forgejo for air-gapped and sovereignty requirements
3. **Leverage GitHub Advanced** — GHAS, Copilot, Actions beyond basics
4. **Choose the right platform** — Understand trade-offs for your context

## Tool Selection Guide

```
WHICH SOURCE CONTROL PLATFORM?
─────────────────────────────────────────────────────────────────

"I want everything integrated: Git, CI/CD, registry, security"
└──▶ GitLab
     • Single platform for entire DevOps lifecycle
     • Built-in container registry
     • Integrated security scanning (SAST, DAST, dependency)
     • Self-hosted or SaaS options

"I need self-hosted, lightweight, air-gapped capable"
└──▶ Gitea / Forgejo
     • Runs in 100MB RAM
     • Single binary deployment
     • GitHub-like UX
     • Forgejo = community fork (more open governance)

"I'm already on GitHub and want to maximize it"
└──▶ GitHub Advanced Security + Actions
     • CodeQL for vulnerability detection
     • Secret scanning with push protection
     • Dependabot beyond basics
     • Copilot for development velocity

"I need enterprise compliance and support"
└──▶ GitLab Ultimate or GitHub Enterprise
     • SSO/SAML integration
     • Audit logging
     • Compliance frameworks
     • Dedicated support

COMPARISON:
─────────────────────────────────────────────────────────────────
                    GitLab        Gitea/Forgejo    GitHub
─────────────────────────────────────────────────────────────────
Self-hosted         ✓             ✓                Enterprise only
Built-in CI         ✓             Basic            Actions (robust)
Container Registry  ✓             Via plugins      GHCR
Security Scanning   ✓ (built-in)  External tools   GHAS (paid)
Lightweight         ✗ (heavy)     ✓✓               N/A (SaaS)
Air-gapped          ✓             ✓                ✗
Community Edition   Free          Free             N/A
Learning Curve      Medium        Low              Low
```

## The Source Control Landscape

```
┌─────────────────────────────────────────────────────────────────┐
│              SOURCE CONTROL & COLLABORATION                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  FULL DEVOPS PLATFORMS                                          │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                                                           │  │
│  │  GitLab                                                   │  │
│  │  ┌─────────────────────────────────────────────────────┐ │  │
│  │  │ Source   │ CI/CD  │ Registry │ Security │ Monitoring│ │  │
│  │  │ Control  │ Pipelines│ Container│ SAST/DAST│ Metrics  │ │  │
│  │  └─────────────────────────────────────────────────────┘ │  │
│  │                                                           │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                  │
│  FOCUSED GIT HOSTING                                            │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                                                           │  │
│  │  GitHub            Gitea/Forgejo        Bitbucket         │  │
│  │  ┌─────────┐      ┌─────────┐          ┌─────────┐       │  │
│  │  │ World's │      │ Self-   │          │ Jira    │       │  │
│  │  │ largest │      │ hosted  │          │ native  │       │  │
│  │  │ + GHAS  │      │ 100MB   │          │ integr. │       │  │
│  │  └─────────┘      └─────────┘          └─────────┘       │  │
│  │                                                           │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                  │
│  INTEGRATION LAYER                                              │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  CI/CD: Jenkins │ Tekton │ Argo │ GitHub Actions          │  │
│  │  Security: Snyk │ Semgrep │ Trivy │ CodeQL                │  │
│  │  Registry: Harbor │ GHCR │ ECR │ Artifact Registry        │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Study Path

```
Module 11.1: GitLab
     │
     │  Full DevOps platform
     │  CI/CD, registry, security scanning
     │  Self-hosted deployment
     ▼
Module 11.2: Gitea & Forgejo
     │
     │  Lightweight self-hosted Git
     │  Air-gapped deployments
     │  Data sovereignty
     ▼
Module 11.3: GitHub Advanced
     │
     │  GHAS security features
     │  Actions beyond basics
     │  Copilot for productivity
     ▼
[Toolkit Complete] → Code Quality Toolkit
```

## Key Concepts

### Platform vs Point Solutions

| Approach | Example | Best For |
|----------|---------|----------|
| **Integrated Platform** | GitLab | Teams wanting single pane of glass |
| **Best-of-breed** | GitHub + Jenkins + Harbor | Specific tool requirements |
| **Lightweight** | Gitea + Drone CI | Resource-constrained environments |

### Self-Hosted Decision Matrix

```
SHOULD YOU SELF-HOST?
─────────────────────────────────────────────────────────────────

YES, self-host when:
├── Regulatory compliance requires data in your datacenter
├── Air-gapped environments (defense, healthcare)
├── Cost optimization at scale (1000+ users)
├── Custom authentication requirements
└── Network latency to SaaS is unacceptable

NO, use SaaS when:
├── Team < 100 people with standard needs
├── No dedicated platform team for maintenance
├── Frequent feature updates are valuable
├── Global team needs edge locations
└── Budget prioritizes features over control
```

## Common Workflows

### Migration Between Platforms

```
PLATFORM MIGRATION WORKFLOW
─────────────────────────────────────────────────────────────────

GitHub → GitLab Migration:
┌─────────────────────────────────────────────────────────────┐
│  1. Import repositories (GitLab has built-in importer)      │
│  2. Convert GitHub Actions → GitLab CI/CD                   │
│  3. Migrate issues/PRs (gl-import tool)                     │
│  4. Update webhooks and integrations                        │
│  5. Redirect old URLs (GitHub can redirect)                 │
│  6. Update CI badge URLs                                    │
│  7. Communicate timeline to team                            │
└─────────────────────────────────────────────────────────────┘

Timeline: 2-4 weeks for 50 repos
Risk: CI/CD translation is the hardest part
```

### Multi-Platform Strategy

```
MULTI-PLATFORM ARCHITECTURE
─────────────────────────────────────────────────────────────────

Common Pattern: GitHub (public) + GitLab (private)

┌─────────────────────────────────────────────────────────────┐
│                                                             │
│  PUBLIC (GitHub)           PRIVATE (GitLab Self-hosted)    │
│  ┌─────────────────┐      ┌─────────────────────────────┐ │
│  │ Open source     │      │ Proprietary code            │ │
│  │ Documentation   │      │ Internal tools              │ │
│  │ Community       │ ──▶  │ Infrastructure configs      │ │
│  │ engagement      │      │ Customer data handling      │ │
│  └─────────────────┘      └─────────────────────────────┘ │
│                                                             │
│  Sync: GitHub → GitLab mirror for open source in CI       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Hands-On Focus

| Module | Key Exercise |
|--------|--------------|
| GitLab | Deploy GitLab on Kubernetes, create CI/CD pipeline |
| Gitea/Forgejo | Run Gitea in Docker, configure Actions runner |
| GitHub Advanced | Enable GHAS, write custom CodeQL query |

## Tool Comparison

```
FEATURE COMPARISON
─────────────────────────────────────────────────────────────────

                        GitLab CE    GitLab EE    GitHub      Gitea
─────────────────────────────────────────────────────────────────
Git hosting             ✓            ✓            ✓           ✓
Built-in CI/CD          ✓            ✓            Actions     Basic
Container Registry      ✓            ✓            GHCR        Plugin
Security Scanning       ✓            ✓✓           GHAS ($$)   External
Self-hosted             ✓            ✓            Enterprise  ✓
Kubernetes deploy       Helm         Operator     N/A         Helm
RAM requirement         4GB+         8GB+         N/A         512MB
Free tier limits        Generous     Trial        Generous    Unlimited
SSO/SAML               Premium      ✓            Enterprise  Plugin
Audit logging          Premium      ✓            Enterprise  Basic
─────────────────────────────────────────────────────────────────
```

## Cost Considerations

```
TOTAL COST OF OWNERSHIP
─────────────────────────────────────────────────────────────────

GitHub (100 users):
├── Team plan: $4/user/month = $4,800/year
├── GHAS: $49/committer/month = ~$29,400/year (50 committers)
├── Actions: Pay per minute after free tier
└── Total: ~$35,000/year

GitLab Self-hosted (100 users):
├── Premium license: $29/user/month = $34,800/year
├── Infrastructure: ~$500/month = $6,000/year
├── Engineer time: 0.25 FTE = ~$40,000/year
└── Total: ~$81,000/year

Gitea Self-hosted (100 users):
├── License: Free
├── Infrastructure: ~$50/month = $600/year
├── Engineer time: 0.1 FTE = ~$16,000/year
├── External CI (Drone/Actions): ~$2,000/year
└── Total: ~$19,000/year

Note: Costs vary significantly by usage patterns and scale
```

## Related Tracks

- **Before**: [DevSecOps Discipline](../../disciplines/reliability-security/devsecops/) — Security integration concepts
- **Before**: [GitOps Discipline](../../disciplines/delivery-automation/gitops/) — Git-centric workflows
- **Related**: [CI/CD Pipelines Toolkit](../ci-cd-pipelines/) — Pipeline implementation
- **Related**: [Code Quality Toolkit](../code-quality/) — Scanning and analysis tools
- **After**: [Security Tools Toolkit](../security-tools/) — Runtime security

---

*"Your source control platform is the foundation of your entire software delivery process. Choose wisely—migration is painful."*
