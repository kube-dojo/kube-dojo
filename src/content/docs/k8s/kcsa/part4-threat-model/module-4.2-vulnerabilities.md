---
title: "Module 4.2: Common Vulnerabilities"
slug: k8s/kcsa/part4-threat-model/module-4.2-vulnerabilities
sidebar:
  order: 3
---
> **Complexity**: `[MEDIUM]` - Threat awareness
>
> **Time to Complete**: 25-30 minutes
>
> **Prerequisites**: [Module 4.1: Attack Surfaces](../module-4.1-attack-surfaces/)

---

## What You'll Be Able to Do

After completing this module, you will be able to:

1. **Identify** common Kubernetes vulnerability categories: CVEs, misconfigurations, and insecure defaults
2. **Assess** vulnerability severity using CVSS scores and exploitability context
3. **Evaluate** the difference between code vulnerabilities and configuration vulnerabilities
4. **Explain** mitigation strategies for the most common Kubernetes vulnerability patterns

---

## Why This Module Matters

Understanding common vulnerabilities helps you anticipate attacks and prioritize defenses. Kubernetes vulnerabilities come in two forms: code vulnerabilities (CVEs) and misconfigurations. Both can lead to cluster compromise, but misconfigurations are far more common.

KCSA tests your awareness of common vulnerability patterns and their mitigations.

---

## Vulnerability Categories

```
┌─────────────────────────────────────────────────────────────┐
│              KUBERNETES VULNERABILITY TYPES                 │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  CVEs (Code Vulnerabilities)                               │
│  • Bugs in Kubernetes, container runtime, or dependencies  │
│  • Require patching to fix                                 │
│  • Tracked with CVE identifiers                            │
│  • Examples: runc escape, API server bypass                │
│                                                             │
│  MISCONFIGURATIONS                                         │
│  • Insecure settings in your cluster                       │
│  • Fixed by configuration changes                          │
│  • Most common vulnerability type                          │
│  • Examples: privileged pods, exposed secrets              │
│                                                             │
│  INSECURE DEFAULTS                                         │
│  • Default settings that aren't secure                     │
│  • Require proactive hardening                             │
│  • Examples: anonymous auth, no network policies           │
│                                                             │
│  SUPPLY CHAIN                                              │
│  • Vulnerabilities in images or dependencies               │
│  • Inherited from upstream sources                         │
│  • Examples: vulnerable base images, malicious packages    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Notable Kubernetes CVEs

### Container Escape CVEs

```
┌─────────────────────────────────────────────────────────────┐
│              CONTAINER ESCAPE VULNERABILITIES               │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  CVE-2019-5736 (runc)                                      │
│  ├── Impact: Container escape via malicious image          │
│  ├── Attack: Overwrite host runc binary                    │
│  ├── Affected: Docker, containerd, CRI-O                   │
│  └── Fix: Update runc                                      │
│                                                             │
│  CVE-2020-15257 (containerd)                               │
│  ├── Impact: Container escape via API                      │
│  ├── Attack: Access containerd-shim API socket             │
│  ├── Affected: containerd before 1.4.3                     │
│  └── Fix: Update containerd                                │
│                                                             │
│  CVE-2022-0811 (CRI-O)                                     │
│  ├── Impact: Container escape via kernel parameters        │
│  ├── Attack: Set kernel.core_pattern to escape             │
│  ├── Affected: CRI-O                                       │
│  └── Fix: Update CRI-O                                     │
│                                                             │
│  LESSON: Container runtimes are critical security layer    │
│  Keep them updated!                                        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

> **Stop and think**: CVE-2019-5736 affected runc — the container runtime used by Docker, containerd, and CRI-O. If your cluster uses containerd, does patching Kubernetes itself fix this vulnerability? What component actually needs updating?

### Kubernetes Core CVEs

```
┌─────────────────────────────────────────────────────────────┐
│              KUBERNETES API/AUTHZ CVEs                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  CVE-2018-1002105 (Privilege Escalation)                   │
│  ├── Impact: Any user → cluster-admin                      │
│  ├── Attack: Upgrade API connection to backend             │
│  ├── Severity: Critical (9.8)                              │
│  └── Fix: Kubernetes 1.10.11, 1.11.5, 1.12.3              │
│                                                             │
│  CVE-2020-8554 (MITM via LoadBalancer)                     │
│  ├── Impact: Intercept traffic to external IPs             │
│  ├── Attack: Create service with ExternalIP                │
│  ├── Severity: Medium                                      │
│  └── Fix: Restrict ExternalIP via admission                │
│                                                             │
│  CVE-2021-25741 (Symlink Attack)                           │
│  ├── Impact: Access files outside volume                   │
│  ├── Attack: Symlink in subPath mount                      │
│  ├── Affected: All Kubernetes before fix                   │
│  └── Fix: Update Kubernetes                                │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Common Misconfigurations

### RBAC Misconfigurations

```
┌─────────────────────────────────────────────────────────────┐
│              RBAC MISCONFIGURATIONS                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  EXCESSIVE PERMISSIONS                                     │
│  ├── Issue: Wildcards (*) in roles                         │
│  ├── Risk: Access to unintended resources                  │
│  └── Fix: Specify exact resources and verbs                │
│                                                             │
│  CLUSTER-WIDE WHEN NAMESPACE ENOUGH                        │
│  ├── Issue: ClusterRoleBinding for namespaced access       │
│  ├── Risk: Access to all namespaces                        │
│  └── Fix: Use RoleBinding with namespace scope             │
│                                                             │
│  BINDING TO DEFAULT SERVICE ACCOUNT                        │
│  ├── Issue: Roles bound to default SA                      │
│  ├── Risk: All pods in namespace get permissions           │
│  └── Fix: Create dedicated ServiceAccounts                 │
│                                                             │
│  DANGEROUS PERMISSIONS                                     │
│  ├── create pods → Can create privileged pods              │
│  ├── get secrets → Can read all secrets in scope           │
│  ├── impersonate → Can act as any user                     │
│  └── Fix: Audit and restrict these permissions             │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Pod Security Misconfigurations

```
┌─────────────────────────────────────────────────────────────┐
│              POD SECURITY MISCONFIGURATIONS                 │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  PRIVILEGED CONTAINERS                                     │
│  privileged: true                                          │
│  └── Impact: Full host access, easy container escape       │
│                                                             │
│  HOST NAMESPACE SHARING                                    │
│  hostPID: true, hostNetwork: true, hostIPC: true          │
│  └── Impact: See host processes, network, IPC             │
│                                                             │
│  DANGEROUS CAPABILITIES                                    │
│  capabilities: { add: [SYS_ADMIN, SYS_PTRACE] }           │
│  └── Impact: Near-root privileges                         │
│                                                             │
│  RUNNING AS ROOT                                           │
│  runAsUser: 0, runAsNonRoot: false                        │
│  └── Impact: Higher privilege if exploited                │
│                                                             │
│  WRITABLE ROOT FILESYSTEM                                  │
│  readOnlyRootFilesystem: false                            │
│  └── Impact: Attacker can persist changes                 │
│                                                             │
│  SENSITIVE HOST PATHS                                      │
│  hostPath: { path: /etc, path: /var/run/docker.sock }     │
│  └── Impact: Host filesystem access, container escape     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Network Misconfigurations

```
┌─────────────────────────────────────────────────────────────┐
│              NETWORK MISCONFIGURATIONS                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  NO NETWORK POLICIES                                       │
│  ├── Default: All pods can reach all pods                  │
│  ├── Risk: Lateral movement after compromise               │
│  └── Fix: Implement default deny + explicit allow          │
│                                                             │
│  EXPOSED API SERVER                                        │
│  ├── Issue: Public API server endpoint                     │
│  ├── Risk: Direct attacks, credential stuffing             │
│  └── Fix: Private endpoint, VPN access                     │
│                                                             │
│  UNNECESSARY SERVICE EXPOSURE                              │
│  ├── Issue: NodePort/LoadBalancer for internal services    │
│  ├── Risk: Expanded attack surface                         │
│  └── Fix: Use ClusterIP, ingress for external              │
│                                                             │
│  NO EGRESS CONTROL                                         │
│  ├── Issue: Pods can reach any external endpoint           │
│  ├── Risk: Data exfiltration, C2 communication             │
│  └── Fix: Egress network policies                          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

> **Pause and predict**: Your vulnerability scanner reports 150 CVEs in a container image: 2 Critical, 8 High, 40 Medium, 100 Low. Management wants all 150 fixed before deployment. Is this realistic, and how would you prioritize?

## Vulnerability Scoring (CVSS)

```
┌─────────────────────────────────────────────────────────────┐
│              CVSS SCORING                                   │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  CVSS (Common Vulnerability Scoring System)                │
│  Standard method to rate vulnerability severity            │
│                                                             │
│  SCORE RANGES:                                             │
│  ├── 0.0       - None                                      │
│  ├── 0.1-3.9   - Low                                       │
│  ├── 4.0-6.9   - Medium                                    │
│  ├── 7.0-8.9   - High                                      │
│  └── 9.0-10.0  - Critical                                  │
│                                                             │
│  FACTORS CONSIDERED:                                       │
│  ├── Attack Vector (Network/Adjacent/Local/Physical)       │
│  ├── Attack Complexity (Low/High)                          │
│  ├── Privileges Required (None/Low/High)                   │
│  ├── User Interaction (None/Required)                      │
│  ├── Scope (Unchanged/Changed)                             │
│  ├── Impact (Confidentiality/Integrity/Availability)       │
│  └── Base/Temporal/Environmental scores                    │
│                                                             │
│  USE FOR PRIORITIZATION:                                   │
│  Critical/High → Immediate action                          │
│  Medium → Plan remediation                                 │
│  Low → Address in regular cycles                           │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Vulnerability Discovery

### Tools for Finding Vulnerabilities

| Tool | Purpose |
|------|---------|
| **Trivy** | Container image scanning |
| **Grype** | Container image scanning |
| **kube-bench** | CIS benchmark checks |
| **kubeaudit** | Security auditing |
| **Falco** | Runtime threat detection |
| **Polaris** | Best practice validation |
| **OPA/Gatekeeper** | Policy enforcement |

### Example: kube-bench Output

```
[INFO] 1 Control Plane Security Configuration
[PASS] 1.1.1 Ensure API server pod file permissions (score)
[FAIL] 1.1.2 Ensure API server pod file ownership (score)
[WARN] 1.2.1 Ensure anonymous-auth is not disabled (info)
...

== Summary ==
45 checks PASS
10 checks FAIL
5 checks WARN
```

---

## Vulnerability Response

```
┌─────────────────────────────────────────────────────────────┐
│              VULNERABILITY RESPONSE PROCESS                 │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. IDENTIFY                                               │
│     • CVE announcements                                    │
│     • Scanning tools                                       │
│     • Security advisories                                  │
│                                                             │
│  2. ASSESS                                                 │
│     • Does it affect my environment?                       │
│     • What's the severity (CVSS)?                          │
│     • Is it being exploited?                               │
│                                                             │
│  3. PRIORITIZE                                             │
│     • Critical + Active exploit → Immediate                │
│     • High + Public exploit → Days                         │
│     • Medium → Weeks                                       │
│     • Low → Regular patch cycle                            │
│                                                             │
│  4. REMEDIATE                                              │
│     • Patch/upgrade if available                           │
│     • Mitigate if patch unavailable                        │
│     • Accept risk with documentation                       │
│                                                             │
│  5. VERIFY                                                 │
│     • Confirm fix applied                                  │
│     • Re-scan for vulnerability                            │
│     • Update documentation                                 │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Did You Know?

- **Most breaches are from misconfigurations**, not zero-days. Fixing configs is often more impactful than chasing CVEs.

- **The average container image has 100+ vulnerabilities**. Prioritization is essential—you can't fix everything.

- **CVE-2018-1002105** was a critical Kubernetes vulnerability that allowed any authenticated user to become cluster-admin. It's why keeping Kubernetes updated matters.

- **Distroless images** have 50-90% fewer CVEs than traditional base images like Ubuntu or Alpine.

---

## Common Mistakes

| Mistake | Why It Hurts | Solution |
|---------|--------------|----------|
| Ignoring critical CVEs | Exploitation risk | Patch critical immediately |
| Scanning but not fixing | False sense of security | Track remediation |
| Only scanning images | Misses runtime issues | Add config scanning |
| No vulnerability SLA | Inconsistent response | Define response times |
| Patching without testing | May break applications | Test in staging first |

---

## Quiz

1. **A vulnerability scan reports CVE-2019-5736 (runc container escape, CVSS 8.6) on your nodes, and separately a misconfiguration finding that 40% of pods run as root. Your team can only address one this week. Which should you prioritize and why?**
   <details>
   <summary>Answer</summary>
   Prioritize the runc CVE first. While misconfigurations are more common, CVE-2019-5736 enables container escape through a malicious image — an attacker can overwrite the host runc binary and gain root on the node. It affects the container runtime itself, meaning all containers on affected nodes are vulnerable regardless of their security settings. The root-running pods are concerning but require an additional exploit to cause harm beyond the container. Fix order: patch runc immediately (runtime update, not Kubernetes update), then address the root container misconfiguration by enforcing Pod Security Standards.
   </details>

2. **Your kube-bench scan shows 10 FAIL findings. Three are authentication issues (anonymous auth enabled), four are file permission problems, and three are missing audit configurations. A colleague says "fix all 10 this weekend." Why might a staged approach be safer?**
   <details>
   <summary>Answer</summary>
   Changing authentication settings (disabling anonymous auth) could break workloads that unknowingly rely on anonymous access, monitoring systems, or health check endpoints. Applying all changes simultaneously means if something breaks, you can't identify which change caused it. Staged approach: (1) Enable audit logging first — this is additive and won't break anything; (2) Fix file permissions — low risk, immediate security improvement; (3) Disable anonymous auth during a maintenance window after verifying no workloads depend on it by enabling audit logging first to see what anonymous requests exist. Test each change in a staging environment first. This demonstrates that vulnerability remediation requires operational planning, not just security urgency.
   </details>

3. **A container image scan reveals a Critical CVE in OpenSSL, but the application inside the container is written in Go and doesn't use OpenSSL at all. The library was included by the base image. Should this block deployment?**
   <details>
   <summary>Answer</summary>
   It depends on context. If the vulnerable OpenSSL is installed but never loaded by any process in the container, the exploitability is very low — the CVSS base score doesn't account for whether the library is actually reachable. However, it should still be addressed because: an attacker who gains code execution might use the vulnerable library, a future application change might introduce OpenSSL usage, and audit compliance often doesn't distinguish unused vulnerabilities. Best approach: use a minimal base image (distroless, scratch) that doesn't include OpenSSL at all — this eliminates the finding entirely. Don't block deployment, but track it and rebuild with a patched base image within the defined SLA.
   </details>

4. **CVE-2018-1002105 allowed any authenticated user to escalate to cluster-admin through the API server. Your cluster is on a version that's affected. You can't upgrade immediately due to application compatibility concerns. What short-term mitigations could reduce the risk?**
   <details>
   <summary>Answer</summary>
   Short-term mitigations: (1) Restrict who can authenticate — remove unnecessary user accounts, audit all ClusterRoleBindings, and limit the number of authenticated users who could exploit this; (2) Enable and monitor audit logging to detect exploitation attempts; (3) Make the API server private (VPN/bastion only) to reduce who can reach it; (4) Use network policies to restrict pod access to the API server; (5) Disable the aggregation layer if not in use (the vulnerability exploited API aggregation). These reduce likelihood while you plan the upgrade. However, for a CVSS 9.8 vulnerability with a public exploit, the upgrade should be prioritized over application compatibility — the risk of cluster compromise outweighs the risk of temporary application disruption.
   </details>

5. **Your organization has both a vulnerability scanning tool (Trivy) and a configuration auditing tool (kube-bench). Explain what each tool catches that the other misses, and why you need both.**
   <details>
   <summary>Answer</summary>
   Trivy scans container images for CVEs in OS packages and language dependencies — it finds code vulnerabilities like Log4Shell, OpenSSL flaws, and vulnerable libraries. It misses cluster configuration issues entirely. kube-bench checks Kubernetes cluster configuration against CIS Benchmarks — it finds misconfigurations like anonymous auth enabled, missing audit logging, and kubelet insecure settings. It doesn't scan container images at all. Together they cover both categories: Trivy protects against "what you're deploying" vulnerabilities, while kube-bench protects against "how your cluster is configured" vulnerabilities. Most breaches involve misconfigurations (kube-bench territory) but the highest-impact incidents involve code vulnerabilities (Trivy territory). Both are essential layers in defense in depth.
   </details>

---

## Hands-On Exercise: Vulnerability Assessment

**Scenario**: You receive this vulnerability scan report. Prioritize the findings:

```
CRITICAL: CVE-2019-5736 in runc (container escape)
HIGH:     Privileged containers in production namespace
HIGH:     CVE-2021-44228 (Log4Shell) in app image
MEDIUM:   No network policies defined
MEDIUM:   Default ServiceAccount token mounted
LOW:      Container image using :latest tag
LOW:      CVE-2020-XXXX in unused library
```

**Rank them by priority and explain:**

<details>
<summary>Prioritization</summary>

1. **CVE-2019-5736 (CRITICAL)** - Container escape, active exploitation
   - Fix: Update runc immediately
   - Impact: Container escape to host

2. **CVE-2021-44228 Log4Shell (HIGH)** - Remote code execution
   - Fix: Update app image urgently
   - Impact: RCE in container

3. **Privileged containers (HIGH)** - Misconfiguration
   - Fix: Remove privileged flag, use specific capabilities
   - Impact: Easy container escape if compromised

4. **No network policies (MEDIUM)** - Misconfiguration
   - Fix: Implement default deny + explicit allow
   - Impact: Lateral movement possible

5. **Default SA token (MEDIUM)** - Misconfiguration
   - Fix: Disable automount, use dedicated SAs
   - Impact: API access from compromised pod

6. **:latest tag (LOW)** - Best practice violation
   - Fix: Use immutable tags with digests
   - Impact: Unpredictable versions

7. **Unused library CVE (LOW)** - Low impact
   - Fix: Remove unused dependency
   - Impact: Minimal (library unused)

</details>

---

## Summary

Kubernetes vulnerabilities come in multiple forms:

| Type | Examples | Response |
|------|----------|----------|
| **Critical CVEs** | runc escape, K8s priv esc | Immediate patching |
| **High CVEs** | Log4Shell, API bypasses | Urgent patching |
| **Misconfigurations** | Privileged pods, no RBAC | Configuration fixes |
| **Insecure Defaults** | Anonymous auth, no policies | Proactive hardening |

Key practices:
- Scan regularly (images, configs, runtime)
- Prioritize by severity and exploitability
- Fix misconfigurations—they're the most common issue
- Keep components updated
- Have a defined vulnerability response process

---

## Next Module

[Module 4.3: Container Escape](../module-4.3-container-escape/) - Understanding and preventing container breakout scenarios.
