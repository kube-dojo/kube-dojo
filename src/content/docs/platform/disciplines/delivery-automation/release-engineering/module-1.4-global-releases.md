---
title: "Module 1.4: Multi-Region & Global Release Orchestration"
slug: platform/disciplines/delivery-automation/release-engineering/module-1.4-global-releases
sidebar:
  order: 5
---
> **Discipline Module** | Complexity: `[COMPLEX]` | Time: 3 hours

## Prerequisites

Before starting this module:
- **Required**: [Module 1.2: Argo Rollouts](../module-1.2-argo-rollouts/) — Canary deployments, automated analysis, progressive delivery
- **Required**: Multi-cluster Kubernetes concepts — Understanding of running workloads across multiple clusters
- **Required**: ArgoCD basics — GitOps principles, Application CRD, sync workflows
- **Recommended**: DNS and global load balancing concepts
- **Recommended**: Understanding of data replication and eventual consistency

---

## Why This Module Matters

On October 4, 2021, Facebook, Instagram, and WhatsApp went dark for six hours. The outage affected 3.5 billion users globally. The root cause was a configuration change to their backbone routers that cascaded across every region simultaneously. There was no containment. There was no staged rollout of the configuration change. One bad push propagated everywhere at once, and the blast radius was the entire planet.

This is the nightmare scenario of global releases: a change that should have been tested in one region before spreading to others instead hits everything simultaneously. And at global scale, "everything" means billions of users, hundreds of data centers, and revenue measured in millions per minute of downtime.

Multi-region release orchestration is the discipline of deploying changes across geographically distributed infrastructure in a controlled, staged manner. Instead of pushing to all clusters at once, you deploy to a canary region first, validate, then progressively roll out to additional regions. Each region acts as a blast radius boundary — if a change fails in EU-West, Asia-Pacific and US-East are unaffected.

This module teaches you how to design and implement ring deployments, manage data consistency during cross-region rollouts, orchestrate traffic shifting with global load balancers, and automate it all with ArgoCD ApplicationSets.

---

## The Geography of Failure

### Why Single-Region Deployments Are Not Enough

In a single cluster, a bad canary affects a percentage of your users. In a global deployment, a bad canary can affect an entire continent:

```
Single-cluster canary:
  5% of users affected if canary is bad
  Recovery: seconds (rollback canary)

Global simultaneous deploy:
  100% of users affected if release is bad
  Recovery: minutes to hours (rollback everywhere)

Ring deployment:
  ~10% of users affected (canary region only)
  Recovery: seconds (halt propagation, rollback one region)
```

### Regional Blast Radius

The core principle: **geography is a natural blast radius boundary**.

```
┌──────────────────────────────────────────────────────────────────┐
│                        Global User Base                          │
│                                                                  │
│   ┌──────────────┐   ┌──────────────┐   ┌──────────────┐       │
│   │  EU-West     │   │  US-East     │   │  AP-South    │       │
│   │  Region      │   │  Region      │   │  Region      │       │
│   │              │   │              │   │              │       │
│   │  30% users   │   │  45% users   │   │  25% users   │       │
│   │              │   │              │   │              │       │
│   └──────────────┘   └──────────────┘   └──────────────┘       │
│                                                                  │
│   Ring 1 (Canary)     Ring 2              Ring 3                │
│   Deploy first        Deploy after        Deploy last           │
│   Smallest region     validation          Largest region        │
└──────────────────────────────────────────────────────────────────┘
```

If Ring 1 fails, 70% of your users are untouched. If Ring 2 also fails, 25% of your users are still safe. Geography gives you natural isolation that no amount of in-cluster canary analysis can provide.

---

## Ring Deployment Architecture

### What Is a Ring Deployment?

A ring deployment divides your infrastructure into concentric rings, with each ring representing a larger blast radius:

```
Ring 0: Internal/Staging
  └─ Company employees, synthetic traffic
  └─ Zero user impact if it fails

Ring 1: Canary Region
  └─ Smallest production region
  └─ ~5-10% of real user traffic
  └─ Full production environment (not staging)

Ring 2: Secondary Regions
  └─ Medium-sized regions
  └─ ~30-40% of total traffic
  └─ Only deployed after Ring 1 bakes for hours

Ring 3: Primary Regions
  └─ Largest regions (US, EU)
  └─ ~50-60% of total traffic
  └─ Only deployed after Ring 2 is stable
```

### Ring Progression

```
Time ──────────────────────────────────────────────────────►

Ring 0 (Internal)
  ████████ Deploy → Validate (1h) → ✓ Promote
                                      │
Ring 1 (Canary: ap-south-1)           │
  ░░░░░░░░░████████ Deploy → Validate (4h) → ✓ Promote
                                                 │
Ring 2 (eu-west-1)                               │
  ░░░░░░░░░░░░░░░░░░░████████ Deploy → Validate (2h) → ✓ Promote
                                                           │
Ring 3 (us-east-1)                                         │
  ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░████████ Deploy → ✓ GA
```

### Choosing Your Canary Region

The canary region should be:

| Criterion | Why |
|-----------|-----|
| **Smallest production region** | Minimizes blast radius |
| **Representative traffic** | Must exercise the same code paths as larger regions |
| **Has monitoring** | Needs the same observability as other regions |
| **Timezone-appropriate** | Deploy during that region's business hours |
| **Recoverable** | Other regions can absorb its traffic during failover |

**Anti-patterns:**
- Choosing your busiest region as canary (defeats the purpose)
- Choosing a region with different traffic patterns (does not validate real behavior)
- Choosing a region without monitoring (blind canary)

---

## Data Replication During Rollouts

### The Cross-Region Data Problem

When deploying across regions, data consistency becomes critical. If the new version writes data in a format the old version cannot read, and data replicates between regions, you have a problem:

```
Region A (v2)          Region B (v1)
  │                       │
  │ Write new format      │
  │ {"name": "Alice",     │
  │  "email_v2": true}    │
  │                       │
  └───── Replicates ──────►  v1 cannot read "email_v2"
                              field → errors or data loss
```

### Safe Cross-Region Deployment Patterns

**Pattern 1: Schema-Compatible Versions Only**

Both v1 and v2 must read and write the same data format. Use the expand-contract pattern from Module 1.1:

```
Phase 1: v2 writes NEW format + OLD format (backward compatible)
Phase 2: All regions on v2 → stop writing OLD format
Phase 3: Clean up OLD format
```

**Pattern 2: Region-Isolated Data**

Each region has its own database. No cross-region replication during rollout:

```
Region A (v2)          Region B (v1)
  │                       │
  │ DB-A (v2 schema)      │ DB-B (v1 schema)
  │                       │
  └─── No replication ────┘  (temporarily paused)
```

After all regions are on v2, resume replication. This requires your application to tolerate temporary data divergence.

**Pattern 3: Feature-Flagged Data Paths**

The new data path is behind a feature flag that is only enabled after all regions have the new code:

```
1. Deploy v2 to all regions (new code present but flag OFF)
2. Verify all regions are on v2
3. Enable feature flag globally
4. New data path activates everywhere simultaneously
```

This is the safest approach but requires the feature flag infrastructure from Module 1.3.

### Data Migration Anti-Patterns in Multi-Region

| Anti-Pattern | Risk | Safe Alternative |
|-------------|------|-----------------|
| Running migrations in canary region only | Other regions cannot read new format | Run backward-compatible migrations everywhere first |
| Replicating during schema transition | v1 regions crash on v2 data | Pause replication or use dual-format writes |
| Assuming eventual consistency is immediate | Stale reads during rollout | Design for stale reads; use version headers |
| Different schema versions across regions for days | Operational complexity, hard to rollback | Minimize the time window; deploy schema separately from code |

---

## Global Load Balancing and Traffic Shifting

### DNS-Based Global Load Balancing

The simplest form of global traffic management uses DNS:

```
                    ┌──────────────────┐
   User request ──► │  DNS (e.g.,     │
                    │  Route 53,       │
                    │  Cloud DNS)      │
                    └────────┬─────────┘
                             │
           ┌─────────────────┼─────────────────┐
           │ Geo-routed      │                  │
           ▼                 ▼                  ▼
    ┌─────────────┐  ┌─────────────┐  ┌─────────────┐
    │  EU Cluster  │  │  US Cluster  │  │  AP Cluster  │
    │  (v2)        │  │  (v1)        │  │  (v1)        │
    └─────────────┘  └─────────────┘  └─────────────┘
```

**Limitations of DNS-based shifting:**
- DNS TTLs mean changes take minutes to propagate
- No traffic percentage control (all-or-nothing per region)
- Client-side caching can override DNS decisions
- No health-check-driven failover at the request level

### Anycast and Global Load Balancers

Modern global load balancers (Cloudflare, AWS Global Accelerator, Google Cloud Load Balancing) use anycast and provide:

- **Per-request routing**: Every request is independently routed
- **Health-check failover**: Unhealthy regions are automatically drained
- **Traffic weights**: Send 10% to EU, 90% to US — per request, not per DNS TTL
- **Header injection**: Add region/version headers for observability

```yaml
# Example: AWS Global Accelerator traffic dial
# Shift 10% of EU traffic to test region during canary
listener:
  endpoint_groups:
    - region: eu-west-1
      weight: 90
      endpoints:
        - id: eu-west-1-prod
    - region: eu-west-2
      weight: 10
      endpoints:
        - id: eu-west-2-canary
```

### Traffic Shifting During Ring Deployment

```
Ring 1 Deploy:
  ┌─────────────────────────────────────────────────────────┐
  │ ap-south-1: 100% traffic → v2 (canary ring)            │
  │ eu-west-1:  100% traffic → v1                          │
  │ us-east-1:  100% traffic → v1                          │
  └─────────────────────────────────────────────────────────┘
                        │
            Validate for 4 hours ✓
                        │
                        ▼
Ring 2 Deploy:
  ┌─────────────────────────────────────────────────────────┐
  │ ap-south-1: 100% traffic → v2 ✓                        │
  │ eu-west-1:  100% traffic → v2 (deploying)              │
  │ us-east-1:  100% traffic → v1                          │
  └─────────────────────────────────────────────────────────┘
                        │
            Validate for 2 hours ✓
                        │
                        ▼
Ring 3 Deploy:
  ┌─────────────────────────────────────────────────────────┐
  │ ap-south-1: 100% traffic → v2 ✓                        │
  │ eu-west-1:  100% traffic → v2 ✓                        │
  │ us-east-1:  100% traffic → v2 (deploying)              │
  └─────────────────────────────────────────────────────────┘
```

### Emergency Regional Failover

If Ring 1 fails, shift its traffic to a healthy region:

```bash
# Before failover:
#   ap-south-1: serving AP users → v2 (BROKEN)
#   eu-west-1: serving EU users → v1 (healthy)

# Failover: drain ap-south-1, shift to eu-west-1
# (Global LB health checks can do this automatically)

# After failover:
#   ap-south-1: 0% traffic (draining)
#   eu-west-1: serving EU + AP users → v1 (healthy, higher load)
```

This is why regions should be provisioned with headroom — they need to absorb traffic from a failed region.

---

## ArgoCD ApplicationSets for Multi-Cluster Deployments

### Why ApplicationSets?

ArgoCD manages deployments to Kubernetes clusters via `Application` CRDs. For a single cluster, you create one Application. For 10 clusters, you would need 10 nearly identical Applications — tedious and error-prone.

**ApplicationSets** are a template that generates Applications dynamically:

```
ApplicationSet (template)
         │
         ├── generates → Application (eu-west-1)
         ├── generates → Application (us-east-1)
         └── generates → Application (ap-south-1)
```

### Basic ApplicationSet

```yaml
apiVersion: argoproj.io/v1alpha1
kind: ApplicationSet
metadata:
  name: webapp
  namespace: argocd
spec:
  generators:
    - list:
        elements:
          - cluster: eu-west-1
            url: https://eu-west-1.k8s.example.com
            ring: "1"
          - cluster: us-east-1
            url: https://us-east-1.k8s.example.com
            ring: "3"
          - cluster: ap-south-1
            url: https://ap-south-1.k8s.example.com
            ring: "2"
  template:
    metadata:
      name: 'webapp-{{cluster}}'
    spec:
      project: default
      source:
        repoURL: https://github.com/myorg/webapp
        targetRevision: HEAD
        path: 'deploy/overlays/{{cluster}}'
      destination:
        server: '{{url}}'
        namespace: webapp
      syncPolicy:
        automated:
          prune: true
          selfHeal: true
```

This generates three ArgoCD Applications — one per cluster — each deploying from a cluster-specific overlay.

### Ring Deployment with ApplicationSets

The key to ring deployments with ApplicationSets is controlling **which clusters get the new version and when**. There are several approaches:

**Approach 1: Branch/Tag per Ring**

```yaml
# Ring 1 clusters point to the release branch
# Ring 2-3 clusters point to the current stable tag
spec:
  generators:
    - list:
        elements:
          - cluster: ap-south-1
            url: https://ap-south-1.k8s.example.com
            revision: release/v2.1.0     # ← New version
          - cluster: eu-west-1
            url: https://eu-west-1.k8s.example.com
            revision: v2.0.0             # ← Current stable
          - cluster: us-east-1
            url: https://us-east-1.k8s.example.com
            revision: v2.0.0             # ← Current stable
  template:
    spec:
      source:
        targetRevision: '{{revision}}'
```

Promote Ring 2 by changing `eu-west-1`'s revision to `release/v2.1.0`. This is a Git commit — auditable, reviewable, reversible.

**Approach 2: Directory-per-Ring with Kustomize**

```
deploy/
├── base/                    # Common configuration
│   ├── deployment.yaml
│   ├── service.yaml
│   └── kustomization.yaml
├── overlays/
│   ├── ring-1/             # Canary ring
│   │   └── kustomization.yaml  (image: v2.1.0)
│   ├── ring-2/             # Secondary ring
│   │   └── kustomization.yaml  (image: v2.0.0)
│   └── ring-3/             # Primary ring
│       └── kustomization.yaml  (image: v2.0.0)
```

```yaml
spec:
  generators:
    - list:
        elements:
          - cluster: ap-south-1
            url: https://ap-south-1.k8s.example.com
            ring: ring-1
          - cluster: eu-west-1
            url: https://eu-west-1.k8s.example.com
            ring: ring-2
          - cluster: us-east-1
            url: https://us-east-1.k8s.example.com
            ring: ring-3
  template:
    spec:
      source:
        path: 'deploy/overlays/{{ring}}'
```

Promote by updating the image in `ring-2/kustomization.yaml`. Git diff shows exactly what changed.

**Approach 3: Progressive Sync with Waves**

Use ArgoCD sync waves to control deployment ordering:

```yaml
# In the Application template, add annotations
template:
  metadata:
    name: 'webapp-{{cluster}}'
    annotations:
      argocd.argoproj.io/sync-wave: '{{ring}}'
```

Sync waves execute in order: wave 1 first, then wave 2, then wave 3. Combined with manual sync gates, this creates a natural ring progression.

### Rollback with ApplicationSets

Rolling back a ring is a Git revert:

```bash
# Ring 1 failed — revert the commit that promoted it
git revert HEAD
git push

# ArgoCD detects the change and syncs Ring 1 back to v2.0.0
# Rings 2 and 3 were never promoted — no action needed
```

This is the power of GitOps: your rollback is a version-controlled, auditable operation.

---

## Observability Across Regions

### Cross-Region Metrics Comparison

During a ring deployment, you need to compare metrics between regions running different versions:

```
Dashboard: Release v2.1.0 Ring Deployment

                Ring 1 (v2.1.0)    Ring 2 (v2.0.0)    Ring 3 (v2.0.0)
                ap-south-1         eu-west-1           us-east-1
─────────────────────────────────────────────────────────────────────
Error Rate      0.3%               0.2%                0.2%
P99 Latency     145ms              120ms               130ms
CPU Usage       42%                38%                 40%
Memory          68%                65%                 64%
QPS             12,400             45,200              52,100
─────────────────────────────────────────────────────────────────────
Status          ⚠ Watch            ✓ Baseline          ✓ Baseline
```

Key metrics to compare:
- **Error rate delta**: Ring 1 vs Ring 2+3 baseline
- **Latency percentiles**: P50, P95, P99 comparison
- **Resource consumption**: Memory/CPU trends (catching leaks early)
- **Business metrics**: Conversion rate, transaction success rate per region

### Automated Ring Promotion Gates

Combine ArgoCD ApplicationSets with automated validation:

```yaml
# promotion-gate.yaml (pseudo-code for automation)
rings:
  ring-1:
    clusters: [ap-south-1]
    validation:
      - type: prometheus
        query: "error_rate{region='ap-south-1'} < 0.01"
        duration: 4h
      - type: prometheus
        query: "p99_latency{region='ap-south-1'} < 200"
        duration: 4h
    on_success: promote ring-2
    on_failure: rollback ring-1

  ring-2:
    clusters: [eu-west-1]
    validation:
      - type: prometheus
        query: "error_rate{region='eu-west-1'} < 0.01"
        duration: 2h
    on_success: promote ring-3
    on_failure: rollback ring-1, ring-2

  ring-3:
    clusters: [us-east-1]
    validation:
      - type: manual_approval
        approvers: [release-team]
```

---

## Multi-Cluster Deployment Strategies Comparison

| Strategy | Complexity | Blast Radius Control | Rollback Speed | Best For |
|----------|-----------|---------------------|----------------|----------|
| **Simultaneous** | Low | None (all at once) | Slow (rollback everywhere) | Non-critical services |
| **Sequential** | Medium | Per-region | Fast (stop propagation) | Most services |
| **Ring deployment** | High | Per-ring (grouped regions) | Fast (rollback ring) | Critical services |
| **Canary region + blast** | Medium | One region first, then all | Medium | Moderate-risk services |

---

## Did You Know?

1. **Google deploys to a single "canary cell" and waits 24 hours before any wider rollout**. Their deployment system, called Borg (the predecessor to Kubernetes), uses a concept of "cells" — isolated clusters in different geographies. A new version is deployed to the smallest cell first, bakes for a full day/night cycle to catch time-dependent bugs, and only then propagates to larger cells. Most Google service deployments take 3-5 days from first deployment to full global rollout.

2. **Microsoft Azure uses five rings for all Azure service deployments**: Ring 0 is internal dogfooding (Microsoft employees), Ring 1 is a single scale unit, Ring 2 is a full region, Ring 3 is a set of regions, and Ring 4 is global. A typical Azure deployment takes 5-7 days to reach Ring 4. This is why Azure outages are rarely global — a bad change is caught before it reaches all regions.

3. **The 2021 Facebook outage propagated globally in under 3 minutes** because their backbone configuration change was not deployed in rings. A single BGP configuration update was pushed to all routers simultaneously, withdrawing Facebook's IP address announcements from the entire internet. Had they used ring deployment for infrastructure changes — not just application code — the blast radius would have been one region instead of the entire planet.

4. **Spotify runs over 200 Kubernetes clusters across multiple regions** and uses a custom deployment orchestrator called "Backstage Deploy" that manages ring deployments across their fleet. Each microservice owner defines their own ring topology, and the orchestrator handles sequencing, validation gates, and automated rollback. The average deployment takes 4-6 hours from first ring to full rollout.

---

## War Story: The Time Zone Bug

A global fintech company deployed a new transaction processing service using ring deployments. Ring 1 (Singapore) deployed at 10 AM SGT and looked perfect for 8 hours. All metrics green. Error rate below 0.1%. The team promoted to Ring 2 (London) at 6 PM SGT / 10 AM GMT.

At 11:55 PM GMT, London's error rate spiked to 15%.

The bug: the new version had a date parsing issue with midnight rollover in UTC. Singapore's Ring 1 deployment happened at 10 AM SGT (2 AM UTC), and by the time midnight UTC came around, it had been running for 22 hours. But the Singapore metrics were aggregated over the full 22 hours, diluting the brief midnight spike to invisibility — a 15-minute spike of errors averaged over 22 hours barely registered.

London deployed at 10 AM GMT — midnight UTC was only 14 hours away, and the spike was more pronounced in the shorter metrics window.

**What they learned:**

1. **Ring 1 must bake through a full 24-hour cycle** — not just "8 hours of green." Time-dependent bugs need a full day/night cycle to surface.

2. **Monitor per-hour metrics, not just rolling averages** — the midnight spike was there in Singapore but invisible in the 22-hour average.

3. **Test across timezone boundaries explicitly** — their pre-deploy test suite ran at a single point in time and never tested the midnight rollover.

Their updated ring policy:

```
Ring 1: Deploy → Wait 24 hours minimum (full day/night cycle)
Ring 2: Deploy → Wait 12 hours minimum
Ring 3: Deploy → Wait 6 hours minimum
```

**Lesson**: Ring deployments protect you from bugs you can find in hours. For time-dependent bugs, you need bake time measured in days.

---

## Common Mistakes

| Mistake | Problem | Solution |
|---------|---------|----------|
| Deploying to all regions simultaneously | No blast radius isolation; global outage risk | Use ring deployments with region-based progression |
| Choosing the busiest region as canary | Maximizes blast radius if canary fails | Choose the smallest production region with representative traffic |
| Ring 1 bake time under 24 hours | Time-dependent bugs slip through | Minimum 24-hour bake for Ring 1 to cover full day/night cycle |
| No automated rollback per ring | Failed ring requires manual intervention at 3 AM | Automated promotion gates with metrics-driven rollback |
| Replicating data during schema transitions | v1 regions cannot read v2 data format | Pause replication or use backward-compatible schemas |
| No regional failover capacity | Failed region cannot shed traffic to healthy regions | Provision 130-150% capacity per region for failover headroom |
| Deploying infrastructure and app changes together | Doubles the blast radius per ring | Separate infrastructure changes from application changes |
| Identical ring timing regardless of service criticality | Over-cautious for low-risk services, under-cautious for high-risk | Tier your services: Tier 1 gets 5-day rollout, Tier 3 gets 1-day |

---

## Quiz: Check Your Understanding

### Question 1
Why is geography used as a blast radius boundary in ring deployments?

<details>
<summary>Show Answer</summary>

Geography provides natural isolation because:

1. **Infrastructure isolation**: Each region has its own clusters, databases, and networking. A failure in one region's infrastructure does not directly cascade to another.

2. **Traffic isolation**: Users are typically routed to their nearest region. A bad deployment in ap-south-1 only affects users routed to that region.

3. **Independent rollback**: You can roll back one region without affecting others, since each region's deployment is managed independently.

4. **Capacity absorption**: Healthy regions can absorb traffic from a failed region (if provisioned with headroom), providing graceful degradation rather than total outage.

In-cluster canary deployments control blast radius within a single region. Ring deployments control blast radius across regions. They are complementary strategies.

</details>

### Question 2
What are the three approaches to handling data replication during cross-region rollouts?

<details>
<summary>Show Answer</summary>

1. **Schema-compatible versions**: Both v1 and v2 read and write the same data format using the expand-contract pattern. v2 writes new format AND old format (backward compatible). Safe but constrains the types of schema changes per release.

2. **Region-isolated data**: Temporarily pause cross-region replication during the rollout. Each region operates on its own database. After all regions are on v2, resume replication. Requires the application to tolerate temporary data divergence.

3. **Feature-flagged data paths**: Deploy v2 everywhere with the new data path behind a feature flag (OFF). After all regions have v2 code, enable the flag globally. The new data path activates everywhere simultaneously, avoiding cross-version data conflicts.

The safest approach is feature-flagged data paths because it avoids any window where different versions handle different data formats simultaneously.

</details>

### Question 3
How does ArgoCD ApplicationSets enable ring deployments?

<details>
<summary>Show Answer</summary>

ApplicationSets generate ArgoCD Applications from a template, one per cluster. For ring deployments, you control which clusters get the new version through several mechanisms:

1. **Branch/tag per ring**: Each cluster's Application points to a different Git revision. Ring 1 points to the release branch, others point to the stable tag. Promote by changing the revision in the ApplicationSet configuration.

2. **Directory per ring**: Each ring has a Kustomize overlay with its own image version. Promote by updating the overlay for the next ring.

3. **Sync waves**: Ring numbers map to sync wave annotations. ArgoCD processes lower waves first, creating natural ordering.

All approaches result in Git commits for promotion and rollback, providing full auditability and reversibility through GitOps.

</details>

### Question 4
Why should Ring 1 bake for a minimum of 24 hours?

<details>
<summary>Show Answer</summary>

A 24-hour bake time is necessary to catch time-dependent bugs that only manifest at specific times:

- **Midnight rollover issues**: Date parsing bugs, timezone transitions, day-boundary calculations
- **Cron job interactions**: Daily batch jobs that interact with the new code
- **Traffic pattern coverage**: Morning peak, afternoon lull, evening peak, overnight batch processing
- **Cache expiry cycles**: Caches that refresh on daily cycles may expose issues when they expire
- **Certificate/token rotation**: Daily rotations that interact with new authentication code

Shorter bake times only validate the traffic patterns present during that window. A 4-hour bake during business hours misses overnight processing entirely. Only a full 24-hour cycle guarantees all time-dependent code paths are exercised.

</details>

### Question 5
What happens when Ring 2 fails in a ring deployment?

<details>
<summary>Show Answer</summary>

When Ring 2 fails:

1. **Halt propagation**: Ring 3 deployment is immediately blocked. Do not deploy to any further rings.

2. **Roll back Ring 2**: Revert Ring 2 clusters to the previous stable version. With GitOps/ApplicationSets, this is a Git revert of the Ring 2 promotion commit.

3. **Evaluate Ring 1**: Ring 1 was stable, but the Ring 2 failure might indicate a latent issue. Either roll back Ring 1 as well (safest) or investigate why Ring 1 passed but Ring 2 failed (different traffic patterns, scale, or data).

4. **Diagnose**: The bug may be scale-dependent (Ring 2 has more traffic), data-dependent (Ring 2 has different data patterns), or region-specific (Ring 2's infrastructure differs).

5. **Fix and restart**: After fixing the issue, restart the ring deployment from Ring 1 with the fix included.

The key principle: a ring failure blocks all downstream rings and triggers investigation of all upstream rings.

</details>

### Question 6
How would you handle a database migration that requires a new column across a globally distributed system?

<details>
<summary>Show Answer</summary>

Use the expand-contract pattern coordinated across all regions:

**Release N (schema migration only, no code change):**
1. Run `ALTER TABLE ADD COLUMN new_col DEFAULT NULL` in ALL regions simultaneously
2. This is backward-compatible — old code ignores the new column
3. Wait for replication to propagate the schema everywhere

**Release N+1 (ring deploy the new code):**
1. New code writes to both old and new columns (dual-write)
2. Deploy via rings: Ring 1 → Ring 2 → Ring 3
3. Old code in later rings ignores the new column; new code in earlier rings writes to both

**Release N+2 (after all regions on N+1):**
1. Backfill old rows: `UPDATE table SET new_col = computed_value WHERE new_col IS NULL`
2. New code reads from new column only

**Release N+3 (cleanup):**
1. Stop writing to old column
2. Drop old column (after verifying no code references it)

The critical principle: **deploy schema changes separately from code changes**, and ensure every schema change is backward-compatible.

</details>

---

## Hands-On Exercise: Ring Deployment Simulation with ApplicationSets

### Objective

Simulate a ring deployment across three "regions" using namespaces on a local kind cluster, deploying different versions to different rings and practicing manual promotion and rollback. This exercise demonstrates the ring deployment pattern; in production, you would automate this with ArgoCD ApplicationSets as described earlier in this module.

### Setup

```bash
# Create a multi-context kind cluster (simulating multiple regions)
cat <<'EOF' > /tmp/kind-config.yaml
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
nodes:
  - role: control-plane
  - role: worker
    labels:
      region: ap-south-1
      ring: "1"
  - role: worker
    labels:
      region: eu-west-1
      ring: "2"
  - role: worker
    labels:
      region: us-east-1
      ring: "3"
EOF

kind create cluster --name global-release-lab --config /tmp/kind-config.yaml
```

### Step 1: Create Namespaces for Each Ring

```bash
# Simulate regions with namespaces
kubectl create namespace ring-1-ap-south
kubectl create namespace ring-2-eu-west
kubectl create namespace ring-3-us-east
```

### Step 2: Deploy Ring 1 (Canary) with v2

Create the manifest file:

```bash
cat <<'EOF' > ring-1-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: webapp
  namespace: ring-1-ap-south
  labels:
    app: webapp
    ring: "1"
    region: ap-south-1
spec:
  replicas: 2
  selector:
    matchLabels:
      app: webapp
  template:
    metadata:
      labels:
        app: webapp
        version: v2
    spec:
      containers:
        - name: webapp
          image: hashicorp/http-echo:0.2.3
          args:
            - "-text=v2.1.0 - Ring 1 (ap-south-1) - NEW VERSION"
            - "-listen=:8080"
          ports:
            - containerPort: 8080
---
apiVersion: v1
kind: Service
metadata:
  name: webapp
  namespace: ring-1-ap-south
spec:
  selector:
    app: webapp
  ports:
    - port: 80
      targetPort: 8080
EOF
```

### Step 3: Deploy Rings 2 and 3 with v1 (Stable)

```bash
cat <<'EOF' > ring-2-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: webapp
  namespace: ring-2-eu-west
  labels:
    app: webapp
    ring: "2"
    region: eu-west-1
spec:
  replicas: 3
  selector:
    matchLabels:
      app: webapp
  template:
    metadata:
      labels:
        app: webapp
        version: v1
    spec:
      containers:
        - name: webapp
          image: hashicorp/http-echo:0.2.3
          args:
            - "-text=v2.0.0 - Ring 2 (eu-west-1) - STABLE"
            - "-listen=:8080"
          ports:
            - containerPort: 8080
---
apiVersion: v1
kind: Service
metadata:
  name: webapp
  namespace: ring-2-eu-west
spec:
  selector:
    app: webapp
  ports:
    - port: 80
      targetPort: 8080
EOF
```

```bash
cat <<'EOF' > ring-3-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: webapp
  namespace: ring-3-us-east
  labels:
    app: webapp
    ring: "3"
    region: us-east-1
spec:
  replicas: 4
  selector:
    matchLabels:
      app: webapp
  template:
    metadata:
      labels:
        app: webapp
        version: v1
    spec:
      containers:
        - name: webapp
          image: hashicorp/http-echo:0.2.3
          args:
            - "-text=v2.0.0 - Ring 3 (us-east-1) - STABLE"
            - "-listen=:8080"
          ports:
            - containerPort: 8080
---
apiVersion: v1
kind: Service
metadata:
  name: webapp
  namespace: ring-3-us-east
spec:
  selector:
    app: webapp
  ports:
    - port: 80
      targetPort: 8080
EOF
```

```bash
kubectl apply -f ring-1-deployment.yaml
kubectl apply -f ring-2-deployment.yaml
kubectl apply -f ring-3-deployment.yaml
```

### Step 4: Verify Ring State

```bash
# Check all rings
echo "=== Ring 1 (Canary - ap-south-1) ==="
kubectl -n ring-1-ap-south get pods -o wide --show-labels
kubectl run curl-r1 --rm -it --restart=Never --image=curlimages/curl -- \
  curl -s webapp.ring-1-ap-south.svc:80

echo ""
echo "=== Ring 2 (eu-west-1) ==="
kubectl -n ring-2-eu-west get pods -o wide --show-labels
kubectl run curl-r2 --rm -it --restart=Never --image=curlimages/curl -- \
  curl -s webapp.ring-2-eu-west.svc:80

echo ""
echo "=== Ring 3 (us-east-1) ==="
kubectl -n ring-3-us-east get pods -o wide --show-labels
kubectl run curl-r3 --rm -it --restart=Never --image=curlimages/curl -- \
  curl -s webapp.ring-3-us-east.svc:80
```

Expected output:
```
Ring 1: v2.1.0 - Ring 1 (ap-south-1) - NEW VERSION
Ring 2: v2.0.0 - Ring 2 (eu-west-1) - STABLE
Ring 3: v2.0.0 - Ring 3 (us-east-1) - STABLE
```

### Step 5: Simulate Ring Promotion (Promote Ring 2)

After validating Ring 1 is healthy, promote Ring 2:

```bash
# Update Ring 2 to v2
kubectl -n ring-2-eu-west patch deployment webapp --type='json' -p='[
  {"op":"replace","path":"/spec/template/spec/containers/0/args","value":["-text=v2.1.0 - Ring 2 (eu-west-1) - NEW VERSION","-listen=:8080"]}
]'

# Wait for rollout
kubectl -n ring-2-eu-west rollout status deployment webapp

# Verify
kubectl run curl-r2v2 --rm -it --restart=Never --image=curlimages/curl -- \
  curl -s webapp.ring-2-eu-west.svc:80
# Output: v2.1.0 - Ring 2 (eu-west-1) - NEW VERSION
```

### Step 6: Simulate Ring 2 Failure and Rollback

```bash
# Simulate failure — roll back Ring 2 to stable
kubectl -n ring-2-eu-west patch deployment webapp --type='json' -p='[
  {"op":"replace","path":"/spec/template/spec/containers/0/args","value":["-text=v2.0.0 - Ring 2 (eu-west-1) - STABLE (ROLLED BACK)","-listen=:8080"]}
]'

kubectl -n ring-2-eu-west rollout status deployment webapp

# Verify rollback
kubectl run curl-rb2 --rm -it --restart=Never --image=curlimages/curl -- \
  curl -s webapp.ring-2-eu-west.svc:80
# Output: v2.0.0 - Ring 2 (eu-west-1) - STABLE (ROLLED BACK)

# Ring 3 was never promoted — still on stable
kubectl run curl-rb3 --rm -it --restart=Never --image=curlimages/curl -- \
  curl -s webapp.ring-3-us-east.svc:80
# Output: v2.0.0 - Ring 3 (us-east-1) - STABLE
```

### Step 7: Verify Isolation

```bash
echo "=== Global Release State ==="
echo "Ring 1 (canary):"
kubectl run curl-iso1 --rm -it --restart=Never --image=curlimages/curl -- \
  curl -s webapp.ring-1-ap-south.svc:80
echo "Ring 2 (rolled back):"
kubectl run curl-iso2 --rm -it --restart=Never --image=curlimages/curl -- \
  curl -s webapp.ring-2-eu-west.svc:80
echo "Ring 3 (untouched):"
kubectl run curl-iso3 --rm -it --restart=Never --image=curlimages/curl -- \
  curl -s webapp.ring-3-us-east.svc:80
```

### Clean Up

```bash
kind delete cluster --name global-release-lab
```

### Success Criteria

You have completed this exercise when you can confirm:

- [ ] Three "regions" (namespaces) were running with different versions
- [ ] Ring 1 had the new version while Rings 2 and 3 had the stable version
- [ ] Promoting Ring 2 updated only that ring, not Ring 3
- [ ] Rolling back Ring 2 left Ring 3 completely untouched
- [ ] You can explain why ring deployments provide better blast radius control than single-cluster canaries
- [ ] You understand how ApplicationSets would automate this with Git-based promotion

---

## Key Takeaways

1. **Geography is a natural blast radius boundary** — region-based ring deployments limit the impact of bad releases to a fraction of your users
2. **Ring 1 must bake for 24+ hours** — time-dependent bugs need a full day/night cycle to surface
3. **Data replication during rollouts is the hardest problem** — use expand-contract, region isolation, or feature-flagged data paths
4. **ArgoCD ApplicationSets automate multi-cluster deployment** — Git commits drive ring promotion, providing full auditability
5. **Global load balancers enable instant regional failover** — drain a bad region and shift traffic to healthy ones in seconds
6. **Ring failures block all downstream rings** — never promote Ring 3 if Ring 2 is unstable
7. **Provision headroom for failover** — healthy regions must absorb traffic from failed regions

---

## Further Reading

**Documentation:**
- **ArgoCD ApplicationSets** — argo-cd.readthedocs.io/en/stable/operator-manual/applicationset/
- **AWS Global Accelerator** — docs.aws.amazon.com/global-accelerator/
- **Google Cloud Global Load Balancing** — cloud.google.com/load-balancing/docs

**Articles:**
- **"Safe Deployments at Scale"** — Azure DevOps Blog (ring deployment at Microsoft)
- **"Deployment at Scale"** — Google SRE Workbook, Chapter 8
- **"Understanding the Facebook Outage"** — Cloudflare Blog (2021 BGP analysis)

**Talks:**
- **"Multi-Cluster Management with ArgoCD"** — KubeCon (YouTube)
- **"Progressive Delivery Across Clusters"** — ArgoCon (YouTube)

---

## Summary

Multi-region release orchestration elevates blast radius control from "percentage of users in one cluster" to "percentage of users on the planet." Ring deployments use geography as a natural isolation boundary, deploying to canary regions first and progressively expanding to larger regions only after validation. Combined with ArgoCD ApplicationSets for Git-driven promotion, global load balancers for traffic management, and careful data replication strategies, ring deployments let you ship changes globally with confidence that a bad release will never become a global outage.

---

## Next Module

Continue to [Module 1.5: Release Engineering Metrics & Observability](../module-1.5-release-metrics/) to learn how to measure release performance with DORA metrics, build deployment-aware dashboards, and correlate releases with production health.

---

*"The best global deployment is one where each region gets a chance to say 'no' before the next one says 'yes'."* — Multi-region deployment wisdom
