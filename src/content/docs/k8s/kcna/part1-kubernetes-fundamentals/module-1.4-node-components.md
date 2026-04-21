---
title: "Module 1.4: Kubernetes Architecture - Node Components"
slug: k8s/kcna/part1-kubernetes-fundamentals/module-1.4-node-components
sidebar:
  order: 5
---
> **Complexity**: `[MEDIUM]` - Core architecture concepts
>
> **Time to Complete**: 20-25 minutes
>
> **Prerequisites**: Module 1.3

---

## What You'll Be Able to Do

After completing this module, you will be able to:

1. **Explain** the role of kubelet, kube-proxy, and the container runtime on each node
2. **Identify** which node component is responsible for a given networking or pod lifecycle behavior
3. **Compare** kube-proxy modes (iptables vs. IPVS) and their trade-offs
4. **Trace** how a pod gets scheduled and started on a worker node

---

## Why This Module Matters

While the control plane makes decisions, worker nodes do the actual work of running containers. Understanding node components completes your picture of Kubernetes architecture—a key KCNA topic.

---

## What is a Node?

A **node** is a worker machine in Kubernetes:

```
┌─────────────────────────────────────────────────────────────┐
│              WHAT IS A NODE?                                │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  A node can be:                                            │
│  • Physical server (bare metal)                            │
│  • Virtual machine (EC2, GCE VM, Azure VM)                │
│  • Cloud instance                                          │
│                                                             │
│  Every node runs:                                          │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  kubelet      - Node agent                          │   │
│  │  kube-proxy   - Network proxy                       │   │
│  │  Container runtime - Runs containers                │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  Nodes register themselves with the control plane          │
│  Control plane assigns Pods to nodes                       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Node Components

### 1. kubelet

The **kubelet** is the primary node agent:

```
┌─────────────────────────────────────────────────────────────┐
│              KUBELET                                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  What it does:                                             │
│  ─────────────────────────────────────────────────────────  │
│  • Runs on every node in the cluster                       │
│  • Watches for Pod assignments from API server             │
│  • Ensures containers are running and healthy              │
│  • Reports node and Pod status back to API server          │
│                                                             │
│  How it works:                                             │
│  ─────────────────────────────────────────────────────────  │
│                                                             │
│  API Server: "Node 2, run Pod X"                          │
│       │                                                     │
│       ▼                                                     │
│  kubelet:                                                  │
│  1. Receives Pod spec                                      │
│  2. Pulls container images                                 │
│  3. Creates containers via runtime                         │
│  4. Monitors container health                              │
│  5. Reports status to API server                          │
│                                                             │
│  Key point:                                                │
│  kubelet doesn't manage containers not created by K8s     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

> **Pause and predict**: The kubelet runs on every node and watches the API server for Pod assignments. But what if the API server goes down temporarily -- do existing Pods on the node stop running? Why or why not?

### 2. kube-proxy

The **kube-proxy** handles networking:

```
┌─────────────────────────────────────────────────────────────┐
│              KUBE-PROXY                                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  What it does:                                             │
│  ─────────────────────────────────────────────────────────  │
│  • Maintains network rules on nodes                        │
│  • Enables Service abstraction                             │
│  • Handles connection forwarding to Pods                   │
│                                                             │
│  How Services work:                                        │
│  ─────────────────────────────────────────────────────────  │
│                                                             │
│       Client                                               │
│          │                                                  │
│          │ Request to Service IP                           │
│          ▼                                                  │
│    ┌───────────┐                                           │
│    │kube-proxy │ → Looks up which Pods back this Service   │
│    └───────────┘                                           │
│          │                                                  │
│          │ Forwards to Pod IP                              │
│          ▼                                                  │
│    ┌───────────┐                                           │
│    │   Pod     │                                           │
│    └───────────┘                                           │
│                                                             │
│  Modes:                                                    │
│  • iptables (default) - Uses iptables rules               │
│  • IPVS - Higher performance for large clusters           │
│  • userspace - Legacy, rarely used                        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 3. Container Runtime

The **container runtime** actually runs containers:

```
┌─────────────────────────────────────────────────────────────┐
│              CONTAINER RUNTIME                              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  What it does:                                             │
│  ─────────────────────────────────────────────────────────  │
│  • Pulls images from registries                            │
│  • Creates and starts containers                           │
│  • Manages container lifecycle                             │
│                                                             │
│  Kubernetes uses CRI (Container Runtime Interface):        │
│  ─────────────────────────────────────────────────────────  │
│                                                             │
│       kubelet                                              │
│          │                                                  │
│          │ CRI (gRPC)                                      │
│          ▼                                                  │
│    ┌─────────────────────────────────────────────────┐     │
│    │  containerd  │  CRI-O  │  Other CRI runtime    │     │
│    └─────────────────────────────────────────────────┘     │
│          │                                                  │
│          │ OCI (Open Container Initiative)                 │
│          ▼                                                  │
│    ┌───────────────┐                                       │
│    │  runc / kata  │  (low-level runtime)                 │
│    └───────────────┘                                       │
│                                                             │
│  Common runtimes:                                          │
│  • containerd - Default in most distributions              │
│  • CRI-O - Lightweight, Kubernetes-focused                │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Node Lifecycle

```
┌─────────────────────────────────────────────────────────────┐
│              NODE LIFECYCLE                                 │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. Node Joins Cluster                                     │
│     • kubelet starts and registers with API server         │
│     • Node appears in "kubectl get nodes"                  │
│                                                             │
│  2. Node Ready                                             │
│     • Passes health checks                                 │
│     • Scheduler can place Pods on it                       │
│     Status: Ready                                          │
│                                                             │
│  3. Node Running                                           │
│     • Runs assigned Pods                                   │
│     • kubelet reports status periodically                  │
│                                                             │
│  4. Node Issues                                            │
│     • Misses heartbeats → Status: Unknown                 │
│     • Low resources → Status: NotReady                    │
│                                                             │
│  5. Node Removed                                           │
│     • Drained (Pods moved elsewhere)                      │
│     • Deleted from cluster                                 │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Node Conditions

| Condition | Meaning |
|-----------|---------|
| **Ready** | Node is healthy and can accept Pods |
| **DiskPressure** | Disk capacity is low |
| **MemoryPressure** | Memory is running low |
| **PIDPressure** | Too many processes |
| **NetworkUnavailable** | Network not configured |

---

## How Pods Get Scheduled and Run

```
┌─────────────────────────────────────────────────────────────┐
│              POD SCHEDULING AND EXECUTION                   │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. User creates Pod                                       │
│     kubectl apply -f pod.yaml                              │
│            │                                                │
│            ▼                                                │
│  2. API Server stores Pod                                  │
│     Pod stored in etcd (no node assigned yet)             │
│            │                                                │
│            ▼                                                │
│  3. Scheduler watches, sees unscheduled Pod               │
│     Evaluates nodes, picks best one                       │
│     Updates Pod with node assignment                       │
│            │                                                │
│            ▼                                                │
│  4. kubelet on target node sees assignment                │
│     "I need to run this Pod"                              │
│            │                                                │
│            ▼                                                │
│  5. kubelet instructs container runtime                   │
│     Pull image, create container, start it                │
│            │                                                │
│            ▼                                                │
│  6. Container runs                                         │
│     kubelet monitors health                               │
│     Reports status to API server                          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

> **Stop and think**: kube-proxy is described as a "network proxy," but it actually maintains iptables rules rather than proxying traffic directly. Why is this distinction important for understanding how Services work at scale?

## Node vs Control Plane Summary

```
┌─────────────────────────────────────────────────────────────┐
│              CONTROL PLANE vs NODE                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  CONTROL PLANE (Brain)          NODE (Muscle)              │
│  ──────────────────────────────────────────────────────    │
│                                                             │
│  Makes decisions                Executes decisions         │
│  Stores cluster state           Runs workloads             │
│  Schedules Pods                 Runs Pods                  │
│  Usually 3+ for HA             Many (10s to 1000s)        │
│                                                             │
│  Components:                    Components:                 │
│  • API Server                   • kubelet                  │
│  • etcd                         • kube-proxy               │
│  • Scheduler                    • Container runtime        │
│  • Controller Manager                                      │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Did You Know?

- **kubelet doesn't run as a container** - It's a system service that runs directly on the node OS. It needs to manage containers, so it can't be one.

- **kube-proxy is being replaced** - Newer CNI plugins (like Cilium) can handle Service routing without kube-proxy, using eBPF.

- **Nodes can have taints** - Taints prevent certain Pods from running on a node. Pods need matching tolerations to schedule there.

- **The pause container** - Every Pod has a hidden "pause" container that holds the network namespace. Other containers in the Pod share it.

---

## Common Mistakes

| Mistake | Why It Hurts | Correct Understanding |
|---------|--------------|----------------------|
| "kubelet is on control plane" | Confusing location | kubelet is on EVERY node, including workers |
| "kube-proxy is a proxy server" | Misleading name | It maintains iptables rules, not a traditional proxy |
| "Container runtime is Docker" | Outdated | containerd is now the default |
| "Nodes are always VMs" | Missing flexibility | Nodes can be bare metal, VMs, or cloud instances |

---

## Quiz

1. **A node in your cluster loses network connectivity to the control plane but the hardware is fine. What happens to the Pods running on that node, and what does the control plane do in response?**
   <details>
   <summary>Answer</summary>
   The Pods continue running on the node because kubelet manages them locally and does not need constant API server connectivity. However, the kubelet cannot send heartbeats, so the Node Controller marks the node's status as Unknown, then NotReady. After a timeout (default 5 minutes), the control plane considers the Pods on that node as potentially dead and may reschedule replacement Pods on healthy nodes. When the node's network recovers, kubelet reconnects and reports the actual state, and duplicate Pods are cleaned up.
   </details>

2. **Your team is choosing between containerd and CRI-O as the container runtime for a new cluster. A developer asks why Kubernetes does not just bundle its own runtime. What would you explain about the CRI architecture and its benefits?**
   <details>
   <summary>Answer</summary>
   Kubernetes uses the Container Runtime Interface (CRI), a standard API that decouples Kubernetes from any specific runtime. The kubelet communicates with the runtime through CRI via gRPC, meaning any CRI-compliant runtime can be swapped in. This pluggable design means Kubernetes does not need to maintain runtime code, runtimes can evolve independently, and organizations can choose the runtime that best fits their needs. containerd is the most popular default; CRI-O is optimized specifically for Kubernetes with a smaller footprint.
   </details>

3. **An engineer notices that a node shows DiskPressure: True in its conditions. What impact will this have on scheduling, and what might happen to existing Pods on that node?**
   <details>
   <summary>Answer</summary>
   When a node reports DiskPressure, the scheduler will avoid placing new Pods on it because the node does not have sufficient disk space. For existing Pods, kubelet may begin evicting Pods to free disk space, starting with those exceeding their ephemeral storage limits. The eviction order prioritizes Pods with the lowest priority class and those using the most resources above their requests. This is why setting appropriate resource requests and monitoring node conditions is important for cluster health.
   </details>

4. **kube-proxy runs on every node, but newer CNI plugins like Cilium can replace it entirely. Why would an organization choose to replace kube-proxy, and what technology enables this?**
   <details>
   <summary>Answer</summary>
   kube-proxy uses iptables (or IPVS) rules to handle Service routing, which can become a performance bottleneck in large clusters with thousands of Services because the number of rules grows linearly. Cilium replaces kube-proxy using eBPF (extended Berkeley Packet Filter), which programs the Linux kernel directly for networking decisions. This is more efficient because eBPF avoids the overhead of processing long iptables chains and provides better observability. Organizations with large clusters or high-performance networking requirements benefit most from this switch.
   </details>

5. **Walk through what happens on a worker node from the moment the scheduler assigns a Pod to it until the application is serving traffic. Which node components are involved at each step?**
   <details>
   <summary>Answer</summary>
   The sequence involves all three node components: (1) kubelet watches the API server and detects a new Pod assigned to its node, (2) kubelet instructs the container runtime (containerd) via CRI to pull the container image from the registry, (3) the container runtime creates and starts the container with the appropriate namespaces and cgroups, (4) kubelet monitors container health through configured probes (liveness, readiness), (5) once the readiness probe passes, kubelet reports the Pod as Ready to the API server, (6) kube-proxy updates its iptables/IPVS rules so that Service traffic can now reach the new Pod. Only after all these steps is the application actually serving traffic.
   </details>

---

## Summary

**Node components**:

| Component | Purpose |
|-----------|---------|
| **kubelet** | Node agent, manages Pods and containers |
| **kube-proxy** | Network rules for Service routing |
| **Container runtime** | Actually runs containers (containerd) |

**Key points**:
- Every node needs all three components
- kubelet is the only component talking to API server
- kube-proxy enables Service discovery
- Container runtime uses CRI to talk to kubelet

**Pod execution flow**:
1. API server stores Pod
2. Scheduler assigns node
3. kubelet sees assignment
4. Container runtime runs containers
5. kubelet monitors and reports

---

<!-- v4:generated type=no_exercise model=codex turn=1 -->
## Hands-On Exercise


Goal: inspect how `kubelet`, `kube-proxy`, and the container runtime work together on a node by tracing a Pod from scheduling to Service access.

- [ ] List the nodes in the cluster and choose one worker node to observe.
  ```bash
  kubectl get nodes -o wide
  kubectl describe node <node-name> | grep -E "Ready|Kubelet Version|Container Runtime Version"
  ```

- [ ] Confirm that the selected node is healthy and note its runtime and kubelet details.
  ```bash
  kubectl get node <node-name>
  kubectl describe node <node-name>
  ```

- [ ] Create a Pod that is pinned to that node so the workload definitely lands there.
  ```bash
  cat <<'EOF' | kubectl apply -f -
  apiVersion: v1
  kind: Pod
  metadata:
    name: node-demo
  spec:
    nodeName: <node-name>
    containers:
    - name: web
      image: nginx:stable
      ports:
      - containerPort: 80
  EOF
  ```

- [ ] Watch the Pod move from `Pending` to `Running` and identify evidence that the kubelet acted on the node assignment.
  ```bash
  kubectl get pod node-demo -w
  kubectl describe pod node-demo
  ```

- [ ] Check which component on the node actually runs the container by inspecting the reported container runtime.
  ```bash
  kubectl describe node <node-name> | grep "Container Runtime Version"
  kubectl get pod node-demo -o wide
  ```

- [ ] Create a ClusterIP Service so traffic can be routed to the Pod through Kubernetes networking.
  ```bash
  kubectl expose pod node-demo --name=node-demo-svc --port=80 --target-port=80
  kubectl get svc node-demo-svc
  kubectl get endpoints node-demo-svc
  ```

- [ ] Verify that the Service points to the Pod endpoint, showing the routing information kube-proxy uses on nodes.
  ```bash
  kubectl describe svc node-demo-svc
  kubectl get endpointslices -l kubernetes.io/service-name=node-demo-svc
  ```

- [ ] Launch a temporary test Pod and send traffic to the Service to confirm end-to-end connectivity.
  ```bash
  kubectl run curl-test --rm -it --image=curlimages/curl --restart=Never -- \
    curl -I http://node-demo-svc
  ```

- [ ] If node shell access is available, inspect the node-level agents directly.
  ```bash
  sudo systemctl status kubelet --no-pager
  sudo crictl ps
  sudo iptables -t nat -S | grep node-demo-svc
  ```

- [ ] Clean up the exercise resources.
  ```bash
  kubectl delete svc node-demo-svc
  kubectl delete pod node-demo
  ```

Verification commands:
```bash
kubectl get nodes
kubectl get pod node-demo -o wide
kubectl describe pod node-demo
kubectl get svc node-demo-svc
kubectl get endpoints node-demo-svc
kubectl get endpointslices -l kubernetes.io/service-name=node-demo-svc
```

Success criteria:
- The selected node shows `Ready` status.
- The node description shows both `Kubelet Version` and `Container Runtime Version`.
- The `node-demo` Pod schedules onto the intended node and reaches `Running`.
- The `node-demo-svc` Service has an endpoint that matches the Pod IP.
- A temporary client Pod successfully reaches the Service over HTTP.
- It is clear which task belongs to `kubelet`, `kube-proxy`, and the container runtime during the exercise.

<!-- /v4:generated -->
## Next Module

[Module 1.5: Pods](../module-1.5-pods/) - The fundamental building block of Kubernetes workloads.
