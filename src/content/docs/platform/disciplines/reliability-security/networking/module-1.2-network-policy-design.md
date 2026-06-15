---
title: "Module 1.2: Network Policy Design Patterns"
slug: platform/disciplines/reliability-security/networking/module-1.2-network-policy-design
sidebar:
  order: 3
revision_pending: false
---
> **Discipline Module** | Complexity: `[COMPLEX]` | Time: 60-70 min

## Prerequisites

Before starting this module:
- **Required**: [Module 1.1: CNI Architecture](../module-1.1-cni-architecture/) — Understanding which CNIs support policies
- **Required**: [Kubernetes Basics](/prerequisites/kubernetes-basics/) — Namespaces, labels, selectors
- **Recommended**: [Security Principles foundations](/platform/foundations/security-principles/) — Zero trust, defense in depth
- **Helpful**: Experience with firewall rules or security groups

## What You'll Be Able to Do

After completing this module, you will be able to:

- **Design network policy architectures that implement zero-trust networking across Kubernetes namespaces**
- **Implement Kubernetes NetworkPolicy and Cilium NetworkPolicy for fine-grained traffic control**
- **Build network policy testing workflows that validate connectivity rules before production deployment**
- **Analyze network traffic patterns to identify missing policies and over-permissive access rules**

## Why This Module Matters

Hypothetical scenario: A platform team runs a 200-node Kubernetes cluster hosting 40 microservices across eight namespaces. After months of operating without network policies, a vulnerability scanner flags a critical CVE in a logging sidecar container that is deployed cluster-wide. Before the team can patch it, an attacker exploits the vulnerability, gains shell access to a single log-shipper Pod in the monitoring namespace, and discovers that from that foothold they can `curl` every Service in every namespace — including the payments database. Three days of lateral movement go undetected because the cluster's flat network model treats every Pod-to-Pod connection as implicitly trusted.

This scenario is not hypothetical architecture — it is the default behavior of every Kubernetes cluster without NetworkPolicy resources. The Kubernetes networking model guarantees that every Pod can reach every other Pod by IP address, regardless of namespace or application boundary. This is a deliberate design choice that prioritizes compatibility and simplicity: any Pod can talk to any other Pod without NAT, without overlay complexity, and without pre-configuration. But it also means that a single compromised container inherits the full network reachability of the entire cluster. In security terms, the blast radius of any Pod compromise is every other Pod in the cluster.

Network policies are the mechanism that shrinks this blast radius from "the whole cluster" to "exactly the Pods this workload needs to talk to." They are the primitive that enables microsegmentation — the practice of defining allowed communication paths at the individual workload level rather than at the network perimeter. When applied systematically, network policies transform the Kubernetes flat network from a trust-everyone model into a zero-trust architecture where every connection is explicitly authorized. This module teaches you to design, implement, and validate those policies.

## The Architecture of Kubernetes Network Segmentation

### Why the Flat Network Needs Constraints

To understand network policy design, you must first internalize what happens without policies. The Kubernetes networking specification requires that every Pod receives a unique, cluster-routable IP address and that every Pod can communicate with every other Pod without NAT. This is the "flat pod network" that Module 1.1 described — it is what makes Kubernetes networking simple to operate. A Service in the `payments` namespace can be reached from a Pod in the `web` namespace simply by its DNS name, with no routing configuration required.

The tradeoff is that this flat network offers no isolation. Every Pod is effectively on the same broadcast domain, regardless of which namespace it occupies, which application it serves, or which team owns it. Namespaces provide administrative boundaries for RBAC, resource quotas, and naming — but they do not provide network isolation. A Pod in the `staging` namespace can reach a Pod in the `production` namespace on any port unless something explicitly prevents it.

This architecture creates a fundamental tension: Kubernetes optimizes for connectivity, but security demands constraint. Network policies resolve this tension by letting platform operators define exactly which connections are permitted, without breaking the underlying flat network model. The network remains flat — every Pod still has a routable IP — but the policy layer selectively allows or drops traffic at the Pod boundary.

### The Mental Model: Additive, Not Subtractive

Kubernetes NetworkPolicy has a semantic model that differs from traditional firewall rules in ways that consistently trip up learners. The single most important concept to internalize is that NetworkPolicy is **additive-only**. There is no deny rule, no ordering, and no priority. If three policies select the same Pod, the effective set of allowed traffic is the **union** of the allows specified by all three policies. You can never use a second policy to revoke or override an allowance created by the first.

This additive model has a practical consequence: you cannot write a NetworkPolicy that says "block traffic from IP range X." The only way to block traffic is to not allow it in the first place. This forces a specific design pattern — start from a position of denying everything, then add explicit allows — which we will explore as the default-deny baseline.

The second critical semantic is what happens when a Pod is first selected by any policy. Before any policy selects a Pod, that Pod operates in "allow-all" mode for both ingress and egress. The instant any policy selects a Pod, that Pod switches to "default-deny" for the direction(s) specified in the policy's `policyTypes` field. If the policy specifies only `Ingress`, the Pod's egress remains unrestricted. If the policy specifies both `Ingress` and `Egress`, the Pod becomes fully default-deny in both directions. This flip happens atomically when the first policy matches — there is no intermediate state.

The third semantic is that an empty `podSelector` — written as `podSelector: {}` — matches **every Pod** in the namespace. This is not a "no selector" or a null; it is a selector with zero constraints, which means it selects the entire set. This is the correct way to write a policy that applies namespace-wide, but it is also a common source of accidents when a Helm chart template variable is undefined and the rendered YAML inadvertently selects everything.

The fourth semantic involves how `podSelector` and `namespaceSelector` compose within a single `from` or `to` entry. When both selectors appear inside the **same** list item, they combine with AND semantics — the traffic source must match both the podSelector and the namespaceSelector. When they appear in **separate** list items, they combine with OR semantics — traffic matching either selector is allowed. This distinction is controlled purely by YAML indentation, and misinterpreting it is one of the most common policy bugs.

## Understanding the Kubernetes NetworkPolicy Model

### The Selector Hierarchy in Depth

NetworkPolicy `from` and `to` rules accept three types of selectors: `podSelector`, `namespaceSelector`, and `ipBlock`. Each rule item can contain one or more of these, and the composition logic determines precisely which traffic is matched.

A `podSelector` used alone — without a `namespaceSelector` — matches Pods in the **same namespace** as the NetworkPolicy resource. This is the intuitive case: a policy in the `production` namespace that selects `app: api` matches Pods with label `app=api` in `production`. To match Pods in a different namespace, you must pair a `namespaceSelector` with a `podSelector`. The `namespaceSelector` identifies the target namespace by its labels, and the `podSelector` then identifies Pods within that namespace.

An `ipBlock` selector matches traffic from (ingress) or to (egress) IP addresses outside the cluster. The `ipBlock` accepts a `cidr` field and an optional `except` field that carves out sub-ranges from the CIDR. This is the only mechanism for controlling traffic to external services with standard NetworkPolicy. The `except` field is particularly useful for patterns like "allow all external egress on port 443 except to cloud metadata endpoints."

The composite selector behavior is where most misconfigurations originate. Consider the following two rules and their fundamentally different meanings:

```yaml
# Rule A: Two separate items in the 'from' list (OR logic)
# Matches: any Pod with app=web in the SAME namespace
#       OR any Pod in any namespace labeled env=production
- from:
    - podSelector:
        matchLabels:
          app: web
    - namespaceSelector:
        matchLabels:
          env: production

# Rule B: Combined in ONE item (AND logic)
# Matches: Pods with app=web that are ALSO
#          in a namespace labeled env=production
- from:
    - podSelector:
        matchLabels:
          app: web
      namespaceSelector:
        matchLabels:
          env: production
```

Rule A creates a much wider aperture. The first item allows any `app=web` Pod in the policy's own namespace. The second item allows any Pod at all — of any label — that happens to reside in a namespace labeled `env=production`. Rule B is far more restrictive: it only allows `app=web` Pods that are specifically located in `env=production` namespaces. The difference between these two rules is whether `namespaceSelector` is indented under the same hyphen as `podSelector` or under its own hyphen. A single level of YAML indentation controls whether you are granting access to a single namespace's web Pods or to every Pod in every production namespace.

### Policy Isolation and the Selection Trigger

A NetworkPolicy applies to Pods matched by its `podSelector`. Once a Pod is selected by any policy, the default for that Pod changes from "allow all" to "deny all" for the direction(s) specified. This has a subtle but important implication: policies are **triggered by selection, not by rule content**. A NetworkPolicy with an empty `ingress` list but with `policyTypes: [Ingress]` that selects a Pod will deny all ingress to that Pod — even though the policy itself specifies no rules. The act of selection is what flips the default, not the presence of allow rules.

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: api-policy
  namespace: production
spec:
  podSelector:
    matchLabels:
      app: api
  policyTypes:
    - Ingress
    - Egress
  ingress:
    - from:
        - podSelector:
            matchLabels:
              app: web
      ports:
        - port: 8080
          protocol: TCP
  egress:
    - to:
        - podSelector:
            matchLabels:
              app: db
      ports:
        - port: 5432
          protocol: TCP
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

This policy selects Pods with `app=api` in the `production` namespace. Once applied, those Pods are default-deny for both ingress and egress. The only allowed connections are: ingress from `app=web` Pods on TCP 8080, egress to `app=db` Pods on TCP 5432, and egress to kube-dns on UDP/TCP 53. Every other connection — including egress to external APIs, ingress from monitoring tools, and even the Pod's own outgoing connections to other services it might depend on — is silently dropped.

The behavioral shift can be summarized compactly. Before any policy selects a Pod, the Pod is fully open: all ingress and egress is permitted. After the first policy selects it — for the direction(s) listed in `policyTypes` — the Pod flips to closed, permitting only explicitly allowed traffic. Subsequent policies that also select the Pod add their allow rules to the union. This additive-trigger model is the foundation on which all network policy design patterns are built.

## Design Pattern 1: Default-Deny Baseline

The default-deny baseline is the single most important pattern in Kubernetes network security, and it should be the starting condition of every production namespace. The pattern is trivial to state: apply a NetworkPolicy with an empty `podSelector` and `policyTypes: [Ingress, Egress]` to every namespace, then layer on explicit allow policies for every legitimate communication path.

Why is this the foundation? Because without it, every other policy you write is optional. An attacker who compromises a Pod in a namespace without default-deny can communicate with any other Pod in the cluster, regardless of what policies exist in other namespaces. The policies in the target namespace might restrict ingress, but if no policy in the source namespace restricts egress, the compromised Pod can still initiate connections. Default-deny on both ingress and egress in every namespace closes this loophole — it means a compromised Pod can talk to nothing except what its namespace's allow policies explicitly permit.

Applying default-deny namespace-wide uses the empty selector:

```yaml
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

This single resource, applied to a namespace, instantly converts every Pod in that namespace to default-deny for both directions. The immediate consequence is that every Pod loses the ability to resolve DNS names, because CoreDNS runs in `kube-system` and egress to it is now blocked. This is the near-universal gotcha: every default-deny egress policy must be paired with a DNS allow rule.

### The DNS Allow Pattern

The DNS allow rule is not an optional companion to default-deny — it is a mandatory co-requirement. Without it, Pods cannot resolve Service names, which means they cannot reach anything by DNS, which means even your carefully crafted allow policies that reference Services by name will fail because the Pod cannot look up the IP.

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

The selector targets the kube-dns Pods in kube-system. Note that this policy specifies only `Egress` in `policyTypes` — it does not affect ingress to the Pods it selects. Since it uses an empty `podSelector`, it applies to every Pod in the namespace, but it only controls egress. The result is that every Pod can make DNS queries to CoreDNS, but all other egress remains blocked unless additional policies explicitly allow it.

In Kubernetes 1.35, CoreDNS is the standard DNS provider and listens on both UDP and TCP port 53. The TCP port is used for responses larger than 512 bytes and for zone transfers. While most DNS queries fit in a single UDP packet, relying solely on UDP can cause intermittent resolution failures for Services with many endpoints. Always include both protocols in your DNS allow rule.

### Automating Default-Deny at Scale

Manually applying default-deny and DNS-allow policies to every namespace does not scale. As teams create new namespaces, they will inevitably forget to add policies, leaving those namespaces wide open. Policy engines like Kyverno solve this by generating NetworkPolicy resources automatically when namespaces are created:

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

The `synchronize: true` field ensures that if someone deletes the generated policy, Kyverno recreates it. The `matchExpressions` exclude system namespaces where default-deny could break cluster services. This Kyverno ClusterPolicy is a set-and-forget mechanism — every new namespace automatically inherits the security baseline.

## Design Pattern 2: Namespace Isolation

Namespace isolation builds on the default-deny baseline by adding a structural constraint: namespaces may not communicate with each other unless an explicit policy allows it. This pattern reflects the organizational reality that different teams own different namespaces, and cross-team traffic should be deliberate rather than accidental.

With default-deny in place, namespace isolation largely happens by default — Pods in different namespaces cannot communicate because egress is blocked at the source and ingress is blocked at the destination. But platform teams typically need to make exceptions: the `frontend` namespace needs to reach the `backend` namespace, and `backend` needs to reach `database`. The namespace isolation pattern formalizes these exceptions as explicit, labeled rules.

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

Each arrow in this diagram represents a pair of policies: an egress rule in the source namespace and an ingress rule in the destination namespace. Why both? Because default-deny operates in both directions. A Pod in `frontend` cannot send traffic to `backend` unless its own egress policy allows it. A Pod in `backend` cannot receive traffic from `frontend` unless its own ingress policy allows it. Both must be explicitly permitted.

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

The namespace isolation pattern uses the `kubernetes.io/metadata.name` label, which Kubernetes automatically applies to every namespace with the namespace's own name as the value. You could alternatively use custom labels like `env: production` or `team: payments` — custom labels are more flexible because multiple namespaces can share them, allowing you to write a single policy that permits traffic from all namespaces in a given environment.

## Design Pattern 3: Zero-Trust Microsegmentation

Microsegmentation is the practice of defining allowed communication at the individual workload level — each microservice gets a policy that specifies exactly which other services it can talk to and on which ports. This is the most granular pattern and represents the full realization of zero-trust networking in Kubernetes: every Pod-to-Pod connection must be explicitly authorized, and no trust is derived from namespace membership, IP address range, or network location.

The practical implementation is a set of egress policies, one per workload, that enumerate every allowed destination. A workload that needs to talk to three other services gets an egress policy with three `to` entries, each specifying a `podSelector` (which service) and `ports` (which port). Anything not listed is denied by the default-deny baseline.

```yaml
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

The microsegmentation pattern scales in proportion to the number of services. For a cluster with 40 microservices, you will have 40 egress policies and potentially 40 ingress policies, each with a handful of rules. The operational challenge is not the quantity of policies — Kubernetes handles thousands of NetworkPolicy resources efficiently — but the accuracy of the policies. A missing rule causes an outage; an over-permissive rule defeats the segmentation.

This is where policy generation from observed traffic becomes essential. Rather than writing policies from scratch and hoping you have enumerated every dependency, you can run your application in a test environment with network observability enabled, capture the actual traffic flows, and generate policies that match the observed behavior.

```bash
# Using Cilium Hubble to observe actual traffic patterns
hubble observe --namespace production --output json | \
  jq -r '[.source.labels[], .destination.labels[]] | @csv' | \
  sort -u

# Using Inspektor Gadget (open source) — monitor traffic and suggest policies
kubectl gadget advise network-policy monitor --namespace production --timeout 60
```

Traffic-based policy generation reduces the risk of incomplete policies but does not eliminate it. It only captures traffic that occurs during the observation window. Infrequent code paths, cron jobs, and startup sequences may not appear. Always review generated policies against your application's documented dependencies, and run them in audit mode before enforcing.

## The Limits of Native NetworkPolicy

Kubernetes NetworkPolicy is a deliberately simple API, and its simplicity creates gaps that real-world platforms inevitably encounter. Understanding these limitations is essential because they determine when you need to reach for CNI-specific extensions or complementary tools.

The most fundamental limitation is that NetworkPolicy operates exclusively at OSI layers 3 and 4. It can filter traffic by source IP (via `podSelector` resolution), destination port, and protocol (TCP/UDP/SCTP). It cannot inspect the content of a connection — it has no visibility into HTTP paths, methods, headers, or gRPC service names. An allow rule for port 8080 permits every HTTP request to every endpoint on that port. If your threat model requires restricting access to specific API routes — allowing GET `/api/v1/health` but denying POST `/api/v1/admin` — native NetworkPolicy cannot express that constraint.

The second limitation is the absence of DNS-name-based egress. The `ipBlock` field accepts CIDR ranges, which means you must know the IP addresses of external services. Many cloud APIs, SaaS endpoints, and third-party services use IP addresses that change without notice. Maintaining egress policies based on IP blocks for external services is operationally fragile. You either over-allow with broad CIDRs (defeating the purpose of egress control) or accept that policies will break when IPs rotate.

The third limitation is the namespace scope. Every NetworkPolicy resource is namespaced. There is no native mechanism to write a policy that says "block egress to 169.254.169.254 (cloud metadata) from every Pod in every namespace." You must replicate that policy in each namespace, which is error-prone at scale and impossible to enforce atomically. Policy engines like Kyverno can automate the replication, but the underlying resource model does not support cluster-wide policy.

The fourth limitation is the absence of observability. NetworkPolicy is a filtering mechanism, not a logging mechanism. When traffic is dropped by a policy, there is no native event, no log entry, and no metric. You cannot answer the question "which policies are actively dropping traffic right now" from the Kubernetes API alone. This makes debugging policy misconfigurations a matter of running connectivity tests rather than inspecting policy decisions.

The fifth limitation is the lack of explicit deny and priority. As discussed, the additive-only model means you cannot write an overriding deny rule. If a namespace owner creates a permissive policy, no higher authority can override it using the same API. The AdminNetworkPolicy resource, discussed below, addresses this gap.

These limitations are not design flaws — they reflect the Kubernetes principle of keeping the core API minimal and extensible. But they mean that production platforms nearly always layer additional capabilities on top of native NetworkPolicy, either through CNI extensions or through the newer policy APIs.

## Beyond Native: Extended Policy APIs and CNI Extensions

### AdminNetworkPolicy — Cluster-Scoped, Prioritized, Deny-Capable

The AdminNetworkPolicy (ANP) and BaselineAdminNetworkPolicy (BANP) resources, developed by SIG-Network under KEP-2091, address the namespace-scope and no-deny limitations of standard NetworkPolicy. These resources are **cluster-scoped**, support **explicit Deny and Pass actions**, and have **numeric priority ordering**. As of Kubernetes 1.32 they reached beta (`policy.networking.k8s.io/v1beta1`), and they are enabled by default in 1.35.

The key architectural difference is that AdminNetworkPolicy is designed for **cluster administrators**, not namespace owners. ANP resources are evaluated before namespace-scoped NetworkPolicy resources, and their Deny actions cannot be overridden by namespace-level policies. This gives platform teams the ability to enforce security baselines — such as blocking access to cloud metadata endpoints — that application teams cannot accidentally or deliberately circumvent.

```yaml
apiVersion: policy.networking.k8s.io/v1beta1
kind: AdminNetworkPolicy
metadata:
  name: cluster-deny-to-metadata
spec:
  priority: 10
  subject:
    namespaces: {}
  egress:
    - name: deny-metadata-service
      action: Deny
      to:
        - networks:
            - 169.254.169.254/32
      ports:
        - portNumber:
            port: 80
            protocol: TCP
```

The `priority` field determines evaluation order — lower numbers are evaluated first. ANP supports `Allow`, `Deny`, and `Pass` actions. `Pass` is the equivalent of "no opinion" and allows lower-priority ANP rules or namespace-level NetworkPolicy rules to make the decision. The `subject` field can target all namespaces (`namespaces: {}`), specific namespaces by label, or specific namespaces by name. A companion resource, BaselineAdminNetworkPolicy, provides a simpler singleton policy that applies as a catch-all after ANP evaluation but before namespace NetworkPolicy evaluation.

The practical impact of ANP is that it adds a layer to the policy evaluation stack. For any given connection, the evaluation order is: AdminNetworkPolicy rules (by priority) → BaselineAdminNetworkPolicy → namespace NetworkPolicy (additive union). An ANP Deny at priority 5 will block traffic regardless of what any namespace-level policy says. This layered model finally gives cluster administrators the enforcement primitives that the original NetworkPolicy API lacked.

### Cilium NetworkPolicy — L7, FQDN, and Identity-Based Rules

Cilium extends the Kubernetes policy model with custom resource definitions that add capabilities beyond L3/L4 filtering. The `CiliumNetworkPolicy` (CNP) resource is namespace-scoped and extends standard NetworkPolicy semantics with L7 filtering, DNS-name-based egress, and identity-based rules. The `CiliumClusterwideNetworkPolicy` (CCNP) extends the same capabilities cluster-wide.

The most impactful extension is L7 policy enforcement. Cilium can inspect HTTP, gRPC, and Kafka protocol traffic and enforce rules based on application-layer attributes. An HTTP rule can restrict access to specific paths and methods; a gRPC rule can restrict access to specific service methods.

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
    - toFQDNs:
        - matchName: "api.stripe.com"
        - matchPattern: "*.amazonaws.com"
      toPorts:
        - ports:
            - port: "443"
```

The `toFQDNs` field is a transformative capability for egress control. Instead of specifying IP CIDRs, you specify DNS names. Cilium resolves the names, tracks the IP addresses associated with them, and dynamically updates the eBPF policy maps when IPs change. A policy allowing egress to `api.stripe.com` on port 443 will continue to work even if Stripe changes its IP addresses, because Cilium re-resolves the name and updates the allowed IP set. The `matchPattern` variant supports wildcards, enabling policies like "allow egress to any `*.amazonaws.com` endpoint."

Cilium's identity-based model assigns a numeric identity to each set of Pods that share the same labels. These identities are used in eBPF programs for policy enforcement, which means policy lookups are O(1) hash table operations rather than linear rule scans. The identity model also enables Cilium to enforce policies across clusters in a mesh configuration, because identities are propagated between clusters rather than requiring matching IP ranges.

Cilium graduated from CNCF incubating to graduated status in October 2023, reflecting its maturity as a networking and security platform. The policy engine is built on eBPF, which means policy enforcement happens in the kernel at the Pod's virtual Ethernet interface — there is no proxy, no sidecar, and no per-connection userspace overhead for L3/L4 policy enforcement. L7 enforcement does introduce a per-connection Envoy proxy component, but it is transparent to the application.

### Calico GlobalNetworkPolicy — Ordered, Deny, and Host Endpoints

Calico (Project Calico) provides its own extended policy resources that predate the AdminNetworkPolicy API and address similar gaps. The `GlobalNetworkPolicy` (GNP) resource is cluster-scoped, supports explicit `Deny` and `Log` actions, and uses an `order` field for priority evaluation (lower numbers evaluated first). The `NetworkPolicy` resource is the namespace-scoped equivalent.

```yaml
apiVersion: projectcalico.org/v3
kind: GlobalNetworkPolicy
metadata:
  name: deny-external-egress
spec:
  order: 100
  selector: "!has(allow-external)"
  types:
    - Egress
  egress:
    - action: Allow
      destination:
        nets:
          - 10.0.0.0/8
          - 172.16.0.0/12
          - 192.168.0.0/16
    - action: Allow
      protocol: UDP
      destination:
        selector: "k8s-app == 'kube-dns'"
        ports: [53]
    - action: Deny
```

A notable Calico capability beyond Cilium is support for **host endpoint policies**. While most Kubernetes network policies target Pods, Calico can apply policies to the Kubernetes node's own network interfaces. This enables use cases like restricting access to the kubelet API, controlling traffic to node-local services, and preventing Pod-to-node network escapes. Host endpoint policies use the same policy model as Pod policies, with a `selector` that matches host endpoint labels rather than Pod labels.

Calico's policy model supports actions beyond `Allow` and `Deny`: the `Log` action records that a packet matched the rule without making an allow/deny decision, and the `Pass` action skips the remaining rules in the current tier. Calico also supports **policy tiers**, which are ordered groups of policies that provide an additional layer of prioritization. Tiers are evaluated in order; within a tier, policies are evaluated by their `order` field. This two-level hierarchy (tiers → ordered policies) gives administrators more control over policy precedence than a flat ordered list.

### Landscape and Rosetta

> **Landscape snapshot — as of 2026-06. This changes fast; verify against vendor docs before relying on specifics.**

This Rosetta compares capabilities across Kubernetes policy APIs and CNI extensions. Each row is a durable capability; each column is a policy provider. Cells represent whether the capability is available natively, and if so, through which mechanism.

| Capability | K8s NetworkPolicy | AdminNetworkPolicy (v1beta1) | Cilium CNP/CCNP | Calico GNP/NP |
|---|---|---|---|---|
| L3/L4 filtering (IP, port, protocol) | Yes (`ipBlock`, `ports`) | Yes | Yes | Yes |
| L7 filtering (HTTP path, method, headers) | No | No | Yes (HTTP, gRPC, Kafka) | Via Envoy (limited) |
| DNS/FQDN-based egress | No | No | Yes (`toFQDNs`) | Yes (FQDN in `nets`) |
| Explicit deny action | No | Yes (`Deny`) | No (additive only) | Yes (`Deny`) |
| Priority / ordering | No (additive union) | Yes (`priority`) | No (additive union) | Yes (`order`, tiers) |
| Cluster-wide scope | No (namespace) | Yes | Yes (CCNP) | Yes (GNP) |
| Host endpoint policies | No | No | No | Yes |
| Policy auditing / logging | No (CNI-dependent) | No | Yes (Hubble, policy verdict) | Yes (flow logs) |
| Identity-based policy | No (label-selector) | No (label-selector) | Yes (numeric identity) | No (label-selector) |

No single policy provider offers every capability. The choice is not about which is "better" but about which combination of capabilities your platform's threat model requires. A platform that only needs namespace isolation and L3/L4 segmentation can operate entirely with native NetworkPolicy and AdminNetworkPolicy. A platform that requires L7 filtering or DNS-based egress must adopt Cilium or Calico extended policies. A platform that needs cluster-wide deny rules can use either AdminNetworkPolicy (if running K8s 1.32+) or Calico GlobalNetworkPolicy.

## Design Pattern 4: Validating and Operating Network Policies

### Testing Policies Before Enforcement

Network policies are infrastructure code, and like all infrastructure code, they must be tested before they affect production traffic. The core challenge is that a policy misconfiguration is silent — Kubernetes accepts any valid YAML, regardless of whether the policy reflects your intent. A policy that accidentally blocks traffic to a critical service does not produce an error; it produces an outage.

Connectivity testing is the most direct validation method. Deploy test Pods with the same labels as your workloads, then run connectivity probes against the expected allow-list and deny-list. A well-structured test validates both that allowed traffic succeeds and that denied traffic is blocked. Tools like Cyclonus automate this by generating a comprehensive matrix of connectivity tests for a given set of policies and reporting which connections are allowed or denied.

```bash
# Cyclonus: generates all-pairs connectivity matrix
# Install and run against a namespace with policies applied
cyclonus generate \
  --include-namespace production \
  --perturbation-wait-seconds 5
```

The output is a matrix showing, for every pair of source and destination labels, whether connectivity succeeded or was blocked by policy. This reveals both over-permissive rules (traffic allowed where it should be denied) and over-restrictive rules (traffic denied where it should be allowed). Cyclonus supports both standard Kubernetes NetworkPolicy and CiliumNetworkPolicy.

### Staged Rollout: Audit Before Enforce

A critical operational pattern is to introduce policies in audit mode before enforcing them. With Cilium, you can apply a policy with an annotation that causes it to log policy decisions without dropping traffic:

```yaml
metadata:
  annotations:
    io.cilium/policy-audit-mode: "enabled"
```

In audit mode, Cilium records every policy decision — allow or deny — in its monitoring subsystem. You can inspect these decisions with `cilium monitor --type policy-verdict` or through Hubble. This allows you to observe what traffic would be blocked by the policy without actually interrupting any connections. After confirming that the policy's decisions match your expectations, you remove the annotation to enforce the policy.

Calico supports a similar pattern through its `Log` action, which records a policy hit without allowing or denying the traffic. A policy can be structured as a sequence of Log rules followed by the actual Allow/Deny rules, giving operators visibility into which rules would match without changing traffic flow.

### Observability: Knowing What Your Policies Are Doing

Once policies are enforced, you need observability to answer operational questions: Which policies are actively dropping traffic? Is a recent deployment failure caused by a missing policy rule? Is there unexpected traffic arriving at a sensitive service?

Cilium Hubble provides per-flow visibility with policy verdict information. Every flow event includes the source and destination identities, the ports and protocols, and the policy decision (allowed or denied). The `hubble observe` command can filter for denied flows specifically, making it the go-to tool for debugging "my service can't reach X" issues.

```bash
# Observe all denied flows in a namespace
hubble observe --namespace production --verdict DROPPED

# Trace policy decision for a specific flow
cilium policy trace --src-pod production/order-service-abc123 \
  --dst-pod production/payment-service-def456 \
  --dport 8443
```

For clusters without Cilium, policy observability is more limited. Standard Kubernetes provides no native mechanism for observing policy decisions. Calico's flow logs, when enabled, provide similar information to Hubble. Without either, the primary debugging approach is connectivity testing — running commands from test Pods to verify whether traffic is allowed or blocked.

## Patterns and Anti-Patterns

### Patterns

Each pattern below represents a design choice that has been validated across production Kubernetes deployments. They are not absolute rules but defaults that should be deviated from only with a clear rationale.

**1. Default-deny in every namespace, no exceptions.** Start from a position where no traffic is allowed, then add explicit allow rules. This pattern is the foundation — without it, all other policies are bypassable. Apply it automatically using Kyverno or an admission controller so that new namespaces inherit the baseline.

**2. Paired egress and ingress policies.** When allowing traffic from namespace A to namespace B, write both an egress policy in A and an ingress policy in B. This is belt-and-suspenders: if either policy is misconfigured or missing, the other still blocks the traffic. It also means that a compromise in namespace A cannot be used to probe what B allows, because A's egress is restricted.

**3. Least-privilege egress per workload.** Rather than writing broad egress policies (such as "allow egress to all Pods in the production namespace"), write per-workload egress policies that enumerate exactly which services each workload communicates with. This limits lateral movement: a compromised order-service Pod cannot reach the payment-service unless the order-service egress policy explicitly allows it.

**4. DNS egress bundled with default-deny.** Every namespace that has default-deny egress must also have a DNS allow rule. Make this a single, automated deployment — not a manual step that can be forgotten. The Kyverno ClusterPolicy pattern shown earlier bundles both rules together.

**5. Cloud metadata endpoint blocked cluster-wide.** Use AdminNetworkPolicy (or Calico GlobalNetworkPolicy) to block egress to `169.254.169.254/32` from all namespaces. This prevents Pods from accessing cloud instance metadata, which can contain credentials. This is a cluster-admin-scoped policy that namespace owners cannot override.

**6. Staged policy rollout with audit mode.** Apply new or modified policies in audit mode for a full business cycle before enforcing them. This catches missing dependencies — the cron job that runs once a day, the health check from the monitoring namespace, the backup process that connects once a week — that would otherwise cause production outages.

### Anti-Patterns

| Anti-Pattern | Why It's Bad | Better Approach |
|---|---|---|
| Writing ingress-only policies without egress policies | A compromised Pod can still initiate outbound connections to any destination, including external C2 servers | Always include egress policies; default-deny egress everywhere |
| Using broad CIDR egress rules (0.0.0.0/0 except private ranges) as a shortcut | Defeats egress control entirely; any compromised Pod can exfiltrate data to any internet host | Enumerate specific external dependencies with ipBlock or FQDN; use an egress proxy for the rest |
| Applying NetworkPolicy on a Flannel cluster | Flannel has no policy enforcement engine; resources are accepted and silently ignored | Switch to Calico or Cilium, or add Calico in policy-only mode alongside Flannel |
| Using an empty podSelector by accident (unset Helm value) | An empty selector matches every Pod; an ingress allowance combined with an accidental empty podSelector grants access to all Pods in the namespace | Validate rendered manifests in CI; use an admission webhook that rejects empty podSelectors unless the policy name indicates default-deny intent |
| Combining podSelector and namespaceSelector in separate list items when you meant AND | Opens traffic to every Pod in the matched namespace, not just the intended subset | Use a single list item with both selectors when you need AND semantics |
| Testing policies without labels on test Pods | Under default-deny egress, a test Pod without matching labels cannot send any traffic, making it appear as though the target is unreachable when the problem is the test Pod's own egress | Always apply the correct workload labels to test Pods; use `--labels` with `kubectl run` |
| Deploying policies directly to production without audit mode | A missing allow rule causes an immediate outage; rollback may take minutes | Audit before enforce using Cilium audit mode or Calico Log action |
| Not including TCP in DNS allow rules alongside UDP | DNS responses over 512 bytes use TCP; intermittent resolution failures appear under load | Always include both UDP and TCP port 53 in DNS egress rules |

### Decision Framework

Use this decision tree to select the appropriate policy mechanism for each requirement on your platform:

```
Requirement: control Pod-to-Pod traffic?
├── L3/L4 only (IP + port)?
│   ├── Namespace-scoped rules managed by app teams?
│   │   └── Use: K8s NetworkPolicy
│   └── Cluster-scoped rules managed by platform team?
│       ├── K8s ≥ 1.32 available?
│       │   └── Use: AdminNetworkPolicy (Deny + priority)
│       └── K8s < 1.32?
│           └── Use: Calico GlobalNetworkPolicy OR Kyverno-generated NetworkPolicy
├── L7 filtering required (HTTP path, gRPC method)?
│   └── Use: CiliumNetworkPolicy (HTTP/gRPC rules)
├── DNS-name-based egress required?
│   └── Use: CiliumNetworkPolicy (toFQDNs) OR Calico (FQDN in nets)
└── Host endpoint protection required?
    └── Use: Calico GlobalNetworkPolicy (host endpoint selector)
```

## Did You Know?

- The 2024 [Fairwinds Kubernetes Benchmark Report](https://www.fairwinds.com/blog/2024-kubernetes-benchmark-report-kubernetes-workload-analysis), which analyzed more than 330,000 workloads, found that **58% of organizations have workloads missing network policy** — a strong signal that default-deny segmentation is still the exception rather than the norm in production clusters.
- Kubernetes NetworkPolicy is **additive-only** — there is no "deny" rule. If no policy selects a Pod, all traffic is allowed. Once any policy selects a Pod, all traffic not explicitly allowed by some policy is denied. This "default-allow, first-policy-flips-to-deny" model confuses most people on first encounter.
- Cilium's L7 network policies can filter HTTP traffic by path, method, and headers — meaning you can write a policy that says "allow GET /api/v1/health but deny POST /api/v1/admin" at the network layer, without changing application code. Traditional K8s NetworkPolicy can only filter by L3/L4 (IP and port).
- The Kubernetes Network Policy API has remained essentially unchanged since its introduction in v1.7 (2017). The AdminNetworkPolicy and BaselineAdminNetworkPolicy resources (KEP-2091) are the first major evolution, adding cluster-scoped policies with explicit deny rules and priority ordering. They reached beta in K8s 1.32 and are enabled by default in 1.35.

## Common Mistakes

| Mistake | Why It Happens | How to Fix It |
|---|---|---|
| Applying default-deny without DNS egress | DNS is "invisible" — people forget Pods need it | Always pair default-deny with a DNS-allow policy; automate both together |
| Combining podSelector and namespaceSelector incorrectly (OR vs AND) | YAML indentation determines whether they're in the same or different list items | Use the two-item pattern for OR, one-item pattern for AND; verify with `kubectl describe` |
| Applying NetworkPolicy on a Flannel cluster | Flannel has no policy engine; resources are accepted but silently ignored | Switch to Calico or Cilium, or add Calico in policy-only mode |
| Not including egress rules for external APIs | Teams focus on ingress but forget Pods also need to reach external services | Audit egress requirements per workload; add ipBlock or FQDN-based egress rules |
| Labeling Pods inconsistently | Helm chart labels differ from kubectl-created labels | Standardize label taxonomy across all deployments; use admission policies to enforce |
| Testing policies in production | "It worked in staging" — but staging has different Services and label patterns | Use `cilium policy trace` or `calicoctl check` to dry-run; audit before enforce |
| Missing port in policy rules | Allow the Pod selector but forget to specify the port | Always include `ports` in rules; omitting ports means "all ports" — which may be too permissive |
| Using an empty podSelector accidentally (undefined Helm variable) | Helm value is unset, template renders `matchLabels: {}` | Validate rendered manifests in CI; add admission webhook to reject empty selectors without annotation |

## Quiz

<details>
<summary>1. In Kubernetes NetworkPolicy, what happens when you create a policy with an empty podSelector (podSelector: {}) and only specify Ingress in policyTypes?</summary>

An empty `podSelector` matches **all Pods** in the namespace. With only `Ingress` in `policyTypes`, this policy affects only incoming traffic — all ingress not explicitly allowed by any policy is denied for all Pods in the namespace. Egress remains unrestricted because it is not listed in `policyTypes`. This is the pattern for "default-deny ingress" — but remember, egress is still wide open unless you add `Egress` to `policyTypes` as well.
</details>

<details>
<summary>2. Why must you always include a DNS egress rule when using default-deny egress policies?</summary>

Pods resolve Service names (like `api.backend.svc.cluster.local`) through CoreDNS, which runs in `kube-system` namespace on port 53 UDP and TCP. A default-deny egress policy blocks ALL outbound traffic, including DNS queries. Without DNS, Pods cannot resolve any Service names — `wget http://api-service:8080` fails because it cannot look up the IP. You must explicitly allow egress to kube-dns Pods in kube-system on port 53. Include both UDP and TCP: UDP handles standard queries, while TCP is needed for responses exceeding 512 bytes.
</details>

<details>
<summary>3. What is the difference between Kubernetes NetworkPolicy and Cilium CiliumNetworkPolicy for egress to external services?</summary>

Standard Kubernetes NetworkPolicy can only filter egress by IP address (`ipBlock` with CIDR). If the external service's IP changes, the policy breaks because the CIDR no longer covers the destination. Cilium CiliumNetworkPolicy supports `toFQDNs` — you can specify DNS names like `api.stripe.com`, and Cilium resolves them and dynamically updates the allowed IPs in the eBPF policy map. This is vastly more practical for real-world egress control where external service IPs are unpredictable. Cilium also supports wildcard patterns like `*.amazonaws.com` for services with many subdomains.
</details>

<details>
<summary>4. Scenario: You applied a NetworkPolicy to allow ingress from Pods with label "app=web" but traffic is still blocked. What should you check first?</summary>

Check these in order: (1) Verify your CNI supports NetworkPolicy — Flannel does not enforce policies. (2) Verify the source Pods actually have the label `app=web` with `kubectl get pods --show-labels`. (3) If the source is in a different namespace, verify you included a `namespaceSelector` — without it, `podSelector` only matches Pods in the **same** namespace. (4) Check that the `ports` field matches the actual port the target is listening on. (5) If using default-deny egress, verify the source namespace has an egress policy allowing traffic to the target namespace.
</details>

<details>
<summary>5. How do AdminNetworkPolicy resources (K8s 1.32+) differ from standard NetworkPolicy?</summary>

AdminNetworkPolicy (ANP) has three key differences: (1) **Cluster-scoped** — they apply across all namespaces, not just one. (2) **Explicit deny** — unlike standard NetworkPolicy which is additive-only, ANP supports `Deny` and `Pass` actions so administrators can write overriding deny rules. (3) **Priority ordering** — ANP resources have a numeric priority field; lower numbers are evaluated first, and an ANP Deny at any priority overrides namespace-level allows. The companion BaselineAdminNetworkPolicy provides a singleton catch-all. ANP is evaluated before namespace NetworkPolicy, giving cluster administrators enforcement primitives that namespace owners cannot override.
</details>

<details>
<summary>6. Why is an empty matchLabels in a podSelector dangerous in a NetworkPolicy?</summary>

An empty `matchLabels: {}` matches **every Pod** in the namespace, not "no Pods." If your policy allows ingress from some source and you accidentally use an empty `podSelector`, you have granted that source access to every Pod in the namespace — not just the intended target. This is a common Helm templating bug where a variable is undefined, resulting in an empty selector. Always validate NetworkPolicy selectors in CI, and consider using admission webhooks to reject policies with empty podSelectors unless they are explicitly intended for default-deny purposes.
</details>

<details>
<summary>7. Scenario: You have default-deny in the "payments" namespace. The payments service needs to call Stripe's API (api.stripe.com) on port 443. How do you allow this with standard Kubernetes NetworkPolicy, and what are the tradeoffs?</summary>

With standard NetworkPolicy, you need an egress rule with an `ipBlock` specifying Stripe's current IP ranges. The challenge is that Stripe's IPs can change without notice. The approach: (1) Look up Stripe's published IP ranges, (2) create an egress rule with those CIDRs, (3) build automation to periodically re-resolve and update the policy. This is fragile and operationally expensive. The practical alternatives: use Cilium's `toFQDNs` for dynamic DNS-based egress, route through an egress proxy with a known IP, or allow egress to all external IPs on port 443 excluding private ranges (`ipBlock: {cidr: 0.0.0.0/0, except: [10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16]}`). The last option is less secure but more practical — the tradeoff is that any external destination on 443 becomes reachable.
</details>

<details>
<summary>8. What happens if two NetworkPolicies in the same namespace have conflicting rules — one allows traffic from Pod A and another has no rule for Pod A?</summary>

There is no conflict. NetworkPolicies are **purely additive** (union). If Policy X allows traffic from Pod A to Pod B, and Policy Y selects Pod B but does not mention Pod A, the traffic is still allowed because Policy X allows it. The final allowed set is the union of all allow rules across all policies that select the target Pod. There is no way to "override" or "revoke" an allow rule with standard NetworkPolicy — you would need AdminNetworkPolicy with an explicit Deny action for that. This is why the default-deny baseline pattern is essential: it ensures that unlisted traffic is denied, and each additional policy only adds specific allow rules.
</details>

## Hands-On

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

Now deploy a three-tier application across three namespaces to use as your policy testbed:

```bash
# Create namespaces
kubectl create namespace frontend
kubectl create namespace backend
kubectl create namespace database

# Deploy components (using bitnami images from Docker Hub for cross-platform compatibility)
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

Before applying any policies, verify that the default flat network allows every pod to reach every other pod. This establishes the baseline you will lock down with network policies:

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

Now apply default-deny to all three namespaces, then selectively allow the specific communication paths that the three-tier architecture requires:

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

To confirm your policies work correctly, run targeted connectivity tests from labelled test pods:

> **Important**: Under default-deny, `kubectl run` test Pods need labels that match
> the egress policies. Without labels, the test Pod's egress is denied (only DNS is allowed).

```bash
# frontend -> backend: should work
kubectl run test -n frontend --rm -it --restart=Never --image=busybox:1.36 \
  --labels="app=web" -- \
  wget --timeout=3 -qO- http://api.backend.svc.cluster.local:8080

# frontend -> database: should be BLOCKED
kubectl run test -n frontend --rm -it --restart=Never --image=busybox:1.36 \
  --labels="app=web" -- \
  sh -c "echo | nc -w 3 db.database.svc.cluster.local 5432 && echo CONNECTED || echo BLOCKED"

# backend -> database: should work
kubectl run test -n backend --rm -it --restart=Never --image=busybox:1.36 \
  --labels="app=api" -- \
  sh -c "echo | nc -w 3 db.database.svc.cluster.local 5432 && echo CONNECTED || echo BLOCKED"
```

After completing these tests, verify the following conditions are all met — these define correct policy behaviour for a properly segmented three-tier application:

- [ ] Applied default-deny policies to all three namespaces
- [ ] Frontend can reach backend API on port 8080
- [ ] Frontend CANNOT reach database directly
- [ ] Backend can reach database on port 5432
- [ ] DNS resolution works in all namespaces

### Exercise 2: Audit Policy Coverage

Policy coverage tends to degrade over time as new namespaces are created and old policies are forgotten. Build a script that audits your cluster for namespaces that lack default-deny protection, so you can catch coverage gaps before they become breach paths. Run the script against your cluster and confirm that every non-system namespace reports default-deny policies present:

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

- [ ] Script runs against your cluster and reports per-namespace policy status
- [ ] All non-system namespaces show `[OK]` with default-deny present

### Exercise 3: Policy Validation with Cyclonus

Manual connectivity testing validates individual paths but does not scale to comprehensive coverage — a cluster with many policies and services has too many source-destination pairs to test by hand. Cyclonus automates this by generating a complete connectivity matrix: it creates test Pods with every label combination present in your policies, probes every possible connection, and reports which succeed and which are blocked. Install Cyclonus and run it against your namespace to verify that your policies produce the intended connectivity matrix with no unexpected allows or denies:

```bash
# Clone and build Cyclonus (Go required)
git clone https://github.com/mattfenwick/cyclonus.git
cd cyclonus
go build -o cyclonus cmd/cyclonus/main.go

# Generate a policy connectivity matrix
./cyclonus generate \
  --include-namespace production \
  --perturbation-wait-seconds 5
```

- [ ] Cyclonus runs successfully against your namespace
- [ ] Connectivity matrix shows expected allows and denies
- [ ] No unexpected allows (over-permissive policies)
- [ ] No unexpected denies (over-restrictive policies)

## Sources

- [Network Policies — Kubernetes Concepts](https://kubernetes.io/docs/concepts/services-networking/network-policies/)
- [Declare Network Policy — Kubernetes Tasks](https://kubernetes.io/docs/tasks/administer-cluster/declare-network-policy/)
- [NetworkPolicy v1 API Reference](https://kubernetes.io/docs/reference/kubernetes-api/policy-resources/network-policy-v1/)
- [AdminNetworkPolicy — SIG-Network Policy API](https://network-policy-api.sigs.k8s.io/api-types/admin-network-policy/)
- [Kubernetes SIG-Network Policy API (GitHub)](https://github.com/kubernetes-sigs/network-policy-api)
- [Kubernetes Network Policy Recipes — Ahmet Alp Balkan](https://github.com/ahmetb/kubernetes-network-policy-recipes)
- [Cilium Network Policy Documentation](https://docs.cilium.io/en/stable/security/policy/)
- [Cilium L7 Network Policy](https://docs.cilium.io/en/stable/security/policy/language/#layer-7-examples)
- [Cilium Kubernetes Policy Integration](https://docs.cilium.io/en/stable/network/kubernetes/policy/)
- [Cilium Hubble Observability](https://docs.cilium.io/en/stable/observability/hubble/)
- [Calico Network Policy Documentation](https://docs.tigera.io/calico/latest/network-policy/)
- [Calico Network Policy Rules](https://docs.tigera.io/calico/latest/network-policy/policy-rules)
- [CoreDNS Manual](https://coredns.io/manual/toc/)
- [CoreDNS Kubernetes Plugin](https://coredns.io/plugins/kubernetes/)
- [NIST SP 800-207 — Zero Trust Architecture](https://csrc.nist.gov/publications/detail/sp/800-207/final)
- [Cyclonus — Network Policy Testing Tool](https://github.com/mattfenwick/cyclonus)

## Hypothetical Scenario: The "Allow All" That Wasn't

A platform team had carefully crafted network policies for their multi-service platform. Every namespace had default-deny. Every service had explicit ingress and egress rules. The security team was confident in their zero-trust posture.

Then an engineer deployed a new `analytics-collector` service. The Helm chart included a NetworkPolicy, but it was templated with a variable that was never set:

```yaml
podSelector:
  matchLabels:
    app: {{ .Values.appName }}    # .Values.appName was empty
```

An empty `matchLabels` is a valid selector — it matches **all Pods** in the namespace. The policy's ingress rule allowed traffic from `app: web-frontend`. Combined with the empty podSelector, this policy allowed `web-frontend` to reach **every Pod** in the namespace, not just the analytics collector. The web frontend could reach the payment processing service directly, bypassing the API gateway that enforced rate limiting and authentication. An automated penetration test caught the issue after roughly two weeks.

The investigation consumed significant engineering time auditing logs to confirm no unauthorized access had occurred. The incident led to mandatory policy validation in CI/CD — every NetworkPolicy now goes through `kubectl apply --dry-run=server` plus a custom admission webhook that rejects policies with empty podSelectors unless explicitly annotated for default-deny use.

The lesson: Network policies are code. Test them like code. An empty selector is not "no selector" — it is "select everything."

## Next Module

In [Module 1.3: Service Mesh Architecture & Strategy](../module-1.3-service-mesh-strategy/), you will explore when you need a service mesh for capabilities that network policies alone cannot provide — mTLS encryption, traffic splitting, L7 observability, and circuit breaking. You will evaluate Istio, Linkerd, and Cilium's sidecarless mesh to make an informed decision for your platform.
