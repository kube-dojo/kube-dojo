---
title: "Module 2.1: Pods Deep-Dive"
slug: k8s/cka/part2-workloads-scheduling/module-2.1-pods
sidebar:
  order: 2
---
> **Complexity**: `[MEDIUM]` - Foundation for all workloads
>
> **Time to Complete**: 40-50 minutes
>
> **Prerequisites**: Module 1.1 (Control Plane), Module 0.2 (Shell Mastery)

---

## Why This Module Matters

Pods are the **atomic unit of deployment** in Kubernetes. Every container you run lives inside a pod. Every Deployment, StatefulSet, DaemonSet, and Job creates pods. If you don't understand pods deeply, you'll struggle with everything else.

The CKA exam tests pod creation, troubleshooting, and multi-container patterns. You'll need to create pods quickly, debug failing pods, and understand how containers within a pod interact.

> **The Apartment Analogy**
>
> Think of a pod like an apartment. Containers are roommates sharing the apartment. They share the same address (IP), the same living space (network namespace), and can share storage (volumes). They have their own rooms (filesystem) but can talk to each other easily (localhost). When the apartment is demolished (pod deleted), all roommates leave together.

---

## What You'll Learn

By the end of this module, you'll be able to:
- Create pods using imperative commands and YAML
- Understand pod lifecycle and states
- Debug pods using logs, exec, and describe
- Create multi-container pods (sidecar, init containers)
- Understand pod networking basics

---

## Part 1: Pod Fundamentals

### 1.1 What Is a Pod?

A pod is:
- The smallest deployable unit in Kubernetes
- A wrapper around one or more containers
- Containers that share network and storage
- Ephemeral (can be killed and recreated)

```
┌────────────────────────────────────────────────────────────────┐
│                           Pod                                   │
│                                                                 │
│   ┌─────────────────┐    ┌─────────────────┐                   │
│   │   Container 1   │    │   Container 2   │                   │
│   │   (main app)    │    │   (sidecar)     │                   │
│   │                 │    │                 │                   │
│   │   Port 8080     │    │   Port 9090     │                   │
│   └─────────────────┘    └─────────────────┘                   │
│            │                      │                             │
│            └──────────┬───────────┘                             │
│                       │                                         │
│              Shared Network Namespace                           │
│              • Same IP address                                  │
│              • localhost communication                          │
│              • Shared ports (can't conflict)                    │
│                                                                 │
│              Shared Volumes (optional)                          │
│              • Mount same volume                                │
│              • Share data between containers                    │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
```

### 1.2 Pod vs Container

| Aspect | Container | Pod |
|--------|-----------|-----|
| Unit | Single process | Group of containers |
| Network | Own network namespace | Shared network namespace |
| IP Address | None (uses pod's) | One per pod |
| Storage | Own filesystem | Can share volumes |
| Lifecycle | Managed by pod | Managed by Kubernetes |

### 1.3 Why Pods, Not Just Containers?

Pods enable:
1. **Co-located helpers**: Sidecar containers for logging, proxying
2. **Shared resources**: Containers that need to share files or communicate
3. **Atomic scheduling**: Tightly coupled containers scheduled together
4. **Abstraction**: Kubernetes manages pods, not raw containers

---

## Part 2: Creating Pods

### 2.1 Imperative Commands (Fast for Exam)

```bash
# Create a simple pod
kubectl run nginx --image=nginx

# Create pod and expose port
kubectl run nginx --image=nginx --port=80

# Create pod with labels
kubectl run nginx --image=nginx --labels="app=web,env=prod"

# Create pod with environment variables
kubectl run nginx --image=nginx --env="ENV=production"

# Create pod with resource requests
kubectl run nginx --image=nginx --requests="cpu=100m,memory=128Mi"

# Create pod with resource limits
kubectl run nginx --image=nginx --limits="cpu=200m,memory=256Mi"

# Generate YAML without creating (essential for exam!)
kubectl run nginx --image=nginx --dry-run=client -o yaml > pod.yaml
```

### 2.2 Declarative YAML

```yaml
# pod.yaml
apiVersion: v1
kind: Pod
metadata:
  name: nginx
  labels:
    app: nginx
    env: production
spec:
  containers:
  - name: nginx
    image: nginx:1.25
    ports:
    - containerPort: 80
    resources:
      requests:
        memory: "64Mi"
        cpu: "100m"
      limits:
        memory: "128Mi"
        cpu: "200m"
```

```bash
# Apply the pod
kubectl apply -f pod.yaml
```

### 2.3 Essential Pod Operations

```bash
# List pods
kubectl get pods
kubectl get pods -o wide        # Show IP and node
kubectl get pods --show-labels  # Show labels

# Describe pod (detailed info)
kubectl describe pod nginx

# Get pod YAML
kubectl get pod nginx -o yaml

# Delete pod
kubectl delete pod nginx

# Delete pod immediately (skip graceful shutdown)
kubectl delete pod nginx --grace-period=0 --force

# Watch pods
kubectl get pods -w
```

> **Did You Know?**
>
> The `--dry-run=client -o yaml` pattern is your best friend in the exam. It generates valid YAML that you can modify, saving you from typing everything from scratch. Master this pattern!

---

## Part 3: Pod Lifecycle

### 3.1 Pod Phases

| Phase | Description |
|-------|-------------|
| **Pending** | Pod accepted, waiting to be scheduled or pull images |
| **Running** | Pod bound to node, at least one container running |
| **Succeeded** | All containers terminated successfully (exit 0) |
| **Failed** | All containers terminated, at least one failed |
| **Unknown** | Pod state cannot be determined (node communication issue) |

### 3.2 Container States

| State | Description |
|-------|-------------|
| **Waiting** | Not running yet (pulling image, applying secrets) |
| **Running** | Executing without issues |
| **Terminated** | Finished execution (successfully or failed) |

### 3.3 Lifecycle Visualization

```
┌────────────────────────────────────────────────────────────────┐
│                      Pod Lifecycle                              │
│                                                                 │
│   Pod Created                                                   │
│       │                                                         │
│       ▼                                                         │
│   ┌─────────┐     No node available                            │
│   │ Pending │◄────────────────────────────────┐                │
│   └────┬────┘                                 │                │
│        │ Scheduled to node                    │                │
│        ▼                                      │                │
│   ┌─────────┐     Container crashes           │                │
│   │ Running │────────────────────────────────►│                │
│   └────┬────┘                                 │                │
│        │                                      │                │
│        ├─────────────────────┐                │                │
│        │                     │                │                │
│        ▼                     ▼                │                │
│   ┌───────────┐        ┌────────┐            │                │
│   │ Succeeded │        │ Failed │            │                │
│   │ (exit 0)  │        │(exit≠0)│            │                │
│   └───────────┘        └────────┘            │                │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
```

### 3.4 Checking Pod Status

```bash
# Quick status
kubectl get pod nginx
# NAME    READY   STATUS    RESTARTS   AGE
# nginx   1/1     Running   0          5m

# Detailed status
kubectl describe pod nginx | grep -A10 "Status:"

# Container states
kubectl get pod nginx -o jsonpath='{.status.containerStatuses[0].state}'

# Check why a pod is pending
kubectl describe pod nginx | grep -A5 "Events:"
```

---

## Part 4: Debugging Pods

### 4.1 The Debugging Workflow

```
Pod Problem
    │
    ├── kubectl get pods (check STATUS)
    │       │
    │       ├── Pending → kubectl describe (check Events)
    │       │               └── ImagePullBackOff, Insufficient resources, etc.
    │       │
    │       ├── CrashLoopBackOff → kubectl logs (check app errors)
    │       │                        └── Application crash, missing config, etc.
    │       │
    │       └── Running but not working → kubectl exec (check inside)
    │                                       └── Network issues, wrong config, etc.
    │
    └── kubectl describe pod (always useful)
```

### 4.2 Viewing Logs

```bash
# Current logs
kubectl logs nginx

# Follow logs (like tail -f)
kubectl logs nginx -f

# Last 100 lines
kubectl logs nginx --tail=100

# Logs from last hour
kubectl logs nginx --since=1h

# Logs from specific container (multi-container pod)
kubectl logs nginx -c sidecar

# Previous container logs (after crash)
kubectl logs nginx --previous
```

### 4.3 Executing Commands in Pods

```bash
# Run a command
kubectl exec nginx -- ls /

# Interactive shell
kubectl exec -it nginx -- /bin/bash
kubectl exec -it nginx -- /bin/sh   # If bash not available

# Specific container in multi-container pod
kubectl exec -it nginx -c sidecar -- /bin/sh

# Run commands without shell
kubectl exec nginx -- cat /etc/nginx/nginx.conf
kubectl exec nginx -- env
kubectl exec nginx -- ps aux
```

### 4.4 Common Pod Issues

| Symptom | Cause | Solution |
|---------|-------|----------|
| `ImagePullBackOff` | Wrong image name or no access | Fix image name, check registry auth |
| `CrashLoopBackOff` | Container keeps crashing | Check logs for app errors |
| `Pending` (no events) | No node has enough resources | Free up resources or add nodes |
| `Pending` (scheduling) | Taints, affinity rules | Check node taints and pod tolerations |
| `Running` but not ready | Readiness probe failing | Check probe configuration and app |
| `OOMKilled` | Out of memory | Increase memory limits |

### 4.5 Debugging Commands Cheat Sheet

```bash
# The trinity of debugging
kubectl get pod nginx              # What's the status?
kubectl describe pod nginx         # What's happening? (events)
kubectl logs nginx                 # What does the app say?

# Deeper investigation
kubectl exec -it nginx -- /bin/sh  # Get inside
kubectl get events --sort-by='.lastTimestamp'  # Recent events
kubectl top pod nginx              # Resource usage (if metrics-server)
```

> **War Story: The Silent Failure**
>
> A junior engineer spent 3 hours debugging why their pod wasn't working. `kubectl get pods` showed `Running`. They finally ran `kubectl describe pod` and saw the readiness probe was failing. The pod was running but not receiving traffic because it wasn't ready. Always check `READY` column and describe output!

---

## Part 5: Multi-Container Pods

### 5.1 Why Multiple Containers?

Multi-container pods are for containers that:
- Need to share resources (network, storage)
- Have tightly coupled lifecycles
- Form a single cohesive unit of service

### 5.2 Multi-Container Patterns

```
┌────────────────────────────────────────────────────────────────┐
│                Multi-Container Patterns                         │
│                                                                 │
│   Sidecar                    Ambassador             Adapter     │
│   ┌──────────────────┐       ┌──────────────────┐  ┌─────────┐ │
│   │ ┌────┐  ┌────┐   │       │ ┌────┐  ┌────┐   │  │┌────┐   │ │
│   │ │Main│  │Log │   │       │ │Main│  │Proxy│  │  ││Main│   │ │
│   │ │App │──│Ship│   │       │ │App │──│     │──┼──││App │   │ │
│   │ └────┘  └────┘   │       │ └────┘  └────┘   │  │└──┬─┘   │ │
│   │   Main + Helper  │       │   Proxy outbound │  │   │     │ │
│   └──────────────────┘       └──────────────────┘  │┌──▼──┐  │ │
│                                                    ││Adapt│  │ │
│   Examples:                  Examples:             ││Log  │  │ │
│   - Log collectors           - Service mesh proxy  │└─────┘  │ │
│   - Config reloaders         - Database proxy      │Transform│ │
│   - Git sync                 - Auth proxy          └─────────┘ │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
```

### 5.3 Sidecar Pattern

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: web-with-sidecar
spec:
  containers:
  # Main application container
  - name: web
    image: nginx
    ports:
    - containerPort: 80
    volumeMounts:
    - name: logs
      mountPath: /var/log/nginx

  # Sidecar container - ships logs
  - name: log-shipper
    image: busybox
    command: ["sh", "-c", "tail -F /var/log/nginx/access.log"]
    volumeMounts:
    - name: logs
      mountPath: /var/log/nginx

  volumes:
  - name: logs
    emptyDir: {}
```

### 5.4 Init Containers

Init containers run **before** app containers and must complete successfully:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: init-demo
spec:
  # Init containers run first, in order
  initContainers:
  - name: wait-for-db
    image: busybox
    command: ['sh', '-c', 'until nc -z db-service 5432; do echo waiting for db; sleep 2; done']

  - name: init-config
    image: busybox
    command: ['sh', '-c', 'echo "config initialized" > /config/ready']
    volumeMounts:
    - name: config
      mountPath: /config

  # App containers start after all init containers succeed
  containers:
  - name: app
    image: myapp
    volumeMounts:
    - name: config
      mountPath: /config

  volumes:
  - name: config
    emptyDir: {}
```

### 5.5 Init Container Use Cases

| Use Case | Example |
|----------|---------|
| Wait for dependency | Wait for database to be ready |
| Setup configuration | Clone git repo, generate config |
| Database migrations | Run migrations before app starts |
| Register with service | Register instance with external system |
| Download assets | Fetch static files from S3 |

> **Did You Know?**
>
> Init containers have the same spec as regular containers but with different restart behavior. If an init container fails, the pod restarts (unless restartPolicy is Never). Init containers don't support readiness probes since they must complete, not stay running.

---

## Part 6: Pod Networking Basics

### 6.1 Pod Network Model

```
┌────────────────────────────────────────────────────────────────┐
│                     Pod Networking                              │
│                                                                 │
│   Every pod gets a unique IP address                           │
│   Containers in pod share that IP                              │
│   Pods can communicate with all other pods (no NAT)            │
│                                                                 │
│   ┌───────────────────────┐    ┌───────────────────────┐       │
│   │ Pod A (10.244.1.5)    │    │ Pod B (10.244.2.8)    │       │
│   │ ┌─────┐    ┌─────┐    │    │ ┌─────┐              │       │
│   │ │ C1  │    │ C2  │    │    │ │ C1  │              │       │
│   │ │:80  │    │:9090│    │    │ │:8080│              │       │
│   │ └──┬──┘    └──┬──┘    │    │ └──┬──┘              │       │
│   │    │          │       │    │    │                 │       │
│   │    └────┬─────┘       │    │    │                 │       │
│   │         │ localhost   │    │    │                 │       │
│   └─────────┼─────────────┘    └────┼─────────────────┘       │
│             │                       │                          │
│             └───────────────────────┘                          │
│                Can reach each other directly                   │
│                10.244.1.5:80 ←→ 10.244.2.8:8080               │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
```

### 6.2 Container Communication in Pod

```bash
# Containers in same pod communicate via localhost
# Container 1 (nginx on port 80)
# Container 2 can reach it at localhost:80

# Example: curl from sidecar to main app
kubectl exec -it pod-name -c sidecar -- curl localhost:80
```

### 6.3 Finding Pod IPs

```bash
# Get pod IP
kubectl get pod nginx -o wide
# NAME    READY   STATUS    IP           NODE
# nginx   1/1     Running   10.244.1.5   worker-1

# Get IP with jsonpath
kubectl get pod nginx -o jsonpath='{.status.podIP}'

# Get all pod IPs
kubectl get pods -o custom-columns='NAME:.metadata.name,IP:.status.podIP'
```

---

## Part 7: Restart Policies

### 7.1 Restart Policy Options

| Policy | Behavior | Use Case |
|--------|----------|----------|
| `Always` (default) | Restart on any termination | Long-running services |
| `OnFailure` | Restart only on non-zero exit | Jobs that should retry on failure |
| `Never` | Never restart | One-time scripts, debugging |

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: restart-demo
spec:
  restartPolicy: OnFailure   # Only restart if container fails
  containers:
  - name: worker
    image: busybox
    command: ["sh", "-c", "exit 1"]  # Will be restarted
```

### 7.2 Restart Behavior

```bash
# Check restart count
kubectl get pods
# NAME    READY   STATUS    RESTARTS   AGE
# nginx   1/1     Running   3          10m

# Describe shows restart details
kubectl describe pod nginx | grep -A5 "Last State"
```

---

## Common Mistakes

| Mistake | Problem | Solution |
|---------|---------|----------|
| Using `latest` tag | Unpredictable deployments | Always specify version tags |
| No resource limits | Pod can consume all node resources | Always set requests and limits |
| Ignoring logs | Missing root cause | Always check `kubectl logs` |
| Not using `--dry-run` | Slow YAML creation | Generate templates with `--dry-run=client -o yaml` |
| Forgetting `-c` flag | Wrong container in multi-container pod | Specify container with `-c name` |

---

## Quiz

1. **What command generates pod YAML without creating the pod?**
   <details>
   <summary>Answer</summary>
   `kubectl run nginx --image=nginx --dry-run=client -o yaml`

   The `--dry-run=client` flag prevents creation, and `-o yaml` outputs the manifest.
   </details>

2. **A pod is in CrashLoopBackOff. What's the first debugging step?**
   <details>
   <summary>Answer</summary>
   `kubectl logs <pod-name> --previous`

   This shows logs from the previous (crashed) container instance. The container is crashing, so `--previous` captures what happened before the crash.
   </details>

3. **How do containers in the same pod communicate?**
   <details>
   <summary>Answer</summary>
   Via `localhost`. Containers in the same pod share the network namespace, so they can reach each other on localhost using their respective ports.
   </details>

4. **What's the difference between init containers and sidecar containers?**
   <details>
   <summary>Answer</summary>
   **Init containers** run before app containers, must complete successfully, and run sequentially. **Sidecar containers** run alongside the main container for the pod's entire lifecycle.
   </details>

---

## Hands-On Exercise

**Task**: Create and debug a multi-container pod.

**Steps**:

1. **Create a pod with init container and sidecar**:
```bash
cat > multi-container-pod.yaml << 'EOF'
apiVersion: v1
kind: Pod
metadata:
  name: webapp
spec:
  initContainers:
  - name: init-setup
    image: busybox
    command: ['sh', '-c', 'echo "Init complete" > /shared/init-status.txt']
    volumeMounts:
    - name: shared
      mountPath: /shared

  containers:
  - name: web
    image: nginx
    ports:
    - containerPort: 80
    volumeMounts:
    - name: shared
      mountPath: /usr/share/nginx/html
    - name: logs
      mountPath: /var/log/nginx

  - name: log-reader
    image: busybox
    command: ['sh', '-c', 'tail -F /logs/access.log 2>/dev/null || sleep infinity']
    volumeMounts:
    - name: logs
      mountPath: /logs

  volumes:
  - name: shared
    emptyDir: {}
  - name: logs
    emptyDir: {}
EOF

kubectl apply -f multi-container-pod.yaml
```

2. **Watch pod startup**:
```bash
kubectl get pod webapp -w
# Watch init container complete, then main containers start
```

3. **Check init container completed**:
```bash
kubectl describe pod webapp | grep -A10 "Init Containers"
```

4. **Verify shared volume**:
```bash
# Init container created this file
kubectl exec webapp -c web -- cat /usr/share/nginx/html/init-status.txt
```

5. **Access the sidecar container**:
```bash
kubectl exec -it webapp -c log-reader -- /bin/sh
# Inside: ls /logs
exit
```

6. **Generate traffic and see logs**:
```bash
# Get pod IP
POD_IP=$(kubectl get pod webapp -o jsonpath='{.status.podIP}')

# Generate traffic from another pod
kubectl run curl --image=curlimages/curl --rm -it --restart=Never -- curl $POD_IP

# Check sidecar saw the log
kubectl logs webapp -c log-reader
```

7. **Debug with logs**:
```bash
# Logs from specific container
kubectl logs webapp -c web
kubectl logs webapp -c log-reader

# Follow logs
kubectl logs webapp -c web -f
```

8. **Cleanup**:
```bash
kubectl delete pod webapp
rm multi-container-pod.yaml
```

**Success Criteria**:
- [ ] Can create pods with imperative commands
- [ ] Can generate YAML with `--dry-run=client -o yaml`
- [ ] Understand pod lifecycle phases
- [ ] Can debug with logs, exec, describe
- [ ] Can create multi-container pods with init and sidecar

---

## Practice Drills

### Drill 1: Pod Creation Speed Test (Target: 2 minutes)

Create 5 different pods as fast as possible:

```bash
# 1. Basic nginx pod
kubectl run nginx --image=nginx

# 2. Pod with labels
kubectl run labeled --image=nginx --labels="app=web,tier=frontend"

# 3. Pod with port
kubectl run webserver --image=nginx --port=80

# 4. Pod with environment variables
kubectl run envpod --image=nginx --env="ENV=production" --env="DEBUG=false"

# 5. Pod with resource requests
kubectl run limited --image=nginx --requests="cpu=100m,memory=128Mi" --limits="cpu=200m,memory=256Mi"

# Verify all pods
kubectl get pods

# Cleanup
kubectl delete pod nginx labeled webserver envpod limited
```

### Drill 2: YAML Generation (Target: 3 minutes)

Generate and modify YAML:

```bash
# Generate base YAML
kubectl run webapp --image=nginx:1.25 --port=80 --dry-run=client -o yaml > webapp.yaml

# View and verify
cat webapp.yaml

# Apply it
kubectl apply -f webapp.yaml

# Modify: add a label
kubectl label pod webapp tier=frontend

# Verify label
kubectl get pod webapp --show-labels

# Cleanup
kubectl delete -f webapp.yaml
rm webapp.yaml
```

### Drill 3: Pod Debugging Workflow (Target: 5 minutes)

Debug a failing pod:

```bash
# Create a pod that will fail
kubectl run failing --image=nginx --command -- /bin/sh -c "exit 1"

# Check status
kubectl get pod failing
# STATUS: CrashLoopBackOff

# Debug step 1: describe
kubectl describe pod failing | tail -20

# Debug step 2: logs
kubectl logs failing --previous

# Debug step 3: check events
kubectl get events --field-selector involvedObject.name=failing

# Cleanup
kubectl delete pod failing
```

### Drill 4: Multi-Container Pod (Target: 5 minutes)

```bash
# Create pod with sidecar
cat << 'EOF' | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: sidecar-demo
spec:
  containers:
  - name: main
    image: nginx
    volumeMounts:
    - name: shared
      mountPath: /usr/share/nginx/html
  - name: sidecar
    image: busybox
    command: ['sh', '-c', 'while true; do date > /html/index.html; sleep 5; done']
    volumeMounts:
    - name: shared
      mountPath: /html
  volumes:
  - name: shared
    emptyDir: {}
EOF

# Wait for ready
kubectl wait --for=condition=ready pod/sidecar-demo --timeout=60s

# Test - sidecar writes timestamp that nginx serves
kubectl exec sidecar-demo -c main -- cat /usr/share/nginx/html/index.html

# Wait 5 seconds and check again - timestamp should change
sleep 5
kubectl exec sidecar-demo -c main -- cat /usr/share/nginx/html/index.html

# Cleanup
kubectl delete pod sidecar-demo
```

### Drill 5: Init Container (Target: 5 minutes)

```bash
# Create pod with init container
cat << 'EOF' | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: init-demo
spec:
  initContainers:
  - name: init-download
    image: busybox
    command: ['sh', '-c', 'echo "Hello from init" > /work/message.txt']
    volumeMounts:
    - name: workdir
      mountPath: /work
  containers:
  - name: main
    image: busybox
    command: ['sh', '-c', 'cat /work/message.txt && sleep 3600']
    volumeMounts:
    - name: workdir
      mountPath: /work
  volumes:
  - name: workdir
    emptyDir: {}
EOF

# Watch init container complete
kubectl get pod init-demo -w

# Verify init worked
kubectl logs init-demo

# Check init container status
kubectl describe pod init-demo | grep -A5 "Init Containers"

# Cleanup
kubectl delete pod init-demo
```

### Drill 6: Pod Networking (Target: 3 minutes)

```bash
# Create two pods
kubectl run pod-a --image=nginx --port=80
kubectl run pod-b --image=busybox --command -- sleep 3600

# Wait for ready
kubectl wait --for=condition=ready pod/pod-a pod/pod-b --timeout=60s

# Get pod-a IP
POD_A_IP=$(kubectl get pod pod-a -o jsonpath='{.status.podIP}')
echo "Pod A IP: $POD_A_IP"

# From pod-b, reach pod-a
kubectl exec pod-b -- wget -qO- $POD_A_IP

# Cleanup
kubectl delete pod pod-a pod-b
```

### Drill 7: Troubleshooting - ImagePullBackOff (Target: 3 minutes)

```bash
# Create pod with wrong image
kubectl run broken --image=nginx:nonexistent-tag

# Check status
kubectl get pod broken
# STATUS: ImagePullBackOff or ErrImagePull

# Diagnose
kubectl describe pod broken | grep -A10 "Events"

# Fix: update the image
kubectl set image pod/broken broken=nginx:1.25

# Verify fixed
kubectl get pod broken
kubectl wait --for=condition=ready pod/broken --timeout=60s

# Cleanup
kubectl delete pod broken
```

### Drill 8: Challenge - Complete Pod Workflow

Without looking at solutions:

1. Create a pod named `challenge` with nginx:1.25
2. Add labels `app=web` and `env=test`
3. Exec into the pod and create file `/tmp/test.txt` with content "Hello"
4. Get the pod's IP address
5. View the pod's logs
6. Delete the pod

```bash
# YOUR TASK: Complete in under 3 minutes
```

<details>
<summary>Solution</summary>

```bash
# 1. Create pod with labels
kubectl run challenge --image=nginx:1.25 --labels="app=web,env=test"

# 2. Wait for ready
kubectl wait --for=condition=ready pod/challenge --timeout=60s

# 3. Create file inside pod
kubectl exec challenge -- sh -c 'echo "Hello" > /tmp/test.txt'

# 4. Verify file
kubectl exec challenge -- cat /tmp/test.txt

# 5. Get IP
kubectl get pod challenge -o jsonpath='{.status.podIP}'

# 6. View logs
kubectl logs challenge

# 7. Delete
kubectl delete pod challenge
```

</details>

---

## Next Module

[Module 2.2: Deployments & ReplicaSets](../module-2.2-deployments/) - Rolling updates, rollbacks, and scaling.
