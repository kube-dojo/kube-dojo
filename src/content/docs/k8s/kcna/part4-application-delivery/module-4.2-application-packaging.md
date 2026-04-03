---
title: "Module 4.2: Application Packaging"
slug: k8s/kcna/part4-application-delivery/module-4.2-application-packaging
sidebar:
  order: 3
---
> **Complexity**: `[MEDIUM]` - Tool concepts
>
> **Time to Complete**: 25-30 minutes
>
> **Prerequisites**: Module 4.1 (CI/CD Fundamentals)

---

## What You'll Be Able to Do

After completing this module, you will be able to:

1. **Compare** Helm and Kustomize as Kubernetes application packaging approaches
2. **Explain** Helm chart structure: templates, values, and release lifecycle
3. **Identify** when to use Helm charts vs. Kustomize overlays for different management scenarios
4. **Evaluate** packaging strategies for multi-environment deployments (dev, staging, production)

---

## Why This Module Matters

Raw Kubernetes manifests become hard to manage at scale. **Helm**, **Kustomize**, and other tools help package, configure, and deploy applications. KCNA tests your understanding of these packaging approaches and when to use them.

---

## The Problem with Raw Manifests

```
┌─────────────────────────────────────────────────────────────┐
│              THE MANIFEST PROBLEM                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Managing many YAML files:                                 │
│  ─────────────────────────────────────────────────────────  │
│                                                             │
│  my-app/                                                   │
│  ├── deployment.yaml                                      │
│  ├── service.yaml                                         │
│  ├── configmap.yaml                                       │
│  ├── secret.yaml                                          │
│  ├── ingress.yaml                                         │
│  └── pvc.yaml                                             │
│                                                             │
│  Problems:                                                 │
│  ─────────────────────────────────────────────────────────  │
│                                                             │
│  1. DUPLICATION                                           │
│     Same app for dev/staging/prod = 3x files              │
│     Only difference: image tag, replicas, resources       │
│                                                             │
│  2. NO TEMPLATING                                         │
│     Can't parameterize values                              │
│     Hardcoded everywhere                                  │
│                                                             │
│  3. NO VERSIONING                                         │
│     What version is deployed?                             │
│     How to rollback?                                      │
│                                                             │
│  4. NO DEPENDENCIES                                       │
│     App needs Redis → manage separately                   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Helm

```
┌─────────────────────────────────────────────────────────────┐
│              HELM                                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  "The package manager for Kubernetes"                     │
│  CNCF Graduated project                                   │
│                                                             │
│  Key concepts:                                             │
│  ─────────────────────────────────────────────────────────  │
│                                                             │
│  CHART                                                     │
│  Package containing Kubernetes resources                  │
│  Templates + values + metadata                            │
│                                                             │
│  RELEASE                                                   │
│  Instance of a chart in a cluster                         │
│  Same chart can have multiple releases                    │
│                                                             │
│  REPOSITORY                                                │
│  Collection of charts (like npm registry)                │
│                                                             │
│  Chart structure:                                         │
│  ─────────────────────────────────────────────────────────  │
│                                                             │
│  my-app/                                                   │
│  ├── Chart.yaml          # Metadata (name, version)      │
│  ├── values.yaml         # Default values                │
│  ├── templates/                                           │
│  │   ├── deployment.yaml                                 │
│  │   ├── service.yaml                                    │
│  │   └── _helpers.tpl                                   │
│  └── charts/             # Dependencies                   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Helm Templating

```
┌─────────────────────────────────────────────────────────────┐
│              HELM TEMPLATING                                │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Template (templates/deployment.yaml):                    │
│  ─────────────────────────────────────────────────────────  │
│                                                             │
│  apiVersion: apps/v1                                      │
│  kind: Deployment                                          │
│  metadata:                                                 │
│    name: {{ .Release.Name }}-app                         │
│  spec:                                                     │
│    replicas: {{ .Values.replicas }}                      │
│    template:                                               │
│      spec:                                                 │
│        containers:                                         │
│        - name: app                                        │
│          image: {{ .Values.image.repository }}:{{         │
│                    .Values.image.tag }}                   │
│          resources:                                        │
│            {{- toYaml .Values.resources | nindent 12 }}  │
│                                                             │
│  Values (values.yaml):                                    │
│  ─────────────────────────────────────────────────────────  │
│                                                             │
│  replicas: 3                                               │
│  image:                                                    │
│    repository: nginx                                      │
│    tag: 1.25                                              │
│  resources:                                                │
│    limits:                                                 │
│      cpu: 100m                                            │
│      memory: 128Mi                                        │
│                                                             │
│  Override values:                                         │
│  ─────────────────────────────────────────────────────────  │
│  helm install my-release ./my-app \                       │
│    --set replicas=5 \                                     │
│    --set image.tag=1.26                                   │
│                                                             │
│  Or use values file:                                      │
│  helm install my-release ./my-app -f prod-values.yaml    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Helm Commands

| Command | Purpose |
|---------|---------|
| `helm install` | Install a chart |
| `helm upgrade` | Upgrade a release |
| `helm rollback` | Rollback to previous version |
| `helm uninstall` | Remove a release |
| `helm list` | List releases |
| `helm repo add` | Add chart repository |
| `helm search` | Search for charts |

---

## Kustomize

```
┌─────────────────────────────────────────────────────────────┐
│              KUSTOMIZE                                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  "Kubernetes native configuration management"             │
│  Built into kubectl (kubectl apply -k)                    │
│                                                             │
│  Key difference from Helm:                                │
│  ─────────────────────────────────────────────────────────  │
│  • NO templating                                          │
│  • Uses overlays and patches                              │
│  • Pure Kubernetes YAML                                   │
│                                                             │
│  Structure:                                                │
│  ─────────────────────────────────────────────────────────  │
│                                                             │
│  my-app/                                                   │
│  ├── base/                    # Common resources          │
│  │   ├── kustomization.yaml                              │
│  │   ├── deployment.yaml                                 │
│  │   └── service.yaml                                    │
│  └── overlays/                                            │
│      ├── dev/                 # Dev-specific             │
│      │   ├── kustomization.yaml                          │
│      │   └── replica-patch.yaml                          │
│      └── prod/                # Prod-specific            │
│          ├── kustomization.yaml                          │
│          └── replica-patch.yaml                          │
│                                                             │
│  How it works:                                            │
│  ─────────────────────────────────────────────────────────  │
│                                                             │
│  Base: The original resources                             │
│  Overlay: Modifications applied on top of base           │
│                                                             │
│        [Base]                                              │
│           │                                                │
│     ┌─────┴─────┐                                         │
│     ▼           ▼                                         │
│  [Overlay:   [Overlay:                                    │
│   Dev]       Prod]                                        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Kustomize Example

```
┌─────────────────────────────────────────────────────────────┐
│              KUSTOMIZE EXAMPLE                              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  base/kustomization.yaml:                                 │
│  ─────────────────────────────────────────────────────────  │
│  apiVersion: kustomize.config.k8s.io/v1beta1             │
│  kind: Kustomization                                      │
│  resources:                                                │
│  - deployment.yaml                                        │
│  - service.yaml                                           │
│                                                             │
│  overlays/prod/kustomization.yaml:                        │
│  ─────────────────────────────────────────────────────────  │
│  apiVersion: kustomize.config.k8s.io/v1beta1             │
│  kind: Kustomization                                      │
│  resources:                                                │
│  - ../../base                                             │
│  namePrefix: prod-                                        │
│  replicas:                                                 │
│  - name: my-app                                           │
│    count: 5                                               │
│  images:                                                   │
│  - name: nginx                                            │
│    newTag: "1.26"                                         │
│                                                             │
│  Apply:                                                   │
│  ─────────────────────────────────────────────────────────  │
│  kubectl apply -k overlays/prod/                         │
│                                                             │
│  Kustomize features:                                      │
│  • namePrefix/nameSuffix: Add prefix to all names        │
│  • namespace: Set namespace for all resources            │
│  • images: Override image tags                           │
│  • replicas: Override replica counts                     │
│  • patches: Modify any field                             │
│  • configMapGenerator: Create ConfigMaps from files      │
│  • secretGenerator: Create Secrets from files            │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Helm vs Kustomize

```
┌─────────────────────────────────────────────────────────────┐
│              HELM vs KUSTOMIZE                              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  HELM:                                                     │
│  ─────────────────────────────────────────────────────────  │
│  + Powerful templating                                    │
│  + Package versioning                                     │
│  + Dependency management                                  │
│  + Large ecosystem (Artifact Hub)                        │
│  + Release tracking                                       │
│  - Complex template syntax                                │
│  - Must learn Go templating                              │
│                                                             │
│  KUSTOMIZE:                                               │
│  ─────────────────────────────────────────────────────────  │
│  + No templating = pure YAML                             │
│  + Built into kubectl                                     │
│  + Easy to understand                                     │
│  + No new syntax to learn                                 │
│  - Limited compared to templating                        │
│  - No package versioning                                 │
│  - No dependency management                               │
│                                                             │
│  When to use what:                                        │
│  ─────────────────────────────────────────────────────────  │
│                                                             │
│  Helm:                                                     │
│  • Distributing apps to others                           │
│  • Complex templating needs                              │
│  • Need dependency management                             │
│  • Using third-party charts                              │
│                                                             │
│  Kustomize:                                               │
│  • Internal apps with environment variations             │
│  • Simple overlays (dev/staging/prod)                    │
│  • Teams unfamiliar with templating                      │
│  • GitOps workflows                                       │
│                                                             │
│  Both together:                                            │
│  • Helm for base chart                                    │
│  • Kustomize for environment overlays                    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Other Packaging Tools

```
┌─────────────────────────────────────────────────────────────┐
│              OTHER TOOLS                                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  JSONNET / TANKA                                          │
│  ─────────────────────────────────────────────────────────  │
│  • Data templating language                               │
│  • Generate JSON/YAML programmatically                   │
│  • Used by Grafana Labs                                   │
│                                                             │
│  CUE                                                      │
│  ─────────────────────────────────────────────────────────  │
│  • Configuration language                                 │
│  • Strong typing and validation                          │
│  • Merge-able configurations                             │
│                                                             │
│  CARVEL (formerly k14s)                                   │
│  ─────────────────────────────────────────────────────────  │
│  • ytt: YAML templating                                  │
│  • kbld: Image building/resolving                        │
│  • kapp: Deployment tool                                 │
│  • CNCF sandbox project                                  │
│                                                             │
│  OPERATORS                                                │
│  ─────────────────────────────────────────────────────────  │
│  • For complex stateful apps                             │
│  • Custom controllers                                    │
│  • Beyond simple packaging                               │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Artifact Hub

```
┌─────────────────────────────────────────────────────────────┐
│              ARTIFACT HUB                                   │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  artifacthub.io                                           │
│  CNCF project                                              │
│                                                             │
│  Central repository for:                                  │
│  ─────────────────────────────────────────────────────────  │
│  • Helm charts                                            │
│  • OPA policies                                           │
│  • Falco rules                                            │
│  • OLM operators                                          │
│  • And more...                                            │
│                                                             │
│  Use it to:                                               │
│  • Find charts for popular applications                  │
│  • Discover alternatives                                  │
│  • Check chart quality/security                          │
│                                                             │
│  Example: Need PostgreSQL?                                │
│  → Search "postgresql" on Artifact Hub                   │
│  → Find Bitnami chart                                    │
│  → helm repo add bitnami https://charts.bitnami.com/...  │
│  → helm install my-postgres bitnami/postgresql          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Did You Know?

- **Helm v3 removed Tiller** - Helm v2 required a server component (Tiller) in the cluster. Helm v3 removed it for better security.

- **Kustomize is built into kubectl** - Since Kubernetes 1.14, you can use `kubectl apply -k` without installing Kustomize separately.

- **Helm uses Go templates** - If you know Go's text/template package, you'll find Helm templating familiar.

- **Charts can have dependencies** - A chart can depend on other charts, automatically installed together (like npm packages).

---

## Common Mistakes

| Mistake | Why It Hurts | Correct Understanding |
|---------|--------------|----------------------|
| Duplicating manifests for envs | Hard to maintain | Use Helm values or Kustomize overlays |
| Complex Helm templates | Hard to debug | Keep templates simple |
| Not versioning charts | Can't track changes | Use semantic versioning |
| Hardcoded secrets | Security risk | Use external secret management |

---

## Quiz

1. **What is a Helm chart?**
   <details>
   <summary>Answer</summary>
   A package containing Kubernetes resources (templates), default values, and metadata. It's like a package in npm or apt, but for Kubernetes applications. Charts can be versioned, shared, and have dependencies.
   </details>

2. **How does Kustomize differ from Helm?**
   <details>
   <summary>Answer</summary>
   Kustomize uses overlays and patches on plain YAML—no templating. Helm uses Go templating to generate YAML. Kustomize is simpler but less powerful. Kustomize is built into kubectl; Helm is a separate tool.
   </details>

3. **What is a Helm release?**
   <details>
   <summary>Answer</summary>
   An instance of a chart installed in a cluster. The same chart can be installed multiple times with different release names. Helm tracks release history for upgrades and rollbacks.
   </details>

4. **What is the Artifact Hub?**
   <details>
   <summary>Answer</summary>
   A CNCF project that serves as a central repository for finding and sharing cloud native artifacts, including Helm charts, OPA policies, Falco rules, and operators. It's like a search engine for Kubernetes packages.
   </details>

5. **When would you use Kustomize instead of Helm?**
   <details>
   <summary>Answer</summary>
   For internal applications with simple environment variations (dev/staging/prod), when teams prefer plain YAML over templating, or for GitOps workflows. Kustomize is also built into kubectl, requiring no additional tooling.
   </details>

---

## Summary

**The problem**:
- Raw manifests don't scale
- Duplication, no parameterization
- No versioning or dependencies

**Helm**:
- Package manager for Kubernetes
- Templates + values + charts
- Powerful but complex

**Kustomize**:
- Overlays and patches
- No templating
- Built into kubectl

**When to use**:
- **Helm**: Distributing apps, complex templating, dependencies
- **Kustomize**: Internal apps, simple environment overlays
- **Both**: Helm chart + Kustomize overlays

**Artifact Hub**:
- Find Helm charts and other artifacts
- Central CNCF repository

---

## KCNA Curriculum Complete!

Congratulations! You've completed the entire KCNA curriculum covering:

| Part | Topic | Weight |
|------|-------|--------|
| Part 1 | Kubernetes Fundamentals | 44% |
| Part 2 | Container Orchestration | 28% |
| Part 3 | Cloud Native Architecture (incl. Observability) | 12% |
| Part 4 | Application Delivery | 16% |

*Updated November 2025: Observability merged into Cloud Native Architecture*

**Next steps**:
1. Review weak areas
2. Take practice quizzes
3. Study CNCF landscape
4. Schedule your exam!

Good luck on your KCNA certification!
