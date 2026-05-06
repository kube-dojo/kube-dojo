---
revision_pending: false
title: "Module 1.2: Kyverno Operations & CLI"
slug: k8s/kca/module-1.2-kyverno-operations-cli
sidebar:
  order: 3
---

# Module 1.2: Kyverno Operations & CLI

> **Complexity**: `[MEDIUM]` - Multiple tools and operational concepts
>
> **Time to Complete**: 70-80 minutes
>
> **Prerequisites**: [KCA README]() (Domain overview), [Kyverno 4.7](/platform/toolkits/security-quality/security-tools/module-4.7-kyverno/) (architecture basics)
>
> **KCA Domains Covered**: Domain 2 (Installation & Configuration, 18%) + Domain 3 (CLI, 12%) + Domain 6 (Policy Management, 10%) = **40% of the exam**

---

## Learning Outcomes

After completing this module, you will be able to:

1. **Design** a production-ready Kyverno installation with multiple replicas, pod anti-affinity, resource requests, failure policies, and exception controls for Kubernetes 1.35+ clusters.
2. **Validate** Kyverno policies before deployment by using `kyverno apply`, `kyverno test`, and `kyverno jp` in a repeatable local or CI workflow.
3. **Diagnose** policy behavior from PolicyReports, ClusterPolicyReports, Prometheus metrics, and admission controller logs without guessing which component made a decision.
4. **Evaluate** when to use audit mode, enforcement mode, resource filters, PolicyExceptions, or policy changes during day-two operations.
5. **Operate** Kyverno upgrades safely by checking compatibility, backing up policy resources, applying CRDs deliberately, and verifying webhook health after the release changes.

## Why This Module Matters

Hypothetical scenario: your platform team has a solid set of Kyverno policies, but the first production rollout happens with one Kyverno replica, no anti-affinity, no policy test suite, and a strict admission failure policy. A worker node is drained for routine maintenance, the single Kyverno pod disappears for a short window, and the Kubernetes API server starts calling a webhook endpoint that has no ready backend. The policies themselves may be correct, yet the operational design has turned policy enforcement into a cluster availability risk.

That scenario is intentionally hypothetical, but the failure mode is real enough to plan around. Admission controllers sit directly in the request path for creates, updates, and other API operations, so their health has a wider blast radius than an ordinary background tool. Kyverno also runs background scans, writes PolicyReports, exposes metrics, manages generate and cleanup controllers, and evaluates policy exceptions. Operating it well means treating it as both a security control and a production service with availability, latency, upgrade, and observability requirements.

This module teaches the operational layer that appears across KCA Domains 2, 3, and 6. You will work with the CLI commands that shift policy validation left, the reporting objects that explain what happened inside the cluster, the exception model that keeps bypasses narrow, and the Helm settings that make Kyverno resilient at scale. By the end, a failed policy test, a noisy PolicyReport, a webhook timeout, or a CRD upgrade will look like a diagnosable system rather than a pile of unrelated symptoms.

## Operating Model: Where Kyverno Decisions Happen

Kyverno is easiest to operate when you separate the policy lifecycle into three places: before the cluster, inside admission, and after admission. Before the cluster, the Kyverno CLI can evaluate policies against YAML files without contacting the API server. Inside admission, Kyverno receives admission review requests from Kubernetes webhooks and decides whether a request should pass, fail, warn, mutate, generate, or be skipped. After admission, background controllers and reporting controllers keep evaluating existing resources so that audit data does not depend only on future API traffic.

That separation matters because each place answers a different operational question. The CLI answers "would this policy behave the way I expect against these manifests?" Admission answers "should this live API request be allowed right now?" PolicyReports and metrics answer "what is the continuing effect of these policies across the cluster?" If you blur those questions together, you will reach for the wrong tool when something fails, such as debugging an offline test with admission logs or blaming a webhook for a background scan result.

The KCA exam often tests this distinction indirectly. A question may describe a manifest that fails in CI, a resource that appears in a PolicyReport, or an API request that is blocked during deployment. The correct response depends on recognizing which part of the operating model is involved. A local test failure points toward `kyverno apply` or `kyverno test` input files, a report entry points toward policy evaluation results stored in the PolicyReport API, and an admission outage points toward webhooks, service endpoints, readiness, replicas, and failure policy.

The following flow is the mental model to keep in mind while reading the rest of the module. It is not a full architecture diagram; it is a troubleshooting map that shows where evidence is produced and where a platform engineer should look first.

```text
+------------------+      +------------------+      +--------------------+
| Git or CI system | ---> | Kyverno CLI       | ---> | Policy test result |
| manifests        |      | apply/test/jp     |      | before deployment  |
+------------------+      +------------------+      +--------------------+
         |
         v
+------------------+      +------------------+      +--------------------+
| Kubernetes API   | ---> | Kyverno webhooks  | ---> | allow, deny, warn, |
| admission request|      | admission path    |      | mutate, generate   |
+------------------+      +------------------+      +--------------------+
         |
         v
+------------------+      +------------------+      +--------------------+
| Existing cluster | ---> | Background scans  | ---> | PolicyReports and |
| resources        |      | reporting control |      | Prometheus metrics |
+------------------+      +------------------+      +--------------------+
```

Pause and predict: if a policy passes `kyverno apply` against a local manifest but the same workload is denied during admission, which inputs changed between the two evaluations? Usually the answer is admission context, namespace data, generated variables, live cluster state, or webhook configuration rather than the policy text alone. That prediction habit will keep your debugging focused, because Kyverno CLI tests are powerful but they only see the files and variables you provide.

## Kyverno CLI: Shift Policy Testing Left

The Kyverno CLI is a standalone binary that does not require a running cluster or a Kyverno installation. That design makes it useful in the same way a compiler or unit test runner is useful: it gives developers and platform teams fast feedback before a change reaches a shared environment. You can test a policy against a single resource, a directory of resources, a structured test suite with expected outcomes, or a JMESPath expression that is difficult to reason about by sight.

Install the CLI in the way that fits your workstation or CI runner. Homebrew is convenient on macOS and many Linux environments, binary downloads are predictable in locked-down CI images, Docker is useful when the runner cannot install packages, and Krew provides a `kubectl kyverno` plugin path for teams that already standardize on kubectl plugins. The important operational rule is not the installation method; it is pinning a known version in automation so policy results do not change because a runner silently picked up a different CLI release.

```bash
brew install kyverno
```

```bash
# Download a pinned release. Check https://github.com/kyverno/kyverno/releases for the current version you standardize on.
curl -LO https://github.com/kyverno/kyverno/releases/download/v1.12.0/kyverno-cli_v1.12.0_linux_amd64.tar.gz
tar -xzf kyverno-cli_v1.12.0_linux_amd64.tar.gz
sudo mv kyverno /usr/local/bin/

# Verify the installed binary before using it in automation.
kyverno version
```

```bash
docker run --rm -v "$(pwd):/workspace" ghcr.io/kyverno/kyverno-cli:latest \
  apply /workspace/policy.yaml --resource /workspace/deploy.yaml
```

```bash
kubectl krew install kyverno
kubectl kyverno version
```

`kyverno apply` is the most direct offline testing command. It reads one or more policies, reads one or more resources, evaluates the matching rules, and prints pass, fail, warn, error, or skip results. When a team says it wants to "shift left" Kyverno, this is usually the first command it needs in pull requests, because it catches obvious policy violations before they become admission failures in a shared cluster.

```bash
# Test a single policy against a single resource.
kyverno apply policy.yaml --resource deployment.yaml

# Test a directory of policies against a directory of resources.
kyverno apply policies/ --resource manifests/

# Show detailed results with per-rule context.
kyverno apply policy.yaml --resource deployment.yaml --detailed-results

# Test against resources in a running cluster when kubeconfig is available.
kyverno apply policy.yaml --cluster

# Provide admission-style variables when the policy references request context.
kyverno apply policy.yaml --resource pod.yaml \
  --set request.object.metadata.namespace=production
```

Exit codes are part of the contract, so treat them as carefully as the printed output. A zero exit means all evaluated resources passed according to the command inputs. A one exit means at least one evaluated result violated the policy expectation. A two exit usually means the test itself could not run, such as invalid YAML, a missing file, or an unreadable path, and that should be handled as a pipeline error rather than a policy decision.

Before running this in CI, what output do you expect if one manifest is intentionally noncompliant and your policy is designed to reject it? The answer should be a nonzero job when you use `kyverno apply` as a gate, but a passing job when you use `kyverno test` and declare that the noncompliant resource is expected to fail. That difference is the reason mature teams use both commands: `apply` gates proposed workloads, while `test` verifies the policy's intended behavior.

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

`kyverno test` adds structure around the same idea by letting you name policies, resources, and expected results in a test file. This is the better tool when you are developing policies because a good policy suite should include examples that pass and examples that fail. If every test resource passes, you only know the happy path works; you do not know whether the policy catches the thing it was created to catch.

```text
tests/
|-- require-labels/
|   |-- policy.yaml
|   |-- resource-pass.yaml
|   |-- resource-fail.yaml
|   `-- kyverno-test.yaml
```

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

```bash
# Run all tests in a directory.
kyverno test tests/

# Run a specific test.
kyverno test tests/require-labels/

# Show detailed output.
kyverno test tests/ --detailed-results
```

The `result` field accepts `pass`, `fail`, `skip`, `warn`, and `error`, which means a test suite can document intended behavior rather than only successful admission. That is especially useful for audit-mode policies, exceptions, preconditions, and deny rules where the interesting behavior is often "this object should not pass." In review, a `kyverno-test.yaml` file becomes executable policy documentation because every expected result explains what the policy author believed should happen.

`kyverno jp` exists because many Kyverno policies depend on JMESPath expressions, and JMESPath bugs are hard to spot in a policy file. A precondition can silently evaluate to false, a variable can return an array when you expected a string, or a missing field can flow into a default expression. Testing the query separately reduces that ambiguity before you blame the match block, webhook configuration, or resource filters.

```bash
# Query a JSON file.
kyverno jp query "metadata.labels.app" -i resource.json

# Parse an admission-style expression.
kyverno jp parse "request.object.metadata.namespace"

# Test a query against JSON supplied on standard input.
echo '{"spec":{"containers":[{"name":"nginx","image":"nginx:1.25"},{"name":"sidecar","image":"envoy:1.28"}]}}' | \
  kyverno jp query "spec.containers[].image"
```

| Expression | What It Returns |
|-----------|-----------------|
| `request.object.metadata.labels.app` | Value of the `app` label |
| `request.object.spec.containers[].image` | All container images as an array |
| `request.object.metadata.namespace || 'default'` | Namespace or `'default'` if empty |
| `length(request.object.spec.containers)` | Number of containers |

Use the CLI as the first diagnostic step when the evidence is local and reproducible. Use admission logs, PolicyReports, and metrics when the evidence depends on live cluster context. That boundary is simple, but it prevents a lot of wasted time because a local CLI test cannot fully represent RBAC, namespace selectors, service readiness, webhook timeouts, or every dynamic value present in an admission review.

## Policy Reports: Read the Audit Trail

PolicyReports and ClusterPolicyReports are the durable audit trail for policy results. When Kyverno evaluates resources in audit mode, background mode, or admission paths that produce reportable outcomes, it can write results into report objects that live inside the Kubernetes API. These reports are not just convenience output; they are the operational bridge between policy authors, application teams, auditors, and monitoring systems.

The scope of the report tells you what kind of resource was evaluated. Namespaced resources, such as Pods, Deployments, and Services, appear in namespace-scoped `PolicyReport` objects. Cluster-scoped resources, such as Namespaces, Nodes, ClusterRoles, and other non-namespaced objects, appear in `ClusterPolicyReport` objects. That distinction mirrors Kubernetes scoping, so your first debugging step should be choosing the correct report type rather than searching every namespace blindly.

| CRD | Scope | Created For |
|-----|-------|-------------|
| `PolicyReport` | Namespace-scoped | Namespaced resources (Pods, Deployments, Services) |
| `ClusterPolicyReport` | Cluster-scoped | Cluster resources (Nodes, Namespaces, ClusterRoles) |

```bash
# List cluster-wide reports.
kubectl get clusterpolicyreport

# List namespace reports with summary counts.
kubectl get policyreport -n production -o wide

# Get detailed results for a specific report.
kubectl get policyreport -n production polr-ns-production -o yaml
```

Each report entry has a `result` field that describes the policy evaluation outcome. Do not treat every non-pass result as the same incident. A `warn` result often means the policy is intentionally auditing before enforcement, an `error` result may indicate a policy evaluation problem, and a `skip` result can be correct when preconditions do not match or an exception applies. The result is a clue, not a final diagnosis.

| Result | Meaning |
|--------|---------|
| `pass` | Resource complies with the policy |
| `fail` | Resource violates the policy |
| `warn` | Policy is in Audit mode and resource violates it |
| `error` | Policy evaluation encountered an error |
| `skip` | Policy was skipped because preconditions were not met or an exception applied |

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

The most important workflow built on reports is audit-to-enforce migration. A cautious team introduces a policy with audit behavior, waits for background scans and normal workload changes to populate reports, fixes violations or approves tightly scoped exceptions, and only then switches the policy to enforcement. That workflow turns enforcement into a measured operational change rather than a surprise outage during a deployment window.

The simple version of the workflow is easy to memorize, but the operational nuance is in the middle steps. You deploy the policy with audit behavior, query `kubectl get policyreport -A -o wide`, inspect specific report entries, distinguish legitimate violations from resources that need exceptions, fix application manifests, and watch the fail or warn counts drop. Only when the remaining findings are understood should the team switch the policy to enforcement.

```bash
# Step 1: inspect namespace-scoped audit results across the cluster.
kubectl get policyreport -A -o wide

# Step 2: inspect one report deeply enough to see policy, rule, message, and resource.
kubectl get policyreport -n production polr-ns-production -o yaml

# Step 3: inspect cluster-scoped results separately.
kubectl get clusterpolicyreport -o yaml
```

Report data also helps you separate a policy problem from an exception problem. If a result is `skip`, look at preconditions, match and exclude selectors, and PolicyExceptions before rewriting the policy. If a result is `error`, inspect the policy expression, variables, context references, and controller logs because an error is not the same as a compliant or noncompliant workload. If the report is missing entirely, check whether reporting is enabled, whether background scans have run, and whether the resource kind is in scope for the policy.

## PolicyExceptions and Operational Bypasses

PolicyExceptions are the operational escape hatch for cases where a specific resource needs to bypass a specific policy rule. They are safer than broad policy exclusions when the exception is narrow, reviewed, and temporary, because the bypass lives in its own Kubernetes resource and can be managed with ordinary change control. They are dangerous when teams use them as a dumping ground for every uncomfortable policy violation.

The first decision is whether the bypass belongs inside the policy or outside it. If an entire class of resources should never be evaluated, such as events or a system namespace that is intentionally filtered, a policy `exclude` block or a Kyverno resource filter may be appropriate. If one named workload needs an exception from one rule because it has a documented operational reason, a `PolicyException` keeps that decision visible and scoped.

| Mechanism | Use When | Scope |
|-----------|----------|-------|
| `exclude` block in policy | Entire categories should be excluded, such as a system namespace or known resource class | Part of policy definition |
| `PolicyException` CRD | A specific operational bypass is needed, such as one CNI pod that requires privileged settings | Separate resource that can be managed by a different team |

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

Several details in that example matter more than they first appear. `policyName` must match the policy name exactly, and `ruleNames` means the exception can target specific rules rather than the entire policy. The `match` block should be as specific as possible, ideally including kind, namespace, and name pattern, because a broad exception is almost the same as disabling enforcement. The feature must also be enabled in Kyverno configuration, otherwise the resource exists but does not produce the bypass behavior you expected.

```yaml
# Helm values
features:
  policyExceptions:
    enabled: true
    namespace: "kyverno-exceptions"
```

Centralizing exceptions in a dedicated namespace is a governance choice rather than a technical requirement. Allowing exceptions in any namespace can reduce friction for application teams, but it also spreads bypass authority across the cluster. Restricting exceptions to a namespace such as `kyverno-exceptions` makes review and RBAC simpler, because only a small group needs permission to create the resources that weaken policy behavior.

Which approach would you choose here and why: one global policy exclusion for `kube-system`, or a named `PolicyException` for one privileged CNI DaemonSet? The exception is usually the better operational answer when the bypass is truly narrow, because it preserves enforcement for every other system workload and leaves an auditable object explaining the exception. The broad exclusion is easier to write, but it hides too much future risk under one convenient selector.

## Observability: Metrics, Logs, and Latency

Kyverno exposes Prometheus metrics on port `8000` at the `/metrics` endpoint by default, and those metrics tell you whether policy evaluation is healthy as a service. Reports answer "what happened to resources," while metrics answer "how often, how quickly, and with what result is Kyverno evaluating requests?" You need both views because a cluster can have no new violations and still have a slow or unhealthy admission path.

The three KCA-relevant metrics to remember are policy results, admission requests, and policy execution duration. `kyverno_policy_results_total` shows policy outcomes by policy, rule, result, and resource information. `kyverno_admission_requests_total` focuses on admission traffic and whether requests were allowed or denied. `kyverno_policy_execution_duration_seconds` is a histogram that helps you identify slow policy evaluation before it becomes a user-visible API latency problem.

| Metric | Type | What It Tells You |
|--------|------|-------------------|
| `kyverno_policy_results_total` | Counter | Total policy evaluations by policy, rule, result, and resource type |
| `kyverno_admission_requests_total` | Counter | Total admission requests received, grouped by allowed or denied outcomes |
| `kyverno_policy_execution_duration_seconds` | Histogram | How long policy evaluation takes, which matters for admission latency SLOs |
| `kyverno_controller_reconcile_total` | Counter | Background controller reconciliation activity |

```promql
# Policy violation rate over the last five minutes.
rate(kyverno_policy_results_total{result="fail"}[5m])

# Admission request latency at p99.
histogram_quantile(0.99, rate(kyverno_policy_execution_duration_seconds_bucket[5m]))

# Total blocked admission requests.
sum(kyverno_admission_requests_total{allowed="false"})

# Violations grouped by policy name.
sum by (policy_name) (kyverno_policy_results_total{result="fail"})
```

Metrics are only useful when they are collected consistently. If your cluster uses Prometheus Operator, the Helm chart can create a `ServiceMonitor` with labels that match your Prometheus selector. If your platform team manages monitoring resources separately, a manually managed `ServiceMonitor` can be clearer because ownership, labels, and scrape intervals are controlled alongside other observability configuration.

```yaml
# Enable via Helm values.
serviceMonitor:
  enabled: true
  additionalLabels:
    release: prometheus
```

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

Grafana dashboards are useful for shared visibility, but do not confuse a dashboard with an alerting strategy. A dashboard can show spikes in failed policy results, admission denials, and execution latency after someone notices a problem. Alerts should focus on service health and user impact, such as missing scrapes, rising webhook latency, a sudden increase in denied admission requests, or policy execution errors that indicate broken expressions.

```bash
# Quick import via Grafana API. Use 127.0.0.1 when testing against a local Grafana instance.
curl -X POST http://127.0.0.1:3000/api/dashboards/import \
  -H "Content-Type: application/json" \
  -d '{"dashboard":{"id":15804},"overwrite":true,"inputs":[{"name":"DS_PROMETHEUS","type":"datasource","value":"Prometheus"}]}'
```

Logs complete the diagnostic picture when metrics and reports tell you something is wrong but not why. Admission controller logs help with webhook handling, policy evaluation errors, and request-time failures. Background controller logs help when reports are stale or generate rules are not producing expected resources. The habit to build is evidence layering: use metrics for trend and latency, reports for resource-level policy results, and logs for component-level errors.

## High Availability, Helm Configuration, and Upgrades

A single Kyverno replica is a production risk because admission webhooks are on the Kubernetes API request path. High availability is not only about keeping the Kyverno Deployment green; it is about keeping admission decisions available when nodes are drained, pods are restarted, or controllers fail over. Production installations should use multiple replicas, anti-affinity or topology spread, resource requests and limits, and a failure policy that matches the organization's risk tolerance.

The common mental model is that all ready replicas can serve admission webhook requests through the Kubernetes Service, while leader election coordinates controller work that should not be performed by every replica at once. That means admission capacity benefits from multiple ready pods, but background scans and generate or cleanup work still need healthy leader election. When diagnosing an outage, check both Service endpoints for admission and Lease behavior for controller leadership.

```text
+-------------------------------------------------------------+
|                    Kyverno HA Setup                         |
|                                                             |
|   Node A              Node B              Node C            |
|   +----------+        +----------+        +----------+       |
|   | kyverno  |        | kyverno  |        | kyverno  |       |
|   | replica-0|        | replica-1|        | replica-2|       |
|   | leader   |        | standby  |        | standby  |       |
|   +----------+        +----------+        +----------+       |
|        |                   |                   |             |
|        +-------------------+-------------------+             |
|                            |                                 |
|                  Leader Election via Lease                   |
|                                                             |
|   Webhooks: all ready replicas serve admission requests      |
|   Background: one leader runs coordinated controller work     |
+-------------------------------------------------------------+
```

Helm values are where most operational intent becomes concrete. Replica count expresses availability expectations, anti-affinity reduces correlated failure during node maintenance, resources prevent Kyverno from being starved or consuming unbounded memory, resource filters keep noisy system objects out of evaluation, and failure policy decides what Kubernetes should do when the webhook cannot be reached. None of those settings is universally correct; each one trades enforcement strictness, availability, and operational noise.

```yaml
# Install: helm install kyverno kyverno/kyverno -n kyverno --create-namespace -f values.yaml

# Replicas for HA.
replicaCount: 3

# Pod anti-affinity to spread replicas across nodes.
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

# Resource limits prevent Kyverno from consuming unbounded memory.
resources:
  limits:
    memory: 512Mi
    cpu: "1"
  requests:
    memory: 256Mi
    cpu: 100m

# Webhook configuration.
webhookAnnotations:
  cert-manager.io/inject-ca-from: kyverno/kyverno-svc.kyverno.svc.tls

# Failure policy controls what happens when Kyverno is unavailable.
config:
  webhooks:
    - failurePolicy: Fail
    # failurePolicy: Ignore

# Resource filters exclude system namespaces and noisy objects from policy evaluation.
config:
  resourceFilters:
    - "[*,kyverno,*]"
    - "[Event,*,*]"
    - "[*,kube-system,*]"
    - "[*,kube-public,*]"
    - "[*,kube-node-lease,*]"

# PolicyExceptions feature.
features:
  policyExceptions:
    enabled: true
    namespace: ""
```

Failure policy deserves special attention because it expresses what Kubernetes should do when Kyverno cannot answer. `Fail` protects the cluster from unreviewed changes when the policy engine is unavailable, but it can block legitimate operations during a Kyverno outage. `Ignore` preserves API availability when the webhook is unhealthy, but it can allow changes that would otherwise be denied. Many teams choose stricter behavior for critical controls and more permissive behavior for noncritical audit policies, but the choice must be deliberate.

Kyverno upgrades require care because CRDs, controller behavior, and policy fields can change between versions. Helm does not upgrade CRDs automatically during a normal `helm upgrade`, so a chart upgrade alone may leave the API server validating policies against old schemas. The safe pattern is to read the migration guide, back up policies and exceptions, apply the target CRDs deliberately, upgrade the Helm release, and verify pods, webhooks, policies, and reports before declaring the upgrade complete.

```bash
kubectl get clusterpolicies -o yaml > clusterpolicies-backup.yaml
kubectl get policies -A -o yaml > policies-backup.yaml
kubectl get policyexceptions -A -o yaml > exceptions-backup.yaml
```

```bash
kubectl apply -f https://raw.githubusercontent.com/kyverno/kyverno/main/config/crds/kyverno/kyverno.io_clusterpolicies.yaml
kubectl apply -f https://raw.githubusercontent.com/kyverno/kyverno/main/config/crds/kyverno/kyverno.io_policies.yaml
```

```bash
helm repo update
helm upgrade kyverno kyverno/kyverno -n kyverno -f values.yaml
```

```bash
kubectl get pods -n kyverno
kubectl get clusterpolicies
kyverno version
```

Version compatibility is not only a paperwork step. A policy written for one Kyverno release may rely on fields, defaults, or API versions that behave differently later, and Kubernetes 1.35+ clusters may also expose admission and resource behavior that older policy examples did not anticipate. Always test policy suites with the target CLI and chart version in a non-production environment, then inspect reports and logs after the upgrade so schema success does not mask runtime behavior changes.

### Operational Runbook Scenarios

Runbooks are where the previous concepts become operational muscle memory. A good Kyverno runbook does not begin with "restart the pod" because Kyverno problems can originate in policy logic, admission webhooks, API schemas, reports, exceptions, Prometheus scraping, or cluster capacity. The first question should always be about the symptom boundary: did the problem happen before deployment, during admission, during a background scan, or while collecting evidence after the fact?

For a CI failure, start with the exact command that failed and the files it evaluated. If `kyverno apply` failed, reproduce the command locally with the same CLI version, policy directory, and resource directory. If `kyverno test` failed, inspect whether the actual policy result changed or whether the expected result in `kyverno-test.yaml` is wrong. That distinction matters because a test failure can mean the policy regressed, the fixture no longer represents reality, or the expected outcome was written incorrectly.

For a live admission denial, move from the user's error message toward Kyverno evidence in layers. First identify the operation, namespace, resource kind, and policy name shown in the admission response. Then check whether the policy is in enforcement mode, whether the rule has preconditions, and whether any exception should have matched. If the denial is surprising, compare the live object or admission request context with the local resource used in CLI tests because admission often contains fields that local manifests omit.

For a missing denial, resist the temptation to assume Kyverno is broken. A policy can be skipped because the resource kind did not match, the namespace selector excluded it, a precondition evaluated to false, a resource filter removed it from consideration, or a PolicyException applied. The fastest path is to inspect the policy match logic and report results before changing webhook settings. If the policy never appears in the relevant report and admission logs show no evaluation, the issue is probably scope rather than enforcement strength.

For stale or confusing PolicyReports, remember that report objects are downstream evidence. They depend on Kyverno controllers running, the resource being in policy scope, report generation being enabled, and background scans having time to observe existing resources. A report that does not update immediately after a manifest change may reflect controller timing rather than incorrect policy behavior. When the report matters for an audit-to-enforce rollout, record when the policy was deployed, when the background scan ran, and which resources were remediated.

For admission latency, treat Prometheus as the starting point and logs as the explanation layer. A high value in `kyverno_policy_execution_duration_seconds` tells you evaluation is slow, but it does not tell you whether the cause is policy complexity, context lookups, CPU pressure, API server load, or a recent change in request volume. Correlate latency spikes with policy releases, Kyverno pod resource usage, admission request counts, and controller logs. Removing a slow policy without understanding why it is slow can simply move the same mistake into the next policy.

For exception reviews, the runbook should ask who owns the exception, what policy and rule it bypasses, which resources it matches, and when it should be revisited. An exception without an owner becomes invisible debt because it weakens enforcement while looking like a normal Kubernetes object. A useful review compares the exception match block with current resources and checks whether the underlying workload has changed enough to remove or narrow the bypass.

For upgrades, the runbook should be boring by design. Read the migration notes, back up `ClusterPolicy`, namespaced `Policy`, and `PolicyException` objects, apply the target CRDs, upgrade the Helm release, and verify pods, Service endpoints, webhooks, policies, reports, and representative CLI tests. If something fails, roll back with enough evidence to know whether the issue was schema validation, controller startup, webhook routing, or policy behavior. A rollback that only restores the Deployment may not restore CRDs or policy resources to the previous state.

For capacity planning, do not wait until users report slow deployments. Kyverno evaluates admission requests on the API path, so CPU throttling, memory pressure, or too few replicas can turn into platform-wide friction. Watch request rate, execution duration, pod restarts, readiness, and queue-like symptoms after policy releases or cluster growth. A policy set that works for a small development cluster may need resource tuning, additional replicas, or rule optimization when applied to a larger shared environment.

For resource filters, document intent as carefully as you document policies. Filters are useful because some resources are noisy, irrelevant, or unsafe to evaluate, but they also remove coverage. If a team filters a namespace or kind, the runbook should explain whether the filter protects Kyverno from loops, reduces report noise, avoids system churn, or reflects a deliberate trust boundary. Without that explanation, future operators cannot tell whether the filter is required or merely a historical workaround.

For failure policy decisions, write down the expected behavior during Kyverno unavailability. If `Fail` is selected, the team is saying that blocking API operations is safer than allowing unreviewed changes while Kyverno is down. If `Ignore` is selected, the team is saying that API availability is more important for that webhook during an outage. Both choices can be defensible, but an undocumented choice becomes a surprise during incident response because different teams assume different priorities.

For exam preparation, practice translating runbook symptoms into evidence sources. "The pull request failed" points to CLI inputs and expected results. "The deployment was denied" points to admission response, policy mode, webhook health, and policy scope. "The dashboard shows slow evaluation" points to metrics, resource pressure, and policy complexity. "The report shows warnings" points to audit-to-enforce remediation. That translation skill is the difference between memorizing commands and operating Kyverno with confidence.

Another useful habit is to classify every Kyverno change by blast radius before it is applied. A CLI test fixture has almost no runtime blast radius, because it only changes repository evidence. A new audit policy has low immediate admission risk but can create reporting noise and remediation work. A new enforcement policy has direct deployment impact. A Helm value change can affect the policy engine itself. A CRD change can affect whether the API server accepts policy resources at all.

That blast-radius classification should influence review depth. A small test fixture change may need only a normal pull request review and a passing `kyverno test` run. A new enforcement policy should include representative fixtures, audit evidence from a staging cluster, an exception plan, and a rollback plan. A chart upgrade should include version notes, CRD handling, health verification, and ownership for post-upgrade observation. The operational maturity is not in making every change slow; it is in matching review rigor to the failure mode.

Think of PolicyReports as shared language between platform and application teams. Instead of telling a service owner that "the policy failed," you can point to the policy name, rule name, resource, namespace, result, and message in a Kubernetes object. That makes remediation concrete because the owner can update the manifest, request a narrow exception, or challenge the policy with evidence. Reports also help platform teams avoid vague enforcement debates because the discussion starts from observed resources rather than theoretical policy intent.

The CLI plays a complementary role in that conversation. When an application team fixes a manifest after seeing a report entry, they should be able to run the same policy against the changed resource before opening a pull request. That gives them fast feedback and reduces back-and-forth with the platform team. Over time, the best policy programs turn report findings into tests so that a class of violation is not rediscovered every time a new service uses the same manifest pattern.

Operational ownership should also be explicit. Kyverno policies are often authored by security or platform engineers, but admission failures are experienced by application teams and cluster availability is owned by whoever runs the control plane platform. If ownership is unclear, every incident becomes a handoff problem. Define who can change policies, who approves exceptions, who responds to Kyverno alerts, who performs upgrades, and who decides when audit findings are ready for enforcement.

Finally, remember that Kyverno is part of a larger Kubernetes control system. It does not replace image scanning, RBAC, network policy, runtime detection, or secure workload design, and it should not be expected to catch every possible misconfiguration alone. Its strength is declarative admission and policy evaluation close to the Kubernetes API. Operate it with that scope in mind, integrate its reports and metrics with the rest of your platform evidence, and it becomes a reliable control instead of a mysterious gatekeeper.

## Patterns & Anti-Patterns

Good Kyverno operations usually come from treating policies as software and Kyverno itself as a production dependency. The policies need tests, version control, review, release notes, and rollback thinking. The Kyverno installation needs capacity planning, health checks, alerting, and upgrade procedures. When a team only writes policies and ignores operations, it may appear successful until the first denied deployment, stale report, or webhook incident forces everyone to debug under pressure.

| Pattern | When to Use It | Why It Works | Scaling Consideration |
|---------|----------------|--------------|-----------------------|
| Policy test suites in CI | Policies are managed in Git and reviewed through pull requests | `kyverno test` documents expected pass and fail behavior before policies reach a cluster | Pin the CLI version and keep representative resources close to the policy |
| Audit-to-enforce rollout | A policy could affect existing workloads or many teams | PolicyReports reveal violations before enforcement blocks deployments | Define a time box for remediation so audit mode does not become permanent |
| HA by default | Kyverno webhooks are part of the admission path | Multiple replicas and anti-affinity reduce disruption during node or pod maintenance | Monitor ready endpoints, webhook latency, and leader election behavior |
| Narrow exceptions | A legitimate workload needs a policy bypass | `PolicyException` scopes the bypass without weakening the policy globally | Centralize exception namespace and require owners, reasons, and review dates |

Anti-patterns are often attractive because they reduce immediate friction. A broad namespace exclusion stops noisy findings quickly, a single replica saves resources, and an unpinned CLI image seems convenient in CI. The cost appears later when enforcement is inconsistent, reports are confusing, or a routine maintenance event creates an admission outage. Treat these as design smells that require a conscious exception, not as defaults.

| Anti-Pattern | What Goes Wrong | Better Alternative |
|--------------|-----------------|--------------------|
| Running one Kyverno replica in production | A pod eviction or node issue can remove the only admission backend | Use multiple replicas, anti-affinity, readiness checks, and alerting |
| Treating audit mode as a final state | Violations remain visible but never remediated, so the control does not actually protect the cluster | Track report counts, assign owners, and schedule enforcement after remediation |
| Creating broad policy exclusions | Entire namespaces or resource classes stop receiving useful policy coverage | Prefer narrow match conditions or reviewed PolicyExceptions |
| Upgrading Helm without CRDs | New policy fields can be rejected or ignored by old API schemas | Apply target CRDs deliberately before upgrading the release |

## Decision Framework

Operational Kyverno decisions usually involve a tradeoff between safety, availability, and clarity. The safest enforcement setting may be too disruptive for a new policy with many unknown violations. The most available webhook behavior may allow changes during an outage that security teams expected to block. The clearest policy may still need an exception when a system workload has a legitimate reason to violate a general rule.

Use the following decision matrix when you need to choose an operational path quickly. It is not a replacement for local policy review, but it gives you a repeatable way to classify the problem before touching manifests or Helm values.

| Situation | First Tool or Setting | Why This Choice Fits | Watch For |
|-----------|----------------------|----------------------|-----------|
| New policy in development | `kyverno test` with pass and fail fixtures | Confirms intended behavior before cluster rollout | Missing admission context variables |
| Pull request with workload manifests | `kyverno apply policies/ --resource manifests/` | Gates proposed resources before they reach admission | CLI version drift across runners |
| Existing workloads may violate policy | Audit mode plus PolicyReports | Makes impact visible before enforcement | Audit findings with no remediation owner |
| One legitimate workload needs a bypass | `PolicyException` with narrow match | Avoids weakening policy for unrelated resources | Exceptions that never expire or get reviewed |
| Admission latency increases | Prometheus histogram and admission logs | Separates slow policy evaluation from resource violations | Dashboards without alerts |
| Kyverno version upgrade | CRD backup, CRD apply, Helm upgrade, verification | Handles schema and controller changes deliberately | Assuming Helm upgraded CRDs for you |

```text
Start with the symptom
|
+-- Local manifest or PR fails? ----------> Use kyverno apply or kyverno test
|
+-- Live request denied? -----------------> Check admission logs, policy mode, and webhook health
|
+-- Existing resources show findings? ----> Read PolicyReports or ClusterPolicyReports
|
+-- One workload needs bypass? -----------> Prefer a narrow PolicyException
|
+-- Kyverno itself looks unhealthy? ------> Check replicas, endpoints, metrics, and failure policy
|
+-- Upgrade planned? ---------------------> Back up policy resources, apply CRDs, then upgrade Helm
```

The decision framework also helps with exam wording. If the prompt mentions a `PolicyReport`, start with report interpretation rather than CLI syntax. If it mentions a CI pipeline, think about `kyverno apply` or `kyverno test`. If it mentions a pod eviction or unavailable webhook, think about replicas, anti-affinity, readiness, Service endpoints, and failure policy. The exam rewards mapping the symptom to the correct operational surface.

## Did You Know?

- **Kyverno CLI works completely offline**: you can test policies against manifests on a laptop with no cluster, no network, and no Kyverno installation in the target cluster, which makes it practical for CI systems and air-gapped review workflows.
- **PolicyReports follow a shared policy-reporting model**: the PolicyReport objects Kyverno writes are based on the Kubernetes policy report API work, so they are designed as Kubernetes resources rather than a Kyverno-only log format.
- **Kyverno exposes more than thirty Prometheus metrics**: KCA-style operations questions usually focus on policy results, admission requests, and execution duration because those metrics connect directly to compliance, denials, and latency.
- **The `kyverno jp` command helps debug JMESPath expressions**: testing a query against JSON before embedding it in a policy can save time when preconditions or variables return an unexpected value.

## Common Mistakes

| Mistake | Why It Happens | How to Fix It |
|---------|----------------|---------------|
| Running `kyverno apply` against cluster resources without `--cluster` | The CLI reads local files by default, so the command is not looking at live resources unless told to do so | Add `--cluster` when kubeconfig-backed cluster evaluation is intended, or pass explicit `--resource` files |
| Forgetting `ruleNames` in a PolicyException | The exception must target specific policy rules, and a vague exception is not enough to produce the intended bypass | Specify the exact `policyName` and every intended rule name, then confirm a report result changes as expected |
| Setting `failurePolicy: Fail` with one replica | The team wants strict admission control but has not made the webhook backend highly available | Use three or more replicas with anti-affinity, then choose `Fail` or `Ignore` according to the policy's criticality |
| Upgrading the Helm release without applying CRDs | Helm does not upgrade CRDs during normal chart upgrades, so API schemas can lag behind controller behavior | Back up policies, apply target CRDs deliberately, then run `helm upgrade` and verify policy resources |
| Ignoring `kyverno_policy_execution_duration_seconds` | Teams watch violation counts but forget that slow policy evaluation adds API request latency | Alert on high percentile execution duration and investigate expensive rules, context lookups, or overload |
| Creating broad namespace exclusions for noisy findings | It is faster than fixing manifests or reviewing exceptions, but it hides unrelated future violations | Use audit mode to inventory impact, fix common causes, and create narrow PolicyExceptions only when justified |
| Testing only resources that should pass | A passing-only test suite cannot prove the policy rejects the behavior it was written to prevent | Add at least one fail fixture per important rule and make `kyverno test` assert the expected failure |

## Quiz

<details>
<summary>Question 1: Your pull request adds three Kubernetes manifests and CI should block the merge if any manifest violates the policy directory. Which Kyverno CLI approach should you use, and why?</summary>

Use `kyverno apply policies/ --resource manifests/ --detailed-results` as the pull request gate. This command evaluates the proposed resources against the policy set before they reach a cluster, and its exit code can fail the CI job when a violation is found. `kyverno test` is still valuable for policy development, but it is better when you are asserting expected pass and fail fixtures rather than simply gating application manifests. A live admission log would be the wrong first tool because the resources have not been deployed yet.

</details>

<details>
<summary>Question 2: A namespace has a PolicyReport with several `warn` results for a new resource-limits policy. What should the team do before changing the policy to enforcement?</summary>

The team should inspect the report entries, identify which workloads violate the rule, fix the manifests or create reviewed narrow exceptions, and watch the report summary drop to an acceptable state. A `warn` result usually means the policy is surfacing a violation without blocking admission, which is exactly the audit-to-enforce workflow. Switching directly to enforcement would turn known findings into deployment failures. Deleting the report would only remove evidence and would not fix the resources or the policy behavior.

</details>

<details>
<summary>Question 3: A CNI DaemonSet needs privileged settings, but the cluster has a policy that denies privileged containers. How should the exception be modeled?</summary>

Create a narrow `PolicyException` that names the specific policy and rule, matches the DaemonSet's pods by kind, namespace, and name pattern, and keep the exception under controlled RBAC. That approach preserves the policy for unrelated workloads while documenting the operational reason for the bypass. A broad exclusion for all of `kube-system` might be easier, but it would hide future violations from other system components. The feature must also be enabled in Kyverno configuration, otherwise the exception resource will not have the intended effect.

</details>

<details>
<summary>Question 4: After a Kyverno upgrade, a policy using a new field is rejected by the API server even though the controller pods are running. What is the most likely operational mistake?</summary>

The likely mistake is upgrading the Helm release without applying the newer Kyverno CRDs. Helm installs CRDs on initial install but does not manage CRD upgrades in the same way as ordinary chart resources, so the API server may still validate policies against an older schema. The fix is to follow the migration guide, back up policy resources, apply the target CRDs, and then run or repeat the Helm upgrade. Checking pod status alone is not enough because the API schema can be stale while controllers appear healthy.

</details>

<details>
<summary>Question 5: During a node drain, admission requests begin timing out because the only Kyverno pod was evicted. Which installation changes reduce this risk?</summary>

Run multiple Kyverno replicas, spread them with pod anti-affinity or topology rules, provide appropriate resource requests, and monitor ready Service endpoints. Multiple ready replicas let the Kubernetes Service route webhook traffic to another pod when one node is drained. Anti-affinity reduces the chance that all replicas land on the same node and disappear together. The team should also revisit failure policy because `Fail` and `Ignore` express different tradeoffs when the webhook cannot answer.

</details>

<details>
<summary>Question 6: A policy rule uses a JMESPath precondition and keeps skipping resources that should match. What is a practical debugging path?</summary>

Start by extracting representative JSON and testing the expression with `kyverno jp`, then compare the returned value with the precondition logic in the policy. If the query returns an array, null, or a different field than expected, the policy may skip correctly according to its current expression even though the author intended something else. After the expression is fixed locally, add a `kyverno test` case that captures the matching and nonmatching resources. Jumping straight to webhook configuration would be premature because the symptom points to rule logic.

</details>

<details>
<summary>Question 7: Prometheus shows a rising p99 for `kyverno_policy_execution_duration_seconds`, but PolicyReports do not show more failures. What does that suggest?</summary>

It suggests policy evaluation is getting slower even if resources are not newly violating policies. The team should inspect expensive rules, context lookups, admission controller logs, resource pressure, and request volume rather than focusing only on fail counts. PolicyReports answer compliance outcomes, while the duration histogram answers latency. A quiet report can coexist with a degraded admission path, so both signals are needed for operations.

</details>

## Hands-On Exercise: Kyverno CLI Pipeline

Exercise scenario: you are adding a resource-limits policy to a Git repository and want a local test suite that behaves like a CI gate. The exercise uses only local files so you can focus on the CLI workflow without depending on a running Kubernetes cluster. You will create one policy, one passing pod, one failing pod, a structured `kyverno-test.yaml`, and a checklist that proves both the policy and the test expectations work.

### Setup

Install the Kyverno CLI with the method your environment supports, then create a clean working directory for the lab. The examples below use Homebrew for convenience and keep all files under `~/kyverno-lab`, but the same file layout works in any temporary directory. If you use a pinned binary in your team CI system, use the same version locally so test behavior matches the automation.

```bash
# Install Kyverno CLI with one supported method.
brew install kyverno
# Or download a binary from https://github.com/kyverno/kyverno/releases

# Create a working directory.
mkdir -p ~/kyverno-lab/tests
cd ~/kyverno-lab
```

### Task 1: Create the Policy

The policy below requires every container in a Pod to declare both CPU and memory limits. It uses a validation pattern rather than a deny rule because the desired resource shape is simple and easy to read. In a real platform repository, you would include matching and exclusions that fit your cluster, but the lab keeps the match broad so the test behavior is obvious.

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

### Task 2: Create Passing and Failing Resources

Good tests include both compliant and noncompliant examples. The first Pod declares limits and should pass. The second Pod omits limits and should fail. Keeping the resource files small makes the policy result easy to understand, and that clarity is more valuable than a realistic application manifest when the goal is policy behavior testing.

```bash
# Resource that should pass.
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

# Resource that should fail.
cat <<'EOF' > tests/bad-pod.yaml
apiVersion: v1
kind: Pod
metadata:
  name: bad-pod
spec:
  containers:
  - name: nginx
    image: nginx:1.25
    # No resource limits.
EOF
```

### Task 3: Test with `kyverno apply`

Run `kyverno apply` against each resource before creating the structured test suite. This step gives immediate feedback and helps you verify that the policy itself behaves as expected. The passing resource should exit successfully, while the failing resource should produce a policy violation and a nonzero exit code.

```bash
# Should pass with exit code 0.
kyverno apply policy.yaml --resource tests/good-pod.yaml --detailed-results

# Should fail with exit code 1.
kyverno apply policy.yaml --resource tests/bad-pod.yaml --detailed-results
```

### Task 4: Create a Structured Test Suite

Now encode the expectations in `kyverno-test.yaml`. This is the file you would keep in version control next to the policy because it documents both the passing and failing behavior. Notice that the bad pod is expected to fail, so a failed policy result can still produce a passing test case when the result matches the expectation.

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

### Task 5: Run the Test Suite

Run the structured suite and compare the summary with the individual `apply` runs. The important point is that both test cases should be reported as successful because each actual outcome matched the declared expected result. If the bad pod is reported as a failed test rather than an expected policy failure, inspect the `policy`, `rule`, `resource`, `kind`, and `result` fields for naming mistakes.

```bash
kyverno test tests/
```

```text
Test Results:
|-- require-resource-limits/check-limits/good-pod  PASSED
`-- require-resource-limits/check-limits/bad-pod   PASSED

Test Summary: 2 tests passed, 0 tests failed
```

### Solutions

<details>
<summary>Expected `kyverno apply` interpretation</summary>

The good pod should pass because its only container has both CPU and memory limits. The bad pod should fail because the pattern requires a `resources.limits.memory` value and a `resources.limits.cpu` value for every container. If both resources pass, the policy pattern is too weak or the wrong files were evaluated. If both resources fail, check indentation, the policy name, and whether the resource YAML is valid.

</details>

<details>
<summary>Expected `kyverno test` interpretation</summary>

The test suite should pass both cases because `good-pod` is expected to pass and `bad-pod` is expected to fail. This distinction is the main reason `kyverno test` is useful for policy authors. A policy violation is not automatically a failed test; it is a failed test only when the actual result differs from the expected result declared in `kyverno-test.yaml`.

</details>

<details>
<summary>Bonus challenge guidance</summary>

Add a third Pod with two containers, where one container has limits and the other does not. Predict that the policy should fail because the pattern applies across the container list and every container should satisfy the required shape. Add the resource to `resources`, add a `results` entry with `result: fail`, and run `kyverno test tests/` again. If the result surprises you, inspect how Kyverno pattern matching applies to arrays.

</details>

### Success Criteria

- [ ] `kyverno version` runs successfully in the lab environment.
- [ ] `kyverno apply policy.yaml --resource tests/good-pod.yaml --detailed-results` exits with success.
- [ ] `kyverno apply policy.yaml --resource tests/bad-pod.yaml --detailed-results` reports a policy violation.
- [ ] `tests/kyverno-test.yaml` includes both the passing and failing resource expectations.
- [ ] `kyverno test tests/` reports both cases as passed because the actual outcomes match the expected outcomes.
- [ ] You can explain when to use `kyverno apply` as a gate and when to use `kyverno test` as a policy behavior suite.

## Sources

- [Kyverno CLI documentation](https://kyverno.io/docs/kyverno-cli/)
- [Kyverno apply command](https://kyverno.io/docs/kyverno-cli/reference/kyverno_apply/)
- [Kyverno test command](https://kyverno.io/docs/kyverno-cli/reference/kyverno_test/)
- [Kyverno jp command](https://kyverno.io/docs/kyverno-cli/reference/kyverno_jp/)
- [Kyverno installation documentation](https://kyverno.io/docs/installation/)
- [Kyverno Helm chart installation](https://kyverno.io/docs/installation/methods/#helm)
- [Kyverno high availability documentation](https://kyverno.io/docs/installation/customization/#high-availability)
- [Kyverno monitoring documentation](https://kyverno.io/docs/monitoring/)
- [Kyverno PolicyReports documentation](https://kyverno.io/docs/policy-reports/)
- [Kyverno PolicyExceptions documentation](https://kyverno.io/docs/exceptions/)
- [Kyverno upgrading documentation](https://kyverno.io/docs/installation/upgrading/)
- [Kyverno releases](https://github.com/kyverno/kyverno/releases)
- [Policy Report API prototypes](https://github.com/kubernetes-sigs/wg-policy-prototypes)
- [Kyverno Playground](https://playground.kyverno.io/)
- [Kyverno cluster policy CRD](https://raw.githubusercontent.com/kyverno/kyverno/main/config/crds/kyverno/kyverno.io_clusterpolicies.yaml)
- [Kyverno policy CRD](https://raw.githubusercontent.com/kyverno/kyverno/main/config/crds/kyverno/kyverno.io_policies.yaml)

## Next Module

Continue with **[Domain 5: Writing Policies](/k8s/kca/)** to practice validate, mutate, generate, verifyImages, and CEL policy patterns after you have the operational workflow in place.
