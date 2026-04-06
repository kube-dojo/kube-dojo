---
title: "Module 1.1: Network Policies Deep Dive"
slug: k8s/cks/part1-cluster-setup/module-1.1-network-policies
sidebar:
  order: 1
lab:
  id: cks-1.1-network-policies
  url: https://killercoda.com/kubedojo/scenario/cks-1.1-network-policies
  duration: "35 min"
  difficulty: advanced
  environment: kubernetes
---
> **Complexity**: `[MEDIUM]` - Core CKS skill
>
> **Time to Complete**: 45-50 minutes
>
> **Prerequisites**: CKA networking knowledge, basic NetworkPolicy experience

---

## What You'll Be Able to Do

After completing this module, you will be able to:

1. **Create** ingress and egress NetworkPolicies that enforce least-privilege pod communication
2. **Debug** connectivity failures caused by missing or overly restrictive policies
3. **Implement** default-deny policies and selectively allow required traffic flows
4. **Audit** existing NetworkPolicies to identify gaps that permit lateral movement

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

> **What would happen if**: You create a default-deny-egress NetworkPolicy but forget to add a DNS allow rule. You then deploy a new application that connects to `postgres.database.svc.cluster.local`. What error does the application see, and why is this confusing to debug?

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

> **Stop and think**: You apply a default-deny-ingress NetworkPolicy to a namespace, then create an allow rule for `app: frontend` to reach `app: api`. But a new pod `app: debug` deployed in the same namespace can still reach `app: api`. Why? (Hint: think about how NetworkPolicies are additive.)

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

> **Pause and predict**: In the multi-tier policy above, the web tier allows ingress only from the ingress-nginx namespace. But what if an attacker compromises a pod in the ingress-nginx namespace that is *not* the ingress controller? Would they get access to the web tier?

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

1. **A security audit reveals that your production namespace has a default-deny-ingress NetworkPolicy, but the API pod is still receiving traffic from pods in the `kube-system` namespace. The team is confused because the deny-all should block everything. What's happening?**
   <details>
   <summary>Answer</summary>
   A NetworkPolicy with `policyTypes: [Ingress]` and no ingress rules denies all ingress to selected pods *from within the NetworkPolicy's enforcement scope*. However, if your CNI plugin doesn't enforce policies on system namespaces, or if there's a second NetworkPolicy that allows traffic from `kube-system` (policies are additive -- the union of all rules applies), traffic will still flow. Check for additional policies with `kubectl get networkpolicies -n production` and verify your CNI enforces policies on all namespaces.
   </details>

2. **You write a NetworkPolicy to allow the `monitoring` namespace to scrape metrics from production pods. It uses `namespaceSelector: {matchLabels: {name: monitoring}}`. Prometheus can't reach the pods. You verify Prometheus is running in the `monitoring` namespace. What did you miss?**
   <details>
   <summary>Answer</summary>
   The `monitoring` namespace likely doesn't have the label `name: monitoring`. Kubernetes namespaces don't automatically get a `name` label matching their name (though `kubernetes.io/metadata.name` is auto-applied in newer versions). You need to explicitly label it: `kubectl label namespace monitoring name=monitoring`. This is a common exam gotcha -- always verify namespace labels with `kubectl get namespace monitoring --show-labels` before writing namespaceSelector rules.
   </details>

3. **During a penetration test, the tester creates a pod in the `production` namespace and successfully curls the database pod. Your NetworkPolicy allows ingress to the database only from pods with `app: api`. The tester's pod has no labels. How did they get through?**
   <details>
   <summary>Answer</summary>
   Check whether you have separate `from` items (OR logic) versus combined selectors (AND logic) in your policy. If the policy has `- podSelector: {matchLabels: {app: api}}` and `- namespaceSelector: {}` as separate list items, it means "from pods labeled `app: api` OR from any namespace" -- the OR makes it too permissive. To require both, put them in the same item: `- podSelector: {matchLabels: {app: api}}` combined with `namespaceSelector` in a single `from` entry. Also verify the policy actually selects the database pod with the correct `podSelector`.
   </details>

4. **After applying a default-deny-egress NetworkPolicy, your application pods can't connect to external APIs. You add an egress rule allowing `0.0.0.0/0`. The pods still can't connect -- `curl` returns "Could not resolve host." What's the root cause?**
   <details>
   <summary>Answer</summary>
   Even though you allowed all egress IP traffic, DNS resolution uses UDP port 53 to kube-dns pods in the `kube-system` namespace. Without an explicit DNS egress rule, pods can't resolve hostnames, so all connections to domain names fail (even though IP-based connections would work). Add a DNS egress rule allowing UDP/TCP port 53 to kube-dns pods. This is the most common NetworkPolicy mistake and catches many CKS candidates.
   </details>

---

## Hands-On Exercise

In this exercise, you will secure a three-tier application (web, api, db) by writing and debugging NetworkPolicies.

### Setup

Run the following commands to create the environment:

```bash
kubectl create namespace exercise
kubectl label namespace exercise name=exercise

kubectl run web --image=nginx -n exercise --labels="tier=web" --port=80
kubectl run api --image=nginx -n exercise --labels="tier=api" --port=80
kubectl run db --image=nginx -n exercise --labels="tier=db" --port=80

kubectl wait --for=condition=Ready pod --all -n exercise
```

### Task 1: Establish a Baseline

Write and apply a NetworkPolicy named `default-deny` in the `exercise` namespace that denies **all** ingress traffic to all pods in the namespace.

> **Hint**: Select all pods using an empty `podSelector` and specify the `Ingress` policy type with no rules.

<details>
<summary>View Solution</summary>

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny
  namespace: exercise
spec:
  podSelector: {}
  policyTypes:
  - Ingress
```
</details>

Verify that the `api` pod can no longer reach the `db` pod:

```bash
kubectl exec -n exercise api -- curl -s --connect-timeout 2 db || echo "Blocked (expected)"
```

### Task 2: Allow Web to API

Write a NetworkPolicy named `allow-web-to-api` that allows pods labeled `tier=web` to connect to pods labeled `tier=api` on port 80.

<details>
<summary>View Solution</summary>

```yaml
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
```
</details>

### Task 3: Allow API to DB

Write a NetworkPolicy named `allow-api-to-db` that allows pods labeled `tier=api` to connect to pods labeled `tier=db` on port 80.

<details>
<summary>View Solution</summary>

```yaml
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
```
</details>

Verify your policies:

```bash
kubectl exec -n exercise web -- curl -s --connect-timeout 2 api  # Should work
kubectl exec -n exercise api -- curl -s --connect-timeout 2 db   # Should work
kubectl exec -n exercise web -- curl -s --connect-timeout 2 db   # Should fail
```

### Task 4: Audit and Debug a Broken Policy

A junior engineer attempted to allow a new `metrics` pod to scrape the `db` pod on port 80, but the metrics pod is receiving "Connection refused" or timing out.

Apply their broken policy and the metrics pod:

```bash
kubectl run metrics --image=nginx -n exercise --labels="tier=metrics"

cat <<EOF | kubectl apply -f -
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-metrics-to-db
  namespace: exercise
spec:
  podSelector:
    matchLabels:
      tier: metrics
  policyTypes:
  - Ingress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          tier: db
    ports:
    - port: 80
EOF
```

**Your Task**: Identify the logical error in the policy above, delete it, and write the correct policy so that the `metrics` pod can curl the `db` pod.

> **Hint**: Look closely at the `podSelector` vs `ingress.from.podSelector`. Who is the target, and who is the source?

<details>
<summary>View Solution</summary>

The broken policy was applied to the `metrics` pod (target) and allowed ingress *from* the `db` pod. It should be applied to the `db` pod (target) and allow ingress *from* the `metrics` pod.

```bash
kubectl delete networkpolicy allow-metrics-to-db -n exercise
```

**Correct Policy:**

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-metrics-to-db
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
          tier: metrics
    ports:
    - port: 80
```

Apply the correct policy, then verify:

```bash
kubectl exec -n exercise metrics -- curl -s --connect-timeout 2 db  # Should work
```
</details>

### Cleanup

```bash
kubectl delete namespace exercise
```

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