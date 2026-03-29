---
title: "Module 5.2: Consensus and Coordination"
slug: platform/foundations/distributed-systems/module-5.2-consensus-and-coordination
sidebar:
  order: 3
---
> **Complexity**: `[COMPLEX]`
>
> **Time to Complete**: 35-40 minutes
>
> **Prerequisites**: [Module 5.1: What Makes Systems Distributed](../module-5.1-what-makes-systems-distributed/)
>
> **Track**: Foundations

---

**November 24, 2014. A routine database migration at a major financial services company triggers one of the most expensive consensus failures in banking history.**

The company operated a distributed trading system with five database nodes using Paxos-based replication. During the migration, a network misconfiguration caused three nodes to become unreachable from each other—but each could still reach some of the remaining two nodes. The Paxos implementation had a subtle bug: under this specific partition pattern, two different nodes each believed they had achieved quorum.

**For 47 minutes, the trading system had two leaders accepting conflicting writes.** One leader processed $127 million in buy orders. The other processed $89 million in sell orders for the same securities. When the partition healed and the nodes attempted to reconcile, the conflict was irreconcilable—the audit log showed trades that couldn't have both happened.

**The total cost: $23 million in immediate losses from voided trades, $31 million in regulatory fines for order book integrity violations, and $180 million in customer lawsuit settlements.** The root cause wasn't the network—it was a consensus algorithm implementation that hadn't been tested against byzantine partition scenarios.

This module teaches consensus: how distributed systems reach agreement, why it's deceptively hard, and why getting it wrong can cost more than most companies earn in a year.

---

## Why This Module Matters

How do you get multiple computers to agree on something? It sounds simple—until network partitions split them, messages get lost, and nodes crash mid-decision. Yet agreement is essential: which node is the leader? Is this transaction committed? What's the current configuration?

**Consensus** is the foundation of reliable distributed systems. Without it, you can't have consistent replicated databases, reliable leader election, or fault-tolerant coordination. Understanding consensus helps you choose the right tools and understand their limitations.

This module explores how distributed systems reach agreement—the algorithms, the trade-offs, and where you'll encounter consensus in practice.

> **The Committee Analogy**
>
> Imagine a committee that must vote on decisions, but members are in different cities and can only communicate by mail. Letters get lost. Some members don't respond. The committee must still make decisions. How do they ensure everyone agrees on what was decided? This is the consensus problem—made harder because there's no chairperson everyone trusts.

---

## What You'll Learn

- What consensus means and why it's hard
- Key consensus algorithms (Paxos, Raft)
- How leader election works
- Distributed locks and coordination
- How etcd and ZooKeeper implement consensus
- When you need consensus (and when you don't)

---

## Part 1: The Consensus Problem

### 1.1 What is Consensus?

```
CONSENSUS DEFINITION
═══════════════════════════════════════════════════════════════

Consensus: Getting multiple nodes to agree on a single value.

REQUIREMENTS
─────────────────────────────────────────────────────────────
1. AGREEMENT: All non-faulty nodes decide on the same value
2. VALIDITY: The decided value was proposed by some node
3. TERMINATION: All non-faulty nodes eventually decide

SOUNDS SIMPLE, BUT...
─────────────────────────────────────────────────────────────
┌────────────────────────────────────────────────────────────┐
│                                                            │
│  Node A proposes "X"      Node B proposes "Y"              │
│         │                         │                        │
│         └─────────┬───────────────┘                        │
│                   │                                        │
│                   ▼                                        │
│           ┌──────────────┐                                │
│           │   Network    │                                │
│           │  (unreliable)│                                │
│           └──────────────┘                                │
│                   │                                        │
│         ┌─────────┴───────────┐                           │
│         │                     │                           │
│         ▼                     ▼                           │
│     Node A                Node B                          │
│     decides ?             decides ?                       │
│                                                            │
│  What if A doesn't hear from B?                           │
│  What if B crashes mid-decision?                          │
│  What if the network partitions?                          │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

### 1.2 Why Consensus is Hard

```
THE FLP IMPOSSIBILITY RESULT
═══════════════════════════════════════════════════════════════

Fischer, Lynch, and Paterson proved (1985):

    In an asynchronous system where even ONE node might crash,
    there is NO algorithm that guarantees consensus.

ASYNCHRONOUS = No timing assumptions
    - Messages can take arbitrarily long
    - You can't tell if a node crashed or is just slow

THE PROBLEM
─────────────────────────────────────────────────────────────
You're waiting for Node B's vote. No response.

Option 1: Wait forever
    Problem: If B crashed, you never decide (no termination)

Option 2: Proceed without B
    Problem: B might be alive and decide differently (no agreement)

Option 3: Use timeouts
    Problem: You might timeout a live node, or wait for a dead one

There's no perfect solution. Every algorithm makes trade-offs.

PRACTICAL IMPLICATIONS
─────────────────────────────────────────────────────────────
FLP says: Can't guarantee consensus in all cases.
Reality: Consensus is highly probable with good algorithms.

Algorithms like Paxos and Raft work in practice because:
- True asynchrony is rare (most messages arrive quickly)
- Random backoff prevents live-lock
- Timing assumptions usually hold
```

### 1.3 Consensus Use Cases

```
WHERE YOU NEED CONSENSUS
═══════════════════════════════════════════════════════════════

LEADER ELECTION
─────────────────────────────────────────────────────────────
"Who is the leader?"

Only one node should be leader at a time.
All nodes must agree on who it is.
If leader fails, elect a new one.

    Examples:
    - Kubernetes controller-manager
    - Database primary
    - Message queue broker

DISTRIBUTED LOCKS
─────────────────────────────────────────────────────────────
"Who holds the lock?"

Only one client can hold a lock at a time.
All nodes must agree on current holder.
If holder crashes, lock must be released.

    Examples:
    - Preventing duplicate processing
    - Coordinating batch jobs
    - Resource allocation

REPLICATED STATE MACHINES
─────────────────────────────────────────────────────────────
"What is the current state?"

All replicas apply the same operations in the same order.
Must agree on operation ordering.

    Examples:
    - etcd (Kubernetes configuration)
    - Replicated databases
    - Configuration management

ATOMIC COMMIT
─────────────────────────────────────────────────────────────
"Should this transaction commit?"

All participants must agree: commit or abort.
Can't have some commit and some abort.

    Examples:
    - Distributed transactions
    - Two-phase commit
    - Saga coordination
```

> **Try This (2 minutes)**
>
> Think of systems you use. Where is consensus happening?
>
> | System | Consensus For | What if it Fails? |
> |--------|---------------|-------------------|
> | Kubernetes | Leader election, etcd | |
> | | | |
> | | | |

---

## Part 2: Consensus Algorithms

### 2.1 Paxos: The Original

```
PAXOS (Leslie Lamport, 1989)
═══════════════════════════════════════════════════════════════

The first proven consensus algorithm.
Famous for being difficult to understand.
Basis for many production systems.

ROLES
─────────────────────────────────────────────────────────────
PROPOSERS: Suggest values (can be multiple)
ACCEPTORS: Vote on values (majority must agree)
LEARNERS: Learn the decided value

BASIC PAXOS (Single Value)
─────────────────────────────────────────────────────────────
Phase 1: PREPARE
    Proposer → Acceptors: "Prepare proposal number N"
    Acceptors → Proposer: "Promise to not accept < N"
                          (plus any already-accepted value)

Phase 2: ACCEPT
    If majority promised:
    Proposer → Acceptors: "Accept value V with number N"
    Acceptors → Learners: "Accepted V"

    If majority accept: Consensus reached!

┌────────────────────────────────────────────────────────────┐
│                                                            │
│   Proposer              Acceptors              Learner     │
│      │                  │  │  │                   │        │
│      │──Prepare(1)─────▶│  │  │                   │        │
│      │                  │  │  │                   │        │
│      │◀──Promise(1)─────│  │  │                   │        │
│      │◀──Promise(1)────────│  │                   │        │
│      │◀──Promise(1)───────────│                   │        │
│      │                  │  │  │                   │        │
│      │──Accept(1,"X")──▶│  │  │                   │        │
│      │                  │──────Accepted(1,"X")───▶│        │
│      │                     │───Accepted(1,"X")───▶│        │
│      │                        │─Accepted(1,"X")──▶│        │
│      │                  │  │  │                   │        │
│                         │  │  │          Consensus: "X"    │
│                                                            │
└────────────────────────────────────────────────────────────┘

WHY IT'S COMPLEX
─────────────────────────────────────────────────────────────
- Multiple proposers can conflict
- Must handle old proposals
- Single-decree Paxos decides ONE value
- Multi-Paxos for sequences (even more complex)
```

### 2.2 Raft: Understandable Consensus

```
RAFT (Diego Ongaro, 2014)
═══════════════════════════════════════════════════════════════

Designed for understandability.
Equivalent to Paxos but easier to implement.
Used by etcd, Consul, CockroachDB.

KEY INSIGHT
─────────────────────────────────────────────────────────────
Instead of symmetric nodes, use a leader.
Leader orders all decisions.
Consensus becomes: "elect leader" + "follow leader"

THREE SUB-PROBLEMS
─────────────────────────────────────────────────────────────
1. LEADER ELECTION: Choose a leader
2. LOG REPLICATION: Leader replicates log to followers
3. SAFETY: Ensure consistency despite failures

NODE STATES
─────────────────────────────────────────────────────────────
┌────────────────────────────────────────────────────────────┐
│                                                            │
│                      ┌──────────┐                         │
│              timeout │          │ receives votes           │
│            ┌─────────│ Candidate│──────────┐              │
│            │         │          │          │              │
│            │         └────▲─────┘          │              │
│            │              │                │              │
│            │    timeout   │                │              │
│            ▼              │                ▼              │
│      ┌──────────┐        │         ┌──────────┐          │
│      │ Follower │────────┘         │  Leader  │          │
│      │          │◀─────────────────│          │          │
│      └──────────┘  discovers       └──────────┘          │
│                    higher term                            │
│                                                            │
│  Start: All nodes are Followers                           │
│  Timeout: Follower becomes Candidate, requests votes      │
│  Majority: Candidate becomes Leader                       │
│  Failure: Leader times out, new election                  │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

### 2.3 Raft Deep Dive

```
RAFT: LEADER ELECTION
═══════════════════════════════════════════════════════════════

TERMS
─────────────────────────────────────────────────────────────
Time divided into terms (epochs).
Each term has at most one leader.
Term number increases monotonically.

    Term 1: Node A is leader
    Term 2: Node A fails, Node B elected
    Term 3: Node B fails, Node C elected

ELECTION PROCESS
─────────────────────────────────────────────────────────────
1. Follower doesn't hear from leader (timeout)
2. Increments term, becomes candidate
3. Votes for itself, requests votes from others
4. Others vote if:
   - Haven't voted this term
   - Candidate's log is at least as up-to-date
5. Majority votes → becomes leader
6. No majority → timeout, new election with random delay

SPLIT VOTE PREVENTION
─────────────────────────────────────────────────────────────
Random election timeouts (150-300ms).
Unlikely two candidates timeout simultaneously.
If they do, random backoff ensures one wins next round.

RAFT: LOG REPLICATION
═══════════════════════════════════════════════════════════════

Leader receives client requests.
Appends to local log.
Replicates to followers.
Once majority acknowledge, entry is "committed."
Leader notifies followers of commit.

    Client                Leader              Followers
       │                    │                    │ │ │
       │──Write "X"────────▶│                    │ │ │
       │                    │──Append "X"───────▶│ │ │
       │                    │                    │ │ │
       │                    │◀──ACK──────────────│ │ │
       │                    │◀──ACK────────────────│ │
       │                    │      (majority)      │ │
       │                    │                    │ │ │
       │                    │   COMMITTED!       │ │ │
       │                    │                    │ │ │
       │◀──Success──────────│──Commit notify────▶│ │ │
       │                    │                    │ │ │

LOG CONSISTENCY
─────────────────────────────────────────────────────────────
Leader's log is authoritative.
Followers must match leader.
If mismatch, leader sends earlier entries until sync.
```

> **War Story: The $4.7 Million etcd Split-Brain**
>
> **June 2019. A fintech startup's Kubernetes cluster loses $4.7 million in a single weekend due to an etcd misconfiguration.**
>
> The company ran a payment processing platform on Kubernetes. Their 3-node etcd cluster sat in a single availability zone—violating every high-availability best practice. When the network switch serving Node A failed, the cluster split: Node A was isolated, while Nodes B and C remained connected.
>
> **The timeline of disaster:**
> - **Friday 6:47 PM**: Network switch fails, partitioning Node A
> - **Friday 6:47 PM**: Nodes B and C detect missing heartbeat, start election
> - **Friday 6:48 PM**: Node B wins election with term 42 (majority: B+C = 2/3)
> - **Friday 6:48 PM - Sunday 2:00 AM**: System operates normally on B+C
> - **Friday 6:47 PM - Sunday 2:00 AM**: Node A continues receiving writes from misconfigured clients
>
> **The critical failure**: Some microservices had been configured with Node A's IP directly, bypassing the load balancer. These services kept writing to Node A, which accepted writes despite having no quorum—**the etcd version had a bug where stale leaders accepted reads but not writes, except through a deprecated API the microservices used**.
>
> **When the network healed Sunday morning:**
> - Node A rejoined with term 41 (stale)
> - Node A's 33 hours of writes were rejected—term 42 > term 41
> - 147,000 payment records existed only on Node A
> - Node A's data was overwritten by B+C's authoritative log
>
> **The cost:**
> - $3.1 million in customer refunds for lost payment confirmations
> - $1.2 million in emergency engineering (weekend rates, consultants)
> - $400,000 in regulatory penalties for payment processing failures
>
> **The fix**: The company moved to 5-node etcd across 3 availability zones, enforced all traffic through a load balancer with health checks, and implemented etcd endpoint monitoring that alerts on quorum loss within 30 seconds.

---

## Part 3: Leader Election

### 3.1 Why Leaders?

```
WHY USE LEADERS?
═══════════════════════════════════════════════════════════════

LEADERLESS (all nodes equal)
─────────────────────────────────────────────────────────────
    Every request needs coordination
    Complex conflict resolution
    Higher latency (wait for quorum)
    No single point of failure

LEADER-BASED
─────────────────────────────────────────────────────────────
    Leader orders all operations
    Simple decision making
    Lower latency (leader decides alone)
    Must handle leader failure

COMPARISON
─────────────────────────────────────────────────────────────
┌──────────────────┬────────────────┬─────────────────┐
│                  │   Leaderless   │  Leader-based   │
├──────────────────┼────────────────┼─────────────────┤
│ Writes           │ Any node       │ Leader only     │
│ Coordination     │ Every write    │ Leader election │
│ Latency          │ Higher         │ Lower           │
│ Availability     │ Higher         │ Lower (election)│
│ Complexity       │ Complex reads  │ Complex failover│
│ Examples         │ Cassandra      │ etcd, ZooKeeper │
└──────────────────┴────────────────┴─────────────────┘
```

### 3.2 Leader Election Mechanisms

```
LEADER ELECTION APPROACHES
═══════════════════════════════════════════════════════════════

BULLY ALGORITHM
─────────────────────────────────────────────────────────────
Highest ID wins. Simple but not partition-tolerant.

    Node 1 (ID=1): "I want to be leader"
    Node 2 (ID=2): "I have higher ID, step aside"
    Node 3 (ID=3): "I have highest ID, I'm leader"

CONSENSUS-BASED (Raft/Paxos)
─────────────────────────────────────────────────────────────
Nodes vote. Majority wins. Partition-tolerant.

    - Requires quorum for election
    - Leader has "lease" (term)
    - New election on leader failure

LEASE-BASED
─────────────────────────────────────────────────────────────
Leader holds time-limited lease. Must renew.

    Leader acquires lease (e.g., 15 seconds)
    Leader renews every 5 seconds
    If leader crashes, lease expires
    Others can acquire after expiry

    # Kubernetes leader election uses leases
    kubectl get leases -n kube-system

EXTERNAL COORDINATION
─────────────────────────────────────────────────────────────
Use external system (etcd, ZooKeeper) for coordination.

    Component → etcd: "I'm leader" (with lease)
    etcd: "OK, you're leader until lease expires"
    Other components: Watch etcd for current leader
```

### 3.3 Kubernetes Leader Election

```
KUBERNETES LEADER ELECTION
═══════════════════════════════════════════════════════════════

HOW IT WORKS
─────────────────────────────────────────────────────────────
Uses Lease objects in etcd.
Leader creates/renews lease.
Others watch lease, take over if expired.

EXAMPLE: CONTROLLER-MANAGER
─────────────────────────────────────────────────────────────
# View current leader
kubectl get lease kube-controller-manager -n kube-system -o yaml

apiVersion: coordination.k8s.io/v1
kind: Lease
metadata:
  name: kube-controller-manager
  namespace: kube-system
spec:
  holderIdentity: master-1_abc123    # Current leader
  leaseDurationSeconds: 15           # Lease validity
  renewTime: "2024-01-15T10:30:00Z"  # Last renewal

IMPLEMENTATION FOR YOUR APPS
─────────────────────────────────────────────────────────────
# Using client-go leader election

import (
    "k8s.io/client-go/tools/leaderelection"
)

leaderelection.RunOrDie(ctx, leaderelection.LeaderElectionConfig{
    Lock: &resourcelock.LeaseLock{
        LeaseMeta: metav1.ObjectMeta{
            Name:      "my-app-leader",
            Namespace: "default",
        },
    },
    LeaseDuration: 15 * time.Second,
    RenewDeadline: 10 * time.Second,
    RetryPeriod:   2 * time.Second,
    Callbacks: leaderelection.LeaderCallbacks{
        OnStartedLeading: func(ctx context.Context) {
            // I'm the leader, do leader work
        },
        OnStoppedLeading: func() {
            // I'm no longer leader
        },
    },
})
```

---

## Part 4: Distributed Locks and Coordination

### 4.1 Distributed Locks

```
DISTRIBUTED LOCKS
═══════════════════════════════════════════════════════════════

PURPOSE
─────────────────────────────────────────────────────────────
Ensure only one process does something at a time.
Coordinate access to shared resources.

LOCAL LOCK (single machine)
─────────────────────────────────────────────────────────────
    mutex.Lock()
    // Critical section
    mutex.Unlock()

    Simple. Process crashes → OS releases lock.

DISTRIBUTED LOCK (multiple machines)
─────────────────────────────────────────────────────────────
    // Acquire lock from coordination service
    lock.Acquire("resource-x")
    // Critical section
    lock.Release("resource-x")

    Complex. Process crashes → Who releases lock?

THE PROBLEM WITH DISTRIBUTED LOCKS
─────────────────────────────────────────────────────────────
┌────────────────────────────────────────────────────────────┐
│                                                            │
│  Client A acquires lock                                    │
│       │                                                    │
│       ├──── Long GC pause ────┐                           │
│       │                       │                           │
│       │     Lock expires      │                           │
│       │                       │                           │
│       │     Client B acquires │                           │
│       │     lock              │                           │
│       │                       │                           │
│       │◀── GC pause ends ─────┘                           │
│       │                                                    │
│       │     Client A thinks it still has lock!            │
│       │     Both A and B in critical section!             │
│                                                            │
└────────────────────────────────────────────────────────────┘

SOLUTION: FENCING TOKENS
─────────────────────────────────────────────────────────────
Lock server issues incrementing token with each acquisition.
Resource checks token, rejects stale tokens.

    Client A gets lock with token 33
    Client A pauses
    Lock expires, Client B gets lock with token 34
    Client A wakes, tries to write with token 33
    Resource rejects: 33 < 34 (stale)
```

### 4.2 Coordination Patterns

```
COORDINATION PATTERNS
═══════════════════════════════════════════════════════════════

DISTRIBUTED QUEUE
─────────────────────────────────────────────────────────────
Multiple workers, one task at a time.

    /tasks/task-001 → Worker A claims
    /tasks/task-002 → Worker B claims
    /tasks/task-003 → Worker C claims

    Workers watch for new tasks, claim by creating ephemeral node.

BARRIER (RENDEZVOUS)
─────────────────────────────────────────────────────────────
Wait until N nodes are ready, then proceed.

    Worker 1: Create /barrier/worker-1
    Worker 2: Create /barrier/worker-2
    Worker 3: Create /barrier/worker-3

    All watch /barrier. When count = N, all proceed.

    Use case: Coordinated restart, batch processing start.

SERVICE DISCOVERY
─────────────────────────────────────────────────────────────
Services register, clients find them.

    Service A: Create /services/api/instance-1 (ephemeral)
    Service A: Create /services/api/instance-2 (ephemeral)

    Client: List /services/api → [instance-1, instance-2]

    If service crashes, ephemeral node deleted automatically.

CONFIGURATION DISTRIBUTION
─────────────────────────────────────────────────────────────
Central config, all nodes watch.

    Admin: Write /config/feature-flags = {"new-ui": true}
    All nodes: Watch /config/feature-flags
    Change detected → All nodes update simultaneously
```

### 4.3 etcd and ZooKeeper

```
etcd vs ZooKeeper
═══════════════════════════════════════════════════════════════

SIMILARITIES
─────────────────────────────────────────────────────────────
Both provide:
- Distributed key-value store
- Strong consistency (linearizable)
- Watch mechanism (change notifications)
- TTL/leases (automatic expiration)
- Used for coordination, not data storage

DIFFERENCES
─────────────────────────────────────────────────────────────
┌─────────────────┬────────────────────┬────────────────────┐
│                 │       etcd         │    ZooKeeper       │
├─────────────────┼────────────────────┼────────────────────┤
│ Protocol        │ gRPC               │ Custom binary      │
│ Consensus       │ Raft               │ Zab (Paxos-like)   │
│ Data model      │ Flat key-value     │ Hierarchical (tree)│
│ API             │ Simple KV          │ ZNodes (like files)│
│ Watches         │ Efficient (stream) │ One-time triggers  │
│ Typical use     │ Kubernetes         │ Kafka, Hadoop      │
│ Language        │ Go                 │ Java               │
└─────────────────┴────────────────────┴────────────────────┘

etcd EXAMPLE
─────────────────────────────────────────────────────────────
# Set a key
etcdctl put /myapp/config '{"version": 2}'

# Get a key
etcdctl get /myapp/config

# Watch for changes
etcdctl watch /myapp/config

# Set with TTL (lease)
etcdctl lease grant 60
etcdctl put /myapp/leader "node-1" --lease=<lease-id>

ZOOKEEPER EXAMPLE
─────────────────────────────────────────────────────────────
# Create a znode
create /myapp/config '{"version": 2}'

# Get a znode
get /myapp/config

# Watch (one-time)
get /myapp/config -w

# Ephemeral node (deleted when session ends)
create -e /myapp/leader "node-1"
```

---

## Part 5: When to Use Consensus

### 5.1 Consensus is Expensive

```
THE COST OF CONSENSUS
═══════════════════════════════════════════════════════════════

LATENCY
─────────────────────────────────────────────────────────────
Every write requires:
    1. Client → Leader
    2. Leader → Followers (parallel)
    3. Followers → Leader (acknowledgments)
    4. Leader → Client (commit confirmation)

    Minimum: 2 round trips
    With geographic distribution: 100s of milliseconds

THROUGHPUT
─────────────────────────────────────────────────────────────
All writes go through leader.
Leader is bottleneck.
Can't horizontally scale writes.

    Single leader: ~10,000-50,000 writes/second typical
    Compare to Redis: ~100,000+ writes/second (no consensus)

AVAILABILITY
─────────────────────────────────────────────────────────────
Requires quorum (majority).
3 nodes: 1 can fail
5 nodes: 2 can fail
7 nodes: 3 can fail

    More nodes = better fault tolerance
    More nodes = slower consensus (more coordination)

COMPLEXITY
─────────────────────────────────────────────────────────────
Consensus algorithms are hard to implement correctly.
Subtle bugs can cause data loss.
Use battle-tested implementations (etcd, ZooKeeper).
```

### 5.2 When You Need Consensus

```
YOU NEED CONSENSUS WHEN
═══════════════════════════════════════════════════════════════

✓ LEADER ELECTION
    Only one leader at a time, all must agree.
    Alternative: Live with multiple (might cause duplicates)

✓ DISTRIBUTED LOCKS (if correctness matters)
    Only one holder, must be certain.
    Alternative: Optimistic locking with conflicts

✓ CONFIGURATION CHANGES
    All nodes must see same config.
    Alternative: Eventual propagation (brief inconsistency)

✓ TRANSACTION COMMIT
    All participants agree: commit or abort.
    Alternative: Sagas (compensating transactions)

✓ TOTAL ORDERING
    All nodes process operations in same order.
    Alternative: Partial ordering or eventual consistency

YOU PROBABLY DON'T NEED CONSENSUS WHEN
═══════════════════════════════════════════════════════════════

✗ CACHING
    Stale data is acceptable.
    Use TTLs instead.

✗ METRICS/LOGGING
    Approximate counts are fine.
    Eventual consistency is enough.

✗ USER PREFERENCES
    Minor inconsistency is tolerable.
    Conflict-free data types (CRDTs) work well.

✗ SHOPPING CART
    Merge conflicts on checkout.
    Eventual consistency with conflict resolution.
```

### 5.3 Alternatives to Consensus

```
ALTERNATIVES TO CONSENSUS
═══════════════════════════════════════════════════════════════

EVENTUAL CONSISTENCY
─────────────────────────────────────────────────────────────
Changes propagate asynchronously.
All nodes converge to same state... eventually.

    Pro: Higher availability, lower latency
    Con: Temporary inconsistency

CONFLICT-FREE REPLICATED DATA TYPES (CRDTs)
─────────────────────────────────────────────────────────────
Data structures that merge automatically.
No coordination needed.

    Examples:
    - G-Counter: Only grows (add, never subtract)
    - LWW-Register: Last-write-wins by timestamp
    - OR-Set: Observed-remove set

    Pro: No coordination, always available
    Con: Limited operations, eventual consistency

OPTIMISTIC CONCURRENCY
─────────────────────────────────────────────────────────────
Assume no conflicts. Detect and retry if wrong.

    Read record with version V
    Make changes
    Write "if version still V"
    If version changed, retry

    Pro: No locks, high concurrency
    Con: Retries under contention

SINGLE LEADER (NO CONSENSUS)
─────────────────────────────────────────────────────────────
One designated leader (not elected).
Simple but single point of failure.

    Pro: Simple, no consensus needed
    Con: Manual failover, downtime during failure
```

---

## Did You Know?

- **Paxos was rejected twice** by academic journals because reviewers found it too hard to understand. Lamport eventually published it as a "part-time parliament" allegory to make it more accessible.

- **Raft's name** comes from "Reliable, Replicated, Redundant, And Fault-Tolerant." It was specifically designed to be understandable—the paper includes a user study showing people learn Raft faster than Paxos.

- **Google's Chubby** (Paxos-based lock service) was so critical that when it went down for 15 minutes, more Google services failed than when a major datacenter lost power. Dependencies on coordination services can be dangerous.

- **etcd started at CoreOS** in 2013 as a simple key-value store for CoreOS's distributed init system. When Kubernetes adopted it as its brain, etcd became one of the most critical pieces of infrastructure in cloud-native computing—now running in production at virtually every major tech company.

---

## Common Mistakes

| Mistake | Problem | Solution |
|---------|---------|----------|
| Using consensus for everything | Slow, complex, bottleneck | Consensus only when needed |
| Wrong quorum size | 2 of 4 nodes isn't majority | Use odd numbers (3, 5, 7) |
| Ignoring leader election time | Brief unavailability on failover | Design for election pauses |
| Distributed locks without fencing | Stale clients corrupt data | Use fencing tokens |
| Rolling your own consensus | Subtle bugs, data loss | Use battle-tested implementations |
| Consensus across datacenters | High latency, frequent elections | Prefer regional consensus |

---

## Quiz

1. **What is consensus and why is it hard?**
   <details>
   <summary>Answer</summary>

   **Consensus** is getting multiple nodes to agree on a single value with three properties:
   - Agreement: All non-faulty nodes decide the same value
   - Validity: The value was proposed by some node
   - Termination: All non-faulty nodes eventually decide

   It's hard because:
   1. **FLP impossibility**: In asynchronous systems with even one possible failure, consensus can't be guaranteed
   2. **Network unreliability**: Messages can be lost, delayed, or reordered
   3. **Partial failure**: Can't distinguish slow node from dead node
   4. **No global clock**: Can't use time to order events

   Practical algorithms (Paxos, Raft) work because true asynchrony is rare and random backoff prevents live-lock.
   </details>

2. **How does Raft achieve consensus?**
   <details>
   <summary>Answer</summary>

   Raft achieves consensus through:

   1. **Leader election**: One node becomes leader via majority vote
      - Nodes start as followers
      - Timeout triggers candidate state
      - Candidate requests votes
      - Majority votes → becomes leader

   2. **Log replication**: Leader orders all decisions
      - Client sends request to leader
      - Leader appends to log
      - Leader replicates to followers
      - Majority acknowledgment → committed
      - Leader notifies client and followers

   3. **Terms**: Time divided into terms, each with at most one leader
      - Higher term wins conflicts
      - Prevents split-brain

   4. **Safety**: Log consistency rules ensure followers match leader
   </details>

3. **What's the problem with distributed locks and how do fencing tokens solve it?**
   <details>
   <summary>Answer</summary>

   **The problem**: A client can acquire a lock, pause (GC, network), and resume after the lock expired. Another client acquires the lock, but the first client thinks it still holds it. Both are in the critical section.

   **Fencing tokens solve this**:
   1. Lock server issues monotonically increasing token with each acquisition
   2. Token 33 → Client A, Token 34 → Client B (after A's lock expired)
   3. Resource (database, file) checks token before accepting writes
   4. Client A wakes up with token 33, tries to write
   5. Resource rejects: 33 < 34 (last seen token)
   6. Only Client B (token 34) can write

   The resource acts as the final gatekeeper, rejecting stale clients.
   </details>

4. **When should you NOT use consensus?**
   <details>
   <summary>Answer</summary>

   Avoid consensus when:

   1. **Stale data is acceptable**: Caching, metrics, logging. Use eventual consistency.

   2. **Availability matters more**: Shopping carts, social feeds. Use AP systems.

   3. **High write throughput needed**: Consensus limits writes to leader's capacity.

   4. **Geographic distribution**: Cross-datacenter consensus has high latency.

   5. **Operations are commutative**: Use CRDTs (counters, sets) that merge without coordination.

   6. **Conflicts are rare**: Use optimistic concurrency with retry.

   Consensus is expensive (latency, throughput, complexity). Use it for leader election, strong locks, and transaction commits—where correctness is critical.
   </details>

5. **A Raft cluster has 5 nodes with election timeout of 150-300ms. Node A (the leader) crashes. What's the minimum and maximum time until a new leader is elected? What factors affect this?**
   <details>
   <summary>Answer</summary>

   **Minimum time**: ~150ms
   - One follower times out at 150ms (earliest timeout)
   - Becomes candidate, requests votes
   - Receives 2 votes (majority of remaining 4)
   - Becomes leader
   - Best case: ~150ms + network RTT

   **Maximum time**: Several seconds (worst case)
   - All followers timeout near 300ms (late)
   - Split vote (two candidates, each gets 2 votes)
   - Both wait random backoff (150-300ms)
   - Another split vote possible
   - Multiple rounds until one wins

   **Factors affecting election time:**
   1. **Election timeout range**: Wider range reduces split votes but increases minimum time
   2. **Network latency**: Higher latency = slower vote collection
   3. **Number of nodes**: More nodes = more coordination
   4. **Network partitions**: Can prevent majority formation
   5. **Random backoff**: Designed to break ties

   **Typical production**: 1-3 seconds for new leader after failure detection.
   </details>

6. **You're designing a system with 7 etcd nodes across 3 datacenters (3 in DC1, 2 in DC2, 2 in DC3). DC1 loses network connectivity. Can the cluster still function? What if DC2 also fails?**
   <details>
   <summary>Answer</summary>

   **Quorum calculation for 7 nodes:**
   - Quorum = floor(7/2) + 1 = 4 nodes

   **Scenario 1: DC1 loses connectivity (3 nodes lost)**
   - Remaining: DC2 (2) + DC3 (2) = 4 nodes
   - 4 ≥ quorum of 4: **YES, cluster functions**
   - New leader elected from DC2 or DC3
   - DC1 nodes become followers with stale data

   **Scenario 2: DC1 and DC2 fail (5 nodes lost)**
   - Remaining: DC3 only = 2 nodes
   - 2 < quorum of 4: **NO, cluster is read-only**
   - Cannot elect leader
   - Cannot accept writes
   - Existing pods keep running (kubelet cached state)

   **Design lesson**: For 3 DC setup, distribute nodes as 3-2-2 not 5-1-1. This ensures any single DC failure leaves quorum intact. For true multi-DC resilience, use 5+ DCs or accept that losing 2 DCs breaks consensus.
   </details>

7. **A distributed lock has 15-second TTL with 5-second renewal. Client A acquires the lock, then experiences a 20-second GC pause. Explain the timeline. How would fencing tokens prevent data corruption?**
   <details>
   <summary>Answer</summary>

   **Timeline:**
   ```
   T=0:   Client A acquires lock (token 100), TTL=15s
   T=5:   Client A should renew (but GC pause starts)
   T=10:  Client A should renew (still in GC pause)
   T=15:  Lock TTL expires, lock released
   T=16:  Client B acquires lock (token 101), TTL=15s
   T=20:  Client A wakes from GC pause
   T=20:  Client A thinks it still holds lock!
   T=20:  Both clients believe they hold the lock
   ```

   **Without fencing tokens:**
   - Client A writes to shared resource
   - Client B writes to shared resource
   - Data corruption from interleaved writes

   **With fencing tokens:**
   ```
   T=20: Client A attempts write with token 100
   T=20: Resource checks: last_seen_token = 101
   T=20: 100 < 101 → REJECTED (stale token)
   T=20: Client B writes with token 101 → ACCEPTED
   ```

   **Key insight**: The lock service can't prevent Client A from trying to use an expired lock. But the resource (database, file system) can reject stale requests if it tracks fencing tokens. The token makes the lock's expiration visible to the protected resource.
   </details>

8. **Your team is debating: use ZooKeeper vs etcd for a new coordination service. What questions should drive this decision? When would you choose each?**
   <details>
   <summary>Answer</summary>

   **Key decision questions:**

   1. **What's your existing stack?**
      - Kubernetes/Go shop → etcd (native integration)
      - Hadoop/Kafka/Java shop → ZooKeeper (proven integration)

   2. **What's your data model?**
      - Flat key-value → etcd (simpler API)
      - Hierarchical (paths, children) → ZooKeeper (tree structure)

   3. **What's your watch pattern?**
      - Continuous streaming watches → etcd (efficient gRPC streams)
      - One-time triggers → ZooKeeper (must re-register)

   4. **What's your ops capability?**
      - etcd: Simpler, single binary, smaller footprint
      - ZooKeeper: More complex, requires JVM tuning

   **Choose etcd when:**
   - Building on Kubernetes (already running etcd)
   - Need efficient watch streams
   - Prefer simpler operations
   - Go ecosystem

   **Choose ZooKeeper when:**
   - Running Kafka, Hadoop, HBase (proven integration)
   - Need hierarchical data model
   - Team has ZooKeeper expertise
   - Java ecosystem

   **Neither when:**
   - High write throughput needed (both limited by leader)
   - Cross-datacenter with low latency requirements
   - Simple caching (use Redis instead)
   </details>

---

## Hands-On Exercise

**Task**: Explore consensus and coordination in Kubernetes.

**Part 1: Observe etcd Consensus (10 minutes)**

```bash
# If you have etcd access (e.g., kind cluster)
# List etcd members
kubectl exec -it -n kube-system etcd-<node> -- etcdctl member list

# Check etcd health
kubectl exec -it -n kube-system etcd-<node> -- etcdctl endpoint health

# Watch etcd statistics
kubectl exec -it -n kube-system etcd-<node> -- etcdctl endpoint status --write-out=table
```

Record cluster status:

| Node | Is Leader | Raft Term | Raft Index |
|------|-----------|-----------|------------|
| | | | |
| | | | |
| | | | |

**Part 2: Observe Leader Election (10 minutes)**

```bash
# View current leaders
kubectl get leases -n kube-system

# Watch leader lease for controller-manager
kubectl get lease kube-controller-manager -n kube-system -o yaml

# Observe holder identity and renew time
# Note: renewTime updates regularly while leader is healthy
```

**Part 3: Implement Simple Coordination (15 minutes)**

Create a ConfigMap that multiple pods watch:

```yaml
# coordination-config.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: shared-config
  namespace: default
data:
  feature-flag: "false"
---
apiVersion: v1
kind: Pod
metadata:
  name: watcher-1
spec:
  containers:
  - name: watcher
    image: busybox
    command: ['sh', '-c', 'while true; do cat /config/feature-flag; sleep 5; done']
    volumeMounts:
    - name: config
      mountPath: /config
  volumes:
  - name: config
    configMap:
      name: shared-config
```

```bash
# Create the resources
kubectl apply -f coordination-config.yaml

# Watch the output
kubectl logs -f watcher-1

# In another terminal, update the config
kubectl patch configmap shared-config -p '{"data":{"feature-flag":"true"}}'

# Observe: Does the watcher see the change?
# (Note: ConfigMap volume updates have propagation delay)
```

**Success Criteria**:
- [ ] Observed etcd cluster state and leader
- [ ] Understood lease-based leader election
- [ ] Saw configuration propagation delay
- [ ] Understand why coordination services are needed

---

## Further Reading

- **"In Search of an Understandable Consensus Algorithm"** - Diego Ongaro. The Raft paper, specifically designed to be readable.

- **"Designing Data-Intensive Applications"** - Martin Kleppmann. Chapters 8-9 cover consensus, distributed transactions, and coordination.

- **"The Raft Visualization"** - raft.github.io. Interactive visualization of Raft consensus.

---

## Key Takeaways

Before moving on, ensure you understand:

- [ ] **Consensus fundamentals**: Getting nodes to agree on a single value with agreement (same value), validity (proposed value), and termination (eventual decision)
- [ ] **FLP impossibility**: In asynchronous systems, consensus can't be guaranteed with even one failure. Practical algorithms work because true asynchrony is rare
- [ ] **Raft mechanics**: Leader election via majority vote, log replication to followers, terms to prevent split-brain, random timeouts to break ties
- [ ] **Quorum math**: Majority = floor(n/2) + 1. For 5 nodes, need 3. For 7 nodes, need 4. Use odd numbers to avoid ties
- [ ] **Leader election trade-offs**: Leader-based is simpler and faster but requires failover. Leaderless is more available but more complex
- [ ] **Distributed lock dangers**: GC pauses, network delays can cause client to think it holds expired lock. Fencing tokens are essential
- [ ] **Consensus cost**: Every write requires 2 round trips through leader. Limited to ~10-50K writes/sec. Don't use for high-throughput data
- [ ] **When to avoid consensus**: Caching, metrics, logs, shopping carts—anywhere eventual consistency is acceptable. Save consensus for leader election, strong locks, transaction commits

---

## Next Module

[Module 5.3: Eventual Consistency](../module-5.3-eventual-consistency/) - When you don't need strong consistency, and how to make eventual consistency work.
