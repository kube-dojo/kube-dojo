# Module 1.5: Incident Management

> **Discipline Module** | Complexity: `[MEDIUM]` | Time: 35-40 min

## Prerequisites

Before starting this module:
- **Required**: [Module 1.1: What is SRE?](module-1.1-what-is-sre.md) — Understanding SRE fundamentals
- **Required**: [Module 1.2: SLOs](module-1.2-slos.md) — Understanding service levels
- **Recommended**: [Observability Theory Track](../../foundations/observability-theory/README.md) — Monitoring and debugging

---

## Why This Module Matters

It's 3 AM. Your phone buzzes. The dashboard is red. Customers are complaining on Twitter.

What do you do?

**Without incident management**: Panic. Random debugging. Blame. Chaos. Hours of downtime.

**With incident management**: Clear roles. Systematic response. Coordinated communication. Resolution.

Incidents will happen. The question is whether you're prepared or not.

This module teaches you how to respond to incidents effectively — minimizing impact, enabling fast recovery, and learning from every failure.

---

## What Is an Incident?

An incident is an unplanned event that:
- Disrupts or degrades service
- Requires immediate response
- Affects users or business operations

Not every alert is an incident. Not every bug is an incident.

### Incident vs. Problem vs. Alert

| Term | Definition | Example |
|------|------------|---------|
| **Alert** | Notification that something might be wrong | "CPU usage above 80%" |
| **Incident** | Active, user-impacting issue requiring response | "Payment processing failing" |
| **Problem** | Root cause of one or more incidents | "Memory leak in payment service" |

An alert might trigger investigation. An incident triggers response. A problem is what you fix to prevent future incidents.

---

## Severity Levels

Not all incidents are equal. Severity levels help you respond appropriately.

### Standard Severity Framework

```
SEV-1 (Critical)
  ├── User impact: Total outage, major feature broken
  ├── Scope: All users affected
  ├── Response: All hands, leadership notified
  └── Example: Complete site down

SEV-2 (High)
  ├── User impact: Significant degradation
  ├── Scope: Many users affected
  ├── Response: On-call team plus escalations
  └── Example: Checkout failing for 50% of users

SEV-3 (Medium)
  ├── User impact: Minor degradation
  ├── Scope: Some users affected
  ├── Response: On-call team handles
  └── Example: Search results slow

SEV-4 (Low)
  ├── User impact: Minimal
  ├── Scope: Few users affected
  ├── Response: Handle during business hours
  └── Example: Admin dashboard unavailable
```

### Severity by SLO Impact

| Severity | Error Budget Impact | Response |
|----------|---------------------|----------|
| SEV-1 | Consuming >100x normal rate | Everyone engaged immediately |
| SEV-2 | Consuming 10-100x normal rate | On-call + escalations |
| SEV-3 | Consuming 2-10x normal rate | On-call investigates |
| SEV-4 | Normal to 2x normal rate | Track, fix when possible |

### Don't Over-Classify

A common mistake is making everything SEV-1. This causes:
- Alert fatigue
- Desensitization to real emergencies
- Resource exhaustion

Be honest about severity. Most incidents are SEV-3 or SEV-4.

---

## Incident Response Roles

Clear roles prevent chaos. Everyone knows their job.

### The Core Roles

```
┌─────────────────────────────────────────────────────────┐
│                 INCIDENT RESPONSE TEAM                   │
├─────────────────────────────────────────────────────────┤
│                                                          │
│    ┌─────────────────────────────────────────────┐      │
│    │          INCIDENT COMMANDER (IC)            │      │
│    │  • Owns overall incident response           │      │
│    │  • Makes decisions, coordinates work        │      │
│    │  • Declares incident resolved               │      │
│    └────────────────────┬────────────────────────┘      │
│                         │                                │
│         ┌───────────────┼───────────────┐               │
│         ▼               ▼               ▼               │
│    ┌─────────┐    ┌─────────┐    ┌─────────┐           │
│    │  COMMS  │    │ TECH    │    │ SUBJECT │           │
│    │  LEAD   │    │ LEAD    │    │ MATTER  │           │
│    │         │    │         │    │ EXPERTS │           │
│    └─────────┘    └─────────┘    └─────────┘           │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

### Role Definitions

**Incident Commander (IC)**
- Overall responsibility for the incident
- Coordinates all response activities
- Makes decisions when needed
- Communicates status to stakeholders
- Declares incident open/closed

**Communications Lead (Comms)**
- External communication (status page, social media)
- Internal communication (leadership, other teams)
- Keeps customers informed
- Handles media if necessary

**Tech Lead**
- Drives technical investigation
- Coordinates debugging efforts
- Recommends and implements fixes
- Documents technical timeline

**Subject Matter Experts (SMEs)**
- Called in based on incident type
- Provide deep expertise in specific areas
- Execute technical tasks under Tech Lead direction

### Role Rotation

The IC doesn't have to be the most senior person. In fact, rotating IC duties:
- Builds incident response skills across team
- Prevents burnout
- Reduces single points of knowledge

---

## Try This: Role-Play an Incident

With your team, practice roles with a mock incident:

```
Scenario: "Payment processing is failing for 30% of transactions"

Assign roles:
  - IC: ______________
  - Comms: ______________
  - Tech Lead: ______________
  - SME (Payments): ______________
  - SME (Database): ______________

Practice:
  1. IC opens incident, assigns roles
  2. Tech Lead begins investigation
  3. Comms drafts status page update
  4. After 5 min, IC requests status update
  5. Practice handoff if IC needs to leave
```

---

## The Incident Lifecycle

Every incident follows a lifecycle:

```
    ┌─────────┐     ┌─────────┐     ┌─────────┐     ┌─────────┐
    │ DETECT  │ ──▶ │ TRIAGE  │ ──▶ │ RESPOND │ ──▶ │ RESOLVE │
    └─────────┘     └─────────┘     └─────────┘     └─────────┘
         │               │               │               │
         ▼               ▼               ▼               ▼
    Monitoring       Severity        Fix/mitigate    Verify
    alerts           assignment      Communication   fixed
    User reports     Role            Coordination    Close
                     assignment                      incident

                               │
                               ▼
                        ┌─────────────┐
                        │  LEARN      │
                        │  (postmortem)│
                        └─────────────┘
```

### Phase 1: Detection

How you learn something is wrong:
- Automated monitoring alerts
- Customer reports
- Internal user reports
- Social media
- Partner notifications

**Goal**: Minimize time to detection (TTD).

### Phase 2: Triage

Quick assessment:
- What's the impact?
- How many users affected?
- What's the severity?
- Who needs to be involved?

**Goal**: Correct severity classification within 5 minutes.

### Phase 3: Response

Active work to resolve:
- Investigation and debugging
- Implementing fixes
- Coordinating across teams
- Communicating status

**Goal**: Effective coordination, not chaos.

### Phase 4: Resolution

Confirming the incident is over:
- Fix deployed and verified
- Monitoring confirms recovery
- Users no longer impacted
- Incident declared resolved

**Goal**: Confident closure, not premature declaration.

### Phase 5: Learning

Post-incident improvement:
- Postmortem conducted (next module)
- Action items identified
- Process improvements made

**Goal**: Never have the same incident twice.

---

## On-Call Best Practices

Being on-call is central to incident management.

### On-Call Structure

```
Primary On-Call
  └── First responder
  └── Available 24/7 during rotation
  └── Handles or escalates all alerts

Secondary On-Call
  └── Backup to primary
  └── Available if primary overwhelmed
  └── Steps in during handoffs

Escalation Path
  └── Manager → Director → VP
  └── For severity or business decisions
  └── Not for technical debugging
```

### Sustainable On-Call

**Do:**
- Maximum 1 week on-call stretches
- Minimum 2 people in rotation
- Compensate for on-call (time off, pay)
- Clear escalation paths
- Runbooks for common issues
- Post-on-call feedback sessions

**Don't:**
- 24/7 on-call for one person
- Alerts for things that aren't actionable
- Expect on-call to also do project work
- Punish people for escalating

### Alert Quality

Good alerts are:
- **Actionable**: Responder can do something
- **Relevant**: Actually indicates a problem
- **Urgent**: Requires immediate attention
- **Clear**: Includes context to start debugging

Bad alerts are:
- "CPU is high" (what should I do?)
- Fires constantly (alert fatigue)
- Requires reading 5 dashboards to understand

### On-Call Metrics

| Metric | Good Target | Why It Matters |
|--------|-------------|----------------|
| Pages per on-call week | < 5 | More = burnout |
| False positive rate | < 20% | Higher = fatigue |
| Time to acknowledge | < 5 min | Faster = faster response |
| Incidents requiring escalation | < 20% | Higher = skill gaps |
| On-call satisfaction | > 3/5 | Lower = retention risk |

---

## Did You Know?

1. **Google's incident management system was inspired by fire department protocols**. The Incident Commander role comes directly from emergency services' Incident Command System (ICS).

2. **The best incident responders often do less, not more**. They focus on coordination and decision-making rather than trying to personally fix everything.

3. **"All hands" incidents often have worse outcomes** than properly staffed responses. Too many people creates confusion and duplicated effort.

4. **PagerDuty's annual "State of On-Call" report** consistently shows that engineers at high-performing organizations get paged less frequently but handle more complex issues—because they've automated away the simple stuff and have better tooling for the hard stuff.

---

## War Story: The Incident That Went Right

A company I worked with had a major outage:

**The Incident:**
- 2:30 AM: Total site down
- Cause: Database corruption from failed migration

**What Made It Go Well:**

**Clear roles activated immediately:**
```
IC: Senior SRE (woken by page)
Comms: Product manager (called in)
Tech Lead: Database engineer (paged)
SME: Migration author (paged)
```

**Structured communication:**
```
2:35 AM: IC opens incident channel
2:40 AM: Comms posts to status page: "Investigating issues"
2:50 AM: Tech Lead: "Identified - database corruption"
3:00 AM: Comms updates status page with ETA
3:30 AM: Database restored from backup
3:45 AM: Site back online
4:00 AM: IC declares incident resolved
```

**What the IC did well:**
- Didn't try to debug personally
- Focused on coordination
- Asked for status every 15 minutes
- Made decision to restore from backup (vs. repair)
- Handled escalation to leadership
- Kept Comms informed for status updates

**The result:**
- 75 minutes total downtime
- Clear communication throughout
- No blame, just focus
- Excellent postmortem material

**Compare to previous incidents:**
- Similar issue 6 months earlier: 4 hours of chaos
- No roles, everyone debugging same thing
- Customers in dark, leadership angry

**Lesson**: Process turns chaos into coordination.

---

## Incident Communication

### Internal Communication

**Incident Channel:**
```
#incident-2024-01-15-payment-outage

[IC] INCIDENT OPEN - SEV-1 - Payment processing failing
[IC] Roles: IC=@alice, Tech=@bob, Comms=@carol
[Tech] Investigating. Initial data shows DB connection failures.
[Comms] Status page updated. ETA 30 min.
[Tech] Root cause identified: Connection pool exhausted
[Tech] Implementing fix: Increasing pool size
[IC] 15-min check: Fix deploying, ETA 10 more minutes
[Tech] Fix deployed. Monitoring.
[IC] Metrics recovering. Watching for 10 minutes.
[IC] INCIDENT RESOLVED - Total duration: 45 minutes
```

**Key Practices:**
- One channel per incident
- All decisions documented
- Regular IC status updates
- Clear open/close announcements

### External Communication

**Status Page Updates:**

```
[INVESTIGATING] 2:45 PM
We are investigating reports of payment processing issues.
Some customers may experience failures when completing checkout.
Next update in 15 minutes.

[IDENTIFIED] 3:00 PM
We have identified the cause and are implementing a fix.
Affected: Payment processing
ETA: 15 minutes
Next update in 15 minutes.

[MONITORING] 3:20 PM
A fix has been deployed. We are monitoring for recovery.
Some transactions may have failed during this period.
Affected transactions will be automatically retried.

[RESOLVED] 3:35 PM
Payment processing has fully recovered.
The issue was caused by a configuration error.
No customer data was affected.
We apologize for the inconvenience.
```

**Principles:**
- Update regularly (every 15-30 min)
- Be honest about what you know
- Give ETAs when you can
- Acknowledge customer impact
- Avoid blame or technical jargon

### Communication Protocols for Major Incidents

During a major incident, unstructured communication causes almost as much damage as the outage itself. These protocols keep everyone informed without overwhelming responders.

**Communication Cadence by Severity:**

| Severity | Internal Update Cadence | Status Page Cadence | Leadership Notification |
|----------|------------------------|--------------------|-----------------------|
| SEV-1 | Every 15 minutes | Every 15 minutes | Immediately, then every 30 min |
| SEV-2 | Every 30 minutes | Every 30 minutes | Within 30 min, then hourly |
| SEV-3 | Every 60 minutes | As status changes | Daily summary if prolonged |
| SEV-4 | As status changes | Not required | Not required |

Even if nothing has changed, post an update. Silence breeds anxiety and speculation.

**Stakeholder Notification Tiers:**

```
Tier 1: Engineering (immediate)
  └── On-call team, incident responders, relevant SMEs
  └── Notified via: PagerDuty, incident Slack channel

Tier 2: Engineering Management (within 15 min for SEV-1)
  └── Engineering managers, directors of affected services
  └── Notified via: Slack, email

Tier 3: Executives (within 30 min for SEV-1)
  └── VP Engineering, CTO, CEO (for customer-facing SEV-1)
  └── Notified via: SMS, phone call, email
  └── They need: impact scope, ETA, whether customers are affected

Tier 4: Customers (within 30-60 min for SEV-1)
  └── Via status page, in-app banner, email for affected accounts
  └── They need: what's broken, workarounds, when it will be fixed
```

**Communication Templates:**

Use these as starting points. The Comms Lead fills in the brackets and posts.

```
INITIAL NOTIFICATION (internal):
"[SEVERITY] incident declared. [SERVICE] is [IMPACT DESCRIPTION].
Approximately [NUMBER/PERCENTAGE] of users affected.
IC: @[NAME] | Tech Lead: @[NAME] | Comms: @[NAME]
Incident channel: #incident-[DATE]-[SHORT-NAME]
Next update in [15/30] minutes."

STATUS UPDATE (internal, use at each cadence interval):
"Update [NUMBER] — [TIME]
Current status: [investigating / identified / fix in progress / monitoring]
What we know: [1-2 sentences]
What we're doing: [current action]
ETA to resolution: [estimate or 'unknown']
Next update in [15/30] minutes."

STATUS PAGE UPDATE (external, customer-facing):
"We are aware of an issue affecting [SERVICE/FEATURE].
Impact: [PLAIN-LANGUAGE DESCRIPTION of what users experience].
Our team is actively working on a resolution.
ETA: [estimate or 'We will provide an update by TIME'].
We apologize for the inconvenience."

RESOLUTION NOTIFICATION (external):
"The issue affecting [SERVICE] has been resolved as of [TIME].
Duration: [START] to [END].
[Brief root cause in plain language, no internal jargon].
[Any actions customers need to take, e.g., retry failed transactions].
We apologize for the disruption and are taking steps to prevent recurrence."
```

**War Room / Bridge Call Protocols:**

For SEV-1 incidents, a bridge call (video or voice) keeps responders aligned.

| Rule | Why |
|------|-----|
| IC opens and runs the bridge | Single point of coordination |
| Mute when not speaking | Reduce noise so updates are heard |
| Tech Lead gives status every 15 min | Keeps IC informed without IC asking repeatedly |
| Non-responders stay off the bridge | Too many people creates chaos (use the Slack channel instead) |
| All decisions spoken aloud and typed in channel | Creates written record, avoids "I thought we said..." |
| Handoff protocol when IC rotates | Outgoing IC summarizes state, incoming IC confirms |

**Post-Incident Customer Communication:**

After resolution, customers deserve a follow-up — especially for SEV-1 and SEV-2 incidents.

- **Within 24 hours**: Post a brief summary on the status page explaining what happened and what you are doing to prevent recurrence.
- **Within 3-5 business days**: For major incidents, send a detailed post-incident report to affected customers. Include root cause, timeline, impact scope, and concrete remediation steps.
- **Tone**: Honest, accountable, specific. Avoid vague language like "an issue occurred." Instead: "A misconfigured database failover caused payment processing to fail for 45 minutes."
- **Don't over-promise**: Say "we are implementing X and Y to reduce the likelihood of recurrence" rather than "this will never happen again."

Customers remember how you communicated during an outage more than the outage itself. Transparent, timely communication builds trust even when things break.

---

## Runbooks and Playbooks

Runbooks reduce time to resolution by documenting common procedures.

### Runbook Example

```markdown
# Runbook: Payment Service High Error Rate

## Trigger
Alert: payment-service-error-rate-high
Threshold: Error rate > 5% for 5 minutes

## Impact
Users unable to complete purchases.
Business impact: ~$X per minute of outage.

## Quick Diagnosis
1. Check payment-service dashboard: [link]
2. Check dependent services:
   - Database: [link]
   - Payment gateway: [link]
   - Auth service: [link]

## Common Causes & Fixes

### Database Connection Exhaustion
**Symptoms**: Connection timeout errors in logs
**Fix**:
```bash
kubectl rollout restart deployment/payment-service -n production
```
**If doesn't resolve**: Check database load, may need failover

### Payment Gateway Outage
**Symptoms**: Gateway timeout errors in logs
**Verify**: Check gateway status page: [link]
**Fix**: Enable fallback payment processor:
```bash
kubectl set env deployment/payment-service GATEWAY=fallback
```

### Auth Service Degradation
**Symptoms**: Auth timeout errors in logs
**Verify**: Check auth service dashboard: [link]
**Fix**: Auth service team owns resolution. Escalate to #auth-team

## Escalation
- If not resolved in 15 min: Page secondary on-call
- If not resolved in 30 min: Page engineering manager
- For business decisions: Contact VP on-call

## Post-Resolution
1. Verify metrics returned to normal
2. Create incident ticket in Jira
3. Schedule postmortem if SEV-2 or higher
```

### Playbook vs. Runbook

| Runbook | Playbook |
|---------|----------|
| Specific procedure | General strategy |
| Step-by-step | Principles and patterns |
| For specific alert/issue | For types of incidents |
| "How to fix X" | "How to approach category" |

Both are valuable. Runbooks for common issues, playbooks for novel situations.

---

## Common Mistakes

| Mistake | Problem | Solution |
|---------|---------|----------|
| Everyone debugging | Duplicated effort, chaos | Assign roles, coordinate |
| No communication | Customers angry, leadership blind | Comms role, regular updates |
| Premature resolution | Problem returns, erodes trust | Verify with metrics |
| Over-escalating | Leadership fatigue, cry wolf | Calibrate severity accurately |
| Under-escalating | Major incident unaddressed | Clear escalation criteria |
| No postmortem | Same incident recurs | Always do postmortems for SEV-1/2 |

---

## Quiz: Check Your Understanding

### Question 1
You receive an alert that API error rate is at 3% (normally 0.1%). How do you triage this?

<details>
<summary>Show Answer</summary>

**Triage Steps:**

1. **Check impact scope**: How many users affected?
2. **Check trend**: Is it getting worse?
3. **Check error types**: 4xx vs 5xx matters
4. **Check dependencies**: Are upstream/downstream services healthy?

**Severity assessment**:
- If 3% and stable, many users affected → SEV-2 or SEV-3
- If 3% and climbing rapidly → SEV-2, may escalate to SEV-1
- If mostly 4xx (client errors) → Maybe SEV-3 or SEV-4
- If mostly 5xx (server errors) → More serious

**Decision**: Classify severity, assign roles if SEV-2+, start investigation.

</details>

### Question 2
What's the IC's main job during an incident?

<details>
<summary>Show Answer</summary>

The IC's main jobs are:

1. **Coordinate**: Ensure roles are assigned and working together
2. **Decide**: Make calls when team is stuck or needs direction
3. **Communicate**: Keep stakeholders informed
4. **Manage scope**: Keep team focused on resolution

What the IC should NOT do:
- Personal debugging (that's Tech Lead)
- External communication (that's Comms)
- Get lost in technical details

The IC is the conductor, not the musician.

</details>

### Question 3
An incident is taking longer than expected. When should you escalate?

<details>
<summary>Show Answer</summary>

Escalate when:

1. **Time thresholds exceeded**: As defined in runbook (e.g., 30 min for SEV-1)
2. **Expertise needed**: Current team lacks skills
3. **Business decisions required**: Need authority to approve risky fix
4. **Scope expansion**: Incident affecting more than originally thought
5. **Customer impact increasing**: Despite mitigation efforts

How to escalate well:
- Summarize situation clearly
- State what you need from escalation
- Don't wait too long (bias toward early escalation)

</details>

### Question 4
How often should you update the status page during an incident?

<details>
<summary>Show Answer</summary>

**Recommended cadence:**

- **During active incident**: Every 15-30 minutes
- **When status changes**: Immediately (investigating → identified → fix deployed)
- **At resolution**: Clear resolution message

**Key principles**:
- Regular updates even if no change ("still investigating")
- Honest about what you know and don't know
- Give ETAs when you can (but don't overpromise)
- Acknowledge customer impact

Silence is worse than "we're still working on it."

</details>

---

## Hands-On Exercise: Build an Incident Response Plan

Create an incident response plan for your team.

### Part 1: Severity Definition

Define your severity levels:

```yaml
severity_levels:
  sev1:
    name: "Critical"
    criteria:
      - # What makes an incident SEV-1?
    response:
      - # Who is paged?
      - # Response time target?
    examples:
      - # Real examples from your systems

  sev2:
    name: "High"
    criteria:
      -
    response:
      -
    examples:
      -

  sev3:
    name: "Medium"
    criteria:
      -
    response:
      -
    examples:
      -
```

### Part 2: Role Assignments

Define who fills each role:

```yaml
roles:
  incident_commander:
    primary: # Who is first IC?
    rotation: # Who rotates?
    responsibilities:
      -
      -

  communications_lead:
    primary:
    backup:
    responsibilities:
      -

  tech_lead:
    primary:
    responsibilities:
      -
```

### Part 3: Communication Templates

Create templates for status updates:

```markdown
## Status Page Template: Investigating

We are investigating reports of [ISSUE].

**Impact**: [WHO IS AFFECTED]
**Current status**: Investigating
**Next update**: [TIME]

---

## Status Page Template: Identified

We have identified the cause of [ISSUE] and are working on a fix.

**Impact**: [WHO IS AFFECTED]
**Root cause**: [HIGH-LEVEL DESCRIPTION]
**ETA**: [ESTIMATED TIME]
**Next update**: [TIME]

---

## Status Page Template: Resolved

[ISSUE] has been resolved.

**Duration**: [START TIME] to [END TIME]
**Impact**: [SUMMARY]
**Root cause**: [BRIEF EXPLANATION]

We apologize for any inconvenience.
```

### Part 4: Runbook Outline

Create a runbook template:

```markdown
# Runbook: [Alert Name]

## Overview
- Alert threshold:
- Impact when triggered:

## Quick Diagnosis
1.
2.
3.

## Common Causes
### Cause 1: [Name]
- Symptoms:
- Fix:

### Cause 2: [Name]
- Symptoms:
- Fix:

## Escalation
- If not resolved in X min:
- For business decisions:
```

### Success Criteria

- [ ] Defined all severity levels with examples
- [ ] Assigned roles with backups
- [ ] Created communication templates
- [ ] Started at least one runbook

---

## Key Takeaways

1. **Incidents need structure**: Roles, severity, process prevent chaos
2. **The IC coordinates, doesn't debug**: Focus on the whole response
3. **Communication is critical**: Internal and external, regular updates
4. **Runbooks save time**: Document common issues and fixes
5. **Sustainable on-call**: Reasonable load, compensation, clear escalation

---

## Further Reading

**Books**:
- **"Site Reliability Engineering"** — Chapter 14: Managing Incidents
- **"Incident Management for Operations"** — Rob Schnepp

**Articles**:
- **"Incident Response at Heroku"** — Heroku engineering blog
- **"On Being On-Call"** — Alice Goldfuss

**Tools**:
- **PagerDuty**: Incident management platform
- **OpsGenie**: Alerting and on-call management
- **Incident.io**: Incident response in Slack

---

## Summary

Incident management is what happens when things go wrong — and things will go wrong.

Effective incident management:
- Clear roles (IC, Comms, Tech Lead, SMEs)
- Defined severity levels
- Structured response process
- Regular communication
- Documented runbooks

Without it, incidents are chaos. With it, incidents are manageable.

---

## Next Module

Continue to [Module 1.6: Postmortems and Learning](module-1.6-postmortems.md) to learn how to learn from incidents and prevent recurrence.

---

*"Every great outage tells a story. Make sure you're listening."* — Unknown
