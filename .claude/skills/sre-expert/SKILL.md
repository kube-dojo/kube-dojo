---
name: sre-expert
description: SRE discipline knowledge. Use for Site Reliability Engineering, SLOs, error budgets, incident management, toil elimination. Triggers on "SRE", "reliability", "SLO", "error budget", "on-call".
---

# SRE Expert Skill

Authoritative knowledge source for Site Reliability Engineering principles, practices, and implementation. Based on Google SRE books, industry best practices, and real-world experience.

## When to Use
- Writing or reviewing SRE curriculum content
- Answering questions about SRE practices
- Designing SLO/SLI frameworks
- Incident management and postmortem guidance
- Toil identification and elimination strategies

## Core SRE Principles

### The SRE Philosophy

SRE is "what happens when you ask a software engineer to design an operations function." Key tenets:

1. **Reliability is THE feature** - Nothing else matters if users can't use your service
2. **Error budgets enable velocity** - Quantify acceptable risk to balance reliability and innovation
3. **Toil is the enemy** - Automate repetitive work, measure and eliminate toil
4. **Embrace risk** - 100% reliability is wrong target; define acceptable failure
5. **Shared ownership** - Developers and SREs share production responsibility

### The 50% Rule
SREs should spend:
- **≤50%** on operational work (toil)
- **≥50%** on engineering work (automation, tooling, reliability improvements)

If toil exceeds 50%, either automate or push back to development teams.

## Service Level Hierarchy

### SLI (Service Level Indicator)
A quantitative measure of service behavior.

**Good SLIs are:**
- User-facing and meaningful
- Measurable and aggregatable
- Comparable over time

**Common SLI Types:**

| Category | SLI Examples |
|----------|--------------|
| Availability | % of successful requests |
| Latency | p50, p95, p99 response times |
| Throughput | Requests per second |
| Correctness | % of correct responses |
| Freshness | Age of data served |

### SLO (Service Level Objective)
Target value for an SLI over a time window.

**SLO Formula:**
```
SLI ≥ SLO target over time window
Example: 99.9% of requests succeed over 30 days
```

**Choosing SLO Targets:**
- Start with what you can measure
- Consider user expectations (not internal goals)
- Account for dependencies (you can't be more reliable than your deps)
- Leave headroom (don't set SLO at current performance)

### SLA (Service Level Agreement)
Business contract with consequences for missing targets.

**SLA < SLO always.** Your SLO should be tighter than your SLA to provide buffer.

```
                    ┌─────────────────────────────┐
                    │         100% uptime         │  ← Impossible
                    ├─────────────────────────────┤
                    │          SLO 99.95%         │  ← Internal target
                    ├─────────────────────────────┤
                    │          SLA 99.9%          │  ← Customer contract
                    └─────────────────────────────┘
```

## Error Budgets

### The Error Budget Concept
Error budget = 1 - SLO target

**Example:**
- SLO: 99.9% availability
- Error budget: 0.1% (43.2 minutes/month)

### Error Budget Policy

When budget is healthy (>50% remaining):
- Ship features aggressively
- Experiment and take calculated risks
- Focus on velocity

When budget is depleted (<0 remaining):
- Freeze non-critical changes
- Focus on reliability improvements
- Conduct postmortems for all incidents
- Increase testing and review requirements

### Error Budget Calculation

```
Monthly error budget (minutes) = 30 days × 24 hours × 60 min × (1 - SLO)

99.9% SLO = 43.2 minutes/month
99.95% SLO = 21.6 minutes/month
99.99% SLO = 4.32 minutes/month
```

## Toil

### What is Toil?
Toil is manual, repetitive, automatable work that:
- Scales linearly with service size
- Has no enduring value
- Is reactive rather than proactive
- Interrupts higher-value work

### Toil Examples

| Toil | Not Toil |
|------|----------|
| Manual deployments | Building deployment automation |
| Ticket-driven config changes | Writing self-service tooling |
| Manual log analysis | Building alerting/dashboards |
| Restarting stuck processes | Fixing root cause |
| Manual capacity provisioning | Implementing autoscaling |

### Toil Budget
- Measure toil hours per person per week
- Target: <2 hours/day (50% rule)
- Track trends over time
- Prioritize automation by toil-hours saved

## Incident Management

### Incident Response Roles

| Role | Responsibility |
|------|----------------|
| Incident Commander (IC) | Overall coordination, communication |
| Operations Lead | Hands-on debugging and mitigation |
| Communications Lead | Status updates, stakeholder comms |
| Planning Lead | Track actions, handoffs, documentation |

### Incident Severity Levels

| Severity | Impact | Response |
|----------|--------|----------|
| SEV1 | Service down, revenue impact | All hands, exec notification |
| SEV2 | Major degradation | On-call + backup |
| SEV3 | Minor degradation | On-call only |
| SEV4 | Potential issue | Next business day |

### Blameless Postmortems

**Required Sections:**
1. **Summary** - What happened, impact, duration
2. **Timeline** - Detailed sequence of events
3. **Root Cause** - Technical explanation (5 Whys)
4. **Impact** - Users affected, revenue impact, SLO burn
5. **Action Items** - Concrete improvements with owners and dates
6. **Lessons Learned** - What we learned, what went well

**Postmortem Culture:**
- Blameless: Focus on systems, not individuals
- Assume good intent
- Share widely (learn from each other)
- Track action item completion

## On-Call

### On-Call Best Practices

**Load Management:**
- Max 2 incidents per shift
- Target: 25% of on-call time actively working
- Compensatory time off after heavy shifts

**Rotation Design:**
- Minimum 2 people per rotation
- Primary/secondary structure
- Follow-the-sun for global teams
- Regular rotation (weekly or bi-weekly)

**Runbooks:**
Every alert should have:
- What the alert means
- How to diagnose
- How to mitigate
- When to escalate

### Alert Quality

**Good Alerts:**
- Actionable (someone needs to do something)
- Urgent (needs attention now)
- Symptomatic (represents user-facing impact)
- Complete (includes context and runbook link)

**Alert Anti-patterns:**
- Alerts with no action → convert to dashboards
- Frequent false positives → tune thresholds
- Alerts ignored → delete or fix
- Low-urgency alerts → batch or automate

## Capacity Planning

### The Four Golden Signals

| Signal | What to Measure |
|--------|-----------------|
| Latency | Request duration (distinguish success/failure) |
| Traffic | Requests per second, concurrent users |
| Errors | Error rate (5xx, timeouts, business errors) |
| Saturation | Resource utilization (CPU, memory, disk, connections) |

### Capacity Planning Process

1. **Measure** current utilization
2. **Model** growth (organic + planned launches)
3. **Forecast** when capacity is needed
4. **Provision** ahead of demand
5. **Validate** predictions vs reality

### Load Testing

- Test at 2x expected peak
- Include failure scenarios
- Validate autoscaling behavior
- Test dependencies under load

## Reliability Patterns

### Redundancy Levels

| Level | Description | Example |
|-------|-------------|---------|
| N+1 | One spare | 3 replicas for 2 needed |
| N+2 | Two spares | Geographic redundancy |
| 2N | Full duplicate | Active-active datacenters |
| 2N+1 | Full duplicate + spare | Critical systems |

### Failure Domains

Distribute workloads across:
- Availability zones
- Regions
- Cloud providers (for critical systems)

### Graceful Degradation

When overloaded:
1. Shed low-priority traffic
2. Serve cached/stale data
3. Disable non-essential features
4. Return fast errors over slow responses

## Key Books & Resources

- **Site Reliability Engineering** (Google SRE Book) - The foundational text
- **The Site Reliability Workbook** - Practical implementation guide
- **Seeking SRE** - Essays from practitioners
- **Implementing Service Level Objectives** - Alex Hidalgo's deep dive

## SRE vs DevOps

| Aspect | SRE | DevOps |
|--------|-----|--------|
| Focus | Reliability | Delivery velocity |
| Metrics | SLOs, error budgets | Deployment frequency |
| Approach | Prescriptive practices | Cultural movement |
| Origin | Google (2003) | Community (2008) |
| Relationship | SRE implements DevOps principles |

*"Hope is not a strategy. SRE makes reliability engineering explicit."*
