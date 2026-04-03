---
title: "Module 4.2: OPA & Gatekeeper"
slug: platform/toolkits/security-quality/security-tools/module-4.2-opa-gatekeeper
sidebar:
  order: 3
---
> **Toolkit Track** | Complexity: `[COMPLEX]` | Time: 45-50 minutes

## Overview

"Trust but verify" doesn't work in Kubernetes—you need "deny by default, allow explicitly." This module covers Open Policy Agent (OPA) and Gatekeeper for policy-as-code admission control, ensuring every resource that enters your cluster meets your security and compliance requirements.

**What You'll Learn**:
- OPA and Rego policy language basics
- Gatekeeper architecture and constraints
- Writing effective admission policies
- Policy testing and CI/CD integration

**Prerequisites**:
- [Security Principles Foundations](../../../foundations/security-principles/)
- Kubernetes admission controllers concept
- Basic programming logic

---

## What You'll Be Able to Do

After completing this module, you will be able to:

- **Deploy OPA Gatekeeper and configure ConstraintTemplates for Kubernetes admission policy enforcement**
- **Implement Rego policies for pod security, resource limits, label requirements, and image restrictions**
- **Configure Gatekeeper audit mode for policy violation reporting without blocking existing workloads**
- **Evaluate OPA Gatekeeper against Kyverno for policy-as-code enforcement complexity and flexibility trade-offs**


## Why This Module Matters

Without admission control, anyone with `kubectl create` permissions can deploy anything—privileged containers, images from untrusted registries, pods without resource limits. Gatekeeper acts as your cluster's bouncer, checking every resource against your policies before allowing it in.

> 💡 **Did You Know?** Open Policy Agent was created by Styra and donated to CNCF in 2018. It's now used beyond Kubernetes—in Terraform, Envoy, Kafka, and even CI/CD pipelines. Learning OPA/Rego is an investment that pays off across the entire cloud-native stack.

---

## The Admission Control Problem

```
WITHOUT POLICY ENFORCEMENT
════════════════════════════════════════════════════════════════════

Developer kubectl apply ──▶ API Server ──▶ etcd ──▶ 😱 Running
                                │
                                │  No checks!
                                │  - Privileged container? ✓
                                │  - No resource limits? ✓
                                │  - Image from docker.io? ✓
                                │  - Root filesystem writable? ✓

═══════════════════════════════════════════════════════════════════

WITH GATEKEEPER
════════════════════════════════════════════════════════════════════

Developer kubectl apply ──▶ API Server ──▶ Gatekeeper ──▶ etcd
                                │              │
                                │              │ Check policies:
                                │              │ - No privileged? ✓
                                │              │ - Has limits? ✓
                                │              │ - Allowed registry? ✓
                                │              │ - Read-only root? ✓
                                │              │
                                │              ▼
                                │    DENY or ALLOW
                                │
                                │    If denied:
                                └──▶ "Error: container must not be privileged"
```

---

## Open Policy Agent (OPA)

### What is OPA?

OPA is a general-purpose policy engine. You give it:
1. **Data** - JSON representing current state
2. **Query** - What you want to know
3. **Policy** - Rules written in Rego

```
OPA DECISION FLOW
════════════════════════════════════════════════════════════════════

┌───────────────┐
│    Policy     │  # Written in Rego
│  (rules.rego) │
└───────┬───────┘
        │
        ▼
┌───────────────┐     ┌───────────────┐
│     OPA       │◀────│    Input      │  # JSON data to evaluate
│    Engine     │     │   (request)   │
└───────┬───────┘     └───────────────┘
        │
        ▼
┌───────────────┐
│   Decision    │  # allow: true/false
│   (output)    │  # violations: [...]
└───────────────┘
```

### Rego Language Basics

```rego
# Rego 101 - The Policy Language

# Package declaration (namespace for rules)
package kubernetes.admission

# Import statements
import future.keywords.in
import future.keywords.contains
import future.keywords.if

# Constants
allowed_registries := ["gcr.io", "registry.example.com"]

# Rules - evaluate to true/false or a set of values

# Simple boolean rule
is_privileged if {
    input.request.object.spec.containers[_].securityContext.privileged == true
}

# Rule with iteration (for each container)
violation contains msg if {
    container := input.request.object.spec.containers[_]
    not container.resources.limits.cpu
    msg := sprintf("Container '%v' has no CPU limit", [container.name])
}

# Rule with comprehension
all_container_images := [image |
    container := input.request.object.spec.containers[_]
    image := container.image
]

# Helper function
starts_with_allowed_registry(image) if {
    some registry in allowed_registries
    startswith(image, registry)
}
```

### Key Rego Concepts

| Concept | Example | Description |
|---------|---------|-------------|
| **Unification** | `x := input.name` | Assignment with pattern matching |
| **Iteration** | `containers[_]` | Iterate over array elements |
| **Comprehension** | `[x \| x := arr[_]]` | Build arrays/sets from iteration |
| **some** | `some i; arr[i]` | Explicit iteration variable |
| **contains** | `set contains msg if {...}` | Add to set when condition true |
| **default** | `default allow := false` | Default value if rule undefined |

> 💡 **Did You Know?** Rego is named after the Lego brick factory in Billund, Denmark. The creators wanted policies to "snap together" like Lego bricks. The language was designed specifically for policy—it's declarative, making it easier to audit than imperative code.

---

## Gatekeeper

### Architecture

```
GATEKEEPER ARCHITECTURE
════════════════════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────────────────┐
│                    Kubernetes Cluster                            │
│                                                                  │
│  kubectl apply ──▶ API Server                                   │
│                         │                                        │
│                         │ ValidatingAdmissionWebhook            │
│                         ▼                                        │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │                    GATEKEEPER                               │ │
│  │                                                             │ │
│  │  ┌─────────────────┐     ┌─────────────────┐              │ │
│  │  │ Constraint      │     │    OPA Engine   │              │ │
│  │  │ Templates       │────▶│                 │              │ │
│  │  │ (Rego policies) │     │  Evaluate       │              │ │
│  │  └─────────────────┘     │  Request        │              │ │
│  │                          └────────┬────────┘              │ │
│  │  ┌─────────────────┐              │                       │ │
│  │  │ Constraints     │──────────────┘                       │ │
│  │  │ (policy params) │                                      │ │
│  │  └─────────────────┘                                      │ │
│  │                                                             │ │
│  └────────────────────────────────────────────────────────────┘ │
│                         │                                        │
│                         ▼                                        │
│               Allow or Deny + Message                           │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Key Components

| Component | Purpose | Example |
|-----------|---------|---------|
| **ConstraintTemplate** | Defines reusable policy logic (Rego) | "Container must have resource limits" |
| **Constraint** | Instance of template with parameters | "Apply to namespace 'prod', require CPU/memory" |
| **Config** | Gatekeeper settings | Exempt namespaces, audit interval |

### Installation

```bash
# Install Gatekeeper
kubectl apply -f https://raw.githubusercontent.com/open-policy-agent/gatekeeper/v3.14.0/deploy/gatekeeper.yaml

# Verify installation
kubectl get pods -n gatekeeper-system

# Check webhook is registered
kubectl get validatingwebhookconfigurations
```

---

## Writing Policies

### ConstraintTemplate Structure

```yaml
apiVersion: templates.gatekeeper.sh/v1
kind: ConstraintTemplate
metadata:
  name: k8srequiredlabels  # lowercase, no spaces
spec:
  crd:
    spec:
      names:
        kind: K8sRequiredLabels  # CamelCase
      validation:
        openAPIV3Schema:
          type: object
          properties:
            labels:
              type: array
              items:
                type: string
  targets:
  - target: admission.k8s.gatekeeper.sh
    rego: |
      package k8srequiredlabels

      violation[{"msg": msg}] {
        # Get provided labels
        provided := {label | input.review.object.metadata.labels[label]}

        # Get required labels
        required := {label | label := input.parameters.labels[_]}

        # Find missing
        missing := required - provided
        count(missing) > 0

        msg := sprintf("Missing required labels: %v", [missing])
      }
```

### Constraint Usage

```yaml
apiVersion: constraints.gatekeeper.sh/v1beta1
kind: K8sRequiredLabels
metadata:
  name: require-team-label
spec:
  match:
    kinds:
    - apiGroups: [""]
      kinds: ["Pod"]
    - apiGroups: ["apps"]
      kinds: ["Deployment", "StatefulSet"]
    namespaces:
    - "production"
    excludedNamespaces:
    - "kube-system"
  parameters:
    labels:
    - "team"
    - "app"
```

### Common Policy Patterns

```yaml
# 1. Require Container Resource Limits
apiVersion: templates.gatekeeper.sh/v1
kind: ConstraintTemplate
metadata:
  name: k8scontainerlimits
spec:
  crd:
    spec:
      names:
        kind: K8sContainerLimits
  targets:
  - target: admission.k8s.gatekeeper.sh
    rego: |
      package k8scontainerlimits

      violation[{"msg": msg}] {
        container := input.review.object.spec.containers[_]
        not container.resources.limits.cpu
        msg := sprintf("Container '%v' has no CPU limit", [container.name])
      }

      violation[{"msg": msg}] {
        container := input.review.object.spec.containers[_]
        not container.resources.limits.memory
        msg := sprintf("Container '%v' has no memory limit", [container.name])
      }
---
# 2. Allowed Container Registries
apiVersion: templates.gatekeeper.sh/v1
kind: ConstraintTemplate
metadata:
  name: k8sallowedrepos
spec:
  crd:
    spec:
      names:
        kind: K8sAllowedRepos
      validation:
        openAPIV3Schema:
          type: object
          properties:
            repos:
              type: array
              items:
                type: string
  targets:
  - target: admission.k8s.gatekeeper.sh
    rego: |
      package k8sallowedrepos

      violation[{"msg": msg}] {
        container := input.review.object.spec.containers[_]
        not image_allowed(container.image)
        msg := sprintf("Container '%v' uses image '%v' from disallowed registry", [container.name, container.image])
      }

      image_allowed(image) {
        repo := input.parameters.repos[_]
        startswith(image, repo)
      }
---
# 3. Block Privileged Containers
apiVersion: templates.gatekeeper.sh/v1
kind: ConstraintTemplate
metadata:
  name: k8sblockprivileged
spec:
  crd:
    spec:
      names:
        kind: K8sBlockPrivileged
  targets:
  - target: admission.k8s.gatekeeper.sh
    rego: |
      package k8sblockprivileged

      violation[{"msg": msg}] {
        container := input.review.object.spec.containers[_]
        container.securityContext.privileged == true
        msg := sprintf("Container '%v' must not run as privileged", [container.name])
      }

      violation[{"msg": msg}] {
        container := input.review.object.spec.initContainers[_]
        container.securityContext.privileged == true
        msg := sprintf("Init container '%v' must not run as privileged", [container.name])
      }
```

> 💡 **Did You Know?** Gatekeeper includes a library of pre-built policies called the [Gatekeeper Library](https://open-policy-agent.github.io/gatekeeper-library/). There are 50+ ready-to-use ConstraintTemplates covering Pod Security Standards, general security, and Kubernetes best practices.

---

## Policy Testing

### Testing Rego Locally

```bash
# Install OPA CLI
brew install opa  # or download from https://www.openpolicyagent.org/

# Create test file
cat > policy_test.rego << 'EOF'
package k8sallowedrepos

test_allowed_registry {
    image_allowed("gcr.io/my-project/app:v1") with input.parameters.repos as ["gcr.io/"]
}

test_disallowed_registry {
    not image_allowed("docker.io/nginx:latest") with input.parameters.repos as ["gcr.io/"]
}
EOF

# Run tests
opa test . -v
```

### Gatekeeper Dry-Run Mode

```yaml
# Test constraint without enforcing
apiVersion: constraints.gatekeeper.sh/v1beta1
kind: K8sBlockPrivileged
metadata:
  name: block-privileged-dry-run
spec:
  enforcementAction: dryrun  # warn or deny for enforcement
  match:
    kinds:
    - apiGroups: [""]
      kinds: ["Pod"]
```

```bash
# Check violations in audit
kubectl get k8sblockprivileged block-privileged-dry-run -o yaml

# Look at status.violations
```

### CI/CD Integration

```yaml
# .github/workflows/policy-test.yaml
name: Test OPA Policies
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4

    - name: Setup OPA
      uses: open-policy-agent/setup-opa@v2
      with:
        version: latest

    - name: Run Rego tests
      run: opa test policies/ -v

    - name: Validate ConstraintTemplates
      run: |
        for file in policies/*.yaml; do
          opa fmt --check "$file" || exit 1
        done
```

---

## Advanced Patterns

### External Data

```yaml
# Sync data from cluster into OPA
apiVersion: config.gatekeeper.sh/v1alpha1
kind: Config
metadata:
  name: config
  namespace: gatekeeper-system
spec:
  sync:
    syncOnly:
    - group: ""
      version: "v1"
      kind: "Namespace"
    - group: "networking.k8s.io"
      version: "v1"
      kind: "Ingress"
```

```rego
# Use synced data in policy
package k8suniqueingress

violation[{"msg": msg}] {
  input.review.kind.kind == "Ingress"
  host := input.review.object.spec.rules[_].host

  # Check against all existing ingresses
  other := data.inventory.namespace[ns][otherapiversion]["Ingress"][name]
  other.spec.rules[_].host == host

  # Not the same ingress
  other.metadata.name != input.review.object.metadata.name

  msg := sprintf("Ingress host '%v' already in use by '%v/%v'", [host, ns, name])
}
```

### Mutation Policies

```yaml
# Gatekeeper also supports mutation
apiVersion: mutations.gatekeeper.sh/v1
kind: Assign
metadata:
  name: add-default-securitycontext
spec:
  applyTo:
  - groups: [""]
    kinds: ["Pod"]
    versions: ["v1"]
  match:
    scope: Namespaced
    kinds:
    - apiGroups: [""]
      kinds: ["Pod"]
  location: "spec.securityContext.runAsNonRoot"
  parameters:
    assign:
      value: true
```

> 💡 **Did You Know?** Gatekeeper's mutation feature was one of its most requested additions. Before mutation, teams had to use separate tools like Kyverno or custom webhooks to add default values. Now you can both validate AND mutate with a single tool—enforce that pods run as non-root, and automatically add the setting if developers forget.

---

## Debugging Policies

```bash
# Check constraint status
kubectl describe k8srequiredlabels require-team-label

# View audit results
kubectl get constraint -o json | jq '.items[].status'

# Check Gatekeeper logs
kubectl logs -n gatekeeper-system -l control-plane=controller-manager

# Test policy with specific input
opa eval --data policy.rego --input input.json "data.k8srequiredlabels.violation"
```

---

## Common Mistakes

| Mistake | Problem | Solution |
|---------|---------|----------|
| Policy blocks kube-system | Core components can't deploy | Exclude `kube-system` in constraints |
| No dry-run testing | Breaking changes hit production | Use `enforcementAction: dryrun` first |
| Overly strict policies | Developers can't work | Start permissive, tighten gradually |
| Complex Rego with no tests | Policy bugs in production | Write unit tests for every policy |
| Forgetting init containers | Security holes in init phase | Always check both containers and initContainers |
| Blocking all during rollout | Existing pods fail validation | Gatekeeper only checks new/updated resources |

---

## War Story: The Policy That Cried Wolf

*A platform team deployed strict container registry policies on Monday. By Wednesday, they'd received 500+ Slack messages asking for exceptions.*

**What went wrong**: They blocked everything except `gcr.io/company-project/`, but:
- Helm charts pulled from `ghcr.io`
- Logging agents used `docker.io/fluent/`
- Monitoring needed `quay.io/prometheus/`

**The fix**:
1. Audit existing images BEFORE deploying policies
2. Start with `dryrun` to identify violations
3. Build allowlist from actual usage, not assumptions
4. Communicate changes with 2-week notice

```bash
# Audit existing images
kubectl get pods -A -o jsonpath='{.items[*].spec.containers[*].image}' | tr ' ' '\n' | sort -u
```

---

## Quiz

### Question 1
What's the difference between a ConstraintTemplate and a Constraint?

<details>
<summary>Show Answer</summary>

**ConstraintTemplate**: Defines the policy LOGIC in Rego. It's like a class definition or function.

**Constraint**: Instance of a template with specific PARAMETERS. It's like calling a function with arguments.

Example:
- ConstraintTemplate: "Check if labels exist"
- Constraint: "Require labels `team` and `env` on Pods in namespace `production`"

One ConstraintTemplate can have many Constraints with different parameters.

</details>

### Question 2
How do you test a policy without blocking deployments?

<details>
<summary>Show Answer</summary>

Use `enforcementAction: dryrun` in the Constraint:

```yaml
spec:
  enforcementAction: dryrun  # Options: deny, dryrun, warn
```

- `deny`: Block violations (default)
- `dryrun`: Record violations but don't block
- `warn`: Show warning but allow

Check violations via: `kubectl get constraint <name> -o yaml`

</details>

### Question 3
Why might a policy work for Pods but miss deployments?

<details>
<summary>Show Answer</summary>

Gatekeeper evaluates the exact resource submitted. When you `kubectl apply` a Deployment, Gatekeeper sees the Deployment—not the Pods it will create.

Solutions:
1. Match on `Pod` - catches pods when created by controllers
2. Match on `Deployment` AND check `.spec.template.spec.containers`
3. Use the pod-specific path in Rego:
   ```rego
   # For Deployments
   containers := input.review.object.spec.template.spec.containers

   # For Pods
   containers := input.review.object.spec.containers
   ```

</details>

---

## Hands-On Exercise

### Objective
Create and deploy policies to enforce container security standards.

### Environment Setup

```bash
# Install Gatekeeper
kubectl apply -f https://raw.githubusercontent.com/open-policy-agent/gatekeeper/v3.14.0/deploy/gatekeeper.yaml

# Wait for it
kubectl wait --for=condition=ready pod -l control-plane=controller-manager -n gatekeeper-system --timeout=90s
```

### Tasks

1. **Create ConstraintTemplate** for allowed registries (provided above)

2. **Deploy Constraint** allowing only `gcr.io/` and `ghcr.io/`:
   ```yaml
   apiVersion: constraints.gatekeeper.sh/v1beta1
   kind: K8sAllowedRepos
   metadata:
     name: allowed-repos
   spec:
     match:
       kinds:
       - apiGroups: [""]
         kinds: ["Pod"]
     parameters:
       repos:
       - "gcr.io/"
       - "ghcr.io/"
   ```

3. **Test policy** by deploying a violating pod:
   ```bash
   kubectl run nginx --image=nginx:latest
   # Should be denied
   ```

4. **Test compliance** with allowed registry:
   ```bash
   kubectl run allowed --image=gcr.io/google-containers/pause:3.2
   # Should succeed
   ```

5. **Check audit results**:
   ```bash
   kubectl get k8sallowedrepos allowed-repos -o yaml
   ```

### Success Criteria
- [ ] Gatekeeper controller running
- [ ] ConstraintTemplate created successfully
- [ ] Constraint shows `0` totalViolations initially
- [ ] `nginx:latest` deployment blocked with clear error message
- [ ] `gcr.io/` image allowed
- [ ] Audit shows violation details for blocked attempt

### Bonus Challenge
Add a second constraint that requires all pods to have a `team` label.

---

## Further Reading

- [OPA Documentation](https://www.openpolicyagent.org/docs/)
- [Gatekeeper Documentation](https://open-policy-agent.github.io/gatekeeper/)
- [Gatekeeper Policy Library](https://open-policy-agent.github.io/gatekeeper-library/)
- [Rego Playground](https://play.openpolicyagent.org/) - Test policies online

---

## Next Module

Continue to [Module 4.3: Falco](../module-4.3-falco/) to learn runtime security monitoring for detecting threats in running containers.

---

*"Security is not a feature you add—it's a constraint you enforce. Gatekeeper makes that constraint automatic."*
