---
title: "Module 1.5: Scaling Platform Organizations"
slug: platform/disciplines/core-platform/leadership/module-1.5-scaling-platform-org
sidebar:
  order: 6
---
> **Discipline Module** | Complexity: `[ADVANCED]` | Time: 55-65 min

## Prerequisites

Before starting this module:
- **Required**: [Module 1.4: Adoption & Migration Strategy](../module-1.4-adoption-migration/) — Driving adoption, managing change
- **Required**: [Module 1.1: Building Platform Teams](../module-1.1-platform-team-building/) — Team topologies and Conway's Law
- **Recommended**: [SRE: Service Level Objectives](../sre/module-1.2-slos/) — Defining measurable reliability targets
- **Recommended**: [FinOps Discipline](../../business-value/finops/) — Cloud cost management
- **Recommended**: Experience managing multi-team engineering organizations

---

## What You'll Be Able to Do

After completing this module, you will be able to:

- **Design organizational structures that scale platform teams from 5 to 50+ engineers**
- **Implement governance models that balance platform consistency with team autonomy at scale**
- **Build platform operating models that work across business units, regions, and cloud environments**
- **Evaluate when to centralize versus federate platform capabilities as the organization grows**

## Why This Module Matters

A payments company had one of the best platform teams in fintech. Five engineers who built and maintained a deployment platform, a monitoring stack, and a self-service database provisioning system. Developers loved them. Adoption was 95%. The team was a case study in doing platform engineering right.

Then the company grew from 80 developers to 350 in 18 months.

The platform team went from heroes to bottleneck overnight. Every new team needed onboarding. Every product launch required platform support. The backlog grew from 15 items to 120. Response time for support requests went from hours to weeks. The five engineers were working 60-hour weeks and still falling behind.

The company's response was to hire more platform engineers. They went from 5 to 25 in a year. But 25 people cannot operate as one team. Communication broke down. Three different engineers built overlapping solutions to the same problem. Standards diverged. The platform that was elegant at 5 people became chaotic at 25.

**Scaling a platform organization is not just hiring.** It requires deliberate structural decisions about governance, ownership, cost allocation, and team boundaries. Get these wrong and you create a bureaucratic mess that is worse than having no platform at all. This module teaches you how to scale without losing what made your platform team effective in the first place.

---

## Did You Know?

> **Dunbar's number** (roughly 150) is the cognitive limit to the number of people with whom one can maintain stable social relationships. When a platform organization exceeds ~8-12 people, informal coordination breaks down and you need explicit processes. Most platform scaling problems happen at exactly this inflection point.

> **Amazon's "two-pizza team" rule** was not about team size — it was about **ownership scope**. Jeff Bezos' insight was that small teams with clear ownership make better decisions and move faster than large teams with shared ownership. This principle applies directly to platform sub-teams.

> According to the 2024 Puppet State of Platform Engineering report, organizations with **mature platform governance** (clear SLOs, documented standards, explicit decision-making processes) scale their platform teams **2.4x more efficiently** than organizations that scale by headcount alone.

> **Google's infrastructure division** employs thousands of engineers, yet maintains consistency through a combination of automated enforcement, design reviews, and a strong culture of documentation. They do not achieve consistency through management oversight — they achieve it through systems.

---

## From 1 Team to 10: Growth Stages

### Stage 1: The Founding Team (2-5 people)

```
┌────────────────────────────────┐
│      PLATFORM TEAM             │
│                                │
│  ┌────┐ ┌────┐ ┌────┐        │
│  │ Eng│ │ Eng│ │ Eng│        │
│  │  A │ │  B │ │  C │        │
│  └────┘ └────┘ └────┘        │
│                                │
│  Everyone does everything.     │
│  Communication is informal.    │
│  Knowledge is shared by        │
│  sitting next to each other.   │
└────────────────────────────────┘
```

**Characteristics**:
- Everyone knows everything
- No formal processes needed
- Fast decision-making
- High bus-factor risk
- Works for 20-80 developers

**What to focus on**: Build the core platform. Validate product-market fit with internal users. Do not worry about governance or structure.

### Stage 2: The Specialized Team (5-12 people)

```
┌──────────────────────────────────────┐
│          PLATFORM TEAM                │
│                                       │
│  ┌─────────────┐  ┌──────────────┐   │
│  │  Infra/K8s  │  │   CI/CD &    │   │
│  │  Engineers   │  │   Developer  │   │
│  │             │  │   Experience │   │
│  │  ┌──┐ ┌──┐ │  │  ┌──┐ ┌──┐  │   │
│  │  │A │ │B │ │  │  │C │ │D │  │   │
│  │  └──┘ └──┘ │  │  └──┘ └──┘  │   │
│  └─────────────┘  └──────────────┘   │
│                                       │
│  + Tech Lead / Manager                │
│  + Product Manager (part-time)        │
│                                       │
│  Informal specialization emerges.     │
│  Communication requires effort.       │
│  Documentation becomes necessary.     │
└──────────────────────────────────────┘
```

**Characteristics**:
- Engineers develop specializations
- You need a tech lead or manager
- Documentation becomes necessary (not everyone knows everything)
- Weekly team meetings become important
- Works for 80-200 developers

**What to focus on**: Formalize ownership areas. Start documenting architecture decisions. Introduce lightweight processes (standups, architecture reviews). Hire or designate a product manager.

### Stage 3: The Multi-Team Organization (12-30 people)

```
┌────────────────────────────────────────────────┐
│           PLATFORM ORGANIZATION                 │
│                                                  │
│  ┌──────────────┐  ┌──────────────┐            │
│  │ Infrastructure│  │  Developer   │            │
│  │ Team          │  │  Experience  │            │
│  │ (5-7 people) │  │  Team        │            │
│  │              │  │  (5-7 people)│            │
│  │ • Kubernetes │  │  • CI/CD     │            │
│  │ • Networking │  │  • Portal    │            │
│  │ • Storage    │  │  • Templates │            │
│  └──────────────┘  └──────────────┘            │
│                                                  │
│  ┌──────────────┐  ┌──────────────┐            │
│  │  Data         │  │  Security &  │            │
│  │  Platform     │  │  Compliance  │            │
│  │  Team         │  │  Team        │            │
│  │  (4-6 people)│  │  (3-5 people)│            │
│  │  • Databases │  │  • IAM       │            │
│  │  • Streaming │  │  • Policies  │            │
│  │  • Analytics │  │  • Scanning  │            │
│  └──────────────┘  └──────────────┘            │
│                                                  │
│  + Director of Platform Engineering              │
│  + Platform Product Manager                      │
│  + Platform Architecture (shared role)           │
└────────────────────────────────────────────────┘
```

**Characteristics**:
- Multiple teams with distinct ownership
- You need a director (manages managers, sets strategy)
- Cross-team coordination becomes a challenge
- Standards and governance are essential
- Works for 200-500 developers

**What to focus on**: Clear team charters and ownership boundaries. Explicit API contracts between platform teams. Architecture reviews for cross-cutting concerns. Shared on-call and incident response.

### Stage 4: The Platform Division (30+ people)

```
┌──────────────────────────────────────────────────────┐
│              PLATFORM DIVISION                        │
│                                                       │
│  VP of Platform Engineering                           │
│  Platform Product Lead                                │
│  Platform Architecture Team                           │
│                                                       │
│  ┌───────────────────────────────────────────┐       │
│  │  Infrastructure Group                      │       │
│  │  ┌──────┐  ┌──────┐  ┌──────┐            │       │
│  │  │ K8s  │  │ Net  │  │Cloud │            │       │
│  │  │ Team │  │ Team │  │ Team │            │       │
│  │  └──────┘  └──────┘  └──────┘            │       │
│  └───────────────────────────────────────────┘       │
│                                                       │
│  ┌───────────────────────────────────────────┐       │
│  │  Developer Experience Group                │       │
│  │  ┌──────┐  ┌──────┐  ┌──────┐            │       │
│  │  │CI/CD │  │Portal│  │DX    │            │       │
│  │  │ Team │  │ Team │  │ Team │            │       │
│  │  └──────┘  └──────┘  └──────┘            │       │
│  └───────────────────────────────────────────┘       │
│                                                       │
│  ┌───────────────────────────────────────────┐       │
│  │  Specialized Platforms Group               │       │
│  │  ┌──────┐  ┌──────┐  ┌──────┐            │       │
│  │  │ Data │  │  ML  │  │  Sec │            │       │
│  │  │ Team │  │ Team │  │ Team │            │       │
│  │  └──────┘  └──────┘  └──────┘            │       │
│  └───────────────────────────────────────────┘       │
└──────────────────────────────────────────────────────┘
```

**Characteristics**:
- Multiple layers of management
- Dedicated architecture and product functions
- Significant coordination overhead
- Governance and standards are critical
- Works for 500+ developers

**What to focus on**: Federated governance (see below). Clear escalation paths. Investment in platform-for-the-platform (internal tooling for your own team). Preventing bureaucracy.

---

## Federated vs Centralized Platform Governance

### The Governance Spectrum

| Model | Description | Pros | Cons |
|-------|-------------|------|------|
| **Centralized** | One team sets all standards and makes all decisions | Consistent, efficient | Slow, disconnected from users |
| **Federated** | Standards set centrally, decisions made locally | Balanced speed and consistency | Requires coordination |
| **Decentralized** | Each team makes its own decisions | Fast, autonomous | Inconsistent, duplicated effort |

### The Federated Model (Recommended at Scale)

```
┌───────────────────────────────────────────────────┐
│              CENTRAL GOVERNANCE                     │
│                                                     │
│  Owns:                                              │
│  • Architecture standards (RFCs, ADRs)              │
│  • Security policies (mandatory guardrails)         │
│  • Technology radar (approved, trial, hold)          │
│  • Shared infrastructure (K8s clusters, networking) │
│  • Cost governance (budgets, chargeback rules)      │
│  • Platform SLOs (availability targets)             │
│                                                     │
│  Decides: "What are the boundaries?"                │
└──────────────────────┬────────────────────────────┘
                       │
         ┌─────────────┼─────────────┐
         ▼             ▼             ▼
┌────────────┐  ┌────────────┐  ┌────────────┐
│ Team A     │  │ Team B     │  │ Team C     │
│            │  │            │  │            │
│ Owns:      │  │ Owns:      │  │ Owns:      │
│ • Their    │  │ • Their    │  │ • Their    │
│   domain   │  │   domain   │  │   domain   │
│ • Their    │  │ • Their    │  │ • Their    │
│   roadmap  │  │   roadmap  │  │   roadmap  │
│ • Their    │  │ • Their    │  │ • Their    │
│   tooling  │  │   tooling  │  │   tooling  │
│   choices  │  │   choices  │  │   choices  │
│   (within  │  │   (within  │  │   (within  │
│   bounds)  │  │   bounds)  │  │   bounds)  │
│            │  │            │  │            │
│ Decides:   │  │ Decides:   │  │ Decides:   │
│ "How do    │  │ "How do    │  │ "How do    │
│ we build   │  │ we build   │  │ we build   │
│ within     │  │ within     │  │ within     │
│ boundaries?"│  │ boundaries?"│  │ boundaries?"│
└────────────┘  └────────────┘  └────────────┘
```

### What Gets Centralized vs Federated

| Decision | Centralize | Federate | Why |
|----------|-----------|----------|-----|
| Kubernetes version | Yes | | Security, compatibility |
| Monitoring stack | Yes | | Consistent observability |
| CI/CD tool | Yes | | Shared investment |
| Programming language for platform tools | | Yes | Teams know their domain best |
| API design standards | Yes | | Interoperability |
| Feature prioritization | | Yes | Teams know their users best |
| Cost budgets | Yes (total) | Yes (per-team allocation) | Central budget, local spending |
| Incident response process | Yes | | Consistency in crisis |
| Hiring criteria | Yes (framework) | Yes (specific skills) | Consistent bar, diverse needs |

### The Technology Radar

A technology radar classifies tools and technologies into four categories:

```
┌─────────────────────────────────────────┐
│           TECHNOLOGY RADAR               │
│                                          │
│  ┌──────────────────────────────────┐   │
│  │ ADOPT — Use in production        │   │
│  │ • ArgoCD        • Kyverno        │   │
│  │ • Terraform     • Backstage      │   │
│  │ • Prometheus    • GitHub Actions  │   │
│  └──────────────────────────────────┘   │
│                                          │
│  ┌──────────────────────────────────┐   │
│  │ TRIAL — Evaluate in pilot        │   │
│  │ • Crossplane    • OpenTofu       │   │
│  │ • Cilium        • Score          │   │
│  └──────────────────────────────────┘   │
│                                          │
│  ┌──────────────────────────────────┐   │
│  │ ASSESS — Research, no production │   │
│  │ • Wasm on K8s   • Radius        │   │
│  │ • eBPF mesh     • KCP           │   │
│  └──────────────────────────────────┘   │
│                                          │
│  ┌──────────────────────────────────┐   │
│  │ HOLD — Do not adopt              │   │
│  │ • Jenkins       • Helm v2        │   │
│  │ • Custom CRDs   • Docker Swarm   │   │
│  │   (without review)               │   │
│  └──────────────────────────────────┘   │
│                                          │
│  Updated: Quarterly                      │
│  Decided by: Architecture review board   │
└─────────────────────────────────────────┘
```

---

## Platform SLOs and Internal SLAs

### Why Internal SLOs Matter

Without SLOs, platform reliability is invisible until it is terrible. With SLOs, you can:
- Prove your platform is reliable (data, not feelings)
- Prioritize reliability work based on budget burn
- Set expectations with development teams
- Justify investment in reliability engineering

### Defining Platform SLOs

| Platform Service | SLI (what you measure) | SLO (target) |
|-----------------|----------------------|---------------|
| **Kubernetes API** | API request success rate | 99.95% |
| **CI/CD pipelines** | Pipeline success rate (infrastructure-caused failures) | 99.9% |
| **Container registry** | Image pull success rate | 99.95% |
| **Deployment system** | Deployment success rate | 99.9% |
| **Developer portal** | Portal availability | 99.9% |
| **Secret management** | Vault API availability | 99.99% |
| **DNS** | DNS resolution success rate | 99.99% |
| **Monitoring stack** | Metric ingestion success rate | 99.9% |

### SLOs vs SLAs

| | SLO (Service Level Objective) | SLA (Service Level Agreement) |
|-|-------------------------------|-------------------------------|
| **What** | Internal reliability target | Formal commitment (sometimes contractual) |
| **Audience** | Platform team | Development teams, leadership |
| **Consequence of miss** | Prioritize reliability work | Remediation plan, possible escalation |
| **Tracking** | Automated dashboards | Monthly or quarterly reviews |
| **Flexibility** | Can adjust based on learning | Changes require negotiation |

### The Internal SLA Document

If your platform is large enough (serving 100+ developers), formalize an internal SLA:

```
PLATFORM TEAM INTERNAL SLA
═══════════════════════════

Coverage: Monday-Friday, 9 AM - 6 PM [timezone]
Emergency: 24/7 for P1 incidents

Response Times:
  P1 (Platform outage):     15 minutes
  P2 (Degraded performance): 2 hours
  P3 (Feature request):      5 business days
  P4 (General inquiry):      10 business days

Availability Targets:
  Core platform (K8s, CI/CD, monitoring): 99.9%
  Developer portal: 99.5%
  Non-production environments: 99%

Maintenance Windows:
  Planned: Tuesday 2-4 AM [timezone], with 48h notice
  Emergency: As needed, with best-effort notice

Escalation:
  Level 1: #platform-support Slack channel
  Level 2: Platform on-call (PagerDuty)
  Level 3: Platform engineering manager
```

---

## Cost Allocation and Chargeback Models

### Why Cost Allocation Matters

Without cost allocation:
- Platform costs are a black hole in the budget
- No incentive for teams to use resources efficiently
- Platform team cannot prove ROI
- Leadership sees platform as "just expense"

With cost allocation:
- Teams understand the cost of their infrastructure
- Natural incentive to optimize
- Platform team can demonstrate value vs cost
- Budget conversations are data-driven

### Cost Allocation Models

| Model | Description | Pros | Cons |
|-------|-------------|------|------|
| **Central funding** | Platform costs in one budget | Simple, no per-team tracking | No cost awareness, hard to justify |
| **Showback** | Show teams their costs, don't charge them | Awareness without friction | No financial incentive to optimize |
| **Chargeback** | Charge teams for their actual usage | Strong optimization incentive | Complex to implement, creates friction |
| **Hybrid** | Base platform centrally funded, usage-based extras charged | Balanced incentives | Medium complexity |

### The Hybrid Model (Recommended)

```
┌────────────────────────────────────────────────────┐
│              COST ALLOCATION MODEL                   │
│                                                      │
│  CENTRALLY FUNDED (platform tax)                     │
│  ─────────────────────────────                       │
│  • Kubernetes control plane                          │
│  • Shared monitoring and logging                     │
│  • CI/CD infrastructure                              │
│  • Developer portal                                  │
│  • Platform team salaries                            │
│  • Base security and compliance tooling              │
│                                                      │
│  CHARGED TO TEAMS (usage-based)                      │
│  ────────────────────────────                        │
│  • Compute resources (CPU, memory)                   │
│  • Storage (persistent volumes, object storage)      │
│  • Data transfer (cross-region, egress)              │
│  • Specialized services (GPU instances, databases)   │
│  • Non-production environments beyond standard       │
│                                                      │
│  COST VISIBILITY                                     │
│  ───────────────                                     │
│  Every team gets a monthly cost report:              │
│  • Total cost                                        │
│  • Cost per service                                  │
│  • Month-over-month trend                            │
│  • Optimization recommendations                      │
│  • Comparison with similar teams                     │
└────────────────────────────────────────────────────┘
```

### Implementing Cost Tagging

Cost allocation requires tagging resources to teams. Enforce this with automated policies:

```yaml
# Example: Required Kubernetes labels (enforced by Kyverno/OPA)
required_labels:
  - team           # e.g., "payments", "search", "platform"
  - environment    # e.g., "production", "staging", "dev"
  - service        # e.g., "checkout-api", "user-service"
  - cost-center    # e.g., "CC-1234"

# Example: Kyverno policy to enforce labels
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata:
  name: require-cost-labels
spec:
  validationFailureAction: Enforce
  rules:
    - name: check-labels
      match:
        any:
          - resources:
              kinds:
                - Deployment
                - StatefulSet
      validate:
        message: "All workloads must have team, environment, service, and cost-center labels."
        pattern:
          metadata:
            labels:
              team: "?*"
              environment: "?*"
              service: "?*"
              cost-center: "?*"
```

---

## Measuring Platform Team Effectiveness

### The Platform Scorecard

Track these metrics monthly or quarterly:

| Category | Metric | Target | Current |
|----------|--------|--------|---------|
| **Adoption** | % of teams on platform | > 80% | ___ |
| **Adoption** | % of deploys via platform | > 90% | ___ |
| **Speed** | Time to first deploy (new service) | < 2 hours | ___ |
| **Speed** | Lead time for changes | < 1 day | ___ |
| **Reliability** | Platform availability | > 99.9% | ___ |
| **Reliability** | Platform-caused incidents | < 2/month | ___ |
| **Satisfaction** | Developer NPS | > 40 | ___ |
| **Satisfaction** | Support satisfaction | > 4/5 | ___ |
| **Efficiency** | Self-service ratio | > 90% | ___ |
| **Efficiency** | Support ticket volume (trend) | Decreasing | ___ |
| **Cost** | Platform cost per developer | < $X/month | ___ |
| **Cost** | Infrastructure cost savings | > $Y/quarter | ___ |

### Platform Team Health Metrics

In addition to user-facing metrics, track team health:

| Metric | Healthy | Warning | Critical |
|--------|---------|---------|----------|
| **Sprint velocity** | Stable or increasing | Declining | Erratic |
| **On-call load** | < 2 pages/week | 3-5 pages/week | > 5 pages/week |
| **Toil ratio** | < 30% | 30-50% | > 50% |
| **Attrition** | < 10%/year | 10-20%/year | > 20%/year |
| **Bus factor** | 3+ per system | 2 per system | 1 per system |
| **Tech debt ratio** | < 20% of work | 20-40% | > 40% |

---

## Build vs Buy vs Partner

### The Decision Framework

Every platform capability faces this question: do we build it ourselves, buy a commercial product, or partner with an open-source community?

| Factor | Build | Buy | Partner (Open Source) |
|--------|-------|-----|---------------------|
| **Control** | Full | Limited | Medium (contribute upstream) |
| **Cost (upfront)** | High (engineering time) | Medium (license fee) | Low (free + integration time) |
| **Cost (ongoing)** | High (maintenance) | Medium (subscription) | Medium (upgrades, customization) |
| **Time to value** | Months | Weeks | Weeks to months |
| **Customization** | Unlimited | Vendor roadmap dependent | Fork-and-extend (risky) |
| **Talent** | Must hire specialists | Vendor provides support | Community knowledge |
| **Risk** | Maintenance burden, bus factor | Vendor lock-in, price increases | Project abandonment, complexity |

### When to Build

Build when:
- Your requirements are truly unique (rare — most infrastructure is not unique)
- The capability is a core differentiator for your platform
- You have the talent to build AND maintain it long-term
- The commercial and open-source options genuinely do not fit

**Warning signs you should NOT build**:
- "We could build a better version" (you probably cannot maintain it)
- "The vendor is too expensive" (compare total cost including engineering time)
- "We need full control" (you rarely actually do)
- "It'll be a fun project" (this is not a valid business reason)

### When to Buy

Buy when:
- The capability is well-served by commercial products
- Your team should focus on higher-value work
- You need support and SLAs
- Time to value is critical

**Warning signs you should NOT buy**:
- The vendor requires deep integration that creates lock-in
- The product requires extensive customization to fit your needs
- The vendor's roadmap does not align with your direction
- The total cost (license + integration + customization) exceeds building

### When to Partner (Open Source)

Partner with open source when:
- Active community with multiple corporate backers
- Extensible architecture that supports your customization
- You can contribute upstream (gives you influence over direction)
- You have talent to integrate and maintain

**Warning signs**:
- Single-company-backed project (risk of abandonment or relicensing)
- Small community (limited support, slow bug fixes)
- Frequent breaking changes (high maintenance burden)
- License changes (recent examples: HashiCorp BSL, Redis SSPL)

### Build vs Buy Decision Matrix

For each capability, score these factors (1-5):

```
Capability: _______________

Build Score:
  Team has expertise:          ___/5
  Requirements are unique:     ___/5
  Long-term maintenance ok:    ___/5
  Time to build acceptable:    ___/5
  Total:                       ___/20

Buy Score:
  Good product exists:         ___/5
  Budget available:            ___/5
  Integration effort low:      ___/5
  Vendor reliable:             ___/5
  Total:                       ___/20

Open Source Score:
  Good project exists:         ___/5
  Active community:            ___/5
  License acceptable:          ___/5
  Team can contribute:         ___/5
  Total:                       ___/20

Recommendation: Highest score → [ ] Build  [ ] Buy  [ ] Open Source
```

---

## Hands-On Exercises

### Exercise 1: Platform Organization Design (45 min)

Design the structure for a platform organization at different scales:

**Scenario A: 100 developers, 5 platform engineers**
```
Team structure:
Specializations:
Communication cadence:
Key risk:
```

**Scenario B: 300 developers, 15 platform engineers**
```
Team structure:
Number of sub-teams:
Team charters:
Governance model:
Key risk:
```

**Scenario C: 800 developers, 40 platform engineers**
```
Organizational structure:
Groups and teams:
Governance bodies:
Central vs federated decisions:
Key risk:
```

For each scenario, answer:
1. What is the biggest organizational risk at this scale?
2. What governance mechanisms are needed?
3. How do teams communicate across boundaries?
4. What is the role of the platform leader?

### Exercise 2: Platform SLO Workshop (40 min)

Define SLOs for your platform services:

**Step 1**: List your platform services
```
1. _______________
2. _______________
3. _______________
4. _______________
5. _______________
```

**Step 2**: For each service, define SLIs and SLOs
```
Service: _______________
SLI (what you measure): _______________
SLO (target): _______________
Measurement method: _______________
Error budget (per month): _______________
Error budget policy: _______________
  If < 50% budget remaining: _______________
  If budget exhausted: _______________
```

**Step 3**: Create an SLO dashboard layout
```
┌────────────────────────────────────────────┐
│          PLATFORM SLO DASHBOARD             │
│                                             │
│  Service 1: _______________                 │
│  SLO: ____%  Current: ____%  Budget: ___   │
│  [────────────────█─────] 30-day view       │
│                                             │
│  Service 2: _______________                 │
│  SLO: ____%  Current: ____%  Budget: ___   │
│  [────────────────█─────] 30-day view       │
│                                             │
└────────────────────────────────────────────┘
```

### Exercise 3: Build vs Buy Analysis (30 min)

Evaluate a platform capability using the decision matrix:

**Choose one**: Service mesh, developer portal, CI/CD, monitoring, secrets management, database provisioning

```
Capability: _______________

Build:
  Effort: ___ person-months
  Maintenance: ___ people ongoing
  Risk: _______________
  Score: ___/20

Buy:
  Product: _______________
  Cost: $___ /year
  Integration: ___ weeks
  Risk: _______________
  Score: ___/20

Open Source:
  Project: _______________
  Integration: ___ weeks
  Customization: ___ weeks
  Risk: _______________
  Score: ___/20

Recommendation: _______________
Justification: _______________
```

### Exercise 4: Cost Allocation Model Design (30 min)

Design a cost allocation model for your platform:

```
COST ALLOCATION MODEL
═════════════════════

Centrally funded items:
  1. _______________  ($___/month)
  2. _______________  ($___/month)
  3. _______________  ($___/month)
  Total central: $___/month

Charged to teams:
  1. _______________  (per ___)
  2. _______________  (per ___)
  3. _______________  (per ___)

Monthly team report includes:
  [ ] Total cost
  [ ] Cost breakdown by service
  [ ] Trend vs previous month
  [ ] Optimization recommendations
  [ ] Comparison with similar teams

Implementation plan:
  Month 1: _______________
  Month 2: _______________
  Month 3: _______________
```

---

## War Story: Scaling From 5 to 50 Platform Engineers

**Company**: Large SaaS company, ~1,200 engineers, publicly traded

**Situation**: The original platform team of 5 engineers was legendary within the company. They had built a deployment platform that developers loved, achieving 92% voluntary adoption in 2 years. They were fast, responsive, and had deep relationships with every development team.

Then the company decided to expand the platform to cover data infrastructure, ML pipelines, and security tooling. The plan: grow from 5 to 50 platform engineers over 18 months.

**Timeline**:

**Month 1-3: Rapid hiring (5 to 15)**
- Hired 10 engineers in 3 months
- All joined the "platform team" as one group
- Slack channel went from 5 people to 15
- Standup went from 10 minutes to 35 minutes
- Decision-making slowed dramatically

**Month 4-6: First split (15 to 25)**
- Split into 3 teams: Infrastructure, Developer Experience, Data Platform
- Each team had a tech lead but shared a manager
- Immediately hit coordination problems: Infrastructure team changed a Kubernetes configuration that broke Data Platform's pipelines
- No API contracts between teams

**Month 7-9: Growing pains (25 to 35)**
- Created "Platform Architecture" role to coordinate across teams
- Introduced bi-weekly architecture reviews
- Established a technology radar (Adopt, Trial, Assess, Hold)
- Hired a platform product manager
- Defined SLOs for all platform services
- Added a Security team

**Month 10-12: Governance (35 to 45)**
- Created a "Platform RFC" process for major changes
- Introduced cost allocation (showback model)
- Published an internal SLA
- Created a "Platform Council" — monthly meeting of all team leads
- Started measuring platform scorecard

**Month 13-18: Maturity (45 to 50)**
- Promoted the original tech lead to Director of Platform Engineering
- Each team had its own manager, tech lead, and roadmap
- Federated governance: central architecture standards, local team decisions
- Platform scorecard reviewed monthly with VP of Engineering

**What worked**:
- Splitting teams early (at 12-15 people, not 25)
- Hiring a platform architect to own cross-cutting concerns
- Technology radar prevented tool sprawl
- SLOs made reliability a measurable commitment
- Cost allocation made platform costs visible and defensible

**What they would do differently**:
- Split teams at 8-10, not 15 (the first split was too late)
- Establish API contracts between teams before the first split
- Hire a product manager earlier (should have been hire #6, not #20)
- Start with federated governance, not centralized (the transition was painful)

**Business impact**: The platform organization reduced time-to-production from 3 weeks to 2 days, reduced infrastructure incidents by 65%, and saved an estimated $4M/year in engineering productivity. The cost of the platform org: $8M/year in salaries. ROI: positive within the first year.

**Lessons**:
1. **Split early**: 8-10 people is the inflection point, not 15-20
2. **Define boundaries before you need them**: API contracts, ownership, and governance should precede team growth
3. **Product management is not optional**: A 50-person engineering org without product management builds impressive things nobody asked for
4. **Governance scales with headcount**: What works at 5 people (informal, trust-based) fails at 50 (need explicit processes)
5. **Measure ruthlessly**: Without the platform scorecard, leadership would have questioned a $8M/year investment

---

## Knowledge Check

### Question 1
At what team size do informal coordination mechanisms typically break down for platform teams?

<details>
<summary>Show Answer</summary>

**8-12 people**. At this size, not everyone can know everything, informal communication misses people, and decision-making slows because more voices need to be heard. This is when you need to introduce explicit team charters, ownership boundaries, documented standards, and regular cross-team coordination mechanisms. The most common mistake is waiting too long to split — many organizations wait until 15-20 people, by which point significant dysfunction has already accumulated.

</details>

### Question 2
What is federated governance and why is it preferred over centralized governance at scale?

<details>
<summary>Show Answer</summary>

Federated governance centralizes **standards and boundaries** while federating **implementation decisions** to individual teams. Central governance owns architecture standards, security policies, technology radar, and SLOs. Individual teams own their roadmaps, implementation approaches, and tooling choices (within the boundaries).

It is preferred because: (1) Centralized governance becomes a bottleneck — every decision waits for the architecture board. (2) Teams closest to users make better local decisions. (3) It preserves autonomy and ownership, which are critical for engineer satisfaction and retention. (4) It scales — adding a team does not add a decision to the central queue. The trade-off is coordination complexity, which is addressed through RFCs, architecture reviews, and technology radars.

</details>

### Question 3
Explain the hybrid cost allocation model. Why is it recommended over pure chargeback?

<details>
<summary>Show Answer</summary>

The hybrid model **centrally funds** base platform infrastructure (Kubernetes control plane, CI/CD, monitoring, portal, team salaries) while **charging teams** for usage-based costs (compute, storage, data transfer, specialized services). It is preferred because: (1) Centrally funding the base platform removes friction from adoption — teams are not penalized for using the platform. (2) Usage-based charging for resources creates incentive to optimize without penalizing platform adoption. (3) Pure chargeback can discourage platform adoption ("why pay for the platform when I can run my own EC2 instance?") and creates perverse incentives to avoid shared infrastructure. (4) The hybrid model makes platform costs defensible to leadership while keeping developer-facing costs reasonable.

</details>

### Question 4
When should you build a platform capability vs buying a commercial product?

<details>
<summary>Show Answer</summary>

**Build** when: requirements are truly unique, the capability is a core differentiator, you have talent to build AND maintain it, and commercial/open-source options genuinely do not fit. **Buy** when: good products exist, your team should focus on higher-value work, you need vendor support and SLAs, and time to value is critical.

Most platform teams over-index on building. The honest test: is your infrastructure problem truly unique, or does it just feel unique? Most companies' CI/CD, monitoring, and deployment needs are well-served by existing products. Build only when the total cost (including maintenance, opportunity cost, and bus-factor risk) is lower than buying — which is less often than engineers think.

</details>

### Question 5
Your platform organization has grown to 30 engineers across 4 teams. Two teams are building overlapping features. What went wrong and how do you fix it?

<details>
<summary>Show Answer</summary>

**Root cause**: Missing or unclear team charters and ownership boundaries. When teams don't have explicit scope definitions, they naturally drift toward interesting problems — which often overlap.

**Fix**: (1) Immediately clarify ownership — who owns what, decided by the platform director. (2) Write explicit team charters that define each team's domain, users, and responsibilities. (3) Establish an RFC process for new capabilities — before building, propose it and get sign-off that it is in your team's scope. (4) Create a regular cross-team coordination meeting (bi-weekly) where teams share what they are building. (5) Assign a platform architect to identify and resolve overlap proactively. Prevention is better than remediation — team charters should be written before teams are formed, not after problems emerge.

</details>

### Question 6
How do platform SLOs differ from application SLOs?

<details>
<summary>Show Answer</summary>

Platform SLOs measure **infrastructure reliability that development teams depend on**: Kubernetes API availability, CI/CD pipeline success rate, deployment system reliability, monitoring ingestion, secrets management. Application SLOs measure **end-user experience**: request latency, error rate, availability.

Key differences: (1) Platform SLO violations affect ALL teams, not just one service — the blast radius is much larger. (2) Platform SLOs should be stricter (99.95%+) because they are a dependency for everything else. (3) Platform SLO violations require platform team response, not development team response. (4) Platform SLOs should be tracked with error budgets just like application SLOs — when budget is low, prioritize reliability over features. They complement each other: good platform SLOs make it possible for applications to meet their own SLOs.

</details>

### Question 7
Your platform team is considering adopting an open-source project with a single corporate backer. What risks should you evaluate?

<details>
<summary>Show Answer</summary>

Key risks: (1) **License change** — the backer may switch to a non-open-source license (precedent: HashiCorp moving Terraform to BSL, Redis moving to SSPL). Evaluate the license history and the company's business model. (2) **Project abandonment** — if the company pivots or is acquired, the project may be abandoned. Check for a diverse maintainer base beyond the one company. (3) **Roadmap control** — the backer controls the roadmap and may prioritize their commercial interests over community needs. (4) **Vendor lock-in by another name** — the "open-source" project may be designed to funnel users to the company's paid product. (5) **Mitigation**: evaluate the project's governance model, contributor diversity, and license. Consider whether you could maintain a fork if necessary. Prefer projects under neutral foundations (CNCF, Apache, Linux Foundation).

</details>

### Question 8
Scenario: Leadership asks you to justify the $5M annual cost of the platform organization. How do you build the business case?

<details>
<summary>Show Answer</summary>

Build the case around measurable impact, not activity. Structure it as:

**Direct savings**: (1) Infrastructure cost optimization achieved through platform automation and governance (quantify). (2) Incident reduction — fewer production incidents means less developer time on firefighting (quantify hours saved x cost/hour). (3) Standardization savings — one monitoring stack instead of 8, one CI system instead of 5 (quantify avoided license and maintenance costs).

**Productivity gains**: (1) Time-to-production improvement (before: 3 weeks, after: 2 days — multiply by number of new services per year). (2) Deploy frequency increase (faster deploys = faster feature delivery). (3) Developer onboarding time reduction (before: 3 weeks, after: 3 days — multiply by hires per year).

**Risk reduction**: (1) Security and compliance posture improvement. (2) Reduced blast radius through standardized infrastructure. (3) Knowledge centralization reducing bus-factor risk.

**The format**: "Platform costs $5M. It saves $X in direct costs, enables $Y in productivity gains, and reduces $Z in risk. Net ROI: positive/negative." If you cannot demonstrate positive ROI, either the platform is not delivering enough value (fix it) or you are not measuring impact (fix your metrics).

</details>

---

## Summary

Scaling a platform organization requires deliberate structural design at every growth stage. What works at 5 people — informal communication, shared ownership, trust-based coordination — breaks at 15. What works at 15 breaks at 50.

Key principles:
- **Split teams early**: 8-10 people, not 15-20
- **Federate governance**: Central standards, local decisions
- **Define SLOs**: Make reliability measurable and visible
- **Allocate costs transparently**: Hybrid model balances incentives
- **Measure everything**: Platform scorecard proves value to leadership
- **Build vs buy honestly**: Most infrastructure is not unique enough to build
- **Invest in governance before you need it**: Team charters, RFCs, technology radar

---

## What's Next

Congratulations on completing the Platform Leadership discipline. You now have frameworks for building teams, designing developer experiences, running your platform as a product, driving adoption, and scaling your organization.

**Recommended next steps**:
- [Platform Engineering Discipline](../platform-engineering/) — Technical depth for the platforms you lead
- [SRE Discipline](../sre/) — Reliability practices your platform must embody
- [FinOps Discipline](../../business-value/finops/) — Cost management at scale
- [GitOps Discipline](../../delivery-automation/gitops/) — Delivery patterns your platform enables

---

*"A platform organization's job is to be invisible. When developers don't think about infrastructure, you've succeeded."*
