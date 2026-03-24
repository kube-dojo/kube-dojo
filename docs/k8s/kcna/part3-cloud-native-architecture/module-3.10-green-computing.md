# Module 3.10: Green Computing and Sustainability

> **Complexity**: `[QUICK]` - Awareness level
>
> **Time to Complete**: 20-25 minutes
>
> **Prerequisites**: Module 3.1 (Cloud Native Principles), Module 3.2 (CNCF Ecosystem)

---

## Why This Module Matters

Data centers consume 1-2% of global electricity — roughly the same as the entire aviation industry. As cloud native adoption accelerates, so does its environmental footprint. The CNCF has recognized this with a dedicated TAG (Technical Advisory Group) for Environmental Sustainability. KCNA expects awareness of how cloud native practices intersect with sustainability and what the community is doing about it.

> **"The greenest compute is the compute you don't use."**

This simple principle drives everything in this module: eliminate waste first, then make what remains as efficient as possible.

---

## The Carbon Footprint of Cloud

```
┌─────────────────────────────────────────────────────────────┐
│              CLOUD'S ENVIRONMENTAL IMPACT                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Data centers globally:                                     │
│  • 1-2% of global electricity consumption                  │
│  • Growing 20-30% annually with AI/ML demand               │
│  • A single large hyperscaler campus can use more          │
│    electricity than a small city                           │
│                                                             │
│  Where the energy goes:                                     │
│  ─────────────────────────────────────────────────────────  │
│                                                             │
│  COMPUTE   ████████████████████████  ~40-50%               │
│  COOLING   ████████████████         ~30-40%                │
│  STORAGE   ██████                   ~10-15%                │
│  NETWORK   ████                     ~5-10%                 │
│                                                             │
│  Carbon sources:                                            │
│  ─────────────────────────────────────────────────────────  │
│                                                             │
│  OPERATIONAL  Energy consumed running workloads            │
│  (Scope 2)    → Depends on the electricity grid            │
│                                                             │
│  EMBODIED     Manufacturing servers, GPUs, network gear    │
│  (Scope 3)    → Fixed cost regardless of utilization       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Why Cloud Native Makes It Better (and Worse)

| Cloud Native Benefit | Sustainability Impact |
|----------------------|----------------------|
| **Autoscaling** | Scale down when idle = less energy wasted |
| **Containerization** | Higher density per server = fewer servers needed |
| **Microservices** | Can scale individual components, not monoliths |
| **Scale-to-zero** | Serverless/KEDA can eliminate idle consumption |

| Cloud Native Risk | Sustainability Impact |
|-------------------|----------------------|
| **Over-provisioning** | Requesting 4 CPU but using 0.5 = 87% waste |
| **Zombie workloads** | Forgotten Deployments running indefinitely |
| **AI/ML explosion** | GPU-intensive training consumes enormous energy |
| **Microservice sprawl** | 200 services with sidecar proxies add overhead |

---

## CNCF TAG Environmental Sustainability

The **CNCF TAG Environmental Sustainability** is the community's organized effort to address cloud native's environmental impact.

```
┌─────────────────────────────────────────────────────────────┐
│              TAG ENVIRONMENTAL SUSTAINABILITY                │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  What TAGs are:                                             │
│  Technical Advisory Groups — cross-project working groups  │
│  that advise the CNCF community on specific topics         │
│                                                             │
│  What this TAG does:                                        │
│  ─────────────────────────────────────────────────────────  │
│  • Defines best practices for sustainable cloud native     │
│  • Evaluates tools and projects for energy efficiency      │
│  • Publishes the Cloud Native Sustainability Landscape     │
│  • Advocates for carbon-awareness in CNCF projects         │
│  • Creates standards for measuring environmental impact    │
│                                                             │
│  Key output: Cloud Native Sustainability Landscape          │
│  (maps tools and projects related to sustainability)        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

> **For KCNA**: Know that CNCF has a TAG specifically for Environmental Sustainability and that the community takes this seriously.

---

## Kepler: Measuring Energy Per Pod

**Kepler** (Kubernetes-based Efficient Power Level Exporter) is the most important project in this space. You cannot reduce what you cannot measure.

```
┌─────────────────────────────────────────────────────────────┐
│              KEPLER                                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  What: Exports energy consumption metrics per Pod          │
│  How:  Uses eBPF and hardware counters (RAPL, ACPI)       │
│  Output: Prometheus metrics (Watts per Pod/container)      │
│  Status: CNCF Sandbox project                              │
│                                                             │
│  ┌──────────────────────────────────────────────────┐      │
│  │                Kubernetes Node                    │      │
│  │                                                    │      │
│  │  ┌─────────────┐  ┌─────────────┐                │      │
│  │  │   Pod A      │  │   Pod B      │                │      │
│  │  │  150 mW      │  │  800 mW      │                │      │
│  │  └─────────────┘  └─────────────┘                │      │
│  │                                                    │      │
│  │  ┌──────────────────────────────────────────┐    │      │
│  │  │  Kepler (DaemonSet)                       │    │      │
│  │  │  Uses eBPF to track CPU cycles per Pod   │    │      │
│  │  │  Maps cycles → energy using power models │    │      │
│  │  │  Exports as Prometheus metrics           │    │      │
│  │  └──────────────────────────────────────────┘    │      │
│  └──────────────────────────────────────────────────┘      │
│                          │                                  │
│                          ▼                                  │
│                    Prometheus → Grafana                     │
│                    (energy dashboards)                      │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

> **Key insight**: Kepler gives you per-Pod energy visibility. Without it, you only know total server power draw — you cannot tell which workloads are responsible. This is like FinOps cost allocation, but for carbon.

---

## Carbon-Aware Scheduling

Not all electricity is created equal. A kilowatt-hour at midnight in Norway (hydropower) has far less carbon impact than a kilowatt-hour at noon in a coal-heavy grid.

```
┌─────────────────────────────────────────────────────────────┐
│              CARBON-AWARE SCHEDULING                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Idea: Run workloads WHEN and WHERE the grid is cleanest  │
│                                                             │
│  TEMPORAL SHIFTING (when)                                   │
│  ─────────────────────────────────────────────────────────  │
│  Delay non-urgent jobs to times when grid carbon           │
│  intensity is lowest                                       │
│                                                             │
│  Example: Training job can run tonight when wind           │
│  power peaks and grid is 80% cleaner                      │
│                                                             │
│  ┌────────────────────────────────────────────┐            │
│  │  Carbon intensity over 24 hours:           │            │
│  │                                            │            │
│  │  High  ████                    ████        │            │
│  │        ████████            ████████        │            │
│  │  Low       ████████████████                │            │
│  │       6am    noon    6pm    midnight       │            │
│  │                                            │            │
│  │  → Schedule batch jobs in the LOW windows  │            │
│  └────────────────────────────────────────────┘            │
│                                                             │
│  SPATIAL SHIFTING (where)                                   │
│  ─────────────────────────────────────────────────────────  │
│  Route workloads to regions with cleaner grids             │
│                                                             │
│  Example: Run in Sweden (hydro) instead of                 │
│  Poland (coal) when possible                               │
│                                                             │
│  Data source: Carbon intensity APIs                        │
│  (WattTime, Electricity Maps, Carbon Aware SDK)            │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

> **Important nuance**: Carbon-aware scheduling only works for **deferrable** or **movable** workloads. Your production API serving user requests cannot wait until midnight. But batch processing, model training, backups, and CI/CD pipelines often can.

---

## Sustainable Cloud Native Practices

### Right-Sizing: The Biggest Win

The single most impactful thing most organizations can do is stop over-provisioning.

```
┌─────────────────────────────────────────────────────────────┐
│              THE OVER-PROVISIONING PROBLEM                   │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Typical Kubernetes cluster utilization: 15-25%            │
│                                                             │
│  Requested:  ████████████████████████████████  2 CPU       │
│  Actually                                                   │
│  used:       ████████                          0.5 CPU     │
│                                                             │
│  That means 75% of allocated resources are WASTED          │
│  Wasted resources = wasted energy = wasted carbon          │
│                                                             │
│  Solutions:                                                 │
│  ─────────────────────────────────────────────────────────  │
│  • VPA (Vertical Pod Autoscaler): auto-adjust requests     │
│  • Regular audits: review resource requests vs actual use  │
│  • Goldilocks: recommends resource settings per workload   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Key Practices

| Practice | What It Means | Impact |
|----------|---------------|--------|
| **Right-sizing** | Match resource requests to actual usage | Reduces wasted compute by 50-75% |
| **Scale-to-zero** | Shut down workloads with no traffic (KEDA, Knative) | Eliminates idle energy consumption |
| **Spot/preemptible instances** | Use excess cloud capacity that would otherwise be wasted | Uses resources that already exist |
| **Bin packing** | Pack Pods efficiently onto fewer nodes | Fewer nodes powered on |
| **Cluster autoscaling** | Remove nodes when demand drops | Scale down infrastructure, not just Pods |
| **Kill zombie workloads** | Find and remove forgotten Deployments | Stops wasting energy on unused services |
| **Efficient images** | Smaller container images, distroless bases | Less network transfer, faster pulls |

---

## GreenOps: Where FinOps Meets Sustainability

```
┌─────────────────────────────────────────────────────────────┐
│              GREENOPS                                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  FinOps:    "How much does this workload COST?"            │
│  GreenOps:  "How much CARBON does this workload emit?"     │
│                                                             │
│  They overlap heavily:                                      │
│  ─────────────────────────────────────────────────────────  │
│  • Over-provisioned resources waste money AND energy       │
│  • Idle workloads cost money AND emit carbon               │
│  • Right-sizing saves money AND reduces emissions          │
│  • Spot instances are cheaper AND use excess capacity      │
│                                                             │
│  The key difference:                                        │
│  ─────────────────────────────────────────────────────────  │
│  • FinOps metric: dollars                                  │
│  • GreenOps metric: grams of CO2 equivalent (gCO2eq)      │
│                                                             │
│  GreenOps adds:                                             │
│  • Carbon intensity of the electricity grid                │
│  • Embodied carbon of hardware                             │
│  • Carbon-aware scheduling decisions                       │
│  • Sustainability reporting and compliance                 │
│                                                             │
│  ┌─────────────────────────────────────┐                   │
│  │  FinOps ∩ GreenOps = reduce waste  │                   │
│  │                                     │                   │
│  │  Most FinOps actions are also       │                   │
│  │  good GreenOps actions              │                   │
│  └─────────────────────────────────────┘                   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Tools and Projects

| Tool/Project | What It Does | Status |
|-------------|-------------|--------|
| **Kepler** | Measures energy consumption per Pod using eBPF | CNCF Sandbox |
| **Green Software Foundation** | Cross-industry org defining green software patterns and standards | Industry body |
| **Carbon Aware SDK** | Library to query carbon intensity of electricity grids | Green Software Foundation |
| **Kube-green** | Shuts down non-production workloads during off-hours automatically | Open source |
| **Goldilocks** | Recommends right-sized resource requests using VPA data | Fairwinds open source |
| **Cloud Carbon Footprint** | Estimates carbon emissions from cloud provider usage | Open source (ThoughtWorks) |

---

## Did You Know?

- **Training a single large AI model can emit as much CO2 as five cars over their lifetime** — Researchers estimated that training GPT-3 consumed approximately 1,287 MWh of electricity. The AI boom is making data center sustainability the most urgent infrastructure challenge of the decade.

- **Most Kubernetes clusters run at 15-25% utilization** — This means 75-85% of provisioned compute capacity is wasted. If every organization right-sized their clusters, the collective energy savings would be massive — equivalent to shutting down thousands of data centers worldwide.

- **Iceland and the Nordics are becoming AI data center hotspots** — Not just because of cold air (free cooling) but because of abundant renewable energy (geothermal, hydro, wind). Carbon-aware location decisions are already reshaping where data centers are built.

---

## Common Mistakes

| Mistake | Why It Hurts | Correct Understanding |
|---------|--------------|----------------------|
| Ignoring sustainability as "not my job" | Regulatory and customer pressure is increasing | Engineers make the provisioning decisions that determine energy consumption |
| Only focusing on operational carbon | Misses a big piece of the picture | Embodied carbon (manufacturing hardware) can be 50%+ of total — extending hardware life matters |
| Over-provisioning "just in case" | The default behavior in most orgs, massive waste | Use autoscaling and VPA instead of static over-provisioning |
| Assuming cloud = green | Cloud providers are not carbon-neutral by default | Cloud region and time-of-day matter; not all regions use renewable energy |
| Carbon-aware scheduling for everything | Not all workloads can be deferred | Only deferrable workloads (batch, training, CI/CD) benefit; latency-sensitive services cannot wait |

---

## Quiz

**1. What does Kepler measure in a Kubernetes cluster?**

A) Network latency between Pods
B) Energy consumption per Pod
C) Carbon intensity of the electricity grid
D) Financial cost of each workload

<details>
<summary>Answer</summary>

**B) Energy consumption per Pod.** Kepler (Kubernetes-based Efficient Power Level Exporter) uses eBPF and hardware power counters to estimate energy consumption at the Pod level, exporting metrics to Prometheus. It is a CNCF Sandbox project.
</details>

**2. What is carbon-aware scheduling?**

A) Scheduling workloads only on ARM-based servers
B) Running workloads when and where the electricity grid is cleanest
C) Automatically shutting down all workloads at night
D) Using carbon fiber network cables for better performance

<details>
<summary>Answer</summary>

**B) Running workloads when and where the electricity grid is cleanest.** Carbon-aware scheduling uses temporal shifting (run at cleaner times) and spatial shifting (run in cleaner regions) to reduce the carbon footprint of deferrable workloads like batch jobs and model training.
</details>

**3. What is the typical resource utilization rate in Kubernetes clusters?**

A) 80-90%
B) 50-60%
C) 15-25%
D) 1-5%

<details>
<summary>Answer</summary>

**C) 15-25%.** Most Kubernetes clusters are heavily over-provisioned, running at only 15-25% utilization. This means 75-85% of allocated resources are wasted. Right-sizing resource requests is the single biggest sustainability win for most organizations.
</details>

**4. Which CNCF group focuses on environmental sustainability in cloud native?**

A) SIG-Scheduling
B) TAG Environmental Sustainability
C) WG-Green-Compute
D) SIG-Energy

<details>
<summary>Answer</summary>

**B) TAG Environmental Sustainability.** The CNCF has a dedicated Technical Advisory Group (TAG) for Environmental Sustainability that defines best practices, evaluates tools, and advocates for carbon-awareness across the cloud native ecosystem.
</details>

**5. How does GreenOps relate to FinOps?**

A) They are completely unrelated disciplines
B) GreenOps replaces FinOps
C) They overlap heavily — reducing waste saves both money and carbon
D) FinOps is a subset of GreenOps

<details>
<summary>Answer</summary>

**C) They overlap heavily — reducing waste saves both money and carbon.** Over-provisioning wastes both money and energy. Right-sizing, scale-to-zero, and spot instances are both FinOps and GreenOps best practices. GreenOps adds carbon-specific concerns like grid carbon intensity and embodied carbon.
</details>

**6. Which workloads are best suited for carbon-aware scheduling?**

A) All production workloads
B) Latency-sensitive API endpoints
C) Deferrable workloads like batch jobs, model training, and CI/CD pipelines
D) Only development environments

<details>
<summary>Answer</summary>

**C) Deferrable workloads like batch jobs, model training, and CI/CD pipelines.** Carbon-aware scheduling delays or relocates workloads to cleaner times/regions. This only works for workloads that can tolerate delay. Production APIs serving user requests must respond immediately regardless of grid carbon intensity.
</details>

---

## Summary

- Data centers consume **1-2% of global electricity** — growing fast with AI/ML demand
- **CNCF TAG Environmental Sustainability** leads the community effort
- **Kepler** (CNCF Sandbox) measures energy consumption per Pod using eBPF
- **Carbon-aware scheduling**: run deferrable workloads when/where the grid is cleanest (temporal and spatial shifting)
- **Right-sizing** is the biggest win — most clusters run at only 15-25% utilization
- Key practices: right-size, scale-to-zero, spot instances, bin packing, kill zombie workloads
- **GreenOps** = FinOps + sustainability; reducing waste saves money AND carbon
- Remember: the greenest compute is the compute you do not use

---

## Next Module

Congratulations! You have completed Part 3: Cloud Native Architecture. Continue to [Part 4](../part4-kubernetes-fundamentals/README.md) to dive into Kubernetes Fundamentals.
