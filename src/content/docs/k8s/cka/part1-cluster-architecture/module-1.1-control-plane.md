---
title: "Module 1.1: Control Plane Deep-Dive"
slug: k8s/cka/part1-cluster-architecture/module-1.1-control-plane
sidebar:
  order: 2
---
> **Complexity**: `[MEDIUM]` - Conceptual understanding required
>
> **Time to Complete**: 35-45 minutes
>
> **Prerequisites**: Module 0.1 (working cluster)

---

## Why This Module Matters

Every `kubectl` command you run talks to the control plane. Every pod that schedules, every service that routes traffic, every secret that stores credentials—it all happens because control plane components are working together.

When troubleshooting fails, when pods won't schedule, when your cluster "just stops working"—you need to understand what's actually running your cluster. The CKA exam tests this. Real-world incidents demand it.

This module takes you inside the machine.

> **The Air Traffic Control Analogy**
>
> Think of Kubernetes as an airport. The control plane is air traffic control—it doesn't fly planes, but nothing flies without it. The API server is the control tower (single point of communication). The scheduler decides which runway (node) each plane (pod) uses. The controller manager monitors everything and calls for help when planes deviate from flight plans. etcd is the flight log—every decision recorded, every state tracked. Workers (nodes) are the runways where actual planes land.

---

## What You'll Learn

By the end of this module, you'll understand:
- What each control plane component does (and doesn't do)
- How they communicate with each other
- What happens when each component fails
- How to check component health
- Where component logs live

---

## Part 1: The Control Plane Overview

### 1.1 Architecture at a Glance

```
┌─────────────────────────────────────────────────────────────────────┐
│                         CONTROL PLANE                                │
│  ┌─────────────┐  ┌─────────────┐  ┌──────────────────────────────┐ │
│  │ API Server  │  │   etcd      │  │    Controller Manager        │ │
│  │ (kube-api)  │◄─┤  (storage)  │  │  ┌────────────────────────┐  │ │
│  │             │  │             │  │  │ Deployment Controller  │  │ │
│  └──────┬──────┘  └─────────────┘  │  │ ReplicaSet Controller  │  │ │
│         │                          │  │ Node Controller        │  │ │
│         │ ┌─────────────────────┐  │  │ Job Controller         │  │ │
│         │ │     Scheduler       │  │  │ ... (40+ controllers)  │  │ │
│         │ │  (kube-scheduler)   │  │  └────────────────────────┘  │ │
│         │ └─────────────────────┘  └──────────────────────────────┘ │
└─────────┼───────────────────────────────────────────────────────────┘
          │
          │ kubelet talks to API server
          ▼
┌─────────────────────────────────────────────────────────────────────┐
│                           WORKER NODES                               │
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │ Node 1                      Node 2                      Node 3  ││
│  │ ┌─────────┐ ┌──────────┐   ┌─────────┐ ┌──────────┐            ││
│  │ │ kubelet │ │kube-proxy│   │ kubelet │ │kube-proxy│   ...      ││
│  │ └─────────┘ └──────────┘   └─────────┘ └──────────┘            ││
│  │ ┌──────────────────────┐   ┌──────────────────────┐            ││
│  │ │ Container Runtime    │   │ Container Runtime    │            ││
│  │ │ (containerd)         │   │ (containerd)         │            ││
│  │ └──────────────────────┘   └──────────────────────┘            ││
│  └─────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────┘
```

### 1.2 Control Plane vs. Worker Nodes

| Component | Runs On | Purpose |
|-----------|---------|---------|
| kube-apiserver | Control plane | API gateway, all communication |
| etcd | Control plane | Cluster state storage |
| kube-scheduler | Control plane | Pod placement decisions |
| kube-controller-manager | Control plane | Reconciliation loops |
| kubelet | Every node | Container lifecycle |
| kube-proxy | Every node | Network rules |
| Container runtime | Every node | Actually runs containers |

> **Did You Know?**
>
> In production, etcd often runs on dedicated machines separate from other control plane components. A three-node etcd cluster can handle thousands of Kubernetes nodes. Google's Borg (Kubernetes' predecessor) inspired this separation.

---

## Part 2: kube-apiserver - The Front Door

### 2.1 What It Does

The API server is the **only** component that talks directly to etcd. Everything else talks to the API server.

```
┌─────────────────────────────────────────────────────────────────┐
│                    All Roads Lead to API Server                  │
│                                                                  │
│   kubectl ────────┐                                              │
│   Scheduler ──────┼────► kube-apiserver ◄───► etcd              │
│   Controllers ────┤                                              │
│   kubelet ────────┤                                              │
│   Dashboard ──────┘                                              │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

**Key responsibilities**:
- Authenticate requests (who are you?)
- Authorize requests (can you do this?)
- Validate requests (is this valid YAML/JSON?)
- Persist to etcd (store the desired state)
- Serve as the cluster's REST API

### 2.2 API Request Flow

When you run `kubectl create -f pod.yaml`:

```
1. kubectl → API Server: "Create this pod please"
2. API Server: Authentication check ✓
3. API Server: Authorization check ✓
4. API Server: Admission controllers run
5. API Server: Validation check ✓
6. API Server → etcd: "Store this pod spec"
7. API Server → kubectl: "Pod created (pending)"
```

The pod doesn't exist yet as a running container—it's just stored in etcd. The scheduler and kubelet take it from there.

### 2.3 Checking API Server Health

```bash
# Is the API server responding?
kubectl cluster-info

# Check API server component status (legacy)
kubectl get componentstatuses  # Deprecated, may not work on all clusters

# Modern health endpoints (preferred)
kubectl get --raw='/readyz?verbose'
kubectl get --raw='/livez?verbose'

# Direct health endpoint
kubectl get --raw='/healthz'

# Detailed health
kubectl get --raw='/healthz?verbose'
```

### 2.4 API Server Logs

```bash
# If running as a static pod (kubeadm setup)
kubectl logs -n kube-system kube-apiserver-<control-plane-node>

# If running as systemd service
journalctl -u kube-apiserver

# Static pod manifest location
cat /etc/kubernetes/manifests/kube-apiserver.yaml
```

> **Gotcha: API Server Unavailable**
>
> If the API server is down, `kubectl` won't work at all. You'll need to SSH into the control plane node and check logs directly with `crictl` or `journalctl`. This is a common CKA troubleshooting scenario.

---

## Part 3: etcd - The Source of Truth

### 3.1 What It Does

etcd is a distributed key-value store. It holds **all** cluster state:
- All resource definitions (pods, services, secrets, etc.)
- Cluster configuration
- Current state of everything

If etcd loses data, your cluster loses its memory.

### 3.2 How Kubernetes Uses etcd

```
Key format: /registry/<resource-type>/<namespace>/<name>

Examples:
/registry/pods/default/nginx
/registry/services/kube-system/kube-dns
/registry/secrets/default/my-secret
/registry/deployments/production/web-app
```

### 3.3 etcd Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    etcd Cluster (Raft Consensus)                 │
│                                                                  │
│   ┌──────────┐      ┌──────────┐      ┌──────────┐              │
│   │  etcd-1  │◄────►│  etcd-2  │◄────►│  etcd-3  │              │
│   │ (Leader) │      │(Follower)│      │(Follower)│              │
│   └──────────┘      └──────────┘      └──────────┘              │
│                                                                  │
│   Writes go to leader, replicated to followers                   │
│   Reads can go to any node                                       │
│   Survives loss of 1 node (quorum = 2/3)                        │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 3.4 Checking etcd Health

```bash
# etcd member list (if you have etcdctl configured)
ETCDCTL_API=3 etcdctl member list \
  --endpoints=https://127.0.0.1:2379 \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key

# Check etcd pod
kubectl get pods -n kube-system | grep etcd
kubectl logs -n kube-system etcd-<control-plane-node>
```

> **Did You Know?**
>
> etcd uses the Raft consensus algorithm. It requires a majority (quorum) to operate. A 3-node cluster tolerates 1 failure. A 5-node cluster tolerates 2 failures. This is why production clusters use odd numbers of etcd nodes.

> **War Story: The etcd Disk Full Incident**
>
> A team ran a cluster for months without monitoring etcd disk usage. etcd keeps a history of all changes (for watch operations). One day, etcd's disk filled up. The entire cluster became read-only—no new pods, no updates, no deletes. The fix? Emergency disk cleanup and enabling etcd auto-compaction. They lost 4 hours of productivity because they didn't monitor a 10GB disk.

---

## Part 4: kube-scheduler - The Matchmaker

### 4.1 What It Does

The scheduler watches for pods with no assigned node and finds the best node for them.

```
┌────────────────────────────────────────────────────────────────┐
│                      Scheduling Process                         │
│                                                                 │
│  1. New pod created (no nodeName) ─────────────────────┐       │
│                                                         │       │
│  2. Scheduler watches API server                        ▼       │
│     "Any pods need scheduling?"  ◄────────────────── Pod Queue │
│                                                                 │
│  3. Filtering: Which nodes CAN run this pod?                   │
│     - Enough CPU/memory?                                        │
│     - Taints/tolerations match?                                 │
│     - Node selectors match?                                     │
│     - Affinity rules satisfied?                                 │
│                                                                 │
│  4. Scoring: Which node is BEST?                               │
│     - Resource balance                                          │
│     - Spreading across zones                                    │
│     - Custom priorities                                         │
│                                                                 │
│  5. Binding: Assign pod to winning node                        │
│     Scheduler → API Server: "pod X goes to node Y"             │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
```

### 4.2 Filtering vs. Scoring

**Filtering** (hard constraints): "Can this node run the pod at all?"
- Does it have enough resources?
- Does it match nodeSelector?
- Does it tolerate the node's taints?
- Does it satisfy affinity requirements?

**Scoring** (soft constraints): "Which eligible node is best?"
- Balance resource utilization
- Spread pods across failure domains
- Prefer nodes with image already pulled
- Custom scoring plugins

### 4.3 When Scheduling Fails

```bash
# Pod stuck in Pending
kubectl describe pod <pod-name>

# Look for Events section:
# "0/3 nodes are available: 1 node(s) had taint {node-role.kubernetes.io/control-plane: },
#  2 node(s) didn't match Pod's node affinity/selector"
```

Common reasons:
- **Insufficient resources**: No node has enough CPU/memory
- **Taints not tolerated**: Node has taints, pod lacks tolerations
- **Affinity not satisfied**: Pod requires specific node labels
- **PVC not bound**: Pod needs storage that doesn't exist

### 4.4 Checking Scheduler Health

```bash
# Scheduler pod
kubectl get pods -n kube-system | grep scheduler
kubectl logs -n kube-system kube-scheduler-<control-plane-node>

# Scheduler leader election (in HA setups)
kubectl get endpoints kube-scheduler -n kube-system -o yaml
```

---

## Part 5: kube-controller-manager - The Reconciler

### 5.1 What It Does

The controller manager runs **controllers**—reconciliation loops that watch the current state and work toward the desired state.

```
┌────────────────────────────────────────────────────────────────┐
│                    Controller Loop Pattern                      │
│                                                                 │
│                    ┌─────────────────┐                         │
│                    │  Desired State  │                         │
│                    │  (in etcd)      │                         │
│                    └────────┬────────┘                         │
│                             │                                   │
│                    Compare  │                                   │
│                             ▼                                   │
│            Is current state = desired state?                    │
│                             │                                   │
│              ┌──────────────┴──────────────┐                   │
│              │ YES                    NO   │                   │
│              ▼                             ▼                   │
│         Do nothing                  Take action                │
│         (wait & watch)              (create/delete/update)     │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
```

### 5.2 Built-in Controllers

There are 40+ controllers. Key ones:

| Controller | Watches | Does |
|------------|---------|------|
| **Deployment** | Deployments | Creates/updates ReplicaSets |
| **ReplicaSet** | ReplicaSets | Ensures correct pod count |
| **Node** | Nodes | Monitors node health, evicts pods from dead nodes |
| **Job** | Jobs | Creates pods, tracks completion |
| **Endpoint** | Services, Pods | Updates Service endpoints |
| **ServiceAccount** | Namespaces | Creates default ServiceAccount |
| **Namespace** | Namespaces | Cleans up resources when namespace deleted |

### 5.3 Example: ReplicaSet Controller

```yaml
# You create this:
apiVersion: apps/v1
kind: ReplicaSet
metadata:
  name: web
spec:
  replicas: 3
  selector:
    matchLabels:
      app: web
  template:
    metadata:
      labels:
        app: web
    spec:
      containers:
      - name: nginx
        image: nginx
```

```
Controller loop:
1. Watch: "ReplicaSet 'web' wants 3 pods"
2. Check: "How many pods with label 'app=web' exist?"
3. Compare: "0 exist, 3 desired"
4. Act: "Create 3 pods"
5. Repeat forever...

Later:
- Pod dies → Controller sees 2 pods → Creates 1 more
- You scale to 5 → Controller sees 3 pods → Creates 2 more
- You scale to 2 → Controller sees 5 pods → Deletes 3
```

### 5.4 Checking Controller Manager

```bash
# Controller manager pod
kubectl get pods -n kube-system | grep controller-manager
kubectl logs -n kube-system kube-controller-manager-<control-plane-node>

# Check for specific controller issues in logs
kubectl logs -n kube-system kube-controller-manager-<node> | grep -i "error\|failed"
```

> **Gotcha: Controller Manager Down**
>
> If the controller manager stops, nothing actively breaks immediately—existing pods keep running. But nothing new happens: deployments won't create pods, dead pods won't be replaced, jobs won't start. The cluster becomes "frozen."

---

## Part 6: Node Components

### 6.1 kubelet - The Node Agent

kubelet runs on every node (including control plane). It's responsible for:
- Registering the node with the cluster
- Watching for pods assigned to its node
- Starting/stopping containers via the container runtime
- Reporting node and pod status back to API server
- Running liveness/readiness probes

```bash
# Check kubelet status
systemctl status kubelet

# kubelet logs
journalctl -u kubelet -f

# kubelet configuration
cat /var/lib/kubelet/config.yaml
```

### 6.2 kube-proxy - The Network Plumber

kube-proxy runs on every node. It maintains network rules so that Services work:
- Watches Services and Endpoints
- Creates iptables/IPVS rules to forward traffic
- Enables ClusterIP, NodePort, LoadBalancer services

```bash
# Check kube-proxy
kubectl get pods -n kube-system | grep kube-proxy
kubectl logs -n kube-system kube-proxy-<id>

# See iptables rules kube-proxy created
iptables -t nat -L KUBE-SERVICES
```

### 6.3 Container Runtime

The actual software that runs containers. Kubernetes supports:
- **containerd** (most common, default in kubeadm)
- **CRI-O** (used by OpenShift)
- Docker (deprecated as of K8s 1.24, but images still work)

```bash
# Check containerd
systemctl status containerd
crictl ps  # List running containers
crictl images  # List images
```

---

## Part 7: Putting It All Together

### 7.1 What Happens When You Create a Deployment

```bash
kubectl create deployment nginx --image=nginx --replicas=3
```

```
┌─────────────────────────────────────────────────────────────────┐
│ Timeline of Events                                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│ 0ms    kubectl → API Server: "Create Deployment nginx"          │
│ 5ms    API Server → etcd: Store Deployment                      │
│                                                                  │
│ 10ms   Deployment Controller sees new Deployment                │
│ 15ms   Deployment Controller → API: "Create ReplicaSet"         │
│ 20ms   API Server → etcd: Store ReplicaSet                      │
│                                                                  │
│ 25ms   ReplicaSet Controller sees new ReplicaSet                │
│ 30ms   ReplicaSet Controller → API: "Create Pod 1, 2, 3"        │
│ 35ms   API Server → etcd: Store 3 Pods (Pending)                │
│                                                                  │
│ 40ms   Scheduler sees 3 unscheduled Pods                        │
│ 50ms   Scheduler → API: "Pod 1→node1, Pod 2→node2, Pod 3→node1" │
│ 55ms   API Server → etcd: Update Pods with nodeName             │
│                                                                  │
│ 60ms   kubelet on node1 sees 2 Pods assigned to it              │
│ 65ms   kubelet on node2 sees 1 Pod assigned to it               │
│ 70ms   kubelets → containerd: "Start nginx containers"          │
│                                                                  │
│ 500ms  Containers running                                        │
│ 505ms  kubelets → API: "Pods are Running"                       │
│ 510ms  API Server → etcd: Update Pod status                     │
│                                                                  │
│ Done!  kubectl get pods shows 3/3 Running                       │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Did You Know?

- **Static pods** are special pods managed directly by kubelet, not the API server. Control plane components (API server, scheduler, controller manager, etcd) run as static pods in kubeadm clusters. Their manifests live in `/etc/kubernetes/manifests/`.

- **The API server is stateless**. All state is in etcd. You can restart the API server and lose nothing. This is why Kubernetes is resilient.

- **Controllers use leader election** in HA setups. Only one controller manager is active at a time, the others are on standby. Same for the scheduler.

---

## Common Mistakes

| Mistake | Problem | Solution |
|---------|---------|----------|
| Thinking kubelet runs in a pod | kubelet is a systemd service | Check with `systemctl status kubelet` |
| Ignoring etcd health | etcd issues cascade to everything | Monitor etcd metrics and disk |
| Not checking component logs | Miss root cause during troubleshooting | Always check logs in kube-system |
| Confusing control plane with worker | Different components, different issues | Know what runs where |
| Forgetting static pods | Can't delete them with kubectl | Edit/delete manifest in `/etc/kubernetes/manifests/` |

---

## Quiz

1. **Which component is the only one that directly communicates with etcd?**
   <details>
   <summary>Answer</summary>
   The kube-apiserver. All other components (scheduler, controllers, kubelet) communicate through the API server, never directly with etcd.
   </details>

2. **A pod is stuck in Pending state. Which component should you investigate first?**
   <details>
   <summary>Answer</summary>
   The kube-scheduler. Pending means the pod hasn't been assigned to a node yet, which is the scheduler's job. Check scheduler logs and run `kubectl describe pod` to see why scheduling failed.
   </details>

3. **You delete a pod from a ReplicaSet. What happens and why?**
   <details>
   <summary>Answer</summary>
   A new pod is created automatically. The ReplicaSet controller continuously watches for pods matching its selector. When it sees fewer pods than desired (spec.replicas), it creates new ones to reconcile the difference.
   </details>

4. **Where are the manifests for control plane static pods located?**
   <details>
   <summary>Answer</summary>
   `/etc/kubernetes/manifests/` on the control plane node. kubelet watches this directory and automatically starts/stops pods based on the YAML files there.
   </details>

---

## Hands-On Exercise

**Task**: Explore your cluster's control plane components.

**Steps**:

1. **List all control plane pods**:
```bash
kubectl get pods -n kube-system
```

2. **Check component health**:
```bash
kubectl get componentstatuses
kubectl get --raw='/healthz?verbose'
```

3. **View API server configuration**:
```bash
# On control plane node
sudo cat /etc/kubernetes/manifests/kube-apiserver.yaml | grep -A5 "command:"
```

4. **Check scheduler logs for recent activity**:
```bash
kubectl logs -n kube-system -l component=kube-scheduler --tail=20
```

5. **Watch controller manager in action**:
```bash
# Terminal 1: Watch controller logs
kubectl logs -n kube-system -l component=kube-controller-manager -f

# Terminal 2: Create and delete a deployment
kubectl create deployment test --image=nginx --replicas=2
kubectl delete deployment test
```

6. **Explore etcd (if available)**:
```bash
# On control plane node with etcdctl
sudo ETCDCTL_API=3 etcdctl get /registry/namespaces/default \
  --endpoints=https://127.0.0.1:2379 \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key
```

**Success Criteria**:
- [ ] Can identify all control plane components and their pods
- [ ] Can check health of API server
- [ ] Can find and read control plane component logs
- [ ] Understand what each component does in pod creation

**Cleanup**:
```bash
# Remove test deployment if created
kubectl delete deployment test --ignore-not-found
```

---

## Practice Drills

### Drill 1: Component Identification Race (Target: 2 minutes)

Without looking at notes, identify which component handles each scenario:

| Scenario | Component |
|----------|-----------|
| Stores all cluster state | ___ |
| Decides which node runs a new pod | ___ |
| Authenticates kubectl requests | ___ |
| Creates pods when ReplicaSet changes | ___ |
| Reports node status to control plane | ___ |
| Maintains iptables rules for Services | ___ |

<details>
<summary>Answers</summary>

1. etcd
2. kube-scheduler
3. kube-apiserver
4. kube-controller-manager (ReplicaSet controller)
5. kubelet
6. kube-proxy

</details>

### Drill 2: Troubleshooting - Missing Scheduler (Target: 5 minutes)

**Scenario**: Pods are stuck in Pending forever.

```bash
# Setup: Break the scheduler
sudo mv /etc/kubernetes/manifests/kube-scheduler.yaml /tmp/

# Create a test pod
kubectl run drill-pod --image=nginx

# Observe the problem
kubectl get pods  # Pending forever
kubectl describe pod drill-pod | grep -A5 Events

# YOUR TASK: Diagnose and fix
# 1. What's missing?
# 2. How do you restore it?
```

<details>
<summary>Solution</summary>

```bash
# Check control plane pods
kubectl get pods -n kube-system | grep scheduler  # Nothing!

# Restore scheduler
sudo mv /tmp/kube-scheduler.yaml /etc/kubernetes/manifests/

# Wait for scheduler and verify
kubectl get pods -n kube-system | grep scheduler  # Running!
kubectl get pod drill-pod  # Now Running

# Cleanup
kubectl delete pod drill-pod
```

</details>

### Drill 3: Troubleshooting - Controller Manager Down (Target: 5 minutes)

**Scenario**: Deployments create ReplicaSets but pods never appear.

```bash
# Setup
sudo mv /etc/kubernetes/manifests/kube-controller-manager.yaml /tmp/

# Create deployment
kubectl create deployment drill-deploy --image=nginx --replicas=3

# Observe
kubectl get deploy  # Shows 0/3 ready
kubectl get rs      # ReplicaSet exists but...
kubectl get pods    # No pods!

# YOUR TASK: Diagnose and fix
```

<details>
<summary>Solution</summary>

```bash
# Check controller manager
kubectl get pods -n kube-system | grep controller  # Nothing!

# Restore controller manager
sudo mv /tmp/kube-controller-manager.yaml /etc/kubernetes/manifests/

# Watch pods appear
kubectl get pods -w  # 3 pods created

# Cleanup
kubectl delete deployment drill-deploy
```

</details>

### Drill 4: API Server Health Deep Dive (Target: 3 minutes)

Check API server health using multiple methods:

```bash
# Method 1: Basic connectivity
kubectl cluster-info

# Method 2: Health endpoints
kubectl get --raw='/healthz'
kubectl get --raw='/readyz'
kubectl get --raw='/livez'

# Method 3: Detailed health
kubectl get --raw='/readyz?verbose' | grep -E "^\[|ok|failed"

# Method 4: Direct curl (from control plane)
curl -k https://localhost:6443/healthz

# Method 5: Check API server logs for errors
kubectl logs -n kube-system -l component=kube-apiserver --tail=20 | grep -i error
```

### Drill 5: Watch the Reconciliation Loop (Target: 5 minutes)

See controllers in action:

```bash
# Terminal 1: Watch controller manager logs
kubectl logs -n kube-system -l component=kube-controller-manager -f | grep -i "replicaset\|deployment"

# Terminal 2: Create, scale, delete deployment
kubectl create deployment watch-me --image=nginx --replicas=2
sleep 5
kubectl scale deployment watch-me --replicas=5
sleep 5
kubectl delete deployment watch-me

# Observe logs in Terminal 1 - see the controller react to each change
```

### Drill 6: etcd Exploration (Target: 5 minutes)

Explore what etcd stores (requires etcdctl on control plane):

```bash
# Set up etcdctl alias
export ETCDCTL_API=3
alias etcdctl='etcdctl --endpoints=https://127.0.0.1:2379 \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key'

# List all keys (be careful in production!)
etcdctl get / --prefix --keys-only | head -50

# Find all pods
etcdctl get /registry/pods --prefix --keys-only

# Get a specific pod's data
etcdctl get /registry/pods/default/<pod-name>
```

### Drill 7: Challenge - Full Control Plane Restart

**Advanced**: Restart all control plane components and verify cluster recovery.

```bash
# WARNING: Only do this on practice clusters!

# 1. Note current state
kubectl get nodes
kubectl get pods -A | wc -l

# 2. Restart all control plane components
sudo systemctl restart kubelet
# Static pods will restart automatically

# 3. Wait and verify recovery
sleep 30
kubectl get nodes  # All Ready?
kubectl get pods -n kube-system  # All Running?

# 4. Test workload scheduling
kubectl run recovery-test --image=nginx
kubectl get pods  # Running?
kubectl delete pod recovery-test
```

---

## Next Module

[Module 1.2: Extension Interfaces (CNI, CSI, CRI)](../module-1.2-extension-interfaces/) - How Kubernetes plugs in networking, storage, and container runtimes.
