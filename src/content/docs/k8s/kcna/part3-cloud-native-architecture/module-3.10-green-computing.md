---
title: "Module 3.10: Green Computing and Sustainability"
slug: k8s/kcna/part3-cloud-native-architecture/module-3.10-green-computing
sidebar:
  order: 11
---
> **Complexity**: `[QUICK]` - Awareness level
>
> **Time to Complete**: 20-25 minutes
>
> **Prerequisites**: Module 3.1 (Cloud Native Principles), Module 3.2 (CNCF Ecosystem)

---

## What You'll Be Able to Do

After completing this module, you will be able to:

1. **Explain** the environmental impact of cloud computing and the CNCF TAG for Environmental Sustainability
2. **Identify** Kubernetes features that reduce resource waste: bin packing, autoscaling, and right-sizing
3. **Compare** strategies for reducing carbon footprint: workload scheduling, spot instances, and resource limits
4. **Evaluate** how green computing practices align with cost optimization in cloud native environments

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

> **Pause and predict**: Most Kubernetes clusters run at only 15-25% utilization, meaning 75-85% of provisioned resources are wasted. If a team requests 4 CPU for a Pod that uses 0.5 CPU, who pays for the waste -- in both money and carbon emissions? What Kubernetes feature could automatically fix this?

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

> **Stop and think**: Carbon-aware scheduling delays workloads to times when the electricity grid is cleaner. But your production API must respond immediately -- it cannot wait until midnight. Which types of workloads in your cluster could actually benefit from temporal shifting, and which cannot?

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
- **E-waste from data centers is a rapidly growing crisis** — Cloud hardware is often refreshed every 3-5 years to maintain peak performance. This rapid turnover contributes to millions of tons of electronic waste annually, making extending the lifespan of servers a crucial, though often overlooked, aspect of green computing.

---

## Common Mistakes

| Mistake | Why It Hurts | Correct Understanding |
|---------|--------------|----------------------|
| Ignoring sustainability as "not my job" | Regulatory and customer pressure is increasing | Engineers make the provisioning decisions that determine energy consumption |
| Only focusing on operational carbon | Misses a big piece of the picture | Embodied carbon (manufacturing hardware) can be 50%+ of total — extending hardware life matters |
| Over-provisioning "just in case" | The default behavior in most orgs, massive waste | Use autoscaling and VPA instead of static over-provisioning |
| Assuming cloud = green | Cloud providers are not carbon-neutral by default | Cloud region and time-of-day matter; not all regions use renewable energy |
| Carbon-aware scheduling for everything | Not all workloads can be deferred | Only deferrable workloads (batch, training, CI/CD) benefit; latency-sensitive services cannot wait |
| Treating FinOps and GreenOps as competitors | Creates unnecessary friction between teams | They are mutually beneficial; most waste reduction strategies save both money and carbon |
| Forgetting about zombie workloads | Idle deployments silently consume resources indefinitely | Regularly audit and delete abandoned deployments, or scale down non-prod environments during off-hours |

---

## Hands-On Exercise: Spotting the Waste

**Goal**: Identify resource waste in a simulated Pod definition.

Imagine you are auditing a deployment for a simple internal web dashboard that gets a few dozen visits per day. Review this YAML snippet:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: internal-dashboard
spec:
  replicas: 3
  template:
    spec:
      containers:
      - name: dashboard
        image: internal-dashboard:v1.2
        resources:
          requests:
            cpu: "2"
            memory: "4Gi"
```

**Task**: Identify three ways this deployment is wasting resources and emitting unnecessary carbon.

<details>
<summary>Solution</summary>

1. **Over-provisioned Requests**: 2 full CPUs and 4GB of RAM is massive for a low-traffic internal dashboard. It likely needs only `cpu: 100m` and `memory: 128Mi`. This prevents other workloads from using that space on the node (bin packing inefficiency).
2. **Unnecessary Replicas**: Running 3 replicas for an internal tool with minimal traffic is overkill. Dropping this to 1 replica (or using scale-to-zero with a tool like Knative) would immediately save 66% of the compute.
3. **No Limits Specified**: While requests handle scheduling, lack of limits means a memory leak in this dashboard could consume the entire node, potentially causing other critical workloads to crash and forcing the cluster to spin up additional nodes unnecessarily.
</details>

---

## Quiz

**1. Your team has been tasked with identifying which specific microservices are consuming the most energy to prioritize them for optimization. However, your cloud provider only shows total node power consumption. Which CNCF tool should you deploy to get the required visibility?**

A) Prometheus Node Exporter
B) Kepler
C) Falco
D) Envoy

<details>
<summary>Answer</summary>

**B) Kepler.** Kepler (Kubernetes-based Efficient Power Level Exporter) uses eBPF and hardware power counters to estimate energy consumption directly at the Pod level. It bridges the gap between total server power draw and individual workload responsibility. Without this granular visibility, it is impossible to accurately identify which specific microservices are the worst carbon offenders. It exports these metrics to Prometheus, enabling teams to build detailed GreenOps dashboards.
</details>

**2. Your organization runs massive machine learning training jobs that take 12 hours to complete, but they don't have a strict deadline. You want to minimize the carbon footprint of these jobs. What is the most effective cloud native strategy to achieve this?**

A) Compress the training data using gzip before processing
B) Implement carbon-aware scheduling to run the jobs at night or in regions with high renewable energy
C) Run the jobs on ARM processors instead of x86
D) Use a Vertical Pod Autoscaler to increase the CPU limits of the training jobs

<details>
<summary>Answer</summary>

**B) Implement carbon-aware scheduling to run the jobs at night or in regions with high renewable energy.** Carbon-aware scheduling leverages the flexibility of deferrable workloads by shifting them spatially or temporally. Since the training job does not have a strict immediate deadline, it can wait for a time when the local grid's carbon intensity is lowest (e.g., when wind power is peaking). Alternatively, it can be scheduled in a cloud region powered primarily by renewable sources. This dramatically reduces the operational carbon footprint without impacting business requirements.
</details>

**3. After auditing your Kubernetes environments, your GreenOps team finds that most clusters are running at 15-25% utilization, meaning the majority of provisioned resources are wasted. What is the most impactful action your engineering teams can take to improve this?**

A) Switch all container base images to Alpine Linux
B) Right-size resource requests and limits for all workloads to match actual historical usage
C) Implement network policies to restrict unnecessary cross-namespace traffic
D) Upgrade the Kubernetes control plane to the latest version

<details>
<summary>Answer</summary>

**B) Right-size resource requests and limits for all workloads to match actual historical usage.** The single largest source of waste in Kubernetes is over-provisioning resource requests "just in case." When a Pod requests 2 CPUs but only uses 0.1, the Kubernetes scheduler reserves those 2 CPUs, preventing other workloads from using them and forcing the cluster to scale up unnecessary nodes. Right-sizing ensures the scheduler packs workloads efficiently (bin packing), which allows cluster autoscalers to shut down unneeded nodes, directly reducing both costs and carbon emissions.
</details>

**4. Your company is developing a new open-source tool for measuring the embodied carbon of hardware running Kubernetes nodes. You want to present this project to the CNCF to get feedback and align with community best practices. Which group should you approach?**

A) SIG-Scheduling
B) Kubernetes Steering Committee
C) TAG Environmental Sustainability
D) OpenTelemetry Technical Committee

<details>
<summary>Answer</summary>

**C) TAG Environmental Sustainability.** The CNCF has a dedicated Technical Advisory Group (TAG) for Environmental Sustainability. This group is explicitly tasked with defining best practices, evaluating tools, and advocating for carbon-awareness across the cloud native ecosystem. By collaborating with this TAG, you ensure your new tool aligns with community standards and gains visibility among organizations looking to improve their GreenOps practices.
</details>

**5. The finance department wants to reduce cloud spend (FinOps), while the sustainability team wants to reduce carbon emissions (GreenOps). They are arguing over whose initiatives should be prioritized. How should you resolve this conflict?**

A) Explain that the two goals are fundamentally opposed, so executive leadership must choose one
B) Prioritize FinOps, as cloud providers automatically offset all carbon emissions anyway
C) Align their efforts, as the core practices of reducing waste (like right-sizing and killing zombie workloads) achieve both goals simultaneously
D) Prioritize GreenOps, as carbon taxes will soon exceed standard cloud computing costs

<details>
<summary>Answer</summary>

**C) Align their efforts, as the core practices of reducing waste (like right-sizing and killing zombie workloads) achieve both goals simultaneously.** FinOps and GreenOps share a fundamental objective: eliminating waste. An over-provisioned cluster wastes both financial budget and electrical energy. By implementing right-sizing, scaling to zero during idle periods, and utilizing spot instances, an organization inherently reduces both its cloud bill and its carbon footprint, making these two disciplines highly complementary rather than opposed.
</details>

**6. Your team operates a user-facing e-commerce API that must respond in under 200ms, as well as a nightly data aggregation cron job. You are implementing a carbon-aware scheduler. How should these workloads be handled?**

A) Schedule both workloads to run only when grid carbon intensity is below a specific threshold
B) Move the e-commerce API to a region with 100% renewable energy, and deprecate the cron job
C) Apply carbon-aware scheduling only to the nightly cron job, as it is a deferrable workload that can tolerate temporal shifting
D) Apply carbon-aware scheduling to the e-commerce API to ensure every user request is processed sustainably

<details>
<summary>Answer</summary>

**C) Apply carbon-aware scheduling only to the nightly cron job, as it is a deferrable workload that can tolerate temporal shifting.** Carbon-aware scheduling delays or relocates workloads to times or places where the electricity grid is cleaner. This strategy only works for deferrable workloads, such as batch jobs, model training, or background data aggregation, which can tolerate flexible start times. Production APIs serving live user requests must respond immediately to maintain user experience, meaning they cannot wait for the grid's carbon intensity to drop.
</details>

**7. You are reviewing a cluster where several test environments were spun up months ago for a project that was subsequently cancelled. The Deployments are still running, but receiving zero traffic. What is the immediate sustainability impact and the best remediation?**

A) They have zero impact because Kubernetes automatically puts idle containers to sleep; no action needed
B) They consume base node resources and energy just by running; the Deployments should be deleted as 'zombie workloads'
C) They only consume network bandwidth; you should implement rate limiting
D) They are optimizing the cluster by keeping the nodes warm; you should label them as system-critical

<details>
<summary>Answer</summary>

**B) They consume base node resources and energy just by running; the Deployments should be deleted as 'zombie workloads'.** Even when receiving zero traffic, running containers consume baseline memory and CPU cycles just to maintain their idle state. More importantly, their requested resources remain reserved by the Kubernetes scheduler, preventing those resources from being used by active workloads. This forces the cluster to keep unnecessary nodes powered on, leading to continuous, unjustifiable carbon emissions until these 'zombie workloads' are actively terminated.
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

Congratulations! You have completed Part 3: Cloud Native Architecture. Continue to [Part 4](../part4-application-delivery/) to explore Application Delivery.