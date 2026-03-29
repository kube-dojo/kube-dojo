---
title: "Module 1.4: Architecture Decision Records & Technical Writing"
slug: platform/foundations/engineering-leadership/module-1.4-adrs
sidebar:
  order: 5
---
> **Complexity**: `[MEDIUM]` | **Time**: 2 hours | **Prerequisites**: System Design basics
>
> **Track**: Foundations / Engineering Leadership

---

## The Decision Nobody Remembers

*Thursday afternoon. Sprint planning.*

"Why are we using RabbitMQ instead of Kafka?"

The room goes quiet. Engineers exchange glances. The tech lead who made that decision left 18 months ago. Someone mutters, "I think there was a Slack thread about it... maybe?" Another engineer opens Confluence and types "messaging" into search. Forty-seven results. None of them answer the question.

So the team does what every team does in this situation: they relitigate the decision from scratch. Two senior engineers spend a week benchmarking. A third writes a comparison document. The VP of Engineering weighs in during a 1:1 and mentions a constraint nobody else knew about. Three weeks later, they arrive at the same conclusion the previous tech lead reached in 2022---but they've burned a month of engineering time to get there.

This happens *constantly*. Not because engineers are careless, but because most organizations have no systematic way to record *why* decisions were made. They document *what* was built (API docs, runbooks, READMEs) but almost never *why it was built that way*.

Architecture Decision Records fix this. They're one of the highest-leverage tools in engineering leadership, and they take about 30 minutes to write.

This module teaches you how to write them well, and more broadly, how to communicate technical decisions to different audiences---because the best decision in the world is worthless if nobody understands or remembers it.

---

## Why This Module Matters

Every engineering team makes hundreds of decisions per quarter. Which database to use. How to handle authentication. Whether to build or buy. Monolith or microservices. Managed service or self-hosted.

Most of these decisions are *invisible*. They live in Slack threads that scroll away, in meeting notes nobody reads, in the heads of engineers who eventually leave. When new team members join, they inherit a codebase full of choices they don't understand. They either:

1. **Accept everything blindly** ("I guess there was a reason for this"), leading to cargo-cult engineering
2. **Question everything constantly** ("Why are we doing it this way?"), burning time and frustrating the team
3. **Redo decisions from scratch** ("Let's migrate to Kafka"), wasting months on already-solved problems

ADRs solve all three. They give newcomers context, protect institutional knowledge, and prevent decision amnesia.

But ADRs are just one form of technical writing. The broader skill---communicating decisions clearly to different audiences---is what separates a good engineer from an engineering leader. You might need to explain the same Kafka decision to:

- **Your team**: with full technical depth, trade-off analysis, and benchmark data
- **Your VP of Engineering**: focused on risk, timeline, and cost implications
- **Your CEO**: one paragraph about business impact

This module teaches the discipline of capturing and communicating technical decisions effectively.

> **The Real Cost of Undocumented Decisions**
>
> A 2021 survey by Stripe estimated that developers spend **17.3 hours per week** on maintenance and technical debt. A significant portion of that time is spent understanding *why* things were built the way they were. ADRs won't eliminate tech debt, but they dramatically reduce the cognitive overhead of working in a mature codebase.

---

## What You'll Learn

- Why documenting decisions matters more than documenting code
- The ADR format: Context, Options, Decision, Consequences
- How to write for different audiences (engineers, product, executives)
- The RFC process and how it connects to ADRs
- How to run effective design reviews
- Real-world ADR examples you can use as templates

---

## Part 1: The Case for Decision Records

### What Decisions Deserve Recording?

Not every decision needs an ADR. You don't need one for choosing between `camelCase` and `snake_case` (that goes in a style guide). You don't need one for which CI/CD tool to use if your company already standardized on one.

ADRs are for **architecturally significant decisions**---choices that are:

- **Hard to reverse** once implemented (database choice, messaging system, API paradigm)
- **Cross-cutting** across multiple teams or services
- **Costly** in terms of engineering time, infrastructure spend, or operational burden
- **Contentious** where reasonable engineers disagree

```
DECISION SIGNIFICANCE FILTER
======================================================================

Ask these questions about a technical decision:

 1. Would reversing this cost more than a sprint?          → YES = ADR
 2. Does it affect more than one team or service?          → YES = ADR
 3. Will people ask "why did we do this?" in 6 months?     → YES = ADR
 4. Are there trade-offs that won't be obvious later?      → YES = ADR
 5. Did multiple engineers disagree on the approach?       → YES = ADR

If you answered YES to any of these, write an ADR.
If you answered YES to three or more, write it TODAY.
```

### Why Not Just Use Confluence/Notion/Google Docs?

You can use any tool, but there's a strong argument for keeping ADRs **in the repository alongside the code they describe**:

| Approach | Pros | Cons |
|----------|------|------|
| **ADRs in repo** (`docs/adr/`) | Versioned with code, survives tool changes, discoverable via grep, reviewed in PRs | Not accessible to non-engineers |
| **Wiki (Confluence/Notion)** | Accessible to everyone, rich formatting | Gets stale, hard to find, not versioned with code, dies when you switch tools |
| **Slack threads** | Fast, natural discussion | Disappears in weeks, unsearchable, no structure |
| **Google Docs** | Collaborative editing, comments | Disconnected from code, access control issues |

The recommendation: **write the ADR in markdown in your repo**, and link to it from your wiki if non-technical stakeholders need access.

---

## Part 2: ADR Structure

### The Standard ADR Format

Michael Nygard proposed the original ADR format in 2011, and it has become the de facto standard. Here's the structure with explanations:

```markdown
# ADR-NNN: Title of the Decision

## Status

[Proposed | Accepted | Deprecated | Superseded by ADR-XXX]

## Date

YYYY-MM-DD

## Context

What is the issue that we're seeing that is motivating this decision?
What are the forces at play? Technical constraints, business requirements,
team capabilities, timeline pressures?

## Options Considered

### Option 1: [Name]
Description, pros, cons, estimated effort.

### Option 2: [Name]
Description, pros, cons, estimated effort.

### Option 3: [Name]
Description, pros, cons, estimated effort.

## Decision

What is the change that we're proposing and/or doing?
State the decision clearly and unambiguously.

## Consequences

What becomes easier or harder as a result of this decision?
Both positive and negative consequences should be listed.
```

Let's break down each section.

### Context: The "Why" Section

This is the most important section. It captures the forces that led to the decision---the business requirements, technical constraints, team dynamics, and timeline pressures that shaped the choice.

**Bad context:**
> We need to choose a message broker for our event-driven architecture.

**Good context:**
> Our order processing system currently uses synchronous HTTP calls between 6 microservices. During Black Friday 2024, this caused cascading failures when the inventory service became slow (see incident report IR-2024-112). Peak load is 15,000 orders/minute with a target of 50,000/minute by Q3. The team has 4 backend engineers, 2 of whom have Kafka experience. Our infrastructure budget for messaging is approximately $3,000/month on AWS.

The good version tells you *why* the decision is being made, *what constraints exist*, and *what success looks like*. Someone reading this in 2 years will understand the full picture.

### Options Considered: Show Your Work

List at least 2-3 options, including ones you rejected. This is critical because:

1. It proves you didn't just pick your favorite technology
2. It helps future engineers understand *what was available* at the time
3. It prevents re-evaluation of options that were already considered

For each option, include:

```
OPTION EVALUATION TEMPLATE
======================================================================

Option Name: [Technology/Approach]

  Description:   What is it? How would we use it?
  Pros:          What does it do well for our use case?
  Cons:          What are the downsides?
  Effort:        How long to implement? What skills needed?
  Cost:          Infrastructure, licensing, operational cost
  Risk:          What could go wrong?
  Team Fit:      Do we have the skills? Can we hire for it?
```

### Decision: Be Unambiguous

State the decision clearly. Don't hedge. Don't say "we might" or "we're leaning toward." Say "We will use X because Y."

**Bad decision:**
> We're going to try Kafka and see how it goes.

**Good decision:**
> We will use AWS MSK (Managed Kafka) for asynchronous event processing between order, inventory, and notification services. We chose managed Kafka over self-hosted to reduce operational burden, accepting the higher per-hour cost in exchange for automatic patching, scaling, and monitoring.

### Consequences: The Honest Part

Every decision has trade-offs. List both positive and negative consequences. This is where you earn trust---by being honest about what you're giving up.

```
CONSEQUENCES TEMPLATE
======================================================================

POSITIVE:
  + Decouples services, reducing cascading failure risk
  + Enables replay of events for debugging and recovery
  + Scales horizontally for Black Friday load requirements

NEGATIVE:
  - Adds operational complexity (topic management, consumer groups)
  - Introduces eventual consistency (team must handle this in code)
  - AWS MSK costs ~$2,800/month (vs ~$800 for self-hosted RabbitMQ)
  - Vendor lock-in to AWS for messaging infrastructure

RISKS:
  ! Team has limited Kafka experience (mitigated by MSK managed service)
  ! Schema evolution could cause consumer breakage (mitigated by Schema Registry)
```

---

## Part 3: ADR Lifecycle

ADRs are not static documents. They have a lifecycle:

```
ADR LIFECYCLE
======================================================================

  PROPOSED        Someone writes the ADR and opens it for discussion.
      │           This might be a PR, a design review agenda item,
      │           or an RFC shared on Slack.
      │
      ▼
  ACCEPTED        The team agrees on the decision. The ADR is merged.
      │           The decision is now the team's official stance.
      │           Implementation begins.
      │
      ▼
  [Time passes, the world changes]
      │
      ▼
  DEPRECATED      The decision no longer applies. The technology was
      │           sunset, the requirements changed, or a better option
      │           emerged. A new ADR explains why.
      │
      ▼
  SUPERSEDED      A new ADR explicitly replaces this one.
  BY ADR-XXX      The old ADR links to the new one, preserving
                  the full decision history.
```

### Never Delete ADRs

This is a common mistake. When a decision is overturned, teams want to delete the old ADR. Don't. The old ADR is *history*. It explains why the previous approach was chosen, which helps people understand the current one.

Instead, mark the old ADR as `Superseded by ADR-XXX` and add a note at the top:

```markdown
## Status

**Superseded by [ADR-042: Migration to Apache Pulsar](042-migration-to-pulsar/)**

> This ADR documented our 2023 decision to use AWS MSK. In 2025, we
> migrated to Apache Pulsar due to multi-cloud requirements. See ADR-042
> for the updated decision and migration plan.
```

### Numbering and Organization

Keep ADRs in a dedicated directory:

```
docs/
└── adr/
    ├── README.md              # Index of all ADRs with status
    ├── 001-use-postgresql.md
    ├── 002-event-driven-architecture.md
    ├── 003-managed-kafka.md
    ├── 004-graphql-api.md
    └── template.md            # Blank template for new ADRs
```

The `README.md` acts as an index:

```markdown
# Architecture Decision Records

| ADR | Title | Status | Date |
|-----|-------|--------|------|
| 001 | Use PostgreSQL for primary data store | Accepted | 2023-03-15 |
| 002 | Adopt event-driven architecture | Accepted | 2023-06-01 |
| 003 | Use AWS MSK for messaging | Superseded by 007 | 2023-08-20 |
| 004 | GraphQL for public API | Accepted | 2023-11-10 |
```

---

## Part 4: Writing for Different Audiences

An ADR is written for engineers. But the same decision often needs to be communicated to product managers, VPs, and executives. The information is the same; the framing changes completely.

### The Audience Pyramid

```
THE AUDIENCE PYRAMID
======================================================================

                    ┌─────────┐
                    │  C-SUITE │   Impact. One paragraph.
                    │  / EXECS │   "What does this mean for the business?"
                    ├──────────┤
                    │    VP /   │   Risk, cost, timeline.
                    │  DIRECTOR │   "What are the trade-offs and
                    │           │    when will it be done?"
                    ├───────────┤
                    │  PRODUCT   │   User impact, feature implications.
                    │  MANAGERS  │   "How does this affect the roadmap?"
                    ├────────────┤
                    │  ENGINEERING │   Full technical detail.
                    │  TEAM        │   "How does this work and why?"
                    └──────────────┘

  Rule: As you go UP the pyramid, remove technical detail
        and add business context.
```

### Same Decision, Four Audiences

Let's say you've decided to migrate from a monolithic API to microservices. Here's how you'd communicate it:

**To your engineering team (ADR):**
> We will decompose the Order module into three microservices (order-api, order-processor, order-notifications) communicating via async events on Kafka. This reduces deployment coupling---currently a change to notifications requires redeploying the entire order system, causing 15-minute deploy windows. Independent services will deploy in under 2 minutes with zero-downtime rolling updates.

**To product managers:**
> We're splitting the order system into independent components. This means the team can ship notification features (like SMS alerts) without touching---or risking---the core order flow. Deploy frequency for order-related features will increase from weekly to multiple times per day.

**To your VP of Engineering:**
> We're investing 6 weeks of engineering time to decompose the order monolith. This reduces our deployment risk (3 incidents in the last quarter were caused by unrelated changes deployed together) and unblocks the notification team, who are currently blocked 2-3 days per sprint waiting for deploy windows. Expected ROI: the engineering time pays for itself within one quarter through reduced incident cost and faster shipping.

**To the CTO/CEO:**
> We're restructuring the order system so teams can ship features independently. This eliminates deployment bottlenecks that have delayed 3 features this quarter and reduces the risk of outages during deploys. Six weeks of investment, payback within one quarter.

### The "So What?" Test

Before sending any technical communication, ask: **"So what?"**

- "We're migrating to Kafka." **So what?** *Orders will process 10x faster during peak load.*
- "We're adding a caching layer." **So what?** *Page load times drop from 3 seconds to 200ms.*
- "We're refactoring the auth module." **So what?** *We can add SSO support, which Sales has been requesting for 6 months.*

Every communication to a non-technical audience should lead with the "so what" answer, not the technical detail.

---

## Part 5: The RFC Process

### ADRs vs RFCs

ADRs and RFCs serve different purposes but complement each other:

| Aspect | ADR | RFC |
|--------|-----|-----|
| **Purpose** | Record a decision | Propose a change and solicit feedback |
| **Timing** | Written when decision is made (or shortly after) | Written before work begins |
| **Length** | 1-2 pages | 3-15 pages |
| **Audience** | Future engineers | Current team + stakeholders |
| **Tone** | Declarative ("We decided...") | Propositional ("I propose...") |
| **Approval** | Team consensus or tech lead decision | Formal review process |

Think of it this way: an RFC is the *discussion*, and the ADR is the *conclusion*.

### RFC Structure

A good RFC includes:

```markdown
# RFC: [Title]

**Author**: [Name]
**Date**: YYYY-MM-DD
**Status**: [Draft | In Review | Accepted | Rejected | Withdrawn]
**Reviewers**: [Names of people whose input is required]

## Summary
One paragraph. What are you proposing and why?

## Motivation
Why is this needed? What problem does it solve?
Include data: error rates, customer complaints, engineering hours wasted.

## Detailed Design
The technical proposal. Architecture diagrams, API contracts,
data models, sequence diagrams. This is the meat of the RFC.

## Alternatives Considered
What else could we do? Why is this proposal better?

## Migration Plan
How do we get from here to there? What's the rollout strategy?
How do we roll back if things go wrong?

## Open Questions
What haven't you figured out yet? What do you need input on?
Being honest about unknowns builds trust.

## Timeline
Rough estimate of effort and milestones.
```

### Running Effective Design Reviews

The RFC is the document. The design review is the meeting where you discuss it. Here's how to run a good one:

```
DESIGN REVIEW BEST PRACTICES
======================================================================

BEFORE THE MEETING:
  - Share the RFC at least 2 business days before the review
  - Ask reviewers to leave async comments first
  - Identify the 2-3 most contentious decisions to focus on

DURING THE MEETING:
  - Don't read the RFC aloud (everyone should have read it)
  - Start with: "What questions do you have?"
  - Focus on trade-offs, not preferences
  - Time-box to 45 minutes (30 discussion + 15 decisions)
  - Assign someone to take notes on decisions made

AFTER THE MEETING:
  - Update the RFC with decisions and rationale
  - Write the ADR(s) capturing final decisions
  - Share the outcome with stakeholders

ANTI-PATTERNS TO AVOID:
  ✗ Bikeshedding (arguing about trivial details)
  ✗ "Let me present for 40 minutes" (it's a discussion, not a lecture)
  ✗ Design-by-committee (someone must own the decision)
  ✗ Blocking on perfection (good enough now > perfect later)
```

---

## Part 6: Documenting "Why" Over "What"

### Code Tells You What. Comments Tell You Why. ADRs Tell You Why at Scale.

This principle applies at every level:

```python
# BAD: Comment says what the code does (I can read the code)
# Retry 3 times with exponential backoff
for i in range(3):
    try:
        response = call_api()
        break
    except TimeoutError:
        time.sleep(2 ** i)

# GOOD: Comment says WHY (I can't read your mind)
# The payment gateway rate-limits aggressive retries.
# After incident INC-2024-089, we found that exponential backoff
# with max 3 retries keeps us under their 10-req/sec threshold.
for i in range(3):
    try:
        response = call_api()
        break
    except TimeoutError:
        time.sleep(2 ** i)
```

The same principle applies to ADRs. Don't just document *what* you chose. Document *why* you chose it, *what you rejected*, and *what trade-offs you accepted*.

### The "Future Engineer" Test

When writing any technical document, imagine someone joining your team in 18 months. They're smart, but they don't know your history. Ask:

1. Will they understand *what* we decided? (The easy part)
2. Will they understand *why* we decided it? (The hard part)
3. Will they know *what alternatives were considered*? (Prevents re-litigation)
4. Will they understand *what constraints existed* at the time? (Prevents unfair criticism)

If the answer to any of these is "no," your documentation is incomplete.

---

## Part 7: Real-World ADR Examples

### Example 1: Database Selection

```markdown
# ADR-012: Use PostgreSQL with Read Replicas Instead of DynamoDB

## Status
Accepted

## Date
2024-09-15

## Context
Our user profile service handles 2,000 reads/sec and 200 writes/sec.
Growth projections suggest 10,000 reads/sec within 12 months. The team
(5 backend engineers) has deep PostgreSQL expertise but no DynamoDB
experience. Our data model includes complex relationships (users →
organizations → roles → permissions) that benefit from JOIN operations.

We evaluated options during Sprint 42 after the CEO asked about
scaling concerns raised by a prospective enterprise customer.

## Options Considered

### Option 1: DynamoDB
- Fully managed, scales automatically
- Pay-per-request pricing at our scale: ~$400/month
- Requires denormalizing our relational data model
- Team would need 2-3 months to become proficient
- No JOIN support; complex queries require application-level logic

### Option 2: PostgreSQL with Read Replicas
- Team already proficient; no ramp-up time
- RDS managed instances with read replicas: ~$600/month
- Handles our relational data model naturally
- Read replicas handle read scaling to 50,000 reads/sec
- Requires manual scaling decisions (add/remove replicas)

### Option 3: CockroachDB
- Distributed SQL; scales horizontally
- Compatible with PostgreSQL wire protocol
- Starting at ~$1,200/month for managed service
- Team would need 1 month to learn operational differences
- Overkill for our current and projected scale

## Decision
We will use PostgreSQL on AWS RDS with read replicas.

Our data model is inherently relational, and the team's PostgreSQL
expertise means we can ship the scaling improvements in 2 weeks
instead of the 2-3 months DynamoDB would require. Read replicas
give us 10x headroom on reads, which covers our 12-month projection.

## Consequences
+ Team ships immediately with no learning curve
+ Relational queries remain simple and maintainable
+ Cost-effective at current and projected scale
- We accept manual scaling decisions (adding read replicas)
- If we exceed 50,000 reads/sec, we'll need to re-evaluate
- Single-region limitation with RDS (acceptable for now)
```

### Example 2: API Paradigm

```markdown
# ADR-018: Use REST for Internal APIs, GraphQL for Public API

## Status
Accepted

## Date
2024-11-20

## Context
We maintain 12 internal microservices and a public API consumed by
~200 third-party integrators. Internal services need simple,
predictable communication. External consumers have diverse data
needs---some need full user profiles, others need just email and name.

Our current REST API forces external consumers to make 3-4 calls
to assemble data that could be fetched in one GraphQL query.
Support tickets about API inefficiency have increased 40% QoQ.

## Decision
Internal services will continue using REST with OpenAPI specs.
The public-facing API will add a GraphQL layer backed by the
existing REST services.

## Consequences
+ External consumers get flexible data fetching (reduced API calls)
+ Internal services remain simple and well-understood
+ GraphQL layer acts as a BFF (Backend for Frontend), insulating
  internal changes from external consumers
- Team must learn and maintain GraphQL (training budget approved)
- Two API paradigms to document and support
- GraphQL introduces query complexity risks (mitigated by depth limiting)
```

---

## Common Mistakes

| Mistake | Why It's a Problem | Better Approach |
|---------|-------------------|-----------------|
| **Writing ADRs after the fact as an afterthought** | Context and reasoning are forgotten; the ADR becomes a hollow justification | Write the ADR during or immediately after the decision. The discussion is freshest then. |
| **Listing only the chosen option** | Future engineers don't know what was considered and re-evaluate from scratch | Always include 2-3 alternatives with honest pros/cons for each. |
| **Omitting negative consequences** | Erodes trust; makes ADRs feel like marketing documents | List trade-offs honestly. Every decision has downsides---acknowledge them. |
| **Making ADRs too long** | Nobody reads 10-page ADRs. They become write-only documents. | Keep ADRs to 1-2 pages. Move detailed analysis to appendices or linked RFCs. |
| **No clear owner or approval process** | ADRs rot in "Proposed" status forever because nobody is responsible for driving them to acceptance | Assign an owner to each ADR. Set a review deadline (1-2 weeks). |
| **Deleting superseded ADRs** | Destroys decision history. Future engineers lose context about why the previous approach was abandoned. | Mark as "Superseded by ADR-XXX" and keep the file. It's an archive, not a wiki. |
| **Using ADRs for non-architectural decisions** | Dilutes the value. Teams get ADR fatigue and stop reading them. | Reserve ADRs for significant, hard-to-reverse decisions. Use style guides, runbooks, and READMEs for everything else. |
| **Writing for yourself instead of your audience** | You understand the jargon and context today. Your reader in 18 months will not. | Apply the "Future Engineer" test. Write for someone smart but new to the team. |

---

## Quiz

Test your understanding of ADRs and technical writing.

**Question 1:** What are the four core sections of a standard ADR?

<details>
<summary>Show Answer</summary>

**Context**, **Options Considered**, **Decision**, and **Consequences**.

The Context explains why the decision is needed. Options Considered shows the alternatives evaluated. Decision states what was chosen and why. Consequences lists both positive and negative outcomes.

Some templates also include Status and Date, which are important metadata but not part of the core reasoning structure.
</details>

**Question 2:** Your team decided to use Redis for caching 2 years ago. Now you're migrating to Memcached. What should you do with the original Redis ADR?

<details>
<summary>Show Answer</summary>

**Do not delete it.** Mark it as "Superseded by ADR-XXX" (the Memcached ADR) and add a brief note explaining the transition. The original ADR is valuable history---it explains why Redis was chosen at the time, which helps future engineers understand the evolution of the system.

The new Memcached ADR should reference the original and explain what changed (requirements, scale, team expertise, cost) to motivate the migration.
</details>

**Question 3:** You need to explain a database migration to your CEO. Which of these is better?

A) "We're migrating from MySQL 5.7 to PostgreSQL 16 because MySQL's query optimizer doesn't support hash joins and our analytical workloads require better parallel query execution."

B) "We're switching databases to handle 10x more reporting queries without slowing down the product. This supports the enterprise sales push by enabling the real-time dashboards large customers are requesting."

<details>
<summary>Show Answer</summary>

**B is better.** The CEO cares about business impact (enterprise sales, customer features), not query optimizer internals. Option A provides technical detail that's irrelevant to the CEO's decision-making context.

Option A would be appropriate for the engineering team's ADR. The skill is matching the depth and framing to your audience.
</details>

**Question 4:** What is the key difference between an ADR and an RFC?

<details>
<summary>Show Answer</summary>

An **RFC** (Request for Comments) is written *before* a decision to propose a change and solicit feedback. It's a discussion document.

An **ADR** (Architecture Decision Record) is written *when* a decision is made to record the outcome. It's a historical record.

Think of it this way: the RFC is the debate, the ADR is the verdict. An RFC often results in one or more ADRs.
</details>

**Question 5:** A junior engineer asks, "Why do we keep ADRs in the git repo instead of Confluence?" Give two strong reasons.

<details>
<summary>Show Answer</summary>

1. **Version control**: ADRs in the repo are versioned alongside the code they describe. You can see exactly what decisions were in effect when a particular version of the code was written. Confluence doesn't provide this temporal alignment.

2. **Durability**: Companies switch wiki tools every few years (Confluence to Notion to Slite to whatever's next). Files in a git repo survive tool migrations. The ADR from 2020 is still readable in 2030.

Bonus reasons: ADRs in the repo are discoverable via `grep`, can be reviewed in pull requests, and can be linked from code comments.
</details>

**Question 6:** You're writing an ADR and you can only think of one option. What should you do?

<details>
<summary>Show Answer</summary>

If you can only think of one option, you haven't done enough research---or the decision isn't significant enough to warrant an ADR.

Every architectural decision has alternatives. At minimum, consider:
- **Do nothing** (keep the status quo)
- **Build vs buy** (if applicable)
- **A competing technology** in the same category

If after research you genuinely believe there's only one viable option, document the alternatives you considered and explain why they were eliminated. The "Options Considered" section should show your reasoning process, even if the conclusion is obvious.
</details>

**Question 7:** What is the "So What?" test and when should you apply it?

<details>
<summary>Show Answer</summary>

The "So What?" test is a technique for ensuring technical communication is relevant to its audience. After writing a statement, ask "So what?"---if the audience wouldn't care about the answer, you're writing at the wrong level of abstraction.

Apply it whenever communicating with non-technical stakeholders:
- "We're adding a CDN." **So what?** "Pages will load 3x faster for international customers."
- "We're containerizing the app." **So what?** "Deployments will go from 2 hours to 5 minutes, and we'll ship features faster."

The test forces you to connect technical decisions to outcomes that matter to your audience.
</details>

---

## Hands-On Exercise: Draft an ADR

### Scenario

Your team runs an event-driven e-commerce platform on Kubernetes. The current RabbitMQ cluster is struggling under load during peak sales events (Black Friday, seasonal promotions). Messages are being dropped, consumers can't keep up, and the operations team spends significant time managing the RabbitMQ cluster.

You need to decide between:

- **Option A: AWS MSK (Managed Kafka)** --- AWS-managed Apache Kafka service
- **Option B: Self-hosted Kafka on Kubernetes** --- Running Kafka using Strimzi operator on your existing K8s clusters

**Constraints:**
- Team of 6 engineers; 2 have Kafka experience, all have Kubernetes experience
- Current message volume: 5,000 events/sec, projected 25,000 events/sec in 12 months
- Infrastructure budget: $5,000/month for messaging
- Company uses AWS for all infrastructure
- Must support at least 7-day message retention for replay capability
- Uptime requirement: 99.95%

### Your Task

Write a complete ADR using the standard format. Your ADR must include:

1. **Context**: Describe the current problem, constraints, and what success looks like
2. **Options Considered**: Evaluate both options with honest pros and cons
3. **Decision**: Choose one option and explain why
4. **Consequences**: List positive and negative outcomes

### Evaluation Hints

Consider these trade-off dimensions:

```
TRADE-OFF ANALYSIS FRAMEWORK
======================================================================

 Dimension          AWS MSK               Self-Hosted (Strimzi)
 ─────────────────────────────────────────────────────────────────
 Operational Cost   Higher $/hour but      Lower $/hour but team
                    zero ops overhead      must manage upgrades,
                                           patches, scaling

 Control            AWS manages broker     Full control over
                    config, limited        configuration, tuning,
                    customization          and version

 Scaling            AWS handles broker     Team must plan and
                    scaling, you manage    execute scaling
                    partition scaling      operations manually

 Skills Required    Kafka application      Kafka application +
                    knowledge only         Kafka operations +
                                           Strimzi operator

 Vendor Lock-in     Tied to AWS MSK        Portable across any
                    (MSK-specific APIs)    Kubernetes cluster

 Reliability        AWS SLA (99.9%),       Depends on your team's
                    managed failover       operational maturity

 Cost at Scale      ~$3,500-4,500/mo       ~$1,200-2,000/mo
                    for projected load     for projected load
```

### Success Criteria

- [ ] ADR follows the standard format (Status, Date, Context, Options, Decision, Consequences)
- [ ] Context section explains the current problem with specific numbers
- [ ] At least 2 options are evaluated with honest pros and cons
- [ ] Decision is clear, unambiguous, and justified
- [ ] Consequences include both positive and negative outcomes
- [ ] A non-technical reader could understand *why* the decision was made (even if not the technical details)
- [ ] The ADR is 1-2 pages (not a 10-page novel)

### Stretch Goals

- Write a 3-sentence summary of the decision for your VP of Engineering (focus on cost and risk)
- Write a 1-sentence summary for the CTO (focus on business impact)
- Identify which consequence is most likely to cause problems in 12 months

---

## Did You Know?

- **Michael Nygard** proposed the ADR format in a blog post in November 2011. The post was barely 500 words long, yet it launched a practice now used by thousands of engineering teams worldwide. Sometimes the most impactful technical writing is the shortest.

- **Amazon's famous "6-pager" memos** are essentially elaborate RFCs. Jeff Bezos banned PowerPoint in 2004, requiring teams to write structured prose documents instead. His reasoning: "The narrative structure of a good memo forces better thinking than the bullet points of a PowerPoint." Meetings begin with 20 minutes of silent reading before any discussion.

- **Google's design documents** are typically 5-20 pages and require approval from at least one "readability reviewer" who ensures the document is clear to someone outside the immediate team. Google engineers write an estimated 1,000+ design docs per week across the company.

- **The Linux kernel** has some of the most thorough decision documentation in open source---not as formal ADRs, but in mailing list discussions that are archived forever. Linus Torvalds' emails explaining *why* a patch was rejected are legendary examples of technical communication. His 2006 email explaining Git's design decisions is still cited today.

---

## Further Reading

- **"Documenting Architecture Decisions"** by Michael Nygard --- The original blog post that started it all. Read this first; it takes 5 minutes.

- **"Design Docs at Google"** --- Google's engineering practices documentation explains their design review process in detail.

- **"Architecture Decision Records" on GitHub** (joelparkerhenderson/architecture-decision-record) --- A comprehensive collection of ADR templates, examples, and tools.

- **"The Staff Engineer's Path"** by Tanya Reilly --- Chapter on technical decision-making and communication. Excellent coverage of writing for different audiences.

- **"Writing for Engineers"** by Karan Goel --- Practical guide to technical writing that engineers will actually read.

---

## Next Module

[Module 1.5: Stakeholder Communication & Managing Expectations](../module-1.5-stakeholders/) --- Translating tech debt into business risk, saying "No" effectively, and communicating during crises to non-technical stakeholders.

---

*"The best time to write an ADR is when you make the decision. The second best time is now."* --- Engineering proverb

*"Architecture is the decisions you wish you could get right early in a project, but that you are not necessarily more likely to get right than any others."* --- Ralph Johnson
