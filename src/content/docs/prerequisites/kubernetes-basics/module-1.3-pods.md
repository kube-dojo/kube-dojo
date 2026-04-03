---
title: "Module 1.3: Pods - The Atomic Unit"
slug: prerequisites/kubernetes-basics/module-1.3-pods
sidebar:
  order: 4
lab:
  id: "prereq-k8s-1.3-pods"
  url: "https://killercoda.com/kubedojo/scenario/prereq-k8s-1.3-pods"
  duration: "25 min"
  difficulty: "beginner"
  environment: "kubernetes"
---
> **Complexity**: `[MEDIUM]` - Core concept, hands-on required
>
> **Time to Complete**: 40-45 minutes
>
> **Prerequisites**: Module 2 (kubectl Basics)

---

## Why This Module Matters

Pods are the smallest deployable unit in Kubernetes. Every container you run in K8s runs inside a Pod. Understanding Pods is fundamental—everything else builds on this concept.

---

## What Is a Pod?

A Pod is a wrapper around one or more containers:

```
┌─────────────────────────────────────────────────────────────┐
│                          POD                                │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                    Pod                               │   │
│  │  ┌─────────────┐     ┌─────────────┐               │   │
│  │  │  Container  │     │  Container  │  (optional)   │   │
│  │  │  (main app) │     │  (sidecar)  │               │   │
│  │  └─────────────┘     └─────────────┘               │   │
│  │                                                     │   │
│  │  Shared:                                           │   │
│  │  • Network namespace (same IP, localhost works)    │   │
│  │  • Storage volumes                                  │   │
│  │  • Pod lifecycle                                   │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  Containers in a Pod:                                      │
│  - Share the same IP address                               │
│  - Can communicate via localhost                           │
│  - Share mounted volumes                                   │
│  - Are scheduled together on the same node                 │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Key Points

- **One container per Pod is typical.** Multi-container Pods are for specific patterns (sidecars, adapters).
- **Pods are ephemeral.** They can be killed and replaced at any time.
- **Pods get a unique IP address.** Other Pods can reach them at this IP.
- **Pods don't self-heal.** If a Pod dies, it stays dead (unless managed by a controller).

---

## Creating Pods

### Imperative (Quick Testing)

```bash
# Simple pod
kubectl run nginx --image=nginx

# With port
kubectl run nginx --image=nginx --port=80

# With labels
kubectl run nginx --image=nginx --labels="app=web,tier=frontend"

# Dry run to see YAML
kubectl run nginx --image=nginx --dry-run=client -o yaml
```

### Declarative (Production Way)

```yaml
# pod.yaml
apiVersion: v1
kind: Pod
metadata:
  name: nginx
  labels:
    app: nginx
spec:
  containers:
  - name: nginx
    image: nginx:1.25
    ports:
    - containerPort: 80
```

```bash
kubectl apply -f pod.yaml
```

---

## Pod YAML Structure

```yaml
apiVersion: v1          # API version
kind: Pod               # Resource type
metadata:               # Metadata
  name: nginx           # Pod name (required)
  namespace: default    # Namespace (optional, defaults to current)
  labels:               # Key-value pairs for selection
    app: nginx
    environment: dev
  annotations:          # Non-identifying metadata
    description: "My nginx pod"
spec:                   # Desired state
  containers:           # List of containers
  - name: nginx         # Container name
    image: nginx:1.25   # Container image
    ports:              # Exposed ports
    - containerPort: 80
    env:                # Environment variables
    - name: MY_VAR
      value: "my-value"
    resources:          # Resource requests/limits
      requests:
        memory: "64Mi"
        cpu: "250m"
      limits:
        memory: "128Mi"
        cpu: "500m"
```

---

## Pod Lifecycle

```
┌─────────────────────────────────────────────────────────────┐
│              POD LIFECYCLE STATES                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Pending ──► Running ──► Succeeded/Failed                  │
│     │           │                                           │
│     │           ▼                                           │
│     │       Unknown (node lost contact)                    │
│     │                                                       │
│     ▼                                                       │
│  Failed (image pull error, etc.)                           │
│                                                             │
│  STATES:                                                   │
│  • Pending    - Waiting to be scheduled or pulling image  │
│  • Running    - At least one container running             │
│  • Succeeded  - All containers completed successfully      │
│  • Failed     - At least one container failed             │
│  • Unknown    - Cannot determine state (node issues)      │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Container States

```bash
kubectl get pod nginx -o jsonpath='{.status.containerStatuses[0].state}'
```

- **Waiting**: Container not yet running (pulling image, etc.)
- **Running**: Container executing
- **Terminated**: Container finished (success or failure)

---

## Common Pod Operations

### View Pods

```bash
# List pods
kubectl get pods
kubectl get pods -o wide          # More info (IP, node)
kubectl get pods --show-labels    # Show labels

# Detailed info
kubectl describe pod nginx

# Watch pod status
kubectl get pods -w
```

### Debug Pods

```bash
# View logs
kubectl logs nginx
kubectl logs nginx -f             # Follow
kubectl logs nginx --previous     # Previous container instance

# Execute commands
kubectl exec nginx -- ls /
kubectl exec -it nginx -- bash    # Interactive shell

# Get events
kubectl get events --field-selector involvedObject.name=nginx
```

### Access Pods

```bash
# Port forward
kubectl port-forward pod/nginx 8080:80
# Now access at localhost:8080

# Get pod IP
kubectl get pod nginx -o jsonpath='{.status.podIP}'
```

### Modify Pods

```bash
# Edit (limited for pods)
kubectl edit pod nginx

# Delete and recreate
kubectl delete pod nginx
kubectl apply -f pod.yaml

# Force delete stuck pod
kubectl delete pod nginx --force --grace-period=0
```

---

## Environment Variables

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: env-demo
spec:
  containers:
  - name: demo
    image: busybox
    command: ['sh', '-c', 'echo $GREETING $NAME && sleep 3600']
    env:
    - name: GREETING
      value: "Hello"
    - name: NAME
      value: "Kubernetes"
```

```bash
kubectl apply -f env-demo.yaml
kubectl logs env-demo
# Output: Hello Kubernetes
```

---

## Resource Requests and Limits

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: resource-demo
spec:
  containers:
  - name: demo
    image: nginx
    resources:
      requests:          # Minimum guaranteed
        memory: "64Mi"
        cpu: "250m"      # 0.25 CPU cores
      limits:            # Maximum allowed
        memory: "128Mi"
        cpu: "500m"
```

```
┌─────────────────────────────────────────────────────────────┐
│              REQUESTS vs LIMITS                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  REQUEST = Minimum guaranteed resources                     │
│  - Used for scheduling decisions                           │
│  - Pod won't be scheduled unless node has this available   │
│                                                             │
│  LIMIT = Maximum allowed resources                          │
│  - Container can use up to this amount                     │
│  - CPU: throttled if exceeded                              │
│  - Memory: OOMKilled if exceeded                           │
│                                                             │
│  Example:                                                   │
│  requests:                                                  │
│    cpu: "250m"     # 0.25 cores guaranteed                 │
│    memory: "64Mi"  # 64 MB guaranteed                      │
│  limits:                                                    │
│    cpu: "500m"     # Can burst to 0.5 cores               │
│    memory: "128Mi" # Killed if exceeds 128 MB              │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Did You Know?

- **Pod IPs are cluster-internal.** You can't access a Pod IP from outside the cluster directly.

- **Pods are cattle, not pets.** They're designed to be replaceable. Never rely on a specific Pod existing.

- **localhost works between containers in a Pod.** They share the network namespace.

- **A Pod without a controller is "naked."** If it dies, nothing recreates it. Always use Deployments in production.

---

## Common Mistakes

| Mistake | Why It Hurts | Solution |
|---------|--------------|----------|
| Using Pods directly | No self-healing or scaling | Use Deployments |
| No resource limits | Can starve other pods | Always set resources |
| Using :latest tag | Unpredictable versions | Use specific tags |
| Ignoring pod status | Miss failures | Check `kubectl get pods` |

---

## Quiz

1. **What is a Pod?**
   <details>
   <summary>Answer</summary>
   A Pod is the smallest deployable unit in Kubernetes—a wrapper around one or more containers that share network and storage. Containers in a Pod share an IP address and can communicate via localhost.
   </details>

2. **Why shouldn't you use naked Pods in production?**
   <details>
   <summary>Answer</summary>
   Naked Pods don't self-heal. If a Pod dies or a node fails, the Pod is gone. Use Deployments or other controllers that automatically recreate failed Pods.
   </details>

3. **What's the difference between resource requests and limits?**
   <details>
   <summary>Answer</summary>
   Requests are guaranteed minimum resources (used for scheduling). Limits are maximums (enforced at runtime). CPU over limit = throttled. Memory over limit = OOMKilled.
   </details>

4. **How do containers in the same Pod communicate?**
   <details>
   <summary>Answer</summary>
   Via localhost. Containers in a Pod share the same network namespace, so they can use localhost or 127.0.0.1 with different ports.
   </details>

---

## Hands-On Exercise

**Task**: Create, inspect, and debug a Pod.

```bash
# 1. Create pod YAML
cat << 'EOF' > my-pod.yaml
apiVersion: v1
kind: Pod
metadata:
  name: my-pod
  labels:
    app: demo
spec:
  containers:
  - name: demo
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
EOF

# 2. Create the pod
kubectl apply -f my-pod.yaml

# 3. Watch it start
kubectl get pods -w

# 4. Get detailed info
kubectl describe pod my-pod

# 5. View logs
kubectl logs my-pod

# 6. Execute command in pod
kubectl exec my-pod -- nginx -v

# 7. Port forward and test
kubectl port-forward pod/my-pod 8080:80 &
curl localhost:8080
kill %1  # Stop port-forward

# 8. Cleanup
kubectl delete -f my-pod.yaml
rm my-pod.yaml
```

**Success criteria**: Pod runs, logs visible, port-forward works.

---

## Summary

Pods are the foundation:

**What they are**:
- Smallest deployable unit
- Wrapper around containers
- Shared network and storage

**Key operations**:
- `kubectl run` / `kubectl apply -f`
- `kubectl get pods`
- `kubectl describe pod`
- `kubectl logs`
- `kubectl exec`

**Best practices**:
- Use controllers (Deployments), not naked Pods
- Set resource requests and limits
- Use specific image tags

---

## Next Module

[Module 1.4: Deployments](../module-1.4-deployments/) - Managing applications at scale.
