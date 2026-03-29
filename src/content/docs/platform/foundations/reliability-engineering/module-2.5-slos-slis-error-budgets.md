---
title: "Module 2.5: SLIs, SLOs, and Error Budgets \u2014 The Theory"
slug: platform/foundations/reliability-engineering/module-2.5-slos-slis-error-budgets
sidebar:
  order: 6
---
> **Complexity**: `[MEDIUM]` — Core SRE mental model
>
> **Time to Complete**: 40-50 minutes
>
> **Prerequisites**: [Module 2.1: What Is Reliability](module-2.1-what-is-reliability/), [Module 2.4: Measuring and Improving Reliability](module-2.4-measuring-and-improving-reliability/)
>
> **Track**: Foundations

---

## The Team With 99.99% Uptime and Angry Users

**March 2019. A Series B fintech startup. The weekly leadership sync.**

The VP of Engineering pulls up the infrastructure dashboard with pride. "We hit 99.99% uptime last quarter. Four nines. That's only 4.3 minutes of downtime per month."

The room applauds. Engineering high-fives. The CTO nods approvingly.

Then the Head of Customer Success opens her laptop. "Interesting. Because I have 340 support tickets from last month. All say the same thing: 'Your app is unusable.'"

Silence.

"Here's one from our largest enterprise customer: *'We've been on hold for 20 minutes trying to load our portfolio dashboard. The app never goes down, but it takes 8 seconds to show my balances. I'm moving to a competitor.'*"

The VP of Engineering stammers. "But... we had 99.99% uptime."

"Your servers were up," the Head of Customer Success replies. "But the *experience* was broken. P99 latency was 8.2 seconds last month. Users don't care that the server responded. They care that it responded in *geological time*."

```
THE DISCONNECT
═══════════════════════════════════════════════════════════════════════════════

What Engineering measured:

    "Is the server responding at all?"

    Month 1: ████████████████████████████████████████  99.99% YES
    Month 2: ████████████████████████████████████████  99.99% YES
    Month 3: ████████████████████████████████████████  99.99% YES

    Conclusion: "We're crushing it."


What users experienced:

    "Did I get my answer in a reasonable time?"

    Month 1: █████████████████████████░░░░░░░░░░░░░░  62% YES
    Month 2: ██████████████████████░░░░░░░░░░░░░░░░░  55% YES
    Month 3: ████████████████████░░░░░░░░░░░░░░░░░░░  48% YES (getting worse!)

    Conclusion: "This product is broken."
```

The problem was not reliability engineering. It was that they were measuring the **wrong thing**. Their SLI (Service Level Indicator) measured availability—"did the server respond?"—when users cared about latency—"did the server respond *fast enough*?"

Once they defined SLOs around latency ("99th percentile response time under 500ms for the portfolio dashboard"), the real picture emerged. They weren't at four nines. They were at barely two nines of *meaningful* reliability.

**The SLO revealed what uptime monitoring hid.** Within two months of focusing on the right SLIs, customer satisfaction scores jumped 34%. Not because they built new features—because they finally measured what mattered.

This is why SLIs, SLOs, and error budgets exist. Not as bureaucratic overhead. As **the lens that shows you reality**.

---

## Why This Module Matters

Every engineering team argues about reliability versus velocity. Developers want to ship. Operators want stability. Product wants both. Without a shared framework, these arguments become political—whoever shouts loudest wins.

SLIs, SLOs, and error budgets replace politics with math. They answer three questions that every team fights about:

1. **"How do we know if we're reliable enough?"** — The SLO answers this.
2. **"What should we measure?"** — The SLI answers this.
3. **"Should we ship or stabilize?"** — The error budget answers this.

This module teaches the **theory** behind these concepts. You will learn what SLIs, SLOs, and error budgets are, why they work, and how to think about them correctly. Later modules cover the operational practices ([Module 1.2: SLO Discipline](../../disciplines/core-platform/sre/)), budget management ([Module 1.3: Error Budget Management](../../disciplines/core-platform/sre/)), and tooling ([Module 1.10: SLO Tooling — Sloth/Pyrra](../../toolkits/observability-intelligence/observability/)).

> **The Restaurant Analogy**
>
> Think of a restaurant. The *SLI* is what you measure: "percentage of meals served within 20 minutes." The *SLO* is your target: "95% of meals within 20 minutes." The *error budget* is how many slow meals you can tolerate before you stop adding new menu items and fix the kitchen.
>
> Without SLOs, the chef keeps adding exotic dishes (features) while wait times creep to 45 minutes. With SLOs, the team knows exactly when to stop expanding the menu and start hiring another line cook.

---

## What You'll Learn

- How to choose SLIs that reflect real user experience
- How to set SLOs that are ambitious but achievable
- How error budgets turn reliability into a spending decision
- How burn rate alerts catch problems before budgets run dry
- How error budget policies align engineering and product
- How to avoid the most common SLO anti-patterns

---

## Part 1: Service Level Indicators (SLIs)

### 1.1 What Is an SLI?

A **Service Level Indicator** is a quantitative measure of some aspect of the level of service being provided. In plain English: it is the number that tells you whether users are happy.

An SLI is always expressed as a ratio:

```
SLI FORMULA
═══════════════════════════════════════════════════════════════════════════════

              Good events
    SLI  =  ─────────────  ×  100%
             Total events


Examples:
─────────────────────────────────────────────────────────────────────────────
Availability SLI:
    Successful HTTP responses (non-5xx) / Total HTTP responses × 100%

Latency SLI:
    Requests completed in < 300ms / Total requests × 100%

Correctness SLI:
    Responses with correct data / Total responses × 100%

Throughput SLI:
    Minutes where throughput > 1000 req/s / Total minutes × 100%
```

The ratio form matters. It lets you express any SLI as a percentage between 0% and 100%, which makes it directly comparable to your SLO target.

### 1.2 The Four Types of SLIs

There are four fundamental categories of SLIs. Most services need at least two.

```
THE FOUR SLI TYPES
═══════════════════════════════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│   1. AVAILABILITY                                                           │
│   ─────────────                                                            │
│   "Did it respond at all?"                                                  │
│                                                                             │
│   Good event: Non-5xx response                                             │
│   Total events: All requests                                                │
│   Best for: Any user-facing service                                         │
│   Example: 99.95% of requests return non-5xx                               │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   2. LATENCY                                                                │
│   ──────────                                                               │
│   "Did it respond fast enough?"                                             │
│                                                                             │
│   Good event: Response within threshold                                     │
│   Total events: All requests (or all successful requests)                   │
│   Best for: Interactive/real-time services                                  │
│   Example: 99% of requests complete in < 200ms                             │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   3. THROUGHPUT                                                             │
│   ────────────                                                             │
│   "Did it handle enough work?"                                              │
│                                                                             │
│   Good event: Minute where throughput exceeds minimum                       │
│   Total events: All minutes in window                                       │
│   Best for: Data pipelines, batch systems                                   │
│   Example: 99.9% of minutes, pipeline processes > 10k events/min           │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   4. CORRECTNESS                                                            │
│   ──────────────                                                           │
│   "Did it give the right answer?"                                           │
│                                                                             │
│   Good event: Response with correct/expected data                           │
│   Total events: All responses                                               │
│   Best for: Financial, search, recommendation systems                       │
│   Example: 99.999% of transactions posted to correct account               │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 1.3 Choosing the Right SLI

Not all SLIs are equally useful. The best SLI is the one closest to the user's actual experience.

**Good vs. Bad SLIs:**

| Bad SLI | Why It's Bad | Good SLI | Why It's Better |
|---------|-------------|----------|----------------|
| CPU utilization < 80% | Users don't experience CPU | Request success rate > 99.9% | Users experience errors directly |
| Average latency < 100ms | Averages hide tail latency | P99 latency < 500ms | Catches the worst user experiences |
| Server is ping-able | Ping doesn't test functionality | Synthetic transaction succeeds | Tests the actual user journey |
| Zero error logs | Logs miss silent failures | End-to-end probe returns correct data | Catches data corruption, not just crashes |
| Disk usage < 90% | Operational metric, not user metric | Write operations succeed within 50ms | Users experience write failures |
| Pod restart count = 0 | Restarts may be invisible to users | No user-visible request dropped during restart | Measures actual user impact |

**The Golden Rule**: Measure at the boundary closest to the user. If you can measure at the load balancer, do that—not at the application, not at the database. The load balancer sees what the user sees.

```
WHERE TO MEASURE SLIs
═══════════════════════════════════════════════════════════════════════════════

                     ┌─────────┐
                     │  USER   │
                     └────┬────┘
                          │
              ════════════╪══════════════  BEST: Measure here
                          │                (real user monitoring or
                     ┌────▼────┐            synthetic probes)
                     │  CDN /  │
                     │  LB     │
                     └────┬────┘
              ────────────┼──────────────  GOOD: Measure here
                          │                (load balancer logs)
                     ┌────▼────┐
                     │  API    │
                     │ Gateway │
                     └────┬────┘
              ────────────┼──────────────  OKAY: Measure here
                          │                (misses network issues)
                     ┌────▼────┐
                     │ Service │
                     │  Code   │
                     └────┬────┘
              ────────────┼──────────────  POOR: Measure here
                          │                (misses everything upstream)
                     ┌────▼────┐
                     │Database │
                     └─────────┘

    The further from the user you measure, the more failures you miss.
```

### 1.4 Request-Based vs. Window-Based SLIs

SLIs come in two flavors, depending on what you are measuring:

**Request-based SLIs** count individual events:
- "99.9% of HTTP requests return successfully"
- Best for: APIs, web services, microservices
- Denominator: total number of requests

**Window-based SLIs** evaluate time slices:
- "99.9% of 1-minute windows have median query time < 100ms"
- Best for: Batch jobs, pipelines, background processes
- Denominator: total number of time windows

```
REQUEST-BASED vs WINDOW-BASED
═══════════════════════════════════════════════════════════════════════════════

REQUEST-BASED: Each request is an event
─────────────────────────────────────────────────────────────────────────────
    Request 1: ✅ 50ms     Request 4: ✅ 80ms     Request 7: ✅ 120ms
    Request 2: ✅ 45ms     Request 5: ❌ timeout   Request 8: ✅ 90ms
    Request 3: ✅ 62ms     Request 6: ✅ 55ms     Request 9: ✅ 73ms

    SLI = 8 good / 9 total = 88.9%


WINDOW-BASED: Each time window is an event
─────────────────────────────────────────────────────────────────────────────
    Minute 1: Pipeline processed 12,000 events  ✅ (> 10k threshold)
    Minute 2: Pipeline processed 11,500 events  ✅
    Minute 3: Pipeline processed 8,200 events   ❌ (< 10k threshold)
    Minute 4: Pipeline processed 10,100 events  ✅
    Minute 5: Pipeline processed 15,000 events  ✅

    SLI = 4 good / 5 total = 80%
```

> **Did You Know?**
>
> Google's Ads system reportedly loses approximately **$200,000 per minute** of latency degradation during peak hours. This is why their SLIs focus obsessively on latency percentiles, not just availability. A system that responds with errors is obviously broken. A system that responds correctly but slowly is *invisibly* broken—and the financial damage accumulates silently.

---

## Part 2: Service Level Objectives (SLOs)

### 2.1 What Is an SLO?

A **Service Level Objective** is a target value for an SLI, measured over a time window. It is the line in the sand that separates "reliable enough" from "not reliable enough."

```
SLO ANATOMY
═══════════════════════════════════════════════════════════════════════════════

    An SLO has three parts:

    ┌────────────────────────────────────────────────────────────────────┐
    │                                                                    │
    │   "99.9% of requests will complete successfully                   │
    │    within 300ms, measured over a rolling 28-day window."          │
    │                                                                    │
    │    ▲              ▲                  ▲                             │
    │    │              │                  │                             │
    │    TARGET         SLI                WINDOW                       │
    │    (99.9%)        (success within    (28 days, rolling)           │
    │                    300ms)                                          │
    │                                                                    │
    └────────────────────────────────────────────────────────────────────┘


    COMPLETE SLO EXAMPLES:
    ─────────────────────────────────────────────────────────────────────
    Web frontend:
    • 99.9% of page loads complete in < 2 seconds (28-day rolling)
    • 99.95% of page loads return HTTP 200 (28-day rolling)

    Payment API:
    • 99.99% of payment requests return non-5xx (30-day calendar)
    • 99.9% of payment requests complete in < 1 second (30-day calendar)

    Data pipeline:
    • 99.5% of 10-minute windows: all records processed within 15 min
      of ingestion (28-day rolling)

    Batch job:
    • 99% of daily report jobs complete within 2 hours of scheduled
      start time (quarterly)
```

### 2.2 Setting the Right Target

Setting the SLO target is the hardest part. Too high and you waste engineering resources. Too low and users leave.

```
THE SLO SPECTRUM: TOO HIGH vs TOO LOW
═══════════════════════════════════════════════════════════════════════════════

    TOO HIGH (99.999%)                              TOO LOW (95%)
    ──────────────────                              ─────────────
    • Engineering spends all time                   • Users experience
      on reliability                                  frequent failures
    • No features ship                              • Competitors win
    • Costs skyrocket                               • Revenue drops
    • Innovation dies                               • Trust erodes

    "We're the most reliable                        "It works... sometimes"
     product nobody uses"


    THE SWEET SPOT
    ─────────────────────────────────────────────────────────────────────

    ◀────────────────────────────────────────────────────────────────▶
    99.999%    99.99%    99.95%    99.9%     99.5%     99%      95%
      │          │         │        │         │        │        │
      │          │         │    ┌───┴───┐     │        │        │
      │          │         │    │ SWEET │     │        │        │
      │          │         │    │ SPOT  │     │        │        │
      │          │         │    │(most  │     │        │        │
      │          │         │    │services│    │        │        │
      │          │         │    └───────┘     │        │        │
    Medical   Financial  Critical    Most     Internal  Non-    Prototype
    devices   trading    infra     services   tools   critical
```

**How to find the right target:**

1. **Start with user expectations.** What latency and error rate do users actually notice? Research shows most users tolerate < 1% errors and < 2 seconds for web pages.

2. **Look at your current performance.** If you are at 99.7%, setting an SLO of 99.99% is aspirational, not operational. Set it slightly above current performance to drive improvement.

3. **Consider your dependencies.** Your SLO cannot exceed the reliability of your least reliable critical dependency. If your database delivers 99.95%, your service cannot promise 99.99%.

4. **Factor in cost.** Each additional nine costs roughly 10x more to achieve. Is the marginal improvement worth the investment?

### 2.3 SLO Math: The Dependency Chain

When services depend on each other, reliability multiplies—and multiplying percentages always makes things worse.

```
THE MULTIPLICATION PROBLEM
═══════════════════════════════════════════════════════════════════════════════

    Your service calls 3 dependencies, each at 99.9%:

    ┌───────────┐     ┌───────────┐     ┌───────────┐     ┌───────────┐
    │ Your API  │────▶│ Auth Svc  │     │ Data Svc  │     │ Payment   │
    │           │────▶│  99.9%    │     │  99.9%    │     │  99.9%    │
    │    ???    │────▶│           │     │           │     │           │
    └───────────┘     └───────────┘     └───────────┘     └───────────┘

    If ALL must succeed for your API to succeed:

    Your max SLI = 99.9% × 99.9% × 99.9% = 99.7%

    ┌─────────────────────────────────────────────────────────────────┐
    │  You CANNOT promise 99.9% if your dependencies multiply        │
    │  down to 99.7%. The math doesn't lie.                          │
    └─────────────────────────────────────────────────────────────────┘

    MORE DEPENDENCIES = LOWER CEILING:
    ─────────────────────────────────────────────────────────────────
    1 dependency  at 99.9%  →  Max SLI: 99.9%
    3 dependencies at 99.9% →  Max SLI: 99.7%
    5 dependencies at 99.9% →  Max SLI: 99.5%
    10 dependencies at 99.9% → Max SLI: 99.0%
    20 dependencies at 99.9% → Max SLI: 98.0%

    This is why microservices with deep call chains struggle with
    reliability. Each hop multiplies the failure probability.
```

**Strategies for beating the multiplication problem:**

| Strategy | How It Helps | Example |
|----------|-------------|---------|
| **Caching** | Removes dependency from critical path | Cache auth tokens locally |
| **Graceful degradation** | Non-critical deps can fail without blocking | Show cached data if recommendation service is down |
| **Async processing** | Decouple from real-time dependency | Queue payments, confirm later |
| **Retries with backoff** | Converts transient failures to successes | Retry failed DB reads 3x |
| **Fallbacks** | Alternative path when primary fails | Use secondary data source |

### 2.4 Rolling vs. Calendar Windows

The measurement window matters more than most people realize.

```
ROLLING vs CALENDAR WINDOWS
═══════════════════════════════════════════════════════════════════════════════

CALENDAR WINDOW (e.g., "per calendar month"):
─────────────────────────────────────────────────────────────────────────────

    Jan 1                              Jan 31    Feb 1
    │◄────────── Window 1 ──────────────▶│◄─── Window 2 ───
    │                                     │
    │  Major incident on Jan 30           │  Budget resets!
    │  uses 80% of budget                 │  Full budget again
    │                                     │
    │  Pro: Simple, matches business      │
    │  Con: "End of month reset" gaming   │

ROLLING WINDOW (e.g., "trailing 28 days"):
─────────────────────────────────────────────────────────────────────────────

    ◄──────────── 28 days ──────────────▶
                                          ◄──────── 28 days ──────────▶
    │                                     │
    │  Every hour, the window slides      │
    │  forward. Bad events from 28 days   │
    │  ago "fall off." No sudden reset.   │
    │                                     │
    │  Pro: No gaming, steady pressure    │
    │  Con: Harder to communicate         │

RECOMMENDATION:
─────────────────────────────────────────────────────────────────────────────
• Use ROLLING windows for operational SLOs (engineers)
• Use CALENDAR windows for business SLAs (contracts)
• Pair a long window (28-30 days) for stability with a
  shorter window (7 days) for responsiveness
```

> **Did You Know?**
>
> Slack's engineering team publicly shared that a single hour-long outage costs them an estimated **$8.2 million** in lost productivity across their customer base. This calculation—total paying customers times average hourly productivity value—is exactly the kind of math that justifies investing in SLOs. When you can put a dollar figure on every minute of your error budget, reliability conversations get very concrete very fast.

---

## Part 3: Error Budgets — The Revolutionary Concept

### 3.1 What Is an Error Budget?

Here is the idea that changed the industry: **reliability has a budget, and you can spend it.**

An error budget is the maximum amount of unreliability your SLO permits. It is the gap between 100% and your SLO target.

```
ERROR BUDGET CALCULATION
═══════════════════════════════════════════════════════════════════════════════

    Error Budget = 100% - SLO

    ┌─────────────────────────────────────────────────────────────────┐
    │                                                                 │
    │   SLO: 99.9%                                                    │
    │   Error Budget: 100% - 99.9% = 0.1%                            │
    │                                                                 │
    │   Over 30 days (43,200 minutes):                                │
    │   Budget = 43,200 × 0.001 = 43.2 minutes                       │
    │                                                                 │
    │   Over 30 days (1,000,000 requests):                            │
    │   Budget = 1,000,000 × 0.001 = 1,000 failed requests           │
    │                                                                 │
    └─────────────────────────────────────────────────────────────────┘


COMMON SLO TARGETS AND THEIR BUDGETS (per 30-day month):
─────────────────────────────────────────────────────────────────────────────

    SLO        Error Budget    Time Budget      Request Budget
                                (30 days)        (1M requests)
    ─────────  ──────────────  ──────────────   ──────────────
    99%        1.0%            7 hours 12 min   10,000
    99.5%      0.5%            3 hours 36 min   5,000
    99.9%      0.1%            43.2 minutes     1,000
    99.95%     0.05%           21.6 minutes     500
    99.99%     0.01%           4.32 minutes     100
    99.999%    0.001%          26 seconds       10
```

### 3.2 Why Error Budgets Are Revolutionary

Before error budgets, reliability conversations were political battles. Developers wanted speed. Operations wanted stability. Nobody had a shared framework.

Error budgets change the game by reframing reliability as a **resource to be spent**, not a **virtue to be maximized**.

```
THE OLD WORLD vs THE NEW WORLD
═══════════════════════════════════════════════════════════════════════════════

OLD WORLD: Reliability is a moral imperative
─────────────────────────────────────────────────────────────────────────────

    Developer: "I want to ship the new checkout flow."
    Ops:       "No. Too risky. We had an incident last week."
    Developer: "When CAN I ship?"
    Ops:       "When I feel comfortable."
    Developer: "That's not a real answer."
    Manager:   "Ops, let them ship."
    Ops:       "Fine. But when it breaks, it's not my fault."

    → Result: Resentment, finger-pointing, politics.


NEW WORLD: Reliability is a budget to be spent
─────────────────────────────────────────────────────────────────────────────

    Developer: "I want to ship the new checkout flow."
    SRE:       "Let's check the error budget."
    Dashboard: "28.4 minutes remaining this month (66% left)."
    SRE:       "Similar deploys historically cause ~5 min of errors."
    Developer: "So we can afford it. Budget goes from 66% to 54%."
    SRE:       "Agreed. Ship it. We'll watch the burn rate."

    → Result: Data-driven decision. Shared ownership.
```

Here is the profound insight: **when the budget is healthy, the SRE team should be pushing developers to take MORE risk, not less.** Unused error budget is wasted opportunity. If you can ship a feature that might cause 2 minutes of errors, and you have 28 minutes of budget remaining, shipping is the rational choice.

The error budget makes reliability a **two-sided** constraint:
- **Floor**: Don't burn through the budget (maintain reliability)
- **Ceiling**: Don't hoard the budget (maintain velocity)

### 3.3 Budget Tracking Over Time

Error budget consumption should be tracked continuously, just like a financial budget.

```
ERROR BUDGET TRACKING: A MONTH IN THE LIFE
═══════════════════════════════════════════════════════════════════════════════

SLO: 99.9% | Monthly budget: 43.2 minutes | 1,000 failed requests allowed

Day 1-5:    ██████████████████████████████████████████  100% remaining
            Smooth sailing. No incidents.

Day 6:      ████████████████████████████████████████░░  95% remaining
            Deployment caused 2.1 min of elevated errors.
            Budget: 41.1 min left.

Day 10:     ███████████████████████████████░░░░░░░░░░░  72% remaining
            Database failover. 12 minutes of errors.
            Budget: 29.1 min left.

Day 15:     ██████████████████████████████░░░░░░░░░░░░  67% remaining
            Midpoint check — healthy. Continue shipping.
            Budget: 29.1 min left.

Day 18:     █████████████████████░░░░░░░░░░░░░░░░░░░░░  48% remaining
            Dependency outage. 8 minutes of cascading errors.
            Budget: 21.1 min left.

Day 22:     ██████████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░  30% remaining
            Bad config push. 7.7 minutes of errors.
            Budget: 13.4 min left. Entering WARNING zone.

Day 25:     █████████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░  28% remaining
            Team discussion: freeze risky deploys for rest of month.
            Budget: 12.1 min left.

Day 30:     ████████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░  25% remaining
            Month closes. SLO met. Budget: 10.8 min unused.
            Next month: budget resets.

                    ┌──────────────────────────────────────┐
                    │        ERROR BUDGET POLICY            │
                    ├──────────────────────────────────────┤
                    │  > 50% left  →  Ship freely          │
                    │  25-50% left →  Ship carefully        │
                    │  < 25% left  →  Freeze risky changes  │
                    │  0% or below →  ALL HANDS reliability │
                    └──────────────────────────────────────┘
```

> **Did You Know?**
>
> Google's original SRE book reveals that some teams intentionally **spend their entire error budget** every quarter by running chaos experiments and risky deployments. Their reasoning: if the budget exists to be spent, and you consistently finish the quarter with budget remaining, your SLO might be set too conservatively. An untouched error budget could mean you are over-investing in reliability at the expense of innovation. At Google scale, that over-investment can represent **tens of millions of dollars** in engineering time that could have gone to new features.

---

## Part 4: Burn Rate and Multi-Window Alerting

### 4.1 What Is Burn Rate?

The error budget tells you how much you can spend. The **burn rate** tells you how fast you are spending it.

```
BURN RATE EXPLAINED
═══════════════════════════════════════════════════════════════════════════════

    Burn Rate = (Observed error rate) / (SLO-allowed error rate)

    If your SLO allows 0.1% errors (99.9% SLO):

    ┌─────────────────────────────────────────────────────────────────┐
    │                                                                 │
    │   Burn Rate 1.0  → Consuming budget at exactly the allowed     │
    │                     rate. Budget will hit zero at end of window. │
    │                                                                 │
    │   Burn Rate 2.0  → Consuming budget 2x faster than allowed.    │
    │                     Budget will run out HALFWAY through window.  │
    │                                                                 │
    │   Burn Rate 10.0 → Consuming budget 10x faster.                │
    │                     Budget exhausted in 1/10 of window          │
    │                     (3 days for a 30-day window).               │
    │                                                                 │
    │   Burn Rate 0.5  → Consuming budget at half the allowed rate.  │
    │                     Will finish window with 50% budget left.    │
    │                                                                 │
    │   Burn Rate 0    → No errors at all. Budget untouched.         │
    │                                                                 │
    └─────────────────────────────────────────────────────────────────┘


EXAMPLE:
─────────────────────────────────────────────────────────────────────────────
    SLO: 99.9% over 30 days
    Allowed error rate: 0.1%
    Current error rate: 0.5%

    Burn rate = 0.5% / 0.1% = 5.0

    At burn rate 5, the 30-day budget lasts only 6 days.
    If this continues, you will blow the budget on day 6.
```

### 4.2 Multi-Window Alerting

A single burn rate check is not enough. A brief spike could trigger a false alarm. A slow leak could go unnoticed. The solution is **multi-window alerting**: check burn rate over multiple time windows simultaneously.

```
MULTI-WINDOW BURN RATE ALERTING
═══════════════════════════════════════════════════════════════════════════════

The principle: require BOTH a long window (did enough bad things
happen?) AND a short window (are bad things still happening?) to fire.


FAST BURN ALERT: Catches acute incidents
─────────────────────────────────────────────────────────────────────────────
    Condition: Burn rate > 14.4 over 1 hour
               AND burn rate > 14.4 over 5 minutes

    What this catches: Major outage burning budget 14x too fast
    Time to budget exhaustion: ~2 days
    Action: PAGE the on-call engineer. This is an emergency.

    Example: Deploy breaks 5% of requests
    Normal error rate: 0.1%  →  Observed: 5%  →  Burn rate: 50  →  ALERT


SLOW BURN ALERT: Catches smoldering issues
─────────────────────────────────────────────────────────────────────────────
    Condition: Burn rate > 3 over 6 hours
               AND burn rate > 3 over 30 minutes

    What this catches: Steady degradation burning budget 3x too fast
    Time to budget exhaustion: ~10 days
    Action: Create a TICKET. Investigate during business hours.

    Example: Slow memory leak causes 0.3% errors
    Normal error rate: 0.1%  →  Observed: 0.3%  →  Burn rate: 3  →  ALERT


WHY TWO WINDOWS?
─────────────────────────────────────────────────────────────────────────────
    Long window only:   Fires on spikes that already recovered (noisy)
    Short window only:  Fires on brief blips that don't matter (noisy)
    Both windows:       Fires only when a real problem is ongoing (precise)
```

```
THE BURN RATE → ALERT → ACTION FLOW
═══════════════════════════════════════════════════════════════════════════════

    ┌──────────┐      ┌───────────────┐      ┌──────────────┐
    │   SLO    │─────▶│ Error Budget  │─────▶│  Burn Rate   │
    │  99.9%   │      │ 43.2 min/mo   │      │  Calculation │
    └──────────┘      └───────────────┘      └──────┬───────┘
                                                     │
                                     ┌───────────────┼───────────────┐
                                     │               │               │
                                     ▼               ▼               ▼
                              ┌────────────┐  ┌────────────┐  ┌────────────┐
                              │ Burn > 14  │  │ Burn > 6   │  │ Burn > 3   │
                              │ (1h + 5m)  │  │ (3h + 15m) │  │ (6h + 30m) │
                              └─────┬──────┘  └─────┬──────┘  └─────┬──────┘
                                    │               │               │
                                    ▼               ▼               ▼
                              ┌────────────┐  ┌────────────┐  ┌────────────┐
                              │   PAGE     │  │   PAGE     │  │   TICKET   │
                              │ Immediate  │  │ Urgent     │  │ Next biz   │
                              │ response   │  │ response   │  │ day        │
                              └─────┬──────┘  └─────┬──────┘  └─────┬──────┘
                                    │               │               │
                                    ▼               ▼               ▼
                              ┌────────────┐  ┌────────────┐  ┌────────────┐
                              │ Mitigate   │  │ Investigate│  │ Root cause │
                              │ NOW        │  │ & fix      │  │ & prevent  │
                              └────────────┘  └────────────┘  └────────────┘
```

### 4.3 Why Traditional Alerting Fails

Traditional threshold alerts ("error rate > 1%") suffer from two problems that burn-rate alerts solve:

| Problem | Traditional Alert | Burn Rate Alert |
|---------|-------------------|-----------------|
| **Brief spikes** | Fires alarm, wakes on-call for 30-second blip | Short window clears quickly, no page |
| **Slow degradation** | 0.3% errors never crosses 1% threshold | Burn rate 3.0 detected over 6 hours |
| **Context-free** | "Error rate is high" — so what? | "At this rate, budget exhausted in 10 days" — actionable |
| **One-size-fits-all** | Same threshold regardless of SLO | Alert thresholds derived from the SLO itself |

---

## Part 5: Error Budget Policies

### 5.1 What Happens When the Budget Runs Out?

An error budget without a policy is just a number on a dashboard. The policy defines the **consequences** of budget status, turning the budget into an actual decision-making tool.

```
ERROR BUDGET POLICY FRAMEWORK
═══════════════════════════════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│   BUDGET > 50% REMAINING                                                    │
│   ─────────────────────                                                    │
│   Status: GREEN — Ship freely                                               │
│                                                                             │
│   • Feature development proceeds at full speed                              │
│   • Risky changes (migrations, refactors) are allowed                       │
│   • Chaos experiments encouraged                                            │
│   • On-call load should be light                                            │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   BUDGET 25-50% REMAINING                                                   │
│   ───────────────────────                                                  │
│   Status: YELLOW — Ship carefully                                           │
│                                                                             │
│   • Feature development continues                                           │
│   • Risky changes require extra review and rollback plan                    │
│   • Increase canary duration for deployments                                │
│   • Begin investigating top error contributors                              │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   BUDGET < 25% REMAINING                                                    │
│   ──────────────────────                                                   │
│   Status: RED — Freeze risky changes                                        │
│                                                                             │
│   • Only ship bug fixes, security patches, and reliability work             │
│   • All deployments require SRE approval                                    │
│   • Post-incident reviews for all budget-consuming events                   │
│   • Dedicate 1+ engineers to reliability improvement                        │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   BUDGET EXHAUSTED (0% or negative)                                         │
│   ──────────────────────────────────                                       │
│   Status: BLACK — Reliability emergency                                     │
│                                                                             │
│   • ALL feature work stops until budget recovers                            │
│   • Engineering focus: reduce error rate and prevent recurrence             │
│   • Daily standups on reliability progress                                  │
│   • Leadership briefing on timeline to recovery                             │
│   • Consider: is the SLO set correctly? Or is this a real crisis?           │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 5.2 Who Owns the Policy?

The error budget policy must be **agreed upon in advance** by all stakeholders. If you negotiate the rules during a crisis, politics wins.

| Stakeholder | Role in Error Budget Policy |
|-------------|---------------------------|
| **Product** | Agrees that feature freezes happen when budget is exhausted |
| **Engineering** | Commits to meeting SLO, accepts velocity constraints |
| **SRE / Platform** | Monitors budget, enforces policy, provides tooling |
| **Leadership** | Sponsors the policy, breaks ties, escalation path |

The policy is a **contract between teams**, not a guideline. Writing it down and getting sign-off is essential. When the budget hits zero at 2 PM on a Thursday and product is screaming for the launch to go out Friday, the written policy is what prevents bad decisions.

> **Did You Know?**
>
> According to Gartner research, the average cost of IT downtime across industries is approximately **$5,600 per minute**, or over **$300,000 per hour**. For large enterprises, that number can exceed $1 million per hour. Error budget policies that freeze risky deploys when budget is low directly prevent these costs. A team that spends 3 days on reliability work to avoid a 2-hour outage has saved the business between $600,000 and $2 million—making the error budget policy one of the highest-ROI practices in engineering.

---

## Part 6: Putting It All Together

### 6.1 SLO Design Checklist for New Services

When defining SLOs for a new service, work through this checklist:

```
SLO DESIGN CHECKLIST
═══════════════════════════════════════════════════════════════════════════════

□ 1. IDENTIFY THE USER JOURNEYS
     What are the critical paths users take?
     Example: "User loads dashboard," "User submits payment"

□ 2. CHOOSE SLIs FOR EACH JOURNEY
     What signals best represent user experience?
     Prefer: latency + availability (for most APIs)
     Measure at: the boundary closest to the user

□ 3. SET INITIAL SLO TARGETS
     Start with current performance minus a small buffer
     If currently at 99.95%, start SLO at 99.9%
     You can tighten later — loosening is politically hard

□ 4. CALCULATE ERROR BUDGETS
     100% - SLO = error budget
     Convert to minutes AND request counts

□ 5. DEFINE MEASUREMENT WINDOW
     Rolling 28 days for operational (recommended)
     Calendar month for business reporting

□ 6. CONFIGURE BURN RATE ALERTS
     Fast burn: page for acute incidents
     Slow burn: ticket for chronic degradation

□ 7. WRITE THE ERROR BUDGET POLICY
     What happens at each budget threshold?
     Get sign-off from product, eng, and leadership

□ 8. DOCUMENT ASSUMPTIONS
     Expected traffic volume and shape
     Dependency reliability expectations
     Cache hit rates and fallback behavior

□ 9. PUBLISH AND COMMUNICATE
     SLO dashboard visible to all stakeholders
     Monthly SLO review meeting on calendar
     Runbooks linked to burn rate alerts

□ 10. SCHEDULE QUARTERLY REVIEW
      Is the SLO too tight? Too loose?
      Are the SLIs still measuring the right thing?
      Has the user journey changed?
```

### 6.2 Real-World SLO Examples

Here are SLO designs for three common service types:

**Web Application (E-commerce Frontend)**

| Component | SLI | SLO Target | Window |
|-----------|-----|-----------|--------|
| Page load | Requests completing in < 2s | 99% | 28-day rolling |
| Page load | Requests returning non-5xx | 99.9% | 28-day rolling |
| Checkout | Checkout completing successfully | 99.95% | 28-day rolling |
| Search | Search returning results in < 500ms | 95% | 28-day rolling |

**REST API (Payment Service)**

| Component | SLI | SLO Target | Window |
|-----------|-----|-----------|--------|
| All endpoints | Requests returning non-5xx | 99.99% | 30-day calendar |
| All endpoints | Requests completing in < 1s | 99.9% | 30-day calendar |
| POST /charge | Charges completing correctly | 99.999% | 30-day calendar |

**Data Pipeline (Event Processing)**

| Component | SLI | SLO Target | Window |
|-----------|-----|-----------|--------|
| Ingestion | Events processed within 5 min of arrival | 99.5% | 28-day rolling |
| Processing | 10-min windows with throughput > 10k/min | 99.9% | 28-day rolling |
| Output | Records with correct schema | 99.99% | 28-day rolling |

### 6.3 Common Anti-Patterns

These are the mistakes that even experienced teams make:

| Anti-Pattern | Why It Seems Reasonable | The Problem | Better Approach |
|-------------|------------------------|-------------|----------------|
| **99.999% SLO** | "We want to be world-class" | Budget is 26 seconds/month. ONE slow deploy blows it. Team is paralyzed. | Start at 99.9%, tighten only when you consistently exceed it |
| **Availability-only SLI** | "If it's up, it works" | Misses latency, correctness, throughput. The fintech war story above. | At minimum: availability AND latency SLIs |
| **Internal SLO = External SLA** | "Same number, less confusion" | No buffer for surprises. Every SLO miss triggers contract penalties. | Set internal SLO 2-10x stricter than external SLA |
| **SLO without policy** | "The dashboard is enough" | When budget runs out, nobody knows what to do. Politics decides. | Written policy with stakeholder sign-off |
| **Too many SLIs** | "Measure everything!" | Alert fatigue. Nobody knows which SLI matters most. | 1-3 SLIs per user journey. One primary, rest secondary. |
| **Ignoring dependencies** | "Each team manages their own SLO" | Your 99.99% SLO can't survive three 99.9% dependencies multiplied together. | Map dependency chain, set SLOs accordingly |
| **Never revising SLOs** | "We set it, we're done" | Business changes, user expectations change, architecture changes. | Quarterly SLO reviews with all stakeholders |
| **Using averages** | "Average latency is 50ms" | Average hides the P99 at 8 seconds. 1% of users rage-quit. | Use percentiles: P50, P90, P95, P99 |
| **Measuring at the server** | "Our app reports 99.99% success" | Misses load balancer errors, network issues, DNS failures. | Measure at the edge closest to the user |
| **Gaming the budget** | "Deploys on day 1 when budget is full" | Concentrates risk, creates month-start chaos. | Rolling windows prevent gaming |

---

## Did You Know?

- **Google's Ads system reportedly loses approximately $200,000 per minute** during latency degradation at peak hours. This single fact explains why Google invented SLOs—when each minute has a six-figure price tag, you need a framework that tells you exactly how many minutes you can afford to lose.

- **The SLO concept predates software engineering.** Manufacturing companies have used Statistical Process Control (SPC) since the 1920s. Walter Shewhart at Bell Labs invented control charts to distinguish "normal variation" from "something is wrong"—the same principle behind error budgets. The SLO is the control limit; the error budget is the acceptable variation.

- **Slack reported that a single hour-long outage costs their customers an estimated $8.2 million** in lost productivity. Their SLO program helped reduce major incidents by 60% in the first year—saving their customer base roughly **$50 million annually** in avoided productivity losses.

- **Amazon's internal rule of thumb**: every 100ms of latency on their retail site costs approximately **$1 billion in annual revenue**. This is why their SLIs measure latency at the P99.9 level, not just availability. The difference between "the site is up" and "the site is fast" is measured in billions.

---

## Common Mistakes

| Mistake | What It Looks Like | Why It's Wrong | How to Fix It |
|---------|-------------------|----------------|---------------|
| **Setting SLOs based on aspirations** | "We should be at 99.99%" without measuring current state | Team immediately fails the SLO, loses trust in the framework | Measure current reliability first, set SLO slightly above |
| **Using server-side metrics as SLIs** | "Our application reports 0% errors" | Server can't see network failures, DNS issues, or load balancer drops | Measure at the load balancer or with synthetic probes |
| **Averaging latency** | "Mean response time: 80ms — we're fine!" | Mean hides a P99 of 12 seconds. 1% of users see terrible performance. | Always use percentiles: P50, P90, P95, P99 |
| **SLO without error budget tracking** | Team has a target but no dashboard | Can't make velocity/reliability trade-offs because nobody knows the budget status | Implement real-time budget tracking visible to all |
| **No error budget policy** | "We'll figure it out when the budget runs out" | When it happens, it's a political negotiation, not a data-driven decision | Write the policy BEFORE you need it. Get sign-off. |
| **One SLI for everything** | "99.9% availability" covers the whole service | Latency degradation, data correctness, throughput drops are all invisible | Define separate SLIs for each critical dimension |
| **Setting SLO tighter than dependencies allow** | 99.99% SLO when your database is at 99.95% | Mathematically impossible to achieve. Team burns out trying. | Map dependency reliability. Your SLO <= weakest critical dep. |
| **Never reviewing or adjusting SLOs** | Same SLO for 3 years despite architecture changes | SLO no longer reflects user expectations or system capabilities | Quarterly SLO reviews. Adjust based on data. |
| **Treating SLO breaches as incidents** | Every time SLI dips below SLO, someone gets paged | SLOs are targets over a window, not instantaneous thresholds | Alert on burn rate, not on instantaneous SLI value |
| **Confusing SLOs and SLAs** | Publishing internal SLO targets as contractual SLAs | No buffer for unexpected events. SLO miss = financial penalty. | SLA should be looser than SLO. SLO is your internal standard. |

---

## Quiz

Test your understanding of SLIs, SLOs, and error budgets:

**1. Your service has an SLO of 99.5% availability over a 30-day window. How many minutes of downtime does your error budget allow?**

<details>
<summary>Answer</summary>

**Calculation:**
- 30 days = 30 x 24 x 60 = 43,200 minutes
- Error budget = 100% - 99.5% = 0.5%
- Budget in minutes = 43,200 x 0.005 = **216 minutes (3 hours 36 minutes)**

This means you can tolerate a total of 3 hours and 36 minutes of downtime per month. That's generous enough for most teams to ship aggressively while maintaining reliability.
</details>

**2. Why is "average latency < 100ms" a bad SLI? What should you use instead?**

<details>
<summary>Answer</summary>

Averages are bad SLIs because they **hide tail latency**. Consider this distribution:

- 990,000 requests at 50ms
- 10,000 requests at 5,000ms (5 seconds!)

Average = (990,000 x 50 + 10,000 x 5000) / 1,000,000 = **99.5ms**

The average says "everything is fine" while 1% of users (10,000 requests) wait 5 seconds. For a service handling 1 million requests per day, that is 10,000 terrible user experiences **every day**.

**Better SLI:** "99th percentile latency < 500ms"

This directly measures the worst common experience. If P99 is under 500ms, you know that at least 99% of users have an acceptable experience. The remaining 1% might still be slow, which is why some teams also track P99.9 or P99.99.
</details>

**3. Your service depends on three other services, each with 99.9% availability. What is the maximum availability your service can achieve (assuming all three must succeed for your service to succeed)?**

<details>
<summary>Answer</summary>

**Calculation:**
- Maximum availability = 99.9% x 99.9% x 99.9%
- = 0.999 x 0.999 x 0.999
- = 0.999^3
- = **99.7%**

This means even if your own code is perfect, your service can at best achieve 99.7% availability. Setting an SLO of 99.9% would be mathematically impossible without strategies like caching, graceful degradation, or async processing to decouple from dependencies.

**Lesson:** Always map your dependency chain before setting your SLO. The math constrains what is achievable.
</details>

**4. Explain the difference between an SLO and an SLA. Why should they be different numbers?**

<details>
<summary>Answer</summary>

- **SLO (Service Level Objective):** An internal target that your team aims for. No contractual consequences for missing it—just operational signals.
- **SLA (Service Level Agreement):** A contractual promise to customers. Missing it triggers financial penalties (credits, refunds).

They should be different because the SLO should be **stricter** than the SLA:

| | SLO (Internal) | SLA (External) |
|--|----------------|----------------|
| Target | 99.95% | 99.9% |
| Consequence of miss | Error budget policy kicks in | Financial credits owed |
| Audience | Engineering team | Customers/legal |

The gap between SLO and SLA is your **safety margin**. If your SLO is 99.95% and your SLA is 99.9%, you have room to miss your internal target without triggering contractual penalties. If they are the same number, every SLO miss is also a contract breach.
</details>

**5. Your SLO is 99.9% over 30 days. You are currently seeing a 0.5% error rate. What is the burn rate, and how long until your budget is exhausted?**

<details>
<summary>Answer</summary>

**Burn rate calculation:**
- SLO-allowed error rate = 100% - 99.9% = 0.1%
- Current error rate = 0.5%
- Burn rate = 0.5% / 0.1% = **5.0**

**Time to exhaustion:**
- At burn rate 1.0, budget lasts exactly 30 days
- At burn rate 5.0, budget lasts 30 / 5 = **6 days**

If this error rate started today and continues unchanged, you will completely exhaust your 30-day error budget in 6 days. This should trigger a fast-burn alert (burn rate > 3 over a sustained window) and prompt immediate investigation.
</details>

**6. A team sets their SLO at 99.999% (five nines). They handle 10 million requests per month. Why might this SLO be harmful?**

<details>
<summary>Answer</summary>

**The math:**
- Error budget = 100% - 99.999% = 0.001%
- Allowed failed requests = 10,000,000 x 0.00001 = **100 requests per month**
- Time budget = 43,200 minutes x 0.00001 = **0.43 minutes (26 seconds)**

**Why this is harmful:**

1. **26 seconds of total downtime per month.** A single slow deployment, a brief network blip, or one DNS hiccup blows the entire budget.

2. **100 failed requests per month.** Normal background noise from network issues and client timeouts often exceeds this. The team will be in permanent SLO violation.

3. **Paralysis.** The team cannot deploy, cannot experiment, cannot take any risk. All energy goes to reliability. No features ship.

4. **Demoralization.** Constantly failing the SLO kills trust in the framework. The team stops paying attention to it.

5. **Cost.** Achieving five nines requires multi-region deployment, automated failover, zero-downtime deployments, and dedicated reliability engineering—potentially millions of dollars per year.

**Better approach:** Start at 99.9% (1,000 allowed failures, 43 minutes of budget). If you consistently beat it, tighten to 99.95%. Let the data guide you upward.
</details>

**7. What is a multi-window burn rate alert, and why is it better than a simple threshold alert like "error rate > 1%"?**

<details>
<summary>Answer</summary>

A **multi-window burn rate alert** requires the burn rate to exceed a threshold over both a long window (e.g., 1 hour) AND a short window (e.g., 5 minutes) before firing.

**Why it is better than "error rate > 1%":**

| Scenario | Threshold Alert | Multi-Window Burn Rate |
|----------|----------------|----------------------|
| 30-second error spike, then recovery | FIRES (noisy page at 3 AM) | Does NOT fire (short window clears) |
| Slow leak: 0.3% error rate for 6 hours | Does NOT fire (below 1% threshold) | FIRES (burn rate 3.0 sustained) |
| 2% error rate for 2 hours | FIRES (correct) | FIRES (correct, with budget context) |

**Additional advantages:**
- Alert message includes burn rate and time-to-exhaustion, which is immediately actionable
- Thresholds are derived from the SLO, not arbitrary guesses
- Different severity levels (fast burn = page, slow burn = ticket) reduce alert fatigue
</details>

**8. Your team's error budget was exhausted on day 18 of the month. Product insists on shipping a major feature this week. Using the error budget policy framework, what should happen?**

<details>
<summary>Answer</summary>

According to the error budget policy framework, when the budget is exhausted (0% or negative), the team enters **BLACK status — reliability emergency**:

1. **ALL feature work stops** until budget recovers or the window resets
2. Engineering focus shifts entirely to reducing error rate and preventing recurrence
3. Daily standups on reliability progress
4. Leadership briefing on recovery timeline

**For the product request specifically:**

- The written policy (agreed upon in advance by product, engineering, and leadership) says feature work is frozen
- This is NOT the SRE blocking product. This is the **pre-agreed policy** being enforced.
- If product believes this particular feature is critical enough to override the policy, they must escalate to leadership, who explicitly accepts the risk of further SLO violation
- The override should be documented—this is spending money you don't have

**Why the policy matters here:** Without a pre-agreed policy, this becomes a political fight at the worst possible time. With the policy, it is a clear decision framework. The answer was decided months ago, in calm conditions, by all stakeholders.
</details>

---

## Hands-On Exercise: Calculate Error Budgets for a Real Scenario

### Scenario

You are the newly hired SRE for **ShopFast**, an e-commerce platform. The CEO has asked you to define SLOs for three critical services. Here is the current monitoring data from the last 30 days:

```
SHOPFAST MONITORING DATA (Last 30 Days)
═══════════════════════════════════════════════════════════════════════════════

SERVICE 1: Product Catalog API
─────────────────────────────────────────────────────────────────────────────
  Total requests:           50,000,000
  Failed requests (5xx):    25,000
  Requests > 500ms:         750,000
  Requests > 2 seconds:     50,000
  Incidents this month:     2 (total downtime: 45 minutes)

SERVICE 2: Checkout/Payment API
─────────────────────────────────────────────────────────────────────────────
  Total requests:           2,000,000
  Failed requests (5xx):    100
  Requests > 1 second:      40,000
  Requests > 5 seconds:     2,000
  Incidents this month:     1 (total downtime: 12 minutes)

SERVICE 3: Order Processing Pipeline (batch)
─────────────────────────────────────────────────────────────────────────────
  Total orders processed:   500,000
  Orders processed > 5 min: 5,000
  Orders with wrong status: 15
  Pipeline stalls:          3 (total stall time: 90 minutes)
```

### Part 1: Define SLIs (10 minutes)

For each service, define at least two SLIs. Express each as "good events / total events."

```
YOUR SLI DEFINITIONS
═══════════════════════════════════════════════════════════════════════════════

Service 1: Product Catalog API

  SLI 1 (Availability): _____ / _____
  SLI 2 (Latency):      _____ / _____

Service 2: Checkout/Payment API

  SLI 1 (Availability): _____ / _____
  SLI 2 (Latency):      _____ / _____

Service 3: Order Processing Pipeline

  SLI 1 (Freshness):    _____ / _____
  SLI 2 (Correctness):  _____ / _____
```

### Part 2: Calculate Current SLI Values (10 minutes)

Using the monitoring data, calculate the actual value of each SLI.

```
YOUR CALCULATIONS
═══════════════════════════════════════════════════════════════════════════════

Service 1: Product Catalog API
  Availability SLI:  (_________ - _________) / _________ = _______%
  Latency SLI (500ms): (_________ - _________) / _________ = _______%

Service 2: Checkout/Payment API
  Availability SLI:  (_________ - _________) / _________ = _______%
  Latency SLI (1s):  (_________ - _________) / _________ = _______%

Service 3: Order Processing Pipeline
  Freshness SLI (5min): (_________ - _________) / _________ = _______%
  Correctness SLI:      (_________ - _________) / _________ = _______%
```

### Part 3: Set SLOs and Calculate Error Budgets (10 minutes)

Based on current performance and user expectations, propose an SLO for each SLI. Then calculate the error budget.

```
YOUR SLO PROPOSALS
═══════════════════════════════════════════════════════════════════════════════

Service 1: Product Catalog API
  Availability SLO: _______% → Budget: _______ failed requests / month
  Latency SLO:      _______% → Budget: _______ slow requests / month

Service 2: Checkout/Payment API
  Availability SLO: _______% → Budget: _______ failed requests / month
  Latency SLO:      _______% → Budget: _______ slow requests / month

Service 3: Order Processing Pipeline
  Freshness SLO:    _______% → Budget: _______ late orders / month
  Correctness SLO:  _______% → Budget: _______ incorrect orders / month
```

### Part 4: Assess Budget Status (5 minutes)

For each SLO you proposed, is the service currently within budget, in warning, or over budget?

```
BUDGET STATUS ASSESSMENT
═══════════════════════════════════════════════════════════════════════════════

  Service 1 Availability:  [ ] Green  [ ] Yellow  [ ] Red  [ ] Over budget
  Service 1 Latency:       [ ] Green  [ ] Yellow  [ ] Red  [ ] Over budget

  Service 2 Availability:  [ ] Green  [ ] Yellow  [ ] Red  [ ] Over budget
  Service 2 Latency:       [ ] Green  [ ] Yellow  [ ] Red  [ ] Over budget

  Service 3 Freshness:     [ ] Green  [ ] Yellow  [ ] Red  [ ] Over budget
  Service 3 Correctness:   [ ] Green  [ ] Yellow  [ ] Red  [ ] Over budget
```

### Part 5: Write a Recommendation (5 minutes)

Which service needs the most attention? What would you prioritize?

---

<details>
<summary>Check Your Work — Sample Answers</summary>

**Part 1 & 2: SLI Definitions and Current Values**

Service 1: Product Catalog API
- Availability SLI: (50M - 25K) / 50M = **99.95%**
- Latency SLI (< 500ms): (50M - 750K) / 50M = **98.5%**

Service 2: Checkout/Payment API
- Availability SLI: (2M - 100) / 2M = **99.995%**
- Latency SLI (< 1s): (2M - 40K) / 2M = **98.0%**

Service 3: Order Processing Pipeline
- Freshness SLI (< 5 min): (500K - 5K) / 500K = **99.0%**
- Correctness SLI: (500K - 15) / 500K = **99.997%**

**Part 3: Proposed SLOs and Error Budgets**

Service 1: Product Catalog API
- Availability SLO: **99.9%** (current: 99.95% — comfortable margin)
  - Budget: 50M x 0.001 = 50,000 failed requests/month
  - Currently using: 25,000 (50% of budget — GREEN)
- Latency SLO: **98%** (current: 98.5% — tight but achievable)
  - Budget: 50M x 0.02 = 1,000,000 slow requests/month
  - Currently using: 750,000 (75% of budget — YELLOW)

Service 2: Checkout/Payment API
- Availability SLO: **99.99%** (current: 99.995% — justified for payments)
  - Budget: 2M x 0.0001 = 200 failed requests/month
  - Currently using: 100 (50% of budget — GREEN)
- Latency SLO: **97%** (current: 98% — margin to improve)
  - Budget: 2M x 0.03 = 60,000 slow requests/month
  - Currently using: 40,000 (67% of budget — YELLOW)

Service 3: Order Processing Pipeline
- Freshness SLO: **98.5%** (current: 99% — healthy)
  - Budget: 500K x 0.015 = 7,500 late orders/month
  - Currently using: 5,000 (67% of budget — YELLOW)
- Correctness SLO: **99.99%** (current: 99.997% — correctness matters most for orders)
  - Budget: 500K x 0.0001 = 50 incorrect orders/month
  - Currently using: 15 (30% of budget — GREEN)

**Part 5: Recommendation**

**Priority 1: Product Catalog Latency.** At 98.5% with a proposed 98% SLO, this service is skating close to the edge. 750,000 requests per month take over 500ms. This directly impacts user browsing experience and conversion rates. Investigate the slow requests—are they specific product pages? Specific regions? A slow database query?

**Priority 2: Checkout Latency.** 40,000 payment requests taking over 1 second is a conversion killer. Users abandon carts when checkout is slow. This has direct revenue impact.

**Priority 3: Pipeline Freshness.** 5,000 orders taking over 5 minutes to process is concerning but less urgent since it does not directly affect the real-time user experience. Monitor the trend.

</details>

---

**Success Criteria:**
- [ ] Defined at least 2 SLIs per service in ratio format
- [ ] Calculated all 6 current SLI values correctly
- [ ] Proposed reasonable SLOs (not too tight, not too loose)
- [ ] Calculated error budgets correctly for each SLO
- [ ] Assessed budget status for all 6 SLIs
- [ ] Identified the highest-priority service with justification

---

## Key Takeaways

```
SLI / SLO / ERROR BUDGET FUNDAMENTALS
═══════════════════════════════════════════════════════════════════════════════

□ SLI = what you measure (good events / total events)
  Choose SLIs that reflect REAL user experience, not server health.

□ SLO = your target for the SLI over a time window
  Set based on user needs and current capability, not aspirations.

□ Error budget = 100% - SLO = how much failure you can afford
  This is not a failure threshold. It is PERMISSION to take risks.

□ Burn rate = how fast you are consuming the budget
  Use multi-window alerts: fast burn (page) + slow burn (ticket).

□ Error budget policy = what happens at each budget level
  Written and agreed upon BEFORE you need it. Not negotiated in crisis.

□ Measure at the user boundary
  Load balancer > API gateway > application code > database metrics.

□ Use percentiles, not averages
  P99 tells you about the worst common experience. Averages lie.

□ Dependencies multiply
  Three 99.9% dependencies = 99.7% ceiling. Map the chain.

□ Review quarterly
  SLOs are living documents. Adjust as systems and users change.

□ The SLO is both a floor AND a ceiling
  Below SLO: stabilize. Above SLO: innovate faster.
```

---

## Further Reading

**Books:**

- **"Site Reliability Engineering"** — Google (free online). Chapters 4-5 cover SLIs, SLOs, and error budgets from the team that created the framework. The original source.

- **"The Site Reliability Workbook"** — Google (free online). Chapters 2-4 provide practical implementation guidance with worked examples and template SLO documents.

- **"Implementing Service Level Objectives"** — Alex Hidalgo. The only book dedicated entirely to SLOs. Covers theory, implementation, and organizational change. Essential reading for SLO practitioners.

**Papers and Articles:**

- **"The Calculus of Service Availability"** — Google. Formalizes the mathematics behind SLO-based alerting and error budget calculations.

- **"Alerting on SLOs like Pros"** — Google Cloud blog. Practical guide to multi-window, multi-burn-rate alerting.

**Talks:**

- **"SLOs Are the API for Your Reliability"** — Liz Fong-Jones (YouTube). Excellent explanation of why SLOs matter and how to implement them culturally.

- **"Setting SLOs and Error Budgets"** — Seth Vargo (YouTube). Hands-on walkthrough of SLO design with real-world examples.

---

## Where to Go Next

This module covered the **theory** of SLIs, SLOs, and error budgets. The following modules build on this foundation with operational practice and tooling:

- [Module 2.1: What Is Reliability](module-2.1-what-is-reliability/) — Review the reliability fundamentals if any concepts here felt unclear
- **Module 1.2: SLO Discipline** (Disciplines track) — How to operationalize SLOs day-to-day: reviews, reporting, cultural adoption
- **Module 1.3: Error Budget Management** (Disciplines track) — Deep dive on budget policies, negotiation, and organizational alignment
- **Module 1.10: SLO Tooling — Sloth/Pyrra** (Toolkits track) — Hands-on with tools that automate SLO calculation, burn rate alerting, and budget dashboards

---

*"An SLO is a contract with your users about what 'good enough' means. Without it, every conversation about reliability is just an argument."* — Adapted from the Google SRE handbook
