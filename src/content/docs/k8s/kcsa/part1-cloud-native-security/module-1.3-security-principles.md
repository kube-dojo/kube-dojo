---
title: "Module 1.3: Security Principles"
slug: k8s/kcsa/part1-cloud-native-security/module-1.3-security-principles
sidebar:
  order: 4
---
> **Complexity**: `[MEDIUM]` - Foundational concepts
>
> **Time to Complete**: 25-30 minutes
>
> **Prerequisites**: [Module 1.2: Cloud Provider Security](../module-1.2-cloud-provider-security/)

---

## What You'll Be Able to Do

After completing this module, you will be able to:

1. **Explain** core security principles: defense in depth, least privilege, zero trust, and separation of duties
2. **Evaluate** Kubernetes configurations against these principles to identify violations
3. **Assess** which principle applies when analyzing a specific security scenario
4. **Design** security controls that implement multiple principles simultaneously

---

## Why This Module Matters

Security principles are the timeless rules that guide security decisions. Technologies change—containers, Kubernetes, cloud—but these principles remain constant. Understanding them helps you evaluate any security question, even for technologies you've never seen before.

KCSA questions often test whether you can apply these principles to specific scenarios. Knowing the principles gives you a framework for answering even unfamiliar questions.

---

## Core Security Principles

### 1. Defense in Depth

**Never rely on a single security control.**

```
┌─────────────────────────────────────────────────────────────┐
│              DEFENSE IN DEPTH                               │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  SINGLE CONTROL (Fragile)                                  │
│                                                             │
│  Firewall ─────────────────────────────────→ Protected     │
│                                               Resource      │
│  If firewall fails, resource is exposed                    │
│                                                             │
│  ───────────────────────────────────────────────────────── │
│                                                             │
│  LAYERED CONTROLS (Resilient)                              │
│                                                             │
│  Firewall → Network Policy → RBAC → Pod Security → App     │
│                                                   Auth     │
│                                                             │
│  Multiple failures required to reach the resource          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**In Kubernetes context:**

| Layer | Security Control |
|-------|-----------------|
| Cloud | VPC, security groups, IAM |
| Cluster | RBAC, audit logging |
| Network | Network policies, service mesh |
| Workload | Pod Security Standards |
| Container | SecurityContext, capabilities |
| Application | Authentication, authorization |

### 2. Principle of Least Privilege

**Grant only the minimum access needed.**

```
┌─────────────────────────────────────────────────────────────┐
│              LEAST PRIVILEGE                                │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  BAD: Overly permissive                                    │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Role: cluster-admin                                 │  │
│  │  Resources: * (everything)                           │  │
│  │  Verbs: * (all actions)                              │  │
│  │  "Just give them admin so they can do their job"     │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
│  GOOD: Precisely scoped                                    │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Role: deployment-reader                             │  │
│  │  Resources: deployments                              │  │
│  │  Verbs: get, list, watch                             │  │
│  │  Namespace: team-a                                   │  │
│  │  "Grant exactly what's needed, nothing more"         │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Key applications:**

| Area | Least Privilege Example |
|------|------------------------|
| RBAC | Namespace-scoped roles over cluster-wide |
| Capabilities | Drop all, add only needed |
| Network | Deny all, allow specific |
| Service accounts | Dedicated per workload |
| File access | Read-only root filesystem |

### 3. Zero Trust

**Never trust, always verify.**

```
┌─────────────────────────────────────────────────────────────┐
│              ZERO TRUST vs PERIMETER SECURITY               │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  TRADITIONAL (Castle and Moat)                             │
│  ┌────────────────────────────────────────────────┐        │
│  │  FIREWALL                                      │        │
│  │  ┌──────────────────────────────────────────┐ │        │
│  │  │  Inside = Trusted                        │ │        │
│  │  │  All internal traffic allowed            │ │        │
│  │  │  Once inside, move freely               │ │        │
│  │  └──────────────────────────────────────────┘ │        │
│  └────────────────────────────────────────────────┘        │
│  Problem: Attacker inside can access everything            │
│                                                             │
│  ZERO TRUST                                                │
│  ┌────────────────────────────────────────────────┐        │
│  │  Every request verified:                      │        │
│  │  • Who is making the request?                 │        │
│  │  • Is the device compliant?                   │        │
│  │  • Is this request normal for this identity? │        │
│  │  • Encrypt all traffic, internal or not      │        │
│  └────────────────────────────────────────────────┘        │
│  Benefit: Breach of one system doesn't give access to all │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Zero Trust in Kubernetes:**

| Principle | Kubernetes Implementation |
|-----------|--------------------------|
| Verify identity | Strong authentication (OIDC, certificates) |
| Verify authorization | RBAC for every request |
| Assume breach | Network policies (deny by default) |
| Encrypt traffic | TLS everywhere, service mesh |
| Limit blast radius | Namespace isolation |

### 4. Separation of Duties

**No single person should control all aspects of a critical process.**

```
┌─────────────────────────────────────────────────────────────┐
│              SEPARATION OF DUTIES                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  BAD: One person does everything                           │
│                                                             │
│  Developer writes code                                      │
│      ↓                                                      │
│  Same person deploys to production                         │
│      ↓                                                      │
│  Same person approves their own changes                    │
│                                                             │
│  Risk: Malicious or erroneous changes go undetected       │
│                                                             │
│  ───────────────────────────────────────────────────────── │
│                                                             │
│  GOOD: Responsibilities divided                            │
│                                                             │
│  Developer → Code review → Security scan → Approval →     │
│                                           Different        │
│                                           person/team      │
│  deploys                                                   │
│                                                             │
│  Benefit: Checks and balances prevent single point of     │
│  compromise                                                │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

> **Stop and think**: If RBAC only allows additive permissions (no deny rules), how would you prevent a specific user from accessing Secrets in a namespace where they have a broad Role?

### 5. Fail Secure

**When a security control fails, default to a secure state.**

```
┌─────────────────────────────────────────────────────────────┐
│              FAIL SECURE vs FAIL OPEN                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  FAIL OPEN (Dangerous)                                     │
│  ├── If authorization service is down, allow all requests │
│  ├── If network policy controller fails, allow all traffic│
│  └── "Better to be available than secure"                  │
│                                                             │
│  FAIL SECURE (Correct)                                     │
│  ├── If authorization service is down, deny all requests  │
│  ├── If network policy controller fails, block traffic    │
│  └── "Better to be secure than available"                  │
│                                                             │
│  Default deny exemplifies fail secure:                     │
│  - Network policy with no rules = deny all                │
│  - RBAC with no bindings = no access                      │
│  - Pod security admission = reject non-compliant pods     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Security Concepts

### CIA Triad

The three pillars of information security:

```
┌─────────────────────────────────────────────────────────────┐
│                    CIA TRIAD                                │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│                   CONFIDENTIALITY                           │
│                        /\                                   │
│                       /  \                                  │
│                      /    \                                 │
│                     /      \                                │
│                    /   CIA  \                               │
│                   /          \                              │
│                  /____________\                             │
│          INTEGRITY            AVAILABILITY                  │
│                                                             │
│  CONFIDENTIALITY: Only authorized access to data          │
│  • Encryption, access control, authentication              │
│                                                             │
│  INTEGRITY: Data is accurate and unmodified               │
│  • Checksums, digital signatures, audit logs               │
│                                                             │
│  AVAILABILITY: Systems accessible when needed              │
│  • Redundancy, backups, DDoS protection                    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**In Kubernetes:**

| Pillar | Kubernetes Examples |
|--------|-------------------|
| Confidentiality | Secrets encryption, RBAC, network policies |
| Integrity | Image signing, admission control, etcd integrity |
| Availability | Replicas, PDBs, cluster redundancy |

### Attack Surface

The sum of all points where an attacker can try to enter or extract data:

```
┌─────────────────────────────────────────────────────────────┐
│              KUBERNETES ATTACK SURFACE                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  EXTERNAL ATTACK SURFACE                                   │
│  ├── API server endpoint                                   │
│  ├── Ingress controllers                                   │
│  ├── Exposed services (LoadBalancer, NodePort)             │
│  └── SSH to nodes                                          │
│                                                             │
│  INTERNAL ATTACK SURFACE                                   │
│  ├── Pod-to-pod communication                              │
│  ├── Service account tokens                                │
│  ├── Kubernetes API from pods                              │
│  ├── kubelet API                                           │
│  └── etcd access                                           │
│                                                             │
│  MINIMIZE ATTACK SURFACE:                                  │
│  • Disable unused features                                 │
│  • Remove unnecessary packages from images                 │
│  • Use private clusters                                    │
│  • Restrict network access                                 │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

> **Pause and predict**: Consider two compromised pods — one running with a cluster-admin ServiceAccount, and one with a namespace-scoped read-only ServiceAccount. How does the blast radius differ, and what principle explains this?

### Blast Radius

The extent of damage if a component is compromised:

```
┌─────────────────────────────────────────────────────────────┐
│              BLAST RADIUS EXAMPLES                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  LARGE BLAST RADIUS (Bad)                                  │
│  • cluster-admin ServiceAccount                            │
│    → Compromise = full cluster access                      │
│  • Privileged container                                    │
│    → Compromise = node access                              │
│  • Default ServiceAccount with secrets access              │
│    → Compromise = all namespace secrets                    │
│                                                             │
│  SMALL BLAST RADIUS (Good)                                 │
│  • Namespace-scoped ServiceAccount                         │
│    → Compromise = limited to one namespace                 │
│  • Non-privileged, capability-dropped container            │
│    → Compromise = limited to container processes           │
│  • Dedicated ServiceAccount, no secrets access             │
│    → Compromise = minimal impact                           │
│                                                             │
│  GOAL: Minimize blast radius at every layer               │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Applying Principles to Kubernetes

### Example: Securing a Web Application

```
┌─────────────────────────────────────────────────────────────┐
│              PRINCIPLES IN ACTION                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  SCENARIO: Deploy a web app that needs database access     │
│                                                             │
│  DEFENSE IN DEPTH                                          │
│  ├── Cloud: VPC with private subnets                       │
│  ├── Cluster: RBAC for deployment permissions              │
│  ├── Network: Network policy for DB access only            │
│  ├── Pod: Restricted security context                      │
│  └── App: Input validation, prepared statements            │
│                                                             │
│  LEAST PRIVILEGE                                           │
│  ├── ServiceAccount: Only secrets it needs                 │
│  ├── RBAC: Read deployments in its namespace only          │
│  ├── Capabilities: All dropped, none added                 │
│  ├── Network: Egress only to database pod                  │
│  └── Database: User with SELECT only, specific tables      │
│                                                             │
│  ZERO TRUST                                                │
│  ├── mTLS between web app and database                     │
│  ├── Network policy denying all except explicit allow      │
│  ├── Short-lived database credentials                      │
│  └── All API calls authenticated                           │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Did You Know?

- **Defense in depth** comes from military strategy. The Maginot Line's failure (single layer) versus successful layered defenses shows why multiple barriers work.

- **"Least privilege"** was formalized by Jerome Saltzer in 1974. The principle is older than most operating systems in use today.

- **Zero Trust** was first described in 2010 by Forrester Research, but Google's BeyondCorp (2014) made it practical for enterprise scale.

- **The CIA triad** dates back to the 1970s. Despite being 50+ years old, it remains the foundation of information security.

---

## Common Mistakes

| Mistake | Why It Hurts | Solution |
|---------|--------------|----------|
| Single layer of security | One failure exposes everything | Defense in depth |
| "Temporary" admin access | Temporary becomes permanent | Time-bound, scoped access |
| Trusting internal traffic | Assumes perimeter is secure | Zero trust, network policies |
| Fail open for availability | Security disabled when most needed | Fail secure |
| Same credentials everywhere | One compromise = total compromise | Unique, scoped credentials |

---

## Quiz

1. **A Kubernetes cluster has RBAC configured and network policies in place, but all pods run as root with no seccomp profiles. An application vulnerability allows remote code execution inside a container. Walk through how defense in depth would limit the impact compared to having only RBAC.**
   <details>
   <summary>Answer</summary>
   With only RBAC: the attacker has root inside the container and can potentially exploit kernel vulnerabilities for container escape. Once on the host, they can access all pods on that node. With defense in depth: RBAC limits API access, network policies prevent lateral movement to other pods, but running as root and lacking seccomp still leaves the container layer weak. If non-root, read-only filesystem, dropped capabilities, and seccomp were also applied, the attacker would be severely constrained even after gaining code execution — unable to install tools, write to filesystem, or make dangerous system calls. Each layer reduces what the attacker can achieve.
   </details>

2. **During an incident, your authorization webhook service goes down for 10 minutes. Pods that don't need API access continue running normally, but new pod creation requests are failing. Is the cluster exhibiting "fail open" or "fail secure" behavior, and is this the correct response?**
   <details>
   <summary>Answer</summary>
   This is fail-secure behavior — when the authorization service is unavailable, requests are denied rather than allowed. This is the correct response because failing open would allow unauthenticated or unauthorized requests during the outage, which could be exploited by an attacker who intentionally caused the outage. The trade-off is temporary operational impact (can't create new pods), but existing workloads are unaffected. This demonstrates why fail-secure is preferred for security controls: availability of the authorization service is an operational concern, while failing open is a security vulnerability.
   </details>

3. **A developer needs temporary access to production secrets to debug an issue. The team lead suggests adding them to a group with permanent "get secrets" access. Which security principles does this violate, and what's a better approach?**
   <details>
   <summary>Answer</summary>
   This violates least privilege (permanent access exceeds what's needed for a temporary task), separation of duties (the developer shouldn't have standing production access), and creates a large blast radius (if their credentials are compromised, all secrets are exposed). Better approach: use time-bound access through a tool like Teleport or a custom approval workflow that grants a temporary RoleBinding with an expiration, requires approval from a second person (separation of duties), and is logged for audit. The access should be scoped to the specific secrets needed, not all secrets in the namespace.
   </details>

4. **Your cluster uses "deny all" default network policies in every namespace. A new monitoring tool is deployed and can't scrape metrics from pods in other namespaces. The team wants to create a blanket "allow all from monitoring namespace" rule. Evaluate this against security principles.**
   <details>
   <summary>Answer</summary>
   A blanket allow-all rule from the monitoring namespace violates least privilege — the monitoring tool only needs access to specific metrics ports (e.g., port 9090 for Prometheus), not all ports on all pods. It also violates defense in depth by creating an overly broad exception that an attacker who compromises the monitoring namespace could exploit for full cluster network access. The correct approach: create network policies that allow ingress only on the metrics port, only from pods with the monitoring label, in each namespace. This follows the principle of minimal, specific access rather than broad exceptions.
   </details>

5. **The CIA triad includes Confidentiality, Integrity, and Availability. A pod running without resource limits can consume all CPU on a node, starving other pods. Which pillar of the CIA triad is violated, and what Kubernetes controls address it?**
   <details>
   <summary>Answer</summary>
   Availability is violated — other pods on the node can't get the CPU resources they need to serve requests. Kubernetes controls: resource limits (spec.containers[].resources.limits) cap how much CPU/memory a container can use; ResourceQuotas limit total resource consumption per namespace; LimitRanges set default limits for pods that don't specify them; PodDisruptionBudgets protect minimum replica counts. Together, these ensure no single workload can monopolize node resources, maintaining availability for all workloads. This is also a denial-of-service concern from a security perspective — a compromised pod could intentionally consume resources.
   </details>
---

## Hands-On Exercise: Principle Application

**Scenario**: Review this configuration and identify which security principle each violates:

```yaml
# Configuration 1
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: dev-access
subjects:
- kind: Group
  name: developers
roleRef:
  kind: ClusterRole
  name: cluster-admin
---
# Configuration 2
apiVersion: v1
kind: Pod
metadata:
  name: web-app
spec:
  containers:
  - name: app
    image: webapp:latest
    securityContext:
      privileged: true
---
# Configuration 3
# Network policy: none defined
# All pods can communicate with all other pods
```

**Identify the violated principle for each:**

<details>
<summary>Answers</summary>

**Configuration 1 - Violates Least Privilege**
- Developers have cluster-admin (full cluster access)
- Should have namespace-scoped roles with specific permissions

**Configuration 2 - Violates Defense in Depth and Least Privilege**
- Privileged mode grants full host access
- Massive blast radius if compromised
- Should run non-privileged with minimal capabilities

**Configuration 3 - Violates Zero Trust and Defense in Depth**
- All pod-to-pod traffic allowed by default
- Trusts internal network
- Should have default-deny network policies

</details>

---

## Summary

Security principles guide all security decisions:

| Principle | Core Idea | Kubernetes Example |
|-----------|-----------|-------------------|
| **Defense in Depth** | Multiple layers | RBAC + Network Policy + PSS |
| **Least Privilege** | Minimum access | Scoped roles, dropped capabilities |
| **Zero Trust** | Never trust, verify | mTLS, network policies |
| **Separation of Duties** | Divided responsibility | Different approvers for production |
| **Fail Secure** | Safe defaults | Default deny network policies |

Key concepts:
- **CIA Triad**: Confidentiality, Integrity, Availability
- **Attack Surface**: Minimize entry points
- **Blast Radius**: Limit damage from compromise

---

## Next Module

[Module 2.1: Control Plane Security](../part2-cluster-component-security/module-2.1-control-plane-security/) - Securing the Kubernetes control plane components.
