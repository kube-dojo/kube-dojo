---
name: platform-engineering-expert
description: Platform Engineering discipline knowledge. Use for Internal Developer Platforms, developer experience, self-service, golden paths, Backstage, Crossplane. Triggers on "platform engineering", "IDP", "developer experience", "self-service", "golden path".
---

# Platform Engineering Expert Skill

Authoritative knowledge source for Platform Engineering principles, Internal Developer Platforms (IDPs), and developer experience optimization. Based on industry best practices from Spotify, Netflix, and the broader platform engineering community.

## When to Use
- Writing or reviewing Platform Engineering curriculum content
- Designing Internal Developer Platforms
- Evaluating platform tools (Backstage, Crossplane, etc.)
- Developer experience improvements
- Self-service infrastructure patterns

## Core Platform Engineering Principles

### What is Platform Engineering?

Platform Engineering is the discipline of designing and building toolchains and workflows that enable self-service capabilities for software engineering organizations. It bridges the gap between developers and infrastructure.

### The Platform Team Mission

> "Reduce cognitive load on stream-aligned teams by providing a compelling internal product that accelerates delivery."

### Key Principles

1. **Platform as Product** - Treat the platform as an internal product with customers (developers)
2. **Self-Service First** - Developers should be able to provision what they need without tickets
3. **Golden Paths** - Paved roads that are easy to follow, not mandated
4. **Thin Platform** - Compose existing tools, don't rebuild everything
5. **Measure Developer Experience** - What gets measured gets improved

## The Platform Maturity Model

### Level 0: No Platform
- Developers manage their own infrastructure
- Snowflake environments everywhere
- High cognitive load on teams
- Slow onboarding

### Level 1: Standardization
- Shared CI/CD pipelines
- Common tooling choices
- Some documentation
- Manual provisioning with templates

### Level 2: Self-Service
- Service catalog
- Automated provisioning
- Golden path templates
- Developer portal

### Level 3: Optimized
- Full self-service
- Automatic compliance
- Integrated observability
- Continuous platform improvement

```
                    Platform Maturity
    ┌───────────────────────────────────────────────────┐
    │  L3: Optimized    │ Full automation, optimization │
    ├───────────────────┼───────────────────────────────┤
    │  L2: Self-Service │ Portal, catalog, golden paths │
    ├───────────────────┼───────────────────────────────┤
    │  L1: Standard     │ Shared CI/CD, templates       │
    ├───────────────────┼───────────────────────────────┤
    │  L0: None         │ Wild west, team autonomy only │
    └───────────────────┴───────────────────────────────┘
```

## Internal Developer Platform (IDP)

### IDP Components

| Component | Purpose | Examples |
|-----------|---------|----------|
| Developer Portal | Single entry point | Backstage, Port, Cortex |
| Service Catalog | Discover services | Backstage catalog |
| Software Templates | Scaffold new services | Backstage scaffolder, Cookiecutter |
| Documentation | Centralized docs | TechDocs, Docusaurus |
| Infrastructure Orchestration | Provision resources | Crossplane, Terraform, Pulumi |
| Environment Management | Dev/staging/prod | ArgoCD, Flux |
| Secrets Management | Secure credentials | Vault, External Secrets |

### The IDP Reference Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     DEVELOPER PORTAL                            │
│    (Backstage, Port, Cortex)                                   │
│    ┌──────────┬──────────┬──────────┬──────────┐               │
│    │ Catalog  │Templates │  Docs    │ Plugins  │               │
│    └──────────┴──────────┴──────────┴──────────┘               │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────┼────────────────────────────────────┐
│                    INTEGRATION LAYER                            │
│    ┌──────────┬──────────┬──────────┬──────────┐               │
│    │   Git    │   CI/CD  │ Secrets  │  ITSM    │               │
│    └──────────┴──────────┴──────────┴──────────┘               │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────┼────────────────────────────────────┐
│                 INFRASTRUCTURE ORCHESTRATION                    │
│    ┌──────────┬──────────┬──────────┬──────────┐               │
│    │Crossplane│Terraform │  ArgoCD  │   Flux   │               │
│    └──────────┴──────────┴──────────┴──────────┘               │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────┼────────────────────────────────────┐
│                    RESOURCE PROVIDERS                           │
│    ┌──────────┬──────────┬──────────┬──────────┐               │
│    │   AWS    │   GCP    │  Azure   │    K8s   │               │
│    └──────────┴──────────┴──────────┴──────────┘               │
└─────────────────────────────────────────────────────────────────┘
```

## Golden Paths

### What is a Golden Path?

A golden path is the opinionated, supported way to accomplish a task. It's not mandatory, but it's the path of least resistance.

**Golden Path Characteristics:**
- Pre-configured for compliance and security
- Integrated with observability
- Well-documented
- Actively maintained
- Easy to adopt

### Golden Path Examples

| Use Case | Golden Path |
|----------|-------------|
| New service | Backstage template → GitHub repo → ArgoCD deployment |
| Database | Request via portal → Crossplane provisions RDS |
| Secrets | External Secrets Operator → auto-sync from Vault |
| Monitoring | Auto-instrumented with OTel → Grafana dashboards |

### Golden Path vs Mandates

| Golden Paths (Good) | Mandates (Avoid) |
|---------------------|------------------|
| "This is the easy way" | "You must do it this way" |
| Compelling by being better | Enforced by policy |
| Teams can deviate if needed | No exceptions |
| Updated based on feedback | Static requirements |

## Developer Experience (DevEx)

### SPACE Framework

| Dimension | What it Measures |
|-----------|-----------------|
| **S**atisfaction | Developer happiness, fulfillment |
| **P**erformance | Outcomes, quality of work |
| **A**ctivity | Volume of actions (use carefully) |
| **C**ommunication | Collaboration effectiveness |
| **E**fficiency | Flow, minimal friction |

### DevEx Metrics

**Lead Time:**
- Code commit → production deployment
- Target: <1 day for standard changes

**Developer Onboarding:**
- Day 0 → first commit
- Target: <1 week to first production change

**Cognitive Load:**
- Survey-based measurement
- "How hard is it to deploy a new service?"

**Platform Adoption:**
- % of services using golden paths
- % of developers using self-service

### Developer Journey Mapping

Map friction points in common tasks:

```
CREATE NEW SERVICE
──────────────────────────────────────────────────────────
                    WITH PLATFORM     WITHOUT PLATFORM
Request infra       Self-service      Ticket (3 days)
Create repo         Template (5min)   Manual (1 hour)
Set up CI/CD        Automatic         Manual (4 hours)
First deploy        Same day          Week 2
Add monitoring      Built-in          Week 3 (maybe)
──────────────────────────────────────────────────────────
Total               < 1 day           2-3 weeks
```

## Platform Team Structure

### Team Topologies for Platforms

Platform teams are **enabling teams** that:
- Reduce cognitive load on stream-aligned teams
- Provide self-service capabilities
- Don't become a bottleneck

### Platform Team Anti-Patterns

| Anti-Pattern | Problem | Solution |
|--------------|---------|----------|
| Ticket-driven | Platform team is bottleneck | Self-service everything |
| Build everything | Slow, reinventing wheels | Compose existing tools |
| No customer focus | Low adoption | Treat devs as customers |
| Mandated adoption | Resentment | Make it compelling |
| No feedback loop | Platform doesn't evolve | Regular surveys, metrics |

### Platform Team Size

**Rough Guideline:**
- 1 platform engineer per 10-15 developers
- Minimum viable team: 3-4 people
- Grow with organization, not infrastructure

## Key Technologies

### Developer Portals

| Tool | Strengths | Considerations |
|------|-----------|----------------|
| Backstage | CNCF, extensible, plugins | Requires development |
| Port | SaaS, quick setup | Less customizable |
| Cortex | Scorecards, compliance | Enterprise pricing |
| OpsLevel | Service maturity | Commercial |

### Infrastructure Orchestration

| Tool | Approach | Best For |
|------|----------|----------|
| Crossplane | Kubernetes-native, CRDs | K8s-centric organizations |
| Terraform | HCL, mature ecosystem | Multi-cloud, existing TF |
| Pulumi | Programming languages | Developers, complex logic |

### GitOps

| Tool | Model | Best For |
|------|-------|----------|
| ArgoCD | Pull-based, UI | Visibility, multi-cluster |
| Flux | Pull-based, GitOps Toolkit | Composable, lightweight |

## Platform Success Metrics

### Adoption Metrics
- % services in catalog
- % using golden path templates
- Self-service usage rate

### Efficiency Metrics
- Time to first deploy
- Lead time for changes
- Mean time to recovery (MTTR)

### Quality Metrics
- Change failure rate
- Security compliance rate
- Documentation coverage

### Satisfaction Metrics
- Developer NPS
- Platform satisfaction survey
- Support ticket volume (should decrease)

## Common Platform Engineering Mistakes

| Mistake | Problem | Solution |
|---------|---------|----------|
| Building before listening | Low adoption | Start with developer research |
| Too much, too fast | Overwhelming | MVP, iterate |
| Platform as gatekeeper | Friction, resentment | Enable, don't block |
| Ignoring existing tools | Reinventing wheels | Compose and integrate |
| No documentation | Invisible value | Docs as product |
| No metrics | Can't prove value | Measure from day 1 |

## Key Books & Resources

- **Team Topologies** - Conway's law, team structures
- **Platform Engineering on Kubernetes** - Salaboy (Manning)
- **The DevEx Book** - Developer experience patterns
- **platformengineering.org** - Community resources
- **Backstage.io** - CNCF developer portal

## Platform Engineering vs DevOps vs SRE

| Aspect | Platform Engineering | DevOps | SRE |
|--------|---------------------|--------|-----|
| Focus | Developer experience | Delivery pipeline | Reliability |
| Output | Internal products | Processes & culture | SLOs & error budgets |
| Customer | Developers | Organization | End users |
| Success | Adoption, satisfaction | Deployment frequency | Uptime, MTTR |

*"The best platform is one developers choose to use, not one they're forced to."*
