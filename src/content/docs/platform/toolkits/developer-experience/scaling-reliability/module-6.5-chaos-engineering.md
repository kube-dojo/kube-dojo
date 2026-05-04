---
revision_pending: true
title: "Module 6.5: Chaos Engineering"
slug: platform/toolkits/developer-experience/scaling-reliability/module-6.5-chaos-engineering
sidebar:
  order: 6
---
> **Toolkit Track** | Complexity: `[COMPLEX]` | Time: ~50 minutes

## Overview

Your monitoring says everything is fine. Your dashboards are green. Your runbooks are untested. Chaos engineering is the discipline of proactively breaking things in controlled ways so that you discover weaknesses before your customers do. This module covers the principles, two leading Kubernetes-native tools (LitmusChaos and Chaos Mesh), and how to run a GameDay that makes your systems genuinely stronger.

**What You'll Learn**:
- Core chaos engineering principles: steady state hypothesis, blast radius, minimize harm
- LitmusChaos installation, ChaosEngine/ChaosExperiment resources, and practical experiments
- Chaos Mesh installation, dashboard, and fault injection types
- How to plan and execute a GameDay safely
- Integrating chaos experiments with observability

**Prerequisites**:
- Kubernetes Deployments, Services, and basic networking
- [Systems Thinking: Complexity and Emergent Behavior](/platform/foundations/systems-thinking/module-1.4-complexity-and-emergent-behavior/)
- [SRE: Error Budgets](/platform/disciplines/core-platform/sre/module-1.3-error-budgets/)
- Familiarity with Helm and kubectl

---

## What You'll Be Able to Do

After completing this module, you will be able to:

- **Deploy Chaos Mesh or Litmus for controlled chaos experiments on Kubernetes workloads**
- **Configure chaos experiments targeting pod failures, network partitions, and resource stress scenarios**
- **Implement steady-state hypothesis validation to measure system resilience during chaos injection**
- **Evaluate chaos engineering frameworks and design progressive chaos maturity programs for teams**


## Why This Module Matters

Netflix pioneered chaos engineering in 2011 by building <!-- incident-xref: netflix-chaos-monkey -->Chaos Monkey — a tool that randomly terminated production instances daily during business hours, forcing every engineering team to build systems that survived instance death. For the full case study, see [Chaos Principles](../../../disciplines/reliability-security/chaos-engineering/module-1.1-chaos-principles/).

The lesson is uncomfortable but clear: the only way to know your system handles failure is to cause failure, deliberately, while you are watching.

---

> **Did You Know?**
>
> 1. Netflix's original <!-- incident-xref: netflix-chaos-monkey -->Chaos Monkey was written in Go and ran exclusively during business hours so that engineers were awake to respond. The team called this "finding weaknesses while the doctors are in the office."
> 2. The CNCF accepted LitmusChaos as an incubating project in 2022, making it the first chaos engineering project in the CNCF landscape to reach that maturity level.
> 3. Chaos Mesh was originally developed by PingCAP (the company behind TiDB) to test distributed database resilience. It injects faults at the kernel level using eBPF and ptrace, giving it precision that application-level tools cannot match.
> 4. According to a 2023 Gremlin State of Chaos Engineering report, 60% of organizations practicing chaos engineering discovered critical bugs that traditional testing missed -- and the median time to detect failures dropped by 40%.

---

## Chaos Engineering Principles

Chaos engineering is not "breaking things for fun." It is a scientific method applied to distributed systems.

### The Three Pillars

```
CHAOS ENGINEERING METHOD
================================================================

1. STEADY STATE HYPOTHESIS
   "Under normal conditions, our checkout service
    handles 500 req/s with p99 latency < 200ms."

   You MUST define what "normal" looks like BEFORE
   you inject any fault. Without this, you are just
   breaking things randomly.

2. BLAST RADIUS
   "We will kill 1 pod out of 5 replicas in staging."

   Start small. Contain the experiment. Never begin
   with "let's take down the production database."
   Increase scope only after you build confidence.

3. MINIMIZE HARM
   "If p99 latency exceeds 500ms, we abort immediately."

   Define rollback criteria before you start.
   Have a kill switch. Chaos experiments must be
   REVERSIBLE. If you cannot undo the fault, do not
   inject it.

================================================================
```

### How It Connects to Error Budgets

Chaos experiments consume error budget. If your SLO allows 99.9% availability (43 minutes of downtime per month), and a chaos experiment causes 2 minutes of degradation, that comes out of your budget. This is why chaos engineering and [error budgets](/platform/disciplines/core-platform/sre/module-1.3-error-budgets/) work hand-in-hand: you spend a small portion of your budget proactively to avoid spending all of it reactively during a real incident.

### Emergent Behavior

Distributed systems exhibit [emergent behavior](/platform/foundations/systems-thinking/module-1.4-complexity-and-emergent-behavior/) -- failures that no single component causes but that arise from interactions between components. A pod restart might trigger a cache stampede, which overwhelms the database, which causes timeouts in an unrelated service. Chaos engineering is the only reliable way to surface these emergent failure modes before production traffic does.

---

## LitmusChaos

LitmusChaos is a CNCF incubating project that provides a Kubernetes-native chaos engineering framework. It uses Custom Resources to define, run, and observe experiments.

### Installation

```bash
# Add the LitmusChaos Helm repository
helm repo add litmuschaos https://litmuschaos.github.io/litmus-helm/
helm repo update

# Install LitmusChaos in a dedicated namespace
helm install litmus litmuschaos/litmus \
  --namespace litmus \
  --create-namespace \
  --set portal.frontend.service.type=NodePort \
  --version 3.9.0 \
  --wait

# Verify pods are running
kubectl get pods -n litmus

# Install the generic experiment charts (pod-level chaos)
kubectl apply -f https://hub.litmuschaos.io/api/chaos/3.9.0?file=charts/generic/experiments.yaml \
  -n litmus
```

### Key Resources

| Resource | Purpose |
|----------|---------|
| **ChaosExperiment** | Defines a fault type (pod-delete, network-loss, etc.) |
| **ChaosEngine** | Binds an experiment to a target application and triggers it |
| **ChaosResult** | Stores the outcome (Pass/Fail) and observations |

### Experiment: Pod Delete

This experiment kills pods to validate that your application recovers through Kubernetes self-healing.

```yaml
apiVersion: litmuschaos.io/v1alpha1
kind: ChaosEngine
metadata:
  name: nginx-pod-delete
  namespace: default
spec:
  appinfo:
    appns: default
    applabel: app=nginx
    appkind: deployment
  engineState: active
  chaosServiceAccount: litmus-admin
  experiments:
    - name: pod-delete
      spec:
        components:
          env:
            - name: TOTAL_CHAOS_DURATION
              value: "30"       # Run for 30 seconds
            - name: CHAOS_INTERVAL
              value: "10"       # Kill a pod every 10 seconds
            - name: FORCE
              value: "false"    # Graceful termination
```

### Experiment: Pod CPU Hog

Simulate CPU pressure to test autoscaling and graceful degradation.

```yaml
apiVersion: litmuschaos.io/v1alpha1
kind: ChaosEngine
metadata:
  name: nginx-cpu-hog
  namespace: default
spec:
  appinfo:
    appns: default
    applabel: app=nginx
    appkind: deployment
  engineState: active
  chaosServiceAccount: litmus-admin
  experiments:
    - name: pod-cpu-hog
      spec:
        components:
          env:
            - name: CPU_CORES
              value: "1"
            - name: TOTAL_CHAOS_DURATION
              value: "60"
            - name: CPU_LOAD
              value: "80"       # 80% CPU utilization
```

### Experiment: Pod Network Loss

Simulate network partition to test timeout handling and circuit breakers.

```yaml
apiVersion: litmuschaos.io/v1alpha1
kind: ChaosEngine
metadata:
  name: nginx-network-loss
  namespace: default
spec:
  appinfo:
    appns: default
    applabel: app=nginx
    appkind: deployment
  engineState: active
  chaosServiceAccount: litmus-admin
  experiments:
    - name: pod-network-loss
      spec:
        components:
          env:
            - name: NETWORK_INTERFACE
              value: "eth0"
            - name: NETWORK_PACKET_LOSS_PERCENTAGE
              value: "100"      # Total packet loss
            - name: TOTAL_CHAOS_DURATION
              value: "30"
```

### Analyzing ChaosResults

```bash
# Check experiment status
kubectl get chaosresults -n default

# Detailed result
kubectl describe chaosresult nginx-pod-delete-pod-delete -n default

# Key fields to check:
# spec.experimentStatus.verdict  → Pass / Fail / Awaited
# spec.experimentStatus.phase    → Completed / Running / Aborted
# spec.experimentStatus.probeSuccessPercentage → "100" means all probes passed
```

A **Pass** verdict means your application survived the fault within the defined steady state criteria. A **Fail** means the chaos exposed a real weakness -- which is exactly what you wanted to find.

---

## Chaos Mesh

Chaos Mesh is a CNCF incubating project originally built by PingCAP. It operates at a lower level than LitmusChaos, using sidecar injection and kernel-level techniques to inject precise faults.

### Installation

```bash
# Add Chaos Mesh Helm repository
helm repo add chaos-mesh https://charts.chaos-mesh.org
helm repo update

# Install Chaos Mesh
helm install chaos-mesh chaos-mesh/chaos-mesh \
  --namespace chaos-mesh \
  --create-namespace \
  --set chaosDaemon.runtime=containerd \
  --set chaosDaemon.socketPath=/run/containerd/containerd.sock \
  --version 2.7.0 \
  --wait

# Verify installation
kubectl get pods -n chaos-mesh
```

### Dashboard

Chaos Mesh includes a built-in web dashboard for creating, scheduling, and monitoring experiments visually.

```bash
# Access the dashboard
kubectl port-forward -n chaos-mesh svc/chaos-dashboard 2333:2333

# Open http://localhost:2333 in your browser
# Create a token for authentication:
kubectl create token account-chaos-mesh-manager -n chaos-mesh
```

### PodChaos: Kill Pods

```yaml
apiVersion: chaos-mesh.org/v1alpha1
kind: PodChaos
metadata:
  name: pod-failure-example
  namespace: default
spec:
  action: pod-kill
  mode: one                    # Kill one matching pod
  selector:
    namespaces:
      - default
    labelSelectors:
      app: nginx
  duration: "30s"
  scheduler:
    cron: "@every 2m"          # Repeat every 2 minutes (optional)
```

### NetworkChaos: Simulate Network Failures

```yaml
apiVersion: chaos-mesh.org/v1alpha1
kind: NetworkChaos
metadata:
  name: network-delay-example
  namespace: default
spec:
  action: delay
  mode: all
  selector:
    namespaces:
      - default
    labelSelectors:
      app: frontend
  delay:
    latency: "200ms"
    jitter: "50ms"
    correlation: "25"
  direction: to
  target:
    selector:
      namespaces:
        - default
      labelSelectors:
        app: backend
  duration: "60s"
```

### StressChaos: CPU and Memory Pressure

```yaml
apiVersion: chaos-mesh.org/v1alpha1
kind: StressChaos
metadata:
  name: memory-stress-example
  namespace: default
spec:
  mode: one
  selector:
    namespaces:
      - default
    labelSelectors:
      app: nginx
  stressors:
    memory:
      workers: 2
      size: "256MB"
    cpu:
      workers: 1
      load: 50
  duration: "60s"
```

### IOChaos: Disk Fault Injection

```yaml
apiVersion: chaos-mesh.org/v1alpha1
kind: IOChaos
metadata:
  name: io-latency-example
  namespace: default
spec:
  action: latency
  mode: one
  selector:
    namespaces:
      - default
    labelSelectors:
      app: database
  volumePath: /data
  path: "*"
  delay: "100ms"
  percent: 50                  # 50% of I/O operations affected
  duration: "60s"
```

---

## GameDay Planning Guide

A GameDay is a structured chaos engineering session where a team deliberately injects failures and observes results together. Think of it as a fire drill for your infrastructure.

### GameDay Checklist

```
GAMEDAY PLANNING TEMPLATE
================================================================

1. HYPOTHESIS
   "When we kill 2 of 3 API pods, the remaining pod will
    handle all traffic with < 500ms p99 latency, and
    Kubernetes will restore the killed pods within 30s."

2. BLAST RADIUS
   - Environment: staging (graduate to production later)
   - Target: api-gateway deployment, 2 of 3 pods
   - Affected users: none (staging)
   - Duration: 2 minutes max

3. ROLLBACK PLAN
   - Abort trigger: p99 > 1s OR error rate > 5%
   - Rollback command: kubectl delete chaosengine <name>
   - Escalation: page on-call if rollback fails

4. COMMUNICATION
   - Notify: #platform-eng Slack channel
   - Participants: SRE team + API team lead
   - War room: Zoom link for real-time coordination
   - Status page: no customer-facing update (staging)

5. OBSERVABILITY
   - Grafana dashboard: open before experiment starts
   - Key metrics: request rate, error rate, p99 latency
   - Logs: tail API pod logs in separate terminal
   - Alerts: temporarily acknowledge (do not silence)

6. POST-EXPERIMENT
   - Document: what happened vs. hypothesis
   - Action items: file tickets for any weaknesses found
   - Share: post results in #engineering
================================================================
```

### Graduating to Production

Only run chaos in production when all of these are true:

1. The same experiment passed in staging at least twice
2. You have automated rollback (not just manual kubectl)
3. On-call is aware and standing by
4. It is during business hours with full staffing
5. You are NOT in a change freeze or near a major release

---

## Running Chaos Safely

### Start Small, Then Expand

```
CHAOS MATURITY LEVELS
================================================================

Level 0: "We don't do chaos"
  → You discover failures from customers

Level 1: Manual experiments in dev/staging
  → Kill a pod, watch what happens

Level 2: Automated experiments in staging
  → Scheduled ChaosEngine runs in CI/CD

Level 3: Automated experiments in production
  → Controlled blast radius, business hours only

Level 4: Continuous chaos in production
  → Netflix-style: always running, fully automated
  → Requires mature observability and fast rollback

Most teams should aim for Level 2-3.
================================================================
```

### Production Readiness Checklist

Before injecting any fault in production:

- [ ] Steady state hypothesis is written down
- [ ] Blast radius is limited (one pod, one service, one AZ)
- [ ] Abort criteria are defined with specific thresholds
- [ ] Rollback is tested and takes less than 30 seconds
- [ ] Observability dashboards are open and showing real-time data
- [ ] On-call is aware and available
- [ ] The experiment has passed in staging first
- [ ] There is no ongoing incident or maintenance window

---

## Integration with Observability

Chaos without observability is just vandalism. You must be watching your system while you break it.

### What to Monitor During Chaos

```bash
# Before starting: open Grafana dashboards for the target service
# Key panels to watch:

# 1. Request rate (did traffic shift when pods died?)
# 2. Error rate (are clients seeing 5xx errors?)
# 3. Latency p50/p95/p99 (is the surviving pod overloaded?)
# 4. Pod count (is Kubernetes replacing killed pods?)
# 5. CPU/memory usage (are remaining pods hitting limits?)
```

### Prometheus Queries for Chaos Experiments

```promql
# Error rate during chaos window
sum(rate(http_requests_total{status=~"5.."}[1m]))
/ sum(rate(http_requests_total[1m])) * 100

# p99 latency spike detection
histogram_quantile(0.99, rate(http_request_duration_seconds_bucket[1m]))

# Pod restart count (should increase during pod-kill experiments)
sum(increase(kube_pod_container_status_restarts_total{namespace="default"}[5m]))
```

If your Grafana dashboard shows a spike in errors that does NOT recover within your defined threshold, the experiment has revealed a real problem. File a ticket, fix it, and re-run the experiment.

---

## Tool Comparison

| Feature | LitmusChaos | Chaos Mesh | Gremlin |
|---------|------------|------------|---------|
| **License** | Apache 2.0 | Apache 2.0 | Commercial |
| **CNCF Status** | Incubating | Incubating | N/A |
| **Installation** | Helm / Operator | Helm / Operator | Agent-based |
| **UI Dashboard** | Yes (ChaosCenter) | Yes (built-in) | Yes (SaaS) |
| **Pod-level chaos** | Yes | Yes | Yes |
| **Network chaos** | Yes | Yes (eBPF) | Yes |
| **I/O chaos** | Limited | Yes (kernel-level) | Yes |
| **Stress testing** | Yes | Yes | Yes |
| **Scheduling** | Via ChaosEngine | Via cron in spec | Via UI/API |
| **RBAC** | Kubernetes native | Kubernetes native | Proprietary |
| **Kernel-level faults** | No | Yes (ptrace/eBPF) | Agent-level |
| **Best for** | GitOps workflows, CI/CD integration | Low-level fault injection, DB testing | Teams wanting managed experience |
| **Learning curve** | Moderate | Moderate | Low |

**Recommendation**: Start with LitmusChaos if you want tight Kubernetes-native integration and GitOps workflows. Choose Chaos Mesh if you need kernel-level fault injection (I/O faults, precise network manipulation). Consider Gremlin if your organization prefers commercial support and a polished SaaS UI.

---

## Common Mistakes

| Mistake | Problem | Solution |
|---------|---------|----------|
| No steady state hypothesis | You cannot tell if the experiment passed or failed | Always define expected behavior before injecting faults |
| Starting in production | Uncontrolled blast radius, real customer impact | Start in dev, graduate to staging, then production |
| No rollback plan | Experiment causes outage you cannot stop | Pre-test rollback; `kubectl delete` the ChaosEngine/ChaosExperiment |
| Silencing alerts during chaos | You miss real incidents masked by the experiment | Acknowledge alerts, do not silence them |
| Running chaos without observability | You break things but learn nothing | Open dashboards first, watch metrics during the experiment |
| Too large blast radius | Taking down entire namespace or cluster | Target one pod, one service, one fault type at a time |
| Never increasing scope | Staying in staging forever, false confidence | Graduate to production once staging experiments are stable |
| Running during incidents | Compounding an existing problem | Check incident channels before starting any GameDay |

---

## Quiz

### Question 1
What is a steady state hypothesis and why is it required before any chaos experiment?

<details>
<summary>Show Answer</summary>

A steady state hypothesis defines the normal, expected behavior of your system in measurable terms -- for example, "the API responds to 99.9% of requests within 200ms with zero 5xx errors." It is required because without it, you have no way to determine whether the system survived the fault. The experiment compares behavior during chaos against this baseline. If metrics stay within the hypothesis bounds, the system is resilient. If they breach the bounds, you have found a weakness.

</details>

### Question 2
What is the difference between a ChaosExperiment and a ChaosEngine in LitmusChaos?

<details>
<summary>Show Answer</summary>

A **ChaosExperiment** is a Custom Resource that defines the type of fault (pod-delete, cpu-hog, network-loss, etc.) along with its default parameters. Think of it as a template.

A **ChaosEngine** is a Custom Resource that binds a ChaosExperiment to a specific target application. It specifies which namespace, which label selector, which deployment to attack, and any parameter overrides. The ChaosEngine is what you apply to actually run the experiment.

The separation lets you reuse the same experiment definition across different applications.

</details>

### Question 3
You are running a chaos experiment in production and the error rate exceeds your abort threshold. What should you do?

<details>
<summary>Show Answer</summary>

Immediately execute the rollback plan:

1. **Delete the ChaosEngine** (LitmusChaos) or the chaos resource (Chaos Mesh) to stop fault injection
2. **Verify recovery** -- watch metrics return to steady state
3. **Check for cascading effects** -- ensure the fault did not trigger secondary failures
4. **Do NOT re-run the experiment** until the root cause is understood
5. **Document the finding** -- this is a success, not a failure. The experiment found a real weakness.
6. **File a ticket** to fix the underlying resilience gap
7. **Re-run after the fix** to confirm the weakness is resolved

The worst response is to panic and start restarting everything. Let Kubernetes self-heal, and focus on observing.

</details>

### Question 4
When should you choose Chaos Mesh over LitmusChaos?

<details>
<summary>Show Answer</summary>

Choose Chaos Mesh when you need:

- **I/O fault injection** (disk latency, read/write errors) -- Chaos Mesh uses kernel-level ptrace for precise I/O manipulation that LitmusChaos cannot match
- **Fine-grained network control** -- Chaos Mesh uses eBPF for network faults, giving per-connection control
- **Database or storage testing** -- Chaos Mesh was built by PingCAP specifically for testing distributed databases under fault conditions
- **Kernel-level precision** -- when application-level chaos is not sufficient

Choose LitmusChaos when you want GitOps-native workflows, ChaosHub experiment libraries, or tighter integration with CI/CD pipelines.

Both are CNCF incubating projects and production-ready. The choice depends on what fault types matter most for your system.

</details>

---

## Hands-On Exercise

### Objective

Deploy a sample application, inject a pod failure using Chaos Mesh, observe the recovery through Kubernetes self-healing, and validate your steady state hypothesis.

### Environment Setup

```bash
# Create a kind cluster (if you don't have one)
kind create cluster --name chaos-lab

# Install Chaos Mesh
helm repo add chaos-mesh https://charts.chaos-mesh.org
helm repo update
helm install chaos-mesh chaos-mesh/chaos-mesh \
  --namespace chaos-mesh \
  --create-namespace \
  --set chaosDaemon.runtime=containerd \
  --set chaosDaemon.socketPath=/run/containerd/containerd.sock \
  --version 2.7.0 \
  --wait

# Deploy a target application (3 replicas)
kubectl create deployment web --image=nginx:1.27 --replicas=3
kubectl expose deployment web --port=80 --target-port=80

# Verify all pods are running
kubectl get pods -l app=web
```

### Tasks

**Step 1: Define your steady state hypothesis.**

Write it down before proceeding: "The web deployment maintains 3 running pods. When 1 pod is killed, Kubernetes replaces it within 30 seconds, and the service remains reachable throughout."

**Step 2: Watch pods in a separate terminal.**

```bash
kubectl get pods -l app=web -w
```

**Step 3: Apply the chaos experiment.**

```yaml
# Save as pod-kill-experiment.yaml
apiVersion: chaos-mesh.org/v1alpha1
kind: PodChaos
metadata:
  name: web-pod-kill
  namespace: default
spec:
  action: pod-kill
  mode: one
  selector:
    namespaces:
      - default
    labelSelectors:
      app: web
  duration: "30s"
```

```bash
kubectl apply -f pod-kill-experiment.yaml
```

**Step 4: Observe and record.**

```bash
# Watch the pod list -- you should see one pod terminate and a new one start
kubectl get pods -l app=web

# Check the chaos experiment status
kubectl get podchaos web-pod-kill -o yaml

# Test service reachability during the experiment
kubectl run curl-test --image=curlimages/curl --rm -it --restart=Never -- \
  curl -s -o /dev/null -w "%{http_code}" http://web.default.svc.cluster.local
```

**Step 5: Validate hypothesis.**

```bash
# After 30s, confirm all 3 pods are running again
kubectl get pods -l app=web

# Clean up the experiment
kubectl delete podchaos web-pod-kill
```

### Success Criteria

- [ ] Chaos Mesh is installed and all pods are running in chaos-mesh namespace
- [ ] Target application has 3 healthy pods before the experiment
- [ ] PodChaos experiment kills exactly 1 pod
- [ ] Kubernetes replaces the killed pod within 30 seconds
- [ ] The service remained reachable during the experiment
- [ ] You can articulate what you would do differently if the hypothesis failed

### Bonus Challenge

Create a NetworkChaos experiment that adds 500ms latency between the web pods and a backend service. Observe how the added latency affects response times and determine at what latency threshold your application becomes unusable.

---

## Further Reading

- [Principles of Chaos Engineering](https://principlesofchaos.org/)
- [LitmusChaos Documentation](https://docs.litmuschaos.io/)
- [Chaos Mesh Documentation](https://chaos-mesh.org/docs/)
- [Netflix Chaos Engineering](https://netflixtechblog.com/tagged/chaos-engineering)

---

## Next Module

Continue to [Module 5.2: Service Mesh](/platform/toolkits/infrastructure-networking/networking/module-5.2-service-mesh/) to learn how Istio and Linkerd add observability, security, and traffic management to your microservices.

---

*"The question is not whether your system will fail. It is whether you will discover how it fails on your terms or your customers' terms."*
