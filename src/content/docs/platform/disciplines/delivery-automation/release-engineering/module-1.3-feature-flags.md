---
title: "Module 1.3: Feature Management at Scale"
slug: platform/disciplines/delivery-automation/release-engineering/module-1.3-feature-flags
sidebar:
  order: 4
---
> **Discipline Module** | Complexity: `[MEDIUM]` | Time: 2.5 hours

## Prerequisites

Before starting this module:
- **Required**: [Module 1.1: Release Strategies](../module-1.1-release-strategies/) — Understanding of progressive delivery, deployment vs release separation
- **Required**: Kubernetes Deployments and Services — Ability to deploy and expose applications
- **Recommended**: Basic understanding of trunk-based development and CI/CD pipelines
- **Recommended**: Familiarity with REST APIs and environment variables

---

## What You'll Be Able to Do

After completing this module, you will be able to:

- **Design a feature flag architecture that decouples deployment from release across microservices**
- **Implement feature flag management with gradual rollouts, user targeting, and kill switches**
- **Build feature flag lifecycle processes that prevent flag debt and stale configurations**
- **Evaluate feature flag platforms — LaunchDarkly, Flagsmith, OpenFeature — against your operational requirements**

## Why This Module Matters

On March 15, 2024, a SaaS company pushed a new recommendation engine to production. The recommendation engine was brilliant — 40% better click-through rates in testing. But in production, it hammered a downstream service that nobody had load-tested, bringing down the entire product catalog for 90 minutes during peak shopping hours.

The postmortem identified the root cause quickly. The fix was also obvious. But rolling back took 22 minutes: rebuilding the previous Docker image, running the pipeline, waiting for health checks. Twenty-two minutes of a dark product catalog because the only way to disable a feature was to redeploy the entire application.

Had they wrapped the recommendation engine in a feature flag, recovery would have taken 3 seconds: one API call, one config change, one toggle. No redeployment. No pipeline. No waiting.

**Feature flags are not a nice-to-have. They are a safety mechanism.** They let you separate the act of deploying code from the act of exposing it to users. They let you turn features on and off without touching your infrastructure. They let you test in production safely, roll out gradually to specific user segments, and kill anything instantly when it misbehaves.

This module teaches you how to build a feature management system that scales from a single flag to thousands, without drowning in technical debt.

---

## Feature Flags: First Principles

### What a Feature Flag Actually Is

At its simplest, a feature flag is an if-statement controlled by external configuration:

```python
# Without feature flag
def get_recommendations(user):
    return new_ml_recommendations(user)

# With feature flag
def get_recommendations(user):
    if feature_flags.is_enabled("new-recommendations", user=user):
        return new_ml_recommendations(user)
    else:
        return legacy_recommendations(user)
```

The key insight: the flag's value is not hardcoded. It comes from a configuration service that can be changed at runtime without redeploying:

```mermaid
flowchart LR
    App[Application<br/>if enabled?] -->|Query| FS[Flag Service<br/>new-reco: true<br/>dark-mode: false]
    UI[Admin UI<br/>Toggle on/off] -->|Update| FS
```

### The Four Types of Feature Flags

Not all flags are created equal. Understanding the types prevents the most common mistake: treating temporary flags as permanent code.

| Type | Lifespan | Who Controls It | Purpose | Example |
|------|----------|----------------|---------|---------|
| **Release toggle** | Days to weeks | Engineering | Gate incomplete features for trunk-based dev | `new-checkout-flow` |
| **Experiment toggle** | Weeks to months | Product/Data | A/B testing, measure user behavior | `button-color-test` |
| **Ops toggle** | Long-lived | Operations | Circuit breakers, kill switches, load shedding | `disable-recommendations` |
| **Permission toggle** | Permanent | Business | Entitlements, premium features, beta access | `premium-analytics` |

The critical difference is **lifespan**. Release toggles should be removed within weeks. If a "temporary" flag is still in your code six months later, it has become technical debt.

### Flag Lifecycle

Every release toggle should follow this lifecycle:

```mermaid
flowchart LR
    A[Create Flag<br/>Day 1] --> B[Test off<br/>Day 1-7]
    B --> C[Rollout % ramp<br/>Day 7-14]
    C --> D[GA 100%<br/>Day 14-21]
    D --> E[Remove Flag<br/>Day 21-28]
    
    style E stroke:#ff0000,stroke-width:2px,stroke-dasharray: 5 5
    noteE[THIS IS MANDATORY<br/>or the flag becomes debt] -.-> E
```

> **Stop and think**: What happens if an organization adopts feature flags but fails to enforce the "Remove Flag" phase of the lifecycle for its release toggles?

---

## Architecture of a Feature Flag System

### Evaluation Strategies

Feature flags can be evaluated in several ways:

**1. Simple Boolean:**
```json
{
  "new-checkout": {
    "enabled": true
  }
}
```

> **Pause and predict**: If you roll a feature out to 25% of your users using random probability instead of a sticky attribute, what will the user experience be as they navigate the site?

**2. Percentage Rollout:**
```json
{
  "new-checkout": {
    "enabled": true,
    "rollout_percentage": 25,
    "stickiness": "userId"
  }
}
```

The `stickiness` field is crucial. Without it, a user would randomly get the new checkout 25% of the time — sometimes seeing it, sometimes not. With stickiness on `userId`, the same user consistently sees the same experience (determined by hashing their user ID).

**3. User/Group Targeting:**
```json
{
  "new-checkout": {
    "enabled": true,
    "rules": [
      {
        "attribute": "email",
        "operator": "endsWith",
        "value": "@company.com",
        "variant": true
      },
      {
        "attribute": "country",
        "operator": "in",
        "value": ["US", "CA"],
        "rollout_percentage": 10,
        "variant": true
      }
    ],
    "default": false
  }
}
```

This configuration means: all company employees see the feature, 10% of US/Canadian users see it, nobody else does.

**4. Gradual Rollout with Kill Switch:**
```json
{
  "new-payment-processor": {
    "enabled": true,
    "kill_switch": true,
    "rollout_percentage": 5,
    "excluded_regions": ["ap-southeast-1"],
    "metrics_gate": {
      "metric": "payment_success_rate",
      "threshold": 0.995,
      "auto_disable_below": 0.99
    }
  }
}
```

### Client-Side vs Server-Side Evaluation

| Aspect | Server-Side | Client-Side |
|--------|-------------|-------------|
| **Where** | In your backend | In browser/mobile SDK |
| **Latency** | Near-zero (local cache) | Depends on network |
| **Security** | Rules hidden from users | Rules visible in payload |
| **Targeting** | Full context available | Limited to client context |
| **Use case** | API behavior, business logic | UI changes, frontend features |

**Best practice**: Use server-side evaluation for business logic and security-sensitive flags. Use client-side evaluation for UI experiments.

### Caching and Performance

A poorly implemented flag system adds latency to every request. The solution: local caching with background refresh.

```mermaid
flowchart TD
    subgraph App[Application]
        Cache[Local Cache]
        Eval[evaluate < 1ms]
        Dec[if enabled?]
        
        Cache --> Eval
        Eval --> Dec
    end
    
    FS[Flag Service<br/>Source of Truth] -->|refresh every 10s| Cache
```

The application caches all flag configurations locally. Evaluations are sub-millisecond (just reading from memory). The cache refreshes from the flag service every 10-30 seconds in the background. If the flag service goes down, the application continues using its cached values — graceful degradation.

---

## Feature Flag Platforms

### Unleash (Open Source)

Unleash is the most popular open-source feature flag platform. It runs on Kubernetes, stores configuration in PostgreSQL, and provides SDKs for every major language.

**Architecture:**

```mermaid
flowchart TD
    subgraph K8s[Kubernetes Cluster]
        API[Unleash API Server] --> DB[(PostgreSQL State)]
        UI[Unleash Admin UI] --> API
        
        App1[App Pod + SDK cached] -->|Polls| API
        App2[App Pod + SDK cached] -->|Polls| API
        App3[App Pod + SDK cached] -->|Polls| API
    end
    
    Devs[Developers] -->|Toggle flags| UI
```

**Key Unleash concepts:**

| Concept | Meaning |
|---------|---------|
| **Feature toggle** | The flag itself (enabled/disabled) |
| **Activation strategy** | How to evaluate (percentage, user ID, etc.) |
| **Environment** | Separate configs for dev/staging/prod |
| **Project** | Group flags by team or domain |
| **Variant** | Return different values (not just on/off) |

### OpenFeature (Standard)

OpenFeature is a CNCF project that provides a vendor-neutral API for feature flags. Instead of locking into Unleash or LaunchDarkly, you code against the OpenFeature interface and swap providers:

```python
from openfeature import api
from openfeature_unleash import UnleashProvider

# Configure the provider (swap this to change platforms)
api.set_provider(UnleashProvider(url="http://unleash:4242/api"))

# Evaluate a flag (same code regardless of provider)
client = api.get_client()
show_new_ui = client.get_boolean_value(
    "new-dashboard",
    default_value=False,
    evaluation_context={"userId": user.id, "country": user.country}
)
```

**Why OpenFeature matters:**
- No vendor lock-in — switch providers without changing application code
- Standard SDK interface across languages
- Growing ecosystem of providers (Unleash, LaunchDarkly, Flagd, CloudBees)
- CNCF backing ensures long-term viability

### Commercial Options

| Platform | Differentiator | Best For |
|----------|---------------|----------|
| **LaunchDarkly** | Most mature, real-time streaming | Enterprise, large scale |
| **Split.io** | Strong experimentation focus | Data-driven product teams |
| **Flagsmith** | Open-source with hosted option | Teams wanting open-source + support |
| **Harness FF** | Integrated with Harness CI/CD | Harness ecosystem users |

---

## Trunk-Based Development and Feature Flags

### Why Long-Lived Branches Are Dangerous

Traditional branching strategies create long-lived feature branches:

```mermaid
gitGraph
    commit
    branch feature-x
    commit
    checkout main
    commit
    commit
    checkout feature-x
    commit
    checkout main
    commit
    commit
    checkout feature-x
    commit
    checkout main
    merge feature-x type: REVERSE
```

After three weeks, the feature branch has diverged so far from main that merging is painful, risky, and often introduces bugs.

### Trunk-Based Development

With feature flags, everyone commits to main every day:

```mermaid
gitGraph
    commit id: "Initial"
    commit id: "Add flag (off)"
    commit id: "WIP feature 1"
    commit id: "WIP feature 2"
    commit id: "Enable flag Dev"
    commit id: "Enable flag 5% Prod"
    commit id: "Enable flag 100% Prod"
    commit id: "Remove flag"
```

Incomplete features are deployed but hidden behind flags:

```python
# This code is in main, deployed to production, but invisible to users
if feature_flags.is_enabled("new-search-engine"):
    results = new_search_engine.search(query)  # Work in progress
else:
    results = legacy_search.search(query)       # What users see
```

**Benefits:**
- No merge conflicts (everyone is on main)
- Code is continuously integrated (not just at merge time)
- Features can be tested in production behind flags
- No "big bang" integration risk
- Deployment and release are decoupled

### The Development Workflow

```
1. Developer creates flag "new-search" (disabled by default)
2. Developer commits search code behind flag to main
3. CI/CD deploys to production (flag is off, users see nothing)
4. Developer enables flag in dev/staging environments for testing
5. QA tests with flag enabled
6. Flag enabled for 5% of production users (percentage rollout)
7. Metrics look good → 25% → 50% → 100%
8. Flag is now 100% — schedule flag removal
9. Developer removes flag code and dead branch (tech debt cleanup)
```

---

## Technical Debt Prevention

### The Flag Graveyard Problem

Every team that adopts feature flags eventually faces this: hundreds of stale flags littering the codebase. Nobody knows if they are still needed. Nobody wants to remove them in case something breaks.

This is the **flag graveyard**, and it is the number one reason teams abandon feature flagging.

### Prevention Strategies

**1. Expiry Dates (Enforced)**

Every release toggle gets a mandatory expiry date:

```yaml
# Flag configuration in Unleash
name: new-checkout-flow
type: release
created: 2026-01-15
expires: 2026-02-15        # 30 days max
owner: checkout-team
jira_ticket: SHOP-1234
```

When a flag expires:
- The flag service sends alerts to the owning team
- After a grace period, the flag is auto-enabled (or auto-disabled, depending on policy)
- CI/CD pipelines can fail builds that reference expired flags

**2. Flag Ownership**

Every flag has an owner (team or individual) who is responsible for its lifecycle:

```
Flag Created → Owner Assigned → Rollout Managed → GA Reached → Owner Removes Flag
```

Unowned flags are a code smell. Regular audits surface flags without active owners.

**3. Automated Detection of Stale Flags**

Add a linter or CI check that detects flag references in code and cross-references them with the flag service:

```bash
#!/bin/bash
# stale-flag-check.sh — Run in CI pipeline

# Extract all flag names from code
FLAGS_IN_CODE=$(grep -roh 'is_enabled("[^"]*")' src/ | sort -u | sed 's/is_enabled("//;s/")//')

# Check each against the flag service
for flag in $FLAGS_IN_CODE; do
  STATUS=$(curl -s "http://unleash:4242/api/admin/features/$flag" | jq -r '.stale')
  if [ "$STATUS" = "true" ]; then
    echo "ERROR: Stale flag '$flag' still referenced in code"
    exit 1
  fi
done
```

**4. The "Flag Tax"**

Some teams impose a "flag tax": for every flag older than 30 days, the owning team must spend 1 hour per sprint on flag cleanup. This creates natural pressure to remove flags promptly.

**5. Maximum Flag Count**

Set a team-level maximum: "No team may have more than 15 active release toggles." When the limit is reached, the team must clean up before creating new flags.

---

## Kill Switches and Circuit Breakers

> **Stop and think**: If a feature flag service goes completely offline, what should the application do when it encounters an `if is_enabled("feature-x")` check?

### The Kill Switch Pattern

A kill switch is an ops toggle that immediately disables a feature without redeployment:

```python
def process_payment(order):
    # Kill switch: if payment processor is misbehaving, fall back
    if feature_flags.is_enabled("use-new-payment-processor"):
        return new_processor.charge(order)
    else:
        return legacy_processor.charge(order)
```

Kill switches should:
- Have the simplest possible evaluation (boolean, no complex rules)
- Default to the safe option (legacy behavior) if the flag service is unavailable
- Be documented in runbooks: "If payment errors exceed 1%, disable flag X"
- Be tested regularly (actually toggle them to verify fallback works)

### Automated Kill Switches

Combine feature flags with monitoring for automated circuit breaking:

```python
class AutoKillSwitch:
    def __init__(self, flag_name, metric_name, threshold):
        self.flag_name = flag_name
        self.metric_name = metric_name
        self.threshold = threshold

    def check(self):
        current_value = prometheus.query(self.metric_name)
        if current_value < self.threshold:
            feature_flags.disable(self.flag_name)
            alert.send(f"Auto-disabled {self.flag_name}: "
                      f"{self.metric_name} dropped to {current_value}")

# Usage
kill_switch = AutoKillSwitch(
    flag_name="new-search-engine",
    metric_name="search_success_rate",
    threshold=0.95
)
# Run every 30 seconds
scheduler.every(30).seconds.do(kill_switch.check)
```

### Circuit Breaker vs Kill Switch vs Feature Flag

| Mechanism | Trigger | Scope | Recovery |
|-----------|---------|-------|----------|
| **Feature flag** | Manual/scheduled | Feature-level | Manual toggle |
| **Kill switch** | Manual (emergency) | Feature-level | Manual toggle |
| **Circuit breaker** | Automatic (error threshold) | Dependency-level | Auto-reset after cooldown |

They are complementary:
- **Feature flags** control what users see
- **Kill switches** are emergency feature flags with faster activation
- **Circuit breakers** protect against downstream dependency failures

---

## Percentage Rollouts in Practice

### How Consistent Hashing Works

When you set a flag to "25% rollout," you need consistency — the same user should always see the same variant. This is done with consistent hashing:

```
User "alice" → hash("alice") = 12   → 12 % 100 = 12  → 12 < 25 → ENABLED
User "bob"   → hash("bob")   = 73   → 73 % 100 = 73  → 73 > 25 → DISABLED
User "carol" → hash("carol") = 8    → 8  % 100 = 8   → 8  < 25 → ENABLED
```

When you increase the rollout from 25% to 50%:
- Alice (12) and Carol (8) still see the feature (below 50)
- Bob (73) still does not (above 50)
- New users between 25-50 now see the feature

This ensures that increasing the percentage **never removes** the feature from users who already had it.

### Rollout Strategy

```
Day 1:  Internal employees only (company email targeting)
Day 2:  1% rollout (validate at minimal scale)
Day 3:  5% rollout (first real user cohort)
Day 5:  25% rollout (meaningful scale, watch metrics)
Day 7:  50% rollout (half your users, statistical significance)
Day 10: 100% rollout (GA)
Day 14: Remove flag from code
```

### Monitoring During Rollout

At each stage, compare metrics between the flag-on and flag-off cohorts:

```
                Flag ON Users        Flag OFF Users
Error Rate:     0.3%                 0.2%            ← Acceptable delta
P99 Latency:    180ms                150ms           ← Watch this
Conversion:     4.2%                 3.8%            ← Feature is working!
Revenue/User:   $12.40               $11.90          ← Business impact confirmed
```

If flag-on metrics significantly degrade, pause or reduce the rollout percentage.

---

## Did You Know?

1. **GitHub uses feature flags for nearly every change**. Their feature flag system, called "Flipper," controls thousands of flags simultaneously. Every new feature starts behind a flag, is tested by GitHub employees ("staff shipping"), then gradually rolled out to a percentage of users. A developer can ship to production on their first day — safely hidden behind a flag.

2. **Facebook's Gatekeeper system evaluates over 10 billion feature flag checks per second** across their infrastructure. The system is so critical that it has its own dedicated reliability team. Flag evaluations are cached client-side and refreshed every few seconds, meaning a flag change propagates globally in under 10 seconds to billions of devices.

3. **Knight Capital<!-- incident-xref: knight-capital-2012 --> lost $440 million in 45 minutes in 2012** because of a deployment that accidentally re-enabled dead code from an old feature flag that was never removed. The flag referenced a trading algorithm that had been repurposed years earlier. When the flag was accidentally toggled during a deployment, the zombie algorithm executed millions of unintended trades. This is the most expensive feature flag tech debt in history. For the full case study, see [Infrastructure as Code](../../../../prerequisites/modern-devops/module-1.1-infrastructure-as-code/).

4. **The CNCF adopted OpenFeature as a sandbox project in 2022**, and it graduated to incubating status in 2024, recognizing that feature flag standardization is as important as observability standardization (OpenTelemetry). The specification defines a vendor-neutral API that lets teams switch between providers (Unleash, LaunchDarkly, etc.) without rewriting application code — the same way OpenTelemetry lets you switch between Jaeger and Zipkin.

---

## War Story: The Flag That Saved Black Friday

An e-commerce platform was preparing for Black Friday — their biggest revenue day. Two weeks before, the team deployed a new recommendation engine behind a feature flag, gradually rolling it out to 50% of users.

On Black Friday morning, traffic was 8x normal. At 9:15 AM, the recommendation engine's backing service started timing out under the load. The feature had been stable for two weeks — but never at Black Friday scale.

The on-call engineer saw the alert:

```
09:15 - ALERT: recommendation_latency_p99 > 2000ms
09:16 - On-call opens Unleash dashboard
09:16 - Disables "new-recommendations" flag
09:17 - Recommendation latency drops to 50ms (legacy engine)
09:17 - All clear. No user-visible impact.
```

Total incident duration: **2 minutes**. No lost revenue. No degraded experience. The legacy recommendation engine handled Black Friday perfectly.

Without the feature flag, recovery would have required a redeployment — 15-20 minutes during which the product catalog was slow for half of all users. On Black Friday, those 20 minutes could have cost millions.

The team fixed the scaling issue the following week and re-enabled the flag gradually.

**Lesson**: Feature flags are not just for gradual rollout. They are your emergency brake.

---

## Common Mistakes

| Mistake | Problem | Solution |
|---------|---------|----------|
| Never removing release toggles | Codebase fills with dead branches and confusing logic | Enforce expiry dates; block PRs that add flags without removal tickets |
| Using feature flags for configuration | Mixing feature toggles with app config creates confusion | Use flags for features, config maps for configuration |
| No default value when flag service is down | App crashes or behaves unpredictably | Always specify a safe default; cache flags locally |
| Testing only with flags on | Flag-off path rots and breaks silently | Test both paths in CI; the off path is your fallback |
| Flags without ownership | Nobody knows who can remove them or why they exist | Every flag must have an owner team and a JIRA ticket |
| Percentage rollout without stickiness | Users randomly flip between experiences | Always use consistent hashing on user ID or session ID |
| Nesting feature flags | `if flag_A and flag_B and not flag_C` becomes impossible to reason about | Limit flag nesting to 2 levels maximum; refactor complex logic |
| Using flags to avoid fixing bugs | "We'll just flag it off" becomes permanent | Flags hide bugs temporarily; fix the root cause on a deadline |

---

## Quiz: Check Your Understanding

### Question 1

**Scenario**: Your team has just merged the final PR for a new payment gateway, guarded by a feature flag `new-payment-gateway`. Simultaneously, the SRE team has added a flag `disable-heavy-reports` to prevent the database from crashing during peak hours. How should the lifecycles of these two flags differ?

<details>
<summary>Show Answer</summary>

A **release toggle** like `new-payment-gateway` is short-lived (days to weeks) and used to gate incomplete features during development. Once the payment gateway is fully rolled out to 100% of users and validated, the flag itself and the legacy code path must be removed from the codebase to prevent technical debt. 

In contrast, an **ops toggle** like `disable-heavy-reports` is a permanent safety mechanism (kill switch/circuit breaker). It is intended to remain in the codebase indefinitely so operations can use it at a moment's notice during incidents.

</details>

### Question 2

**Scenario**: You configure a feature flag to show a redesigned shopping cart to 25% of your users. During the first day, you notice support tickets complaining that the cart "keeps changing back and forth" while users navigate the site. What went wrong with your rollout configuration?

<details>
<summary>Show Answer</summary>

The rollout was likely configured using random percentage distribution on each request rather than **consistent hashing** tied to a sticky attribute like a `userId` or `sessionId`. Without a sticky attribute, the flag service recalculates the 25% probability on every page load, causing a single user's experience to flicker. Consistent hashing ensures that `hash(userId)` always maps to the same deterministic value, guaranteeing that a user who falls into the 25% bucket remains in that bucket for all subsequent requests, providing a stable user experience.

</details>

### Question 3

**Scenario**: A senior engineer argues that trunk-based development is too risky for your monolith because incomplete features could accidentally be released to production if everyone commits to `main` daily. How does a feature flag system directly solve this concern?

<details>
<summary>Show Answer</summary>

Feature flags decouple **deployment** (pushing code to production servers) from **release** (exposing that code to users). By wrapping incomplete code in a feature flag that defaults to `false`, developers can merge their unfinished work into `main` and deploy it to production multiple times a day without impacting actual users. This eliminates the need for long-lived feature branches and merge conflict hell, while ensuring that code is continuously integrated and tested alongside the rest of the application.

</details>

### Question 4

**Scenario**: A new engineer joins the company and asks why there are `if` statements checking flags like `xmas-promo-2022` and `beta-v2-migration` in the core transaction logic. No one on the team knows what these flags do or if it is safe to remove them. What organizational failure led to this situation, and how can you automate its prevention?

<details>
<summary>Show Answer</summary>

This is the **flag graveyard**, which occurs when release toggles are treated as permanent code rather than temporary scaffolding. It happens because there was no defined owner or mandatory expiration for these flags. To prevent this, teams should automate lifecycle management by enforcing strict expiry dates (e.g., 30 days maximum for a release toggle) and integrating checks into the CI/CD pipeline. A CI script can parse the codebase for flag references, query the flag service to check their age or status, and fail the build if any flag exceeds its permitted lifespan, forcing developers to clean up debt.

</details>

### Question 5

**Scenario**: The product catalog service occasionally experiences huge latency spikes when an external inventory API goes down. In a separate issue, a new ML-based product sorting algorithm is generating bizarre recommendations that are confusing customers. Should you use a kill switch or a circuit breaker for each situation?

<details>
<summary>Show Answer</summary>

You should use a **circuit breaker** for the external inventory API, and a **kill switch** for the ML sorting algorithm. A circuit breaker automatically trips based on error rates or latency thresholds to protect the system from a failing downstream dependency, and automatically resets when the dependency recovers. A kill switch, however, is an ops feature flag manually toggled by human judgment when a feature is technically functioning (no errors or latency) but producing bad business outcomes.

</details>

### Question 6

**Scenario**: Your cloud provider experiences a regional outage, taking your centralized feature flag service offline for 45 minutes. Your application pods continue running, but they can no longer query the flag service. How do you ensure the application continues serving traffic without crashing or changing user experiences randomly?

<details>
<summary>Show Answer</summary>

The application must rely on a combination of **local caching** and **safe defaults** to degrade gracefully. Instead of calling the flag service on every request, the application SDK should evaluate flags against an in-memory cache that is updated periodically by a background thread. If the flag service goes down, the background thread simply fails to update, and the application continues evaluating against the last known state in the cache. Additionally, the SDK must define safe fallback values (e.g., `is_enabled("new-ui", default=False)`) so that if a pod restarts during the outage and has empty cache, it defaults to a safe, predictable baseline behavior rather than crashing.

</details>

---

## Hands-On Exercise: Deploy Unleash and Toggle a Feature by User ID

### Objective

Deploy Unleash on Kubernetes, create a feature flag with user ID targeting, and demonstrate toggling a feature for specific users without redeploying.

### Setup

```bash
# Create cluster
kind create cluster --name feature-flags-lab
```

### Step 1: Deploy Unleash

```yaml
# unleash.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: unleash-db
spec:
  replicas: 1
  selector:
    matchLabels:
      app: unleash-db
  template:
    metadata:
      labels:
        app: unleash-db
    spec:
      containers:
        - name: postgres
          image: postgres:15
          env:
            - name: POSTGRES_DB
              value: unleash
            - name: POSTGRES_USER
              value: unleash
            - name: POSTGRES_PASSWORD
              value: unleash-pass
          ports:
            - containerPort: 5432
          volumeMounts:
            - name: pg-data
              mountPath: /var/lib/postgresql/data
      volumes:
        - name: pg-data
          emptyDir: {}
---
apiVersion: v1
kind: Service
metadata:
  name: unleash-db
spec:
  selector:
    app: unleash-db
  ports:
    - port: 5432
      targetPort: 5432
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: unleash
spec:
  replicas: 1
  selector:
    matchLabels:
      app: unleash
  template:
    metadata:
      labels:
        app: unleash
    spec:
      containers:
        - name: unleash
          image: unleashorg/unleash-server:6
          env:
            - name: DATABASE_URL
              value: postgres://unleash:unleash-pass@unleash-db:5432/unleash
            - name: DATABASE_SSL
              value: "false"
            - name: INIT_ADMIN_API_TOKENS
              value: "*:*.unleash-admin-api-token"
            - name: INIT_CLIENT_API_TOKENS
              value: "default:development.unleash-client-api-token"
          ports:
            - containerPort: 4242
          readinessProbe:
            httpGet:
              path: /health
              port: 4242
            initialDelaySeconds: 15
            periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: unleash
spec:
  selector:
    app: unleash
  ports:
    - port: 4242
      targetPort: 4242
```

```bash
kubectl apply -f unleash.yaml

# Wait for Unleash to be ready
kubectl rollout status deployment unleash --timeout=120s
```

### Step 2: Create a Feature Flag via the API

```bash
# Port-forward to access Unleash API
kubectl port-forward svc/unleash 4242:4242 &

# Wait for port-forward
sleep 3

# Create a project (default project already exists)
# Create a feature flag
curl -s -X POST http://localhost:4242/api/admin/projects/default/features \
  -H "Authorization: *:*.unleash-admin-api-token" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "new-ui-dashboard",
    "description": "New dashboard UI with charts",
    "type": "release"
  }' | jq .

# Enable the flag in the development environment with userIds strategy
curl -s -X POST http://localhost:4242/api/admin/projects/default/features/new-ui-dashboard/environments/development/strategies \
  -H "Authorization: *:*.unleash-admin-api-token" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "userWithId",
    "parameters": {
      "userIds": "user-42,user-99"
    }
  }' | jq .

# Enable the flag in development environment
curl -s -X POST http://localhost:4242/api/admin/projects/default/features/new-ui-dashboard/environments/development/on \
  -H "Authorization: *:*.unleash-admin-api-token" | jq .
```

### Step 3: Deploy a Sample Application

```yaml
# sample-app.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-code
data:
  server.py: |
    from http.server import HTTPServer, BaseHTTPRequestHandler
    import urllib.request
    import json
    import os

    UNLEASH_URL = os.getenv("UNLEASH_URL", "http://unleash:4242/api")
    API_TOKEN = os.getenv("UNLEASH_API_TOKEN", "default:development.unleash-client-api-token")

    def check_flag(flag_name, user_id):
        """Simple flag check against Unleash API."""
        try:
            url = f"{UNLEASH_URL}/client/features/{flag_name}"
            req = urllib.request.Request(url)
            req.add_header("Authorization", API_TOKEN)
            with urllib.request.urlopen(req, timeout=2) as resp:
                data = json.loads(resp.read())
                # Simple check - in production use the SDK
                if not data.get("enabled", False):
                    return False
                for strategy in data.get("strategies", []):
                    if strategy["name"] == "userWithId":
                        user_ids = strategy["parameters"]["userIds"].split(",")
                        return user_id in user_ids
                return data.get("enabled", False)
        except Exception as e:
            print(f"Flag check failed: {e}")
            return False  # Safe default

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            # Extract user ID from query param
            user_id = "anonymous"
            if "?" in self.path:
                params = dict(p.split("=") for p in self.path.split("?")[1].split("&"))
                user_id = params.get("user", "anonymous")

            # Check feature flag
            new_ui = check_flag("new-ui-dashboard", user_id)

            if new_ui:
                body = f"<h1>NEW Dashboard for {user_id}</h1><p>Charts, graphs, and analytics!</p>"
            else:
                body = f"<h1>Classic Dashboard for {user_id}</h1><p>Simple text view.</p>"

            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(body.encode())

    HTTPServer(("", 8080), Handler).serve_forever()
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: sample-app
spec:
  replicas: 2
  selector:
    matchLabels:
      app: sample-app
  template:
    metadata:
      labels:
        app: sample-app
    spec:
      containers:
        - name: app
          image: python:3.12-slim
          command: ["python", "/app/server.py"]
          env:
            - name: UNLEASH_URL
              value: "http://unleash:4242/api"
            - name: UNLEASH_API_TOKEN
              value: "default:development.unleash-client-api-token"
          ports:
            - containerPort: 8080
          volumeMounts:
            - name: code
              mountPath: /app
      volumes:
        - name: code
          configMap:
            name: app-code
---
apiVersion: v1
kind: Service
metadata:
  name: sample-app
spec:
  selector:
    app: sample-app
  ports:
    - port: 80
      targetPort: 8080
```

```bash
kubectl apply -f sample-app.yaml
kubectl rollout status deployment sample-app --timeout=60s

# Port-forward the app
kubectl port-forward svc/sample-app 8080:80 &
sleep 2
```

### Step 4: Test Feature Flag Targeting

```bash
# User 42 should see the NEW dashboard
curl -s "http://localhost:8080/?user=user-42"
# Output: <h1>NEW Dashboard for user-42</h1><p>Charts, graphs, and analytics!</p>

# User 1 should see the CLASSIC dashboard
curl -s "http://localhost:8080/?user=user-1"
# Output: <h1>Classic Dashboard for user-1</h1><p>Simple text view.</p>

# User 99 should see the NEW dashboard
curl -s "http://localhost:8080/?user=user-99"
# Output: <h1>NEW Dashboard for user-99</h1><p>Charts, graphs, and analytics!</p>
```

### Step 5: Toggle the Flag Without Redeploying

```bash
# Disable the flag — no redeployment needed
curl -s -X POST http://localhost:4242/api/admin/projects/default/features/new-ui-dashboard/environments/development/off \
  -H "Authorization: *:*.unleash-admin-api-token" | jq .

# Now user-42 sees the classic dashboard
curl -s "http://localhost:8080/?user=user-42"
# Output: <h1>Classic Dashboard for user-42</h1><p>Simple text view.</p>

# Re-enable
curl -s -X POST http://localhost:4242/api/admin/projects/default/features/new-ui-dashboard/environments/development/on \
  -H "Authorization: *:*.unleash-admin-api-token" | jq .

# User 42 sees new dashboard again
curl -s "http://localhost:8080/?user=user-42"
# Output: <h1>NEW Dashboard for user-42</h1><p>Charts, graphs, and analytics!</p>
```

### Step 6: Add More Users Without Redeploying

```bash
# Get the strategy ID first
STRATEGY_ID=$(curl -s http://localhost:4242/api/admin/projects/default/features/new-ui-dashboard/environments/development/strategies \
  -H "Authorization: *:*.unleash-admin-api-token" | jq -r '.[0].id')

echo "Strategy ID: $STRATEGY_ID"

# Update the strategy to add user-7 to the targeting list
curl -s -X PUT "http://localhost:4242/api/admin/projects/default/features/new-ui-dashboard/environments/development/strategies/$STRATEGY_ID" \
  -H "Authorization: *:*.unleash-admin-api-token" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "userWithId",
    "parameters": {
      "userIds": "user-42,user-99,user-7"
    }
  }' | jq .

# Now user-7 also sees the new dashboard
curl -s "http://localhost:8080/?user=user-7"
# Output: <h1>NEW Dashboard for user-7</h1>
```

### Clean Up

```bash
kill %1 %2 2>/dev/null
kind delete cluster --name feature-flags-lab
```

### Success Criteria

You have completed this exercise when you can confirm:

- [ ] Unleash is running on Kubernetes with PostgreSQL backend
- [ ] A feature flag was created via the Unleash API
- [ ] User ID targeting correctly showed different UIs to different users
- [ ] Toggling the flag on/off changed behavior **without any redeployment**
- [ ] Adding new users to the targeting list changed behavior **without any redeployment**
- [ ] You understand the difference between deployment (code on servers) and release (feature visible to users)

---

## Key Takeaways

1. **Feature flags decouple deployment from release** — deploy any time, release when ready
2. **Four types of flags exist** — release, experiment, ops, and permission — each with different lifespans
3. **Kill switches are non-negotiable** — every critical feature needs an instant off switch
4. **Flag cleanup prevents technical debt** — enforce expiry dates, ownership, and maximum flag counts
5. **Consistent hashing ensures stable user experiences** — the same user always sees the same variant
6. **Trunk-based development requires feature flags** — merge to main daily, hide incomplete work behind flags
7. **OpenFeature prevents vendor lock-in** — code against a standard interface, swap providers freely

---

## Further Reading

**Documentation:**
- **Unleash Docs** — docs.getunleash.io
- **OpenFeature Specification** — openfeature.dev
- **LaunchDarkly Guides** — docs.launchdarkly.com/guides

**Articles:**
- **"Feature Toggles (aka Feature Flags)"** — Pete Hodgson, martinfowler.com
- **"Trunk-Based Development"** — trunkbaseddevelopment.com
- **"The Knight Capital Disaster"** — Doug Seven (dougseven.com)

**Books:**
- **"Continuous Delivery"** — Jez Humble, David Farley (Chapter on feature toggles)
- **"Accelerate"** — Forsgren, Humble, Kim (trunk-based development as a high-performance practice)

---

## Summary

Feature flags transform releases from binary, all-or-nothing events into gradual, controllable processes. By separating deployment from release, they enable trunk-based development, instant kill switches, and percentage-based rollouts. The key discipline is treating flags as temporary scaffolding — enforce expiry dates and clean them up, or they will become the technical debt that buries your codebase. Combined with a platform like Unleash and a standard like OpenFeature, feature flags become a foundational safety mechanism for any release engineering practice.

---

## Next Module

Continue to [Module 1.4: Multi-Region & Global Release Orchestration](../module-1.4-global-releases/) to learn how to coordinate releases across geographies, manage blast radius at planetary scale, and use ring deployments with ArgoCD ApplicationSets.