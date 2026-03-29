---
title: "Module 4.7: Kyverno"
slug: platform/toolkits/security-quality/security-tools/module-4.7-kyverno
sidebar:
  order: 8
---
> **Toolkit Track** | Complexity: `[MEDIUM]` | Time: 35-40 minutes

## Overview

Kyverno is a Kubernetes-native policy engine. Unlike OPA/Gatekeeper which uses Rego, Kyverno policies are plain YAML -- no new language to learn. It can validate, mutate, and generate resources, making it a Swiss Army knife for cluster governance.

**What You'll Learn**:
- Kyverno architecture and policy model
- Writing validate, mutate, and generate policies
- Policy reports and audit mode
- Kyverno CLI for CI/CD integration
- When to choose Kyverno vs OPA/Gatekeeper

**Prerequisites**:
- [Security Principles Foundations](../../../foundations/security-principles/)
- [Module 4.2: OPA & Gatekeeper](module-4.2-opa-gatekeeper/) (recommended, not required)
- Kubernetes admission controllers concept

---

## Why This Module Matters

In 2023, a fintech company pushed a Friday deploy with a root container, no resource limits, and an image tagged `latest` from a public registry. By Monday, cryptominers had consumed 80% of cluster CPU. Cost: $340,000 in cloud spend, a week of incident response, and a mandatory regulator audit. A single Kyverno ClusterPolicy requiring non-root containers and pinned image tags would have stopped it at the gate.

> **Did You Know?**
> - Kyverno means "govern" in Greek. It became a CNCF Incubating project in 2022 and is one of the most popular Kubernetes policy engines.
> - Kyverno policies are pure Kubernetes resources -- manage them with Argo CD or Flux without special adapters.
> - Kyverno can **generate** new resources automatically (NetworkPolicies, ResourceQuotas) -- something OPA/Gatekeeper cannot do natively.
> - The Kyverno policy library contains 200+ ready-to-use policies covering Pod Security Standards, best practices, and multi-tenancy.

---

## Kyverno Architecture

```
KYVERNO ARCHITECTURE
════════════════════════════════════════════════════════════════════

  kubectl apply ──▶ API Server
                         │
                         │ Admission Webhooks
                         ▼
  ┌────────────────────────────────────────────────────────────┐
  │                     KYVERNO                                │
  │                                                             │
  │  ┌──────────┐  ┌──────────┐  ┌──────────┐                │
  │  │ Validate │  │  Mutate  │  │ Generate  │                │
  │  │ Webhook  │  │ Webhook  │  │ Controller│                │
  │  └──────────┘  └──────────┘  └──────────┘                │
  │                                                             │
  │  ClusterPolicy / Policy (YAML) ──▶ PolicyReport (audit)   │
  └────────────────────────────────────────────────────────────┘
                         │
                         ▼
            Allow, Deny, Mutate, or Generate
```

| Action | What It Does | Example |
|--------|-------------|---------|
| **Validate** | Block or audit resources that violate rules | Deny pods without resource limits |
| **Mutate** | Modify resources before they're stored | Auto-add labels, inject sidecars |
| **Generate** | Create new resources when triggered | NetworkPolicy when a namespace is created |

---

## Installation

```bash
helm repo add kyverno https://kyverno.github.io/kyverno/
helm repo update
helm install kyverno kyverno/kyverno -n kyverno --create-namespace

# Verify
kubectl get pods -n kyverno
kubectl get validatingwebhookconfigurations | grep kyverno
kubectl get mutatingwebhookconfigurations | grep kyverno
```

---

## Policy Scope: ClusterPolicy vs Policy

| Resource | Scope | Use Case |
|----------|-------|----------|
| **ClusterPolicy** | Cluster-wide, all namespaces | Org-wide security baselines |
| **Policy** | Namespaced, single namespace only | Team-specific rules |

```yaml
# ClusterPolicy - applies everywhere
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata:
  name: require-labels

# Policy - applies only in "team-alpha" namespace
apiVersion: kyverno.io/v1
kind: Policy
metadata:
  name: require-labels
  namespace: team-alpha
```

---

## Validation Policies

### 1. Require Labels on All Resources

```yaml
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata:
  name: require-labels
spec:
  validationFailureAction: Enforce
  background: true
  rules:
  - name: check-labels
    match:
      any:
      - resources:
          kinds:
          - Pod
    validate:
      message: "Labels 'app' and 'team' are required."
      pattern:
        metadata:
          labels:
            app: "?*"
            team: "?*"
```

```bash
# DENIED -- missing labels
kubectl run nginx --image=nginx:1.27

# ALLOWED -- labels present
kubectl run nginx --image=nginx:1.27 --labels="app=web,team=platform"
```

### 2. Block the `latest` Tag

```yaml
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata:
  name: disallow-latest-tag
spec:
  validationFailureAction: Enforce
  rules:
  - name: validate-image-tag
    match:
      any:
      - resources:
          kinds:
          - Pod
    validate:
      message: "The 'latest' tag is not allowed. Pin images to a specific version."
      pattern:
        spec:
          containers:
          - image: "!*:latest"
```

### 3. Enforce Resource Limits

```yaml
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
```

### 4. Require Non-Root Containers

```yaml
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata:
  name: require-non-root
spec:
  validationFailureAction: Enforce
  rules:
  - name: check-non-root
    match:
      any:
      - resources:
          kinds:
          - Pod
    exclude:
      any:
      - resources:
          namespaces:
          - kube-system
    validate:
      message: "Containers must set securityContext.runAsNonRoot to true."
      pattern:
        spec:
          containers:
          - securityContext:
              runAsNonRoot: true
```

---

## Generate Policies

### Auto-Generate NetworkPolicy for New Namespaces

Every time a namespace is created, Kyverno generates a default-deny NetworkPolicy inside it. This is a killer feature that Gatekeeper lacks.

```yaml
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata:
  name: generate-default-deny-netpol
spec:
  rules:
  - name: default-deny
    match:
      any:
      - resources:
          kinds:
          - Namespace
    exclude:
      any:
      - resources:
          names:
          - kube-system
          - kube-public
          - kyverno
    generate:
      synchronize: true
      apiVersion: networking.k8s.io/v1
      kind: NetworkPolicy
      name: default-deny-all
      namespace: "{{request.object.metadata.name}}"
      data:
        spec:
          podSelector: {}
          policyTypes:
          - Ingress
          - Egress
```

With `synchronize: true`, if someone deletes the NetworkPolicy, Kyverno recreates it.

---

## Mutating Policies

### Auto-Add Labels

```yaml
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata:
  name: add-default-labels
spec:
  rules:
  - name: add-labels
    match:
      any:
      - resources:
          kinds:
          - Pod
    mutate:
      patchStrategicMerge:
        metadata:
          labels:
            +(managed-by): kyverno
            +(cost-center): "default"
```

The `+()` notation means "add only if not already present" -- it won't overwrite labels developers set explicitly.

### Inject Sidecar Container

Match on an annotation to opt in specific pods:

```yaml
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata:
  name: inject-logging-sidecar
spec:
  rules:
  - name: inject-sidecar
    match:
      any:
      - resources:
          kinds:
          - Pod
          annotations:
            inject-logger: "true"
    mutate:
      patchStrategicMerge:
        spec:
          containers:
          - name: logger
            image: fluent/fluent-bit:3.0
            resources:
              limits:
                memory: "64Mi"
                cpu: "50m"
```

---

## Policy Reports and Audit Mode

Set `validationFailureAction: Audit` to log violations without blocking. This is how you safely roll out new policies.

```bash
# View policy reports
kubectl get clusterpolicyreport
kubectl get policyreport -A

# Detailed results
kubectl get policyreport -n default -o yaml
```

Kyverno generates PolicyReport resources following the Kubernetes Policy WG standard -- they work with dashboards like Policy Reporter UI.

---

## Kyverno CLI for CI/CD

Test policies against manifests *before* deploying. Shift-left your policy enforcement.

```bash
# Install
brew install kyverno

# Test locally
kyverno apply policy.yaml --resource deployment.yaml
kyverno apply policies/ --resource manifests/ --detailed-results
```

```yaml
# .github/workflows/kyverno-check.yaml
name: Kyverno Policy Check
on: [push, pull_request]
jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
    - name: Install Kyverno CLI
      run: |
        curl -LO https://github.com/kyverno/kyverno/releases/latest/download/kyverno-cli_linux_amd64.tar.gz
        tar -xzf kyverno-cli_linux_amd64.tar.gz
        sudo mv kyverno /usr/local/bin/
    - name: Validate manifests
      run: kyverno apply policies/ --resource k8s-manifests/ --detailed-results
```

---

## Kyverno vs OPA/Gatekeeper

| Feature | Kyverno | OPA/Gatekeeper |
|---------|---------|----------------|
| **Policy language** | YAML (Kubernetes-native) | Rego (custom DSL) |
| **Learning curve** | Low -- know YAML, you're ready | Steep -- Rego takes weeks |
| **Mutation** | First-class support | Added later, less mature |
| **Generation** | Yes -- auto-create resources | No |
| **Policy reports** | Built-in (K8s Policy WG standard) | Via constraint status |
| **CLI for CI/CD** | `kyverno apply` | `opa test` + `gator verify` |
| **Policy library** | 200+ policies | 50+ ConstraintTemplates |
| **Complex logic** | Limited (YAML + JMESPath) | Powerful (Rego handles anything) |
| **Non-K8s use** | Kubernetes only | Terraform, Envoy, Kafka, etc. |
| **CNCF status** | Incubating | Graduated (OPA) |

**Bottom line**: Kyverno wins on simplicity and breadth of actions (validate + mutate + generate). Gatekeeper wins on expressiveness and reach beyond Kubernetes. Many organizations use both.

> See [Module 4.2: OPA & Gatekeeper](module-4.2-opa-gatekeeper/) for Rego-based policies. For CKS exam prep, understand both -- the exam covers admission controllers broadly.

---

## Common Mistakes

| Mistake | Problem | Solution |
|---------|---------|----------|
| Enforcing before auditing | Breaks existing workloads on day one | Start with `Audit`, review reports, then `Enforce` |
| No `exclude` for system namespaces | Kyverno blocks kube-system | Always exclude `kube-system`, `kube-public`, `kyverno` |
| Confusing generate with validate | Expecting generate to block resources | Generate creates resources; it doesn't deny anything |
| Not setting `background: true` | Existing violations are invisible | Enable background scanning for running resources |
| Overly broad `match` | Policies hit every resource type | Be specific with `kinds` and `namespaces` |
| Ignoring init containers | Security holes in init phase | Add rules for `initContainers` or use `=(initContainers)` |

---

## Quiz

### Question 1
What are the three main policy actions Kyverno supports?

<details>
<summary>Show Answer</summary>

**Validate**, **Mutate**, and **Generate**. Kyverno also supports **verifyImages** for container image signature verification.

</details>

### Question 2
What is the difference between ClusterPolicy and Policy?

<details>
<summary>Show Answer</summary>

**ClusterPolicy** is cluster-scoped and applies to all namespaces. **Policy** is namespace-scoped and only affects resources in the namespace where it lives. Use ClusterPolicy for org-wide baselines, Policy for team-specific rules.

</details>

### Question 3
How do you safely roll out a new policy in production?

<details>
<summary>Show Answer</summary>

1. Deploy with `validationFailureAction: Audit` (not Enforce).
2. Set `background: true` to scan existing resources.
3. Review PolicyReport resources for violations.
4. Work with teams to fix violations.
5. Switch to `Enforce` once violations are resolved.

</details>

### Question 4
What does `synchronize: true` do on a generate rule?

<details>
<summary>Show Answer</summary>

It makes Kyverno continuously reconcile the generated resource. If someone deletes or modifies it, Kyverno recreates or restores it. Without synchronize, the resource is generated once and never managed again. Use it for security-critical generated resources like default-deny NetworkPolicies.

</details>

---

## Hands-On Exercise

### Objective
Install Kyverno, deploy validation and generation policies, and verify enforcement.

### Setup

```bash
kind create cluster --name kyverno-lab
helm repo add kyverno https://kyverno.github.io/kyverno/
helm repo update
helm install kyverno kyverno/kyverno -n kyverno --create-namespace
kubectl wait --for=condition=ready pod -l app.kubernetes.io/instance=kyverno -n kyverno --timeout=120s
```

### Tasks

1. **Deploy the "require labels" policy** with `validationFailureAction: Enforce`.

2. **Verify unlabeled pods are blocked**:
   ```bash
   kubectl run test-nginx --image=nginx:1.27
   # Expected: DENIED
   ```

3. **Verify labeled pods succeed**:
   ```bash
   kubectl run test-nginx --image=nginx:1.27 --labels="app=web,team=platform"
   # Expected: pod/test-nginx created
   ```

4. **Deploy "block latest tag" policy** and test:
   ```bash
   kubectl run bad --image=nginx:latest --labels="app=web,team=platform"
   # Expected: DENIED
   ```

5. **Deploy "generate NetworkPolicy" policy**, then:
   ```bash
   kubectl create namespace test-generate
   kubectl get networkpolicy -n test-generate
   # Expected: default-deny-all exists
   ```

6. **Check policy reports**: `kubectl get policyreport -A`

### Success Criteria
- [ ] Kyverno pods running in `kyverno` namespace
- [ ] Unlabeled pod blocked with clear error
- [ ] Labeled pod created successfully
- [ ] Pod with `latest` tag blocked
- [ ] New namespace auto-gets default-deny NetworkPolicy
- [ ] Policy reports show pass/fail results

### Bonus
Write a mutating policy that adds `environment: dev` to all pods in the `development` namespace only if not already set.

---

## Further Reading

- [Kyverno Documentation](https://kyverno.io/docs/)
- [Kyverno Policy Library](https://kyverno.io/policies/)
- [Kyverno Playground](https://playground.kyverno.io/)
- [Module 4.2: OPA & Gatekeeper](module-4.2-opa-gatekeeper/) - Compare approaches

---

## Next Module

Continue to the [Security Tools README]() to review all security toolkit modules and plan your learning path.

---

*"The best policy engine is the one your team actually uses. If your developers can read the policies, they'll follow them."*
