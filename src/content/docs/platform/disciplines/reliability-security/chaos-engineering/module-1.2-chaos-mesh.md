---
title: "Module 1.2: Chaos Mesh Fundamentals"
slug: platform/disciplines/reliability-security/chaos-engineering/module-1.2-chaos-mesh
sidebar:
  order: 3
revision_pending: false
---
> **Discipline Module** | Complexity: `[MEDIUM]` | Time: 2.5 hours | Prerequisites: [Module 1.1: Principles of Chaos Engineering](../module-1.1-chaos-principles/), Kubernetes Deployments, Services, Namespaces, and RBAC

## What You'll Be Able to Do

After completing this module, you should be able to move from a chaos hypothesis to a constrained Kubernetes experiment, explain why the experiment is safe enough to run, and describe how the same practice maps to another Kubernetes-native chaos tool without treating any tool as magic.

- **Implement Chaos Mesh on Kubernetes with proper RBAC, namespace scoping, and experiment scheduling**
- **Design pod-level chaos experiments — kill, CPU stress, memory stress, I/O delay — with Chaos Mesh CRDs**
- **Configure Chaos Mesh dashboards and workflows for recurring reliability validation**
- **Build automated chaos experiments that run as part of CI/CD pipelines before production deployments**

## Why This Module Matters

Hypothetical scenario: a checkout service runs with ten replicas, steady latency, and a clean deployment history. During a routine node drain, two replicas move at the same time, one remaining replica has a slow dependency call, and the service begins returning intermittent failures even though every individual Kubernetes object looks healthy. A team that only performs happy-path deployment tests learns about the weakness during an incident. A team that practices controlled chaos can discover the same weakness by killing one pod, delaying one dependency path, and watching whether the user-visible steady state stays inside its agreed bounds.

Chaos on Kubernetes matters because Kubernetes already gives you a control plane, an authorization system, an audit trail, selectors, namespaces, and reconciliation. A Kubernetes-native chaos tool turns a failure experiment into an API object that can be reviewed, applied, watched, paused, and deleted through the same operational muscle your team uses for Deployments and NetworkPolicies. The durable lesson is not that one project has a clever dashboard. The durable lesson is that failure injection becomes safer when the intent is declarative, scoped, observable, and reversible.

Chaos Mesh is the worked example in this module because it exposes the Kubernetes-native pattern clearly. You declare a `PodChaos`, `NetworkChaos`, `StressChaos`, or related custom resource, the controller-manager reconciles that object, and node-local daemons perform the low-level work needed to affect target pods. LitmusChaos uses a different object model and execution flow, but it teaches the same larger practice: represent chaos intent as Kubernetes resources, bind it to a narrow application target, execute it with controlled permissions, and record the result.

The most important shift is from "can I break a pod" to "can I test a falsifiable resilience claim with a bounded blast radius." A pod kill that proves nothing about user-visible behavior is only fault injection. A pod kill that begins with a steady-state metric, names the expected impact, limits the target set, defines abort conditions, and produces a decision is chaos engineering. Tools help you run the fault, but the engineering value comes from the question, the safety constraints, and the learning loop.

> **The Laboratory Analogy**
>
> A chaos platform is like a lab bench with labeled controls, safety interlocks, and a notebook. You still need a hypothesis, a small sample, and a way to stop the experiment. Without those, the same equipment becomes a way to make a mess faster.

> **Landscape snapshot — as of 2026-06. This changes fast; verify against vendor docs before relying on specifics.**
>
> Chaos Mesh is listed by CNCF as an Incubating project, and the current Chaos Mesh documentation set identifies version 2.8.3 while keeping the chaos experiment API group at `chaos-mesh.org/v1alpha1`. CNCF also lists Litmus as an Incubating project. Treat those maturity and version facts as dated skin: useful for tool selection and support checks, but not the durable spine of the practice.

## Kubernetes-Native Chaos Through CRDs

A Kubernetes-native chaos tool models experiments as custom resources because that is the native extension point for cluster intent. Kubernetes custom resources use the same API server path, authentication, authorization, and audit mechanisms as built-in resources, which means a `PodChaos` object can be governed like any other operational object. This is a large practical difference from a shell script that SSHes into nodes, because the API object can be reviewed before it runs, limited by RBAC, stored in Git, observed with `kubectl`, and deleted when the experiment must stop.

The CRD model also changes the mental model from imperative action to desired state. An imperative script says "run these commands against these processes right now," which pushes safety into script code and operator memory. A declarative resource says "for this duration, inject this fault into pods selected by this namespace and label rule," which gives the controller a resource to reconcile and gives humans a durable record to inspect. The tool still executes kernel-level or process-level work, but the request enters through a structured API.

That structure is why chaos experiments fit naturally into GitOps. A team can review a YAML manifest that names the namespace, labels, target mode, duration, and expected fault type before it ever reaches a cluster. The merge request discussion can focus on the hypothesis and blast radius instead of reverse-engineering a script. When the manifest is applied, the cluster records who created the object, which resource was changed, and what status the controller reports. When the manifest is removed, the controller has a clear signal to restore the injected fault.

The CRD pattern is not a guarantee of safety. A valid CRD can still target the wrong namespace, select too many pods, run for too long, or overload a shared node. Kubernetes gives you control points, not good judgment. The practice is to combine CRDs with narrow selectors, namespace policy, service-account permissions, admission controls when available, observability, and human review proportional to the risk of the target workload.

In LitmusChaos, the equivalent idea appears through resources such as `ChaosExperiment`, `ChaosEngine`, `ChaosResult`, and Argo-based workflow resources in current Litmus documentation. The names differ, and the execution model uses experiment templates and runners rather than the exact Chaos Mesh controller-manager plus daemon layout. The durable concept is the same: the experiment is a Kubernetes object with a lifecycle, a target, permissions, and results rather than an untracked command run from an operator laptop.

## Chaos Mesh Architecture

Chaos Mesh separates control-plane decisions from node-local injection. The Chaos Dashboard gives humans a visual way to create, observe, pause, and archive experiments. The chaos-controller-manager watches Chaos Mesh custom resources, schedules the requested work, reconciles status, and coordinates workflows and schedules. The chaos-daemon runs as a DaemonSet on nodes and performs the low-level injection tasks that require access to the target pod's process, network, file system, kernel, or cgroup context.

That split is a good design lesson even if you later use a different chaos tool. The controller-manager should understand desired state, ownership, and lifecycle, while the node agent should understand local mechanics. Network latency is not created by the API server itself; it is commonly implemented through Linux traffic-control rules in the relevant network namespace. CPU and memory pressure are not created by editing a Deployment; they are created by a process or mechanism that consumes resources in the selected container context. Keeping those responsibilities separate makes the system easier to reason about.

The architecture also explains why chaos-daemon permissions are a real security concern. The daemon is expected to affect network devices, file systems, kernels, and target pod namespaces, and the Chaos Mesh overview documents that it runs as a DaemonSet with privileged permission by default unless that is changed. This is not an incidental implementation detail. Any component that can enter namespaces or manipulate kernel-facing controls deserves the same review you would give a powerful node agent.

The safest way to think about the architecture is "Kubernetes API for intent, controller for lifecycle, daemon for injection, dashboard for visibility." The API object is where you constrain the blast radius. The controller is where the cluster turns that object into a running experiment. The daemon is where the physical fault is applied. The dashboard and `kubectl describe` output are where operators watch whether the experiment is injecting, running, paused, finished, or stuck.

The following sketch keeps the important control path visible without pretending every internal call matters to the learner:

```text
User or GitOps controller
        |
        v
Kubernetes API Server
        |
        v
Chaos Mesh custom resource
        |
        v
chaos-controller-manager
        |
        v
chaos-daemon on the target node
        |
        v
selected pod namespace, cgroup, network path, or file path
```

When an experiment does nothing, this architecture gives you a troubleshooting map. If the API server rejects the manifest, the YAML, CRD, or RBAC path is wrong. If the object exists but never selects targets, the namespace, labels, field selectors, or mode are wrong. If targets are selected but no fault appears, the node-local daemon, runtime socket, permissions, or injection mechanism is the next place to inspect.

## Fault Taxonomy: What You Are Really Testing

Fault types are useful only when they are connected to a resilience question. `PodChaos` tests how the workload and platform react when a pod or container disappears or remains unavailable. `NetworkChaos` tests whether timeouts, retries, load balancing, circuit breakers, and dependency behavior survive latency, loss, partition, corruption, or bandwidth pressure. `StressChaos` tests whether resource requests, limits, throttling, autoscaling, and overload behavior work under CPU or memory pressure. Each fault should map to a real event the system might face.

Chaos Mesh exposes additional fault types that widen the taxonomy beyond pods and packets. `IOChaos` can delay, fail, or corrupt file-system operations and should be treated carefully because storage faults can damage data. `TimeChaos` changes time behavior for selected pods, which is useful for testing caches, certificate logic, leases, and deadline code. `DNSChaos` returns errors or random responses for matching domains, which helps test name-resolution assumptions. `KernelChaos` targets kernel-level failures, and `HTTPChaos` affects request or response behavior such as aborts, delays, replacement, and patching for HTTP traffic.

The durable taxonomy is process, network, resource, storage, time, name resolution, kernel, and application protocol. The tool-specific resource names help you express those categories on Kubernetes, but the category is what guides experiment design. If the production risk is "one replica disappears," `PodChaos` is a close match. If the risk is "the payment provider becomes slow but not down," network delay or HTTP delay is closer than a pod kill. If the risk is "a shared node becomes noisy," CPU or memory stress may be the right first probe.

The equivalent in LitmusChaos is not a one-to-one name match for every Chaos Mesh kind. Litmus commonly packages faults as templates or fault definitions from ChaosHub and combines them into experiments through ChaosCenter and workflow resources. A Chaos Mesh `PodChaos` pod-kill and a Litmus pod-delete fault both test workload behavior when a selected pod disappears, but their YAML shape, runners, result objects, and dashboards differ. Avoid translating by tool names alone; translate by the failure mode and the target scope.

The first mistake beginners make is choosing the most dramatic fault instead of the smallest fault that can disprove the hypothesis. If you want to test whether a stateless service tolerates one replica loss, killing all replicas is not more rigorous. It simply bypasses the question and creates guaranteed downtime. If you want to test retry behavior, adding a small amount of latency to one dependency path is often more revealing than deleting the dependency entirely, because slow partial failure is where many distributed systems behave worst.

## Targeting, Modes, and Blast Radius

Targeting is the safety core of Kubernetes chaos. Chaos Mesh selectors can use namespaces, labels, expressions, annotations, fields, pod phases, nodes, or explicit pod lists, and multiple selectors narrow the target set together unless you use an explicit pod list that overrides other selector rules. The defaulting behavior also matters: if a namespace selector is omitted, Chaos Mesh uses the namespace of the experiment object. That can be convenient in a lab, but production experiments should make target namespaces explicit so review does not depend on implicit behavior.

The `mode` field controls how many eligible targets are affected after the selector identifies the candidate set. `one` chooses one random pod, `all` chooses every eligible pod, `fixed` chooses a specific count, `fixed-percent` chooses a percentage, and `random-max-percent` chooses up to a percentage. The `value` field is required for the modes that need an argument, such as `fixed` or `fixed-percent`. This pairing is where the blast radius becomes concrete rather than aspirational.

For early experiments, `mode: one` is usually the best teaching mode because it keeps the experiment legible. If the system cannot survive one selected pod failure in a non-production namespace, you have learned something before involving more targets. After the team has validated observability, abort behavior, and recovery expectations, `fixed` or a small `fixed-percent` can model partial capacity loss. `mode: all` should be reserved for environments and workloads where full-target impact is intentional, understood, and approved.

Duration is another blast-radius boundary. A one-time experiment with a `duration` lets Chaos Mesh restore supported faults when the timer expires, while deleting or pausing the experiment gives operators an immediate control action. Duration is not a substitute for abort conditions, because a bad experiment can cause unacceptable impact before the timer ends. It is still an important safety default because it prevents forgotten experiments from becoming permanent environmental damage.

Namespace controls add a second layer. Current Chaos Mesh documentation describes a `FilterNamespace` feature that must be enabled before namespace allowlisting takes effect; when it is enabled, Chaos Mesh injects into namespaces annotated with `chaos-mesh.org/inject=enabled`, while other namespaces are protected from injection. This is the opposite of the common but unsafe habit of trusting people to avoid production by memory. Make allowed namespaces explicit, and then bind service accounts only to the namespaces where chaos should run.

```yaml
apiVersion: chaos-mesh.org/v1alpha1
kind: PodChaos
metadata:
  name: frontend-one-pod-kill
  namespace: chaos-demo
spec:
  action: pod-kill
  mode: one
  selector:
    namespaces:
      - chaos-demo
    labelSelectors:
      app: frontend
  duration: "30s"
  gracePeriod: 0
```

This manifest is intentionally small. It names one namespace, uses one label selector, chooses one eligible pod, sets a short duration, and uses `gracePeriod: 0` to model a hard pod termination. The same pattern in LitmusChaos would be a pod-delete style fault bound through a `ChaosEngine` or a current ChaosCenter experiment to a target namespace and application label, with runner permissions scoped to the experiment namespace.

## Designing Pod, Resource, and I/O Experiments

Pod-level chaos is the first practical bridge from theory to cluster behavior. A `pod-kill` experiment tests whether controllers replace failed pods, readiness gates remove unhealthy endpoints, clients retry safely, and enough replicas remain available. A `pod-failure` experiment is different: it keeps a pod unavailable for the configured duration and is closer to a hung or inaccessible dependency. A `container-kill` experiment is useful when a pod has sidecars or multiple containers and you need to know whether losing only one container breaks the pod's contract.

CPU and memory stress ask a different question. They are less about replacement and more about saturation, throttling, limits, autoscaling, and overload protection. A service may survive a killed pod but fail badly when one replica becomes slow and still receives traffic. That is why stress experiments are important: real failures often degrade rather than disappear, and degraded replicas can poison latency percentiles, retry queues, and downstream dependencies before Kubernetes decides they are unhealthy.

I/O chaos is even more sensitive because it touches the persistence boundary. Delaying or failing file operations can reveal whether a database, cache, queue, or application handles storage slowness correctly, but careless production I/O faults can corrupt data or trigger recovery paths that are hard to reverse. Start with disposable state, replicas, snapshots, and non-production environments. If you later test a production-like storage path, make the hypothesis, rollback plan, and data-protection controls explicit before the CRD is applied.

The design method is the same across these resource types. First write the user-visible steady state, such as error rate, successful checkout count, or response latency. Then pick the smallest fault that represents the real event. Next choose selectors and `mode` to bound the target set. Finally decide how you will observe impact and when you will abort. YAML is the last step, not the first step.

```yaml
apiVersion: chaos-mesh.org/v1alpha1
kind: StressChaos
metadata:
  name: backend-cpu-stress-one-pod
  namespace: chaos-demo
spec:
  mode: one
  selector:
    namespaces:
      - chaos-demo
    labelSelectors:
      app: backend
  stressors:
    cpu:
      workers: 1
      load: 60
  duration: "90s"
```

This CPU stress example is deliberately modest because it is meant to validate the experiment loop, not prove toughness through spectacle. The `workers` and `load` fields map to the current StressChaos CPU stressor shape, and the selected pod should already have CPU requests, CPU limits, readiness probes, and useful metrics. If those basics are missing, the chaos experiment will mostly reveal that the platform hygiene is incomplete.

For memory stress, the same caution applies more strongly. Allocating memory inside a constrained container may trigger an OOM kill, which can be a valid experiment if that is the intended failure mode. It is a poor surprise. If the hypothesis is about graceful degradation under pressure, use a size comfortably below the memory limit and watch the service-level symptom. If the hypothesis is about OOM recovery, say so plainly and treat the experiment like a pod loss plus overload test.

## NetworkChaos as the Distributed-Systems Workhorse

Network faults are often the highest-value chaos experiments because distributed systems are built on fallible communication. A service can lose a packet, receive a slow response, hit a bandwidth ceiling, see a corrupted packet, or become partitioned from a dependency while everything still appears "up" from a process perspective. Those are exactly the conditions where retry storms, queue buildup, thread exhaustion, and broken timeout budgets appear.

Chaos Mesh `NetworkChaos` supports actions such as `delay`, `loss`, `duplicate`, `corrupt`, `partition`, `bandwidth`, and `netem`, with `target` and `direction` controlling which traffic is affected. The selector names the source pods that receive the injection, while the optional target selector and direction constrain packets relative to another selected set. If you omit target constraints, you may affect more traffic than intended. That is why a network experiment must be reviewed as a traffic-path experiment, not merely as a pod-selection experiment.

```yaml
apiVersion: chaos-mesh.org/v1alpha1
kind: NetworkChaos
metadata:
  name: frontend-to-backend-delay
  namespace: chaos-demo
spec:
  action: delay
  mode: all
  selector:
    namespaces:
      - chaos-demo
    labelSelectors:
      app: frontend
  delay:
    latency: "150ms"
    correlation: "50"
    jitter: "25ms"
  target:
    selector:
      namespaces:
        - chaos-demo
      labelSelectors:
        app: backend
    mode: all
  direction: to
  duration: "120s"
```

This example adds latency to packets from the selected frontend pods to the selected backend pods. The important part is not the particular latency value; it is the explicit path. The manifest says which source pods, which target pods, which direction, and how long. A review can now ask whether frontend timeouts, retries, and user-visible latency budgets make this a meaningful experiment. Without that path specificity, a broad network fault may accidentally include probes, metrics, or unrelated dependencies.

Packet loss and corruption should be introduced with even more care. Small loss rates can produce large latency changes when clients retry aggressively or when TCP congestion control reacts to repeated loss. Corruption tests are useful when you need to understand protocol robustness, but many application stacks already rely on lower layers to detect corrupted packets, so the learning value depends on the path. Bandwidth limits are valuable for backup, replication, and bulk-transfer behavior because they reveal whether systems degrade fairly or starve interactive traffic.

The equivalent in LitmusChaos is usually selected from network-oriented faults in ChaosHub or current ChaosCenter fault catalogs, then bound into an experiment with probes and target metadata. Again, do not compare tools by asking which YAML looks shorter. Compare whether the chosen tool can express the real path, constrain the blast radius, expose status, run under acceptable permissions, and integrate with your observation and rollback process.

This module points you to [Module 1.3: Advanced Network & Application Fault Injection](../module-1.3-network-fault-injection/) for deeper network work because network chaos deserves its own treatment. The key foundation here is that Kubernetes-native chaos is still distributed-systems engineering. The manifest is only correct if it represents the communication path you intend to stress.

## Orchestration: Schedules, Workflows, Status, and Abort Paths

Single experiments are good for learning the mechanics, but reliability validation becomes durable when experiments can be repeated under controlled conditions. Chaos Mesh uses a `Schedule` custom resource for scheduled or cyclic experiments, with cron-like scheduling, `historyLimit`, and `concurrencyPolicy` fields. That is useful when a team wants to verify a known resilience property periodically, such as one frontend pod loss in staging every weekday during office hours.

Scheduling chaos is not the same as making chaos safe. A recurring experiment needs the same hypothesis, target scope, observation, and abort criteria as a manual one, plus a review of timing. An experiment that is safe during a quiet non-production window may be noisy during a load test or release rehearsal. `concurrencyPolicy: Forbid` is a sensible default when overlapping experiments would make results confusing or amplify risk.

```yaml
apiVersion: chaos-mesh.org/v1alpha1
kind: Schedule
metadata:
  name: weekday-frontend-one-pod-kill
  namespace: chaos-demo
spec:
  schedule: "0 14 * * 1-5"
  historyLimit: 5
  concurrencyPolicy: "Forbid"
  type: "PodChaos"
  podChaos:
    action: pod-kill
    mode: one
    selector:
      namespaces:
        - chaos-demo
      labelSelectors:
        app: frontend
    duration: "30s"
    gracePeriod: 0
```

Workflows are for multi-step experiments where the order matters. Chaos Mesh Workflow can run experiments serially or in parallel, include task nodes, check status, and use status checks that can abort a workflow when a monitored system becomes unhealthy. That gives you a way to encode a game-day script as a cluster object: verify a dependency is healthy, inject a pod fault, check the application, inject a network delay, check again, and stop if a guardrail fails.

Status is part of the learning loop, not an afterthought. Chaos Mesh documents lifecycle states such as injecting, running, paused, and finished, and `kubectl describe` exposes status and events for an experiment object. If an experiment stays in injecting for too long, that is a signal to inspect selectors, events, daemon health, and permissions. A dashboard can make active experiments visible, but `kubectl` status remains important because it works in automation and incident response.

Pause and delete paths need to be practiced before a risky experiment. Deleting or pausing an experiment should restore supported injected faults, and workflows can use status checks as an automated abort path. Operators should know both the dashboard action and the `kubectl` action because dashboards can be unavailable during the same infrastructure stress you are investigating. If a network fault lingers because node-local cleanup failed, deleting the affected pod may be safer than hand-editing low-level network rules in a live incident.

LitmusChaos has equivalent orchestration concerns, even though the implementation differs. Current Litmus documentation describes chaos experiments built from steps, Argo workflow resources, ChaosEngine target binding, ChaosResult output, probes, and cron-style scheduling. The durable question is whether the orchestration records intent, sequences faults, verifies probes, captures results, and gives operators a way to stop safely.

## RBAC, Namespace Boundaries, and Operational Safety

Chaos permissions should be narrower than deployment permissions in many organizations. A developer may be allowed to deploy a service to staging without being allowed to inject kernel or network faults into every namespace. Kubernetes RBAC lets you grant verbs for resources in the `chaos-mesh.org` API group just as you would for built-in resources. The safest starting point is a namespaced Role that allows creating only the specific chaos resource types needed for the lab or service team.

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: chaos-demo-operator
  namespace: chaos-demo
rules:
  - apiGroups: ["chaos-mesh.org"]
    resources: ["podchaos", "networkchaos", "stresschaos"]
    verbs: ["get", "list", "watch", "create", "update", "patch", "delete"]
  - apiGroups: ["chaos-mesh.org"]
    resources: ["iochaos", "timechaos", "dnschaos", "httpchaos", "kernelchaos"]
    verbs: ["get", "list", "watch"]
---
apiVersion: v1
kind: ServiceAccount
metadata:
  name: chaos-demo-runner
  namespace: chaos-demo
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: chaos-demo-runner
  namespace: chaos-demo
subjects:
  - kind: ServiceAccount
    name: chaos-demo-runner
    namespace: chaos-demo
roleRef:
  kind: Role
  name: chaos-demo-operator
  apiGroup: rbac.authorization.k8s.io
```

This Role intentionally makes advanced fault families read-only for the runner. That is not because `IOChaos`, `TimeChaos`, `DNSChaos`, `HTTPChaos`, or `KernelChaos` are bad. It is because they deserve a separate review when a team is still learning the platform. Permissions should reflect the organization's current operating maturity, not the tool's full feature list.

Dashboard access needs the same discipline. Chaos Mesh user-permission documentation notes that the dashboard uses RBAC authorization and warns against disabling permission authentication in production environments. In a lab, a temporarily open dashboard may help a learner understand the interface. In shared environments, the dashboard should authenticate users and map their actions back to Kubernetes permissions so the visual UI does not bypass the same controls you require from YAML.

Namespace allowlisting should be part of installation design, not a cleanup task after someone makes a mistake. If `FilterNamespace` is enabled, only namespaces annotated with `chaos-mesh.org/inject=enabled` are allowed injection targets. That creates a positive allowlist. Pair it with service-account Roles in those namespaces, resource quotas, observability, and environment naming that makes target selection obvious during code review.

Finally, run the first version of every new experiment in non-production unless there is a documented reason not to. The Principles of Chaos Engineering encourage production realism, but they also emphasize minimizing blast radius. The path is progressive: prove the manifest selects the intended targets in a lab, prove the observation and abort path in staging, then decide whether a production experiment is justified and how small it can be.

## CI/CD Integration Without Turning Chaos Into a Stunt

Automated chaos belongs in CI/CD only when the experiment is deterministic enough to provide a useful signal and constrained enough not to turn a build into an incident. A pre-production pipeline can deploy an ephemeral environment, wait for steady state, apply a short `PodChaos` or `NetworkChaos` object, watch user-visible checks, delete the object, and fail the pipeline if the agreed steady state is violated. That is a reliability gate, not a random disruption.

The first useful pipeline experiment is usually a single pod failure for a stateless service with at least two replicas, readiness probes, and service-level checks. The pipeline should not merely assert that the Kubernetes pod returns to Running. It should assert that the service stayed inside its user-facing error and latency bounds or that the expected short degradation was observed and recovered. A chaos pipeline that only watches pod status can miss the customer symptom entirely.

Chaos Mesh has a GitHub Actions integration documented by the project, but the durable pattern does not depend on one CI provider. Any pipeline can apply a CRD, poll status, query metrics, and clean up resources if it has the right cluster access. The important controls are isolation, short duration, cleanup on failure, metrics-based pass/fail, and narrow service-account permissions. A pipeline service account with broad cluster chaos rights is a future incident waiting for a typo.

GitOps changes the integration point. Instead of a pipeline directly applying chaos YAML, a repository change can add or modify a scheduled experiment in a non-production cluster. Reviewers can discuss the hypothesis, target scope, and rollback path in the pull request. The cluster reconciles the approved object, and the dashboard or metrics system records the result. This is especially useful for recurring experiments because drift is visible in Git.

LitmusChaos offers similar automation concepts through ChaosCenter, GitOps configuration, Argo workflow integration, probes, and cron experiments. The main comparison is not "which tool has CI." It is whether your automation model gives reviewers enough context, limits credentials, records results, and stops safely when the system is unhealthy. Chaos automation that cannot explain its own outcome is just a scheduled disturbance.

## Chaos Mesh and LitmusChaos as Peer Patterns

Chaos Mesh and LitmusChaos are both CNCF Incubating projects in the current CNCF project pages, and both are Kubernetes-native in the sense that they model chaos through cluster resources and controller-driven execution. They are peers, not a ranked ladder. The right comparison is capability and operating model: how each expresses targets, faults, schedules, workflows, probes, permissions, dashboards, and result history.

Chaos Mesh is direct when you want to teach fault CRDs as first-class objects. A `PodChaos` resource is the experiment intent, a `NetworkChaos` resource is the network fault, and a `Schedule` or `Workflow` composes repetition or sequence. This makes it a clear learning tool for Kubernetes operators who already understand custom resources and reconciliation. The tradeoff is that learners must understand each fault kind and its fields well enough to avoid overbroad injection.

LitmusChaos is template- and experiment-oriented. Current Litmus documentation describes ChaosHub as a repository-backed collection of experiment templates and faults, and a chaos experiment as a workflow-like composition that can install faults, create a `ChaosEngine`, run probes, revert chaos, and calculate results. This can be attractive when a team wants a catalog and experiment assembly experience. The tradeoff is that the object model has more moving pieces to understand before debugging a failed run.

The Rosetta below keeps the durable capability as the row and the project-specific expression as the cell. Use it to translate concepts, not to choose a winner.

| Durable capability | Chaos Mesh expression | LitmusChaos expression |
|---|---|---|
| Declare a pod failure | `PodChaos` with `pod-kill`, `pod-failure`, or `container-kill` | Pod-delete or related fault bound through experiment resources |
| Declare a network fault | `NetworkChaos` with delay, loss, partition, corrupt, bandwidth, or netem | Network fault from ChaosHub or ChaosCenter catalog |
| Bind target scope | `selector`, namespace filters, labels, `mode`, and `value` | Application metadata, experiment variables, and ChaosEngine target binding |
| Repeat experiments | `Schedule` custom resource | Cron chaos experiment or scheduled workflow |
| Sequence multiple steps | `Workflow` and workflow nodes | Argo-based chaos experiment workflow |
| Check health during a run | Workflow `StatusCheck`, metrics, and external probes | Litmus probes and result calculation |
| Observe results | Dashboard, `kubectl describe`, status, and events | ChaosCenter, ChaosResult, workflow status, and probes |

The practical decision is usually local. If your team already operates CRDs through GitOps and wants direct fault resources, Chaos Mesh may be easier to explain. If your team wants a hub of reusable fault templates and a workflow-centered experiment UI, LitmusChaos may fit better. In both cases, the tool should be evaluated against your safety requirements, supported environments, audit model, and ability to teach engineers what the experiment actually does.

## Patterns & Anti-Patterns

Good chaos practice begins with a small falsifiable claim. The pattern is "one hypothesis, one target set, one fault, one observation window, one rollback path." This keeps the result interpretable. If the experiment passes, you know which claim gained confidence. If it fails, you know which recovery behavior needs work. If you combine five new faults, three services, and unclear metrics, you may generate excitement but little engineering knowledge.

Another strong pattern is treating selectors as a safety interface. Namespace, label, and mode choices should be reviewed with the same seriousness as a production NetworkPolicy or RBAC change. A manifest with `mode: all` and a broad label selector should trigger a discussion before it triggers a fault. A manifest with explicit namespace, application label, duration, and a small mode is easier to approve because the blast radius is visible.

A third pattern is pairing chaos with observability before automation. Metrics, logs, traces, synthetic checks, and dashboard visibility should already show steady state before an experiment runs. The experiment then tests the system and the observability at the same time. If the service fails and nobody sees it in the expected place, the observability gap is part of the finding.

| Pattern | Why it works | Example |
|---|---|---|
| Hypothesis-first manifest | Prevents random fault injection from replacing learning | "One frontend pod can die while HTTP success stays inside the agreed bound" |
| Progressive blast radius | Builds confidence before widening impact | Lab namespace, then staging service, then tightly scoped production window if justified |
| API-object review | Makes scope, duration, and permissions visible | Review `PodChaos`, `NetworkChaos`, `Schedule`, and RBAC in Git |
| Observable abort path | Stops experiments when the user-visible state is unhealthy | Workflow status check, dashboard pause, and `kubectl delete` cleanup path |

Anti-patterns tend to hide risk. The most common is using chaos as a demo stunt: someone kills pods in a meeting, the cluster repairs them, and the team declares victory without checking user-visible behavior. Another anti-pattern is tool maximalism, where a team adopts every fault type before it can safely run one simple experiment. A third is dashboard-only operation, where experiments are created visually but never reviewed, versioned, or tied to a hypothesis.

| Anti-pattern | Why it is risky | Better approach |
|---|---|---|
| Fault first, hypothesis later | The result cannot be interpreted as evidence | Write the steady-state claim before choosing the fault |
| Broad selectors in shared clusters | A small typo can select unrelated workloads | Use explicit namespaces, labels, and small `mode` values |
| Unauthenticated or overprivileged dashboard | Visual convenience bypasses authorization discipline | Map dashboard users to RBAC and avoid disabled auth in shared environments |
| Recurring chaos without ownership | Scheduled faults become background noise | Assign an owner, review results, and expire experiments that no longer teach |

### Decision Framework

Use this matrix when deciding whether an experiment is ready to run. A "no" in the left columns does not always block the experiment, but it should move the experiment to a safer environment or force a design change before automation.

| Decision question | Safer answer | Riskier answer | Action |
|---|---|---|---|
| Is the hypothesis falsifiable? | It names a steady-state metric and expected behavior | It says "see what happens" | Rewrite the hypothesis before applying YAML |
| Is the target narrow? | Namespace, labels, and `mode` bound impact | Broad selector or `mode: all` | Reduce target scope or move to a lab |
| Is the abort path practiced? | Dashboard, `kubectl`, and cleanup owner are known | Nobody has tested pause or delete | Rehearse abort on a harmless experiment |
| Is observability ready? | User-visible checks exist before injection | Only pod phase will be watched | Add service-level checks before running |
| Are permissions least-privilege? | Namespaced Role and limited chaos kinds | Cluster-wide create on all chaos resources | Split roles by namespace and fault family |

## Did You Know?

- **Chaos Mesh keeps the API group at `chaos-mesh.org/v1alpha1` in current examples**: The version string in a CRD API group is not the same thing as the Helm chart or documentation version, so verify the CRD schema rather than assuming the project release number changes the manifest prefix.
- **Namespace allowlisting is positive, not negative**: With the current `FilterNamespace` feature enabled, Chaos Mesh injects into namespaces annotated with `chaos-mesh.org/inject=enabled`, so protected namespaces are the ones that lack the allowlist annotation.
- **Network direction is part of the fault, not decoration**: In `NetworkChaos`, `target` and `direction` decide which packets are affected, so a valid manifest can still be the wrong experiment if it delays probes, metrics, or unrelated service calls.
- **LitmusChaos changed some user-facing terminology in version 3.0.0**: Current Litmus docs note a terminology shift from "Chaos Experiment" to "Chaos Fault" and from scenario or workflow language to "Chaos Experiment," which is why concept translation matters more than memorizing names.

## Common Mistakes

| Mistake | Why It's a Problem | Better Approach |
|---|---|---|
| Treating a pod kill as proof of resilience | Kubernetes replacement can succeed while users still see errors, slow retries, or failed sessions | Measure user-visible steady state before, during, and after the pod fault |
| Omitting explicit namespaces in selectors | Reviewers must infer scope from object placement, which is fragile under copy-paste and automation | Always name target namespaces in production-like manifests |
| Starting with `mode: all` | Full-target impact often proves only that removing every healthy replica causes downtime | Start with `mode: one`, then widen deliberately if the hypothesis requires it |
| Running StressChaos without resource limits | CPU or memory pressure can spill into node-level symptoms and obscure the workload behavior | Add requests, limits, probes, and metrics before stress experiments |
| Using dashboard security shortcuts in shared environments | Convenience can bypass RBAC expectations and make audit trails harder to trust | Enable authenticated dashboard use and bind actions to scoped service accounts |
| Scheduling experiments without result review | Recurring chaos becomes noise and may mask drift or flaky services | Assign an owner, review history, and remove stale schedules |
| Treating Chaos Mesh and LitmusChaos as rankings | Tool advocacy distracts from fault model, scope, permissions, and evidence | Compare capabilities and tradeoffs against the experiment you need to run |
| Forgetting cleanup verification | Deleted objects may not prove the user-visible fault is gone, especially after node-agent disruption | Verify experiment status, service metrics, and target pod behavior after cleanup |

## Quiz

### Question 1

Your platform team wants to **Implement Chaos Mesh on Kubernetes with proper RBAC, namespace scoping, and experiment scheduling** for a staging checkout namespace. The proposed plan gives the CI service account cluster-wide create permissions on every Chaos Mesh resource because "staging is not production." What should you change before approving the plan?

<details>
<summary>Answer</summary>

Use a namespaced Role in the staging namespace and grant only the chaos kinds needed for the first experiments, such as `podchaos`, `networkchaos`, and `stresschaos`. Enable namespace allowlisting if your installation uses the Chaos Mesh `FilterNamespace` feature, then annotate only approved namespaces with `chaos-mesh.org/inject=enabled`. For scheduling, require `concurrencyPolicy: "Forbid"` unless overlapping runs are explicitly part of the hypothesis. This implements the outcome without letting a pipeline typo target unrelated namespaces or advanced fault families.

</details>

### Question 2

You need to **Design pod-level chaos experiments — kill, CPU stress, memory stress, I/O delay — with Chaos Mesh CRDs** for a service that currently has one replica and no readiness probe. Which experiment should run first, and why?

<details>
<summary>Answer</summary>

No destructive experiment should run first because the workload is not ready for meaningful chaos. A single-replica pod kill only proves that removing the only serving replica causes downtime, and stress without probes or resource limits gives you little interpretable data. Add replicas, readiness probes, resource requests, resource limits, and service-level checks before using `PodChaos` or `StressChaos`. For I/O delay, use disposable data or a non-production storage path because storage faults can affect correctness, not only availability.

</details>

### Question 3

A team applies a `NetworkChaos` delay and sees the backend marked unready, even though the intended hypothesis was only about frontend calls to the backend. The manifest selected backend pods and used `direction: both` without a target selector. What likely went wrong?

<details>
<summary>Answer</summary>

The experiment affected a broader traffic set than the hypothesis required. By selecting backend pods and using `direction: both` without a target selector, the team risked delaying traffic beyond the frontend-to-backend path, including probes or unrelated communication. The corrected design should select the source pods, add a target selector for the dependency path, and choose `direction` deliberately. This is why network experiments must be reviewed as path experiments rather than only pod experiments.

</details>

### Question 4

You want to **Configure Chaos Mesh dashboards and workflows for recurring reliability validation** after several successful manual experiments. What should be true before turning a pod-kill experiment into a weekday `Schedule`?

<details>
<summary>Answer</summary>

The manual run should already have a clear hypothesis, reliable metrics, a known cleanup path, and a result that the team reviewed. The scheduled manifest should keep target scope narrow, use a short duration, set `historyLimit`, and usually set `concurrencyPolicy: "Forbid"` so overlapping runs do not confuse results. Dashboard visibility is useful, but `kubectl describe` and metrics should also show status for automation and incident response. A schedule without ownership is not validation; it is a recurring disturbance.

</details>

### Question 5

Your CI pipeline deploys an ephemeral namespace, applies a short `PodChaos`, waits for pods to return to Running, and then marks the build successful. The team claims this **Build automated chaos experiments that run as part of CI/CD pipelines before production deployments** outcome is complete. What is missing?

<details>
<summary>Answer</summary>

The pipeline is checking Kubernetes recovery but not the user-visible steady state. It should send or query service-level checks before, during, and after the fault, then fail if error rate, latency, or another agreed output violates the hypothesis. It should also delete the chaos object on success or failure and use a scoped service account for the ephemeral namespace. A useful CI chaos gate produces evidence about application resilience, not only pod lifecycle repair.

</details>

### Question 6

Your team compares Chaos Mesh and LitmusChaos and asks which one is "the best Kubernetes chaos tool." How should you reframe the decision?

<details>
<summary>Answer</summary>

Reframe the question around capabilities and tradeoffs rather than ranking. Ask how each tool expresses target scope, fault types, schedules, workflows, probes, dashboard access, RBAC, results, and GitOps integration for your experiments. Chaos Mesh gives direct fault CRDs such as `PodChaos` and `NetworkChaos`, while LitmusChaos emphasizes ChaosHub, ChaosCenter, workflow composition, `ChaosEngine`, and result resources. The better choice is the one your team can operate safely and explain clearly for the failure modes you actually need to test.

</details>

### Question 7

During a chaos run, the `PodChaos` object exists but no pod is selected. The controller and daemon pods are healthy, and RBAC allows the object to be created. Which part of the manifest should you inspect first?

<details>
<summary>Answer</summary>

Inspect the selector and namespace fields first because selection happens before injection. A missing namespace selector may default differently than the author expected, a label selector may not match current pod labels, or a pod phase selector may exclude the intended target. Then inspect `mode` and `value` to ensure the selected candidate set can produce an affected pod. If no target is selected, debugging the chaos-daemon is premature because the daemon has not received meaningful work for that pod.

</details>

## Hands-On

In this exercise, you will run a narrow pod-kill experiment against a disposable namespace and document whether a simple Service keeps responding. The goal is not to create a heroic failure; it is to practice the loop of steady state, hypothesis, scoped CRD, observation, cleanup, and conclusion.

### Setup a Disposable Target

Create the namespace and deployment below in a non-production cluster where Chaos Mesh is already installed. The `nginx:1.27` and `curlimages/curl:8.11.1` image tags were verified at authoring time, but image availability can still change, so recheck them if your registry mirror blocks public pulls.

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: chaos-demo
  labels:
    purpose: chaos-lab
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: frontend
  namespace: chaos-demo
spec:
  replicas: 3
  selector:
    matchLabels:
      app: frontend
  template:
    metadata:
      labels:
        app: frontend
    spec:
      containers:
        - name: nginx
          image: nginx:1.27
          ports:
            - containerPort: 80
          readinessProbe:
            httpGet:
              path: /
              port: 80
            initialDelaySeconds: 5
            periodSeconds: 5
          resources:
            requests:
              cpu: 50m
              memory: 64Mi
            limits:
              cpu: 200m
              memory: 128Mi
---
apiVersion: v1
kind: Service
metadata:
  name: frontend
  namespace: chaos-demo
spec:
  selector:
    app: frontend
  ports:
    - name: http
      port: 80
      targetPort: 80
```

```bash
kubectl apply -f frontend-demo.yaml
kubectl wait --for=condition=available deployment/frontend -n chaos-demo --timeout=120s
kubectl get pods -n chaos-demo -l app=frontend
```

### Record Steady State

Run a short service check before applying chaos. If this check is already flaky, stop and fix the target before injecting faults.

```bash
kubectl run frontend-check \
  --image=curlimages/curl:8.11.1 \
  --rm -i --restart=Never \
  -n chaos-demo \
  -- sh -c 'for i in $(seq 1 10); do curl -s -o /dev/null -w "%{http_code}\n" http://frontend.chaos-demo.svc.cluster.local/; done'
```

Write a hypothesis in your notes before continuing. A suitable starter hypothesis is: "The frontend Service will return HTTP 200 for every sampled request while one of three frontend pods is killed, because the Service has remaining ready endpoints and the Deployment will create a replacement pod."

### Apply the PodChaos

Save this manifest as `frontend-pod-kill.yaml`, apply it, and watch pods and service checks in separate terminals. Keep the duration short so the exercise remains easy to reason about.

```yaml
apiVersion: chaos-mesh.org/v1alpha1
kind: PodChaos
metadata:
  name: frontend-pod-kill
  namespace: chaos-demo
spec:
  action: pod-kill
  mode: one
  selector:
    namespaces:
      - chaos-demo
    labelSelectors:
      app: frontend
  duration: "30s"
  gracePeriod: 0
```

```bash
kubectl get pods -n chaos-demo -l app=frontend -w
```

```bash
kubectl apply -f frontend-pod-kill.yaml
kubectl describe podchaos frontend-pod-kill -n chaos-demo
```

```bash
kubectl run frontend-check-during-chaos \
  --image=curlimages/curl:8.11.1 \
  --rm -i --restart=Never \
  -n chaos-demo \
  -- sh -c 'for i in $(seq 1 20); do date +%H:%M:%S; curl -s -o /dev/null -w "%{http_code}\n" http://frontend.chaos-demo.svc.cluster.local/; sleep 1; done'
```

### Clean Up and Decide

Cleanup is part of the experiment, not housekeeping. Delete the chaos object, confirm that the pods are ready, and write whether the hypothesis was confirmed, refuted, or inconclusive.

```bash
kubectl delete podchaos frontend-pod-kill -n chaos-demo --ignore-not-found
kubectl wait --for=condition=available deployment/frontend -n chaos-demo --timeout=120s
kubectl get podchaos,networkchaos,stresschaos -n chaos-demo
kubectl get pods -n chaos-demo -l app=frontend
```

### Success Criteria

- [ ] You recorded steady state before applying the chaos resource.
- [ ] You wrote a falsifiable hypothesis that named both the fault and the expected service behavior.
- [ ] You applied a `PodChaos` manifest with explicit namespace, label selector, `mode: one`, and short duration.
- [ ] You observed both pod lifecycle and HTTP response behavior during the experiment.
- [ ] You deleted the chaos object and verified no chaos resources remained in the namespace.
- [ ] You documented whether the result confirmed, refuted, or failed to test the hypothesis.

## Sources

- [Chaos Mesh Overview](https://chaos-mesh.org/docs/)
- [Chaos Mesh Basic Features](https://chaos-mesh.org/docs/basic-features/)
- [Install Chaos Mesh using Helm](https://chaos-mesh.org/docs/production-installation-using-helm/)
- [Define the Scope of Chaos Experiments](https://chaos-mesh.org/docs/define-chaos-experiment-scope/)
- [Run a Chaos Experiment](https://chaos-mesh.org/docs/run-a-chaos-experiment/)
- [Inspect Results of Chaos Experiments](https://chaos-mesh.org/docs/inspect-chaos-experiments/)
- [Define Scheduling Rules](https://chaos-mesh.org/docs/define-scheduling-rules/)
- [Create Chaos Mesh Workflow](https://chaos-mesh.org/docs/create-chaos-mesh-workflow/)
- [Status Check in Workflow](https://chaos-mesh.org/docs/status-check-in-workflow/)
- [Manage User Permissions](https://chaos-mesh.org/docs/manage-user-permissions/)
- [Configure namespace for Chaos experiments](https://chaos-mesh.org/docs/configure-enabled-namespace/)
- [Simulate Pod Faults](https://chaos-mesh.org/docs/simulate-pod-chaos-on-kubernetes/)
- [Simulate Network Faults](https://chaos-mesh.org/docs/simulate-network-chaos-on-kubernetes/)
- [Simulate Stress Scenarios](https://chaos-mesh.org/docs/simulate-heavy-stress-on-kubernetes/)
- [Simulate File I/O Faults](https://chaos-mesh.org/docs/simulate-io-chaos-on-kubernetes/)
- [Chaos Mesh CNCF Project](https://www.cncf.io/projects/chaosmesh/)
- [Litmus CNCF Project](https://www.cncf.io/projects/litmus/)
- [LitmusChaos ChaosHub](https://docs.litmuschaos.io/docs/concepts/chaoshub)
- [LitmusChaos Chaos Experiment](https://docs.litmuschaos.io/docs/concepts/chaos-workflow)
- [Kubernetes Custom Resources](https://kubernetes.io/docs/concepts/extend-kubernetes/api-extension/custom-resources/)
- [Kubernetes RBAC Authorization](https://kubernetes.io/docs/reference/access-authn-authz/rbac/)
- [Principles of Chaos Engineering](https://principlesofchaos.org/)

## Next Module

Continue to [Module 1.3: Advanced Network & Application Fault Injection](../module-1.3-network-fault-injection/) — Deep dive into latency injection, DNS failures, HTTP-level chaos, clock skew, and JVM/kernel fault injection.
