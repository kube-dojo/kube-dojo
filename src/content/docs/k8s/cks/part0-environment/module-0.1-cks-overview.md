---
title: "Module 0.1: CKS Exam Overview"
slug: k8s/cks/part0-environment/module-0.1-cks-overview
sidebar:
  order: 1
lab:
  id: cks-0.1-cks-overview
  url: https://killercoda.com/kubedojo/scenario/cks-0.1-cks-overview
  duration: "30 min"
  difficulty: advanced
  environment: kubernetes
---
> **Complexity**: `[QUICK]` - Essential orientation
>
> **Time to Complete**: 20-25 minutes
>
> **Prerequisites**: CKA certification (must have passed CKA at any point — active certification no longer required)

---

## What You'll Be Able to Do

After completing this module, you will be able to:

1. **Explain** the CKS exam format, domains, and passing criteria
2. **Evaluate** your readiness based on CKS prerequisites and domain weights
3. **Design** a study plan that prioritizes high-weight security domains
4. **Compare** CKS scope and difficulty with CKA and other Kubernetes certifications

---

## Why This Module Matters

The CKS (Certified Kubernetes Security Specialist) is the most advanced Kubernetes certification. It requires you to have **passed the CKA** (it no longer needs to be active). This isn't arbitrary gatekeeping—security requires deep operational knowledge first.

You can't secure what you don't understand.

This module sets your expectations, explains what makes CKS different, and maps out your study path.

---

## CKS vs CKA: What Changes

```
┌─────────────────────────────────────────────────────────────┐
│              CKA → CKS PROGRESSION                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  CKA (Kubernetes Administrator)                            │
│  ├── Build and maintain clusters                           │
│  ├── Deploy and manage workloads                           │
│  ├── Troubleshoot failures                                 │
│  └── "Make it work"                                        │
│                                                             │
│            ↓ Foundation for ↓                              │
│                                                             │
│  CKS (Kubernetes Security Specialist)                      │
│  ├── Harden clusters against attack                        │
│  ├── Secure supply chain                                   │
│  ├── Detect and respond to threats                         │
│  └── "Make it secure"                                      │
│                                                             │
│  Key difference:                                           │
│  CKA asks "Does it run?"                                   │
│  CKS asks "Can it be compromised?"                         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Exam Format

| Aspect | Details |
|--------|---------|
| **Duration** | 2 hours (120 minutes) |
| **Format** | Performance-based (CLI tasks) |
| **Questions** | ~15-20 tasks |
| **Passing Score** | 67% |
| **Prerequisite** | CKA certification (passed at any point) |
| **Environment** | Ubuntu-based, kubeadm clusters |
| **Validity** | 2 years |

### Allowed Resources

During the exam, you may access:
- kubernetes.io/docs
- kubernetes.io/blog
- helm.sh/docs
- github.com/kubernetes
- aquasecurity.github.io/trivy (Trivy docs)
- falco.org/docs (Falco docs)

**Note**: Security tool documentation (Trivy, Falco) is explicitly allowed—learn to navigate these docs!

---

## Exam Domains

```
┌─────────────────────────────────────────────────────────────┐
│              CKS DOMAIN WEIGHTS                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Cluster Setup                    ████░░░░░░░░░░░░░░ 10%   │
│  Network policies, CIS benchmarks, ingress security         │
│                                                             │
│  Cluster Hardening                ██████░░░░░░░░░░░░ 15%   │
│  RBAC, ServiceAccounts, API security, upgrades              │
│                                                             │
│  System Hardening                 ██████░░░░░░░░░░░░ 15%   │
│  AppArmor, seccomp, host OS, kernel hardening               │
│                                                             │
│  Microservice Vulnerabilities     ████████░░░░░░░░░░ 20%   │
│  Security contexts, Pod Security, secrets, sandboxing       │
│                                                             │
│  Supply Chain Security            ████████░░░░░░░░░░ 20%   │
│  Image scanning, Trivy, signing, SBOM, static analysis      │
│                                                             │
│  Monitoring & Runtime Security    ████████░░░░░░░░░░ 20%   │
│  Falco, audit logs, immutable containers, incident response │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Where to Focus

**60% of the exam** comes from three domains:
- Microservice Vulnerabilities (20%)
- Supply Chain Security (20%)
- Monitoring & Runtime Security (20%)

These are the "new" security-specific skills. Cluster Setup and Hardening build on CKA knowledge.

---

## Key Security Tools

You must be proficient with these tools:

| Tool | Purpose | Exam Use |
|------|---------|----------|
| **Trivy** | Image vulnerability scanning | Find CVEs in images |
| **Falco** | Runtime threat detection | Write/modify rules |
| **kube-bench** | CIS benchmark checking | Audit cluster security |
| **kubesec** | Manifest static analysis | Score YAML security |
| **AppArmor** | Application access control | Create/apply profiles |
| **seccomp** | System call filtering | Restrict container syscalls |

---

## Security Mindset Shift

```
┌─────────────────────────────────────────────────────────────┐
│              ADMINISTRATOR vs SECURITY THINKING             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Administrator sees:          Security specialist sees:     │
│  ─────────────────────────────────────────────────────────  │
│  "Pod is running"             "Pod runs as root"            │
│  "Service is accessible"      "Service has no NetworkPolicy"│
│  "App deploys successfully"   "Image has 47 CVEs"           │
│  "Cluster is operational"     "API server allows anonymous" │
│  "Secrets are mounted"        "Secrets in plain text in etcd│
│                                                             │
│  Key insight:                                              │
│  Working ≠ Secure                                          │
│  Everything you built in CKA, CKS teaches you to harden    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Curriculum Structure

This curriculum follows the exam domains:

| Part | Domain | Weight | Modules |
|------|--------|--------|---------|
| 0 | Environment Setup | - | Exam prep, lab setup, tools |
| 1 | Cluster Setup | 10% | Network policies, CIS, ingress |
| 2 | Cluster Hardening | 15% | RBAC, ServiceAccounts, API |
| 3 | System Hardening | 15% | AppArmor, seccomp, OS |
| 4 | Microservice Vulnerabilities | 20% | Security contexts, PSA, secrets |
| 5 | Supply Chain Security | 20% | Trivy, signing, SBOM |
| 6 | Runtime Security | 20% | Falco, audit, incidents |

---

## Three-Pass Strategy for CKS

Same strategy as CKA, security-focused:

```
┌─────────────────────────────────────────────────────────────┐
│              CKS THREE-PASS STRATEGY                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  PASS 1: Quick Security Wins (1-3 min each)                │
│  ├── Create NetworkPolicy                                  │
│  ├── Apply existing AppArmor profile                       │
│  ├── Fix obvious RBAC issue                                │
│  ├── Set runAsNonRoot: true                                │
│  └── Enable audit logging                                  │
│                                                             │
│  PASS 2: Tool-Based Tasks (4-6 min each)                   │
│  ├── Scan image with Trivy, fix vulnerabilities            │
│  ├── Create seccomp profile                                │
│  ├── Configure Pod Security Admission                       │
│  └── Run kube-bench, fix findings                          │
│                                                             │
│  PASS 3: Complex Scenarios (7+ min each)                   │
│  ├── Write custom Falco rule                               │
│  ├── Investigate runtime incident                          │
│  ├── Multi-step hardening task                             │
│  └── Complex NetworkPolicy scenarios                       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Did You Know?

- **CKS pass rate is lower than CKA.** The security focus requires new skills beyond administration. Don't underestimate it.

- **Falco was created at Sysdig** and donated to CNCF. It's the de facto standard for Kubernetes runtime security.

- **The biggest CKS challenge isn't Kubernetes**—it's Linux security concepts like AppArmor and seccomp that many candidates haven't used before.

- **Supply chain security became critical** after attacks like SolarWinds and Log4Shell. CKS heavily tests this domain.

---

## Common Mistakes

| Mistake | Why It Hurts | Solution |
|---------|--------------|----------|
| Skipping Linux security basics | AppArmor/seccomp are essential | Learn Linux security fundamentals |
| Only using Trivy for scanning | Must understand and fix CVEs | Practice remediation workflows |
| Ignoring Falco rule syntax | Custom rules are tested | Practice writing rules |
| Not practicing NetworkPolicies | Complex egress/ingress rules | Do many hands-on exercises |
| Assuming CKA skills transfer | Security requires new thinking | Study security specifically |

---

## Quiz

1. **What is the prerequisite for taking the CKS exam?**
   <details>
   <summary>Answer</summary>
   A CKA certification — you must have passed CKA at any point (it no longer needs to be active/unexpired).
   </details>

2. **What percentage of the CKS exam covers runtime security and monitoring?**
   <details>
   <summary>Answer</summary>
   20%. Combined with Supply Chain Security (20%) and Microservice Vulnerabilities (20%), these three domains make up 60% of the exam.
   </details>

3. **What security tool documentation is explicitly allowed during the CKS exam?**
   <details>
   <summary>Answer</summary>
   Trivy (aquasecurity.github.io/trivy) and Falco (falco.org/docs) documentation, in addition to standard Kubernetes docs.
   </details>

4. **Why does the CKS require CKA as a prerequisite?**
   <details>
   <summary>Answer</summary>
   You can't secure what you don't understand. Security requires deep operational knowledge of Kubernetes architecture, networking, and workload management that CKA provides.
   </details>

---

## Hands-On Exercise

**Task**: Explore your current security posture and identify gaps.

```bash
# Step 1: Check if your cluster has basic security features
echo "=== Checking API Server Security ==="
kubectl get pods -n kube-system | grep apiserver
kubectl get pods -n kube-system kube-apiserver-* -o yaml 2>/dev/null | grep -E "enable-admission|audit" | head -5 || echo "Check on control plane node"

# Step 2: Check for NetworkPolicies (most clusters have none by default!)
echo "=== NetworkPolicy Count ==="
kubectl get networkpolicies -A
NETPOL_COUNT=$(kubectl get networkpolicies -A --no-headers 2>/dev/null | wc -l)
echo "Total NetworkPolicies: $NETPOL_COUNT"
if [ "$NETPOL_COUNT" -eq 0 ]; then
  echo "⚠️  No NetworkPolicies! All pods can communicate freely."
fi

# Step 3: Check for pods running as root
echo "=== Pods Running as Root ==="
kubectl get pods -A -o jsonpath='{range .items[*]}{.metadata.namespace}/{.metadata.name}: runAsNonRoot={.spec.securityContext.runAsNonRoot}{"\n"}{end}' | head -10

# Step 4: Check for privileged containers
echo "=== Privileged Containers ==="
kubectl get pods -A -o jsonpath='{range .items[*]}{range .spec.containers[*]}{.name}: privileged={.securityContext.privileged}{"\n"}{end}{end}' 2>/dev/null | grep -v "privileged=$" | head -10

# Step 5: Check Pod Security Admission labels
echo "=== Pod Security Standards ==="
kubectl get namespaces -o jsonpath='{range .items[*]}{.metadata.name}: {.metadata.labels.pod-security\.kubernetes\.io/enforce}{"\n"}{end}' | grep -v ": $"

# Step 6: Identify security improvements needed
echo ""
echo "=== Security Gaps Identified ==="
echo "Review the output above. Common gaps include:"
echo "- No NetworkPolicies (pods can talk to anything)"
echo "- Pods running as root"
echo "- No Pod Security Standards enforced"
echo "- Missing audit logging"
```

**Success criteria**: Understand your cluster's current security gaps and what CKS teaches you to fix.

---

## Summary

**CKS builds on CKA** with security-specific skills:

- **New tools**: Trivy, Falco, kube-bench, kubesec
- **New concepts**: AppArmor, seccomp, supply chain security
- **New mindset**: "Working" is not enough—must be "secure"

**Exam format**:
- 2 hours, ~15-20 tasks
- 67% to pass
- Ubuntu-based kubeadm clusters
- Trivy/Falco docs allowed

**Focus areas** (60% of exam):
- Microservice Vulnerabilities
- Supply Chain Security
- Runtime Security

---

## Next Module

[Module 0.2: Security Lab Setup](../module-0.2-security-lab/) - Build your CKS practice environment with security tools.
