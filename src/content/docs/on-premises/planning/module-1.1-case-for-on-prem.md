---
title: "Module 1.1: The Case for On-Premises Kubernetes"
slug: on-premises/planning/module-1.1-case-for-on-prem
sidebar:
  order: 2
---

> **Complexity**: `[MEDIUM]` | Time: 45 minutes
>
> **Prerequisites**: [Cloud Native 101](../../prerequisites/cloud-native-101/), [Kubernetes Basics](../../prerequisites/kubernetes-basics/)

---

## Why This Module Matters

In 2023, a mid-sized European bank spent $4.2 million per year running 340 microservices on AWS EKS across three regions. Their compliance team flagged a problem: under GDPR and the Digital Operational Resilience Act (DORA), they needed to demonstrate that customer financial data never left the EU — and that they could operate independently if their cloud provider experienced a prolonged outage. Their AWS bill was growing 22% year-over-year. Their CTO commissioned a study.

The study took three months. The conclusion: moving their core banking platform to on-premises Kubernetes in two colocation facilities would cost $2.8 million upfront (servers, networking, storage) and $1.1 million per year in operations (power, cooling, staffing, maintenance). The three-year TCO was $6.1 million on-premises versus $12.6 million on cloud. They made the move. Eighteen months later, they were running 480 microservices on bare metal Kubernetes with better latency, full data sovereignty, and a 52% reduction in infrastructure costs.

This is not a cloud-bashing story. Cloud is right for most organizations. But for a significant minority — regulated industries, high-data-volume workloads, latency-sensitive applications, and organizations at scale — on-premises Kubernetes is not just viable, it is optimal. The challenge is knowing which category you are in and making the decision with data, not emotion.

> **The Restaurant Analogy**
>
> Cloud is like eating out. Someone else cooks, cleans, and manages the kitchen. You pay per meal. It is convenient and scales perfectly for occasional dining. On-premises is like building your own kitchen. High upfront cost, you maintain everything, but if you cook three meals a day for a family of 50, it is dramatically cheaper than restaurants. The breakeven point is what matters — and most organizations never calculate it.

---

## What You'll Learn

- When on-premises Kubernetes makes strategic sense (and when it does not)
- The five drivers that push organizations toward on-prem: sovereignty, latency, economics, control, compliance
- How to build a cloud vs on-prem decision framework
- Common mistakes in the build-vs-buy decision
- How to calculate a rough breakeven point

---

## The Five Drivers for On-Premises

### 1. Data Sovereignty and Regulatory Requirements

Some data cannot leave your physical control. Period.

```
┌─────────────────────────────────────────────────────────────┐
│                 DATA SOVEREIGNTY SPECTRUM                     │
│                                                               │
│  LOW SENSITIVITY              HIGH SENSITIVITY                │
│  ─────────────────────────────────────────────               │
│                                                               │
│  Marketing    SaaS App     Financial    Healthcare  Defense   │
│  website      data         records      (PHI)       classified│
│                                                               │
│  Cloud OK     Cloud OK     Cloud with   On-prem    Air-gapped│
│               (encrypt)    restrictions preferred   mandatory │
│                                                               │
│               ◄── Cloud makes sense ──► ◄── On-prem ──►      │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

**Regulatory examples that push toward on-prem:**

| Regulation | Requirement | Impact |
|-----------|-------------|--------|
| GDPR (EU) | Data must stay in EU; right to deletion must be provable | Cloud works if region-locked, but audit complexity increases |
| DORA (EU Financial) | ICT risk management; must demonstrate operational resilience without third-party dependency | Pushes toward on-prem or hybrid |
| HIPAA (US Healthcare) | PHI must have physical safeguards; BAA required with cloud provider | Cloud possible but complex |
| PCI DSS | Cardholder data environment must be segmented and auditable | Both work; on-prem gives simpler audit scope |
| ITAR (US Defense) | Classified data cannot leave US sovereign infrastructure | GovCloud or on-prem only |
| China CSL | Critical data must stay in mainland China; security review for cross-border transfer | On-prem or domestic cloud only |

### 2. Latency and Performance

Physics does not care about your architecture.

```
┌─────────────────────────────────────────────────────────────┐
│                    LATENCY REALITY                            │
│                                                               │
│  On-premises (same rack)      :    < 0.1 ms                 │
│  On-premises (same DC)        :    0.1 - 0.5 ms             │
│  Cloud (same AZ)              :    0.5 - 1 ms               │
│  Cloud (cross-AZ)             :    1 - 2 ms                  │
│  Cloud (cross-region)         :    20 - 100 ms               │
│                                                               │
│  For every 1ms of latency:                                   │
│    Amazon: -1% revenue                                       │
│    Google: -0.5% searches                                    │
│    HFT firms: millions in lost trades                        │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

**Workloads where latency matters:**
- **High-frequency trading**: Microsecond-level decisions. Cloud is not an option.
- **Real-time video processing**: Surveillance, autonomous vehicles, quality inspection.
- **Gaming servers**: Players notice >20ms. Regional bare metal is standard.
- **Database-heavy applications**: Joins across millions of rows. NVMe on bare metal is 10x faster than cloud EBS.

### 3. Economics at Scale

Cloud pricing is linear. On-premises cost is mostly fixed.

```
┌─────────────────────────────────────────────────────────────┐
│                                                               │
│  Monthly     │                                                │
│  Cost ($)    │           ╱ Cloud (linear)                     │
│              │         ╱                                      │
│              │       ╱                                        │
│              │     ╱                                          │
│   ───────────│───╳──────── On-prem (mostly fixed)            │
│              │ ╱   ↑                                          │
│              │╱    Breakeven                                  │
│              │     point                                      │
│              └──────────────────────────────── Scale          │
│                                                               │
│  Below breakeven: cloud wins (no upfront cost)               │
│  Above breakeven: on-prem wins (amortized hardware)          │
│                                                               │
│  Typical breakeven: 50-200 nodes, depending on workload      │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

**Real-world economics:**

| Cost Category | Cloud (100 nodes) | On-Prem (100 nodes) |
|--------------|-------------------|---------------------|
| Compute | ~$50K/month (m6i.2xlarge) | ~$400K upfront / 36mo = $11K/mo |
| Storage | ~$15K/month (gp3 + S3) | ~$80K upfront / 36mo = $2.2K/mo |
| Networking | ~$8K/month (data transfer) | ~$50K upfront / 36mo = $1.4K/mo |
| Managed K8s | ~$2.4K/month (EKS) | $0 (self-managed) |
| Staffing | 2 engineers (~$30K/mo) | 3-4 engineers (~$50K/mo) |
| Facility | $0 | ~$8K/mo (colo, power, cooling) |
| **Monthly total** | **~$105K** | **~$73K** |
| **3-year total** | **~$3.8M** | **~$2.6M + $530K upfront = $3.1M** |

These numbers are illustrative — your mileage will vary dramatically based on region, workload, and negotiated cloud discounts. The point is: **at scale, on-prem is almost always cheaper**. The question is whether the operational complexity is worth the savings.

### 4. Control and Customization

On-premises gives you choices cloud providers do not offer:

- **Hardware selection**: Choose exact CPU (Intel vs AMD), memory configuration, NVMe models, GPU types
- **Network topology**: Design your own spine-leaf, choose your own CNI with bare metal optimizations
- **Kernel tuning**: Custom kernels, specific sysctl parameters, real-time scheduling
- **Security perimeter**: Physical air gaps, no shared tenancy, no cloud provider access to your data
- **Upgrade timing**: Upgrade Kubernetes on your schedule, not the provider's

### 5. Compliance Simplification

Paradoxically, on-premises can be **simpler** to audit than cloud:

```
┌─────────────────────────────────────────────────────────────┐
│              AUDIT SCOPE COMPARISON                          │
│                                                               │
│  CLOUD AUDIT:                                                │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐    │
│  │ Your     │  │ Cloud    │  │ Shared   │  │ Cloud    │    │
│  │ workload │  │ IAM      │  │ resp.    │  │ physical │    │
│  │ config   │  │ config   │  │ model    │  │ security │    │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘    │
│  You audit     You audit     You prove     You trust       │
│                              boundaries    SOC2 report      │
│                                                               │
│  ON-PREM AUDIT:                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ Everything is yours. One boundary. One audit scope.  │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

---

## When NOT to Go On-Premises

On-prem is wrong when:

| Situation | Why Cloud Wins |
|-----------|---------------|
| Startup / small team (<20 engineers) | Cannot justify infrastructure team overhead |
| Unpredictable scaling needs | Cloud elasticity is unbeatable for bursty workloads |
| Global distribution needed | Cloud has 60+ regions; building your own is prohibitive |
| Managed service dependency | If you rely on DynamoDB, BigQuery, Cosmos DB — there is no on-prem equivalent |
| Short project lifespan (<2 years) | Cannot amortize hardware investment |
| No datacenter expertise | Operating bare metal requires deep Linux, networking, and hardware skills |

> **War Story: The Startup That Went On-Prem Too Early**
>
> A Series A fintech startup (18 engineers) decided to run on-premises Kubernetes to save money. They leased a quarter-rack in a colocation facility, bought 6 servers, and spent 4 months building their platform. Then their lead infrastructure engineer quit. Nobody else knew how to replace a failed disk, upgrade the OS, or troubleshoot BGP peering with the colo's network. They migrated everything to GKE in 3 weeks and shut down the colo contract — eating the remaining 18 months of the lease ($54K). Total cost of the on-prem experiment: ~$180K in hardware, colo fees, and lost engineering time. The CTO's postmortem: "We optimized for the wrong constraint. We needed speed to market, not infrastructure cost savings."

---

## The Decision Framework

Use this framework to evaluate whether on-premises makes sense for your organization:

```
┌─────────────────────────────────────────────────────────────┐
│            ON-PREM DECISION FRAMEWORK                        │
│                                                               │
│  1. REGULATORY REQUIREMENT?                                  │
│     └── Yes → On-prem or hybrid (non-negotiable)            │
│     └── No → Continue                                        │
│                                                               │
│  2. LATENCY REQUIREMENT < 1ms?                               │
│     └── Yes → On-prem for those workloads                   │
│     └── No → Continue                                        │
│                                                               │
│  3. RUNNING > 50 NODES STEADY-STATE?                         │
│     └── Yes → Calculate TCO (likely on-prem wins)           │
│     └── No → Cloud (scale is too small for on-prem ROI)     │
│                                                               │
│  4. HAVE 3+ INFRASTRUCTURE ENGINEERS?                        │
│     └── Yes → On-prem is operationally feasible             │
│     └── No → Cloud (cannot staff for on-prem operations)    │
│                                                               │
│  5. DATA VOLUME > 100TB?                                     │
│     └── Yes → On-prem storage is dramatically cheaper       │
│     └── No → Cloud storage is fine                          │
│                                                               │
│  RESULT: If 2+ "Yes" answers → Seriously evaluate on-prem   │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

---

## Did You Know?

- **Dropbox saved $75 million over two years** by moving from AWS to on-premises infrastructure in 2016. They built custom servers ("Diskotech" for storage, "Edgerouter" for networking) and reduced their storage cost per GB by 50%. As of 2024, they run one of the largest private clouds in the world.

- **Apple runs one of the largest on-premises Kubernetes deployments**, managing tens of thousands of nodes across multiple datacenters. Their internal platform team built custom tooling for bare metal provisioning, and they contribute to several CNCF projects.

- **37signals (Basecamp/HEY) published their cloud exit numbers in 2023**: they were spending $3.2 million per year on AWS. Their on-premises replacement cost $600K in hardware and $200K/year in operations — a $2.4 million annual savings. David Heinemeier Hansson called it "leaving the cloud."

- **The Kubernetes project itself started as an internal Google tool** (Borg) running on Google's own bare metal infrastructure. The irony is that Kubernetes was born on-premises and then became synonymous with cloud.

---

## Common Mistakes

| Mistake | Problem | Solution |
|---------|---------|----------|
| Comparing list-price cloud to on-prem | Cloud discounts (RIs, EDPs) can be 40-60% off list | Use your actual cloud bill, not calculator estimates |
| Forgetting staffing costs | On-prem needs 1 engineer per 50-100 nodes | Include staffing in TCO; it is often the largest cost |
| Ignoring opportunity cost | Engineers maintaining hardware are not building product | Factor in what else those engineers could be doing |
| Over-provisioning hardware | Buying for peak load that happens 2 days/year | Size for P90 load; burst to cloud for peaks (hybrid) |
| Under-provisioning networking | Buying 1GbE when K8s east-west traffic needs 25GbE+ | Network is the hardest thing to upgrade later |
| Skipping colo evaluation | Building your own datacenter when colo is available | Colo gives you the rack; you bring the servers |
| Single-vendor lock | Buying all Dell or all HPE with no alternative | Ensure your automation works across vendors |
| No exit plan | Going all-in on on-prem with no cloud fallback | Maintain hybrid capability for DR and burst |

---

## Quiz

### Question 1
Your company runs 30 nodes on AWS and spends $45K/month. A vendor quotes $200K for equivalent on-prem hardware with a 3-year lifecycle. Should you move to on-prem?

<details>
<summary>Answer</summary>

**Probably not.** The math:
- Cloud: $45K/month x 36 months = $1.62M
- On-prem: $200K hardware + ~$15K/month operations (staffing, colo, power) x 36 = $200K + $540K = $740K

The on-prem TCO looks cheaper ($740K vs $1.62M), but 30 nodes is below the typical breakeven for operational complexity. You need at least 2-3 infrastructure engineers ($300K-$450K/year) who could instead be building product. At 30 nodes, the staffing cost alone may exceed the cloud savings. Additionally, cloud pricing at this scale can often be negotiated 30-40% lower with committed use discounts.

**The right answer depends on**: Do you have the team? Is this growing to 100+ nodes? Are there regulatory requirements?
</details>

### Question 2
A healthcare company stores 500TB of medical imaging data. They need sub-millisecond access for their ML inference pipeline. Currently on AWS with $180K/month in storage and compute costs. What is your recommendation?

<details>
<summary>Answer</summary>

**Strong case for on-premises or hybrid.**

Three factors align:
1. **Data volume** (500TB) — cloud storage costs dominate at this scale. On-prem NVMe storage is ~$0.10/GB one-time vs ~$0.023/GB/month on S3 (breakeven in ~4 months).
2. **Latency** — sub-millisecond access requires local NVMe, not network-attached cloud storage.
3. **Regulatory** — HIPAA requires physical safeguards for PHI; on-prem simplifies the audit scope.

**Recommended architecture**: On-prem GPU nodes with local NVMe for inference, cloud for non-sensitive workloads (dev/test, CI/CD). Hybrid connectivity via Direct Connect or VPN for data that can flow to cloud.
</details>

### Question 3
What is the most commonly underestimated cost in on-premises Kubernetes?

<details>
<summary>Answer</summary>

**Staffing.** Hardware is a one-time cost amortized over 3-5 years. Power and cooling are predictable. But the people who operate bare metal Kubernetes — handling firmware updates, disk replacements, network troubleshooting, OS patching, K8s upgrades, and 3AM hardware failures — are expensive and hard to hire.

The rule of thumb is 1 infrastructure engineer per 50-100 nodes. At $150K-$200K fully loaded per engineer, a 200-node cluster needs 2-4 engineers costing $300K-$800K per year. This is often more than the cloud compute cost it replaces.

Organizations that succeed with on-prem invest heavily in automation (Cluster API, GitOps, machine health checks) to increase the nodes-per-engineer ratio.
</details>

### Question 4
Your CEO read an article about cloud repatriation and wants to move everything on-premises. What questions should you ask before proceeding?

<details>
<summary>Answer</summary>

Critical questions:

1. **What is our actual cloud spend?** (Not list price — actual bill with discounts)
2. **Which workloads are candidates?** (Steady-state compute, not bursty or globally distributed)
3. **Do we have the team?** (Need 3+ infrastructure engineers with bare metal experience)
4. **What managed services do we depend on?** (RDS, DynamoDB, SQS have no on-prem equivalent — you would need to operate them yourself)
5. **What is our timeline?** (On-prem migration takes 6-12 months; hardware procurement alone is 2-4 months)
6. **Where will we host?** (Own datacenter vs colocation)
7. **What is our DR strategy?** (On-prem needs a second site or cloud failover)
8. **What is the 3-year TCO comparison?** (Include hardware, staffing, facility, networking, and opportunity cost)

The CEO's instinct may be right at scale, but the decision must be data-driven. A 3-month evaluation with a detailed TCO model is the right next step.
</details>

---

## Hands-On Exercise: Build a Cloud vs On-Prem TCO Model

**Task**: Create a spreadsheet-based TCO comparison for a realistic workload.

### Scenario
Your company runs a data analytics platform:
- 80 worker nodes (m6i.xlarge equivalent: 4 vCPU, 16GB RAM)
- 3 control plane nodes
- 50TB persistent storage
- Running on AWS EKS in us-east-1

### Steps

1. **Calculate current cloud cost** (monthly):
   - Compute: 80 x m6i.xlarge on-demand ($0.192/hr) = 80 x $140/mo = $11,200/mo
   - EKS fee: $73/mo (1 cluster)
   - Storage: 50TB gp3 at $0.08/GB = $4,096/mo
   - Data transfer: estimate 5TB egress at $0.09/GB = $461/mo
   - Total: ~$15,830/mo = ~$190K/year

2. **Calculate on-prem equivalent**:
   - Servers: 10 x Dell R660 (2x 32-core Xeon, 256GB, 4x 3.84TB NVMe) ≈ $18K each = $180K
   - Networking: 2x spine + 10x ToR switches ≈ $60K
   - Storage: Additional Ceph nodes if needed ≈ $40K
   - Colocation: 3 racks x $1,500/mo = $4,500/mo
   - Power: ~$3,000/mo
   - Staffing: 2 engineers x $175K/yr = $350K/yr = $29,166/mo
   - Hardware maintenance: $2,000/mo
   - **Monthly operational**: $38,666/mo = $464K/year
   - **Year 1**: $280K (hardware) + $464K (ops) = $744K
   - **Year 2-3**: $464K/year each

3. **Compare 3-year TCO**:
   - Cloud: $190K x 3 = $570K (with 30% RI discount: ~$400K)
   - On-prem: $744K + $464K + $464K = $1.67M

4. **Analyze**: At 80 nodes, cloud with reserved instances is significantly cheaper. On-prem breakeven would be around 200+ nodes for this workload mix.

### Success Criteria
- [ ] Cloud monthly cost calculated with actual instance pricing
- [ ] On-prem costs include hardware, networking, colo, power, staffing
- [ ] 3-year TCO comparison completed
- [ ] Breakeven point identified
- [ ] Document which factors would change the decision

---

## Key Takeaways

1. **On-prem is not anti-cloud** — it is a different tool for different constraints
2. **The five drivers**: sovereignty, latency, economics at scale, control, compliance
3. **Breakeven is typically 50-200 nodes** — below that, cloud wins on operational simplicity
4. **Staffing is the hidden cost** — 1 engineer per 50-100 nodes, and they are hard to hire
5. **Never go all-in** — maintain hybrid capability for DR and burst

---

## Further Reading

- **"The Cloud Exit" by 37signals** — Detailed public accounting of their AWS-to-on-prem migration
- **Dropbox IPO filing (S-1)** — Section on infrastructure economics and the move from AWS
- **"Cloud Repatriation" by Andreessen Horowitz** — Data on the trend of moving workloads back on-premises
- **CNCF Survey 2024** — Statistics on on-premises Kubernetes adoption across industries

---

## Next Module

Continue to [Module 1.2: Server Sizing & Hardware Selection](module-1.2-server-sizing/) to learn how to choose the right hardware for your Kubernetes clusters.
