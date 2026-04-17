---
title: "Module 1.4: TCO & Budget Planning"
slug: on-premises/planning/module-1.4-tco-budget
sidebar:
  order: 5
---

> **Complexity**: `[MEDIUM]` | Time: 45 minutes
>
> **Prerequisites**: [Module 1.2: Server Sizing](../module-1.2-server-sizing/), [FinOps Fundamentals](/k8s/finops/module-1.1-finops-fundamentals/)

---

## What You'll Be Able to Do

After completing this module, you will be able to:

1. **Design** a comprehensive TCO model that captures hardware, staffing, facilities, networking, and opportunity costs
2. **Evaluate** cloud vs. on-premises economics with accurate 3-5 year projections including hidden costs
3. **Plan** budget proposals that account for colocation, power, cooling, maintenance contracts, and staffing overhead
4. **Diagnose** common budgeting blind spots that cause on-premises projects to exceed estimates by 2-3x

---

## Why This Module Matters

In 2023, a logistics company presented their board with a plan to move from AWS to on-premises Kubernetes. The infrastructure team calculated hardware costs: $380,000 for servers, networking, and storage. The CFO approved. Twelve months later, the actual spend was $1.1 million. The team had not budgeted for colocation fees ($72K/year), redundant internet circuits ($36K/year), a part-time facilities manager ($45K/year), two additional engineers ($350K/year), hardware maintenance contracts ($38K/year), or the $180K in professional services for the initial buildout. The "savings" over cloud disappeared entirely.

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

> **Pause and predict**: A team presents their on-premises budget to the CFO showing only the CapEx line items above. The CFO approves. What categories are missing from this budget that will cause the project to exceed estimates? List at least four before reading the OpEx section below.

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

> **Stop and think**: Your organization currently manages 80 nodes with 2 engineers using Ansible and shell scripts. You want to grow to 200 nodes. Should you hire 2 more engineers, or invest in Cluster API and GitOps automation? What factors beyond cost would influence this decision?

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

### Regional Staffing Reality Check

The `3 engineers x $175K fully loaded` example is deliberately conservative for a US-centric mid-to-senior infrastructure team. Do not reuse it blindly.

| Market | Typical fully loaded infrastructure engineer cost |
|---|---|
| Central / Eastern Europe | `$90K-130K` |
| Western Europe | `$120K-180K` |
| UK / Ireland | `$140K-200K` |
| US non-coastal | `$150K-210K` |
| US coastal / major tech hubs | `$175K-240K+` |

If your staffing market is cheaper than the example, the on-prem model improves. If you need scarce specialists in a major metro or 24x7 coverage, it worsens. Always localize the staffing line before presenting the TCO model as a decision document.

---

> **Pause and predict**: Before looking at the TCO model below, estimate what percentage of total 3-year on-premises cost is hardware vs. staffing for a 100-node cluster. Write down your guess, then check it against the model.

## 3-Year TCO Model

### Template

```
┌─────────────────────────────────────────────────────────────┐
│   3-YEAR TCO MODEL (100 K8s nodes on 13 bare-metal servers) │
│   (Each server: 64 cores, 256GB → ~8 K8s nodes per server)  │
│                                                               │
│  YEAR 0 (SETUP)                                              │
│  ────────────────────────────────────────                    │
│  Servers (13 x $15K)                    $195,000            │
│  Networking (switches + cabling)         $45,000            │
│  Storage (Ceph nodes, 3 x $12K)         $36,000            │
│  Racks + PDUs                            $8,000             │
│  Professional services (buildout)        $60,000            │
│  ────────────────────────────────────────                    │
│  CapEx subtotal                         $344,000            │
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
│  CapEx                                  $344,000            │
│  OpEx (3 years)                       $1,970,400            │
│  ────────────────────────────────────────                    │
│  TOTAL                                $2,314,400            │
│  Per month                               $64,289            │
│                                                               │
│  CLOUD COMPARISON (illustrative AWS pricing check:          │
│  2026-04-17, us-east-1, Linux, m6i.2xlarge equivalent)      │
│  ────────────────────────────────────────                    │
│  On-demand: 100 x $280/mo           $1,008,000 (3 yr)      │
│  1-year RI (no upfront, ~35% off)      $655,000 (3 yr)     │
│  3-year RI (all upfront, ~55% off)     $454,000 (3 yr)     │
│  3-year RI (~40% off sensitivity)     $605,000 (3 yr)      │
│  + EKS fee + storage + data xfer     ~$200,000 (3 yr)      │
│                                                               │
│  VERDICT at 100 nodes (13 servers):                          │
│  Cloud (3yr RI + extras) ≈ $650K vs On-prem ≈ $2.3M        │
│  → Cloud wins decisively (staffing dominates on-prem)       │
│                                                               │
│  Breakeven: ~300-500 nodes where staffing amortizes         │
│  and cloud egress/storage costs grow linearly                │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

Use that cloud block as a dated template, not a universal truth:
- pricing assumptions drift, so stamp the provider, region, date, and instance family every time
- compare against your real cloud bill when possible, not list pricing
- always run at least one reserved-commit sensitivity test such as `40%` and `55%` discount cases, because the breakeven line moves materially

---

## 5-Year TCO Model

The 3-year model is usually the easiest board-level comparison because cloud reserved-commit terms and common depreciation windows line up neatly. But many on-prem decisions only make sense when you model the extra two years explicitly.

Years 4 and 5 are where teams either prove that a private platform has become efficient, or discover that deferred refreshes, support renewals, and capacity growth erased the apparent savings.

### What Changes In Years 4 And 5

| Cost area | 3-year assumption | 5-year adjustment |
|---|---|---|
| Servers | initial purchase only | decide whether to keep, expand, or refresh the fleet |
| Maintenance | 3-5% of hardware per year | often rises after year 3 as vendor support ages |
| Capacity growth | often ignored | add new nodes, racks, and network ports for realistic growth |
| Storage | sized for current need | include retention growth, backup growth, or archival tiers |
| Power and colo | steady-state estimate | increase for growth, density changes, or power repricing |
| Staffing | fixed ratio | reflect whether automation improves the nodes-per-engineer ratio |
| Opportunity cost | mostly qualitative | reassess whether the platform now accelerates or slows product work |

### 5-Year Carry-Forward Template

Use the same 100-node / 13-server scenario, but carry the model forward year by year instead of multiplying the 3-year result by `5/3`.

```
┌─────────────────────────────────────────────────────────────┐
│               5-YEAR CARRY-FORWARD MODEL                    │
│                                                             │
│  ASSUMPTIONS                                                │
│  ───────────────────────────────────────                    │
│  Workload growth                           15% per year     │
│  Discount rate for NPV                      8%              │
│  Hardware strategy          keep fleet through year 4,      │
│                             partial refresh in year 5       │
│  Support pricing           5% years 1-3, 7% on aging gear   │
│                                                             │
│  YEAR 0 (SETUP)                                              │
│  CapEx                                  $344,000           │
│                                                             │
│  YEAR 1 (BASELINE)                                           │
│  OpEx                                   $656,800           │
│                                                             │
│  YEAR 2 (STEADY STATE)                                       │
│  OpEx                                   $656,800           │
│                                                             │
│  YEAR 3 (STEADY STATE)                                       │
│  OpEx                                   $656,800           │
│                                                             │
│  YEAR 4 (GROWTH WITHOUT FULL REFRESH)                        │
│  2 new servers + optics + rack space      $41,000 CapEx    │
│  Base Year 3 OpEx                        $656,800          │
│  Maintenance uplift on aging hardware     $18,600          │
│  Extra colo + power + network             $12,500          │
│  Staffing flat due to automation           $0              │
│  Year 4 OpEx subtotal                    $687,900          │
│                                                             │
│  YEAR 5 (PARTIAL REFRESH + RETIREMENT)                      │
│  Refresh 6 oldest servers               $120,000           │
│  Retirement / data-destruction credit   -$12,000           │
│  Maintenance on mixed old/new fleet      $28,000           │
│  Extra storage expansion                 $24,000           │
│  Colo + power repricing uplift           $12,000           │
│  Year 5 OpEx subtotal                    $720,800          │
│                                                             │
│  5-YEAR CASH TOTAL                                            │
│  ───────────────────────────────────────                    │
│  CapEx (years 0, 4, 5)                  $493,000          │
│  OpEx (years 1-5)                     $3,379,100          │
│  TOTAL                                 $3,872,100          │
│  NPV @ 8%                              $3,132,000          │
│                                                             │
│  Effective monthly average (5 years)      $64,535          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### How To Use 5-Year Modeling Correctly

- build the 5-year sheet as separate yearly rows with CapEx, OpEx, and cumulative total instead of extrapolating from the 3-year total
- tie utilization and growth to power, cooling, and rack density so a busier cluster increases PUE-adjusted facility cost rather than staying flat
- make the asset decision explicit each year: keep, expand, refresh, or retire; maintenance and support pricing changes with that choice
- include network switch lifecycle and OS / distribution subscription renewals if they are part of your operating model; those often show up after the "servers only" budget has already been approved
- show both nominal cash total and discounted NPV so finance can compare on-prem spend with cloud reserved-commit terms
- run at least three scenarios: base case, utilization `+20%`, and delayed refresh by 12 months

### Practical Interpretation

The 5-year view often changes the conclusion:

- **cloud still wins** when staffing remains flat but the on-prem fleet stays small enough that overhead never amortizes
- **on-prem improves** when the team automates aggressively, extends hardware life safely, and spreads fixed staffing across more workload
- **hybrid becomes sensible** when only a subset of predictable, steady-state workloads belong on owned hardware

If your 3-year model barely favors on-prem, the 5-year model is where you discover whether that margin is real or imaginary.

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

**Probably not.** $2,000/node/year × 100 nodes = $200,000/year — more than the `$175K` fully loaded engineer used in this example.

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

**Task**: Create both a 3-year and a 5-year TCO model for your organization's on-premises Kubernetes deployment and compare them to cloud.

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

5. **Extend the model to 5 years** with one row per year and explicit assumptions for:
   - maintenance renewals and higher support rates after year 3
   - workload growth, storage growth, and the resulting power / colo increase
   - hardware refresh, retirement, and certified disposal or resale credits
   - discount rate / NPV for comparing owned hardware with cloud commitments
   - staffing change or automation gain

6. **Compare and document** the breakeven point in both the base case and a stressed case such as utilization `+20%` or a 12-month refresh delay

### Success Criteria
- [ ] All CapEx categories populated
- [ ] All OpEx categories populated (including staffing)
- [ ] Power calculated with PUE
- [ ] Cloud comparison uses discounted pricing (not list)
- [ ] 3-year baseline completed
- [ ] 5-year carry-forward completed with separate Year 4 and Year 5 CapEx / OpEx rows
- [ ] Refresh, retirement, and support-renewal assumptions documented
- [ ] Breakeven point identified and re-checked at year 5
- [ ] Sensitivity analysis includes utilization `+20%`, cloud pricing `-30%`, and refresh timing changes

---

## Key Takeaways

1. **Hardware is 20-30% of total cost** — staffing, facility, and operations dominate
2. **PUE multiplies your power bill** — always ask for the facility's PUE
3. **A 5-year model is not just a longer spreadsheet** — refresh cycles, maintenance drift, and growth assumptions change the answer
4. **Automation determines your staffing ratio** — invest in Cluster API and GitOps early
5. **Breakeven is typically 150-250 nodes** — below that, cloud is simpler and often cheaper
6. **Get 3 quotes** — for colo, hardware, and support contracts. Never take the first offer.

---

## Next Module

Continue to [Module 2.1: Datacenter Fundamentals](/on-premises/provisioning/module-2.1-datacenter-fundamentals/) to learn the physical infrastructure that supports your Kubernetes cluster.
