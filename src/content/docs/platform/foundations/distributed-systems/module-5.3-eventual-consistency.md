---
title: "Module 5.3: Eventual Consistency"
slug: platform/foundations/distributed-systems/module-5.3-eventual-consistency
sidebar:
  order: 4
---
> **Complexity**: `[MEDIUM]`
>
> **Time to Complete**: 30-35 minutes
>
> **Prerequisites**: [Module 5.2: Consensus and Coordination](module-5.2-consensus-and-coordination/)
>
> **Track**: Foundations

---

**December 26, 2012. Amazon's retail website experiences intermittent failures during the busiest shopping week of the year—and the root cause is surprisingly simple: they chose the wrong consistency model for their inventory system.**

Amazon's engineers had designed a strongly consistent inventory system. Every purchase required immediate confirmation from all database replicas before the customer saw "Order Confirmed." This worked perfectly at normal load. But on the day after Christmas, with millions of gift card recipients flooding the site, the synchronous replication became a bottleneck. Database replicas couldn't keep up, write latency spiked to 30+ seconds, and shopping carts started timing out.

**For 49 minutes, an estimated $66,000 per minute in potential revenue was lost**—not because servers were down, but because the system was waiting for perfect consistency that customers didn't actually need.

The irony: customers don't need to know the exact inventory count. They need to know if they can buy the item. Amazon's post-incident analysis led to a fundamental architecture shift: use eventual consistency everywhere possible, reserve strong consistency only for the actual purchase transaction.

**The lesson rippled through the industry.** Amazon's 2007 Dynamo paper, describing their eventually consistent key-value store, became the blueprint for Cassandra, Riak, and DynamoDB. The paper's core insight: for most data, "close enough" consistency with high availability beats perfect consistency that fails under load.

This module teaches eventual consistency—when to use it, how to design for it, and the patterns that make it work in production.

---

## Why This Module Matters

Strong consistency is expensive. Consensus requires coordination, coordination adds latency, and during network partitions you must choose: be unavailable or be inconsistent. For many applications, that's an unacceptable trade-off.

**Eventual consistency** is the alternative. Instead of guaranteeing immediate agreement, it guarantees that if updates stop, all nodes will eventually converge to the same state. It sounds weak—but it enables systems that are faster, more available, and more resilient.

This module explores eventual consistency: what it means, when to use it, how to design for it, and the patterns that make it practical.

> **The Library Analogy**
>
> Imagine a library with multiple branches. When you return a book at Branch A, other branches don't instantly know. Someone at Branch B might see the book as "checked out" for a few minutes. Eventually, all branches sync their records. The slight inconsistency is acceptable—it's better than making every checkout wait for all branches to agree.

---

## What You'll Learn

- What eventual consistency actually means
- The consistency spectrum (strong to eventual)
- Replication strategies and their trade-offs
- Conflict resolution approaches
- Read-your-writes and other consistency models
- CRDTs: conflict-free data structures

---

## Part 1: Understanding Eventual Consistency

### 1.1 What is Eventual Consistency?

```
EVENTUAL CONSISTENCY DEFINITION
═══════════════════════════════════════════════════════════════

"If no new updates are made, eventually all nodes will return
the same value for a given key."

KEY PROPERTIES
─────────────────────────────────────────────────────────────
1. EVENTUAL CONVERGENCE
   All replicas will eventually have the same data.
   "Eventually" could be milliseconds or seconds.

2. NO GUARANTEE ON "WHEN"
   No bound on how long convergence takes.
   (Though in practice, usually very fast)

3. READS MAY RETURN STALE DATA
   You might read old values during propagation.
   Different clients might see different values.

EXAMPLE
─────────────────────────────────────────────────────────────
┌────────────────────────────────────────────────────────────┐
│                                                            │
│  Time 0: All replicas have X = 1                          │
│                                                            │
│       Replica A        Replica B        Replica C         │
│          X=1              X=1              X=1            │
│                                                            │
│  Time 1: Client writes X = 2 to Replica A                 │
│                                                            │
│       Replica A        Replica B        Replica C         │
│          X=2              X=1              X=1            │
│           │                                                │
│           │────────replication───────────▶                │
│                                                            │
│  Time 2: Replication in progress                          │
│                                                            │
│       Replica A        Replica B        Replica C         │
│          X=2              X=2              X=1            │
│                           │                                │
│                           │──────────────▶                │
│                                                            │
│  Time 3: All replicas converged (eventually consistent)   │
│                                                            │
│       Replica A        Replica B        Replica C         │
│          X=2              X=2              X=2            │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

### 1.2 The Consistency Spectrum

```
CONSISTENCY MODELS SPECTRUM
═══════════════════════════════════════════════════════════════

STRONGEST                                              WEAKEST
    │                                                      │
    ▼                                                      ▼
┌────────┬──────────┬──────────────┬───────────┬──────────┐
│Lineariz│Sequential│   Causal     │  Session  │ Eventual │
│ ability│Consistency│ Consistency │ Guarantees│Consistency│
└────────┴──────────┴──────────────┴───────────┴──────────┘
    │                      │              │           │
    │                      │              │           │
"Global real-      "If A caused    "Within one  "Eventually
 time order"        B, see A         session,    converges"
                    before B"        see own
                                    writes"

LINEARIZABILITY (Strongest)
─────────────────────────────────────────────────────────────
Operations appear to execute atomically at a single point in time.
All clients see operations in real-time order.

    Example: etcd, Spanner
    Cost: High latency, limited availability

SEQUENTIAL CONSISTENCY
─────────────────────────────────────────────────────────────
Operations appear in some total order consistent with program order.
Not necessarily real-time order.

CAUSAL CONSISTENCY
─────────────────────────────────────────────────────────────
Causally related operations seen in order.
Concurrent operations may be seen in any order.

    If I write X, then read X, then write Y...
    Anyone who sees Y must have seen my X.

SESSION CONSISTENCY
─────────────────────────────────────────────────────────────
Within a session, client sees consistent view.
May include read-your-writes, monotonic reads.

EVENTUAL CONSISTENCY (Weakest)
─────────────────────────────────────────────────────────────
Only guarantees eventual convergence.
No ordering guarantees.

    Example: DNS, CDN caches
    Benefit: Maximum availability, lowest latency
```

### 1.3 Why Choose Eventual Consistency?

```
TRADE-OFFS
═══════════════════════════════════════════════════════════════

STRONG CONSISTENCY
─────────────────────────────────────────────────────────────
    ✓ Easy to reason about
    ✓ No stale reads
    ✓ No conflict resolution needed

    ✗ Higher latency (wait for replication)
    ✗ Lower availability (need quorum)
    ✗ Doesn't scale writes well

EVENTUAL CONSISTENCY
─────────────────────────────────────────────────────────────
    ✓ Lower latency (respond immediately)
    ✓ Higher availability (no quorum needed)
    ✓ Better write scalability
    ✓ Works during partitions

    ✗ Harder to reason about
    ✗ May read stale data
    ✗ Must handle conflicts

WHEN EVENTUAL CONSISTENCY MAKES SENSE
─────────────────────────────────────────────────────────────
┌────────────────────────────────────────────────────────────┐
│                                                            │
│  ✓ User-generated content (posts, comments)               │
│    Seeing a post 1 second late is fine.                   │
│                                                            │
│  ✓ Like counts, view counts                               │
│    Approximate is good enough.                            │
│                                                            │
│  ✓ Shopping carts                                         │
│    Merge on checkout, not on every add.                   │
│                                                            │
│  ✓ DNS                                                    │
│    TTL-based caching, eventual propagation.               │
│                                                            │
│  ✓ CDN cached content                                     │
│    Stale content is better than no content.               │
│                                                            │
│  ✓ Session data                                           │
│    User doesn't notice brief inconsistency.               │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

> **Try This (2 minutes)**
>
> For each scenario, which consistency level is appropriate?
>
> | Scenario | Consistency | Why |
> |----------|-------------|-----|
> | Bank transfer | Strong | Can't show wrong balance |
> | Twitter likes | Eventual | Approximate OK |
> | Inventory count | | |
> | User profile photo | | |
> | Order status | | |

---

## Part 2: Replication Strategies

### 2.1 Synchronous vs Asynchronous Replication

```
REPLICATION STRATEGIES
═══════════════════════════════════════════════════════════════

SYNCHRONOUS REPLICATION
─────────────────────────────────────────────────────────────
Write completes after ALL replicas acknowledge.

    Client ──Write──▶ Primary
                        │
                        ├──▶ Replica 1 ──ACK──┐
                        │                     │
                        └──▶ Replica 2 ──ACK──┼──▶ Primary ──ACK──▶ Client
                                              │
                                              │
                        Wait for all ACKs before responding

    ✓ Strong consistency
    ✓ No data loss on primary failure
    ✗ High latency (wait for slowest replica)
    ✗ Availability depends on all replicas

ASYNCHRONOUS REPLICATION
─────────────────────────────────────────────────────────────
Write completes after PRIMARY acknowledges.

    Client ──Write──▶ Primary ──ACK──▶ Client
                        │
                        │ (background)
                        │
                        ├──▶ Replica 1
                        │
                        └──▶ Replica 2

    ✓ Low latency (respond immediately)
    ✓ Availability only needs primary
    ✗ Eventual consistency
    ✗ Data loss possible if primary fails before replication

SEMI-SYNCHRONOUS (Quorum)
─────────────────────────────────────────────────────────────
Write completes after MAJORITY acknowledges.

    Client ──Write──▶ Primary
                        │
                        ├──▶ Replica 1 ──ACK──┐
                        │                     │
                        └──▶ Replica 2        ├──▶ Primary ──ACK──▶ Client
                                              │
                        Wait for majority (2 of 3)

    ✓ Balance of consistency and performance
    ✓ Tolerate some replica failures
    ✗ Still some latency for quorum
```

### 2.2 Multi-Leader and Leaderless Replication

```
REPLICATION TOPOLOGIES
═══════════════════════════════════════════════════════════════

SINGLE-LEADER
─────────────────────────────────────────────────────────────
    All writes go to one leader.
    Leader replicates to followers.

        Writes ──▶ Leader ──▶ Follower 1
                     │
                     └──────▶ Follower 2

    ✓ No write conflicts
    ✓ Simple
    ✗ Leader is bottleneck
    ✗ Cross-region latency for writes

MULTI-LEADER
─────────────────────────────────────────────────────────────
    Each region has a leader.
    Leaders sync with each other.

        Region A                    Region B
        ┌────────┐                 ┌────────┐
        │Leader A│◀═══ sync ═════▶│Leader B│
        └────────┘                 └────────┘
             │                          │
        ┌────▼────┐                ┌────▼────┐
        │Followers│                │Followers│
        └─────────┘                └─────────┘

    ✓ Low latency writes in each region
    ✓ Tolerates region failure
    ✗ Write conflicts between regions
    ✗ Conflict resolution complexity

LEADERLESS (Dynamo-style)
─────────────────────────────────────────────────────────────
    Write to ANY node.
    Read from multiple nodes, resolve conflicts.

        Client writes to W nodes (e.g., 2 of 3)
        Client reads from R nodes (e.g., 2 of 3)
        If W + R > N, guaranteed overlap (quorum)

        ┌─────────┐
        │ Node 1  │◀──write──┐
        └─────────┘          │
        ┌─────────┐          │
        │ Node 2  │◀──write──┼── Client
        └─────────┘          │
        ┌─────────┐          │
        │ Node 3  │          │
        └─────────┘

    ✓ No single point of failure
    ✓ High availability
    ✗ Must handle conflicts on read
    ✗ Complex consistency tuning (W, R, N values)
```

### 2.3 Consistency Tuning

```
QUORUM CONSISTENCY
═══════════════════════════════════════════════════════════════

N = Number of replicas
W = Write quorum (how many must acknowledge write)
R = Read quorum (how many to read from)

STRONG CONSISTENCY
─────────────────────────────────────────────────────────────
    W + R > N

    Example: N=3, W=2, R=2

    Write touches 2 nodes.
    Read touches 2 nodes.
    At least 1 node has latest data.

          Write         Read
           │             │
           ▼             ▼
        ┌─────┐       ┌─────┐
        │  A  │◀──────│  A  │ ← overlaps, sees latest
        └─────┘       └─────┘
        ┌─────┐       ┌─────┐
        │  B  │◀──────│  B  │
        └─────┘       └─────┘
        ┌─────┐       ┌─────┐
        │  C  │       │  C  │
        └─────┘       └─────┘

EVENTUAL CONSISTENCY
─────────────────────────────────────────────────────────────
    W + R ≤ N

    Example: N=3, W=1, R=1

    Faster but might read stale data.

TUNING EXAMPLES
─────────────────────────────────────────────────────────────
N=3, W=1, R=3: Fast writes, slow reads, eventual
N=3, W=3, R=1: Slow writes, fast reads, strong
N=3, W=2, R=2: Balanced, strong consistency
N=5, W=3, R=3: More fault tolerant, still strong
```

---

## Part 3: Conflict Resolution

### 3.1 Why Conflicts Happen

```
CONFLICT SCENARIOS
═══════════════════════════════════════════════════════════════

CONCURRENT WRITES
─────────────────────────────────────────────────────────────
Two clients write different values to the same key simultaneously.

    Client 1: SET user.email = "alice@new.com"
    Client 2: SET user.email = "alice@work.com"

    Both happen at "the same time" (no ordering).
    Which one wins?

PARTITION DURING WRITES
─────────────────────────────────────────────────────────────
Network partition splits replicas. Both sides accept writes.

    Region A (partition) ─────── Region B

    User in A: Update profile
    User in B: Update profile

    Partition heals. Which update wins?

OFFLINE EDITS
─────────────────────────────────────────────────────────────
User edits document offline. Another user edits online.

    User A (offline): Edit paragraph 1
    User B (online): Edit paragraph 1

    User A reconnects. Conflict!
```

### 3.2 Conflict Resolution Strategies

```
CONFLICT RESOLUTION STRATEGIES
═══════════════════════════════════════════════════════════════

LAST-WRITE-WINS (LWW)
─────────────────────────────────────────────────────────────
Highest timestamp wins. Simple but lossy.

    Write 1: {value: "A", timestamp: 100}
    Write 2: {value: "B", timestamp: 101}

    Result: "B" (higher timestamp)

    ✓ Simple, deterministic
    ✗ Loses data (A is discarded)
    ✗ Depends on clock accuracy

FIRST-WRITE-WINS
─────────────────────────────────────────────────────────────
Lowest timestamp wins. Used for immutable data.

    Once created, can't be overwritten.
    Useful for: Event logs, ledgers

MULTI-VALUE (Siblings)
─────────────────────────────────────────────────────────────
Keep all conflicting values. Application resolves.

    Write 1: "A"
    Write 2: "B"

    Read returns: ["A", "B"] (conflict!)
    Application must choose or merge.

    ✓ No data loss
    ✗ Application complexity
    ✗ Conflicts can cascade

MERGE FUNCTION
─────────────────────────────────────────────────────────────
Custom logic to merge conflicting values.

    Shopping cart merge:
    Cart A: [item1, item2]
    Cart B: [item1, item3]
    Merged: [item1, item2, item3] (union)

    ✓ Semantic merge
    ✗ Application-specific logic
    ✗ Not always possible

OPERATIONAL TRANSFORMATION
─────────────────────────────────────────────────────────────
Transform operations to preserve intent.

    Used by: Google Docs, collaborative editors

    User A: Insert "hello" at position 0
    User B: Insert "world" at position 0

    Transform: A sees B's insert, adjusts position
    Result: "worldhello" or "helloworld" (consistent order)
```

### 3.3 Version Vectors

```
VERSION VECTORS
═══════════════════════════════════════════════════════════════

Track causality, not wall-clock time.
Each node maintains counter per known node.

EXAMPLE
─────────────────────────────────────────────────────────────
Initial: X = {value: "A", version: {Node1: 1, Node2: 0}}

Node 1 writes:
    X = {value: "B", version: {Node1: 2, Node2: 0}}

Node 2 writes (didn't see Node 1's update):
    X = {value: "C", version: {Node1: 1, Node2: 1}}

CONFLICT DETECTION
─────────────────────────────────────────────────────────────
Version {Node1: 2, Node2: 0} vs {Node1: 1, Node2: 1}

Neither dominates (not strictly greater in all components).
This is a conflict!

Version {Node1: 2, Node2: 0} vs {Node1: 1, Node2: 0}

First dominates (Node1: 2 > 1, Node2: 0 = 0).
No conflict, first is newer.

AFTER MERGE
─────────────────────────────────────────────────────────────
Merged version: {Node1: 2, Node2: 1}
Merged value: Application decides (merge or pick one)
```

> **War Story: The $8.2 Million Shopping Cart Bug**
>
> **Black Friday 2018. A major electronics retailer discovers their shopping carts are "eating" high-value items—and the timing couldn't be worse.**
>
> The company had implemented eventually consistent shopping carts using last-write-wins (LWW) conflict resolution. The theory was sound: shopping carts are a classic eventual consistency use case. But the implementation had a fatal flaw.
>
> **The bug**: When a user added an item on their phone, then added a different item on their laptop before the phone's write replicated, the laptop's write included only its local cart state. Last-write-wins meant the phone's item disappeared.
>
> **Timeline of the disaster:**
> - **Wednesday before Black Friday**: QA notices occasional "missing item" reports but can't reproduce
> - **Black Friday 6:00 AM**: Doors open, traffic spikes 40x normal
> - **Black Friday 8:15 AM**: Customer complaints surge—"I added a TV but it's gone"
> - **Black Friday 9:00 AM**: Engineering traces bug to LWW conflict resolution
> - **Black Friday 10:30 AM**: Hotfix deployed—all cart writes now merge (union) instead of replace
> - **Black Friday 6:00 PM**: Final tally: 127,000 carts affected, 23,000 abandoned purchases
>
> **The cost:**
> - $4.8 million in lost sales (abandoned carts with high-value items)
> - $2.1 million in emergency discounts to affected customers
> - $1.3 million in overtime engineering and customer service
>
> **The fix**: The team replaced their cart data structure with a CRDT-style design:
> ```
> Before: cart = {items: ["tv", "laptop"]}  // Single value, LWW
> After:  cart = {
>           adds: {"tv": uuid1, "laptop": uuid2},
>           removes: {}
>         }  // OR-Set style, merges correctly
> ```
>
> **The lesson**: Eventual consistency requires thinking about conflict resolution at design time, not after the bug reports come in. "Last-write-wins" is almost never what you actually want for user data.

---

## Part 4: Practical Consistency Patterns

### 4.1 Read-Your-Writes

```
READ-YOUR-WRITES CONSISTENCY
═══════════════════════════════════════════════════════════════

Users should always see their own updates.
Even with eventual consistency, this is often required.

THE PROBLEM
─────────────────────────────────────────────────────────────
User writes to Node A.
User's next read goes to Node B (not yet replicated).
User sees old data. "Where's my update?!"

        User ──write──▶ Node A ──(replicating)──▶ Node B
             ◀──read────────────────────────────── Node B
                                              (stale data!)

SOLUTIONS
─────────────────────────────────────────────────────────────
1. STICKY SESSIONS
   Route user to same node that received write.

       User writes to Node A
       All reads from same user go to Node A

   ✓ Simple
   ✗ Load imbalance, failover complexity

2. READ FROM WRITE QUORUM
   Read from enough nodes to guarantee overlap.

       Write to W nodes
       Read from R nodes where W + R > N

   ✓ Guaranteed consistency
   ✗ Higher latency

3. VERSION-BASED READS
   Client tracks version of last write.
   Reads wait until node has that version.

       User writes, gets version V
       Read request includes "at least version V"
       Node waits until it has V or newer

   ✓ Precise guarantees
   ✗ Complexity, potential delays

4. SYNCHRONOUS REPLICATION FOR SENSITIVE DATA
   Write synchronously, read from anywhere.

   ✓ Simple reads
   ✗ Higher write latency
```

### 4.2 Monotonic Reads

```
MONOTONIC READS
═══════════════════════════════════════════════════════════════

Once you've seen a value, you shouldn't see an older one.
Time shouldn't "go backwards."

THE PROBLEM
─────────────────────────────────────────────────────────────
Read 1: User sees X = 2 (from Node A, fully replicated)
Read 2: User sees X = 1 (from Node B, lagging behind)

"Wait, the count went down!"

SOLUTION: SAME NODE OR VERSION TRACKING
─────────────────────────────────────────────────────────────
1. Session affinity to same replica
2. Track last-seen version, only accept newer

    Read 1 from Node A: X = 2, version V1
    Read 2 to Node B: "I've seen V1"
    Node B: Waits until it has V1 or newer
```

### 4.3 Causal Consistency

```
CAUSAL CONSISTENCY
═══════════════════════════════════════════════════════════════

If event B depends on event A, everyone sees A before B.
Concurrent events (no dependency) can appear in any order.

EXAMPLE
─────────────────────────────────────────────────────────────
Alice posts: "I got a promotion!"
Bob comments: "Congratulations!"

Bob's comment DEPENDS on Alice's post.
Everyone should see post before comment.

Without causal consistency:
    Some users see: "Congratulations!" (comment on... what?)
    Then later: "I got a promotion!"

IMPLEMENTATION
─────────────────────────────────────────────────────────────
Track dependencies with version vectors or explicit references.

    Post: {id: 1, content: "I got a promotion!", deps: []}
    Comment: {id: 2, content: "Congratulations!", deps: [1]}

    Replica doesn't show comment until it has post 1.

CAUSAL CONSISTENCY IN DATABASES
─────────────────────────────────────────────────────────────
Some databases offer causal consistency:
- MongoDB (causal consistency sessions)
- CockroachDB (by default)
- Spanner (via TrueTime)
```

---

## Part 5: CRDTs - Conflict-Free Data Types

### 5.1 What are CRDTs?

```
CONFLICT-FREE REPLICATED DATA TYPES
═══════════════════════════════════════════════════════════════

Data structures that automatically merge without conflicts.
No coordination needed—math guarantees convergence.

KEY PROPERTY: COMMUTATIVITY
─────────────────────────────────────────────────────────────
Order of operations doesn't matter.
A + B = B + A

    Node 1: Add "apple"
    Node 2: Add "banana"

    Order doesn't matter:
    {"apple", "banana"} = {"banana", "apple"}

WHY CRDTs MATTER
─────────────────────────────────────────────────────────────
Traditional data + replication = conflicts
CRDTs + replication = automatic merge

    ┌──────────────────────────────────────────────────────┐
    │                                                      │
    │   Node A: counter = 5                                │
    │   Node B: counter = 5                                │
    │                                                      │
    │   Node A: increment() → 6                            │
    │   Node B: increment() → 6                            │
    │                                                      │
    │   Regular merge: 6 vs 6 = 6 (lost one increment!)   │
    │                                                      │
    │   CRDT G-Counter:                                    │
    │   Node A: {A: 6, B: 5}                               │
    │   Node B: {A: 5, B: 6}                               │
    │   Merge: {A: 6, B: 6} = 12 (correct!)               │
    │                                                      │
    └──────────────────────────────────────────────────────┘
```

### 5.2 Common CRDTs

```
COMMON CRDT TYPES
═══════════════════════════════════════════════════════════════

G-COUNTER (Grow-only counter)
─────────────────────────────────────────────────────────────
Only increments. Each node has its own counter.

    Structure: {nodeA: count, nodeB: count, ...}
    Increment: node[self]++
    Value: sum(all counts)
    Merge: max(each node's count)

    Node A: {A: 3, B: 0}
    Node B: {A: 0, B: 2}
    Merge: {A: 3, B: 2} = 5

PN-COUNTER (Positive-Negative counter)
─────────────────────────────────────────────────────────────
Increments and decrements. Two G-Counters.

    Structure: {P: G-Counter, N: G-Counter}
    Increment: P.increment()
    Decrement: N.increment()
    Value: P.value - N.value

G-SET (Grow-only set)
─────────────────────────────────────────────────────────────
Only add, never remove.

    Add: set.add(element)
    Merge: union of sets

    Node A: {apple, banana}
    Node B: {apple, cherry}
    Merge: {apple, banana, cherry}

2P-SET (Two-Phase set)
─────────────────────────────────────────────────────────────
Add and remove, but removed elements can't be re-added.

    Structure: {added: G-Set, removed: G-Set}
    Add: added.add(element)
    Remove: removed.add(element)
    Value: added - removed

OR-SET (Observed-Remove set)
─────────────────────────────────────────────────────────────
Add and remove. Can re-add after remove.
Each add tagged with unique ID.

    Add "apple" → {(apple, uuid1)}
    Add "apple" again → {(apple, uuid1), (apple, uuid2)}
    Remove "apple" uuid1 → {(apple, uuid2)}
    Apple is still in set!

LWW-REGISTER (Last-Writer-Wins register)
─────────────────────────────────────────────────────────────
Simple value with timestamp.

    Structure: {value, timestamp}
    Write: if new_timestamp > timestamp: update
    Merge: keep higher timestamp
```

### 5.3 CRDTs in Practice

```
CRDTs IN PRODUCTION
═══════════════════════════════════════════════════════════════

RIAK (Database)
─────────────────────────────────────────────────────────────
Built-in CRDT support: counters, sets, maps, registers.

    # Increment a counter
    riak.update_type(bucket, key, :counter, 1)

REDIS (CRDTs in Redis Enterprise)
─────────────────────────────────────────────────────────────
Conflict-free replication across geo-distributed clusters.

AUTOMERGE (Collaborative editing)
─────────────────────────────────────────────────────────────
JSON CRDT for building collaborative apps.

    import Automerge from 'automerge'

    let doc1 = Automerge.change(doc, d => {
        d.text = "Hello"
    })

    let doc2 = Automerge.change(doc, d => {
        d.text = "World"
    })

    let merged = Automerge.merge(doc1, doc2)
    // Conflict resolved automatically

SOUNDCLOUD (Activity counts)
─────────────────────────────────────────────────────────────
G-Counters for play counts, like counts.
Eventually consistent but always increasing.

LIMITATIONS
─────────────────────────────────────────────────────────────
✗ Memory overhead (version vectors grow)
✗ Limited operations (can't do arbitrary logic)
✗ Eventual, not immediate consistency
✗ Some types are complex (OR-Set)
```

---

## Did You Know?

- **Amazon's shopping cart** was one of the first famous eventually consistent systems. Their 2007 Dynamo paper showed how eventual consistency enables high availability and became the blueprint for Cassandra, Riak, and DynamoDB.

- **CRDTs were independently discovered** multiple times. The mathematical foundations (lattices, semilattices) existed long before distributed systems, but applying them to replication was a breakthrough in 2011.

- **DNS is eventually consistent** by design. When you update a DNS record, it can take up to 48 hours (or the TTL) to propagate worldwide. Yet the internet works fine because most applications tolerate stale DNS.

- **Figma uses CRDTs** for real-time collaborative design. Multiple designers can edit the same file simultaneously, and their changes merge automatically without conflicts. When you drag a shape while your colleague resizes it, both operations succeed—no "your changes were overwritten" errors.

---

## Common Mistakes

| Mistake | Problem | Solution |
|---------|---------|----------|
| Assuming immediate consistency | Read stale data, confused users | Implement read-your-writes |
| Last-write-wins without thought | Silent data loss | Use merge functions or CRDTs |
| Ignoring conflict resolution | Conflicts surface as bugs later | Design conflict strategy upfront |
| Clock-based ordering | Clock skew causes wrong order | Use logical clocks or version vectors |
| No causal ordering | Comments before posts, replies before questions | Track causality explicitly |
| Over-engineering consistency | Complexity without benefit | Start eventual, add consistency where needed |

---

## Quiz

1. **What does "eventual consistency" actually guarantee?**
   <details markdown="1">
   <summary>Answer</summary>

   Eventual consistency guarantees:

   1. **Convergence**: If no new updates occur, all replicas will eventually have identical data
   2. **No data loss**: All acknowledged writes will eventually be visible everywhere

   It does NOT guarantee:
   - When convergence happens (could be milliseconds or seconds)
   - What you'll read during propagation
   - Order of operations across nodes

   "Eventually" means "given enough time without updates"—in practice, this is usually very fast (milliseconds to seconds), but there's no strict bound.
   </details>

2. **How do version vectors help with conflict detection?**
   <details markdown="1">
   <summary>Answer</summary>

   Version vectors track causality instead of wall-clock time:

   - Each node maintains a counter per known node
   - When node X writes, it increments its own counter
   - When nodes sync, they exchange version vectors

   Conflict detection:
   - Compare two version vectors element by element
   - If A ≥ B in all elements, A dominates (no conflict)
   - If neither dominates, it's a concurrent write (conflict!)

   Example:
   ```
   {Node1: 2, Node2: 1} vs {Node1: 1, Node2: 2}
   Neither dominates → Conflict!

   {Node1: 2, Node2: 1} vs {Node1: 1, Node2: 1}
   First dominates → No conflict, first is newer
   ```

   Unlike timestamps, version vectors don't depend on synchronized clocks.
   </details>

3. **What is a CRDT and why does it eliminate conflicts?**
   <details markdown="1">
   <summary>Answer</summary>

   **CRDT** (Conflict-free Replicated Data Type) is a data structure designed so that concurrent operations always merge deterministically.

   Why no conflicts:
   1. **Commutative operations**: Order doesn't matter (A + B = B + A)
   2. **Associative operations**: Grouping doesn't matter ((A + B) + C = A + (B + C))
   3. **Idempotent merge**: Merging same data twice gives same result

   Example (G-Counter):
   - Each node tracks its own increment count
   - Merge takes maximum of each node's count
   - No matter what order updates arrive, result is correct

   ```
   Node A: {A: 5, B: 3}
   Node B: {A: 4, B: 7}
   Merge: {A: 5, B: 7} = 12 (always correct)
   ```

   CRDTs trade some expressiveness for automatic conflict resolution.
   </details>

4. **When should you use eventual consistency vs strong consistency?**
   <details markdown="1">
   <summary>Answer</summary>

   **Use eventual consistency when**:
   - Availability matters more than immediate consistency
   - Stale reads are acceptable (social media, metrics, caches)
   - Operations can be merged or ordered later (shopping carts)
   - High write throughput needed
   - Geographic distribution required

   **Use strong consistency when**:
   - Correctness is critical (financial transactions, inventory)
   - Users must see their own writes immediately
   - Operations don't commute (can't be reordered)
   - Regulatory requirements demand it

   **Hybrid approach**:
   - Strong consistency for critical paths (payment, inventory decrement)
   - Eventual consistency for everything else (product views, recommendations)
   - Read-your-writes within sessions, eventual across users
   </details>

5. **A system uses N=5 replicas. Calculate the minimum W and R values needed for: (a) strong consistency, (b) fast writes with strong reads, (c) maximum availability.**
   <details markdown="1">
   <summary>Answer</summary>

   **Quorum rule for strong consistency**: W + R > N

   **For N=5:**

   **(a) Strong consistency (balanced):**
   - W=3, R=3 (3+3=6 > 5) ✓
   - Tolerates 2 failures for both reads and writes
   - Most common production configuration

   **(b) Fast writes, strong reads:**
   - W=1, R=5 (1+5=6 > 5) ✓
   - Writes return immediately after 1 ACK
   - Reads must contact all 5 nodes
   - Use case: Write-heavy workloads where reads are less frequent

   **(c) Maximum availability (eventual consistency):**
   - W=1, R=1 (1+1=2 ≤ 5) ✗ (not strongly consistent)
   - Can tolerate 4 failures
   - Fastest but may read stale data
   - Use case: Caching, metrics, non-critical data

</details>

**Trade-off matrix:**

| Config | Write Latency | Read Latency | Consistency | Availability |
|--------|---------------|--------------|-------------|--------------|
| W=3,R=3 | Medium | Medium | Strong | Medium |
| W=1,R=5 | Low | High | Strong | Low (reads) |
| W=5,R=1 | High | Low | Strong | Low (writes) |
| W=1,R=1 | Low | Low | Eventual | High |

6. **A social media platform stores user posts with eventual consistency. User A posts "Hello", then immediately comments "First!". Another user B sees "First!" but not "Hello". What consistency property is violated? How would you fix it?**
   <details markdown="1">
   <summary>Answer</summary>

   **Violated property: Causal consistency**

   The comment causally depends on the post (you can't comment on something that doesn't exist). User B should never see the effect (comment) before the cause (post).

   **Why it happened:**
   - Post written to Replica 1
   - Comment written to Replica 1 (references post)
   - User B reads from Replica 2
   - Comment replicated faster than post (or post delayed)
   - Replica 2 has comment but not post

   **Solutions:**

   1. **Explicit dependencies:**
   ```
   Post: {id: 1, content: "Hello", deps: []}
   Comment: {id: 2, content: "First!", deps: [1]}
   ```
   Replica doesn't show comment until it has all dependencies.

   2. **Version vectors:**
   - Post increments writer's version: {A: 1}
   - Comment includes causal context: {A: 1}
   - Replica delays showing comment until it's seen {A: 1}

   3. **Same-replica routing:**
   - Route all reads for a thread to the same replica
   - That replica has consistent view of causally related items

   4. **Synchronous replication for dependencies:**
   - When writing comment, wait for post to replicate first
   - Increases latency but guarantees causality
   </details>

7. **You're implementing a collaborative document editor. User A inserts "Hello" at position 0. User B inserts "World" at position 0 (concurrently, before seeing A's edit). After sync, what are the possible results? How do CRDTs or OT handle this?**
   <details markdown="1">
   <summary>Answer</summary>

   **Possible results without proper handling:**
   - "HelloWorld" (A's edit applied first)
   - "WorldHello" (B's edit applied first)
   - "Hello" or "World" (one overwrites the other - data loss!)

   **The challenge:**
   Both edits target position 0, but position 0 means something different after the first edit is applied.

   **Operational Transformation (OT) approach:**
   ```
   A's operation: insert("Hello", pos=0)
   B's operation: insert("World", pos=0)

   When A receives B's op:
   - A already has "Hello" at 0-4
   - Transform B's op: insert("World", pos=0) stays at 0
   - Result at A: "WorldHello"

   When B receives A's op:
   - B already has "World" at 0-4
   - Transform A's op: insert("Hello", pos=5) (shifted by "World" length)
   - Result at B: "WorldHello"
   ```
   Both converge to same result through transformation.

   **CRDT approach (e.g., RGA - Replicated Growable Array):**
   - Each character has unique ID (timestamp + node)
   - Insert specifies "insert after character with ID X"
   - Concurrent inserts at same position sorted by ID
   - Deterministic ordering without transformation

   ```
   A inserts "Hello" with ID (A,1) after start
   B inserts "World" with ID (B,1) after start
   Sort by ID: (A,1) < (B,1) → "HelloWorld"
   (or (B,1) < (A,1) → "WorldHello" - consistent either way)
   ```

   **Key insight**: Both OT and CRDTs guarantee convergence, but via different mechanisms—OT transforms operations, CRDTs use commutative data structures.
   </details>

8. **A G-Counter CRDT has the following state across 3 nodes. Calculate the total count. Then Node B increments by 5 and syncs with Node A. What's Node A's new state?**
   ```
   Node A: {A: 10, B: 3, C: 7}
   Node B: {A: 8,  B: 3, C: 5}
   Node C: {A: 10, B: 2, C: 7}
   ```
   <details markdown="1">
   <summary>Answer</summary>

   **Current total count at each node:**
   - Node A: 10 + 3 + 7 = **20**
   - Node B: 8 + 3 + 5 = **16**
   - Node C: 10 + 2 + 7 = **19**

   Note: Nodes have different views because replication is eventual. The "true" count is the maximum of each component: max(10,8,10) + max(3,3,2) + max(7,5,7) = 10 + 3 + 7 = **20**

   **After Node B increments by 5:**
   ```
   Node B: {A: 8, B: 8, C: 5}  (B's count: 3 + 5 = 8)
   ```

   **After Node B syncs with Node A:**

   G-Counter merge rule: take max of each component
   ```
   Node A before: {A: 10, B: 3, C: 7}
   Node B after:  {A: 8,  B: 8, C: 5}

   Merge:
   A: max(10, 8) = 10
   B: max(3, 8) = 8
   C: max(7, 5) = 7

   Node A after: {A: 10, B: 8, C: 7}
   Total: 10 + 8 + 7 = 25
   ```

   **Why this works:**
   - Each node only ever increments its own counter
   - Taking max never loses increments
   - Order of syncs doesn't matter (commutative)
   - Syncing twice gives same result (idempotent)
   </details>

---

## Hands-On Exercise

**Task**: Explore eventual consistency behavior.

**Part 1: Observe Replication Lag (10 minutes)**

If using a multi-node Kubernetes cluster:

```bash
# Create a ConfigMap
kubectl create configmap test-data --from-literal=value=1

# Immediately read from different nodes
# (Results may vary based on your cluster setup)
kubectl get configmap test-data -o jsonpath='{.data.value}'

# Update the ConfigMap
kubectl patch configmap test-data -p '{"data":{"value":"2"}}'

# Read again immediately - you should see consistent results
# (Kubernetes uses etcd with strong consistency)
```

Note: Kubernetes uses strongly consistent etcd, so you won't see replication lag. This exercise shows the contrast.

**Part 2: Simulate Conflict Resolution (15 minutes)**

Create a simple conflict scenario:

```yaml
# Create two versions of a ConfigMap in different files
# version-a.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: conflict-test
data:
  setting: "value-from-A"

# version-b.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: conflict-test
data:
  setting: "value-from-B"
```

```bash
# Apply version A
kubectl apply -f version-a.yaml

# Quickly apply version B
kubectl apply -f version-b.yaml

# Which value won?
kubectl get configmap conflict-test -o jsonpath='{.data.setting}'

# Kubernetes uses last-write-wins (based on resourceVersion)
```

**Part 3: Design a CRDT Counter (15 minutes)**

On paper, design a distributed like counter:

1. Multiple servers receive "like" requests
2. Users can like from any server
3. Total count should eventually be accurate

Questions:
- How would you structure the data?
- How would servers sync?
- What happens if a server is temporarily unreachable?

**Success Criteria**:
- [ ] Observed that Kubernetes provides strong consistency
- [ ] Understood last-write-wins behavior
- [ ] Designed a G-Counter approach for distributed counting

---

## Further Reading

- **"Designing Data-Intensive Applications"** - Martin Kleppmann. Chapter 5 covers replication and consistency in depth.

- **"A comprehensive study of Convergent and Commutative Replicated Data Types"** - Shapiro et al. The foundational CRDT paper.

- **"Dynamo: Amazon's Highly Available Key-value Store"** - DeCandia et al. The paper that popularized eventual consistency.

---

## Key Takeaways

Before moving on, ensure you understand:

- [ ] **Eventual consistency guarantee**: If updates stop, all replicas converge to the same state. No bound on "when"—but usually milliseconds in practice
- [ ] **The consistency spectrum**: Linearizability → Sequential → Causal → Session → Eventual. Stronger = more latency, less availability
- [ ] **Quorum math**: W + R > N for strong consistency. W=R=majority is common. Tuning W and R trades consistency for performance
- [ ] **Replication trade-offs**: Synchronous = strong but slow. Asynchronous = fast but eventual. Multi-leader = available but conflicts
- [ ] **Conflict resolution strategies**: Last-write-wins (simple, lossy), merge functions (semantic), version vectors (detect conflicts), CRDTs (conflict-free by design)
- [ ] **CRDTs eliminate conflicts**: Commutative + associative + idempotent operations. G-Counter, PN-Counter, OR-Set. Use when available, but limited expressiveness
- [ ] **Read-your-writes is essential**: Even with eventual consistency, users should see their own updates. Implement via sticky sessions, quorum reads, or version tracking
- [ ] **Design for conflict upfront**: "Last-write-wins" is almost never what you want for user data. Choose conflict resolution strategy before you ship

---

## Track Complete: Distributed Systems

Congratulations! You've completed the Distributed Systems foundation. You now understand:

- Why distribution is hard: latency, partial failure, no global clock
- Consensus: how nodes agree, and when you need it
- Eventual consistency: when immediate agreement isn't necessary
- Conflict resolution: handling concurrent updates

**Where to go from here:**

| Your Interest | Next Track |
|---------------|------------|
| Platform building | [Platform Engineering Discipline](../../disciplines/core-platform/platform-engineering/) |
| Reliability | [SRE Discipline](../../disciplines/core-platform/sre/) |
| Kubernetes deep dive | [CKA Certification](../../../k8s/cka/) |
| Observability tools | [Observability Toolkit](../../toolkits/observability-intelligence/observability/) |

---

## Foundations Complete!

You've now completed all five Foundations tracks:

| Track | Key Takeaway |
|-------|--------------|
| Systems Thinking | See the whole system, not just components |
| Reliability Engineering | Design for failure, measure what matters |
| Observability Theory | Understand through metrics, logs, traces |
| Security Principles | Defense in depth, least privilege, secure defaults |
| Distributed Systems | Consensus when needed, eventual when possible |

These foundations prepare you for the Disciplines and Toolkits tracks, where you'll apply these concepts to real-world practices and tools.

*"A distributed system is one in which the failure of a computer you didn't even know existed can render your own computer unusable."* — Leslie Lamport
