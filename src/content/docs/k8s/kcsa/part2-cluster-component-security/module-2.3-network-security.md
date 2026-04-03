---
title: "Module 2.3: Network Security"
slug: k8s/kcsa/part2-cluster-component-security/module-2.3-network-security
sidebar:
  order: 4
---
> **Complexity**: `[MEDIUM]` - Core knowledge
>
> **Time to Complete**: 25-30 minutes
>
> **Prerequisites**: [Module 2.2: Node Security](../module-2.2-node-security/)

---

## What You'll Be Able to Do

After completing this module, you will be able to:

1. **Evaluate** the Kubernetes flat network model and its security implications
2. **Assess** NetworkPolicy coverage to identify unprotected namespaces and pods
3. **Explain** how service mesh mTLS provides encryption and identity verification for pod traffic
4. **Compare** CNI plugin security capabilities and their support for network policy enforcement

---

## Why This Module Matters

By default, all pods in Kubernetes can communicate with all other pods. This flat network model is convenient but dangerous—a compromised pod can reach any other pod in the cluster. Understanding network security is essential for implementing Zero Trust principles in Kubernetes.

Network policies and service mesh are your primary tools for controlling traffic within the cluster.

---

## Kubernetes Networking Model

```
┌─────────────────────────────────────────────────────────────┐
│              DEFAULT KUBERNETES NETWORKING                  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  BY DEFAULT:                                               │
│  • All pods can communicate with all other pods            │
│  • No network isolation between namespaces                 │
│  • Any pod can reach any service                           │
│  • Pods can reach external networks                        │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │         ALL PODS ←──────────────→ ALL PODS          │   │
│  │                                                     │   │
│  │  Pod A ───→ Pod B ───→ Pod C ───→ Pod D            │   │
│  │    ↑                                 │              │   │
│  │    └─────────────────────────────────┘              │   │
│  │                                                     │   │
│  │  No restrictions, full mesh connectivity            │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  THIS IS DANGEROUS:                                        │
│  • Compromised pod can scan entire cluster                 │
│  • Lateral movement is trivial                             │
│  • No defense in depth                                     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Container Network Interface (CNI)

CNI plugins implement Kubernetes networking and often provide network policy enforcement.

```
┌─────────────────────────────────────────────────────────────┐
│              CNI PLUGIN RESPONSIBILITIES                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  BASIC NETWORKING                                          │
│  • Assign IP addresses to pods                             │
│  • Enable pod-to-pod communication                         │
│  • Route traffic between nodes                             │
│                                                             │
│  SECURITY FEATURES (varies by plugin)                      │
│  • Network policy enforcement                              │
│  • Encryption in transit                                   │
│  • Egress controls                                         │
│  • Observability and logging                               │
│                                                             │
│  COMMON CNI PLUGINS                                        │
│  ┌──────────────┬────────────────────────────────────┐    │
│  │ Plugin       │ Network Policy Support             │    │
│  ├──────────────┼────────────────────────────────────┤    │
│  │ Calico       │ Full (plus extensions)             │    │
│  │ Cilium       │ Full (plus extensions)             │    │
│  │ Weave        │ Full                               │    │
│  │ Flannel      │ None (basic networking only)       │    │
│  │ AWS VPC CNI  │ Via Calico add-on                  │    │
│  └──────────────┴────────────────────────────────────┘    │
│                                                             │
│  ⚠️  Flannel doesn't support network policies!            │
│     Choose a CNI that supports your security needs        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

> **Stop and think**: By default, all pods in a Kubernetes cluster can communicate with every other pod. If you deploy a network policy that selects only your frontend pods, what happens to pods that are NOT selected by any policy?

## Network Policies

Network policies are Kubernetes' built-in mechanism for traffic control.

### Network Policy Basics

```
┌─────────────────────────────────────────────────────────────┐
│              NETWORK POLICY CONCEPT                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Network policies are ADDITIVE:                            │
│  • No policy = allow all traffic                           │
│  • Policy exists = default deny for selected pods          │
│  • Multiple policies = union of allowed traffic            │
│                                                             │
│  POLICY COMPONENTS:                                        │
│                                                             │
│  podSelector:     Which pods this policy applies to        │
│  policyTypes:     [Ingress, Egress] or both               │
│  ingress:         Rules for incoming traffic               │
│  egress:          Rules for outgoing traffic               │
│                                                             │
│  SELECTOR OPTIONS:                                         │
│  • podSelector    - Match by pod labels                    │
│  • namespaceSelector - Match by namespace labels           │
│  • ipBlock        - Match by CIDR range                    │
│  • ports          - Match by port/protocol                 │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Default Deny Pattern

The recommended starting point for network security:

```yaml
# Default deny all ingress in namespace
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-ingress
  namespace: production
spec:
  podSelector: {}  # Selects all pods in namespace
  policyTypes:
  - Ingress
  # No ingress rules = deny all ingress
```

```yaml
# Default deny all egress in namespace
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-egress
  namespace: production
spec:
  podSelector: {}
  policyTypes:
  - Egress
  # No egress rules = deny all egress
```

### Allow Specific Traffic

After default deny, explicitly allow required traffic:

```yaml
# Allow frontend to communicate with backend
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-frontend-to-backend
  namespace: production
spec:
  podSelector:
    matchLabels:
      app: backend
  policyTypes:
  - Ingress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: frontend
    ports:
    - protocol: TCP
      port: 8080
```

---

## Network Policy Patterns

### Namespace Isolation

```
┌─────────────────────────────────────────────────────────────┐
│              NAMESPACE ISOLATION PATTERN                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  BEFORE (Default - No Isolation):                          │
│  ┌────────────────┐    ┌────────────────┐                  │
│  │  namespace: dev │←──→│ namespace: prod │                 │
│  │  Pod A ←───────┼────┼───→ Pod B       │                 │
│  └────────────────┘    └────────────────┘                  │
│  All namespaces can communicate                            │
│                                                             │
│  AFTER (Namespace Isolation):                              │
│  ┌────────────────┐    ┌────────────────┐                  │
│  │  namespace: dev │ ✗  │ namespace: prod │                 │
│  │  Pod A ────────┼────┼───X Pod B       │                 │
│  └────────────────┘    └────────────────┘                  │
│  Cross-namespace traffic blocked                           │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

```yaml
# Only allow traffic from same namespace
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-same-namespace
  namespace: production
spec:
  podSelector: {}
  policyTypes:
  - Ingress
  ingress:
  - from:
    - podSelector: {}  # Any pod in same namespace
```

### Database Isolation

```yaml
# Only allow backend pods to reach database
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: database-access
  namespace: production
spec:
  podSelector:
    matchLabels:
      app: database
  policyTypes:
  - Ingress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          role: backend
    ports:
    - protocol: TCP
      port: 5432
```

---

## Service Mesh Security

Service mesh adds a sidecar proxy to each pod, providing security features beyond network policies.

```
┌─────────────────────────────────────────────────────────────┐
│              SERVICE MESH ARCHITECTURE                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  WITHOUT SERVICE MESH:                                     │
│  ┌─────────┐                    ┌─────────┐                │
│  │  Pod A  │ ─── HTTP/TCP ───→ │  Pod B  │                │
│  │  (app)  │                    │  (app)  │                │
│  └─────────┘                    └─────────┘                │
│  Unencrypted, no identity                                  │
│                                                             │
│  WITH SERVICE MESH:                                        │
│  ┌─────────────────┐            ┌─────────────────┐        │
│  │  Pod A          │            │  Pod B          │        │
│  │  ┌─────┐┌─────┐│            │┌─────┐┌─────┐   │        │
│  │  │ app ││proxy│├── mTLS ───→│proxy ││ app │   │        │
│  │  └─────┘└─────┘│            │└─────┘└─────┘   │        │
│  └─────────────────┘            └─────────────────┘        │
│  Encrypted, identity-based, observable                     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Service Mesh Security Features

| Feature | Description |
|---------|-------------|
| **mTLS** | Automatic encryption between services |
| **Identity** | Cryptographic identity for each workload |
| **Authorization** | Fine-grained access policies |
| **Observability** | Traffic metrics, tracing |
| **Traffic control** | Rate limiting, retries, timeouts |

### Common Service Mesh Options

| Mesh | Description |
|------|-------------|
| **Istio** | Full-featured, complex, widely adopted |
| **Linkerd** | Lightweight, simple, fast |
| **Cilium** | eBPF-based, combined CNI and mesh |
| **Consul Connect** | HashiCorp's service mesh |

---

> **Pause and predict**: Network policies control which pods can talk to each other, but they don't encrypt traffic. If an attacker compromises a node, can they sniff traffic between pods on that node even with network policies in place?

## Encrypting Traffic

### mTLS (Mutual TLS)

```
┌─────────────────────────────────────────────────────────────┐
│              mTLS EXPLAINED                                 │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  REGULAR TLS (one-way)                                     │
│  Client ──────→ Server                                     │
│  • Client verifies server identity                         │
│  • Server doesn't verify client                            │
│  • Like HTTPS to a website                                 │
│                                                             │
│  MUTUAL TLS (two-way)                                      │
│  Client ←─────→ Server                                     │
│  • Client verifies server identity                         │
│  • Server verifies client identity                         │
│  • Both parties authenticated                              │
│                                                             │
│  IN KUBERNETES:                                            │
│  • Service mesh handles mTLS automatically                 │
│  • Each pod gets a certificate                             │
│  • Certificates rotated automatically                      │
│  • Zero Trust networking achieved                          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Why Encrypt In-Cluster Traffic?

```
┌─────────────────────────────────────────────────────────────┐
│              WHY ENCRYPT INTERNAL TRAFFIC?                  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  "But it's inside my network, why encrypt?"                │
│                                                             │
│  THREAT: Network eavesdropping                             │
│  • Compromised node can sniff traffic                      │
│  • Network devices could be compromised                    │
│  • Cloud provider could theoretically observe              │
│                                                             │
│  THREAT: Man-in-the-middle attacks                         │
│  • Without mTLS, pods can impersonate others               │
│  • No verification of "who is talking to who"              │
│                                                             │
│  COMPLIANCE:                                               │
│  • Many regulations require encryption in transit          │
│  • PCI-DSS, HIPAA, SOC2 often require it                  │
│                                                             │
│  ZERO TRUST:                                               │
│  • Assume the network is compromised                       │
│  • Encrypt everything, verify everything                   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Did You Know?

- **Network policies are namespaced** - they only affect pods in their namespace. You can't create a cluster-wide "deny all" with standard network policies.

- **Flannel doesn't support network policies** - it's one of the most common CNI plugins, but it only provides basic connectivity. You need Calico or Cilium for policy enforcement.

- **Service mesh adoption is growing** - while it adds complexity, the security benefits (automatic mTLS, identity) make it increasingly common in production.

- **Cilium uses eBPF** - this allows it to enforce policies at the kernel level, making it faster and more capable than iptables-based solutions.

---

## Common Mistakes

| Mistake | Why It Hurts | Solution |
|---------|--------------|----------|
| No network policies | All pods can reach all pods | Implement default deny |
| Flannel without policy add-on | Network policies have no effect | Use Calico, Cilium, or add policy support |
| Allowing all egress | Pods can exfiltrate data anywhere | Control egress traffic |
| Not encrypting internal traffic | Subject to eavesdropping | Use service mesh with mTLS |
| Overly permissive policies | Defeats purpose of policies | Follow least privilege |

---

## Quiz

1. **During a security review, you discover pods in the default namespace can communicate with pods in every other namespace. No network policies exist anywhere in the cluster. What Kubernetes resource would you use to restrict this, and what is the critical first step?**
   <details>
   <summary>Answer</summary>
   Use NetworkPolicy resources to restrict traffic. The critical first step is to verify your CNI plugin supports network policies — if you're using Flannel, NetworkPolicy resources will be accepted by the API server but never enforced, creating a false sense of security. After confirming CNI support (Calico, Cilium, Weave), implement default-deny NetworkPolicies in each namespace with an empty podSelector and policyTypes: [Ingress, Egress]. Then add explicit allow rules for required traffic flows. Don't forget to allow DNS egress (port 53 to kube-dns) or applications will break immediately.
   </details>

2. **A team creates two network policies for their backend pod: Policy A allows ingress from pods labeled `app: frontend` on port 8080, and Policy B allows ingress from pods labeled `app: monitoring` on port 9090. A pod labeled `app: frontend` tries to reach the backend on port 9090. Is this allowed?**
   <details>
   <summary>Answer</summary>
   No, this is denied. Network policies are additive — the allowed traffic is the union of all policies. Policy A allows frontend on port 8080, Policy B allows monitoring on port 9090. The union allows: frontend→8080 OR monitoring→9090. Frontend on port 9090 is neither of these, so it's denied. Within each policy rule, the `from` selectors and `ports` are combined with AND logic (must match both source AND port). This is a common source of confusion — policies are OR'd together, but within each rule, conditions are AND'd.
   </details>

3. **Your cluster uses Cilium as the CNI. A compliance requirement mandates that all pod-to-pod communication for PCI-scoped workloads must be encrypted. Network policies alone don't encrypt traffic. What solution would you recommend and why?**
   <details>
   <summary>Answer</summary>
   Implement a service mesh with mTLS (Istio, Linkerd, or Cilium's built-in encryption). Network policies control which traffic is allowed but transmit it in plaintext — a compromised node or network tap could read the data. mTLS provides both encryption (protecting confidentiality) and mutual authentication (verifying both parties' identities). For Cilium specifically, you can use its WireGuard-based transparent encryption, which encrypts node-to-node traffic without a full service mesh. This satisfies PCI-DSS Requirement 4 (encrypt transmission of cardholder data over open/public networks) and supports zero-trust principles.
   </details>

4. **A developer adds egress network policies to restrict outbound traffic from their application pods. After deploying, the application can't resolve any service names and crashes. What did they forget, and why is this such a common mistake?**
   <details>
   <summary>Answer</summary>
   They forgot to allow DNS egress. When you create an egress NetworkPolicy, it creates an implicit deny-all for egress traffic from selected pods. DNS resolution requires UDP port 53 (and sometimes TCP 53) to the kube-dns pods in the kube-system namespace. Without this exception, pods can't resolve service names like `my-service.production.svc.cluster.local`. This is the most common egress policy mistake because DNS is invisible infrastructure — developers don't think about it until it breaks. The fix: add an egress rule allowing UDP/TCP port 53 to pods with label `k8s-app: kube-dns` across all namespaces.
   </details>

5. **A security architect proposes using both Kubernetes NetworkPolicies AND Istio AuthorizationPolicies. A colleague says this is redundant. Who is right?**
   <details>
   <summary>Answer</summary>
   The security architect is right — they're complementary, not redundant. NetworkPolicies operate at Layer 3/4 (IP addresses, ports) and are enforced by the CNI plugin at the network level. Istio AuthorizationPolicies operate at Layer 7 (HTTP methods, paths, headers) and are enforced by the sidecar proxy. Example: a NetworkPolicy might allow frontend to reach backend on port 8080, while an Istio policy further restricts to only GET and POST methods on specific URL paths. This is defense in depth — even if one layer is misconfigured or bypassed, the other still provides protection. NetworkPolicies also protect non-mesh traffic that Istio sidecars don't handle.
   </details>
---

## Hands-On Exercise: Network Policy Design

**Scenario**: Design network policies for a three-tier application:
- Frontend pods (label: tier=frontend)
- Backend pods (label: tier=backend)
- Database pods (label: tier=database)

Requirements:
1. Frontend can receive traffic from anywhere
2. Backend can only receive traffic from frontend
3. Database can only receive traffic from backend
4. No pod should have unrestricted egress

**Write the network policies:**

<details>
<summary>Solution</summary>

```yaml
# 1. Default deny all ingress and egress
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-all
  namespace: app
spec:
  podSelector: {}
  policyTypes:
  - Ingress
  - Egress
---
# 2. Allow ingress to frontend from anywhere
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: frontend-ingress
  namespace: app
spec:
  podSelector:
    matchLabels:
      tier: frontend
  policyTypes:
  - Ingress
  ingress:
  - {}  # Allow from anywhere
---
# 3. Allow frontend to reach backend
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: backend-from-frontend
  namespace: app
spec:
  podSelector:
    matchLabels:
      tier: backend
  policyTypes:
  - Ingress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          tier: frontend
    ports:
    - port: 8080
---
# 4. Allow backend to reach database
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: database-from-backend
  namespace: app
spec:
  podSelector:
    matchLabels:
      tier: database
  policyTypes:
  - Ingress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          tier: backend
    ports:
    - port: 5432
---
# 5. Allow frontend egress to backend
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: frontend-egress
  namespace: app
spec:
  podSelector:
    matchLabels:
      tier: frontend
  policyTypes:
  - Egress
  egress:
  - to:
    - podSelector:
        matchLabels:
          tier: backend
    ports:
    - port: 8080
  - to:  # Allow DNS
    - namespaceSelector: {}
      podSelector:
        matchLabels:
          k8s-app: kube-dns
    ports:
    - port: 53
      protocol: UDP
---
# 6. Allow backend egress to database
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: backend-egress
  namespace: app
spec:
  podSelector:
    matchLabels:
      tier: backend
  policyTypes:
  - Egress
  egress:
  - to:
    - podSelector:
        matchLabels:
          tier: database
    ports:
    - port: 5432
  - to:  # Allow DNS
    - namespaceSelector: {}
      podSelector:
        matchLabels:
          k8s-app: kube-dns
    ports:
    - port: 53
      protocol: UDP
```

</details>

---

## Summary

Network security in Kubernetes requires active configuration:

| Concept | Key Points |
|---------|------------|
| **Default Behavior** | All pods can reach all pods - implement default deny |
| **CNI Plugins** | Choose one that supports network policies (Calico, Cilium) |
| **Network Policies** | Additive, namespace-scoped, require explicit allows |
| **Service Mesh** | Provides mTLS, identity, and fine-grained authorization |
| **mTLS** | Encrypts traffic AND verifies both parties |

Key patterns:
- Start with default deny
- Allow only required traffic
- Consider egress controls
- Use mTLS for sensitive communications
- Verify your CNI supports policies

---

## Next Module

[Module 2.4: PKI and Certificates](../module-2.4-pki-certificates/) - Understanding Kubernetes certificate management and PKI.
