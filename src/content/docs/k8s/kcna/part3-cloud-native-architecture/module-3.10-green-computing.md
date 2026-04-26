---
title: "Module 3.10: Green Computing and Sustainability"
slug: k8s/kcna/part3-cloud-native-architecture/module-3.10-green-computing
sidebar:
  order: 11
---

> **Complexity**: `[QUICK]` - Awareness and applied analysis level
>
> **Time to Complete**: 30-40 minutes
>
> **Prerequisites**: Module 3.1 (Cloud Native Principles), Module 3.2 (CNCF Ecosystem), basic Kubernetes resource requests and limits

---

## What You'll Be Able to Do

After completing this module, you will be able to:

1. **Analyze** how Kubernetes resource requests, idle replicas, and node utilization translate into financial waste and carbon impact.
2. **Diagnose** common sustainability problems in cloud native workloads, including over-provisioning, zombie workloads, and misplaced carbon-aware scheduling.
3. **Compare** right-sizing, autoscaling, scale-to-zero, spot capacity, and carbon-aware scheduling for different workload types.
4. **Evaluate** when GreenOps decisions align with FinOps goals, and when reliability, latency, or data residency constraints limit the greener option.
5. **Design** a practical improvement plan for a Kubernetes workload using measurable sustainability signals and safe operational guardrails.

---

## Why This Module Matters

A platform engineer is asked to review the monthly cloud bill after a product team complains that the bill doubled even though traffic barely changed. The first dashboard shows money, not carbon, but the pattern is familiar: three non-production environments are still running after a project was cancelled, several services request far more CPU than they use, and nightly jobs all start during the same regional demand peak. Nothing is obviously broken from a user perspective, yet the platform is wasting electricity every hour.

This is why green computing belongs in a Kubernetes curriculum. Cloud native systems make it easy to create more workloads, more replicas, more regions, and more automation, but the same mechanisms can either reduce waste or multiply it. Containers improve density only when resource requests are realistic. Autoscaling reduces idle capacity only when it is configured against a useful signal. Carbon-aware scheduling helps only when the workload can actually move in time or location.

For KCNA, the goal is not to turn you into a carbon accounting specialist. The goal is to recognize sustainability as an engineering property that appears in architecture reviews, capacity planning, scheduling decisions, and operational dashboards. A strong beginner can name green computing practices; a stronger practitioner can look at a workload and decide which practice is safe, measurable, and worth doing first.

> **Working principle**: The greenest compute is the compute you do not need to run. Measure first, remove waste next, then optimize the work that must remain.

---

## From Cloud Waste to Carbon Impact

The first step is to connect an ordinary Kubernetes decision to an environmental consequence. When a Pod requests CPU and memory, Kubernetes reserves capacity for that Pod during scheduling. If the Pod requests far more than it uses, the cluster may need extra nodes even though the real application load would fit on fewer machines. Those machines still draw power, produce heat, require cooling, and eventually contribute to hardware replacement cycles.

```
┌────────────────────────────────────────────────────────────────────────────┐
│                    FROM RESOURCE REQUEST TO CARBON IMPACT                  │
├────────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│  Developer sets requests:                                                  │
│                                                                            │
│      cpu: "2"                                                              │
│      memory: "4Gi"                                                         │
│                                                                            │
│                         │                                                  │
│                         ▼                                                  │
│                                                                            │
│  Kubernetes scheduler reserves capacity even when real usage is lower:     │
│                                                                            │
│      requested CPU:  2.0 cores                                             │
│      observed CPU:   0.2 cores                                             │
│      unused reserve: 1.8 cores                                             │
│                                                                            │
│                         │                                                  │
│                         ▼                                                  │
│                                                                            │
│  Cluster autoscaler may keep more nodes online than the workload needs:    │
│                                                                            │
│      more powered servers → more cooling → more operational emissions      │
│      more hardware demand  → more manufacturing and disposal emissions     │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘
```

Operational emissions come from running the system: electricity for compute, storage, networking, and cooling. Embodied emissions come from manufacturing, shipping, maintaining, and disposing of hardware. Kubernetes teams most directly influence operational emissions day to day, but their decisions also affect embodied emissions over time because poor utilization encourages organizations to buy or rent more hardware than necessary.

Cloud native can make this better. A well-run platform can pack workloads efficiently, scale replicas down when traffic drops, remove idle test environments, and shift deferrable jobs away from dirtier grid windows. Cloud native can also make this worse. Microservice sprawl, sidecar overhead, over-sized requests, and forgotten namespaces can create hundreds of small costs that no single team notices until the aggregate bill and carbon footprint are large.

| Cloud Native Pattern | How It Can Reduce Waste | How It Can Increase Waste |
|---|---|---|
| Containers | Higher workload density can reduce the number of active nodes. | Poor requests can reserve unused capacity and block bin packing. |
| Autoscaling | Replicas and nodes can shrink when demand falls. | Bad scaling signals can add replicas without improving service quality. |
| Microservices | Each component can scale independently based on its own demand. | Too many always-on services and sidecars add baseline overhead. |
| Multi-region design | Workloads can move closer to users or cleaner electricity. | Duplicate active stacks can run everywhere even when traffic is small. |
| Batch automation | Jobs can run during cheaper or cleaner periods when deadlines allow. | Uncontrolled jobs can start together and create avoidable capacity peaks. |

> **Active learning prompt**: Imagine two teams each run a dashboard that gets little traffic. Team A runs one replica with realistic requests. Team B runs three replicas with CPU requests ten times higher than observed usage. Before reading further, decide which team creates the bigger scheduling problem and why the answer is about reserved capacity, not only current CPU usage.

The important mental shift is that sustainability is not separate from good operations. A cluster with realistic requests, useful autoscaling, and regular cleanup usually costs less and emits less. The hard part is not believing that waste is bad; the hard part is choosing an improvement that does not break reliability, hide risk, or move emissions somewhere else.

---

## The CNCF Sustainability Context

The CNCF community treats environmental sustainability as a cloud native concern because cloud native tools decide where workloads run, how many replicas exist, how much infrastructure is reserved, and what telemetry operators can see. The CNCF TAG Environmental Sustainability supports initiatives related to building, deploying, managing, and operating cloud native applications with lower environmental impact. It is a community group, not a magic product, and its value comes from shared guidance, working groups, landscapes, and project collaboration.

```
┌────────────────────────────────────────────────────────────────────────────┐
│                  CNCF ENVIRONMENTAL SUSTAINABILITY CONTEXT                 │
├────────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│  CNCF TAG Environmental Sustainability                                     │
│                                                                            │
│      ├─ Advocates for sustainable cloud native practices                    │
│      ├─ Supports projects and initiatives in the ecosystem                  │
│      ├─ Helps evaluate sustainability approaches and tooling                │
│      ├─ Publishes landscape material and community guidance                 │
│      └─ Connects practitioners through meetings, repositories, and Slack    │
│                                                                            │
│  Typical engineering questions                                             │
│                                                                            │
│      ├─ Can this workload run on fewer resources safely?                    │
│      ├─ Can this batch job run when the grid is cleaner?                    │
│      ├─ Can this service move to a cleaner region without hurting users?    │
│      ├─ Can we attribute energy use to teams, namespaces, or workloads?     │
│      └─ Can platform defaults prevent waste before it reaches production?   │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘
```

This matters because sustainability needs shared language. If one team talks only about cost, another talks only about carbon, and another talks only about performance, they may miss the fact that many first actions are identical. Right-sizing, cleanup, scale-to-zero, and better scheduling usually improve more than one objective. The conflict appears later, when the greener option has a latency, availability, compliance, or migration cost.

The CNCF ecosystem also includes projects and adjacent tools that help teams measure and act. Kepler measures energy-related workload signals and exports Prometheus metrics. KEDA and Knative can support event-driven scaling and scale-to-zero patterns. Goldilocks uses Vertical Pod Autoscaler data to recommend resource settings. The Carbon Aware SDK from the Green Software Foundation can help applications and automation choose cleaner times or locations when workloads are flexible enough.

| Community Area | Practitioner Question | Example Tooling or Practice |
|---|---|---|
| Measurement | Which workload is responsible for energy use? | Kepler, Prometheus, Grafana, cloud carbon reports |
| Right-sizing | Are requests and limits close to real usage? | VPA recommendations, Goldilocks, usage reviews |
| Scaling | Can replicas or nodes shrink safely when demand falls? | HPA, KEDA, Knative, Cluster Autoscaler |
| Scheduling | Can flexible work run at cleaner times or places? | Carbon-aware scheduling, batch queues, regional placement |
| Governance | Can teams make sustainable defaults repeatable? | Platform policies, service templates, review checklists |

For KCNA, remember the shape of the ecosystem rather than memorizing every project name. The pattern is measurement, waste removal, efficient scaling, and carbon-aware placement. If a question asks what group organizes cloud native environmental sustainability, the answer is the CNCF TAG Environmental Sustainability. If a question asks how to see per-workload energy signals, Kepler is the important CNCF project to recognize.

---

## Measuring Before Optimizing

Teams often start green computing work by guessing. They assume the biggest service is the worst offender, or that deleting small workloads cannot matter, or that moving to a famous renewable region automatically solves the problem. Those guesses may be wrong because energy use depends on utilization, hardware, replicas, request patterns, cooling, and the electricity grid. Measurement does not make the decision for you, but it keeps the decision honest.

Kepler, the Kubernetes-based Efficient Power Level Exporter, is a Prometheus exporter that estimates energy consumption at container, Pod, process, and node levels. It uses hardware energy counters where available and workload attribution models to connect node-level power information to Kubernetes objects. The result is similar in spirit to cost allocation: instead of seeing only a monthly cloud bill, teams can ask which namespace, workload, or service is contributing most to energy use.

```
┌────────────────────────────────────────────────────────────────────────────┐
│                         KEPLER MEASUREMENT FLOW                            │
├────────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│  ┌──────────────────────────── Kubernetes Node ──────────────────────────┐ │
│  │                                                                        │ │
│  │  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐   │ │
│  │  │ Pod: api        │    │ Pod: worker     │    │ Pod: dashboard  │   │ │
│  │  │ cpu + memory    │    │ cpu + memory    │    │ cpu + memory    │   │ │
│  │  └─────────────────┘    └─────────────────┘    └─────────────────┘   │ │
│  │                                                                        │ │
│  │  ┌──────────────────────────────────────────────────────────────────┐  │ │
│  │  │ Kepler DaemonSet                                                 │  │ │
│  │  │ reads hardware counters and kernel signals                       │  │ │
│  │  │ attributes energy estimates to workloads                         │  │ │
│  │  │ exports Prometheus metrics with Kubernetes labels                 │  │ │
│  │  └──────────────────────────────────────────────────────────────────┘  │ │
│  │                                                                        │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                  │                                         │
│                                  ▼                                         │
│                         Prometheus scrapes metrics                         │
│                                  │                                         │
│                                  ▼                                         │
│                     Grafana dashboard or GreenOps report                   │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘
```

Measurement has limitations. Public cloud providers may not expose every hardware and power signal. Workload attribution is often an estimate, especially on shared nodes. A dashboard can show a strong optimization candidate, but it cannot decide whether that workload is business-critical, latency-sensitive, or constrained by compliance. Treat energy metrics as operational evidence that must be combined with service ownership and reliability context.

A useful first dashboard usually includes resource requests, observed usage, replica count, node count, and energy or carbon estimates. If energy metrics are unavailable, teams can still start with proxy signals such as low utilization, idle namespaces, unused PersistentVolumes, and stale Deployments. The best dashboards show trends, not just snapshots, because a workload that is quiet today may be busy during payroll, reporting, or seasonal traffic.

| Signal | What It Reveals | How to Interpret It Carefully |
|---|---|---|
| Requested CPU versus observed CPU | Scheduling waste and poor bin packing | Low usage may be normal for bursty services, so check history before cutting. |
| Requested memory versus observed memory | Memory reservation waste and possible over-sizing | Memory has different risk than CPU because limits can trigger OOM kills. |
| Replica count versus traffic | Idle or over-replicated services | Some replicas are required for availability even when traffic is low. |
| Namespace age and owner | Zombie environments and abandoned projects | Confirm ownership before deleting anything in shared clusters. |
| Job start time and duration | Deferrable work that may shift to cleaner windows | Only shift jobs when business deadlines and dependencies allow it. |
| Region and data residency | Spatial shifting opportunities | Cleaner regions may violate latency, cost, or regulatory requirements. |

> **Active learning prompt**: Your dashboard shows a service with very low CPU usage but steady memory usage near its request. Would you lower CPU, memory, both, or neither first? Decide what evidence you would want before changing each value, because CPU and memory failures behave differently in Kubernetes.

---

## Right-Sizing and Bin Packing

Right-sizing is the practice of setting resource requests and limits close to what a workload actually needs, with enough headroom for normal variation. In Kubernetes, this is one of the highest-value sustainability practices because requests affect scheduling. A Pod that requests two CPU cores reserves that amount from the scheduler's perspective even if it usually consumes a small fraction of a core.

Bin packing is the scheduler's ability to place workloads efficiently onto nodes. If requests are accurate, more Pods can fit on fewer nodes without increasing risk. If requests are inflated, the scheduler sees nodes as full while real CPU sits idle. The cluster autoscaler may then add nodes even though the existing nodes could have handled the real demand.

```
┌────────────────────────────────────────────────────────────────────────────┐
│                         BIN PACKING WITH REQUESTS                          │
├────────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│  Poor requests: scheduler sees each Pod as large                           │
│                                                                            │
│      Node A capacity: 4 CPU                                                 │
│      ┌────────────────────────────────────────────┐                        │
│      │ Pod 1 requests 2 CPU but uses 0.2 CPU       │                        │
│      │ Pod 2 requests 2 CPU but uses 0.2 CPU       │                        │
│      │ Scheduler thinks node is full               │                        │
│      └────────────────────────────────────────────┘                        │
│                                                                            │
│      Result: more nodes stay powered for little real work                  │
│                                                                            │
│  Better requests: scheduler sees realistic demand                          │
│                                                                            │
│      Node B capacity: 4 CPU                                                 │
│      ┌────────────────────────────────────────────┐                        │
│      │ Pod 1 requests 250m CPU                     │                        │
│      │ Pod 2 requests 250m CPU                     │                        │
│      │ Pod 3 requests 250m CPU                     │                        │
│      │ Pod 4 requests 250m CPU                     │                        │
│      │ More workloads fit before another node adds │                        │
│      └────────────────────────────────────────────┘                        │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘
```

Right-sizing is not the same as making everything tiny. A service with unpredictable spikes may need higher CPU requests, horizontal autoscaling, or a performance test before requests are reduced. A memory-heavy service may need generous memory requests because memory pressure can cause eviction or out-of-memory failures. Sustainable engineering is not reckless minimization; it is evidence-based allocation.

Vertical Pod Autoscaler can recommend or adjust requests based on observed usage. Goldilocks presents VPA recommendations in a way that is easier for teams to review. Human review still matters because tools see metrics, not product launches, one-off migrations, upcoming traffic events, or the cost of a restart. The safest first workflow is to observe, recommend, apply a conservative change, monitor, and repeat.

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: internal-dashboard
  labels:
    app: internal-dashboard
spec:
  replicas: 1
  selector:
    matchLabels:
      app: internal-dashboard
  template:
    metadata:
      labels:
        app: internal-dashboard
    spec:
      containers:
        - name: dashboard
          image: nginx:1.27
          resources:
            requests:
              cpu: "100m"
              memory: "128Mi"
            limits:
              cpu: "500m"
              memory: "256Mi"
```

The manifest above is not a universal recommendation; it is a realistic shape for a small internal dashboard in a lab. A production dashboard with strict availability requirements might need multiple replicas and a PodDisruptionBudget. A dashboard with a memory-heavy runtime might need more memory. The point is to justify requests from evidence and service requirements instead of copying large defaults.

| Right-Sizing Decision | Good Evidence | Risk If Done Carelessly |
|---|---|---|
| Lower CPU request | Sustained usage is far below request and latency is healthy. | CPU throttling or slower request handling during bursts. |
| Lower memory request | Working set and peak memory are consistently below request. | Evictions if the node experiences memory pressure. |
| Set memory limit | Application has known memory envelope and restart behavior is acceptable. | OOM kills if the limit is too tight or traffic changes. |
| Reduce replicas | Traffic, availability needs, and disruption tolerance allow it. | Outage risk during node maintenance or sudden spikes. |
| Add autoscaling | Metric reflects real demand and scale behavior is tested. | Oscillation, cost spikes, or insufficient capacity if metrics lag. |

A senior-level habit is to ask what failure mode the change introduces. Lowering CPU tends to cause slower work or throttling; lowering memory can terminate processes. Reducing replicas may save energy but reduce fault tolerance. Carbon savings are not useful if the team compensates by running emergency infrastructure later because the change caused instability.

---

## Autoscaling, Scale-to-Zero, and Zombie Workloads

Autoscaling reduces waste when it connects supply to demand. Horizontal Pod Autoscaler changes the number of Pod replicas. Cluster Autoscaler changes the number of nodes. KEDA can scale workloads based on event sources such as queue length, and some platforms can scale services to zero when they have no traffic. These mechanisms are powerful because they remove the assumption that yesterday's peak should run all day.

```
┌────────────────────────────────────────────────────────────────────────────┐
│                       SCALING LAYERS IN KUBERNETES                         │
├────────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│  Workload demand changes                                                   │
│             │                                                              │
│             ▼                                                              │
│  ┌──────────────────────────────┐                                          │
│  │ HPA or KEDA changes replicas │  fewer or more Pods for the workload     │
│  └──────────────────────────────┘                                          │
│             │                                                              │
│             ▼                                                              │
│  ┌──────────────────────────────┐                                          │
│  │ Scheduler places the Pods    │  requests decide where Pods can fit      │
│  └──────────────────────────────┘                                          │
│             │                                                              │
│             ▼                                                              │
│  ┌──────────────────────────────┐                                          │
│  │ Cluster Autoscaler changes   │  fewer or more nodes for the cluster     │
│  │ node count when possible     │                                          │
│  └──────────────────────────────┘                                          │
│                                                                            │
│  Sustainability win appears only when lower replicas allow lower nodes.    │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘
```

Autoscaling a Deployment from ten replicas to two saves Pod-level overhead, but the largest infrastructure win appears when nodes can also be removed. If other workloads or inflated requests keep the nodes full from the scheduler's perspective, the cluster may not scale down. This is why right-sizing and autoscaling should be treated as a combined system rather than separate checkboxes.

Scale-to-zero is useful for workloads that can tolerate cold starts or are not needed continuously. Non-production preview environments, internal tools, queue workers, and development services are common candidates. A customer-facing API with a strict latency objective is usually not a good candidate unless the platform has a proven warmup path and the business accepts the trade-off.

Zombie workloads are different from intentionally idle services. A zombie workload is a Deployment, Job, database, namespace, or environment that no longer has a valid owner or purpose but still consumes resources. Kubernetes will not automatically know that a project was cancelled. Without ownership labels, TTL policies, environment expiration, and regular reviews, zombie workloads can run for months.

| Workload Type | Better GreenOps Pattern | Why It Fits |
|---|---|---|
| User-facing API | Right-size, autoscale, and keep enough replicas for availability. | Low latency and reliability matter more than temporal shifting. |
| Queue worker | Scale from queue depth and allow low or zero idle replicas. | Demand is visible and work can often wait briefly. |
| Nightly report | Run during a cleaner window when deadlines allow. | Batch work has flexible timing and predictable duration. |
| Preview environment | Auto-expire after a pull request closes or after a fixed lifetime. | Temporary environments are common sources of zombie waste. |
| Internal dashboard | Reduce replicas, right-size requests, and consider off-hours scale-down. | Low traffic and internal users usually allow conservative savings. |
| Model training job | Evaluate cleaner regions, cleaner windows, and specialized hardware. | Long-running compute can create large carbon differences. |

> **Stop and reason**: A cluster scales Deployments down every night, but the cloud bill barely changes. What would you check next: Pod replicas, node count, resource requests, or all three? The useful answer is all three, because sustainability gains often require the whole scaling chain to complete.

A practical cleanup program starts with labels. Every namespace and workload should have an owner, environment, application, and expiration policy where appropriate. Cleanup becomes safer when platform teams can distinguish a production service from a stale preview namespace. Without those labels, green computing work turns into manual detective work, and teams become afraid to delete anything.

```bash
kubectl get deployments --all-namespaces \
  -o custom-columns='NAMESPACE:.metadata.namespace,NAME:.metadata.name,REPLICAS:.spec.replicas,OWNER:.metadata.labels.owner,ENV:.metadata.labels.environment'
```

The command uses `kubectl`; in later modules and daily practice you may see the common alias `k` for the same command. The output is a starting point, not a deletion list. A responsible engineer confirms traffic, ownership, and dependencies before scaling down or removing a workload, especially in shared clusters.

---

## Carbon-Aware Scheduling

Carbon-aware scheduling means running flexible work when or where electricity has lower carbon intensity. The same amount of compute can have different emissions depending on the grid mix at that time and location. This is why a batch job may be greener if it runs during a period of high wind or solar availability, or in a region with cleaner electricity, assuming the business constraints allow it.

```
┌────────────────────────────────────────────────────────────────────────────┐
│                         CARBON-AWARE SCHEDULING                            │
├────────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│  Temporal shifting: choose WHEN                                             │
│                                                                            │
│      High carbon intensity:  ██████████        ████████                    │
│      Medium intensity:       ██████    ████████        ████                │
│      Low carbon intensity:          █████████              ███████         │
│                              06:00   12:00   18:00   00:00                │
│                                                                            │
│      Candidate action: run deferrable batch work during low windows.       │
│                                                                            │
│  Spatial shifting: choose WHERE                                             │
│                                                                            │
│      Region A: closer to users, higher grid carbon at this hour            │
│      Region B: farther from users, lower grid carbon at this hour          │
│                                                                            │
│      Candidate action: move only workloads that tolerate the trade-off.    │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘
```

The word flexible is doing most of the work. A production checkout API cannot wait several hours for cleaner electricity because users expect immediate responses. A nightly analytics job might wait, provided downstream reports still finish before the business day starts. A machine learning training job may move to another region if data gravity, privacy, cost, and accelerator availability do not block the move.

Carbon-aware scheduling also has a rebound risk. Moving a job to a cleaner region can increase network transfer, create duplicate storage, or violate data residency. Delaying too much work into the same clean window can create a capacity spike that forces extra nodes online. A mature GreenOps design considers the whole system rather than optimizing one metric in isolation.

| Constraint | Question to Ask | Scheduling Consequence |
|---|---|---|
| Latency | Does a user or system need an immediate response? | Low-latency services usually cannot wait for cleaner windows. |
| Deadline | When must the result be available? | Batch jobs can shift only inside their deadline slack. |
| Data residency | Can the data legally and contractually move regions? | Some workloads cannot use spatial shifting. |
| Data volume | Would moving data create more transfer and storage overhead? | Large datasets may be better processed where they already live. |
| Capacity | Will many jobs move into the same window? | Batch queues need throttling and priorities. |
| Reliability | What happens if the cleaner window is missed? | Schedulers need fallback rules, not perfect-only plans. |

A practical carbon-aware scheduler needs a policy, not only a carbon intensity feed. The policy should describe which workloads are eligible, how long they can wait, what regions are allowed, and what fallback to use when cleaner capacity is unavailable. Without policy, carbon awareness becomes a fragile script that may surprise application teams.

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: nightly-aggregation
  labels:
    app: reporting
    carbon-aware: "candidate"
spec:
  schedule: "30 1 * * *"
  jobTemplate:
    spec:
      template:
        spec:
          restartPolicy: OnFailure
          containers:
            - name: aggregate
              image: busybox:1.36
              command:
                - /bin/sh
                - -c
                - "date && echo aggregating-report-data && sleep 5"
              resources:
                requests:
                  cpu: "200m"
                  memory: "128Mi"
                limits:
                  cpu: "500m"
                  memory: "256Mi"
```

This CronJob is runnable in a Kubernetes 1.35+ cluster, but the label is only a marker. A real carbon-aware platform would connect policy, carbon data, batch orchestration, and admission controls or scheduler extensions. At KCNA level, focus on deciding which workloads are eligible and what trade-offs must be checked before moving them.

---

## GreenOps and FinOps Together

FinOps asks how cloud spending maps to business value. GreenOps asks how energy and carbon map to useful work. These disciplines overlap because waste is expensive and waste emits carbon. An over-provisioned Deployment, a forgotten namespace, and an always-on development cluster are usually bad in both frameworks.

```
┌────────────────────────────────────────────────────────────────────────────┐
│                         FINOPS AND GREENOPS OVERLAP                        │
├────────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│  FinOps question:   Are we spending money on useful work?                  │
│  GreenOps question: Are we emitting carbon for useful work?                │
│                                                                            │
│  Shared first moves:                                                        │
│                                                                            │
│      ├─ Remove unused workloads                                             │
│      ├─ Right-size requests and limits                                      │
│      ├─ Scale idle systems down                                             │
│      ├─ Improve bin packing and node utilization                            │
│      ├─ Use efficient images and startup paths                              │
│      └─ Prefer flexible scheduling for deferrable work                      │
│                                                                            │
│  Difference: GreenOps also asks about grid carbon, embodied carbon,         │
│  hardware life cycle, and the timing or location of computation.            │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘
```

The alignment is strongest when the action removes unnecessary work. Deleting a zombie environment saves money and carbon without a complicated debate. Right-sizing a service based on evidence improves bin packing and can reduce nodes. Scaling a queue worker to zero when there are no messages prevents idle resource consumption.

The alignment is weaker when the greener option costs more, increases latency, or requires engineering effort that displaces higher-value work. A cleaner region may be more expensive or farther from users. Specialized efficient hardware may require application changes. A carbon-aware batch system may need new operational controls. Senior engineers do not pretend those trade-offs vanish; they make the trade-off explicit and measure the result.

| Decision | FinOps View | GreenOps View | Balanced Recommendation |
|---|---|---|
| Delete abandoned preview namespaces | Immediate cost reduction | Immediate energy and carbon reduction | Do it after ownership and dependency checks. |
| Reduce inflated CPU requests | Better bin packing and lower node count | Less powered idle capacity | Do it gradually with monitoring and rollback. |
| Move API to cleaner distant region | May change cost and data transfer | May reduce grid carbon | Avoid if latency or residency suffers. |
| Shift nightly reports to cleaner window | Often neutral or cheaper | Lower operational carbon | Use deadlines and fallback rules. |
| Keep hardware longer | May delay capital spend | Reduces embodied carbon pressure | Balance against efficiency, reliability, and support lifecycle. |
| Use spot capacity for batch jobs | Lower compute price | Uses existing spare capacity | Use only when interruption is acceptable. |

A useful meeting question is, "What is the smallest change that removes confirmed waste without changing the user experience?" That question usually leads to cleanup, requests, and scaling before region moves or sophisticated schedulers. Advanced sustainability work is valuable, but it should build on the basics instead of distracting from obvious waste.

---

## Worked Example: Audit a Low-Traffic Dashboard

This worked example shows how to reason about a workload before you are asked to perform the same analysis independently. The scenario is intentionally small because the habit matters more than the manifest size: inspect purpose, traffic, replicas, requests, limits, and scaling behavior before recommending changes.

A team runs an internal dashboard that receives a few dozen visits per day. It is useful during business hours, but it is not customer-facing and does not process payments. The current Deployment requests large resources and runs three replicas in a shared cluster.

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: internal-dashboard
  labels:
    app: internal-dashboard
    owner: platform-tools
    environment: internal
spec:
  replicas: 3
  selector:
    matchLabels:
      app: internal-dashboard
  template:
    metadata:
      labels:
        app: internal-dashboard
    spec:
      containers:
        - name: dashboard
          image: nginx:1.27
          resources:
            requests:
              cpu: "2"
              memory: "4Gi"
```

The first finding is over-sized requests. Three replicas each request two CPU cores and four GiB of memory, so the scheduler reserves six CPU cores and twelve GiB of memory before considering any other workload. If observed usage is closer to a small static dashboard, these requests block bin packing and may keep extra nodes online. The correct response is not to guess tiny values permanently, but to review metrics and apply conservative requests that match real demand.

The second finding is replica count. Three replicas may be justified for a customer-facing service with availability requirements, but this internal dashboard has low traffic and limited criticality. One replica may be enough, or two may be chosen if the team wants some availability during node maintenance. The recommendation should name the reliability trade-off rather than pretending lower replicas are always correct.

The third finding is missing limits and missing lifecycle policy. CPU and memory limits are not a sustainability solution by themselves, but they protect the node from unexpected runaway behavior and make resource usage easier to reason about. The workload also lacks an off-hours or scale-to-zero plan. If the dashboard is not needed outside business hours, a scheduled scale-down or event-driven pattern could reduce idle consumption further.

A better first revision could look like this in a lab. In production, you would validate observed metrics, latency, restart behavior, and user requirements before applying it.

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: internal-dashboard
  labels:
    app: internal-dashboard
    owner: platform-tools
    environment: internal
    sustainability.kubedojo.io/reviewed: "true"
spec:
  replicas: 1
  selector:
    matchLabels:
      app: internal-dashboard
  template:
    metadata:
      labels:
        app: internal-dashboard
    spec:
      containers:
        - name: dashboard
          image: nginx:1.27
          resources:
            requests:
              cpu: "100m"
              memory: "128Mi"
            limits:
              cpu: "500m"
              memory: "256Mi"
```

The teaching point is the decision sequence. First, classify the workload. Second, compare requested resources with observed usage. Third, consider replica count against reliability needs. Fourth, add guardrails such as limits, labels, ownership, and monitoring. Finally, verify that the cluster can actually remove nodes or free capacity after the change. Without that last step, a team may celebrate a smaller manifest while the same number of nodes continues running.

---

## Did You Know?

- **Kepler is a CNCF Sandbox project for Kubernetes energy metrics**: It exports Prometheus metrics that help teams estimate energy consumption at workload levels, which makes GreenOps conversations more concrete than node-level guessing.
- **Idle does not mean free**: A quiet container can still reserve memory, keep processes alive, hold scheduling capacity, and contribute to a node staying powered even when users send no traffic.
- **Carbon-aware scheduling depends on flexibility**: The same idea that works well for batch jobs can be wrong for user-facing APIs, because delayed work is only acceptable when the workload has deadline slack.
- **Embodied carbon changes the hardware conversation**: Replacing servers with newer efficient hardware can reduce operational energy, but manufacturing and disposal impacts mean the best answer depends on lifecycle analysis, not only power draw.

---

## Common Mistakes

| Mistake | Why It Hurts | Better Practice |
|---|---|---|
| Treating sustainability as only a facilities problem | Application teams set requests, replicas, retries, images, and schedules that directly affect infrastructure demand. | Make sustainability part of workload review and platform defaults. |
| Reducing replicas without checking availability needs | A lower replica count can create outages during node maintenance, rollouts, or traffic bursts. | Classify the workload and document the reliability trade-off before reducing replicas. |
| Lowering memory requests too aggressively | Memory pressure can evict Pods or trigger OOM kills, causing instability and rework. | Use historical memory peaks and restart behavior before changing memory settings. |
| Expecting Pod autoscaling alone to reduce emissions | Nodes may stay online if requests, DaemonSets, or other workloads prevent scale-down. | Verify the full chain from replicas to scheduling to node removal. |
| Applying carbon-aware scheduling to live APIs | User-facing services cannot usually wait for cleaner grid windows without harming latency. | Reserve temporal shifting for batch, training, reporting, CI, and other deferrable work. |
| Deleting workloads based only on low traffic | Some low-traffic systems are compliance, admin, or emergency tools with real value. | Confirm ownership, purpose, dependencies, and recovery path before deletion. |
| Optimizing a single metric in isolation | A greener region can add latency, data transfer, duplicate storage, or compliance risk. | Evaluate cost, carbon, reliability, data residency, and user impact together. |
| Measuring once and assuming the result is permanent | Traffic, releases, seasonal events, and team ownership change over time. | Review trends and schedule recurring sustainability audits. |

---

## Quiz

**1. Your team finds a Deployment with five replicas, each requesting one full CPU core, but the last two weeks of metrics show each replica usually consumes less than 100m CPU. The service is internal, low traffic, and not part of an outage response path. What should you recommend first?**

A) Delete the Deployment immediately because it is clearly unused  
B) Reduce requests and replica count conservatively, then monitor latency, restarts, and node scale-down behavior  
C) Move the Deployment to another cloud region because carbon-aware scheduling always gives the largest savings  
D) Increase the CPU limit so the service can finish work faster and emit less carbon

<details>
<summary>Answer</summary>

**B) Reduce requests and replica count conservatively, then monitor latency, restarts, and node scale-down behavior.** The evidence points to over-provisioning, but the safe engineering response is measured change rather than deletion. Right-sizing requests improves bin packing, and reducing replicas may be appropriate for a low-traffic internal service. Verification matters because the sustainability benefit is strongest when the cluster can actually free capacity or remove nodes.
</details>

**2. A platform team wants to apply carbon-aware scheduling to every workload in the cluster. The cluster hosts a checkout API with a 200 ms latency objective, a nightly invoice generator, and a weekly machine learning training job. Which workloads are the best candidates?**

A) The checkout API only, because it has the most business value  
B) The invoice generator and training job, if their deadlines and data constraints allow shifting  
C) All three workloads, because all electricity has carbon impact  
D) None of the workloads, because Kubernetes cannot run batch jobs

<details>
<summary>Answer</summary>

**B) The invoice generator and training job, if their deadlines and data constraints allow shifting.** Carbon-aware scheduling works best for deferrable or movable workloads. The checkout API must respond immediately, so delaying it would harm users. Batch reporting and training jobs often have deadline slack, but the team still needs to check data residency, capacity, and fallback rules.
</details>

**3. Your GreenOps dashboard shows that a namespace has almost no network traffic, but several Deployments still reserve CPU and memory. The project label points to an initiative that ended months ago. What is the most responsible next action?**

A) Confirm ownership and dependencies, then scale down or delete the zombie workloads through an agreed cleanup process  
B) Ignore the namespace because low network traffic means it emits no carbon  
C) Add more replicas so the namespace can be highly available if someone uses it later  
D) Move the namespace to a different region without asking the owner

<details>
<summary>Answer</summary>

**A) Confirm ownership and dependencies, then scale down or delete the zombie workloads through an agreed cleanup process.** This is likely a zombie workload scenario, but deletion should still be controlled. Idle workloads can reserve capacity and help keep nodes online. Ownership checks, dependency checks, and a rollback or recovery path prevent sustainability cleanup from becoming an operational incident.
</details>

**4. A finance leader says, "We only care about cost this quarter, not carbon." The sustainability lead says, "We should ignore cost and choose the lowest-carbon region." How should the platform team frame the first improvement plan?**

A) Start with waste-reduction actions such as right-sizing, cleanup, and scale-down because they usually reduce both cost and carbon  
B) Choose only the cheapest region because cloud providers handle all sustainability concerns automatically  
C) Choose only the cleanest grid region because latency and data transfer do not affect sustainability  
D) Stop the program until both leaders agree on a single metric

<details>
<summary>Answer</summary>

**A) Start with waste-reduction actions such as right-sizing, cleanup, and scale-down because they usually reduce both cost and carbon.** FinOps and GreenOps overlap strongly when the action removes unnecessary work. Region moves may involve trade-offs, but cleanup and right-sizing are usually easier first actions. This framing gives both leaders measurable progress while leaving harder trade-offs for explicit review.
</details>

**5. A team lowers CPU requests for many services and sees better scheduled capacity, but the cloud bill and node count stay almost unchanged after several days. What should they investigate next?**

A) Whether cluster autoscaling can remove nodes, whether other requests block bin packing, and whether DaemonSets or node groups set a floor  
B) Whether Prometheus is installed, because Prometheus automatically powers down unused servers  
C) Whether every service has a memory limit, because memory limits always reduce node count  
D) Whether the Kubernetes version is exactly 1.35, because older patch versions cannot scale

<details>
<summary>Answer</summary>

**A) Whether cluster autoscaling can remove nodes, whether other requests block bin packing, and whether DaemonSets or node groups set a floor.** Smaller requests help only if the rest of the system can use the freed capacity. Node group minimums, DaemonSet overhead, remaining inflated requests, and placement constraints can all prevent node removal. Sustainability verification should follow the complete scaling chain.
</details>

**6. A team proposes moving a large analytics job to a cleaner region. The job reads many terabytes from a database that must stay in the original region for regulatory reasons. What is the best evaluation?**

A) Move the job anyway because cleaner electricity always wins  
B) Reject all carbon-aware scheduling for the organization  
C) Compare carbon savings against data transfer, duplicate storage, compliance constraints, runtime, and deadline requirements  
D) Remove resource limits from the job so it finishes before the grid gets dirtier

<details>
<summary>Answer</summary>

**C) Compare carbon savings against data transfer, duplicate storage, compliance constraints, runtime, and deadline requirements.** Spatial shifting can reduce carbon, but it is not automatically correct. Moving large datasets may create extra network and storage overhead, and regulatory limits may block the move entirely. A senior evaluation considers the whole system rather than one carbon-intensity number.
</details>

**7. Your team wants per-workload visibility into energy use for Kubernetes namespaces so service owners can prioritize optimization. The cloud provider gives only broad infrastructure reports. Which approach best fits the need?**

A) Deploy workload-level energy telemetry such as Kepler and export metrics to Prometheus for namespace and Pod analysis  
B) Use only `kubectl get pods` because Pod names are enough to calculate carbon precisely  
C) Replace every Deployment with a StatefulSet because StatefulSets are more sustainable  
D) Disable all limits so workloads can share nodes more freely

<details>
<summary>Answer</summary>

**A) Deploy workload-level energy telemetry such as Kepler and export metrics to Prometheus for namespace and Pod analysis.** Kepler is designed to estimate and expose energy-related metrics for Kubernetes workloads. The measurements still require careful interpretation, but they give teams much better evidence than total infrastructure reports alone. Names and controller types do not provide energy attribution by themselves.
</details>

---

## Hands-On Exercise: Build a GreenOps Review Plan

**Goal**: Practice diagnosing sustainability waste and designing a safe improvement plan for a Kubernetes workload. This exercise is independent work; the worked example above showed the reasoning pattern, and now you will apply it to a different scenario without a provided solution.

You are reviewing a staging workload for a document conversion service. Product managers say the service is needed during business hours for testing, but it receives almost no requests overnight. Developers also mention that conversions are queued, so short delays are acceptable during staging tests. Review the manifest and create a GreenOps plan that improves sustainability without pretending staging reliability is irrelevant.

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: document-converter-staging
  labels:
    app: document-converter
    environment: staging
    owner: docs-team
spec:
  replicas: 4
  selector:
    matchLabels:
      app: document-converter
      environment: staging
  template:
    metadata:
      labels:
        app: document-converter
        environment: staging
    spec:
      containers:
        - name: converter
          image: nginx:1.27
          resources:
            requests:
              cpu: "1500m"
              memory: "2Gi"
            limits:
              cpu: "2"
              memory: "3Gi"
```

### Task

Create a short review note that includes three parts. First, identify the likely sources of waste in the manifest and explain why each one matters for scheduling, node count, or idle energy. Second, propose a safer revised manifest or policy direction, such as lower requests, fewer replicas, event-driven scaling, off-hours scale-down, or a queue-based scaling approach. Third, define how you would verify the change after rollout using metrics or Kubernetes commands.

### Suggested Commands

Use these commands as examples if you have a Kubernetes 1.35+ practice cluster. They are safe inspection commands, and they help connect the paper exercise to real cluster operations. If you do not have a cluster available, write the expected evidence you would request from the platform team.

```bash
kubectl get deployment document-converter-staging -o yaml
kubectl top pods -l app=document-converter
kubectl get pods -l app=document-converter -o wide
kubectl describe deployment document-converter-staging
```

After you have used `kubectl` once, many Kubernetes practitioners use the alias `k` for speed. The alias is only a shell shortcut; it does not change the command behavior.

```bash
alias k=kubectl
k get deployment document-converter-staging
```

### Success Criteria

- [ ] Your review identifies at least three likely waste sources, including either replica count, resource requests, idle staging behavior, or missing queue-aware scaling.
- [ ] Your recommendations distinguish between safe staging changes and risky production assumptions, rather than claiming that all workloads should scale to zero.
- [ ] Your plan explains how the change could reduce node pressure or idle energy, not only how it changes the YAML.
- [ ] Your verification section includes at least two measurable signals, such as observed CPU, observed memory, replica count, pending Pods, node count, latency, queue depth, or restart count.
- [ ] Your plan includes a rollback or guardrail, such as restoring replicas, increasing requests, watching OOM kills, or setting a minimum replica count during business hours.
- [ ] Your answer uses the same reasoning pattern as the worked example: classify the workload, compare requests with usage, choose a practice, then verify the outcome.

### Reflection

When you finish, ask whether your plan saves carbon by removing actual waste or merely moves risk to another team. Good GreenOps changes are measurable and reversible. They improve the resource system while preserving the service promises that still matter.

---

## Next Module

Congratulations! You have completed Part 3: Cloud Native Architecture. Continue to [Part 4](/k8s/kcna/part4-application-delivery/) to explore Application Delivery.
