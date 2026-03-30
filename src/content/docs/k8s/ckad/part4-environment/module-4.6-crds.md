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

1. **What's the difference between a CRD and a Custom Resource?**
   <details>
   <summary>Answer</summary>
   A CRD (Custom Resource Definition) defines a new resource type (like a schema). A Custom Resource (CR) is an instance of that type (actual data). CRD is the definition, CR is the object created from it.
   </details>

2. **What happens when you delete a CRD?**
   <details>
   <summary>Answer</summary>
   All Custom Resources of that type are also deleted. This is cascading deletion.
   </details>

3. **What is an Operator?**
   <details>
   <summary>Answer</summary>
   An Operator is a pattern combining a CRD with a controller. The CRD defines the resource structure, and the controller watches for CRs and takes automated actions (creating pods, managing state, etc.).
   </details>

4. **How do you list all CRDs in a cluster?**
   <details>
   <summary>Answer</summary>
   `kubectl get crd` or `kubectl get customresourcedefinitions`
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

# Edit
k edit website my-blog
# Change replicas to 2
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

---

## Next Module

[Part 4 Cumulative Quiz](../part4-cumulative-quiz/) - Test your mastery of environment, configuration, and security topics.
