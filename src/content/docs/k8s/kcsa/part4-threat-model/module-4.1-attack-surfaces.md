---
title: "Module 4.1: Attack Surfaces"
slug: k8s/kcsa/part4-threat-model/module-4.1-attack-surfaces
sidebar:
  order: 2
---
> **Complexity**: `[MEDIUM]` - Threat awareness
>
> **Time to Complete**: 25-30 minutes
>
> **Prerequisites**: [Module 3.5: Network Policies](../part3-security-fundamentals/module-3.5-network-policies/)

---

## What You'll Be Able to Do

After completing this module, you will be able to:

1. **Identify** Kubernetes attack surfaces across API server, kubelet, etcd, and container runtime
2. **Evaluate** which attack vectors pose the highest risk in a given cluster configuration
3. **Assess** external vs. internal threat actors and their likely entry points
4. **Design** attack surface reduction strategies by disabling unnecessary endpoints and features

---

## Why This Module Matters

To defend a system, you must understand how it can be attacked. The attack surface is the sum of all points where an attacker can try to enter or extract data. Kubernetes has a large attack surface due to its complexity—understanding it helps you prioritize security efforts.

Threat modeling is a core security skill, and KCSA tests your ability to identify and assess attack vectors.

---

## What is an Attack Surface?

```
┌─────────────────────────────────────────────────────────────┐
│              ATTACK SURFACE DEFINITION                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Attack Surface = All entry points an attacker can target  │
│                                                             │
│  LARGER ATTACK SURFACE:                                    │
│  • More exposed services                                   │
│  • More open ports                                         │
│  • More users with access                                  │
│  • More complex configurations                             │
│  = More opportunities for attackers                        │
│                                                             │
│  SMALLER ATTACK SURFACE:                                   │
│  • Minimal exposed services                                │
│  • Restricted network access                               │
│  • Few privileged users                                    │
│  • Simple, hardened configurations                         │
│  = Fewer opportunities for attackers                       │
│                                                             │
│  GOAL: Minimize attack surface while maintaining function  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Kubernetes Attack Surfaces

```
┌─────────────────────────────────────────────────────────────┐
│              KUBERNETES ATTACK SURFACE MAP                  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  EXTERNAL ATTACK SURFACE (from outside cluster)            │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  • Kubernetes API server                            │   │
│  │  • Ingress/Load Balancers                           │   │
│  │  • NodePort services                                │   │
│  │  • SSH to nodes                                     │   │
│  │  • Cloud provider APIs                              │   │
│  │  • Container registries                             │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  INTERNAL ATTACK SURFACE (from inside cluster)             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  • Pod-to-pod networking                            │   │
│  │  • Kubernetes API (from pods)                       │   │
│  │  • kubelet API                                      │   │
│  │  • etcd                                             │   │
│  │  • Service account tokens                           │   │
│  │  • Secrets                                          │   │
│  │  • Host filesystem (if mounted)                     │   │
│  │  • Container runtime                                │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  SUPPLY CHAIN ATTACK SURFACE                               │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  • Container images                                 │   │
│  │  • Base images                                      │   │
│  │  • Application dependencies                         │   │
│  │  • CI/CD pipelines                                  │   │
│  │  • Helm charts/manifests                            │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## External Attack Surface

### API Server Exposure

```
┌─────────────────────────────────────────────────────────────┐
│              API SERVER ATTACK SURFACE                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  PUBLIC API SERVER                                         │
│  • Accessible from internet                                │
│  • Target for brute force                                  │
│  • Target for credential stuffing                          │
│  • Vulnerable to API exploits                              │
│                                                             │
│  ATTACK SCENARIOS:                                         │
│  1. Stolen credentials → Full cluster access               │
│  2. Anonymous auth enabled → Information disclosure        │
│  3. API vulnerability → Remote code execution              │
│  4. RBAC misconfiguration → Privilege escalation           │
│                                                             │
│  MITIGATIONS:                                              │
│  • Private API endpoint (VPN/bastion required)             │
│  • Strong authentication (OIDC, certificates)              │
│  • Disable anonymous auth                                  │
│  • Network firewall rules                                  │
│  • API audit logging                                       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Ingress Attack Surface

```
┌─────────────────────────────────────────────────────────────┐
│              INGRESS ATTACK SURFACE                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  WHAT'S EXPOSED:                                           │
│  • Ingress controller (nginx, traefik, etc.)               │
│  • Backend applications through ingress                    │
│  • TLS termination point                                   │
│                                                             │
│  ATTACK SCENARIOS:                                         │
│  1. Ingress controller vulnerability                       │
│  2. Application vulnerabilities (OWASP Top 10)             │
│  3. Misrouted traffic (host header attacks)                │
│  4. TLS/certificate issues                                 │
│  5. Path traversal to unintended backends                  │
│                                                             │
│  MITIGATIONS:                                              │
│  • Keep ingress controller updated                         │
│  • WAF (Web Application Firewall)                          │
│  • Strict ingress rules                                    │
│  • Strong TLS configuration                                │
│  • Rate limiting                                           │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Internal Attack Surface

### From a Compromised Pod

```
┌─────────────────────────────────────────────────────────────┐
│              POD-LEVEL ATTACK SURFACE                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  SCENARIO: Attacker compromises application in pod         │
│                                                             │
│  WHAT THEY CAN ACCESS:                                     │
│                                                             │
│  ALWAYS AVAILABLE:                                         │
│  ├── Container filesystem                                  │
│  ├── Environment variables (may contain secrets)           │
│  ├── Mounted volumes                                       │
│  └── Network (all pods by default)                         │
│                                                             │
│  IF TOKEN MOUNTED (default):                               │
│  ├── Kubernetes API access                                 │
│  ├── Service account permissions                           │
│  └── Secrets accessible via RBAC                           │
│                                                             │
│  IF MISCONFIGURED:                                         │
│  ├── privileged: true → Host access                        │
│  ├── hostPath mounts → Host filesystem                     │
│  ├── hostNetwork → Host network                            │
│  ├── hostPID → Host processes                              │
│  └── Excessive RBAC → Cluster compromise                   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Kubelet Attack Surface

```
┌─────────────────────────────────────────────────────────────┐
│              KUBELET ATTACK SURFACE                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  KUBELET API (port 10250)                                  │
│  • /exec - Execute commands in containers                  │
│  • /run - Run commands                                     │
│  • /pods - List pods                                       │
│  • /logs - Read logs                                       │
│                                                             │
│  ATTACK SCENARIOS:                                         │
│  1. Anonymous kubelet access → Execute in any container    │
│  2. Node compromise → Kubelet credentials stolen           │
│  3. Network access to kubelet → Bypass API server auth     │
│                                                             │
│  MITIGATIONS:                                              │
│  • Disable anonymous auth                                  │
│  • Disable read-only port (10255)                          │
│  • Network isolation for kubelet                           │
│  • Node authorization mode                                 │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Attack Surface by Actor

```
┌─────────────────────────────────────────────────────────────┐
│              THREAT ACTORS                                  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  EXTERNAL ATTACKER                                         │
│  • No initial access                                       │
│  • Targets: Exposed services, stolen credentials           │
│  • Goal: Initial foothold                                  │
│                                                             │
│  COMPROMISED POD                                           │
│  • Limited container access                                │
│  • Targets: Other pods, secrets, API, container escape     │
│  • Goal: Lateral movement, escalation                      │
│                                                             │
│  MALICIOUS INSIDER                                         │
│  • Legitimate credentials                                  │
│  • Targets: Abuse permissions, plant backdoors             │
│  • Goal: Data theft, persistence                           │
│                                                             │
│  SUPPLY CHAIN ATTACKER                                     │
│  • Compromises trusted components                          │
│  • Targets: Images, dependencies, CI/CD                    │
│  • Goal: Widespread compromise                             │
│                                                             │
│  EACH ACTOR HAS DIFFERENT ATTACK SURFACE                   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Reducing Attack Surface

### Principle: Minimize Exposure

```
┌─────────────────────────────────────────────────────────────┐
│              ATTACK SURFACE REDUCTION                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  NETWORK                                                   │
│  ☐ Private API server endpoint                             │
│  ☐ Network policies (default deny)                         │
│  ☐ No unnecessary NodePort/LoadBalancer services           │
│  ☐ Firewall rules for node access                          │
│                                                             │
│  AUTHENTICATION                                            │
│  ☐ Disable anonymous auth (API server, kubelet)            │
│  ☐ Short-lived credentials                                 │
│  ☐ Strong authentication (MFA, certificates)               │
│                                                             │
│  WORKLOADS                                                 │
│  ☐ No privileged containers                                │
│  ☐ No host namespace sharing                               │
│  ☐ Read-only root filesystem                               │
│  ☐ Disable service account token mounting                  │
│  ☐ Minimal container images                                │
│                                                             │
│  NODES                                                     │
│  ☐ Minimal OS (Bottlerocket, Flatcar)                      │
│  ☐ Disable SSH if possible                                 │
│  ☐ Regular patching                                        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Did You Know?

- **The median time to detect a breach** in cloud environments is over 200 days. Attack surface reduction means fewer places to hide.

- **70% of breaches** involve lateral movement after initial access. Reducing internal attack surface is as important as perimeter security.

- **Container images average 400+ packages** - each is part of your attack surface. Minimal images dramatically reduce exposure.

- **The Kubernetes API server** is one of the most common targets because it provides direct cluster access.

---

## Common Mistakes

| Mistake | Why It Hurts | Solution |
|---------|--------------|----------|
| Public API server | Direct attack target | Private endpoint + VPN |
| Default ServiceAccount tokens | Unnecessary API access | Disable auto-mounting |
| Allow-all network policies | Full lateral movement | Default deny |
| Privileged pods | Host compromise possible | Pod Security Standards |
| Fat container images | Large attack surface | Minimal/distroless images |

---

## Quiz

1. **What constitutes the external attack surface of a Kubernetes cluster?**
   <details>
   <summary>Answer</summary>
   Entry points accessible from outside the cluster: API server, ingress controllers, LoadBalancer services, NodePort services, SSH access to nodes, and any other externally exposed endpoints.
   </details>

2. **Why is the kubelet API a significant attack surface?**
   <details>
   <summary>Answer</summary>
   The kubelet API allows executing commands in containers, reading logs, and listing pods. If not properly secured (anonymous auth disabled, network restricted), it can be exploited to control any container on the node.
   </details>

3. **How does a compromised pod typically expand its attack surface?**
   <details>
   <summary>Answer</summary>
   By accessing the ServiceAccount token to query the Kubernetes API, scanning the network for other services, reading mounted secrets/volumes, and if misconfigured, escaping to the host through privileged settings.
   </details>

4. **What's the difference between external and internal attack surfaces?**
   <details>
   <summary>Answer</summary>
   External attack surface is what's accessible from outside the cluster (internet-facing). Internal attack surface is what's accessible from within the cluster (pod-to-pod, API from pods). Both need protection.
   </details>

5. **Why do minimal container images reduce attack surface?**
   <details>
   <summary>Answer</summary>
   Fewer packages mean fewer potential vulnerabilities, fewer tools for attackers to use if they compromise the container, and less complexity to audit and patch.
   </details>

---

## Hands-On Exercise: Attack Surface Assessment

**Scenario**: Review this cluster configuration and identify attack surface concerns:

```yaml
# API Server flags
--anonymous-auth=true
--authorization-mode=AlwaysAllow

# Kubelet config
authentication:
  anonymous:
    enabled: true
readOnlyPort: 10255

# Sample pod
apiVersion: v1
kind: Pod
spec:
  hostNetwork: true
  hostPID: true
  containers:
  - name: app
    image: ubuntu:latest
    securityContext:
      privileged: true
```

**List the attack surface issues:**

<details>
<summary>Attack Surface Issues</summary>

**API Server:**
1. `anonymous-auth=true` - Anyone can access API without authentication
2. `authorization-mode=AlwaysAllow` - No authorization, all requests permitted

**Kubelet:**
3. `anonymous.enabled: true` - Kubelet API accessible without auth
4. `readOnlyPort: 10255` - Information disclosure, pod enumeration

**Pod:**
5. `hostNetwork: true` - Pod uses host network, can sniff traffic
6. `hostPID: true` - Pod can see all host processes
7. `privileged: true` - Full host access, container escape trivial
8. `ubuntu:latest` - Large image with many packages, mutable tag

**Impact**:
- External attackers can access API without auth
- Any compromised pod has full host access
- Kubelet accessible for container execution
- Information readily available for reconnaissance

</details>

---

## Summary

Attack surface is the sum of all entry points:

| Surface Type | Examples | Reduction Strategy |
|-------------|----------|-------------------|
| **External** | API server, Ingress, NodePort | Private endpoints, firewalls |
| **Internal** | Pod network, kubelet, API from pods | Network policies, disable tokens |
| **Supply Chain** | Images, dependencies, CI/CD | Scanning, signing, minimal images |

Key principles:
- What's not exposed can't be attacked
- Minimize privileges at every layer
- Assume breach, limit blast radius
- Different actors have different attack surfaces

---

## Next Module

[Module 4.2: Common Vulnerabilities](../module-4.2-vulnerabilities/) - Understanding CVEs and misconfigurations in Kubernetes.
