---
title: "Module 3.5: Network Policies"
slug: k8s/kcsa/part3-security-fundamentals/module-3.5-network-policies
sidebar:
  order: 6
---
> **Complexity**: `[MEDIUM]` - Core knowledge
>
> **Time to Complete**: 25-30 minutes
>
> **Prerequisites**: [Module 3.4: ServiceAccount Security](../module-3.4-serviceaccounts/)

---

## What You'll Be Able to Do

After completing this module, you will be able to:

1. **Evaluate** network policy coverage to identify unprotected pods and namespaces
2. **Assess** whether network policies implement default-deny and least-privilege traffic rules
3. **Identify** gaps in network segmentation that allow lateral movement between workloads
4. **Explain** how ingress and egress policies combine to control pod-to-pod and external traffic

---

## Why This Module Matters

By default, all pods can talk to all other pods in Kubernetes. This flat network is convenient but dangerous—a compromised pod can scan your entire cluster and reach any service. Network policies are your firewall within the cluster.

This module builds on the network security concepts from Part 2, focusing on practical policy implementation.

---

## Network Policy Fundamentals

```
┌─────────────────────────────────────────────────────────────┐
│              NETWORK POLICY BASICS                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  DEFAULT BEHAVIOR (No policies):                           │
│  • All pods can reach all other pods                       │
│  • All pods can reach external endpoints                   │
│  • All pods accept traffic from anywhere                   │
│                                                             │
│  WITH NETWORK POLICY:                                      │
│  • Pods selected by policy have restricted traffic         │
│  • Unselected pods still have full connectivity            │
│  • Policies are additive (union of allowed traffic)        │
│                                                             │
│  KEY INSIGHT:                                              │
│  Applying ANY policy to a pod creates implicit deny        │
│  for the specified direction (ingress/egress)              │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Policy Structure

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: example-policy
  namespace: production
spec:
  # 1. Which pods does this policy apply to?
  podSelector:
    matchLabels:
      app: backend

  # 2. What direction(s) does it control?
  policyTypes:
  - Ingress
  - Egress

  # 3. What traffic is allowed IN?
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: frontend
    ports:
    - protocol: TCP
      port: 8080

  # 4. What traffic is allowed OUT?
  egress:
  - to:
    - podSelector:
        matchLabels:
          app: database
    ports:
    - protocol: TCP
      port: 5432
```

### Selector Types

```
┌─────────────────────────────────────────────────────────────┐
│              NETWORK POLICY SELECTORS                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  podSelector                                               │
│  • Match pods by labels                                    │
│  • Within same namespace as policy                         │
│  from:                                                     │
│  - podSelector:                                            │
│      matchLabels:                                          │
│        app: frontend                                       │
│                                                             │
│  namespaceSelector                                         │
│  • Match namespaces by labels                              │
│  • Then all pods in matching namespaces                    │
│  from:                                                     │
│  - namespaceSelector:                                      │
│      matchLabels:                                          │
│        env: production                                     │
│                                                             │
│  ipBlock                                                   │
│  • Match by CIDR range                                     │
│  • For external IPs                                        │
│  from:                                                     │
│  - ipBlock:                                                │
│      cidr: 10.0.0.0/8                                      │
│      except:                                               │
│      - 10.0.1.0/24                                         │
│                                                             │
│  COMBINED (AND logic):                                     │
│  from:                                                     │
│  - podSelector:            # Pods with app: web           │
│      matchLabels:          # AND                          │
│        app: web            # in namespaces with env: prod │
│    namespaceSelector:                                      │
│      matchLabels:                                          │
│        env: production                                     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Common Patterns

### Default Deny All

Start with deny all, then allow specific traffic:

```yaml
# Deny all ingress in namespace
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-ingress
  namespace: production
spec:
  podSelector: {}       # Empty = all pods
  policyTypes:
  - Ingress
  # No ingress rules = deny all ingress
```

```yaml
# Deny all egress in namespace
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

```yaml
# Deny all (both directions)
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-all
  namespace: production
spec:
  podSelector: {}
  policyTypes:
  - Ingress
  - Egress
```

### Allow DNS

Essential when using egress policies:

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-dns
  namespace: production
spec:
  podSelector: {}
  policyTypes:
  - Egress
  egress:
  - to:
    - namespaceSelector: {}
      podSelector:
        matchLabels:
          k8s-app: kube-dns
    ports:
    - protocol: UDP
      port: 53
    - protocol: TCP
      port: 53
```

### Same-Namespace Only

Allow traffic only within the namespace:

```yaml
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

### Web Application Pattern

```yaml
# Allow ingress to web tier from anywhere
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: web-ingress
  namespace: app
spec:
  podSelector:
    matchLabels:
      tier: web
  policyTypes:
  - Ingress
  ingress:
  - from: []  # Empty = allow from anywhere
    ports:
    - port: 443
---
# Allow web to reach API
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: api-ingress
  namespace: app
spec:
  podSelector:
    matchLabels:
      tier: api
  policyTypes:
  - Ingress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          tier: web
    ports:
    - port: 8080
---
# Allow API to reach database
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: db-ingress
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
          tier: api
    ports:
    - port: 5432
```

---

## Policy Behavior Details

### How Multiple Policies Combine

```
┌─────────────────────────────────────────────────────────────┐
│              POLICY COMBINATION                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  SCENARIO: Two policies select the same pod                │
│                                                             │
│  Policy A allows:    Policy B allows:                      │
│  - from: app=web     - from: app=api                       │
│  - port: 80          - port: 8080                          │
│                                                             │
│  RESULT: Union of both                                     │
│  - from: app=web on port 80      ✓ Allowed                │
│  - from: app=api on port 8080    ✓ Allowed                │
│  - from: app=web on port 8080    ✗ Denied                 │
│  - from: app=other               ✗ Denied                 │
│                                                             │
│  Policies are OR'd together (additive)                     │
│  Within a policy, from/to elements are OR'd               │
│  Within a from/to element, selectors are AND'd            │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### AND vs OR in Selectors

```yaml
# OR: Traffic from EITHER app=web OR app=api
ingress:
- from:
  - podSelector:
      matchLabels:
        app: web
  - podSelector:            # Separate list item = OR
      matchLabels:
        app: api

# AND: Traffic from pods that are BOTH in production namespace
#      AND have label app=web
ingress:
- from:
  - podSelector:            # Same list item = AND
      matchLabels:
        app: web
    namespaceSelector:
      matchLabels:
        env: production
```

---

## Egress Control

```
┌─────────────────────────────────────────────────────────────┐
│              EGRESS POLICY CONSIDERATIONS                   │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  WHY CONTROL EGRESS:                                       │
│  • Prevent data exfiltration                               │
│  • Limit lateral movement                                  │
│  • Compliance requirements                                 │
│  • Reduce attack surface                                   │
│                                                             │
│  WHAT TO ALLOW:                                            │
│  • DNS (almost always required)                            │
│  • Required backend services                               │
│  • External APIs (specific IPs if possible)                │
│  • Monitoring endpoints                                    │
│                                                             │
│  CHALLENGES:                                               │
│  • Dynamic IPs of external services                        │
│  • Cloud metadata endpoints (169.254.169.254)              │
│  • Cluster services (kube-system)                          │
│                                                             │
│  TIP: Start with audit/monitoring, then enforce            │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Block Cloud Metadata

```yaml
# Block access to cloud metadata service
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: block-metadata
  namespace: production
spec:
  podSelector: {}
  policyTypes:
  - Egress
  egress:
  - to:
    - ipBlock:
        cidr: 0.0.0.0/0
        except:
        - 169.254.169.254/32  # AWS/GCP metadata
```

---

## Troubleshooting Network Policies

```
┌─────────────────────────────────────────────────────────────┐
│              TROUBLESHOOTING CHECKLIST                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. CNI SUPPORTS NETWORK POLICIES?                         │
│     • Flannel: NO (basic networking only)                  │
│     • Calico: YES                                          │
│     • Cilium: YES                                          │
│     • Weave: YES                                           │
│                                                             │
│  2. POLICY SELECTS THE POD?                                │
│     kubectl get netpol -n <ns>                             │
│     kubectl describe netpol <name> -n <ns>                 │
│                                                             │
│  3. POD LABELS MATCH?                                      │
│     kubectl get pod --show-labels                          │
│                                                             │
│  4. NAMESPACE LABELS MATCH? (if using namespaceSelector)   │
│     kubectl get ns --show-labels                           │
│                                                             │
│  5. CORRECT PORTS?                                         │
│     Check port numbers and protocols                       │
│                                                             │
│  6. EGRESS INCLUDES DNS?                                   │
│     Most common egress issue                               │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Did You Know?

- **Network policies don't apply to host network pods** - pods with `hostNetwork: true` bypass network policies.

- **Empty podSelector ({}) means all pods** - this is how default deny policies work.

- **Policies are namespaced** - they only affect pods in their namespace (but can reference other namespaces).

- **Order doesn't matter** - policies are additive regardless of creation order.

---

## Common Mistakes

| Mistake | Why It Hurts | Solution |
|---------|--------------|----------|
| Forgetting DNS in egress | App can't resolve names | Always allow DNS egress |
| CNI doesn't support policies | Policies have no effect | Use Calico, Cilium, etc. |
| Missing namespace labels | Cross-namespace rules fail | Label namespaces |
| Wrong AND/OR logic | Unexpected allow/deny | Test policies carefully |
| No default deny | New pods unrestricted | Start with default deny |

---

## Quiz

1. **What happens when no network policies exist in a namespace?**
   <details>
   <summary>Answer</summary>
   All traffic is allowed. Pods can communicate with any other pod in the cluster and with external endpoints. Network policies create restrictions; without them, there are none.
   </details>

2. **How do you create a "default deny all ingress" policy?**
   <details>
   <summary>Answer</summary>
   Create a NetworkPolicy with empty podSelector (matches all pods), policyTypes including Ingress, and no ingress rules. The empty rules list means no ingress is allowed.
   </details>

3. **Why must egress policies usually allow DNS?**
   <details>
   <summary>Answer</summary>
   Most applications need DNS to resolve service names. Without DNS egress, pods can't resolve hostnames for services they need to reach, breaking most applications.
   </details>

4. **What's the difference between having podSelector AND namespaceSelector in the same list item vs separate list items?**
   <details>
   <summary>Answer</summary>
   Same list item = AND (must match both). Separate list items = OR (match either). This is a common source of policy bugs.
   </details>

5. **Can network policies block traffic to/from pods using hostNetwork: true?**
   <details>
   <summary>Answer</summary>
   No. Pods using hostNetwork bypass network policies because they use the host's network namespace, not the pod network namespace where policies are enforced.
   </details>

---

## Hands-On Exercise: Design Network Policies

**Scenario**: Design network policies for this architecture:

```
┌─────────────────────────────────────────────────────────────┐
│  namespace: frontend                                        │
│  ┌─────────┐                                               │
│  │   web   │ ← External traffic (ingress controller)       │
│  │  :443   │                                               │
│  └────┬────┘                                               │
└───────┼─────────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────────────┐
│  namespace: backend                                         │
│  ┌─────────┐     ┌─────────┐                               │
│  │   api   │────→│   db    │                               │
│  │  :8080  │     │  :5432  │                               │
│  └─────────┘     └─────────┘                               │
└─────────────────────────────────────────────────────────────┘
```

Requirements:
1. Default deny all in both namespaces
2. Web can receive from ingress-nginx namespace
3. Web can reach API in backend namespace
4. API can reach DB (same namespace)
5. Nothing else allowed

<details>
<summary>Solution</summary>

```yaml
# Label namespaces first
# kubectl label ns frontend name=frontend
# kubectl label ns backend name=backend
# kubectl label ns ingress-nginx name=ingress-nginx

---
# Default deny in frontend
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny
  namespace: frontend
spec:
  podSelector: {}
  policyTypes:
  - Ingress
  - Egress
---
# Default deny in backend
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny
  namespace: backend
spec:
  podSelector: {}
  policyTypes:
  - Ingress
  - Egress
---
# Allow ingress to web from ingress-nginx
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: web-ingress
  namespace: frontend
spec:
  podSelector:
    matchLabels:
      app: web
  policyTypes:
  - Ingress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: ingress-nginx
    ports:
    - port: 443
---
# Allow web to reach API + DNS
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: web-egress
  namespace: frontend
spec:
  podSelector:
    matchLabels:
      app: web
  policyTypes:
  - Egress
  egress:
  - to:
    - namespaceSelector:
        matchLabels:
          name: backend
      podSelector:
        matchLabels:
          app: api
    ports:
    - port: 8080
  - to:  # DNS
    - namespaceSelector: {}
      podSelector:
        matchLabels:
          k8s-app: kube-dns
    ports:
    - port: 53
      protocol: UDP
---
# Allow API ingress from web
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: api-ingress
  namespace: backend
spec:
  podSelector:
    matchLabels:
      app: api
  policyTypes:
  - Ingress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: frontend
      podSelector:
        matchLabels:
          app: web
    ports:
    - port: 8080
---
# Allow API to reach DB + DNS
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: api-egress
  namespace: backend
spec:
  podSelector:
    matchLabels:
      app: api
  policyTypes:
  - Egress
  egress:
  - to:
    - podSelector:
        matchLabels:
          app: db
    ports:
    - port: 5432
  - to:  # DNS
    - namespaceSelector: {}
      podSelector:
        matchLabels:
          k8s-app: kube-dns
    ports:
    - port: 53
      protocol: UDP
---
# Allow DB ingress from API
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: db-ingress
  namespace: backend
spec:
  podSelector:
    matchLabels:
      app: db
  policyTypes:
  - Ingress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: api
    ports:
    - port: 5432
```

</details>

---

## Summary

Network policies implement zero trust networking:

| Concept | Key Points |
|---------|------------|
| **Default Behavior** | All traffic allowed without policies |
| **podSelector** | Which pods the policy applies to |
| **policyTypes** | Ingress, Egress, or both |
| **Selectors** | podSelector, namespaceSelector, ipBlock |
| **Combination** | Policies are additive (OR) |

Best practices:
- Start with default deny
- Always allow DNS for egress
- Use namespace labels for cross-namespace rules
- Test policies before production
- Verify CNI supports network policies

---

## Next Module

[Module 4.1: Attack Surfaces](../part4-threat-model/module-4.1-attack-surfaces/) - Understanding Kubernetes attack vectors.
