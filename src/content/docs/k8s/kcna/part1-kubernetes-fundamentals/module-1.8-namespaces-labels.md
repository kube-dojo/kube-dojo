---
title: "Module 1.8: Namespaces and Labels"
slug: k8s/kcna/part1-kubernetes-fundamentals/module-1.8-namespaces-labels
sidebar:
  order: 9
---
> **Complexity**: `[QUICK]` - Organization concepts
>
> **Time to Complete**: 20-25 minutes
>
> **Prerequisites**: Modules 1.5-1.7

---

## What You'll Be Able to Do

After completing this module, you will be able to:

1. **Explain** how namespaces provide logical isolation and resource organization
2. **Identify** when to use namespaces vs. labels vs. annotations for different purposes
3. **Compare** namespace-scoped and cluster-scoped resources
4. **Evaluate** label selector expressions used by Services, Deployments, and NetworkPolicies

---

## Why This Module Matters

Namespaces and labels are how Kubernetes organizes resources. Labels enable Services to find Pods, Deployments to manage ReplicaSets, and operators to select resources. KCNA tests your understanding of these organizational primitives.

---

## Namespaces

### What is a Namespace?

A **namespace** is a way to divide cluster resources between multiple users or teams:

```
┌─────────────────────────────────────────────────────────────┐
│              NAMESPACES                                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                   CLUSTER                            │   │
│  │                                                      │   │
│  │  ┌─────────────────────────────────────────────┐    │   │
│  │  │  Namespace: production                       │    │   │
│  │  │  ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐          │    │   │
│  │  │  │ Pod │ │ Svc │ │ Dep │ │ CM  │          │    │   │
│  │  │  └─────┘ └─────┘ └─────┘ └─────┘          │    │   │
│  │  └─────────────────────────────────────────────┘    │   │
│  │                                                      │   │
│  │  ┌─────────────────────────────────────────────┐    │   │
│  │  │  Namespace: staging                          │    │   │
│  │  │  ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐          │    │   │
│  │  │  │ Pod │ │ Svc │ │ Dep │ │ CM  │          │    │   │
│  │  │  └─────┘ └─────┘ └─────┘ └─────┘          │    │   │
│  │  └─────────────────────────────────────────────┘    │   │
│  │                                                      │   │
│  │  ┌─────────────────────────────────────────────┐    │   │
│  │  │  Namespace: development                      │    │   │
│  │  │  ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐          │    │   │
│  │  │  │ Pod │ │ Svc │ │ Dep │ │ CM  │          │    │   │
│  │  │  └─────┘ └─────┘ └─────┘ └─────┘          │    │   │
│  │  └─────────────────────────────────────────────┘    │   │
│  │                                                      │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Default Namespaces

Every cluster has these built-in namespaces:

| Namespace | Purpose |
|-----------|---------|
| **default** | Default namespace for resources without namespace |
| **kube-system** | Kubernetes system components (API server, etc.) |
| **kube-public** | Publicly readable resources (rarely used) |
| **kube-node-lease** | Node heartbeat leases |

### What Namespaces Provide

```
┌─────────────────────────────────────────────────────────────┐
│              NAMESPACE BENEFITS                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. NAME SCOPING                                           │
│     • Same resource name in different namespaces: OK       │
│     • "backend" in production ≠ "backend" in staging      │
│                                                             │
│  2. ACCESS CONTROL                                         │
│     • RBAC can be namespace-scoped                         │
│     • "Team A can only access namespace-a"                 │
│                                                             │
│  3. RESOURCE QUOTAS                                        │
│     • Limit CPU/memory per namespace                       │
│     • Prevent one team from using all resources           │
│                                                             │
│  4. ORGANIZATION                                           │
│     • Logical separation of applications                   │
│     • Environments (dev/staging/prod)                     │
│     • Teams (team-a, team-b)                              │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### What's NOT Namespaced

Some resources are **cluster-scoped** (exist across all namespaces):

| Cluster-Scoped | Why |
|----------------|-----|
| **Nodes** | Physical/virtual machines |
| **PersistentVolumes** | Storage is cluster-wide |
| **Namespaces** | They contain other resources |
| **ClusterRoles** | Cluster-wide permissions |
| **StorageClasses** | Storage configurations |

---

## Labels

### What are Labels?

**Labels** are key-value pairs attached to resources for identification:

```
┌─────────────────────────────────────────────────────────────┐
│              LABELS                                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Labels are arbitrary metadata:                            │
│                                                             │
│  metadata:                                                 │
│    labels:                                                 │
│      app: frontend                                         │
│      environment: production                               │
│      team: platform                                        │
│      version: v2.1.0                                       │
│                                                             │
│  Labels can be:                                            │
│  • Any key-value pair                                      │
│  • Multiple labels per resource                            │
│  • Used for selection                                      │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### How Labels are Used

```
┌─────────────────────────────────────────────────────────────┐
│              LABEL SELECTORS                                │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Service selecting Pods:                                   │
│  ─────────────────────────────────────────────────────────  │
│                                                             │
│  Service:                   Pods:                          │
│  selector:                  ┌─────────────────────┐        │
│    app: web                 │ labels:             │ ✓ Match│
│                             │   app: web          │        │
│                             │   env: prod         │        │
│                             └─────────────────────┘        │
│                             ┌─────────────────────┐        │
│                             │ labels:             │ ✓ Match│
│                             │   app: web          │        │
│                             │   env: staging      │        │
│                             └─────────────────────┘        │
│                             ┌─────────────────────┐        │
│                             │ labels:             │ ✗ No   │
│                             │   app: api          │        │
│                             │   env: prod         │        │
│                             └─────────────────────┘        │
│                                                             │
│  Only Pods with "app: web" are selected                   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Label Selector Types

```
┌─────────────────────────────────────────────────────────────┐
│              SELECTOR TYPES                                 │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  EQUALITY-BASED:                                           │
│  ─────────────────────────────────────────────────────────  │
│  selector:                                                 │
│    app: frontend        # app equals frontend              │
│                                                             │
│  Or using matchLabels:                                     │
│  selector:                                                 │
│    matchLabels:                                            │
│      app: frontend                                         │
│      env: production                                       │
│                                                             │
│  SET-BASED (more powerful):                                │
│  ─────────────────────────────────────────────────────────  │
│  selector:                                                 │
│    matchExpressions:                                       │
│    - key: app                                              │
│      operator: In                                          │
│      values: [frontend, backend]                          │
│    - key: env                                              │
│      operator: NotIn                                       │
│      values: [development]                                │
│                                                             │
│  Operators: In, NotIn, Exists, DoesNotExist               │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Annotations

### Labels vs Annotations

```
┌─────────────────────────────────────────────────────────────┐
│              LABELS vs ANNOTATIONS                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  LABELS:                       ANNOTATIONS:                │
│  ─────────────────────────────────────────────────────────  │
│  • For identification          • For metadata              │
│  • Used in selectors           • NOT used in selectors     │
│  • Short values                • Can be longer             │
│  • Meaningful to K8s           • For tools/humans          │
│                                                             │
│  Label example:                Annotation example:         │
│  labels:                       annotations:                │
│    app: frontend                 description: "Main web UI"│
│    version: v2                   git-commit: "abc123..."   │
│                                  contact: "team@example.com"│
│                                                             │
│  Use labels for:               Use annotations for:        │
│  • Selection                   • Build info                │
│  • Organization                • Contact info              │
│  • Grouping                    • Configuration hints       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Common Label Conventions

Kubernetes recommends these standard labels:

| Label | Purpose | Example |
|-------|---------|---------|
| `app.kubernetes.io/name` | Application name | `mysql` |
| `app.kubernetes.io/instance` | Instance name | `mysql-prod` |
| `app.kubernetes.io/version` | Version | `5.7.21` |
| `app.kubernetes.io/component` | Component | `database` |
| `app.kubernetes.io/part-of` | Higher-level app | `wordpress` |
| `app.kubernetes.io/managed-by` | Managing tool | `helm` |

---

## How Services, Deployments Use Labels

```
┌─────────────────────────────────────────────────────────────┐
│              LABELS IN ACTION                               │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Deployment:                                               │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  name: frontend                                      │   │
│  │  selector:                                           │   │
│  │    matchLabels:                                      │   │
│  │      app: frontend    ─────────┐                    │   │
│  │  template:                      │                    │   │
│  │    metadata:                    │                    │   │
│  │      labels:                    │ Must match!       │   │
│  │        app: frontend  ←────────┘                    │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  Service:                                                  │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  name: frontend-service                              │   │
│  │  selector:                                           │   │
│  │    app: frontend      → Finds Pods with this label  │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  The chain:                                                │
│  Deployment.selector → Pod template labels                │
│  Service.selector → Pod labels                            │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Did You Know?

- **Namespaces don't provide network isolation** - By default, Pods in different namespaces can communicate. Use NetworkPolicies for isolation.

- **Labels have length limits** - Keys can be up to 63 characters (253 with prefix). Values up to 63 characters.

- **You can query by labels** - `kubectl get pods -l app=frontend,env=prod` shows pods matching both labels.

- **Namespace names are DNS subdomains** - They must be lowercase, alphanumeric, with hyphens allowed.

---

## Common Mistakes

| Mistake | Why It Hurts | Correct Understanding |
|---------|--------------|----------------------|
| Thinking namespaces isolate network | Security risk | Use NetworkPolicies for isolation |
| Label key typos | Selectors don't match | Double-check label names |
| Too few labels | Hard to organize/select | Use consistent labeling scheme |
| Labels for long metadata | Wrong tool | Use annotations for descriptions |

---

## Quiz

1. **What are the default namespaces in Kubernetes?**
   <details>
   <summary>Answer</summary>
   `default`, `kube-system`, `kube-public`, and `kube-node-lease`.
   </details>

2. **Are Nodes namespace-scoped or cluster-scoped?**
   <details>
   <summary>Answer</summary>
   Cluster-scoped. Nodes exist across all namespaces because they're physical/virtual machines that the whole cluster uses.
   </details>

3. **How does a Service find its Pods?**
   <details>
   <summary>Answer</summary>
   Using label selectors. The Service's `selector` field specifies labels, and any Pod with matching labels becomes an endpoint.
   </details>

4. **What's the difference between labels and annotations?**
   <details>
   <summary>Answer</summary>
   Labels are for identification and selection (used by Kubernetes). Annotations are for arbitrary metadata (used by tools and humans). You can't select by annotations.
   </details>

5. **Can two Pods have the same name in different namespaces?**
   <details>
   <summary>Answer</summary>
   Yes. Namespaces provide name scoping. `frontend` in namespace `prod` is different from `frontend` in namespace `dev`.
   </details>

---

## Summary

**Namespaces**:
- Divide cluster resources
- Provide name scoping
- Enable RBAC and quotas
- Don't isolate network (use NetworkPolicies)

**Labels**:
- Key-value pairs for identification
- Used by selectors (Services, Deployments)
- Enable organization and selection

**Annotations**:
- Key-value pairs for metadata
- NOT used for selection
- For tools, humans, longer descriptions

**Common patterns**:
- `app`, `environment`, `version` labels
- Namespaces per team or environment
- Consistent labeling across resources

---

## Part 1 Complete!

You've finished **Kubernetes Fundamentals** (46% of the exam). You now understand:
- What Kubernetes is and why it exists
- Containers and how they work
- Control plane and node components
- Pods, Deployments, ReplicaSets
- Services and discovery
- Namespaces and labels

**Next Part**: [Part 2: Container Orchestration](../part2-container-orchestration/module-2.1-scheduling/) - How Kubernetes manages workloads at scale.
