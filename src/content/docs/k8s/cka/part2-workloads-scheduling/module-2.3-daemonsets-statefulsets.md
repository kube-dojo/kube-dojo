---
title: "Module 2.3: DaemonSets & StatefulSets"
slug: k8s/cka/part2-workloads-scheduling/module-2.3-daemonsets-statefulsets
sidebar:
  order: 4
---
> **Complexity**: `[MEDIUM]` - Specialized workload patterns
>
> **Time to Complete**: 40-50 minutes
>
> **Prerequisites**: Module 2.1 (Pods), Module 2.2 (Deployments)

---

## Why This Module Matters

Deployments work great for stateless applications, but not everything is stateless. Some workloads have special requirements:

- **DaemonSets**: When you need exactly one pod per node (logging, monitoring, network plugins)
- **StatefulSets**: When pods need stable identities and persistent storage (databases, distributed systems)

The CKA exam tests your understanding of when to use each controller and how to troubleshoot them. Knowing the right tool for the job is a key admin skill.

> **The Specialist Teams Analogy**
>
> Think of your cluster as a hospital. **Deployments** are like general practitioners—you can have any number, they're interchangeable, and patients don't care which one they see. **DaemonSets** are like security guards—you need exactly one per entrance (node), no more, no less. **StatefulSets** are like surgeons—each has a unique identity, their own dedicated tools (storage), and patients specifically request "Dr. Smith" (stable network identity).

---

## What You'll Learn

By the end of this module, you'll be able to:
- Create and manage DaemonSets
- Understand when to use DaemonSets vs Deployments
- Create and manage StatefulSets
- Understand stable network identity and storage
- Troubleshoot DaemonSet and StatefulSet issues

---

## Part 1: DaemonSets

### 1.1 What Is a DaemonSet?

A DaemonSet ensures that **all (or some) nodes run a copy of a pod**.

```
┌────────────────────────────────────────────────────────────────┐
│                       DaemonSet                                 │
│                                                                 │
│   Node 1              Node 2              Node 3               │
│   ┌─────────────┐     ┌─────────────┐     ┌─────────────┐      │
│   │ ┌─────────┐ │     │ ┌─────────┐ │     │ ┌─────────┐ │      │
│   │ │ DS Pod  │ │     │ │ DS Pod  │ │     │ │ DS Pod  │ │      │
│   │ │(fluentd)│ │     │ │(fluentd)│ │     │ │(fluentd)│ │      │
│   │ └─────────┘ │     │ └─────────┘ │     │ └─────────┘ │      │
│   │             │     │             │     │             │      │
│   │ [App Pods] │     │ [App Pods] │     │ [App Pods] │      │
│   │             │     │             │     │             │      │
│   └─────────────┘     └─────────────┘     └─────────────┘      │
│                                                                 │
│   When Node 4 joins → DaemonSet automatically creates pod      │
│   When Node 2 leaves → Pod is terminated                       │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
```

### 1.2 Common DaemonSet Use Cases

| Use Case | Example |
|----------|---------|
| Log collection | Fluentd, Filebeat |
| Node monitoring | Node Exporter, Datadog agent |
| Network plugins | Calico, Cilium, Weave |
| Storage daemons | GlusterFS, Ceph |
| Security agents | Falco, Sysdig |

### 1.3 Creating a DaemonSet

```yaml
# fluentd-daemonset.yaml
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: fluentd
  labels:
    app: fluentd
spec:
  selector:
    matchLabels:
      app: fluentd
  template:
    metadata:
      labels:
        app: fluentd
    spec:
      containers:
      - name: fluentd
        image: fluentd:v1.16
        resources:
          limits:
            memory: 200Mi
          requests:
            cpu: 100m
            memory: 200Mi
        volumeMounts:
        - name: varlog
          mountPath: /var/log
      volumes:
      - name: varlog
        hostPath:
          path: /var/log
```

```bash
kubectl apply -f fluentd-daemonset.yaml
```

### 1.4 DaemonSet vs Deployment

| Aspect | DaemonSet | Deployment |
|--------|-----------|------------|
| Pod count | One per node (automatic) | Specified replicas |
| Scheduling | Bypasses scheduler | Uses scheduler |
| Node addition | Auto-creates pod | No automatic action |
| Use case | Node-level services | Application workloads |

### 1.5 DaemonSet Commands

```bash
# List DaemonSets
kubectl get daemonsets
kubectl get ds           # Short form

# Describe DaemonSet
kubectl describe ds fluentd

# Check pods created by DaemonSet
kubectl get pods -l app=fluentd -o wide

# Delete DaemonSet
kubectl delete ds fluentd
```

> **Did You Know?**
>
> DaemonSets ignore most scheduling constraints by default. They even run on control plane nodes if there are no taints preventing it. Use `nodeSelector` or `tolerations` to control placement.

---

## Part 2: DaemonSet Scheduling

### 2.1 Running on Specific Nodes

Use `nodeSelector` to run only on certain nodes:

```yaml
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: ssd-monitor
spec:
  selector:
    matchLabels:
      app: ssd-monitor
  template:
    metadata:
      labels:
        app: ssd-monitor
    spec:
      nodeSelector:
        disk: ssd            # Only nodes with this label
      containers:
      - name: monitor
        image: busybox
        command: ["sleep", "infinity"]
```

```bash
# Label a node
kubectl label node worker-1 disk=ssd

# DaemonSet only runs on labeled nodes
kubectl get pods -l app=ssd-monitor -o wide
```

### 2.2 Tolerating Taints

DaemonSets often need to run on tainted nodes:

```yaml
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: node-monitor
spec:
  selector:
    matchLabels:
      app: node-monitor
  template:
    metadata:
      labels:
        app: node-monitor
    spec:
      tolerations:
      # Tolerate control-plane taint
      - key: node-role.kubernetes.io/control-plane
        operator: Exists
        effect: NoSchedule
      # Tolerate all taints (run everywhere)
      - operator: Exists
      containers:
      - name: monitor
        image: prom/node-exporter
```

### 2.3 Update Strategy

```yaml
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: fluentd
spec:
  updateStrategy:
    type: RollingUpdate        # Default
    rollingUpdate:
      maxUnavailable: 1        # Update one node at a time
  selector:
    matchLabels:
      app: fluentd
  template:
    # ...
```

| Strategy | Behavior |
|----------|----------|
| `RollingUpdate` | Gradually update pods, one node at a time |
| `OnDelete` | Only update when pod is manually deleted |

---

## Part 3: StatefulSets

### 3.1 What Is a StatefulSet?

StatefulSets manage stateful applications with:
- **Stable, unique network identifiers**
- **Stable, persistent storage**
- **Ordered, graceful deployment and scaling**

```
┌────────────────────────────────────────────────────────────────┐
│                       StatefulSet                               │
│                                                                 │
│   Unlike Deployments, pods have stable identities:             │
│                                                                 │
│   ┌───────────────┐  ┌───────────────┐  ┌───────────────┐      │
│   │    web-0      │  │    web-1      │  │    web-2      │      │
│   │  (always 0)   │  │  (always 1)   │  │  (always 2)   │      │
│   │               │  │               │  │               │      │
│   │ PVC: data-0   │  │ PVC: data-1   │  │ PVC: data-2   │      │
│   │ DNS: web-0... │  │ DNS: web-1... │  │ DNS: web-2... │      │
│   └───────────────┘  └───────────────┘  └───────────────┘      │
│                                                                 │
│   If web-1 dies and restarts:                                  │
│   - Still named web-1 (not web-3)                              │
│   - Reattaches to PVC data-1                                   │
│   - Same DNS name: web-1.nginx.default.svc.cluster.local       │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
```

### 3.2 StatefulSet Use Cases

| Use Case | Example |
|----------|---------|
| Databases | PostgreSQL, MySQL, MongoDB |
| Distributed systems | Kafka, Zookeeper, etcd |
| Search engines | Elasticsearch |
| Message queues | RabbitMQ |

### 3.3 StatefulSet Requirements

StatefulSets require a **Headless Service** for network identity:

```yaml
# Headless Service (required)
apiVersion: v1
kind: Service
metadata:
  name: nginx
  labels:
    app: nginx
spec:
  ports:
  - port: 80
    name: web
  clusterIP: None          # This makes it headless
  selector:
    app: nginx
---
# StatefulSet
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: web
spec:
  serviceName: nginx       # Must reference the headless service
  replicas: 3
  selector:
    matchLabels:
      app: nginx
  template:
    metadata:
      labels:
        app: nginx
    spec:
      containers:
      - name: nginx
        image: nginx
        ports:
        - containerPort: 80
        volumeMounts:
        - name: data
          mountPath: /usr/share/nginx/html
  volumeClaimTemplates:    # Creates PVC for each pod
  - metadata:
      name: data
    spec:
      accessModes: ["ReadWriteOnce"]
      resources:
        requests:
          storage: 1Gi
```

### 3.4 Stable Network Identity

```bash
# Pod DNS names follow pattern:
# <pod-name>.<service-name>.<namespace>.svc.cluster.local

# For StatefulSet "web" with headless service "nginx":
web-0.nginx.default.svc.cluster.local
web-1.nginx.default.svc.cluster.local
web-2.nginx.default.svc.cluster.local

# Other pods can reach specific instances:
curl web-0.nginx
curl web-1.nginx
```

### 3.5 Stable Storage

```bash
# Each pod gets its own PVC named:
# <volumeClaimTemplates.name>-<pod-name>
data-web-0
data-web-1
data-web-2

# When pod restarts, it reattaches to its specific PVC
# Data persists across pod restarts
```

> **Did You Know?**
>
> When you delete a StatefulSet, the PVCs are NOT automatically deleted. This is a safety feature—you keep your data. To clean up, manually delete the PVCs after deleting the StatefulSet.

---

## Part 4: StatefulSet Operations

### 4.1 Ordered Creation and Deletion

```
Scaling Up (0 → 3):
web-0 created and ready → web-1 created and ready → web-2 created

Scaling Down (3 → 1):
web-2 terminated → web-1 terminated → web-0 remains

Each pod waits for previous to be Running and Ready
```

### 4.2 Pod Management Policy

```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: web
spec:
  podManagementPolicy: OrderedReady   # Default - sequential
  # podManagementPolicy: Parallel     # All at once (like Deployment)
```

| Policy | Behavior |
|--------|----------|
| `OrderedReady` | Sequential creation/deletion (default) |
| `Parallel` | All pods created/deleted simultaneously |

### 4.3 Update Strategy

```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: web
spec:
  updateStrategy:
    type: RollingUpdate
    rollingUpdate:
      partition: 2          # Only update pods >= 2
```

**Partition** enables canary deployments:
- With `partition: 2`, only web-2 gets updated
- web-0 and web-1 keep the old version
- Useful for testing updates on subset of pods

### 4.4 StatefulSet Commands

```bash
# List StatefulSets
kubectl get statefulsets
kubectl get sts           # Short form

# Describe
kubectl describe sts web

# Scale
kubectl scale sts web --replicas=5

# Check pods (notice ordered names)
kubectl get pods -l app=nginx

# Check PVCs (one per pod)
kubectl get pvc

# Delete StatefulSet (PVCs remain!)
kubectl delete sts web

# Delete PVCs manually
kubectl delete pvc data-web-0 data-web-1 data-web-2
```

---

## Part 5: Deployment vs StatefulSet

### 5.1 Comparison

| Aspect | Deployment | StatefulSet |
|--------|------------|-------------|
| Pod names | Random suffix (nginx-5d5dd5d5fb-xyz) | Ordinal index (web-0, web-1) |
| Network identity | None (use Service) | Stable DNS per pod |
| Storage | Shared or none | Dedicated PVC per pod |
| Scaling order | Any order | Sequential (ordered) |
| Rolling update | Random order | Reverse order (N-1 first) |
| Use case | Stateless apps | Stateful apps |

### 5.2 When to Use What

```
┌────────────────────────────────────────────────────────────────┐
│                   Choosing the Right Controller                 │
│                                                                 │
│   Does each pod need unique identity?                          │
│         │                                                       │
│         ├── No ──► Does each node need one pod?                │
│         │                │                                      │
│         │                ├── Yes ──► DaemonSet                 │
│         │                │                                      │
│         │                └── No ──► Deployment                 │
│         │                                                       │
│         └── Yes ──► Does it need persistent storage?           │
│                          │                                      │
│                          └── Yes/No ──► StatefulSet            │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
```

> **War Story: The Database Disaster**
>
> A team deployed PostgreSQL using a Deployment with a PVC. It worked—until the pod was rescheduled. The new pod got a different IP, replication broke, and the standby couldn't find the primary. Switching to a StatefulSet with stable network identity fixed everything. Use the right tool!

---

## Part 6: Headless Services Deep Dive

### 6.1 What Is a Headless Service?

A Service with `clusterIP: None`. Instead of load balancing, DNS returns individual pod IPs.

```yaml
# Regular Service
apiVersion: v1
kind: Service
metadata:
  name: nginx-regular
spec:
  selector:
    app: nginx
  ports:
  - port: 80
# DNS: nginx-regular → ClusterIP (load balanced)

---
# Headless Service
apiVersion: v1
kind: Service
metadata:
  name: nginx-headless
spec:
  clusterIP: None           # Headless!
  selector:
    app: nginx
  ports:
  - port: 80
# DNS: nginx-headless → Returns all pod IPs
# DNS: web-0.nginx-headless → Specific pod IP
```

### 6.2 DNS Resolution Comparison

```bash
# Regular service - returns ClusterIP
nslookup nginx-regular
# Server: 10.96.0.10
# Address: 10.96.0.10#53
# Name: nginx-regular.default.svc.cluster.local
# Address: 10.96.100.50  (ClusterIP)

# Headless service - returns pod IPs
nslookup nginx-headless
# Server: 10.96.0.10
# Address: 10.96.0.10#53
# Name: nginx-headless.default.svc.cluster.local
# Address: 10.244.1.5  (Pod IP)
# Address: 10.244.2.6  (Pod IP)
# Address: 10.244.3.7  (Pod IP)
```

---

## Common Mistakes

| Mistake | Problem | Solution |
|---------|---------|----------|
| StatefulSet without headless Service | Pods don't get stable DNS names | Create headless Service with matching selector |
| Deleting StatefulSet expecting PVC cleanup | Data remains, storage quota consumed | Manually delete PVCs if data not needed |
| Using Deployment for databases | No stable identity, storage issues | Use StatefulSet for stateful workloads |
| DaemonSet on all nodes unexpectedly | Runs on control plane too | Add appropriate tolerations/nodeSelector |
| Wrong serviceName in StatefulSet | DNS resolution fails | Ensure serviceName matches headless Service name |

---

## Quiz

1. **What ensures exactly one pod runs on each node?**
   <details>
   <summary>Answer</summary>
   A **DaemonSet**. It automatically creates a pod on each node (or selected nodes via nodeSelector) and removes pods when nodes are removed.
   </details>

2. **Why do StatefulSets need a headless Service?**
   <details>
   <summary>Answer</summary>
   A headless Service (clusterIP: None) provides stable DNS names for each pod. Without it, pods wouldn't have predictable network identities. The DNS format is `<pod-name>.<service-name>.<namespace>.svc.cluster.local`.
   </details>

3. **What happens to PVCs when you delete a StatefulSet?**
   <details>
   <summary>Answer</summary>
   PVCs are **NOT** automatically deleted. This is a safety feature to preserve data. You must manually delete the PVCs if you want to remove the storage.
   </details>

4. **How does StatefulSet scaling differ from Deployment?**
   <details>
   <summary>Answer</summary>
   StatefulSets scale **sequentially**. Scale up: web-0, then web-1, then web-2 (each waits for previous to be Ready). Scale down: reverse order. Deployments scale pods in parallel.
   </details>

---

## Hands-On Exercise

**Task**: Create a DaemonSet and StatefulSet, understand their behaviors.

**Steps**:

### Part A: DaemonSet

1. **Create a DaemonSet**:
```bash
cat > node-monitor-ds.yaml << 'EOF'
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: node-monitor
spec:
  selector:
    matchLabels:
      app: node-monitor
  template:
    metadata:
      labels:
        app: node-monitor
    spec:
      containers:
      - name: monitor
        image: busybox
        command: ["sh", "-c", "while true; do echo $(hostname); sleep 60; done"]
        resources:
          limits:
            memory: 50Mi
            cpu: 50m
EOF

kubectl apply -f node-monitor-ds.yaml
```

2. **Verify one pod per node**:
```bash
kubectl get pods -l app=node-monitor -o wide
kubectl get ds node-monitor
# DESIRED = CURRENT = READY = number of nodes
```

3. **Check logs from a specific node's pod**:
```bash
kubectl logs -l app=node-monitor --all-containers
```

4. **Cleanup DaemonSet**:
```bash
kubectl delete ds node-monitor
rm node-monitor-ds.yaml
```

### Part B: StatefulSet

1. **Create headless Service and StatefulSet**:
```bash
cat > statefulset-demo.yaml << 'EOF'
apiVersion: v1
kind: Service
metadata:
  name: nginx
spec:
  clusterIP: None
  selector:
    app: nginx
  ports:
  - port: 80
---
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: web
spec:
  serviceName: nginx
  replicas: 3
  selector:
    matchLabels:
      app: nginx
  template:
    metadata:
      labels:
        app: nginx
    spec:
      containers:
      - name: nginx
        image: nginx
        ports:
        - containerPort: 80
EOF

kubectl apply -f statefulset-demo.yaml
```

2. **Watch ordered creation**:
```bash
kubectl get pods -l app=nginx -w
# web-0 Running, then web-1, then web-2
```

3. **Verify stable network identity**:
```bash
# Create a test pod
kubectl run dns-test --image=busybox --rm -it --restart=Never -- nslookup web-0.nginx
kubectl run dns-test --image=busybox --rm -it --restart=Never -- nslookup web-1.nginx
```

4. **Scale down and observe order**:
```bash
kubectl scale sts web --replicas=1
kubectl get pods -l app=nginx -w
# web-2 terminates, then web-1
```

5. **Scale back up**:
```bash
kubectl scale sts web --replicas=3
kubectl get pods -l app=nginx -w
# web-1 created, then web-2
```

6. **Cleanup**:
```bash
kubectl delete -f statefulset-demo.yaml
rm statefulset-demo.yaml
```

**Success Criteria**:
- [ ] Can create DaemonSets
- [ ] Understand one pod per node behavior
- [ ] Can create StatefulSets with headless Services
- [ ] Understand ordered scaling
- [ ] Know when to use each controller

---

## Practice Drills

### Drill 1: DaemonSet Creation (Target: 3 minutes)

```bash
# Create DaemonSet
cat << 'EOF' | kubectl apply -f -
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: log-collector
spec:
  selector:
    matchLabels:
      app: log-collector
  template:
    metadata:
      labels:
        app: log-collector
    spec:
      containers:
      - name: collector
        image: busybox
        command: ["sleep", "infinity"]
EOF

# Verify
kubectl get ds log-collector
kubectl get pods -l app=log-collector -o wide

# Cleanup
kubectl delete ds log-collector
```

### Drill 2: DaemonSet with nodeSelector (Target: 5 minutes)

```bash
# Label one node
NODE=$(kubectl get nodes -o jsonpath='{.items[0].metadata.name}')
kubectl label node $NODE disk=ssd

# Create DaemonSet with nodeSelector
cat << 'EOF' | kubectl apply -f -
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: ssd-only
spec:
  selector:
    matchLabels:
      app: ssd-only
  template:
    metadata:
      labels:
        app: ssd-only
    spec:
      nodeSelector:
        disk: ssd
      containers:
      - name: app
        image: busybox
        command: ["sleep", "infinity"]
EOF

# Verify - should only run on labeled node
kubectl get pods -l app=ssd-only -o wide

# Cleanup
kubectl delete ds ssd-only
kubectl label node $NODE disk-
```

### Drill 3: StatefulSet Basic (Target: 5 minutes)

```bash
# Create headless service and StatefulSet
cat << 'EOF' | kubectl apply -f -
apiVersion: v1
kind: Service
metadata:
  name: db
spec:
  clusterIP: None
  selector:
    app: db
  ports:
  - port: 5432
---
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: db
spec:
  serviceName: db
  replicas: 3
  selector:
    matchLabels:
      app: db
  template:
    metadata:
      labels:
        app: db
    spec:
      containers:
      - name: postgres
        image: busybox
        command: ["sleep", "infinity"]
EOF

# Watch ordered creation
kubectl get pods -l app=db -w &
sleep 30
kill %1

# Verify names
kubectl get pods -l app=db

# Cleanup
kubectl delete sts db
kubectl delete svc db
```

### Drill 4: StatefulSet DNS Test (Target: 5 minutes)

```bash
# Create StatefulSet with headless service
cat << 'EOF' | kubectl apply -f -
apiVersion: v1
kind: Service
metadata:
  name: nginx
spec:
  clusterIP: None
  selector:
    app: nginx
  ports:
  - port: 80
---
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: web
spec:
  serviceName: nginx
  replicas: 2
  selector:
    matchLabels:
      app: nginx
  template:
    metadata:
      labels:
        app: nginx
    spec:
      containers:
      - name: nginx
        image: nginx
EOF

# Wait for ready
kubectl wait --for=condition=ready pod/web-0 pod/web-1 --timeout=60s

# Test DNS resolution
kubectl run dns-test --image=busybox --rm -it --restart=Never -- nslookup nginx
kubectl run dns-test --image=busybox --rm -it --restart=Never -- nslookup web-0.nginx
kubectl run dns-test --image=busybox --rm -it --restart=Never -- nslookup web-1.nginx

# Cleanup
kubectl delete sts web
kubectl delete svc nginx
```

### Drill 5: StatefulSet Scaling Order (Target: 3 minutes)

```bash
# Create StatefulSet
cat << 'EOF' | kubectl apply -f -
apiVersion: v1
kind: Service
metadata:
  name: order-test
spec:
  clusterIP: None
  selector:
    app: order-test
  ports:
  - port: 80
---
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: order
spec:
  serviceName: order-test
  replicas: 1
  selector:
    matchLabels:
      app: order-test
  template:
    metadata:
      labels:
        app: order-test
    spec:
      containers:
      - name: nginx
        image: nginx
EOF

# Scale up and watch order
kubectl scale sts order --replicas=3
kubectl get pods -l app=order-test -w &
sleep 30
kill %1

# Scale down and watch reverse order
kubectl scale sts order --replicas=1
kubectl get pods -l app=order-test -w &
sleep 30
kill %1

# Cleanup
kubectl delete sts order
kubectl delete svc order-test
```

### Drill 6: Troubleshooting - DaemonSet Not Running on Node

```bash
# Taint a node
NODE=$(kubectl get nodes -o jsonpath='{.items[0].metadata.name}')
kubectl taint node $NODE special=true:NoSchedule

# Create DaemonSet without toleration
cat << 'EOF' | kubectl apply -f -
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: no-toleration
spec:
  selector:
    matchLabels:
      app: no-toleration
  template:
    metadata:
      labels:
        app: no-toleration
    spec:
      containers:
      - name: app
        image: busybox
        command: ["sleep", "infinity"]
EOF

# Check - won't run on tainted node
kubectl get pods -l app=no-toleration -o wide
kubectl get ds no-toleration

# YOUR TASK: Fix by adding toleration
# (Delete and recreate with toleration)

# Cleanup
kubectl delete ds no-toleration
kubectl taint node $NODE special-
```

<details>
<summary>Solution</summary>

```bash
cat << 'EOF' | kubectl apply -f -
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: with-toleration
spec:
  selector:
    matchLabels:
      app: with-toleration
  template:
    metadata:
      labels:
        app: with-toleration
    spec:
      tolerations:
      - key: special
        operator: Equal
        value: "true"
        effect: NoSchedule
      containers:
      - name: app
        image: busybox
        command: ["sleep", "infinity"]
EOF

kubectl get pods -l app=with-toleration -o wide
kubectl delete ds with-toleration
```

</details>

### Drill 7: Challenge - Identify the Right Controller

For each scenario, identify whether to use Deployment, DaemonSet, or StatefulSet:

1. Web application with 5 replicas
2. Log collector on every node
3. PostgreSQL database cluster
4. REST API service
5. Prometheus node exporter
6. Kafka cluster
7. nginx reverse proxy

<details>
<summary>Answers</summary>

1. **Deployment** - Stateless web app
2. **DaemonSet** - Need one per node
3. **StatefulSet** - Needs stable identity and storage
4. **Deployment** - Stateless REST API
5. **DaemonSet** - Monitoring agent per node
6. **StatefulSet** - Distributed system with stable identity
7. **Deployment** - Stateless proxy (unless specific instance needed)

</details>

---

## Next Module

[Module 2.4: Jobs & CronJobs](../module-2.4-jobs-cronjobs/) - Batch workloads and scheduled tasks.
