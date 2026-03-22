# Module 2: Kyverno Operations & CLI

> **Complexity**: `[MEDIUM]` - Multiple tools and operational concepts
>
> **Time to Complete**: 50-60 minutes
>
> **Prerequisites**: [KCA README](README.md) (Domain overview), [Kyverno 4.7](../../platform/toolkits/security-tools/module-4.7-kyverno.md) (architecture basics)
>
> **KCA Domains Covered**: Domain 2 (Installation & Configuration, 18%) + Domain 3 (CLI, 12%) + Domain 6 (Policy Management, 10%) = **40% of the exam**

---

## Why This Module Matters

Writing Kyverno policies is only half the job. The other half is **operating Kyverno in production**: installing it reliably, testing policies before they hit a cluster, monitoring what policies are doing, and upgrading without breaking your admission pipeline.

This module covers the operational side -- the CLI tools that let you shift policy testing left into CI/CD, the reporting and metrics that give you visibility, and the configuration knobs that keep Kyverno healthy at scale. Together, Domains 2, 3, and 6 account for 40% of the KCA exam. These are your "free points" if you prepare well, because unlike the policy-writing domain, the answers here are concrete and memorizable.

> **War Story**: A platform team at a fintech company deployed Kyverno with `failurePolicy: Fail` and a single replica. During a routine node drain, the Kyverno pod was evicted. For the next 90 seconds, every single Deployment, ConfigMap, and Secret creation in the cluster was rejected -- including the kube-system components trying to reschedule. The result was a cascading failure that took 15 minutes to resolve. The fix? Three replicas with pod anti-affinity and `failurePolicy: Ignore` for non-critical policies. Operations matter.

---

## Did You Know?

- **Kyverno CLI works completely offline** -- you can test policies against manifests on a laptop with no cluster, no network, and no Kyverno installation. This makes it perfect for CI/CD pipelines and air-gapped environments.
- **PolicyReports follow a CNCF standard** -- the PolicyReport CRD isn't Kyverno-specific. It's part of the [Policy Report API](https://github.com/kubernetes-sigs/wg-policy-prototypes), meaning other tools (Falco Adapter, Trivy Operator) can write to the same CRDs.
- **Kyverno exposes 30+ Prometheus metrics** out of the box, but only three are heavily tested on the KCA: `kyverno_policy_results_total`, `kyverno_admission_requests_total`, and `kyverno_policy_execution_duration_seconds`.
- **The `kyverno jp` command** was inspired by the standalone `jp` tool from JMESPath. It lets you interactively test JMESPath expressions against JSON -- invaluable when debugging preconditions that silently evaluate to `false`.

---

## Part 1: Kyverno CLI

The Kyverno CLI is a standalone binary. It does **not** require a running cluster or a Kyverno installation. Think of it as a linter and test runner for Kyverno policies.

### 1.1 Installation

**Homebrew (macOS/Linux):**

```bash
brew install kyverno
```

**Binary download:**

```bash
# Download the latest release (check https://github.com/kyverno/kyverno/releases)
curl -LO https://github.com/kyverno/kyverno/releases/download/v1.12.0/kyverno-cli_v1.12.0_linux_amd64.tar.gz
tar -xzf kyverno-cli_v1.12.0_linux_amd64.tar.gz
sudo mv kyverno /usr/local/bin/

# Verify
kyverno version
```

**Docker (no install needed):**

```bash
docker run --rm -v $(pwd):/workspace ghcr.io/kyverno/kyverno-cli:latest \
  apply /workspace/policy.yaml --resource /workspace/deploy.yaml
```

**Krew (kubectl plugin manager):**

```bash
kubectl krew install kyverno
kubectl kyverno version
```

### 1.2 kyverno apply -- Offline Policy Testing

`kyverno apply` evaluates policies against resource manifests without a cluster. This is the bread and butter of shift-left policy testing.

```bash
# Test a single policy against a single resource
kyverno apply policy.yaml --resource deployment.yaml

# Test a directory of policies against a directory of resources
kyverno apply policies/ --resource manifests/

# Show detailed results (pass/fail per rule)
kyverno apply policy.yaml --resource deployment.yaml --detailed-results

# Test against a running cluster's resources (requires kubeconfig)
kyverno apply policy.yaml --cluster

# Use variable substitution for policies that reference admission context
kyverno apply policy.yaml --resource pod.yaml \
  --set request.object.metadata.namespace=production
```

**Exit codes matter for CI/CD:**
- `0` = all resources pass all policies
- `1` = one or more resources violate a policy
- `2` = error (invalid YAML, missing file, etc.)

**CI/CD pipeline example:**

```yaml
# .github/workflows/policy-check.yaml
name: Kyverno Policy Check
on: [pull_request]
jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
    - name: Install Kyverno CLI
      run: |
        curl -LO https://github.com/kyverno/kyverno/releases/download/v1.12.0/kyverno-cli_v1.12.0_linux_amd64.tar.gz
        tar -xzf kyverno-cli_v1.12.0_linux_amd64.tar.gz
        sudo mv kyverno /usr/local/bin/
    - name: Test policies
      run: kyverno apply policies/ --resource k8s-manifests/ --detailed-results
```

### 1.3 kyverno test -- Structured Test Suites

`kyverno test` runs structured test cases defined in a YAML file. Unlike `apply`, which just checks pass/fail, `test` lets you assert **expected results** -- including expecting failures.

**Test directory structure:**

```
tests/
├── require-labels/
│   ├── policy.yaml           # The policy under test
│   ├── resource-pass.yaml    # Resource that should pass
│   ├── resource-fail.yaml    # Resource that should fail
│   └── kyverno-test.yaml     # Test definition
```

**kyverno-test.yaml format:**

```yaml
apiVersion: cli.kyverno.io/v1alpha1
kind: Test
metadata:
  name: require-labels-test
policies:
  - policy.yaml
resources:
  - resource-pass.yaml
  - resource-fail.yaml
results:
  - policy: require-app-label
    rule: check-for-app-label
    resource: good-deployment
    kind: Deployment
    result: pass
  - policy: require-app-label
    rule: check-for-app-label
    resource: bad-deployment
    kind: Deployment
    result: fail
```

**Running tests:**

```bash
# Run all tests in a directory
kyverno test tests/

# Run a specific test
kyverno test tests/require-labels/

# Show detailed output
kyverno test tests/ --detailed-results
```

The `result` field accepts: `pass`, `fail`, `skip`, `warn`, and `error`.

### 1.4 kyverno jp -- JMESPath Query Testing

Kyverno policies use JMESPath expressions extensively in preconditions, variables, and context lookups. The `kyverno jp` command lets you test expressions interactively.

```bash
# Query a JSON file
kyverno jp query "metadata.labels.app" -i resource.json

# Interactive mode -- type expressions and see results live
kyverno jp parse "request.object.metadata.namespace"

# Test complex expressions
echo '{"spec":{"containers":[{"name":"nginx","image":"nginx:1.25"},{"name":"sidecar","image":"envoy:1.28"}]}}' | \
  kyverno jp query "spec.containers[].image"
```

**Common JMESPath patterns for Kyverno:**

| Expression | What It Returns |
|-----------|-----------------|
| `request.object.metadata.labels.app` | Value of the `app` label |
| `request.object.spec.containers[].image` | All container images as an array |
| `request.object.metadata.namespace || 'default'` | Namespace or `'default'` if empty |
| `length(request.object.spec.containers)` | Number of containers |

---

## Part 2: Policy Reports

When policies run in **Audit** mode (or even in Enforce mode for passed checks), Kyverno writes results to PolicyReport and ClusterPolicyReport CRDs.

### 2.1 PolicyReport vs ClusterPolicyReport

| CRD | Scope | Created For |
|-----|-------|-------------|
| `PolicyReport` | Namespace-scoped | Namespaced resources (Pods, Deployments, Services) |
| `ClusterPolicyReport` | Cluster-scoped | Cluster resources (Nodes, Namespaces, ClusterRoles) |

```bash
# List cluster-wide reports
kubectl get clusterpolicyreport

# List namespace reports with summary counts
kubectl get policyreport -n production -o wide

# Get detailed results for a specific report
kubectl get policyreport -n production polr-ns-production -o yaml
```

### 2.2 Interpreting Report Results

Each report entry has a `result` field:

| Result | Meaning |
|--------|---------|
| `pass` | Resource complies with the policy |
| `fail` | Resource violates the policy |
| `warn` | Policy is in Audit mode and resource violates it |
| `error` | Policy evaluation encountered an error |
| `skip` | Policy was skipped (preconditions not met, or exception applied) |

**Example PolicyReport snippet:**

```yaml
apiVersion: wgpolicyk8s.io/v1alpha2
kind: PolicyReport
metadata:
  name: polr-ns-production
  namespace: production
summary:
  pass: 42
  fail: 3
  warn: 1
  error: 0
  skip: 0
results:
  - policy: require-resource-limits
    rule: check-limits
    result: fail
    message: "CPU and memory limits are required."
    resources:
      - apiVersion: v1
        kind: Pod
        name: legacy-app-7f8b9c
        namespace: production
```

### 2.3 Audit-to-Enforce Workflow

PolicyReports are critical for the audit-to-enforce migration pattern:

1. Deploy policy with `validationFailureAction: Audit`
2. Wait for background scan to populate PolicyReports
3. Query reports: `kubectl get policyreport -A -o wide`
4. Fix violations or create PolicyExceptions for legitimate cases
5. When fail count is zero (or only excepted), switch to `Enforce`

---

## Part 3: PolicyExceptions

PolicyExceptions let you exempt specific resources from specific policies without modifying the policy itself. This is the operational escape hatch for legitimate bypasses.

### 3.1 When to Use Exceptions vs Exclude

| Mechanism | Use When | Scope |
|-----------|----------|-------|
| `exclude` block in policy | Entire categories should be excluded (e.g., kube-system) | Part of policy definition |
| `PolicyException` CRD | Specific operational bypass needed (e.g., one CNI pod needs privileged) | Separate resource, can be managed by different team |

### 3.2 PolicyException Structure

```yaml
apiVersion: kyverno.io/v2
kind: PolicyException
metadata:
  name: allow-privileged-cni
  namespace: kube-system
spec:
  exceptions:
  - policyName: disallow-privileged-containers
    ruleNames:
    - require-non-privileged
  match:
    any:
    - resources:
        kinds:
        - Pod
        namespaces:
        - kube-system
        names:
        - "calico-node-*"
```

Key points:
- **`policyName`** must match the ClusterPolicy/Policy name exactly
- **`ruleNames`** is a list -- you can exempt from specific rules, not the whole policy
- **`match`** scopes the exception -- always scope tightly (namespace + name pattern)
- PolicyExceptions must be **enabled** in Kyverno config (`--enablePolicyException=true` or Helm `features.policyExceptions.enabled: true`)

### 3.3 Namespace-Scoped Exceptions

By default, PolicyExceptions can be created in any namespace. For tighter control, configure Kyverno to only allow exceptions in specific namespaces:

```yaml
# Helm values
features:
  policyExceptions:
    enabled: true
    namespace: "kyverno-exceptions"  # Only allow exceptions in this namespace
```

---

## Part 4: Prometheus Metrics

Kyverno exposes metrics on port `8000` at the `/metrics` endpoint by default. These are critical for monitoring policy health in production.

### 4.1 Key Metrics

| Metric | Type | What It Tells You |
|--------|------|-------------------|
| `kyverno_policy_results_total` | Counter | Total policy evaluations by policy, rule, result (pass/fail/error), and resource type |
| `kyverno_admission_requests_total` | Counter | Total admission requests received, by allowed/denied |
| `kyverno_policy_execution_duration_seconds` | Histogram | How long policy evaluation takes -- critical for latency SLOs |
| `kyverno_controller_reconcile_total` | Counter | Background controller reconciliation activity |

### 4.2 Useful PromQL Queries

```promql
# Policy violation rate (last 5 minutes)
rate(kyverno_policy_results_total{result="fail"}[5m])

# Admission request latency (p99)
histogram_quantile(0.99, rate(kyverno_policy_execution_duration_seconds_bucket[5m]))

# Total blocked requests
sum(kyverno_admission_requests_total{allowed="false"})

# Violations by policy name
sum by (policy_name) (kyverno_policy_results_total{result="fail"})
```

### 4.3 ServiceMonitor for Prometheus Operator

```yaml
# Enable via Helm values
serviceMonitor:
  enabled: true
  additionalLabels:
    release: prometheus   # Match your Prometheus Operator selector
```

Or create manually:

```yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: kyverno
  namespace: kyverno
spec:
  selector:
    matchLabels:
      app.kubernetes.io/name: kyverno
  endpoints:
  - port: metrics
    interval: 30s
```

### 4.4 Grafana Dashboard

Kyverno provides an official Grafana dashboard (ID: `15804`). Import it via Grafana UI or provision it:

```bash
# Quick import via Grafana API
curl -X POST http://localhost:3000/api/dashboards/import \
  -H "Content-Type: application/json" \
  -d '{"dashboard":{"id":15804},"overwrite":true,"inputs":[{"name":"DS_PROMETHEUS","type":"datasource","value":"Prometheus"}]}'
```

---

## Part 5: High Availability & Helm Configuration

### 5.1 HA Deployment

A single Kyverno replica is a single point of failure for your entire admission pipeline. Production clusters need HA.

```
┌─────────────────────────────────────────────────────────────┐
│                    Kyverno HA Setup                          │
│                                                              │
│   Node A              Node B              Node C             │
│   ┌──────────┐        ┌──────────┐        ┌──────────┐     │
│   │ kyverno  │        │ kyverno  │        │ kyverno  │     │
│   │ replica-0│        │ replica-1│        │ replica-2│     │
│   │ (leader) │        │ (standby)│        │ (standby)│     │
│   └──────────┘        └──────────┘        └──────────┘     │
│        │                   │                   │             │
│        └───────────────────┴───────────────────┘             │
│                            │                                 │
│                  Leader Election via Lease                    │
│                                                              │
│   Webhooks: All replicas serve admission requests            │
│   Background: Only leader runs background scans              │
└─────────────────────────────────────────────────────────────┘
```

Key HA concepts:
- **All replicas** handle webhook (admission) requests -- Kubernetes Service load-balances
- **Only the leader** runs background scans and generate/cleanup controllers
- **Leader election** uses Kubernetes Lease objects -- automatic failover
- **Pod anti-affinity** ensures replicas land on different nodes

### 5.2 Key Helm Values

```yaml
# Install: helm install kyverno kyverno/kyverno -n kyverno --create-namespace -f values.yaml

# Replicas for HA
replicaCount: 3

# Pod anti-affinity (spread across nodes)
podAntiAffinity:
  preferredDuringSchedulingIgnoredDuringExecution:
  - weight: 100
    podAffinityTerm:
      labelSelector:
        matchExpressions:
        - key: app.kubernetes.io/name
          operator: In
          values:
          - kyverno
      topologyKey: kubernetes.io/hostname

# Resource limits (prevent Kyverno from consuming unbounded memory)
resources:
  limits:
    memory: 512Mi
    cpu: "1"
  requests:
    memory: 256Mi
    cpu: 100m

# Webhook configuration
webhookAnnotations:
  # Useful for cert-manager integration
  cert-manager.io/inject-ca-from: kyverno/kyverno-svc.kyverno.svc.tls

# Failure policy -- what happens when Kyverno is unavailable
config:
  webhooks:
    - failurePolicy: Fail      # Block requests if Kyverno is down (strict)
    # failurePolicy: Ignore    # Allow requests if Kyverno is down (permissive)

# Resource filters -- exclude system namespaces from policy evaluation
config:
  resourceFilters:
    - "[*,kyverno,*]"
    - "[Event,*,*]"
    - "[*,kube-system,*]"
    - "[*,kube-public,*]"
    - "[*,kube-node-lease,*]"

# PolicyExceptions feature
features:
  policyExceptions:
    enabled: true
    namespace: ""  # Empty = allow in all namespaces
```

### 5.3 Upgrading Kyverno

Kyverno upgrades require care because policies are CRDs, and CRD schemas change between versions.

**Upgrade checklist:**

1. **Check version compatibility** -- read the [migration guide](https://kyverno.io/docs/installation/upgrading/) for your target version
2. **Back up CRDs and policies** before upgrading:
   ```bash
   kubectl get clusterpolicies -o yaml > clusterpolicies-backup.yaml
   kubectl get policies -A -o yaml > policies-backup.yaml
   kubectl get policyexceptions -A -o yaml > exceptions-backup.yaml
   ```
3. **Upgrade CRDs first** (Helm does not upgrade CRDs automatically):
   ```bash
   kubectl apply -f https://raw.githubusercontent.com/kyverno/kyverno/main/config/crds/kyverno/kyverno.io_clusterpolicies.yaml
   kubectl apply -f https://raw.githubusercontent.com/kyverno/kyverno/main/config/crds/kyverno/kyverno.io_policies.yaml
   # Apply all relevant CRDs for your version
   ```
4. **Upgrade Helm release:**
   ```bash
   helm repo update
   helm upgrade kyverno kyverno/kyverno -n kyverno -f values.yaml
   ```
5. **Verify** after upgrade:
   ```bash
   kubectl get pods -n kyverno
   kubectl get clusterpolicies
   kyverno version
   ```

**Version compatibility notes:**
- Kyverno follows semver -- minor versions may introduce new CRD fields
- Policies written for v1.x may need API version changes for v2.x (`kyverno.io/v1` -> `kyverno.io/v2beta1` for some features)
- Always test upgrades in a non-production cluster first
- The `kyverno.io/v1` API remains supported across versions for core policy types

---

## Common Mistakes

| Mistake | Why It Fails | Fix |
|---------|-------------|-----|
| Running `kyverno apply` against cluster resources without `--cluster` flag | CLI only reads local files by default | Add `--cluster` flag or specify `--resource` files |
| Forgetting `ruleNames` in PolicyException | Exception silently has no effect -- it must target specific rules | Always specify which rules to exempt |
| Setting `failurePolicy: Fail` with 1 replica | Kyverno pod eviction blocks all API requests | Use 3+ replicas with anti-affinity, or use `Ignore` for non-critical policies |
| Not upgrading CRDs before Helm upgrade | New policy fields silently rejected by old CRD schema | Always `kubectl apply` new CRDs before `helm upgrade` |
| Ignoring `kyverno_policy_execution_duration_seconds` | Slow policies add latency to every API request | Set alerts on p99 latency; optimize or remove slow policies |
| Creating PolicyExceptions without enabling the feature | Exceptions are ignored -- no error, no warning | Set `features.policyExceptions.enabled: true` in Helm values |
| Testing policies with `kyverno test` but wrong `result` field | Test passes when it shouldn't (expected `fail` but wrote `pass`) | Double-check expected results; test both pass and fail cases |

---

## Quiz

Test your knowledge of Kyverno operations. Try answering before revealing the solution.

### Question 1: CLI Apply
**Which command tests a policy against a local manifest file without needing a cluster?**

<details>
<summary>Show Answer</summary>

```bash
kyverno apply policy.yaml --resource deployment.yaml
```

The `kyverno apply` command works entirely offline. It reads both the policy and resource from local files.

</details>

### Question 2: Test Suites
**In a `kyverno-test.yaml` file, what are the three required top-level fields?**

<details>
<summary>Show Answer</summary>

`policies`, `resources`, and `results`.

- `policies` -- list of policy files to test
- `resources` -- list of resource files to test against
- `results` -- expected outcomes (policy, rule, resource, result)

</details>

### Question 3: PolicyExceptions
**What must be true for a PolicyException to take effect? (Two requirements)**

<details>
<summary>Show Answer</summary>

1. PolicyExceptions must be **enabled** in Kyverno configuration (`features.policyExceptions.enabled: true`)
2. The exception must specify both `policyName` and `ruleNames` matching actual policy/rule names

Without either of these, the exception is silently ignored.

</details>

### Question 4: Metrics
**Which Prometheus metric tells you the total number of policy violations?**

<details>
<summary>Show Answer</summary>

`kyverno_policy_results_total` with label `result="fail"`.

Example PromQL: `sum(kyverno_policy_results_total{result="fail"})`

Note: `kyverno_admission_requests_total` counts admission requests (allowed/denied), not policy-level results.

</details>

### Question 5: High Availability
**In a 3-replica Kyverno HA deployment, which replicas handle admission webhook requests?**

<details>
<summary>Show Answer</summary>

**All three replicas** handle admission webhook requests. The Kubernetes Service load-balances across all ready pods.

Only the **leader** runs background scans and generate/cleanup controllers. Leader election uses Kubernetes Lease objects.

</details>

### Question 6: Upgrading
**Why must you upgrade Kyverno CRDs separately from the Helm chart upgrade?**

<details>
<summary>Show Answer</summary>

Helm **does not upgrade CRDs** during `helm upgrade` by design (Helm's CRD management limitation). If new policy fields were introduced in the new version, the old CRD schema will silently reject them.

You must `kubectl apply` the new CRDs before running `helm upgrade`.

</details>

### Question 7: PolicyReports
**What is the difference between a PolicyReport and a ClusterPolicyReport?**

<details>
<summary>Show Answer</summary>

- **PolicyReport** is namespace-scoped -- it contains results for namespaced resources (Pods, Deployments, Services) within that namespace
- **ClusterPolicyReport** is cluster-scoped -- it contains results for cluster-scoped resources (Nodes, Namespaces, ClusterRoles)

Both follow the same CNCF Policy Report API specification.

</details>

---

## Hands-On Exercise: Kyverno CLI Pipeline

**Goal**: Build a local policy test suite using the Kyverno CLI, simulating what you'd run in CI/CD.

### Setup

```bash
# Install Kyverno CLI (pick your method)
brew install kyverno
# OR: download binary from https://github.com/kyverno/kyverno/releases

# Create working directory
mkdir -p ~/kyverno-lab/tests && cd ~/kyverno-lab
```

### Step 1: Create a Policy

```bash
cat <<'EOF' > policy.yaml
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata:
  name: require-resource-limits
spec:
  validationFailureAction: Enforce
  rules:
  - name: check-limits
    match:
      any:
      - resources:
          kinds:
          - Pod
    validate:
      message: "CPU and memory limits are required for all containers."
      pattern:
        spec:
          containers:
          - resources:
              limits:
                memory: "?*"
                cpu: "?*"
EOF
```

### Step 2: Create Test Resources

```bash
# Resource that should PASS
cat <<'EOF' > tests/good-pod.yaml
apiVersion: v1
kind: Pod
metadata:
  name: good-pod
spec:
  containers:
  - name: nginx
    image: nginx:1.25
    resources:
      limits:
        memory: "128Mi"
        cpu: "500m"
EOF

# Resource that should FAIL
cat <<'EOF' > tests/bad-pod.yaml
apiVersion: v1
kind: Pod
metadata:
  name: bad-pod
spec:
  containers:
  - name: nginx
    image: nginx:1.25
    # No resource limits!
EOF
```

### Step 3: Test with kyverno apply

```bash
# Should pass (exit code 0)
kyverno apply policy.yaml --resource tests/good-pod.yaml --detailed-results

# Should fail (exit code 1)
kyverno apply policy.yaml --resource tests/bad-pod.yaml --detailed-results
```

### Step 4: Create a Structured Test Suite

```bash
cat <<'EOF' > tests/kyverno-test.yaml
apiVersion: cli.kyverno.io/v1alpha1
kind: Test
metadata:
  name: resource-limits-test
policies:
  - ../policy.yaml
resources:
  - good-pod.yaml
  - bad-pod.yaml
results:
  - policy: require-resource-limits
    rule: check-limits
    resource: good-pod
    kind: Pod
    result: pass
  - policy: require-resource-limits
    rule: check-limits
    resource: bad-pod
    kind: Pod
    result: fail
EOF
```

### Step 5: Run the Test Suite

```bash
kyverno test tests/
```

### Success Criteria

You should see output like:

```
Test Results:
├── require-resource-limits/check-limits/good-pod  PASSED
└── require-resource-limits/check-limits/bad-pod   PASSED

Test Summary: 2 tests passed, 0 tests failed
```

Both tests show `PASSED` because the actual results matched the expected results -- the good pod passed the policy, and the bad pod failed it, exactly as declared in the test file.

### Bonus Challenge

Add a third test resource: a Pod with limits on one container but not another (multi-container pod). Predict the result, add it to `kyverno-test.yaml`, and verify with `kyverno test`.

---

## Key Takeaways

1. **Kyverno CLI** (`apply`, `test`, `jp`) works offline -- no cluster needed
2. **PolicyReports** are the audit trail -- always check them before switching from Audit to Enforce
3. **PolicyExceptions** are the escape hatch -- scope them tightly and enable the feature first
4. **Prometheus metrics** give you operational visibility -- `kyverno_policy_results_total` is the most important
5. **HA requires 3+ replicas** with anti-affinity -- a single replica is a production risk
6. **CRDs must be upgraded separately** from the Helm chart -- Helm does not manage CRD upgrades

---

## Next Steps

- **Domain 5 (Writing Policies, 32%)**: The largest exam domain -- practice validate, mutate, generate, verifyImages, and CEL policies
- **[Kyverno Toolkit Module](../../platform/toolkits/security-tools/module-4.7-kyverno.md)**: Deep dive into policy architecture and writing patterns
- **[Prometheus Module](../../platform/toolkits/observability/module-1.1-prometheus.md)**: Learn Prometheus fundamentals for monitoring Kyverno metrics
- **[Kyverno Playground](https://playground.kyverno.io/)**: Test policies in-browser without any installation
