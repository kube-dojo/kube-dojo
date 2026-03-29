---
title: "Module 1.7: Namespaces and Labels"
slug: prerequisites/kubernetes-basics/module-1.7-namespaces-labels/
sidebar:
  order: 8
---
> **Complexity**: `[QUICK]` - Organizational concepts
>
> **Time to Complete**: 25-30 minutes
>
> **Prerequisites**: Module 3 (Pods), Module 4 (Deployments)

---

## Why This Module Matters

As clusters grow, organization becomes critical. Namespaces provide isolation and scope. Labels enable selection and organization. Together, they keep large clusters manageable.

---

## Namespaces

### What Are Namespaces?

Namespaces are virtual clusters within a cluster:

```
┌─────────────────────────────────────────────────────────────┐
│              KUBERNETES CLUSTER                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────────┐  ┌──────────────────┐               │
│  │    Namespace:    │  │    Namespace:    │               │
│  │    "frontend"    │  │    "backend"     │               │
│  │  ┌────┐ ┌────┐   │  │  ┌────┐ ┌────┐   │               │
│  │  │web │ │api │   │  │  │db  │ │cache│  │               │
│  │  └────┘ └────┘   │  │  └────┘ └────┘   │               │
│  │                  │  │                  │               │
│  │  Isolated from   │  │  Isolated from   │               │
│  │  other namespaces│  │  other namespaces│               │
│  └──────────────────┘  └──────────────────┘               │
│                                                             │
│  ┌──────────────────┐                                      │
│  │    Namespace:    │  Default namespaces:                 │
│  │   "kube-system"  │  • default                          │
│  │  System pods     │  • kube-system                       │
│  └──────────────────┘  • kube-public                       │
│                        • kube-node-lease                   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Creating Namespaces

```bash
# Create namespace
kubectl create namespace my-app
kubectl create ns my-app          # Short form

# View namespaces
kubectl get namespaces
kubectl get ns
```

```yaml
# namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: my-app
  labels:
    team: backend
```

### Working with Namespaces

```bash
# Run command in specific namespace
kubectl get pods -n my-app
kubectl get pods --namespace=my-app

# All namespaces
kubectl get pods -A
kubectl get pods --all-namespaces

# Set default namespace for context
kubectl config set-context --current --namespace=my-app

# Check current default
kubectl config view --minify | grep namespace
```

### Default Namespaces

| Namespace | Purpose |
|-----------|---------|
| `default` | Where resources go if no namespace specified |
| `kube-system` | System components (API server, scheduler, etc.) |
| `kube-public` | Publicly accessible data |
| `kube-node-lease` | Node heartbeat data |

---

## Labels

### What Are Labels?

Labels are key-value pairs attached to resources:

```yaml
metadata:
  name: my-pod
  labels:
    app: nginx
    environment: production
    team: frontend
    version: v1.2.3
```

### Using Labels

```bash
# Add labels when creating
kubectl run nginx --image=nginx --labels="app=nginx,env=prod"

# Add labels to existing resource
kubectl label pod nginx tier=frontend

# Remove label
kubectl label pod nginx tier-

# Update label (overwrite)
kubectl label pod nginx env=staging --overwrite
```

### Selecting by Labels

```bash
# Filter by single label
kubectl get pods -l app=nginx
kubectl get pods --selector=app=nginx

# Multiple labels (AND)
kubectl get pods -l app=nginx,env=prod

# Set-based selectors
kubectl get pods -l 'env in (prod, staging)'
kubectl get pods -l 'app notin (test)'
kubectl get pods -l 'tier'              # Has label
kubectl get pods -l '!tier'             # Doesn't have label

# Show labels
kubectl get pods --show-labels
```

---

## Labels in Action

```
┌─────────────────────────────────────────────────────────────┐
│              LABEL SELECTION                                │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Service selector:        Pods:                            │
│  ┌──────────────────┐    ┌──────────────────┐             │
│  │ selector:        │    │ labels:          │             │
│  │   app: nginx     │───►│   app: nginx     │  ✓ Match   │
│  │   tier: frontend │    │   tier: frontend │             │
│  └──────────────────┘    └──────────────────┘             │
│                          ┌──────────────────┐             │
│                          │ labels:          │             │
│                      ╳   │   app: nginx     │  ✗ No tier │
│                          │                  │             │
│                          └──────────────────┘             │
│                          ┌──────────────────┐             │
│                          │ labels:          │             │
│                      ╳   │   app: redis     │  ✗ Wrong   │
│                          │   tier: frontend │     app    │
│                          └──────────────────┘             │
│                                                             │
│  Service only routes to pods matching ALL selector labels  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Labels vs Annotations

| Labels | Annotations |
|--------|-------------|
| Used for selection | Used for metadata |
| Key/value restrictions | Can store larger data |
| Used by K8s internally | For humans and tools |
| Limited characters | Nearly unlimited content |

```yaml
metadata:
  labels:                    # For selection
    app: nginx
    version: v1
  annotations:               # For metadata
    description: "Main web server"
    git-commit: "abc123"
    monitoring.enabled: "true"
```

---

## Best Practices

### Recommended Labels

```yaml
metadata:
  labels:
    app.kubernetes.io/name: nginx
    app.kubernetes.io/version: "1.25"
    app.kubernetes.io/component: frontend
    app.kubernetes.io/part-of: website
    app.kubernetes.io/managed-by: helm
```

### Namespace Strategy

```
Development environments:
  - dev
  - staging
  - prod

Team-based:
  - team-frontend
  - team-backend
  - team-data

Application-based:
  - app-website
  - app-api
  - app-admin
```

---

## Did You Know?

- **Some resources are not namespaced.** Nodes, PersistentVolumes, and Namespaces themselves are cluster-scoped.

- **Labels have constraints.** Keys and values have character limits and format requirements.

- **Namespaces don't provide security by default.** Pods in different namespaces can communicate unless NetworkPolicies restrict it.

- **The `default` namespace is a trap.** Use explicit namespaces to avoid mixing unrelated resources.

---

## Quiz

1. **What's the difference between labels and annotations?**
   <details>
   <summary>Answer</summary>
   Labels are for selection (used by Services, Deployments, etc.) and have format restrictions. Annotations are for arbitrary metadata (used by humans and tools) and can store larger data.
   </details>

2. **How do you see pods in all namespaces?**
   <details>
   <summary>Answer</summary>
   `kubectl get pods -A` or `kubectl get pods --all-namespaces`
   </details>

3. **How do you select pods with label app=nginx AND env=prod?**
   <details>
   <summary>Answer</summary>
   `kubectl get pods -l app=nginx,env=prod` (comma-separated labels are AND)
   </details>

4. **Are namespaces security boundaries?**
   <details>
   <summary>Answer</summary>
   Not by default. Pods can communicate across namespaces unless NetworkPolicies restrict it. Namespaces are organizational boundaries, not security boundaries, without additional configuration.
   </details>

---

## Hands-On Exercise

**Task**: Practice namespaces and labels.

```bash
# 1. Create namespaces
kubectl create namespace frontend
kubectl create namespace backend

# 2. Create pods with labels in different namespaces
kubectl run web --image=nginx -n frontend --labels="app=web,tier=frontend"
kubectl run api --image=nginx -n backend --labels="app=api,tier=backend"
kubectl run cache --image=redis -n backend --labels="app=cache,tier=backend"

# 3. List all pods
kubectl get pods -A

# 4. Filter by label
kubectl get pods -A -l tier=backend

# 5. Show labels
kubectl get pods -A --show-labels

# 6. Add label to existing pod
kubectl label pod web -n frontend version=v1

# 7. Set default namespace
kubectl config set-context --current --namespace=frontend
kubectl get pods  # Now shows frontend by default

# 8. Reset to default
kubectl config set-context --current --namespace=default

# 9. Cleanup
kubectl delete namespace frontend backend
```

**Success criteria**: Can filter pods by namespace and labels.

---

## Summary

**Namespaces**:
- Virtual clusters within a cluster
- Provide scope and organization
- Not security boundaries by default
- Use `-n namespace` or `-A` for all

**Labels**:
- Key-value pairs on resources
- Enable selection (Services, Deployments)
- Use `-l key=value` to filter
- Comma separates AND conditions

**Best practices**:
- Use meaningful namespace names
- Adopt consistent labeling conventions
- Never work in `default` for real workloads

---

## Next Module

[Module 8: YAML for Kubernetes](module-1.8-yaml-kubernetes/) - Writing and understanding K8s manifests.
