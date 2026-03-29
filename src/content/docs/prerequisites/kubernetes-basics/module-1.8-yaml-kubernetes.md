---
title: "Module 1.8: YAML for Kubernetes"
slug: prerequisites/kubernetes-basics/module-1.8-yaml-kubernetes
sidebar:
  order: 9
---
> **Complexity**: `[MEDIUM]` - Essential skill
>
> **Time to Complete**: 35-40 minutes
>
> **Prerequisites**: Previous modules (familiarity with K8s resources)

---

## Why This Module Matters

Every Kubernetes resource is defined in YAML. Understanding YAML syntax and K8s resource structure is essential for:
- Writing manifests
- Understanding examples and documentation
- Debugging configuration errors
- Certification exams

---

## YAML Basics

### Structure

```yaml
# This is a comment

# Scalars (simple values)
string: hello
number: 42
float: 3.14
boolean: true
null_value: null

# Lists (arrays)
items:
- item1
- item2
- item3

# Or inline
items: [item1, item2, item3]

# Maps (objects)
person:
  name: John
  age: 30

# Or inline
person: {name: John, age: 30}
```

### Indentation Rules

```yaml
# YAML uses spaces, NOT tabs
# Typically 2 spaces per level

parent:
  child:
    grandchild: value

# Wrong (tabs will break):
parent:
	child:      # This is a tab - WRONG!
```

### Multi-line Strings

```yaml
# Literal block (preserves newlines)
literal: |
  Line 1
  Line 2
  Line 3

# Folded block (joins lines with spaces)
folded: >
  This is a
  very long
  sentence.
# Results in: "This is a very long sentence."
```

---

## Kubernetes Resource Structure

Every K8s resource follows this structure:

```yaml
apiVersion: v1              # API version
kind: Pod                   # Resource type
metadata:                   # Resource metadata
  name: my-pod
  namespace: default
  labels:
    app: myapp
  annotations:
    description: "My pod"
spec:                       # Desired state (varies by resource)
  containers:
  - name: main
    image: nginx
status:                     # Current state (managed by K8s, read-only)
  phase: Running
```

### Required Fields

| Field | Description |
|-------|-------------|
| `apiVersion` | API version for this resource type |
| `kind` | Type of resource |
| `metadata.name` | Unique name within namespace |
| `spec` | Desired state (varies by kind) |

---

## Common API Versions

| Resource | apiVersion |
|----------|------------|
| Pod, Service, ConfigMap, Secret | `v1` |
| Deployment, ReplicaSet | `apps/v1` |
| Ingress | `networking.k8s.io/v1` |
| NetworkPolicy | `networking.k8s.io/v1` |
| PersistentVolume, PVC | `v1` |
| StorageClass | `storage.k8s.io/v1` |
| Role, ClusterRole | `rbac.authorization.k8s.io/v1` |

```bash
# Find API version for any resource
kubectl api-resources | grep -i deployment
# deployments    deploy    apps/v1    true    Deployment
```

---

## Generating YAML (Don't Memorize!)

Never write YAML from scratch—generate it:

```bash
# Generate Pod YAML
kubectl run nginx --image=nginx --dry-run=client -o yaml

# Generate Deployment YAML
kubectl create deployment nginx --image=nginx --dry-run=client -o yaml

# Generate Service YAML
kubectl expose deployment nginx --port=80 --dry-run=client -o yaml

# Save to file
kubectl create deployment nginx --image=nginx --dry-run=client -o yaml > deployment.yaml
```

### Explain Command (Documentation)

```bash
# Get field documentation
kubectl explain pod
kubectl explain pod.spec
kubectl explain pod.spec.containers
kubectl explain pod.spec.containers.resources

# Recursive (all fields)
kubectl explain pod.spec --recursive | less
```

---

## Common Patterns

### Pod Template (in Deployments)

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: myapp
spec:
  replicas: 3
  selector:
    matchLabels:
      app: myapp
  template:                    # Pod template starts here
    metadata:
      labels:
        app: myapp             # Must match selector
    spec:
      containers:
      - name: main
        image: nginx:1.25
        ports:
        - containerPort: 80
```

### Environment Variables

```yaml
containers:
- name: app
  image: myapp
  env:
  # Direct value
  - name: LOG_LEVEL
    value: "debug"
  # From ConfigMap
  - name: DB_HOST
    valueFrom:
      configMapKeyRef:
        name: app-config
        key: database_host
  # From Secret
  - name: DB_PASS
    valueFrom:
      secretKeyRef:
        name: app-secrets
        key: password
```

### Volume Mounts

```yaml
spec:
  containers:
  - name: app
    image: myapp
    volumeMounts:
    - name: config
      mountPath: /etc/config
    - name: data
      mountPath: /data
  volumes:
  - name: config
    configMap:
      name: app-config
  - name: data
    persistentVolumeClaim:
      claimName: app-pvc
```

### Resource Requirements

```yaml
containers:
- name: app
  image: myapp
  resources:
    requests:
      memory: "64Mi"
      cpu: "250m"
    limits:
      memory: "128Mi"
      cpu: "500m"
```

---

## Multiple Documents

```yaml
# First document
apiVersion: v1
kind: ConfigMap
metadata:
  name: config
data:
  key: value
---                          # Document separator
# Second document
apiVersion: v1
kind: Service
metadata:
  name: service
spec:
  # ...
---                          # Another document
apiVersion: apps/v1
kind: Deployment
# ...
```

```bash
# Apply all documents in file
kubectl apply -f multi-doc.yaml
```

---

## Validation

```bash
# Server-side validation (dry-run)
kubectl apply -f pod.yaml --dry-run=server

# Client-side validation
kubectl apply -f pod.yaml --dry-run=client

# Validate without applying
kubectl create -f pod.yaml --dry-run=client --validate=true

# Check YAML syntax
kubectl apply -f pod.yaml --dry-run=client -o yaml
```

---

## Common YAML Errors

### Indentation

```yaml
# WRONG - inconsistent indentation
spec:
  containers:
   - name: app    # 3 spaces
    image: nginx  # 4 spaces - ERROR!

# CORRECT
spec:
  containers:
  - name: app
    image: nginx
```

### Quotes

```yaml
# Some values need quotes

# WRONG - colon causes parsing error
message: Error: something failed

# CORRECT
message: "Error: something failed"

# Numbers that should be strings
port: "8080"   # If you need string, quote it
```

### Booleans

```yaml
# These are all true:
enabled: true
enabled: True
enabled: yes
enabled: on

# These are all false:
enabled: false
enabled: False
enabled: no
enabled: off

# Be careful with strings that look like booleans
value: "yes"    # This is string "yes"
value: yes      # This is boolean true
```

---

## Did You Know?

- **JSON is valid YAML.** YAML is a superset of JSON. You can paste JSON into YAML files.

- **K8s ignores unknown fields** by default. Typos in field names don't error—they're silently ignored.

- **`kubectl explain` is your friend.** It shows documentation for any field, pulled from the API.

- **Server-side dry-run validates against cluster.** It catches more errors than client-side.

---

## Quiz

1. **What's the difference between `--dry-run=client` and `--dry-run=server`?**
   <details>
   <summary>Answer</summary>
   Client-side validation only checks YAML syntax. Server-side sends to the API server which validates against the schema and cluster state (like checking if referenced ConfigMaps exist).
   </details>

2. **How do you find the correct apiVersion for a resource?**
   <details>
   <summary>Answer</summary>
   `kubectl api-resources | grep RESOURCE` shows the API group/version. Or use `kubectl explain RESOURCE` which shows the version at the top.
   </details>

3. **What does `---` mean in a YAML file?**
   <details>
   <summary>Answer</summary>
   Document separator. One YAML file can contain multiple documents (resources). `kubectl apply -f` processes all documents in the file.
   </details>

4. **How do you see documentation for a specific field?**
   <details>
   <summary>Answer</summary>
   `kubectl explain RESOURCE.FIELD.PATH`, e.g., `kubectl explain pod.spec.containers.resources`
   </details>

---

## Hands-On Exercise

**Task**: Practice YAML generation and validation.

```bash
# 1. Generate deployment YAML
kubectl create deployment web --image=nginx --replicas=3 --dry-run=client -o yaml > web.yaml

# 2. View it
cat web.yaml

# 3. Add resource limits (edit the file)
# Add under containers[0]:
#   resources:
#     requests:
#       memory: "64Mi"
#       cpu: "100m"
#     limits:
#       memory: "128Mi"
#       cpu: "200m"

# 4. Validate
kubectl apply -f web.yaml --dry-run=server

# 5. Apply
kubectl apply -f web.yaml

# 6. Verify
kubectl get deployment web

# 7. Generate service YAML
kubectl expose deployment web --port=80 --dry-run=client -o yaml > service.yaml

# 8. Apply service
kubectl apply -f service.yaml

# 9. Use explain
kubectl explain deployment.spec.strategy

# 10. Cleanup
kubectl delete -f web.yaml -f service.yaml
rm web.yaml service.yaml
```

**Success criteria**: Resources created from generated YAML.

---

## Summary

**YAML basics**:
- Spaces for indentation (not tabs)
- `-` for list items
- `:` for key-value pairs
- `---` separates documents

**K8s resource structure**:
- apiVersion, kind, metadata, spec
- Use `kubectl explain` for field documentation
- Use `--dry-run=client -o yaml` to generate

**Validation**:
- `--dry-run=client` for syntax
- `--dry-run=server` for full validation

**Best practices**:
- Never write YAML from scratch
- Generate, modify, apply
- Use `kubectl explain` liberally

---

## Track Complete!

Congratulations! You've finished the **Kubernetes Basics** prerequisite track. You now understand:

1. Setting up a local cluster (kind)
2. kubectl commands and patterns
3. Pods - the atomic unit
4. Deployments - managing applications
5. Services - stable networking
6. ConfigMaps and Secrets - configuration
7. Namespaces and Labels - organization
8. YAML for Kubernetes - writing manifests

**Next Steps**:
- [CKA Curriculum](../../k8s/cka/part0-environment/module-0.1-cluster-setup/) - Administrator certification
- [CKAD Curriculum](../../k8s/ckad/part0-environment/module-0.1-ckad-overview/) - Developer certification
- [Modern DevOps Practices](../modern-devops/module-1.1-infrastructure-as-code/) - Complementary skills
