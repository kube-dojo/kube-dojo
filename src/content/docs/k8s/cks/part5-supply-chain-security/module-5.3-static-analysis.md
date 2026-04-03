---
title: "Module 5.3: Static Analysis with kubesec and OPA"
slug: k8s/cks/part5-supply-chain-security/module-5.3-static-analysis
sidebar:
  order: 3
lab:
  id: cks-5.3-static-analysis
  url: https://killercoda.com/kubedojo/scenario/cks-5.3-static-analysis
  duration: "35 min"
  difficulty: advanced
  environment: kubernetes
---
> **Complexity**: `[MEDIUM]` - Security tooling
>
> **Time to Complete**: 45-50 minutes
>
> **Prerequisites**: Module 5.2 (Image Scanning), Kubernetes manifest basics

---

## What You'll Be Able to Do

After completing this module, you will be able to:

1. **Audit** Kubernetes manifests using kubesec to identify security misconfigurations
2. **Write** OPA Rego policies to enforce custom security rules at admission time
3. **Deploy** OPA Gatekeeper ConstraintTemplates and Constraints for policy enforcement
4. **Evaluate** static analysis tool output to prioritize security fixes before deployment

---

## Why This Module Matters

Static analysis examines Kubernetes manifests before deployment, catching misconfigurations early. Tools like kubesec score security posture, while OPA Gatekeeper enforces policies at admission time.

CKS tests both ad-hoc analysis (kubesec) and policy enforcement (OPA).

---

## Static Analysis Overview

```
┌─────────────────────────────────────────────────────────────┐
│              STATIC ANALYSIS PIPELINE                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Developer writes YAML                                     │
│         │                                                   │
│         ▼                                                   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Static Analysis (Pre-commit/CI)                    │   │
│  │  ├── kubesec (security scoring)                    │   │
│  │  ├── Trivy (misconfiguration)                      │   │
│  │  ├── kube-linter (best practices)                  │   │
│  │  └── Checkov (policy as code)                      │   │
│  └─────────────────────────────────────────────────────┘   │
│         │                                                   │
│         ▼                                                   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Admission Controllers (Deploy time)                │   │
│  │  ├── OPA Gatekeeper                                 │   │
│  │  ├── Kyverno                                        │   │
│  │  └── Pod Security Admission                         │   │
│  └─────────────────────────────────────────────────────┘   │
│         │                                                   │
│         ▼                                                   │
│  Kubernetes API Server accepts/rejects                     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## kubesec

kubesec analyzes Kubernetes manifests and assigns a security score.

### Installation

```bash
# Download binary
wget https://github.com/controlplaneio/kubesec/releases/download/v2.13.0/kubesec_linux_amd64.tar.gz
tar -xzf kubesec_linux_amd64.tar.gz
sudo mv kubesec /usr/local/bin/

# Or use Docker
docker run -i kubesec/kubesec:v2 scan /dev/stdin < pod.yaml

# Or use online API
curl -sSX POST --data-binary @pod.yaml https://v2.kubesec.io/scan
```

### Basic Usage

```bash
# Scan a file
kubesec scan pod.yaml

# Scan from stdin
cat pod.yaml | kubesec scan -

# Scan multiple files
kubesec scan deployment.yaml service.yaml
```

### Understanding kubesec Output

```json
[
  {
    "object": "Pod/insecure-pod.default",
    "valid": true,
    "score": -30,
    "scoring": {
      "critical": [
        {
          "selector": "containers[] .securityContext .privileged == true",
          "reason": "Privileged containers can allow almost completely unrestricted host access",
          "points": -30
        }
      ],
      "advise": [
        {
          "selector": "containers[] .securityContext .runAsNonRoot == true",
          "reason": "Force the running image to run as a non-root user",
          "points": 1
        },
        {
          "selector": ".spec .serviceAccountName",
          "reason": "Service accounts restrict Kubernetes API access",
          "points": 3
        }
      ]
    }
  }
]
```

### kubesec Scoring System

```
┌─────────────────────────────────────────────────────────────┐
│              KUBESEC SCORING                                │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  CRITICAL (negative points):                               │
│  ─────────────────────────────────────────────────────────  │
│  • privileged: true                    → -30 points        │
│  • hostNetwork: true                   → -9 points         │
│  • hostPID: true                       → -9 points         │
│  • hostIPC: true                       → -9 points         │
│  • capabilities.add: SYS_ADMIN         → -30 points        │
│                                                             │
│  POSITIVE (security improvements):                         │
│  ─────────────────────────────────────────────────────────  │
│  • runAsNonRoot: true                  → +1 point          │
│  • runAsUser > 10000                   → +1 point          │
│  • readOnlyRootFilesystem: true        → +1 point          │
│  • capabilities.drop: ALL              → +1 point          │
│  • resources.limits.cpu                → +1 point          │
│  • resources.limits.memory             → +1 point          │
│                                                             │
│  Score > 0: Generally acceptable                           │
│  Score < 0: Critical issues present                        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## kubesec Examples

### Insecure Pod

```yaml
# insecure-pod.yaml
apiVersion: v1
kind: Pod
metadata:
  name: insecure
spec:
  containers:
  - name: app
    image: nginx
    securityContext:
      privileged: true
```

```bash
kubesec scan insecure-pod.yaml
# Score: -30 (CRITICAL: privileged container)
```

### Secure Pod

```yaml
# secure-pod.yaml
apiVersion: v1
kind: Pod
metadata:
  name: secure
spec:
  securityContext:
    runAsNonRoot: true
    runAsUser: 10001
  containers:
  - name: app
    image: nginx
    securityContext:
      allowPrivilegeEscalation: false
      readOnlyRootFilesystem: true
      capabilities:
        drop: ["ALL"]
    resources:
      limits:
        memory: "128Mi"
        cpu: "500m"
```

```bash
kubesec scan secure-pod.yaml
# Score: 7+ (multiple security best practices)
```

---

## KubeLinter

KubeLinter is a static analysis tool that checks Kubernetes manifests against best practices and common misconfigurations. It's faster and more opinionated than kubesec, focusing on deployment safety.

```bash
# Install
curl -sL https://github.com/stackrox/kube-linter/releases/latest/download/kube-linter-linux -o kube-linter
chmod +x kube-linter

# Lint a manifest
./kube-linter lint deployment.yaml

# Lint an entire directory
./kube-linter lint manifests/

# List all available checks
./kube-linter checks list
```

KubeLinter catches issues like:
- Containers running as root
- No resource limits set
- No readiness/liveness probes
- Writable root filesystems
- Privileged containers
- Missing network policies

```bash
# Example output
deployment.yaml: (object: default/nginx apps/v1, Kind=Deployment)
  - container "nginx" does not have a read-only root file system
    (check: no-read-only-root-fs, remediation: Set readOnlyRootFilesystem to true)
  - container "nginx" has cpu limit 0 (check: unset-cpu-requirements)
  - container "nginx" is not set to runAsNonRoot (check: run-as-non-root)
```

> **kubesec vs KubeLinter**: kubesec scores overall security posture (good for audits). KubeLinter catches specific issues with actionable remediations (good for CI pipelines). Use both.

---

## OPA Gatekeeper

Open Policy Agent (OPA) Gatekeeper provides policy enforcement at admission time.

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│              OPA GATEKEEPER ARCHITECTURE                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  kubectl apply -f pod.yaml                                 │
│         │                                                   │
│         ▼                                                   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │            Kubernetes API Server                     │   │
│  │                    │                                 │   │
│  │           ValidatingWebhook                         │   │
│  │                    │                                 │   │
│  └────────────────────┼────────────────────────────────┘   │
│                       │                                     │
│                       ▼                                     │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              OPA Gatekeeper                          │   │
│  │  ┌─────────────────────────────────────────────┐    │   │
│  │  │  ConstraintTemplate (defines policy)        │    │   │
│  │  │  e.g., "K8sRequiredLabels"                  │    │   │
│  │  └─────────────────────────────────────────────┘    │   │
│  │  ┌─────────────────────────────────────────────┐    │   │
│  │  │  Constraint (applies policy)                │    │   │
│  │  │  e.g., "require label: team"                │    │   │
│  │  └─────────────────────────────────────────────┘    │   │
│  └─────────────────────────────────────────────────────┘   │
│                       │                                     │
│                       ▼                                     │
│              Allow or Deny request                         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Installing Gatekeeper

```bash
# Install using kubectl
kubectl apply -f https://raw.githubusercontent.com/open-policy-agent/gatekeeper/release-3.14/deploy/gatekeeper.yaml

# Verify installation
kubectl get pods -n gatekeeper-system
kubectl get crd | grep gatekeeper
```

### Creating a Policy

#### Step 1: ConstraintTemplate

```yaml
apiVersion: templates.gatekeeper.sh/v1
kind: ConstraintTemplate
metadata:
  name: k8srequiredlabels
spec:
  crd:
    spec:
      names:
        kind: K8sRequiredLabels
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
          provided := {label | input.review.object.metadata.labels[label]}
          required := {label | label := input.parameters.labels[_]}
          missing := required - provided
          count(missing) > 0
          msg := sprintf("Missing required labels: %v", [missing])
        }
```

#### Step 2: Constraint

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
    namespaces: ["production"]
  parameters:
    labels: ["team", "app"]
```

### Testing the Policy

```bash
# This pod will be rejected
kubectl apply -f - <<EOF
apiVersion: v1
kind: Pod
metadata:
  name: unlabeled-pod
  namespace: production
spec:
  containers:
  - name: nginx
    image: nginx
EOF
# Error: Missing required labels: {"app", "team"}

# This pod will be allowed
kubectl apply -f - <<EOF
apiVersion: v1
kind: Pod
metadata:
  name: labeled-pod
  namespace: production
  labels:
    team: platform
    app: web
spec:
  containers:
  - name: nginx
    image: nginx
EOF
```

---

## Common Gatekeeper Policies

### Block Privileged Containers

```yaml
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
          msg := sprintf("Privileged container not allowed: %v", [container.name])
        }
---
apiVersion: constraints.gatekeeper.sh/v1beta1
kind: K8sBlockPrivileged
metadata:
  name: block-privileged-containers
spec:
  match:
    kinds:
      - apiGroups: [""]
        kinds: ["Pod"]
```

### Require Non-Root

```yaml
apiVersion: templates.gatekeeper.sh/v1
kind: ConstraintTemplate
metadata:
  name: k8srequirenonroot
spec:
  crd:
    spec:
      names:
        kind: K8sRequireNonRoot
  targets:
    - target: admission.k8s.gatekeeper.sh
      rego: |
        package k8srequirenonroot

        violation[{"msg": msg}] {
          container := input.review.object.spec.containers[_]
          not container.securityContext.runAsNonRoot
          msg := sprintf("Container must set runAsNonRoot: %v", [container.name])
        }
```

### Block :latest Tag

```yaml
apiVersion: templates.gatekeeper.sh/v1
kind: ConstraintTemplate
metadata:
  name: k8sblocklatesttag
spec:
  crd:
    spec:
      names:
        kind: K8sBlockLatestTag
  targets:
    - target: admission.k8s.gatekeeper.sh
      rego: |
        package k8sblocklatesttag

        violation[{"msg": msg}] {
          container := input.review.object.spec.containers[_]
          endswith(container.image, ":latest")
          msg := sprintf("Image with :latest tag not allowed: %v", [container.image])
        }

        violation[{"msg": msg}] {
          container := input.review.object.spec.containers[_]
          not contains(container.image, ":")
          msg := sprintf("Image without tag (defaults to :latest) not allowed: %v", [container.image])
        }
```

---

## Real Exam Scenarios

### Scenario 1: Scan Pod with kubesec

```bash
# Create test pod
cat <<EOF > test-pod.yaml
apiVersion: v1
kind: Pod
metadata:
  name: web
spec:
  containers:
  - name: nginx
    image: nginx
    securityContext:
      privileged: true
EOF

# Scan with kubesec
kubesec scan test-pod.yaml

# Fix the pod based on kubesec recommendations
cat <<EOF > test-pod-fixed.yaml
apiVersion: v1
kind: Pod
metadata:
  name: web
spec:
  securityContext:
    runAsNonRoot: true
    runAsUser: 10001
  containers:
  - name: nginx
    image: nginx
    securityContext:
      allowPrivilegeEscalation: false
      readOnlyRootFilesystem: true
      capabilities:
        drop: ["ALL"]
    resources:
      limits:
        memory: "128Mi"
        cpu: "500m"
EOF

kubesec scan test-pod-fixed.yaml
# Score should be positive now
```

### Scenario 2: Create Gatekeeper Policy

```bash
# Create ConstraintTemplate
cat <<EOF | kubectl apply -f -
apiVersion: templates.gatekeeper.sh/v1
kind: ConstraintTemplate
metadata:
  name: k8srequirelimits
spec:
  crd:
    spec:
      names:
        kind: K8sRequireLimits
  targets:
    - target: admission.k8s.gatekeeper.sh
      rego: |
        package k8srequirelimits

        violation[{"msg": msg}] {
          container := input.review.object.spec.containers[_]
          not container.resources.limits.memory
          msg := sprintf("Container must have memory limits: %v", [container.name])
        }

        violation[{"msg": msg}] {
          container := input.review.object.spec.containers[_]
          not container.resources.limits.cpu
          msg := sprintf("Container must have CPU limits: %v", [container.name])
        }
EOF

# Create Constraint
cat <<EOF | kubectl apply -f -
apiVersion: constraints.gatekeeper.sh/v1beta1
kind: K8sRequireLimits
metadata:
  name: require-resource-limits
spec:
  match:
    kinds:
      - apiGroups: [""]
        kinds: ["Pod"]
    namespaces: ["production"]
EOF

# Test - this should fail
kubectl run test --image=nginx -n production
# Error: Container must have memory limits

# Test - this should succeed
kubectl run test --image=nginx -n production \
  --limits='memory=128Mi,cpu=500m'
```

### Scenario 3: Audit Existing Violations

```bash
# Check constraint status for violations
kubectl get k8srequiredlabels require-team-label -o yaml

# Look at the status.violations section
kubectl get constraints -A -o json | \
  jq '.items[] | {name: .metadata.name, violations: .status.totalViolations}'
```

---

## Did You Know?

- **kubesec was created by Control Plane** (formerly Aqua) and is specifically designed for Kubernetes security scoring.

- **OPA uses Rego**, a purpose-built policy language. It's declarative and designed for expressing complex access control policies.

- **Gatekeeper operates as a ValidatingAdmissionWebhook**, which means it can only allow or deny requests—it can't modify them. For mutation, use MutatingAdmissionWebhooks.

- **Gatekeeper supports audit mode**, which reports violations without blocking them. Great for rolling out new policies.

---

## Common Mistakes

| Mistake | Why It Hurts | Solution |
|---------|--------------|----------|
| Ignoring kubesec warnings | Deployments have known issues | Address critical findings |
| Complex Rego policies | Hard to debug and maintain | Start simple, test thoroughly |
| No exemptions | System pods blocked | Use match.excludedNamespaces |
| Audit mode forgotten | Violations not enforced | Change to enforce after testing |
| Missing error messages | Users confused | Include clear violation messages |

---

## Quiz

1. **What does a negative kubesec score indicate?**
   <details>
   <summary>Answer</summary>
   A negative score indicates critical security issues like privileged containers, hostNetwork, or dangerous capabilities. These issues should be addressed immediately.
   </details>

2. **What are the two resources needed to create a Gatekeeper policy?**
   <details>
   <summary>Answer</summary>
   ConstraintTemplate (defines the policy logic in Rego) and Constraint (applies the policy to specific resources). The template is reusable, and constraints parameterize it.
   </details>

3. **How do you test Gatekeeper policies without blocking deployments?**
   <details>
   <summary>Answer</summary>
   Use audit mode by setting `enforcementAction: dryrun` on the Constraint. Violations are recorded but not blocked.
   </details>

4. **What language does OPA Gatekeeper use for policies?**
   <details>
   <summary>Answer</summary>
   Rego - a declarative query language specifically designed for expressing policies over complex hierarchical data.
   </details>

---

## Hands-On Exercise

**Task**: Use kubesec and create a Gatekeeper policy.

```bash
# Part 1: kubesec Analysis

# Create insecure pod
cat <<EOF > insecure.yaml
apiVersion: v1
kind: Pod
metadata:
  name: insecure
spec:
  containers:
  - name: app
    image: nginx
    securityContext:
      privileged: true
EOF

# Scan with kubesec (using API if not installed locally)
echo "=== kubesec Scan (Insecure) ==="
curl -sSX POST --data-binary @insecure.yaml https://v2.kubesec.io/scan | jq '.[0].score'

# Create secure version
cat <<EOF > secure.yaml
apiVersion: v1
kind: Pod
metadata:
  name: secure
spec:
  securityContext:
    runAsNonRoot: true
    runAsUser: 10001
  containers:
  - name: app
    image: nginx
    securityContext:
      allowPrivilegeEscalation: false
      readOnlyRootFilesystem: true
      capabilities:
        drop: ["ALL"]
    resources:
      limits:
        memory: "128Mi"
        cpu: "500m"
EOF

echo "=== kubesec Scan (Secure) ==="
curl -sSX POST --data-binary @secure.yaml https://v2.kubesec.io/scan | jq '.[0].score'

# Part 2: Gatekeeper Policy (if Gatekeeper is installed)

# Check if Gatekeeper is installed
if kubectl get crd constrainttemplates.templates.gatekeeper.sh &>/dev/null; then
  echo "=== Creating Gatekeeper Policy ==="

  # Create ConstraintTemplate
  cat <<EOF | kubectl apply -f -
apiVersion: templates.gatekeeper.sh/v1
kind: ConstraintTemplate
metadata:
  name: k8sblockdefaultnamespace
spec:
  crd:
    spec:
      names:
        kind: K8sBlockDefaultNamespace
  targets:
    - target: admission.k8s.gatekeeper.sh
      rego: |
        package k8sblockdefaultnamespace
        violation[{"msg": msg}] {
          input.review.object.metadata.namespace == "default"
          msg := "Deployments to default namespace are not allowed"
        }
EOF

  # Create Constraint in dryrun mode
  cat <<EOF | kubectl apply -f -
apiVersion: constraints.gatekeeper.sh/v1beta1
kind: K8sBlockDefaultNamespace
metadata:
  name: block-default-namespace
spec:
  enforcementAction: dryrun
  match:
    kinds:
      - apiGroups: [""]
        kinds: ["Pod"]
EOF

  echo "Policy created in dryrun mode"
else
  echo "Gatekeeper not installed, skipping policy creation"
fi

# Cleanup
rm -f insecure.yaml secure.yaml
```

**Success criteria**: Understand kubesec scoring and Gatekeeper policy structure.

---

## Summary

**kubesec**:
- Security scoring tool
- Negative score = critical issues
- Positive score = security best practices
- Use in CI/CD pipelines

**OPA Gatekeeper**:
- Admission controller for policies
- ConstraintTemplate + Constraint
- Rego policy language
- Audit mode for testing

**Best Practices**:
- Scan manifests before deployment
- Block privileged containers
- Require resource limits
- Test policies in audit mode first

**Exam Tips**:
- Know kubesec command syntax
- Understand Gatekeeper CRDs
- Be able to write basic Rego

---

## Next Module

[Module 5.4: Admission Controllers](../module-5.4-admission-controllers/) - Custom admission control for security.
