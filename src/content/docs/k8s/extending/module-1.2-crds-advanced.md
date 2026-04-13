---
title: "Module 1.2: Custom Resource Definitions Deep Dive"
slug: k8s/extending/module-1.2-crds-advanced
sidebar:
  order: 3
---
> **Complexity**: `[MEDIUM]` - Defining your own Kubernetes APIs
>
> **Time to Complete**: 3 hours
>
> **Prerequisites**: Module 1.1 (API Deep Dive), familiarity with YAML and JSON Schema

---

## What You'll Be Able to Do

After completing this module, you will be able to:

1. **Design** a CRD schema with structural validation, CEL rules, and default values that reject invalid input at admission time
2. **Implement** CRD versioning with storage versions and conversion webhooks so v1alpha1 and v1 objects coexist safely
3. **Configure** subresources (status, scale) and additional printer columns so `kubectl get` displays meaningful operational data
4. **Diagnose** CRD validation failures and version-skew issues using API discovery and dry-run requests

---

## Why This Module Matters

Custom Resource Definitions (CRDs) are the foundation of every Kubernetes extension. When you install Istio, Argo CD, Prometheus Operator, or Cert-Manager, the first thing they do is register CRDs. These CRDs define new resource types -- `VirtualService`, `Application`, `ServiceMonitor`, `Certificate` -- that extend the Kubernetes API without modifying a single line of API Server code.

But most tutorials stop at "apply a basic CRD." In production, you need **validation** (so users cannot submit garbage), **versioning** (so you can evolve your API without breaking clients), **subresources** (so `kubectl get` shows useful columns and `kubectl scale` works), and **conversion webhooks** (so v1alpha1 and v1 objects coexist). This module covers all of that.

> **The Database Table Analogy**
>
> A CRD is like a CREATE TABLE statement in a database. It tells Kubernetes: "I have a new kind of thing. Here is its name, its structure, and its validation rules." Once the table exists, anyone with the right permissions can INSERT (create), SELECT (get), UPDATE, and DELETE rows (resources). The API Server handles all the CRUD operations, etcd stores the data, and you just need to define the schema.

---

## What You'll Learn

By the end of this module, you will be able to:
- Create CRDs with comprehensive OpenAPI v3 validation
- Use structural schemas with proper types and constraints
- Implement CRD versioning with storage versions
- Configure status and scale subresources
- Add printer columns for kubectl output
- Set up conversion webhooks between versions

---

## Did You Know?

- **There are over 200 well-known CRDs** in the CNCF ecosystem. The Kubernetes API itself only defines ~60 resource types, but CRDs have expanded the API surface by 3x or more in most production clusters.

- **CRDs are stored in etcd as JSON**, just like built-in resources. The API Server validates them on the way in and serves them on the way out, with no additional backend required. This is why CRDs are called "level 1" extensions -- they use the existing API Server machinery.

- **Structural schemas became mandatory in Kubernetes 1.16**. Before that, CRDs had almost no validation, and users could store arbitrary JSON blobs. The switch to structural schemas was one of the most impactful API quality improvements in Kubernetes history.

---

## Part 1: CRD Fundamentals Recap

### 1.1 Anatomy of a CRD

```yaml
apiVersion: apiextensions.k8s.io/v1
kind: CustomResourceDefinition
metadata:
  name: backuppolicies.data.kubedojo.io    # plural.group
spec:
  group: data.kubedojo.io                   # API group
  names:
    kind: BackupPolicy                      # PascalCase
    listKind: BackupPolicyList
    plural: backuppolicies                  # URL path
    singular: backuppolicy                  # kubectl alias
    shortNames:
    - bp                                    # kubectl shorthand
    categories:
    - all                                   # appears in `kubectl get all`
  scope: Namespaced                         # or Cluster
  versions:
  - name: v1alpha1
    served: true                            # API Server serves this version
    storage: true                           # Stored in etcd as this version
    schema:
      openAPIV3Schema:                      # Validation schema
        type: object
        properties:
          spec:
            type: object
            properties:
              schedule:
                type: string
              retention:
                type: integer
```

### 1.2 Naming Conventions

| Field | Convention | Example |
|-------|-----------|---------|
| `group` | Reverse domain, owned by you | `data.kubedojo.io` |
| `kind` | PascalCase, singular | `BackupPolicy` |
| `plural` | lowercase, plural | `backuppolicies` |
| `singular` | lowercase, singular | `backuppolicy` |
| `shortNames` | 1-4 letter abbreviations | `bp` |
| CRD `metadata.name` | `{plural}.{group}` | `backuppolicies.data.kubedojo.io` |

> **Warning**: Never use `k8s.io`, `kubernetes.io`, or any group you do not own. These are reserved for Kubernetes core. Using them will cause conflicts and is considered bad practice.

> **Stop and think**: What would happen if two different operators installed on the same cluster both tried to define a CRD with the same `group` and `kind`? How does the reverse-domain naming convention prevent this?

---

## Part 2: OpenAPI v3 Validation

### 2.1 Structural Schema Requirements

Every CRD must have a **structural schema**. This means:
1. Every field has a declared `type`
2. No `additionalProperties` at the root (unless explicitly enabled per-field)
3. All validation keywords (`minimum`, `pattern`, etc.) are within typed fields
4. No use of `$ref`, `allOf`, `oneOf`, `anyOf`, `not` at the root level

### 2.2 Comprehensive Validation Example

```yaml
apiVersion: apiextensions.k8s.io/v1
kind: CustomResourceDefinition
metadata:
  name: webapps.apps.kubedojo.io
spec:
  group: apps.kubedojo.io
  names:
    kind: WebApp
    listKind: WebAppList
    plural: webapps
    singular: webapp
    shortNames:
    - wa
  scope: Namespaced
  versions:
  - name: v1alpha1
    served: true
    storage: true
    schema:
      openAPIV3Schema:
        type: object
        description: "WebApp defines a web application deployment."
        required:
        - spec
        properties:
          spec:
            type: object
            description: "WebAppSpec defines the desired state."
            required:
            - image
            - replicas
            properties:
              image:
                type: string
                description: "Container image in registry/repo:tag format."
                pattern: '^[a-z0-9]+([._-][a-z0-9]+)*(/[a-z0-9]+([._-][a-z0-9]+)*)*:[a-zA-Z0-9][a-zA-Z0-9._-]{0,127}$'
                minLength: 3
                maxLength: 255
              replicas:
                type: integer
                description: "Number of desired pod replicas."
                minimum: 1
                maximum: 100
                default: 2
              port:
                type: integer
                description: "Container port to expose."
                minimum: 1
                maximum: 65535
                default: 8080
              env:
                type: array
                description: "Environment variables for the container."
                maxItems: 50
                items:
                  type: object
                  required:
                  - name
                  - value
                  properties:
                    name:
                      type: string
                      description: "Environment variable name."
                      pattern: '^[A-Z_][A-Z0-9_]*$'
                      minLength: 1
                      maxLength: 128
                    value:
                      type: string
                      description: "Environment variable value."
                      maxLength: 4096
              resources:
                type: object
                description: "Resource requirements."
                properties:
                  cpuLimit:
                    type: string
                    description: "CPU limit (e.g., 500m, 1)."
                    pattern: '^[0-9]+m?$'
                    default: "500m"
                  memoryLimit:
                    type: string
                    description: "Memory limit (e.g., 128Mi, 1Gi)."
                    pattern: '^[0-9]+(Ki|Mi|Gi|Ti)?$'
                    default: "256Mi"
              ingress:
                type: object
                description: "Ingress configuration."
                properties:
                  enabled:
                    type: boolean
                    default: false
                  host:
                    type: string
                    description: "Hostname for ingress."
                    pattern: '^[a-z0-9]([-a-z0-9]*[a-z0-9])?(\.[a-z0-9]([-a-z0-9]*[a-z0-9])?)*$'
                  path:
                    type: string
                    default: "/"
                  tlsEnabled:
                    type: boolean
                    default: false
              healthCheck:
                type: object
                description: "Health check configuration."
                properties:
                  path:
                    type: string
                    description: "HTTP path for health checks."
                    default: "/healthz"
                  intervalSeconds:
                    type: integer
                    minimum: 5
                    maximum: 300
                    default: 10
                  timeoutSeconds:
                    type: integer
                    minimum: 1
                    maximum: 60
                    default: 3
          status:
            type: object
            description: "WebAppStatus defines the observed state."
            properties:
              readyReplicas:
                type: integer
                description: "Number of pods that are ready."
              availableReplicas:
                type: integer
                description: "Number of pods available for service."
              conditions:
                type: array
                description: "Current conditions of the WebApp."
                items:
                  type: object
                  required:
                  - type
                  - status
                  properties:
                    type:
                      type: string
                      description: "Condition type."
                    status:
                      type: string
                      description: "Condition status."
                      enum:
                      - "True"
                      - "False"
                      - "Unknown"
                    reason:
                      type: string
                      description: "Machine-readable reason."
                    message:
                      type: string
                      description: "Human-readable message."
                    lastTransitionTime:
                      type: string
                      format: date-time
                      description: "When the condition last changed."
              observedGeneration:
                type: integer
                format: int64
                description: "Generation observed by the controller."
```

> **Pause and predict**: If a user submits a `WebApp` with an environment variable name `1_INVALID`, which specific line in this schema will trigger the rejection, and at what phase of the API request lifecycle will it happen?

### 2.3 Validation Keywords Reference

| Keyword | Applies To | Example |
|---------|-----------|---------|
| `minimum` / `maximum` | integer, number | `minimum: 1` |
| `exclusiveMinimum` / `exclusiveMaximum` | integer, number | `exclusiveMinimum: true` |
| `minLength` / `maxLength` | string | `maxLength: 253` |
| `pattern` | string | `pattern: '^[a-z]+$'` |
| `enum` | any | `enum: ["debug", "info", "warn"]` |
| `minItems` / `maxItems` | array | `maxItems: 10` |
| `uniqueItems` | array | `uniqueItems: true` |
| `required` | object | `required: ["name"]` |
| `default` | any | `default: 3` |
| `format` | string | `format: date-time` |
| `nullable` | any | `nullable: true` |

### 2.4 x-kubernetes Validation Extensions

Kubernetes adds its own validation extensions beyond standard OpenAPI:

```yaml
properties:
  metadata:
    type: object
    properties:
      name:
        type: string
        # Validate like a Kubernetes name
        x-kubernetes-validations:
        - rule: "self.matches('^[a-z0-9]([-a-z0-9]*[a-z0-9])?$')"
          message: "must be a valid Kubernetes name"

  ports:
    type: array
    x-kubernetes-list-type: map
    x-kubernetes-list-map-keys:
    - containerPort
    items:
      type: object
      properties:
        containerPort:
          type: integer
        protocol:
          type: string

  labels:
    type: object
    additionalProperties:
      type: string
    x-kubernetes-map-type: granular   # SSA tracks individual keys

  immutableField:
    type: string
    x-kubernetes-validations:
    - rule: "self == oldSelf"
      message: "field is immutable once set"
```

### 2.5 CEL Validation Rules

Common Expression Language (CEL) rules allow complex cross-field validation directly in the CRD schema:

```yaml
spec:
  type: object
  x-kubernetes-validations:
  - rule: "self.minReplicas <= self.maxReplicas"
    message: "minReplicas must not exceed maxReplicas"
    fieldPath: ".minReplicas"
  - rule: "self.replicas >= self.minReplicas && self.replicas <= self.maxReplicas"
    message: "replicas must be between minReplicas and maxReplicas"
  - rule: "!self.ingress.tlsEnabled || self.ingress.host != ''"
    message: "host is required when TLS is enabled"
  properties:
    minReplicas:
      type: integer
    maxReplicas:
      type: integer
    replicas:
      type: integer
    ingress:
      type: object
      properties:
        tlsEnabled:
          type: boolean
        host:
          type: string
```

CEL rule reference:

| Expression | Description |
|-----------|------------|
| `self` | Current value of the field |
| `oldSelf` | Previous value (for update validation) |
| `self.field` | Access a sub-field |
| `self.list.exists(x, x.name == 'foo')` | Check if any item matches |
| `self.list.all(x, x.port > 0)` | Check all items match |
| `self.matches('^[a-z]+$')` | Regex match |
| `size(self) <= 10` | Collection/string size check |
| `has(self.optionalField)` | Check if optional field is set |

---

## Part 3: CRD Versioning

### 3.1 Why Version Your CRD?

Your CRD's schema will evolve. Fields get added, types change, structures get reorganized. Kubernetes CRD versioning lets you serve multiple versions simultaneously, with automatic conversion between them.

### 3.2 Multiple Versions

```yaml
apiVersion: apiextensions.k8s.io/v1
kind: CustomResourceDefinition
metadata:
  name: webapps.apps.kubedojo.io
spec:
  group: apps.kubedojo.io
  names:
    kind: WebApp
    listKind: WebAppList
    plural: webapps
    singular: webapp
  scope: Namespaced
  versions:
  - name: v1alpha1
    served: true       # Clients can read/write this version
    storage: false      # NOT the storage version
    deprecated: true    # Show deprecation warning
    deprecationWarning: "apps.kubedojo.io/v1alpha1 WebApp is deprecated; use v1beta1"
    schema:
      openAPIV3Schema:
        type: object
        properties:
          spec:
            type: object
            properties:
              image:
                type: string
              replicas:
                type: integer
              port:
                type: integer
          status:
            type: object
            properties:
              readyReplicas:
                type: integer

  - name: v1beta1
    served: true       # Clients can read/write this version
    storage: true       # THIS version is stored in etcd
    schema:
      openAPIV3Schema:
        type: object
        properties:
          spec:
            type: object
            required:
            - image
            properties:
              image:
                type: string
              replicas:
                type: integer
                minimum: 1
                maximum: 100
                default: 2
              ports:                  # Renamed from 'port' to 'ports' (array)
                type: array
                items:
                  type: object
                  properties:
                    name:
                      type: string
                    containerPort:
                      type: integer
                    protocol:
                      type: string
                      enum: ["TCP", "UDP"]
                      default: "TCP"
              resources:              # New field in v1beta1
                type: object
                properties:
                  cpuLimit:
                    type: string
                  memoryLimit:
                    type: string
          status:
            type: object
            properties:
              readyReplicas:
                type: integer
              conditions:
                type: array
                items:
                  type: object
                  properties:
                    type:
                      type: string
                    status:
                      type: string
```

### 3.3 Version Conversion

When a client requests a version different from the storage version, the API Server must convert. There are two approaches:

**None Strategy** (no-op): Only works when versions are compatible (additive changes only). New fields in newer versions get default values or are empty in older versions.

**Webhook Strategy**: A webhook server converts between versions. Required when schemas are structurally different.

```yaml
spec:
  conversion:
    strategy: Webhook
    webhook:
      conversionReviewVersions: ["v1"]
      clientConfig:
        service:
          namespace: webapp-system
          name: webapp-webhook
          path: /convert
          port: 443
        caBundle: <base64-encoded-CA-cert>
```

### 3.4 Storage Version Migration

When you change the storage version, existing objects in etcd are still stored in the old format. They get converted on the fly when read. To actually migrate the storage:

```bash
# List all objects (triggers conversion on read)
k get webapps --all-namespaces -o yaml > /dev/null

# Or use the storage version migrator (kube-storage-version-migrator)
# This systematically reads and rewrites all objects in the new storage version
```

> **Stop and think**: If you have 10,000 `WebApp` resources stored in etcd as `v1alpha1`, and you change the CRD to make `v1beta1` the storage version, do those 10,000 resources instantly get rewritten in etcd? What is the performance implication?

### 3.5 Diagnosing Version-Skew and Validation Failures

When evolving CRDs, you may encounter version-skew issues (e.g., clients using an older API version while the conversion webhook fails) or complex CEL validation errors. Use these techniques to diagnose them without modifying cluster state:

- **API Discovery**: Run `kubectl api-resources | grep <crd>` to verify which API version is preferred and currently served by the API Server.
- **Explicit Version Requests**: Fetch a resource using a specific fully-qualified version like `kubectl get webapps.v1alpha1.apps.kubedojo.io my-app -o yaml` to see exactly what older clients receive and test conversion webhook output.
- **Server-Side Dry Run**: Run `kubectl apply --dry-run=server -f <manifest>` to execute all CEL validation rules and admission webhooks in the API Server. This surfaces validation rejections immediately without saving partial or invalid objects to etcd.

---

## Part 4: Subresources

### 4.1 Status Subresource

The status subresource separates the `spec` (desired state, written by users) from `status` (observed state, written by controllers):

```yaml
versions:
- name: v1beta1
  served: true
  storage: true
  subresources:
    status: {}      # Enable /status subresource
  schema:
    openAPIV3Schema:
      # ... schema here
```

With the status subresource enabled:
- `PUT /apis/apps.kubedojo.io/v1beta1/namespaces/default/webapps/my-app` updates **only spec** (status changes are ignored)
- `PUT /apis/apps.kubedojo.io/v1beta1/namespaces/default/webapps/my-app/status` updates **only status** (spec changes are ignored)

```bash
# Users update spec
k patch webapp my-app --type=merge -p '{"spec":{"replicas":5}}'

# Controllers update status (using client-go)
# webapp.Status.ReadyReplicas = 5
# client.Status().Update(ctx, webapp)
```

### 4.2 Scale Subresource

The scale subresource lets `kubectl scale` and HPA work with your custom resource:

```yaml
versions:
- name: v1beta1
  served: true
  storage: true
  subresources:
    status: {}
    scale:
      specReplicasPath: .spec.replicas
      statusReplicasPath: .status.readyReplicas
      labelSelectorPath: .status.labelSelector
```

Now you can:

```bash
# Scale the custom resource
k scale webapp my-app --replicas=5

# Use HPA
k autoscale webapp my-app --min=2 --max=10 --cpu-percent=80
```

> **Pause and predict**: If you configure the HPA to scale your custom resource, but forget to define the `scale` subresource in your CRD, what exact error or behavior will you observe when the HPA attempts to read the current replica count?

---

## Part 5: Printer Columns

### 5.1 Custom kubectl Output

By default, `kubectl get <your-crd>` shows only Name and Age. Printer columns let you display useful fields:

```yaml
versions:
- name: v1beta1
  served: true
  storage: true
  additionalPrinterColumns:
  - name: Image
    type: string
    description: "Container image"
    jsonPath: .spec.image
    priority: 0          # 0 = always shown, 1+ = shown with -o wide
  - name: Replicas
    type: integer
    description: "Desired replicas"
    jsonPath: .spec.replicas
  - name: Ready
    type: integer
    description: "Ready replicas"
    jsonPath: .status.readyReplicas
  - name: Status
    type: string
    description: "Current status"
    jsonPath: .status.conditions[?(@.type=="Ready")].status
    priority: 0
  - name: Age
    type: date
    jsonPath: .metadata.creationTimestamp
```

Result:

```
$ kubectl get webapps
NAME       IMAGE             REPLICAS   READY   STATUS   AGE
my-app     nginx:1.27        3          3       True     5m
frontend   react-app:2.1     2          1       False    2m
```

### 5.2 JSONPath Reference for Printer Columns

| JSONPath Expression | Selects |
|-------------------|---------|
| `.spec.replicas` | Simple field |
| `.status.conditions[0].status` | First array element |
| `.status.conditions[?(@.type=="Ready")].status` | Filter by field value |
| `.metadata.creationTimestamp` | Standard field (use with `type: date`) |
| `.metadata.labels.app` | Label value |

---

## Part 6: Complete Production CRD

### 6.1 Putting It All Together

Here is a production-grade CRD that uses every feature covered in this module. Save this as `webapp-crd.yaml`:

```yaml
apiVersion: apiextensions.k8s.io/v1
kind: CustomResourceDefinition
metadata:
  name: webapps.apps.kubedojo.io
  annotations:
    controller-gen.kubebuilder.io/version: v0.17.0
spec:
  group: apps.kubedojo.io
  names:
    kind: WebApp
    listKind: WebAppList
    plural: webapps
    singular: webapp
    shortNames:
    - wa
    categories:
    - all
    - kubedojo
  scope: Namespaced
  versions:
  - name: v1beta1
    served: true
    storage: true
    subresources:
      status: {}
      scale:
        specReplicasPath: .spec.replicas
        statusReplicasPath: .status.readyReplicas
    additionalPrinterColumns:
    - name: Image
      type: string
      jsonPath: .spec.image
    - name: Desired
      type: integer
      jsonPath: .spec.replicas
    - name: Ready
      type: integer
      jsonPath: .status.readyReplicas
    - name: Phase
      type: string
      jsonPath: .status.phase
    - name: Age
      type: date
      jsonPath: .metadata.creationTimestamp
    schema:
      openAPIV3Schema:
        type: object
        description: "WebApp manages a web application deployment with optional ingress."
        required:
        - spec
        properties:
          apiVersion:
            type: string
          kind:
            type: string
          metadata:
            type: object
          spec:
            type: object
            description: "Desired state of the WebApp."
            required:
            - image
            x-kubernetes-validations:
            - rule: "self.minReplicas <= self.maxReplicas"
              message: "minReplicas cannot exceed maxReplicas"
            - rule: "self.replicas >= self.minReplicas && self.replicas <= self.maxReplicas"
              message: "replicas must be within [minReplicas, maxReplicas]"
            properties:
              image:
                type: string
                description: "Container image."
                minLength: 1
                maxLength: 255
              replicas:
                type: integer
                description: "Desired number of replicas."
                minimum: 0
                maximum: 500
                default: 2
              minReplicas:
                type: integer
                description: "Minimum replicas for autoscaling."
                minimum: 0
                default: 1
              maxReplicas:
                type: integer
                description: "Maximum replicas for autoscaling."
                minimum: 1
                maximum: 500
                default: 10
              ports:
                type: array
                description: "Ports to expose."
                maxItems: 20
                x-kubernetes-list-type: map
                x-kubernetes-list-map-keys:
                - containerPort
                items:
                  type: object
                  required:
                  - containerPort
                  properties:
                    name:
                      type: string
                      maxLength: 15
                    containerPort:
                      type: integer
                      minimum: 1
                      maximum: 65535
                    protocol:
                      type: string
                      enum: ["TCP", "UDP", "SCTP"]
                      default: "TCP"
              env:
                type: array
                description: "Environment variables."
                maxItems: 100
                items:
                  type: object
                  required:
                  - name
                  properties:
                    name:
                      type: string
                    value:
                      type: string
                    valueFrom:
                      type: string
                      description: "Secret or ConfigMap reference (name:key format)."
              resources:
                type: object
                properties:
                  requests:
                    type: object
                    properties:
                      cpu:
                        type: string
                        default: "100m"
                      memory:
                        type: string
                        default: "128Mi"
                  limits:
                    type: object
                    properties:
                      cpu:
                        type: string
                        default: "500m"
                      memory:
                        type: string
                        default: "512Mi"
              ingress:
                type: object
                x-kubernetes-validations:
                - rule: "!self.tlsEnabled || self.host != ''"
                  message: "host is required when TLS is enabled"
                properties:
                  enabled:
                    type: boolean
                    default: false
                  host:
                    type: string
                  path:
                    type: string
                    default: "/"
                  tlsEnabled:
                    type: boolean
                    default: false
                  tlsSecretName:
                    type: string
          status:
            type: object
            description: "Observed state of the WebApp."
            properties:
              phase:
                type: string
                enum: ["Pending", "Deploying", "Running", "Degraded", "Failed"]
              readyReplicas:
                type: integer
              availableReplicas:
                type: integer
              observedGeneration:
                type: integer
                format: int64
              conditions:
                type: array
                x-kubernetes-list-type: map
                x-kubernetes-list-map-keys:
                - type
                items:
                  type: object
                  required:
                  - type
                  - status
                  properties:
                    type:
                      type: string
                    status:
                      type: string
                      enum: ["True", "False", "Unknown"]
                    reason:
                      type: string
                    message:
                      type: string
                    lastTransitionTime:
                      type: string
                      format: date-time
```

### 6.2 Testing the CRD

```bash
# Apply the CRD
k apply -f webapp-crd.yaml

# Verify it registered and wait for the API server to serve it
k wait --for=condition=established crd/webapps.apps.kubedojo.io
k api-resources | grep webapp

# Create a valid WebApp
cat << 'EOF' | k apply -f -
apiVersion: apps.kubedojo.io/v1beta1
kind: WebApp
metadata:
  name: my-frontend
  namespace: default
spec:
  image: nginx:1.27
  replicas: 3
  minReplicas: 1
  maxReplicas: 10
  ports:
  - name: http
    containerPort: 80
  - name: metrics
    containerPort: 9090
  env:
  - name: NODE_ENV
    value: production
  resources:
    requests:
      cpu: "250m"
      memory: "256Mi"
    limits:
      cpu: "1"
      memory: "1Gi"
  ingress:
    enabled: true
    host: frontend.example.com
    path: /
    tlsEnabled: true
    tlsSecretName: frontend-tls
EOF

# Check printer columns
k get webapps
k get wa            # shortName works

# Try an invalid resource to diagnose validation failures using server dry-run
cat << 'EOF' | k apply --dry-run=server -f -
apiVersion: apps.kubedojo.io/v1beta1
kind: WebApp
metadata:
  name: invalid-app
spec:
  image: nginx:1.27
  replicas: 3
  minReplicas: 10     # ERROR: minReplicas > maxReplicas (default 10)
  maxReplicas: 5      # ERROR: less than minReplicas
EOF
# Expected: admission error from CEL validation

# Test scale subresource
k scale webapp my-frontend --replicas=5
k get webapp my-frontend -o jsonpath='{.spec.replicas}'
```

---

## Common Mistakes

| Mistake | Problem | Solution |
|---------|---------|----------|
| Non-structural schema | CRD rejected on apply | Ensure every field has a `type` |
| Missing `required` on spec | Users create empty objects | Mark essential fields as required |
| Regex too permissive | Invalid data gets through | Test patterns with edge cases |
| No status subresource | Users can overwrite controller status | Always enable status subresource |
| Changing storage version without migration | Old objects read with wrong schema | Migrate storage or use conversion webhook |
| Using `additionalProperties: true` at root | Untyped fields bypass validation | Only use on specific map fields |
| Forgetting printer columns | `kubectl get` shows only Name/Age | Add columns for key spec/status fields |
| CEL rules too complex | Slow validation, hard to debug | Keep rules simple, test individually |
| No `maxItems` / `maxLength` | Unbounded data fills etcd | Set reasonable limits on all collections |

---

## Quiz

1. **You are reviewing a colleague's CRD pull request. The schema uses `additionalProperties: true` at the root level and lacks explicit `type` declarations for several nested objects. When they try to apply it to a Kubernetes 1.22 cluster, it fails. Why does this happen, and what specific changes are needed to make the schema 'structural'?**
   <details>
   <summary>Answer</summary>
   The API Server rejects the CRD because Kubernetes 1.16+ strictly requires structural schemas for custom resources. A structural schema ensures the API Server can safely perform operations like server-side pruning and server-side apply. To fix this, your colleague must explicitly declare a `type` for every field, remove `additionalProperties` from the root of the schema, avoid references like `$ref`, and ensure all validation keywords are placed inside typed fields. Without these guarantees, the API Server cannot reliably validate or manage the lifecycle of the resource data.
   </details>

2. **Your team has deployed a custom `Database` CRD with a `status` field, but without enabling the status subresource. A developer accidentally applies a manifest that overwrites the `status.activeConnections` field, causing your controller to panic. How does enabling the `status` subresource prevent this, and how does it change how the controller updates the status?**
   <details>
   <summary>Answer</summary>
   Without the status subresource, the `status` field is treated like any other field in the `spec`, meaning anyone with update permissions on the resource can modify it directly. Enabling the status subresource creates a strict separation of concerns where the main resource endpoint ignores changes to `status`, and the separate `/status` endpoint ignores changes to `spec`. This prevents users from accidentally or maliciously tampering with the observed state. Your controller will then need to specifically target the `/status` subresource endpoint to update the `activeConnections` metric, ensuring only authorized components manage the state.
   </details>

3. **Your cluster has a `Certificate` CRD installed with `v1alpha1` configured as the storage version and `v1beta1` as a served version. A developer creates a new certificate using the `v1beta1` API. If you inspect the raw data stored in etcd, what version will you see, and how did it get there?**
   <details>
   <summary>Answer</summary>
   You will see the `v1alpha1` representation of the resource in etcd. When the API Server receives the `v1beta1` payload, it must first convert it to the designated storage version (`v1alpha1`) before persisting it. It accomplishes this either through a configured conversion webhook or via a no-op conversion if the strategy allows it. When any client subsequently reads the resource, the API Server will dynamically convert it from the `v1alpha1` storage format back to the version requested by the client on the fly.
   </details>

4. **Users of your `BackupJob` CRD keep entering invalid cron strings like "every day" in the `schedule` field, causing the backend controller to crash. You want to reject these invalid inputs at the API server level before they even reach your controller. Write a CEL validation rule that ensures the `schedule` field contains exactly 5 space-separated fields.**
   <details>
   <summary>Answer</summary>

   ```yaml
   x-kubernetes-validations:
   - rule: "self.matches('^(\\\\S+\\\\s+){4}\\\\S+$')"
     message: "schedule must be a valid cron expression with 5 fields"
   ```

   By embedding this CEL rule directly into the CRD schema, the API Server evaluates the regular expression during the admission phase. If a user submits an invalid string like "every day", the `matches` function evaluates to false, and the API Server synchronously rejects the request with the provided message. This prevents malformed data from ever being persisted to etcd or processed by your controller, significantly improving the robustness of your system. Note that while this validates the structural format, semantic validation of cron values requires a validating admission webhook.
   </details>

5. **Two different automation scripts are trying to update the `ports` array in your custom `LoadBalancer` resource simultaneously. Script A adds port 80, while Script B adds port 443. Currently, whoever saves last overwrites the other's port. How can you use `x-kubernetes-list-type: map` to solve this race condition?**
   <details>
   <summary>Answer</summary>
   By default, Kubernetes treats arrays as atomic lists, meaning an update will replace the entire array, causing the race condition you observed. By adding the `x-kubernetes-list-type: map` annotation and specifying `x-kubernetes-list-map-keys`, you instruct Server-Side Apply (SSA) to treat the array as a map keyed by a specific field. When Script A and Script B apply their updates, the API Server will merge the items intelligently based on their unique keys rather than replacing the whole list. This allows multiple actors to safely manage distinct elements within the same array without conflict.
   </details>

6. **You've added `default: 2` to the `replicas` field of your `WebApp` CRD, along with a CEL rule requiring `replicas >= minReplicas`. A user submits a manifest containing `minReplicas: 1` but omits the `replicas` field entirely. Does the resource pass validation, and what exactly happens to the `replicas` field during the request lifecycle?**
   <details>
   <summary>Answer</summary>
   Yes, the resource will pass validation because the defaulting mechanism happens before the validation phase. When the API Server receives the request, the mutating admission phase applies the CRD's defaulting logic, injecting `replicas: 2` into the object. By the time the CEL validation rule evaluates `self.replicas >= self.minReplicas`, the value is 2, satisfying the condition. The resource is then persisted to etcd with the default value explicitly set, even though the user didn't provide it in their original manifest.
   </details>

7. **Your platform team complains that `kubectl get myresource` outputs too many columns and wraps on smaller terminal screens. You want to hide the `LastBackup` and `StatusReason` columns by default, but still allow power users to view them without outputting raw JSON/YAML. How do you configure the printer columns to achieve this?**
   <details>
   <summary>Answer</summary>
   You achieve this by assigning a `priority: 1` (or higher) to the `LastBackup` and `StatusReason` printer columns, while keeping the essential columns at `priority: 0`. Priority 0 columns are always displayed in the standard `kubectl get` output, keeping the default view clean and concise. Columns with priority 1 or higher are considered extended information and are only revealed when a user explicitly requests them by appending `-o wide` to their command. This provides a better user experience by balancing immediate readability with accessible detail.
   </details>

8. **A developer typos the `image` field as `imgae` in their `DeploymentConfig` custom resource manifest. The CRD uses a strict structural schema. They apply the manifest, receive a success message, but the controller doesn't deploy the new image. When they inspect the resource in the cluster, the `imgae` field is completely missing. Why did this happen?**
   <details>
   <summary>Answer</summary>
   The API Server silently removed the `imgae` field because of a feature called server-side pruning, which is enforced by structural schemas. When the API Server receives a resource containing fields not explicitly defined in the CRD's OpenAPI schema, it drops those unknown fields before validating and persisting the object to etcd. This ensures that the stored data strictly conforms to the declared schema and prevents obsolete or misspelled data from accumulating over time. If you legitimately need to store arbitrary data in a specific sub-tree, you must explicitly configure that field with `x-kubernetes-preserve-unknown-fields: true`.
   </details>

---

## Hands-On Exercise

**Task**: Create a production-grade CRD for a `BackupPolicy` resource with comprehensive validation, multiple versions, printer columns, and subresources.

**Requirements**:

The `BackupPolicy` CRD should model a backup scheduling system with:
- **v1alpha1**: Basic fields (schedule, retention days, target)
- **v1beta1**: Extended fields (schedule, retention with policy, target with selectors, notifications)
- Validation: cron schedule format, sane retention limits, cross-field validation
- Status and scale subresources
- Printer columns showing schedule, retention, last backup time, status

**Steps**:

1. **Create the CRD** with both versions:
```bash
cat << 'CRDEOF' | k apply -f -
apiVersion: apiextensions.k8s.io/v1
kind: CustomResourceDefinition
metadata:
  name: backuppolicies.data.kubedojo.io
spec:
  group: data.kubedojo.io
  names:
    kind: BackupPolicy
    listKind: BackupPolicyList
    plural: backuppolicies
    singular: backuppolicy
    shortNames:
    - bp
    categories:
    - kubedojo
  scope: Namespaced
  versions:
  - name: v1alpha1
    served: true
    storage: false
    deprecated: true
    deprecationWarning: "data.kubedojo.io/v1alpha1 BackupPolicy is deprecated; use v1beta1"
    schema:
      openAPIV3Schema:
        type: object
        properties:
          spec:
            type: object
            required:
            - schedule
            - target
            properties:
              schedule:
                type: string
              retentionDays:
                type: integer
                minimum: 1
                maximum: 365
                default: 30
              target:
                type: string
          status:
            type: object
            properties:
              lastBackup:
                type: string
                format: date-time
              backupCount:
                type: integer
    additionalPrinterColumns:
    - name: Schedule
      type: string
      jsonPath: .spec.schedule
    - name: Retention
      type: integer
      jsonPath: .spec.retentionDays
    - name: Age
      type: date
      jsonPath: .metadata.creationTimestamp

  - name: v1beta1
    served: true
    storage: true
    subresources:
      status: {}
    additionalPrinterColumns:
    - name: Schedule
      type: string
      jsonPath: .spec.schedule
    - name: Retention
      type: string
      jsonPath: .spec.retention.maxAge
    - name: Last Backup
      type: string
      jsonPath: .status.lastBackupTime
    - name: Status
      type: string
      jsonPath: .status.phase
    - name: Backups
      type: integer
      jsonPath: .status.successfulBackups
      priority: 1
    - name: Age
      type: date
      jsonPath: .metadata.creationTimestamp
    schema:
      openAPIV3Schema:
        type: object
        required:
        - spec
        properties:
          spec:
            type: object
            required:
            - schedule
            - target
            x-kubernetes-validations:
            - rule: "self.retention.maxCount >= self.retention.minCount"
              message: "maxCount must be >= minCount"
            properties:
              schedule:
                type: string
                description: "Cron schedule expression."
                minLength: 9
                maxLength: 100
              paused:
                type: boolean
                default: false
              retention:
                type: object
                properties:
                  maxAge:
                    type: string
                    description: "Maximum age (e.g., 30d, 12h)."
                    pattern: '^[0-9]+(d|h|m)$'
                    default: "30d"
                  maxCount:
                    type: integer
                    minimum: 1
                    maximum: 1000
                    default: 100
                  minCount:
                    type: integer
                    minimum: 1
                    maximum: 100
                    default: 3
              target:
                type: object
                required:
                - kind
                properties:
                  kind:
                    type: string
                    enum: ["Deployment", "StatefulSet", "PersistentVolumeClaim", "Namespace"]
                  name:
                    type: string
                  labelSelector:
                    type: object
                    properties:
                      matchLabels:
                        type: object
                        additionalProperties:
                          type: string
              notifications:
                type: array
                maxItems: 5
                items:
                  type: object
                  required:
                  - type
                  - endpoint
                  properties:
                    type:
                      type: string
                      enum: ["slack", "email", "webhook"]
                    endpoint:
                      type: string
                    onlyOnFailure:
                      type: boolean
                      default: true
          status:
            type: object
            properties:
              phase:
                type: string
                enum: ["Active", "Paused", "Failing", "Unknown"]
              lastBackupTime:
                type: string
                format: date-time
              nextBackupTime:
                type: string
                format: date-time
              successfulBackups:
                type: integer
              failedBackups:
                type: integer
              conditions:
                type: array
                items:
                  type: object
                  required:
                  - type
                  - status
                  properties:
                    type:
                      type: string
                    status:
                      type: string
                      enum: ["True", "False", "Unknown"]
                    reason:
                      type: string
                    message:
                      type: string
                    lastTransitionTime:
                      type: string
                      format: date-time
CRDEOF
```

```bash
# Wait for the CRD to become established before using it
k wait --for=condition=established crd/backuppolicies.data.kubedojo.io
```

2. **Create a valid BackupPolicy**:
```bash
cat << 'EOF' | k apply -f -
apiVersion: data.kubedojo.io/v1beta1
kind: BackupPolicy
metadata:
  name: daily-db-backup
  namespace: default
spec:
  schedule: "0 2 * * *"
  retention:
    maxAge: "30d"
    maxCount: 90
    minCount: 7
  target:
    kind: StatefulSet
    name: postgres
  notifications:
  - type: slack
    endpoint: "https://hooks.slack.com/services/xxx"
    onlyOnFailure: true
EOF
```

3. **Verify printer columns**:
```bash
k get backuppolicies
k get bp              # shortName
k get bp -o wide      # includes priority 1 columns
```

4. **Test validation** (these should fail):
```bash
# Missing required field
cat << 'EOF' | k apply -f - 2>&1 || true
apiVersion: data.kubedojo.io/v1beta1
kind: BackupPolicy
metadata:
  name: bad-policy-1
spec:
  schedule: "0 2 * * *"
EOF

# Invalid retention (minCount > maxCount)
cat << 'EOF' | k apply -f - 2>&1 || true
apiVersion: data.kubedojo.io/v1beta1
kind: BackupPolicy
metadata:
  name: bad-policy-2
spec:
  schedule: "0 2 * * *"
  retention:
    maxCount: 2
    minCount: 10
  target:
    kind: Deployment
    name: my-app
EOF
```

5. **Test the deprecated v1alpha1**:
```bash
cat << 'EOF' | k apply -f -
apiVersion: data.kubedojo.io/v1alpha1
kind: BackupPolicy
metadata:
  name: old-style-backup
spec:
  schedule: "0 3 * * 0"
  retentionDays: 14
  target: "deployment/web"
EOF
# You should see a deprecation warning
```

6. **Cleanup**:
```bash
k delete backuppolicies --all
k delete crd backuppolicies.data.kubedojo.io
```

**Success Criteria**:
- [ ] CRD registers successfully with both versions
- [ ] Valid resources create without errors
- [ ] Invalid resources are rejected with clear error messages
- [ ] CEL cross-field validation works (minCount <= maxCount)
- [ ] Printer columns display correctly
- [ ] ShortName `bp` works
- [ ] v1alpha1 shows deprecation warning
- [ ] Status subresource is enabled (verify with `k get crd webapps.apps.kubedojo.io -o yaml`)

---

## Next Module

[Module 1.3: Building Controllers with client-go](../module-1.3-controllers-client-go/) - Write a complete Kubernetes controller from scratch using the patterns you learned in Modules 1.1 and 1.2.