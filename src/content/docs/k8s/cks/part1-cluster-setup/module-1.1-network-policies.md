---
title: "Module 1.1: Network Policies Deep Dive"
slug: k8s/cks/part1-cluster-setup/module-1.1-network-policies
sidebar:
  order: 1
---
> **Complexity**: `[MEDIUM]` - Core CKS skill
>
> **Time to Complete**: 45-50 minutes
>
> **Prerequisites**: CKA networking knowledge, basic NetworkPolicy experience

---

## Why This Module Matters

NetworkPolicies are the firewall of Kubernetes. By default, all pods can communicate with all other pods—a security nightmare. NetworkPolicies let you define exactly which pods can talk to which, blocking lateral movement in case of compromise.

CKS tests NetworkPolicies heavily. You must write them quickly and correctly under exam pressure.

---

## The Default Problem

```
┌─────────────────────────────────────────────────────────────┐
│              DEFAULT KUBERNETES NETWORKING                  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Without NetworkPolicies:                                  │
│                                                             │
│    ┌─────────┐     ┌─────────┐     ┌─────────┐           │
│    │ Web Pod │◄───►│ API Pod │◄───►│ DB Pod  │           │
│    └────┬────┘     └────┬────┘     └────┬────┘           │
│         │               │               │                  │
│         └───────────────┼───────────────┘                  │
│                         │                                  │
│         ┌───────────────┼───────────────┐                  │
│         │               │               │                  │
│    ┌────┴────┐     ┌────┴────┐     ┌────┴────┐           │
│    │Attacker │◄───►│ Any Pod │◄───►│ Secrets │           │
│    │  Pod    │     │         │     │  Pod    │           │
│    └─────────┘     └─────────┘     └─────────┘           │
│                                                             │
│  ❌ Every pod can reach every other pod                    │
│  ❌ Compromised pod = access to everything                 │
│  ❌ No network segmentation                                │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## NetworkPolicy Fundamentals

### How They Work

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: example
  namespace: default
spec:
  # Which pods this policy applies to
  podSelector:
    matchLabels:
      app: web

  # Which directions to control
  policyTypes:
  - Ingress  # Incoming traffic
  - Egress   # Outgoing traffic

  # What's allowed IN
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: frontend
    ports:
    - port: 80

  # What's allowed OUT
  egress:
  - to:
    - podSelector:
        matchLabels:
          app: database
    ports:
    - port: 5432
```

### Key Concepts

```
┌─────────────────────────────────────────────────────────────┐
│              NETWORKPOLICY MENTAL MODEL                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  podSelector: WHO does this policy apply to?               │
│               (Empty = all pods in namespace)              │
│                                                             │
│  policyTypes: WHAT traffic directions to control?          │
│               - Ingress only                               │
│               - Egress only                                │
│               - Both                                       │
│                                                             │
│  ingress.from: WHO can send traffic TO selected pods?      │
│                                                             │
│  egress.to: WHERE can selected pods send traffic?          │
│                                                             │
│  ports: WHICH ports are allowed?                           │
│         (Omit = all ports)                                 │
│                                                             │
│  CRITICAL: No ingress/egress rules = DENY ALL              │
│            (if policyType is specified)                    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Essential Patterns

### Pattern 1: Default Deny All

```yaml
# Deny all ingress traffic to namespace
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-ingress
  namespace: secure
spec:
  podSelector: {}  # All pods
  policyTypes:
  - Ingress
  # No ingress rules = deny all ingress
---
# Deny all egress traffic from namespace
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-egress
  namespace: secure
spec:
  podSelector: {}
  policyTypes:
  - Egress
  # No egress rules = deny all egress
---
# Deny BOTH ingress and egress
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-all
  namespace: secure
spec:
  podSelector: {}
  policyTypes:
  - Ingress
  - Egress
```

### Pattern 2: Allow Specific Pod-to-Pod

```yaml
# Allow frontend pods to access api pods on port 8080
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-frontend-to-api
  namespace: production
spec:
  podSelector:
    matchLabels:
      app: api
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

### Pattern 3: Allow from Namespace

```yaml
# Allow any pod from 'monitoring' namespace
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-from-monitoring
  namespace: production
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
          name: monitoring
```

### Pattern 4: Allow to External CIDR

```yaml
# Allow egress to specific IP range
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-external-api
  namespace: production
spec:
  podSelector:
    matchLabels:
      app: backend
  policyTypes:
  - Egress
  egress:
  - to:
    - ipBlock:
        cidr: 10.0.0.0/8
        except:
        - 10.0.1.0/24  # Except this subnet
    ports:
    - port: 443
```

### Pattern 5: Allow DNS (Critical!)

```yaml
# Allow DNS - ALWAYS needed for egress policies
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
    - port: 53
      protocol: UDP
    - port: 53
      protocol: TCP
```

---

## Combining Selectors

### AND vs OR Logic

```yaml
# OR: Allow from EITHER namespace OR pods with label
ingress:
- from:
  - namespaceSelector:
      matchLabels:
        env: prod
  - podSelector:
      matchLabels:
        role: frontend

# AND: Allow from pods with label IN namespace with label
ingress:
- from:
  - namespaceSelector:
      matchLabels:
        env: prod
    podSelector:
      matchLabels:
        role: frontend
```

```
┌─────────────────────────────────────────────────────────────┐
│              SELECTOR COMBINATION RULES                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Two list items = OR                                       │
│  - from:                                                   │
│    - namespaceSelector: ...    # OR                        │
│    - podSelector: ...          # Match either              │
│                                                             │
│  Same item, multiple selectors = AND                       │
│  - from:                                                   │
│    - namespaceSelector: ...    # AND                       │
│      podSelector: ...          # Both must match           │
│                                                             │
│  ⚠️  This is a common exam gotcha!                         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Real Exam Scenarios

### Scenario 1: Isolate Database

```yaml
# Only API pods can reach database on port 5432
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: db-isolation
  namespace: production
spec:
  podSelector:
    matchLabels:
      app: database
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: api
    ports:
    - port: 5432
  egress: []  # No egress allowed
```

### Scenario 2: Multi-tier Application

```yaml
# Web tier: only from ingress controller
---
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: web-policy
  namespace: app
spec:
  podSelector:
    matchLabels:
      tier: web
  policyTypes:
  - Ingress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: ingress-nginx
    ports:
    - port: 80

# API tier: only from web tier
---
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: api-policy
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

# DB tier: only from API tier
---
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: db-policy
  namespace: app
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
          tier: api
    ports:
    - port: 5432
```

### Scenario 3: Block Metadata Service

```yaml
# Block access to cloud metadata (169.254.169.254)
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: block-metadata
  namespace: default
spec:
  podSelector: {}
  policyTypes:
  - Egress
  egress:
  - to:
    - ipBlock:
        cidr: 0.0.0.0/0
        except:
        - 169.254.169.254/32
```

---

## Debugging NetworkPolicies

```bash
# List policies in namespace
kubectl get networkpolicies -n production

# Describe policy details
kubectl describe networkpolicy db-isolation -n production

# Check if CNI supports NetworkPolicies
# (Calico, Cilium, Weave support them; Flannel doesn't!)
kubectl get pods -n kube-system | grep -E "calico|cilium|weave"

# Test connectivity
kubectl exec -it frontend-pod -- nc -zv api-pod 8080
kubectl exec -it frontend-pod -- curl -s api-pod:8080

# Check pod labels (policies match on labels!)
kubectl get pod -n production --show-labels
```

---

## Did You Know?

- **NetworkPolicies are additive.** If multiple policies select a pod, the union of all rules applies. You can't use one policy to override another.

- **The default behavior is allow-all.** NetworkPolicies only restrict—they don't explicitly allow. A pod with no policies selecting it allows all traffic.

- **DNS is often forgotten.** When you add egress policies, pods can't resolve DNS unless you explicitly allow UDP/TCP 53 to kube-dns.

- **Not all CNIs support NetworkPolicies.** Flannel doesn't. Calico, Cilium, and Weave do. Check your cluster!

- **Cilium goes beyond NetworkPolicies.** Cilium supports standard Kubernetes NetworkPolicies plus its own `CiliumNetworkPolicy` CRD for L7 (HTTP/gRPC) filtering, DNS-aware policies, and **transparent Pod-to-Pod encryption** (WireGuard or IPsec) without any application changes. If your CKS exam environment uses Cilium, you get network encryption essentially for free:

```yaml
# Enable Cilium transparent encryption (cluster-level)
# In Cilium Helm values or ConfigMap:
encryption:
  enabled: true
  type: wireguard  # or ipsec
```

---

## Common Mistakes

| Mistake | Why It Hurts | Solution |
|---------|--------------|----------|
| Forgetting DNS egress | Pods can't resolve names | Always allow DNS with egress policies |
| Wrong selector logic | Policy doesn't match intended pods | AND = same item, OR = separate items |
| Missing namespace labels | namespaceSelector doesn't match | Label namespaces with metadata |
| Testing from wrong pod | Thinks policy doesn't work | Verify source pod labels match |
| CNI doesn't support NP | Policy exists but not enforced | Use Calico, Cilium, or Weave |

---

## Quiz

1. **What happens if a NetworkPolicy specifies `policyTypes: [Ingress]` but has no `ingress` rules?**
   <details>
   <summary>Answer</summary>
   All ingress traffic to selected pods is denied. Specifying a policyType with no rules means "deny all for this type."
   </details>

2. **How do you allow traffic from any pod in a specific namespace?**
   <details>
   <summary>Answer</summary>
   Use `namespaceSelector` with labels matching that namespace. The namespace must have a label to select on, e.g., `namespaceSelector: {matchLabels: {name: monitoring}}`.
   </details>

3. **What's the difference between two `from` items vs two selectors in one `from` item?**
   <details>
   <summary>Answer</summary>
   Two `from` items = OR (match either). Two selectors in one item = AND (match both). This is critical for complex policies.
   </details>

4. **Why do egress policies often break DNS resolution?**
   <details>
   <summary>Answer</summary>
   DNS uses UDP port 53 to kube-dns pods. Egress policies that don't explicitly allow this block DNS, breaking name resolution for the affected pods.
   </details>

---

## Hands-On Exercise

**Task**: Create NetworkPolicies for a three-tier application.

```bash
# Setup
kubectl create namespace exercise
kubectl label namespace exercise name=exercise

# Create pods
kubectl run web --image=nginx -n exercise -l tier=web
kubectl run api --image=nginx -n exercise -l tier=api
kubectl run db --image=nginx -n exercise -l tier=db

# Wait for pods
kubectl wait --for=condition=Ready pod --all -n exercise

# Task 1: Create default deny all ingress
cat <<EOF | kubectl apply -f -
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny
  namespace: exercise
spec:
  podSelector: {}
  policyTypes:
  - Ingress
EOF

# Verify: api can't reach db anymore
kubectl exec -n exercise web -- curl -s --connect-timeout 2 db || echo "Blocked (expected)"

# Task 2: Allow web -> api on port 80
cat <<EOF | kubectl apply -f -
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-web-to-api
  namespace: exercise
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
    - port: 80
EOF

# Task 3: Allow api -> db on port 80
cat <<EOF | kubectl apply -f -
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-api-to-db
  namespace: exercise
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
          tier: api
    ports:
    - port: 80
EOF

# Verify
kubectl exec -n exercise web -- curl -s --connect-timeout 2 api  # Should work
kubectl exec -n exercise api -- curl -s --connect-timeout 2 db   # Should work
kubectl exec -n exercise web -- curl -s --connect-timeout 2 db   # Should fail

# Cleanup
kubectl delete namespace exercise
```

**Success criteria**: Web can reach API, API can reach DB, Web cannot directly reach DB.

---

## Summary

**NetworkPolicy essentials**:
- `podSelector`: Which pods the policy applies to
- `policyTypes`: Ingress, Egress, or both
- `ingress/egress`: What traffic is allowed

**Critical patterns**:
- Default deny: `podSelector: {}` with no rules
- Always allow DNS with egress policies
- AND vs OR: Same item = AND, separate items = OR

**Exam tips**:
- Label pods and namespaces correctly
- Test connectivity after applying policies
- Remember: no policy = allow all

---

## Next Module

[Module 1.2: CIS Benchmarks](../module-1.2-cis-benchmarks/) - Auditing cluster security with kube-bench.
