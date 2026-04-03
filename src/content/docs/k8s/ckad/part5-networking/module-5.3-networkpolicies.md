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

> **Pause and predict**: Look at the two YAML examples below — "Combined (AND Logic)" and "Separate Items (OR Logic)." The only difference is indentation. Can you explain what each one allows before reading the descriptions?

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

> **Stop and think**: You apply a default-deny egress policy to a namespace. Suddenly, all your pods can't resolve DNS names and Service connections fail. What did you forget to allow, and why is DNS so critical for Kubernetes networking?

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

1. **After applying a default-deny ingress NetworkPolicy to the `production` namespace, the backend pods can no longer receive traffic from the frontend pods in the same namespace. Both frontend and backend pods are correctly labeled. What do you need to create to restore communication while keeping the default deny in place?**
   <details>
   <summary>Answer</summary>
   Create an additional NetworkPolicy that explicitly allows ingress to the backend pods from the frontend pods. The default-deny policy selects all pods and provides no ingress rules, blocking everything. Since NetworkPolicies are additive, you add a new policy that selects the backend pods (`podSelector: matchLabels: tier: backend`) and allows ingress from frontend pods (`from: - podSelector: matchLabels: tier: frontend`). Both policies apply simultaneously — the deny policy blocks all traffic by default, and the allow policy opens the specific path needed. You don't need to modify or delete the deny policy.
   </details>

2. **A developer creates a NetworkPolicy with this `from` rule and is confused about what it allows. The policy has one `from` item containing both `namespaceSelector: matchLabels: env: staging` and `podSelector: matchLabels: role: api`. Does this allow traffic from ALL pods in staging namespaces OR only `role: api` pods in staging namespaces?**
   <details>
   <summary>Answer</summary>
   When `namespaceSelector` and `podSelector` are in the SAME `from` list item (same YAML block, same indentation level under a single dash), they combine with AND logic. This allows traffic only from pods labeled `role: api` that are in namespaces labeled `env: staging`. If they were separate items (each under its own dash), it would be OR logic — allowing traffic from any pod in staging namespaces OR any `role: api` pod in the local namespace. This AND vs OR distinction is one of the most common sources of NetworkPolicy bugs, and it hinges entirely on YAML indentation.
   </details>

3. **You apply a default-deny egress NetworkPolicy to a namespace. Immediately, all pods lose the ability to connect to any Service by name, even Services within the same namespace. Connections by IP address still work. What is happening and how do you fix it?**
   <details>
   <summary>Answer</summary>
   DNS resolution is blocked. When pods connect to a Service by name (e.g., `http://my-service`), they first make a DNS query to kube-dns (CoreDNS) on UDP port 53. The default-deny egress policy blocks all outgoing traffic, including DNS queries. Connections by IP bypass DNS so they still work. Fix by adding an egress NetworkPolicy that allows UDP port 53 to the kube-dns pods: allow egress to `namespaceSelector: {}` with `podSelector: matchLabels: k8s-app: kube-dns` on port 53 UDP. This is so common that you should always pair a default-deny egress policy with a DNS allow policy.
   </details>

4. **Your cluster uses Flannel as the CNI plugin. You create a NetworkPolicy to isolate your database pods, but when you test, any pod can still connect to the database. The NetworkPolicy YAML is correct and `kubectl get netpol` shows it exists. What is wrong?**
   <details>
   <summary>Answer</summary>
   Flannel does not support NetworkPolicies. NetworkPolicies are a Kubernetes API concept, but enforcement is handled by the CNI plugin. If the CNI doesn't support them, the policies are stored in the API server (so `kubectl get netpol` shows them) but completely ignored at the network level. You need a CNI that supports NetworkPolicies — Calico, Cilium, or Weave are the most common choices. Some teams run Calico alongside Flannel specifically for NetworkPolicy support. This is a critical detail because everything looks correct from the Kubernetes API perspective, but no enforcement happens at the network layer.
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
