---
title: "Module 5.3: NetworkPolicies"
slug: k8s/ckad/part5-networking/module-5.3-networkpolicies
sidebar:
  order: 3
lab:
  id: ckad-5.3-networkpolicies
  url: https://killercoda.com/kubedojo/scenario/ckad-5.3-networkpolicies
  duration: "40 min"
  difficulty: advanced
  environment: kubernetes
---
> **Complexity**: `[MEDIUM]` - Important for security, requires understanding selectors
>
> **Time to Complete**: 45-55 minutes
>
> **Prerequisites**: Module 5.1 (Services), understanding of labels and selectors

---

## Learning Outcomes

After completing this module, you will be able to:
- **Write** NetworkPolicies that restrict ingress and egress traffic using pod, namespace, and CIDR selectors
- **Debug** blocked traffic by analyzing NetworkPolicy rules and verifying label matches
- **Design** a default-deny network posture with explicit allow rules for required communication paths
- **Explain** how NetworkPolicy rules combine and why order of rules does not matter

---

## Why This Module Matters

By default, all pods can communicate with all other pods. NetworkPolicies let you control which pods can talk to which, implementing the principle of least privilege for network access. This is critical for security and multi-tenant clusters.

The CKAD exam tests:
- Creating NetworkPolicies
- Understanding ingress and egress rules
- Using selectors to target pods
- Debugging connectivity issues

> **The Office Building Security Analogy**
>
> Think of NetworkPolicies as building security rules. By default, the building has no security—anyone can go anywhere. NetworkPolicies are like adding key card readers. You define who can enter which floors (ingress) and which floors people can leave from (egress). The "default deny" policy is like requiring a key card for every door.

---

## NetworkPolicy Basics

### Default Behavior

Without NetworkPolicies:
- All pods can communicate with all pods
- All pods can reach external endpoints
- No restrictions

### How NetworkPolicies Work

1. NetworkPolicies are **additive**—they can only allow traffic, not deny
2. If ANY policy selects a pod, only traffic allowed by policies is permitted
3. If NO policy selects a pod, all traffic is allowed (default)
4. Requires a **CNI plugin that supports NetworkPolicies** (Calico, Cilium, etc.)

---

## Basic Structure

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: my-policy
  namespace: default
spec:
  podSelector:           # Which pods this policy applies to
    matchLabels:
      app: my-app
  policyTypes:           # What traffic types to control
  - Ingress              # Incoming traffic
  - Egress               # Outgoing traffic
  ingress:               # Rules for incoming traffic
  - from:
    - podSelector:
        matchLabels:
          role: frontend
  egress:                # Rules for outgoing traffic
  - to:
    - podSelector:
        matchLabels:
          role: database
```

---

## Policy Types

### Ingress (Incoming Traffic)

Control what can connect TO the selected pods:

```yaml
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

### Egress (Outgoing Traffic)

Control what the selected pods can connect TO:

```yaml
spec:
  podSelector:
    matchLabels:
      app: frontend
  policyTypes:
  - Egress
  egress:
  - to:
    - podSelector:
        matchLabels:
          app: backend
    ports:
    - protocol: TCP
      port: 8080
```

---

## Selector Types

### podSelector

Select pods in the same namespace:

```yaml
ingress:
- from:
  - podSelector:
      matchLabels:
        role: frontend
```

### namespaceSelector

Select pods from specific namespaces:

```yaml
ingress:
- from:
  - namespaceSelector:
      matchLabels:
        env: production
```

### Combined (AND Logic)

Pod must match both selectors:

```yaml
ingress:
- from:
  - namespaceSelector:
      matchLabels:
        env: production
    podSelector:           # Same list item = AND
      matchLabels:
        role: frontend
```

### Separate Items (OR Logic)

Traffic allowed from either selector:

```yaml
ingress:
- from:
  - namespaceSelector:     # First item
      matchLabels:
        env: production
  - podSelector:           # Second item = OR
      matchLabels:
        role: frontend
```

### ipBlock

Select by IP range (typically external):

```yaml
ingress:
- from:
  - ipBlock:
      cidr: 10.0.0.0/8
      except:
      - 10.0.1.0/24
```

---

## Visualization

```
┌─────────────────────────────────────────────────────────────┐
│                NetworkPolicy Concepts                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Default (No Policy):                                       │
│  ┌─────────┐     ┌─────────┐     ┌─────────┐              │
│  │ Pod A   │◄───►│ Pod B   │◄───►│ Pod C   │              │
│  └─────────┘     └─────────┘     └─────────┘              │
│       All traffic allowed                                   │
│                                                             │
│  With Policy (Pod B selected):                             │
│  ┌─────────┐     ┌─────────┐     ┌─────────┐              │
│  │ Pod A   │────►│ Pod B   │     │ Pod C   │              │
│  │(frontend)│     │(backend)│     │(other)  │              │
│  └─────────┘     └─────────┘     └─────────┘              │
│       ✓ allowed      X blocked                             │
│                                                             │
│  Selector Types:                                           │
│  ┌──────────────────────────────────────────────────┐     │
│  │                                                   │     │
│  │  podSelector:        Same namespace pods          │     │
│  │  namespaceSelector:  Pods from labeled namespaces │     │
│  │  ipBlock:            External IP ranges           │     │
│  │                                                   │     │
│  │  Combined in same from/to item = AND              │     │
│  │  Separate from/to items = OR                      │     │
│  │                                                   │     │
│  └──────────────────────────────────────────────────┘     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Common Patterns

### Default Deny All Ingress

Block all incoming traffic to pods in namespace:

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-ingress
spec:
  podSelector: {}          # Empty = select all pods
  policyTypes:
  - Ingress
  # No ingress rules = deny all
```

### Default Deny All Egress

Block all outgoing traffic from pods in namespace:

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-egress
spec:
  podSelector: {}
  policyTypes:
  - Egress
  # No egress rules = deny all
```

### Default Deny All

Block both directions:

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-all
spec:
  podSelector: {}
  policyTypes:
  - Ingress
  - Egress
```

### Allow All Ingress

Explicitly allow all (useful to override):

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-all-ingress
spec:
  podSelector: {}
  policyTypes:
  - Ingress
  ingress:
  - {}                     # Empty rule = allow all
```

### Allow DNS Egress

Essential when using default deny egress:

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-dns
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
```

---

## Complete Example: Three-Tier App

```yaml
# Frontend: can receive from anywhere, can reach backend
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: frontend-policy
spec:
  podSelector:
    matchLabels:
      tier: frontend
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - {}                     # Allow all ingress
  egress:
  - to:
    - podSelector:
        matchLabels:
          tier: backend
    ports:
    - port: 8080
---
# Backend: only from frontend, can reach database
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: backend-policy
spec:
  podSelector:
    matchLabels:
      tier: backend
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          tier: frontend
    ports:
    - port: 8080
  egress:
  - to:
    - podSelector:
        matchLabels:
          tier: database
    ports:
    - port: 5432
---
# Database: only from backend
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: database-policy
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
```

---

## Quick Reference

```bash
# Create NetworkPolicy (must use YAML)
k apply -f policy.yaml

# View NetworkPolicies
k get networkpolicy
k get netpol

# Describe policy
k describe netpol NAME

# Test connectivity
k exec pod1 -- wget -qO- --timeout=2 pod2-svc:80

# Check if CNI supports NetworkPolicies
k get pods -n kube-system | grep -E 'calico|cilium|weave'
```

---

## Did You Know?

- **NetworkPolicies require a compatible CNI.** Flannel doesn't support them by default. Calico, Cilium, and Weave do.

- **Policies are additive, not subtractive.** You can't create a policy that denies specific traffic—you can only allow. "Deny" happens by selecting a pod without allowing traffic.

- **Empty podSelector `{}` selects all pods** in the namespace.

- **When you specify ports in egress, you might also need to allow DNS** (port 53 UDP) or pod name resolution won't work.

---

## Common Mistakes

| Mistake | Why It Hurts | Solution |
|---------|--------------|----------|
| CNI doesn't support NetworkPolicies | Policies created but ignored | Use Calico, Cilium, or Weave |
| Forgot DNS in egress deny | Pod can't resolve names | Add egress rule for kube-dns |
| AND vs OR confusion | Wrong pods selected | Remember: same item=AND, different items=OR |
| Empty podSelector confusion | Selected all pods unexpectedly | `{}` means "all pods in namespace" |
| Forgot policyTypes | Policy doesn't do what expected | Always specify Ingress and/or Egress |

---

## Quiz

1. **What happens to pods that have no NetworkPolicy selecting them?**
   <details>
   <summary>Answer</summary>
   All traffic is allowed to and from those pods (default open).
   </details>

2. **How do you block all incoming traffic to pods in a namespace?**
   <details>
   <summary>Answer</summary>
   Create a default deny ingress policy:
   ```yaml
   spec:
     podSelector: {}
     policyTypes:
     - Ingress
   ```
   With no ingress rules, all ingress is denied.
   </details>

3. **What's the difference between AND and OR logic in NetworkPolicy selectors?**
   <details>
   <summary>Answer</summary>
   - **AND**: Selectors in the same `from/to` item (namespaceSelector + podSelector together)
   - **OR**: Separate items in the `from/to` list
   </details>

4. **Why might pods not be able to resolve DNS names after applying a default deny egress policy?**
   <details>
   <summary>Answer</summary>
   DNS queries (port 53 UDP) are blocked. You need to explicitly allow egress to kube-dns pods.
   </details>

---

## Hands-On Exercise

**Task**: Implement network isolation for a simple application.

**Setup:**
```bash
# Create namespace
k create ns netpol-demo

# Create pods
k run frontend --image=nginx -n netpol-demo -l tier=frontend
k run backend --image=nginx -n netpol-demo -l tier=backend
k run database --image=nginx -n netpol-demo -l tier=database

# Wait for pods
k wait --for=condition=Ready pod --all -n netpol-demo --timeout=60s

# Create services
k expose pod frontend --port=80 -n netpol-demo
k expose pod backend --port=80 -n netpol-demo
k expose pod database --port=80 -n netpol-demo
```

**Part 1: Test Default Connectivity**
```bash
# All pods can reach all pods
k exec -n netpol-demo frontend -- wget -qO- --timeout=2 backend:80
k exec -n netpol-demo backend -- wget -qO- --timeout=2 database:80
k exec -n netpol-demo database -- wget -qO- --timeout=2 frontend:80
# All should succeed
```

**Part 2: Apply Default Deny**
```bash
cat << 'EOF' | k apply -f -
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny
  namespace: netpol-demo
spec:
  podSelector: {}
  policyTypes:
  - Ingress
EOF

# Now test - all should fail (if CNI supports NetworkPolicies)
k exec -n netpol-demo frontend -- wget -qO- --timeout=2 backend:80
# Should timeout
```

**Part 3: Allow Frontend to Backend**
```bash
cat << 'EOF' | k apply -f -
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: backend-allow-frontend
  namespace: netpol-demo
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
    - port: 80
EOF

# Test
k exec -n netpol-demo frontend -- wget -qO- --timeout=2 backend:80
# Should succeed

k exec -n netpol-demo database -- wget -qO- --timeout=2 backend:80
# Should fail
```

**Cleanup:**
```bash
k delete ns netpol-demo
```

---

## Practice Drills

### Drill 1: Default Deny Ingress (Target: 2 minutes)

```bash
k create ns drill1
k run web --image=nginx -n drill1

cat << 'EOF' | k apply -f -
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: deny-ingress
  namespace: drill1
spec:
  podSelector: {}
  policyTypes:
  - Ingress
EOF

k get netpol -n drill1
k delete ns drill1
```

### Drill 2: Allow Specific Pod (Target: 3 minutes)

```bash
k create ns drill2
k run server --image=nginx -n drill2 -l role=server
k run client --image=nginx -n drill2 -l role=client
k expose pod server --port=80 -n drill2

cat << 'EOF' | k apply -f -
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-client
  namespace: drill2
spec:
  podSelector:
    matchLabels:
      role: server
  policyTypes:
  - Ingress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          role: client
    ports:
    - port: 80
EOF

k describe netpol allow-client -n drill2
k delete ns drill2
```

### Drill 3: Egress Policy (Target: 3 minutes)

```bash
k create ns drill3
k run app --image=nginx -n drill3 -l app=web
k run db --image=nginx -n drill3 -l app=db
k expose pod db --port=80 -n drill3

cat << 'EOF' | k apply -f -
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: app-egress
  namespace: drill3
spec:
  podSelector:
    matchLabels:
      app: web
  policyTypes:
  - Egress
  egress:
  - to:
    - podSelector:
        matchLabels:
          app: db
    ports:
    - port: 80
EOF

k get netpol -n drill3
k delete ns drill3
```

### Drill 4: Namespace Selector (Target: 3 minutes)

```bash
k create ns drill4-source
k create ns drill4-target
k label ns drill4-source env=trusted

k run target --image=nginx -n drill4-target -l app=target
k expose pod target --port=80 -n drill4-target

cat << 'EOF' | k apply -f -
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: from-trusted
  namespace: drill4-target
spec:
  podSelector:
    matchLabels:
      app: target
  policyTypes:
  - Ingress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          env: trusted
EOF

k describe netpol from-trusted -n drill4-target
k delete ns drill4-source drill4-target
```

### Drill 5: Combined Selectors (AND) (Target: 3 minutes)

```bash
k create ns drill5
k label ns drill5 env=prod

k run backend --image=nginx -n drill5 -l tier=backend
k run frontend --image=nginx -n drill5 -l tier=frontend

cat << 'EOF' | k apply -f -
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: combined-and
  namespace: drill5
spec:
  podSelector:
    matchLabels:
      tier: backend
  policyTypes:
  - Ingress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          env: prod
      podSelector:
        matchLabels:
          tier: frontend
EOF

k describe netpol combined-and -n drill5
k delete ns drill5
```

### Drill 6: IP Block (Target: 3 minutes)

```bash
k create ns drill6
k run web --image=nginx -n drill6

cat << 'EOF' | k apply -f -
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: ip-block
  namespace: drill6
spec:
  podSelector: {}
  policyTypes:
  - Ingress
  ingress:
  - from:
    - ipBlock:
        cidr: 10.0.0.0/8
        except:
        - 10.0.1.0/24
EOF

k describe netpol ip-block -n drill6
k delete ns drill6
```

---

## Next Module

[Part 5 Cumulative Quiz](../part5-cumulative-quiz/) - Test your mastery of Services, Ingress, and NetworkPolicies.
