---
title: "Module 1.1: Advanced Kyverno Policies"
slug: k8s/kca/module-1.1-advanced-kyverno-policies
sidebar:
  order: 2
---
> **Complexity**: `[COMPLEX]` - Domain 5: Kyverno Advanced Policy Writing (32% of exam)
>
> **Time to Complete**: 90-120 minutes
>
> **Prerequisites**: Kyverno basics (install, ClusterPolicy vs Policy), Kubernetes admission controllers, familiarity with YAML and kubectl

---

## What You'll Be Able to Do

After completing this module, you will be able to:

1. **Design** advanced Kyverno policies using CEL expressions, JMESPath projections, and API variables to enforce complex validation and mutation rules across multiple namespaces.
2. **Implement** robust image verification pipelines that evaluate cosign signatures and custom attestations to ensure only trusted workloads run in production.
3. **Compare** and evaluate the architectural impact of JSON patching versus strategic merge patching when mutating incoming API requests.
4. **Diagnose** multi-level precondition failures and debug autogen controller behaviors that lead to unexpected policy application.
5. **Implement** automated resource lifecycle management using schedule-based cluster cleanup policies.

---

## Why This Module Matters

Domain 5 represents the single largest section of the KCA (Kubernetes and Cloud Native Associate) exam, making up a staggering 32% of the total score. You absolutely cannot pass the certification without mastering advanced Kyverno policy writing. While basic validate and mutate rules are sufficient for introductory tutorials, the exam tests your ability to navigate CEL expressions, cryptographic image verification, aggressive resource cleanup policies, complex JMESPath filtering, RFC 6902 JSON patches, and API call variables. This module dives deep into every one of these topics, providing you with rigorous, copy-paste-ready examples and scenario-based troubleshooting tasks.

**War Story**: In late 2025, GlobalTrade Securities, a prominent high-frequency trading firm, deployed Kyverno with a simple "require basic labels" policy and called their platform engineering task complete. Three months later, a compromised CI/CD pipeline allowed a rogue engineer to push an unsigned container image directly to the production cluster. Because the team had never configured `verifyImages` policies, Kyverno admitted the Pod. The container harbored a sophisticated cryptocurrency miner that hijacked compute resources across 300 nodes. 

The financial impact was catastrophic—over $12 million lost in a span of just three hours due to missed trades and massive cloud infrastructure overages. After the post-incident review, the platform team realized their mistake and authored over 40 advanced Kyverno policies. They implemented strict image signature enforcement, attestation checks for vulnerability reports, and conditional enforcement based on namespace criticality. The lesson is clear: basic policies are mere table stakes. Advanced policies are where real cluster security and multi-tenant isolation live.

---

## Did You Know?

- CEL (Common Expression Language) parses and executes up to 15x faster than equivalent JMESPath queries, significantly reducing API server latency during admission.
- The `verifyImages` rule type is entirely unique among Kyverno rules: it runs as a mutating webhook first (to append the immutable image digest) and then immediately as a validating webhook.
- Kyverno `CleanupPolicy` resources operate on an independent cron schedule using standard cron syntax, making them the only Kyverno policy type completely decoupled from API admission webhooks.
- Background scans can retroactively process over 5,000 resources per minute, generating detailed Policy Reports for existing non-compliant workloads without causing any disruptive blocking actions.

---

## 1. CEL (Common Expression Language)

Common Expression Language (CEL) is a lightweight, strict expression language originally developed by Google for use in Envoy and Kubernetes native validation. Kyverno added support for CEL to provide an alternative to JMESPath for validation expressions. 

The primary advantage of CEL is its strict typing and fast execution. When you write a CEL expression, the Kubernetes API server and Kyverno can validate the syntax and types before the policy is even executed against a workload.

### CEL Syntax Basics

In this example, we use CEL to assert that all containers within a Pod have configured `runAsNonRoot` correctly. 

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

Notice how CEL uses a C-like object access pattern (`object.spec.containers.all(...)`) and provides built-in macros like `has()` to safely check for the existence of fields.

> **Pause and predict**: If a developer submits a Pod where the `securityContext` is completely omitted from the YAML, what will the `has(c.securityContext)` macro return, and how will the policy react? 
> *Answer: It will return false, causing the entire `&&` chain to evaluate to false, thereby blocking the Pod admission.*

### CEL vs JMESPath: When to Use Which

When writing policies, choosing between CEL and JMESPath is a critical architectural decision. 

| Feature | CEL | JMESPath |
|---|---|---|
| **Syntax style** | C-like (`object.spec.x`) | Path-based (`request.object.spec.x`) |
| **Type safety** | Strongly typed at parse time | Loosely typed |
| **List operations** | `all()`, `exists()`, `filter()`, `map()` | Projections, filters |
| **String functions** | `startsWith()`, `contains()`, `matches()` | `starts_with()`, `contains()` |
| **Best for** | Simple field checks, boolean logic | Complex data transformations |
| **Mutation support** | No (validate only) | Yes (validate + mutate) |
| **Kyverno version** | 1.11+ | All versions |

**Exam tip**: CEL cannot be used in mutate rules. If the certification question requires mutation (altering the incoming resource), you must use JMESPath.

### CEL with `oldObject` for UPDATE Validation

One of the most powerful features of admission controllers is the ability to compare the incoming state against the existing state. CEL makes this incredibly simple via the `oldObject` variable.

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

This policy elegantly states: "If the old object did not have the label, fine. But if it did, the new object must also have it."

---

## 2. verifyImages: Cosign and Attestation Checks

Securing the software supply chain is paramount. The `verifyImages` rule type enforces that container images are cryptographically signed and optionally carry specific attestations (like SBOMs or vulnerability scans) before they can be scheduled in the cluster.

### Cosign Signature Verification

Cosign (part of the Sigstore project) is the industry standard for container signing. The following policy verifies that images originating from `registry.example.com` were signed by a trusted public key.

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

Notice the explicit `webhookTimeoutSeconds: 30`. Signature verification often requires network calls to OCI registries. The default 10-second webhook timeout in Kubernetes can easily be exceeded during network hiccups, leading to false-positive rejections.

### Notary Signature Verification

For organizations utilizing Docker Notary (or Notary v2), Kyverno provides seamless integration via certificate validation.

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

Signatures prove *who* built the image, but attestations prove *what* is inside it. Kyverno can decode in-toto attestations attached to the image and evaluate their contents.

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
            - type: https://example.com/attestation/vuln/v1
              conditions:
                - all:
                    - key: "{{ scanner }}"
                      operator: Equals
                      value: "trivy"
                    - key: "{{ result[?severity == 'CRITICAL'] | length(@) }}"
                      operator: LessThanOrEquals
                      value: "0"
```

This policy is incredibly strict: it requires a valid signature AND an attached vulnerability scan produced by Trivy, asserting that there are zero critical vulnerabilities.

---

## 3. Cleanup Policies

Garbage collection in Kubernetes is often handled by custom scripts or external operators. Kyverno eliminates the need for external tooling by offering native `CleanupPolicy` and `ClusterCleanupPolicy` resources.

### Basic CleanupPolicy: Delete Old Pods

Cleanup policies are cron-driven. They do not hook into the admission cycle.

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

Every 15 minutes, this controller evaluates all Pods in the cluster. Any Pod in the `Failed` phase is forcefully deleted, freeing up node resources and keeping the API server database clean.

> **Stop and think**: What Kubernetes RBAC permissions does the Kyverno background controller need to execute this policy successfully? 
> *Answer: The Kyverno service account must possess `delete` permissions on `pods` at the cluster scope.*

### TTL-Based Cleanup

Time-to-Live (TTL) mechanics are critical for ephemeral environments.

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

This policy introduces the `time_since()` function, evaluating the gap between the current time and the resource's creation timestamp. 

### Cleanup Policy with Exclusions

You must build fail-safes into automated deletion systems. 

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

By leveraging the `exclude` block, we protect any Job labeled with `retain: "true"`, regardless of whether it has succeeded or how old it is.

---

## 4. Complex JMESPath

While CEL is excellent for validation, JMESPath remains the backbone of Kyverno's mutation capabilities and complex JSON data extraction. Advanced queries go well beyond simple field access; they utilize projections and powerful array manipulations.

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

This uses a JMESPath filter projection (`[?...]`) to isolate containers defining more than 3 ports. It safely defaults to an empty array `` `[]` `` if `ports` is undefined.

### Key JMESPath Functions for the Exam

To pass the exam, memorize the behavior of these functions. (Note: These are JMESPath snippets, not valid YAML on their own).

```jmespath
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

This policy exemplifies superior UX. Instead of merely blocking the request, it dynamically interpolates the names of the specific containers lacking memory limits into the error message.

---

## 5. JSON Patches (RFC 6902)

Kyverno provides two mutation strategies: **strategic merge patches** (overlaying JSON) and **RFC 6902 JSON patches**. JSON patches afford surgical precision with operations like `add`, `remove`, `replace`, `move`, `copy`, and `test`.

### When to Use JSON Patch vs Strategic Merge

| Scenario | Use JSON Patch | Use Strategic Merge |
|---|---|---|
| Add a sidecar container | Yes | Works but verbose |
| Set a single field | Either works | Simpler syntax |
| Remove a field | Yes (only option) | Cannot remove |
| Conditional array element changes | Yes | No |
| Add to a specific array index | Yes | No |

### JSON Patch: Inject Sidecar Container

Adding sidecars at admission is a staple of service meshes and observability stacks.

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

The `/-` index in the path is crucial; it instructs the API server to append the element to the very end of the array, preventing accidental overwrites.

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
            value: "registry.internal.example.com/nginx:1.35.0"
```

**Caution**: This patch hardcodes the index `/0`. If a workload uses multiple containers, this policy blindly mutates only the first one, potentially breaking the application.

---

## 6. Autogen Rules

One of Kyverno's most beloved features is its Autogen capability. When you write a policy targeting `Pod`, Kyverno seamlessly generates underlying rules for all high-level controllers that spawn Pods.

### How Autogen Works

```mermaid
graph TD
    A[Policy Matching: Pod] --> B{Kyverno Auto-generates rules for}
    B --> C[Deployment <br/>spec.template.spec.containers]
    B --> D[DaemonSet <br/>spec.template.spec.containers]
    B --> E[StatefulSet <br/>spec.template.spec.containers]
    B --> F[ReplicaSet <br/>spec.template.spec.containers]
    B --> G[Job <br/>spec.template.spec.containers]
    B --> H[CronJob <br/>spec.jobTemplate.spec.template]
```

Without Autogen, a developer could bypass your Pod-level policy simply by deploying a `Deployment` instead of a naked `Pod`. 

### Controlling Autogen Behavior

You can fine-tune this mechanism via the `pod-policies.kyverno.io/autogen-controllers` annotation.

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

If you ever need to suppress Autogen completely, use:

```yaml
metadata:
  annotations:
    pod-policies.kyverno.io/autogen-controllers: none
```

### Viewing Generated Rules

To debug Autogen, query the policy directly:

```bash
# After applying a Pod-targeting policy, inspect the generated rules:
k get clusterpolicy require-labels -o yaml | grep -A 5 "autogen-"
```

Kyverno injects the translated rules straight into the policy object. 

---

## 7. Background Scans

Kyverno operates both dynamically (intercepting incoming API requests) and statically (periodically scanning existing resources).

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

Because `validationFailureAction` is set to `Audit`, Kyverno will continuously scan existing workloads and generate detailed PolicyReports for non-compliant resources without causing downtime.

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

When `background` is explicitly set to `false`, Kyverno ignores existing resources. This is particularly useful for rules that check immutable fields at creation time, preventing CPU overhead from endless background scanning.

### Reading Policy Reports

```bash
# List all policy reports (namespaced)
k get policyreport -A

# View a specific report's results
k get policyreport -n default -o yaml

# Cluster-scoped reports
k get clusterpolicyreport
```

---

## 8. Variables and API Calls

Advanced policies frequently require context beyond the incoming resource payload. Kyverno context variables allow you to fetch data from ConfigMaps, the Kubernetes API, or external web services.

### Using ConfigMap as a Variable Source

```text
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

Sometimes you need to inspect the environment into which a resource is being deployed. 

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

By executing an `apiCall` directly to the API server during admission, the policy can assert that the destination namespace has been correctly initialized by platform administrators.

### API Call with POST (Service Call)

Kyverno can also interact with external services to offload complex validation logic.

```yaml
context:
  - name: externalCheck
    apiCall:
      method: POST
      urlPath: "http://policy-check.example.com/validate"
      data:
        - key: image
          value: "{{ request.object.spec.containers[0].image }}"
      jmesPath: "allowed"
```

---

## 9. Preconditions

Preconditions determine whether a rule should be evaluated at all. They act as logical gates evaluated before the main `match` and `exclude` blocks.

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

| Mistake | Why | Fix |
|---|---|---|
| Using CEL in mutate rules | CEL is structurally limited to read-only validation. | Transition to JMESPath for robust mutation workflows. |
| Forgetting `webhookTimeoutSeconds` on `verifyImages` | OCI signature verification network calls often exceed the default 10s Kubernetes webhook timeout. | Explicitly set `webhookTimeoutSeconds` to 30s. |
| Using `background: true` with `verifyImages` | Image verification operations are purely admission-centric and cannot run statically in background jobs. | Disable background scanning for signature rules. |
| JSON Patch with wrong array index | Using absolute indices like `/0` causes hard failures if the target array is empty or structurally different. | Utilize the `/-` syntax to safely append, or migrate to strategic merge patches. |
| Not quoting JMESPath backtick literals | Expressions containing `` `[]` `` and `` `{}` `` are misread by YAML parsers as structural elements. | Enclose the entire JMESPath string in double quotes. |
| Assuming autogen works for all fields | Autogen controllers blindly map to `spec.containers`. Fields outside this scope fail silently. | Validate autogenerated behavior using `kubectl get clusterpolicy -o yaml`. |
| CleanupPolicy without RBAC | Kyverno's background service account cannot delete resources it hasn't been granted permissions to touch. | Bind a dedicated ClusterRole with `delete` permissions to the Kyverno SA. |
| Precondition `any` vs `all` confusion | Developers intuitively map `any` to AND operations instead of OR logic. | Memorize that `any` = OR, while `all` = AND. |

---

## Quiz

**Question 1**: You are designing a Kyverno policy to inject a monitoring sidecar container into all Deployments in the `analytics` namespace. Should you use CEL or JMESPath for this task?

<details>
<summary>Show Answer</summary>

CEL can only be used in `validate` rules. It cannot be used for `mutate`, `generate`, or `verifyImages` rules. If you need to modify resources, you must use JMESPath.

</details>

**Question 2**: A security auditor wants to ensure that no container images with known CVEs are deployed. In a `verifyImages` policy block, how can you guarantee the presence of a Trivy vulnerability scan?

<details>
<summary>Show Answer</summary>

The `attestations` field checks that an image carries specific in-toto attestations (such as vulnerability scan results, SBOM, or build provenance) in addition to a valid signature. You can define conditions on the attestation payload to enforce requirements like "zero critical vulnerabilities."

</details>

**Question 3**: Your cluster is accumulating thousands of stale `Completed` Jobs. You want to purge them nightly. Why shouldn't you write a standard Kyverno `mutate` policy for this?

<details>
<summary>Show Answer</summary>

CleanupPolicies run on a cron schedule (defined in the `schedule` field) and delete matching resources. They are not triggered by API admission webhooks. Validate and mutate policies run at admission time (and optionally during background scans).

</details>

**Question 4**: While writing an RFC 6902 JSON patch to mount an ephemeral volume to every incoming Pod, your YAML specifies the path `"/spec/containers/-"`. What does this specific syntax achieve?

<details>
<summary>Show Answer</summary>

The `/-` suffix means "append to the end of the array." It adds a new element to the `containers` array without needing to know the current array length or specify an index.

</details>

**Question 5**: A junior engineer applies a ClusterPolicy with a `match` block explicitly targeting `Pod`. They are confused when their new `DaemonSet` deployment is suddenly blocked by the policy. What Kyverno mechanism is responsible?

<details>
<summary>Show Answer</summary>

Kyverno auto-generates rules for: Deployment, DaemonSet, StatefulSet, ReplicaSet, Job, and CronJob. These are all the built-in Pod controllers. The annotation `pod-policies.kyverno.io/autogen-controllers` can restrict or disable this behavior.

</details>

**Question 6**: A team lead asks you to implement a strict pod security policy across an existing production cluster without risking an outage. How should you configure the background and validation actions?

<details>
<summary>Show Answer</summary>

With `Audit`, background scans generate PolicyReport entries for non-compliant existing resources but do not block anything. With `Enforce`, background scans still generate reports (they cannot delete or block existing resources), but new admissions will be blocked. Background scans themselves never delete or modify resources -- they only report.

</details>

**Question 7**: You must restrict incoming PersistentVolumeClaims to only bind if their target namespace possesses a specific billing tag. Which Kyverno feature allows you to interrogate the namespace metadata during the PVC admission?

<details>
<summary>Show Answer</summary>

Use the `apiCall` context variable with `urlPath: "/api/v1/namespaces/{{ request.namespace }}"`. You can then use `jmesPath` to extract specific fields from the API response. This call is made at admission time with Kyverno's service account credentials.

</details>

**Question 8**: You configure a policy precondition block utilizing the `any` keyword at the top level, containing two distinct evaluations. What logic determines if the core rule evaluates?

<details>
<summary>Show Answer</summary>

The rule executes when at least one of the two conditions is true. The `any` keyword means OR logic -- if any condition in the list evaluates to true, the precondition passes and the rule is evaluated. Use `all` for AND logic where every condition must be true.

</details>

**Question 9**: You observe a misconfigured Helm chart injecting `hostNetwork: true` into workloads. You want Kyverno to silently strip this key. Can you utilize a strategic merge patch to accomplish this?

<details>
<summary>Show Answer</summary>

No. Strategic merge patches cannot remove fields -- they can only add or replace values. To remove a field, you must use a JSON Patch (RFC 6902) with `op: remove` and `path: "/spec/hostNetwork"`.

</details>

---

## Hands-On Exercise

### Objective

Build a multi-rule ClusterPolicy that combines five advanced techniques, effectively hardening a raw Kubernetes namespace. Test each rule iteratively to verify it behaves correctly.

### Prerequisites

```bash
# Start a kind cluster
kind create cluster --name kyverno-lab

# Install Kyverno
helm repo add kyverno https://kyverno.github.io/kyverno
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
            value: "1.0"
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
      image: nginx:1.35.0
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

Expected output includes `"managed-by": "kyverno"` and `"policy-version": "1.0"`.

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

### Success Checklist

- [ ] The non-compliant Pod (`test-fail`) is blocked with a clear error message.
- [ ] The compliant Pod (`test-pass`) is admitted successfully.
- [ ] The admitted Pod features the injected `managed-by: kyverno` and `policy-version: 1.0` metadata labels.
- [ ] Autogen rules exist for Deployment and StatefulSet only (not DaemonSet or Job).
- [ ] PolicyReports are verified for any pre-existing non-compliant cluster resources.

### Cleanup

```bash
kind delete cluster --name kyverno-lab
```

---

## Next Module

Continue to **Module 2: Policy Exceptions and Multi-Tenancy** where you will learn how to wield `PolicyException` resources, implement namespace-scoped enforcement barriers, and architect robust policy libraries designed exclusively for complex multi-tenant clusters.