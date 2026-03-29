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

1. **What is the default network policy behavior in Kubernetes?**
   <details>
   <summary>Answer</summary>
   Allow all traffic. By default, all pods can communicate with all other pods and external endpoints. Network policies must be explicitly created to restrict traffic.
   </details>

2. **How do network policies behave when multiple policies apply to a pod?**
   <details>
   <summary>Answer</summary>
   Network policies are additive. The allowed traffic is the union of all applicable policies. If any policy allows traffic, it's allowed.
   </details>

3. **What does a network policy with an empty podSelector do?**
   <details>
   <summary>Answer</summary>
   It selects all pods in the namespace where the policy is created. This is used for default deny policies.
   </details>

4. **Why might network policies not work in your cluster?**
   <details>
   <summary>Answer</summary>
   The CNI plugin might not support network policies. Flannel, for example, doesn't enforce network policies. You need a CNI like Calico, Cilium, or Weave that supports policy enforcement.
   </details>

5. **What security feature does mTLS provide that regular TLS doesn't?**
   <details>
   <summary>Answer</summary>
   Mutual authentication. In regular TLS, only the client verifies the server. In mTLS, both parties verify each other's identity, preventing impersonation attacks.
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
