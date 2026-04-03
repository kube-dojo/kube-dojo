---
title: "Module 10.10: FinOps at Enterprise Scale"
slug: cloud/enterprise-hybrid/module-10.10-enterprise-finops
sidebar:
  order: 11
---
**Complexity**: [COMPLEX] | **Time to Complete**: 2h | **Prerequisites**: Cloud Essentials (AWS/Azure/GCP), Kubernetes Resource Management, Enterprise Landing Zones (Module 10.1)

## What You'll Be Able to Do

After completing this module, you will be able to:

- **Implement enterprise FinOps practices with cloud billing integration, team-level cost allocation, and Kubernetes cost attribution**
- **Configure multi-cloud cost visibility using Kubecost, OpenCost, or FOCUS-compliant tools across the fleet**
- **Design chargeback and showback models that map Kubernetes namespace and label costs to business units**
- **Deploy automated cost optimization pipelines that enforce resource quotas, right-size recommendations, and waste detection**

---

## Why This Module Matters

In March 2024, the CFO of a Series D SaaS company called an emergency board meeting. Their cloud bill had grown from $1.2 million per month to $4.8 million per month in 18 months -- a 4x increase while revenue grew only 1.6x. The engineering team had no explanation. When pressed, the VP of Engineering admitted they did not know which teams or services were responsible for the growth. Their Kubernetes clusters ran hundreds of services, each requesting resources based on "better safe than sorry" estimates. The average CPU utilization across their fleet was 11%. They were paying for 9x more compute than they actually used.

The board demanded a plan. The company hired a FinOps consultant who discovered: (1) 23% of their spend was on idle resources that no team claimed ownership of, (2) their Reserved Instance coverage was 18% when it should have been 60-70%, (3) three teams were running GPU instances for machine learning experiments that finished months ago but whose clusters were never decommissioned, and (4) cross-region data transfer costs were $340,000/month because two services that communicated constantly were deployed in different regions for no good reason.

This story is not unusual. It is the norm. The FinOps Foundation's 2024 State of FinOps report found that 73% of organizations consider cloud waste their top FinOps challenge, and the average organization wastes 28% of its cloud spend. At enterprise scale -- where cloud bills reach $10-100 million per year -- that waste translates to millions of dollars that could fund entire engineering teams.

FinOps at enterprise scale is not about nickel-and-diming individual pod requests. It is about building the organizational capability to understand, forecast, and optimize cloud spending as a continuous practice. In this module, you will learn cloud economics at scale, how Enterprise Discount Programs work, forecasting and anomaly detection, chargeback models for shared Kubernetes clusters, the true cost of multi-cloud, and how to build a FinOps culture.

---

## Cloud Economics at Scale

### The Cloud Pricing Model

Cloud providers price compute, storage, and networking differently, but they share a common pattern: the more you commit, the less you pay per unit.

```text
┌──────────────────────────────────────────────────────────────┐
│  CLOUD PRICING SPECTRUM (Compute)                              │
│                                                                │
│  Most Expensive                              Least Expensive   │
│  ◄──────────────────────────────────────────────────────────► │
│                                                                │
│  On-Demand    Savings Plans    Reserved       Spot/Preemptible │
│  (1.00x)      (0.60-0.72x)    (0.40-0.60x)   (0.10-0.30x)   │
│                                                                │
│  No commit    1-3 year commit  1-3 year commit No guarantee   │
│  Full flex    Moderate flex    Rigid (type/    Can be revoked  │
│               (any instance)   region locked)  at any time     │
│                                                                │
│  Example: m6i.xlarge in us-east-1                              │
│  On-Demand:  $0.192/hr  ($1,682/yr)                           │
│  Savings:    $0.121/hr  ($1,060/yr)  = 37% savings            │
│  Reserved:   $0.077/hr  ($675/yr)    = 60% savings            │
│  Spot:       $0.058/hr  ($508/yr)    = 70% savings            │
└──────────────────────────────────────────────────────────────┘
```

### Enterprise Discount Programs (EDPs)

At enterprise scale ($1M+/year), cloud providers offer negotiated discounts through Enterprise Discount Programs:

| Provider | Program | Typical Discount | Commitment |
| :--- | :--- | :--- | :--- |
| **AWS** | Enterprise Discount Program (EDP) | 5-15% on total spend | 1-5 year, minimum annual commit |
| **Azure** | Enterprise Agreement (EA) | 5-20% on consumption | 1-3 year, minimum annual commit |
| **GCP** | Committed Use Discounts (CUD) + Negotiated | 5-30% on specific services | 1-3 year per service |

```text
┌──────────────────────────────────────────────────────────────┐
│  LAYERED DISCOUNT MODEL                                        │
│                                                                │
│  Total Cloud Spend: $10M/year                                  │
│                                                                │
│  Layer 1: EDP/EA Base Discount         -10%    = -$1.0M       │
│  Layer 2: Reserved Instances (65%)     -25%*   = -$2.25M      │
│  Layer 3: Spot Instances (15%)         -65%*   = -$0.97M      │
│  Layer 4: Right-sizing optimization    -20%*   = -$1.15M      │
│                                                                │
│  * Applied to remaining spend after previous discounts         │
│                                                                │
│  Effective spend: $4.63M (54% savings)                        │
│  Without optimization: $10M                                    │
│  Annual savings: $5.37M                                        │
│                                                                │
│  That $5.37M funds ~30 senior engineers for a year            │
└──────────────────────────────────────────────────────────────┘
```

### Kubernetes-Specific Cost Drivers

| Cost Driver | What It Is | Why It Grows | How to Optimize |
| :--- | :--- | :--- | :--- |
| **Over-provisioned pods** | Requests set too high, pods use fraction of allocated resources | Fear of OOM kills, copy-paste from examples | Right-size using VPA recommendations, Goldilocks |
| **Idle clusters** | Dev/test clusters running 24/7 but used only during business hours | Forgot to scale down, no automation | Auto-scaling to 0 nodes off-hours, cluster hibernation |
| **Cross-AZ traffic** | Pods talking to services in different AZs | Default round-robin load balancing ignores topology | Topology-aware routing, colocate communicating services |
| **Persistent volumes** | Over-sized PVs, snapshot retention too long | Provisioned "just in case," no lifecycle management | Right-size PVs, automate snapshot expiry, use dynamic provisioning |
| **NAT Gateway** | All outbound traffic from private subnets goes through NAT | Default architecture for private EKS | Use VPC endpoints for AWS services, reduce external calls |
| **Load Balancers** | One ALB/NLB per Service of type LoadBalancer | Developers create LoadBalancer Services by default | Use an Ingress Controller (one LB for many services) |
| **Data transfer** | Cross-region, cross-cloud, internet egress | Microservices sprawl, poor placement decisions | Place communicating services in the same region/AZ |

---

## Forecasting and Anomaly Detection

### Cost Forecasting Model

```bash
# AWS Cost Explorer: Forecast next 3 months
aws ce get-cost-forecast \
  --time-period Start=$(date -u +%Y-%m-01),End=$(date -u -d "+3 months" +%Y-%m-01) \
  --metric UNBLENDED_COST \
  --granularity MONTHLY \
  --query '{
    Forecast: ResultsByTime[*].{
      Period: TimePeriod.Start,
      Mean: MeanValue,
      Min: PredictionIntervalLowerBound,
      Max: PredictionIntervalUpperBound
    }
  }' --output table
```

### Anomaly Detection Pipeline

```text
┌──────────────────────────────────────────────────────────────┐
│  COST ANOMALY DETECTION PIPELINE                               │
│                                                                │
│  ┌────────────┐   ┌──────────────┐   ┌───────────────────┐   │
│  │ Cloud Bill  │──►│ Normalize &  │──►│ Statistical       │   │
│  │ (hourly)    │   │ Categorize   │   │ Analysis          │   │
│  └────────────┘   └──────────────┘   │ - Moving average  │   │
│                                       │ - Std deviation   │   │
│                                       │ - Seasonality     │   │
│                                       └─────────┬─────────┘   │
│                                                 │              │
│                                       ┌─────────▼─────────┐   │
│                                       │ Anomaly?           │   │
│                                       │ > 2 std dev from   │   │
│                                       │   moving average   │   │
│                                       └─────────┬─────────┘   │
│                                                 │              │
│                                    ┌────────────┤             │
│                                    ▼            ▼             │
│                              ┌──────────┐ ┌──────────┐       │
│                              │ Alert    │ │ Ignore   │       │
│                              │ (Slack,  │ │ (within  │       │
│                              │  PagerDuty)│  normal) │       │
│                              └──────────┘ └──────────┘       │
└──────────────────────────────────────────────────────────────┘
```

```bash
# AWS Cost Anomaly Detection setup
aws ce create-anomaly-monitor \
  --anomaly-monitor '{
    "MonitorName": "k8s-cost-monitor",
    "MonitorType": "DIMENSIONAL",
    "MonitorDimension": "SERVICE"
  }'

aws ce create-anomaly-subscription \
  --anomaly-subscription '{
    "SubscriptionName": "k8s-cost-alerts",
    "MonitorArnList": ["arn:aws:ce::123456789012:anomalymonitor/abc-123"],
    "Subscribers": [
      {"Address": "finops-team@company.com", "Type": "EMAIL"},
      {"Address": "arn:aws:sns:us-east-1:123456789012:finops-alerts", "Type": "SNS"}
    ],
    "Threshold": 100,
    "ThresholdExpression": {
      "Dimensions": {
        "Key": "ANOMALY_TOTAL_IMPACT_ABSOLUTE",
        "Values": ["100"],
        "MatchOptions": ["GREATER_THAN_OR_EQUAL"]
      }
    },
    "Frequency": "DAILY"
  }'
```

---

## Chargeback for Shared Kubernetes Clusters

The hardest FinOps problem in Kubernetes is attributing costs to teams when multiple teams share the same cluster and nodes. A node running pods from 5 different teams needs its cost split fairly.

### Chargeback Models

```text
┌──────────────────────────────────────────────────────────────┐
│  KUBERNETES COST ALLOCATION MODELS                             │
│                                                                │
│  Model 1: REQUEST-BASED (Most Common)                         │
│  Team pays for what they REQUEST, not what they USE            │
│  Pro: Simple, encourages right-sizing                          │
│  Con: Teams that request 4 CPU but use 0.5 still pay for 4   │
│                                                                │
│  Model 2: USAGE-BASED (Fairest)                               │
│  Team pays for actual CPU/memory consumption                   │
│  Pro: Fair, incentivizes efficiency                            │
│  Con: Complex to calculate, requires metering                  │
│                                                                │
│  Model 3: HYBRID (Recommended)                                │
│  Base charge = max(request, usage) + shared cost overhead     │
│  Pro: Balances fairness with incentivizing right-sizing        │
│  Con: Requires good tooling                                    │
│                                                                │
│  Model 4: FIXED ALLOCATION                                     │
│  Team gets N nodes, pays fixed monthly fee                    │
│  Pro: Predictable, easy to budget                              │
│  Con: Inefficient, leads to over-provisioning                  │
└──────────────────────────────────────────────────────────────┘
```

### OpenCost: Open-Source Kubernetes Cost Allocation

```bash
# Install OpenCost (CNCF sandbox project)
helm repo add opencost https://opencost.github.io/opencost-helm-chart
helm install opencost opencost/opencost \
  --namespace opencost --create-namespace \
  --set opencost.exporter.defaultClusterId=eks-prod-east \
  --set opencost.exporter.aws.spot_data_region=us-east-1 \
  --set opencost.exporter.aws.spot_data_bucket=company-spot-pricing \
  --set opencost.ui.enabled=true

# Query cost allocation by namespace
curl -s "http://localhost:9003/allocation/compute?window=7d&aggregate=namespace" | \
  jq '.data[0] | to_entries | sort_by(.value.totalCost) | reverse | .[:10] |
  .[] | {namespace: .key, totalCost: (.value.totalCost | . * 100 | round / 100),
  cpuCost: (.value.cpuCost | . * 100 | round / 100),
  memoryCost: (.value.ramCost | . * 100 | round / 100),
  cpuEfficiency: (.value.cpuEfficiency | . * 100 | round),
  memoryEfficiency: (.value.ramEfficiency | . * 100 | round)}'
```

### Kubecost: Enterprise Cost Management

```yaml
# Kubecost deployment for detailed cost allocation
# helm install kubecost kubecost/cost-analyzer --namespace kubecost --create-namespace

# Kubecost cost allocation API
# GET /model/allocation?window=30d&aggregate=namespace,label:team
# Response includes:
# - CPU cost (request-based + usage-based)
# - Memory cost (request-based + usage-based)
# - Network cost (in-zone, cross-zone, internet)
# - PV cost (per namespace)
# - Shared cost (control plane, monitoring, system pods)
# - Efficiency score (usage / request ratio)
```

### Building a Chargeback Report

```bash
#!/bin/bash
# chargeback-report.sh

echo "============================================="
echo "  KUBERNETES COST CHARGEBACK REPORT"
echo "  Period: $(date -d "-30 days" +%Y-%m-%d) to $(date +%Y-%m-%d)"
echo "  Cluster: eks-prod-east"
echo "============================================="

# Get node costs (total cluster cost)
NODE_COUNT=$(kubectl get nodes --no-headers | wc -l | tr -d ' ')
# Assume m6i.xlarge at $0.192/hr on-demand
HOURLY_COST=$(echo "$NODE_COUNT * 0.192" | bc)
MONTHLY_COST=$(echo "$HOURLY_COST * 730" | bc)

echo ""
echo "--- Cluster Cost Summary ---"
echo "  Nodes: $NODE_COUNT"
echo "  Estimated Monthly Cost: \$$(printf '%.2f' $MONTHLY_COST)"

echo ""
echo "--- Cost Allocation by Namespace ---"
echo "  (Based on resource requests)"

TOTAL_CPU_REQ=0
for NS in $(kubectl get namespaces -o jsonpath='{.items[*].metadata.name}' | tr ' ' '\n' | grep -v '^kube-' | grep -v '^default$'); do
  # Sum CPU requests in millicores
  CPU_REQ=$(kubectl get pods -n $NS -o json 2>/dev/null | \
    jq '[.items[].spec.containers[].resources.requests.cpu // "0" |
    if endswith("m") then rtrimstr("m") | tonumber
    elif . == "0" then 0
    else (tonumber * 1000) end] | add // 0')

  MEM_REQ=$(kubectl get pods -n $NS -o json 2>/dev/null | \
    jq '[.items[].spec.containers[].resources.requests.memory // "0" |
    if endswith("Mi") then rtrimstr("Mi") | tonumber
    elif endswith("Gi") then rtrimstr("Gi") | tonumber * 1024
    elif . == "0" then 0
    else 0 end] | add // 0')

  if [ "$CPU_REQ" -gt 0 ] || [ "$MEM_REQ" -gt 0 ]; then
    echo "  $NS: CPU=${CPU_REQ}m, Memory=${MEM_REQ}Mi"
  fi
done

echo ""
echo "--- Optimization Recommendations ---"

# Check for over-provisioned pods
echo "  Top over-provisioned pods (requests >> usage):"
kubectl top pods -A --no-headers 2>/dev/null | while read NS NAME CPU MEM; do
  # Compare actual usage to requests
  REQ_CPU=$(kubectl get pod $NAME -n $NS -o jsonpath='{.spec.containers[0].resources.requests.cpu}' 2>/dev/null)
  if [ -n "$REQ_CPU" ]; then
    echo "    $NS/$NAME: using $CPU (requested $REQ_CPU)"
  fi
done | head -10

echo ""
echo "============================================="
```

---

## The True Cost of Multi-Cloud

Most enterprises underestimate the true cost of multi-cloud because they only count compute and storage. The hidden costs are significant.

### Multi-Cloud Cost Model

```text
┌──────────────────────────────────────────────────────────────┐
│  TRUE COST OF MULTI-CLOUD                                      │
│                                                                │
│  VISIBLE COSTS (what the bill shows):                          │
│  ├── Compute (EC2, VMs, GCE)                    $5.0M/yr     │
│  ├── Storage (S3, Blob, GCS)                    $1.2M/yr     │
│  ├── Networking (VPN, DX, peering)              $0.8M/yr     │
│  └── Managed services (RDS, Cosmos, BigQuery)   $1.5M/yr     │
│                                              ─────────────    │
│                                    Visible:   $8.5M/yr       │
│                                                                │
│  HIDDEN COSTS (what does NOT appear on the bill):             │
│  ├── Platform team (12 extra engineers)         $2.4M/yr     │
│  ├── Training (3 clouds x certifications)       $0.06M/yr    │
│  ├── Tooling (multi-cloud monitoring, IAM)      $0.3M/yr     │
│  ├── Lost discounts (split spend = weaker EDPs) $0.5M/yr     │
│  ├── Data transfer between clouds               $0.4M/yr     │
│  ├── Compliance (audit 3 environments)          $0.15M/yr    │
│  └── Cognitive load (context switching)          Hard to      │
│                                                  quantify     │
│                                              ─────────────    │
│                                    Hidden:    $3.85M/yr      │
│                                                                │
│                                    TOTAL:     $12.35M/yr     │
│                                    Hidden costs = 45% of total│
└──────────────────────────────────────────────────────────────┘
```

### When Multi-Cloud Makes Financial Sense

| Scenario | Cost Justification |
| :--- | :--- |
| Best-of-breed services (GCP ML + AWS compute) | Productivity gains > multi-cloud overhead |
| Regulatory (data residency requiring specific provider) | Compliance cost of violation > multi-cloud cost |
| M&A (acquired company on different cloud) | Migration cost > ongoing multi-cloud cost (short-term) |
| Vendor negotiation leverage | Demonstrable multi-cloud capability reduces EDP rates |
| DR across providers (true zero-dependency) | Business continuity value > infrastructure duplication cost |

| Scenario | Cost Justification |
| :--- | :--- |
| "Avoiding vendor lock-in" (abstract fear) | No concrete savings, only added complexity |
| "Each team picks their own cloud" (no strategy) | Fragmentation without benefit |
| Political (CTO wants resume-building) | Cost center, not value driver |

---

## Right-Sizing Kubernetes Workloads

### Vertical Pod Autoscaler (VPA) for Recommendations

```yaml
# Install VPA and use it in recommendation-only mode
apiVersion: autoscaling.k8s.io/v1
kind: VerticalPodAutoscaler
metadata:
  name: payment-service-vpa
  namespace: payments
spec:
  targetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: payment-service
  updatePolicy:
    updateMode: "Off"  # Recommendation only, no auto-update
  resourcePolicy:
    containerPolicies:
      - containerName: payment-service
        minAllowed:
          cpu: 50m
          memory: 64Mi
        maxAllowed:
          cpu: "4"
          memory: 8Gi
```

```bash
# Read VPA recommendations
kubectl get vpa payment-service-vpa -n payments -o jsonpath='{.status.recommendation.containerRecommendations[0]}' | jq .
# Output:
# {
#   "containerName": "payment-service",
#   "lowerBound": {"cpu": "100m", "memory": "128Mi"},
#   "target": {"cpu": "250m", "memory": "384Mi"},
#   "upperBound": {"cpu": "800m", "memory": "1Gi"},
#   "uncappedTarget": {"cpu": "250m", "memory": "384Mi"}
# }
#
# If current requests are cpu: 2, memory: 4Gi
# VPA recommends cpu: 250m, memory: 384Mi
# Savings: 87.5% CPU, 90.6% memory
```

### Goldilocks: Dashboard for Right-Sizing

```bash
# Install Goldilocks (VPA-based right-sizing dashboard)
helm repo add fairwinds-stable https://charts.fairwinds.com/stable
helm install goldilocks fairwinds-stable/goldilocks \
  --namespace goldilocks --create-namespace

# Enable Goldilocks for a namespace
kubectl label namespace payments goldilocks.fairwinds.com/enabled=true

# Goldilocks creates VPA objects for every Deployment and provides
# a dashboard showing current requests vs recommended requests
# Dashboard: http://goldilocks-dashboard.goldilocks.svc:80
```

### Automated Right-Sizing Pipeline

```text
┌──────────────────────────────────────────────────────────────┐
│  RIGHT-SIZING PIPELINE                                         │
│                                                                │
│  Week 1: Deploy VPA in "Off" mode for all namespaces          │
│  ─────── Collect usage data                                    │
│                                                                │
│  Week 2-4: Analyze recommendations                             │
│  ─────────                                                     │
│  ┌────────────────────────────────────────────────┐           │
│  │  For each workload:                             │           │
│  │  Current: cpu=2, mem=4Gi                        │           │
│  │  VPA target: cpu=250m, mem=384Mi                │           │
│  │  Savings: $127/month per replica                │           │
│  │  Risk: Low (P95 usage well below target)        │           │
│  └────────────────────────────────────────────────┘           │
│                                                                │
│  Week 4: Apply right-sized requests in staging                │
│  ─────── Verify no OOM kills, no CPU throttling               │
│                                                                │
│  Week 5: Apply to production                                   │
│  ─────── Monitor for 1 week                                    │
│                                                                │
│  Ongoing: VPA in "Auto" mode for non-critical workloads       │
│           VPA in "Off" mode for critical (manual approval)    │
└──────────────────────────────────────────────────────────────┘
```

---

## Building a FinOps Culture

### The FinOps Maturity Model

| Stage | Characteristics | Actions |
| :--- | :--- | :--- |
| **Crawl** | No cost visibility. Teams do not know their spend. | Install OpenCost/Kubecost. Create basic dashboards. Tag resources with team/environment. |
| **Walk** | Teams see their costs. Basic optimization (Reserved Instances). | Implement chargeback reports. Set up anomaly alerts. Right-size top 20 workloads. |
| **Run** | Real-time cost awareness. Automated optimization. Cost is a design consideration. | Automated right-sizing. FinOps in CI/CD (cost estimate per PR). Cost goals per team. |

### FinOps Team Structure

```text
┌──────────────────────────────────────────────────────────────┐
│  FINOPS ORGANIZATIONAL MODEL                                   │
│                                                                │
│  ┌────────────────────────────────────────────┐              │
│  │  FinOps Team (Central, 2-4 people)         │              │
│  │  - FinOps practitioner / analyst            │              │
│  │  - Cloud cost engineer                      │              │
│  │  - Finance partner                          │              │
│  │                                              │              │
│  │  Owns: Tooling, reports, EDP negotiations   │              │
│  │  Does NOT own: Individual team optimization  │              │
│  └──────────┬─────────────────────────────────┘              │
│             │                                                 │
│    ┌────────┴───────────────────────────────────┐            │
│    │                                             │            │
│    │  FinOps Champions (1 per engineering team)  │            │
│    │  - Part-time role (10% of time)             │            │
│    │  - Attends monthly FinOps review            │            │
│    │  - Drives optimization within their team    │            │
│    │  - Presents cost trends at team standups    │            │
│    │                                             │            │
│    │  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐      │            │
│    │  │Pay-  │ │Ident-│ │Search│ │Plat- │      │            │
│    │  │ments │ │ity   │ │      │ │form  │      │            │
│    │  └──────┘ └──────┘ └──────┘ └──────┘      │            │
│    └─────────────────────────────────────────────┘            │
└──────────────────────────────────────────────────────────────┘
```

---

## Did You Know?

1. The average Kubernetes cluster runs at 11-15% CPU utilization and 25-35% memory utilization, according to Datadog's 2024 Container Report. This means enterprises are paying for 3-9x more compute than they use. The primary cause is not laziness -- it is fear of OOM kills and CPU throttling combined with the difficulty of predicting resource needs for microservices with variable traffic patterns. The Vertical Pod Autoscaler was specifically designed to solve this, but only 12% of organizations use it.

2. AWS data transfer pricing is the most complex cost category in cloud computing. There are at least 23 different data transfer pricing dimensions: intra-AZ, inter-AZ, inter-region, internet egress, VPN, Direct Connect, NAT Gateway, VPC peering, Transit Gateway, PrivateLink, CloudFront, S3 Transfer Acceleration, and more. A single API call from an EKS pod to an S3 bucket in a different AZ incurs 3 separate data transfer charges: NAT Gateway processing ($0.045/GB), inter-AZ transfer ($0.01/GB), and S3 request pricing. AWS intentionally makes this complex because data transfer is one of their highest-margin services.

3. Enterprise Discount Programs (EDPs) with AWS typically require a minimum commitment of $1 million per year. The discount starts at 5% for a 1-year $1M commitment and can reach 15% for a 5-year $100M+ commitment. However, the EDP discount is applied AFTER all other discounts (Reserved Instances, Savings Plans, Spot). This means the EDP is most valuable for on-demand spend that cannot be covered by other commitment mechanisms. Some enterprises have negotiated EDPs where the discount is applied to the TOTAL bill, but this requires significant leverage.

4. OpenCost, the CNCF sandbox project for Kubernetes cost allocation, was originally developed internally at Kubecost and open-sourced in 2022. It uses a clever algorithm to allocate shared node costs to individual pods: it calculates each pod's share of the node based on the maximum of (resource request, actual usage) for each resource dimension. This "max of request and usage" approach is considered the fairest model because it penalizes both over-requesting (wasting capacity) and over-consuming (using more than requested without paying for it).

---

## Common Mistakes

| Mistake | Why It Happens | How to Fix It |
| :--- | :--- | :--- |
| **No resource requests on pods** | Developers do not set requests. All pods are "best effort." Cost allocation is impossible. | Enforce requests via Kyverno/Gatekeeper admission policy. Pods without requests should be rejected. |
| **Reserved Instances purchased without analysis** | Finance buys RIs based on current spend snapshot without understanding utilization patterns. RIs go unused when workloads are right-sized. | Analyze 90-day usage patterns before purchasing. Buy RIs for the FLOOR of usage, not the ceiling. Use Savings Plans for flexibility. |
| **Chargeback without context** | Teams receive a bill but cannot understand why it increased. No breakdown by service, workload, or time period. | Use OpenCost/Kubecost with per-service granularity. Show cost per deployment, not just per namespace. Include efficiency metrics alongside costs. |
| **Spot instances for stateful workloads** | Over-enthusiastic cost optimization. "Everything on Spot saves 70%." Then Spot reclamation takes down the database. | Use Spot only for stateless, fault-tolerant workloads (batch jobs, stateless web servers with multiple replicas). Never for databases, single-replica services, or services with long startup times. |
| **Ignoring data transfer costs** | Compute dominates the bill, so data transfer is overlooked. Then it grows to 15-25% of total spend. | Monitor data transfer costs separately. Use VPC endpoints for AWS service communication. Colocate high-traffic services in the same AZ. Use S3 gateway endpoints (free). |
| **Cost optimization as a one-time project** | "We did a right-sizing exercise last quarter." But workloads change constantly. | Treat FinOps as a continuous practice, not a project. Monthly cost reviews. Automated anomaly detection. VPA running continuously. |
| **No team ownership of costs** | Cloud bill goes to "IT department." No team knows or cares about their cost contribution. | Implement chargeback or showback. Every team sees their monthly cost. Set cost efficiency goals alongside delivery goals. |
| **Multi-cloud for negotiation without tracking** | "We will use Azure to negotiate with AWS." But the Azure spend is never large enough to matter, and the overhead of managing two clouds exceeds any discount gained. | If using multi-cloud for negotiation leverage, the secondary cloud spend must be credible (>20% of total). Otherwise, the leverage argument is hollow and the multi-cloud overhead is pure waste. |

---

## Quiz

<details>
<summary>Question 1: Your EKS cluster has 20 m6i.xlarge nodes running 24/7. Average CPU utilization is 14%. What is the estimated monthly waste, and how would you reduce it?</summary>

Each m6i.xlarge costs $0.192/hr = $140/month. 20 nodes = $2,800/month. At 14% CPU utilization, approximately 86% of compute is wasted. However, you cannot simply remove 86% of nodes because memory utilization may be higher, and you need headroom for traffic spikes.

A realistic optimization: (1) Right-size pods using VPA recommendations -- this typically increases effective utilization from 14% to 35-45%. (2) With 3x better packing efficiency, reduce from 20 nodes to 8-10 nodes. (3) Apply Savings Plans (37% discount) to the remaining nodes. Result: 10 nodes at $0.121/hr = $883/month. Savings: $2,800 - $883 = $1,917/month = $23,000/year.

Additional optimization: scale non-production clusters to zero outside business hours (12 hours/day, 5 days/week = 37% of hours). If 8 of the 20 nodes were non-production, this saves another $500/month.
</details>

<details>
<summary>Question 2: Explain the difference between request-based and usage-based chargeback for Kubernetes. Which is more fair?</summary>

**Request-based** chargeback charges teams for the CPU and memory they *request* in their pod specs, regardless of actual usage. If a team requests 4 CPU but uses only 0.5 CPU, they pay for 4 CPU. This is simple to calculate but penalizes teams that over-request (which is most teams, because over-requesting is the safe default).

**Usage-based** chargeback charges teams for the CPU and memory they actually consume (measured via metrics). If a team uses 0.5 CPU, they pay for 0.5 CPU. This is more fair but harder to calculate, requires reliable metering, and has a problem: it does not account for the capacity that was *reserved* by the requests -- capacity that other pods could not use even though it was idle.

**The fairest model is hybrid**: charge for max(request, usage) per resource dimension, plus a proportional share of shared infrastructure costs (control plane, monitoring, system pods). This incentivizes teams to right-size their requests (because over-requesting is expensive) while also capturing actual consumption spikes.
</details>

<details>
<summary>Question 3: Your company spends $5M/year on AWS and $2M/year on Azure. A consultant recommends consolidating to one cloud for "negotiation leverage." Should you consolidate?</summary>

It depends on **why** you are on two clouds. If the split is strategic (Azure for specific services like Active Directory integration, AWS for compute and EKS), the two-cloud approach may deliver more value than the consolidation savings. Consolidating to $7M on AWS might improve your EDP discount from 8% to 10%, saving $140K/year. But if the Azure workloads do not migrate well to AWS equivalents, migration costs ($500K-1M typically) and ongoing friction outweigh the discount.

However, if the split is accidental (a team chose Azure without strategic justification), consolidation is worth pursuing. The hidden costs of multi-cloud (extra engineers, training, tooling) at $5M+$2M scale are roughly $800K-1.5M/year. Consolidating eliminates these hidden costs AND improves negotiation leverage. The decision framework: calculate total cost of ownership (TCO) for both scenarios including hidden costs. If multi-cloud TCO exceeds single-cloud TCO by more than the strategic value of the second cloud, consolidate.
</details>

<details>
<summary>Question 4: What is the difference between Savings Plans and Reserved Instances? When would you choose each?</summary>

**Reserved Instances (RIs)** commit you to a specific instance type in a specific region for 1 or 3 years. You get 40-60% discount but lose flexibility -- if you change instance types or regions, the RI does not apply. **Savings Plans** commit you to a dollar amount of compute per hour (e.g., "$10/hr of compute") for 1 or 3 years. They apply across instance types, sizes, and (for Compute Savings Plans) across regions. Discount is 30-40%.

Choose **Savings Plans** when: your workloads change frequently (different instance types, different regions), you are early in your cloud journey and still optimizing, or you use multiple instance families. Choose **RIs** when: your workloads are stable and predictable (same instance type for years), you want the maximum possible discount, or you use specific high-cost instances (like GPU instances) that benefit most from the deeper RI discount.

For Kubernetes specifically, Savings Plans are usually better because cluster autoscalers and node groups may change instance types as availability and pricing change.
</details>

<details>
<summary>Question 5: Cross-AZ data transfer costs $0.01/GB. Your cluster has 200 services averaging 50 Mbps of inter-service traffic. Estimate the monthly data transfer cost.</summary>

50 Mbps per service = 50/8 = 6.25 MB/s per service. With 200 services, total internal traffic is approximately 200 * 6.25 = 1,250 MB/s (this is bidirectional, but let us use the sender's perspective). In a 3-AZ cluster with round-robin load balancing, approximately 2/3 of traffic crosses AZ boundaries (requests go to pods in other AZs).

Cross-AZ traffic: 1,250 MB/s * 0.67 = 837.5 MB/s = 837.5 * 86,400 * 30 / 1,000,000 = ~2,170 TB/month. At $0.01/GB = $10/TB: 2,170 * $10 = **$21,700/month** or **$260,000/year** in cross-AZ data transfer alone.

Mitigation: (1) Enable topology-aware routing (Kubernetes topologySpreadConstraints + Service topology hints) to prefer same-AZ endpoints. This can reduce cross-AZ traffic by 60-80%. (2) Colocate high-traffic service pairs in the same AZ. (3) Use a service mesh with locality-aware load balancing. Realistically, reducing cross-AZ traffic by 70% saves approximately $182,000/year.
</details>

<details>
<summary>Question 6: How do you build a FinOps culture where engineering teams care about costs?</summary>

Building a FinOps culture requires four elements: (1) **Visibility**: Every team must see their costs. Install OpenCost/Kubecost and create dashboards visible to all engineers. Share monthly cost reports in team channels. If teams cannot see their costs, they cannot care about them. (2) **Accountability**: Assign cost ownership to teams through chargeback or showback. Include cost efficiency as a metric in team health dashboards alongside latency and error rate. (3) **Incentives**: Create positive incentives for optimization. Celebrate teams that reduce waste. Give teams a portion of savings to reinvest (e.g., "save $10K/month, get $2K/month for new tools or training"). (4) **Education**: Train engineers on cloud pricing. Most engineers have never seen a cloud bill. Lunch-and-learn sessions on "how to read your cost dashboard" and "why that LoadBalancer costs $50/month" build awareness. The FinOps Foundation recommends a "FinOps Champion" program: one engineer per team who attends monthly cost reviews and brings insights back to the team.
</details>

---

## Hands-On Exercise: Build a Kubernetes Cost Dashboard

In this exercise, you will deploy a cost analysis environment, calculate resource efficiency, build a chargeback report, and create an optimization plan.

### Task 1: Create the Cost Lab Cluster with Workloads

<details>
<summary>Solution</summary>

```bash
kind create cluster --name finops-lab

# Create team namespaces with cost labels
for TEAM in payments identity search platform; do
  cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Namespace
metadata:
  name: $TEAM
  labels:
    team: $TEAM
    cost-center: "cc-${TEAM}"
EOF
done

# Deploy workloads with varying resource requests (some over-provisioned)
cat <<'EOF' | kubectl apply -f -
# Payments: reasonably sized
apiVersion: apps/v1
kind: Deployment
metadata:
  name: payment-api
  namespace: payments
  labels:
    app: payment-api
spec:
  replicas: 3
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
          image: nginx:1.27.3
          resources:
            requests:
              cpu: 200m
              memory: 256Mi
            limits:
              cpu: 500m
              memory: 512Mi
---
# Identity: massively over-provisioned
apiVersion: apps/v1
kind: Deployment
metadata:
  name: auth-service
  namespace: identity
  labels:
    app: auth-service
spec:
  replicas: 5
  selector:
    matchLabels:
      app: auth-service
  template:
    metadata:
      labels:
        app: auth-service
    spec:
      containers:
        - name: auth
          image: nginx:1.27.3
          resources:
            requests:
              cpu: "2"
              memory: 4Gi
            limits:
              cpu: "4"
              memory: 8Gi
---
# Search: moderately over-provisioned
apiVersion: apps/v1
kind: Deployment
metadata:
  name: search-engine
  namespace: search
  labels:
    app: search-engine
spec:
  replicas: 2
  selector:
    matchLabels:
      app: search-engine
  template:
    metadata:
      labels:
        app: search-engine
    spec:
      containers:
        - name: search
          image: nginx:1.27.3
          resources:
            requests:
              cpu: 500m
              memory: 1Gi
            limits:
              cpu: "1"
              memory: 2Gi
---
# Platform: minimal
apiVersion: apps/v1
kind: Deployment
metadata:
  name: monitoring-agent
  namespace: platform
  labels:
    app: monitoring-agent
spec:
  replicas: 1
  selector:
    matchLabels:
      app: monitoring-agent
  template:
    metadata:
      labels:
        app: monitoring-agent
    spec:
      containers:
        - name: agent
          image: nginx:1.27.3
          resources:
            requests:
              cpu: 100m
              memory: 128Mi
            limits:
              cpu: 200m
              memory: 256Mi
EOF

# Wait for all pods to be ready
for NS in payments identity search platform; do
  kubectl wait --for=condition=ready pod -l app -n $NS --timeout=60s 2>/dev/null || true
done

echo "Workloads deployed. Some are intentionally over-provisioned for the exercise."
```

</details>

### Task 2: Analyze Resource Efficiency

<details>
<summary>Solution</summary>

```bash
cat <<'SCRIPT' > /tmp/efficiency-report.sh
#!/bin/bash
echo "============================================="
echo "  RESOURCE EFFICIENCY ANALYSIS"
echo "  $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "============================================="

# Assume m6i.xlarge: 4 vCPU, 16GB RAM, $0.192/hr
NODE_CPU_MILLIS=4000
NODE_MEM_MI=16384
NODE_HOURLY_COST=0.192
NODE_MONTHLY_COST=$(echo "$NODE_HOURLY_COST * 730" | bc)
NODE_COUNT=$(kubectl get nodes --no-headers | wc -l | tr -d ' ')

echo ""
echo "--- Cluster Resources ---"
TOTAL_CPU=$((NODE_COUNT * NODE_CPU_MILLIS))
TOTAL_MEM=$((NODE_COUNT * NODE_MEM_MI))
echo "  Nodes: $NODE_COUNT"
echo "  Total CPU: ${TOTAL_CPU}m"
echo "  Total Memory: ${TOTAL_MEM}Mi"
echo "  Monthly Cost: \$$(echo "$NODE_COUNT * $NODE_MONTHLY_COST" | bc)"

echo ""
echo "--- Per-Namespace Resource Analysis ---"
printf "  %-15s %-10s %-12s %-10s %-12s\n" "NAMESPACE" "CPU_REQ" "MEM_REQ" "REPLICAS" "EST_MONTHLY"

TOTAL_NS_CPU=0
TOTAL_NS_MEM=0

for NS in payments identity search platform; do
  CPU_REQ=$(kubectl get pods -n $NS -o json | \
    jq '[.items[].spec.containers[].resources.requests.cpu // "0" |
    if endswith("m") then rtrimstr("m") | tonumber
    elif . == "0" then 0
    else (tonumber * 1000) end] | add // 0')

  MEM_REQ=$(kubectl get pods -n $NS -o json | \
    jq '[.items[].spec.containers[].resources.requests.memory // "0" |
    if endswith("Mi") then rtrimstr("Mi") | tonumber
    elif endswith("Gi") then rtrimstr("Gi") | tonumber * 1024
    elif . == "0" then 0
    else 0 end] | add // 0')

  REPLICAS=$(kubectl get pods -n $NS --no-headers | wc -l | tr -d ' ')

  # Estimate cost based on proportion of node resources
  CPU_FRACTION=$(echo "scale=4; $CPU_REQ / $TOTAL_CPU" | bc)
  MEM_FRACTION=$(echo "scale=4; $MEM_REQ / $TOTAL_MEM" | bc)
  # Use the larger fraction (the binding constraint)
  if [ "$(echo "$CPU_FRACTION > $MEM_FRACTION" | bc)" -eq 1 ]; then
    COST_FRACTION=$CPU_FRACTION
  else
    COST_FRACTION=$MEM_FRACTION
  fi
  MONTHLY=$(echo "scale=2; $COST_FRACTION * $NODE_COUNT * $NODE_MONTHLY_COST" | bc)

  printf "  %-15s %-10s %-12s %-10s \$%-11s\n" "$NS" "${CPU_REQ}m" "${MEM_REQ}Mi" "$REPLICAS" "$MONTHLY"

  TOTAL_NS_CPU=$((TOTAL_NS_CPU + CPU_REQ))
  TOTAL_NS_MEM=$((TOTAL_NS_MEM + MEM_REQ))
done

echo ""
echo "--- Cluster Efficiency ---"
CPU_UTIL=$(echo "scale=1; $TOTAL_NS_CPU * 100 / $TOTAL_CPU" | bc)
MEM_UTIL=$(echo "scale=1; $TOTAL_NS_MEM * 100 / $TOTAL_MEM" | bc)
echo "  CPU Request Utilization: ${CPU_UTIL}%"
echo "  Memory Request Utilization: ${MEM_UTIL}%"
echo "  (Note: This is request-based. Actual usage is likely much lower.)"

echo ""
echo "--- Optimization Recommendations ---"
# Identity team analysis
IDENTITY_CPU=$(kubectl get pods -n identity -o json | \
  jq '[.items[].spec.containers[].resources.requests.cpu // "0" |
  if endswith("m") then rtrimstr("m") | tonumber
  else (tonumber * 1000) end] | add // 0')

if [ "$IDENTITY_CPU" -gt 5000 ]; then
  echo "  [HIGH] identity namespace: ${IDENTITY_CPU}m CPU requested"
  echo "         5 replicas x 2000m = 10000m. Likely needs right-sizing."
  echo "         Recommendation: Deploy VPA, analyze for 2 weeks, likely reduce to 200-500m per pod."
  SAVINGS=$(echo "scale=0; ($IDENTITY_CPU - 2500) * $NODE_MONTHLY_COST / $NODE_CPU_MILLIS" | bc)
  echo "         Estimated savings: ~\$${SAVINGS}/month"
fi

echo ""
echo "============================================="
SCRIPT

chmod +x /tmp/efficiency-report.sh
bash /tmp/efficiency-report.sh
```

</details>

### Task 3: Build the Chargeback Report

<details>
<summary>Solution</summary>

```bash
cat <<'SCRIPT' > /tmp/chargeback-report.sh
#!/bin/bash
NODE_HOURLY=0.192
NODE_MONTHLY=$(echo "$NODE_HOURLY * 730" | bc)
NODE_COUNT=$(kubectl get nodes --no-headers | wc -l | tr -d ' ')
CLUSTER_MONTHLY=$(echo "$NODE_COUNT * $NODE_MONTHLY" | bc)
NODE_CPU=4000
NODE_MEM=16384
TOTAL_CPU=$((NODE_COUNT * NODE_CPU))
TOTAL_MEM=$((NODE_COUNT * NODE_MEM))

echo "============================================="
echo "  MONTHLY CHARGEBACK REPORT"
echo "  Cluster: finops-lab"
echo "  Period: $(date +%B' '%Y)"
echo "============================================="
echo ""
echo "  Total Cluster Cost: \$$CLUSTER_MONTHLY"
echo ""
printf "  %-15s | %-8s | %-10s | %-8s | %-10s | %-8s\n" \
  "TEAM" "CPU_REQ" "MEM_REQ" "CPU%" "MEM%" "CHARGE"
printf "  %-15s-+-%-8s-+-%-10s-+-%-8s-+-%-10s-+-%-8s\n" \
  "---------------" "--------" "----------" "--------" "----------" "--------"

TOTAL_CHARGE=0
for NS in payments identity search platform; do
  CPU_REQ=$(kubectl get pods -n $NS -o json | \
    jq '[.items[].spec.containers[].resources.requests.cpu // "0" |
    if endswith("m") then rtrimstr("m") | tonumber
    elif . == "0" then 0
    else (tonumber * 1000) end] | add // 0')

  MEM_REQ=$(kubectl get pods -n $NS -o json | \
    jq '[.items[].spec.containers[].resources.requests.memory // "0" |
    if endswith("Mi") then rtrimstr("Mi") | tonumber
    elif endswith("Gi") then rtrimstr("Gi") | tonumber * 1024
    elif . == "0" then 0
    else 0 end] | add // 0')

  CPU_PCT=$(echo "scale=1; $CPU_REQ * 100 / $TOTAL_CPU" | bc)
  MEM_PCT=$(echo "scale=1; $MEM_REQ * 100 / $TOTAL_MEM" | bc)

  # Charge based on max(CPU%, MEM%) of cluster cost
  if [ "$(echo "$CPU_PCT > $MEM_PCT" | bc)" -eq 1 ]; then
    MAX_PCT=$CPU_PCT
  else
    MAX_PCT=$MEM_PCT
  fi
  CHARGE=$(echo "scale=2; $MAX_PCT * $CLUSTER_MONTHLY / 100" | bc)
  TOTAL_CHARGE=$(echo "scale=2; $TOTAL_CHARGE + $CHARGE" | bc)

  printf "  %-15s | %-8s | %-10s | %-7s%% | %-9s%% | \$%-7s\n" \
    "$NS" "${CPU_REQ}m" "${MEM_REQ}Mi" "$CPU_PCT" "$MEM_PCT" "$CHARGE"
done

# Shared/unallocated costs
UNALLOCATED=$(echo "scale=2; $CLUSTER_MONTHLY - $TOTAL_CHARGE" | bc)
printf "  %-15s | %-8s | %-10s | %-8s | %-10s | \$%-7s\n" \
  "shared/system" "-" "-" "-" "-" "$UNALLOCATED"

echo ""
echo "  Total Allocated: \$$TOTAL_CHARGE"
echo "  Shared/System:   \$$UNALLOCATED"
echo "  Cluster Total:   \$$CLUSTER_MONTHLY"
echo ""
echo "============================================="
SCRIPT

chmod +x /tmp/chargeback-report.sh
bash /tmp/chargeback-report.sh
```

</details>

### Task 4: Create an Optimization Plan

<details>
<summary>Solution</summary>

```bash
cat <<'SCRIPT' > /tmp/optimization-plan.sh
#!/bin/bash
echo "============================================="
echo "  COST OPTIMIZATION PLAN"
echo "  Generated: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "============================================="

echo ""
echo "--- Priority 1: Right-Size Identity Namespace ---"
echo "  Current: 5 replicas x 2 CPU, 4Gi = 10 CPU, 20Gi total"
echo "  Nginx containers typically use <100m CPU, <128Mi memory"
echo "  Recommended: 3 replicas x 200m CPU, 256Mi"
echo "  Action: Deploy VPA in Off mode, collect 2 weeks data"
echo "  Estimated savings: ~80% of identity namespace cost"

echo ""
echo "--- Priority 2: Right-Size Search Namespace ---"
echo "  Current: 2 replicas x 500m CPU, 1Gi"
echo "  Recommended: 2 replicas x 200m CPU, 256Mi"
echo "  Action: Apply VPA recommendations"
echo "  Estimated savings: ~60% of search namespace cost"

echo ""
echo "--- Priority 3: Cluster Right-Sizing ---"
echo "  After pod right-sizing, total cluster resource requests will decrease"
echo "  This enables node count reduction via Cluster Autoscaler"
echo "  Current nodes: $(kubectl get nodes --no-headers | wc -l | tr -d ' ')"
echo "  Estimated nodes after optimization: 1-2 (for kind lab)"

echo ""
echo "--- Priority 4: Commitment Discounts ---"
echo "  After right-sizing stabilizes (4 weeks), purchase:"
echo "  - Compute Savings Plan for 60% of steady-state compute"
echo "  - Remaining 40% on-demand for flexibility"
echo "  Estimated additional savings: 25-37% on committed portion"

echo ""
echo "--- Implementation Timeline ---"
echo "  Week 1: Deploy VPA in Off mode for all namespaces"
echo "  Week 2-3: Collect usage data"
echo "  Week 4: Apply right-sized requests in staging"
echo "  Week 5: Apply to production, monitor"
echo "  Week 6: Reduce node count, verify stability"
echo "  Week 8: Purchase Savings Plans based on new baseline"
echo ""
echo "============================================="
SCRIPT

chmod +x /tmp/optimization-plan.sh
bash /tmp/optimization-plan.sh
```

</details>

### Task 5: Apply Right-Sizing and Measure Impact

<details>
<summary>Solution</summary>

```bash
echo "=== BEFORE OPTIMIZATION ==="
echo "Identity namespace resources:"
kubectl get pods -n identity -o custom-columns=\
NAME:.metadata.name,\
CPU_REQ:.spec.containers[0].resources.requests.cpu,\
MEM_REQ:.spec.containers[0].resources.requests.memory

# Apply right-sized resources
kubectl patch deployment auth-service -n identity --type=json \
  -p='[
    {"op":"replace","path":"/spec/replicas","value":3},
    {"op":"replace","path":"/spec/template/spec/containers/0/resources/requests/cpu","value":"200m"},
    {"op":"replace","path":"/spec/template/spec/containers/0/resources/requests/memory","value":"256Mi"},
    {"op":"replace","path":"/spec/template/spec/containers/0/resources/limits/cpu","value":"500m"},
    {"op":"replace","path":"/spec/template/spec/containers/0/resources/limits/memory","value":"512Mi"}
  ]'

kubectl patch deployment search-engine -n search --type=json \
  -p='[
    {"op":"replace","path":"/spec/template/spec/containers/0/resources/requests/cpu","value":"200m"},
    {"op":"replace","path":"/spec/template/spec/containers/0/resources/requests/memory","value":"256Mi"},
    {"op":"replace","path":"/spec/template/spec/containers/0/resources/limits/cpu","value":"500m"},
    {"op":"replace","path":"/spec/template/spec/containers/0/resources/limits/memory","value":"512Mi"}
  ]'

# Wait for rollout
kubectl rollout status deployment/auth-service -n identity --timeout=60s
kubectl rollout status deployment/search-engine -n search --timeout=60s

echo ""
echo "=== AFTER OPTIMIZATION ==="
echo "Identity namespace resources:"
kubectl get pods -n identity -o custom-columns=\
NAME:.metadata.name,\
CPU_REQ:.spec.containers[0].resources.requests.cpu,\
MEM_REQ:.spec.containers[0].resources.requests.memory

echo ""
echo "=== IMPACT: Re-running chargeback report ==="
bash /tmp/chargeback-report.sh
```

</details>

### Clean Up

```bash
kind delete cluster --name finops-lab
rm /tmp/efficiency-report.sh /tmp/chargeback-report.sh /tmp/optimization-plan.sh
```

### Success Criteria

- [ ] I deployed workloads with varying resource profiles (some intentionally over-provisioned)
- [ ] I analyzed resource efficiency and identified over-provisioned namespaces
- [ ] I built a chargeback report showing cost allocation per team
- [ ] I created a prioritized optimization plan with timeline
- [ ] I applied right-sizing to over-provisioned workloads and measured the impact
- [ ] I can explain the difference between request-based and usage-based chargeback
- [ ] I can describe the layered discount model (EDP + RI/SP + Spot + right-sizing)

---

## Next Module

Congratulations on completing the Enterprise & Hybrid phase of the Cloud Deep Dive track. You now have the knowledge to design, secure, and optimize enterprise Kubernetes architectures across cloud and on-premises environments. Return to the [Enterprise & Hybrid README]() to review the full phase and explore advanced topics.
