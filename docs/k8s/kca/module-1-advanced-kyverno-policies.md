# Module 1: Advanced Kyverno Policies

> **Complexity**: `[COMPLEX]` - Domain 5: Kyverno Advanced Policy Writing (32% of exam)
>
> **Time to Complete**: 90-120 minutes
>
> **Prerequisites**: Kyverno basics (install, ClusterPolicy vs Policy), Kubernetes admission controllers, familiarity with YAML and kubectl

---

## Why This Module Matters

Domain 5 is the single largest section of the KCA exam at 32%. You cannot pass without mastering advanced Kyverno policy writing. While basic validate/mutate rules get you started, the exam tests CEL expressions, image verification, cleanup policies, complex JMESPath, JSON patches, autogen behavior, background scans, API call variables, and preconditions. This module covers every one of those topics with copy-paste-ready examples.

**War Story**: A platform team at a fintech company deployed Kyverno with a simple "require labels" policy and called it done. Three months later, an engineer pushed an unsigned container image to production that contained a cryptocurrency miner. The team had never configured `verifyImages`. After the incident, they wrote 40+ advanced policies covering image signatures, resource cleanup, and conditional enforcement. The lesson: basic policies are table stakes. Advanced policies are where real security lives.

---

## Did You Know?

- Kyverno's CEL support (added in 1.11) lets you write validation rules that are 3-5x shorter than equivalent JMESPath expressions for simple field checks.
- The `verifyImages` rule type runs as a mutating webhook first (to add the image digest) and then as a validating webhook, making it unique among Kyverno rule types.
- Kyverno `CleanupPolicy` resources run on a schedule using a CronJob-like syntax, not as admission webhooks -- they are the only Kyverno policy type that is not triggered by API requests.
- Background scans can retroactively flag every non-compliant resource in your cluster, generating Policy Reports without blocking anything -- perfect for audit-first rollouts.

---

## 1. CEL (Common Expression Language)

CEL is a lightweight expression language originally developed by Google. Kyverno supports CEL as an alternative to JMESPath for validation expressions.

### CEL Syntax Basics

```yaml
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata:
  name: require-run-as-nonroot
spec:
  validationFailureAction: Enforce
  rules:
    - name: check-nonroot
      match:
        any:
          - resources:
              kinds:
                - Pod
      validate:
        cel:
          expressions:
            - expression: >-
                object.spec.containers.all(c,
                  has(c.securityContext) &&
                  has(c.securityContext.runAsNonRoot) &&
                  c.securityContext.runAsNonRoot == true)
              message: "All containers must set securityContext.runAsNonRoot to true."
```

### CEL vs JMESPath: When to Use Which

| Feature | CEL | JMESPath |
|---|---|---|
| **Syntax style** | C-like (`object.spec.x`) | Path-based (`request.object.spec.x`) |
| **Type safety** | Strongly typed at parse time | Loosely typed |
| **List operations** | `all()`, `exists()`, `filter()`, `map()` | Projections, filters |
| **String functions** | `startsWith()`, `contains()`, `matches()` | `starts_with()`, `contains()` |
| **Best for** | Simple field checks, boolean logic | Complex data transformations |
| **Mutation support** | No (validate only) | Yes (validate + mutate) |
| **Kyverno version** | 1.11+ | All versions |

**Exam tip**: CEL cannot be used in mutate rules. If the question requires mutation, you must use JMESPath.

### CEL with `oldObject` for UPDATE Validation

```yaml
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata:
  name: prevent-label-removal
spec:
  validationFailureAction: Enforce
  rules:
    - name: block-label-delete
      match:
        any:
          - resources:
              kinds:
                - Deployment
              operations:
                - UPDATE
      validate:
        cel:
          expressions:
            - expression: >-
                !has(oldObject.metadata.labels.app) ||
                has(object.metadata.labels.app)
              message: "The 'app' label cannot be removed once set."
```

---

## 2. verifyImages: Cosign and Attestation Checks

The `verifyImages` rule type enforces that container images are signed and optionally carry specific attestations before they can run in the cluster.

### Cosign Signature Verification

```yaml
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata:
  name: verify-image-signature
spec:
  validationFailureAction: Enforce
  webhookTimeoutSeconds: 30
  rules:
    - name: verify-cosign-signature
      match:
        any:
          - resources:
              kinds:
                - Pod
      verifyImages:
        - imageReferences:
            - "registry.example.com/*"
          attestors:
            - count: 1
              entries:
                - keys:
                    publicKeys: |-
                      -----BEGIN PUBLIC KEY-----
                      MFkwEwYHKoZIzj0CAQYIKoZIzj0DAQcDQgAEsLeM2H+JQfHi1PtMFbJFo3pABv2
                      OKjrFHxGnTYNeFJ4mDPOI8gMSMcKzfcWaVMPe8ZuGAsCmoAxmyBXnbPHTQ==
                      -----END PUBLIC KEY-----
```

### Notary Signature Verification

```yaml
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata:
  name: verify-notary-signature
spec:
  validationFailureAction: Enforce
  rules:
    - name: verify-notary
      match:
        any:
          - resources:
              kinds:
                - Pod
      verifyImages:
        - imageReferences:
            - "registry.example.com/*"
          attestors:
            - entries:
                - certificates:
                    cert: |-
                      -----BEGIN CERTIFICATE-----
                      ...your certificate here...
                      -----END CERTIFICATE-----
```

### Attestation Checks (SBOM / Vulnerability Scan)

```yaml
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata:
  name: verify-vulnerability-scan
spec:
  validationFailureAction: Enforce
  rules:
    - name: check-vuln-attestation
      match:
        any:
          - resources:
              kinds:
                - Pod
      verifyImages:
        - imageReferences:
            - "registry.example.com/*"
          attestors:
            - entries:
                - keys:
                    publicKeys: |-
                      -----BEGIN PUBLIC KEY-----
                      ...
                      -----END PUBLIC KEY-----
          attestations:
            - type: https://cosign.sigstore.dev/attestation/vuln/v1
              conditions:
                - all:
                    - key: "{{ scanner }}"
                      operator: Equals
                      value: "trivy"
                    - key: "{{ result[?severity == 'CRITICAL'] | length(@) }}"
                      operator: LessThanOrEquals
                      value: "0"
```

This policy blocks any image that has critical vulnerabilities in its Trivy attestation.

---

## 3. Cleanup Policies

Cleanup policies automatically delete resources matching specific criteria on a schedule. They are defined using the `CleanupPolicy` (namespaced) or `ClusterCleanupPolicy` (cluster-wide) CRDs.

### Basic CleanupPolicy: Delete Old Pods

```yaml
apiVersion: kyverno.io/v2
kind: ClusterCleanupPolicy
metadata:
  name: delete-failed-pods
spec:
  match:
    any:
      - resources:
          kinds:
            - Pod
  conditions:
    any:
      - key: "{{ target.status.phase }}"
        operator: Equals
        value: Failed
  schedule: "*/15 * * * *"
```

This runs every 15 minutes and deletes all Pods in `Failed` phase across the cluster.

### TTL-Based Cleanup

```yaml
apiVersion: kyverno.io/v2
kind: CleanupPolicy
metadata:
  name: cleanup-old-configmaps
  namespace: staging
spec:
  match:
    any:
      - resources:
          kinds:
            - ConfigMap
          selector:
            matchLabels:
              temporary: "true"
  conditions:
    any:
      - key: "{{ time_since('', '{{ target.metadata.creationTimestamp }}', '') }}"
        operator: GreaterThan
        value: "24h"
  schedule: "0 */6 * * *"
```

Every 6 hours, this deletes ConfigMaps labeled `temporary: "true"` that are older than 24 hours.

### Cleanup Policy with Exclusions

```yaml
apiVersion: kyverno.io/v2
kind: ClusterCleanupPolicy
metadata:
  name: cleanup-completed-jobs
spec:
  match:
    any:
      - resources:
          kinds:
            - Job
  exclude:
    any:
      - resources:
          selector:
            matchLabels:
              retain: "true"
  conditions:
    all:
      - key: "{{ target.status.succeeded }}"
        operator: GreaterThan
        value: 0
  schedule: "0 2 * * *"
```

---

## 4. Complex JMESPath

JMESPath is Kyverno's primary expression language. Advanced queries go well beyond simple field access.

### Multi-Level Queries and Projections

```yaml
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata:
  name: limit-container-ports
spec:
  validationFailureAction: Enforce
  rules:
    - name: max-three-ports
      match:
        any:
          - resources:
              kinds:
                - Pod
      validate:
        message: "Each container may expose a maximum of 3 ports."
        deny:
          conditions:
            any:
              - key: "{{ request.object.spec.containers[?length(ports || `[]`) > `3`] | length(@) }}"
                operator: GreaterThan
                value: 0
```

This uses a JMESPath filter projection (`[?...]`) to find containers with more than 3 ports, then checks whether any matched.

### Key JMESPath Functions for the Exam

```yaml
# length() - count items or string length
"{{ request.object.spec.containers | length(@) }}"

# contains() - check if array/string contains a value
"{{ contains(request.object.metadata.labels.keys(@), 'app') }}"

# starts_with() / ends_with() - string prefix/suffix checks
"{{ starts_with(request.object.metadata.name, 'prod-') }}"

# join() - concatenate array elements
"{{ request.object.spec.containers[*].name | join(', ', @) }}"

# to_string() / to_number() - type conversion
"{{ to_number(request.object.spec.containers[0].resources.limits.cpu || '0') }}"

# merge() - combine objects
"{{ merge(request.object.metadata.labels, `{\"managed-by\": \"kyverno\"}`) }}"

# not_null() - return first non-null value
"{{ not_null(request.object.metadata.labels.team, 'unknown') }}"
```

### Multi-Level Projection Example

```yaml
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata:
  name: require-resource-limits
spec:
  validationFailureAction: Enforce
  rules:
    - name: check-all-containers
      match:
        any:
          - resources:
              kinds:
                - Pod
      validate:
        message: >-
          All containers must define memory limits. Missing in:
          {{ request.object.spec.containers[?!contains(keys(resources.limits || `{}`), 'memory')].name | join(', ', @) }}
        deny:
          conditions:
            any:
              - key: "{{ request.object.spec.containers[?!contains(keys(resources.limits || `{}`), 'memory')] | length(@) }}"
                operator: GreaterThan
                value: 0
```

This policy not only blocks non-compliant Pods but tells the user exactly which containers are missing memory limits.

---

## 5. JSON Patches (RFC 6902)

Kyverno supports two mutation approaches: **strategic merge patches** (overlay) and **RFC 6902 JSON patches**. JSON patches give you precise control with `add`, `remove`, `replace`, `move`, `copy`, and `test` operations.

### When to Use JSON Patch vs Strategic Merge

| Scenario | Use JSON Patch | Use Strategic Merge |
|---|---|---|
| Add a sidecar container | Yes | Works but verbose |
| Set a single field | Either works | Simpler syntax |
| Remove a field | Yes (only option) | Cannot remove |
| Conditional array element changes | Yes | No |
| Add to a specific array index | Yes | No |

### JSON Patch: Inject Sidecar Container

```yaml
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata:
  name: inject-logging-sidecar
spec:
  rules:
    - name: add-sidecar
      match:
        any:
          - resources:
              kinds:
                - Pod
              selector:
                matchLabels:
                  inject-sidecar: "true"
      mutate:
        patchesJson6902: |-
          - op: add
            path: "/spec/containers/-"
            value:
              name: log-collector
              image: fluent/fluent-bit:3.0
              resources:
                limits:
                  memory: "128Mi"
                  cpu: "100m"
              volumeMounts:
                - name: shared-logs
                  mountPath: /var/log/app
          - op: add
            path: "/spec/volumes/-"
            value:
              name: shared-logs
              emptyDir: {}
```

The `/-` at the end of the path means "append to the array."

### JSON Patch: Remove and Replace

```yaml
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata:
  name: enforce-image-registry
spec:
  rules:
    - name: replace-image-registry
      match:
        any:
          - resources:
              kinds:
                - Pod
      mutate:
        patchesJson6902: |-
          - op: replace
            path: "/spec/containers/0/image"
            value: "registry.internal.example.com/nginx:1.27"
```

**Caution**: JSON Patch uses integer array indices (`/0`, `/1`). If the index does not exist, the patch will fail. Strategic merge is safer when you do not know the exact array position.

---

## 6. Autogen Rules

Kyverno automatically generates rules for Pod controllers (Deployments, DaemonSets, StatefulSets, Jobs, CronJobs, ReplicaSets) from policies that target Pods. This means you write one rule for Pods and get coverage for all controllers that create Pods.

### How Autogen Works

```
┌─────────────────────────────────────────────────────┐
│  You write a policy matching: Pod                   │
│                                                     │
│  Kyverno auto-generates rules for:                  │
│  ├── Deployment    (spec.template.spec.containers)  │
│  ├── DaemonSet     (spec.template.spec.containers)  │
│  ├── StatefulSet   (spec.template.spec.containers)  │
│  ├── ReplicaSet    (spec.template.spec.containers)  │
│  ├── Job           (spec.template.spec.containers)  │
│  └── CronJob       (spec.jobTemplate.spec.template) │
└─────────────────────────────────────────────────────┘
```

### Controlling Autogen Behavior

You can disable autogen entirely or for specific controllers using the `pod-policies.kyverno.io/autogen-controllers` annotation:

```yaml
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata:
  name: require-labels
  annotations:
    # Only auto-generate for Deployments and StatefulSets
    pod-policies.kyverno.io/autogen-controllers: Deployment,StatefulSet
spec:
  rules:
    - name: require-app-label
      match:
        any:
          - resources:
              kinds:
                - Pod
      validate:
        message: "The label 'app' is required."
        pattern:
          metadata:
            labels:
              app: "?*"
```

To disable autogen completely:

```yaml
metadata:
  annotations:
    pod-policies.kyverno.io/autogen-controllers: none
```

### Viewing Generated Rules

```bash
# After applying a Pod-targeting policy, inspect the generated rules:
k get clusterpolicy require-labels -o yaml | grep -A 5 "autogen-"
```

Kyverno stores the autogenerated rules directly in the policy object under `status.autogen` (or inline in the spec, depending on version). Each generated rule has a name prefixed with `autogen-`.

**Exam tip**: If your policy uses a field path not under `spec.containers` (for example `spec.nodeName`), autogen will not be able to translate it for controllers and may silently skip generation. Always verify with `kubectl get`.

---

## 7. Background Scans

By default, Kyverno evaluates policies both at admission time (when resources are created/updated) and through periodic background scans of existing resources.

### Configuring Background Scan Behavior

```yaml
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata:
  name: audit-privileged-containers
spec:
  validationFailureAction: Audit
  background: true  # default is true
  rules:
    - name: deny-privileged
      match:
        any:
          - resources:
              kinds:
                - Pod
      validate:
        message: "Privileged containers are not allowed."
        pattern:
          spec:
            containers:
              - securityContext:
                  privileged: "!true"
```

With `background: true` and `validationFailureAction: Audit`, Kyverno scans all existing Pods and generates PolicyReport entries for violations without blocking anything.

### Admission-Only Enforcement

```yaml
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata:
  name: block-latest-tag
spec:
  validationFailureAction: Enforce
  background: false  # only check at admission time
  rules:
    - name: no-latest
      match:
        any:
          - resources:
              kinds:
                - Pod
      validate:
        message: "The ':latest' tag is not allowed."
        pattern:
          spec:
            containers:
              - image: "!*:latest"
```

Set `background: false` when the rule only makes sense at admission time or when you want to avoid generating reports for pre-existing resources.

### Reading Policy Reports

```bash
# List all policy reports (namespaced)
k get policyreport -A

# View a specific report's results
k get policyreport -n default -o yaml

# Cluster-scoped reports
k get clusterpolicyreport
```

Policy Reports follow the [Policy Report CRD standard](https://github.com/kubernetes-sigs/wg-policy-prototypes) and include `pass`, `fail`, `warn`, and `error` results for each scanned resource.

---

## 8. Variables and API Calls

Kyverno policies can use context variables to pull data from external sources, including the Kubernetes API, ConfigMaps, and image registries.

### Using ConfigMap as a Variable Source

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: allowed-registries
  namespace: kyverno
data:
  registries: "registry.example.com,gcr.io/my-project,docker.io/myorg"
---
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata:
  name: restrict-registries-from-configmap
spec:
  validationFailureAction: Enforce
  rules:
    - name: check-registry
      match:
        any:
          - resources:
              kinds:
                - Pod
      context:
        - name: allowedRegistries
          configMap:
            name: allowed-registries
            namespace: kyverno
      validate:
        message: >-
          Image registry is not in the allowed list.
          Allowed: {{ allowedRegistries.data.registries }}
        deny:
          conditions:
            all:
              - key: "{{ request.object.spec.containers[].image | [0] | split(@, '/') | [0] }}"
                operator: AnyNotIn
                value: "{{ allowedRegistries.data.registries | split(@, ',') }}"
```

### Calling the Kubernetes API

```yaml
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata:
  name: require-namespace-label
spec:
  validationFailureAction: Enforce
  rules:
    - name: check-ns-label
      match:
        any:
          - resources:
              kinds:
                - Pod
      context:
        - name: nsLabels
          apiCall:
            urlPath: "/api/v1/namespaces/{{ request.namespace }}"
            jmesPath: "metadata.labels"
      validate:
        message: >-
          Pods can only be created in namespaces with a 'team' label.
          Namespace '{{ request.namespace }}' is missing the 'team' label.
        deny:
          conditions:
            any:
              - key: team
                operator: AnyNotIn
                value: "{{ nsLabels | keys(@) }}"
```

This calls the Kubernetes API at admission time to fetch the namespace's labels and blocks Pod creation if the namespace is missing a `team` label.

### API Call with POST (Service Call)

```yaml
context:
  - name: externalCheck
    apiCall:
      method: POST
      urlPath: "https://policy-check.internal/validate"
      data:
        - key: image
          value: "{{ request.object.spec.containers[0].image }}"
      jmesPath: "allowed"
```

---

## 9. Preconditions

Preconditions control whether a rule executes at all. They are evaluated before the rule's match/exclude logic and are ideal for conditional enforcement.

### Basic Precondition

```yaml
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata:
  name: require-probes-in-prod
spec:
  validationFailureAction: Enforce
  rules:
    - name: check-readiness-probe
      match:
        any:
          - resources:
              kinds:
                - Pod
      preconditions:
        all:
          - key: "{{ request.namespace }}"
            operator: In
            value:
              - production
              - prod-*
      validate:
        message: "All containers in production namespaces must have a readinessProbe."
        pattern:
          spec:
            containers:
              - readinessProbe: {}
```

This rule only fires for Pods in production namespaces. In staging, no readiness probe is required.

### Preconditions with Complex Logic

```yaml
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata:
  name: enforce-image-digest-for-critical
spec:
  validationFailureAction: Enforce
  rules:
    - name: digest-required
      match:
        any:
          - resources:
              kinds:
                - Pod
      preconditions:
        any:
          - key: "{{ request.object.metadata.labels.criticality || '' }}"
            operator: Equals
            value: "high"
          - key: "{{ request.namespace }}"
            operator: In
            value:
              - production
              - financial
      validate:
        message: >-
          Critical workloads must use image digests, not tags.
          Use image@sha256:... format.
        deny:
          conditions:
            any:
              - key: "{{ request.object.spec.containers[?!contains(@.image, '@sha256:')] | length(@) }}"
                operator: GreaterThan
                value: 0
```

This applies image digest requirements only to Pods labeled `criticality: high` OR in `production`/`financial` namespaces.

### Precondition Operators Reference

| Operator | Description | Example |
|---|---|---|
| `Equals` / `NotEquals` | Exact match | `key: "foo"`, `value: "foo"` |
| `In` / `NotIn` | Membership check | `key: "foo"`, `value: ["foo","bar"]` |
| `GreaterThan` / `LessThan` | Numeric comparison | `key: "5"`, `value: 3` |
| `GreaterThanOrEquals` / `LessThanOrEquals` | Inclusive comparison | `key: "5"`, `value: 5` |
| `AnyIn` / `AnyNotIn` | Any element matches | Array-to-array comparison |
| `AllIn` / `AllNotIn` | All elements match | Array-to-array comparison |
| `DurationGreaterThan` | Time duration comparison | `key: "2h"`, `value: "1h"` |

---

## Common Mistakes

| Mistake | Problem | Solution |
|---|---|---|
| Using CEL in mutate rules | CEL only works with validate | Use JMESPath for mutation |
| Forgetting `webhookTimeoutSeconds` on `verifyImages` | Signature verification can be slow; default 10s may timeout | Set to 30s for image verification policies |
| Using `background: true` with `verifyImages` | Image verification cannot run in background scans | Kyverno ignores background for verifyImages, but be aware |
| JSON Patch with wrong array index | Index out of bounds causes patch failure | Use `/-` to append, or use strategic merge |
| Not quoting JMESPath backtick literals | `` `[]` `` and `` `{}` `` are JMESPath literals, not YAML | Wrap entire expression in double quotes |
| Assuming autogen works for all fields | Fields outside `spec.containers` may not translate | Verify with `kubectl get clusterpolicy -o yaml` |
| CleanupPolicy without RBAC | Kyverno SA needs delete permission on target resources | Ensure Kyverno ClusterRole covers cleanup targets |
| Precondition `any` vs `all` confusion | `any` = OR logic, `all` = AND logic | Think "any of these must be true" vs "all must be true" |

---

## Quiz

**Question 1**: What is the key limitation of CEL compared to JMESPath in Kyverno?

<details>
<summary>Show Answer</summary>

CEL can only be used in `validate` rules. It cannot be used for `mutate`, `generate`, or `verifyImages` rules. If you need to modify resources, you must use JMESPath.

</details>

**Question 2**: In a `verifyImages` policy, what is the purpose of the `attestations` field?

<details>
<summary>Show Answer</summary>

The `attestations` field checks that an image carries specific in-toto attestations (such as vulnerability scan results, SBOM, or build provenance) in addition to a valid signature. You can define conditions on the attestation payload to enforce requirements like "zero critical vulnerabilities."

</details>

**Question 3**: How does a `CleanupPolicy` differ from a `validate` or `mutate` policy in terms of execution model?

<details>
<summary>Show Answer</summary>

CleanupPolicies run on a cron schedule (defined in the `schedule` field) and delete matching resources. They are not triggered by API admission webhooks. Validate and mutate policies run at admission time (and optionally during background scans).

</details>

**Question 4**: What does the JSON Patch path `"/spec/containers/-"` mean?

<details>
<summary>Show Answer</summary>

The `/-` suffix means "append to the end of the array." It adds a new element to the `containers` array without needing to know the current array length or specify an index.

</details>

**Question 5**: You write a ClusterPolicy targeting Pods. Without any annotations, which resource kinds will Kyverno auto-generate rules for?

<details>
<summary>Show Answer</summary>

Kyverno auto-generates rules for: Deployment, DaemonSet, StatefulSet, ReplicaSet, Job, and CronJob. These are all the built-in Pod controllers. The annotation `pod-policies.kyverno.io/autogen-controllers` can restrict or disable this behavior.

</details>

**Question 6**: What is the difference between `background: true` with `validationFailureAction: Audit` vs `validationFailureAction: Enforce`?

<details>
<summary>Show Answer</summary>

With `Audit`, background scans generate PolicyReport entries for non-compliant existing resources but do not block anything. With `Enforce`, background scans still generate reports (they cannot delete or block existing resources), but new admissions will be blocked. Background scans themselves never delete or modify resources -- they only report.

</details>

**Question 7**: In a policy context, how do you call the Kubernetes API to fetch information about the namespace where a Pod is being created?

<details>
<summary>Show Answer</summary>

Use the `apiCall` context variable with `urlPath: "/api/v1/namespaces/{{ request.namespace }}"`. You can then use `jmesPath` to extract specific fields from the API response. This call is made at admission time with Kyverno's service account credentials.

</details>

**Question 8**: A precondition block has `any` at the top level containing two conditions. When does the rule execute?

<details>
<summary>Show Answer</summary>

The rule executes when at least one of the two conditions is true. The `any` keyword means OR logic -- if any condition in the list evaluates to true, the precondition passes and the rule is evaluated. Use `all` for AND logic where every condition must be true.

</details>

**Question 9**: You need to remove the `hostNetwork: true` field from a Pod spec using mutation. Can you use strategic merge patch for this? Why or why not?

<details>
<summary>Show Answer</summary>

No. Strategic merge patches cannot remove fields -- they can only add or replace values. To remove a field, you must use a JSON Patch (RFC 6902) with `op: remove` and `path: "/spec/hostNetwork"`.

</details>

---

## Hands-On Exercise

### Objective

Build a multi-rule ClusterPolicy that combines five advanced techniques. Test each rule to verify it works.

### Prerequisites

```bash
# Start a kind cluster
kind create cluster --name kyverno-lab

# Install Kyverno
helm repo add kyverno https://kyverno.github.io/kyverno/
helm repo update
helm install kyverno kyverno/kyverno -n kyverno --create-namespace
```

### Step 1: Create the Combined Policy

Save this as `advanced-policy.yaml` and apply it:

```yaml
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata:
  name: advanced-kca-exercise
  annotations:
    pod-policies.kyverno.io/autogen-controllers: Deployment,StatefulSet
spec:
  validationFailureAction: Enforce
  background: true
  webhookTimeoutSeconds: 30
  rules:
    # Rule 1: CEL validation - require runAsNonRoot
    - name: cel-nonroot
      match:
        any:
          - resources:
              kinds:
                - Pod
      validate:
        cel:
          expressions:
            - expression: >-
                object.spec.containers.all(c,
                  has(c.securityContext) &&
                  has(c.securityContext.runAsNonRoot) &&
                  c.securityContext.runAsNonRoot == true)
              message: "All containers must set runAsNonRoot: true (CEL check)."

    # Rule 2: JMESPath - require memory limits with helpful message
    - name: jmespath-memory-limits
      match:
        any:
          - resources:
              kinds:
                - Pod
      preconditions:
        all:
          - key: "{{ request.namespace }}"
            operator: NotEquals
            value: kube-system
      validate:
        message: >-
          Memory limits are required. Missing in containers:
          {{ request.object.spec.containers[?!resources.limits.memory].name | join(', ', @) }}
        deny:
          conditions:
            any:
              - key: "{{ request.object.spec.containers[?!resources.limits.memory] | length(@) }}"
                operator: GreaterThan
                value: 0

    # Rule 3: JSON Patch mutation - add standard labels
    - name: add-managed-labels
      match:
        any:
          - resources:
              kinds:
                - Pod
      mutate:
        patchesJson6902: |-
          - op: add
            path: "/metadata/labels/managed-by"
            value: "kyverno"
          - op: add
            path: "/metadata/labels/policy-version"
            value: "v1"
```

```bash
k apply -f advanced-policy.yaml
```

### Step 2: Test -- Should Be BLOCKED

```bash
# This Pod has no securityContext and no memory limits -- should fail
k run test-fail --image=nginx --restart=Never
```

Expected: Denied by `cel-nonroot` rule.

### Step 3: Test -- Should SUCCEED

```bash
# Create a compliant Pod
cat <<'EOF' | k apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: test-pass
spec:
  containers:
    - name: nginx
      image: nginx:1.27
      securityContext:
        runAsNonRoot: true
        runAsUser: 1000
      resources:
        limits:
          memory: "128Mi"
          cpu: "100m"
EOF
```

### Step 4: Verify Mutation

```bash
# Check that Kyverno added the labels
k get pod test-pass -o jsonpath='{.metadata.labels}' | jq .
```

Expected output includes `"managed-by": "kyverno"` and `"policy-version": "v1"`.

### Step 5: Verify Autogen

```bash
# Check the policy for auto-generated rules
k get clusterpolicy advanced-kca-exercise -o yaml | grep "name: autogen"
```

Expected: You see `autogen-cel-nonroot`, `autogen-jmespath-memory-limits`, and `autogen-add-managed-labels` rules generated for Deployment and StatefulSet.

### Step 6: Check Background Scan Reports

```bash
k get policyreport -A
```

### Success Criteria

- [ ] The non-compliant Pod (`test-fail`) is blocked with a clear error message
- [ ] The compliant Pod (`test-pass`) is admitted
- [ ] The admitted Pod has `managed-by: kyverno` and `policy-version: v1` labels
- [ ] Autogen rules exist for Deployment and StatefulSet only (not DaemonSet or Job)
- [ ] PolicyReports are generated for any pre-existing non-compliant resources

### Cleanup

```bash
kind delete cluster --name kyverno-lab
```

---

## Next Module

Continue to **Module 2: Policy Exceptions and Multi-Tenancy** where you will learn `PolicyException` resources, namespace-scoped enforcement, and building policy libraries for multi-tenant clusters.
