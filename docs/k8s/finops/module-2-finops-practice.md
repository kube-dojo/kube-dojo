# Module 2: FinOps in Practice

> **Certification Track** | Complexity: `[MEDIUM]` | Time: 50 minutes

## Overview

Module 1 gave you the "why" and "what" of FinOps. This module gives you the "how." You will learn the practical capabilities that FinOps practitioners use every day — from allocating costs to the right teams, to optimizing cloud rates, to understanding the anatomy of a cloud bill. The module closes with Kubernetes-specific FinOps, bridging the conceptual exam content with real-world platform engineering.

**What You'll Learn**:
- Cost allocation strategies: tagging, labeling, showback vs. chargeback
- Budgeting and forecasting techniques
- Rate optimization: reserved instances, savings plans, spot instances
- Workload optimization: right-sizing, scheduling, idle resource elimination
- Cloud billing anatomy: line items, blended rates, amortization
- Kubernetes-specific FinOps: namespace cost allocation and OpenCost

**Prerequisites**:
- [Module 1: FinOps Fundamentals](module-1-finops-fundamentals.md) — Principles, lifecycle, team structure
- Basic cloud familiarity (AWS/Azure/GCP concepts)
- For K8s section: Basic understanding of namespaces, pods, resource requests/limits

> **Exam Coverage**: This module covers **FinOps Capabilities (28%)** and **Terminology & Cloud Bill (10%)** — totaling **38%** of the FOCP exam.

---

## Why This Module Matters

Knowing the 6 FinOps Principles is like knowing the rules of chess — necessary but not sufficient. To pass the exam and be useful in the real world, you need to understand the *capabilities* — the concrete practices that turn principles into action.

Cost allocation is the foundation of all FinOps work. If you cannot answer "who spent what, and on what?" then optimization is guesswork. Rate optimization can save 30-60% on committed workloads. Right-sizing can eliminate 40-70% of wasted compute. And understanding the cloud bill itself — the actual line items, amortization, and blended rates — separates FinOps practitioners from everyone else staring at a confusing invoice.

---

## Did You Know?

- The average organization has **less than 50% of cloud resources tagged** for cost allocation. This means more than half of cloud spending cannot be attributed to a team, project, or service. It is like running a business where half your expenses have no receipt.
- **Reserved instances** (1-year or 3-year commitments) save 30-60% compared to on-demand pricing, but **the FinOps Foundation reports** that organizations typically leave 15-25% of their reservations underutilized — paying for commitments they don't fully use.
- A single misconfigured auto-scaling group can cost more than an engineer's annual salary. One company accidentally left max-nodes set to 500 on a test cluster over a holiday weekend. Monday morning bill: **$47,000** for 2.5 days of compute nobody used.

---

## Cost Allocation

Cost allocation is the practice of mapping cloud spending to the teams, projects, services, and environments that generated it. It is the cornerstone of the Inform phase and the foundation for everything else in FinOps.

### Why Allocation Matters

Without allocation, the cloud bill is one giant number. Nobody owns it. Nobody can optimize what they cannot see. With allocation, every dollar has an owner, and that owner has the context and motivation to optimize.

```
WITHOUT COST ALLOCATION          WITH COST ALLOCATION
════════════════════════         ════════════════════════

Monthly Cloud Bill:              Monthly Cloud Bill:
$150,000                         $150,000
                                  ├── Team Alpha:    $45,000
"Who spent this?"                │   ├── Prod:       $38,000
"Why did it go up?"              │   └── Staging:     $7,000
"Which team should fix it?"      ├── Team Beta:     $52,000
                                 │   ├── Prod:       $41,000
Nobody knows.                    │   └── Dev:        $11,000
Nobody acts.                     ├── Team Gamma:    $28,000
                                 ├── Shared/Infra:  $18,000
                                 └── Unallocated:    $7,000

                                 Every team sees their spend.
                                 Every team can act.
```

### Tagging and Labeling

Tags (AWS/Azure) and labels (GCP/Kubernetes) are key-value pairs attached to cloud resources that enable cost allocation.

**Common tagging strategy**:

| Tag Key | Example Values | Purpose |
|---------|---------------|---------|
| `team` | alpha, beta, gamma | Who owns this resource? |
| `environment` | prod, staging, dev, test | What lifecycle stage? |
| `service` | payments, auth, search | What application? |
| `cost-center` | CC-1234, CC-5678 | Financial accounting code |
| `project` | phoenix, atlas | Business initiative |
| `managed-by` | terraform, helm, manual | How was it created? |

**Tagging best practices**:
- Define a **mandatory tag set** (e.g., team, environment, service are required)
- **Enforce tagging** through policy (deny resource creation without required tags)
- **Audit regularly** — tag compliance degrades over time without enforcement
- Use **consistent naming conventions** (lowercase, hyphens, no spaces)
- **Automate tagging** where possible (Terraform modules, Kubernetes admission webhooks)

### Showback vs. Chargeback

Once costs are allocated, you need a model for communicating them back to teams. There are two approaches:

**Showback**: Show teams what they spent, but do not charge their budget. This is informational — "here is what your team's cloud usage cost this month." No financial consequences.

**Chargeback**: Charge teams' budgets for their actual cloud usage. This creates direct financial accountability — if Team Alpha overspends, it comes out of Team Alpha's budget.

| Aspect | Showback | Chargeback |
|--------|----------|------------|
| Financial impact | None — informational only | Direct — charges to team budget |
| Accountability | Soft — "you should know" | Hard — "you are paying for this" |
| Complexity | Lower — approximate allocation is OK | Higher — needs accurate, auditable allocation |
| Culture | Educational, non-threatening | Can create friction if perceived as unfair |
| Best for | Organizations starting FinOps (Crawl/Walk) | Mature organizations (Walk/Run) |
| Risk | Teams may ignore reports | Teams may game the system to reduce charges |

> **Exam tip**: The exam often asks about the tradeoffs between showback and chargeback. The key insight: showback is easier to implement and less politically charged, but chargeback creates stronger incentives for optimization.

### Shared Costs

Not all costs map cleanly to one team. Shared infrastructure — Kubernetes control planes, networking, monitoring stacks, CI/CD systems — benefits everyone. There are three common approaches for handling shared costs:

1. **Proportional allocation**: Split shared costs based on each team's usage (e.g., Team Alpha uses 30% of cluster CPU, so they pay 30% of shared costs)
2. **Even split**: Divide shared costs equally among all teams
3. **Fixed overhead**: Charge a flat platform fee per team, regardless of usage

Most mature FinOps practices use proportional allocation for fairness, but even split is simpler to implement and often "good enough" for getting started.

---

## Budgeting and Forecasting

Budgeting and forecasting are Operate-phase activities that bring predictability to cloud spending.

### Budgeting

A cloud budget sets a spending target for a team, project, or the entire organization. Budgets answer: "How much should we spend?"

**Types of budgets**:
- **Fixed budget**: "Team Alpha gets $50,000/month." Simple but inflexible — does not account for growth.
- **Variable budget**: "Team Alpha gets $2.50 per 1,000 active users." Scales with the business but harder to predict.
- **Threshold-based**: "Spend up to $50,000 without approval; anything over requires VP sign-off." Combines flexibility with governance.

**Budget alerts**: Set alerts at multiple thresholds (50%, 75%, 90%, 100% of budget). Cloud providers offer native budget alerting (AWS Budgets, Azure Cost Management, GCP Billing Alerts).

### Forecasting

Forecasting predicts future cloud costs based on historical data, growth trends, and planned changes. It answers: "How much will we spend?"

**Forecasting approaches**:
- **Trend-based**: Extrapolate from the last 3-6 months of spending data. Simple but misses step-function changes (new product launch, migration).
- **Driver-based**: Model costs based on business drivers (users, transactions, data volume). More accurate but requires understanding cost-to-driver relationships.
- **Bottom-up**: Each team forecasts their own costs based on planned work. Most accurate but most effort.

**Common forecasting mistakes**:

| Mistake | Why It Happens | Better Approach |
|---------|---------------|-----------------|
| Linear extrapolation only | Easy to calculate | Combine with driver-based for step changes |
| Ignoring seasonality | Using short data windows | Use 12+ months of data to capture seasonal patterns |
| Not accounting for commitments | Forecasting on-demand only | Factor in RI/SP expirations and renewals |
| Single-point estimates | Overconfidence | Use ranges: best case, expected, worst case |

---

## Rate Optimization

Rate optimization reduces the *price* you pay for cloud resources without changing what you use. It is the closest thing to "free money" in FinOps.

### Reserved Instances (RIs)

A reserved instance is a commitment to use a specific instance type in a specific region for 1 or 3 years. In exchange, you get a significant discount.

```
RESERVED INSTANCE SAVINGS
══════════════════════════════════════════════════════════════

On-Demand:        $0.192/hour    (no commitment)
1-Year RI:        $0.120/hour    (37% savings)
3-Year RI:        $0.075/hour    (61% savings)

For a single m5.xlarge running 24/7:
On-Demand:        $1,402/month
1-Year RI:          $876/month   (save $526/month)
3-Year RI:          $548/month   (save $854/month)
```

**RI considerations**:
- **Utilization risk**: If the workload shrinks or is decommissioned, you still pay for the reservation
- **Flexibility**: Standard RIs are locked to instance type; Convertible RIs can be exchanged (at lower discount)
- **Payment options**: All upfront (biggest discount), partial upfront, or no upfront (smallest discount)

### Savings Plans

Savings Plans (AWS) and Committed Use Discounts (GCP) offer flexibility over RIs. Instead of committing to a specific instance type, you commit to a dollar amount of compute per hour.

**Example**: "I commit to spending $10/hour on compute for 1 year." You get a discount on any compute that fills that commitment, regardless of instance type, region, or even service (EC2, Fargate, Lambda).

**Savings Plans vs. RIs**:

| Aspect | Reserved Instances | Savings Plans |
|--------|-------------------|---------------|
| Commitment | Specific instance type + region | Dollar amount of compute per hour |
| Flexibility | Low (Standard) / Medium (Convertible) | High — applies across instance types |
| Discount depth | Slightly higher | Slightly lower |
| Best for | Stable, predictable workloads | Diverse or evolving workloads |

### Spot Instances

Spot instances (AWS) / Preemptible VMs (GCP) / Spot VMs (Azure) use spare cloud capacity at 60-90% discount. The catch: the cloud provider can terminate them with 2 minutes notice.

**Good for spot**:
- Batch processing, data pipelines
- CI/CD build agents
- Stateless web workers (behind a load balancer)
- Development and testing environments
- Any workload designed to handle interruption

**Not good for spot**:
- Databases and stateful workloads
- Single-instance services with no redundancy
- Long-running jobs that cannot checkpoint

> **Exam tip**: The exam tests whether you understand the tradeoffs between on-demand, reserved, savings plans, and spot. The key: match the commitment level to the workload's stability and criticality.

---

## Workload Optimization

Rate optimization reduces the price per resource. Workload optimization reduces the *number and size* of resources you need.

### Right-Sizing

Right-sizing matches resource allocation to actual usage. Most cloud resources are oversized because engineers provision for peak load (or worse, for "just in case").

```
RIGHT-SIZING EXAMPLE
══════════════════════════════════════════════════════════════

Current allocation:      m5.2xlarge (8 vCPU, 32 GB RAM)
Actual peak usage:       1.2 vCPU, 6.4 GB RAM
Recommended size:        m5.large (2 vCPU, 8 GB RAM)

Monthly cost:
  Before:    $280.32/month
  After:      $70.08/month
  Savings:   $210.24/month (75%)

Multiply by 50 similar instances: $10,512/month saved
```

**Right-sizing process**:
1. Collect usage metrics (CPU, memory, network, disk) over 14-30 days
2. Identify resources where peak utilization is below 40-50% of allocation
3. Recommend a smaller size that provides headroom above peak usage
4. Implement changes during maintenance windows
5. Monitor after resizing to confirm performance is acceptable

### Scheduling

Non-production environments often run 24/7 but are only used during business hours. Scheduling shuts them down during off-hours.

```
SCHEDULING SAVINGS
══════════════════════════════════════════════════════════════

Dev/staging environment: 10 instances
Running 24/7:            $7,200/month
Running 10h/day, 5d/wk:  $2,142/month (70% savings)

The math:
  24h × 7d = 168 hours/week
  10h × 5d =  50 hours/week
  Savings: 70% of compute cost
```

### Idle Resource Elimination

Idle resources are cloud resources that exist but serve no purpose. Common culprits:

| Idle Resource | How It Happens | Detection Method |
|---------------|---------------|------------------|
| Unattached EBS volumes | Instance terminated, volume remains | Filter for `available` state |
| Old snapshots | Backup snapshots never cleaned up | Age-based policies (>90 days) |
| Unused elastic IPs | Service moved, IP not released | Filter for unassociated IPs |
| Forgotten load balancers | No healthy targets registered | Check target group health |
| Orphaned databases | Dev DB from a project that ended | CPU utilization near 0% for 14+ days |
| Stale ECR images | Old container images accumulate | Lifecycle policies based on age/count |

> **Exam tip**: The exam often asks which optimization type (rate vs. workload) applies to a scenario. Reserved instances = rate optimization. Right-sizing = workload optimization. Scheduling = workload optimization. The distinction matters.

---

## Cloud Billing Anatomy

Understanding a cloud bill is a core FOCP exam topic. Let's break down the key terms.

### Line Items

A cloud bill is composed of line items. Each line item represents a charge for a specific resource in a specific region for a specific time period.

**Example AWS line item**:
```
Account:        123456789012
Service:        Amazon EC2
Usage Type:     USEast1-BoxUsage:m5.xlarge
Operation:      RunInstances
Usage Amount:   744 hours
Unblended Cost: $142.85
```

### Key Billing Terms

| Term | Definition | Example |
|------|-----------|---------|
| **On-demand cost** | The list price with no discounts | $0.192/hour for m5.xlarge |
| **Unblended cost** | The actual charge per line item, before any amortization | $142.85 for 744 hours of m5.xlarge |
| **Blended rate** | Average rate across on-demand and discounted usage | If 50% is on-demand ($0.192) and 50% is RI ($0.120), blended = $0.156 |
| **Amortized cost** | Upfront RI/SP payments spread evenly across the commitment period | $8,760 upfront RI / 12 months = $730/month |
| **Net cost** | Cost after all discounts, credits, and amortization | The "real" cost to the business |
| **List price** | Published on-demand price before any negotiation | The sticker price |

### Understanding Amortization

When you buy a 1-year reserved instance with an upfront payment, you pay a lump sum on day one. But for budgeting and allocation purposes, you want to spread that cost evenly across 12 months.

```
AMORTIZATION EXAMPLE
══════════════════════════════════════════════════════════════

1-Year RI purchase: $8,760 all-upfront on January 1

Without amortization:
  January:   $8,760  (huge spike!)
  Feb-Dec:   $0      (looks free!)

With amortization:
  January:   $730    (spread evenly)
  February:  $730
  March:     $730
  ...
  December:  $730

Amortization gives you the true monthly cost.
```

### Data Transfer Costs

Data transfer is the hidden cost that surprises many organizations. Ingress (data in) is usually free. Egress (data out) is not.

**Common data transfer charges**:
- Cross-region traffic (e.g., us-east-1 to eu-west-1)
- Cross-AZ traffic (even within the same region)
- Internet egress (data leaving the cloud)
- VPN/Direct Connect bandwidth
- NAT Gateway processing charges

> **Exam tip**: The exam may ask about cost components. Remember that compute, storage, and data transfer are the three pillars of cloud cost. Most organizations focus on compute and storage, but data transfer can be 10-20% of the bill and is often overlooked.

---

## Kubernetes-Specific FinOps

Kubernetes adds a layer of complexity to FinOps because it *abstracts away* the underlying cloud resources. An EC2 instance might run 15 pods from 5 different teams. Whose cost is it?

### The Kubernetes Cost Problem

```
THE K8S COST ATTRIBUTION CHALLENGE
══════════════════════════════════════════════════════════════

Cloud bill shows:       Node (m5.2xlarge): $280/month

But the node runs:
  ├── Pod A (Team Alpha):    requests 2 CPU, 4Gi RAM
  ├── Pod B (Team Alpha):    requests 1 CPU, 2Gi RAM
  ├── Pod C (Team Beta):     requests 0.5 CPU, 1Gi RAM
  ├── Pod D (Team Gamma):    requests 1 CPU, 2Gi RAM
  ├── System pods (kube-*):  requests 0.5 CPU, 1Gi RAM
  └── Idle capacity:         3 CPU, 22Gi RAM (unused!)

Who pays for the idle capacity?
How do you split the node cost fairly?
```

### Namespace-Based Cost Allocation

In Kubernetes, the namespace is the primary unit for cost allocation. Each team owns one or more namespaces, and costs are calculated based on resource requests within those namespaces.

**Cost allocation formula**:
```
Team's cost = (Team's resource requests / Total node resources) × Node cost
```

**Example**:
- Node cost: $280/month
- Node capacity: 8 CPU, 32 Gi RAM
- Team Alpha pods request: 3 CPU, 6 Gi RAM
- Team Alpha's cost: (3/8) × $280 = $105/month (CPU-based) or (6/32) × $280 = $52.50/month (RAM-based)

In practice, tools like OpenCost use a weighted average of CPU and RAM to calculate fair allocation.

### Kubernetes Resource Requests vs. Limits

Resource **requests** are what Kubernetes uses for scheduling and what FinOps tools use for cost allocation. Resource **limits** are the maximum a pod can use.

| Concept | Scheduling | Cost Allocation | Why It Matters for FinOps |
|---------|-----------|-----------------|--------------------------|
| Requests | Used by scheduler to place pods | Used to calculate team's share of node cost | Over-requesting = paying for unused capacity |
| Limits | Not used for scheduling | Not typically used for allocation | Setting limits too high wastes memory |
| Actual usage | N/A | Some tools offer usage-based allocation | Most accurate but complex |

**FinOps implication**: If a team requests 4 CPU but only uses 0.5 CPU, they are "paying for" 4 CPU in a request-based allocation model. This creates an incentive to right-size requests — which is exactly what FinOps wants.

### Labels for Cost Allocation

Kubernetes labels serve the same purpose as cloud tags for cost allocation:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: payment-service
  namespace: team-alpha
  labels:
    app: payments
    team: alpha
    environment: production
    cost-center: "CC-1234"
```

**Best practices for K8s cost labels**:
- Use a **consistent label schema** across all workloads
- Enforce labels with **admission webhooks** (OPA/Gatekeeper or Kyverno)
- Include at minimum: `team`, `environment`, `app`, `cost-center`
- Apply labels to namespaces for default cost allocation

### OpenCost Integration

OpenCost is the CNCF sandbox project for Kubernetes cost monitoring. It provides real-time cost allocation at the namespace, deployment, pod, and container level.

**What OpenCost provides**:
- Per-namespace cost breakdown (CPU, RAM, storage, network)
- Idle cost identification (unallocated cluster resources)
- Efficiency metrics (requested vs. actual usage)
- Cost by label (team, environment, service)
- Integration with Prometheus for historical data

**OpenCost cost model**:
```
Pod cost = (CPU requests × CPU cost/hour) + (RAM requests × RAM cost/hour)
           + (PV storage × storage cost/hour) + (network × network cost/GB)

Idle cost = Total node cost - Sum of all pod costs

Cluster efficiency = Sum of pod costs / Total node cost × 100%
```

> For hands-on OpenCost installation, dashboards, and right-sizing exercises, see our toolkit module: [Module 6.4: FinOps with OpenCost](../../platform/toolkits/scaling-reliability/module-6.4-finops-opencost.md)

### Kubernetes Optimization Strategies

| Strategy | What It Does | Savings Potential |
|----------|-------------|-------------------|
| Right-size requests | Match requests to actual usage | 40-70% compute reduction |
| Namespace quotas | Cap resource usage per team | Prevents runaway spending |
| LimitRanges | Set default/max resource limits | Prevents oversized pods |
| Cluster autoscaling | Scale nodes based on demand | Avoid paying for idle nodes |
| Spot node pools | Run fault-tolerant workloads on spot | 60-90% node cost reduction |
| Schedule non-prod | Shut down dev/test after hours | 50-70% non-prod savings |
| Pod Disruption Budgets | Enable safe spot/preemptible use | Supports spot adoption |
| VPA (Vertical Pod Autoscaler) | Auto-adjust resource requests | Continuous right-sizing |

---

## War Story: The Tag That Saved $400K

A Fortune 500 company migrated to Kubernetes on AWS (EKS) with 12 engineering teams and 300+ microservices. Their monthly cloud bill was $650,000 and growing. The FinOps team was asked to "find savings."

The first challenge: only 35% of resources had cost allocation tags. The Kubernetes layer was a complete black box — the AWS bill showed EC2 instances, but nobody knew which teams' pods ran on which instances.

Step 1 (Inform): They deployed OpenCost and enforced a mandatory label policy using Kyverno. Any pod without `team`, `environment`, and `service` labels was rejected by the admission webhook. Within two weeks, 95% of workloads were labeled.

Step 2 (Inform): They built a Grafana dashboard showing cost per team per environment. The results shocked everyone:

- Team Delta's "small test service" was requesting 24 CPU across 6 replicas — in the dev namespace. It had been load-testing a service that was decommissioned 4 months ago. Cost: $3,200/month.
- The staging environment was an exact replica of production (same node count, same instance types). Nobody had questioned this. Cost: $180,000/month — 28% of the entire bill.
- Three teams were running their own Prometheus instances (with 90-day retention each) instead of using the shared monitoring stack. Combined cost: $12,000/month.

Step 3 (Optimize): They right-sized the staging environment to 20% of production capacity (sufficient for integration testing). They killed the zombie load-test pods. They consolidated monitoring.

Step 4 (Operate): They established monthly cost reviews per team, budget alerts at 80% and 100%, and a quarterly RI purchasing process.

Result: Monthly bill dropped from $650,000 to $410,000 — a $240,000/month reduction ($2.88M/year). The single biggest win? The staging right-sizing, which came directly from making costs visible through namespace-level allocation. The tag that saved $400K was `environment: staging`.

---

## Common Mistakes

| Mistake | Why It Happens | Better Approach |
|---------|---------------|-----------------|
| Allocating by limits, not requests | Limits feel like "what you're using" | Requests determine scheduling and should drive allocation |
| Ignoring idle cluster cost | "Unallocated" seems like nobody's problem | Distribute idle cost proportionally or track separately |
| Tagging after the fact | "We'll tag resources later" | Enforce tagging at creation time with admission policies |
| Buying RIs without usage data | "3-year RI saves the most!" | Analyze 3+ months of usage before committing |
| Optimizing before understanding | Jumping to "buy spot instances!" | Start with Inform — understand where money goes first |
| Using on-demand for stable workloads | Default instance type, never changed | Stable 24/7 workloads should always use RIs or savings plans |

---

## Quiz

Test your understanding of FinOps capabilities and practices.

### Question 1
**A team wants their engineers to see their cloud costs each month, but without directly impacting team budgets. Which model should they use?**

A) Chargeback
B) Showback
C) Proportional allocation
D) Fixed overhead

<details>
<summary>Show Answer</summary>

**B) Showback.**

Showback provides cost visibility without financial consequences. It shows teams what they spent, but does not charge their budget. This is ideal for organizations building cost awareness before moving to chargeback.

</details>

### Question 2
**Which of the following is the BEST candidate for spot instances?**

A) A production PostgreSQL database
B) A CI/CD build pipeline that runs test suites
C) A single-replica authentication service
D) An etcd cluster for Kubernetes

<details>
<summary>Show Answer</summary>

**B) A CI/CD build pipeline that runs test suites.**

CI/CD builds are stateless, fault-tolerant, and can be restarted if interrupted — ideal for spot instances. Databases, single-replica services, and etcd clusters cannot tolerate sudden termination.

</details>

### Question 3
**An organization pays $8,760 upfront for a 1-year reserved instance on January 1. What is the amortized monthly cost?**

A) $8,760 in January, $0 for the rest of the year
B) $730/month for 12 months
C) $2,190/quarter
D) It depends on usage

<details>
<summary>Show Answer</summary>

**B) $730/month for 12 months.**

Amortization spreads the upfront payment evenly across the commitment period: $8,760 / 12 = $730/month. This gives a true picture of the monthly cost of the resource.

</details>

### Question 4
**In Kubernetes, what is the primary resource metric used by most FinOps tools for cost allocation?**

A) Resource limits
B) Resource requests
C) Actual resource usage
D) Pod count

<details>
<summary>Show Answer</summary>

**B) Resource requests.**

Resource requests are what Kubernetes uses for scheduling and what FinOps tools like OpenCost use as the primary basis for cost allocation. Requests represent the guaranteed resources a pod reserves on a node.

</details>

### Question 5
**A company's cloud bill shows "blended rate" of $0.156/hour for m5.xlarge instances. What does this mean?**

A) They negotiated a special price with the cloud provider
B) It is the average rate across their on-demand and discounted usage
C) It is the rate after subtracting tax
D) It is the rate for a 1-year reserved instance

<details>
<summary>Show Answer</summary>

**B) It is the average rate across their on-demand and discounted usage.**

Blended rate averages the different rates an organization pays across on-demand, reserved, and savings plan usage for the same instance type. If 50% is on-demand at $0.192 and 50% is RI at $0.120, the blended rate is $0.156.

</details>

### Question 6
**Which optimization strategy reduces the PRICE of cloud resources without changing usage?**

A) Right-sizing
B) Scheduling non-production environments
C) Purchasing savings plans
D) Eliminating idle resources

<details>
<summary>Show Answer</summary>

**C) Purchasing savings plans.**

Savings plans are rate optimization — they reduce the price per unit of compute. Right-sizing, scheduling, and idle resource elimination are workload optimization — they reduce the amount of resources consumed.

</details>

### Question 7
**A team requests 4 CPU for a pod but actual usage averages 0.5 CPU. In a request-based cost allocation model, how much CPU cost does the team pay for?**

A) 0.5 CPU
B) 4 CPU
C) 2.25 CPU (average of request and usage)
D) 0 CPU (usage is below the request threshold)

<details>
<summary>Show Answer</summary>

**B) 4 CPU.**

In a request-based allocation model, cost is calculated on what you requested, not what you used. The team "owns" 4 CPU worth of node capacity. This creates an incentive to right-size requests — a key FinOps benefit.

</details>

### Question 8
**Which of the following is a data transfer cost that organizations commonly overlook?**

A) Compute cost for running instances
B) Cross-availability-zone traffic within the same region
C) Storage cost for EBS volumes
D) Reserved instance amortization

<details>
<summary>Show Answer</summary>

**B) Cross-availability-zone traffic within the same region.**

Data transfer between AZs is charged (typically $0.01/GB each way on AWS) and is often overlooked because teams assume "same region = free." For high-traffic services across AZs, this can be significant.

</details>

### Question 9
**What is the main advantage of Savings Plans over Reserved Instances?**

A) Deeper discounts
B) Flexibility across instance types and services
C) No commitment required
D) Guaranteed instance availability

<details>
<summary>Show Answer</summary>

**B) Flexibility across instance types and services.**

Savings Plans commit to a dollar amount of compute per hour, not a specific instance type. This means the discount applies even if you change instance families, regions (with Compute Savings Plans), or services. RIs lock you to a specific instance type and region.

</details>

### Question 10
**An organization has 40% of resources tagged, uses showback reports monthly, and performs manual right-sizing quarterly. What FinOps maturity level are they at?**

A) Crawl
B) Walk
C) Run
D) Pre-Crawl

<details>
<summary>Show Answer</summary>

**A) Crawl.**

With only 40% tagging coverage, monthly (not weekly) showback, and manual/infrequent optimization, this organization is at the Crawl maturity level. Walk requires 70%+ tagging, regular reviews, and some automation. Run requires near-complete tagging, chargeback, and extensive automation.

</details>

---

## Hands-On Exercise: Cloud Cost Analysis

This exercise is conceptual — no cluster required. It tests your ability to apply FinOps practices to a realistic scenario.

### Scenario

You are a new FinOps practitioner at CloudCorp. Here is the current situation:

**Monthly cloud bill**: $120,000
**Cloud provider**: AWS
**Teams**: 4 engineering teams, 1 data team, 1 platform team
**Kubernetes**: EKS cluster with 25 nodes (m5.xlarge, on-demand)
**Tagging coverage**: 30%
**Current cost visibility**: One AWS account, no cost breakdown by team

### Your Task

Work through the FinOps lifecycle for CloudCorp. Write down your answers before checking the solution.

**Step 1 (Inform)**: What are the first 3 actions you would take to create cost visibility?

<details>
<summary>Show Answer</summary>

1. **Implement mandatory tagging policy** — Define required tags (team, environment, service, cost-center) and enforce via AWS SCPs and Kubernetes admission webhooks (Kyverno/OPA). Target: 80%+ coverage in 30 days.

2. **Deploy OpenCost on the EKS cluster** — Get immediate namespace-level cost visibility for the Kubernetes workloads, which are likely 60-70% of the bill.

3. **Build a cost dashboard** — Create a Grafana or AWS Cost Explorer dashboard showing cost by team, environment, and service. Share it with all team leads and finance. Make it self-service, not a monthly PDF.

</details>

**Step 2 (Optimize)**: The 25 EKS nodes are all m5.xlarge on-demand at $0.192/hour. Average cluster CPU utilization is 35%. What optimizations would you recommend?

<details>
<summary>Show Answer</summary>

1. **Right-size the cluster** — At 35% average utilization, the cluster is significantly over-provisioned. Enable Karpenter or Cluster Autoscaler to dynamically scale nodes based on pending pod requests. This could reduce from 25 to ~12-15 nodes.

2. **Purchase Savings Plans** — For the baseline compute that runs 24/7 (likely 10-12 nodes worth), purchase a 1-year Compute Savings Plan. Savings: ~35% on committed compute.

3. **Introduce spot node pools** — For fault-tolerant workloads (dev/test, batch jobs, stateless services with multiple replicas), create a spot node pool. Savings: 60-70% on those nodes.

4. **Schedule non-production namespaces** — If dev/staging environments run 24/7 but are only used 10 hours/day, 5 days/week, scheduling saves ~70% on those workloads.

Combined potential savings: $40,000-$60,000/month (33-50% reduction).

</details>

**Step 3 (Operate)**: What governance processes would you establish to sustain these improvements?

<details>
<summary>Show Answer</summary>

1. **Weekly cost review** — 30-minute meeting with team leads reviewing cost dashboards, anomalies, and optimization opportunities.

2. **Budget alerts** — Set alerts at 80% and 100% of each team's monthly budget in AWS Budgets.

3. **Tagging compliance audit** — Monthly report on tagging coverage by team. Teams below 80% get flagged.

4. **Quarterly RI/SP review** — Review commitment utilization and purchase additional reservations for new stable workloads.

5. **Anomaly detection** — Configure AWS Cost Anomaly Detection to alert the FinOps Slack channel when any service's daily cost exceeds 2x the 7-day average.

</details>

### Success Criteria

You have completed this exercise successfully if you:
- [ ] Identified Inform actions that create visibility before optimizing
- [ ] Recommended rate AND workload optimizations (not just one type)
- [ ] Included governance processes that make FinOps sustainable
- [ ] Connected recommendations to specific FinOps principles and lifecycle phases

---

## Summary

FinOps capabilities turn principles into practice. The key skills tested on the FOCP exam:

**Cost Allocation**: Tags/labels map costs to owners. Showback educates; chargeback creates accountability. Shared costs need a fair distribution model.

**Rate Optimization**: Reserved instances (30-60% savings), savings plans (flexible commitments), and spot instances (60-90% savings for fault-tolerant workloads).

**Workload Optimization**: Right-sizing (match requests to usage), scheduling (shut down non-prod after hours), and idle resource elimination (find and kill zombies).

**Cloud Billing**: Understand line items, blended rates, amortized costs, and data transfer charges. These terms appear directly on the exam.

**Kubernetes FinOps**: Namespace-based allocation using resource requests, label policies enforced by admission webhooks, and OpenCost for real-time cost visibility.

---

## Next Steps

You have completed the FOCP curriculum modules. To continue your learning:

- **Hands-on practice**: Work through [Module 6.4: FinOps with OpenCost](../../platform/toolkits/scaling-reliability/module-6.4-finops-opencost.md) for practical Kubernetes cost monitoring
- **Review Module 1**: Re-take the [Module 1 quiz](module-1-finops-fundamentals.md#quiz) to confirm you know the 6 principles and lifecycle phases cold
- **Official resources**: Visit [finops.org](https://www.finops.org/) for the FinOps Foundation's free training materials
- **Take the exam**: Register at [training.linuxfoundation.org](https://training.linuxfoundation.org/)
