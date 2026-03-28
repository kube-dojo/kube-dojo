---
title: "Module 1.2: Network Policy Design Patterns"
slug: platform/disciplines/networking/module-1.2-network-policy-design
sidebar:
  order: 3
---
> **Discipline Module** | Complexity: `[COMPLEX]` | Time: 60-70 min

## Prerequisites

Before starting this module:
- **Required**: [Module 1.1: CNI Architecture](../module-1.1-cni-architecture/) — Understanding which CNIs support policies
- **Required**: [Kubernetes Basics](../../../prerequisites/kubernetes-basics/) — Namespaces, labels, selectors
- **Recommended**: [Security Principles foundations](../../foundations/security-principles/) — Zero trust, defense in depth
- **Helpful**: Experience with firewall rules or security groups

---

## Why This Module Matters

In January 2024, a healthcare SaaS provider discovered that a compromised Pod in their staging namespace had been making API calls to their production database for three weeks. The attacker had exploited a known CVE in an unpatched logging sidecar, gained shell access, and then simply `curl`-ed the production PostgreSQL Service — because there were no network policies anywhere in the cluster. Every Pod could talk to every other Pod across every namespace.

The breach exposed 180,000 patient records. The regulatory fine under HIPAA was $2.1 million. The engineering team had "planned to add network policies" for over a year. The Kubernetes NetworkPolicy resources had been sitting in a `security/` directory in their Git repo, reviewed in three separate PRs, but never applied because "they might break something."

Network policies are the firewall rules of Kubernetes. Without them, your cluster is a flat network where any compromised Pod can reach any other Pod, any Service, and potentially any external endpoint. This module teaches you to design network policies that enforce zero-trust segmentation without accidentally cutting off legitimate traffic.

---

## Did You Know?

> A 2024 survey by Fairwinds found that **83% of Kubernetes clusters** have no network policies at all. Of the 17% that do, most only have policies in a single namespace. Full default-deny coverage across all namespaces is found in less than 3% of clusters.

> Kubernetes NetworkPolicy is **additive-only** — there is no "deny" rule. If no policy selects a Pod, all traffic is allowed. Once any policy selects a Pod, all traffic not explicitly allowed by some policy is denied. This "default-allow, first-policy-flips-to-deny" model confuses most people on first encounter.

> Cilium's L7 network policies can filter HTTP traffic by path, method, and headers — meaning you can write a policy that says "allow GET /api/v1/health but deny POST /api/v1/admin" at the network layer, without changing application code. Traditional K8s NetworkPolicy can only filter by L3/L4 (IP and port).

> The Kubernetes Network Policy API has remained essentially unchanged since its introduction in v1.7 (2017). The AdminNetworkPolicy and BaselineAdminNetworkPolicy resources (KEP-2091) are the first major evolution, adding cluster-scoped policies with explicit deny rules and priority ordering. They reached beta in K8s 1.32.

---

## Understanding the Kubernetes NetworkPolicy Model

### The Default: Allow Everything

With no NetworkPolicy resources, Kubernetes allows all traffic:

```
┌──────────────────────────────────────────────────────────┐
│                   Cluster (no policies)                    │
│                                                           │
│  ┌─────────┐   ←→   ┌─────────┐   ←→   ┌─────────┐     │
│  │ Pod A   │         │ Pod B   │         │ Pod C   │     │
│  │ (web)   │         │ (api)   │         │ (db)    │     │
│  └─────────┘         └─────────┘         └─────────┘     │
│       ↕                   ↕                   ↕           │
│  Everything talks to everything. No restrictions.         │
└──────────────────────────────────────────────────────────┘
```

### How NetworkPolicy Selection Works

A NetworkPolicy applies to Pods matched by its `podSelector`. Once a Pod is selected by *any* policy, the default for that Pod changes from "allow all" to "deny all" for the direction(s) specified (ingress and/or egress).

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: api-policy
  namespace: production
spec:
  podSelector:
    matchLabels:
      app: api          # This policy applies to Pods with app=api
  policyTypes:
    - Ingress           # Controls incoming traffic TO these Pods
    - Egress            # Controls outgoing traffic FROM these Pods
  ingress:
    - from:
        - podSelector:
            matchLabels:
              app: web  # Allow traffic FROM Pods with app=web
      ports:
        - port: 8080
          protocol: TCP
  egress:
    - to:
        - podSelector:
            matchLabels:
              app: db   # Allow traffic TO Pods with app=db
      ports:
        - port: 5432
          protocol: TCP
    - to:                # Allow DNS (required for name resolution)
        - namespaceSelector:
            matchLabels:
              kubernetes.io/metadata.name: kube-system
          podSelector:
            matchLabels:
              k8s-app: kube-dns
      ports:
        - port: 53
          protocol: UDP
        - port: 53
          protocol: TCP
```

The critical mental model:

```
Before any policy:     Pod is "open" — all traffic allowed
After first policy:    Pod is "closed" — only explicitly allowed traffic passes
More policies:         Union of all allow rules (policies are additive)
```

### The Selector Hierarchy

NetworkPolicy `from`/`to` rules can combine three selector types. Understanding how they compose is essential:

```yaml
ingress:
  - from:
      # These are OR'd (any match allows traffic):
      - podSelector:          # Match Pods in SAME namespace
          matchLabels:
            role: frontend
      - namespaceSelector:    # Match Pods in OTHER namespaces
          matchLabels:
            env: production
      - ipBlock:              # Match external IPs
          cidr: 10.0.0.0/8
          except:
            - 10.0.1.0/24
```

**Critical gotcha** — combining `podSelector` and `namespaceSelector` in the same rule item vs. separate items:

```yaml
# Rule A: Two separate items (OR logic)
# Allows: any Pod with role=frontend in SAME namespace
#    OR   any Pod in any namespace labeled env=production
- from:
    - podSelector:
        matchLabels:
          role: frontend
    - namespaceSelector:
        matchLabels:
          env: production

# Rule B: Combined in ONE item (AND logic)
# Allows: Pods with role=frontend that are ALSO
#         in a namespace labeled env=production
- from:
    - podSelector:
        matchLabels:
          role: frontend
      namespaceSelector:
        matchLabels:
          env: production
```

This is one of the most common sources of network policy misconfiguration. Rule A opens traffic to an entire namespace. Rule B is much more restrictive.

---

## Design Pattern 1: Default-Deny

The foundation of every secure cluster. Apply a deny-all policy in every namespace, then add specific allow rules.

### Deny All Ingress and Egress

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-all
  namespace: production
spec:
  podSelector: {}       # Empty selector = ALL Pods in namespace
  policyTypes:
    - Ingress
    - Egress
```

**Warning**: This blocks ALL traffic including DNS. Pods cannot resolve Service names. You must pair it with a DNS allow rule:

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
        - namespaceSelector:
            matchLabels:
              kubernetes.io/metadata.name: kube-system
          podSelector:
            matchLabels:
              k8s-app: kube-dns
      ports:
        - port: 53
          protocol: UDP
        - port: 53
          protocol: TCP
```

### Automating Default-Deny with Kyverno

Manually applying deny policies to every namespace is error-prone. Use a policy engine:

```yaml
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata:
  name: add-default-deny
spec:
  rules:
    - name: default-deny-ingress-egress
      match:
        any:
          - resources:
              kinds:
                - Namespace
              selector:
                matchExpressions:
                  - key: kubernetes.io/metadata.name
                    operator: NotIn
                    values: ["kube-system", "kube-public", "kube-node-lease"]
      generate:
        apiVersion: networking.k8s.io/v1
        kind: NetworkPolicy
        name: default-deny-all
        namespace: "{{request.object.metadata.name}}"
        synchronize: true
        data:
          spec:
            podSelector: {}
            policyTypes:
              - Ingress
              - Egress
    - name: allow-dns
      match:
        any:
          - resources:
              kinds:
                - Namespace
              selector:
                matchExpressions:
                  - key: kubernetes.io/metadata.name
                    operator: NotIn
                    values: ["kube-system", "kube-public", "kube-node-lease"]
      generate:
        apiVersion: networking.k8s.io/v1
        kind: NetworkPolicy
        name: allow-dns
        namespace: "{{request.object.metadata.name}}"
        synchronize: true
        data:
          spec:
            podSelector: {}
            policyTypes:
              - Egress
            egress:
              - to:
                  - namespaceSelector:
                      matchLabels:
                        kubernetes.io/metadata.name: kube-system
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

## Design Pattern 2: Namespace Isolation

Isolate namespaces so they cannot communicate with each other, then poke specific holes.

```
┌─────────────────────┐     ┌─────────────────────┐
│  namespace: frontend │     │  namespace: backend  │
│                      │     │                      │
│  ┌───┐ ┌───┐ ┌───┐ │ ──→ │  ┌───┐ ┌───┐ ┌───┐ │
│  │web│ │web│ │web│  │     │  │api│ │api│ │api│  │
│  └───┘ └───┘ └───┘ │     │  └───┘ └───┘ └───┘ │
│                      │     │    │                 │
└──────────────────────┘     └────┼────────────────┘
                                  │ (allowed)
                             ┌────▼────────────────┐
                             │  namespace: database │
                             │  ┌────┐ ┌────┐      │
                             │  │ pg │ │ pg │      │
                             │  └────┘ └────┘      │
                             └─────────────────────┘
```

```yaml
# In the 'backend' namespace: allow ingress only from 'frontend'
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-from-frontend
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
              kubernetes.io/metadata.name: frontend
          podSelector:
            matchLabels:
              app: web
      ports:
        - port: 8080
          protocol: TCP

---
# In the 'database' namespace: allow ingress only from 'backend'
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-from-backend
  namespace: database
spec:
  podSelector:
    matchLabels:
      app: postgresql
  policyTypes:
    - Ingress
  ingress:
    - from:
        - namespaceSelector:
            matchLabels:
              kubernetes.io/metadata.name: backend
          podSelector:
            matchLabels:
              app: api
      ports:
        - port: 5432
          protocol: TCP
```

---

## Design Pattern 3: Zero-Trust Microsegmentation

In zero-trust, every Pod-to-Pod communication path is explicitly defined. No implicit trust based on namespace membership.

### Application-Level Segmentation

```yaml
# Each microservice gets a specific policy
# Example: order-service can ONLY talk to:
#   - inventory-service (port 8080)
#   - payment-service (port 8443)
#   - postgresql (port 5432)
#   - kafka (port 9092)
# Nothing else.

apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: order-service-egress
  namespace: production
spec:
  podSelector:
    matchLabels:
      app: order-service
  policyTypes:
    - Egress
  egress:
    - to:
        - podSelector:
            matchLabels:
              app: inventory-service
      ports:
        - port: 8080
    - to:
        - podSelector:
            matchLabels:
              app: payment-service
      ports:
        - port: 8443
    - to:
        - podSelector:
            matchLabels:
              app: postgresql
      ports:
        - port: 5432
    - to:
        - podSelector:
            matchLabels:
              app: kafka
      ports:
        - port: 9092
    - to:                   # DNS
        - namespaceSelector:
            matchLabels:
              kubernetes.io/metadata.name: kube-system
          podSelector:
            matchLabels:
              k8s-app: kube-dns
      ports:
        - port: 53
          protocol: UDP
        - port: 53
          protocol: TCP
```

### Generating Policies from Observed Traffic

Writing policies from scratch is tedious and error-prone. Use observability tools to generate them:

```bash
# Using Cilium Hubble to observe actual traffic patterns
hubble observe --namespace production --output json | \
  jq -r '[.source.labels[], .destination.labels[]] | @csv' | \
  sort -u

# Using Calico's flow log visualization
# Enable flow logs in Calico Enterprise or Calico Cloud
# Then export the discovered traffic flows as NetworkPolicy YAML

# Using Inspektor Gadget (open source) — monitor traffic and suggest policies
kubectl gadget advise network-policy monitor --namespace production --timeout 60
```

---

## Extended Policies: Beyond Standard NetworkPolicy

### Cilium Network Policies

Cilium extends standard Kubernetes NetworkPolicy with L7 filtering, DNS-based policies, and identity-based rules:

```yaml
apiVersion: cilium.io/v2
kind: CiliumNetworkPolicy
metadata:
  name: api-l7-policy
  namespace: production
spec:
  endpointSelector:
    matchLabels:
      app: api-gateway
  ingress:
    - fromEndpoints:
        - matchLabels:
            app: web-frontend
      toPorts:
        - ports:
            - port: "8080"
              protocol: TCP
          rules:
            http:
              - method: GET
                path: "/api/v1/products.*"
              - method: POST
                path: "/api/v1/orders"
                headers:
                  - 'Content-Type: application/json'
  egress:
    - toEndpoints:
        - matchLabels:
            app: product-db
      toPorts:
        - ports:
            - port: "5432"
    - toFQDNs:                    # DNS-based egress
        - matchName: "api.stripe.com"
        - matchPattern: "*.amazonaws.com"
      toPorts:
        - ports:
            - port: "443"
```

### Calico GlobalNetworkPolicy

Calico provides cluster-scoped policies that apply across all namespaces:

```yaml
apiVersion: projectcalico.org/v3
kind: GlobalNetworkPolicy
metadata:
  name: deny-external-egress
spec:
  order: 100
  selector: "!has(allow-external)"       # All Pods WITHOUT this label
  types:
    - Egress
  egress:
    - action: Allow
      destination:
        nets:
          - 10.0.0.0/8                    # Allow internal traffic
          - 172.16.0.0/12
          - 192.168.0.0/16
    - action: Allow
      protocol: UDP
      destination:
        selector: "k8s-app == 'kube-dns'"
        ports: [53]
    - action: Deny                         # Deny everything else
```

### AdminNetworkPolicy (K8s 1.32+ Beta)

The new cluster-scoped policy API with explicit deny and priority:

```yaml
apiVersion: policy.networking.k8s.io/v1beta1
kind: AdminNetworkPolicy
metadata:
  name: cluster-deny-to-metadata
spec:
  priority: 10                      # Lower = higher priority
  subject:
    namespaces: {}                  # All namespaces
  egress:
    - name: deny-metadata-service
      action: Deny
      to:
        - networks:
            - 169.254.169.254/32   # Block cloud metadata service
      ports:
        - portNumber:
            port: 80
            protocol: TCP
```

### Policy API Comparison

| Feature | K8s NetworkPolicy | Cilium CNP | Calico GNP | AdminNetworkPolicy |
|---------|:--:|:--:|:--:|:--:|
| Scope | Namespace | Namespace | Cluster | Cluster |
| Explicit deny | No | No | Yes | Yes |
| L7 (HTTP) rules | No | Yes | Via Envoy | No |
| DNS-based egress | No | Yes | Yes | No |
| Priority ordering | No | No | Yes (order field) | Yes (priority field) |
| Label-based Pod selection | Yes | Yes | Yes | Yes |
| Status: K8s version | Stable (v1.7+) | Cilium-only | Calico-only | Beta (v1.32+) |

---

## Troubleshooting Network Policies

### Step 1: Verify Policies Are Being Enforced

```bash
# Check if your CNI supports NetworkPolicy
# Flannel: NO policy support
# Calico/Cilium: YES

# List all policies in a namespace
kubectl get networkpolicy -n production

# Describe a specific policy to verify selectors
kubectl describe networkpolicy api-policy -n production
```

### Step 2: Verify Pod Label Matching

```bash
# Check what Pods a policy selects
kubectl get pods -n production -l app=api --show-labels

# Check what namespaces match a namespaceSelector
kubectl get namespaces -l env=production
```

### Step 3: Test Connectivity

```bash
# From a test Pod, attempt to reach the target
kubectl run test-conn --image=busybox:1.36 -n frontend --rm -it --restart=Never -- \
  wget --timeout=3 -qO- http://api-service.backend.svc.cluster.local:8080/healthz

# If blocked, you'll see:
# wget: download timed out

# Using Cilium's policy verdict
cilium policy get -n production
cilium monitor --type drop -n production
```

### Step 4: Check for Common Issues

```bash
# Is DNS blocked? (Most common issue with default-deny)
kubectl run dns-test --image=busybox:1.36 -n production --rm -it --restart=Never -- \
  nslookup kubernetes.default.svc.cluster.local

# Are labels correct?
kubectl get pods -n production -o custom-columns=NAME:.metadata.name,LABELS:.metadata.labels

# Cilium: check endpoint identity and policy
cilium endpoint list
cilium policy trace --src-identity <id> --dst-identity <id> --dport 8080
```

---

## Common Mistakes

| Mistake | Why It Happens | How to Fix It |
|---------|---------------|---------------|
| Applying default-deny without DNS egress | DNS is "invisible" — people forget Pods need it | Always pair default-deny with a DNS-allow policy |
| Combining podSelector and namespaceSelector incorrectly (OR vs AND) | YAML indentation determines whether they're in the same or different list items | Use the two-item (OR) vs one-item (AND) patterns shown above; test with `kubectl describe` |
| Applying NetworkPolicy on a Flannel cluster | Flannel has no policy engine; resources are accepted but silently ignored | Switch to Calico or Cilium, or add Calico in policy-only mode |
| Not including egress rules for external APIs | Teams focus on ingress but forget Pods also need to reach external services | Audit egress requirements; add ipBlock or FQDN-based egress rules |
| Labeling Pods inconsistently | Helm chart labels differ from kubectl-created labels | Standardize label taxonomy across all deployments; use admission policies to enforce |
| Testing policies in production | "It worked in staging" — but staging has different Services and label patterns | Use `cilium policy trace` or `calicoctl check` to dry-run before applying |
| Missing port in policy rules | Allow the Pod selector but forget to specify the port | Always include `ports` in rules; omitting ports means "all ports" — which may be too permissive |

---

## Hands-On Exercises

### Exercise 1: Default-Deny with Selective Allow

```bash
# Create a kind cluster with Calico
cat <<'EOF' > kind-netpol.yaml
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
networking:
  disableDefaultCNI: true
  podSubnet: "10.244.0.0/16"
nodes:
  - role: control-plane
  - role: worker
EOF
kind create cluster --name netpol-lab --config kind-netpol.yaml

# Install Calico
kubectl create -f https://raw.githubusercontent.com/projectcalico/calico/v3.29/manifests/tigera-operator.yaml
cat <<'EOF' | kubectl apply -f -
apiVersion: operator.tigera.io/v1
kind: Installation
metadata:
  name: default
spec:
  calicoNetwork:
    ipPools:
      - name: default
        cidr: 10.244.0.0/16
        encapsulation: VXLANCrossSubnet
        natOutgoing: Enabled
EOF
kubectl wait --for=condition=ready pod -l k8s-app=calico-node -n calico-system --timeout=300s
```

**Task 1**: Deploy a 3-tier application.

```bash
# Create namespaces
kubectl create namespace frontend
kubectl create namespace backend
kubectl create namespace database

# Deploy components
kubectl run web --image=nginx:1.27 -n frontend -l app=web
kubectl run api --image=hashicorp/http-echo:0.2.3 -n backend -l app=api \
  -- -listen=:8080 -text="API OK"
kubectl run db --image=postgres:16 -n database -l app=db \
  --env=POSTGRES_PASSWORD=testpass

# Expose services
kubectl expose pod web -n frontend --port=80
kubectl expose pod api -n backend --port=8080
kubectl expose pod db -n database --port=5432

# Wait for all pods
kubectl wait --for=condition=ready pod -l app=web -n frontend --timeout=120s
kubectl wait --for=condition=ready pod -l app=api -n backend --timeout=120s
kubectl wait --for=condition=ready pod -l app=db -n database --timeout=120s
```

**Task 2**: Verify everything can talk to everything (before policies).

```bash
# From frontend, reach backend
kubectl run test -n frontend --rm -it --restart=Never --image=busybox:1.36 -- \
  wget --timeout=3 -qO- http://api.backend.svc.cluster.local:8080
# Expected: "API OK"

# From frontend, reach database (should NOT be allowed in a real setup)
kubectl run test -n frontend --rm -it --restart=Never --image=busybox:1.36 -- \
  sh -c "echo | nc -w 3 db.database.svc.cluster.local 5432 && echo CONNECTED || echo BLOCKED"
# Expected: CONNECTED (no policies yet)
```

**Task 3**: Apply default-deny and selective allow policies.

<details>
<summary>Solution: Default deny + allow rules</summary>

```bash
# Apply default-deny to all three namespaces
for NS in frontend backend database; do
cat <<EOF | kubectl apply -f -
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-all
  namespace: $NS
spec:
  podSelector: {}
  policyTypes:
    - Ingress
    - Egress
---
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-dns
  namespace: $NS
spec:
  podSelector: {}
  policyTypes:
    - Egress
  egress:
    - to:
        - namespaceSelector:
            matchLabels:
              kubernetes.io/metadata.name: kube-system
          podSelector:
            matchLabels:
              k8s-app: kube-dns
      ports:
        - port: 53
          protocol: UDP
        - port: 53
          protocol: TCP
EOF
done

# Allow frontend -> backend
cat <<'EOF' | kubectl apply -f -
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: web-egress-to-api
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
              kubernetes.io/metadata.name: backend
          podSelector:
            matchLabels:
              app: api
      ports:
        - port: 8080
---
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: api-ingress-from-web
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
              kubernetes.io/metadata.name: frontend
          podSelector:
            matchLabels:
              app: web
      ports:
        - port: 8080
EOF

# Allow backend -> database
cat <<'EOF' | kubectl apply -f -
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: api-egress-to-db
  namespace: backend
spec:
  podSelector:
    matchLabels:
      app: api
  policyTypes:
    - Egress
  egress:
    - to:
        - namespaceSelector:
            matchLabels:
              kubernetes.io/metadata.name: database
          podSelector:
            matchLabels:
              app: db
      ports:
        - port: 5432
---
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: db-ingress-from-api
  namespace: database
spec:
  podSelector:
    matchLabels:
      app: db
  policyTypes:
    - Ingress
  ingress:
    - from:
        - namespaceSelector:
            matchLabels:
              kubernetes.io/metadata.name: backend
          podSelector:
            matchLabels:
              app: api
      ports:
        - port: 5432
EOF
```

</details>

**Task 4**: Verify the policies work correctly.

```bash
# frontend -> backend: should work
kubectl run test -n frontend --rm -it --restart=Never --image=busybox:1.36 -- \
  wget --timeout=3 -qO- http://api.backend.svc.cluster.local:8080

# frontend -> database: should be BLOCKED
kubectl run test -n frontend --rm -it --restart=Never --image=busybox:1.36 -- \
  sh -c "echo | nc -w 3 db.database.svc.cluster.local 5432 && echo CONNECTED || echo BLOCKED"

# backend -> database: should work
kubectl run test -n backend --rm -it --restart=Never --image=busybox:1.36 -- \
  sh -c "echo | nc -w 3 db.database.svc.cluster.local 5432 && echo CONNECTED || echo BLOCKED"
```

**Success Criteria:**
- [ ] Applied default-deny policies to all three namespaces
- [ ] Frontend can reach backend API on port 8080
- [ ] Frontend CANNOT reach database directly
- [ ] Backend can reach database on port 5432
- [ ] DNS resolution works in all namespaces

### Exercise 2: Audit Policy Coverage

Write a script that checks which namespaces lack default-deny policies:

```bash
#!/bin/bash
echo "=== Network Policy Audit ==="
for NS in $(kubectl get namespaces -o jsonpath='{.items[*].metadata.name}'); do
  POLICIES=$(kubectl get networkpolicy -n "$NS" --no-headers 2>/dev/null | wc -l)
  HAS_DENY=$(kubectl get networkpolicy -n "$NS" -o json 2>/dev/null | \
    jq '[.items[] | select(.spec.podSelector == {} and .spec.policyTypes != null)] | length')
  if [ "$HAS_DENY" -gt 0 ]; then
    echo "[OK]    $NS — $POLICIES policies, has default-deny"
  elif [ "$POLICIES" -gt 0 ]; then
    echo "[WARN]  $NS — $POLICIES policies, NO default-deny"
  else
    echo "[FAIL]  $NS — no policies at all"
  fi
done
```

---

## War Story

**The "Allow All" That Wasn't**

A media streaming company had carefully crafted network policies for their 40-service platform. Every namespace had default-deny. Every service had explicit ingress and egress rules. The security team was proud of their zero-trust posture.

Then an engineer deployed a new `analytics-collector` service. The Helm chart included a NetworkPolicy, but it was templated with a variable that was never set:

```yaml
podSelector:
  matchLabels:
    app: {{ .Values.appName }}    # .Values.appName was empty
```

An empty `matchLabels` is a valid selector — it matches **all Pods** in the namespace. The policy's ingress rule allowed traffic from `app: web-frontend`. Combined with the empty podSelector, this policy allowed `web-frontend` to reach **every Pod** in the namespace, not just the analytics collector.

For 16 days, the web frontend could reach the payment processing service directly, bypassing the API gateway that enforced rate limiting and authentication. An automated penetration test finally caught it.

**Business impact**: The security team spent 120 hours auditing logs to confirm no unauthorized access had occurred. The incident led to mandatory policy validation in CI/CD — every NetworkPolicy now goes through `kubectl apply --dry-run=server` plus a custom admission webhook that rejects policies with empty podSelectors unless explicitly annotated.

**Lesson**: Network policies are code. Test them like code. An empty selector is not "no selector" — it's "select everything."

---

## Knowledge Check

<details>
<summary>1. In Kubernetes NetworkPolicy, what happens when you create a policy with an empty podSelector (podSelector: {}) and only specify Ingress in policyTypes?</summary>

An empty `podSelector` matches **all Pods** in the namespace. With only `Ingress` in `policyTypes`, this policy affects only incoming traffic — all ingress not explicitly allowed by any policy is denied for all Pods in the namespace. Egress remains unrestricted because it's not listed in `policyTypes`. This is the pattern for "default-deny ingress" — but remember, egress is still wide open unless you add `Egress` to `policyTypes` as well.
</details>

<details>
<summary>2. Why must you always include a DNS egress rule when using default-deny egress policies?</summary>

Pods resolve Service names (like `api.backend.svc.cluster.local`) through CoreDNS, which runs in `kube-system` namespace on port 53 UDP/TCP. A default-deny egress policy blocks ALL outbound traffic, including DNS queries. Without DNS, Pods cannot resolve any Service names — `wget http://api-service:8080` fails because it can't look up the IP. You must explicitly allow egress to kube-dns pods in kube-system on port 53.
</details>

<details>
<summary>3. What is the difference between Kubernetes NetworkPolicy and Cilium CiliumNetworkPolicy for egress to external services?</summary>

Standard Kubernetes NetworkPolicy can only filter egress by IP address (`ipBlock` with CIDR). If the external service's IP changes, the policy breaks. Cilium CiliumNetworkPolicy supports `toFQDNs` — you can specify DNS names like `api.stripe.com`, and Cilium resolves them and dynamically updates the allowed IPs. This is vastly more practical for real-world egress control where external service IPs are unpredictable.
</details>

<details>
<summary>4. Scenario: You applied a NetworkPolicy to allow ingress from Pods with label "app=web" but traffic is still blocked. What should you check first?</summary>

Check these in order: (1) Verify your CNI supports NetworkPolicy — Flannel does not. (2) Verify the source Pods actually have the label `app=web` with `kubectl get pods --show-labels`. (3) If the source is in a different namespace, verify you included a `namespaceSelector` — without it, `podSelector` only matches Pods in the **same** namespace. (4) Check that the `ports` field matches the actual port the target is listening on. (5) If using default-deny egress, verify the source namespace allows egress to the target.
</details>

<details>
<summary>5. How do AdminNetworkPolicy resources (K8s 1.32+) differ from standard NetworkPolicy?</summary>

AdminNetworkPolicy (ANP) has three key differences: (1) **Cluster-scoped** — they apply across all namespaces, not just one. (2) **Explicit deny** — unlike standard NetworkPolicy which is additive-only, ANP supports `Deny` and `Pass` actions. (3) **Priority ordering** — ANP resources have a numeric priority field; lower numbers are evaluated first. This lets cluster admins enforce security baselines (like blocking metadata service access) that namespace owners cannot override with their own policies. Standard NetworkPolicy remains for namespace-level, developer-managed rules.
</details>

<details>
<summary>6. Why is an empty matchLabels in a podSelector dangerous in a NetworkPolicy?</summary>

An empty `matchLabels: {}` matches **every Pod** in the namespace, not "no Pods." If your policy allows ingress from some source and you accidentally use an empty `podSelector`, you've granted that source access to every Pod in the namespace — not just the intended target. This is a common Helm templating bug where a variable is undefined, resulting in an empty selector. Always validate NetworkPolicy selectors, and consider using admission webhooks to reject policies with empty podSelectors unless they're explicitly intended (like default-deny).
</details>

<details>
<summary>7. Scenario: You have default-deny in the "payments" namespace. The payments service needs to call Stripe's API (api.stripe.com) on port 443. How do you allow this with standard Kubernetes NetworkPolicy?</summary>

You need an egress rule with an `ipBlock` specifying Stripe's IP ranges. The challenge is that Stripe's IPs can change. With standard NetworkPolicy: (1) Look up Stripe's published IP ranges, (2) create an egress rule with those CIDRs, (3) maintain and update the policy when IPs change. This is fragile. A better approach is to use Cilium's `toFQDNs` or route through an egress proxy with a known IP. Alternatively, allow egress to all external IPs on port 443 (less secure but more practical) with `ipBlock: {cidr: 0.0.0.0/0, except: [10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16]}`.
</details>

<details>
<summary>8. What happens if two NetworkPolicies in the same namespace have conflicting rules — one allows traffic from Pod A and another has no rule for Pod A?</summary>

There is no conflict. NetworkPolicies are **purely additive** (union). If Policy X allows traffic from Pod A to Pod B, and Policy Y selects Pod B but doesn't mention Pod A, the traffic is still allowed because Policy X allows it. The final allowed set is the union of all allow rules across all policies that select the target Pod. There is no way to "override" or "revoke" an allow rule with standard NetworkPolicy — you'd need AdminNetworkPolicy with an explicit Deny action for that.
</details>

---

## Summary

Network policies are the mechanism that transforms Kubernetes from a flat, trust-everyone network into a segmented, zero-trust environment. The key patterns are:

1. **Default-deny everywhere** — Start by blocking everything, then allow specific paths
2. **Namespace isolation** — Prevent cross-namespace traffic except where explicitly needed
3. **Microsegmentation** — Define allowed communication for each service individually
4. **Always allow DNS** — Every default-deny egress policy must include DNS
5. **Use extended policies** — Cilium CNP for L7, AdminNetworkPolicy for cluster-wide rules

Remember: NetworkPolicy resources are silently ignored if your CNI doesn't support them. Verify your CNI first.

## What's Next

In [Module 1.3: Service Mesh Architecture & Strategy](../module-1.3-service-mesh-strategy/), you'll explore when you need a service mesh for capabilities that network policies alone cannot provide — mTLS encryption, traffic splitting, L7 observability, and circuit breaking. You'll evaluate Istio, Linkerd, and Cilium's sidecarless mesh to make an informed decision for your platform.
