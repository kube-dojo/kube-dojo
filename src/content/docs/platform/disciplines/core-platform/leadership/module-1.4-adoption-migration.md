---
title: "Module 1.4: Platform Adoption & Migration Strategy"
slug: platform/disciplines/core-platform/leadership/module-1.4-adoption-migration
sidebar:
  order: 5
---
> **Discipline Module** | Complexity: `[ADVANCED]` | Time: 55-65 min

## Prerequisites

Before starting this module:
- **Required**: [Module 1.3: Platform as Product](./module-1.3-platform-as-product/) — Product management, user research, roadmapping
- **Required**: [Module 1.2: Developer Experience Strategy](./module-1.2-developer-experience/) — DX measurement, golden paths
- **Recommended**: [SRE: Toil and Automation](../sre/module-1.4-toil-automation/) — Understanding repetitive work and automation ROI
- **Recommended**: Experience with organizational change or system migrations

---

## What You'll Be Able to Do

After completing this module, you will be able to:

- **Design migration strategies that move teams to the platform incrementally with minimal disruption**
- **Implement adoption tracking dashboards that identify teams struggling with platform onboarding**
- **Build champion programs that turn early adopters into advocates who accelerate platform adoption**
- **Lead organizational change management for platform migrations spanning hundreds of services**

## Why This Module Matters

In 2020, a healthcare technology company mandated that all 35 development teams migrate to their new Kubernetes-based platform within 6 months. They sent an email, set a deadline, and waited.

At the 6-month mark, 8 teams had migrated. The other 27 had not started. Some cited competing priorities. Some were afraid of breaking production during migration. Some had tried and hit blockers that were never resolved. Three teams had quietly built their own deployment systems to avoid the mandate entirely.

The platform team was furious. "We built exactly what they asked for. Why won't they use it?"

The answer was simple: **building a platform and getting people to use it are completely different skills.** The platform was technically sound. The migration strategy was not a strategy at all — it was a deadline with no plan, no support, and no understanding of what migration actually costs the migrating team.

This module teaches you how to drive adoption and manage migrations without mandates, ultimatums, or organizational warfare. You will learn patterns that work and patterns that create resentment.

---

## Did You Know?

> Geoffrey Moore's "Crossing the Chasm" — the seminal book about technology adoption — applies directly to internal platforms. The gap between early adopters (enthusiastic teams who try anything new) and the early majority (pragmatic teams who wait for proof) is where most platform adoption stalls. If you only reach the enthusiasts, you have not succeeded.

> A 2023 survey by the Platform Engineering Community found that **62% of platform teams cite adoption as their biggest challenge** — more than technical complexity (41%), funding (38%), or staffing (35%). Building the platform is the easy part.

> The "strangler fig" pattern — gradually replacing a legacy system by routing traffic to the new system piece by piece — was named by Martin Fowler after the strangler fig tree, which grows around an existing tree and eventually replaces it entirely. It is the safest migration pattern because the old system remains functional throughout.

> Research on organizational change (Kotter, 1995) found that **70% of major change initiatives fail**, usually because leaders underestimate the effort required to change habits. Platform migrations are change initiatives, not technical projects. Treat them accordingly.

---

## Adoption Models: Voluntary vs Mandatory

### The Adoption Spectrum

```
VOLUNTARY ◄─────────────────────────────────────► MANDATORY

  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐
  │ Fully    │  │ Strongly │  │ Opt-out  │  │ Fully    │
  │ Optional │  │ Encour-  │  │ (default │  │ Mandatory│
  │          │  │ aged     │  │  but can  │  │          │
  │ "Use it  │  │ "Here's  │  │  exempt)  │  │ "You    │
  │  if you  │  │  why you │  │           │  │  must    │
  │  want"   │  │  should" │  │ "You're   │  │  use it" │
  │          │  │          │  │  on it    │  │          │
  │          │  │          │  │  unless   │  │          │
  │          │  │          │  │  you opt  │  │          │
  │          │  │          │  │  out"     │  │          │
  └──────────┘  └──────────┘  └──────────┘  └──────────┘

  Low adoption     Sweet spot                 High adoption
  risk-free        for most                   high resentment
                   organizations
```

### When Each Model Is Appropriate

| Model | When to Use | Risks |
|-------|-------------|-------|
| **Fully optional** | New features, experimental capabilities | Low adoption, may never reach critical mass |
| **Strongly encouraged** | Core platform services, golden paths | Some teams will ignore encouragement |
| **Opt-out default** | Security/compliance features, standard tooling | Resentment from teams that want exceptions |
| **Fully mandatory** | Regulatory requirements, security baselines | High resentment, shadow IT, reduced trust |

### The Hybrid Approach (Recommended)

Most successful platforms use a layered model:

```
┌──────────────────────────────────────────┐
│  MANDATORY (guardrails)                   │
│  Security scanning, access controls,      │
│  audit logging, resource limits            │
│  → Enforced by automated policies          │
├──────────────────────────────────────────┤
│  OPT-OUT DEFAULT (strong defaults)        │
│  Standard CI/CD, monitoring, alerting,    │
│  deployment pipeline                       │
│  → Teams use by default, can opt out      │
│    with justification                      │
├──────────────────────────────────────────┤
│  VOLUNTARY (golden paths)                 │
│  Service templates, developer portal,     │
│  advanced features                         │
│  → Teams choose to adopt                   │
└──────────────────────────────────────────┘
```

---

## Migration Patterns

### Pattern 1: Strangler Fig

**How it works**: Gradually route functionality from the old system to the new system. The old system continues to work but handles less and less until it can be decommissioned.

```
Phase 1: New system handles 0%, old handles 100%
┌─────────────────────────────────┐
│ OLD SYSTEM ████████████████████ │  100%
│ NEW SYSTEM                      │    0%
└─────────────────────────────────┘

Phase 2: New system handles 30%, old handles 70%
┌─────────────────────────────────┐
│ OLD SYSTEM ██████████████       │   70%
│ NEW SYSTEM ██████               │   30%
└─────────────────────────────────┘

Phase 3: New system handles 80%, old handles 20%
┌─────────────────────────────────┐
│ OLD SYSTEM ████                 │   20%
│ NEW SYSTEM ████████████████     │   80%
└─────────────────────────────────┘

Phase 4: New system handles 100%, old decommissioned
┌─────────────────────────────────┐
│ OLD SYSTEM                      │    0%
│ NEW SYSTEM ████████████████████ │  100%
└─────────────────────────────────┘
```

**When to use**: Most migrations. Lowest risk. Allows learning and adjustment during migration.

**Platform example**: Migrating from Jenkins to a new CI system. Start by running both in parallel. New services use the new system. Existing services migrate one at a time. Jenkins is decommissioned when the last service migrates.

**Key success factor**: The old system must continue to work reliably while migration is in progress. Do not neglect maintenance of the old system just because you are excited about the new one.

### Pattern 2: Parallel Run

**How it works**: Both systems run simultaneously with the same inputs. Compare outputs to verify the new system is correct before switching.

```
┌──────────┐
│  Input   │
└────┬─────┘
     │
     ├────────────────────────┐
     ▼                        ▼
┌──────────┐           ┌──────────┐
│ OLD      │           │ NEW      │
│ SYSTEM   │           │ SYSTEM   │
│ (primary)│           │ (shadow) │
└────┬─────┘           └────┬─────┘
     │                      │
     ▼                      ▼
┌────────────────────────────────┐
│      COMPARE OUTPUTS           │
│  Match? → Ready to switch      │
│  Mismatch? → Debug new system  │
└────────────────────────────────┘
```

**When to use**: Critical systems where correctness must be verified. Payment processing, data pipelines, authentication.

**Platform example**: Migrating from one monitoring system to another. Run both in parallel. Alert when they disagree. Switch to the new system only when they agree for 30 days.

**Key success factor**: The comparison mechanism must be automated. Manual comparison does not scale.

### Pattern 3: Big Bang

**How it works**: Switch everyone to the new system at once on a specific date.

**When to use**: Almost never. Only when:
- The old system is being decommissioned by a vendor
- Regulatory deadline requires it
- The systems are incompatible and cannot run in parallel
- The migration is simple enough that risk is low

**Risks**: Everything breaks at once. Rollback is difficult or impossible. Every team's workflow is disrupted simultaneously.

**If you must do a big bang**:
- Practice with a full rehearsal in a staging environment
- Have a detailed rollback plan
- Schedule during lowest-traffic period
- Staff extra support for the first week
- Communicate obsessively (daily countdown, what to expect, who to contact)

### Pattern 4: Feature Flag Migration

**How it works**: Use feature flags to gradually shift teams from old to new system. Each team (or percentage of traffic) can be individually toggled.

```
Team A: ──old──→ [flag on] ──new──→
Team B: ──old────────────→ [flag on] ──new──→
Team C: ──old──────────────────────→ [flag on] ──new──→
                                                  │
Time ─────────────────────────────────────────────►
```

**When to use**: Platform services that can be toggled per-team. Deployment pipelines, monitoring integrations, DNS routing.

**Key success factor**: Robust feature flag infrastructure. The ability to quickly toggle back if problems arise.

---

## Dealing with Holdouts and Legacy Teams

### Why Teams Resist Migration

Understanding resistance is the first step to overcoming it. Common reasons:

| Reason | What They Say | What They Mean |
|--------|--------------|----------------|
| **Risk** | "We can't afford downtime" | "I don't trust the new system" |
| **Effort** | "We don't have capacity" | "This is not my team's priority" |
| **Comfort** | "Our current setup works fine" | "I don't want to learn something new" |
| **Bad experience** | "We tried last time and it broke" | "I don't trust your team" |
| **Legitimate concern** | "Our use case is unique" | "Your platform genuinely doesn't support our needs" |
| **Political** | "We need to evaluate options" | "I want to build my own thing" |

### Strategies for Each Type of Resistance

**For risk-averse teams**:
- Offer to do the migration for them (white-glove service)
- Start with a non-critical service as proof
- Provide an instant rollback mechanism
- Share data from other teams' migrations (incidents, downtime)

**For capacity-constrained teams**:
- Build migration tooling that minimizes their effort
- Offer embedded platform engineer support for 1-2 weeks
- Time migration around their lower-pressure periods
- Quantify the ongoing cost of NOT migrating (maintenance burden on old system)

**For comfortable teams**:
- Show them what they are missing (faster deploys, better monitoring)
- Create FOMO through internal marketing (success stories from other teams)
- Do not force them — they will come around when peers demonstrate value

**For teams with bad past experiences**:
- Acknowledge the past failure honestly
- Explain what is different this time (specific changes)
- Offer a trial period with explicit opt-out
- Build trust through small wins before asking for the big migration

**For teams with legitimate concerns**:
- Listen. They may be right.
- Add their use case to the platform roadmap if it affects multiple teams
- If their needs are truly unique, agree on a supported exception path
- Do not pretend the platform supports something it does not

**For politically resistant teams**:
- Escalate to leadership only as a last resort
- Focus on making the platform so good that resistance looks unreasonable
- Find an ally on the resistant team (there is usually one person who wants to migrate)
- Be patient — political resistance dissolves when peer teams succeed visibly

---

## Incentive Design for Adoption

### The Carrot Is Better Than the Stick

Mandates create compliance. Incentives create adoption. The difference matters.

| Approach | Short-term Effect | Long-term Effect |
|----------|-------------------|-----------------|
| **Mandate** | High compliance | Resentment, shadow IT, loss of trust |
| **Deadline** | Urgency | Rushed migrations, quality issues |
| **Incentive** | Moderate initial adoption | Sustained adoption, goodwill |
| **Social proof** | Moderate adoption | Organic growth, peer influence |
| **Making it easy** | High adoption | Permanent behavior change |

### Effective Incentives for Platform Adoption

| Incentive | How It Works | Example |
|-----------|-------------|---------|
| **Reduced toil** | Migrated teams get automation that non-migrated teams don't | "On the new platform, deploys are 1 click. On the old, it's still 12 steps." |
| **Better support** | Platform team prioritizes support for teams on the platform | "Teams on the platform get SLA-backed support. Old system is best-effort." |
| **Featured in demos** | Public recognition for early adopters | Monthly demo day showcases teams using new capabilities |
| **Priority access** | Early adopters get first access to new features | Beta program for platform features |
| **Budget relief** | Old infrastructure costs charged to teams that stay on it | "The old CI system costs $X/month. Migrated teams don't pay." |
| **Removal of friction** | Migrate for them where possible | Automated migration tooling that does 80% of the work |

### The Sunset Strategy

If you need teams off the old system, sunset it gradually:

```
Month 0:  Announce sunset timeline. New system available.
          "Old system supported until Month 12."

Month 3:  Reduce support for old system.
          "Old system: community support only. No SLA."

Month 6:  Stop adding features to old system.
          "No new integrations for old CI. All new work on new CI."

Month 9:  Begin decomissioning old system infrastructure.
          "Old system: read-only access to build history."

Month 12: Decommission old system.
          "Old system offline. Migration assistance available."
```

**Critical rule**: Never decommission the old system before you have migrated (or explicitly exempted) every team. Surprise decommissions destroy trust permanently.

---

## Communication Strategies for Platform Changes

### The Communication Matrix

Different changes require different communication strategies:

| Change Type | Audience | Channel | Timing | Tone |
|------------|----------|---------|--------|------|
| **Breaking change** | All platform users | Email + Slack + meeting | 4+ weeks advance | Serious, detailed |
| **New feature** | All platform users | Slack + changelog + demo | At launch | Excited, practical |
| **Deprecation** | Affected teams directly | Email + Slack DM | 8+ weeks advance | Empathetic, helpful |
| **Incident** | All platform users | Slack #incidents | Real-time | Factual, calm |
| **Roadmap update** | All platform users | Monthly newsletter | Monthly | Strategic, transparent |
| **Migration guide** | Migrating teams | Documentation + workshop | As needed | Step-by-step, supportive |

### The Breaking Change Protocol

Breaking changes are where platform teams lose the most trust. Follow this protocol:

```
Breaking Change Communication Plan
════════════════════════════════════

Week -8: Discovery
  [ ] Identify all affected teams and services
  [ ] Quantify migration effort per team
  [ ] Create migration guide and tooling
  [ ] Identify highest-risk teams

Week -6: Announcement
  [ ] Email to all platform users with:
      - What is changing
      - Why it is changing
      - Who is affected
      - What they need to do
      - Timeline
      - Where to get help
  [ ] Slack announcement in #platform
  [ ] Offer 1:1 meetings with high-risk teams

Week -4: Support
  [ ] Workshop for teams that need help
  [ ] Migration office hours (weekly)
  [ ] Track migration progress per team
  [ ] Identify and unblock stuck teams

Week -2: Final push
  [ ] Contact non-migrated teams directly
  [ ] Offer white-glove migration assistance
  [ ] Confirm rollback plan if needed

Week 0: Change goes live
  [ ] Monitor for issues
  [ ] Rapid response team on standby
  [ ] Post-change verification with affected teams

Week +1: Retrospective
  [ ] Survey affected teams
  [ ] Document lessons learned
  [ ] Update communication template
```

### Managing Organizational Resistance

When resistance is not about technology but about organizational dynamics:

**The ADKAR Model** (a change management framework):

| Stage | Question | Platform Application |
|-------|----------|---------------------|
| **A**wareness | "Do they know why we're changing?" | Explain the business case, not just the tech |
| **D**esire | "Do they want to change?" | Show personal benefit, not just org benefit |
| **K**nowledge | "Do they know how to change?" | Training, documentation, support |
| **A**bility | "Can they actually do it?" | Time, tools, migration assistance |
| **R**einforcement | "Will they stick with it?" | Celebrate wins, remove old system |

**Most platform teams skip Awareness and Desire**, jumping straight to Knowledge ("here's the docs") and Ability ("here's the migration tool"). But if people do not understand why they are changing and do not want to change, knowledge and ability are irrelevant.

---

## Hands-On Exercises

### Exercise 1: Migration Strategy Design (45 min)

Design a migration strategy for a realistic scenario:

**Scenario**: Your organization has 20 development teams using Jenkins (self-hosted). You have built a new CI/CD platform based on GitHub Actions + ArgoCD. You need to migrate all 20 teams.

**Step 1**: Choose a migration pattern
```
Selected pattern: [ ] Strangler Fig  [ ] Parallel Run
                  [ ] Big Bang       [ ] Feature Flag
Justification:
```

**Step 2**: Design the migration timeline
```
Phase 1 (Month 1-2): _______________
  Teams: [which teams and why?]
  Success criteria: _______________

Phase 2 (Month 3-4): _______________
  Teams: [which teams and why?]
  Success criteria: _______________

Phase 3 (Month 5-6): _______________
  Teams: [which teams and why?]
  Success criteria: _______________

Sunset (Month 7-9): _______________
  Old system: _______________
```

**Step 3**: Identify risks
```
Risk 1: _______________
  Mitigation: _______________

Risk 2: _______________
  Mitigation: _______________

Risk 3: _______________
  Mitigation: _______________
```

**Step 4**: Design the communication plan using the breaking change protocol above.

### Exercise 2: Resistance Role Play (30 min)

Practice handling the 6 types of resistance. For each scenario, write your response:

**Scenario A** (risk-averse): "We handle patient data. We can't afford any downtime during migration."
Your response: _______________

**Scenario B** (capacity-constrained): "We're 3 weeks from our product launch. We can't migrate now."
Your response: _______________

**Scenario C** (comfortable): "Our setup works fine. We've been using it for 3 years."
Your response: _______________

**Scenario D** (bad experience): "Last time we migrated to your platform, we had 4 hours of downtime."
Your response: _______________

**Scenario E** (legitimate concern): "We use custom build steps that your new platform doesn't support."
Your response: _______________

**Scenario F** (political): "We've evaluated GitHub Actions and we prefer GitLab CI. We want to use our own."
Your response: _______________

For each response, check:
- [ ] Did you acknowledge their concern?
- [ ] Did you avoid dismissing their feelings?
- [ ] Did you offer a concrete next step?
- [ ] Did you avoid using authority or mandates?

### Exercise 3: Adoption Metrics Dashboard (30 min)

Design a dashboard that tracks platform adoption:

```
PLATFORM ADOPTION DASHBOARD - [Platform Name]
═══════════════════════════════════════════════

Overall Adoption
  Teams on platform: ___/___  (___%)
  Services on platform: ___/___  (___%)
  Deploys via platform (last 30d): ___/___  (___%)

Adoption Trend (weekly)
  Week 1: ___%
  Week 2: ___%
  Week 3: ___%
  Week 4: ___%
  Trend: [ ] Growing  [ ] Flat  [ ] Declining

Migration Health
  Teams migrated this month: ___
  Teams in-progress: ___
  Teams blocked: ___
  Average migration time: ___ days

Adoption by Team
  ┌────────────────┬──────────┬──────────┬──────────┐
  │ Team           │ Status   │ Services │ Blockers │
  ├────────────────┼──────────┼──────────┼──────────┤
  │                │          │          │          │
  └────────────────┴──────────┴──────────┴──────────┘

Satisfaction (migrated teams)
  Overall: ___/5
  Migration experience: ___/5
  Platform reliability: ___/5
  Support quality: ___/5
```

Identify which metrics you would check daily vs weekly vs monthly.

### Exercise 4: ADKAR Assessment (20 min)

For your current or planned platform migration, assess each ADKAR stage:

```
ADKAR Assessment - [Migration Name]
═════════════════════════════════════

AWARENESS (Do teams know why we're changing?)
  Score (1-5): ___
  Evidence: _______________
  Gap: _______________
  Action: _______________

DESIRE (Do teams want to change?)
  Score (1-5): ___
  Evidence: _______________
  Gap: _______________
  Action: _______________

KNOWLEDGE (Do teams know how to change?)
  Score (1-5): ___
  Evidence: _______________
  Gap: _______________
  Action: _______________

ABILITY (Can teams actually do it?)
  Score (1-5): ___
  Evidence: _______________
  Gap: _______________
  Action: _______________

REINFORCEMENT (Will teams stick with it?)
  Score (1-5): ___
  Evidence: _______________
  Gap: _______________
  Action: _______________

Weakest stage: _______________
Priority action: _______________
```

---

## War Story: The Migration That Almost Killed the Platform Team

**Company**: Online marketplace, ~250 engineers, Series E

**Situation**: The platform team had built a new deployment system to replace a 5-year-old homegrown tool called "Ship" that everyone loved but nobody could maintain (the original author had left 2 years ago). The new system was objectively better: faster, more reliable, better monitoring, and built on standard tools (ArgoCD + Kustomize) instead of custom scripts.

**The plan**: Migrate all 18 teams in 4 months. Mandatory.

**What happened**:

**Month 1**: Platform team sent the migration guide (a 23-page document) and a deadline. Three enthusiastic teams migrated in week 1. Two hit blockers (missing features they used in Ship) and filed bugs. One team's migration caused a 2-hour production outage because the new system handled database migrations differently.

**Month 2**: Word of the outage spread. Six teams that had planned to migrate paused "until it's stable." The two teams with blockers were angry — they had migrated in good faith and were now stuck. The platform team was heads-down fixing bugs and had no time for communication.

**Month 3**: Engineering leadership asked for a status update. 5 teams migrated (28%), 2 stuck with blockers, 11 had not started. The CTO was unhappy. The platform team's morale was low. Two platform engineers updated their LinkedIn profiles.

**The pivot**:

The engineering director stepped in and made three changes:

1. **Paused the mandate**: "Nobody is forced to migrate until we fix the blockers and provide proper support."
2. **Assigned a migration buddy**: Each migrating team got a platform engineer embedded for 1 week.
3. **Built automated migration tooling**: A script that converted Ship configs to ArgoCD configs, handling 90% of the work automatically.

**Month 4-5** (after pivot):
- Fixed all blockers from the stuck teams
- Migration buddies helped 6 more teams migrate with zero incidents
- Automated tooling reduced migration effort from 2 weeks to 2 days
- Published success metrics from migrated teams: 60% faster deploys, 40% fewer incidents

**Month 6**: 15 out of 18 teams migrated (83%). The remaining 3 had legitimate edge cases that the platform team was working to support.

**Month 8**: 18/18 teams migrated. Ship was decommissioned. Developer satisfaction with deployment tools: 4.1/5 (up from 3.2/5).

**Business impact**: The 2-month delay cost approximately $400K in engineering time and one platform engineer who left during Month 3. But the forced pause and pivot saved the platform program from failure.

**Lessons**:
1. **Mandates without support are empty threats**: A deadline without migration tooling, embedded support, and fixed blockers is just a date on a calendar
2. **First migrations set the tone**: The outage in Month 1 poisoned adoption for months. Invest heavily in making early migrations flawless
3. **Communication vacuum fills with fear**: When the platform team went silent in Month 2, developers filled the silence with worst-case assumptions
4. **Automated migration tooling is not optional**: If migration takes 2 weeks of developer effort, most teams will not do it voluntarily
5. **Pause and fix is better than push through**: The 2-month pause felt like failure in the moment but saved the program

---

## Knowledge Check

### Question 1
What are the four migration patterns and when is each appropriate?

<details>
<summary>Show Answer</summary>

**Strangler Fig**: Gradually route functionality from old to new system. Use for most migrations — lowest risk, allows incremental learning.

**Parallel Run**: Run both systems simultaneously and compare outputs. Use for critical systems where correctness must be verified (payments, data pipelines).

**Big Bang**: Switch everyone at once on a specific date. Use rarely — only when systems cannot run in parallel or vendor deadlines force it.

**Feature Flag**: Toggle teams individually from old to new using feature flags. Use when the platform service can be switched per-team. Combines the safety of strangler fig with the speed of big bang.

</details>

### Question 2
A team says: "We tried your platform last year and had a 4-hour outage." How do you handle this?

<details>
<summary>Show Answer</summary>

First, **acknowledge the failure honestly**: "You're right, that happened and it shouldn't have. I'm sorry for the impact." Then explain **what changed**: specific improvements, new safeguards, what you learned from that incident. Offer a **low-risk trial**: migrate a non-critical service first, with a guaranteed instant rollback path. Provide **extra support**: embedded platform engineer for their migration. Share **data from recent migrations**: how many teams migrated since then without incidents. Do NOT: dismiss their concern, blame their team, or pretend it didn't happen. Trust is rebuilt through actions, not words.

</details>

### Question 3
Why is "strongly encouraged" usually better than "mandatory" for platform adoption?

<details>
<summary>Show Answer</summary>

"Strongly encouraged" preserves team autonomy while creating strong incentives to adopt. It avoids the negative effects of mandates: resentment, shadow IT, compliance theater, and loss of trust. When adoption is encouraged rather than forced, the feedback you receive is honest ("I'm not using it because X doesn't work") rather than political ("I'll get to it eventually"). It also means that adoption signals genuine value — if 80% of teams voluntarily choose your platform, that proves it's good. If 80% of teams are forced onto it, you have no signal about quality. The exception: security and compliance requirements should be mandatory, enforced by automated guardrails.

</details>

### Question 4
Explain the ADKAR model. Which stage do platform teams most often skip?

<details>
<summary>Show Answer</summary>

ADKAR: **Awareness** (do they know why?), **Desire** (do they want to?), **Knowledge** (do they know how?), **Ability** (can they do it?), **Reinforcement** (will they stick with it?).

Platform teams most often skip **Awareness** and **Desire**. They jump straight to Knowledge ("here's the documentation") and Ability ("here's the migration tool") without establishing why the migration matters and why it benefits the migrating team. Without Awareness, developers see migration as a burden imposed on them. Without Desire, they will procrastinate indefinitely or comply minimally. The fix: start every migration initiative with a clear business case that explains benefits to the migrating team, not just the platform team.

</details>

### Question 5
You're sunsetting an old system. Three teams refuse to migrate with 2 months left on the timeline. What do you do?

<details>
<summary>Show Answer</summary>

Step 1: **Talk to each team individually** to understand their specific blockers. Are they legitimate (missing features, genuine risk) or organizational (inertia, competing priorities)?

Step 2: For legitimate blockers, **extend the timeline for those teams** while you fix the gaps. Breaking things for teams with real concerns destroys trust.

Step 3: For organizational blockers, **reduce migration effort** (automated tooling, embedded support, white-glove service).

Step 4: **Escalate to leadership only if necessary** and only after exhausting support options. Present it as "these teams need prioritization support" not "these teams are non-compliant."

Step 5: **Never decommission until all teams are migrated or explicitly exempted.** Surprise decommissions are the fastest way to destroy platform team credibility.

</details>

### Question 6
Scenario: Your platform has 60% adoption. The remaining 40% are teams with 3+ years of custom infrastructure. What's your strategy?

<details>
<summary>Show Answer</summary>

This is a classic "chasm" problem — you've saturated early adopters and the remaining teams have higher switching costs. Strategy: (1) **Quantify the cost of staying off-platform** for each team: maintenance burden, security risk, operational overhead. Make the invisible cost visible. (2) **Invest in migration tooling** specific to their legacy setup. If migration takes 2 weeks, few will do it. If it takes 2 days, many will. (3) **Offer incremental migration**: don't require all-or-nothing. Can they migrate CI but keep their deployment? Can they use platform monitoring but keep their own deployment pipeline? (4) **Budget conversation**: if the old infrastructure costs are charged to the teams instead of centralized, the business case for migration becomes personal. (5) **Accept that some teams may never migrate** — if their setup works and the cost is acceptable, forced migration may not be worth the political capital.

</details>

### Question 7
What is the strangler fig pattern and why is it the safest migration approach?

<details>
<summary>Show Answer</summary>

The strangler fig pattern gradually replaces a legacy system by routing functionality to the new system piece by piece, while the old system continues to work. It is the safest because: (1) **The old system remains functional** — if the new system fails, traffic routes back. (2) **Issues are discovered incrementally** — problems with 5% of traffic are manageable; problems with 100% of traffic are outages. (3) **Teams migrate at their own pace** — no big-bang coordination required. (4) **Learning happens during migration** — each phase teaches you something for the next. (5) **Rollback is per-component**, not all-or-nothing. Named after the strangler fig tree which grows around an existing tree, gradually replacing it.

</details>

### Question 8
Your platform team built automated migration tooling. Only 3 teams have used it. Why might this be?

<details>
<summary>Show Answer</summary>

Possible reasons: (1) **Teams don't know it exists** — marketing and discoverability problem. (2) **They don't trust it** — no evidence it works safely. Fix by publishing success data from teams that used it. (3) **It doesn't work for their setup** — the tool may only handle common cases and their setup is non-standard. (4) **They haven't allocated time** — even automated migration requires someone to run it, verify, and fix edge cases. (5) **It's hard to use** — the tool itself has poor DX. (6) **They tried it and it failed** — bugs or edge cases broke their confidence. Check your usage analytics: are teams trying the tool and abandoning it (UX/bug problem) or never trying it (awareness/trust problem)?

</details>

---

## Summary

Platform adoption and migration are organizational change challenges, not technical challenges. The technology is the easy part. The hard part is getting people to change their workflows, trust a new system, and invest time in migration.

Key principles:
- **Voluntary beats mandatory**: Incentives create real adoption; mandates create compliance theater
- **Strangler fig is your friend**: Gradual migration beats big bang in almost every case
- **Reduce migration cost obsessively**: If migration is easy, people will do it. If it is hard, they will not.
- **Understand resistance**: There are 6 types, and each needs a different response
- **Communicate proactively**: Silence breeds fear and rumors
- **ADKAR before technical**: Awareness and Desire before Knowledge and Ability
- **Early migrations set the tone**: Invest disproportionately in making the first migrations flawless

---

## What's Next

Continue to [Module 1.5: Scaling Platform Organizations](./module-1.5-scaling-platform-org/) to learn how to grow from a single platform team to a platform organization.

---

*"You can build the best platform in the world, but if nobody migrates to it, you've built nothing."*
