---
title: "Module 2.4: Helm & Kustomize"
slug: platform/toolkits/cicd-delivery/gitops-deployments/module-2.4-helm-kustomize
sidebar:
  order: 5
---
> **Toolkit Track** | Complexity: `[MEDIUM]` | Time: 50-60 min

## Prerequisites

Before starting this module, you should be comfortable reading Kubernetes manifests and recognizing the difference between desired state and current state. You do not need to be a Helm or Kustomize expert yet, but you should already understand Deployments, Services, ConfigMaps, Secrets, namespaces, image tags, and basic GitOps reconciliation.

You should complete [Module 2.1: ArgoCD](../module-2.1-argocd/) or [Module 2.3: Flux](../module-2.3-flux/) first, because this module assumes you know why Git becomes the source of truth in a GitOps workflow. You should also be able to run `kubectl`; after the first mention, this module uses the common alias `k` to mean `kubectl`.

## Learning Outcomes

After completing this module, you will be able to:

- **Design** a Helm chart structure that separates reusable application packaging from environment-specific values.
- **Debug** rendered Helm manifests by tracing a bad runtime symptom back to templates, values files, schema validation, or release state.
- **Implement** Kustomize bases, overlays, patches, generators, and image transformations without copying full manifests between environments.
- **Compare** Helm, Kustomize, and combined GitOps patterns using practical trade-offs such as reviewability, drift risk, rollback behavior, and ownership.
- **Evaluate** whether a deployment problem belongs in a chart, a values file, a Kustomize overlay, a GitOps controller setting, or the application itself.

## Why This Module Matters

A platform engineer at a payments company once reviewed a production incident that looked boring at first: one service had three slightly different Deployment manifests across development, staging, and production. The staging file had the new resource limits, the production file had the old image tag, and the development file had a debug environment variable that should never have left a sandbox. Nobody had intentionally created a risky deployment system. They had simply copied YAML when the team was small, then kept copying it as the business grew.

That pattern breaks quietly before it breaks loudly. The first failure is usually wasted review time, because engineers must inspect entire manifests to understand one environment-specific difference. The second failure is drift, because a critical field gets fixed in one environment and forgotten in another. The third failure is an incident, because production no longer represents a controlled promotion of tested state; it becomes a manually maintained sibling of tested state.

Helm and Kustomize solve the same broad problem from different angles. Helm packages Kubernetes applications as charts with templates, defaults, dependencies, and release history. Kustomize keeps Kubernetes YAML recognizable and applies structured transformations through bases, overlays, patches, generators, and image substitutions. A senior platform engineer needs both tools, not because every deployment should use both, but because every organization eventually has both kinds of problems: reusable application packaging and environment-specific customization.

This module teaches the tools through the deployment decisions they support. You will start with the packaging problem Helm solves, then switch to the overlay problem Kustomize solves, then combine them in GitOps patterns used by ArgoCD and Flux. Along the way, you will practice predicting rendered output, debugging bad changes before they reach a cluster, and choosing the smallest configuration mechanism that makes the system easier to review.

## Core Content

## 1. The Configuration Drift Problem

Kubernetes manifests are declarative, but a directory full of copied manifests is not automatically disciplined. If three environments each have a full Deployment, Service, ConfigMap, and Ingress, then each environment becomes its own source of truth. A reviewer must compare whole files to discover whether production differs because it should differ or because someone forgot to promote a change.

Consider a simple web application that has five Kubernetes resources per environment. With development, staging, and production, the team now maintains fifteen files for one service. Multiply that by a dozen services and the repository looks organized while still hiding a dangerous operational question: which fields are intentionally different, and which fields drifted by accident?

```text
COPY-PASTE MANIFEST SPRAWL
────────────────────────────────────────────────────────────────────
repo/
├── dev/
│   ├── deployment.yaml        image: app:v1.8.0, replicas: 1
│   ├── service.yaml           port: 80
│   ├── configmap.yaml         LOG_LEVEL=debug
│   ├── ingress.yaml           host: dev.example.com
│   └── hpa.yaml               minReplicas: 1
├── staging/
│   ├── deployment.yaml        image: app:v1.8.0, replicas: 2
│   ├── service.yaml           port: 80
│   ├── configmap.yaml         LOG_LEVEL=info
│   ├── ingress.yaml           host: staging.example.com
│   └── hpa.yaml               minReplicas: 2
└── production/
    ├── deployment.yaml        image: app:v1.7.3, replicas: 3
    ├── service.yaml           port: 80
    ├── configmap.yaml         LOG_LEVEL=info
    ├── ingress.yaml           host: app.example.com
    └── hpa.yaml               minReplicas: 3
────────────────────────────────────────────────────────────────────
Reviewer question: Is production intentionally on v1.7.3, or did promotion fail?
```

The important lesson is not that file counts are always bad. A repository can have many files and still be healthy if each file has a clear owner and reason to exist. The risk appears when large files are copied so that tiny differences can be changed in place. That design makes the accidental difference look exactly like the intentional difference.

Helm and Kustomize reduce drift by creating a relationship between shared configuration and local differences. Helm says, "Package the application, then feed it values." Kustomize says, "Keep a base, then apply overlays." Both approaches make review easier when used well, because the reviewer can focus on the values or patches that are supposed to differ.

```text
CONFIGURATION MODELS
────────────────────────────────────────────────────────────────────
                     SHARED INTENT                 LOCAL DIFFERENCE
Helm                 Chart templates               values-dev.yaml
                     default values                values-prod.yaml
                     dependencies                  --set image.tag=v1.8.0

Kustomize            base resources                overlays/dev
                     plain YAML                    overlays/production
                     reusable components           patches and generators

Combined GitOps      chart or rendered base         controller values
                     application package           post-render patches
                     release version               image transformations
────────────────────────────────────────────────────────────────────
```

**Stop and think:** Your team changes `securityContext.runAsNonRoot` for a service after a security review. In a copy-paste directory structure, where could that change be missed? In a Helm chart, where should the default live? In a Kustomize layout, should it belong in the base or in an overlay? Write down the answer before continuing, because that placement decision is the core skill in this module.

A good rule is to put invariant safety requirements in the shared layer and true environment differences in the environment layer. If every environment must run as non-root, the setting belongs in the Helm template or Kustomize base. If production needs more replicas, that belongs in a production values file or production overlay. If a field is both sensitive and environment-specific, such as an external database endpoint, the configuration should be explicit and validated rather than hidden inside a clever template.

## 2. Helm Fundamentals: Packaging Applications

Helm treats an application as a package called a chart. A chart contains metadata, default values, Kubernetes templates, optional helper templates, tests, and dependency declarations. When Helm renders a chart, it combines the templates with values and produces ordinary Kubernetes manifests that can be installed, upgraded, rolled back, inspected, and stored as a release.

The package model is useful when the application is reused across teams, clusters, or customers. A chart can encode common naming conventions, labels, resource templates, optional features, and dependencies such as PostgreSQL or Redis. That does not mean every possible choice should become a value. The best charts expose meaningful variation while keeping security, identity, and operational invariants simple to review.

```text
HELM CHART ANATOMY
────────────────────────────────────────────────────────────────────
my-app/
├── Chart.yaml              package metadata, version, dependencies
├── values.yaml             default configuration values
├── values.schema.json      optional validation for supplied values
├── charts/                 downloaded chart dependencies
├── templates/
│   ├── deployment.yaml     Kubernetes manifest with Go template syntax
│   ├── service.yaml        Kubernetes manifest with Go template syntax
│   ├── ingress.yaml        optional resource controlled by values
│   ├── configmap.yaml      generated application configuration
│   ├── _helpers.tpl        reusable named template snippets
│   ├── NOTES.txt           post-install notes shown by Helm
│   └── tests/
│       └── test-connection.yaml
└── README.md               chart usage, values, examples, ownership
────────────────────────────────────────────────────────────────────
```

The `Chart.yaml` file describes the package rather than the deployed runtime state. Its `version` describes the chart package version, while `appVersion` describes the application version. Those two numbers may move together in simple projects, but they are not the same thing. A chart bug fix can change the chart version without changing the application image, and an application release can change `appVersion` while chart structure stays stable.

```yaml
apiVersion: v2
name: my-app
description: A Helm chart for a web application
type: application
version: 1.0.0
appVersion: "2.3.1"

keywords:
  - web
  - platform

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

The `values.yaml` file holds defaults that templates consume. Defaults should make the chart render successfully in a safe, minimal environment. They should also teach the reader what the chart expects. When defaults are vague, such as `image.tag: latest`, the chart becomes harder to reproduce because the same release intent can resolve to different images over time.

```yaml
replicaCount: 1

image:
  repository: nginx
  tag: "1.25"
  pullPolicy: IfNotPresent

service:
  type: ClusterIP
  port: 80

ingress:
  enabled: false
  className: nginx
  hosts:
    - host: my-app.local
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

The template layer is where Helm becomes powerful and risky. Template expressions can reference values, chart metadata, release metadata, functions, conditionals, loops, and helper templates. Used carefully, that power removes duplication and creates consistent resources. Used carelessly, it hides too much logic in files that reviewers expected to behave like YAML.

```yaml
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
          resources:
            {{- toYaml .Values.resources | nindent 12 }}
```

A worked example makes the rendering model concrete. Suppose the release name is `shop`, the chart name is `my-app`, and the default `replicaCount` is overridden to `3`. Helm evaluates the template functions, substitutes values, indents nested YAML where requested, and emits a normal Deployment. Kubernetes never receives the template syntax; it receives only the rendered manifest.

```bash
helm template shop ./my-app \
  --namespace staging \
  --set replicaCount=3 \
  --set image.tag=2.3.1
```

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: shop-my-app
  labels:
    helm.sh/chart: my-app-1.0.0
    app.kubernetes.io/name: my-app
    app.kubernetes.io/instance: shop
    app.kubernetes.io/managed-by: Helm
spec:
  replicas: 3
  selector:
    matchLabels:
      app.kubernetes.io/name: my-app
      app.kubernetes.io/instance: shop
  template:
    metadata:
      labels:
        app.kubernetes.io/name: my-app
        app.kubernetes.io/instance: shop
    spec:
      containers:
        - name: my-app
          image: "nginx:2.3.1"
          imagePullPolicy: IfNotPresent
          ports:
            - name: http
              containerPort: 80
```

**Active check:** Before reading the next paragraph, predict what would happen if `image.tag` were supplied as the unquoted value `1.10` in a YAML values file. Would Helm preserve it as the string `1.10`, or could YAML parsing change the value before the template sees it? The practical lesson is that image tags, environment variable values, and anything that must remain textual should be quoted in values files and usually quoted again in rendered YAML.

Helm helper templates reduce repetition, especially for names and labels. They also centralize decisions that must remain consistent across resources. A Service selector must match the Pod template labels, so it is safer to define selector labels once and include them everywhere than to type them manually in each template.

```yaml
{{- define "my-app.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{- define "my-app.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}

{{- define "my-app.selectorLabels" -}}
app.kubernetes.io/name: {{ include "my-app.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{- define "my-app.labels" -}}
helm.sh/chart: {{ .Chart.Name }}-{{ .Chart.Version }}
{{ include "my-app.selectorLabels" . }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}
```

Helm's release object is another reason teams adopt it. When you run `helm install`, Helm stores release information in the cluster. When you run `helm upgrade`, Helm renders a new manifest and compares it to the previous release. When you run `helm rollback`, Helm can move the release back to a previous revision. This is useful, but it also creates a debugging trap: Helm's release status is not the same thing as application health.

```bash
helm lint ./my-app
helm template shop ./my-app -f values-staging.yaml
helm install shop ./my-app --namespace staging --create-namespace -f values-staging.yaml
helm upgrade shop ./my-app --namespace staging -f values-staging.yaml
helm rollback shop 1 --namespace staging
helm list --all-namespaces
helm get values shop --namespace staging
helm get manifest shop --namespace staging
helm uninstall shop --namespace staging
```

A healthy Helm workflow renders before it applies. `helm lint` catches common chart mistakes, `helm template` shows the exact Kubernetes manifests, and `helm install --dry-run --debug` exercises Helm's install path without committing changes. In GitOps, your controller often performs the install or upgrade, but the same principle remains: reviewers should be able to inspect rendered output before trusting a change.

```text
HELM RENDERING AND RELEASE FLOW
────────────────────────────────────────────────────────────────────
Chart files + values files
          │
          ▼
helm lint and schema validation
          │
          ▼
helm template renders Kubernetes YAML
          │
          ▼
GitOps controller or Helm CLI applies resources
          │
          ▼
Kubernetes controllers reconcile workloads
          │
          ▼
Pods run, fail, restart, or expose runtime symptoms
────────────────────────────────────────────────────────────────────
Debugging rule: move backward from symptoms to rendered YAML to values.
```

Values files are where environment differences often begin. A development values file may use one replica and lower resource requests, while production uses more replicas, pinned image tags, and stricter ingress settings. The danger is allowing values files to become miniature programs. If a reviewer must reason through hundreds of nested flags to understand whether encryption is enabled, the chart has crossed from configurable into opaque.

```yaml
# values-dev.yaml
replicaCount: 1

image:
  repository: ghcr.io/org/shop
  tag: "2.3.1"

ingress:
  enabled: true
  hosts:
    - host: shop.dev.example.com
      paths:
        - path: /
          pathType: Prefix

resources:
  limits:
    cpu: 200m
    memory: 256Mi
```

```yaml
# values-prod.yaml
replicaCount: 5

image:
  repository: ghcr.io/org/shop
  tag: "2.3.1"

ingress:
  enabled: true
  hosts:
    - host: shop.example.com
      paths:
        - path: /
          pathType: Prefix

resources:
  limits:
    cpu: "1"
    memory: 1Gi
```

A senior chart design habit is to distinguish release variation from environment policy. Release variation includes image tags, replica counts, feature enablement, and dependency toggles. Environment policy includes labels required by the platform, node placement rules, admission-control requirements, and organization-wide security settings. You can put both in Helm, but you should notice when environment policy is being repeated across many charts; that may be a sign that Kustomize overlays or platform admission policies would be more reviewable.

Schema validation helps keep values files honest. A `values.schema.json` file lets Helm validate supplied values before rendering. It cannot prove that your application will behave correctly, but it can catch missing required fields, wrong types, invalid ranges, and unsafe values such as `latest` when your release process requires immutable tags.

```json
{
  "$schema": "https://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["replicaCount", "image", "resources"],
  "properties": {
    "replicaCount": {
      "type": "integer",
      "minimum": 1,
      "maximum": 20
    },
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
          "pattern": "^v?[0-9]+\\.[0-9]+\\.[0-9]+(-[A-Za-z0-9.-]+)?$"
        }
      }
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
              "pattern": "^[0-9]+(Mi|Gi)$"
            }
          }
        }
      }
    }
  }
}
```

**Stop and think:** If production accidentally omits `resources.limits.memory`, where should the failure happen? The least expensive answer is at pull-request validation or Helm rendering time. The more expensive answer is after the Pod gets scheduled, competes for memory, and fails during live traffic.

Helm dependencies solve another packaging problem: applications often need supporting services. A chart can declare a PostgreSQL dependency and allow values to enable, disable, or configure it. This is powerful for development and self-contained installs, but production teams often separate stateful dependencies from application releases. The decision should come from operational ownership, not from whether Helm can technically install both.

```yaml
apiVersion: v2
name: shop
version: 1.0.0

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
postgresql:
  enabled: true
  auth:
    database: shop
  primary:
    persistence:
      size: 20Gi

redis:
  enabled: false
```

```bash
helm dependency update ./shop
helm dependency build ./shop
helm template shop ./shop -f values-prod.yaml
```

Helm is at its best when it produces a clear, reusable package with constrained variation. It becomes a risk when it turns into a hidden programming language for every policy decision. The next tool, Kustomize, takes a different approach: instead of turning YAML into templates, it keeps YAML mostly literal and applies targeted transformations.

## 3. Pause and Predict: How Would Kustomize Solve the Same Problem?

Before seeing Kustomize syntax, pause and predict its shape from the problem. Helm solved duplication by introducing templates and values. If Kustomize refuses to use templates, it still needs a way to represent shared resources, environment changes, image changes, generated ConfigMaps, generated Secrets, and reusable optional behavior. What structures would you invent if the only allowed input were Kubernetes YAML plus a small instruction file?

A reasonable prediction is "base plus patch." The base would contain normal Kubernetes manifests that could almost be applied directly. The production overlay would point at the base and then say, "Change replicas to five, change the image tag, put everything in the production namespace, and add production-only ingress." That prediction is close to how Kustomize works.

```text
PAUSE AND PREDICT MODEL
────────────────────────────────────────────────────────────────────
Problem Helm solved with values:
  replicas: 1 in dev, 5 in production
  image tag differs by promotion
  ingress host differs by environment
  ConfigMap values differ by environment

How Kustomize is likely to solve it:
  shared Deployment lives in base/
  overlays/dev patches only dev differences
  overlays/production patches only production differences
  kustomization.yaml records the transformation recipe
────────────────────────────────────────────────────────────────────
```

**Pause and predict:** If the base Deployment is named `shop`, and the production overlay adds `namePrefix: prod-`, what name do you expect the rendered Deployment to have? If the overlay also targets a patch at `name: shop`, should the patch target the original name or the prefixed name? Make a prediction now, then verify later with `kustomize build`. The answer matters because debugging Kustomize often means understanding whether a transformation happens before or after a selector is resolved.

This prediction moment is not just a learning trick. It is the mental model senior engineers use during reviews. Before reading Kustomize output, they predict which fields should change and which fields must remain stable. If the rendered output changes more than expected, the overlay is too broad, the patch target is wrong, or the base is carrying environment-specific state that should have been moved.

## 4. Kustomize Fundamentals: Bases, Overlays, and Patches

Kustomize starts with ordinary Kubernetes YAML and a `kustomization.yaml` file. A base is a reusable set of resources. An overlay references the base and applies transformations such as namespace assignment, name prefixes, labels, annotations, patches, image changes, ConfigMap generation, Secret generation, replacements, and components.

The strongest feature of Kustomize is reviewability. A base Deployment looks like a Deployment, not like a Go template. A production overlay can be small enough to show only the production differences. That makes Kustomize especially useful for your own applications, where you already control the manifests and mainly need environment variation without duplication.

```text
KUSTOMIZE DIRECTORY STRUCTURE
────────────────────────────────────────────────────────────────────
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
────────────────────────────────────────────────────────────────────
```

A base `kustomization.yaml` lists resources and shared transformations. The base should describe what is true for every environment. If a setting is not true for every environment, keep it out of the base or set a safe minimum that overlays can change deliberately.

```yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

resources:
  - deployment.yaml
  - service.yaml
  - configmap.yaml

commonLabels:
  app: my-app

commonAnnotations:
  team: platform
```

The base resources are normal manifests. That is valuable because Kubernetes engineers can read them without learning a template language first. The trade-off is that Kustomize cannot express arbitrary logic the way Helm can. It transforms known structures; it does not ask you to write a program inside YAML.

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-app
spec:
  replicas: 1
  selector:
    matchLabels:
      app.kubernetes.io/name: my-app
  template:
    metadata:
      labels:
        app.kubernetes.io/name: my-app
    spec:
      containers:
        - name: app
          image: nginx:1.25
          ports:
            - containerPort: 80
          resources:
            limits:
              cpu: 100m
              memory: 128Mi
```

An overlay references the base and declares differences. The production overlay below changes the namespace, adds a prefix, includes a production-only Ingress, patches the replica count, changes the image location and tag, and generates configuration. Notice that the overlay describes production differences without copying the full Deployment.

```yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

namespace: production
namePrefix: prod-

resources:
  - ../../base
  - ingress.yaml

patches:
  - path: replica-patch.yaml

images:
  - name: nginx
    newName: registry.example.com/platform/my-app
    newTag: "1.25-prod"

configMapGenerator:
  - name: app-config
    literals:
      - ENVIRONMENT=production
      - LOG_LEVEL=info
```

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-app
spec:
  replicas: 5
```

Strategic merge patches look like partial Kubernetes resources. They are comfortable when you want to change fields by structure, such as setting `spec.replicas`. JSON patches are more explicit about operations and paths, which makes them useful for adding to arrays or replacing deeply nested fields. Both styles are valid, but mixing many patch styles in one overlay makes reviews harder.

```yaml
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
```

```yaml
patches:
  - path: increase-memory.yaml
    target:
      kind: Deployment
      labelSelector: "app=my-app"
```

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-app
spec:
  template:
    spec:
      containers:
        - name: app
          resources:
            limits:
              memory: 512Mi
```

**Active check:** Your production patch targets `kind: Deployment` but does not specify `name` or `labelSelector`. What happens when the base later gains a second Deployment for a worker process? The patch may apply more broadly than intended, or it may fail depending on the patch content. A precise target is not ceremony; it is how you keep a future base change from silently widening the blast radius.

Kustomize generators create ConfigMaps and Secrets from literals, files, or environment files. By default, generated resource names include a content hash, which helps Kubernetes roll workloads when referenced configuration changes. This behavior is useful, but it must be understood by GitOps reviewers because the name in the rendered output may not match the base name exactly.

```yaml
configMapGenerator:
  - name: app-config
    literals:
      - ENVIRONMENT=production
      - LOG_LEVEL=warn

secretGenerator:
  - name: app-secrets
    literals:
      - DATABASE_URL=postgres://prod-db:5432/app
    type: Opaque
```

Images are a common overlay concern because image promotion is often environment-specific. Kustomize can rewrite the image name and tag without patching the whole container spec. This is cleaner than replacing a Deployment when the only intended change is the artifact reference.

```yaml
images:
  - name: nginx
    newName: registry.example.com/platform/my-app
    newTag: "2.3.1"
```

Replacements let one resource field feed another resource field. They are useful when generated or transformed names must be propagated, but they should be used sparingly. When replacements become a web of indirect references, the overlay stops being easier to read than a template.

```yaml
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

Components package reusable optional transformations. For example, several overlays might need monitoring annotations or hardened security settings. A component can apply those changes without copying the same patch into every overlay. The same caution applies here as with Helm helpers: reusable pieces should make the result easier to reason about, not hide a pile of surprising changes.

```yaml
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
```

```yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

resources:
  - ../../base

components:
  - ../../components/monitoring
  - ../../components/security
```

The core Kustomize command is `kustomize build`, which renders the final manifests without applying them. Because Kustomize is built into `kubectl`, you can also run `kubectl apply -k` and `kubectl diff -k`. In this module's examples, `k` means `kubectl` after you define the alias in your shell with `alias k=kubectl`.

```bash
kustomize build overlays/production
kubectl diff -k overlays/production
kubectl apply -k overlays/production
k get -f <(kustomize build overlays/production) -o name
```

A strong Kustomize review starts with a prediction, then checks the rendered output. If production should only change replicas and image tag, the rendered diff should not change selectors, names, ports, service accounts, or security context. If it does, stop and explain why before applying.

```text
KUSTOMIZE REVIEW LOOP
────────────────────────────────────────────────────────────────────
Predict intended differences:
  replicas, image tag, namespace, ingress host

Render overlay:
  kustomize build overlays/production

Inspect generated YAML:
  names, selectors, labels, images, generated ConfigMaps

Compare to live or previous output:
  kubectl diff -k overlays/production

Apply only after the diff matches the intent:
  kubectl apply -k overlays/production
────────────────────────────────────────────────────────────────────
```

One subtle Kustomize risk involves labels and selectors. Older examples often use `commonLabels`, which may add labels to selectors as well as metadata. Changing selectors on an existing Deployment can fail because Kubernetes treats selectors as immutable. Newer label transformer patterns allow you to add labels to metadata without touching selectors, which is safer for existing workloads.

```yaml
labels:
  - pairs:
      team: platform
      cost-center: engineering
    includeSelectors: false
```

**Stop and think:** If you add `team: platform` to a Service selector after the Service already exists, what could happen to traffic? The Service may stop selecting Pods that do not have the new label, or Kubernetes may reject an immutable selector update depending on the resource and field. Label changes are not just metadata when selectors are involved.

Kustomize is not a Helm replacement in every case. It does not have chart dependencies, release history, or a package repository model by itself. It is excellent for controlled transformations of resources you own, but it is not always the best way to distribute a complex third-party application. That distinction leads naturally to the combined patterns used in GitOps.

## 5. Helm vs Kustomize: Choosing the Right Boundary

The most useful question is not "Which tool is better?" The useful question is "Which layer owns this decision?" Helm owns packaging decisions well. Kustomize owns environment overlays well. GitOps controllers own reconciliation decisions well. Kubernetes controllers own runtime convergence. Application code owns behavior. Confusing those layers creates configuration that technically works but becomes hard to debug.

```text
HELM vs KUSTOMIZE
────────────────────────────────────────────────────────────────────
                    HELM                         KUSTOMIZE
                    ────                         ─────────
Primary model       Package and release           Base and overlays

Input shape         Templates plus values         Plain YAML plus transforms

Best fit            Reusable applications         Environment differences
                    Third-party charts            Last-mile customization
                    Dependency bundles            Patching rendered output
                    Release rollback              Reviewable drift control

Typical file        Chart.yaml                    kustomization.yaml
                    values.yaml                   deployment.yaml
                    templates/*.yaml              patches/*.yaml

Risk when abused    Over-templating               Over-patching
                    Hidden conditionals           Broad targets
                    Huge values files             Selector surprises
                    Runtime flags for policy      Generated-name confusion

Debug question      What did Helm render?          What did overlay change?
                    Which values were used?        Which patch matched?
                    What release revision?         What did build output?
────────────────────────────────────────────────────────────────────
```

| Scenario | Prefer Helm | Prefer Kustomize | Often combine |
|---|---|---|---|
| Installing a vendor-supported monitoring stack | Yes, because charts package dependencies and defaults | Sometimes for local policy patches | Yes, when GitOps adds site-specific patches |
| Deploying your own small service across three environments | Sometimes, if you standardize charts per service | Yes, if manifests are simple and owned by the team | Sometimes, if packaging and overlays are both useful |
| Applying a common label to many already-running workloads | Sometimes through chart helpers | Yes, but avoid selector mutation | Yes, when Helm output needs platform labels |
| Managing a stateful database dependency | Sometimes for development or self-contained installs | Rarely as the primary package mechanism | Carefully, with ownership boundaries documented |
| Patching a third-party chart field not exposed in values | No, unless you fork the chart | Yes, as a post-render patch | Yes, Helm renders and Kustomize patches |
| Creating reusable internal application packages | Yes, especially across teams | Sometimes for team-specific overlays | Yes, for platform baseline plus environment patching |

A useful boundary rule is to put product-level variation in Helm values and site-level variation in Kustomize overlays. Product-level variation answers "How should this application package behave?" Site-level variation answers "How does this cluster, environment, or platform team need to adapt it?" The same field can move between layers as organizations mature, so document the boundary rather than pretending it is universal.

For example, `replicaCount` could be a Helm value for a chart used by many teams. It could also be a Kustomize patch if the chart is rendered once as a base and environments own scaling differences. Neither is automatically wrong. The right choice is the one that makes promotion, review, rollback, and incident debugging clearer for your organization.

**Active check:** Your team wants to add a required `securityContext` to every workload in every environment. Would you implement it as a Helm value, a Helm template default, a Kustomize component, or an admission policy? The most senior answer is probably not "make it configurable." If the requirement is universal and security-critical, prefer a default or enforced policy over an optional values flag.

The anti-pattern is treating configuration mechanisms as a place to avoid decisions. A chart with thirty boolean flags is often a design that refused to decide what the package guarantees. An overlay with broad patches against every Deployment is often a design that refused to create a reusable base or component. Good configuration makes intentional differences visible; bad configuration makes every difference plausible.

## 6. Helm and Kustomize Together in GitOps

GitOps controllers can combine Helm and Kustomize in several ways. The simplest pattern is to let Helm render a chart and let Kustomize patch the rendered output. This is common when a third-party chart is mostly acceptable but lacks one field your platform requires, such as a label, annotation, image override, security context, or network policy adjustment.

```text
COMBINED GITOPS FLOW
────────────────────────────────────────────────────────────────────
Git repository
  ├── chart reference or local chart
  ├── values files
  └── kustomize overlays
          │
          ▼
GitOps controller reads desired state
          │
          ▼
Helm renders chart into Kubernetes YAML
          │
          ▼
Kustomize post-renderer applies site patches
          │
          ▼
Controller applies final manifests
          │
          ▼
Kubernetes reconciles workloads
────────────────────────────────────────────────────────────────────
```

One repository layout uses Helm to generate a base and Kustomize overlays for each environment. This can be simple to understand because the base is a rendered artifact checked into Git or generated during CI. The downside is that rendered files can be large and noisy, so teams must decide whether generated output belongs in the repository or in a build step.

```text
my-deployment/
├── chart/
│   ├── Chart.yaml
│   ├── values.yaml
│   └── templates/
├── base/
│   ├── kustomization.yaml
│   └── all.yaml              rendered by helm template in CI
└── overlays/
    ├── staging/
    │   ├── kustomization.yaml
    │   └── values-patch.yaml
    └── production/
        ├── kustomization.yaml
        └── values-patch.yaml
```

```bash
helm template my-app ./chart -f chart/values.yaml > base/all.yaml
kustomize build overlays/production
```

ArgoCD supports Helm sources and Kustomize sources, but combining them depends on repository structure and controller capabilities. In practice, many teams keep the Helm chart as the primary source and use ArgoCD configuration for values, or they use a Kustomize layer that points to rendered or remote resources. The goal is not to use every feature in one Application; the goal is to make the final desired state reproducible and reviewable.

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: my-app
spec:
  project: default
  source:
    repoURL: https://charts.example.com
    chart: my-app
    targetRevision: 1.0.0
    helm:
      values: |
        replicaCount: 3
        image:
          tag: "2.3.1"
  destination:
    server: https://kubernetes.default.svc
    namespace: production
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
```

Flux has a clear HelmRelease model and supports Kustomize post-renderers for Helm releases. This pattern is valuable when the chart is external, but the platform team needs to apply standardized changes after rendering. The patch is recorded in Git and reconciled by Flux, so it remains part of desired state rather than a manual mutation.

```yaml
apiVersion: helm.toolkit.fluxcd.io/v2
kind: HelmRelease
metadata:
  name: my-app
spec:
  interval: 5m
  chart:
    spec:
      chart: my-app
      sourceRef:
        kind: HelmRepository
        name: my-charts
      version: "1.0.0"

  values:
    replicaCount: 3

  postRenderers:
    - kustomize:
        patches:
          - patch: |-
              - op: add
                path: /metadata/labels/platform.example.com~1owner
                value: delivery-team
            target:
              kind: Deployment

        images:
          - name: my-app
            newTag: "2.3.1"
```

An umbrella chart is a different Helm-centered pattern. It packages several dependent charts behind one parent chart. This can be useful for a platform bundle such as ingress, certificates, and monitoring. It can also become difficult to upgrade safely if one release controls too many independent operational domains.

```yaml
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

The senior review question for combined patterns is "Where would I look during an incident?" If a Pod is crashing, start with Kubernetes events and logs. If the manifest is wrong, inspect the final rendered output. If the final rendered output is wrong, trace backward through Kustomize patches, Helm values, chart templates, and GitOps controller configuration. A good repository layout makes that path obvious.

```text
INCIDENT DEBUGGING BACKTRACK
────────────────────────────────────────────────────────────────────
Runtime symptom:
  Pod CrashLoopBackOff in production
          │
          ▼
Cluster evidence:
  k describe pod, k logs --previous, events
          │
          ▼
Applied manifest:
  k get deployment prod-my-app -o yaml
          │
          ▼
GitOps desired output:
  controller diff or local kustomize build
          │
          ▼
Kustomize layer:
  overlay patches, images, generators, components
          │
          ▼
Helm layer:
  values-prod.yaml, values.schema.json, templates
          │
          ▼
Source decision:
  chart design, environment boundary, application behavior
────────────────────────────────────────────────────────────────────
```

**Stop and think:** If `helm get manifest` shows the correct image tag but the live Deployment shows an older image tag, which layer is suspect? The answer is probably not the chart template. You would check GitOps reconciliation status, drift, paused automation, failed syncs, or another controller changing the object.

Jsonnet is worth recognizing because some advanced platform teams use it for Kubernetes configuration. Jsonnet treats configuration as programmable data and is often used through tools such as Tanka. It can solve duplication with functions and object composition rather than Helm templates or Kustomize patches. In most Kubernetes organizations, Helm and Kustomize are still the dominant tools, so you should learn them first and treat Jsonnet as a specialized pattern you may encounter in mature platform repositories.

## 7. Worked Example: Refactoring Drift into Helm Plus Kustomize

Imagine a team owns a `checkout` service. Development and production each have a full Deployment manifest. Production has five replicas and a stricter memory limit, while development has one replica and lower limits. A recent incident happened because production accidentally kept an old image tag after staging was promoted. The goal is not to invent a complex platform; the goal is to make the intended differences visible.

Start with the shared application package. The Helm chart owns the common Deployment shape, Service, labels, probes, container port, and default resource structure. It exposes image repository, image tag, replica count, and resource limits as values because those fields are expected to vary by release or environment.

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ include "checkout.fullname" . }}
  labels:
    {{- include "checkout.labels" . | nindent 4 }}
spec:
  replicas: {{ .Values.replicaCount }}
  selector:
    matchLabels:
      {{- include "checkout.selectorLabels" . | nindent 6 }}
  template:
    metadata:
      labels:
        {{- include "checkout.selectorLabels" . | nindent 8 }}
    spec:
      containers:
        - name: checkout
          image: "{{ .Values.image.repository }}:{{ .Values.image.tag }}"
          ports:
            - name: http
              containerPort: 8080
          readinessProbe:
            httpGet:
              path: /ready
              port: http
          resources:
            {{- toYaml .Values.resources | nindent 12 }}
```

Development values stay small. They describe the release artifact and the scale needed for a low-traffic environment. They do not repeat labels, selectors, probes, or Service definitions because those are shared package behavior.

```yaml
replicaCount: 1

image:
  repository: ghcr.io/example/checkout
  tag: "2.4.0"

resources:
  limits:
    cpu: 250m
    memory: 256Mi
  requests:
    cpu: 100m
    memory: 128Mi
```

Production values are equally explicit. They use the same image tag during promotion, which makes drift easy to spot in review. If production should lag behind, that decision becomes visible in one line rather than hidden inside a copied Deployment.

```yaml
replicaCount: 5

image:
  repository: ghcr.io/example/checkout
  tag: "2.4.0"

resources:
  limits:
    cpu: "1"
    memory: 1Gi
  requests:
    cpu: 500m
    memory: 512Mi
```

Now add a Kustomize production overlay for site-specific policy that should not be chart-specific. The platform team wants every production resource to carry ownership labels and a production namespace. Those are environment and platform concerns, so an overlay can apply them after Helm renders the package.

```yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

namespace: checkout-production
namePrefix: prod-

resources:
  - ../../base

labels:
  - pairs:
      platform.example.com/team: checkout
      platform.example.com/environment: production
    includeSelectors: false

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
      name: checkout
```

The review now has two clear questions. First, did the Helm values promote the intended image and resource settings? Second, did the Kustomize overlay apply only platform concerns? If the production diff changes a selector or removes a probe, the reviewer has a concrete reason to stop the change.

```bash
helm template checkout ./chart -f values-production.yaml > base/all.yaml
kustomize build overlays/production > rendered-production.yaml
kubectl diff -f rendered-production.yaml
```

This worked example shows the "I do" part of the learning pattern. The chart packaged shared application structure, the values described release and scale variation, and the overlay applied platform policy. In the exercise later, you will create a similar structure yourself and verify that the rendered environments differ only where expected.

## 8. Debugging Patterns and Senior Review Habits

Helm and Kustomize failures rarely announce themselves as "a Helm problem" or "a Kustomize problem." They show up as Pods not starting, Services not routing traffic, GitOps syncs failing, admission webhooks rejecting manifests, or reviewers unable to understand a change. The first debugging habit is to classify the symptom before choosing the tool.

If Helm rendering fails, inspect chart syntax, missing values, schema errors, indentation, and helper templates. If Kustomize build fails, inspect resource paths, patch targets, JSON patch paths, duplicate resource IDs, and generated names. If rendering succeeds but the cluster rejects the resource, inspect Kubernetes API validation, immutable fields, admission policies, and namespace existence. If the resource applies but the app fails, inspect Pods, logs, probes, ConfigMaps, Secrets, and application configuration.

```text
SYMPTOM TO LAYER MAP
────────────────────────────────────────────────────────────────────
helm lint fails
  → chart metadata, template syntax, missing helpers, bad schema

helm template fails
  → invalid values, nil references, invalid functions, bad indentation

kustomize build fails
  → missing resource path, duplicate IDs, bad patch target, invalid JSON path

kubectl apply fails
  → Kubernetes schema, immutable field, admission policy, namespace missing

GitOps sync fails
  → controller permissions, source fetch, render settings, health checks

Pod runs but crashes
  → application config, image, secret, command, probes, external dependency
────────────────────────────────────────────────────────────────────
```

A common Helm debugging trap is believing `STATUS: deployed` means the application is healthy. Helm records whether it installed or upgraded the release from its perspective. It does not continuously inspect whether your Pods are crash-looping, your readiness probe is failing, or your application cannot reach the database. In GitOps, the controller may add health assessment, but even then you should distinguish release state from workload state.

```bash
helm status checkout --namespace production
helm get values checkout --namespace production
helm get manifest checkout --namespace production
k get pods -n production -l app.kubernetes.io/instance=checkout
k describe pod -n production <pod-name>
k logs -n production <pod-name> --previous
```

Another trap is the "no changes" upgrade. Helm compares rendered manifests, not application behavior. If you rebuild the same image tag with different bits, Helm may see no manifest change. That is one reason immutable image tags or image digests are operationally cleaner than mutable tags such as `latest`.

```bash
helm template checkout ./chart -f values-prod.yaml > new.yaml
helm get manifest checkout --namespace production > old.yaml
diff -u old.yaml new.yaml
```

When the rendered manifests are identical, you need to change the desired state or fix the application artifact. Bump the image tag, use a digest, update a checksum annotation tied to ConfigMap content, or run a controlled rollout restart when appropriate. Do not hide this problem with random annotations unless your team has explicitly chosen that pattern and understands the audit trail.

```yaml
spec:
  template:
    metadata:
      annotations:
        checksum/config: {{ include (print $.Template.BasePath "/configmap.yaml") . | sha256sum }}
```

Kustomize debugging starts with build output. If an overlay does not apply a patch, check whether the target name, kind, namespace, API version, or label selector matches the resource before or after transformations. If a JSON patch path fails, remember that arrays and escaped characters are exact. For example, annotation keys containing `/` use `~1` in JSON patch paths.

```yaml
patches:
  - patch: |-
      - op: add
        path: /metadata/annotations/platform.example.com~1owner
        value: checkout-team
    target:
      kind: Deployment
      name: checkout
```

A senior review habit is to test the final rendered output with Kubernetes-aware tools, not just text comparison. `kubectl diff -k` shows the cluster-facing change. `kubeconform`, policy checks, or admission dry-runs can catch problems that text diffs cannot. In a GitOps repository, these checks should run before merge so the controller is not the first system to discover invalid desired state.

```bash
kustomize build overlays/production > rendered.yaml
kubectl apply --dry-run=server -f rendered.yaml
kubectl diff -f rendered.yaml
```

A second senior habit is to keep release boundaries small. One chart controlling an entire platform can create impressive demos and painful incidents. One overlay patching every Deployment in a repository can create quick compliance and broad accidental damage. Prefer small, composable units whose rendered output a human can inspect during review.

## 9. War Story: When Chart Complexity Became a Deployment Risk

A healthcare software team let a Helm chart grow from a simple package into a large, hard-to-review set of values and conditionals. The chart supported a sensitive application, and its growing complexity made deployments hard to review confidently. Nobody set out to disable encryption. They created enough nested configuration that reviewers stopped being able to prove encryption was always enabled.

```yaml
encryption:
  enabled: {{ .Values.compliance.hipaa.enabled | default "false" }}
  algorithm: {{ .Values.encryption.algorithm | default "AES-256" }}
  keyRotation:
    enabled: {{ if and .Values.compliance.hipaa.enabled .Values.encryption.keyRotation.enabled }}true{{ else }}false{{ end }}
    intervalDays: {{ .Values.encryption.keyRotation.intervalDays | default 90 | int }}
```

The deployment worked in staging because staging values explicitly set every nested field. Production values omitted one nested key because the team believed the chart default would protect them. The template did not behave the way the reviewer assumed, and the rendered manifest disabled a security requirement that should never have been configurable in the first place.

```text
TEMPLATE COMPLEXITY INCIDENT TIMELINE
────────────────────────────────────────────────────────────────────
Tuesday 2:00 PM      Developer adds a feature flag to the chart
Tuesday 2:30 PM      Pull request approved after shallow values review
Tuesday 3:00 PM      Staging deployment succeeds with explicit values
Tuesday 4:00 PM      Production deployment begins with partial values
Tuesday 4:01 PM      Helm renders successfully without schema failure
Tuesday 4:02 PM      Pods start with encryption disabled by template logic
Wednesday 9:00 AM    Security audit detects unencrypted sensitive output
Wednesday 9:30 AM    Incident response begins and production is restricted
Wednesday 6:00 PM    Encryption restored after chart simplification
Following weeks      Audit, notification, remediation, and retraining
────────────────────────────────────────────────────────────────────
```

The root cause was not "Helm is unsafe." The root cause was treating a legal and security invariant as a configurable feature flag, then burying the behavior in nested template logic. Schema validation would have helped by catching missing values, but the better design was simpler: encryption should be enabled by default or enforced by policy, not selected through a fragile conditional.

```yaml
replicaCount: 1

image:
  repository: patient-records
  tag: "2.3.1"

resources:
  limits:
    memory: 2Gi
    cpu: "1"

security:
  encryption:
    enabled: true
```

Then environment differences moved into a small Kustomize overlay. Production still had legitimate differences, such as replica count, image promotion tag, logging level, and resource limits. Those differences became visible in short patches instead of hidden in hundreds of lines of values and conditionals.

```yaml
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
      name: patient-records

images:
  - name: patient-records
    newTag: "2.3.1-prod"

configMapGenerator:
  - name: env-config
    literals:
      - ENVIRONMENT=production
      - LOG_LEVEL=warn
```

The lesson is that configuration mechanisms should reduce review burden, not transfer risk into a more abstract file. If a setting is mandatory, make it mandatory. If a value must exist, validate it. If an environment differs, isolate the difference. If the final output is hard to predict, render it and review it before the controller applies it.

## Did You Know?

- **[Helm v3 removed Tiller entirely](https://helm.sh/docs/v3/faq/changes_since_helm2/)**, which means modern Helm no longer requires the Helm v2 server-side component that created security and RBAC concerns.
- **[Kustomize is built into kubectl](https://kubernetes.io/docs/tasks/manage-kubernetes-objects/kustomization)**, so you can use `kubectl apply -k` for overlays without installing a separate binary in many workflows.
- **Helm charts can include `values.schema.json`**, allowing invalid configuration to fail during rendering instead of waiting for a workload to fail after deployment.
- **Jsonnet and Tanka solve a related configuration problem**, but they use programmable data composition rather than Helm's template package model or Kustomize's patch-and-overlay model.

## Common Mistakes

| Mistake | Why It Hurts | Better Approach |
|---|---|---|
| Putting every possible behavior behind a Helm value | Reviewers must reason through a custom configuration language instead of a clear deployment contract | Expose meaningful release variation, keep invariants as defaults or policy, and validate required values |
| Using mutable image tags such as `latest` in values files | Helm and GitOps diffs may show no meaningful change while the runtime artifact changes underneath | Promote immutable tags or image digests and make image changes explicit in review |
| Copying full manifests into every Kustomize overlay | Environment drift becomes invisible because every overlay owns its own version of shared resources | Keep shared resources in a base and let overlays contain only intentional differences |
| Patching every resource with broad Kustomize targets | Future resources may accidentally receive patches that were meant for one workload | Target by kind and name or by a precise label selector, then inspect rendered output |
| Adding common labels without considering selectors | Selector changes can break traffic or be rejected because some selector fields are immutable | Use label transformer options such as `includeSelectors: false` when metadata-only labels are intended |
| Treating Helm release status as workload health | A release can be deployed while Pods are crash-looping or failing readiness checks | Inspect Kubernetes events, logs, rollout status, and GitOps health separately from Helm status |
| Combining Helm and Kustomize without documenting ownership | Engineers cannot tell whether a field should be changed in values, templates, overlays, or controller settings | Document the boundary: chart owns package behavior, overlay owns environment policy, controller owns reconciliation |

## Quiz

### Question 1

Your team deploys a service to development, staging, and production. A security setting must be identical in every environment, but the replica count differs by environment. During review, one engineer proposes making both fields configurable in `values.yaml`. How would you evaluate that design, and what would you change?

<details>
<summary>Show Answer</summary>

The design makes a mandatory security invariant look optional, which increases review and incident risk. The security setting should live in the shared chart template, Kustomize base, or an enforced admission policy depending on ownership. Replica count is a legitimate environment difference, so it can live in a values file or overlay patch. The key distinction is whether a field represents required behavior or intentional variation.
</details>

### Question 2

A Helm chart renders successfully in CI, but production Pods enter `CrashLoopBackOff` after deployment. `helm status` shows `deployed`, and the team wants to roll back immediately. What should you inspect before deciding whether rollback is the right fix?

<details>
<summary>Show Answer</summary>

Inspect the workload evidence first: `k describe pod`, `k logs --previous`, events, readiness and liveness probe failures, ConfigMap and Secret references, and the live Deployment. Then compare `helm get manifest` with the newly rendered manifest to determine whether the desired state is wrong. Helm status only tells you the release operation succeeded from Helm's perspective; it does not prove the application is healthy. If the crash is caused by a bad image or config, rollback may help. If it is caused by an external dependency or cluster policy, rollback may not address the root cause.
</details>

### Question 3

A production Kustomize overlay contains a JSON patch with `target: { kind: Deployment }` and no name or selector. It works today because the base has one Deployment. Next week the base adds a worker Deployment, and production starts applying the same resource limits to both workloads. What is the review failure, and how should you fix it?

<details>
<summary>Show Answer</summary>

The overlay used an overly broad patch target. The original reviewer accepted a patch whose future blast radius was larger than the intended change. Fix it by targeting the specific Deployment name or a precise label selector, then render the overlay and confirm only the intended Deployment changes. If both workloads need a shared resource policy, create an explicit component or patch that documents that intent.
</details>

### Question 4

Your organization installs a third-party ingress controller with Helm. The chart does not expose a value for a required platform annotation, and forking the chart would create upgrade burden. What combined Helm and Kustomize pattern would you recommend?

<details>
<summary>Show Answer</summary>

Use Helm for the third-party package and apply a Kustomize post-render patch through the GitOps controller or release workflow. This keeps the vendor chart upgradeable while recording the local platform requirement in Git. The patch should target the exact resource that needs the annotation, and CI should render the final output so reviewers can see the chart plus local customization together.
</details>

### Question 5

A developer changes `commonLabels` in a Kustomize base to add `team: platform`. The rendered diff shows changes under `spec.selector.matchLabels` for an existing Deployment. Why is this risky, and what safer pattern should the team consider?

<details>
<summary>Show Answer</summary>

Deployment selectors are immutable after creation, so changing selector labels may be rejected by the Kubernetes API. Even where selector changes are accepted for other resources, they can change traffic routing or workload selection unexpectedly. A safer pattern is using the newer `labels` transformer with `includeSelectors: false` when the goal is metadata labeling only, or applying labels through a targeted patch that avoids selectors.
</details>

### Question 6

A team rebuilds an application image but reuses the same tag in `values-prod.yaml`. They run `helm upgrade`, and Helm reports no changes. The Pods keep running the old behavior. What happened, and what release practice prevents this?

<details>
<summary>Show Answer</summary>

Helm compared the previously rendered manifest with the newly rendered manifest and found them identical because the image reference did not change. Kubernetes also had no reason to roll out new Pods if the Deployment template was unchanged. Prevent this by using immutable image tags or image digests for every build, and make promotion update the desired image reference in Git. A checksum annotation helps for ConfigMap changes, but it does not solve mutable image provenance.
</details>

### Question 7

Your team has twelve services and wants a standard monitoring annotation on every production Deployment. One engineer wants to add it to every Helm chart helper, while another wants one Kustomize component used by production overlays. How would you choose?

<details>
<summary>Show Answer</summary>

Choose based on ownership and desired scope. If the annotation is platform policy applied consistently across services, a Kustomize component used by production overlays is often more reviewable and avoids editing every chart. If each chart already owns monitoring behavior and teams need chart-specific control, Helm helpers may be appropriate. In either case, render at least one service before merging and verify the annotation lands on Pod templates, not only top-level Deployment metadata.
</details>

### Question 8

A GitOps sync fails after you add a Kustomize overlay around Helm-rendered output. `kustomize build` works locally, but server-side dry run fails with an immutable field error. What sequence should you use to debug the issue?

<details>
<summary>Show Answer</summary>

First inspect the final rendered output from the same path and settings the controller uses. Then compare it with the live object using `kubectl diff` or `k get <resource> -o yaml`. Identify which immutable field changed, such as a Deployment selector or Service cluster IP. Trace that field backward to the overlay patch, label transformer, name transformation, or Helm template value that changed it. The fix is usually to avoid changing the immutable field, create a migration plan for resource replacement, or adjust the transformer so metadata-only changes do not affect selectors.
</details>

## Hands-On Exercise

### Scenario: Build a Reviewable Multi-Environment Deployment

You are supporting a small application called `quote-api`. The team wants a reusable Helm chart because several teams deploy the same service pattern. The platform team also wants Kustomize overlays because production needs standard labels, annotations, namespace assignment, and a higher replica count. Your task is to create the chart, render it into a base, customize it for development and production, and prove the output differs only where intended.

### Step 1: Create a Working Directory

Use a temporary directory outside your application repository so the exercise is easy to clean up. The commands below assume you have Helm, Kustomize, and `kubectl` available. If you do not have a cluster available, you can still complete the render and diff steps.

```bash
mkdir -p /tmp/kubedojo-helm-kustomize
cd /tmp/kubedojo-helm-kustomize
alias k=kubectl
```

### Step 2: Create a Minimal Helm Chart

Create a chart named `quote-api`. Helm will generate more files than you need, so remove the default templates and replace them with a small Deployment and Service. This keeps the exercise focused on rendering and overlays rather than chart scaffolding.

```bash
helm create quote-api
rm -rf quote-api/templates/*
```

```bash
cat > quote-api/Chart.yaml << 'EOF'
apiVersion: v2
name: quote-api
description: A small API used to practice Helm and Kustomize
type: application
version: 1.0.0
appVersion: "1.0.0"
EOF
```

```bash
cat > quote-api/values.yaml << 'EOF'
replicaCount: 1

image:
  repository: nginx
  tag: "1.25"
  pullPolicy: IfNotPresent

service:
  port: 80

resources:
  limits:
    cpu: 100m
    memory: 128Mi
  requests:
    cpu: 50m
    memory: 64Mi
EOF
```

### Step 3: Add Helm Helpers and Templates

The helper template centralizes names and selector labels. This matters because the Deployment selector and Pod labels must match. If you type those labels manually in each file, you increase the chance of breaking service routing during a later edit.

```bash
cat > quote-api/templates/_helpers.tpl << 'EOF'
{{- define "quote-api.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{- define "quote-api.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name (include "quote-api.name" .) | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}

{{- define "quote-api.selectorLabels" -}}
app.kubernetes.io/name: {{ include "quote-api.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{- define "quote-api.labels" -}}
helm.sh/chart: {{ .Chart.Name }}-{{ .Chart.Version }}
{{ include "quote-api.selectorLabels" . }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}
EOF
```

```bash
cat > quote-api/templates/deployment.yaml << 'EOF'
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ include "quote-api.fullname" . }}
  labels:
    {{- include "quote-api.labels" . | nindent 4 }}
spec:
  replicas: {{ .Values.replicaCount }}
  selector:
    matchLabels:
      {{- include "quote-api.selectorLabels" . | nindent 6 }}
  template:
    metadata:
      labels:
        {{- include "quote-api.selectorLabels" . | nindent 8 }}
    spec:
      containers:
        - name: quote-api
          image: "{{ .Values.image.repository }}:{{ .Values.image.tag }}"
          imagePullPolicy: {{ .Values.image.pullPolicy }}
          ports:
            - name: http
              containerPort: 80
          resources:
            {{- toYaml .Values.resources | nindent 12 }}
EOF
```

```bash
cat > quote-api/templates/service.yaml << 'EOF'
apiVersion: v1
kind: Service
metadata:
  name: {{ include "quote-api.fullname" . }}
  labels:
    {{- include "quote-api.labels" . | nindent 4 }}
spec:
  ports:
    - name: http
      port: {{ .Values.service.port }}
      targetPort: http
  selector:
    {{- include "quote-api.selectorLabels" . | nindent 4 }}
EOF
```

### Step 4: Add Values Validation

Add a small schema so invalid values fail before deployment. This is not a complete production schema, but it demonstrates the habit. The schema requires a semver-like image tag, a replica count between one and ten, and a memory limit.

```bash
cat > quote-api/values.schema.json << 'EOF'
{
  "$schema": "https://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["replicaCount", "image", "resources"],
  "properties": {
    "replicaCount": {
      "type": "integer",
      "minimum": 1,
      "maximum": 10
    },
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
          "pattern": "^[0-9]+\\.[0-9]+(\\.[0-9]+)?(-[A-Za-z0-9.-]+)?$"
        }
      }
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
              "pattern": "^[0-9]+(Mi|Gi)$"
            }
          }
        }
      }
    }
  }
}
EOF
```

### Step 5: Render the Helm Base

Render the chart into a Kustomize base. In a production repository, you would decide whether this rendered file belongs in Git or is generated in CI. For this exercise, writing it to a base makes the next steps visible.

```bash
mkdir -p deploy/base
helm lint ./quote-api
helm template quote-api ./quote-api > deploy/base/all.yaml
```

```bash
cat > deploy/base/kustomization.yaml << 'EOF'
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

resources:
  - all.yaml
EOF
```

### Step 6: Create Development and Production Overlays

The development overlay should be intentionally small. It assigns a namespace and prefix, but it leaves most chart defaults alone. The production overlay changes replica count, adds metadata-only labels, and changes the image tag through Kustomize so you can see both Helm and overlay behavior.

```bash
mkdir -p deploy/overlays/dev deploy/overlays/production
```

```bash
cat > deploy/overlays/dev/kustomization.yaml << 'EOF'
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

namespace: quote-dev
namePrefix: dev-

resources:
  - ../../base

labels:
  - pairs:
      platform.example.com/environment: development
      platform.example.com/team: platform
    includeSelectors: false
EOF
```

```bash
cat > deploy/overlays/production/kustomization.yaml << 'EOF'
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

namespace: quote-production
namePrefix: prod-

resources:
  - ../../base

labels:
  - pairs:
      platform.example.com/environment: production
      platform.example.com/team: platform
    includeSelectors: false

patches:
  - patch: |-
      - op: replace
        path: /spec/replicas
        value: 5
      - op: add
        path: /spec/template/metadata/annotations
        value:
          prometheus.io/scrape: "true"
          prometheus.io/port: "80"
    target:
      kind: Deployment
      name: quote-api

images:
  - name: nginx
    newTag: "1.25.3"
EOF
```

### Step 7: Build and Inspect the Rendered Output

Render both overlays and compare them. Do not skip this step. The point of Helm and Kustomize is not that they make YAML disappear; the point is that they let you generate YAML whose differences are intentional and inspectable.

```bash
kustomize build deploy/overlays/dev > rendered-dev.yaml
kustomize build deploy/overlays/production > rendered-production.yaml
diff -u rendered-dev.yaml rendered-production.yaml || true
```

Inspect the production Deployment directly. You should see five replicas, the production namespace, the `prod-` name prefix, production labels, and the updated image tag. You should not see selector labels changed by the metadata-only platform labels.

```bash
grep -n "replicas:\|namespace:\|image:\|platform.example.com\|prometheus.io" rendered-production.yaml
```

### Step 8: Optional Cluster Apply and Verification

If you have a disposable cluster, apply both overlays and verify that the rendered resources behave as expected. If you do not have a cluster, use server-side dry run when possible or stop after rendering and comparison.

```bash
kubectl create namespace quote-dev --dry-run=client -o yaml | kubectl apply -f -
kubectl create namespace quote-production --dry-run=client -o yaml | kubectl apply -f -

kubectl apply -k deploy/overlays/dev
kubectl apply -k deploy/overlays/production

kubectl rollout status deployment/dev-quote-api -n quote-dev
kubectl rollout status deployment/prod-quote-api -n quote-production

kubectl get deployment -n quote-dev dev-quote-api -o jsonpath='{.spec.replicas}{"\n"}'
kubectl get deployment -n quote-production prod-quote-api -o jsonpath='{.spec.replicas}{"\n"}'
```

### Step 9: Debug One Intentional Mistake

Change the production image tag to `latest` and run Helm lint or render again from the chart values if you move that tag into values. The schema should reject invalid tags at Helm render time. Then undo the mistake and confirm rendering works again. This small failure is the point: the cheapest deployment bug is the one caught before Kubernetes receives a manifest.

```bash
helm template quote-api ./quote-api --set image.tag=latest
```

### Success Criteria

- [ ] The Helm chart renders a Deployment and Service without template errors.
- [ ] `values.schema.json` rejects an invalid image tag such as `latest`.
- [ ] The Kustomize base references Helm-rendered output through `deploy/base/all.yaml`.
- [ ] The development overlay renders with one replica and development metadata.
- [ ] The production overlay renders with five replicas, production metadata, and image tag `1.25.3`.
- [ ] Platform labels are added without changing Deployment selector labels.
- [ ] The rendered diff shows intentional environment differences rather than copied-manifest drift.
- [ ] If applied to a cluster, both Deployments roll out successfully in separate namespaces.

### Cleanup

```bash
kubectl delete -k deploy/overlays/dev --ignore-not-found
kubectl delete -k deploy/overlays/production --ignore-not-found
kubectl delete namespace quote-dev quote-production --ignore-not-found
cd /
rm -rf /tmp/kubedojo-helm-kustomize
```

## Next Module

Continue to [CI/CD Pipelines Toolkit](/platform/toolkits/cicd-delivery/ci-cd-pipelines/) where you will connect deployment configuration to build pipelines, workflow engines, and delivery automation.

## Sources

- [Helm Charts](https://helm.sh/docs/topics/charts/) — Backs Helm chart structure, Chart.yaml, values.yaml, templates, dependencies, chart packaging, chart types, and general claims about how Helm models reusable Kubernetes application packages.
- [github.com: kustomize](https://github.com/kubernetes-sigs/kustomize) — The official Kustomize repository describes it as customization of raw, template-free YAML.
- [helm.sh: changes since helm2](https://helm.sh/docs/v3/faq/changes_since_helm2/) — Helm's official Helm 2 to Helm 3 changes page directly explains Tiller's removal and the RBAC/security motivation.
- [kubernetes.io: kustomization](https://kubernetes.io/docs/tasks/manage-kubernetes-objects/kustomization) — The Kubernetes docs explicitly state that kubectl has supported Kustomize since 1.14 and show `kubectl apply -k`.
- [Flux HelmRelease Post Renderers](https://v2-0.docs.fluxcd.io/flux/components/helm/helmreleases/) — Useful for the module's Helm-plus-Kustomize pattern because it documents Kustomize post-rendering in Flux HelmRelease.
