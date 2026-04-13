---
title: "Module 4.6: Custom Resource Definitions (CRDs)"
slug: k8s/ckad/part4-environment/module-4.6-crds
sidebar:
  order: 6
lab:
  id: ckad-4.6-crds
  url: https://killercoda.com/kubedojo/scenario/ckad-4.6-crds
  duration: "40 min"
  difficulty: advanced
  environment: kubernetes
---
> **Complexity**: `[MEDIUM]` - New to CKAD 2025, conceptual understanding important
>
> **Time to Complete**: 35-45 minutes
>
> **Prerequisites**: Understanding of Kubernetes resources and API structure

---

## Learning Outcomes

After completing this module, you will be able to:
- **Create** a CustomResourceDefinition with proper schema validation and versioning
- **Explain** how CRDs extend the Kubernetes API and how controllers reconcile custom resources
- **Deploy** custom resources and interact with them using standard kubectl commands
- **Debug** CRD validation errors and understand the relationship between CRDs and operators

---

## Why This Module Matters

Custom Resource Definitions extend Kubernetes with your own resource types. Instead of only working with Pods, Services, and Deployments, you can define resources like `Database`, `Certificate`, or `BackupJob` that make sense for your domain.

The CKAD exam (2025) tests:
- Understanding what CRDs are
- Working with custom resources
- Using `kubectl` to interact with CRs
- Recognizing Operator patterns

> **The Custom Forms Analogy**
>
> Kubernetes built-in resources are like standard government forms—everyone uses the same Pod form, the same Service form. CRDs are like creating your own custom form for your organization. You define what fields it has (`spec`), and Kubernetes stores and validates it. Operators are like automated clerks that watch for these forms and take action when they're submitted.

---

## CRD Basics

### What is a CRD?

A **Custom Resource Definition (CRD)** tells Kubernetes about a new resource type:

```yaml
apiVersion: apiextensions.k8s.io/v1
kind: CustomResourceDefinition
metadata:
  name: databases.example.com    # plural.group format
spec:
  group: example.com
  versions:
  - name: v1
    served: true
    storage: true
    schema:
      openAPIV3Schema:
        type: object
        properties:
          spec:
            type: object
            properties:
              engine:
                type: string
              size:
                type: string
  scope: Namespaced
  names:
    plural: databases
    singular: database
    kind: Database
    shortNames:
    - db
```

> **Pause and predict**: You see `kubectl get certificates` being used in a cluster. Is `Certificate` a built-in Kubernetes resource? How would you find out whether it's a CRD?

### What is a Custom Resource (CR)?

Once the CRD exists, you can create instances—Custom Resources:

```yaml
apiVersion: example.com/v1
kind: Database
metadata:
  name: my-database
spec:
  engine: postgres
  size: large
```

---

## CRD Components

### Names

```yaml
names:
  plural: databases      # Used in URLs: /apis/example.com/v1/databases
  singular: database     # Used in CLI: kubectl get database
  kind: Database         # Used in YAML: kind: Database
  shortNames:
  - db                   # Shortcuts: kubectl get db
```

### Scope

```yaml
scope: Namespaced    # Resources exist in namespaces
# or
scope: Cluster       # Resources are cluster-wide
```

### Versions

```yaml
versions:
- name: v1
  served: true       # API server serves this version
  storage: true      # Store in etcd using this version (only one can be true)
```

### Schema Validation

```yaml
schema:
  openAPIV3Schema:
    type: object
    required: ["spec"]
    properties:
      spec:
        type: object
        required: ["engine"]
        properties:
          engine:
            type: string
            enum: ["postgres", "mysql", "mongodb"]
          size:
            type: string
            default: "small"
```

---

## Working with CRDs

### View Installed CRDs

```bash
# List all CRDs
k get crd

# Describe a CRD
k describe crd certificates.cert-manager.io

# Get CRD YAML
k get crd mycrd.example.com -o yaml
```

### Working with Custom Resources

```bash
# List custom resources (once CRD exists)
k get databases
k get db                    # Using shortName

# Describe a CR
k describe database my-database

# Get CR YAML
k get database my-database -o yaml

# Delete a CR
k delete database my-database
```

### Understanding Schema Validation Errors

One of the main benefits of CRDs is that the Kubernetes API server validates the custom resources before accepting them. If a user tries to create a CR that doesn't match the `openAPIV3Schema` defined in the CRD, the API server rejects it immediately.

For example, if our `Database` CRD requires `engine` to be one of `["postgres", "mysql", "mongodb"]`, and you apply this YAML:

```yaml
apiVersion: example.com/v1
kind: Database
metadata:
  name: my-database
spec:
  engine: redis
  size: large
```

The API server will reject it with a descriptive error:

```bash
$ kubectl apply -f bad-db.yaml
The Database "my-database" is invalid: spec.engine: Unsupported value: "redis": supported values: "postgres", "mysql", "mongodb"
```

> **Stop and think**: If a CRD does not define an `openAPIV3Schema`, what happens when you submit a CR with misspelled fields like `engin: postgres`? The API server will accept it blindly, but the operator watching the CR might fail to process it, making debugging much harder! Strict schema validation prevents this.

---

## Common CRDs You'll Encounter

### cert-manager

```bash
k get crd | grep cert-manager
# certificates.cert-manager.io
# clusterissuers.cert-manager.io
# issuers.cert-manager.io

# Create a Certificate
k get certificates
k describe certificate my-cert
```

### Prometheus Operator

```bash
k get crd | grep monitoring
# servicemonitors.monitoring.coreos.com
# prometheusrules.monitoring.coreos.com
```

### Gateway API

```bash
k get crd | grep gateway
# gateways.gateway.networking.k8s.io
# httproutes.gateway.networking.k8s.io
```

---

## Operators Pattern

### What is an Operator?

An **Operator** = CRD + Controller

- **CRD**: Defines the "what" (custom resource structure)
- **Controller**: Handles the "how" (watches CRs and takes action)

```
┌─────────────────────────────────────────────────────────────┐
│                    Operator Pattern                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. User Creates Custom Resource                            │
│  ┌─────────────────────────────────┐                       │
│  │ apiVersion: example.com/v1      │                       │
│  │ kind: Database                  │                       │
│  │ spec:                           │                       │
│  │   engine: postgres              │                       │
│  └─────────────────────────────────┘                       │
│                    │                                        │
│                    ▼                                        │
│  2. Controller Watches for Database CRs                    │
│  ┌─────────────────────────────────┐                       │
│  │ Operator Pod                    │                       │
│  │ - Sees new Database CR          │                       │
│  │ - Creates StatefulSet           │                       │
│  │ - Creates Service               │                       │
│  │ - Creates Secret (password)     │                       │
│  │ - Updates CR status             │                       │
│  └─────────────────────────────────┘                       │
│                    │                                        │
│                    ▼                                        │
│  3. Actual Resources Created                               │
│  ┌─────────────────────────────────┐                       │
│  │ StatefulSet: my-database        │                       │
│  │ Service: my-database            │                       │
│  │ Secret: my-database-creds       │                       │
│  └─────────────────────────────────┘                       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

> **Stop and think**: A CRD for `Database` exists in the cluster, and you create a `Database` custom resource. But no actual database gets provisioned. What's missing? A CRD alone doesn't do anything — why not?

### Why Use Operators?

| Benefit | Example |
|---------|---------|
| Abstraction | Create `Database`, operator handles StatefulSet, PVC, etc. |
| Automation | Operator handles backups, failover, scaling |
| Domain expertise | Operator knows how to properly configure Postgres |
| Day 2 operations | Upgrades, restores, monitoring built-in |

---

## kubectl explain with CRDs

```bash
# Works for CRDs too (if installed)
k explain database
k explain database.spec
k explain certificate.spec.secretName
```

---

## Quick Reference

```bash
# List CRDs
k get crd

# View CRD details
k describe crd NAME

# Work with custom resources
k get <resource>
k describe <resource> NAME
k delete <resource> NAME

# Get API resources (includes CRDs)
k api-resources | grep example.com

# Check if CRD exists
k get crd myresource.example.com
```

---

## Visualization

```
┌─────────────────────────────────────────────────────────────┐
│                 CRD Creates New API Endpoint                │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Before CRD:                                                │
│  ┌─────────────────────────────────┐                       │
│  │ /api/v1/pods                    │                       │
│  │ /api/v1/services                │                       │
│  │ /apis/apps/v1/deployments       │                       │
│  └─────────────────────────────────┘                       │
│                                                             │
│  After CRD (group: example.com, plural: databases):        │
│  ┌─────────────────────────────────┐                       │
│  │ /api/v1/pods                    │                       │
│  │ /api/v1/services                │                       │
│  │ /apis/apps/v1/deployments       │                       │
│  │ /apis/example.com/v1/databases  │  ← NEW!               │
│  └─────────────────────────────────┘                       │
│                                                             │
│  kubectl commands now work:                                │
│  $ k get databases                                         │
│  $ k describe database my-db                               │
│  $ k delete database my-db                                 │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Did You Know?

- **CRDs are themselves a Kubernetes resource.** The `apiextensions.k8s.io/v1` group defines how to define custom resources.

- **Deleting a CRD deletes all its Custom Resources.** Be careful! `kubectl delete crd databases.example.com` wipes all Database CRs.

- **CRDs support multiple versions.** You can have v1alpha1, v1beta1, and v1 served simultaneously for smooth migrations.

- **The most popular Kubernetes projects are Operators.** Prometheus, cert-manager, ArgoCD, Istio—all use CRDs extensively.

---

## Common Mistakes

| Mistake | Why It Hurts | Solution |
|---------|--------------|----------|
| Confusing CRD with CR | CRD is definition, CR is instance | CRD = template, CR = actual resource |
| Deleting CRD accidentally | Deletes all CRs too | Double-check before deleting CRDs |
| Not checking if CRD exists | kubectl commands fail | `k get crd NAME` first |
| Thinking CRDs do something alone | CRDs just store data | Need controller/operator for actions |
| Wrong plural/singular usage | kubectl commands fail | Check `k api-resources` for correct names |

---

## Quiz

1. **A team installs a `Database` CRD and creates a custom resource `kind: Database` with `spec.engine: postgres`. Nothing happens — no StatefulSet, no Service, no PVC is created. The CRD is correctly installed (confirmed with `kubectl get crd`). What is wrong?**
   <details>
   <summary>Answer</summary>
   A CRD only defines the schema — it tells Kubernetes how to store and validate the custom resource, but it doesn't contain any logic to act on it. What's missing is a controller (operator) that watches for Database CRs and creates the actual Kubernetes resources (StatefulSet, Service, PVC, Secret, etc.). The CRD is the "form," and the operator is the "clerk that processes the form." You need to install the database operator (a pod that runs the controller logic) alongside the CRD for anything to actually happen.
   </details>

2. **A colleague accidentally runs `kubectl delete crd databases.example.com` thinking it would just clean up the definition. The team immediately discovers that all 15 Database custom resources across 5 namespaces are gone. Why did this happen and how can you prevent it?**
   <details>
   <summary>Answer</summary>
   Deleting a CRD triggers cascading deletion of all Custom Resources of that type cluster-wide. Kubernetes treats the CRD as the "owner" of all its CRs — removing the definition removes all instances. To prevent this: (1) use RBAC to restrict who can delete CRDs (they're cluster-scoped resources), (2) back up CRs before any CRD operations, (3) consider adding the `foregroundDeletion` finalizer pattern in your operator to handle cleanup gracefully. This is one of the most dangerous operations in Kubernetes because a single command can wipe data across all namespaces.
   </details>

3. **You join a new team and need to understand what custom resources are installed in the cluster. You run `kubectl get pods` and see several pods with names like `cert-manager-controller` and `prometheus-operator`. How do you discover all CRDs and which ones are actively being used?**
   <details>
   <summary>Answer</summary>
   Run `kubectl get crd` to list all installed CRDs — this shows every custom resource type available. To see which ones have actual instances, iterate through them: `kubectl get crd -o name | while read crd; do echo "$crd:"; kubectl get $(echo $crd | sed 's/customresourcedefinitions.apiextensions.k8s.io\///') -A 2>/dev/null | head -5; done`. You can also use `kubectl api-resources` to see all resources (including CRD-backed ones) and their short names. CRDs from well-known operators are easy to identify by their group names: `cert-manager.io`, `monitoring.coreos.com`, `gateway.networking.k8s.io`, etc.
   </details>

4. **You create a CRD with `scope: Namespaced` and a custom resource in the `production` namespace. A developer in the `staging` namespace tries `kubectl get databases` and sees nothing. They think the CRD is broken. What do you tell them?**
   <details>
   <summary>Answer</summary>
   The CRD is working correctly. Because it's defined as `scope: Namespaced`, custom resources exist within specific namespaces — just like ConfigMaps or Secrets. The Database CR was created in `production`, so it's only visible there. The developer needs to either create a Database CR in `staging` or look in the right namespace with `kubectl get databases -n production`. If the resource should be visible cluster-wide (like a shared configuration), the CRD should use `scope: Cluster` instead, but that's a design decision with trade-offs — cluster-scoped resources can't be isolated by namespace RBAC.
   </details>

5. **You are tasked with deploying a new `KafkaTopic` custom resource provided by another team. When you run `kubectl apply -f topic.yaml`, you receive the error: `The KafkaTopic "orders-topic" is invalid: spec.partitions: Invalid value: 0: spec.partitions in body should be greater than or equal to 1`. You check your `topic.yaml` and see `partitions: 0`. The developer who gave you the file insists that "0 partitions" means auto-scaling in their operator logic. Why did this happen, and how should it be resolved?**
   <details>
   <summary>Answer</summary>
   The error is generated by the Kubernetes API server, not the Kafka operator. The team that authored the `KafkaTopic` CRD defined an `openAPIV3Schema` that strictly enforces `spec.partitions` to have a `minimum: 1`. Because the API server validates the custom resource against this schema before the operator even sees it, the resource is rejected at the API level. To resolve this, the CRD author must either update the CRD schema to allow `0` as a valid value (if auto-scaling is indeed a supported feature), or you must update your YAML to provide a valid partition count greater than or equal to 1.
   </details>

---

## Hands-On Exercise

**Task**: Work with a CRD and Custom Resources.

**Part 1: Create a CRD**
```bash
cat << 'EOF' | k apply -f -
apiVersion: apiextensions.k8s.io/v1
kind: CustomResourceDefinition
metadata:
  name: websites.example.com
spec:
  group: example.com
  versions:
  - name: v1
    served: true
    storage: true
    schema:
      openAPIV3Schema:
        type: object
        properties:
          spec:
            type: object
            properties:
              domain:
                type: string
              replicas:
                type: integer
  scope: Namespaced
  names:
    plural: websites
    singular: website
    kind: Website
    shortNames:
    - ws
EOF

# Verify CRD created
k get crd websites.example.com
```

**Part 2: Create Custom Resources**
```bash
cat << 'EOF' | k apply -f -
apiVersion: example.com/v1
kind: Website
metadata:
  name: my-blog
spec:
  domain: blog.example.com
  replicas: 3
---
apiVersion: example.com/v1
kind: Website
metadata:
  name: my-shop
spec:
  domain: shop.example.com
  replicas: 5
EOF

# List using different names
k get websites
k get website
k get ws
```

**Part 3: Inspect and Modify**
```bash
# Describe
k describe website my-blog

# Get YAML
k get ws my-blog -o yaml

# Edit (using patch for non-interactive automation)
k patch website my-blog --type=merge -p '{"spec":{"replicas":2}}'
```

**Part 4: Explore API**
```bash
# Check API resources
k api-resources | grep example.com

# Use explain
k explain website
```

**Cleanup:**
```bash
k delete website my-blog my-shop
k delete crd websites.example.com
```

---

## Practice Drills

### Drill 1: List CRDs (Target: 1 minute)

```bash
# List all CRDs
k get crd

# Count CRDs
k get crd --no-headers | wc -l
```

### Drill 2: Describe a CRD (Target: 1 minute)

```bash
# If cert-manager or similar is installed
k describe crd certificates.cert-manager.io 2>/dev/null || echo "cert-manager not installed"

# Otherwise use any CRD
k get crd -o name | head -1 | xargs k describe
```

### Drill 3: Create CRD (Target: 3 minutes)

```bash
cat << 'EOF' | k apply -f -
apiVersion: apiextensions.k8s.io/v1
kind: CustomResourceDefinition
metadata:
  name: backups.drill.example.com
spec:
  group: drill.example.com
  versions:
  - name: v1
    served: true
    storage: true
    schema:
      openAPIV3Schema:
        type: object
        properties:
          spec:
            type: object
            properties:
              schedule:
                type: string
              retention:
                type: integer
  scope: Namespaced
  names:
    plural: backups
    singular: backup
    kind: Backup
    shortNames:
    - bk
EOF

k get crd backups.drill.example.com
k delete crd backups.drill.example.com
```

### Drill 4: Create and Query CR (Target: 3 minutes)

```bash
# First create CRD
cat << 'EOF' | k apply -f -
apiVersion: apiextensions.k8s.io/v1
kind: CustomResourceDefinition
metadata:
  name: tasks.drill.example.com
spec:
  group: drill.example.com
  versions:
  - name: v1
    served: true
    storage: true
    schema:
      openAPIV3Schema:
        type: object
        properties:
          spec:
            type: object
            properties:
              priority:
                type: string
  scope: Namespaced
  names:
    plural: tasks
    singular: task
    kind: Task
EOF

# Create CR
cat << 'EOF' | k apply -f -
apiVersion: drill.example.com/v1
kind: Task
metadata:
  name: important-task
spec:
  priority: high
EOF

# Query
k get tasks
k describe task important-task
k get task important-task -o yaml

# Cleanup
k delete task important-task
k delete crd tasks.drill.example.com
```

### Drill 5: Check API Resources (Target: 2 minutes)

```bash
# List all API resources
k api-resources

# Filter for a specific group
k api-resources | grep networking

# Show only CRD-backed resources (custom)
k api-resources | grep -v "^NAME" | grep "\."
```

### Drill 6: Use kubectl explain on CRD (Target: 2 minutes)

```bash
# Create a simple CRD
cat << 'EOF' | k apply -f -
apiVersion: apiextensions.k8s.io/v1
kind: CustomResourceDefinition
metadata:
  name: configs.drill.example.com
spec:
  group: drill.example.com
  versions:
  - name: v1
    served: true
    storage: true
    schema:
      openAPIV3Schema:
        type: object
        properties:
          spec:
            type: object
            properties:
              key:
                type: string
              value:
                type: string
  scope: Namespaced
  names:
    plural: configs
    singular: config
    kind: Config
EOF

# Use explain
k explain config
k explain config.spec

# Cleanup
k delete crd configs.drill.example.com
```

### Drill 7: Troubleshoot CRD Validation (Target: 4 minutes)

**Task:** Create a CRD with strict schema validation, attempt to create an invalid CR, observe the error, and fix it.

```bash
# 1. Create a CRD with validation
cat << 'EOF' | k apply -f -
apiVersion: apiextensions.k8s.io/v1
kind: CustomResourceDefinition
metadata:
  name: caches.drill.example.com
spec:
  group: drill.example.com
  versions:
  - name: v1
    served: true
    storage: true
    schema:
      openAPIV3Schema:
        type: object
        required: ["spec"]
        properties:
          spec:
            type: object
            required: ["memoryLimit"]
            properties:
              memoryLimit:
                type: integer
                minimum: 128
  scope: Namespaced
  names:
    plural: caches
    singular: cache
    kind: Cache
EOF

# 2. Try to apply an invalid CR (memoryLimit is a string instead of integer, and too small)
cat << 'EOF' | k apply -f -
apiVersion: drill.example.com/v1
kind: Cache
metadata:
  name: bad-cache
spec:
  memoryLimit: "64"
EOF

# Notice the validation error from the API server!
# error: ValidationError(Cache.spec.memoryLimit): invalid type for drill.example.com/v1.Cache.spec.memoryLimit: got "string", expected "integer"

# 3. Fix the CR by providing a valid integer >= 128
cat << 'EOF' | k apply -f -
apiVersion: drill.example.com/v1
kind: Cache
metadata:
  name: good-cache
spec:
  memoryLimit: 256
EOF

# 4. Verify it was created successfully
k get cache good-cache

# 5. Cleanup
k delete crd caches.drill.example.com
```

---

## Next Module

[Part 4 Cumulative Quiz](../part4-cumulative-quiz/) - Test your mastery of environment, configuration, and security topics.