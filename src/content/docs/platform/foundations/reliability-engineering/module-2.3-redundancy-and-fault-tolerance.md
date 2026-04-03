---
title: "Module 2.3: Redundancy and Fault Tolerance"
slug: platform/foundations/reliability-engineering/module-2.3-redundancy-and-fault-tolerance
sidebar:
  order: 4
---
> **Complexity**: `[MEDIUM]`
>
> **Time to Complete**: 35-40 minutes
>
> **Prerequisites**: [Module 2.2: Failure Modes and Effects](../module-2.2-failure-modes-and-effects/)
>
> **Track**: Foundations

### What You'll Be Able to Do

After completing this module, you will be able to:

1. **Design** redundancy architectures (active-active, active-passive, N+1) appropriate for different failure domains and cost constraints
2. **Evaluate** whether redundant components are truly independent or share hidden common-cause failure modes
3. **Implement** fault-tolerance patterns including leader election, quorum-based writes, and cross-region failover
4. **Analyze** the tradeoffs between redundancy cost, recovery time, and data durability for a given service tier

---

## The $150 Million Lesson in Independence

**January 15, 2009. New York City. 3:26 PM.**

US Airways Flight 1549 lifts off from LaGuardia Airport. Captain Chesley "Sully" Sullenberger has 19,000 flying hours. First Officer Jeff Skiles manages the controls as they climb over the Bronx.

At 2,800 feet, the unthinkable happens.

A flock of Canada geese strikes the aircraft. Both engines ingest multiple birds. Within seconds, both engines lose thrust. The cockpit fills with the smell of burning birds.

The aircraft has dual redundant engines—but both failed simultaneously. This is a **correlated failure**—a single cause (bird strike) taking out multiple redundant components.

But the Airbus A320 has something else: triple-redundant fly-by-wire controls, independent hydraulic systems, and an auxiliary power unit. The plane can still fly. It can still be controlled.

Sully has 208 seconds to find somewhere to land a commercial aircraft in the most densely populated city in America.

The answer: the Hudson River.

All 155 souls aboard survive. The aircraft, worth $60 million, is destroyed.

But here's what made it possible: **independence**. The hydraulic systems didn't share fluid lines. The flight computers didn't share power supplies. The bird strike killed the engines, but the redundancy that mattered—the ability to control the aircraft—remained intact.

**This is the lesson of redundancy**: It's not about having two of everything. It's about ensuring that when one thing fails, the backup is still working.

In software systems, the parallel is exact. Having two database replicas doesn't help if they're on the same physical server. Having three availability zones doesn't help if they share a power grid. Having ten microservice instances doesn't help if they all connect to the same overloaded dependency.

The question isn't "Do you have redundancy?" The question is: **"When component A fails, why is component B still working?"**

---

## Why This Module Matters

You've identified how your system can fail. Now, how do you keep it working when those failures happen?

The answer is **redundancy**—having more than one of critical components so that when one fails, another can take over. But redundancy isn't just "add more servers." Done wrong, it adds complexity without adding reliability. Done right, it lets your system survive failures that would otherwise cause outages.

This module teaches you to think about redundancy as an engineering discipline: when to use it, how to implement it, and the trade-offs involved.

```
THE REDUNDANCY PARADOX
═══════════════════════════════════════════════════════════════════════════════

Many teams add redundancy and actually DECREASE reliability.

How is this possible?

SIMPLE SYSTEM (99% reliable)
────────────────────────────────────────────────────────────────
    [Component A] ───────────▶ Output

    Reliability: 99%
    Failure: 1 in 100 requests

"LET'S ADD REDUNDANCY!"
────────────────────────────────────────────────────────────────

    [Component A] ──┐             ┌─────────────┐
                    ├── Failover ─┤ Routing Logic├──▶ Output
    [Component B] ──┘   Logic     │  (complex)  │
                                  └─────────────┘

    A reliability: 99%
    B reliability: 99%
    Failover logic: 90% (untested, has bugs)

    Actual reliability = 99% + (1% × 90% × 99%) = 99.89%

    Wait... that's barely better than before!

    And if failover logic is only 50% reliable?

    Actual reliability = 99% + (1% × 50% × 99%) = 99.49%

    ⚠️  WORSE THAN NO REDUNDANCY!

THE LESSON
────────────────────────────────────────────────────────────────
Redundancy only works if:
1. Components fail INDEPENDENTLY
2. Failover mechanism is TESTED
3. Complexity doesn't outweigh benefit
```

> **The Airplane Analogy**
>
> Commercial aircraft have redundant everything: multiple engines, multiple hydraulic systems, multiple flight computers, multiple pilots. But it's not just duplication—each redundant system is designed to be **independent**. Separate power sources, separate wiring paths, separate maintenance schedules. The goal isn't just "more," it's "independent."

---

## What You'll Learn

- Types of redundancy and when to use each
- The difference between high availability and fault tolerance
- Active-passive vs. active-active architectures
- Common redundancy patterns in distributed systems
- The hidden costs and risks of redundancy

---

## Part 1: Understanding Redundancy

### 1.1 What is Redundancy?

**Redundancy** is having extra components beyond the minimum required for normal operation, so the system can continue if some components fail.

```
REDUNDANCY BASICS
═══════════════════════════════════════════════════════════════

NO REDUNDANCY (Single Point of Failure)
────────────────────────────────────────
    Request ──▶ [Service] ──▶ Response
                    │
                If fails → Outage

WITH REDUNDANCY
────────────────────────────────────────
                ┌─────────┐
    Request ──▶ │Service A│ ──▶ Response
                └────┬────┘
                     │ fails
                ┌────▼────┐
                │Service B│ ──▶ Response (continued)
                └─────────┘
```

### 1.2 Types of Redundancy

| Type | Description | Example |
|------|-------------|---------|
| **Hardware redundancy** | Multiple physical components | RAID arrays, dual power supplies |
| **Software redundancy** | Multiple service instances | 3 replicas of a pod |
| **Data redundancy** | Multiple copies of data | Database replication |
| **Geographic redundancy** | Multiple locations | Multi-region deployment |
| **Temporal redundancy** | Retry over time | Automatic retry with backoff |
| **Informational redundancy** | Extra data for validation | Checksums, parity bits |

```
THE SIX TYPES OF REDUNDANCY - FIELD GUIDE
═══════════════════════════════════════════════════════════════════════════════

1. HARDWARE REDUNDANCY
────────────────────────────────────────────────────────────────
   What: Multiple physical components
   Where: Disks, power supplies, network cards, servers

   ┌─────────────────────────────────────────────────────────┐
   │  Server with Dual Power Supplies                       │
   │                                                        │
   │    PSU A ──┬──▶ Components                            │
   │            │                                           │
   │    PSU B ──┘    (If PSU A fails, PSU B keeps running) │
   │                                                        │
   └─────────────────────────────────────────────────────────┘

   Cost: $$$ (physical hardware)
   Complexity: Low
   Common pitfall: Same power circuit for both PSUs

2. SOFTWARE REDUNDANCY
────────────────────────────────────────────────────────────────
   What: Multiple instances of the same service
   Where: Web servers, API gateways, workers

   ┌─────────────────────────────────────────────────────────┐
   │                 Load Balancer                          │
   │                      │                                 │
   │         ┌────────────┼────────────┐                   │
   │         ▼            ▼            ▼                   │
   │    [Pod A]      [Pod B]      [Pod C]                  │
   │                                                        │
   │    Same code, same config, interchangeable            │
   │                                                        │
   └─────────────────────────────────────────────────────────┘

   Cost: $$ (compute)
   Complexity: Medium
   Common pitfall: Shared downstream dependency (single DB)

3. DATA REDUNDANCY
────────────────────────────────────────────────────────────────
   What: Multiple copies of the same data
   Where: Databases, caches, object storage

   ┌─────────────────────────────────────────────────────────┐
   │                                                        │
   │    [Primary DB] ──sync──▶ [Replica 1]                │
   │         │                                              │
   │         └─────sync──▶ [Replica 2]                    │
   │                                                        │
   │    Every write goes to 3 places                       │
   │                                                        │
   └─────────────────────────────────────────────────────────┘

   Cost: $$$$ (3x storage, replication overhead)
   Complexity: High
   Common pitfall: Replication lag, split-brain

4. GEOGRAPHIC REDUNDANCY
────────────────────────────────────────────────────────────────
   What: Same system in multiple physical locations
   Where: Data centers, cloud regions

   ┌─────────────────────────────────────────────────────────┐
   │                                                        │
   │      US-EAST              EU-WEST             AP-SOUTH │
   │    ┌─────────┐         ┌─────────┐         ┌─────────┐│
   │    │  App    │         │  App    │         │  App    ││
   │    │  DB     │◀───────▶│  DB     │◀───────▶│  DB     ││
   │    └─────────┘         └─────────┘         └─────────┘│
   │                                                        │
   │    Survive entire region failure                      │
   │    Serve users from nearest location                  │
   │                                                        │
   └─────────────────────────────────────────────────────────┘

   Cost: $$$$$ (3x infrastructure + cross-region traffic)
   Complexity: Very High
   Common pitfall: Latency, consistency, split-brain

5. TEMPORAL REDUNDANCY
────────────────────────────────────────────────────────────────
   What: Retry failed operations over time
   Where: Network calls, queue processing, batch jobs

   ┌─────────────────────────────────────────────────────────┐
   │                                                        │
   │    Request ──▶ Fail                                   │
   │           └──▶ Retry (100ms later) ──▶ Fail          │
   │                         └──▶ Retry (200ms) ──▶ Success│
   │                                                        │
   │    The same operation, repeated until it works        │
   │                                                        │
   └─────────────────────────────────────────────────────────┘

   Cost: $ (just time)
   Complexity: Low
   Common pitfall: Retry storms, idempotency issues

6. INFORMATIONAL REDUNDANCY
────────────────────────────────────────────────────────────────
   What: Extra data to detect/correct errors
   Where: Storage, network transmission

   ┌─────────────────────────────────────────────────────────┐
   │                                                        │
   │    Original data:  [A B C D]                          │
   │    With checksum:  [A B C D | CRC32]                  │
   │                                                        │
   │    If data corrupts, checksum won't match → detected  │
   │                                                        │
   │    With ECC:       [A B C D | parity bits]            │
   │    Can actually CORRECT single bit errors             │
   │                                                        │
   └─────────────────────────────────────────────────────────┘

   Cost: ~5-15% storage overhead
   Complexity: Low (usually built into hardware/protocols)
   Common pitfall: Silent data corruption (bit rot)
```

### 1.3 Redundancy Notation: N+M

Redundancy is often expressed as N+M:
- **N** = minimum needed for normal operation
- **M** = extra for failure tolerance

```
REDUNDANCY NOTATION - THE COMPLETE GUIDE
═══════════════════════════════════════════════════════════════════════════════

N+0: NO REDUNDANCY (Single Point of Failure)
────────────────────────────────────────────────────────────────
    [A] ───▶ Output

    If A fails → OUTAGE
    Survives: 0 failures
    Use case: Dev environment, non-critical batch jobs

N+1: ONE SPARE
────────────────────────────────────────────────────────────────
    [A] [B] ───▶ Output

    Load: Either can handle 100% alone
    If A fails → B takes over
    Survives: 1 failure
    Use case: Most production systems

    ⚠️  DURING MAINTENANCE:
    Take A down for patching → only B left (now N+0)
    If B fails during maintenance → OUTAGE

N+2: TWO SPARES (Maintenance + Failure)
────────────────────────────────────────────────────────────────
    [A] [B] [C] ───▶ Output

    Load: Any two can handle 100%
    If A fails → B and C continue
    Survives: 2 failures OR 1 failure during maintenance
    Use case: Critical production, financial services

    ✓ DURING MAINTENANCE:
    Take A down for patching → B and C remain (N+1)
    If B fails during maintenance → C continues

2N: FULL DUPLICATION
────────────────────────────────────────────────────────────────
    Site 1:  [A₁] [B₁] [C₁]     Active
                   │
                   │ replication
                   │
    Site 2:  [A₂] [B₂] [C₂]     Standby (or Active)

    Complete mirror of entire system
    Survives: Entire site failure
    Use case: Disaster recovery, regulatory compliance

2N+1: FULL DUPLICATION PLUS SPARE
────────────────────────────────────────────────────────────────
    Site 1:  [A₁] [B₁] [C₁]     Active
                   │
    Site 2:  [A₂] [B₂] [C₂]     Active
                   │
    Site 3:  [A₃]               Witness/Tiebreaker

    Survives: Entire site failure + one more component
    Use case: Mission-critical, global financial systems

CAPACITY PLANNING REALITY CHECK
────────────────────────────────────────────────────────────────

    "We have 3 replicas for redundancy!"

    But what's the LOAD on each replica?

    3 replicas at 80% CPU each:
    ┌────────────────────────────────────────────┐
    │ [Pod A: 80%]  [Pod B: 80%]  [Pod C: 80%] │
    └────────────────────────────────────────────┘

    If Pod A fails, traffic redistributes:
    ┌────────────────────────────────────────────┐
    │     ✗        [Pod B: 120%] [Pod C: 120%] │
    │              ↑ OVERLOADED! ↑              │
    └────────────────────────────────────────────┘

    For true N+1, each replica must handle 50% of total load
    For true N+2, each replica must handle 33% of total load

    FORMULA:
    Max load per replica = Total Load ÷ (Number of replicas - tolerated failures)
```

> **Gotcha: N+1 Isn't Always Enough**
>
> N+1 protects against single failures, but what about during maintenance? If you have 3 servers (N+1 where N=2) and take one down for updates, you're now at N+0. If another fails, you're down. Consider N+2 for critical systems to allow for maintenance + one unexpected failure.

> **The Math of Simultaneous Failures**
>
> Why is N+2 often necessary? Consider a system with N+1 redundancy (3 servers where 2 can handle the load). If each server has 99% availability, what's the chance of two failing at the same time?
>
> Naive calculation: 1% × 1% = 0.01% (1 in 10,000) — seems rare!
>
> But failures aren't independent. Common causes include:
> - Same software version → same bug affects all
> - Same rack → same power failure affects all
> - Same deployment → bad config affects all
> - Cascading failure → one failure causes another
>
> In practice, simultaneous failures happen more often than math suggests.

---

## Part 2: High Availability vs. Fault Tolerance

### 2.1 The Distinction

These terms are often used interchangeably, but they're fundamentally different engineering approaches with different costs, complexities, and use cases.

| Aspect | High Availability (HA) | Fault Tolerance (FT) |
|--------|------------------------|----------------------|
| Goal | Minimize downtime | Zero downtime |
| During failure | Brief interruption okay | No interruption |
| Data loss | May lose in-flight data | No data loss |
| Cost | Moderate | High |
| Complexity | Moderate | High |
| Use case | Most web services | Financial, medical, aviation |

```
HIGH AVAILABILITY vs FAULT TOLERANCE - THE REAL DIFFERENCE
═══════════════════════════════════════════════════════════════════════════════

HIGH AVAILABILITY (HA)
────────────────────────────────────────────────────────────────
Time: ──────────────────────────────────────────────────────────────▶

      Normal Operation    Failure    Recovery    Normal Operation
      ████████████████████ ▒▒▒▒▒▒▒▒ ███████████████████████████████
                          ↑        ↑
                          │        │
                     Detection  Failover
                     (seconds)  (seconds to minutes)

User Experience:
  - 10:00:00 - Page loads fine
  - 10:00:05 - Server crashes
  - 10:00:07 - Health check fails (detection)
  - 10:00:10 - Failover triggered
  - 10:00:15 - New server ready
  - 10:00:15 - "Please try again" message during 10-second window
  - 10:00:16 - Page loads fine again

What Happens to In-Flight Requests:
  Request A: Started at 10:00:04, completed at 10:00:04 ✓
  Request B: Started at 10:00:05, ERROR - connection reset ✗
  Request C: Started at 10:00:15, completed at 10:00:15 ✓

FAULT TOLERANCE (FT)
────────────────────────────────────────────────────────────────
Time: ──────────────────────────────────────────────────────────────▶

      Normal Operation    Failure    (Seamless)   Normal Operation
      █████████████████████████████████████████████████████████████
                          ↑
                          │
                     Primary fails, secondary
                     continues INSTANTLY

User Experience:
  - 10:00:00 - Page loads fine
  - 10:00:05 - Primary server crashes (user doesn't know)
  - 10:00:05 - Secondary server handles request (user doesn't know)
  - 10:00:06 - Page loads fine (user never noticed)

What Happens to In-Flight Requests:
  Request A: Started at 10:00:04, completed at 10:00:04 ✓
  Request B: Started at 10:00:05, handed off, completed at 10:00:06 ✓
  Request C: Started at 10:00:06, completed at 10:00:06 ✓

THE COST DIFFERENCE
────────────────────────────────────────────────────────────────

HIGH AVAILABILITY                    FAULT TOLERANCE

Infrastructure:                      Infrastructure:
  2-3 servers                          2× everything (synchronized)
  Load balancer                        Specialized hardware
  Health checks                        Real-time state replication

Complexity:                          Complexity:
  Detect failure (seconds)             Continuous synchronization
  Route away from failed node          Lock-step execution
  Restart/replace failed node          Zero-switch-time handoff

Cost multiplier: 2-3×                Cost multiplier: 4-10×

Why FT costs so much more:
  - Synchronous replication (every write waits for acknowledgment)
  - Specialized hardware (VMware FT, Stratus systems)
  - Network latency budget (must be < switch time)
  - Complex failure detection (can't be slow, can't be wrong)
```

### 2.2 When to Use Which

**High Availability is usually sufficient when:**
- Brief outages are acceptable
- Retrying failed requests is okay
- Cost matters
- Simpler architecture is valuable

**Fault Tolerance is required when:**
- Any downtime is unacceptable
- Transactions can't be retried
- Legal/regulatory requirements
- Lives depend on the system

```
THE HA vs FT DECISION FRAMEWORK
═══════════════════════════════════════════════════════════════════════════════

ASK THESE QUESTIONS:

1. "Can the user retry?"
   ├── YES → HA is probably fine
   │         (Web pages, API calls, most interactions)
   │
   └── NO → Consider FT
             (Wire transfers mid-transaction, surgical robots)

2. "What's the cost of a 30-second outage?"
   ├── Annoying → HA
   │   (Blog down, users wait)
   │
   ├── Expensive → Strong HA
   │   (E-commerce checkout, lost sales)
   │
   └── Catastrophic → FT
       (Stock trading, medical devices)

3. "Is there regulatory/compliance requirement?"
   ├── NO → Design based on business needs
   │
   └── YES → Check specific requirements
       - PCI-DSS doesn't mandate FT
       - Aviation DO-178C does mandate FT
       - Financial services vary by jurisdiction

4. "What's your budget multiplier?"
   ├── 2-3× acceptable → HA achievable
   │
   └── 4-10× acceptable → FT achievable

DECISION MATRIX
────────────────────────────────────────────────────────────────

                        │ Retry OK │ Retry Not OK │
────────────────────────┼──────────┼──────────────┤
Low cost of outage      │   HA     │    HA        │
────────────────────────┼──────────┼──────────────┤
High cost of outage     │ Strong HA│    FT        │
────────────────────────┼──────────┼──────────────┤
Lives at stake          │   FT     │    FT        │
────────────────────────┴──────────┴──────────────┘
```

> **Try This (2 minutes)**
>
> Classify these systems—do they need HA or FT?
>
> | System | HA or FT? | Why? |
> |--------|-----------|------|
> | Blog | | |
> | Online banking | | |
> | Aircraft control | | |
> | E-commerce checkout | | |
> | Pacemaker | | |
>
> <details>
> <summary>See Answers</summary>
>
> | System | HA or FT? | Why? |
> |--------|-----------|------|
> | Blog | HA | Users can refresh, low cost of outage |
> | Online banking | Strong HA → FT for transfers | Viewing balance: HA. Wire transfer mid-execution: FT |
> | Aircraft control | FT | Lives at stake, no retry possible at 30,000 feet |
> | E-commerce checkout | Strong HA | Lost sales hurt, but users can retry |
> | Pacemaker | FT | Life-critical, no "please try again" for heartbeats |
>
> </details>

---

## Part 3: Redundancy Architectures

### 3.1 Active-Passive (Standby)

One component handles traffic; others wait to take over.

```
ACTIVE-PASSIVE
═══════════════════════════════════════════════════════════════

NORMAL OPERATION
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│    Traffic ──▶ [Active: Primary] ──▶ Response              │
│                                                             │
│                [Passive: Standby] ← (idle, syncing)        │
│                                                             │
└─────────────────────────────────────────────────────────────┘

AFTER FAILOVER
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│                [Failed: Primary] ✗                         │
│                                                             │
│    Traffic ──▶ [Now Active: Standby] ──▶ Response          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Characteristics:**
- Simpler to implement
- Standby capacity is "wasted" during normal operation
- Failover takes time (seconds to minutes)
- Risk: Standby may have stale data or config

**Use when:**
- Cost is a concern
- You can tolerate brief failover time
- Traffic doesn't justify multiple active instances

### 3.2 Active-Active (Load Shared)

All components handle traffic simultaneously.

```
ACTIVE-ACTIVE
═══════════════════════════════════════════════════════════════

NORMAL OPERATION
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│                ┌──▶ [Active: Node A] ──┐                   │
│                │                        │                   │
│    Traffic ──▶ LB                       ├──▶ Response       │
│                │                        │                   │
│                └──▶ [Active: Node B] ──┘                   │
│                                                             │
└─────────────────────────────────────────────────────────────┘

AFTER NODE A FAILS
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│                     [Failed: Node A] ✗                     │
│                                                             │
│    Traffic ──▶ LB ──▶ [Active: Node B] ──▶ Response        │
│                                                             │
│    (All traffic now handled by B; may need to scale)       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Characteristics:**
- All capacity is used during normal operation
- No failover time—traffic immediately routes away from failed node
- More complex (need to handle shared state)
- Better resource utilization

**Use when:**
- Traffic justifies multiple instances
- You need instant failover
- Workload can be distributed

### 3.3 Comparison

| Aspect | Active-Passive | Active-Active |
|--------|----------------|---------------|
| Resource usage | ~50% (standby idle) | ~100% |
| Failover time | Seconds to minutes | Instant |
| Complexity | Lower | Higher |
| State management | Sync to standby | Distributed state |
| Scaling | Limited | Horizontal |
| Cost efficiency | Lower | Higher |

> **Did You Know?**
>
> Most cloud load balancers use active-active architecture internally. AWS ELB, for example, runs across multiple availability zones with all nodes active. When one fails, traffic is simply not sent there—no failover needed because there's no single "active" node.

---

## Part 4: Redundancy Patterns

### 4.1 Database Replication

```
DATABASE REPLICATION PATTERNS
═══════════════════════════════════════════════════════════════

PRIMARY-REPLICA (Read Scaling)
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│    Writes ──▶ [Primary] ──sync──▶ [Replica 1]              │
│                   │                                         │
│                   └───sync──▶ [Replica 2]                  │
│                                                             │
│    Reads ───▶ [Any Replica] ──▶ Response                   │
│                                                             │
│    + Read scalability                                       │
│    - Single write point, replication lag                   │
│                                                             │
└─────────────────────────────────────────────────────────────┘

MULTI-PRIMARY (Write Scaling)
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│    Writes ──▶ [Primary A] ◀──sync──▶ [Primary B]           │
│                                                             │
│    + Write scalability                                      │
│    - Conflict resolution complexity                        │
│    - Harder to reason about consistency                    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 4.2 Kubernetes Redundancy

```
KUBERNETES POD REDUNDANCY
═══════════════════════════════════════════════════════════════

Deployment: replicas: 3

┌──────────────────────────────────────────────────────────┐
│  Node 1           Node 2           Node 3               │
│  ┌─────────┐      ┌─────────┐      ┌─────────┐         │
│  │  Pod A  │      │  Pod B  │      │  Pod C  │         │
│  └─────────┘      └─────────┘      └─────────┘         │
└──────────────────────────────────────────────────────────┘

                          │
                    Service (LB)
                          │
                     ┌────┴────┐
                     │ Traffic │
                     └─────────┘

If Pod A fails:
- Kubernetes detects via health check
- Traffic routes to B and C
- New pod scheduled automatically
```

```yaml
# Kubernetes deployment with redundancy
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api-server
spec:
  replicas: 3                    # N+2 redundancy
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxUnavailable: 1          # Always keep 2 running
      maxSurge: 1
  template:
    spec:
      affinity:
        podAntiAffinity:         # Spread across nodes
          requiredDuringSchedulingIgnoredDuringExecution:
          - labelSelector:
              matchLabels:
                app: api-server
            topologyKey: kubernetes.io/hostname
      containers:
      - name: api
        resources:
          requests:
            cpu: 100m
            memory: 128Mi
        livenessProbe:           # Detect failures
          httpGet:
            path: /health
            port: 8080
          periodSeconds: 10
        readinessProbe:          # Route traffic only when ready
          httpGet:
            path: /ready
            port: 8080
          periodSeconds: 5
```

### 4.3 Multi-Region Redundancy

```
MULTI-REGION ARCHITECTURE
═══════════════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────────────┐
│                        Global DNS                           │
│                    (Route53, CloudFlare)                    │
│                           │                                 │
│           ┌───────────────┼───────────────┐                │
│           │               │               │                 │
│           ▼               ▼               ▼                 │
│    ┌──────────┐    ┌──────────┐    ┌──────────┐           │
│    │ Region A │    │ Region B │    │ Region C │           │
│    │ (US-East)│    │ (EU-West)│    │ (AP-SE)  │           │
│    │          │    │          │    │          │           │
│    │ [App]    │    │ [App]    │    │ [App]    │           │
│    │ [DB Pri] │◀──▶│ [DB Rep] │◀──▶│ [DB Rep] │           │
│    │          │    │          │    │          │           │
│    └──────────┘    └──────────┘    └──────────┘           │
│                                                             │
│    Benefits:                                                │
│    - Survive entire region failure                         │
│    - Lower latency for global users                        │
│    - Disaster recovery                                      │
│                                                             │
│    Challenges:                                              │
│    - Cross-region data replication lag                     │
│    - Complexity of distributed state                       │
│    - Cost (3x infrastructure)                              │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 4.4 Circuit Breaker Pattern

Not traditional redundancy, but enables graceful handling when redundancy fails:

```
CIRCUIT BREAKER
═══════════════════════════════════════════════════════════════

States:
┌─────────┐     failures > threshold     ┌─────────┐
│ CLOSED  │ ─────────────────────────▶  │  OPEN   │
│(normal) │                              │(failing)│
└─────────┘                              └────┬────┘
     ▲                                        │
     │                                   timeout
     │         ┌──────────┐                  │
     └─────────│HALF-OPEN │◀─────────────────┘
    success    │ (testing)│
               └──────────┘
                    │
               failure → back to OPEN

Implementation:
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│   Request ──▶ Circuit Breaker ──▶ Service                  │
│                     │                                       │
│               (if OPEN)                                     │
│                     │                                       │
│                     └──▶ Fallback Response                 │
│                         (cached data, default, error)      │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

> **Try This (3 minutes)**
>
> Your service calls a payment provider. Design the circuit breaker:
>
> - After how many failures should it open?
> - How long before trying again (half-open)?
> - What's the fallback response?

---

## Part 5: The Costs of Redundancy

### 5.1 Redundancy Isn't Free

```
THE COSTS OF REDUNDANCY
═══════════════════════════════════════════════════════════════

FINANCIAL COSTS
─────────────────────────────────────────────────────────────
- 2x or 3x infrastructure costs
- Cross-region data transfer fees
- Additional monitoring/management tools
- More complex debugging (more places to look)

COMPLEXITY COSTS
─────────────────────────────────────────────────────────────
- More moving parts = more failure modes
- State synchronization challenges
- Split-brain scenarios
- Harder to reason about behavior

OPERATIONAL COSTS
─────────────────────────────────────────────────────────────
- More deployments to manage
- More configuration to keep in sync
- More capacity planning complexity
- Testing redundancy (does failover actually work?)
```

### 5.2 Common Redundancy Failures

| Failure | What Happens | Prevention |
|---------|--------------|------------|
| **Correlated failure** | Both primary and backup fail together | Independent failure domains |
| **Split brain** | Both think they're primary | Proper leader election, fencing |
| **Replication lag** | Backup has stale data | Monitor lag, consider sync replication |
| **Untested failover** | Failover doesn't work when needed | Regular failover drills |
| **Config drift** | Backup has different config | Infrastructure as code, sync config |

### 5.3 The Redundancy Paradox

> **Did You Know?**
>
> Adding redundancy can sometimes *decrease* reliability. More components means more things that can fail. If the redundancy mechanism itself is complex, it adds failure modes. A 2013 study found that ~30% of failures at large internet companies involved failure of the failover mechanism itself.

```
THE REDUNDANCY PARADOX
═══════════════════════════════════════════════════════════════

Simple system:
    Component A ─── Reliability: 99%

"More reliable" with redundancy:
    Component A ───┐
                   ├─── Failover Logic ─── Output
    Component B ───┘

    A reliability: 99%
    B reliability: 99%
    Failover reliability: 95%

    System reliability = P(A works) + P(A fails) × P(failover works) × P(B works)
                      = 0.99 + 0.01 × 0.95 × 0.99
                      = 0.99 + 0.0094
                      = 99.94%

    But if failover has bugs...

    Failover reliability: 50% (untested, has bugs)
    System reliability = 0.99 + 0.01 × 0.50 × 0.99 = 99.49%

    WORSE than no redundancy!
```

**Lesson**: Redundancy only helps if the failover mechanism is reliable. Test it regularly.

> **War Story: The Backup That Wasn't**
>
> A financial services company had "highly available" PostgreSQL: a primary with streaming replication to a standby. They were proud of their architecture diagrams. They never tested failover.
>
> When the primary failed, they triggered manual failover. The standby came up—with a 6-hour replication lag. Transactions from the last 6 hours were gone. It turned out monitoring had been alerting on lag for months, but the alerts went to a distribution list nobody read.
>
> Recovery took 3 days: restore from backup, replay transaction logs, reconcile with payment processors, apologize to customers. The CEO learned what "replication lag" means the hard way.
>
> Now they run failover drills monthly. They verify replication lag every deploy. And someone actually reads the alerts.

```
WAR STORY: THE $8.6 MILLION UNTESTED FAILOVER
═══════════════════════════════════════════════════════════════════════════════

TIMELINE OF DISASTER
────────────────────────────────────────────────────────────────

                ARCHITECTURE (looked great on paper)
                ┌─────────────────────────────────────────────────┐
                │                                                 │
                │  [Primary PostgreSQL] ──streaming──▶ [Standby] │
                │       us-east-1a              replication  1b   │
                │                                                 │
                │  "We're highly available!"                      │
                │  "We have a replica!"                           │
                │                                                 │
                └─────────────────────────────────────────────────┘

WHAT NOBODY NOTICED (for 7 months):

  Monitoring Dashboard (ignored):
  ┌────────────────────────────────────────────────────────────┐
  │  Replication Lag: 6h 23m 17s  ← ⚠️  CRITICAL              │
  │  Alert Status: Firing since March 15th                    │
  │  Recipients: ops-alerts@company.com (unmonitored mailbox) │
  └────────────────────────────────────────────────────────────┘

THE DAY IT HAPPENED - October 15th:

  02:14 AM  Primary database server: disk controller fails
            └── All writes stop immediately
            └── Connection queue fills in 3 seconds
            └── Application errors cascade

  02:15 AM  On-call engineer paged
            └── "Database unreachable"
            └── Checks primary: dead
            └── Triggers manual failover to standby

  02:19 AM  Standby promoted to primary
            └── Application reconnects
            └── Traffic flowing again
            └── "Incident resolved" (narrator: it wasn't)

  02:47 AM  Customer service: "Customers calling about missing transactions"
            └── Order placed at 11:00 PM = gone
            └── Payment at 8:00 PM = gone
            └── Everything since 8 PM = gone

  02:52 AM  Engineer checks: standby was 6 hours behind
            └── 6 hours of transactions = lost
            └── WAL files still on dead primary
            └── Cannot access dead primary (disk controller dead)

  03:00 AM  Executive escalation begins

RECOVERY (3 painful days):

  Day 1: Forensics
    - Send dead server to data recovery specialist
    - Find last good backup: 24 hours old
    - Begin planning manual reconciliation

  Day 2: Reconstruction
    - Data recovery extracts WAL files from dead disk
    - Replay transactions on backup
    - Cross-reference with payment processor logs
    - Identify 847 affected transactions

  Day 3: Cleanup
    - Customer notification (847 customers)
    - Manual transaction correction
    - Regulatory notification (required by law)
    - Post-incident review begins

FINANCIAL IMPACT
────────────────────────────────────────────────────────────────

  Direct costs:
    Data recovery service:                    $45,000
    Customer compensation:                   $127,000
    Emergency consulting:                     $89,000
    Regulatory fine:                         $500,000
    ─────────────────────────────────────────────────
    Direct total:                            $761,000

  Indirect costs:
    Customer churn (next quarter):         $2,100,000
    Brand damage (estimated):              $3,200,000
    Engineering time (post-incident):        $340,000
    Insurance premium increase:              $180,000
    Delayed product launch:                $2,000,000
    ─────────────────────────────────────────────────
    Indirect total:                        $7,820,000

  TOTAL IMPACT:                            $8,581,000

ROOT CAUSES
────────────────────────────────────────────────────────────────

  1. Never tested failover
     └── Would have discovered lag immediately

  2. Alerts to unmonitored mailbox
     └── Classic "alert fatigue to alert ignore" pipeline

  3. No replication lag SLO
     └── "It's replicating" ≠ "It's usable for failover"

  4. Manual failover process
     └── Took 4 minutes instead of seconds
     └── No automated verification before promotion

WHAT THEY DO NOW
────────────────────────────────────────────────────────────────

  ✓ Monthly failover drills (automated)
  ✓ Replication lag < 1 second SLO
  ✓ Alerts page on-call (not email)
  ✓ Pre-failover verification: "Is replica caught up?"
  ✓ Synchronous replication for critical tables
  ✓ Quarterly chaos engineering (kill primary in production)
```

---

## Did You Know?

- **RAID 5 lost data** at major companies because the rebuild process (after one disk failed) stressed the remaining disks, causing a second failure before rebuild completed. RAID 6 (which tolerates two failures) is now recommended for large arrays.

- **The DNS root servers** use Anycast—the same IP address is announced from multiple locations. Your request goes to the nearest one. If one fails, routing protocols automatically send you elsewhere. No failover logic needed.

- **Google's Borg** (precursor to Kubernetes) was designed around the assumption that machines will fail. Jobs are automatically rescheduled when machines die. Google expects ~1% of machines to fail per year, so redundancy isn't optional—it's the default.

- **The "Pets vs. Cattle" metaphor** for servers was coined by Bill Baker at Microsoft. Pets have names, are irreplaceable, and get nursed back to health when sick. Cattle have numbers, are identical, and get replaced when sick. Modern cloud-native redundancy assumes cattle: any instance is expendable.

---

## Common Mistakes

| Mistake | Problem | Solution |
|---------|---------|----------|
| Same failure domain | Both replicas fail together | Spread across zones/regions |
| Not testing failover | Failover doesn't work | Regular chaos engineering |
| Sync replication everywhere | Performance impact | Use async where eventual consistency okay |
| Ignoring replication lag | Read your own writes fails | Read from primary after write |
| No health checks | Traffic sent to failed node | Implement proper health checks |
| Manual failover | Slow recovery | Automate failover |

---

## Quiz

1. **What does N+2 redundancy mean, and why might you choose it over N+1?**
   <details>
   <summary>Answer</summary>

   N+2 means having two spare components beyond the minimum needed for normal operation.

   Why N+2 over N+1:
   - **Maintenance**: With N+1, if you take one component down for maintenance, you're at N+0. Another failure causes an outage. N+2 allows maintenance + one unexpected failure.
   - **Rolling updates**: During deployment, you temporarily have one fewer healthy component.
   - **Concurrent failures**: While rare, two components can fail close together, especially if there's a common cause (bad deploy, correlated failure).

   N+2 is common for critical systems where maintenance windows are frequent or where the cost of outage is high.
   </details>

2. **What's the key difference between high availability and fault tolerance?**
   <details>
   <summary>Answer</summary>

   **High Availability (HA)**: System remains operational with minimal downtime. Brief interruptions during failure are acceptable. In-flight requests may fail but new requests succeed quickly.

   **Fault Tolerance (FT)**: System continues operating without any interruption. No requests fail, even during component failure. Typically uses synchronous replication and instant failover.

   HA is cheaper and simpler; FT is more expensive and complex. Most web services use HA because users can retry. Financial transactions, medical systems, and aviation control need FT because any failure can have serious consequences.
   </details>

3. **Why might active-active be preferred over active-passive for a web service?**
   <details>
   <summary>Answer</summary>

   Active-active advantages:
   1. **No failover time**: Traffic immediately routes away from failed nodes
   2. **Better resource utilization**: All capacity handles traffic (passive nodes are "wasted")
   3. **No standby staleness**: All nodes are processing real traffic, so config and behavior are validated
   4. **Horizontal scaling**: Easy to add more active nodes as load increases
   5. **Geographic distribution**: Can serve users from nearest active node

   Active-passive is simpler and may be preferred when:
   - Traffic is low
   - Stateful workloads are hard to distribute
   - Cost of idle standby is acceptable
   </details>

4. **How can adding redundancy actually decrease reliability?**
   <details>
   <summary>Answer</summary>

   Redundancy can decrease reliability when:

   1. **Failover mechanism is unreliable**: If the code/process that detects failure and switches to backup is buggy or untested, it can fail to failover or failover incorrectly.

   2. **Added complexity introduces bugs**: More components = more code = more potential bugs. The redundancy management layer itself can fail.

   3. **Split-brain scenarios**: Both nodes think they're primary, causing data corruption or conflicts.

   4. **Correlated failures**: If redundant components share a failure domain (same rack, same code bug, same config), they can fail together.

   5. **Masking problems**: Redundancy can hide underlying issues until they affect enough components to cause an outage.

   Prevention: Test failover regularly, keep redundancy mechanisms simple, use independent failure domains.
   </details>

5. **Your team has 3 pods running at 70% CPU each. They claim this is N+1 redundancy. Is it? Calculate what happens if one pod fails.**
   <details>
   <summary>Answer</summary>

   **No, this is NOT true N+1 redundancy.**

   Calculation:
   - Current total load: 3 pods × 70% = 210% of one pod's capacity
   - If one pod fails, load redistributes to 2 pods
   - Load per remaining pod: 210% ÷ 2 = 105% CPU

   **Each pod would be overloaded (105% > 100%)**, leading to degraded performance or cascading failure.

   For true N+1 with 3 pods:
   - Two pods must handle total load alone
   - Maximum load per pod = Total Load ÷ 2 = 50%
   - At 70% each, this is actually N+0.5 (one partial failure away from degradation)

   **Fix**: Either add a 4th pod (N+2) or reduce per-pod load to ~50%.
   </details>

6. **What is split-brain, and how does it occur in active-passive systems?**
   <details>
   <summary>Answer</summary>

   **Split-brain** occurs when both nodes in an active-passive cluster believe they are the active node, leading to two "primaries" operating simultaneously.

   How it happens:
   1. Network partition between primary and standby
   2. Standby can't reach primary, assumes primary is dead
   3. Standby promotes itself to primary
   4. Original primary is still alive, still accepting writes
   5. Two primaries accepting writes = data divergence

   Consequences:
   - Data corruption (conflicting writes)
   - Data loss (when trying to reconcile)
   - Application errors (inconsistent state)

   Prevention:
   - **Fencing**: Kill the old primary before promoting standby (STONITH - "Shoot The Other Node In The Head")
   - **Quorum**: Require majority agreement before leadership changes
   - **Witness nodes**: Third node breaks ties
   - **Shared storage with locks**: Only one node can write at a time
   </details>

7. **Why is geographic redundancy more complex than single-region redundancy?**
   <details>
   <summary>Answer</summary>

   Geographic redundancy adds complexity in several dimensions:

   1. **Latency**: Cross-region network calls are 50-200ms vs. 1-5ms within region. Synchronous replication becomes expensive.

   2. **Consistency**: Either accept replication lag (eventual consistency) or pay latency penalty (strong consistency). CAP theorem applies.

   3. **Data sovereignty**: Some data can't leave certain regions (GDPR, data residency laws).

   4. **Network partitions**: Regions can become isolated from each other. Need to handle "split brain" at region level.

   5. **Operational complexity**:
      - Deploy to multiple regions
      - Monitor multiple regions
      - Incident response spans time zones
      - Testing is harder

   6. **Cost**: 2-3× infrastructure plus cross-region data transfer fees.

   7. **DNS/Routing**: Need global load balancing, health checks across regions, failover routing.

   Geographic redundancy is worth it for: disaster recovery, serving global users, regulatory compliance. Overkill for: single-market applications, cost-sensitive workloads.
   </details>

---

## Hands-On Exercise

**Task**: Design and test redundancy for a Kubernetes deployment.

**Part A: Create a Redundant Deployment (15 minutes)**

```bash
# Create namespace
kubectl create namespace redundancy-lab

# Create a deployment with redundancy
cat <<EOF | kubectl apply -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web-app
  namespace: redundancy-lab
spec:
  replicas: 3
  selector:
    matchLabels:
      app: web-app
  template:
    metadata:
      labels:
        app: web-app
    spec:
      affinity:
        podAntiAffinity:
          preferredDuringSchedulingIgnoredDuringExecution:
          - weight: 100
            podAffinityTerm:
              labelSelector:
                matchLabels:
                  app: web-app
              topologyKey: kubernetes.io/hostname
      containers:
      - name: nginx
        image: nginx:alpine
        ports:
        - containerPort: 80
        readinessProbe:
          httpGet:
            path: /
            port: 80
          initialDelaySeconds: 2
          periodSeconds: 3
        livenessProbe:
          httpGet:
            path: /
            port: 80
          initialDelaySeconds: 5
          periodSeconds: 5
        resources:
          requests:
            cpu: 50m
            memory: 64Mi
---
apiVersion: v1
kind: Service
metadata:
  name: web-app
  namespace: redundancy-lab
spec:
  selector:
    app: web-app
  ports:
  - port: 80
    targetPort: 80
EOF
```

**Part B: Verify Redundancy (5 minutes)**

```bash
# Check pods are distributed
kubectl get pods -n redundancy-lab -o wide

# Check service endpoints
kubectl get endpoints web-app -n redundancy-lab
```

**Part C: Test Failover (10 minutes)**

Terminal 1 - Watch pods:
```bash
kubectl get pods -n redundancy-lab -w
```

Terminal 2 - Simulate failure:
```bash
# Delete one pod
kubectl delete pod -n redundancy-lab -l app=web-app \
  $(kubectl get pod -n redundancy-lab -l app=web-app -o jsonpath='{.items[0].metadata.name}')

# Observe:
# - Pod terminates
# - New pod is scheduled
# - Endpoints update
```

Terminal 2 - More aggressive failure:
```bash
# Delete two pods simultaneously
kubectl delete pod -n redundancy-lab -l app=web-app \
  $(kubectl get pod -n redundancy-lab -l app=web-app -o jsonpath='{.items[0].metadata.name} {.items[1].metadata.name}')

# Observe: System recovers even with 2/3 pods gone
```

**Part D: Test PodDisruptionBudget (5 minutes)**

```bash
# Add a PodDisruptionBudget
cat <<EOF | kubectl apply -f -
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: web-app-pdb
  namespace: redundancy-lab
spec:
  minAvailable: 2
  selector:
    matchLabels:
      app: web-app
EOF

# Try to drain a node (if you have multiple nodes)
# kubectl drain <node-name> --ignore-daemonsets --delete-emptydir-data

# The PDB will prevent draining if it would leave fewer than 2 pods
```

**Part E: Clean Up**

```bash
kubectl delete namespace redundancy-lab
```

**Analysis Questions:**
1. How long did it take for a new pod to become ready after deletion?
2. Did the service maintain endpoints during the failure?
3. What would happen if all 3 pods were deleted simultaneously?
4. How does podAntiAffinity improve reliability?

**Success Criteria**:
- [ ] Deployment created with 3 replicas
- [ ] Pod anti-affinity configured
- [ ] Single pod failure tested and recovered
- [ ] Multi-pod failure tested and recovered
- [ ] Understand what PodDisruptionBudget does

---

## Key Takeaways

```
REDUNDANCY AND FAULT TOLERANCE - WHAT TO REMEMBER
═══════════════════════════════════════════════════════════════════════════════

THE CORE PRINCIPLE
────────────────────────────────────────────────────────────────
Redundancy is about INDEPENDENCE, not DUPLICATION.

    ✗ "We have two servers"
    ✓ "We have two servers that fail independently"

If the same event can take out both your primary and backup,
you don't have redundancy—you have expensive duplication.

THE CHECKLIST
────────────────────────────────────────────────────────────────
Before calling your system "redundant," verify:

[ ] Components are in different failure domains
    └── Different racks? Different zones? Different regions?

[ ] Failover mechanism is tested regularly
    └── When did you last kill production to verify?

[ ] Capacity math works out
    └── N+1 means remaining components handle 100% load

[ ] Replication lag is monitored and acceptable
    └── Async replication = potential data loss in failover

[ ] Health checks actually detect failures
    └── Does "healthy" mean "can serve traffic"?

[ ] Recovery is automated or has runbook
    └── Manual failover at 3 AM: how fast can you do it?

THE DECISION FRAMEWORK
────────────────────────────────────────────────────────────────

1. HIGH AVAILABILITY (99.9%): Most applications
   - Brief interruption okay
   - Users can retry
   - 2-3× cost multiplier

2. FAULT TOLERANCE (99.999%): Critical systems only
   - Zero interruption
   - Lives or major money at stake
   - 4-10× cost multiplier

THE REDUNDANCY LEVELS
────────────────────────────────────────────────────────────────

N+0: No redundancy (dev only)
N+1: Survive one failure (most production)
N+2: Survive maintenance + failure (critical production)
2N:  Survive entire site failure (disaster recovery)

THE ARCHITECTURES
────────────────────────────────────────────────────────────────

ACTIVE-PASSIVE: Simple, wasted capacity, failover delay
ACTIVE-ACTIVE: Complex, efficient, instant failover

Choose active-active when:
- Traffic justifies multiple instances
- You need instant failover
- Workload can be distributed

THE WARNING SIGNS
────────────────────────────────────────────────────────────────

🚩 "We've never tested failover" = It won't work when needed
🚩 "Both replicas are in the same AZ" = Single failure domain
🚩 "Each pod runs at 80% CPU" = No headroom for failover
🚩 "Alerts go to an email list" = Nobody's watching
🚩 "We have replication lag" = Potential data loss

THE PARADOX
────────────────────────────────────────────────────────────────

Adding redundancy can DECREASE reliability if:
- Failover mechanism is buggy or untested
- Components share hidden dependencies
- Complexity exceeds team's ability to understand
- Split-brain scenarios aren't handled

Simpler redundancy, tested regularly > Complex redundancy, never tested
```

---

## Further Reading

- **"Designing Data-Intensive Applications"** - Martin Kleppmann. Chapters on replication and fault tolerance are essential reading for anyone building distributed systems.

- **"Site Reliability Engineering"** - Google. Chapter 26 on "Data Integrity" covers redundancy patterns at scale.

- **"Building Microservices"** - Sam Newman. Practical patterns for service redundancy and deployment.

- **"Release It!"** - Michael Nygard. The "Stability Patterns" chapter covers circuit breakers, bulkheads, and other redundancy patterns.

- **Netflix Tech Blog** - Their posts on "Chaos Engineering" and "Fault Injection" show how to test redundancy in practice.

- **Jepsen.io** - Kyle Kingsbury's distributed systems testing. Shows how "redundant" databases actually behave under failure.

---

## Next Module

[Module 2.4: Measuring and Improving Reliability](../module-2.4-measuring-and-improving-reliability/) - SLIs, SLOs, and the practice of continuous reliability improvement.
