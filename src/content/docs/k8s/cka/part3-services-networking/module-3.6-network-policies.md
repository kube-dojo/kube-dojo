---
title: "Module 3.6: Network Policies"
slug: k8s/cka/part3-services-networking/module-3.6-network-policies
sidebar:
  order: 7
---
> **Complexity**: `[MEDIUM]` - Pod-level firewalling
>
> **Time to Complete**: 45-55 minutes
>
> **Prerequisites**: Module 3.1 (Services), Module 2.1 (Pods)

---

## Why This Module Matters

By default, Kubernetes allows all pods to communicate with all other pods—a **flat network** with no restrictions. Network Policies let you control this traffic, implementing **microsegmentation** for security. Without Network Policies, a compromised pod can freely communicate with every other pod in the cluster.

The CKA exam frequently tests Network Policies. You'll need to create ingress/egress rules, understand selectors, and debug policy issues quickly.

> **The Apartment Building Analogy**
>
> Imagine a Kubernetes cluster as an apartment building where every apartment door is unlocked. Any tenant can walk into any other apartment. Network Policies are like installing locks on doors and giving keys only to specific people. You decide who can enter (ingress) and where tenants can go (egress).

---

## What You'll Learn

By the end of this module, you'll be able to:
- Understand when pods are isolated by Network Policies
- Create ingress and egress rules
- Use pod, namespace, and IP block selectors
- Allow DNS traffic properly
- Debug Network Policy issues

---

## Did You Know?

- **NetworkPolicy is just a spec**: The API server accepts NetworkPolicy objects, but without a CNI that supports them (like Calico, Cilium, or Weave), they're ignored.

- **Default deny is powerful**: A single "deny all" policy instantly blocks all traffic to selected pods. This is a common security pattern.

- **Order doesn't matter**: Unlike traditional firewalls, NetworkPolicy rules are additive. If any policy allows traffic, it's allowed. There's no "deny" rule—just absence of "allow".

---

## Part 1: Network Policy Fundamentals

### 1.1 How Network Policies Work

```
┌────────────────────────────────────────────────────────────────┐
│                   Network Policy Flow                           │
│                                                                 │
│   Without NetworkPolicy:                                       │
│   ┌─────────────────────────────────────────────────────────┐  │
│   │  All pods can talk to all pods (flat network)           │  │
│   │                                                          │  │
│   │  Pod A ◄────────────────────────────► Pod B             │  │
│   │    │                                    │               │  │
│   │    │◄──────────────────────────────────►│               │  │
│   │    │            Pod C                   │               │  │
│   │    └──────────────────────────────────────►Pod D        │  │
│   └─────────────────────────────────────────────────────────┘  │
│                                                                 │
│   With NetworkPolicy selecting Pod B:                          │
│   ┌─────────────────────────────────────────────────────────┐  │
│   │  Pod B is now isolated (only allowed traffic permitted) │  │
│   │                                                          │  │
│   │  Pod A ────────────────────────────X──► Pod B           │  │
│   │    │                                    │               │  │
│   │    │◄──────────────────────────────────►│               │  │
│   │    │            Pod C                   │               │  │
│   │    └──────────────────────────────────────►Pod D        │  │
│   │                                                          │  │
│   │  (Pod B ingress blocked unless explicitly allowed)      │  │
│   └─────────────────────────────────────────────────────────┘  │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
```

### 1.2 Key Concepts

| Concept | Description |
|---------|-------------|
| **Ingress** | Traffic coming INTO the pod |
| **Egress** | Traffic going OUT from the pod |
| **podSelector** | Which pods the policy applies to |
| **Isolated pods** | Pods selected by any NetworkPolicy |
| **Additive rules** | Multiple policies = union of all rules |

### 1.3 When Are Pods Isolated?

A pod is isolated when:
1. A NetworkPolicy selects it (via `spec.podSelector`)
2. The policy type matches the traffic direction (ingress/egress)

Once isolated:
- **Ingress isolated**: Only traffic explicitly allowed by ingress rules is permitted
- **Egress isolated**: Only traffic explicitly allowed by egress rules is permitted

```yaml
# This policy makes pods with app=web isolated for INGRESS
# (they can still make outbound connections)
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: isolate-ingress
spec:
  podSelector:
    matchLabels:
      app: web         # Selects these pods
  policyTypes:
  - Ingress            # Only ingress is affected
```

---

## Part 2: Basic Network Policies

### 2.1 Deny All Ingress (Default Deny)

```yaml
# Deny all incoming traffic to pods in namespace
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: deny-all-ingress
  namespace: production
spec:
  podSelector: {}        # Empty = select ALL pods
  policyTypes:
  - Ingress              # No ingress rules = deny all ingress
```

### 2.2 Deny All Egress

```yaml
# Deny all outgoing traffic from pods in namespace
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: deny-all-egress
  namespace: production
spec:
  podSelector: {}        # All pods
  policyTypes:
  - Egress               # No egress rules = deny all egress
```

### 2.3 Deny All (Both Directions)

```yaml
# Complete lockdown
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: deny-all
spec:
  podSelector: {}
  policyTypes:
  - Ingress
  - Egress
```

### 2.4 Allow All Ingress

```yaml
# Explicitly allow all ingress (useful to override deny policies)
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-all-ingress
spec:
  podSelector: {}
  policyTypes:
  - Ingress
  ingress:
  - {}                   # Empty rule = allow all
```

### 2.5 Allow All Egress

```yaml
# Explicitly allow all egress
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-all-egress
spec:
  podSelector: {}
  policyTypes:
  - Egress
  egress:
  - {}                   # Empty rule = allow all
```

---

## Part 3: Selective Policies

### 3.1 Allow Ingress from Specific Pods

```yaml
# Allow traffic from pods with label app=frontend
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-frontend
spec:
  podSelector:
    matchLabels:
      app: backend         # This policy applies to backend pods
  policyTypes:
  - Ingress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: frontend    # Allow traffic from frontend pods
```

```
┌────────────────────────────────────────────────────────────────┐
│                   Pod Selector Example                          │
│                                                                 │
│   ┌─────────────────┐         ┌─────────────────┐             │
│   │  Pod            │         │  Pod            │             │
│   │  app: frontend  │────────►│  app: backend   │             │
│   │                 │    ✓    │                 │             │
│   └─────────────────┘         └─────────────────┘             │
│                                                                 │
│   ┌─────────────────┐         ┌─────────────────┐             │
│   │  Pod            │         │  Pod            │             │
│   │  app: other     │────X───►│  app: backend   │             │
│   │                 │    ✗    │                 │             │
│   └─────────────────┘         └─────────────────┘             │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
```

### 3.2 Allow Ingress from Namespace

```yaml
# Allow traffic from all pods in namespace "monitoring"
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-monitoring
spec:
  podSelector:
    matchLabels:
      app: backend
  policyTypes:
  - Ingress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: monitoring    # Namespace must have this label
```

> **Important**: Namespaces need labels! Add with:
> ```bash
> k label namespace monitoring name=monitoring
> ```

### 3.3 Allow Ingress from IP Block

```yaml
# Allow traffic from specific IP ranges
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-external
spec:
  podSelector:
    matchLabels:
      app: web
  policyTypes:
  - Ingress
  ingress:
  - from:
    - ipBlock:
        cidr: 192.168.1.0/24      # Allow this range
        except:
        - 192.168.1.100/32        # Except this IP
```

### 3.4 Allow Ingress on Specific Ports

```yaml
# Allow HTTP and HTTPS only
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-web-ports
spec:
  podSelector:
    matchLabels:
      app: web
  policyTypes:
  - Ingress
  ingress:
  - from:
    - podSelector: {}            # From any pod
    ports:
    - protocol: TCP
      port: 80
    - protocol: TCP
      port: 443
```

---

## Part 4: Combining Selectors

### 4.1 AND vs OR Logic

```yaml
# OR logic: from frontend pods OR from monitoring namespace
ingress:
- from:
  - podSelector:
      matchLabels:
        app: frontend
- from:
  - namespaceSelector:
      matchLabels:
        name: monitoring
```

```yaml
# AND logic: from frontend pods IN monitoring namespace
ingress:
- from:
  - podSelector:
      matchLabels:
        app: frontend
    namespaceSelector:
      matchLabels:
        name: monitoring
```

```
┌────────────────────────────────────────────────────────────────┐
│                   Selector Logic                                │
│                                                                 │
│   Two separate "from" items = OR                               │
│   - from:                                                       │
│     - podSelector: {app: A}     # Match A                      │
│   - from:                                                       │
│     - podSelector: {app: B}     # OR match B                   │
│                                                                 │
│   Same "from" item = AND                                       │
│   - from:                                                       │
│     - podSelector: {app: A}     # Match A                      │
│       namespaceSelector: {x: y}  # AND in namespace with x=y   │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
```

### 4.2 Complex Example

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: complex-policy
spec:
  podSelector:
    matchLabels:
      app: api
  policyTypes:
  - Ingress
  - Egress
  ingress:
  # Rule 1: Allow from frontend in same namespace
  - from:
    - podSelector:
        matchLabels:
          app: frontend
    ports:
    - port: 8080
  # Rule 2: Allow from any pod in monitoring namespace
  - from:
    - namespaceSelector:
        matchLabels:
          name: monitoring
    ports:
    - port: 9090
  egress:
  # Rule 1: Allow to database pods
  - to:
    - podSelector:
        matchLabels:
          app: database
    ports:
    - port: 5432
  # Rule 2: Allow DNS
  - to:
    - namespaceSelector: {}
    ports:
    - port: 53
      protocol: UDP
    - port: 53
      protocol: TCP
```

---

## Part 5: Egress Policies

### 5.1 Allow Egress to Specific Pods

```yaml
# Backend can only talk to database
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: backend-egress
spec:
  podSelector:
    matchLabels:
      app: backend
  policyTypes:
  - Egress
  egress:
  - to:
    - podSelector:
        matchLabels:
          app: database
    ports:
    - port: 5432
```

### 5.2 Allow DNS (Critical!)

When restricting egress, you must allow DNS or pods can't resolve service names:

```yaml
# Allow DNS to kube-system
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
    - namespaceSelector:
        matchLabels:
          kubernetes.io/metadata.name: kube-system
    ports:
    - port: 53
      protocol: UDP
    - port: 53
      protocol: TCP
```

### 5.3 Allow External Traffic

```yaml
# Allow egress to external IPs
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-external
spec:
  podSelector:
    matchLabels:
      app: web
  policyTypes:
  - Egress
  egress:
  - to:
    - ipBlock:
        cidr: 0.0.0.0/0        # All IPs
        except:
        - 10.0.0.0/8           # Except private ranges
        - 172.16.0.0/12
        - 192.168.0.0/16
```

---

## Part 6: Debugging Network Policies

### 6.1 Debugging Workflow

```
Network Policy Issue?
    │
    ├── Does CNI support NetworkPolicy?
    │   (Calico, Cilium, Weave = yes; Flannel = no)
    │
    ├── kubectl get networkpolicy -n <namespace>
    │   (List policies affecting pods)
    │
    ├── kubectl describe networkpolicy <name>
    │   (Check selectors and rules)
    │
    ├── Check pod labels match
    │   kubectl get pods --show-labels
    │
    ├── Check namespace labels (for namespaceSelector)
    │   kubectl get namespace --show-labels
    │
    └── Test connectivity
        kubectl exec <pod> -- nc -zv <target> <port>
```

### 6.2 Common Commands

```bash
# List network policies
k get networkpolicy
k get netpol                 # Short form

# Describe policy
k describe networkpolicy <name>

# Check pod labels
k get pods --show-labels

# Check namespace labels
k get namespaces --show-labels

# Test connectivity
k exec <pod> -- nc -zv <service> <port>
k exec <pod> -- wget --spider --timeout=1 http://<service>
k exec <pod> -- curl -s --max-time 1 http://<service>
```

### 6.3 Common Issues

| Symptom | Cause | Solution |
|---------|-------|----------|
| Policy not enforced | CNI doesn't support | Use Calico, Cilium, or Weave |
| Can't resolve DNS | DNS egress blocked | Add egress rule for port 53 |
| Cross-namespace blocked | namespaceSelector wrong | Label namespaces, check selector |
| All traffic blocked | Empty podSelector in deny | Create allow rules for needed traffic |
| Pods can still communicate | Labels don't match | Verify podSelector matches pod labels |

---

## Part 7: Common Patterns

### 7.1 Database Protection

```yaml
# Only allow backend pods to access database
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: db-protection
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
          app: backend
    ports:
    - port: 5432
```

### 7.2 Three-Tier Application

```yaml
# Web tier - only from ingress controller
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: web-policy
spec:
  podSelector:
    matchLabels:
      tier: web
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: ingress-nginx
  policyTypes:
  - Ingress
---
# App tier - only from web tier
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: app-policy
spec:
  podSelector:
    matchLabels:
      tier: app
  ingress:
  - from:
    - podSelector:
        matchLabels:
          tier: web
  policyTypes:
  - Ingress
---
# DB tier - only from app tier
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: db-policy
spec:
  podSelector:
    matchLabels:
      tier: db
  ingress:
  - from:
    - podSelector:
        matchLabels:
          tier: app
    ports:
    - port: 5432
  policyTypes:
  - Ingress
```

### 7.3 Namespace Isolation

```yaml
# Default deny all, then allow within namespace only
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: namespace-isolation
spec:
  podSelector: {}
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - podSelector: {}      # Same namespace only
  egress:
  - to:
    - podSelector: {}      # Same namespace only
  - to:                    # Plus DNS
    - namespaceSelector: {}
    ports:
    - port: 53
      protocol: UDP
```

---

## Common Mistakes

| Mistake | Problem | Solution |
|---------|---------|----------|
| Using unsupported CNI | Policies ignored | Switch to Calico, Cilium, or Weave |
| Forgetting DNS egress | Pods can't resolve names | Add port 53 UDP/TCP egress |
| Unlabeled namespaces | namespaceSelector fails | Label namespaces first |
| Wrong selector logic | Too permissive/restrictive | Check AND vs OR (same from vs separate) |
| Empty ingress array | Blocks all ingress | Use `ingress: [{}]` to allow all |

---

## Quiz

1. **What happens when a NetworkPolicy selects a pod?**
   <details>
   <summary>Answer</summary>
   The pod becomes "isolated" for the policy types specified (Ingress/Egress). Traffic not explicitly allowed by rules is denied.
   </details>

2. **How do you deny all ingress traffic to pods in a namespace?**
   <details>
   <summary>Answer</summary>
   Create a NetworkPolicy with empty `podSelector: {}` (selects all pods), `policyTypes: [Ingress]`, and no `ingress` rules.
   </details>

3. **What's the difference between these two ingress rules?**
   ```yaml
   # Version A
   ingress:
   - from:
     - podSelector: {matchLabels: {app: a}}
     - namespaceSelector: {matchLabels: {name: x}}

   # Version B
   ingress:
   - from:
     - podSelector: {matchLabels: {app: a}}
       namespaceSelector: {matchLabels: {name: x}}
   ```
   <details>
   <summary>Answer</summary>
   Version A uses OR logic: allows from pods with `app=a` OR from any pod in namespace with `name=x`.
   Version B uses AND logic: allows only from pods with `app=a` that are also in namespace with `name=x`.
   </details>

4. **Why is allowing DNS egress important?**
   <details>
   <summary>Answer</summary>
   Pods need DNS to resolve service names. Without port 53 egress, pods can't look up `my-service.default.svc.cluster.local`, breaking service discovery.
   </details>

5. **NetworkPolicy is created but traffic isn't blocked. What's wrong?**
   <details>
   <summary>Answer</summary>
   Most likely the CNI plugin doesn't support NetworkPolicy. Flannel, for example, doesn't enforce NetworkPolicy. Use Calico, Cilium, or Weave.
   </details>

---

## Hands-On Exercise

**Task**: Implement network policies for a three-tier application.

**Steps**:

1. **Create test pods**:
```bash
# Create pods with different roles
k run frontend --image=nginx --labels="tier=frontend"
k run backend --image=nginx --labels="tier=backend"
k run database --image=nginx --labels="tier=database"

# Wait for pods to be ready
k wait --for=condition=ready pod/frontend pod/backend pod/database --timeout=60s
```

2. **Verify default connectivity** (everything should work):
```bash
BACKEND_IP=$(k get pod backend -o jsonpath='{.status.podIP}')
k exec frontend -- wget --spider --timeout=1 http://$BACKEND_IP
# Should succeed
```

3. **Create deny-all policy**:
```bash
cat << 'EOF' | k apply -f -
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: deny-all
spec:
  podSelector: {}
  policyTypes:
  - Ingress
EOF
```

4. **Test connectivity** (should fail if CNI supports it):
```bash
k exec frontend -- wget --spider --timeout=1 http://$BACKEND_IP
# Should timeout (if CNI supports NetworkPolicy)
```

5. **Allow frontend to backend**:
```bash
cat << 'EOF' | k apply -f -
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-frontend-to-backend
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
```

6. **Test again**:
```bash
k exec frontend -- wget --spider --timeout=1 http://$BACKEND_IP
# Should succeed now

# But database to backend should still fail
DATABASE_IP=$(k get pod database -o jsonpath='{.status.podIP}')
k exec database -- wget --spider --timeout=1 http://$BACKEND_IP
# Should fail
```

7. **Allow backend to database**:
```bash
cat << 'EOF' | k apply -f -
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-backend-to-database
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
    - port: 80
EOF
```

8. **List all policies**:
```bash
k get networkpolicy
k describe networkpolicy
```

9. **Cleanup**:
```bash
k delete networkpolicy deny-all allow-frontend-to-backend allow-backend-to-database
k delete pod frontend backend database
```

**Success Criteria**:
- [ ] Understand default-allow behavior without policies
- [ ] Can create deny-all policies
- [ ] Can create selective allow policies
- [ ] Understand pod selector matching
- [ ] Can debug policy issues

---

## Practice Drills

### Drill 1: Deny All Ingress (Target: 2 minutes)

```bash
# Create pod
k run test-pod --image=nginx --labels="app=test"

# Create deny-all ingress
cat << 'EOF' | k apply -f -
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: deny-ingress
spec:
  podSelector:
    matchLabels:
      app: test
  policyTypes:
  - Ingress
EOF

# Verify
k describe networkpolicy deny-ingress

# Cleanup
k delete networkpolicy deny-ingress
k delete pod test-pod
```

### Drill 2: Allow from Specific Pod (Target: 3 minutes)

```bash
# Create pods
k run server --image=nginx --labels="role=server"
k run client --image=nginx --labels="role=client"
k run other --image=nginx --labels="role=other"

# Create policy allowing only client
cat << 'EOF' | k apply -f -
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-client
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

# Verify policy
k describe networkpolicy allow-client

# Cleanup
k delete networkpolicy allow-client
k delete pod server client other
```

### Drill 3: Allow from Namespace (Target: 4 minutes)

```bash
# Create namespace with label
k create namespace allowed
k label namespace allowed name=allowed

# Create pods
k run target --image=nginx --labels="app=target"
k run source --image=nginx -n allowed

# Create policy
cat << 'EOF' | k apply -f -
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-namespace
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
          name: allowed
EOF

# Verify
k describe networkpolicy allow-namespace

# Cleanup
k delete networkpolicy allow-namespace
k delete pod target
k delete namespace allowed
```

### Drill 4: Egress with DNS (Target: 4 minutes)

```bash
# Create pod
k run egress-test --image=nginx --labels="app=egress"

# Create egress policy with DNS
cat << 'EOF' | k apply -f -
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: egress-dns
spec:
  podSelector:
    matchLabels:
      app: egress
  policyTypes:
  - Egress
  egress:
  # Allow DNS
  - to:
    - namespaceSelector: {}
    ports:
    - port: 53
      protocol: UDP
    - port: 53
      protocol: TCP
  # Allow HTTPS
  - to: []
    ports:
    - port: 443
EOF

# Verify
k describe networkpolicy egress-dns

# Cleanup
k delete networkpolicy egress-dns
k delete pod egress-test
```

### Drill 5: Port-Specific Ingress (Target: 3 minutes)

```bash
# Create pod
k run web --image=nginx --labels="app=web"

# Allow only ports 80 and 443
cat << 'EOF' | k apply -f -
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: web-ports
spec:
  podSelector:
    matchLabels:
      app: web
  policyTypes:
  - Ingress
  ingress:
  - ports:
    - port: 80
      protocol: TCP
    - port: 443
      protocol: TCP
EOF

# Verify
k describe networkpolicy web-ports

# Cleanup
k delete networkpolicy web-ports
k delete pod web
```

### Drill 6: IP Block Policy (Target: 3 minutes)

```bash
# Create pod
k run ip-test --image=nginx --labels="app=ip-test"

# Create policy with IP block
cat << 'EOF' | k apply -f -
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: ip-block
spec:
  podSelector:
    matchLabels:
      app: ip-test
  policyTypes:
  - Ingress
  ingress:
  - from:
    - ipBlock:
        cidr: 10.0.0.0/8
        except:
        - 10.0.1.0/24
EOF

# Verify
k describe networkpolicy ip-block

# Cleanup
k delete networkpolicy ip-block
k delete pod ip-test
```

### Drill 7: Combined AND Selector (Target: 4 minutes)

```bash
# Create namespace
k create namespace restricted
k label namespace restricted name=restricted

# Create pod
k run secure --image=nginx --labels="app=secure"

# Create policy with AND logic
cat << 'EOF' | k apply -f -
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: and-policy
spec:
  podSelector:
    matchLabels:
      app: secure
  policyTypes:
  - Ingress
  ingress:
  - from:
    # AND: must be frontend pod IN restricted namespace
    - podSelector:
        matchLabels:
          role: frontend
      namespaceSelector:
        matchLabels:
          name: restricted
EOF

# Verify
k describe networkpolicy and-policy

# Cleanup
k delete networkpolicy and-policy
k delete pod secure
k delete namespace restricted
```

### Drill 8: Challenge - Complete Network Isolation

Without looking at solutions:

1. Create namespace `secure` with label `zone=secure`
2. Create pods: `app` (label: tier=app), `db` (label: tier=db)
3. Create deny-all ingress policy
4. Allow `app` to receive traffic from any pod in cluster
5. Allow `db` to receive traffic only from `app` pods, port 5432
6. Verify with `kubectl describe`
7. Cleanup everything

```bash
# YOUR TASK: Complete in under 7 minutes
```

<details>
<summary>Solution</summary>

```bash
# 1. Create namespace
k create namespace secure
k label namespace secure zone=secure

# 2. Create pods
k run app -n secure --image=nginx --labels="tier=app"
k run db -n secure --image=nginx --labels="tier=db"

# 3. Deny all ingress
cat << 'EOF' | k apply -f -
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: deny-all
  namespace: secure
spec:
  podSelector: {}
  policyTypes:
  - Ingress
EOF

# 4. Allow app from anywhere
cat << 'EOF' | k apply -f -
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-app
  namespace: secure
spec:
  podSelector:
    matchLabels:
      tier: app
  policyTypes:
  - Ingress
  ingress:
  - from:
    - namespaceSelector: {}
EOF

# 5. Allow db from app only
cat << 'EOF' | k apply -f -
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-db
  namespace: secure
spec:
  podSelector:
    matchLabels:
      tier: db
  policyTypes:
  - Ingress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          tier: app
    ports:
    - port: 5432
EOF

# 6. Verify
k get networkpolicy -n secure
k describe networkpolicy -n secure

# 7. Cleanup
k delete namespace secure
```

</details>

---

## Next Module

[Module 3.7: CNI & Cluster Networking](../module-3.7-cni/) - Understanding the Container Network Interface.
