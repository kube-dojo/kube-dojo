---
title: "Module 4.2: Pod Security Admission (PSA)"
slug: k8s/cks/part4-microservice-vulnerabilities/module-4.2-pod-security-admission
sidebar:
  order: 2
lab:
  id: cks-4.2-pod-security-admission
  url: https://killercoda.com/kubedojo/scenario/cks-4.2-pod-security-admission
  duration: "35 min"
  difficulty: advanced
  environment: kubernetes
---
> **Complexity**: `[MEDIUM]` - Core CKS skill
>
> **Time to Complete**: 40-45 minutes
>
> **Prerequisites**: Module 4.1 (Security Contexts), namespace basics

---

## What You'll Be Able to Do

After completing this module, you will be able to:

1. **Configure** Pod Security Admission labels on namespaces for enforce, audit, and warn modes
2. **Implement** baseline and restricted security profiles across cluster namespaces
3. **Diagnose** PSA rejection messages and adjust pod specs to comply with security standards
4. **Design** a namespace-level security strategy using PSA profiles appropriate to workload sensitivity

---

## Why This Module Matters

Pod Security Admission (PSA) enforces security standards at the namespace level. Instead of manually checking every pod's security context, PSA automatically validates pods against defined security profiles and blocks non-compliant ones.

PSA replaced PodSecurityPolicy (removed in Kubernetes 1.25). This is a critical CKS topic.

---

## Pod Security Standards

```
┌─────────────────────────────────────────────────────────────┐
│              POD SECURITY STANDARDS                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Privileged (most permissive)                              │
│  ─────────────────────────────────────────────────────────  │
│  • No restrictions                                         │
│  • For system-level workloads                              │
│  • CNI, CSI, logging agents                                │
│                                                             │
│  Baseline (reasonable default)                             │
│  ─────────────────────────────────────────────────────────  │
│  • Prevents known privilege escalations                    │
│  • Blocks hostNetwork, hostPID, hostIPC                   │
│  • Blocks privileged containers                            │
│  • Allows running as root                                  │
│                                                             │
│  Restricted (most secure)                                  │
│  ─────────────────────────────────────────────────────────  │
│  • Maximum security                                        │
│  • Requires running as non-root                            │
│  • Requires dropping ALL capabilities                      │
│  • Requires read-only root filesystem                      │
│  • Requires seccomp profile                                │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## PSA Modes

```
┌─────────────────────────────────────────────────────────────┐
│              PSA ENFORCEMENT MODES                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  enforce                                                   │
│  └── Reject pods that violate the policy                   │
│      (Pod creation fails)                                  │
│                                                             │
│  warn                                                      │
│  └── Allow but show warning to user                        │
│      (Good for migration)                                  │
│                                                             │
│  audit                                                     │
│  └── Record violation in audit log                         │
│      (Pod still created)                                   │
│                                                             │
│  You can use different profiles for each mode:             │
│  • enforce: baseline (block obvious issues)               │
│  • warn: restricted (show what would fail)                │
│  • audit: restricted (log for review)                     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Configuring PSA via Labels

```yaml
# Apply PSA to a namespace using labels
apiVersion: v1
kind: Namespace
metadata:
  name: secure-ns
  labels:
    # Enforce baseline standard
    pod-security.kubernetes.io/enforce: baseline
    pod-security.kubernetes.io/enforce-version: latest

    # Warn on restricted violations
    pod-security.kubernetes.io/warn: restricted
    pod-security.kubernetes.io/warn-version: latest

    # Audit restricted violations
    pod-security.kubernetes.io/audit: restricted
    pod-security.kubernetes.io/audit-version: latest
```

### Label Format

```
pod-security.kubernetes.io/<MODE>: <PROFILE>
pod-security.kubernetes.io/<MODE>-version: <VERSION>

MODE:    enforce | warn | audit
PROFILE: privileged | baseline | restricted
VERSION: latest | v1.28 | v1.27 | etc.
```

---

## Profile Requirements

### Baseline Profile Restrictions

```yaml
# Baseline blocks these:
hostNetwork: true          # Blocked
hostPID: true              # Blocked
hostIPC: true              # Blocked
privileged: true           # Blocked
hostPorts: [80, 443]       # Blocked (hostPort)

# These capabilities blocked:
capabilities:
  add:
    - NET_ADMIN            # Blocked
    - SYS_ADMIN            # Blocked
    - ALL                  # Blocked

# Baseline ALLOWS:
runAsUser: 0               # Running as root OK
runAsNonRoot: false        # Not required
readOnlyRootFilesystem: false  # Not required
```

### Restricted Profile Requirements

```yaml
# Restricted REQUIRES:
securityContext:
  runAsNonRoot: true               # Required
  allowPrivilegeEscalation: false  # Required
  seccompProfile:
    type: RuntimeDefault           # Required (or Localhost)
  capabilities:
    drop: ["ALL"]                  # Required

# For containers specifically:
containers:
- name: app
  securityContext:
    runAsNonRoot: true
    allowPrivilegeEscalation: false
    readOnlyRootFilesystem: true   # Recommended but not required
    capabilities:
      drop: ["ALL"]
```

---

## Practical Examples

### Create Restricted Namespace

```bash
# Create namespace with restricted enforcement
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Namespace
metadata:
  name: production
  labels:
    pod-security.kubernetes.io/enforce: restricted
    pod-security.kubernetes.io/enforce-version: latest
    pod-security.kubernetes.io/warn: restricted
    pod-security.kubernetes.io/audit: restricted
EOF
```

### Test Policy Enforcement

```bash
# This pod will be REJECTED in restricted namespace
cat <<EOF | kubectl apply -f - -n production
apiVersion: v1
kind: Pod
metadata:
  name: insecure-pod
spec:
  containers:
  - name: app
    image: nginx
EOF

# Error: pods "insecure-pod" is forbidden:
# violates PodSecurity "restricted:latest":
# allowPrivilegeEscalation != false,
# unrestricted capabilities,
# runAsNonRoot != true,
# seccompProfile

# This pod SUCCEEDS in restricted namespace
cat <<EOF | kubectl apply -f - -n production
apiVersion: v1
kind: Pod
metadata:
  name: secure-pod
spec:
  securityContext:
    runAsNonRoot: true
    runAsUser: 1000
    seccompProfile:
      type: RuntimeDefault
  containers:
  - name: app
    image: nginx
    securityContext:
      allowPrivilegeEscalation: false
      capabilities:
        drop: ["ALL"]
EOF
```

---

## Exemptions

### Namespace-Level Exemptions

```yaml
# Exempt specific namespaces in AdmissionConfiguration
apiVersion: apiserver.config.k8s.io/v1
kind: AdmissionConfiguration
plugins:
- name: PodSecurity
  configuration:
    apiVersion: pod-security.admission.config.k8s.io/v1
    kind: PodSecurityConfiguration
    defaults:
      enforce: "baseline"
      enforce-version: "latest"
    exemptions:
      # Exempt kube-system namespace
      namespaces:
        - kube-system
      # Exempt specific users
      usernames:
        - system:serviceaccount:kube-system:*
      # Exempt specific runtime classes
      runtimeClasses:
        - gvisor
```

### Exempt System Namespaces

```bash
# kube-system typically needs privileged access
kubectl label namespace kube-system pod-security.kubernetes.io/enforce=privileged --overwrite
```

---

## Migration Strategy

```
┌─────────────────────────────────────────────────────────────┐
│              PSA MIGRATION STRATEGY                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Phase 1: Audit Only                                       │
│  ─────────────────────────────────────────────────────────  │
│  pod-security.kubernetes.io/audit: restricted              │
│  • All pods still created                                  │
│  • Violations logged                                       │
│  • Review audit logs for issues                            │
│                                                             │
│  Phase 2: Warn and Audit                                   │
│  ─────────────────────────────────────────────────────────  │
│  pod-security.kubernetes.io/warn: restricted               │
│  pod-security.kubernetes.io/audit: restricted              │
│  • Developers see warnings                                 │
│  • Still non-blocking                                      │
│                                                             │
│  Phase 3: Enforce Baseline, Warn Restricted               │
│  ─────────────────────────────────────────────────────────  │
│  pod-security.kubernetes.io/enforce: baseline              │
│  pod-security.kubernetes.io/warn: restricted               │
│  • Block obvious violations                                │
│  • Warn on restricted issues                               │
│                                                             │
│  Phase 4: Full Enforcement                                 │
│  ─────────────────────────────────────────────────────────  │
│  pod-security.kubernetes.io/enforce: restricted            │
│  • Maximum security                                        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Real Exam Scenarios

### Scenario 1: Enable Restricted Mode

```bash
# Apply restricted enforcement to namespace
kubectl label namespace production \
  pod-security.kubernetes.io/enforce=restricted \
  pod-security.kubernetes.io/enforce-version=latest

# Verify label
kubectl get namespace production --show-labels
```

### Scenario 2: Fix Pod for Restricted Namespace

```yaml
# Original pod (fails in restricted)
apiVersion: v1
kind: Pod
metadata:
  name: web
spec:
  containers:
  - name: nginx
    image: nginx

# Fixed pod (works in restricted)
apiVersion: v1
kind: Pod
metadata:
  name: web
spec:
  securityContext:
    runAsNonRoot: true
    runAsUser: 101  # nginx user
    seccompProfile:
      type: RuntimeDefault
  containers:
  - name: nginx
    image: nginx
    securityContext:
      allowPrivilegeEscalation: false
      capabilities:
        drop: ["ALL"]
      readOnlyRootFilesystem: true
    volumeMounts:
    - name: cache
      mountPath: /var/cache/nginx
    - name: run
      mountPath: /var/run
  volumes:
  - name: cache
    emptyDir: {}
  - name: run
    emptyDir: {}
```

### Scenario 3: Debug PSA Rejection

```bash
# Check namespace labels
kubectl get namespace production -o yaml | grep -A10 labels

# Create pod and see detailed error
kubectl apply -f pod.yaml -n production 2>&1 | head -20

# Dry run to check without creating
kubectl apply -f pod.yaml -n production --dry-run=server
```

---

## Did You Know?

- **PSA replaced PodSecurityPolicy (PSP)** which was deprecated in Kubernetes 1.21 and removed in 1.25. PSA is simpler and based on namespace labels.

- **The "latest" version** follows the Kubernetes version. Using "latest" means the policy updates when you upgrade Kubernetes.

- **System namespaces need privileged.** kube-system pods (CNI, CSI, kube-proxy) often require host access. Always exempt or use privileged level.

- **PSA is built into the API server** and enabled by default since Kubernetes 1.25. No additional installation needed.

---

## Common Mistakes

| Mistake | Why It Hurts | Solution |
|---------|--------------|----------|
| Enforcing restricted on kube-system | System pods fail | Use privileged for system namespaces |
| No runAsNonRoot in restricted | Pods rejected | Add runAsNonRoot: true |
| Missing seccompProfile | Restricted requires it | Add RuntimeDefault |
| Not dropping capabilities | Restricted requires it | Drop ALL |
| Skipping warn phase | Sudden failures | Migrate gradually |

---

## Quiz

1. **What are the three Pod Security Standards?**
   <details>
   <summary>Answer</summary>
   Privileged (no restrictions), Baseline (prevents known escalations), and Restricted (maximum security). Each level is progressively more secure.
   </details>

2. **What's the difference between enforce, warn, and audit modes?**
   <details>
   <summary>Answer</summary>
   Enforce: Reject violating pods. Warn: Allow but show warning. Audit: Log to audit log but allow. You can use different profiles for each mode.
   </details>

3. **What security context fields are required for the restricted profile?**
   <details>
   <summary>Answer</summary>
   runAsNonRoot: true, allowPrivilegeEscalation: false, capabilities.drop: ["ALL"], and seccompProfile.type: RuntimeDefault (or Localhost).
   </details>

4. **How do you apply PSA to a namespace?**
   <details>
   <summary>Answer</summary>
   Using labels: `pod-security.kubernetes.io/enforce: <profile>` and optionally `-version: latest` on the namespace.
   </details>

---

## Hands-On Exercise

**Task**: Configure and test Pod Security Admission.

```bash
# Step 1: Create namespace with baseline enforcement
kubectl create namespace psa-test
kubectl label namespace psa-test \
  pod-security.kubernetes.io/enforce=baseline \
  pod-security.kubernetes.io/warn=restricted

# Step 2: Verify labels
kubectl get namespace psa-test --show-labels

# Step 3: Test baseline allows regular pods
kubectl run baseline-test --image=nginx -n psa-test
kubectl get pod baseline-test -n psa-test

# Step 4: Test baseline blocks privileged
cat <<EOF | kubectl apply -f - -n psa-test
apiVersion: v1
kind: Pod
metadata:
  name: privileged-pod
spec:
  containers:
  - name: app
    image: nginx
    securityContext:
      privileged: true
EOF
# Should be rejected

# Step 5: Upgrade to restricted
kubectl label namespace psa-test \
  pod-security.kubernetes.io/enforce=restricted --overwrite

# Step 6: Previous pod now shows warning at restricted level
# Delete and recreate
kubectl delete pod baseline-test -n psa-test
kubectl run restricted-test --image=nginx -n psa-test 2>&1 || echo "Rejected (expected)"

# Step 7: Create compliant pod
cat <<EOF | kubectl apply -f - -n psa-test
apiVersion: v1
kind: Pod
metadata:
  name: compliant-pod
spec:
  securityContext:
    runAsNonRoot: true
    runAsUser: 1000
    seccompProfile:
      type: RuntimeDefault
  containers:
  - name: app
    image: busybox
    command: ["sleep", "3600"]
    securityContext:
      allowPrivilegeEscalation: false
      capabilities:
        drop: ["ALL"]
EOF

kubectl get pod compliant-pod -n psa-test

# Cleanup
kubectl delete namespace psa-test
```

**Success criteria**: Understand how PSA blocks non-compliant pods.

---

## Summary

**Pod Security Standards**:
- Privileged: No restrictions
- Baseline: Block known escalations
- Restricted: Maximum security

**Modes**:
- enforce: Block violations
- warn: Show warnings
- audit: Log violations

**Required for Restricted**:
- runAsNonRoot: true
- allowPrivilegeEscalation: false
- capabilities.drop: ["ALL"]
- seccompProfile: RuntimeDefault

**Exam Tips**:
- Know namespace label format
- Memorize restricted requirements
- Migrate gradually (audit → warn → enforce)

---

## Next Module

[Module 4.3: Secrets Management](../module-4.3-secrets-management/) - Securing Kubernetes secrets.
