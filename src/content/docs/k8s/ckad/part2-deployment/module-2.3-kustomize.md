---
title: "Module 2.3: Kustomize"
slug: k8s/ckad/part2-deployment/module-2.3-kustomize
sidebar:
  order: 3
lab:
  id: ckad-2.3-kustomize
  url: https://killercoda.com/kubedojo/scenario/ckad-2.3-kustomize
  duration: "30 min"
  difficulty: intermediate
  environment: kubernetes
---
> **Complexity**: `[MEDIUM]` - Template-free customization for Kubernetes
>
> **Time to Complete**: 40-50 minutes
>
> **Prerequisites**: Module 2.1 (Deployments), basic YAML understanding

---

## Learning Outcomes

After completing this module, you will be able to:
- **Build** Kustomize overlays that customize base resources for different environments
- **Apply** patches and transformations using `kubectl apply -k` without modifying original YAML
- **Compare** Kustomize vs Helm and choose the right tool for a given deployment scenario
- **Debug** Kustomize rendering issues using `kubectl kustomize` to preview output

---

## Why This Module Matters

Kustomize lets you customize Kubernetes resources without templates. Instead of using variables and logic (like Helm), Kustomize uses overlays and patches to modify base configurations. It's built into kubectl (`kubectl apply -k`), making it exam-friendly.

The CKAD tests Kustomize for:
- Creating and applying kustomizations
- Using overlays for different environments
- Patching resources
- Managing ConfigMaps and Secrets

> **The Sticker Customization Analogy**
>
> Imagine buying a laptop. The base laptop (base resources) is the same for everyone. But you add stickers, skins, and accessories (overlays) to make it yours. You don't rebuild the laptop—you customize it. Kustomize works the same way: keep your base Kubernetes resources clean, then apply overlays for dev/staging/prod.

---

## Kustomize Basics

### Key Concepts

| Concept | Description |
|---------|-------------|
| **Base** | Original, unmodified Kubernetes resources |
| **Overlay** | Customizations applied on top of base |
| **Patch** | Modifications to specific fields |
| **kustomization.yaml** | File that defines what to customize |

### How Kustomize Works

```
┌─────────────────────────────────────────────────────────┐
│                   Kustomize Flow                        │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Base                    Overlay                        │
│  ┌─────────────┐        ┌─────────────┐                │
│  │ deployment  │───────▶│  + replicas │                │
│  │   service   │        │  + env vars │                │
│  │  configmap  │        │  + labels   │                │
│  └─────────────┘        └─────────────┘                │
│         │                     │                         │
│         └─────────┬───────────┘                         │
│                   ▼                                     │
│            ┌─────────────┐                              │
│            │  Combined   │                              │
│            │  Resources  │                              │
│            └─────────────┘                              │
│                   │                                     │
│                   ▼                                     │
│         kubectl apply -k ./                             │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## Creating a Kustomization

### Basic Structure

```
my-app/
├── kustomization.yaml
├── deployment.yaml
└── service.yaml
```

### kustomization.yaml

```yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

resources:
- deployment.yaml
- service.yaml
```

### Apply with kubectl

```bash
# Preview what will be applied
kubectl kustomize ./my-app/

# Apply the kustomization
kubectl apply -k ./my-app/

# Delete resources
kubectl delete -k ./my-app/
```

---

## Common Transformations

### Add Labels to All Resources

```yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

resources:
- deployment.yaml
- service.yaml

commonLabels:
  app: my-app
  environment: production
```

### Add Annotations

```yaml
commonAnnotations:
  owner: team-platform
  managed-by: kustomize
```

### Add Name Prefix/Suffix

```yaml
namePrefix: prod-
nameSuffix: -v1
```

Result: `deployment` becomes `prod-deployment-v1`

### Set Namespace

```yaml
namespace: production
```

All resources will be deployed to this namespace.

---

> **Pause and predict**: You add `namePrefix: prod-` to your kustomization.yaml. A Deployment named `web-app` references a Service named `web-app` by name. After applying Kustomize, will the Service reference inside the Deployment also get the prefix? Think about what would break if it didn't.

## ConfigMaps and Secrets

### Generate ConfigMap

```yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

resources:
- deployment.yaml

configMapGenerator:
- name: app-config
  literals:
  - LOG_LEVEL=info
  - API_URL=http://api.example.com
```

### Generate ConfigMap from Files

```yaml
configMapGenerator:
- name: app-config
  files:
  - config.properties
  - settings.json
```

### Generate Secrets

```yaml
secretGenerator:
- name: db-credentials
  literals:
  - username=admin
  - password=secret123

# Or from files
secretGenerator:
- name: tls-certs
  files:
  - tls.crt
  - tls.key
  type: kubernetes.io/tls
```

> **Stop and think**: Kustomize appends a hash suffix to generated ConfigMaps (e.g., `app-config-abc123`). Why would this be useful? Hint: think about what happens when you update a ConfigMap and need pods to pick up the change.

### ConfigMap/Secret Behavior

By default, Kustomize adds a hash suffix to generated ConfigMaps/Secrets:
- `app-config` becomes `app-config-abc123`
- References are automatically updated

Disable with:
```yaml
generatorOptions:
  disableNameSuffixHash: true
```

---

## Images

### Override Image Tags

```yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

resources:
- deployment.yaml

images:
- name: nginx
  newTag: "1.21"

- name: myapp
  newName: my-registry.com/myapp
  newTag: v2.0.0
```

---

## Patches

### Strategic Merge Patch

Add or modify fields:

```yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

resources:
- deployment.yaml

patches:
- patch: |-
    apiVersion: apps/v1
    kind: Deployment
    metadata:
      name: my-app
    spec:
      replicas: 5
```

### Patch from File

```yaml
patches:
- path: increase-replicas.yaml
```

**increase-replicas.yaml:**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-app
spec:
  replicas: 5
```

### JSON Patch

For precise modifications:

```yaml
patches:
- target:
    kind: Deployment
    name: my-app
  patch: |-
    - op: replace
      path: /spec/replicas
      value: 5
    - op: add
      path: /metadata/labels/version
      value: v2
```

> **What would happen if**: Your overlay references `../../base` but the base directory was renamed to `common`. What error do you get, and how quickly can you diagnose it?

### Patch All Deployments

```yaml
patches:
- target:
    kind: Deployment
  patch: |-
    - op: add
      path: /spec/template/spec/containers/0/resources
      value:
        limits:
          memory: 256Mi
          cpu: 200m
```

---

## Overlays

### Directory Structure

```
my-app/
├── base/
│   ├── kustomization.yaml
│   ├── deployment.yaml
│   └── service.yaml
├── overlays/
│   ├── dev/
│   │   └── kustomization.yaml
│   ├── staging/
│   │   └── kustomization.yaml
│   └── prod/
│       └── kustomization.yaml
```

### Base kustomization.yaml

```yaml
# base/kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

resources:
- deployment.yaml
- service.yaml
```

### Dev Overlay

```yaml
# overlays/dev/kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

resources:
- ../../base

namePrefix: dev-
namespace: development

patches:
- patch: |-
    apiVersion: apps/v1
    kind: Deployment
    metadata:
      name: my-app
    spec:
      replicas: 1

images:
- name: my-app
  newTag: dev-latest
```

### Prod Overlay

```yaml
# overlays/prod/kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

resources:
- ../../base

namePrefix: prod-
namespace: production

patches:
- patch: |-
    apiVersion: apps/v1
    kind: Deployment
    metadata:
      name: my-app
    spec:
      replicas: 5

images:
- name: my-app
  newTag: v1.2.3

configMapGenerator:
- name: app-config
  literals:
  - LOG_LEVEL=warn
  - ENABLE_DEBUG=false
```

### Apply Overlays

```bash
# Apply dev
kubectl apply -k overlays/dev/

# Apply prod
kubectl apply -k overlays/prod/

# Preview
kubectl kustomize overlays/prod/
```

---

## Exam Quick Reference

```bash
# Preview kustomization
kubectl kustomize ./

# Apply kustomization
kubectl apply -k ./

# Delete kustomization
kubectl delete -k ./

# View specific overlay
kubectl kustomize overlays/prod/
```

### Minimal kustomization.yaml

```yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
resources:
- deployment.yaml
```

### Common Customizations

```yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

resources:
- deployment.yaml
- service.yaml

namespace: my-namespace
namePrefix: prod-

commonLabels:
  app: my-app

images:
- name: nginx
  newTag: "1.21"

configMapGenerator:
- name: config
  literals:
  - KEY=value
```

---

## Did You Know?

- **Kustomize is built into kubectl** since version 1.14. You don't need to install anything extra—just use `kubectl apply -k`.

- **Hash suffixes on ConfigMaps/Secrets ensure updates propagate.** When content changes, the hash changes, creating a new ConfigMap. Deployments referencing it automatically update.

- **Kustomize vs Helm**: Kustomize is simpler (no templates, no variables), while Helm is more powerful (conditionals, loops, packaging). Use Kustomize for simple overlays; use Helm for complex applications.

---

## Common Mistakes

| Mistake | Why It Hurts | Solution |
|---------|--------------|----------|
| Wrong path to base | Resources not found | Use relative paths (`../../base`) |
| Patch target name mismatch | Patch doesn't apply | Match exact resource name |
| Missing `apiVersion` in kustomization | Invalid file | Always include version |
| Forgetting `resources` section | Nothing deployed | List all resource files |
| Not previewing before apply | Unexpected results | Always run `kubectl kustomize` first |

---

## Quiz

1. **Your team has a base deployment that works perfectly in dev. For production, you need to: change the namespace to `production`, increase replicas to 5, and use image tag `v2.1.0` instead of `latest`. You want to do this without modifying the base files. How do you set this up with Kustomize?**
   <details>
   <summary>Answer</summary>
   Create an overlay directory (e.g., `overlays/prod/kustomization.yaml`) that references the base and adds customizations:
   ```yaml
   apiVersion: kustomize.config.k8s.io/v1beta1
   kind: Kustomization
   resources:
   - ../../base
   namespace: production
   images:
   - name: nginx
     newTag: "v2.1.0"
   patches:
   - patch: |-
       apiVersion: apps/v1
       kind: Deployment
       metadata:
         name: web-app
       spec:
         replicas: 5
   ```
   Apply with `kubectl apply -k overlays/prod/`. The base files remain untouched, and each environment gets its own overlay with specific customizations.
   </details>

2. **You run `kubectl apply -k ./` but get an error: "no such file or directory" for a resource listed in kustomization.yaml. The file definitely exists when you `ls` the directory. What are the two most common causes of this error?**
   <details>
   <summary>Answer</summary>
   The two most common causes are: (1) a path mismatch -- the filename in `resources:` doesn't match the actual filename (case sensitivity, typo, or `.yaml` vs `.yml` extension); (2) the `kustomization.yaml` references a base using a relative path like `../../base` but you're running the command from the wrong directory. Always run `kubectl kustomize ./` first to preview and debug before applying. Check that paths in `resources:` match exactly, including case. On the exam, typos in resource paths are a common time waster.
   </details>

3. **A colleague asks: "Why not just use Helm for everything? Why would I use Kustomize?" Give them two concrete scenarios where Kustomize is the better choice.**
   <details>
   <summary>Answer</summary>
   Kustomize is better when: (1) You have existing YAML manifests and just need environment-specific variations (dev/staging/prod) without learning a template language -- Kustomize works directly with valid Kubernetes YAML, no `{{ .Values }}` syntax needed, making it simpler and less error-prone for straightforward overlays. (2) You want to customize a third-party tool's generated YAML without forking it -- Kustomize can patch any Kubernetes resource as a post-processing step. Additionally, Kustomize is built into kubectl (no extra tooling to install), which matters in restricted environments and on the CKAD exam where Helm may not always be the expected approach.
   </details>

4. **You use `configMapGenerator` in your kustomization.yaml to create a ConfigMap. After updating a literal value and reapplying, you notice TWO ConfigMaps in the namespace -- the old one and a new one with a different hash suffix. Your Deployment picked up the new one, but the old ConfigMap is still there. Is this a bug?**
   <details>
   <summary>Answer</summary>
   This is not a bug -- it's by design. Kustomize generates ConfigMaps with a content-based hash suffix (e.g., `app-config-abc123`). When content changes, a new ConfigMap with a new hash is created, and the Deployment reference is automatically updated to point to the new one, triggering a rolling update. The old ConfigMap remains for rollback safety -- if you roll back the Deployment, it still references the old ConfigMap. Clean up orphaned ConfigMaps manually with `kubectl delete cm <old-name>` or use a garbage collection tool. This hash-based approach guarantees pods always get the correct config version.
   </details>

---

## Hands-On Exercise

**Task**: Create a complete Kustomize setup with base and overlays.

**Part 1: Create Base**

```bash
mkdir -p /tmp/kustomize-demo/base
cd /tmp/kustomize-demo

# Create deployment
cat << 'EOF' > base/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web-app
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
      - name: nginx
        image: nginx:1.20
        ports:
        - containerPort: 80
EOF

# Create service
cat << 'EOF' > base/service.yaml
apiVersion: v1
kind: Service
metadata:
  name: web-app
spec:
  selector:
    app: web
  ports:
  - port: 80
EOF

# Create base kustomization
cat << 'EOF' > base/kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
resources:
- deployment.yaml
- service.yaml
EOF
```

**Part 2: Create Dev Overlay**

```bash
mkdir -p overlays/dev

cat << 'EOF' > overlays/dev/kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

resources:
- ../../base

namePrefix: dev-
namespace: development

images:
- name: nginx
  newTag: "1.21"

configMapGenerator:
- name: app-config
  literals:
  - ENV=development
  - DEBUG=true
EOF
```

**Part 3: Create Prod Overlay**

```bash
mkdir -p overlays/prod

cat << 'EOF' > overlays/prod/kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

resources:
- ../../base

namePrefix: prod-
namespace: production

patches:
- patch: |-
    apiVersion: apps/v1
    kind: Deployment
    metadata:
      name: web-app
    spec:
      replicas: 3

images:
- name: nginx
  newTag: "1.22"

configMapGenerator:
- name: app-config
  literals:
  - ENV=production
  - DEBUG=false
EOF
```

**Part 4: Preview and Apply**

```bash
# Preview dev
kubectl kustomize overlays/dev/

# Preview prod
kubectl kustomize overlays/prod/

# Apply dev (create namespace first)
kubectl create ns development
kubectl apply -k overlays/dev/

# Verify
kubectl get all -n development

# Cleanup
kubectl delete -k overlays/dev/
kubectl delete ns development
```

---

## Practice Drills

### Drill 1: Basic Kustomization (Target: 3 minutes)

```bash
mkdir -p /tmp/drill1 && cd /tmp/drill1

# Create deployment
cat << 'EOF' > deployment.yaml
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

# Create kustomization
cat << 'EOF' > kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
resources:
- deployment.yaml
namespace: default
commonLabels:
  environment: test
EOF

# Preview
kubectl kustomize ./

# Apply
kubectl apply -k ./

# Cleanup
kubectl delete -k ./
```

### Drill 2: Image Override (Target: 2 minutes)

```bash
mkdir -p /tmp/drill2 && cd /tmp/drill2

cat << 'EOF' > deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: app
spec:
  selector:
    matchLabels:
      app: app
  template:
    metadata:
      labels:
        app: app
    spec:
      containers:
      - name: app
        image: nginx:1.19
EOF

cat << 'EOF' > kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
resources:
- deployment.yaml
images:
- name: nginx
  newTag: "1.22"
EOF

# Verify image changed
kubectl kustomize ./ | grep image

# Cleanup
cd /tmp && rm -rf drill2
```

### Drill 3: ConfigMap Generator (Target: 3 minutes)

```bash
mkdir -p /tmp/drill3 && cd /tmp/drill3

cat << 'EOF' > deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: app
spec:
  selector:
    matchLabels:
      app: app
  template:
    metadata:
      labels:
        app: app
    spec:
      containers:
      - name: app
        image: nginx
        envFrom:
        - configMapRef:
            name: app-config
EOF

cat << 'EOF' > kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
resources:
- deployment.yaml
configMapGenerator:
- name: app-config
  literals:
  - DATABASE_URL=postgres://localhost
  - LOG_LEVEL=debug
EOF

# Preview - notice hash suffix
kubectl kustomize ./

# Cleanup
cd /tmp && rm -rf drill3
```

### Drill 4: Patches (Target: 4 minutes)

```bash
mkdir -p /tmp/drill4 && cd /tmp/drill4

cat << 'EOF' > deployment.yaml
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
      - name: nginx
        image: nginx
EOF

cat << 'EOF' > kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
resources:
- deployment.yaml
patches:
- patch: |-
    apiVersion: apps/v1
    kind: Deployment
    metadata:
      name: web
    spec:
      replicas: 3
      template:
        spec:
          containers:
          - name: nginx
            resources:
              limits:
                memory: 128Mi
                cpu: 100m
EOF

# Verify patch applied
kubectl kustomize ./

# Cleanup
cd /tmp && rm -rf drill4
```

### Drill 5: Name Prefix and Namespace (Target: 2 minutes)

```bash
mkdir -p /tmp/drill5 && cd /tmp/drill5

cat << 'EOF' > deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: app
spec:
  selector:
    matchLabels:
      app: app
  template:
    metadata:
      labels:
        app: app
    spec:
      containers:
      - name: nginx
        image: nginx
EOF

cat << 'EOF' > kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
resources:
- deployment.yaml
namePrefix: staging-
namespace: staging
commonLabels:
  env: staging
EOF

# Verify transformations
kubectl kustomize ./

# Cleanup
cd /tmp && rm -rf drill5
```

### Drill 6: Complete Overlay Scenario (Target: 6 minutes)

```bash
mkdir -p /tmp/drill6/{base,overlays/dev,overlays/prod}
cd /tmp/drill6

# Base
cat << 'EOF' > base/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api
spec:
  replicas: 1
  selector:
    matchLabels:
      app: api
  template:
    metadata:
      labels:
        app: api
    spec:
      containers:
      - name: api
        image: my-api:latest
        ports:
        - containerPort: 8080
EOF

cat << 'EOF' > base/kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
resources:
- deployment.yaml
EOF

# Dev overlay
cat << 'EOF' > overlays/dev/kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
resources:
- ../../base
namePrefix: dev-
namespace: dev
images:
- name: my-api
  newTag: dev-latest
EOF

# Prod overlay
cat << 'EOF' > overlays/prod/kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
resources:
- ../../base
namePrefix: prod-
namespace: prod
images:
- name: my-api
  newTag: v1.0.0
patches:
- patch: |-
    apiVersion: apps/v1
    kind: Deployment
    metadata:
      name: api
    spec:
      replicas: 3
EOF

# Compare outputs
echo "=== DEV ===" && kubectl kustomize overlays/dev/
echo "=== PROD ===" && kubectl kustomize overlays/prod/

# Cleanup
cd /tmp && rm -rf drill6
```

---

## Next Module

[Module 2.4: Deployment Strategies](../module-2.4-deployment-strategies/) - Blue/green, canary, and rolling deployment patterns.
