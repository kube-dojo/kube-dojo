---
title: "Module 1.2: Developer Experience Strategy"
slug: platform/disciplines/leadership/module-1.2-developer-experience
sidebar:
  order: 3
---
> **Discipline Module** | Complexity: `[ADVANCED]` | Time: 55-65 min

## Prerequisites

Before starting this module:
- **Required**: [Module 1.1: Building Platform Teams](./module-1.1-platform-team-building/) — Team structures and organizational design
- **Required**: [Engineering Leadership Track](../../foundations/engineering-leadership/) — Stakeholder communication and ADRs
- **Recommended**: [SRE: Service Level Objectives](../sre/module-1.2-slos/) — Measuring outcomes with SLIs/SLOs
- **Recommended**: Experience using internal developer platforms (as a consumer)

---

## Why This Module Matters

In 2022, a large retail company invested $4 million in a new Kubernetes-based internal developer platform. Eighteen months later, their internal developer satisfaction survey showed a 15-point *drop*. Developers complained about longer deploy times, more YAML to write, and a steeper learning curve. The platform was technically superior to what it replaced, but the developer experience was worse.

The platform team had optimized for the wrong thing. They built a technically elegant abstraction layer, but every interaction with it required developers to understand Kubernetes concepts they did not care about. The "self-service" portal required 47 clicks to deploy a service. The documentation assumed familiarity with Helm charts.

**Developer experience is not about technology. It is about how it feels to get your work done.** The best platform in the world is worthless if developers dread using it. This module teaches you to measure, design, and continuously improve the experience your platform provides.

---

## Did You Know?

> A 2023 study by DX (formerly the Developer Experience Lab at the University of Victoria) found that developers spend only **52 minutes per day** in a state of deep focus. The rest is consumed by context switching, waiting for builds, searching for documentation, and navigating internal tools. Platform teams that reduce these interruptions have disproportionate impact.

> **GitHub's research** found that developer satisfaction is a stronger predictor of retention than compensation. Developers who rate their tools and processes positively are **2.3x less likely to leave** within a year, even controlling for salary.

> The concept of "cognitive load" in software teams comes from educational psychology. John Sweller's Cognitive Load Theory (1988) was about classroom learning, but it maps perfectly to developer experience: every unnecessary concept a developer must hold in working memory reduces their ability to do their actual job.

> **Google's internal research** (published via DORA) found that elite-performing teams deploy **973x more frequently** than low performers, with **6,570x faster lead time**. The difference is almost entirely in tooling and process, not individual skill.

---

## Measuring Developer Experience

### The Measurement Trap

Most organizations measure developer experience badly. They either:
1. **Don't measure at all**: "We'll know it when we see it"
2. **Measure the wrong things**: Lines of code, number of deploys, tickets closed
3. **Measure too infrequently**: Annual survey that's outdated by the time results arrive
4. **Measure without acting**: Dashboards nobody looks at

You need a multi-layered approach that combines quantitative metrics with qualitative signals.

### DORA Metrics: The Industry Standard

The DevOps Research and Assessment (DORA) team identified four key metrics that predict software delivery performance:

| Metric | What It Measures | Elite | High | Medium | Low |
|--------|-----------------|-------|------|--------|-----|
| **Deployment Frequency** | How often you deploy to production | On-demand (multiple/day) | Weekly to monthly | Monthly to 6-monthly | Fewer than 6-monthly |
| **Lead Time for Changes** | Time from commit to production | Less than 1 hour | 1 day to 1 week | 1 week to 1 month | 1 to 6 months |
| **Change Failure Rate** | % of deployments causing failure | 0-15% | 16-30% | 16-30% | 16-30% |
| **Failed Deployment Recovery Time** | Time to restore service | Less than 1 hour | Less than 1 day | 1 day to 1 week | More than 6 months |

**How to use DORA for platform teams**:
- Track these metrics **per team**, not just org-wide
- Compare teams **on your platform** vs teams **not on your platform**
- If platform teams perform worse on DORA metrics, your platform is a liability
- Set improvement targets: "Teams on our platform will achieve High DORA performance within 6 months"

### SPACE Framework: Beyond Speed

DORA metrics focus on delivery speed. The SPACE framework (from Microsoft Research, GitHub, and University of Victoria) captures a fuller picture:

| Dimension | What It Measures | Example Metrics |
|-----------|-----------------|-----------------|
| **S**atisfaction | How happy developers are | Survey: "How satisfied are you with our deployment process?" (1-5) |
| **P**erformance | Outcomes of work | Code review quality, incident reduction, feature completion |
| **A**ctivity | Volume of work | Deploys, commits, PRs merged (careful — easy to game) |
| **C**ommunication | Collaboration quality | PR review turnaround, knowledge sharing, doc contributions |
| **E**fficiency | Flow and minimal friction | Build time, deploy time, time waiting for reviews |

**The SPACE principle**: Never use fewer than 3 dimensions. Any single metric can be gamed or misinterpreted. Triangulate.

### Developer Surveys: The Qualitative Layer

Surveys catch what metrics miss. Run them quarterly (not annually) with a mix of:

**Quantitative questions** (track trends over time):
```
On a scale of 1-5, how would you rate:
[ ] Ease of deploying a new service
[ ] Quality of platform documentation
[ ] Speed of getting help when stuck
[ ] Overall satisfaction with developer tools
[ ] Confidence that deploys won't break production
```

**Qualitative questions** (discover unknown problems):
```
1. What's the most frustrating part of your development workflow?
2. If you could change one thing about our platform, what would it be?
3. What do you spend too much time on that should be automated?
4. What's something that works well that we should protect?
```

**Net Promoter Score for platforms**:
```
On a scale of 0-10, how likely are you to recommend our platform
to a colleague at another company?
```

A platform NPS below 30 means you have serious problems. Above 50 is excellent.

---

## Golden Paths vs Guardrails vs Mandates

This is the single most important strategic decision for developer experience: how much freedom do developers have?

### The Spectrum

```
FREEDOM ◄──────────────────────────────────────► CONTROL

   ┌─────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐
   │ No       │  │ Golden   │  │ Guard-   │  │ Mandates │
   │ Platform │  │ Paths    │  │ rails    │  │          │
   │          │  │          │  │          │  │          │
   │ Teams    │  │ Best way │  │ Must     │  │ Must use │
   │ choose   │  │ is easy, │  │ stay     │  │ exactly  │
   │ every-   │  │ but not  │  │ within   │  │ this     │
   │ thing    │  │ required │  │ bounds   │  │ tool/way │
   └─────────┘  └──────────┘  └──────────┘  └──────────┘

   Chaos           Sweet           Compliance
   at scale        Spot            theater
```

### Golden Paths: The Recommended Approach

A golden path is an **opinionated, well-supported, and easy default** that developers can choose to follow. It is not mandatory, but it is clearly the path of least resistance.

**What makes a good golden path**:
- **Faster than the alternative**: If the golden path is slower, nobody will use it
- **Well-documented**: Clear guides, examples, and troubleshooting
- **Supported**: If something goes wrong on the golden path, the platform team helps
- **Opinionated**: Makes decisions for you (language, framework, deploy target, monitoring)
- **Escapable**: You can go off-path if you have a good reason

**Example: Golden path for a new microservice**

```
┌─────────────────────────────────────────────────────┐
│            GOLDEN PATH: New Microservice             │
│                                                     │
│  1. Run: `platform create service --name my-svc`    │
│     → Scaffolds repo, CI/CD, Dockerfile, k8s manifests│
│                                                     │
│  2. Write your business logic in src/               │
│     → Framework, logging, metrics pre-configured    │
│                                                     │
│  3. Push to main                                    │
│     → Auto: lint, test, build, deploy to staging    │
│                                                     │
│  4. Merge PR                                        │
│     → Auto: canary deploy to production             │
│                                                     │
│  Time from "I have an idea" to "It's in prod":      │
│  < 2 hours (vs 2 weeks without golden path)         │
└─────────────────────────────────────────────────────┘
```

### Guardrails: Non-Negotiable Boundaries

Guardrails are constraints that prevent teams from doing dangerous or unsupportable things. Unlike golden paths, guardrails are mandatory.

| Guardrail | Rationale | Implementation |
|-----------|-----------|----------------|
| All containers must have resource limits | Prevents noisy neighbor problems | Admission controller (OPA/Kyverno) |
| All services must expose health endpoints | Required for reliable deployments | CI pipeline check |
| No public S3 buckets | Security requirement | IAM policy + automated scanner |
| All services must have at least 2 replicas in prod | Availability requirement | Deployment validation webhook |
| Secrets must come from vault, not env vars | Security baseline | CI check + runtime policy |

**The key principle**: Guardrails should be **automated**, not documented. If a guardrail exists only in a wiki, it is not a guardrail — it is a suggestion.

### Mandates: Use Sparingly

Mandates are hard requirements: "You must use this specific tool/process." They should be rare and have clear justification.

**When mandates are appropriate**:
- Regulatory compliance (SOC 2, HIPAA, PCI-DSS)
- Security requirements (authentication, encryption)
- Operational necessities (monitoring, logging in a standard format)
- Cost control (approved instance types, regions)

**When mandates backfire**:
- "Everyone must use Go" (kills innovation, frustrates teams)
- "All services must use our custom framework" (creates vendor lock-in to your own platform)
- "No exceptions to the deployment process" (blocks teams with legitimate edge cases)

---

## Self-Service Platforms: What Developers Actually Want

### The Self-Service Maturity Model

| Level | Description | Developer Experience |
|-------|-------------|---------------------|
| **0: Manual** | File a ticket, wait for someone | "I submitted a request 3 days ago..." |
| **1: Documented** | Follow a wiki guide, run scripts yourself | "I followed the guide but step 7 is outdated" |
| **2: Templated** | Use a template/scaffold, some manual steps | "I scaffolded the project but had to edit 5 files" |
| **3: Self-service** | Click a button or run a command, everything provisioned | "I ran one command and I'm deploying" |
| **4: Automated** | It happens without developer action | "I merged my PR and it's live in 5 minutes" |

**Most platform teams overestimate where they are.** They think they are at Level 3 but developers experience Level 1.

### What Developers Actually Want (Based on Research)

The Platform Engineering community surveyed over 4,000 developers. Here is what they want, ranked:

| Rank | Capability | % of Developers |
|------|-----------|-----------------|
| 1 | Fast, reliable CI/CD | 89% |
| 2 | Easy environment provisioning (dev, staging, prod) | 78% |
| 3 | Clear documentation and examples | 74% |
| 4 | Self-service database/storage provisioning | 68% |
| 5 | Standardized monitoring and logging | 65% |
| 6 | Secret management | 61% |
| 7 | Service catalog (what exists, who owns it) | 58% |
| 8 | Cost visibility | 42% |

Notice what is **not** on this list: advanced service mesh, custom Kubernetes operators, or sophisticated multi-cloud abstraction. Developers want the basics to work well before you build anything fancy.

### Reducing Cognitive Load

Cognitive load is the mental effort required to use your platform. There are three types:

| Type | Definition | Platform Example |
|------|-----------|-----------------|
| **Intrinsic** | Inherent complexity of the task | "Distributed systems are hard" |
| **Extraneous** | Unnecessary complexity from poor design | "Why do I need 3 YAML files for a simple deploy?" |
| **Germane** | Productive learning effort | "I'm learning how canary deployments work" |

**Your goal as a platform leader**: Minimize extraneous load. You cannot reduce intrinsic load (distributed systems will always be complex), and you should not reduce germane load (developers need to learn). But extraneous load — the stuff that is hard because your tools are bad — that is your responsibility.

**Cognitive load audit checklist**:
```
For each developer workflow, ask:
[ ] How many tools do they need to use?
[ ] How many concepts do they need to understand?
[ ] How many config files do they need to write?
[ ] How many people do they need to talk to?
[ ] How many dashboards do they need to check?
[ ] How many docs pages do they need to read?

For each answer, ask:
[ ] Is this number the minimum possible?
[ ] Can we eliminate, automate, or abstract any of these?
```

---

## Paved Roads at Scale

### Backstage (Spotify)

**What it is**: An open-source developer portal that provides a single pane of glass for all internal services, documentation, and tooling.

**Key capabilities**:
- **Software catalog**: What services exist, who owns them, what their status is
- **Templates**: Scaffold new services with pre-configured CI/CD, monitoring, and deployment
- **TechDocs**: Documentation lives next to the code, rendered in the portal
- **Plugins**: Extensible — connect to your existing tools (PagerDuty, Kubernetes, CI/CD)

**When to use Backstage**:
- Organization > 100 developers
- More than 50 services
- Discoverability is a problem ("where is the docs for X?")
- You want a composable platform, not a monolithic one

**When NOT to use Backstage**:
- Under 50 developers (overhead exceeds value)
- You need a complete IDP out of the box (Backstage requires significant customization)
- You lack engineers to maintain it (it is a platform for your platform)

### Port

**What it is**: A commercial internal developer portal with a focus on self-service actions and a software catalog.

**Key differentiator**: Port focuses on **actions** — developers can provision infrastructure, trigger deployments, and manage resources through the portal without writing code. Its "self-service hub" approach requires less custom development than Backstage.

**When to use Port**: Teams that want an IDP without building one from scratch. Organizations where developer self-service is the primary goal.

### Humanitec

**What it is**: A platform orchestrator that provides a reference architecture for internal developer platforms.

**Key differentiator**: Humanitec focuses on **workload-centric** abstractions. Developers describe what they need (a service with a database and a message queue), and the orchestrator handles the infrastructure details based on environment (dev vs staging vs prod).

**When to use Humanitec**: Teams that want to separate "what the developer needs" from "how infrastructure provisions it." Works well for organizations with multiple environments and deployment targets.

### Choosing the Right Approach

| Factor | Backstage | Port | Humanitec | Custom |
|--------|-----------|------|-----------|--------|
| **Setup time** | Months | Weeks | Weeks | Months-years |
| **Customization** | Very high (open source) | Medium (configurable) | Medium | Unlimited |
| **Maintenance burden** | High | Low (SaaS) | Low (SaaS) | Very high |
| **Cost** | Free + engineering time | Subscription | Subscription | Engineering time |
| **Best for** | Large orgs wanting full control | Mid-size wanting fast time-to-value | Orgs focused on workload abstraction | Unique requirements |

---

## The Developer Inner Loop and Outer Loop

Understanding these two loops is essential for DX strategy:

```
┌──────────────────────────────────────────────────────────┐
│                    INNER LOOP                             │
│         (developer's local workflow)                      │
│                                                           │
│    Write Code → Build → Test → Debug → Repeat            │
│                                                           │
│    Speed target: Seconds to minutes                       │
│    Ownership: Developer + IDE + local tools               │
└────────────────────────┬─────────────────────────────────┘
                         │ git push
                         ▼
┌──────────────────────────────────────────────────────────┐
│                    OUTER LOOP                             │
│         (platform-owned workflow)                         │
│                                                           │
│    CI → CD → Deploy → Monitor → Feedback → Repeat        │
│                                                           │
│    Speed target: Minutes to hours                         │
│    Ownership: Platform team + CI/CD + infrastructure      │
└──────────────────────────────────────────────────────────┘
```

**Platform teams often focus too much on the outer loop** (CI/CD, deployment, monitoring) and neglect the inner loop (local dev, build times, test speed). But developers spend 80% of their time in the inner loop.

**Inner loop improvements with high ROI**:
- Faster local builds (caching, incremental compilation)
- Hot reload for development servers
- Local environment that mirrors production
- Fast, reliable tests that run locally
- IDE integrations that surface platform information

---

## Hands-On Exercises

### Exercise 1: Developer Experience Baseline Assessment (60 min)

Measure your platform's current developer experience. This exercise creates a baseline you can track over time.

**Step 1: Time the critical workflows** (measure each 3 times, take the median)

| Workflow | Target | Your Time | Gap |
|----------|--------|-----------|-----|
| Create a new service (scaffold to first deploy) | < 2 hours | ___ | ___ |
| Deploy a code change to staging | < 15 min | ___ | ___ |
| Deploy a code change to production | < 30 min | ___ | ___ |
| Roll back a bad deployment | < 5 min | ___ | ___ |
| Provision a new database | < 10 min | ___ | ___ |
| Add monitoring to a service | < 30 min | ___ | ___ |
| Find documentation for a service | < 2 min | ___ | ___ |
| Onboard a new developer | < 1 day | ___ | ___ |

**Step 2: Run a mini-survey** (send to 5-10 developers)

Use the questions from the survey section above. Calculate averages and identify the lowest-scoring areas.

**Step 3: Create a DX improvement backlog**

Rank improvements by:
- Pain level (how much does this hurt developers?)
- Reach (how many developers are affected?)
- Effort (how hard is it to fix?)

### Exercise 2: Golden Path Design Workshop (45 min)

Design a golden path for the most common developer workflow at your organization.

**Step 1**: Identify the workflow (e.g., "deploy a new microservice," "add a new API endpoint," "create a database migration")

**Step 2**: Map the current steps:
```
Current workflow: [name]
Steps:
1. [step] — Time: ___ — Pain: Low/Med/High
2. [step] — Time: ___ — Pain: Low/Med/High
3. [step] — Time: ___ — Pain: Low/Med/High
...
Total time: ___
Total steps: ___
```

**Step 3**: Design the golden path:
```
Golden path: [name]
Steps:
1. [step] — Time: ___
2. [step] — Time: ___
...
Total time: ___
Total steps: ___

What we eliminated: [list]
What we automated: [list]
What we abstracted: [list]
```

**Step 4**: Identify what would need to be built to make the golden path real. Estimate effort.

### Exercise 3: Cognitive Load Mapping (30 min)

Pick one workflow your platform supports and map its cognitive load:

For each step, classify the cognitive load:
- **I** = Intrinsic (inherent complexity)
- **E** = Extraneous (unnecessary complexity from tools/process)
- **G** = Germane (productive learning)

```
Workflow: Deploy a service to Kubernetes
Step                              Load Type  Load Level (1-5)
─────────────────────────────────────────────────────────
Write Dockerfile                  I          2
Write Kubernetes YAML             E          4  ← Target for reduction
Configure CI pipeline             E          3  ← Target for reduction
Set up monitoring                 E          3  ← Target for reduction
Understand canary deployment      G          2
Debug failing health check        I          3
Update service mesh config        E          4  ← Target for reduction
```

**Goal**: Identify and prioritize the reduction of Extraneous load items.

---

## War Story: The Platform Nobody Used

**Company**: European e-commerce company, ~400 engineers, 60 services

**Situation**: The platform team spent 9 months building a "next-generation deployment platform" based on Kubernetes, ArgoCD, and a custom abstraction layer. It was technically excellent: blue-green deployments, automatic rollbacks, integrated monitoring, cost optimization. The CTO was excited. The platform team was proud.

**The launch**: They announced the platform in an all-hands meeting. Created documentation. Ran two training sessions. Then waited for adoption.

**What happened**:
- **Month 1**: 3 teams migrated (out of 25). All were teams with a platform engineer friend who helped them personally.
- **Month 2**: 1 more team migrated. Two teams that migrated filed tickets about missing features.
- **Month 3**: No new adoption. Internal Slack messages: "Is the new platform stable?" "I heard Team X had problems." "Our current setup works fine, why switch?"
- **Month 6**: 6 teams total (24%). Leadership starts asking uncomfortable questions.

**Root cause analysis**:
1. **No user research**: The platform team assumed they knew what developers wanted. They built features developers did not ask for and missed features they desperately needed (local development support, fast rollback, simple log access).
2. **High migration cost**: Migrating from the old system required rewriting CI/CD configs, Dockerfiles, and deployment scripts. This was 2-3 weeks of work per service — work that competed with feature delivery.
3. **Passive launch**: Docs and training sessions are not a launch strategy. The team expected developers to come to them.
4. **No internal champions**: Nobody outside the platform team was advocating for the new platform.

**What they did to fix it**:
1. Hired a developer advocate who spent 2 weeks embedded with the 3 lowest-adopting teams, understanding their actual workflows
2. Built a migration tool that converted old CI/CD configs to new format automatically (reduced migration from 2-3 weeks to 2 days)
3. Added the missing features: local dev support, one-click rollback, log streaming
4. Created a "migration buddy" program where engineers from early-adopting teams helped later teams
5. Started publishing weekly metrics: "Teams on the new platform deploy 4x faster and have 60% fewer incidents"

**Month 12 (after fixes)**: 19 out of 25 teams migrated (76%). Developer satisfaction with deployment tools went from 2.1/5 to 4.2/5.

**Business impact**: The 6-month delay cost approximately $1.2M in engineering time (60 engineers x $200K fully loaded x 20% productivity loss from bad tooling x 0.5 years) and delayed two product launches that depended on the new deployment capabilities.

**Lessons**:
1. **Build with users, not for users**: Embedded user research would have caught the missing features before launch
2. **Reduce migration cost aggressively**: Every hour of migration effort is a barrier to adoption
3. **Launch is marketing**: Treat your platform like a product launch, not a code release
4. **Measure adoption as the primary metric**: Lines of code and features shipped are vanity metrics for platforms

---

## Knowledge Check

### Question 1
What are the four DORA metrics and why are they relevant to platform teams?

<details>
<summary>Show Answer</summary>

The four DORA metrics are: **Deployment Frequency** (how often you deploy), **Lead Time for Changes** (time from commit to production), **Change Failure Rate** (% of deployments causing failures), and **Failed Deployment Recovery Time** (time to restore service).

They are relevant to platform teams because: (1) They measure the outcomes that platform teams exist to improve. (2) Comparing teams on vs off the platform proves platform value. (3) They are industry-standardized, making benchmarking possible. (4) They capture both speed (deployment frequency, lead time) and stability (change failure rate, recovery time).

</details>

### Question 2
Explain the difference between golden paths, guardrails, and mandates. Give an example of when each is appropriate.

<details>
<summary>Show Answer</summary>

**Golden paths** are opinionated defaults that are easy to follow but not required. Example: "Use our service template to get CI/CD, monitoring, and deployment pre-configured." Appropriate when you want to guide behavior while preserving team autonomy.

**Guardrails** are automated constraints that prevent dangerous actions. Example: "All containers must have resource limits" enforced by an admission controller. Appropriate for safety and security requirements.

**Mandates** are hard requirements with no exceptions. Example: "All services must use our centralized authentication service" for SOC 2 compliance. Appropriate only for regulatory, security, or critical operational requirements. Use sparingly — too many mandates kill developer autonomy and satisfaction.

</details>

### Question 3
Your DORA metrics show that teams on your platform deploy 3x more frequently, but their change failure rate is 2x higher than teams not on the platform. What's happening?

<details>
<summary>Show Answer</summary>

The platform is making it easier to deploy but not easier to deploy **safely**. Possible causes: (1) The platform lacks automated testing gates — deploys go out without adequate validation. (2) Canary/progressive deployment is not configured properly — bad changes reach all users before detection. (3) Monitoring and rollback are not integrated — failures are not caught early. (4) The platform optimized for speed (deployment frequency) without equal investment in safety (testing, rollback, observability).

The fix: Add automated quality gates (tests must pass), progressive delivery (canary deploys with automated rollback), and fast rollback mechanisms. Deploy frequency should improve change failure rate, not worsen it — fast deploys mean smaller changes, which should mean fewer failures.

</details>

### Question 4
What is cognitive load in the context of developer experience, and what are the three types?

<details>
<summary>Show Answer</summary>

Cognitive load is the mental effort required to complete a task. The three types are:

- **Intrinsic**: Inherent to the task (distributed systems are complex — you cannot simplify this away)
- **Extraneous**: Created by poor tooling or process (writing 3 YAML files for a simple deploy — you can and should eliminate this)
- **Germane**: Productive learning (understanding how canary deployments work — you should preserve this)

Platform teams should focus on reducing **extraneous** cognitive load. Developers should spend their mental energy on their business problem (intrinsic) and learning (germane), not fighting tools (extraneous).

</details>

### Question 5
Why is the developer inner loop (code-build-test locally) often more important than the outer loop (CI/CD-deploy-monitor) for developer experience?

<details>
<summary>Show Answer</summary>

Developers spend roughly **80% of their time in the inner loop**: writing code, building, testing, and debugging locally. The outer loop (CI/CD, deployment, monitoring) matters but runs less frequently and often in the background. Improvements to the inner loop — faster builds, better hot reload, reliable local testing, good IDE integration — have disproportionate impact because they affect every working hour, not just deploy time. Many platform teams over-invest in the outer loop while neglecting inner loop tools, which limits their impact on overall developer productivity.

</details>

### Question 6
Scenario: You're launching a developer satisfaction survey. A senior director says "Just ask them if they're happy — keep it simple." Why is this insufficient?

<details>
<summary>Show Answer</summary>

A single satisfaction question misses actionable detail. You need the SPACE framework's multiple dimensions: **Satisfaction** (are they happy?), **Performance** (are outcomes good?), **Activity** (what are they doing?), **Communication** (how well do they collaborate?), **Efficiency** (where is the friction?). You also need both quantitative questions (track trends over time) and qualitative questions (discover unknown problems). A developer can be "happy" overall but frustrated by a specific tool. Without targeted questions, you will not know what to fix. The survey should take 5-10 minutes, not 30 seconds — developers who care about their tools will invest the time.

</details>

### Question 7
Your platform team built a new feature. After 3 months, you check metrics: 40% of teams adopted it voluntarily. Is this good or bad?

<details>
<summary>Show Answer</summary>

**Context matters, but 40% in 3 months is generally good** for voluntary adoption. Key questions: (1) Is it the right 40%? If the teams that need it most adopted it, that is a strong signal. (2) Why didn't the other 60%? Talk to them — it might be awareness (fixable with marketing), migration cost (fixable with tooling), or poor fit (you built the wrong thing). (3) What's the trend? 40% and growing is healthy; 40% and flat means you've saturated early adopters and have a chasm to cross. For comparison, most internal platforms see 20-30% organic adoption in the first quarter. Getting to 80%+ usually requires reducing migration cost and sustained internal marketing. If you are expecting 100% adoption of a voluntary feature, adjust your expectations.

</details>

### Question 8
What's the difference between Backstage, Port, and Humanitec, and when would you choose each?

<details>
<summary>Show Answer</summary>

**Backstage** (open source, Spotify): A developer portal focused on software catalog, templates, and docs. Best for large organizations wanting full customization and control. Requires significant engineering investment to set up and maintain.

**Port** (commercial): A developer portal focused on self-service actions. Best for mid-size organizations wanting fast time-to-value without building a portal from scratch. Less customizable than Backstage but lower maintenance.

**Humanitec** (commercial): A platform orchestrator focused on workload-centric abstraction. Best for organizations that want to separate developer intent from infrastructure implementation. Different from the other two — it orchestrates infrastructure rather than just presenting a portal.

Choose Backstage if you have the engineers to maintain it and want full control. Choose Port if you want an IDP quickly with less engineering investment. Choose Humanitec if your primary challenge is environment provisioning across dev/staging/prod.

</details>

---

## Summary

Developer experience is the measure of how easily and effectively engineers can do their work using your platform. It is not a feeling — it is measurable through DORA metrics, SPACE dimensions, developer surveys, and workflow timing.

Key principles:
- **Measure before you build**: Baseline your current DX so you can prove improvement
- **Golden paths over mandates**: Make the right thing the easy thing
- **Reduce cognitive load**: Eliminate unnecessary complexity, preserve useful learning
- **Focus on the inner loop**: Where developers spend most of their time
- **Self-service is a spectrum**: Know where you are and where you are going
- **Adoption is the metric**: A platform nobody uses has zero value

---

## What's Next

Continue to [Module 1.3: Platform as Product](../module-1.3-platform-as-product/) to learn how to apply product management practices to your internal platform.

---

*"The goal is not to build a platform. The goal is to make developers productive. The platform is just how you get there."*
