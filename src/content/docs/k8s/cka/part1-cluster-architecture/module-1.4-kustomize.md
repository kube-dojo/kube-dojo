---
title: "Module 1.4: Kustomize - Template-Free Configuration"
slug: k8s/cka/part1-cluster-architecture/module-1.4-kustomize
sidebar:
  order: 5
---
> **Complexity**: `[MEDIUM]` - Essential exam skill for 2025
>
> **Time to Complete**: 35-45 minutes
>
> **Prerequisites**: Module 0.1 (working cluster), basic YAML knowledge

---

## Why This Module Matters

Kustomize is **new to the CKA 2025 curriculum**. You will be tested on it.

Kustomize solves a common problem: you have the same application deployed to dev, staging, and production, but each environment needs slightly different configuration—different replicas, different resource limits, different image tags.

Without Kustomize, you'd either:
1. Maintain separate YAML files for each environment (duplication nightmare)
2. Use templates with placeholders (adds complexity)

Kustomize takes a different approach: **overlay and patch**. Start with a base, layer environment-specific changes on top. No templating. Pure YAML. Built into kubectl.

> **The Transparent Film Analogy**
>
> Think of Kustomize like transparent film overlays on a projector. Your base slide shows the application structure. For production, you overlay a film that adds "replicas: 10". For dev, you overlay a film that changes the image tag. Each overlay modifies the base without duplicating it. Stack as many overlays as you need.

---

## What You'll Learn

By the end of this module, you'll be able to:
- Create Kustomize bases and overlays
- Patch resources without modifying originals
- Use common transformations (labels, namespaces, prefixes)
- Generate ConfigMaps and Secrets from files
- Apply Kustomize configurations with kubectl

---

## Part 1: Kustomize Concepts

### 1.1 Core Terminology

| Term | Definition |
|------|------------|
| **Base** | Original, reusable resource definitions |
| **Overlay** | Environment-specific customizations |
| **Patch** | Partial YAML that modifies a resource |
| **kustomization.yaml** | Manifest that defines what to include and transform |

### 1.2 Directory Structure

```
myapp/
├── base/                      # Shared, reusable definitions
│   ├── kustomization.yaml
│   ├── deployment.yaml
│   ├── service.yaml
│   └── configmap.yaml
│
└── overlays/                  # Environment-specific
    ├── dev/
    │   ├── kustomization.yaml
    │   └── patch-replicas.yaml
    │
    ├── staging/
    │   ├── kustomization.yaml
    │   └── patch-resources.yaml
    │
    └── production/
        ├── kustomization.yaml
        ├── patch-replicas.yaml
        └── patch-resources.yaml
```

### 1.3 How Kustomize Works

```
┌────────────────────────────────────────────────────────────────┐
│                     Kustomize Flow                              │
│                                                                 │
│   Base Resources                    Overlay Patches             │
│   ┌─────────────────┐              ┌─────────────────┐         │
│   │ deployment.yaml │              │ patch-prod.yaml │         │
│   │ replicas: 1     │      +       │ replicas: 10    │         │
│   │ image: v1       │              │ image: v2       │         │
│   └─────────────────┘              └─────────────────┘         │
│            │                              │                     │
│            └──────────────┬───────────────┘                     │
│                           │                                     │
│                           ▼                                     │
│                    ┌─────────────┐                              │
│                    │  Kustomize  │                              │
│                    │  (merge)    │                              │
│                    └──────┬──────┘                              │
│                           │                                     │
│                           ▼                                     │
│                    Final Output                                 │
│                    ┌─────────────────┐                          │
│                    │ deployment.yaml │                          │
│                    │ replicas: 10    │                          │
│                    │ image: v2       │                          │
│                    └─────────────────┘                          │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
```

> **Did You Know?**
>
> Kustomize is built into kubectl since v1.14. You don't need to install anything extra—just use `kubectl apply -k` or `kubectl kustomize`. This is why it's a CKA exam favorite: it works out of the box.

---

## Part 2: Creating a Base

### 2.1 The kustomization.yaml File

Every Kustomize directory needs a `kustomization.yaml`:

```yaml
# base/kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

resources:
  - deployment.yaml
  - service.yaml
  - configmap.yaml
```

### 2.2 Base Resources

```yaml
# base/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: myapp
spec:
  replicas: 1
  selector:
    matchLabels:
      app: myapp
  template:
    metadata:
      labels:
        app: myapp
    spec:
      containers:
      - name: myapp
        image: nginx:1.25
        ports:
        - containerPort: 80
        resources:
          requests:
            memory: "64Mi"
            cpu: "100m"
```

```yaml
# base/service.yaml
apiVersion: v1
kind: Service
metadata:
  name: myapp
spec:
  selector:
    app: myapp
  ports:
  - port: 80
    targetPort: 80
```

### 2.3 Preview Base Output

```bash
# See what the base produces
kubectl kustomize base/

# Or using kustomize directly
kustomize build base/
```

---

## Part 3: Creating Overlays

### 3.1 Simple Overlay

```yaml
# overlays/dev/kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

resources:
  - ../../base    # Reference the base

namePrefix: dev-           # Prefix all resource names
namespace: development     # Put everything in this namespace

commonLabels:
  environment: dev         # Add this label to all resources
```

### 3.2 Production Overlay with Patches

```yaml
# overlays/production/kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

resources:
  - ../../base

namePrefix: prod-
namespace: production

commonLabels:
  environment: production

patches:
  - path: patch-replicas.yaml
  - path: patch-resources.yaml
```

```yaml
# overlays/production/patch-replicas.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: myapp     # Must match the base resource name
spec:
  replicas: 10    # Override replicas
```

```yaml
# overlays/production/patch-resources.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: myapp
spec:
  template:
    spec:
      containers:
      - name: myapp
        resources:
          requests:
            memory: "256Mi"
            cpu: "500m"
          limits:
            memory: "512Mi"
            cpu: "1000m"
```

### 3.3 Preview and Apply Overlays

```bash
# Preview production overlay
kubectl kustomize overlays/production/

# Apply to cluster
kubectl apply -k overlays/production/

# Apply dev overlay
kubectl apply -k overlays/dev/
```

---

## Part 4: Common Transformers

### 4.1 namePrefix and nameSuffix

```yaml
# kustomization.yaml
namePrefix: prod-
nameSuffix: -v2

# Result: deployment "myapp" becomes "prod-myapp-v2"
```

### 4.2 namespace

```yaml
# kustomization.yaml
namespace: production

# All resources get namespace: production
```

### 4.3 commonLabels

```yaml
# kustomization.yaml
commonLabels:
  app.kubernetes.io/name: myapp
  app.kubernetes.io/env: production

# Added to ALL resources (metadata.labels AND selector)
```

### 4.4 commonAnnotations

```yaml
# kustomization.yaml
commonAnnotations:
  team: platform
  oncall: platform@example.com

# Added to all resources' metadata.annotations
```

### 4.5 images

Change image names/tags without patching:

```yaml
# kustomization.yaml
images:
  - name: nginx           # Original image name
    newName: my-registry/nginx
    newTag: "2.0"

# Changes all nginx images to my-registry/nginx:2.0
```

---

## Part 5: Patching Strategies

### 5.1 Strategic Merge Patch (Default)

Merges your patch with the base:

```yaml
# patches/add-sidecar.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: myapp
spec:
  template:
    spec:
      containers:
      - name: sidecar           # Added to existing containers
        image: busybox
        command: ["sleep", "infinity"]
```

### 5.2 JSON 6902 Patch

More precise control using JSON Patch syntax:

```yaml
# kustomization.yaml
patches:
  - target:
      kind: Deployment
      name: myapp
    patch: |-
      - op: replace
        path: /spec/replicas
        value: 5
      - op: add
        path: /metadata/annotations/patched
        value: "true"
```

### 5.3 Patch Targeting

Target specific resources:

```yaml
# kustomization.yaml
patches:
  - path: patch-replicas.yaml
    target:
      kind: Deployment
      name: myapp
```

Target by label:

```yaml
patches:
  - path: patch-memory.yaml
    target:
      kind: Deployment
      labelSelector: "tier=frontend"
```

---

## Part 6: Generators

### 6.1 ConfigMap Generator

Generate ConfigMaps from files or literals:

```yaml
# kustomization.yaml
configMapGenerator:
  - name: app-config
    literals:
      - DATABASE_HOST=postgres
      - DATABASE_PORT=5432
    files:
      - config.properties

# Creates ConfigMap with hashed name suffix
# e.g., app-config-8h2k9d
```

### 6.2 Secret Generator

```yaml
# kustomization.yaml
secretGenerator:
  - name: db-credentials
    literals:
      - username=admin
      - password=secret123
    type: Opaque

# Creates Secret with hashed name suffix
```

### 6.3 Why Hashed Names?

```
app-config-8h2k9d
            ^^^^^^
            content hash
```

When ConfigMap content changes, the hash changes, which changes the name. This triggers a rolling update of pods using the ConfigMap—they detect the new reference automatically.

### 6.4 Disabling Hash Suffixes

```yaml
# kustomization.yaml
configMapGenerator:
  - name: app-config
    literals:
      - KEY=value

generatorOptions:
  disableNameSuffixHash: true
```

---

## Part 7: Real-World Example

### 7.1 Full Directory Structure

```
webapp/
├── base/
│   ├── kustomization.yaml
│   ├── deployment.yaml
│   ├── service.yaml
│   └── config/
│       └── nginx.conf
│
└── overlays/
    ├── dev/
    │   └── kustomization.yaml
    └── prod/
        ├── kustomization.yaml
        ├── patch-replicas.yaml
        └── secrets/
            └── db-password.txt
```

### 7.2 Base kustomization.yaml

```yaml
# base/kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

resources:
  - deployment.yaml
  - service.yaml

configMapGenerator:
  - name: nginx-config
    files:
      - config/nginx.conf
```

### 7.3 Production Overlay

```yaml
# overlays/prod/kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

resources:
  - ../../base

namespace: production
namePrefix: prod-

commonLabels:
  environment: production

images:
  - name: nginx
    newTag: "1.25-alpine"

patches:
  - path: patch-replicas.yaml

secretGenerator:
  - name: db-credentials
    files:
      - password=secrets/db-password.txt
```

---

## Part 8: kubectl Integration

### 8.1 Essential Commands

```bash
# Preview kustomization output
kubectl kustomize <directory>

# Apply kustomization to cluster
kubectl apply -k <directory>

# Delete resources from kustomization
kubectl delete -k <directory>

# Diff against current cluster state
kubectl diff -k <directory>
```

### 8.2 Exam-Ready Commands

```bash
# Quick apply for exam
kubectl apply -k overlays/production/

# Verify what was created
kubectl get all -n production

# If you need to debug
kubectl kustomize overlays/production/ | kubectl apply --dry-run=client -f -
```

---

## Part 9: Kustomize vs Helm

| Aspect | Kustomize | Helm |
|--------|-----------|------|
| Approach | Overlay/patch | Template |
| Learning curve | Lower | Higher |
| Pure YAML | Yes | No (Go templates) |
| Package sharing | Directories | Charts |
| Rollback | Not built-in | Built-in |
| Best for | Config variants | Complex apps |

**Use Kustomize when**: You have your own manifests and need environment variations.

**Use Helm when**: You're installing third-party applications or need templating.

> **Exam Tip**
>
> The CKA exam may ask you to use either Helm or Kustomize. Know both. For quick environment customization, Kustomize is faster to set up.

---

## Did You Know?

- **Kustomize was a separate tool** before being merged into kubectl. You can still install standalone `kustomize` for additional features.

- **Argo CD and Flux** (GitOps tools) natively understand Kustomize. Your overlay structure becomes your deployment strategy.

- **You can combine Helm and Kustomize**. Generate manifests from Helm, then customize with Kustomize overlays.

---

## Common Mistakes

| Mistake | Problem | Solution |
|---------|---------|----------|
| Wrong path to base | "resource not found" | Use relative paths like `../../base` |
| Forgetting kustomization.yaml | kubectl errors | Every directory needs one |
| Patch name mismatch | Patch not applied | Patch metadata.name must match base |
| Missing namespace | Resources in wrong ns | Add `namespace:` to overlay |
| commonLabels breaking selectors | Selector mismatch | Test carefully, labels affect selectors |

---

## Quiz

1. **What's the difference between base and overlay in Kustomize?**
   <details>
   <summary>Answer</summary>
   A **base** contains the original, reusable resource definitions. An **overlay** references a base and adds environment-specific customizations (patches, labels, namespaces). Overlays modify bases without duplicating them.
   </details>

2. **How do you apply a Kustomize configuration to your cluster?**
   <details>
   <summary>Answer</summary>
   `kubectl apply -k <directory>` where the directory contains a kustomization.yaml file. Example: `kubectl apply -k overlays/production/`
   </details>

3. **Why does Kustomize add a hash suffix to generated ConfigMaps?**
   <details>
   <summary>Answer</summary>
   The hash is based on the ConfigMap's content. When content changes, the hash changes, which changes the ConfigMap name. Pods referencing the ConfigMap detect the new name and trigger a rolling update, ensuring they get the new configuration.
   </details>

4. **You need to change the image tag for production without modifying the base. How?**
   <details>
   <summary>Answer</summary>
   Use the `images` transformer in your overlay's kustomization.yaml:
   ```yaml
   images:
     - name: nginx
       newTag: "1.25-production"
   ```
   This changes all references to the nginx image without touching base files.
   </details>

---

## Hands-On Exercise

**Task**: Create a Kustomize structure for a web application with dev and prod overlays.

**Steps**:

1. **Create directory structure**:
```bash
mkdir -p webapp/base webapp/overlays/dev webapp/overlays/prod
```

2. **Create base deployment**:
```bash
cat > webapp/base/deployment.yaml << 'EOF'
apiVersion: apps/v1
kind: Deployment
metadata:
  name: webapp
spec:
  replicas: 1
  selector:
    matchLabels:
      app: webapp
  template:
    metadata:
      labels:
        app: webapp
    spec:
      containers:
      - name: webapp
        image: nginx:1.25
        ports:
        - containerPort: 80
EOF
```

3. **Create base service**:
```bash
cat > webapp/base/service.yaml << 'EOF'
apiVersion: v1
kind: Service
metadata:
  name: webapp
spec:
  selector:
    app: webapp
  ports:
  - port: 80
EOF
```

4. **Create base kustomization**:
```bash
cat > webapp/base/kustomization.yaml << 'EOF'
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
resources:
  - deployment.yaml
  - service.yaml
EOF
```

5. **Create dev overlay**:
```bash
cat > webapp/overlays/dev/kustomization.yaml << 'EOF'
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
resources:
  - ../../base
namePrefix: dev-
namespace: development
commonLabels:
  environment: dev
EOF
```

6. **Create prod overlay with patch**:
```bash
cat > webapp/overlays/prod/patch-replicas.yaml << 'EOF'
apiVersion: apps/v1
kind: Deployment
metadata:
  name: webapp
spec:
  replicas: 5
EOF

cat > webapp/overlays/prod/kustomization.yaml << 'EOF'
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
resources:
  - ../../base
namePrefix: prod-
namespace: production
commonLabels:
  environment: production
images:
  - name: nginx
    newTag: "1.25-alpine"
patches:
  - path: patch-replicas.yaml
EOF
```

7. **Preview and compare**:
```bash
echo "=== DEV ===" && kubectl kustomize webapp/overlays/dev/
echo "=== PROD ===" && kubectl kustomize webapp/overlays/prod/
```

8. **Apply dev overlay**:
```bash
kubectl create namespace development
kubectl apply -k webapp/overlays/dev/
kubectl get all -n development
```

9. **Apply prod overlay**:
```bash
kubectl create namespace production
kubectl apply -k webapp/overlays/prod/
kubectl get all -n production
```

**Success Criteria**:
- [ ] Understand base vs overlay structure
- [ ] Can create kustomization.yaml files
- [ ] Can use namePrefix, namespace, commonLabels
- [ ] Can create and apply patches
- [ ] Can preview output with `kubectl kustomize`

**Cleanup**:
```bash
kubectl delete -k webapp/overlays/dev/
kubectl delete -k webapp/overlays/prod/
kubectl delete namespace development production
rm -rf webapp/
```

---

## Practice Drills

### Drill 1: Kustomize vs kubectl apply (Target: 2 minutes)

Understand the difference:

```bash
# Create base
mkdir -p drill1/base
cat << 'EOF' > drill1/base/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: nginx
spec:
  replicas: 1
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

cat << 'EOF' > drill1/base/kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
resources:
  - deployment.yaml
EOF

# Preview vs apply
kubectl kustomize drill1/base/          # Just preview
kubectl apply -k drill1/base/           # Actually apply
kubectl get deploy nginx
kubectl delete -k drill1/base/
rm -rf drill1
```

### Drill 2: Namespace Transformation (Target: 3 minutes)

```bash
mkdir -p drill2/base drill2/overlays/dev
cat << 'EOF' > drill2/base/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: app
spec:
  replicas: 1
  selector:
    matchLabels:
      app: myapp
  template:
    metadata:
      labels:
        app: myapp
    spec:
      containers:
      - name: app
        image: nginx
EOF

cat << 'EOF' > drill2/base/kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
resources:
  - deployment.yaml
EOF

cat << 'EOF' > drill2/overlays/dev/kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
resources:
  - ../../base
namespace: dev-namespace
namePrefix: dev-
EOF

# Preview - see the transformations
kubectl kustomize drill2/overlays/dev/

# Apply
kubectl create namespace dev-namespace
kubectl apply -k drill2/overlays/dev/
kubectl get deploy -n dev-namespace  # Shows dev-app

# Cleanup
kubectl delete -k drill2/overlays/dev/
kubectl delete namespace dev-namespace
rm -rf drill2
```

### Drill 3: Image Transformation (Target: 3 minutes)

```bash
mkdir -p drill3
cat << 'EOF' > drill3/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web
spec:
  replicas: 1
  selector:
    matchLabels:
      app: web
  template:
    metadata:
      labels:
        app: web
    spec:
      containers:
      - name: web
        image: nginx:1.19
EOF

cat << 'EOF' > drill3/kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
resources:
  - deployment.yaml
images:
  - name: nginx
    newTag: "1.25"
EOF

# Preview - notice image changed to nginx:1.25
kubectl kustomize drill3/

# Apply and verify
kubectl apply -k drill3/
kubectl get deploy web -o jsonpath='{.spec.template.spec.containers[0].image}'
# Output: nginx:1.25

# Cleanup
kubectl delete -k drill3/
rm -rf drill3
```

### Drill 4: Troubleshooting - Broken Kustomization (Target: 5 minutes)

```bash
# Create broken kustomization
mkdir -p drill4
cat << 'EOF' > drill4/kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
resources:
  - deployment.yaml    # File doesn't exist!
  - service.yaml       # File doesn't exist!
commonLabels:
  app: myapp
EOF

# Try to build - will fail
kubectl kustomize drill4/

# YOUR TASK: Fix by creating the missing files
```

<details>
<summary>Solution</summary>

```bash
cat << 'EOF' > drill4/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: myapp
spec:
  replicas: 1
  selector:
    matchLabels:
      app: myapp
  template:
    metadata:
      labels:
        app: myapp
    spec:
      containers:
      - name: app
        image: nginx
EOF

cat << 'EOF' > drill4/service.yaml
apiVersion: v1
kind: Service
metadata:
  name: myapp
spec:
  selector:
    app: myapp
  ports:
  - port: 80
EOF

# Now it works
kubectl kustomize drill4/
rm -rf drill4
```

</details>

### Drill 5: Strategic Merge Patch (Target: 5 minutes)

```bash
mkdir -p drill5/base drill5/overlay
cat << 'EOF' > drill5/base/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: app
spec:
  replicas: 1
  selector:
    matchLabels:
      app: myapp
  template:
    metadata:
      labels:
        app: myapp
    spec:
      containers:
      - name: app
        image: nginx
        resources:
          requests:
            memory: "64Mi"
            cpu: "100m"
EOF

cat << 'EOF' > drill5/base/kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
resources:
  - deployment.yaml
EOF

# Create patch to increase resources for production
cat << 'EOF' > drill5/overlay/patch-resources.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: app
spec:
  replicas: 3
  template:
    spec:
      containers:
      - name: app
        resources:
          requests:
            memory: "256Mi"
            cpu: "500m"
          limits:
            memory: "512Mi"
            cpu: "1000m"
EOF

cat << 'EOF' > drill5/overlay/kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
resources:
  - ../base
patches:
  - path: patch-resources.yaml
EOF

# Preview the result
kubectl kustomize drill5/overlay/
rm -rf drill5
```

### Drill 6: ConfigMap Generator (Target: 3 minutes)

```bash
mkdir -p drill6
cat << 'EOF' > drill6/app.properties
DATABASE_URL=postgres://localhost:5432/mydb
LOG_LEVEL=info
FEATURE_FLAG=enabled
EOF

cat << 'EOF' > drill6/kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
configMapGenerator:
  - name: app-config
    files:
      - app.properties
    literals:
      - EXTRA_KEY=extra-value
EOF

# Preview - notice ConfigMap with hash suffix
kubectl kustomize drill6/
rm -rf drill6
```

### Drill 7: Challenge - Multi-Environment Setup

Create a complete Kustomize structure for 3 environments without looking at solutions:

**Requirements**:
- Base: nginx deployment, service
- Dev: 1 replica, namespace `dev`, image `nginx:1.24`
- Staging: 2 replicas, namespace `staging`, image `nginx:1.25`
- Prod: 5 replicas, namespace `production`, image `nginx:1.25`, add resource limits

```bash
mkdir -p challenge/{base,overlays/{dev,staging,prod}}
# YOUR TASK: Create all kustomization.yaml and resource files
```

<details>
<summary>Solution Structure</summary>

```
challenge/
├── base/
│   ├── deployment.yaml
│   ├── service.yaml
│   └── kustomization.yaml
├── overlays/
│   ├── dev/
│   │   └── kustomization.yaml
│   ├── staging/
│   │   └── kustomization.yaml
│   └── prod/
│       ├── kustomization.yaml
│       └── patch-resources.yaml
```

Test each: `kubectl kustomize challenge/overlays/dev/`

</details>

---

## Next Module

[Module 1.5: CRDs & Operators](../module-1.5-crds-operators/) - Extending Kubernetes with Custom Resource Definitions.
