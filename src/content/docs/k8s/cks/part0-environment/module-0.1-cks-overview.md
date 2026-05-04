---
revision_pending: true
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

> **Pause and predict**: Looking at the domain weights above, why do you think Cluster Setup is only 10% while Supply Chain Security and Runtime Security are each 20%? What does this tell you about what the exam values?

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

> **Stop and think**: You have a cluster running in production with workloads deployed. Everything is "working." Now put on your security hat -- what are the first three things you would check to determine if the cluster is actually *secure*?

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

- **Supply chain security became critical** as a heavily tested CKS domain. The track covers two canonical incidents in depth: a [build-system compromise that pushed signed-but-malicious updates to thousands of downstream customers](/prerequisites/modern-devops/module-1.3-cicd-pipelines/) <!-- incident-xref: solarwinds-2020 --> and a [transitive Java logging library vulnerability that exposed any application accepting attacker-controlled input strings](/platform/disciplines/reliability-security/devsecops/module-4.4-supply-chain-security/) <!-- incident-xref: log4shell -->.

---

> **What would happen if**: You walked into the CKS exam and were asked to troubleshoot a Pod that immediately crashes upon startup. If you only apply CKA-level troubleshooting (checking logs, events, and resource limits), what critical CKS-specific security enforcement mechanisms might you completely overlook as the root cause?

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

1. **A colleague's CKA certification expired last month, but they want to register for the CKS exam today to validate their new security skills. They plan to focus exclusively on Kubernetes API resources like NetworkPolicies and RBAC for their preparation. Can they register, and is their study plan technically sound for the CKS?**
   <details>
   <summary>Answer</summary>
   Yes, they can register, as the Linux Foundation now only requires candidates to have passed the CKA at any point in the past, regardless of its current active status. However, their study plan is technically insufficient because it only covers the Cluster Setup and Hardening domains (25% of the exam). To pass the CKS, they must study external security tooling like Falco for runtime detection and Trivy for supply chain scanning. Furthermore, they need hands-on practice with Linux kernel-level security features like AppArmor and seccomp, which operate completely outside standard Kubernetes API resources.
   </details>

2. **You are designing a 4-week CKS study plan for your team and decide to allocate equal time to mastering `kubeadm` cluster setup, RBAC configuration, and Falco runtime rule generation. A senior engineer rejects this plan immediately. Based on the exam structure, why is this time allocation highly inefficient?**
   <details>
   <summary>Answer</summary>
   This allocation is inefficient because it gives equal weight to topics that have vastly different representation on the actual exam. Cluster Setup (which includes `kubeadm` configuration) only accounts for 10% of the exam, and RBAC falls under Cluster Hardening (15%), both of which heavily overlap with existing CKA knowledge. In contrast, Runtime Security (which includes Falco) is worth 20% and introduces completely new concepts like syscall interception and rule syntax. A proper study plan must disproportionately front-load the heavier, net-new domains like Supply Chain, Microservice Vulnerabilities, and Runtime Security to maximize scoring potential.
   </details>

3. **During a high-pressure CKS exam scenario, you are tasked with modifying a Falco macro to detect unauthorized shell spawns in containers. You open `kubernetes.io/docs` to search for the correct macro syntax but cannot find any references. What specific exam environment rule have you misunderstood, and how do you recover?**
   <details>
   <summary>Answer</summary>
   You have misunderstood the boundaries of the allowed documentation, as third-party tools like Falco and Trivy are not documented within the core Kubernetes website. The CKS exam explicitly permits access to specific external domains, including `falco.org/docs` for runtime security and `aquasecurity.github.io/trivy` for vulnerability scanning. To recover, you must navigate directly to the allowed Falco documentation domain to reference the correct macro syntax. Failing to utilize these specific external domains will make completing the heavy 20% Runtime Security domain nearly impossible.
   </details>

4. **An administrator successfully deploys a microservice to a production cluster. The Pod reaches a `Running` state, services are routing traffic, and no errors appear in the logs. However, a security auditor immediately fails the deployment during a CKS-style review. Technically speaking, what invisible vulnerabilities could exist in this perfectly 'working' deployment?**
   <details>
   <summary>Answer</summary>
   A deployment can be completely functional while simultaneously violating critical security boundaries, which is the core distinction between CKA and CKS mindsets. The Pod might be executing with the `privileged: true` flag, allowing containerized processes direct access to host-level kernel capabilities. It could also be lacking a default-deny NetworkPolicy, meaning a compromise of this specific Pod would allow lateral movement to any other Pod in the cluster. Additionally, the underlying container image might contain unpatched critical CVEs that are exploitable remotely, none of which would prevent the container from starting or serving traffic.
   </details>

---

## Hands-On Exercise

**Task**: Explore your current security posture and identify gaps.

```bash
# Step 1: Check if your cluster has basic security features
echo "=== Checking API Server Security ==="
kubectl get pods -n kube-system | grep apiserver
kubectl get pods -n kube-system -l component=kube-apiserver -o yaml 2>/dev/null | grep -E "enable-admission|audit" | head -5 || echo "Check on control plane node"

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