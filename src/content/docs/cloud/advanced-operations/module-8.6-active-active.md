---
title: "Module 8.6: Multi-Region Active-Active Deployments"
slug: cloud/advanced-operations/module-8.6-active-active
sidebar:
  order: 7
---
> **Complexity**: `[COMPLEX]`
>
> **Time to Complete**: 3 hours
>
> **Prerequisites**: [Module 8.5: Disaster Recovery](../module-8.5-disaster-recovery/), understanding of distributed systems basics (CAP theorem)
>
> **Track**: Advanced Cloud Operations

## What You'll Be Able to Do

After completing this module, you will be able to:

- **Design multi-region active-active Kubernetes deployments with global load balancing and data replication**
- **Implement traffic routing strategies (DNS-based, anycast, global LB) for active-active failover patterns**
- **Configure data replication and conflict resolution mechanisms for stateful workloads across regions**
- **Evaluate active-active vs active-passive tradeoffs including cost, complexity, and consistency guarantees**

---

## Why This Module Matters

**October 2021. A global food delivery platform. 34 million daily orders.**

The platform ran in a single AWS region (us-east-1) with a warm standby in eu-west-1 for DR. At 14:22 UTC, an AWS networking issue caused elevated packet loss in us-east-1 for 23 minutes. Not a full outage -- services were degraded, not dead. The warm standby couldn't help because the primary was technically "up," just slow. Health checks passed (they tested reachability, not latency). For those 23 minutes, order placement latency spiked from 200ms to 4.5 seconds. Users abandoned carts. Restaurants received stale orders. Delivery ETAs became meaningless.

The financial impact was $3.8 million in lost orders. But the strategic impact was larger: the company's biggest competitor, which ran active-active across three regions, experienced zero user-visible impact from the same AWS issue. Users who switched during those 23 minutes didn't come back.

This incident drove a six-month migration to active-active. The engineering team discovered that active-active is not "DR but better." It is a fundamentally different architecture that changes how you think about state, consistency, routing, and failure. This module teaches you how to design, implement, and operate multi-region active-active Kubernetes deployments -- including the hard parts that architecture diagrams always skip.

---

## What Active-Active Actually Means

Active-active means every region serves production traffic simultaneously. There is no standby. There is no failover. Every region is a primary.

```
ACTIVE-ACTIVE vs ACTIVE-PASSIVE
════════════════════════════════════════════════════════════════

ACTIVE-PASSIVE (DR):
  Region A: 100% traffic ──▶ Region B: 0% traffic (standby)
  Failure: Failover to B (minutes of downtime)

ACTIVE-ACTIVE:
  Region A: 50% traffic ◀──▶ Region B: 50% traffic
  Failure: Region A dies, Region B absorbs 100% (seconds)

  The difference is not just about redundancy.
  Active-active means:
  - Both regions write data (state management is HARD)
  - Both regions must stay in sync (replication lag is REAL)
  - Routing must be intelligent (not just DNS failover)
  - Every service must be designed for multi-writer (or partitioned)
```

### The Active-Active Spectrum

Not everything needs to be active-active. Most organizations use a hybrid approach.

| Component | Active-Active? | Strategy |
|---|---|---|
| Stateless APIs | Yes | Deploy in all regions, route by latency |
| Static assets / CDN | Yes | Replicated at edge automatically |
| Session state | Yes (with care) | Sticky sessions or distributed cache (Redis Global) |
| User data (reads) | Yes | Read replicas in each region |
| User data (writes) | Depends | Single-writer or CRDT-based |
| Financial transactions | Rarely | Single-writer with async replication |
| Search index | Yes | Replicated index per region |
| Message queues | Regional | Each region has its own queue, cross-region for specific flows |

---

## Stateless Active-Active: The Easy Part

Stateless services (APIs that don't maintain local state between requests) are straightforward to run active-active. Deploy the same service in multiple regions, put a global load balancer in front, and route by latency.

```
STATELESS ACTIVE-ACTIVE
════════════════════════════════════════════════════════════════

  User (Tokyo)                    User (New York)
       │                               │
       ▼                               ▼
  ┌─────────────────────────────────────────────┐
  │           Global Load Balancer               │
  │  (GCP GLB / AWS Global Accelerator /         │
  │   Cloudflare / Azure Front Door)             │
  │                                              │
  │  Routing: Lowest latency                     │
  │  Failover: Automatic on health check failure │
  └──────────┬────────────────────┬──────────────┘
             │                    │
    ┌────────┴────────┐  ┌───────┴─────────┐
    │  ap-northeast-1 │  │  us-east-1      │
    │  ┌────────────┐ │  │  ┌────────────┐ │
    │  │ EKS Cluster│ │  │  │ EKS Cluster│ │
    │  │ API: 3 pods│ │  │  │ API: 3 pods│ │
    │  │ Auth: 2    │ │  │  │ Auth: 2    │ │
    │  │ Search: 2  │ │  │  │ Search: 2  │ │
    │  └────────────┘ │  │  └────────────┘ │
    │                  │  │                 │
    │  Read replica    │  │  Primary DB     │
    │  (async, ~100ms) │  │  (writes here)  │
    └──────────────────┘  └─────────────────┘
```

### Deploying with ArgoCD ApplicationSets

```yaml
# ArgoCD ApplicationSet to deploy to multiple clusters
apiVersion: argoproj.io/v1alpha1
kind: ApplicationSet
metadata:
  name: payment-api
  namespace: argocd
spec:
  generators:
    - clusters:
        selector:
          matchLabels:
            environment: production
        values:
          region: '{{metadata.labels.region}}'
  template:
    metadata:
      name: 'payment-api-{{values.region}}'
    spec:
      project: default
      source:
        repoURL: https://github.com/company/k8s-manifests
        targetRevision: main
        path: 'apps/payment-api/overlays/{{values.region}}'
      destination:
        server: '{{server}}'
        namespace: payments
      syncPolicy:
        automated:
          prune: true
          selfHeal: true
        syncOptions:
          - CreateNamespace=true
```

### Regional Configuration with Kustomize

```yaml
# apps/payment-api/overlays/us-east-1/kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
resources:
  - ../../base
patches:
  - target:
      kind: Deployment
      name: payment-api
    patch: |
      - op: replace
        path: /spec/replicas
        value: 6
  - target:
      kind: ConfigMap
      name: payment-config
    patch: |
      - op: replace
        path: /data/DATABASE_URL
        value: "postgres://primary.us-east-1.rds.amazonaws.com:5432/payments"
      - op: replace
        path: /data/CACHE_URL
        value: "redis://global-cache.us-east-1.cache.amazonaws.com:6379"
      - op: replace
        path: /data/REGION
        value: "us-east-1"
```

---

## Global State Management: The Hard Part

The moment your active-active deployment needs to write data, everything gets complicated. The fundamental problem is the CAP theorem: in the presence of a network partition, you must choose between consistency and availability. Active-active chooses availability, which means you must deal with inconsistency.

### Strategy 1: Single-Writer, Multi-Reader

The simplest approach: one region owns writes for each piece of data. Other regions serve reads from replicas.

```
SINGLE-WRITER PATTERN
════════════════════════════════════════════════════════════════

  us-east-1 (Primary)              eu-west-1 (Replica)
  ┌─────────────────────┐         ┌─────────────────────┐
  │  Writes: YES         │         │  Writes: NO          │
  │  Reads: YES          │         │  Reads: YES          │
  │                     │ async   │                     │
  │  PostgreSQL Primary │────────▶│  PostgreSQL Replica  │
  │  (RDS Multi-AZ)    │ ~100ms  │  (RDS Cross-Region)  │
  │                     │ lag     │                     │
  └─────────────────────┘         └─────────────────────┘

  Read from eu-west-1: user sees data that is ~100ms old
  Write from eu-west-1: proxied to us-east-1 (adds ~80ms latency)

  When us-east-1 fails:
  - Promote eu-west-1 replica to primary (minutes)
  - Some recent writes may be lost (RPO = replication lag)
```

```yaml
# Application config: route writes to primary, reads to local replica
apiVersion: v1
kind: ConfigMap
metadata:
  name: db-config
  namespace: payments
data:
  # Application reads from the nearest replica
  DATABASE_READ_URL: "postgres://read.payments-db.local:5432/payments"
  # Application writes always go to the primary
  DATABASE_WRITE_URL: "postgres://primary.us-east-1.rds.amazonaws.com:5432/payments"
  # Connection pooling config
  READ_POOL_SIZE: "20"
  WRITE_POOL_SIZE: "5"
```

### Strategy 2: Partitioned Writes (Geo-Sharding)

Each region owns writes for data that "belongs" to it. A user in Europe writes to the European database. A user in the US writes to the US database.

```
GEO-SHARDED WRITES
════════════════════════════════════════════════════════════════

  User in Paris                     User in New York
       │                                  │
       ▼                                  ▼
  eu-west-1                         us-east-1
  ┌────────────────────┐           ┌────────────────────┐
  │                    │           │                    │
  │  EU Users DB       │           │  US Users DB       │
  │  (writes for EU)   │           │  (writes for US)   │
  │                    │   async   │                    │
  │  EU shard: users   │◀─────────│  (read replica of  │
  │  where region=EU   │─────────▶│   EU data for      │
  │                    │   async   │   global queries)  │
  └────────────────────┘           └────────────────────┘

  Partition key: user's home region (set at registration)

  Advantage: No write conflicts (each region owns its partition)
  Disadvantage: Cross-region queries are slower (need to fan out)

  Example: User in Paris reads US friend's profile
  -> Read from US data replica in eu-west-1 (~100ms stale)
  -> Or read from us-east-1 directly (adds ~80ms latency, fresh)
```

### Strategy 3: Conflict-Free Replicated Data Types (CRDTs)

CRDTs are data structures that allow concurrent modifications in different regions and can be merged automatically without conflicts.

```
CRDT EXAMPLE: SHOPPING CART (G-Counter + OR-Set)
════════════════════════════════════════════════════════════════

  Region A: User adds item X          Region B: User adds item Y
  Cart = {X: 1}                       Cart = {Y: 1}

  Network partition: Both regions operate independently

  Region A: User adds item Z          Region B: User increases X to 2
  Cart = {X: 1, Z: 1}                Cart = {X: 2, Y: 1}

  Network restores: MERGE using CRDT rules
  - OR-Set: Union of all items = {X, Y, Z}
  - G-Counter: Max of each counter = {X: 2, Y: 1, Z: 1}

  Final cart in BOTH regions: {X: 2, Y: 1, Z: 1}
  No conflicts. No data loss. Mathematically guaranteed.

  CRDTs work for:
  - Counters (likes, views, inventory decrements)
  - Sets (shopping carts, friend lists, tags)
  - Registers (last-writer-wins for simple values)

  CRDTs DON'T work for:
  - Bank balances (need strong consistency)
  - Inventory that can't go negative
  - Sequential operations (order processing)
```

### Choosing Your Consistency Model

| Data Type | Consistency Need | Recommended Strategy |
|---|---|---|
| User profiles | Eventual (stale reads OK) | Single-writer + async replicas |
| Shopping cart | Eventual (merge conflicts OK) | CRDTs (OR-Set) |
| Inventory count | Strong (can't oversell) | Single-writer or distributed lock |
| Financial transactions | Strong (must not lose) | Single-writer, synchronous |
| Session tokens | Eventual (sticky routing helps) | Distributed cache (Redis Global) |
| Search results | Eventual (slightly stale OK) | Regional index, async update |
| Chat messages | Causal (order matters per conversation) | Causal broadcast or geo-shard by conversation |

---

## Replication Lag: The Silent Killer

In any multi-region deployment, replication lag is the time between a write in one region and that write becoming visible in another region. It is not a bug to fix -- it is a physics constraint to design around.

```
REPLICATION LAG REALITY
════════════════════════════════════════════════════════════════

  Within same AZ:     < 1ms
  Cross-AZ:           1-2ms
  Cross-region (US):  20-40ms
  US to Europe:       70-120ms
  US to Asia:         150-250ms

  These are NETWORK latencies. Actual replication lag includes:
  - Write to primary WAL: ~1ms
  - WAL shipping to replica: network latency
  - Replay on replica: ~1-5ms

  Realistic replication lag:
  - Same region: 5-20ms
  - Cross-region: 100-500ms
  - Under load: Can spike to seconds
```

### The Read-Your-Own-Writes Problem

```
THE USER EXPERIENCE PROBLEM
════════════════════════════════════════════════════════════════

  1. User in EU updates their profile name to "Alice"
     -> Write goes to us-east-1 primary (their home region)

  2. Page refreshes, reads from eu-west-1 replica
     -> Replica hasn't received the update yet (150ms lag)
     -> User sees their OLD name

  3. User thinks the update failed, submits again
     -> Duplicate write, confusion, support ticket

  Solution: "Read-your-own-writes" consistency
  After a write, route that user's reads to the primary
  for a short window (e.g., 5 seconds) before reverting to replica.
```

```python
# Read-your-own-writes implementation
import time
import redis

cache = redis.Redis(host="session-cache.local", port=6379)

def write_user_profile(user_id, data):
    """Write to primary and set a read-after-write flag."""
    primary_db.execute("UPDATE users SET name = %s WHERE id = %s",
                       (data["name"], user_id))

    # Set a flag: "this user wrote recently, read from primary"
    cache.setex(f"raw:{user_id}", 5, "1")  # Expires in 5 seconds

def read_user_profile(user_id):
    """Read from primary if user wrote recently, otherwise replica."""
    if cache.get(f"raw:{user_id}"):
        # User wrote recently -- read from primary to ensure consistency
        return primary_db.execute("SELECT * FROM users WHERE id = %s",
                                  (user_id,))
    else:
        # Safe to read from local replica
        return replica_db.execute("SELECT * FROM users WHERE id = %s",
                                  (user_id,))
```

---

## Traffic Routing for Active-Active

### Latency-Based Routing

```bash
# AWS Route53: Latency-based routing
aws route53 change-resource-record-sets \
  --hosted-zone-id Z1234567890 \
  --change-batch '{
    "Changes": [
      {
        "Action": "CREATE",
        "ResourceRecordSet": {
          "Name": "api.example.com",
          "Type": "A",
          "SetIdentifier": "us-east-1",
          "Region": "us-east-1",
          "TTL": 60,
          "ResourceRecords": [{"Value": "10.0.1.100"}],
          "HealthCheckId": "hc-us-east-1"
        }
      },
      {
        "Action": "CREATE",
        "ResourceRecordSet": {
          "Name": "api.example.com",
          "Type": "A",
          "SetIdentifier": "eu-west-1",
          "Region": "eu-west-1",
          "TTL": 60,
          "ResourceRecords": [{"Value": "10.1.1.100"}],
          "HealthCheckId": "hc-eu-west-1"
        }
      },
      {
        "Action": "CREATE",
        "ResourceRecordSet": {
          "Name": "api.example.com",
          "Type": "A",
          "SetIdentifier": "ap-northeast-1",
          "Region": "ap-northeast-1",
          "TTL": 60,
          "ResourceRecords": [{"Value": "10.2.1.100"}],
          "HealthCheckId": "hc-ap-northeast-1"
        }
      }
    ]
  }'
```

### Weighted Routing for Gradual Rollout

```bash
# Start with 90/10 split to canary new region
aws route53 change-resource-record-sets \
  --hosted-zone-id Z1234567890 \
  --change-batch '{
    "Changes": [
      {
        "Action": "CREATE",
        "ResourceRecordSet": {
          "Name": "api.example.com",
          "Type": "A",
          "SetIdentifier": "us-east-1-weighted",
          "Weight": 90,
          "TTL": 60,
          "ResourceRecords": [{"Value": "10.0.1.100"}],
          "HealthCheckId": "hc-us-east-1"
        }
      },
      {
        "Action": "CREATE",
        "ResourceRecordSet": {
          "Name": "api.example.com",
          "Type": "A",
          "SetIdentifier": "eu-west-1-weighted",
          "Weight": 10,
          "TTL": 60,
          "ResourceRecords": [{"Value": "10.1.1.100"}],
          "HealthCheckId": "hc-eu-west-1"
        }
      }
    ]
  }'
```

---

## Idempotency: The Active-Active Safety Net

In an active-active deployment, requests can be retried, duplicated, or rerouted between regions. Every write operation must be idempotent -- applying it twice must produce the same result as applying it once.

```
WHY IDEMPOTENCY MATTERS IN ACTIVE-ACTIVE
════════════════════════════════════════════════════════════════

  User clicks "Pay" button:

  1. Request goes to us-east-1 (normal routing)
  2. us-east-1 processes payment, starts writing to DB
  3. Network blip: client doesn't receive response
  4. Client retries (automatic retry or user clicks again)
  5. Retry goes to eu-west-1 (load balancer rerouted)
  6. eu-west-1 processes payment AGAIN

  Without idempotency: User charged twice.
  With idempotency: Second request recognized as duplicate,
                     returns original result.
```

### Implementing Idempotency Keys

```python
# Idempotency key pattern
import hashlib
import redis
import json

cache = redis.Redis(host="idempotency-cache.local", port=6379)

def process_payment(request):
    """Process a payment with idempotency protection."""
    # Client must send an idempotency key (UUID generated client-side)
    idempotency_key = request.headers.get("Idempotency-Key")
    if not idempotency_key:
        return {"error": "Idempotency-Key header required"}, 400

    # Check if we've seen this request before
    cached_result = cache.get(f"idempotent:{idempotency_key}")
    if cached_result:
        # We've already processed this request -- return the cached result
        return json.loads(cached_result), 200

    # Try to acquire a lock (prevent concurrent processing of same key)
    lock_acquired = cache.set(
        f"idempotent-lock:{idempotency_key}",
        "processing",
        nx=True,  # Only set if not exists
        ex=30     # Lock expires in 30 seconds
    )

    if not lock_acquired:
        # Another instance is processing this request right now
        return {"error": "Request is being processed"}, 409

    try:
        # Process the payment
        result = payment_gateway.charge(
            amount=request.json["amount"],
            currency=request.json["currency"],
            customer_id=request.json["customer_id"]
        )

        # Cache the result for 24 hours
        cache.setex(
            f"idempotent:{idempotency_key}",
            86400,  # 24 hours
            json.dumps(result)
        )

        return result, 200
    finally:
        cache.delete(f"idempotent-lock:{idempotency_key}")
```

```yaml
# Kubernetes deployment with idempotency cache
apiVersion: apps/v1
kind: Deployment
metadata:
  name: payment-api
  namespace: payments
spec:
  replicas: 4
  selector:
    matchLabels:
      app: payment-api
  template:
    metadata:
      labels:
        app: payment-api
    spec:
      containers:
        - name: api
          image: company/payment-api:v2.8.1
          env:
            - name: IDEMPOTENCY_CACHE_URL
              value: "redis://idempotency-redis.payments.svc:6379"
            - name: IDEMPOTENCY_TTL_SECONDS
              value: "86400"
            - name: REGION
              valueFrom:
                configMapKeyRef:
                  name: region-config
                  key: REGION
```

---

## Cost Implications of Active-Active

Active-active is expensive. Understanding the cost model helps you make informed decisions about which components justify the investment.

```
ACTIVE-ACTIVE COST BREAKDOWN
════════════════════════════════════════════════════════════════

  Single-Region Cost: $25,000/month
  ┌──────────────────────────────────────┐
  │ EKS cluster (6 nodes)      $4,200   │
  │ RDS Primary (Multi-AZ)     $3,800   │
  │ ElastiCache                $1,200   │
  │ ALB + NAT Gateway          $800     │
  │ S3 + CloudFront            $600     │
  │ Other (monitoring, etc.)   $2,400   │
  │ Data transfer              $2,000   │
  └──────────────────────────────────────┘

  Active-Active (2 regions) Cost: $58,000/month (+132%)
  ┌──────────────────────────────────────┐
  │ 2x EKS clusters            $8,400   │  (2x compute)
  │ RDS Primary + Cross-Region  $6,200  │  (+63% for replica)
  │ 2x ElastiCache Global      $3,200   │  (2.6x for global)
  │ 2x ALB + NAT               $1,600   │  (2x)
  │ S3 + CloudFront (shared)   $800     │  (+33%)
  │ 2x Monitoring              $4,800   │  (2x)
  │ Cross-region replication    $3,500   │  (NEW cost)
  │ Data transfer (cross-region)$5,500  │  (+175%)
  │ Global Load Balancer        $1,000  │  (NEW cost)
  │ Additional operational cost $3,000   │  (NEW: multi-region ops)
  └──────────────────────────────────────┘

  Active-Active is NOT 2x. It's 2-3x due to:
  - Cross-region data replication costs
  - Global load balancing
  - Increased operational complexity (monitoring, debugging, deploys)
```

### Cost Optimization for Active-Active

```
COST OPTIMIZATION STRATEGIES
════════════════════════════════════════════════════════════════

1. Not everything needs active-active
   Stateless APIs: YES (easy, cheap)
   Read-heavy services: YES (replicas are cheap)
   Write-heavy services: MAYBE (consider geo-sharding)
   Batch processing: NO (run in one region, failover)

2. Right-size the secondary region
   Primary: 6 nodes (100% capacity)
   Secondary: 4 nodes (70% capacity)
   On failover: auto-scale secondary to 6 nodes
   Saves: ~$1,400/month on compute

3. Use reserved instances / savings plans
   Active-active GUARANTEES you'll use compute in both regions
   Perfect candidate for 1-year commitments
   Saves: 30-40% on compute

4. Compress cross-region replication
   Database WAL compression: 60-70% reduction
   Application-level compression for event streams
   Saves: $1,000-$2,000/month on data transfer
```

---

## Did You Know?

1. **Netflix runs active-active across three AWS regions** (us-east-1, us-west-2, eu-west-1) and has been doing so since 2012. Their "Zuul" gateway handles over 300 billion requests per day across these regions. The annual cost of their multi-region infrastructure is estimated at over $400 million, but a single hour of global downtime would cost approximately $16 million in lost revenue -- making active-active a clear business case.

2. **CockroachDB was specifically designed for multi-region active-active writes.** It implements a distributed consensus protocol (a variant of Raft) that can commit writes across regions with serializable isolation. The trade-off is write latency: a cross-region write requires a round-trip to achieve consensus, adding 100-250ms. For read-heavy workloads (which most web applications are), this trade-off is excellent.

3. **The "read-your-own-writes" consistency problem** was formally defined by Doug Terry et al. at Microsoft Research in 1994. Thirty years later, it remains one of the most common bugs in distributed systems. Amazon's DynamoDB, Google's Spanner, and Azure's Cosmos DB all offer "session consistency" modes that guarantee read-your-own-writes, but only if the client maintains session affinity.

4. **Cross-region data transfer between AWS regions costs $0.02/GB**, but between AWS and GCP or Azure it costs $0.09/GB (standard internet egress rates). This 4.5x cost difference is one reason why multi-cloud active-active is significantly more expensive than multi-region active-active within a single cloud. Google's "cross-cloud interconnect" and AWS's "site-to-site VPN" reduce this somewhat, but never to intra-cloud rates.

---

## Common Mistakes

| Mistake | Why It Happens | How to Fix It |
|---|---|---|
| Treating active-active as "just deploy twice" | Underestimating state management complexity | Start with stateless services only. Add stateful active-active incrementally, service by service, with explicit consistency strategies. |
| Not handling replication lag in the application | "The database handles replication" | Build read-your-own-writes logic. Display "update pending" states. Use causal consistency where available. |
| Skipping idempotency for write operations | "Retries are rare" | In active-active, retries happen constantly due to routing changes. Every write must be idempotent. Add idempotency keys to all mutation APIs. |
| Global distributed locks | "We need consistency so let's lock across regions" | Cross-region locks add 100-300ms to every locked operation. Use geo-sharding instead: each region owns writes to its data partition. |
| Running the same batch jobs in every region | "Active-active means everything runs everywhere" | Batch jobs, cron jobs, and migrations should run in ONE region. Use leader election or a designated "batch region." |
| Not testing regional failover under load | "We tested failover in staging" | Production traffic patterns create cascading failures that staging can't replicate. Run monthly failover drills during peak traffic with real user traffic redirected. |
| Using synchronous cross-region replication for everything | "We need strong consistency" | Synchronous replication adds 100-300ms to every write. Only use it for data that truly needs it (financial transactions). Use async for everything else. |
| Ignoring clock skew between regions | "NTP handles it" | Clock skew between regions can be 10-50ms even with NTP. Use Hybrid Logical Clocks (HLC) or TrueTime-style APIs for ordering events across regions. |

---

## Quiz

<details>
<summary>1. Why is active-active not simply "deploy the same thing in two regions"?</summary>

Active-active requires solving the distributed state problem. When both regions can write data, you must handle: (a) replication lag -- reads in one region may not see recent writes from another, (b) write conflicts -- two regions modifying the same data simultaneously, (c) idempotency -- requests retried or rerouted between regions, and (d) ordering -- events from different regions must be merged into a consistent timeline. Stateless services are easy to deploy in multiple regions, but stateful services require explicit consistency strategies (single-writer, geo-sharding, CRDTs) that fundamentally change application design.
</details>

<details>
<summary>2. When would you choose geo-sharded writes over single-writer for an active-active deployment?</summary>

Choose geo-sharding when: (a) data has a natural geographic affinity (user data belongs to the user's home region), (b) cross-region writes are latency-sensitive (geo-sharding keeps writes local), (c) write volume is high enough that a single-writer becomes a bottleneck, and (d) cross-shard queries are infrequent. Choose single-writer when: (a) all data must be globally consistent (financial systems), (b) there is no natural partition key, (c) cross-entity transactions are common, or (d) the write volume is low enough that one primary can handle it. Geo-sharding reduces write latency but increases complexity for queries that span shards.
</details>

<details>
<summary>3. A user in Europe updates their profile. One second later, they refresh the page and see their old data. What happened and how do you fix it?</summary>

The user's write went to the primary database (possibly in us-east-1). The page refresh read from the European replica, which has not yet received the replication update (100-500ms lag). The user sees stale data because the replica is eventually consistent. Fix with "read-your-own-writes" consistency: after a write, set a short-lived flag (in a distributed cache like Redis) indicating this user wrote recently. For the next 5-10 seconds, route this user's reads to the primary instead of the replica. The flag expires after the replication lag window, and subsequent reads safely go to the local replica again. This balances consistency (users see their own writes) with performance (most reads are still local).
</details>

<details>
<summary>4. Why is idempotency critical in active-active deployments specifically?</summary>

In active-active, requests can be duplicated or rerouted between regions due to: (a) load balancer failover during transient network issues -- the request was partially processed in region A, then retried in region B; (b) client-side retries when responses are lost due to routing changes; (c) message queue redelivery when a consumer in one region fails and the message is picked up by another region. Without idempotency, these scenarios cause double charges, duplicate orders, or inconsistent state. The idempotency key pattern (client sends a unique key, server caches the result) ensures that processing a request twice produces the same outcome as processing it once.
</details>

<details>
<summary>5. An active-active deployment costs 2.3x the single-region deployment. The business asks if it's worth it. How do you frame the cost justification?</summary>

Frame it as a risk calculation: (1) Calculate hourly revenue impact of downtime. If the company makes $10M/month, each hour of downtime costs approximately $14,000. (2) Calculate expected downtime reduction. Active-passive with 15-minute RTO might have 2-4 hours of downtime per year (including detection time). Active-active reduces this to minutes per year. (3) Calculate the cost difference. If active-active costs $33K/month extra ($396K/year), and it prevents 3 hours of downtime worth $42K, the pure financial case is negative. But add: reputational damage, customer churn, SLA penalties, and competitive risk. The food delivery example in this module lost $3.8M in a single 23-minute degradation. Often a single major incident justifies years of active-active costs.
</details>

<details>
<summary>6. Why should batch jobs and cron jobs NOT run in every region in an active-active deployment?</summary>

Batch jobs often perform operations that should happen exactly once: sending daily email digests, generating reports, processing end-of-day settlements, running database migrations. If the same cron job runs in three regions, users get three emails, reports are generated three times, and migrations might conflict. The fix is to designate one region as the "batch leader" (using leader election or static configuration) and run cron jobs only there. If that region fails, another region can take over batch leadership. This is different from API traffic, which should be distributed -- batch jobs are inherently single-instance operations that need coordination, not replication.
</details>

---

## Hands-On Exercise: Design an Active-Active Architecture

In this exercise, you will design an active-active architecture for a realistic application and implement the key patterns.

### Scenario

**Application**: TravelBook (a travel booking platform)
- 5 million monthly active users
- 60% of traffic from North America, 30% from Europe, 10% from Asia
- Core operations: search (read-heavy), booking (write), user profiles (read/write)
- Current setup: single-region (us-east-1), RTO=30min, RPO=5min
- Target: active-active in us-east-1 + eu-west-1, near-zero RTO/RPO

### Task 1: Classify Services by Consistency Need

For each TravelBook service, determine the active-active strategy.

<details>
<summary>Solution</summary>

| Service | Read/Write Ratio | Consistency Need | Strategy |
|---|---|---|---|
| Search API | 99% read | Eventual (stale results OK for seconds) | Active-active, regional search index |
| Booking Engine | 20% write | Strong (can't double-book) | Single-writer (us-east-1), proxied writes from EU |
| User Profiles | 95% read | Session (read-your-own-writes) | Single-writer + read replicas + RYOW cache |
| Payment Service | 100% write | Strong + idempotent | Single-writer (us-east-1), idempotency keys |
| Notification Service | 90% write | Eventual (delayed delivery OK) | Regional queues, deduplicated delivery |
| Image/CDN Service | 100% read | Eventual (cached at edge) | CloudFront/CDN, origin in both regions |
| Review System | 80% read | Eventual (new reviews appear within seconds) | Single-writer + async replication |

Key decisions:
- Booking and Payment stay single-writer because consistency > latency
- Search index is replicated per region for fastest reads
- User profiles use read-your-own-writes pattern
</details>

### Task 2: Design the Data Replication Strategy

For each database, specify the replication approach and expected lag.

<details>
<summary>Solution</summary>

```
Database Replication Plan
═══════════════════════════════════════

1. Primary PostgreSQL (users, bookings, payments)
   Primary: us-east-1 (RDS Multi-AZ)
   Replica: eu-west-1 (RDS Cross-Region Read Replica)
   Replication: Async, expected lag 100-300ms
   Failover: Manual promotion (RPO = replication lag)

2. Elasticsearch (search index)
   us-east-1: Independent cluster, fed by CDC from PostgreSQL
   eu-west-1: Independent cluster, fed by CDC from PostgreSQL
   Not replicated between regions -- each rebuilds from source
   Lag: 1-5 seconds (CDC processing time)

3. Redis (session cache, idempotency keys, RYOW flags)
   us-east-1: ElastiCache Global Datastore (primary)
   eu-west-1: ElastiCache Global Datastore (replica, reads)
   Replication: Async, expected lag < 1ms (same continent)
   Special: Idempotency keys written to BOTH regions
            (using Global Datastore's cross-region replication)

4. S3 (images, documents)
   us-east-1: Primary bucket
   eu-west-1: Cross-Region Replication
   Replication: Async, typically < 15 minutes
   CloudFront caches in both regions (edge caching)
```
</details>

### Task 3: Implement Read-Your-Own-Writes Pattern

Write the application code and Kubernetes configuration for the RYOW pattern for user profiles.

<details>
<summary>Solution</summary>

```python
# user_service.py - Read-your-own-writes implementation
import redis
import psycopg2
import os
import json

REGION = os.environ["REGION"]
RYOW_TTL = int(os.environ.get("RYOW_TTL_SECONDS", "5"))

# Database connections
primary_db = psycopg2.connect(os.environ["DATABASE_WRITE_URL"])
replica_db = psycopg2.connect(os.environ["DATABASE_READ_URL"])
cache = redis.Redis.from_url(os.environ["CACHE_URL"])

def update_profile(user_id, data):
    """Update user profile with RYOW flag."""
    with primary_db.cursor() as cur:
        cur.execute(
            "UPDATE users SET name=%s, bio=%s, updated_at=NOW() WHERE id=%s RETURNING *",
            (data["name"], data["bio"], user_id)
        )
        updated = cur.fetchone()
        primary_db.commit()

    # Set RYOW flag: "this user wrote, read from primary for N seconds"
    cache.setex(f"ryow:{user_id}", RYOW_TTL, REGION)

    return updated

def get_profile(user_id):
    """Read profile from primary if RYOW, otherwise local replica."""
    ryow_flag = cache.get(f"ryow:{user_id}")

    if ryow_flag:
        # Recent write detected -- read from primary for consistency
        db = primary_db
        source = "primary"
    else:
        # No recent write -- safe to read from local replica
        db = replica_db
        source = "replica"

    with db.cursor() as cur:
        cur.execute("SELECT * FROM users WHERE id = %s", (user_id,))
        profile = cur.fetchone()

    return {"profile": profile, "_source": source}
```

```yaml
# Kubernetes deployment for us-east-1
apiVersion: apps/v1
kind: Deployment
metadata:
  name: user-service
  namespace: travelbook
spec:
  replicas: 4
  selector:
    matchLabels:
      app: user-service
  template:
    metadata:
      labels:
        app: user-service
    spec:
      containers:
        - name: api
          image: company/user-service:v3.1.0
          env:
            - name: REGION
              value: "us-east-1"
            - name: DATABASE_WRITE_URL
              value: "postgres://primary.rds.us-east-1.amazonaws.com:5432/travelbook"
            - name: DATABASE_READ_URL
              value: "postgres://replica.rds.us-east-1.amazonaws.com:5432/travelbook"
            - name: CACHE_URL
              value: "redis://global-cache.us-east-1.cache.amazonaws.com:6379"
            - name: RYOW_TTL_SECONDS
              value: "5"
          ports:
            - containerPort: 8080
          readinessProbe:
            httpGet:
              path: /healthz
              port: 8080
            initialDelaySeconds: 5
            periodSeconds: 10
```
</details>

### Task 4: Implement Idempotent Booking

Write the idempotency key pattern for the booking service.

<details>
<summary>Solution</summary>

```python
# booking_service.py - Idempotent booking
import redis
import json
import uuid
from datetime import datetime

cache = redis.Redis.from_url(os.environ["CACHE_URL"])
IDEMPOTENCY_TTL = 86400  # 24 hours

def create_booking(request):
    """Create a booking with idempotency protection."""
    idem_key = request.headers.get("Idempotency-Key")
    if not idem_key:
        return {"error": "Idempotency-Key header is required"}, 400

    # Check for cached result
    cached = cache.get(f"booking:idem:{idem_key}")
    if cached:
        result = json.loads(cached)
        result["_idempotent"] = True  # Flag that this is a cached response
        return result, 200

    # Acquire processing lock
    if not cache.set(f"booking:lock:{idem_key}", "1", nx=True, ex=60):
        return {"error": "Booking is being processed, please wait"}, 409

    try:
        # Check availability (read from primary for consistency)
        available = check_availability(
            request.json["hotel_id"],
            request.json["check_in"],
            request.json["check_out"]
        )
        if not available:
            result = {"error": "Room no longer available"}
            cache.setex(f"booking:idem:{idem_key}", IDEMPOTENCY_TTL,
                       json.dumps(result))
            return result, 409

        # Create the booking
        booking_id = str(uuid.uuid4())
        booking = {
            "booking_id": booking_id,
            "hotel_id": request.json["hotel_id"],
            "check_in": request.json["check_in"],
            "check_out": request.json["check_out"],
            "guest_id": request.json["guest_id"],
            "status": "confirmed",
            "created_at": datetime.utcnow().isoformat(),
            "region": os.environ["REGION"]
        }

        db.execute(
            "INSERT INTO bookings (id, hotel_id, check_in, check_out, guest_id, status) "
            "VALUES (%s, %s, %s, %s, %s, %s)",
            (booking_id, booking["hotel_id"], booking["check_in"],
             booking["check_out"], booking["guest_id"], "confirmed")
        )
        db.commit()

        # Cache the result
        cache.setex(f"booking:idem:{idem_key}", IDEMPOTENCY_TTL,
                   json.dumps(booking))

        return booking, 201

    finally:
        cache.delete(f"booking:lock:{idem_key}")
```
</details>

### Task 5: Calculate the Cost

Estimate the monthly cost difference between single-region and active-active for TravelBook.

<details>
<summary>Solution</summary>

```
Single-Region (us-east-1):
  EKS (6x m7i.xlarge nodes)         $3,600
  RDS (db.r7g.xlarge, Multi-AZ)     $2,800
  ElastiCache (cache.r7g.large)     $900
  Elasticsearch (3x r7g.large)      $1,500
  ALB                                $200
  NAT Gateway + data processing     $800
  S3 + CloudFront                    $500
  Data transfer (internet egress)    $1,800
  Monitoring (Datadog/Prometheus)    $1,200
  ─────────────────────────────────────────
  TOTAL:                            $13,300/month

Active-Active (us-east-1 + eu-west-1):
  2x EKS (5 nodes each, smaller secondary) $5,800
  RDS Primary + Cross-Region Replica       $4,100
  ElastiCache Global Datastore             $2,400
  2x Elasticsearch (independent clusters)  $3,000
  2x ALB                                   $400
  2x NAT Gateway                           $1,600
  S3 + CRR + CloudFront                    $800
  Cross-region data transfer               $2,200
  Global Load Balancer (Route53/GA)        $400
  2x Monitoring                            $2,400
  Additional operational overhead          $1,500
  ─────────────────────────────────────────────
  TOTAL:                                   $24,600/month

Cost increase: $11,300/month (+85%)

Break-even analysis:
  If 1 hour of downtime = $15,000 in lost bookings
  Active-active prevents ~4 hours of downtime per year
  Prevented losses: $60,000/year
  Active-active cost: $135,600/year
  Pure financial ROI: negative

  BUT: Add customer trust, competitive positioning, and
  SLA penalty avoidance, and the case usually becomes positive
  for businesses above $50M annual revenue.
```
</details>

### Success Criteria

- [ ] Each service classified with appropriate consistency strategy
- [ ] Data replication plan specifies mechanism, lag, and failover for each database
- [ ] RYOW implementation correctly routes reads to primary after writes
- [ ] Idempotency key pattern prevents duplicate bookings across regions
- [ ] Cost analysis includes cross-region transfer, replication, and operational overhead

---

## Next Module

[Module 8.7: Stateful Workload Migration & Data Gravity](../module-8.7-stateful-migration/) -- You know how to run workloads across regions. Now learn how to move them. Database migrations, the Strangler Fig pattern, CSI snapshots, and the art of zero-downtime migration for stateful workloads.
