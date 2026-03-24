# Module 1.1: Release Strategies & Progressive Delivery Fundamentals

> **Discipline Module** | Complexity: `[MEDIUM]` | Time: 2 hours

## Prerequisites

Before starting this module:
- **Required**: CI/CD Fundamentals — Understanding build pipelines, artifact promotion, and deployment automation
- **Required**: [Kubernetes Deployments](../../../k8s/ckad/README.md) — Working knowledge of Deployments, Services, and label selectors
- **Recommended**: Basic understanding of load balancers and HTTP routing
- **Recommended**: Familiarity with monitoring/observability concepts

---

## Why This Module Matters

It is 2:47 AM. Your phone is screaming. A deployment that went out six hours ago has been silently corrupting customer invoices. Every single user is affected. The rollback takes 40 minutes because nobody tested it. By the time you are back in bed, 12,000 invoices need manual correction, and the CEO wants a meeting at 8 AM.

This scenario plays out every week at companies around the world. Not because the code was terrible, but because the **release strategy** was terrible — or, more accurately, because there was no strategy at all.

Release engineering is the discipline of getting code from "it works on my machine" to "it works for every user" **safely, repeatedly, and reversibly**. The difference between teams that deploy with confidence and teams that deploy with dread comes down to one thing: how they manage the blast radius of change.

In this module, you will learn the fundamental release strategies — Blue/Green, Canary, Shadow, and more — and understand when each one is the right tool. You will also learn the art of progressive delivery: the idea that a release is not a binary event but a **graduated exposure** of change to increasingly larger audiences.

By the end, you will never again think of deployment as flipping a switch. You will think of it as turning a dial.

---

## The Problem with Big-Bang Releases

### Why "Deploy Everything at Once" Fails

Traditional releases work like this:

```
Developer commits → Build passes → Deploy to all servers → Hope for the best
```

This is the **big-bang release**. Everything goes live at once. If it works, great. If it does not, every user is affected simultaneously.

The math is brutal:

| Release Pattern | Blast Radius | Rollback Time | Risk |
|----------------|-------------|---------------|------|
| Big-bang deploy | 100% of users | Minutes to hours | Extreme |
| Blue/Green | 100% → 0% instantly | Seconds | Low |
| Canary | 1-5% → gradually | Seconds | Very Low |
| Shadow/Dark | 0% (mirrored only) | N/A | Near Zero |

The goal of release engineering is to move from the top of that table to the bottom.

### Blast Radius: The Core Concept

**Blast radius** is the percentage of users, requests, or systems affected if a release goes wrong.

Think of it like testing fireworks. You would not set off an untested firework in a crowded stadium. You would test it in an empty field first, then a small gathering, then a larger event, and only then at the stadium.

Progressive delivery applies the same logic to software:

```
┌──────────────────────────────────────────────────────────────┐
│                    Blast Radius Over Time                     │
│                                                              │
│  100% ─────────────────────────────────────────── ■ Full GA  │
│   75% ──────────────────────────────── ■ Region 2            │
│   50% ──────────────────── ■ Region 1                        │
│   25% ──────── ■ Beta users                                  │
│    5% ── ■ Internal                                          │
│    0% ■ Shadow                                               │
│     Time →                                                   │
└──────────────────────────────────────────────────────────────┘
```

Every step validates the release before expanding the blast radius.

---

## Release Strategy Deep Dive

### Blue/Green Deployments

Blue/Green is the simplest progressive strategy. You maintain two identical production environments:

- **Blue**: The current live environment
- **Green**: The new version, fully deployed but receiving no traffic

When you are confident Green is healthy, you switch all traffic from Blue to Green. If something goes wrong, you switch back.

```
                   ┌──────────────┐
                   │  Load        │
                   │  Balancer    │
                   └──────┬───────┘
                          │
              ┌───────────┴───────────┐
              │                       │
     ┌────────▼────────┐    ┌────────▼────────┐
     │   Blue (v1)     │    │  Green (v2)     │
     │   LIVE ✓        │    │  STANDBY        │
     │                 │    │                 │
     │  Pod Pod Pod    │    │  Pod Pod Pod    │
     └─────────────────┘    └─────────────────┘
```

**After cutover:**

```
                   ┌──────────────┐
                   │  Load        │
                   │  Balancer    │
                   └──────┬───────┘
                          │
              ┌───────────┴───────────┐
              │                       │
     ┌────────▼────────┐    ┌────────▼────────┐
     │   Blue (v1)     │    │  Green (v2)     │
     │   STANDBY       │    │  LIVE ✓         │
     │                 │    │                 │
     │  Pod Pod Pod    │    │  Pod Pod Pod    │
     └─────────────────┘    └─────────────────┘
```

**In Kubernetes**, Blue/Green is achieved with label selectors on Services:

```yaml
# Service pointing to Blue (v1)
apiVersion: v1
kind: Service
metadata:
  name: my-app
spec:
  selector:
    app: my-app
    version: blue    # ← Change this to "green" for cutover
  ports:
    - port: 80
      targetPort: 8080
```

**Advantages:**
- Instant rollback (just switch the selector back)
- Full environment validation before cutover
- Zero downtime if done correctly

**Disadvantages:**
- Requires double the infrastructure (temporarily)
- All-or-nothing traffic switch (no gradual rollout)
- Database migrations are tricky (both versions must work with the schema)

**When to use:**
- Critical services where instant rollback is essential
- When you need full integration testing before going live
- Services with simple state management

### Canary Deployments

Named after the canaries coal miners used to detect toxic gases, a canary deployment sends a small percentage of traffic to the new version first.

```
                   ┌──────────────┐
                   │  Load        │
                   │  Balancer    │
                   └──────┬───────┘
                          │
              ┌───────────┴───────────┐
              │ 95%                5%  │
     ┌────────▼────────┐    ┌────────▼────────┐
     │  Stable (v1)    │    │  Canary (v2)    │
     │                 │    │                 │
     │  Pod Pod Pod    │    │  Pod            │
     │  Pod Pod Pod    │    │                 │
     └─────────────────┘    └─────────────────┘
```

If the canary is healthy (low error rates, acceptable latency), traffic gradually increases:

```
5% → 10% → 25% → 50% → 100%
```

If the canary shows problems, it gets killed — and only 5% of users were ever affected.

**Advantages:**
- Minimal blast radius
- Real production traffic validation
- Automated promotion/rollback possible
- Gradual confidence building

**Disadvantages:**
- More complex to set up
- Requires traffic splitting capability
- Metrics analysis needed to determine health
- Session affinity can complicate things

**When to use:**
- High-traffic services where even brief outages are costly
- When you want metrics-driven deployment decisions
- Services where user behavior validation matters

### Shadow (Dark Launch) Deployments

Shadow deployments mirror production traffic to the new version **without serving responses to users**. The new version processes real requests, but its responses are discarded.

```
                   ┌──────────────┐
         Request → │  Load        │ → Response from v1 only
                   │  Balancer    │
                   └──────┬───────┘
                          │
              ┌───────────┴───────────┐
              │ serves              mirrors │
     ┌────────▼────────┐    ┌────────▼────────┐
     │  Production(v1) │    │  Shadow (v2)    │
     │  Serves users   │    │  Processes but  │
     │                 │    │  discards output│
     └─────────────────┘    └─────────────────┘
```

**Advantages:**
- Zero user impact — users never see v2 responses
- Tests with real production load patterns
- Validates performance under actual traffic
- Great for data pipeline or ML model changes

**Disadvantages:**
- Cannot test user-facing changes (UI differences)
- Write operations are dangerous (double-writes)
- Requires infrastructure to mirror and discard
- Does not validate client-side behavior

**When to use:**
- Backend services with no side effects on reads
- Performance validation before launch
- ML model comparisons (A/B testing the model, not the UX)
- Database query optimization validation

### Rolling Updates

Kubernetes' default strategy. Pods are replaced one at a time (or in batches):

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-app
spec:
  replicas: 6
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1        # Allow 1 extra pod during update
      maxUnavailable: 0   # Always keep all pods available
```

**Update sequence:**

```
Step 1: [v1] [v1] [v1] [v1] [v1] [v1] [v2]    ← 1 new pod added
Step 2: [v1] [v1] [v1] [v1] [v1] [v2] [v2]    ← 1 old pod removed, 1 new added
Step 3: [v1] [v1] [v1] [v1] [v2] [v2] [v2]
Step 4: [v1] [v1] [v1] [v2] [v2] [v2] [v2]
Step 5: [v1] [v1] [v2] [v2] [v2] [v2] [v2]
Step 6: [v1] [v2] [v2] [v2] [v2] [v2] [v2]
Step 7: [v2] [v2] [v2] [v2] [v2] [v2]          ← Complete
```

**Advantages:**
- Built into Kubernetes (zero extra tooling)
- Simple to configure
- Gradual replacement

**Disadvantages:**
- No fine-grained traffic control (traffic split depends on pod count)
- Mixed versions serve traffic simultaneously
- Rollback is another rolling update (not instant)

---

## Feature Flags vs Release Toggles

### Decoupling Deployment from Release

Here is a critical insight: **deployment and release are not the same thing**.

- **Deployment**: Putting code on servers
- **Release**: Making a feature available to users

Feature flags let you deploy code without releasing it:

```python
# Feature is deployed but not released
if feature_flags.is_enabled("new-checkout-flow", user=current_user):
    return new_checkout_flow(cart)
else:
    return old_checkout_flow(cart)
```

This separation is powerful because it means:
- You can deploy any time (even Friday afternoon)
- You can release to specific users first
- You can kill a feature without redeploying
- You can A/B test without infrastructure changes

### Types of Feature Flags

| Type | Lifespan | Purpose | Example |
|------|----------|---------|---------|
| **Release toggle** | Days/weeks | Gate incomplete features | New checkout flow |
| **Experiment toggle** | Weeks/months | A/B testing | Button color test |
| **Ops toggle** | Permanent | Circuit breakers | Disable recommendations |
| **Permission toggle** | Permanent | Entitlements | Premium features |

### The Kill Switch Pattern

Every critical feature should have a kill switch — an ops toggle that immediately disables it:

```yaml
# Feature flag configuration
new_payment_processor:
  enabled: true
  kill_switch: true           # Can be disabled instantly
  rollout_percentage: 25      # Only 25% of users see it
  excluded_regions:
    - ap-southeast-1          # Not yet tested in APAC
```

If the new payment processor starts failing, one API call disables it:

```bash
curl -X PUT https://flags.internal/api/flags/new_payment_processor \
  -d '{"enabled": false}'
```

No redeployment. No rollback. Instant recovery.

---

## Database Migrations During Zero-Downtime Releases

### The Hardest Problem in Release Engineering

Code is stateless and replaceable. Databases are not. This makes database schema changes the most dangerous part of any release.

The fundamental problem: during a rolling deployment, **both old and new versions of your application run simultaneously**. Both must work with the same database schema.

### The Expand-Contract Pattern

Never make breaking schema changes in a single release. Use expand-contract (also called parallel change):

**Phase 1 — Expand (Release N):**
Add new columns/tables, keep old ones working.

```sql
-- Add new column, allow NULL (backward compatible)
ALTER TABLE users ADD COLUMN email_verified BOOLEAN DEFAULT NULL;
```

Old code ignores the new column. New code starts writing to it.

**Phase 2 — Migrate (Release N+1):**
Backfill data and start reading from new column.

```sql
-- Backfill existing rows
UPDATE users SET email_verified = false WHERE email_verified IS NULL;
```

**Phase 3 — Contract (Release N+2):**
Remove old columns/code once fully migrated.

```sql
-- Now safe to add NOT NULL constraint
ALTER TABLE users ALTER COLUMN email_verified SET NOT NULL;

-- Later: remove old column if it was replaced
-- ALTER TABLE users DROP COLUMN old_email_status;
```

### Migration Anti-Patterns

| Anti-Pattern | Why It Breaks | Safe Alternative |
|-------------|---------------|------------------|
| `DROP COLUMN` in same release | Old pods still reading it | Expand-contract over 2+ releases |
| `RENAME COLUMN` | Old code uses old name | Add new column, backfill, drop old |
| `ALTER TYPE` (e.g., int→bigint) | Can lock table for hours | Create new column, dual-write, swap |
| Non-reversible migration | Cannot roll back release | Always write reversible migrations |
| Big table migration in one tx | Locks table, kills production | Batch in small chunks |

---

## MTTR vs MTBF: Two Philosophies of Reliability

### The Old Way: Maximize MTBF

**MTBF** (Mean Time Between Failures) asks: "How do we prevent failures?"

Organizations optimizing for MTBF:
- Have heavy change approval processes
- Deploy infrequently (monthly or quarterly)
- Test exhaustively before release
- Avoid changes to "stable" systems

The problem: failures still happen. And when they do, recovery is slow because the team has no practice at it.

### The Modern Way: Minimize MTTR

**MTTR** (Mean Time to Recovery) asks: "How fast can we recover from failure?"

Organizations optimizing for MTTR:
- Deploy frequently (many times per day)
- Invest in rollback mechanisms
- Practice incident response
- Accept that failures will happen

```
MTBF-Focused:
──────────────────────────────X──────(long recovery)──────────────────
  Long time between failures         Slow, unpracticed recovery

MTTR-Focused:
────X──(quick fix)──────X──(quick fix)──────X──(quick fix)──────
  More frequent failures    But fast, practiced recoveries
```

The key insight from the DORA research (which we will explore in Module 1.5): **high-performing teams optimize for MTTR, not MTBF**. They deploy more often, fail more gracefully, and recover faster.

### How Release Strategies Enable Low MTTR

| Strategy | MTTR Contribution |
|----------|-------------------|
| Blue/Green | Instant rollback by switching traffic |
| Canary | Auto-rollback before most users are affected |
| Feature flags | Disable features without redeployment |
| Shadow | Catch problems before any user is affected |

---

## Choosing the Right Strategy

### Decision Matrix

| Factor | Blue/Green | Canary | Shadow | Rolling |
|--------|-----------|--------|--------|---------|
| **Complexity** | Low | Medium | High | Very Low |
| **Blast radius** | 0→100% | Gradual | 0% | Gradual |
| **Rollback speed** | Instant | Fast | N/A | Slow |
| **Infra cost** | 2x (temporary) | +10-20% | 2x | +0-10% |
| **Traffic control** | Binary | Fine-grained | Mirrored | None |
| **DB-safe** | Needs expand-contract | Needs expand-contract | Read-only safe | Needs expand-contract |
| **Best for** | Critical services | High-traffic APIs | Backend/ML | Simple services |

### Combining Strategies

Real-world release engineering combines multiple strategies:

```
1. Shadow deploy → Validate performance with real traffic
2. Canary to 1% → Watch metrics for 30 minutes
3. Canary to 10% → Watch metrics for 1 hour
4. Blue/Green the rest → Full cutover with instant rollback
5. Feature flag → Gradually enable new UI for users
```

This is **progressive delivery** in practice: layering strategies to minimize risk at every stage.

---

## Did You Know?

1. **Facebook deploys code to production thousands of times per day**, but features reach users over days or weeks through a sophisticated feature flag system called Gatekeeper. The average feature is tested on Facebook employees first, then 1% of users, then gradually ramped up. A deployment is never a release.

2. **The term "canary deployment" comes from the practice of taking canaries into coal mines**. The birds were more sensitive to carbon monoxide than humans, so if the canary stopped singing, miners knew to evacuate. In software, your canary pods are the first to "stop singing" (show errors), warning you before the toxic change reaches everyone.

3. **LinkedIn pioneered the concept of "Dark Launches" in 2009** when they needed to test a completely rewritten backend. They mirrored 100% of production read traffic to the new system for weeks, comparing responses without users ever knowing. By the time they switched over, they had months of production validation — and the cutover was uneventful.

4. **Blue/Green deployments were first described by Daniel North and Jez Humble in 2005**, and the technique predates Kubernetes by a decade. The original implementation used DNS switching between two physical server clusters. In Kubernetes, the same concept is achieved with a single label selector change — what used to take hours now takes milliseconds.

---

## War Story: The Migration That Ate Production

A team was migrating from a monolith to microservices. They had been developing the new services for months and were ready to switch.

Their plan: big-bang cutover on a Saturday night. Move all traffic from the monolith to the new services at once.

What happened:

1. **7:00 PM** — Cut traffic to new services. Response times look good.
2. **7:15 PM** — Connection pool exhaustion. The new services open 10x more DB connections than the monolith.
3. **7:30 PM** — Roll back. But the rollback script has a bug. Monolith cannot start because a database migration already ran.
4. **8:00 PM** — Emergency manual fix of the migration. Monolith is back but running on the new schema with patched queries.
5. **11:00 PM** — All data integrity issues identified and corrected.
6. **3:00 AM** — Post-incident meeting. Everyone is exhausted and demoralized.

What they should have done:

1. **Shadow deploy** the new services for two weeks to find the connection pool issue
2. **Canary** at 1% to validate real user traffic patterns
3. **Expand-contract** the database to support both services simultaneously
4. **Feature flags** to gradually shift functionality, not traffic

They eventually did exactly this over the next three months, and the second attempt was anticlimactic — which is the goal.

**Lesson**: The measure of a great release is how boring it is.

---

## Common Mistakes

| Mistake | Problem | Solution |
|---------|---------|----------|
| No rollback plan | "We'll figure it out if something goes wrong" | Test rollback before every release; automate it |
| Canary without metrics | Deploying to 5% but not measuring anything | Define success metrics before deployment starts |
| Blue/Green with DB migrations | Both environments need the same schema | Use expand-contract pattern over multiple releases |
| Feature flags as permanent code | Codebase fills with dead branches | Set expiry dates; track flag lifecycle; clean up quarterly |
| Testing only in staging | Staging never matches production | Use shadow deployments for production-traffic validation |
| Deploying on Fridays | Nobody monitors over the weekend | Deploy early in the week, or invest in proper on-call and automation |
| Skipping smoke tests after cutover | Assuming traffic switch means success | Automated post-deployment health checks are non-negotiable |
| Ignoring session state | Users mid-transaction get errors during switch | Implement graceful connection draining and sticky sessions |

---

## Quiz: Check Your Understanding

### Question 1
What is the fundamental difference between a deployment and a release?

<details>
<summary>Show Answer</summary>

A **deployment** is putting code onto servers — making it physically available to run. A **release** is making a feature available to users.

Feature flags decouple these: you can deploy code to production at any time without releasing the feature. This lets you deploy continuously while controlling when and how users experience changes. This separation is the foundation of progressive delivery.

</details>

### Question 2
When would you choose a Shadow deployment over a Canary deployment?

<details>
<summary>Show Answer</summary>

Choose **Shadow** when:
- You need to validate performance under real traffic without any user risk
- The change is backend-only (no user-facing differences)
- The service only processes reads (writes would cause duplication)
- You are validating ML models, database query optimizations, or architectural changes

Choose **Canary** when:
- You need to validate user-facing changes
- You want real user feedback (error rates, conversion)
- The service involves write operations
- You need to gradually build confidence before full rollout

Shadow has zero user impact but cannot validate user-facing behavior. Canary has minimal user impact and validates everything.

</details>

### Question 3
Why is the expand-contract pattern necessary for database migrations during zero-downtime releases?

<details>
<summary>Show Answer</summary>

During a rolling deployment (or Blue/Green), both old and new application versions run simultaneously and share the same database. If you make a breaking schema change (drop a column, rename a table), the old version immediately crashes.

The expand-contract pattern solves this by splitting the migration into three phases:
1. **Expand**: Add new structures alongside old ones (backward compatible)
2. **Migrate**: Backfill data, update code to use new structures
3. **Contract**: Remove old structures once fully migrated

This ensures both versions work with the schema at every point during the deployment.

</details>

### Question 4
Why do high-performing teams optimize for MTTR instead of MTBF?

<details>
<summary>Show Answer</summary>

Optimizing for **MTBF** (preventing failures) leads to infrequent, high-risk deployments with slow, unpracticed recovery. Failures still happen despite heavy process, and the team is ill-prepared when they do.

Optimizing for **MTTR** (fast recovery) means:
- Deploying frequently with small changes (easier to diagnose)
- Investing in rollback mechanisms (faster recovery)
- Practicing incident response regularly (muscle memory)
- Accepting failures as normal and focusing on limiting their impact

The DORA research shows that high performers deploy more often AND have lower failure rates — because small, frequent releases are inherently less risky than large, infrequent ones.

</details>

### Question 5
What is the kill switch pattern and when should you use it?

<details>
<summary>Show Answer</summary>

A **kill switch** is an operational feature flag that can instantly disable a feature without redeployment. It is an ops toggle with a permanent lifespan.

Use it for:
- Any new feature that touches critical user flows (payments, authentication)
- Features that depend on external services (can disable if the external service fails)
- Features with uncertain performance characteristics
- Any feature where the cost of failure is high

Example: A new payment processor can be disabled with a single API call if it starts failing, reverting to the old processor immediately without a deployment or rollback.

</details>

### Question 6
A team does Blue/Green deployments but their rollbacks still take 30 minutes. What are they likely doing wrong?

<details>
<summary>Show Answer</summary>

Common causes of slow Blue/Green rollbacks:

1. **Database migrations are not backward-compatible**: They ran a destructive migration (DROP COLUMN, RENAME) in the same release, so switching back to Blue fails because Blue cannot work with the new schema.

2. **They are redeploying instead of switching**: True Blue/Green rollback is a traffic switch (seconds), not a redeployment. If they are rebuilding the old version, they have lost the key benefit.

3. **Cache or state invalidation**: The Green deployment warmed caches or changed shared state that Blue depends on.

4. **DNS-based switching with high TTLs**: If they are using DNS to switch traffic and the TTL is 30 minutes, clients keep hitting Green until the TTL expires. Use load balancer or service selector switching instead.

5. **No pre-validated Blue environment**: They tore down Blue after cutover, so rollback requires re-provisioning.

The fix: Keep Blue running and healthy, use instant switching mechanisms (K8s Service selectors, LB rules), and never run destructive database migrations in a single release.

</details>

---

## Hands-On Exercise: Manual Blue/Green Deployment with Kubernetes

### Objective

Deploy a web application using the Blue/Green strategy in Kubernetes, perform a zero-downtime cutover, and practice instant rollback.

### Setup

Create a local Kubernetes cluster:

```bash
kind create cluster --name release-lab
```

### Step 1: Deploy the Blue Version

```yaml
# blue-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: webapp-blue
  labels:
    app: webapp
    version: blue
spec:
  replicas: 3
  selector:
    matchLabels:
      app: webapp
      version: blue
  template:
    metadata:
      labels:
        app: webapp
        version: blue
    spec:
      containers:
        - name: webapp
          image: hashicorp/http-echo:0.2.3
          args:
            - "-text=Hello from BLUE (v1)"
            - "-listen=:8080"
          ports:
            - containerPort: 8080
          readinessProbe:
            httpGet:
              path: /
              port: 8080
            initialDelaySeconds: 2
            periodSeconds: 3
```

```yaml
# webapp-service.yaml
apiVersion: v1
kind: Service
metadata:
  name: webapp
spec:
  type: NodePort
  selector:
    app: webapp
    version: blue       # ← Currently pointing to Blue
  ports:
    - port: 80
      targetPort: 8080
      nodePort: 30080
```

Apply both:

```bash
k apply -f blue-deployment.yaml
k apply -f webapp-service.yaml
```

Verify Blue is live:

```bash
k get pods -l version=blue
# Should show 3 pods Running

# Test the service
k port-forward svc/webapp 8080:80 &
curl http://localhost:8080
# Output: Hello from BLUE (v1)
```

### Step 2: Deploy the Green Version (No Traffic Yet)

```yaml
# green-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: webapp-green
  labels:
    app: webapp
    version: green
spec:
  replicas: 3
  selector:
    matchLabels:
      app: webapp
      version: green
  template:
    metadata:
      labels:
        app: webapp
        version: green
    spec:
      containers:
        - name: webapp
          image: hashicorp/http-echo:0.2.3
          args:
            - "-text=Hello from GREEN (v2)"
            - "-listen=:8080"
          ports:
            - containerPort: 8080
          readinessProbe:
            httpGet:
              path: /
              port: 8080
            initialDelaySeconds: 2
            periodSeconds: 3
```

```bash
k apply -f green-deployment.yaml
k get pods -l version=green
# Should show 3 pods Running — but no traffic is going to them yet
```

Verify Green works by directly port-forwarding to one of its pods:

```bash
# Find a green pod name
GREEN_POD=$(k get pods -l version=green -o jsonpath='{.items[0].metadata.name}')
k port-forward $GREEN_POD 8081:8080 &
curl http://localhost:8081
# Output: Hello from GREEN (v2)
```

### Step 3: Perform the Cutover

Switch the Service selector from Blue to Green:

```bash
k patch service webapp -p '{"spec":{"selector":{"version":"green"}}}'
```

Verify the switch:

```bash
curl http://localhost:8080
# Output: Hello from GREEN (v2)
```

That is it. One command. Instant cutover.

### Step 4: Practice Instant Rollback

Simulate a problem with Green and roll back:

```bash
# Rollback to Blue
k patch service webapp -p '{"spec":{"selector":{"version":"blue"}}}'

curl http://localhost:8080
# Output: Hello from BLUE (v1)
```

### Step 5: Verify with a Traffic Loop

Run a continuous traffic loop to prove zero downtime during switching:

```bash
# In one terminal — continuous requests
while true; do
  RESPONSE=$(curl -s http://localhost:8080)
  echo "$(date +%H:%M:%S) - $RESPONSE"
  sleep 0.5
done
```

In another terminal, perform the cutover:

```bash
k patch service webapp -p '{"spec":{"selector":{"version":"green"}}}'
```

Watch the first terminal. You should see the response change from Blue to Green **with zero failed requests**.

### Step 6: Clean Up

```bash
kill %1 %2 2>/dev/null    # Stop port-forwards
kind delete cluster --name release-lab
```

### Success Criteria

You have completed this exercise when you can confirm:

- [ ] Both Blue and Green deployments ran simultaneously with 3 pods each
- [ ] The Service selector controlled which version received traffic
- [ ] Cutover from Blue to Green happened with a single `kubectl patch` command
- [ ] Rollback from Green to Blue was equally instant
- [ ] The traffic loop showed zero failed requests during the switch
- [ ] You understand that the Blue pods remained running as a rollback target

---

## Key Takeaways

1. **Deployment is not release** — Feature flags and progressive delivery decouple putting code on servers from exposing it to users
2. **Blast radius is everything** — Every release strategy is ultimately about controlling how many users are affected if something goes wrong
3. **Blue/Green gives instant rollback** — Keep the old version running and switch traffic with a selector change
4. **Canary gives gradual confidence** — Start with 1% and increase only when metrics confirm health
5. **Shadow validates without risk** — Mirror production traffic to test performance before any user is exposed
6. **Database migrations need expand-contract** — Never make breaking schema changes in a single release
7. **Optimize for MTTR, not MTBF** — Fast recovery beats rare failure every time

---

## Further Reading

**Books:**
- **"Continuous Delivery"** — Jez Humble and David Farley (the foundational text on release engineering)
- **"Accelerate"** — Nicole Forsgren, Jez Humble, Gene Kim (DORA research on deployment performance)
- **"Release It!"** — Michael Nygard (patterns for production-ready software)

**Articles:**
- **"Progressive Delivery"** — James Governor, RedMonk (redmonk.com)
- **"BlueGreenDeployment"** — Martin Fowler (martinfowler.com)
- **"Feature Toggles"** — Pete Hodgson, Martin Fowler (martinfowler.com/articles/feature-toggles.html)

**Talks:**
- **"Progressive Delivery"** — James Governor (YouTube)
- **"Testing in Production"** — Charity Majors (YouTube)

---

## Summary

Release engineering is the discipline of getting changes to users safely and reversibly. The fundamental strategies — Blue/Green, Canary, Shadow, and Rolling — each control blast radius differently. Progressive delivery layers these strategies together, treating a release as a gradual dial-turn rather than a binary switch. Combined with feature flags and proper database migration patterns, these techniques let you deploy with confidence instead of dread.

The measure of great release engineering is how boring your deployments become.

---

## Next Module

Continue to [Module 1.2: Advanced Canary Deployments with Argo Rollouts](module-1.2-argo-rollouts.md) to learn how to automate canary deployments with metrics-driven promotion and rollback.

---

*"If deploying your code makes you nervous, you are not deploying often enough."* — Traditional release engineering wisdom
