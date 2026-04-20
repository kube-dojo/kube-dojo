---
title: "Module 2.4: Helm & Kustomize"
slug: platform/toolkits/cicd-delivery/gitops-deployments/module-2.4-helm-kustomize
sidebar:
  order: 5
---
> **Toolkit Track** | Complexity: `[MEDIUM]` | Time: 35-40 min

A team had copied production manifests across multiple environments and ended up with configuration drift across nearly identical YAML files. After consolidating the setup with Helm charts and Kustomize overlays, they were able to deploy more frequently and reduce drift-related debugging.

## Prerequisites

Before starting this module:
- [Module 2.1: ArgoCD](../module-2.1-argocd/) or [Module 2.3: Flux](../module-2.3-flux/)
- Basic Kubernetes YAML knowledge
- Understanding of templating concepts

## What You'll Be Able to Do

After completing this module, you will be able to:

- **Configure Helm charts with values files for multi-environment deployments (dev, staging, production)**
- **Implement Kustomize overlays to patch Kubernetes manifests without modifying base configurations**
- **Integrate Helm and Kustomize together for template rendering with environment-specific patches**
- **Evaluate when to use Helm charts versus Kustomize overlays based on team and project requirements**


## Why This Module Matters

Raw Kubernetes YAML doesn't scale. When you have 50 services, each with development, staging, and production variants, you need a way to manage configuration. Helm and Kustomize are the two dominant solutions—and they work together beautifully.

[Helm packages applications as charts with templates](https://helm.sh/docs/topics/charts/). [Kustomize overlays modifications without templates](https://github.com/kubernetes-sigs/kustomize). Understanding both—and when to use each—is essential for Kubernetes operations.

## Did You Know?

- **[Helm v3 removed Tiller entirely](https://helm.sh/docs/v3/faq/changes_since_helm2/)**—Helm v2's server-side component was a security concern; now Helm is purely client-side
- **[Kustomize is built into kubectl](https://kubernetes.io/docs/tasks/manage-kubernetes-objects/kustomization)**—since 1.14, you can use `kubectl apply -k` without installing anything
- **Helm uses nautical branding consistent with the Kubernetes ecosystem**
- **Kustomize emerged from the Kubernetes ecosystem as a template-free way to customize configurations**

## Helm vs Kustomize

```
┌─────────────────────────────────────────────────────────────────┐
│                    HELM vs KUSTOMIZE                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  HELM                              KUSTOMIZE                     │
│  ────                              ─────────                     │
│                                                                  │
│  Model: Packaging                  Model: Patching               │
│  • Chart = package                 • Base + overlays             │
│  • Templates + values              • No templates                │
│  • Releases tracked                • Pure YAML                   │
│                                                                  │
│  Good for:                         Good for:                     │
│  • Third-party apps                • Your own apps               │
│  • Complex applications            • Environment variants        │
│  • Version management              • Last-mile customization     │
│  • Sharing across teams            • Patching Helm output        │
│                                                                  │
│  Template syntax:                  Patch syntax:                 │
│  {{ .Values.replicas }}            - op: replace                 │
│                                      path: /spec/replicas        │
│                                      value: 3                    │
│                                                                  │
│  BEST PRACTICE: Use together!                                   │
│  Helm for packages → Kustomize for environment-specific patches │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### A Note on Jsonnet

Beyond Helm and Kustomize, **Jsonnet** is a data templating language that some teams use to generate Kubernetes manifests. [Grafana Labs uses Jsonnet extensively for their Kubernetes deployments](https://grafana.com/blog/how-the-jsonnet-based-project-tanka-improves-kubernetes-usage/), and you may also encounter it in GitOps-focused materials and projects. Jsonnet treats configuration as programmable data rather than text templates -- you write functions and objects that evaluate to JSON/YAML.

In practice, Jsonnet has a smaller community than Helm or Kustomize, and most organizations choose one of the two dominant tools. However, if you encounter a project using Jsonnet (or the Kubernetes configuration tool **Tanka**), understand that it solves the same problem -- reducing YAML duplication -- with a different paradigm: a full programming language for configuration rather than templates (Helm) or patches (Kustomize).

## Helm Fundamentals

### Chart Structure

```
my-app/
├── Chart.yaml          # Metadata
├── values.yaml         # Default values
├── charts/             # Dependencies
├── templates/
│   ├── deployment.yaml
│   ├── service.yaml
│   ├── ingress.yaml
│   ├── configmap.yaml
│   ├── _helpers.tpl    # Template helpers
│   ├── NOTES.txt       # Post-install notes
│   └── tests/
│       └── test-connection.yaml
└── README.md
```

### Chart.yaml

```yaml
apiVersion: v2
name: my-app
description: A Helm chart for my application
type: application  # or "library"
version: 1.0.0     # Chart version
appVersion: "2.3.1"  # App version

keywords:
  - app
  - web

home: https://github.com/org/my-app
sources:
  - https://github.com/org/my-app

maintainers:
  - name: Platform Team
    email: platform@example.com

dependencies:
  - name: postgresql
    version: "12.x"
    repository: https://charts.bitnami.com/bitnami
    condition: postgresql.enabled
```

### values.yaml

```yaml
# values.yaml - defaults
replicaCount: 1

image:
  repository: myapp
  tag: "latest"
  pullPolicy: IfNotPresent

service:
  type: ClusterIP
  port: 80

ingress:
  enabled: false
  className: nginx
  hosts:
    - host: myapp.local
      paths:
        - path: /
          pathType: Prefix

resources:
  limits:
    cpu: 100m
    memory: 128Mi
  requests:
    cpu: 50m
    memory: 64Mi

postgresql:
  enabled: true
  auth:
    database: myapp
```

### Template Syntax

```yaml
# templates/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ include "my-app.fullname" . }}
  labels:
    {{- include "my-app.labels" . | nindent 4 }}
spec:
  replicas: {{ .Values.replicaCount }}
  selector:
    matchLabels:
      {{- include "my-app.selectorLabels" . | nindent 6 }}
  template:
    metadata:
      labels:
        {{- include "my-app.selectorLabels" . | nindent 8 }}
    spec:
      containers:
        - name: {{ .Chart.Name }}
          image: "{{ .Values.image.repository }}:{{ .Values.image.tag }}"
          imagePullPolicy: {{ .Values.image.pullPolicy }}
          ports:
            - name: http
              containerPort: 80
          {{- if .Values.resources }}
          resources:
            {{- toYaml .Values.resources | nindent 12 }}
          {{- end }}
          {{- if .Values.env }}
          env:
            {{- range $key, $value := .Values.env }}
            - name: {{ $key }}
              value: {{ $value | quote }}
            {{- end }}
          {{- end }}
```

### Template Helpers

```yaml
# templates/_helpers.tpl
{{/*
Expand the name of the chart.
*/}}
{{- define "my-app.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
*/}}
{{- define "my-app.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "my-app.labels" -}}
helm.sh/chart: {{ include "my-app.chart" . }}
{{ include "my-app.selectorLabels" . }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "my-app.selectorLabels" -}}
app.kubernetes.io/name: {{ include "my-app.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}
```

### Helm Commands

```bash
# Create new chart
helm create my-app

# Lint chart
helm lint my-app/

# Template locally (dry-run)
helm template my-release my-app/ -f values-prod.yaml

# Install
helm install my-release my-app/ \
  --namespace production \
  --create-namespace \
  -f values-prod.yaml

# Upgrade
helm upgrade my-release my-app/ \
  --namespace production \
  -f values-prod.yaml

# Rollback
helm rollback my-release 1 --namespace production

# List releases
helm list --all-namespaces

# Get release values
helm get values my-release --namespace production

# Uninstall
helm uninstall my-release --namespace production

# Package chart
helm package my-app/

# Push to OCI registry
helm push my-app-1.0.0.tgz oci://ghcr.io/org/charts
```

### Helm Dependencies

```bash
# Update dependencies
helm dependency update my-app/

# Build dependencies
helm dependency build my-app/
```

```yaml
# Chart.yaml
dependencies:
  - name: postgresql
    version: "12.1.0"
    repository: https://charts.bitnami.com/bitnami
    condition: postgresql.enabled
    tags:
      - database

  - name: redis
    version: "17.x"
    repository: https://charts.bitnami.com/bitnami
    condition: redis.enabled
```

```yaml
# values.yaml
postgresql:
  enabled: true
  primary:
    persistence:
      size: 10Gi

redis:
  enabled: false
```

## Kustomize Fundamentals

### Directory Structure

```
my-app/
├── base/
│   ├── kustomization.yaml
│   ├── deployment.yaml
│   ├── service.yaml
│   └── configmap.yaml
└── overlays/
    ├── development/
    │   ├── kustomization.yaml
    │   └── replica-patch.yaml
    ├── staging/
    │   ├── kustomization.yaml
    │   └── namespace.yaml
    └── production/
        ├── kustomization.yaml
        ├── replica-patch.yaml
        └── ingress.yaml
```

### Base kustomization.yaml

```yaml
# base/kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

resources:
  - deployment.yaml
  - service.yaml
  - configmap.yaml

# Common labels for all resources
commonLabels:
  app: my-app

# Common annotations
commonAnnotations:
  team: platform
```

### Overlay kustomization.yaml

```yaml
# overlays/production/kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

namespace: production
namePrefix: prod-

resources:
  - ../../base
  - ingress.yaml

# Strategic merge patches
patches:
  - path: replica-patch.yaml

# Or inline patches
patches:
  - patch: |-
      - op: replace
        path: /spec/replicas
        value: 5
    target:
      kind: Deployment
      name: my-app

# Image overrides
images:
  - name: myapp
    newName: myregistry/myapp
    newTag: v2.0.0

# ConfigMap/Secret generators
configMapGenerator:
  - name: app-config
    literals:
      - ENVIRONMENT=production
      - LOG_LEVEL=info

secretGenerator:
  - name: app-secrets
    literals:
      - DATABASE_URL=postgres://prod-db:5432/app
    type: Opaque
```

### Patch Types

```yaml
# Strategic Merge Patch (default)
# replica-patch.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-app
spec:
  replicas: 5

---
# JSON Patch
# kustomization.yaml
patches:
  - patch: |-
      - op: replace
        path: /spec/replicas
        value: 5
      - op: add
        path: /metadata/labels/env
        value: production
    target:
      kind: Deployment
      name: my-app

---
# Patch file with target
# kustomization.yaml
patches:
  - path: increase-memory.yaml
    target:
      kind: Deployment
      labelSelector: "app=my-app"
```

### Components (Reusable Patches)

```yaml
# components/monitoring/kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1alpha1
kind: Component

patches:
  - patch: |-
      - op: add
        path: /spec/template/metadata/annotations/prometheus.io~1scrape
        value: "true"
      - op: add
        path: /spec/template/metadata/annotations/prometheus.io~1port
        value: "8080"
    target:
      kind: Deployment

---
# overlays/production/kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

resources:
  - ../../base

components:
  - ../../components/monitoring
  - ../../components/security
```

### Replacements (Variable Substitution)

```yaml
# kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

resources:
  - deployment.yaml
  - configmap.yaml

replacements:
  - source:
      kind: ConfigMap
      name: app-config
      fieldPath: data.HOSTNAME
    targets:
      - select:
          kind: Deployment
          name: my-app
        fieldPaths:
          - spec.template.spec.containers.[name=app].env.[name=HOSTNAME].value
```

### Kustomize Commands

```bash
# Build (render YAML)
kustomize build overlays/production

# Apply
kubectl apply -k overlays/production

# Preview diff
kubectl diff -k overlays/production

# View resources
kustomize build overlays/production | kubectl get -f - -o name
```

## Helm + Kustomize Together

### Pattern: Kustomize Wrapping Helm

```
my-deployment/
├── base/
│   ├── kustomization.yaml
│   └── helmrelease.yaml      # Flux HelmRelease or ArgoCD Application
└── overlays/
    ├── staging/
    │   ├── kustomization.yaml
    │   └── values-patch.yaml
    └── production/
        ├── kustomization.yaml
        └── values-patch.yaml
```

### ArgoCD: Helm + Kustomize

```yaml
# ArgoCD Application using both
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: my-app
spec:
  source:
    repoURL: https://charts.example.com
    chart: my-app
    targetRevision: 1.0.0

    # Helm values
    helm:
      values: |
        replicaCount: 3

    # Plus Kustomize patches
    kustomize:
      patches:
        - patch: |-
            - op: add
              path: /metadata/annotations
              value:
                custom.annotation: "true"
          target:
            kind: Deployment
```

### Flux: Post-Rendering with Kustomize

```yaml
# HelmRelease with post-rendering
apiVersion: helm.toolkit.fluxcd.io/v2
kind: HelmRelease
metadata:
  name: my-app
spec:
  chart:
    spec:
      chart: my-app
      sourceRef:
        kind: HelmRepository
        name: my-charts

  values:
    replicaCount: 3

  # Post-render with Kustomize
  postRenderers:
    - kustomize:
        patches:
          - patch: |-
              - op: add
                path: /metadata/labels/custom
                value: label
            target:
              kind: Deployment

        images:
          - name: my-app
            newTag: v2.0.0-custom
```

### Umbrella Chart Pattern

```yaml
# Chart.yaml - umbrella chart
apiVersion: v2
name: platform
version: 1.0.0

dependencies:
  - name: cert-manager
    version: "1.13.0"
    repository: https://charts.jetstack.io
    condition: cert-manager.enabled

  - name: ingress-nginx
    version: "4.8.0"
    repository: https://kubernetes.github.io/ingress-nginx
    condition: ingress-nginx.enabled

  - name: prometheus
    version: "25.0.0"
    repository: https://prometheus-community.github.io/helm-charts
    condition: prometheus.enabled
```

```yaml
# values.yaml
cert-manager:
  enabled: true
  installCRDs: true

ingress-nginx:
  enabled: true
  controller:
    replicaCount: 2

prometheus:
  enabled: true
  alertmanager:
    enabled: false
```

## Common Mistakes

| Mistake | Why It's Bad | Better Approach |
|---------|--------------|-----------------|
| Hardcoded values in templates | Can't customize | Use `{{ .Values.x }}` with defaults |
| Deeply nested values | Hard to override | Keep values 2-3 levels deep max |
| No schema validation | Invalid values accepted | Use `values.schema.json` |
| Kustomize without base | Duplication across overlays | Usually use base + overlays |
| Mixing patch types | Confusing, hard to debug | Pick one style per patch file |
| Over-templating | Unmaintainable | Use Kustomize for simple overrides |

## War Story: When Chart Complexity Became a Deployment Risk

A healthcare software team let a Helm chart grow from a simple package into a large, hard-to-review set of values and conditionals.

The chart supported a sensitive application, and its growing complexity made deployments hard to review confidently.

```yaml
# values.yaml (actual excerpt from the incident)
encryption:
  enabled: {{ .Values.compliance.hipaa.enabled | default "false" }}
  algorithm: {{ .Values.encryption.algorithm | default "AES-256" }}
  keyRotation:
    enabled: {{ if and .Values.compliance.hipaa.enabled .Values.encryption.keyRotation.enabled }}true{{ else }}false{{ end }}
    intervalDays: {{ .Values.encryption.keyRotation.intervalDays | default 90 | int }}
    # 200 more lines of nested conditionals...
```

Then came the incident.

```
THE TEMPLATE EXPLOSION TIMELINE
─────────────────────────────────────────────────────────────────
TUESDAY 2:00 PM    Developer updates chart to add new feature
TUESDAY 2:30 PM    PR approved (nobody fully reviewed 800-line values.yaml)
TUESDAY 3:00 PM    Helm chart deployed to staging - works
TUESDAY 4:00 PM    Production deployment begins
TUESDAY 4:01 PM    Helm template renders successfully
TUESDAY 4:02 PM    Pods start, but encryption is DISABLED
                   (nested conditional evaluated wrong in prod)

TUESDAY 4:02 PM    Patient data begins flowing WITHOUT encryption

WEDNESDAY 9:00 AM  Security audit discovers unencrypted data in logs
WEDNESDAY 9:30 AM  Incident declared, HIPAA breach protocol activated
WEDNESDAY 10:00 AM System taken offline for remediation
WEDNESDAY 6:00 PM  Encryption re-enabled, data audit begins

NEXT 6 WEEKS       Mandatory HIPAA breach investigation
```

**Financial Impact:**

```
INCIDENT COST BREAKDOWN
─────────────────────────────────────────────────────────────────
Downtime (8 hours × 23 hospitals):
  - Lost appointment revenue               = $340,000
  - Emergency staff overtime               = $45,000

HIPAA Breach Response:
  - Mandatory patient notifications        = $180,000
  - External security audit                = $250,000
  - Legal review and documentation         = $150,000
  - Regulatory fine (Level 2 violation)    = $500,000

Remediation:
  - Chart rewrite (2 engineers × 4 weeks)  = $80,000
  - Additional testing infrastructure      = $25,000
  - Mandatory staff training               = $35,000

Reputation damage (estimated):
  - Contract delays from 3 hospitals       = $200,000

TOTAL COST: $1,805,000
─────────────────────────────────────────────────────────────────
```

**The Root Cause:**

```yaml
# The problematic conditional (simplified)
{{ if and .Values.compliance.hipaa.enabled .Values.encryption.keyRotation.enabled }}

# In staging values-staging.yaml:
compliance:
  hipaa:
    enabled: true    # Explicit
encryption:
  keyRotation:
    enabled: true    # Explicit

# In production values-prod.yaml:
compliance:
  hipaa:
    enabled: true    # ✓ Set
# encryption.keyRotation.enabled was MISSING
# Default was supposed to be "true" but Go template defaulted to false
```

**The Fix—Simplified Chart + Kustomize:**

```yaml
# NEW values.yaml (20 values, not 847)
replicaCount: 1
image:
  repository: patient-records
  tag: latest
resources:
  limits:
    memory: 2Gi
    cpu: "1"

# Encryption is ALWAYS enabled, not configurable
# HIPAA compliance is the law, not an option
```

```yaml
# Environment differences via Kustomize
# overlays/production/kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

resources:
  - ../../base

patches:
  - patch: |-
      - op: replace
        path: /spec/replicas
        value: 5
    target:
      kind: Deployment

images:
  - name: patient-records
    newTag: v2.3.1-prod

configMapGenerator:
  - name: env-config
    literals:
      - ENVIRONMENT=production
      - LOG_LEVEL=warn
```

**Lessons Learned:**

1. **Don't template security settings**—encryption should usually be enabled by default, not a flag
2. **Template what varies between releases, not between environments**—use Kustomize for environment differences
3. **If values.yaml becomes very large and hard to review, you're probably over-templating**
4. **Test with production values in CI**—the staging/prod divergence was the root cause
5. **[Mandatory schema validation](https://helm.sh/docs/topics/charts/)**—`values.schema.json` would have caught the missing value

## Quiz

### Question 1
When would you use Helm over Kustomize, and vice versa?

<details>
<summary>Show Answer</summary>

**Use Helm when:**
- Installing third-party applications (nginx-ingress, prometheus, etc.)
- Packaging complex applications with many configuration options
- You need version management and rollback
- Sharing applications across teams or organizations
- Application has complex conditional logic

**Use Kustomize when:**
- Customizing your own applications for different environments
- Patching third-party Helm charts with minor changes
- You want template-free, pure YAML
- Making last-mile customizations
- Simple overlay patterns (dev/staging/prod)

**Best practice**: Use both! Helm for packaging, Kustomize for environment customization.
</details>

### Question 2
What's wrong with this Helm template?

```yaml
containers:
  - name: app
    image: myapp:{{ .Values.image.tag }}
    env:
      {{- range .Values.env }}
      - name: {{ .name }}
        value: {{ .value }}
      {{- end }}
```

<details>
<summary>Show Answer</summary>

Two issues:

1. **Missing quote function for tag**: If `tag` is a number like `1.0`, YAML will interpret it as a float. Use `{{ .Values.image.tag | quote }}` or `"{{ .Values.image.tag }}"`.

2. **Values not quoted**: The `value` field should be quoted in case it contains special characters.

Fixed:
```yaml
containers:
  - name: app
    image: "myapp:{{ .Values.image.tag }}"
    env:
      {{- range .Values.env }}
      - name: {{ .name | quote }}
        value: {{ .value | quote }}
      {{- end }}
```
</details>

### Question 3
Write a Kustomize patch that adds a sidecar container to all Deployments in the overlay.

<details>
<summary>Show Answer</summary>

```yaml
# kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

resources:
  - ../../base

patches:
  - patch: |-
      - op: add
        path: /spec/template/spec/containers/-
        value:
          name: sidecar
          image: fluentd:latest
          resources:
            limits:
              memory: 100Mi
              cpu: 50m
    target:
      kind: Deployment

# Or using strategic merge patch file:
# sidecar-patch.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: not-used  # Will be overwritten by target selector
spec:
  template:
    spec:
      containers:
        - name: sidecar
          image: fluentd:latest
```

The JSON Patch with `/-` adds to the end of the containers array.
</details>

### Question 4
How do you pass values to a Helm subchart (dependency)?

<details>
<summary>Show Answer</summary>

In the parent chart's `values.yaml`, nest values under the subchart name:

```yaml
# Parent values.yaml
replicaCount: 3

# Values for postgresql subchart
postgresql:
  auth:
    database: myapp
    username: myuser
  primary:
    persistence:
      size: 20Gi

# Values for redis subchart
redis:
  architecture: standalone
  master:
    persistence:
      enabled: false
```

The subchart name must match the `name` field in `Chart.yaml` dependencies. Helm automatically passes the nested values to the subchart.

You can also use `--set postgresql.auth.database=myapp` on the command line.
</details>

### Question 5
Your team has 12 microservices, each with dev/staging/prod environments. Calculate the YAML file count for: (A) copy-paste approach, (B) Helm-only, (C) Kustomize base+overlays. Which approach would you recommend?

<details>
<summary>Show Answer</summary>

**Calculation:**

```
YAML FILE COUNT COMPARISON
─────────────────────────────────────────────────────────────────
APPROACH A: Copy-Paste
  - 12 services × 3 environments × 5 files each = 180 YAML files
  - Duplication: 100%
  - Drift risk: EXTREMELY HIGH

APPROACH B: Helm-Only
  - 12 services × 1 chart each = 12 charts
  - Each chart: ~8 files (Chart.yaml, values.yaml, 5 templates, helpers)
  - Plus 3 values files per service (dev/staging/prod)
  - Total: 12 × 8 + 12 × 3 = 132 files
  - Duplication: LOW (values files have some overlap)
  - Drift risk: MEDIUM (values files can diverge)

APPROACH C: Kustomize Base+Overlays
  - 12 services × 1 base = 12 bases
  - Each base: 5 files (kustomization + 4 manifests)
  - 3 overlays per service: 12 × 3 × 2 = 72 overlay files
  - Total: 60 + 72 = 132 files
  - Duplication: VERY LOW (overlays only contain differences)
  - Drift risk: LOW (base is single source of truth)

RECOMMENDED APPROACH D: Helm + Kustomize
─────────────────────────────────────────────────────────────────
  - 12 services × 1 chart = 12 charts (~96 chart files)
  - 1 Kustomize base per service = 12 × 1 file (generated from Helm)
  - 3 overlays per service = 36 kustomization.yaml files
  - Total: ~144 files
  - Duplication: MINIMAL
  - Drift risk: LOWEST (Helm for packaging, Kustomize for environment)
```

**Recommendation:** Approach D (Helm + Kustomize combined)

```yaml
# Pattern: Helm generates base, Kustomize patches per environment
# deploy/base/kustomization.yaml
resources:
  - all.yaml  # Generated via: helm template my-service ./chart > all.yaml

# deploy/overlays/production/kustomization.yaml
resources:
  - ../../base
patches:
  - target:
      kind: Deployment
    patch: |-
      - op: replace
        path: /spec/replicas
        value: 5
images:
  - name: my-service
    newTag: v2.1.0-prod
```

For 12 services × 3 environments, this gives you:
- Single source of truth per service (Helm chart)
- Minimal environment-specific files (just patches)
- Clear separation of concerns
</details>

### Question 6
Write a `values.schema.json` that validates: image.tag must be semver format, replicaCount must be 1-100, resources.limits.memory must be set.

<details>
<summary>Show Answer</summary>

```json
{
  "$schema": "https://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["image", "replicaCount", "resources"],
  "properties": {
    "image": {
      "type": "object",
      "required": ["repository", "tag"],
      "properties": {
        "repository": {
          "type": "string",
          "minLength": 1
        },
        "tag": {
          "type": "string",
          "pattern": "^v?[0-9]+\\.[0-9]+\\.[0-9]+(-[a-zA-Z0-9]+)?$",
          "description": "Semver format: v1.2.3 or 1.2.3 or 1.2.3-alpha"
        },
        "pullPolicy": {
          "type": "string",
          "enum": ["Always", "IfNotPresent", "Never"]
        }
      }
    },
    "replicaCount": {
      "type": "integer",
      "minimum": 1,
      "maximum": 100,
      "description": "Number of pod replicas (1-100)"
    },
    "resources": {
      "type": "object",
      "required": ["limits"],
      "properties": {
        "limits": {
          "type": "object",
          "required": ["memory"],
          "properties": {
            "memory": {
              "type": "string",
              "pattern": "^[0-9]+(Mi|Gi)$",
              "description": "Memory limit (e.g., 128Mi, 2Gi)"
            },
            "cpu": {
              "type": "string",
              "pattern": "^[0-9]+(m)?$",
              "description": "CPU limit (e.g., 100m, 1)"
            }
          }
        },
        "requests": {
          "type": "object",
          "properties": {
            "memory": { "type": "string" },
            "cpu": { "type": "string" }
          }
        }
      }
    }
  }
}
```

**Usage:**

```bash
# Helm validates against schema automatically
helm install my-app ./chart -f values.yaml

# Example validation errors:
# - "image.tag: Does not match pattern '^v?[0-9]+...' (got: 'latest')"
# - "replicaCount: Must be <= 100 (got: 150)"
# - "resources.limits: 'memory' is required"
```

**Why this matters:** Schema validation catches configuration errors at `helm template` time, not runtime. The healthcare incident in the war story would likely have been caught during templating.
</details>

### Question 7
You need to add the same set of labels and annotations to ALL resources across 8 microservices. Compare implementing this with Helm `_helpers.tpl` vs Kustomize `commonLabels`. Which is better?

<details>
<summary>Show Answer</summary>

**Helm Approach (_helpers.tpl):**

```yaml
# templates/_helpers.tpl
{{- define "common.labels" -}}
app.kubernetes.io/name: {{ .Chart.Name }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/version: {{ .Chart.AppVersion }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
team: platform
cost-center: engineering
environment: {{ .Values.environment }}
{{- end }}

# templates/deployment.yaml
metadata:
  labels:
    {{- include "common.labels" . | nindent 4 }}

# templates/service.yaml (must repeat)
metadata:
  labels:
    {{- include "common.labels" . | nindent 4 }}
```

**Kustomize Approach:**

```yaml
# kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

commonLabels:
  team: platform
  cost-center: engineering

commonAnnotations:
  prometheus.io/scrape: "true"

resources:
  - deployment.yaml
  - service.yaml
  - configmap.yaml
```

**Comparison:**

| Aspect | Helm _helpers.tpl | Kustomize commonLabels |
|--------|-------------------|------------------------|
| Where applied | Must include in each template | Automatically all resources |
| Selector labels | Can control which go to selectors | Adds to ALL selectors (⚠️) |
| Flexibility | Full Go templating power | Simple key-value only |
| Maintenance | Update in one place | Update in one place |
| Learning curve | Must understand Go templates | Simple YAML |
| Risk | Forgetting to include | Selector mismatch on update |

**The catch with Kustomize commonLabels:**

```yaml
# WARNING: commonLabels adds to ALL selectors, including:
# - Deployment.spec.selector.matchLabels
# - Service.spec.selector

# If you ADD a new commonLabel after deployment, the selectors change,
# and Kubernetes rejects the update (selector is immutable)

# Safer approach: Use labels transformer
transformers:
  - |-
    apiVersion: builtin
    kind: LabelTransformer
    metadata:
      name: add-labels
    labels:
      team: platform
    fieldSpecs:
      - path: metadata/labels
        create: true
      # Explicitly exclude selectors
```

**Recommendation:**

- **For new projects**: Kustomize `commonLabels` is simpler
- **For existing deployments**: Use Helm helpers or labels transformer to avoid selector changes
- **For 8 microservices**: Create a shared Helm library chart with common helpers, or a Kustomize component

```yaml
# components/common-labels/kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1alpha1
kind: Component

labels:
  - pairs:
      team: platform
      cost-center: engineering
    includeSelectors: false  # ← Safe for existing deployments
```
</details>

### Question 8
Your Helm release shows `STATUS: deployed` but the pods are in CrashLoopBackOff. You run `helm upgrade` with a fix but get "no changes". What's happening and how do you fix it?

<details>
<summary>Show Answer</summary>

**The Problem:**

Helm tracks releases based on the **rendered manifests**, not pod status. If your values haven't changed, Helm sees no diff and skips the upgrade—even if pods are crashing.

Common scenarios:
1. Bug is in the application code, not the chart
2. ConfigMap/Secret content is the same (even if mounted file has issues)
3. Environment variable references an external resource that failed

**Investigation:**

```bash
# Check what Helm thinks is deployed
helm get manifest my-release | head -50

# Compare to what you're trying to deploy
helm template my-release ./chart -f values.yaml | head -50

# Check actual pod status
kubectl get pods -l app.kubernetes.io/instance=my-release
kubectl describe pod <crashing-pod>
kubectl logs <crashing-pod> --previous
```

**Solutions:**

**1. Force resource update with annotation:**

```yaml
# values.yaml
podAnnotations:
  rollme: {{ randAlphaNum 5 | quote }}  # Forces new deployment

# Or use --set
helm upgrade my-release ./chart --set podAnnotations.restartedAt=$(date +%s)
```

**2. Use helm upgrade --force:**

```bash
# WARNING: This deletes and recreates resources
helm upgrade my-release ./chart --force
```

**3. Trigger via ConfigMap hash:**

```yaml
# templates/deployment.yaml
spec:
  template:
    metadata:
      annotations:
        checksum/config: {{ include (print $.Template.BasePath "/configmap.yaml") . | sha256sum }}
```

When ConfigMap changes, deployment rolls automatically.

**4. If the fix is in application code (new image):**

```bash
# Image tag changed from v1.0.0 to v1.0.1
helm upgrade my-release ./chart --set image.tag=v1.0.1

# Or if using 'latest' tag (not recommended):
kubectl rollout restart deployment/my-release
```

**Root Cause Analysis:**

```
WHY HELM SHOWS "NO CHANGES"
─────────────────────────────────────────────────────────────────
Helm compares:
  Current release manifest (stored in Secret)
  vs
  New rendered manifest

If identical → "no changes detected"

Helm does NOT check:
  - Pod status (Running, CrashLoopBackOff)
  - Container logs
  - Actual cluster state

This is by design—Helm is declarative about DESIRED state,
not CURRENT state.
```

**Best Practice:**

Always change something when deploying a fix:
- Bump image tag (even for same code rebuild)
- Use image digest instead of tag
- Add a `deployedAt` annotation to force rollout
</details>

## Hands-On Exercise

### Scenario: Multi-Environment Application

Create a Helm chart with Kustomize overlays for dev, staging, and production.

### Create Helm Chart

```bash
# Create chart
helm create my-app
cd my-app

# Simplify values.yaml
cat > values.yaml << 'EOF'
replicaCount: 1

image:
  repository: nginx
  tag: "1.25"
  pullPolicy: IfNotPresent

service:
  type: ClusterIP
  port: 80

resources:
  limits:
    cpu: 100m
    memory: 128Mi
  requests:
    cpu: 50m
    memory: 64Mi

env: []
EOF
```

### Create Kustomize Structure

```bash
cd ..
mkdir -p kustomize/{base,overlays/{dev,staging,production}}

# Generate base from Helm
helm template my-app ./my-app > kustomize/base/all.yaml

# Create base kustomization
cat > kustomize/base/kustomization.yaml << 'EOF'
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
resources:
  - all.yaml
EOF

# Dev overlay
cat > kustomize/overlays/dev/kustomization.yaml << 'EOF'
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
namespace: dev
namePrefix: dev-
resources:
  - ../../base
patches:
  - patch: |-
      - op: replace
        path: /spec/replicas
        value: 1
    target:
      kind: Deployment
EOF

# Production overlay
cat > kustomize/overlays/production/kustomization.yaml << 'EOF'
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
namespace: production
namePrefix: prod-
resources:
  - ../../base
patches:
  - patch: |-
      - op: replace
        path: /spec/replicas
        value: 5
      - op: replace
        path: /spec/template/spec/containers/0/resources/limits/memory
        value: 512Mi
    target:
      kind: Deployment
images:
  - name: nginx
    newTag: "1.25-alpine"
EOF
```

### Build and Compare

```bash
# Build dev
kustomize build kustomize/overlays/dev

# Build production
kustomize build kustomize/overlays/production

# Compare
diff <(kustomize build kustomize/overlays/dev) \
     <(kustomize build kustomize/overlays/production)
```

### Apply to Cluster

```bash
# Create namespaces
kubectl create namespace dev
kubectl create namespace production

# Apply
kubectl apply -k kustomize/overlays/dev
kubectl apply -k kustomize/overlays/production

# Verify
kubectl get pods -n dev
kubectl get pods -n production
```

### Success Criteria

- [ ] Helm chart renders correctly
- [ ] Kustomize overlays modify base
- [ ] Dev has 1 replica, production has 5
- [ ] Production uses alpine image tag
- [ ] Can apply to different namespaces

### Cleanup

```bash
kubectl delete -k kustomize/overlays/dev
kubectl delete -k kustomize/overlays/production
kubectl delete namespace dev production
rm -rf my-app kustomize
```

## Key Takeaways

Before moving on, ensure you can:

- [ ] Explain when to use Helm (packaging, third-party apps) vs Kustomize (environment overlays)
- [ ] Create a Helm chart with Chart.yaml, values.yaml, and templates
- [ ] Use Helm template functions: `{{ .Values.x }}`, `include`, `toYaml`, `nindent`
- [ ] Write `_helpers.tpl` for reusable template definitions
- [ ] Manage Helm dependencies in Chart.yaml with conditions
- [ ] Create Kustomize base + overlays structure for multiple environments
- [ ] Use strategic merge patches and JSON patches for modifications
- [ ] Generate ConfigMaps and Secrets with Kustomize generators
- [ ] Combine Helm + Kustomize using post-renderers or base generation
- [ ] Validate Helm values with `values.schema.json` to catch errors early

## Summary

You've completed the GitOps & Deployments Toolkit! You now understand:

- **ArgoCD**: Application-centric GitOps with UI
- **Argo Rollouts**: Progressive delivery (canary, blue-green)
- **Flux**: Toolkit-based GitOps with image automation
- **Helm & Kustomize**: Package management and overlays

These tools form the foundation of modern Kubernetes deployment practices.

## Next Steps

Continue to [CI/CD Pipelines Toolkit](/platform/toolkits/cicd-delivery/ci-cd-pipelines/) where we'll explore Dagger, Tekton, and Argo Workflows for building before deploying.

---

*"The best config is the one you understand. The second best is the one that works. Helm and Kustomize help you get both."*

## Sources

- [Helm Charts](https://helm.sh/docs/topics/charts/) — Backs Helm chart structure, Chart.yaml, values.yaml, templates, dependencies, chart packaging, chart types, and general claims about how Helm models reusable Kubernetes application packages.
- [github.com: kustomize](https://github.com/kubernetes-sigs/kustomize) — The official Kustomize repository describes it as customization of raw, template-free YAML.
- [helm.sh: changes since helm2](https://helm.sh/docs/v3/faq/changes_since_helm2/) — Helm's official Helm 2 to Helm 3 changes page directly explains Tiller's removal and the RBAC/security motivation.
- [kubernetes.io: kustomization](https://kubernetes.io/docs/tasks/manage-kubernetes-objects/kustomization) — The Kubernetes docs explicitly state that kubectl has supported Kustomize since 1.14 and show `kubectl apply -k`.
- [grafana.com: how the jsonnet based project tanka improves kubernetes usage](https://grafana.com/blog/how-the-jsonnet-based-project-tanka-improves-kubernetes-usage/) — Grafana's own documentation and blog posts describe using Tanka/Jsonnet to manage its Kubernetes infrastructure.
- [Flux HelmRelease Post Renderers](https://v2-0.docs.fluxcd.io/flux/components/helm/helmreleases/) — Useful for the module's Helm-plus-Kustomize pattern because it documents Kustomize post-rendering in Flux HelmRelease.
