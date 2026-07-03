---
citations_verified: true
title: "Module 1.1: The Case for On-Premises Kubernetes"
slug: on-premises/planning/module-1.1-case-for-on-prem
sidebar:
  order: 2
---

> **Complexity**: `[MEDIUM]` | Time: 90 minutes
>
> **Prerequisites**: [CKA](/k8s/cka/) (cluster architecture, kubeadm) — required. You should already be comfortable with core Kubernetes troubleshooting, Linux networking/storage/security, and day-2 operational thinking. Foundational refreshers: [Cloud Native 101](/prerequisites/cloud-native-101/), [Kubernetes Basics](/prerequisites/kubernetes-basics/).

---

## What You'll Be Able to Do

After completing this module, you will be able to:

1. **Evaluate** whether on-premises Kubernetes is the right fit for a workload by comparing regulatory, latency, cost, operational, and resilience constraints.
2. **Design** a decision framework that compares cloud, hybrid, and on-premises deployment models using quantitative and qualitative evidence.
3. **Diagnose** organizational readiness gaps that must be closed before committing to bare-metal Kubernetes infrastructure.
4. **Plan** a phased migration from managed cloud Kubernetes to on-premises Kubernetes with measurable gates, rollback points, and success criteria.
5. **Defend** a recommendation to executives by explaining the trade-offs behind cost, control, speed, staffing, and risk.

---

## Why This Module Matters

In 2023, a mid-sized European bank ran three hundred forty microservices on AWS EKS across three regions. The platform worked well technically, but the business context changed around it. Compliance leaders needed stronger evidence that customer financial records stayed inside approved jurisdictions, risk leaders wanted operational independence from a single cloud provider, and finance leaders saw the infrastructure bill growing faster than revenue. The CTO did not ask the platform team to "leave the cloud." She asked them to prove which hosting model would best serve the next five years of the business.

The team built a decision model instead of starting with an opinion. They grouped workloads by data sensitivity, latency requirement, scaling profile, managed-service dependency, and recovery objective. They compared the actual cloud bill against colocation, hardware, power, network, software support, and staffing costs. They also included migration risk, procurement delay, incident response maturity, and the opportunity cost of pulling senior engineers away from product work. The final answer was not "everything on-premises." It was a hybrid target: core banking workloads moved to two colocation sites, while development environments, burst analytics, and some managed services stayed in cloud.

That distinction is the heart of this module. On-premises Kubernetes is not a moral stance against cloud providers. It is a deployment model with a different cost curve, different failure modes, and different responsibilities. It can reduce long-term cost, improve latency, simplify some audits, and restore control over hardware and data placement. It can also trap a small team inside infrastructure work they are not staffed to perform. Senior engineers earn trust by showing both sides clearly.

> **The Restaurant Analogy**
>
> Cloud is like eating out. Someone else owns the kitchen, hires the cooks, washes the dishes, replaces broken equipment, and charges you per meal. On-premises is like building your own commercial kitchen. The first bill is large, the maintenance never disappears, and you need people who know how to keep it running. If you serve a few meals a week, restaurants win. If you serve thousands of predictable meals every day, owning the kitchen may become cheaper and more controllable. The breakeven point matters, but so does whether you can safely operate the kitchen.

This module teaches the decision process behind that judgment. You will start with the forces that push organizations toward on-premises Kubernetes, then learn when those forces are not enough. You will work through a decision framework, calculate a rough total cost of ownership, and then build a phased migration strategy with gates that prevent a risky all-at-once cutover.

---

## From Cloud Convenience to On-Prem Responsibility

Managed cloud Kubernetes hides a large amount of operational work. The provider handles much of the control plane lifecycle, datacenter power, physical security, hardware replacement, many network primitives, and the procurement pipeline. Your team still owns application health, cluster configuration, security posture, and cost discipline, but the provider absorbs entire layers of infrastructure failure. That abstraction is valuable, and any on-premises plan must account for the work that returns to your team.

On-premises Kubernetes changes the responsibility boundary. The Kubernetes API may look familiar, but the platform underneath it is no longer someone else's product. Nodes are real servers with firmware, disks, network cards, BIOS settings, remote management ports, warranties, and replacement lead times. Networking is no longer a virtual private cloud with managed route tables; it is switches, VLANs, routing protocols, load balancers, cabling, and capacity planning. Storage is no longer a managed volume service; it is a design decision with failure domains, replication costs, rebuild times, and operational procedures.

```text
┌────────────────────────────────────────────────────────────────────┐
│                 RESPONSIBILITY SHIFT: CLOUD TO ON-PREM              │
├──────────────────────────────┬─────────────────────────────────────┤
│ Managed cloud Kubernetes      │ On-premises Kubernetes              │
├──────────────────────────────┼─────────────────────────────────────┤
│ Provider manages hardware     │ Your team manages hardware          │
│ Provider manages facilities   │ Your team contracts or owns space   │
│ Provider abstracts network    │ Your team designs network fabric    │
│ Provider offers block storage │ Your team operates storage systems  │
│ Provider patches control plane│ Your team owns lifecycle strategy   │
│ Provider absorbs procurement  │ Your team handles supply timelines  │
│ You focus higher in the stack │ You own more of the stack directly  │
└──────────────────────────────┴─────────────────────────────────────┘
```

The practical question is not whether your team can install Kubernetes on bare metal once. Many teams can do that in a lab. The question is whether your organization can operate that platform during hardware failures, security incidents, capacity crunches, maintenance windows, and staff turnover. A credible on-premises plan treats Kubernetes installation as the beginning of ownership, not the finish line.

| Layer | Managed cloud default | On-premises ownership question | Evidence to collect |
|---|---|---|---|
| Facilities | Provider owns power, cooling, and physical access | Which site or colocation contract meets uptime and access needs? | Rack power limits, access procedures, SLA, remote hands pricing |
| Hardware | Provider replaces failed hosts invisibly | How quickly can you detect, replace, and reprovision failed nodes? | Warranty terms, spare pool, provisioning runbook, parts lead time |
| Network | Provider exposes managed VPC primitives | Who designs routing, load balancing, and segmentation? | Network diagram, BGP plan, firewall rules, test failover results |
| Storage | Provider offers managed volumes and object storage | Which storage system meets latency, durability, and recovery goals? | Benchmark data, failure tests, restore timing, support contract |
| Kubernetes lifecycle | Provider automates parts of upgrades | Who owns cluster upgrades, conformance, and rollback? | Upgrade runbook, test cluster, maintenance window, version policy |
| Security | Provider handles physical controls | How are physical, host, cluster, and app controls audited together? | Access logs, hardening baseline, evidence collection workflow |

> **Active learning prompt:** Before reading further, choose one workload your organization or a familiar company runs today. Write down which three layers in the table would become riskiest if that workload moved from managed cloud Kubernetes to on-premises Kubernetes. Then explain whether those risks are technical, staffing-related, financial, or regulatory.

The rest of the module builds a disciplined evaluation. You will see cases where on-premises is compelling, cases where cloud remains the better tool, and cases where hybrid architecture is the safest recommendation. Keep the responsibility shift in mind as you evaluate each driver, because every benefit of control comes with an operating burden attached.

---

## The Five Drivers for On-Premises

Organizations usually consider on-premises Kubernetes because one or more business constraints are not well served by a pure public cloud model. The strongest cases combine several drivers at once. A company with sensitive data, steady utilization, high storage volume, and strict latency requirements has a very different decision profile from a small software startup that mostly wants to reduce a surprising cloud bill.

A useful evaluation starts by separating durable drivers from temporary discomfort. A temporary discomfort is something like an unoptimized bill, an inefficient autoscaling policy, or an overprovisioned managed database. Those problems can often be fixed inside the cloud. A durable driver is something like legal data residency, sub-millisecond local processing, predictable high utilization, specialized hardware, or mandatory physical isolation. Durable drivers may justify changing the deployment model itself.

### 1. Data Sovereignty and Regulatory Requirements

Some workloads are constrained by where data may reside, who may access it, and how auditors must verify control. Public cloud can satisfy many regulatory regimes when configured correctly, especially with region selection, encryption, private networking, and provider attestations. The problem is that cloud compliance still depends on shared responsibility, provider contracts, and evidence from systems your team does not physically control. For some organizations, that shared boundary is acceptable. For others, it creates audit complexity or unacceptable third-party dependency.

```text
┌────────────────────────────────────────────────────────────────────┐
│                     DATA SOVEREIGNTY SPECTRUM                      │
│                                                                    │
│  LOW SENSITIVITY                              HIGH SENSITIVITY     │
│  ─────────────────────────────────────────────────────────────     │
│                                                                    │
│  Marketing       SaaS usage      Financial       Health     Defense│
│  website         analytics       records         PHI        secret │
│                                                                    │
│  Cloud usually   Cloud with      Cloud with      Hybrid or  Isolated│
│  sufficient      controls        strict evidence on-prem    platform│
│                                                                    │
│  ◄──────── Cloud usually fits ────────► ◄── On-prem likely ─────►  │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

The key teaching point is that sovereignty is not the same as security. A well-run cloud environment may be more secure than a poorly run private datacenter. Sovereignty asks a narrower question: can the organization prove where the data is, who can access the systems that process it, and which legal jurisdictions can compel provider action? A team that cannot answer those questions with evidence may face compliance risk even if the technical controls are strong.

| Regulation or regime | Practical requirement | Impact on hosting decision |
|---|---|---|
| GDPR in the European Union | Personal data location, deletion, processor controls, and transfer rules must be demonstrable | Cloud can work with strong controls, but on-premises may simplify evidence for high-risk datasets |
| DORA for EU financial entities | ICT risk, resilience, third-party dependency, and exit planning must be managed explicitly | Hybrid or on-premises designs can reduce dependency concentration for critical services |
| HIPAA in United States healthcare | Protected health information requires administrative, physical, and technical safeguards | Cloud can work with a BAA, but on-premises may simplify physical safeguard evidence |
| PCI DSS for cardholder data | Cardholder environments must be segmented, monitored, and auditable | Both models can work; on-premises may reduce shared-service scope for some designs |
| ITAR and defense-related controls | Certain technical data must remain under approved national or organizational control | Government cloud or on-premises infrastructure is often required for sensitive workloads |
| Critical infrastructure rules | Operators may need resilience, domestic control, and incident evidence under sector-specific laws | On-premises or sovereign-cloud patterns may be required for the most critical systems |

A senior recommendation should identify the exact control requirement instead of using "compliance" as a vague justification. If the requirement is data residency, a region-locked cloud deployment may be enough. If the requirement is operational independence from a third-party provider during a sector-wide incident, on-premises or multi-provider architecture may be necessary. If the requirement is physical isolation, ordinary public cloud may not be an option.

### 2. Latency and Performance

Latency-sensitive workloads expose the limits of geography, network hops, and shared infrastructure. Kubernetes scheduling can place containers close together inside a cluster, but it cannot make a distant cloud region physically closer to users, cameras, trading venues, industrial controllers, or storage devices. When every millisecond matters, the location of compute and data becomes an architecture decision rather than an implementation detail.

```text
┌────────────────────────────────────────────────────────────────────┐
│                         LATENCY REALITY                            │
│                                                                    │
│  Same host process boundary                 :   microseconds       │
│  Same rack on-premises                      :   below 0.1 ms       │
│  Same datacenter on-premises                :   0.1 to 0.5 ms      │
│  Cloud same availability zone               :   0.5 to 1 ms        │
│  Cloud cross-availability-zone path         :   1 to 2 ms          │
│  Cloud cross-region path                    :   20 to 100 ms       │
│                                                                    │
│  The numbers vary by provider and network, but distance always     │
│  appears in the budget. Architecture cannot negotiate with physics.│
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

A latency argument is strongest when the workload has a hard budget and cloud distance consumes a measurable portion of it. Real-time video inspection, factory automation, high-frequency trading, low-latency multiplayer gaming, telecommunications, and edge inference can fall into this category. A latency argument is weak when the system has not been profiled, when database queries are inefficient, or when the application performs unnecessary synchronous calls. Moving a poorly designed service on-premises may only make a bad architecture slightly faster.

> **Active learning prompt:** Your company processes video from ten thousand cameras. Each frame must be analyzed within fifty milliseconds, and the nearest cloud region adds twelve milliseconds of round-trip network time before compute even starts. Would you choose cloud, on-premises, or hybrid? Write a two-sentence recommendation that includes one non-latency factor, such as data volume, physical site reliability, or staffing.

Performance also includes storage throughput, network predictability, and hardware specialization. Cloud block storage is flexible and convenient, but it may not match local NVMe for database-heavy workloads with high input/output pressure. Cloud GPUs are easy to rent, but availability and price can vary by region. Bare-metal clusters let teams choose exact hardware, tune BIOS settings, isolate noisy neighbors, and design network fabrics for east-west traffic. Those capabilities matter only if the team has the expertise to use them safely.

### 3. Economics at Scale

Cloud cost is usually variable and usage-based, while on-premises cost is mostly fixed after procurement. This difference is the source of many repatriation stories. Cloud is financially attractive when demand is uncertain, growth is uneven, teams are small, and managed services replace operational labor. On-premises becomes financially attractive when utilization is high, workloads are steady, storage volume is large, and the organization can amortize hardware over several years.

```text
┌────────────────────────────────────────────────────────────────────┐
│                     COST CURVE: CLOUD VS ON-PREM                   │
│                                                                    │
│  Monthly cost                                                      │
│      │                                                             │
│      │                                      ╱ Cloud usage cost      │
│      │                                    ╱                         │
│      │                                  ╱                           │
│      │                                ╱                             │
│      │                 ─────────────╳──────────── On-prem baseline  │
│      │                            ╱  ↑                              │
│      │                          ╱    Breakeven region               │
│      │                        ╱                                      │
│      └─────────────────────────────────────────────── Scale         │
│                                                                    │
│  Below breakeven, cloud often wins because it avoids fixed cost.    │
│  Above breakeven, on-premises may win if operations are mature.     │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

A trustworthy total cost model starts with the actual cloud bill, not public calculator estimates. Enterprise discounts, committed-use contracts, reserved instances, savings plans, data transfer patterns, support plans, and managed service charges all matter. The on-premises side must include servers, storage, switching, racks, power, cooling, colocation or facility cost, support contracts, spares, monitoring, backup, security tooling, procurement overhead, and staff. If staffing is missing, the model is not credible.

| Cost category | Cloud model | On-premises model | Common modeling mistake |
|---|---|---|---|
| Compute | Instance, node, or container runtime cost | Server purchase amortized over lifecycle | Comparing on-demand cloud list price against discounted hardware only |
| Storage | Managed block, file, object, snapshot, and request charges | Disk, SSD, storage servers, replication overhead, support | Forgetting rebuild capacity and backup infrastructure |
| Networking | Load balancers, NAT, inter-zone, inter-region, and egress charges | Switches, routers, firewalls, transit, cross-connects | Underestimating east-west traffic and redundancy |
| Operations | Fewer physical tasks, more cloud configuration tasks | Hardware, OS, network, storage, and Kubernetes lifecycle | Treating existing cloud engineers as free capacity |
| Facilities | Included in provider pricing | Colocation, power, cooling, remote hands, access control | Ignoring power density and growth limits |
| Risk | Provider outages, account lockouts, cost surprises | Hardware failures, spare shortages, local site failures | Omitting disaster recovery and rollback cost |

The breakeven point is workload-specific. A steady platform with hundreds of nodes and large storage volume may justify on-premises quickly. An eighty-node environment using reserved cloud capacity may remain cheaper in cloud after staff and facility costs are included. A bursty retail workload may look expensive during peak season but still fit cloud better because building for peak hardware utilization would leave servers idle most of the year.

### 4. Control and Customization

Control is the driver most likely to be overstated by teams that are frustrated with cloud constraints. On-premises gives real control over CPU models, memory density, accelerators, disks, network cards, kernel versions, storage topology, physical segmentation, and upgrade timing. That control is valuable for workloads with unusual hardware needs or strict isolation requirements. It is less valuable when the organization does not have a specific use for the added control.

Control also brings design accountability. If your team chooses a storage backend, it owns the data loss scenario. If it chooses a network topology, it owns failover behavior. If it delays Kubernetes upgrades, it owns security exposure and version skew. In cloud, provider defaults sometimes hide hard decisions. On-premises makes those decisions explicit, which is useful only when the team is prepared to make them.

```text
┌────────────────────────────────────────────────────────────────────┐
│                        CONTROL TRADE-OFF MAP                       │
├──────────────────────────────┬─────────────────────────────────────┤
│ Extra control                 │ New responsibility                  │
├──────────────────────────────┼─────────────────────────────────────┤
│ Choose exact server hardware  │ Validate firmware, supply, support  │
│ Tune kernel and BIOS settings │ Maintain host baselines safely      │
│ Design network fabric         │ Debug routing and packet loss       │
│ Select storage architecture   │ Test replication and recovery       │
│ Schedule upgrades             │ Own version skew and security fixes │
│ Enforce physical isolation    │ Prove access controls continuously  │
└──────────────────────────────┴─────────────────────────────────────┘
```

A good architecture review asks, "Which specific control do we need, and what measurable outcome does it improve?" If the answer is "we want more control in general," the case is weak. If the answer is "we need GPU models unavailable in our cloud region, local NVMe latency for inference, and physical isolation for regulated datasets," the case becomes more concrete.

### 5. Compliance Simplification

On-premises can simplify some audits because the organization controls the full stack inside a clearer physical boundary. Instead of mapping controls across a shared responsibility model, cloud IAM, managed services, provider attestations, and multiple accounts, the auditor may inspect one operational domain. This simplification is real for some organizations, especially when data location and physical safeguards dominate the audit.

```text
┌────────────────────────────────────────────────────────────────────┐
│                       AUDIT SCOPE COMPARISON                       │
│                                                                    │
│  CLOUD AUDIT                                                       │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────┐   │
│  │ Workload   │  │ Cloud IAM  │  │ Shared     │  │ Provider   │   │
│  │ controls   │  │ controls   │  │ boundary   │  │ evidence   │   │
│  └────────────┘  └────────────┘  └────────────┘  └────────────┘   │
│       You own        You own        You explain      You rely on   │
│                                                                    │
│  ON-PREM AUDIT                                                     │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ One operational boundary, but every layer is your evidence.  │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

The word "simplify" does not mean "reduce work." It means the evidence chain may be easier to reason about because fewer third-party boundaries are involved. Your team still needs access logs, change records, vulnerability management, network segmentation evidence, backup tests, incident response records, and physical access controls. A weak on-premises evidence process can be worse than a mature cloud compliance program.

---

## When Not to Go On-Premises

A strong engineer can argue against an attractive but premature on-premises plan. The most common failure pattern is optimizing for a visible cloud bill while ignoring the invisible cost of operating infrastructure. Cloud invoices are painful because they are explicit. On-premises costs are painful because they are distributed across people, procurement, facilities, support contracts, and delayed product work.

Cloud usually wins when demand is unpredictable, the team is small, the product needs speed more than control, or the workload depends heavily on managed services. It also wins when the organization lacks incident response maturity. If a team struggles to patch managed clusters, control cloud IAM, or maintain observability today, moving down the stack will usually amplify those problems.

| Situation | Why cloud usually wins | Warning sign |
|---|---|---|
| Startup or small platform team | The fixed staffing cost overwhelms infrastructure savings | One or two engineers would become the only people who understand production |
| Bursty or seasonal workload | Elasticity avoids buying hardware for rare peaks | Average utilization is low outside specific events |
| Global user base | Cloud regions and edge services are hard to reproduce privately | Users need low latency across continents |
| Heavy managed-service dependency | Replacing databases, queues, object storage, and analytics is expensive | The architecture assumes provider-native services everywhere |
| Short project lifespan | Hardware cannot be amortized over enough useful time | The business may pivot before the servers pay back |
| Weak infrastructure operations | Bare metal adds failure modes before the team is ready | There are no tested runbooks for current incidents |
| Procurement uncertainty | Hardware lead times and contracts slow delivery | Product teams need capacity next month, not after a long purchase cycle |
| Unclear regulatory driver | Compliance is used as a slogan instead of a control requirement | No one can name the exact evidence gap cloud fails to satisfy |

Consider a Series A fintech startup with eighteen engineers. The team leases a quarter rack, buys six servers, and spends several months building an on-premises Kubernetes platform to reduce cloud cost. Then the lead infrastructure engineer leaves. Nobody else is comfortable replacing failed disks, troubleshooting switch configuration, or planning safe Kubernetes upgrades. The team migrates back to managed Kubernetes under time pressure and absorbs hardware, lease, and engineering opportunity costs. The mistake was not that on-premises is bad. The mistake was optimizing for infrastructure cost before the organization had the staffing depth to own infrastructure risk.

> **Active learning prompt:** A CEO forwards a cloud repatriation article and asks, "Why are we still paying our provider?" Draft three questions you would ask before making any recommendation. At least one question must test workload fit, one must test team readiness, and one must test financial assumptions.

The safest answer is often hybrid. Hybrid does not mean a confused half-step; it means placing each workload where its constraints fit best. Latency-sensitive inference may run near cameras. Regulated records may stay in a controlled facility. Development environments may remain in cloud. Disaster recovery may use a second private site, a cloud region, or both. A nuanced decision beats a slogan.

---

## A Decision Framework That Produces Evidence

The decision framework should turn debate into evidence. It does not replace engineering judgment, but it forces the team to collect the right facts before choosing a deployment model. The framework below starts with non-negotiable constraints, then evaluates economics and readiness. That order matters because cost savings cannot compensate for an illegal data placement, and a cheap hardware quote cannot compensate for a team that cannot operate the platform.

```text
┌────────────────────────────────────────────────────────────────────┐
│                    ON-PREM DECISION FRAMEWORK                      │
│                                                                    │
│  1. Is there a hard sovereignty, isolation, or resilience need?     │
│     ├── Yes: evaluate on-premises or sovereign hybrid patterns      │
│     └── No: continue to workload fit                                │
│                                                                    │
│  2. Does the workload have strict locality or latency requirements? │
│     ├── Yes: evaluate local compute for those workload slices       │
│     └── No: continue to cost shape                                  │
│                                                                    │
│  3. Is utilization steady enough to amortize fixed infrastructure?  │
│     ├── Yes: build a three-year TCO model                           │
│     └── No: cloud elasticity is likely more valuable                │
│                                                                    │
│  4. Can the team operate hardware, network, storage, and K8s?       │
│     ├── Yes: plan a gated pilot                                     │
│     └── No: close readiness gaps before migration                   │
│                                                                    │
│  5. Can the organization tolerate migration and rollback risk?      │
│     ├── Yes: design phased migration with measurable gates          │
│     └── No: optimize cloud first and revisit later                  │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

The framework should produce a recommendation with evidence, not a binary label. A recommendation might say: "Move regulated inference and storage to on-premises over twelve months, keep managed analytics in cloud, and revisit development environments after the first operational quarter." Another recommendation might say: "Do not migrate now; reduce cloud spend through rightsizing and reservations, hire one senior infrastructure engineer, and run a storage benchmark before reconsidering." Both recommendations can be excellent if they follow from evidence.

| Decision dimension | Strong on-premises signal | Strong cloud signal | Evidence source |
|---|---|---|---|
| Regulation | Physical control or third-party independence is required | Region and encryption controls satisfy auditors | Legal requirement, auditor notes, risk register |
| Latency | Local processing materially changes user or machine outcome | Most latency comes from application design | Traces, packet captures, benchmarks |
| Cost | High steady utilization and large data volume dominate spend | Discounts and elasticity keep total cost lower | Actual invoices, utilization reports, TCO model |
| Operations | Team has deep Linux, network, storage, and Kubernetes skills | Team is already overloaded managing cloud platform | Incident history, staffing plan, runbook quality |
| Managed services | Dependencies can be replaced or remain hybrid | Provider-native services are central to product speed | Architecture inventory, service dependency map |
| Resilience | Organization can run multiple sites or hybrid DR | Single private site would reduce resilience | DR tests, recovery objectives, failure-mode analysis |

### Worked Example: The Analytics Platform

Suppose a company runs an analytics platform on EKS. The platform uses eighty worker nodes, three control-plane nodes, fifty terabytes of persistent storage, and moderate data egress. The cloud bill looks high enough that executives ask for an on-premises study. The first instinct might be to compare node prices against server prices, but that would miss the point. The correct analysis compares three-year total cost, operational readiness, and workload fit.

Here is a small runnable calculator that illustrates the structure of the model. It is intentionally simple, so learners can modify the assumptions without needing a finance tool. Save it as `tco.py`, run it with `.venv/bin/python tco.py` from a repository that already has a Python virtual environment, or use any Python 3.12 environment if you are studying outside this project.

```python
cloud_monthly = {
    "compute": 11200,
    "managed_kubernetes": 73,
    "storage": 4096,
    "egress": 461,
    "support_and_observability": 2500,
}

on_prem_upfront = {
    "servers": 180000,
    "networking": 60000,
    "storage_expansion": 40000,
    "spares_and_rack_setup": 30000,
}

on_prem_monthly = {
    "colocation": 4500,
    "power": 3000,
    "staffing": 29166,
    "hardware_maintenance": 2000,
    "network_transit": 1800,
    "backup_and_security_tools": 2400,
}

years = 3
months = years * 12

cloud_three_year = sum(cloud_monthly.values()) * months
on_prem_three_year = sum(on_prem_upfront.values()) + sum(on_prem_monthly.values()) * months

print(f"Cloud monthly: ${sum(cloud_monthly.values()):,.0f}")
print(f"Cloud 3-year: ${cloud_three_year:,.0f}")
print(f"On-prem upfront: ${sum(on_prem_upfront.values()):,.0f}")
print(f"On-prem monthly: ${sum(on_prem_monthly.values()):,.0f}")
print(f"On-prem 3-year: ${on_prem_three_year:,.0f}")

if cloud_three_year < on_prem_three_year:
    print("Recommendation: optimize cloud first; on-prem does not clear the cost gate.")
else:
    print("Recommendation: continue on-prem evaluation; cost gate may be satisfied.")
```

In this scenario, on-premises does not automatically win. The staffing line changes the result more than most beginners expect. Even if hardware pricing looks attractive, a small platform may not have enough scale to amortize the people and facilities needed to operate it well. A senior engineer would present the result as a decision gate: cost does not justify migration yet, unless another driver such as regulation or latency is strong enough to override pure economics.

> **Active learning check:** Change the calculator so the platform has two hundred worker nodes and one hundred fifty terabytes of storage. Keep the staffing number realistic rather than pretending the same two engineers can operate a much larger estate. Does the recommendation change, and which input changed the result most?

---

## Diagnosing Organizational Readiness

Organizational readiness is the part of on-premises planning that technical teams often under-scaffold. A cluster can pass a benchmark while the organization remains unready to operate it. Readiness means the team can repeatedly provision nodes, recover from hardware failures, rotate credentials, apply security patches, upgrade Kubernetes, restore data, test disaster recovery, and communicate incidents without depending on one heroic engineer.

A useful readiness review examines capabilities rather than job titles. A team may have excellent cloud engineers who understand Kubernetes deeply but have limited experience with BGP, switch firmware, disk failure modes, storage rebuild pressure, or remote hands procedures. Another team may have traditional datacenter engineers who understand hardware well but need stronger GitOps and Kubernetes automation. The gap is not a reason to reject on-premises automatically; it is a reason to plan training, hiring, automation, and a slower migration gate.

| Capability | Minimum credible evidence | Risk if missing |
|---|---|---|
| Bare-metal provisioning | A node can be rebuilt from empty hardware to schedulable Kubernetes node through automation | Manual rebuilds create inconsistent hosts and long recovery times |
| Network operations | The team can explain routing, load balancing, firewalling, and failover paths | Incidents become difficult to diagnose under packet loss or route failure |
| Storage operations | Backup, restore, replication, and disk-failure tests are documented and practiced | Data loss or long recovery during the first serious storage event |
| Kubernetes lifecycle | Upgrades are tested in staging with rollback and conformance checks | Version skew, security exposure, and failed upgrades accumulate |
| Observability | Hardware, OS, network, storage, cluster, and app signals are correlated | Teams see symptoms but cannot locate the failing layer |
| Security evidence | Host hardening, access control, patching, and audit logs are continuously collected | Compliance work becomes a manual scramble before audits |
| Incident response | On-call, escalation, vendor support, and remote hands procedures are tested | Small incidents wait for the one person who knows the system |

Readiness has a practical output: a go, no-go, or close-gaps decision. "Go" means the organization can begin a limited pilot with controlled risk. "No-go" means the constraints do not justify the burden or the team cannot staff it. "Close gaps" means the on-premises direction may be correct, but the next quarter should focus on automation, hiring, training, vendor selection, and operational drills before production migration begins.

```text
┌────────────────────────────────────────────────────────────────────┐
│                      READINESS DECISION GATE                       │
│                                                                    │
│  Technical prototype passes?                                       │
│        │                                                           │
│        ├── No  → keep experimenting outside production             │
│        │                                                           │
│        └── Yes                                                     │
│             │                                                      │
│             ▼                                                      │
│  Operational runbooks tested under failure?                        │
│        │                                                           │
│        ├── No  → close readiness gaps before migration             │
│        │                                                           │
│        └── Yes                                                     │
│             │                                                      │
│             ▼                                                      │
│  Staffing, support, and rollback funded?                           │
│        │                                                           │
│        ├── No  → do not start production migration                 │
│        │                                                           │
│        └── Yes → begin phased migration with explicit gates         │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

The readiness review should be uncomfortable. It should ask who replaces a failed switch during a holiday weekend, who approves emergency firmware updates, how secrets are recovered if a control-plane node fails, how the team proves backup integrity, and which workloads are allowed to fail back to cloud. These questions are not bureaucracy. They are the difference between a platform that survives real operations and a platform that only looked good during installation.

---

## Planning a Phased Migration Strategy

A phased migration strategy turns an on-premises decision into a controlled learning process. The goal is not to move everything as quickly as possible. The goal is to reduce uncertainty in the safest order: first prove the platform can be built repeatedly, then prove it can serve low-risk workloads, then prove it can handle state and failure, and only then reduce cloud dependency. Each phase should have entry criteria, exit criteria, rollback options, and a clear owner.

The previous sections focused heavily on evaluation. Planning requires a different skill: sequencing. A senior migration plan moves from reversible to less reversible decisions. It avoids migrating stateful systems before network and observability are stable. It avoids decommissioning cloud capacity before recovery paths are tested. It also avoids declaring success after a single good day. Production platforms need sustained evidence.

```text
┌────────────────────────────────────────────────────────────────────┐
│                    PHASED MIGRATION OVERVIEW                       │
│                                                                    │
│  Phase 1          Phase 2             Phase 3          Phase 4      │
│  Foundation  ──▶  Stateless pilot ──▶ Stateful pilot ─▶ Cutover    │
│                                                                    │
│  Build repeatable  Serve limited       Move selected    Shift main  │
│  clusters and      traffic while       data workloads   production  │
│  operations        cloud remains       after restore    only after  │
│  evidence          the fallback        tests pass       gates pass  │
│                                                                    │
│  Reversible        Mostly reversible   Riskier          Least       │
│  decisions         decisions           decisions        reversible  │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

### Worked Scenario: Migrating a Regulated Analytics Platform

Imagine a healthcare analytics company running a managed Kubernetes platform in cloud. The platform processes medical imaging data, trains models, and serves inference results to hospital systems. The business drivers are strong: five hundred terabytes of sensitive data, high storage cost, audit pressure around physical safeguards, and inference workloads that benefit from GPUs and local NVMe. The team is not ready for a full cutover, but the evidence supports a serious on-premises pilot.

The plan starts with a small but production-shaped foundation. The team leases colocation space in two facilities, buys enough hardware for a non-critical workload slice, and builds an automated provisioning path using tools such as Cluster API, Metal3, Tinkerbell, or vendor-supported bare-metal automation. The exact tool is less important than the outcome: a failed node can be replaced by process, not memory. The team also creates observability that spans hardware, OS, network, storage, Kubernetes, and application metrics.

Phase two moves stateless services first. The team sends five percent of read-only inference traffic to the on-premises cluster while cloud remains the main serving path. This phase tests ingress, service discovery, certificate automation, logging, deployment pipelines, and on-call readiness. The rollback is simple: route traffic back to cloud. The exit gate is not "traffic worked once." It is stable latency, error rate, deployment success, and incident handling for a defined observation window.

Phase three introduces state cautiously. The team migrates a replicated cache or a non-critical data processing queue before attempting primary databases. They test backup restores, storage node failure, network partition behavior, and data consistency. They also verify that compliance evidence can be produced without manual heroics. If restore time misses the recovery objective, the phase does not pass. The platform team improves storage design and tries again.

Phase four shifts primary production only after the prior gates have produced sustained evidence. Cloud resources are not immediately destroyed. They are reduced gradually while disaster recovery, burst capacity, and rollback options remain funded. The business may decide that the final architecture remains hybrid permanently, and that can be a successful outcome. A good migration plan optimizes for business risk, not ideological purity.

| Phase | Primary question | Entry criteria | Exit criteria | Rollback path |
|---|---|---|---|---|
| Foundation and tooling | Can we build and rebuild the platform repeatably? | Site, hardware, network, automation, and observability plan approved | Bare-metal cluster build is automated and conformance tests pass repeatedly | Keep all production workloads in cloud |
| Stateless pilot | Can the platform serve real traffic safely? | Foundation exit gate passed and traffic routing is controllable | Limited production traffic meets latency, error, and deployment baselines | Route traffic back to cloud load balancers |
| Stateful pilot | Can the platform protect and recover data? | Stateless operations stable and storage design reviewed | Restore, failover, consistency, and backup tests meet objectives | Promote cloud data path or restore from tested backup |
| Production cutover | Can the organization operate this as the primary platform? | Stateful gate passed and support model funded | Main workloads stable for a defined period with cloud spend reduced as planned | Execute documented failback or hybrid continuation plan |

> **Active learning check:** In the healthcare analytics scenario, the CTO asks to move the primary database during phase two because the cloud database bill is high. Write a short response explaining why the plan should or should not change. Your answer should reference reversibility, evidence, and recovery testing.

### A Practical Migration Template

Use this template when you design your own phased strategy. It intentionally asks for measurable gates because vague phrases such as "platform stable" do not protect learners or production systems. A gate should be something a reviewer can verify with logs, dashboards, test reports, or cost data.

| Planning field | What to write | Example |
|---|---|---|
| Workload slice | Which services or data move in this phase | Read-only inference API for two hospital tenants |
| Business reason | Why this slice belongs in this phase | High latency sensitivity but no write-path risk |
| Technical dependency | What must exist before the phase starts | Private connectivity, certificates, ingress, metrics, deployment pipeline |
| Success metric | How the phase proves progress | p95 latency at or below cloud baseline for thirty days |
| Failure trigger | What condition stops or rolls back the phase | Error budget burn exceeds agreed threshold for two consecutive days |
| Rollback mechanism | How the team returns to a safer state | DNS and load balancer weights route all traffic back to cloud |
| Evidence artifact | What proves the gate passed | Dashboard export, incident review, conformance report, restore log |

A phased strategy also needs decision rights. Someone must be allowed to stop the migration when evidence is weak. That person should not be punished for protecting the platform. The plan should define who approves phase entry, who owns rollback, who communicates risk to stakeholders, and who signs off on decommissioning cloud resources. Without decision rights, gates become decoration.

---

## Building the Recommendation

A recommendation should be short enough for executives to understand and detailed enough for engineers to trust. It should name the target model, the reason, the expected benefit, the main risks, and the next decision gate. Avoid presenting on-premises as a guaranteed savings plan unless the TCO model proves it under realistic assumptions. Avoid presenting cloud as a default forever if the evidence shows durable drivers for change.

A useful structure is: decision, evidence, risks, next step. For example: "Adopt a hybrid model. Move regulated imaging inference and hot storage to two colocation sites over twelve months, while keeping development, burst analytics, and disaster recovery in cloud. The recommendation is supported by storage cost, latency tests, and audit evidence needs. The largest risks are staffing, storage operations, and migration rollback, so the next step is a ninety-day foundation pilot with explicit failure tests." This format shows judgment without hiding complexity.

| Recommendation type | When it fits | What to say |
|---|---|---|
| Stay in cloud and optimize | Drivers are weak or readiness is low | Rightsize, commit capacity, improve architecture, and revisit after measurable gaps close |
| Run a limited pilot | Drivers are plausible but evidence is incomplete | Test one workload slice, collect benchmarks, and decide after operational gates |
| Adopt hybrid | Some workloads need locality or control while others benefit from cloud | Place workloads by constraint and keep cloud where it remains the better tool |
| Move primary platform on-premises | Multiple strong drivers align and readiness is credible | Migrate in phases with rollback, DR, staffing, and evidence gates funded upfront |
| Reject on-premises | The plan is driven by hype or incomplete math | Explain which assumptions fail and propose a safer alternative |

The recommendation must also include what would change your mind. This is a mark of senior reasoning. If cloud costs double without a matching discount, the cost gate may change. If auditors accept cloud evidence, the sovereignty driver may weaken. If the team hires experienced infrastructure engineers and automates provisioning, readiness may improve. If product strategy shifts toward global expansion, cloud may become more valuable. A decision model that can update is stronger than a one-time verdict.

---

## Did You Know?

- **Kubernetes was influenced by Google's Borg system**, which ran massive workloads on Google's own infrastructure before Kubernetes became widely associated with managed cloud services.

- **Dropbox publicly described major infrastructure savings after reducing reliance on public cloud storage**, but the move required deep engineering investment, custom systems, and enough scale to justify the work.

- **Cloud repatriation stories often involve steady, high-utilization workloads**, not small or unpredictable systems where elasticity and managed services still dominate the economics.

- **Many mature organizations choose hybrid architectures permanently**, because different workloads have different constraints and a single hosting model rarely optimizes every dimension at once.

---

## Common Mistakes

| Mistake | Why it hurts | Better approach |
|---|---|---|
| Comparing public cloud list prices against discounted hardware | The model exaggerates cloud cost and hides real negotiated pricing | Use the actual bill, committed-use options, support costs, and realistic hardware quotes |
| Treating existing engineers as free on-premises staff | The same team must absorb hardware, network, storage, and lifecycle work | Model staffing explicitly and define which current work will stop or be automated |
| Moving stateful workloads before proving operations | Storage failures create data risk and long recovery windows | Start with foundation and stateless traffic, then test restore and failover before stateful migration |
| Ignoring managed-service dependencies | Replacing cloud databases, queues, analytics, and identity services can dwarf compute savings | Inventory dependencies and decide which remain cloud, which move, and which are redesigned |
| Buying hardware for rare peak demand | Idle servers erase economic benefits and reduce flexibility | Size for steady demand, keep burst capacity in cloud, or use hybrid overflow |
| Under-designing the network | Kubernetes east-west traffic, storage replication, and ingress can overwhelm weak fabrics | Plan redundant switching, routing, bandwidth, observability, and failure testing early |
| Skipping rollback planning | Teams discover too late that decommissioned cloud paths cannot be restored quickly | Keep rollback funded until production evidence supports reducing cloud capacity |
| Using compliance as a vague argument | Auditors need evidence, not architecture slogans | Name the exact control, evidence gap, jurisdiction, or resilience requirement being addressed |

---

## Quiz

### Question 1

Your company runs thirty Kubernetes worker nodes in a managed cloud service and spends heavily on compute. A hardware vendor says equivalent servers would be much cheaper over three years. The platform team has two engineers, both focused on application delivery and cloud automation. What should you recommend, and what evidence would you collect before revisiting the decision?

<details>
<summary>Answer</summary>

You should recommend optimizing cloud first rather than starting a production on-premises migration. At thirty nodes, staffing and operational overhead can erase apparent hardware savings, especially when the existing team does not have spare capacity for hardware, network, storage, and lifecycle work. The vendor quote is only one input, not a full TCO model.

Before revisiting the decision, collect the actual cloud bill, utilization data, committed-use discount options, managed-service dependency inventory, incident history, and a staffing plan. If the workload grows substantially, becomes steadier, or develops a regulatory or latency driver, a limited pilot may become reasonable.
</details>

### Question 2

A healthcare analytics company stores five hundred terabytes of imaging data and runs GPU inference near hospital systems. Auditors are asking for stronger evidence around physical safeguards, and traces show cloud network distance consumes a meaningful part of the inference budget. Which hosting model should you evaluate, and why?

<details>
<summary>Answer</summary>

You should evaluate a hybrid or on-premises model for the sensitive storage and inference path. Multiple durable drivers align: large data volume, latency sensitivity, hardware specialization, and compliance evidence around physical safeguards. This is much stronger than a simple cost complaint.

The recommendation should still be phased. Keep lower-risk services, development environments, burst analytics, or disaster recovery in cloud where they fit well. Start with a foundation pilot, then limited stateless inference traffic, then carefully tested stateful migration after restore and failover evidence exists.
</details>

### Question 3

A retail company wants to leave cloud because peak-season bills are painful. Utilization reports show the platform runs at low average capacity for most of the year, then spikes sharply during two major sales events. The executive sponsor argues that owning hardware will avoid surprise bills. How do you respond?

<details>
<summary>Answer</summary>

You should challenge the assumption that on-premises will reduce total cost. A bursty workload is often a strong cloud signal because cloud elasticity avoids buying hardware that sits idle most of the year. If the company buys enough private capacity for peak events, it may waste capital during normal months. If it buys for average demand, it may fail during the events that matter most.

A better recommendation is to optimize cloud autoscaling, reserved or committed capacity for the steady baseline, and perhaps use hybrid overflow only if there is a stable core workload. The decision should be based on utilization curves, not the emotional impact of peak invoices.
</details>

### Question 4

Your CTO asks to migrate the primary database in the second phase of an on-premises migration because it is the largest cloud cost. The foundation cluster exists, but the team has not completed storage failure tests, restore drills, or network partition tests. What should you do?

<details>
<summary>Answer</summary>

You should reject moving the primary database in that phase and explain the risk in terms of reversibility and evidence. Databases are less reversible than stateless services because data consistency, restore time, replication behavior, and failure handling must be proven before production migration. A high bill does not remove the need for recovery evidence.

The safer plan is to continue with stateless or read-only traffic first, then pilot a lower-risk stateful component. The database can move only after backup restore, failover, storage node failure, and data consistency tests meet the agreed recovery objectives.
</details>

### Question 5

A defense contractor says cloud is impossible because "compliance requires on-premises." During review, nobody can name the exact regulation, data category, jurisdiction, or evidence gap. What is the right next step?

<details>
<summary>Answer</summary>

The right next step is to turn the compliance claim into specific requirements before making an architecture decision. Ask legal, risk, and security teams to identify the data category, applicable control regime, location restrictions, third-party dependency limits, and required evidence. Without those details, "compliance" is a slogan rather than a design constraint.

The final answer may still be on-premises, government cloud, sovereign cloud, or hybrid. The hosting model should follow from named controls and evidence requirements, not from an untested assumption.
</details>

### Question 6

A platform team builds a successful bare-metal Kubernetes proof of concept. Nodes join the cluster, conformance tests pass, and a demo application works. Leadership wants to approve full migration immediately. Which readiness gaps should you check before agreeing?

<details>
<summary>Answer</summary>

You should check operational readiness beyond installation success. The team must prove automated reprovisioning, hardware failure handling, network failover, storage backup and restore, Kubernetes upgrades, observability across layers, security evidence collection, and incident response. A proof of concept that only demonstrates installation does not prove production operability.

The decision should move to a gated pilot only if runbooks, staffing, vendor support, rollback paths, and failure tests are credible. Otherwise, the next phase should close readiness gaps before production workloads move.
</details>

### Question 7

An engineering director proposes a hybrid model: keep product development, CI, and burst analytics in cloud, but move regulated low-latency inference and hot storage to two colocation sites. What makes this recommendation stronger than "move everything" or "stay cloud forever"?

<details>
<summary>Answer</summary>

The hybrid recommendation places workloads according to their constraints. Regulated low-latency inference and hot storage have strong locality, data volume, and compliance drivers, so private infrastructure may be justified. Development, CI, and burst analytics benefit from elasticity, managed services, and speed, so cloud remains a good fit.

This is stronger because it avoids treating hosting as an ideology. It preserves cloud advantages where they matter while investing on-premises effort only where evidence supports it.
</details>

---

## Hands-On Exercise: Build a Cloud vs On-Prem Decision Brief

**Task**: Create a decision brief for a realistic workload and defend whether it should stay in cloud, move to on-premises, or adopt a hybrid model. The goal is not to prove one answer. The goal is to show disciplined reasoning that an executive and a senior engineer could both review.

### Scenario

Your company runs a data analytics platform with the following profile. It currently uses managed Kubernetes in a public cloud region. The business is growing, and leadership wants to know whether the next platform investment should remain cloud-first or include an on-premises build.

- Eighty worker nodes equivalent to four vCPU and sixteen gigabytes of memory each.
- Three managed control-plane nodes hidden behind the provider service.
- Fifty terabytes of persistent storage with steady monthly growth.
- Five terabytes of monthly egress to external customers and partners.
- Moderate latency sensitivity, but no confirmed sub-millisecond requirement.
- Two platform engineers who currently manage cloud infrastructure, CI/CD, and observability.
- Several managed-service dependencies, including hosted database, object storage, and queueing.

### Step 1: Build the Current-State Summary

Write a short paragraph describing the workload in operational terms. Include whether utilization is steady or bursty, which services are managed by the cloud provider, and which business constraints are confirmed versus assumed. Do not start with cost. Start with what the system does and which constraints matter.

### Step 2: Estimate Cloud Cost

Use the actual bill if you have one. If you do not, build a rough model from compute, managed Kubernetes fees, storage, egress, support, observability, backup, and managed services. Record whether committed-use discounts or reserved capacity could reduce the cost without changing the hosting model.

### Step 3: Estimate On-Premises Cost

Include servers, storage, network gear, racks, colocation, power, cooling, hardware maintenance, spares, monitoring, backup tooling, security tooling, and staffing. Treat staffing as a real cost even if the engineers are already employed, because time spent operating infrastructure is time not spent elsewhere.

### Step 4: Score the Five Drivers

For each driver, assign a strength of low, medium, or high and explain the evidence. The five drivers are sovereignty, latency, economics at scale, control, and compliance simplification. If you cannot produce evidence for a driver, mark it as an assumption rather than inflating the score.

### Step 5: Diagnose Readiness

Evaluate the team's readiness for bare-metal provisioning, network operations, storage operations, Kubernetes lifecycle, observability, security evidence, and incident response. Identify at least three gaps that must be closed before any production migration.

### Step 6: Recommend a Target Model

Choose one of these recommendations: stay in cloud and optimize, run a limited pilot, adopt hybrid, move primary platform on-premises, or reject on-premises for now. Your recommendation must include the reason, the strongest supporting evidence, the largest risk, and the next decision gate.

### Step 7: Draft a Phased Migration Plan if Needed

If your recommendation includes a pilot, hybrid model, or on-premises migration, write a four-phase plan. Each phase must include workload slice, entry criteria, exit criteria, success metrics, failure triggers, rollback mechanism, and evidence artifact.

### Success Criteria

- [ ] Decision brief starts with workload constraints rather than a predetermined answer.
- [ ] Cloud cost model uses actual or clearly stated pricing assumptions.
- [ ] On-premises cost model includes hardware, network, facility, staffing, support, and tooling.
- [ ] Five drivers are scored with evidence rather than opinion.
- [ ] Readiness review identifies at least three operational gaps.
- [ ] Recommendation names one target model and explains why alternatives are weaker.
- [ ] Migration plan includes measurable gates if any workload moves.
- [ ] Rollback paths remain funded until production evidence supports reducing them.
- [ ] Final brief states what evidence would change the recommendation later.

---

## Key Takeaways

On-premises Kubernetes is a deployment model with real advantages and real costs. It can be the right answer for regulated data, strict latency, large steady workloads, specialized hardware, and organizations that need direct control over infrastructure. It can be the wrong answer for small teams, bursty products, short-lived projects, heavy managed-service architectures, and organizations without operational maturity.

The strongest decisions combine evidence from multiple dimensions. Cost matters, but cost alone is not enough. Compliance matters, but only when the control requirement is specific. Control matters, but only when it improves a measurable outcome. A serious recommendation names the workload slices that should move, the ones that should stay, and the evidence required before each phase proceeds.

Phased migration is the practical bridge between evaluation and execution. Start with reversible steps, prove the foundation, move stateless traffic, test stateful recovery, and cut over only after gates pass. A migration plan without rollback is optimism. A migration plan with evidence gates is engineering.

---

## Further Reading

- "The Cloud Exit" by 37signals for a public example of cloud repatriation economics and the organizational debate around it.
- Dropbox public engineering and financial discussions about reducing public cloud storage dependence at very large scale.
- CNCF materials on Kubernetes operations, cluster lifecycle, and production readiness for organizations running their own infrastructure.
- Regulatory guidance relevant to your sector, because the exact control requirement matters more than generic compliance language.
- Vendor documentation for Cluster API, Metal3, Tinkerbell, Talos, Flatcar, Ceph, and other tools commonly used in bare-metal Kubernetes platforms.

---

## Next Module

Continue to [Module 1.2: Server Sizing & Hardware Selection](../module-1.2-server-sizing/) to learn how to translate workload requirements into server, storage, and network capacity decisions.

## Sources

- [Kubernetes Production Environment](https://kubernetes.io/docs/setup/production-environment/) — Upstream guidance on the availability, scaling, security, and node-management work that comes with self-managed clusters.
- [Out of the Clouds onto the Ground](https://kubernetes.io/blog/2018/08/03/out-of-the-clouds-onto-the-ground-how-to-make-kubernetes-production-grade-anywhere/) — Kubernetes guidance specifically focused on making clusters production-grade outside public cloud environments.
- [Google Cloud Hybrid Deployment Archetype](https://docs.cloud.google.com/architecture/deployment-archetypes/hybrid) — Concrete hybrid patterns help frame when some workload slices should stay on-premises and others should remain in cloud.
