---
title: "Module 1.4: TCO & Budget Planning"
slug: on-premises/planning/module-1.4-tco-budget
sidebar:
  order: 5
---

> **Complexity**: `[MEDIUM]` | Time: 45 minutes
>
> **Prerequisites**: [Module 1.2: Server Sizing](module-1.2-server-sizing/), [FinOps Fundamentals](../../k8s/finops/module-1-finops-fundamentals/)

---

## Why This Module Matters

In 2023, a logistics company presented their board with a plan to move from AWS to on-premises Kubernetes. The infrastructure team calculated hardware costs: $380,000 for servers, networking, and storage. The CFO approved. Twelve months later, the actual spend was $1.2 million. The team had not budgeted for colocation fees ($72K/year), redundant internet circuits ($36K/year), a part-time facilities manager ($45K/year), two additional engineers ($350K/year), hardware maintenance contracts ($38K/year), or the $180K in professional services for the initial buildout. The "savings" over cloud disappeared entirely.

The infrastructure team was not incompetent — they were engineers, not financial modelers. They calculated what they knew (hardware) and missed what they did not (everything else). This module teaches you to build a complete TCO model so your budget reflects reality.

> **The Iceberg Analogy**
>
> Hardware cost is the tip of the iceberg — visible and easy to calculate. Below the waterline: staffing, power, cooling, colocation, networking, maintenance contracts, licenses, insurance, and opportunity cost. The submerged portion is typically 3-5x the hardware cost.

---

## What You'll Learn

- The complete cost taxonomy for on-premises Kubernetes
- How to build a 3-year and 5-year TCO model
- CapEx vs OpEx trade-offs and financial implications
- Power and cooling calculations
- Staffing models and the cost of expertise
- Cloud breakeven analysis methodology

---

## Cost Taxonomy

### Capital Expenditure (CapEx)

One-time costs that are depreciated over the asset's life (typically 3-5 years):

```
┌─────────────────────────────────────────────────────────────┐
│                    CAPEX COMPONENTS                          │
│                                                               │
│  COMPUTE                                                     │
│  ├── Servers (CPU, RAM, NVMe)          $8K-25K per node     │
│  ├── GPU accelerators (if needed)      $10K-40K per GPU     │
│  └── Spare parts (drives, PSUs, RAM)   5-10% of server cost│
│                                                               │
│  NETWORKING                                                  │
│  ├── Spine switches (100GbE)           $15K-40K each        │
│  ├── ToR switches (25GbE)              $3K-8K each          │
│  ├── Management switches (1GbE)        $500-2K each         │
│  ├── Cabling (fiber + copper)          $2K-5K per rack      │
│  ├── Firewalls / load balancers        $5K-50K              │
│  └── Out-of-band management network    $1K-3K              │
│                                                               │
│  STORAGE (if not using server-local)                        │
│  ├── SAN/NAS (enterprise)              $50K-500K            │
│  └── Dedicated Ceph nodes              $10K-20K each        │
│                                                               │
│  INFRASTRUCTURE                                              │
│  ├── Racks (42U)                       $1K-3K each          │
│  ├── PDUs (redundant A+B)             $500-2K per rack      │
│  ├── UPS (if not colo-provided)        $5K-20K             │
│  └── KVM / console access              $1K-5K              │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### Operating Expenditure (OpEx)

Recurring monthly or annual costs:

```
┌─────────────────────────────────────────────────────────────┐
│                    OPEX COMPONENTS                           │
│                                                               │
│  FACILITY (monthly)                                          │
│  ├── Colocation (per rack)             $800-2,500/mo        │
│  ├── Power (per kW)                    $80-150/kW/mo        │
│  ├── Cooling (included in colo or      ~40% of power cost   │
│  │   separate HVAC cost)                                     │
│  ├── Internet circuits (redundant)     $500-3,000/mo        │
│  └── Cross-connects to other cages     $200-500/mo each     │
│                                                               │
│  STAFFING (annual, fully loaded)                             │
│  ├── Infrastructure engineer           $150K-220K           │
│  ├── Network engineer (shared)         $70K-110K (0.5 FTE)  │
│  ├── Security engineer (shared)        $80K-120K (0.5 FTE)  │
│  └── On-call compensation              $15K-30K/person/yr   │
│                                                               │
│  MAINTENANCE (annual)                                        │
│  ├── Hardware support contract          3-5% of hardware    │
│  │   (Dell ProSupport, HPE Pointnext)  cost per year        │
│  ├── Software licenses                 $0-50K (RHEL, etc.)  │
│  └── Professional services             $20K-100K (one-time) │
│                                                               │
│  HIDDEN COSTS                                                │
│  ├── Opportunity cost (eng not         Hard to quantify     │
│  │   building product)                                       │
│  ├── Insurance (equipment)             $2K-10K/yr           │
│  ├── Compliance/audit                  $10K-50K/yr          │
│  └── Training & conferences            $5K-15K/yr           │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

---

## Power and Cooling Calculations

### Per-Server Power

```
┌─────────────────────────────────────────────────────────────┐
│                 POWER ESTIMATION                             │
│                                                               │
│  Component           Idle Power    Full Load                 │
│  ─────────────────   ──────────   ─────────                 │
│  Dual Xeon/EPYC      120W         500-600W                  │
│  RAM (512GB DDR5)    20W          40W                       │
│  NVMe (4x 3.84TB)   8W           20W                       │
│  NICs (2x 25GbE)    5W           15W                       │
│  Fans + PSU loss     30W          60W                       │
│  ─────────────────   ──────────   ─────────                 │
│  Total per server    ~180W        ~700W                     │
│                                                               │
│  GPU server (4x A100): add 1,200W at full load              │
│                                                               │
│  Typical K8s utilization: 40-60% = ~400W average            │
│                                                               │
│  Per rack (8 servers):                                       │
│    Average: 8 x 400W = 3.2 kW                              │
│    Peak: 8 x 700W = 5.6 kW                                 │
│                                                               │
│  Monthly power cost:                                         │
│    3.2 kW x 730 hours x $0.12/kWh = $280/month             │
│    Plus cooling (PUE 1.4): $280 x 1.4 = $392/month         │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### PUE (Power Usage Effectiveness)

```
Total facility power
PUE = ─────────────────
      IT equipment power

PUE 1.0 = perfect (impossible)
PUE 1.2 = excellent (hyperscaler DCs)
PUE 1.4 = good (modern colo)
PUE 1.6 = average (older facility)
PUE 2.0 = poor (needs upgrade)

Your effective power cost = IT power cost × PUE
```

---

## Staffing Models

### The Nodes-Per-Engineer Ratio

| Automation Level | Nodes per Engineer | Tools |
|-----------------|-------------------|-------|
| Manual (kubectl + scripts) | 20-30 | Shell scripts, manual provisioning |
| Partially automated | 50-80 | Ansible, Terraform, basic CI/CD |
| Fully automated | 100-200 | Cluster API, GitOps, machine health checks |
| Platform team at scale | 200-500 | Custom controllers, self-service portal |

```
┌─────────────────────────────────────────────────────────────┐
│               STAFFING COST MODEL                            │
│                                                               │
│  Cluster Size    Engineers    Annual Staff Cost               │
│  ────────────    ─────────   ─────────────────               │
│  20 nodes        2 (shared)  $200K (0.5 FTE dedicated)      │
│  50 nodes        2           $350K                           │
│  100 nodes       3           $525K                           │
│  200 nodes       4           $700K                           │
│  500 nodes       6-8         $1.2M                           │
│  1000+ nodes     10-15       $2M+                            │
│                                                               │
│  Note: "shared" means engineers also do other work.          │
│  Fully loaded cost = salary × 1.3-1.5 (benefits, tax, etc.)│
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

---

## 3-Year TCO Model

### Template

```
┌─────────────────────────────────────────────────────────────┐
│   3-YEAR TCO MODEL (100 K8s nodes on 12 bare-metal servers) │
│   (Each server: 64 cores, 256GB → ~8 K8s nodes per server)  │
│                                                               │
│  YEAR 0 (SETUP)                                              │
│  ────────────────────────────────────────                    │
│  Servers (12 x $15K)                    $180,000            │
│  Networking (switches + cabling)         $45,000            │
│  Storage (Ceph nodes, 3 x $12K)         $36,000            │
│  Racks + PDUs                            $8,000             │
│  Professional services (buildout)        $60,000            │
│  ────────────────────────────────────────                    │
│  CapEx subtotal                         $329,000            │
│                                                               │
│  ANNUAL OPEX                                                 │
│  ────────────────────────────────────────                    │
│  Colocation (3 racks)                    $54,000            │
│  Power + cooling (7kW IT x PUE 1.4      $10,300            │
│    x $0.12/kWh x 8,760 hrs)                                 │
│  Internet (2x circuits)                  $24,000            │
│  Staffing (3 engineers)                 $525,000            │
│  Maintenance contracts                   $16,500            │
│  Software licenses                       $12,000            │
│  Insurance + compliance                  $15,000            │
│  ────────────────────────────────────────                    │
│  OpEx subtotal (per year)              $656,800             │
│                                                               │
│  3-YEAR TOTAL                                                │
│  ────────────────────────────────────────                    │
│  CapEx                                  $329,000            │
│  OpEx (3 years)                       $1,970,400            │
│  ────────────────────────────────────────                    │
│  TOTAL                                $2,299,400            │
│  Per month                               $63,872            │
│                                                               │
│  CLOUD COMPARISON (100 x m6i.2xlarge @ $0.384/hr)           │
│  ────────────────────────────────────────                    │
│  On-demand: 100 x $280/mo           $1,008,000 (3 yr)      │
│  1-year RI (no upfront, ~35% off)      $655,000 (3 yr)     │
│  3-year RI (all upfront, ~55% off)     $454,000 (3 yr)     │
│  + EKS fee + storage + data xfer     ~$200,000 (3 yr)      │
│                                                               │
│  VERDICT at 100 nodes (12 servers):                          │
│  Cloud (3yr RI + extras) ≈ $650K vs On-prem ≈ $2.3M        │
│  → Cloud wins decisively (staffing dominates on-prem)       │
│                                                               │
│  Breakeven: ~300-500 nodes where staffing amortizes         │
│  and cloud egress/storage costs grow linearly                │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

---

## Did You Know?

- **Colocation pricing varies 3-4x by market.** A full rack in Northern Virginia (Ashburn) costs ~$800-1,200/month. The same rack in London costs ~$1,500-2,500/month. In Singapore, it can exceed $3,000/month. Location choice has a massive TCO impact.

- **Power costs are the fastest-growing component** of on-prem TCO. Electricity prices have increased 20-40% in many markets since 2020. GPU servers make this worse — a rack of 8 GPU servers can draw 15-20 kW, costing $1,500-3,000/month in power alone.

- **Hardware refresh cycles are getting longer.** In 2010, servers were refreshed every 3 years. Today, 5-year cycles are common because modern servers (DDR5, PCIe Gen5) depreciate more slowly and firmware updates extend useful life. This improves the TCO case for on-prem.

- **The biggest hidden cost is not hardware, it is hiring.** Finding engineers who can operate bare metal Kubernetes (Linux, networking, storage, hardware troubleshooting) takes 3-6 months and costs $20K-40K in recruiting fees per hire. Many organizations underestimate this lead time.

---

## Common Mistakes

| Mistake | Problem | Solution |
|---------|---------|----------|
| Hardware-only budgeting | Actual cost is 3-5x hardware | Use the full cost taxonomy |
| Forgetting PUE | Power bill is 1.2-1.6x raw IT power | Multiply power by facility PUE |
| Linear staffing model | Assuming 1 engineer per 50 nodes always | Automation reduces the ratio dramatically |
| Ignoring opportunity cost | Engineers maintaining infra not building product | Include in decision, even if hard to quantify |
| Not negotiating colo | Taking the first quote from the colo provider | Get 3+ quotes; negotiate multi-year commits for 15-25% discounts |
| Comparing list prices | Cloud list vs on-prem actual | Use your real cloud bill; apply RI/CUD discounts |
| No hardware buffer budget | First year always has surprise needs | Add 15-20% contingency to CapEx |
| Forgetting decommission costs | Old hardware needs disposal, data wiping | Budget for certified data destruction and e-waste recycling |

---

## Quiz

### Question 1
Your on-prem cluster uses 5 kW of IT power in a colocation facility with PUE 1.5. Electricity costs $0.12/kWh. What is the total monthly power cost?

<details>
<summary>Answer</summary>

**$657/month.**

Calculation:
- IT power: 5 kW
- Total facility power: 5 kW × PUE 1.5 = 7.5 kW
- Hours per month: 730 (24 × 365/12)
- Monthly cost: 7.5 kW × 730 hours × $0.12/kWh = $657

The PUE multiplier accounts for cooling, lighting, UPS losses, and other facility overhead. A PUE of 1.5 means for every watt of IT power, you pay for 1.5 watts total.
</details>

### Question 2
You need 3 infrastructure engineers ($175K fully loaded each) to manage 100 nodes. At what node count does this staffing model break even against cloud at $500/node/month?

<details>
<summary>Answer</summary>

**Staffing alone costs $525K/year = $43,750/month.** At $500/node/month cloud cost:

- Staffing per node: $43,750 / N nodes per month
- At 100 nodes: $437.50/node/month in staffing alone (88% of cloud cost before adding hardware, colo, power)
- At 200 nodes: $218.75/node/month in staffing (with same 3 engineers + automation)
- At 300 nodes: $145.83/node/month in staffing

With automation, 3 engineers can manage 200-300 nodes. The staffing cost per node drops to $145-218, leaving room for hardware ($100-200/node/month amortized) and facility ($50-100/node/month) while still being cheaper than $500/node/month cloud.

**Breakeven: approximately 200 nodes** where staffing + hardware + facility < cloud cost.
</details>

### Question 3
A vendor offers "free" Kubernetes distribution but charges $2,000/node/year for enterprise support. Is this a good deal for a 100-node cluster?

<details>
<summary>Answer</summary>

**Probably not.** $2,000/node/year × 100 nodes = $200,000/year — almost the cost of an additional engineer.

Compare:
- Vanilla Kubernetes (free) + 1 additional engineer ($175K/year): more flexible, builds internal expertise
- Enterprise K8s ($200K/year): less operational burden but vendor lock-in, annual renewal pressure

The calculation changes if:
- You have < 2 K8s engineers (vendor support covers the gap)
- You need SLA-backed support for regulatory compliance
- The distribution includes features you would otherwise build (multi-tenancy, security hardening)

For most organizations > 50 nodes, investing in team capability is better long-term than paying per-node license fees. The exception is highly regulated environments where vendor support contracts are a compliance requirement.
</details>

### Question 4
Should you own your datacenter or use colocation?

<details>
<summary>Answer</summary>

**Colocation for almost everyone.** Building a datacenter costs $10-50 million and takes 12-24 months. It only makes sense at massive scale (1,000+ servers) or for specific regulatory requirements (government, defense).

Colocation advantages:
- No construction/permitting costs
- Shared cooling, power, physical security
- Redundant utility feeds and generators included
- Flexible scaling (add/remove racks)
- Multiple colo providers per market (avoid vendor lock)

Own datacenter advantages:
- Full physical control (government/classified requirements)
- Lower per-kW cost at massive scale
- Custom cooling (liquid cooling for high-density GPU racks)
- No monthly rent

Rule of thumb: if you need < 50 racks, colocation wins. If you need 200+ racks and have a 10+ year horizon, evaluate building.
</details>

---

## Hands-On Exercise: Build a Complete TCO Model

**Task**: Create a 3-year TCO model for your organization's on-premises Kubernetes deployment and compare to cloud.

### Steps

1. **Define your requirements:**
   - Number of worker nodes
   - CPU and RAM per node
   - Storage requirements (persistent + ephemeral)
   - GPU requirements (if any)
   - Number of clusters
   - Number of datacenters/sites

2. **Calculate CapEx** using the cost taxonomy above

3. **Calculate annual OpEx** including all hidden costs

4. **Calculate 3-year cloud alternative** using:
   - Your cloud provider's pricing calculator
   - Apply realistic discounts (RI/CUD: 30-60%)
   - Include data transfer, managed K8s fees, storage

5. **Compare and document** the breakeven point

### Success Criteria
- [ ] All CapEx categories populated
- [ ] All OpEx categories populated (including staffing)
- [ ] Power calculated with PUE
- [ ] Cloud comparison uses discounted pricing (not list)
- [ ] Breakeven point identified
- [ ] Sensitivity analysis: what if staffing costs +20%? What if cloud pricing -30%?

---

## Key Takeaways

1. **Hardware is 20-30% of total cost** — staffing, facility, and operations dominate
2. **PUE multiplies your power bill** — always ask for the facility's PUE
3. **Automation determines your staffing ratio** — invest in Cluster API and GitOps early
4. **Breakeven is typically 150-250 nodes** — below that, cloud is simpler and often cheaper
5. **Get 3 quotes** — for colo, hardware, and support contracts. Never take the first offer.

---

## Next Module

Continue to [Module 2.1: Datacenter Fundamentals](../provisioning/module-2.1-datacenter-fundamentals/) to learn the physical infrastructure that supports your Kubernetes cluster.
