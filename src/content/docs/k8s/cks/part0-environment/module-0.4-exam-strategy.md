---
title: "Module 0.4: CKS Exam Strategy"
slug: k8s/cks/part0-environment/module-0.4-exam-strategy
sidebar:
  order: 4
lab:
  id: cks-0.4-exam-strategy
  url: https://killercoda.com/kubedojo/scenario/cks-0.4-exam-strategy
  duration: "30 min"
  difficulty: advanced
  environment: kubernetes
---
> **Complexity**: `[QUICK]` - Critical for exam success
>
> **Time to Complete**: 20-25 minutes
>
> **Prerequisites**: CKA certification, Module 0.1-0.3

---

## What You'll Be Able to Do

After completing this module, you will be able to:

1. **Implement** the three-pass strategy adapted for security-specific CKS tasks
2. **Evaluate** task complexity to decide skip-or-solve within the first 30 seconds
3. **Design** a time budget that maximizes points across all CKS domains
4. **Create** a personal exam-day checklist covering environment setup and kubectl shortcuts

---

## Why This Module Matters

The CKS exam is 2 hours, ~15-20 tasks, 67% to pass. Time pressure is real. Many candidates who know the material fail because they manage time poorly or get stuck on complex tasks.

This module adapts the three-pass strategy for security-specific challenges.

---

## The Security Three-Pass Strategy

```
┌─────────────────────────────────────────────────────────────┐
│              CKS THREE-PASS STRATEGY                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  PASS 1: Quick Security Wins (40-50 min)                   │
│  Target: 1-3 min per task                                  │
│  ─────────────────────────────────────────────────────────  │
│  ✓ Create/modify NetworkPolicy                             │
│  ✓ Fix RBAC permission issue                               │
│  ✓ Apply existing AppArmor profile                         │
│  ✓ Set securityContext fields                              │
│  ✓ Enable audit logging                                    │
│  ✓ Run Trivy scan, identify vulnerabilities                │
│                                                             │
│  PASS 2: Tool-Based Tasks (40-50 min)                      │
│  Target: 4-6 min per task                                  │
│  ─────────────────────────────────────────────────────────  │
│  ✓ Create seccomp profile from scratch                     │
│  ✓ Configure Pod Security Admission                         │
│  ✓ Run kube-bench, fix specific findings                   │
│  ✓ Create NetworkPolicy with egress rules                  │
│  ✓ Set up ServiceAccount with minimal permissions          │
│                                                             │
│  PASS 3: Complex Scenarios (20-30 min)                     │
│  Target: 7+ min per task                                   │
│  ─────────────────────────────────────────────────────────  │
│  ✓ Write custom Falco rule                                 │
│  ✓ Investigate and respond to runtime incident             │
│  ✓ Multi-step cluster hardening                            │
│  ✓ Complex NetworkPolicy (multiple pods, namespaces)       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Task Classification

Learn to recognize task complexity in seconds:

### Pass 1 Tasks (Quick)

| Pattern | Example | Time |
|---------|---------|------|
| "Set runAsNonRoot" | Add field to securityContext | 1-2 min |
| "Create NetworkPolicy to allow..." | Single ingress/egress rule | 2-3 min |
| "Grant permission to..." | Create Role/RoleBinding | 2-3 min |
| "Apply AppArmor profile" | Add annotation | 1-2 min |
| "Scan image with Trivy" | Run command, report findings | 2-3 min |

### Pass 2 Tasks (Medium)

| Pattern | Example | Time |
|---------|---------|------|
| "Create seccomp profile" | Write JSON, reference in pod | 4-5 min |
| "Fix all kube-bench failures" | Multiple config changes | 5-6 min |
| "Configure PSA for namespace" | Labels + test pods | 4-5 min |
| "Restrict ServiceAccount" | RBAC + automount settings | 4-5 min |
| "NetworkPolicy with multiple rules" | Ingress + egress | 5-6 min |

### Pass 3 Tasks (Complex)

| Pattern | Example | Time |
|---------|---------|------|
| "Write Falco rule to detect..." | Custom condition + output | 7-10 min |
| "Investigate incident" | Read logs, identify cause, fix | 8-12 min |
| "Harden cluster based on..." | Multiple components | 10-15 min |
| "Isolate compromised pod" | NetworkPolicy + analysis | 8-10 min |

---

## Time Budget

```
┌─────────────────────────────────────────────────────────────┐
│              120 MINUTE TIME BUDGET                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  0:00  ─────── Pass 1 Start ───────                        │
│  │                                                          │
│  │     Quick wins: RBAC, basic NetworkPolicy,              │
│  │     securityContext, AppArmor annotations               │
│  │                                                          │
│  0:50  ─────── Pass 2 Start ───────                        │
│  │                                                          │
│  │     Tool tasks: seccomp, PSA, kube-bench fixes,        │
│  │     complex NetworkPolicies, ServiceAccount hardening   │
│  │                                                          │
│  1:40  ─────── Pass 3 Start ───────                        │
│  │                                                          │
│  │     Complex: Falco rules, incident investigation,       │
│  │     multi-step hardening                                │
│  │                                                          │
│  2:00  ─────── Exam End ───────                            │
│                                                             │
│  Reserve 5 min at end for verification!                    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Security-Specific Tips

### 1. Know Your Documentation

```bash
# Bookmark these in exam browser:

# NetworkPolicy examples
kubernetes.io/docs/concepts/services-networking/network-policies/

# Pod Security Standards
kubernetes.io/docs/concepts/security/pod-security-standards/

# seccomp profiles
kubernetes.io/docs/tutorials/security/seccomp/

# AppArmor
kubernetes.io/docs/tutorials/security/apparmor/

# Trivy
aquasecurity.github.io/trivy/

# Falco
falco.org/docs/
```

### 2. Template Commands Ready

```bash
# Trivy scan
trivy image --severity HIGH,CRITICAL <image>

# kube-bench
./kube-bench run --targets=master

# Check AppArmor profiles
cat /sys/kernel/security/apparmor/profiles

# Check seccomp support
grep SECCOMP /boot/config-$(uname -r)

# Audit logs location
/var/log/kubernetes/audit.log
```

### 3. Common Security Context Fields

```yaml
# Memorize this pattern
securityContext:
  runAsNonRoot: true
  runAsUser: 1000
  readOnlyRootFilesystem: true
  allowPrivilegeEscalation: false
  capabilities:
    drop: ["ALL"]
```

### 4. NetworkPolicy Patterns

```yaml
# Default deny all ingress
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-ingress
spec:
  podSelector: {}
  policyTypes:
  - Ingress

# Allow specific pod
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-app
spec:
  podSelector:
    matchLabels:
      app: web
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: api
    ports:
    - port: 80
```

---

## Exam Environment Tips

### Security Tool Locations

| Tool | Location in Exam |
|------|------------------|
| Trivy | Pre-installed or provided |
| Falco | Running in cluster or installable |
| kube-bench | Download or job manifest |
| kubesec | May need to download |

### File Locations

| File | Path |
|------|------|
| API server manifest | `/etc/kubernetes/manifests/kube-apiserver.yaml` |
| kubelet config | `/var/lib/kubelet/config.yaml` |
| Audit policy | `/etc/kubernetes/audit-policy.yaml` |
| seccomp profiles | `/var/lib/kubelet/seccomp/` |
| AppArmor profiles | `/etc/apparmor.d/` |

---

## When to Skip

**Skip immediately if**:
- Task requires tool you've never used
- Complex Falco rule with unfamiliar syntax
- Multi-namespace NetworkPolicy with unclear requirements

**Come back if time permits**. Partial credit exists—submit something.

---

## Verification Checklist

Before moving to next task:

```bash
# For pods/deployments
kubectl get pods -n <namespace>  # Running?

# For NetworkPolicy
kubectl describe networkpolicy <name>  # Applied?

# For RBAC
kubectl auth can-i <verb> <resource> --as=<user>  # Works?

# For security context
kubectl get pod <name> -o yaml | grep -A 10 securityContext

# For Trivy
trivy image <image>  # Scans correctly?
```

---

## Did You Know?

- **67% pass rate means you can miss ~5-6 tasks** out of 15-20 and still pass. Don't panic if you skip some.

- **Partial credit is possible.** Even incomplete answers may score points. Always submit something.

- **The exam is open book.** Your challenge is finding information fast, not memorizing everything.

- **Security tasks often have multiple valid approaches.** The exam checks the result, not the exact method.

---

## Common Mistakes

| Mistake | Why It Hurts | Solution |
|---------|--------------|----------|
| Starting with complex tasks | Time wasted, confidence lost | Three-pass strategy |
| Not reading task completely | Missing requirements | Read twice before typing |
| Forgetting namespace | Changes in wrong namespace | Always `-n namespace` |
| Not verifying | Partial solutions | Check before moving on |
| Over-engineering | Simple solution was enough | Match requirements exactly |

---

## Quiz

1. **In the three-pass strategy, what tasks should you do first?**
   <details>
   <summary>Answer</summary>
   Quick wins (Pass 1): Simple RBAC fixes, basic NetworkPolicies, securityContext additions, AppArmor annotation additions. Tasks taking 1-3 minutes each.
   </details>

2. **How much time should you reserve for Pass 3 (complex tasks)?**
   <details>
   <summary>Answer</summary>
   20-30 minutes. Complex tasks like Falco rules and incident investigation need more time. But don't start here—earn points with quick wins first.
   </details>

3. **What should you do if you encounter a completely unfamiliar task?**
   <details>
   <summary>Answer</summary>
   Flag it and skip. Return in Pass 3 if time permits. Spending 15 minutes on one task you can't solve wastes time better spent on tasks you can complete.
   </details>

4. **Why verify each task before moving on?**
   <details>
   <summary>Answer</summary>
   Partial solutions don't score. A NetworkPolicy that doesn't apply, a pod that doesn't run, or RBAC that doesn't work scores zero. Verification catches these.
   </details>

---

## Hands-On Exercise

**Task**: Practice time management with sample tasks.

```bash
# Simulate exam conditions:
# Set a 15-minute timer for these 5 tasks
# START YOUR TIMER NOW!

# Task 1 (2 min): Create NetworkPolicy
kubectl create namespace secure

cat <<EOF | kubectl apply -f -
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: deny-all
  namespace: secure
spec:
  podSelector: {}
  policyTypes:
  - Ingress
EOF

# Verify:
kubectl get networkpolicy -n secure

# Task 2 (2 min): Fix security context
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: insecure-pod
  namespace: secure
spec:
  containers:
  - name: app
    image: busybox
    command: ["sleep", "3600"]
    securityContext:
      runAsUser: 1000
      runAsNonRoot: true
EOF

# Verify:
kubectl get pod insecure-pod -n secure -o jsonpath='{.spec.containers[0].securityContext}'
echo ""

# Task 3 (3 min): RBAC
kubectl create serviceaccount app-sa -n secure

cat <<EOF | kubectl apply -f -
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: pod-reader
  namespace: secure
rules:
- apiGroups: [""]
  resources: ["pods"]
  verbs: ["get", "list", "watch"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: read-pods
  namespace: secure
subjects:
- kind: ServiceAccount
  name: app-sa
  namespace: secure
roleRef:
  kind: Role
  name: pod-reader
  apiGroup: rbac.authorization.k8s.io
EOF

# Verify:
kubectl auth can-i list pods -n secure --as=system:serviceaccount:secure:app-sa

# Task 4 (4 min): Trivy scan
# (Requires Trivy installed - skip if not available)
trivy image --severity CRITICAL nginx:1.20 2>/dev/null || echo "Trivy not installed - would scan for CVEs"

# Task 5 (4 min): AppArmor
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: web
  namespace: secure
  annotations:
    container.apparmor.security.beta.kubernetes.io/web: runtime/default
spec:
  containers:
  - name: web
    image: nginx:alpine
    securityContext:
      runAsNonRoot: false  # nginx needs root initially
EOF

# Verify:
kubectl get pod web -n secure -o jsonpath='{.metadata.annotations}'
echo ""

# STOP TIMER - How did you do?
echo "=== Task Summary ==="
kubectl get networkpolicy,pods,role,rolebinding,sa -n secure

# Cleanup
kubectl delete namespace secure
```

**Success criteria**: Complete at least 4/5 tasks in 15 minutes.

---

## Summary

**Three-pass strategy for CKS**:
- Pass 1 (50 min): Quick wins—RBAC, basic NetworkPolicy, securityContext
- Pass 2 (50 min): Tool tasks—seccomp, PSA, kube-bench
- Pass 3 (20 min): Complex—Falco rules, incident response

**Key principles**:
- Earn points early with quick wins
- Skip unfamiliar tasks, return later
- Verify every solution
- Use documentation efficiently
- Reserve time for verification

**Remember**: 67% to pass. You can skip some tasks and still succeed.

---

## Part 0 Complete!

You've finished the **Environment Setup** section. You now have:
- Understanding of CKS exam format and domains
- Security lab with essential tools
- Proficiency with Trivy, Falco, kube-bench
- Exam strategy for security tasks

**Next Part**: [Part 1: Cluster Setup](../part1-cluster-setup/module-1.1-network-policies/) - Deep dive into network security.
