---
title: "Module 1.5: Multi-Cluster & Hybrid Networking"
slug: platform/disciplines/reliability-security/networking/module-1.5-multi-cluster-networking
sidebar:
  order: 6
revision_pending: false
---
> **Discipline Module** | Complexity: `[COMPLEX]` | Time: 60-70 min

## Prerequisites

Before starting this module:
- **Required**: [Module 1.1: CNI Architecture](../module-1.1-cni-architecture/) — CNI fundamentals, especially Cilium
- **Required**: [Module 1.4: Ingress & Gateway API](../module-1.4-ingress-gateway/) — Gateway API, multi-cluster ingress concepts
- **Recommended**: [Module 1.3: Service Mesh Strategy](../module-1.3-service-mesh-strategy/) — Multi-cluster mesh patterns
- **Helpful**: Experience with multiple Kubernetes clusters, VPNs, or cloud VPCs

---

## What You'll Be Able to Do

After completing this module, you will be able to:

- **Design multi-cluster networking architectures that connect services across clusters, regions, and clouds**
- **Implement cross-cluster service discovery using DNS, service mesh federation, or Submariner**
- **Configure network policies that span cluster boundaries while maintaining security isolation**
- **Evaluate multi-cluster networking trade-offs — latency, complexity, cost — for your distributed architecture**

---

## Why This Module Matters

Hypothetical scenario: an organization runs two Kubernetes clusters — one in a North American region and one in a European region. Each cluster is self-contained, with its own databases, caches, and application stacks. The European users are routing through the North American cluster because a DNS misconfiguration in the global load balancer points all traffic there.

When the North American cluster experiences a roughly 40-minute outage from an availability-zone failure, European users lose service entirely even though the European cluster is perfectly healthy. The organization had invested heavily building the second cluster for disaster recovery, but the networking layer — the piece that connects clusters and routes traffic intelligently — was an afterthought. The failover was manual, undocumented, and had never been tested.

This scenario plays out across organizations of every size because multi-cluster networking is almost always deferred. Teams stand up a second cluster for resilience, for regional proximity, or for regulatory compliance, but they underestimate what it takes to make two clusters behave as one logical service topology. The connectivity between clusters is the hard part — not because the tools are immature, but because the problem spans DNS, routing, encryption, identity, service discovery, and traffic policy. Every one of those layers must be configured correctly and tested under failure for the multi-cluster architecture to deliver the resilience it promises.

Multi-cluster networking is not just about connecting clusters. It is about building a resilient service topology where traffic flows to the right cluster based on latency, availability, and business rules. This module covers the durable principles, the proven patterns, the operational practices, and the trade-offs that make multi-cluster Kubernetes work in production — across regions, across clouds, and across cluster boundaries.

---

## Part 1: Why Run Multiple Clusters at All

Before you design a multi-cluster networking architecture, you need to understand why the clusters exist in the first place. The networking requirement flows from the business driver, and different drivers produce different connectivity demands. A cluster pair connected for disaster recovery needs different traffic behavior than a pair connected for data-residency compliance. Knowing the why prevents you from over-engineering the solution.

### Blast-Radius Isolation

A single Kubernetes cluster is a single failure domain. A malfunctioning controller, a runaway operator, a corrupted etcd database, or a misconfigured admission webhook can affect every workload in the cluster. Running multiple independent clusters limits the damage radius of any single control-plane failure. If one cluster goes down, the blast is contained to the services running on that cluster. The remaining clusters continue operating with their own API servers, their own etcd instances, and their own scheduling decisions.

This is the most common driver for multi-cluster architectures, and it imposes a specific networking requirement: the clusters must remain independently functional. You do not want to create a cross-cluster dependency that turns two independent failure domains into one coupled one. If Cluster A's workloads cannot function without Cluster B's services, then you have not actually isolated your blast radius — you have just moved the single point of failure from inside the cluster to between the clusters.

### Regional and Latency Proximity

Users in Tokyo experience materially different latency to a cluster in Frankfurt than they do to a cluster in Tokyo. For latency-sensitive workloads — real-time trading systems, multiplayer game backends, interactive SaaS applications — running a cluster close to users is not optional. A multi-cluster architecture places workloads near the users they serve, and the networking layer routes traffic to the nearest healthy cluster.

This driver demands topology-aware routing: traffic must prefer the local cluster, fail over to a remote cluster only when the local one is unhealthy, and return to the local cluster when it recovers. It also demands consistent latency measurement, because "nearest" is not always obvious — a cluster in a nearby region with a congested backbone link may perform worse than a slightly more distant region with a clean path.

### Regulatory and Data-Residency Boundaries

Some jurisdictions require that data be stored and processed within national or regional borders. A single global cluster cannot satisfy this requirement because data would transit across borders. Instead, organizations deploy per-region clusters, each holding data for users in that region. The networking requirement here is not connectivity — it is the absence of connectivity. These clusters should not share services, should not route traffic across borders, and should not leak metadata through cross-cluster DNS resolution. The networking design is deliberately partitioned.

### Scale Beyond a Single Cluster's Limits

Kubernetes clusters have practical ceilings: roughly 5 000 nodes and 150 000 Pods per cluster in current versions (1.35). For most organizations these limits are theoretical, but for large-scale infrastructure providers, SaaS platforms with millions of tenants, or high-density edge computing deployments, they are real. Multi-cluster architectures allow horizontal scaling beyond a single cluster's capacity by sharding workloads across multiple control planes.

When scaling drives the multi-cluster decision, the networking requirement is typically service-level connectivity — individual services are shared between shards rather than all Pods being reachable everywhere. This keeps the cross-cluster surface area manageable and avoids the combinatorial explosion of full mesh routing between thousands of nodes.

### Environment and Tenant Separation

Strong isolation between environments (development, staging, production) or between tenants (different customers, different business units) is often enforced through separate clusters rather than namespace-level isolation within a single cluster. This provides defense in depth: a compromised credential in the development cluster cannot reach production workloads, and a noisy neighbor in one tenant's namespace cannot starve another tenant of resources.

When environments are separate clusters, the networking requirement shifts from cross-cluster service discovery to API-level integration. A staging cluster does not need to share Services with production — it needs to test against production-like services. A tenant cluster does not need to route Pod traffic to another tenant — it needs to integrate at the API gateway level with explicit, authenticated endpoints.

### Migration and Gradual Rollout

Clusters are not immortal. Kubernetes versions, CNI plugins, control-plane configurations, and cloud-provider integrations all evolve. A multi-cluster architecture supports blue-green cluster migration: deploy a new cluster with the target configuration, gradually shift traffic from the old cluster, and decommission the old cluster once traffic reaches zero. The networking layer makes this possible by providing a mechanism to split and shift traffic between clusters without changing application code or DNS configurations.

Each of these drivers shapes the networking architecture differently. The mistake teams make is choosing a networking tool first and then trying to fit their requirements into the tool's model. The correct approach is to articulate which of these drivers apply, define the required connectivity semantics from those drivers, and only then evaluate which tool or combination of tools satisfies the requirements with the least operational complexity.

---

## Part 2: The Connectivity Problem

Connecting Kubernetes clusters is fundamentally harder than connecting groups of VMs or physical servers because Kubernetes abstracts the network twice: once at the Pod IP layer and once at the Service layer. Two clusters do not just have different IP ranges — they have different API servers, different DNS zones, different identity providers, and different network policy engines. Making them work together means reconciling all of these layers.

### Axis 1: Pod-IP Routability Across Clusters

In a single cluster, every Pod can reach every other Pod by IP address, regardless of which node either Pod is running on. The CNI plugin ensures this through a combination of bridge interfaces, VXLAN or Geneve tunnels, and routing rules. Pod 10.1.5.23 on node-3 in cluster A can ping Pod 10.1.9.87 on node-12 in cluster A without any application-level configuration.

Across clusters, that guarantee disappears. The Pod CIDRs might overlap — both clusters could use the default 10.244.0.0/16 range, and a Pod IP 10.244.1.42 could exist simultaneously in both clusters with no way to distinguish them. Even if the Pod CIDRs do not overlap, there is no route between the clusters that tells the network how to deliver a packet destined for 10.2.0.0/16 to cluster B's nodes.

There are two durable approaches to this problem, and choosing between them is the most consequential decision in a multi-cluster networking design. The first approach, flat or routed networking, requires non-overlapping CIDRs and network-level routes (VPC peering, VPN, or dedicated interconnect) that make Pod IPs from one cluster reachable from another. This gives you the simplest and fastest path — Pod-to-Pod traffic flows directly without encapsulation — but it demands careful CIDR planning and network infrastructure that supports the route table size. The second approach, gateway-bridged networking with some form of address translation, tolerates overlapping CIDRs by encapsulating cross-cluster traffic through gateway nodes that rewrite source and destination IPs. This is more flexible and easier to retrofit onto existing clusters, but it adds latency from encapsulation and translation overhead.

### Axis 2: Service Discovery Across Clusters

In a single cluster, a workload finds a Service by resolving a DNS name like `payment-service.production.svc.cluster.local`. CoreDNS, running inside the cluster, resolves that name to the Service's ClusterIP, and kube-proxy or the CNI's eBPF dataplane routes traffic to a healthy endpoint.

Across clusters, none of this works automatically. A Pod in cluster A resolving `payment-service.production.svc.cluster.local` will get cluster A's CoreDNS answer — and that Service may not exist in cluster A, or it may resolve to entirely different endpoints. Even if the Service name exists in both clusters, the Pod IPs behind it are only reachable from within the same cluster under default networking.

The Multi-Cluster Services (MCS) API, standardized through the `multicluster.x-k8s.io` API group, addresses this directly. It introduces two new resources: `ServiceExport`, created in the cluster that owns the service, and `ServiceImport`, automatically created in consuming clusters to represent the exported service. When a `ServiceExport` exists for a Service, workloads in other clusters resolve `<name>.<namespace>.svc.clusterset.local` — note the `clusterset.local` domain instead of `cluster.local` — and the resolution returns endpoints from all clusters that export the service. This is the Kubernetes-native answer to cross-cluster service discovery, and it is the pattern that several tools implement (Submariner natively, Cilium ClusterMesh through its annotation-based mechanism, Istio through its own service registry federation).

### Axis 3: Separate API Servers and Separate Identity

Every Kubernetes cluster has its own API server, its own authentication and authorization configuration, and its own identity domain. A ServiceAccount token issued by cluster A's API server means nothing to cluster B. A NetworkPolicy defined in cluster A has no effect on traffic arriving in cluster B. A CertificateSigningRequest approved by cluster A's controller manager creates a certificate that cluster B's workloads will not trust.

This separation is intentional — it is why multiple clusters provide blast-radius isolation — but it also means that cross-cluster traffic crosses a trust boundary. Without a shared identity system, mTLS between clusters requires manually distributing certificates, and network policies cannot express rules that span clusters. The SPIFFE standard and its Kubernetes integration through tools like cert-manager with CSI drivers provide one path to a shared trust domain. Service mesh control planes (Istio, Linkerd, Cilium) provide another by federating their identity registries and distributing cross-cluster trust bundles.

---

## Part 3: Multi-Cluster Networking Models

The connectivity problem resolves into three architectural models, each making different trade-offs between simplicity, performance, security, and flexibility. These models are not mutually exclusive — a real deployment might use flat networking between clusters in the same cloud region and service-level connectivity for clusters in different clouds or on-premises.

### Model 1: Flat Networking — Routed Pod IPs

In the flat networking model, all clusters share a routable Pod network. Pod IPs from cluster A are directly reachable from cluster B because the underlying network knows how to route packets between the Pod CIDRs. No encapsulation, no translation, no gateway.

```
┌─────────────────────┐     ┌─────────────────────┐
│  Cluster A           │     │  Cluster B           │
│  Pods: 10.1.0.0/16  │     │  Pods: 10.2.0.0/16  │
│                      │     │                      │
│  ┌───┐     ┌───┐    │     │  ┌───┐     ┌───┐    │
│  │ P │     │ P │    │     │  │ P │     │ P │    │
│  │.1 │────→│.5 │    │     │  │.3 │     │.7 │    │
│  └───┘     └───┘    │     │  └───┘     └───┘    │
│       └──────────────┼─────┼──→                   │
│  Direct Pod-to-Pod   │     │  Direct Pod-to-Pod   │
└─────────────────────┘     └─────────────────────┘
         │                             │
         └──────────┬──────────────────┘
                    │
          VPC Peering / VPN / Direct Connect
          (non-overlapping CIDRs required)
```

This model delivers the lowest possible cross-cluster latency because there is no additional encapsulation. Packets leave a Pod's interface in cluster A, traverse the underlay network (VPC peering, VPN tunnel, or direct interconnect), and arrive at the target Pod's interface in cluster B with the same headers they started with. The CNI's existing routing takes care of delivering the packet to the right node within each cluster — the underlay only needs to carry packets between clusters.

The cost of this simplicity is CIDR discipline. Every Pod CIDR, Service CIDR, and Node CIDR across every cluster in the mesh must be unique and non-overlapping. Changing a CIDR on an existing cluster is a destructive operation — you must drain every node, recreate every Pod, and potentially rebuild the cluster. This makes flat networking ideal for greenfield deployments where CIDR planning happens before the first cluster is created, and challenging for brownfield deployments where overlapping CIDRs already exist. It also works best when all clusters reside in the same cloud provider or connected network fabric, because cross-cloud VPC peering or inter-region VPN tunnels add their own latency and bandwidth constraints that partially negate the performance advantage of flat routing.

### Model 2: Overlay Networking — Tunneled with Address Translation

Overlay networking encapsulates cross-cluster traffic inside tunnels (IPsec, WireGuard, VXLAN) and handles address conflicts through translation. This model accepts that Pod CIDRs may overlap and solves the routing ambiguity by assigning global-scope addresses to exported services and NATing traffic at gateway nodes.

```
┌─────────────────────┐     ┌─────────────────────┐
│  Cluster A           │     │  Cluster B           │
│  Pods: 10.244.0.0/16│     │  Pods: 10.244.0.0/16│
│  (same CIDR!)        │     │  (same CIDR!)        │
│                      │     │                      │
│  ┌────────────────┐  │     │  ┌────────────────┐  │
│  │ Submariner GW  │──┼─────┼──│ Submariner GW  │  │
│  │ (IPsec/WG)     │  │     │  │ (IPsec/WG)     │  │
│  └────────────────┘  │     │  └────────────────┘  │
│  Globalnet: 242.x    │     │  Globalnet: 243.x    │
└─────────────────────┘     └─────────────────────┘
```

The gateway nodes run in each cluster and maintain encrypted tunnels to every other cluster's gateway. When a Pod in cluster A sends traffic to an exported Service, the traffic is intercepted (typically through iptables rules or eBPF programs on the gateway node), the source Pod IP is NATed to a global-scope IP assigned to cluster A, the destination Service IP is translated to the global-scope IP assigned by the target cluster, and the resulting packet is encapsulated and sent through the tunnel. On the receiving side, the tunnel is decapsulated, the global IPs are NATed back to the actual Pod IPs, and the traffic is delivered.

The double NAT adds measurable latency — typically 1 to 3 milliseconds per round trip for the translation step alone, plus the tunnel encapsulation overhead of 5 to 10 percent throughput reduction. For most workloads this is negligible; for latency-sensitive applications making multiple cross-cluster hops per transaction, it can accumulate beyond acceptable SLOs. The operational trade-off is clear: overlay networking lets you connect clusters with zero CIDR planning and works across any network that allows UDP traffic between the gateway nodes, but you pay for that flexibility with every cross-cluster packet.

### Model 3: Service-Level Connectivity — Explicit Export

Service-level connectivity abandons the goal of universal Pod-to-Pod reachability. Instead, only specifically exported Services are shared across clusters, and all traffic passes through a controlled gateway. Pods cannot reach arbitrary Pods in other clusters by IP — they can only reach Services that have been explicitly published.

```
┌──────────────────────┐     ┌──────────────────────┐
│  Cluster A            │     │  Cluster B            │
│                       │     │                       │
│  ┌──────────────┐    │     │  ┌──────────────┐    │
│  │ api-service   │◄───┼─────┼──│ payment-svc   │    │
│  │ (ClusterIP)  │    │     │  │ (exported)    │    │
│  └──────────────┘    │     │  └──────────────┘    │
│        ▲              │     │                       │
│  ServiceImport        │     │  ServiceExport        │
│  (from Cluster B)     │     │  (to Cluster A)       │
└──────────────────────┘     └──────────────────────┘
```

This model prioritizes security and explicit control over universal connectivity. It forces teams to declare which Services cross the cluster boundary, making cross-cluster dependencies visible and auditable. The gateway that terminates cross-cluster traffic is a natural point for applying policy — mTLS enforcement, rate limiting, traffic filtering — without requiring those policies to be distributed to every Pod in the mesh.

The trade-off is reduced flexibility. If a developer in cluster A needs to reach a Service in cluster B that has not been exported, they must go through an explicit export process rather than simply addressing it by IP. In practice, this constraint is often desirable — it prevents the accidental creation of invisible cross-cluster dependencies that complicate failure analysis and cluster decommissioning.

### Choosing the Right Model

This table compares the three models on the dimensions that matter in production. No model is universally superior; the right choice depends on your specific constraints and priorities.

| Factor | Flat | Overlay | Service-Level |
|--------|:----:|:-------:|:-------------:|
| CIDR overlap OK | No — requires unique, non-overlapping CIDRs across all clusters | Yes — address translation handles overlaps transparently | N/A — Services, not Pods, are the unit of connectivity |
| Cross-cluster latency | Best — zero encapsulation overhead | Good — adds 5 to 10 percent round-trip overhead from tunnel encapsulation and NAT | Good — gateway hop adds one additional network segment |
| Security posture | Low — any Pod can reach any Pod across clusters by IP unless you layer NetworkPolicy enforcement across the mesh | Medium — encrypted tunnel protects traffic in transit, but Pod IPs are still routable | Highest — only exported Services are reachable; gateway provides a policy enforcement point |
| CIDR planning burden | High — every new cluster, every environment, every region must coordinate CIDR allocation | None — clusters can use whatever CIDRs they already have | Low — Service names, not IPs, are the coordination surface |
| Operational complexity | Low to medium — works where network infrastructure supports route propagation | Medium — gateway nodes and tunnel configuration add moving parts | Medium to high — export/import lifecycle, gateway management, and service registry synchronization |
| Cross-cloud / hybrid cloud | Requires VPN, VPC peering, or dedicated interconnect between every site | Works anywhere UDP traffic can pass between gateway nodes | Works anywhere — gateway can run behind NAT, through firewalls, over any transport |

---

## Part 4: Tool Deep Dives and the Durable Capability Set

The tools that implement multi-cluster networking evolve rapidly, but the capabilities they provide are durable. This section examines four representative tools — Cilium ClusterMesh, Submariner, Istio multi-cluster, and Linkerd multi-cluster — through the lens of the durable capabilities they implement. A dated landscape snapshot and a capability Rosetta follow, so you can map any current or future tool to the same capability framework.

### Cilium ClusterMesh

ClusterMesh connects Cilium-managed clusters into a single logical mesh where Services, endpoints, and network policy state are synchronized across clusters. It operates at the eBPF dataplane level, which means cross-cluster traffic follows the same fast path as intra-cluster traffic once the endpoint mapping is resolved.

The architecture relies on a shared etcd-based ClusterMesh API server. Each cluster contributes its endpoints for globally-annotated Services to this API server, and each cluster watches the shared state to discover remote endpoints. When a Pod in cluster A resolves `payment-service.production.svc.cluster.local`, Cilium's DNS proxy intercepts the query and returns both local and remote endpoints. The eBPF dataplane then selects an endpoint based on the configured affinity — local first, remote as fallback, or round-robin across all.

The identity system is a critical part of ClusterMesh. Cilium assigns each Pod a numeric security identity derived from its labels and namespace. These identities are synchronized across clusters through the ClusterMesh API server, which means a NetworkPolicy in cluster A can refer to identities from cluster B. A policy that says "allow traffic from `app=frontend` in namespace `production`" will match Pods with those labels regardless of which cluster they run in. This is one of the few implementations that provides cross-cluster NetworkPolicy enforcement without a separate service mesh layer.

```bash
# Prerequisites: Cilium installed on both clusters with unique cluster IDs
# Cluster A:
cilium install --cluster-name cluster-a --cluster-id 1 \
  --set cluster.name=cluster-a \
  --set cluster.id=1

# Cluster B:
cilium install --cluster-name cluster-b --cluster-id 2 \
  --set cluster.name=cluster-b \
  --set cluster.id=2

# Enable ClusterMesh on both clusters
cilium clustermesh enable --service-type LoadBalancer
# (Use NodePort if no LoadBalancer available)

# Wait for ClusterMesh API server to be ready
cilium clustermesh status --wait

# Connect the clusters
cilium clustermesh connect --destination-context cluster-b
```

**Sharing Services across clusters:**

```yaml
# In Cluster B: annotate the Service to be global
apiVersion: v1
kind: Service
metadata:
  name: payment-service
  namespace: production
  annotations:
    service.cilium.io/global: "true"
    # Optional: prefer local endpoints, fall back to remote
    service.cilium.io/affinity: "local"
spec:
  selector:
    app: payment
  ports:
    - port: 8080
```

Once annotated, Pods in Cluster A can reach `payment-service.production.svc.cluster.local` and traffic will be load balanced across endpoints in both clusters.

```bash
# Verify cross-cluster connectivity
cilium clustermesh status
# Shows: connected clusters, shared services, endpoint counts

# View cross-cluster endpoints
kubectl get ciliumendpoints -A | grep -i payment
```

### Submariner

Submariner creates encrypted tunnels between clusters and supports the Multi-Cluster Services (MCS) API natively. It is CNI-agnostic — it works with any CNI plugin that provides standard Kubernetes networking — which makes it the default choice when clusters run different CNIs or when you cannot require a specific CNI across all clusters.

The architecture has three components: a Broker (a lightweight coordination component deployed on one cluster that exchanges metadata), Gateway Engine (runs on gateway nodes in each cluster, establishes and maintains IPsec or WireGuard tunnels), and Route Agent (runs on every node, configures routing and iptables rules to steer cross-cluster traffic through the local gateway).

Submariner's Globalnet component is its answer to the overlapping CIDR problem. When enabled, Globalnet assigns each cluster a unique "global" CIDR block (drawn from a private range configured during deployment). Every exported Service gets a global IP from its cluster's block. When a Pod in cluster A connects to an exported Service from cluster B, the source Pod IP is NATed to cluster A's global range, the destination is rewritten to the Service's global IP in cluster B's range, and the packet traverses the encrypted tunnel. On arrival, cluster B's Globalnet reverses the NAT and delivers the packet to the actual Pod.

```bash
# Install subctl CLI
curl -Ls https://get.submariner.io | VERSION=0.23.1 bash

# Deploy the broker (coordination component) on Cluster A
subctl deploy-broker --kubeconfig kubeconfig-cluster-a

# Join Cluster A to the broker
subctl join broker-info.subm --kubeconfig kubeconfig-cluster-a \
  --clusterid cluster-a \
  --nattport 4500

# Join Cluster B
subctl join broker-info.subm --kubeconfig kubeconfig-cluster-b \
  --clusterid cluster-b \
  --nattport 4500

# Verify connectivity
subctl show all
subctl verify --kubeconfig kubeconfig-cluster-a \
  --toconfig kubeconfig-cluster-b --only connectivity
```

**Exporting Services with MCS API:**

```yaml
# In Cluster B: export the service
apiVersion: multicluster.x-k8s.io/v1alpha1
kind: ServiceExport
metadata:
  name: payment-service
  namespace: production
```

```yaml
# In Cluster A: the ServiceImport is created automatically
# Pods can now reach:
#   payment-service.production.svc.clusterset.local
# (Note: .clusterset.local instead of .cluster.local)
```

```bash
# Verify service export
kubectl get serviceexport -n production
kubectl get serviceimport -n production  # On the consuming cluster
```

### Istio Multi-Cluster

Istio's multi-cluster model takes a service-mesh-first approach. Rather than connecting Pod networks, Istio federates its service registries across clusters so that an Istio sidecar in cluster A knows about services and endpoints in cluster B. Traffic flows through east-west gateways — dedicated Istio ingress gateways configured to accept cross-cluster mesh traffic with mutual TLS.

There are two deployment models. In a single-network deployment (clusters share a flat network), Istio configures sidecars to reach remote Pod IPs directly, using mTLS but no gateway hop. In a multi-network deployment (clusters are on separate, non-routable networks), cross-cluster traffic passes through east-west gateways in both clusters. The gateways terminate mTLS, forward traffic to the destination sidecar, and ensure that traffic is encrypted end-to-end.

The advantage of Istio's model is that it integrates cross-cluster traffic into the same observability, policy, and security framework as intra-cluster traffic. Distributed tracing spans continue across cluster boundaries. Authorization policies defined in one cluster can reference principals from another cluster. The trade-off is that every Pod that participates in cross-cluster communication needs an Istio sidecar, which adds resource overhead and operational complexity.

### Linkerd Multi-Cluster

Linkerd takes a deliberately simpler approach. Its multi-cluster model mirrors services across clusters using a gateway-based mechanism. A service in cluster B can be "mirrored" into cluster A, which creates a shadow Service in cluster A that points to the gateway in cluster B. When a Pod in cluster A calls the mirrored service, Linkerd's proxy routes the traffic to the local gateway, which forwards it across an encrypted link to cluster B's gateway, which delivers it to the actual service.

Linkerd's design philosophy — minimal configuration, automatic mTLS, and transparent proxying — carries through to its multi-cluster implementation. There is no shared control plane, no federated identity registry, and no cross-cluster policy engine. Each cluster remains independent, with mirrored services providing a controlled window between them. This simplicity makes Linkerd multi-cluster fast to set up and easy to reason about, but it limits the cross-cluster features to service mirroring — there is no cross-cluster traffic splitting, no cross-cluster fault injection, and no cross-cluster authorization policies.

### Skupper (Application-Layer Connectivity)

Skupper uses an application-layer Virtual Application Network (VAN) to connect services without VPN or special network configuration. It is the right choice when you need to connect Kubernetes clusters to non-Kubernetes workloads (VMs, bare metal) or connect clusters across restrictive firewalls where VPN setup is impossible.

```bash
# Install Skupper CLI
curl https://skupper.io/install.sh | sh

# In Cluster A: initialize Skupper
skupper init --site-name cluster-a

# In Cluster B: initialize and create a link token
skupper init --site-name cluster-b
skupper token create cluster-b-token.yaml

# In Cluster A: use the token to establish the link
skupper link create cluster-b-token.yaml

# In Cluster B: expose a service
skupper expose deployment payment-service --port 8080

# In Cluster A: the service is now accessible
kubectl get services  # payment-service appears as a local ClusterIP
```

---

### Landscape Snapshot — as of 2026-06

This changes fast; verify against vendor docs before relying on specifics.

| Tool | CNCF Status | Model | Transport | Max Clusters (documented) |
|------|------------|-------|-----------|---------------------------|
| Cilium ClusterMesh | Graduated | Flat or tunneled, eBPF-based | VXLAN, Geneve, or WireGuard | 255 |
| Submariner | Sandbox | Overlay (IPsec/WireGuard tunnels) | IPsec or WireGuard | 20 to 30 (practical guidance) |
| Istio multi-cluster | Graduated | Service-level via east-west gateways | mTLS over TCP, with gateway hops for multi-network | No hard limit; tested in large meshes |
| Linkerd multi-cluster | Graduated | Service mirroring via gateways | mTLS over TCP | No published hard limit |

### Capability Rosetta

Each row is a durable capability. Each column shows how a representative tool implements it. Use this to compare any tool against the capability set, including tools introduced after this writing.

| Capability | Cilium ClusterMesh | Submariner | Istio multi-cluster | Linkerd multi-cluster |
|------------|-------------------|------------|---------------------|----------------------|
| Cross-cluster Pod routing | Yes — direct Pod-to-Pod routing via synchronized endpoint state in the ClusterMesh API | Yes — routed through encrypted tunnels between gateway nodes, with Globalnet NAT for overlapping CIDRs | No — traffic is service-to-service through sidecar proxies; raw Pod IP routing is not the model | No — service mirroring only; individual Pods are not addressable across clusters |
| Service discovery (MCS API) | Own annotation-based mechanism (`cilium.io/global`); does not implement the MCS CRD contract | Native `ServiceExport`/`ServiceImport` via the `multicluster.x-k8s.io` CRDs | Own service registry federation; does not implement MCS CRDs but achieves the same outcome through Istio's service mesh abstractions | Own mirroring mechanism; does not implement MCS CRDs |
| Cross-cluster mTLS | Yes — through Cilium's WireGuard or IPsec transparent encryption; optionally through Cilium's own identity-based network policy | Yes — IPsec or WireGuard tunnels encrypt all cross-cluster traffic between gateways | Yes — Istio's mutual TLS between sidecars, with east-west gateways for multi-network deployments | Yes — Linkerd's automatic mTLS between proxies, terminated at gateways for cross-cluster hops |
| CIDR-overlap handling | No — requires unique, non-overlapping Pod CIDRs across all clusters in the mesh | Yes — Globalnet assigns each cluster a unique global CIDR and performs double NAT on cross-cluster traffic | N/A — services, not Pod IPs, are the unit of routing; CIDR overlap is transparent | N/A — services, not Pod IPs, are the unit of routing |
| Locality-aware failover | Yes — `cilium.io/affinity: local` annotation prefers local endpoints, falls back to remote | Via Kubernetes topology-aware routing with `topology.kubernetes.io/zone` labels | Yes — Istio locality load balancing with failover priority configured in DestinationRules | No built-in locality support; symmetric service mirroring only |
| Cross-cluster NetworkPolicy | Yes — CiliumNetworkPolicy can reference identities from remote clusters via the synchronized identity store | No — Submariner does not synchronize NetworkPolicy state or identity across clusters | Yes — Istio AuthorizationPolicy can reference principals by SPIFFE identity, which is federated across clusters | No — Linkerd does not federate policy state across clusters |
| Non-K8s workload support | No — Cilium requires its CNI on every participating node | No — Submariner requires Kubernetes clusters for its gateway engine and route agent | No — Istio requires its sidecar proxy | No — Linkerd requires its sidecar proxy |
| CNI dependency | Yes — clusters must run Cilium as their CNI | No — works with any CNI that provides standard Kubernetes networking | No — works with any CNI; requires Istio sidecar injection | No — works with any CNI; requires Linkerd sidecar injection |

> **Note on Skupper**: Skupper is excluded from the Rosetta because it operates at the application layer (L7) rather than the network or service-mesh layer. It is the tool to reach for when connecting Kubernetes to non-Kubernetes workloads, or when firewall restrictions prevent any tunnel or mesh-based approach. It does not compete with the tools above on network-level capabilities.

---

## Part 5: Identity and Trust Across Clusters

When a Pod in cluster A sends a request to a Service in cluster B, that request crosses a trust boundary. The two clusters have separate certificate authorities, separate ServiceAccount token issuers, and separate NetworkPolicy engines. Without a shared identity framework, you cannot authenticate the caller, you cannot enforce fine-grained authorization, and you cannot audit the call chain. The traffic itself may be encrypted (through IPsec tunnels or WireGuard), but encryption without authentication protects against eavesdroppers, not against impersonators.

The SPIFFE (Secure Production Identity Framework for Everyone) standard provides the durable answer to cross-cluster identity. SPIFFE defines a universal identity format — the SPIFFE ID, which looks like `spiffe://trust-domain.example/ns/production/sa/payment-processor` — and a mechanism for issuing and verifying these identities through the SPIRE agent. When SPIFFE is deployed across clusters, every workload gets a short-lived X.509 certificate or JWT token that carries its SPIFFE ID. A workload in cluster A can verify that a workload in cluster B genuinely runs as `spiffe://cluster-b.example/ns/production/sa/payment-service` because the certificate chains back to a trust root that both clusters recognize.

In practice, most teams do not deploy standalone SPIFFE. Instead, they get cross-cluster identity through the service mesh they are already running. Istio's Citadel component (in older versions) or its cert-manager integration (in current versions) acts as a SPIFFE-compatible identity provider, issuing certificates to each sidecar with the workload's SPIFFE ID. Linkerd's identity controller does the same, with a simpler trust model that federates across clusters by sharing a common trust anchor. Cilium, when operating in ClusterMesh mode, synchronizes numeric security identities — derived from Pod labels and namespaces — through the shared etcd-based API server, which provides identity-based policy enforcement even without SPIFFE certificates.

The operational lesson is that cross-cluster identity is not optional if you have cross-cluster traffic. Without it, your security model has a gap: traffic is encrypted in transit, but you cannot answer the question "who is calling me?" across the cluster boundary. With it, your authorization policies — whether Kubernetes NetworkPolicies, CiliumNetworkPolicies, Istio AuthorizationPolicies, or Linkerd ServerAuthorization resources — can express rules that span clusters, and your audit logs can trace a request from its origin in one cluster to its destination in another.

Building a shared trust domain requires exactly two things: a common trust root (the CA certificate that all clusters trust) and a mechanism for distributing identity documents (certificates or JWTs) to workloads. Service meshes provide both. If you are running without a service mesh, you can achieve the same outcome with cert-manager's CSI driver and a shared CA, or with SPIRE deployed across clusters. The mechanism matters less than the outcome: every workload that participates in cross-cluster communication must carry a verifiable identity that is recognized on both sides of the cluster boundary.

---

## Part 6: DNS-Based Service Discovery

DNS is the universal discovery mechanism in Kubernetes, and it extends naturally to multi-cluster topologies. The challenge is that each cluster runs its own CoreDNS instance authoritative for `cluster.local`, and these instances do not know about each other's services by default. There are two durable patterns for multi-cluster DNS: internal resolution through CoreDNS forwarding and global discovery through external DNS providers.

### Internal Cross-Cluster DNS with CoreDNS

When two clusters share a network — either through flat routing or through tunneled connectivity — you can configure CoreDNS in each cluster to forward queries for the other cluster's domain. A stub domain configuration in CoreDNS tells it: "for any query ending in `cluster-b.local`, forward the request to cluster B's CoreDNS service IP."

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: coredns
  namespace: kube-system
data:
  Corefile: |
    .:53 {
        errors
        health
        ready
        kubernetes cluster.local in-addr.arpa ip6.arpa {
            pods insecure
            fallthrough in-addr.arpa ip6.arpa
        }
        # Forward queries for cluster-b services to cluster-b's DNS
        cluster-b.local:53 {
            forward . 10.100.0.10   # Cluster B's CoreDNS IP
        }
        forward . /etc/resolv.conf
        cache 30
        loop
        reload
        loadbalance
    }
```

This approach works well for clusters in the same administrative domain where you control the CoreDNS configuration on both sides. It does not scale to many clusters — each new cluster requires a new stub domain entry in every other cluster's CoreDNS ConfigMap — and it does not handle dynamic service discovery (you are forwarding DNS queries, not synchronizing service registries). The MCS API and its `clusterset.local` domain solve this more cleanly for tools that implement it, but CoreDNS forwarding remains a lightweight option for simple two-cluster or three-cluster setups.

### Global Discovery with external-dns

The `external-dns` project synchronizes Kubernetes Service, Ingress, and Gateway API resources with external DNS providers (Route53, Cloudflare, Google Cloud DNS, Azure DNS, and over 30 others). In a multi-cluster setup, external-dns runs in each cluster with a unique owner identifier, creating and updating DNS records for the resources in that cluster. When the same hostname appears in multiple clusters, external-dns creates multiple records, and the DNS provider's routing policy determines how traffic is distributed.

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: external-dns
  namespace: kube-system
spec:
  replicas: 1
  selector:
    matchLabels:
      app: external-dns
  template:
    metadata:
      labels:
        app: external-dns
    spec:
      serviceAccountName: external-dns
      containers:
        - name: external-dns
          image: registry.k8s.io/external-dns/external-dns:v0.15.1
          args:
            - --source=service
            - --source=ingress
            - --source=gateway-httproute   # Gateway API support
            - --provider=aws               # or google, azure, cloudflare
            - --domain-filter=example.com
            - --aws-zone-type=public
            - --txt-owner-id=cluster-a     # Unique per cluster
            - --policy=upsert-only         # Don't delete records from other clusters
```

The `--txt-owner-id` flag is critical: it ensures that external-dns in cluster A does not delete records created by external-dns in cluster B. With `--policy=upsert-only`, external-dns adds and updates its own records but never removes records owned by another cluster.

### DNS-Based Failover Pattern

External DNS, combined with health checks at the DNS provider, provides cluster-level failover without any cross-cluster networking at all. Each cluster operates independently, publishing its own DNS records with its own health check. When a cluster goes unhealthy, the DNS provider stops routing traffic to its records, and traffic shifts to the remaining healthy clusters.

```
┌─────────────────────────────────────────────────────────────┐
│  Route53 (weighted routing)                                  │
│  api.example.com                                             │
│    ├── 50% → cluster-a.api.example.com (us-east-1)          │
│    └── 50% → cluster-b.api.example.com (eu-west-1)          │
│                                                              │
│  Health checks:                                              │
│    cluster-a: GET /healthz → 200 ✓                           │
│    cluster-b: GET /healthz → 200 ✓                           │
│                                                              │
│  If cluster-a fails health check:                            │
│    100% → cluster-b.api.example.com                          │
└─────────────────────────────────────────────────────────────┘
```

```bash
# AWS Route53 health check + weighted routing
aws route53 create-health-check --caller-reference "cluster-a-$(date +%s)" \
  --health-check-config '{
    "IPAddress": "203.0.113.10",
    "Port": 443,
    "Type": "HTTPS",
    "ResourcePath": "/healthz",
    "RequestInterval": 10,
    "FailureThreshold": 3
  }'
```

This approach has an important limitation: DNS-based failover only works for north-south (external) traffic that arrives through Ingress or Gateway resources. East-west traffic between Pods in different clusters — a service in cluster A calling a service in cluster B — is not routed through external DNS. For east-west failover, you need one of the mesh- or tunnel-based approaches described in Part 4, combined with locality-aware routing.

---

## Part 7: Failover, Locality, and Traffic Policy

Having multiple clusters is not the same as being resilient. Resilience comes from the ability to detect when a cluster is unhealthy and shift traffic away from it — automatically, quickly, and without losing in-flight requests. The durable patterns for multi-cluster failover fall into three layers, each solving a different part of the problem.

### Topology-Aware Routing

Kubernetes provides built-in topology-aware routing through the `topology.kubernetes.io/zone` and `topology.kubernetes.io/region` labels on nodes. When a Service has `service.kubernetes.io/topology-mode: Auto` (the default in recent versions), kube-proxy prefers endpoints in the same zone as the calling Pod, falling back to other zones only when no local endpoints are healthy. In a multi-cluster context, tools like Cilium ClusterMesh extend this concept across cluster boundaries: the `service.cilium.io/affinity: local` annotation tells Cilium to prefer endpoints in the same cluster, falling back to remote clusters only when the local cluster has no healthy endpoints for the service.

Topology-aware routing addresses the latency problem — traffic stays local when possible — but it does not, by itself, handle failover. If a local endpoint becomes unhealthy, kube-proxy or the eBPF dataplane removes it from the endpoint list immediately. But if the entire local cluster becomes unhealthy, the DNS or service discovery mechanism must be reconfigured to remove the cluster's endpoints before traffic will shift. This is where health checking and traffic policy take over.

### Active-Active vs Active-Passive

An active-active deployment runs the same service in multiple clusters and distributes traffic across all of them. When one cluster fails, traffic that was going to that cluster is redistributed to the remaining clusters. The failover is graceful — no traffic shift is necessary, only a reduction in total capacity. Active-active requires that all clusters be capable of serving traffic for the workload, which in turn requires that data be available in all clusters (through replication, distributed databases, or stateless workloads).

An active-passive deployment runs the service in one primary cluster and keeps a standby in another. Traffic flows exclusively to the primary. When the primary fails, a failover mechanism — DNS health check, global load balancer reconfiguration, or manual intervention — shifts traffic to the standby. Active-passive is simpler to reason about because only one cluster is active at a time, but the failover is a discrete event with a non-zero window during which the service is degraded or unavailable.

The choice between these models depends on the data layer, not the networking layer. If your data cannot be replicated across clusters with acceptable consistency and latency, you cannot run active-active — the networking will route traffic correctly, but the data will be stale or inconsistent. If your data is stateless or replicated, active-active provides the smoothest failover behavior because there is no failover event at all — just a capacity reduction that is absorbed by the remaining clusters.

### Health Checking at the Right Level

Health checks for multi-cluster failover must operate at the cluster level, not the Pod level. A Pod health check tells you whether that specific Pod is healthy; it does not tell you whether the cluster's control plane is functional, whether the CNI is routing traffic correctly, or whether the cluster's DNS is resolving names. A cluster-level health check — an HTTP endpoint served from within the cluster that exercises DNS resolution, service connectivity, and a database ping — provides a more reliable signal. When this health check fails, the entire cluster should be removed from the traffic rotation, even if individual Pod health checks are still passing.

### The Role of DNS TTL

DNS-based failover is gated by TTL (Time To Live). When a cluster goes down and its DNS record is removed or deprioritized, clients that have cached the old DNS response continue sending traffic to the failed cluster until the cached entry expires. A TTL of 300 seconds (5 minutes) means up to 5 minutes of traffic to a failed cluster after the DNS record is updated. A TTL of 30 seconds means at most 30 seconds of stale traffic.

Lower TTLs reduce the failover window but increase DNS query volume and add per-request latency for initial resolutions. The trade-off is straightforward: for services where 5 minutes of downtime is acceptable, a 300-second TTL is fine. For services where 10 seconds of downtime triggers an incident, a 10-second TTL is necessary, and you should pair it with a DNS provider that can handle the increased query load and with client-side connection pooling to amortize the resolution cost.

---

## Part 8: Hybrid Cloud Connectivity

Connecting Kubernetes clusters that span cloud providers and on-premises data centers introduces additional constraints: varying network topologies, different bandwidth and latency profiles, firewall policies you do not control, and infrastructure teams with different priorities and tooling. The durable patterns for hybrid cloud networking are the same as those for single-cloud multi-cluster networking, but the operational surface is larger and the failure modes are more numerous.

### VPN Connectivity

```
┌──────────────────┐          ┌──────────────────┐
│  Cloud (AWS)      │          │  On-Prem DC       │
│  VPC: 10.0.0.0/16│          │  Net: 172.16.0.0/12│
│                   │          │                    │
│  K8s Cluster      │  IPsec   │  K8s Cluster       │
│  Pods: 10.1.0.0/16│←────────→│  Pods: 10.2.0.0/16 │
│                   │  VPN     │                    │
│  AWS VPN Gateway  │          │  On-prem VPN GW    │
└──────────────────┘          └──────────────────┘
```

IPsec VPN tunnels between cloud and on-premises environments are the most common integration pattern, and they work reliably when the constraints are understood. The tunnel endpoints must have consistent MTU configurations — IPsec encapsulation reduces the effective MTU, and mismatched MTU values cause silent packet drops on large payloads that are notoriously difficult to diagnose. VPN throughput is typically 1 to 5 Gbps per tunnel, which is sufficient for most cross-cluster service traffic but not for bulk data transfer or large-scale Pod migration. Latency is a function of geographic distance plus tunnel encapsulation overhead, typically 1 to 5 milliseconds of added processing delay per hop.

For production deployments, use redundant VPN tunnels with different endpoint IPs and monitor tunnel state continuously. A single tunnel is a single point of failure, and VPN tunnel flaps — where the tunnel drops and re-establishes — can cause cascading failures in applications that do not handle transient network errors gracefully.

### Direct Connect and ExpressRoute

For environments where VPN throughput or reliability is insufficient, AWS Direct Connect and Azure ExpressRoute provide dedicated, private network connections between on-premises infrastructure and cloud VPCs or VNets. These connections offer higher bandwidth (up to 100 Gbps), lower and more consistent latency, and service-level agreements that VPNs cannot match.

The trade-off is cost and lead time. A Direct Connect circuit can take weeks to provision and costs several thousand dollars per month in port charges alone, independent of data transfer. For clusters that exchange high volumes of traffic — continuous database replication, large-scale log aggregation, cross-cluster storage synchronization — the dedicated connection pays for itself in reliability. For clusters that exchange only occasional service-to-service calls, VPN is usually sufficient.

### CIDR Planning Template

CIDR allocation across environments must be coordinated before the first cluster is created. The template below shows a typical non-overlapping allocation for three clusters spanning cloud regions and an on-premises data center. Every address range — Node CIDR, Pod CIDR, and Service CIDR — must be unique across all clusters.

| Environment | Node CIDR | Pod CIDR | Service CIDR |
|-------------|-----------|----------|-------------|
| Cluster A (us-east-1) | 10.0.0.0/16 | 10.1.0.0/16 | 10.96.0.0/16 |
| Cluster B (eu-west-1) | 10.10.0.0/16 | 10.11.0.0/16 | 10.97.0.0/16 |
| Cluster C (on-prem) | 172.16.0.0/16 | 172.17.0.0/16 | 172.18.0.0/16 |

Rules for CIDR planning that prevent expensive retrofits:
1. No overlap between any CIDR ranges across all clusters — Node, Pod, and Service CIDRs must all be disjoint.
2. Reserve space for future clusters. Do not allocate a /8 to a single cluster; use /16 blocks and leave the surrounding address space unallocated.
3. Maintain a central CIDR registry — a simple document or spreadsheet — that tracks every allocated range, the cluster that owns it, and the date of allocation.
4. If you inherit clusters with overlapping CIDRs, Submariner Globalnet is the lowest-friction retrofit. Accept the added latency as the cost of the legacy allocation and plan to rebuild clusters with clean CIDRs during the next major upgrade cycle.

---

## Part 9: Troubleshooting Cross-Cluster Networking

Cross-cluster networking failures are harder to diagnose than intra-cluster failures because the problem can exist in any of five layers: the underlay network between clusters, the tunnel or peering mechanism, the DNS configuration, the service discovery synchronization, or the application itself. A systematic diagnostic approach — working from the lowest layer upward — prevents the most common troubleshooting mistake: spending an hour debugging application code when the real issue is an MTU mismatch on the VPN tunnel.

### Diagnostic Checklist

```bash
# 1. Underlay: Can nodes in Cluster A reach nodes in Cluster B?
ping <cluster-b-node-ip>

# 2. Tunnel/peering: Is the cross-cluster link established?
# Submariner:
subctl show connections
# Cilium ClusterMesh:
cilium clustermesh status

# 3. DNS: Can Pods resolve cross-cluster DNS names?
kubectl run dns-test --rm -it --image=busybox:1.36 --restart=Never -- \
  nslookup payment-service.production.svc.clusterset.local

# 4. Connectivity: Can Pods reach cross-cluster Services?
kubectl run net-test --rm -it --image=nicolaka/netshoot --restart=Never -- \
  curl -v http://payment-service.production.svc.clusterset.local:8080/healthz

# 5. MTU: Check for MTU issues (the most common silent failure)
kubectl run mtu-test --rm -it --image=nicolaka/netshoot --restart=Never -- \
  ping -M do -s 1400 <remote-pod-ip>
# If this fails but ping -s 1300 works, you have an MTU issue.
# Reduce the MTU on the tunnel interface or the Pod network.

# 6. Firewall: Verify required ports are open
# Submariner needs: UDP 4500 (IPsec NAT-T), UDP 4490 (tunnel)
# Cilium ClusterMesh needs: TCP 2379 (etcd), TCP 4240 (health)
```

The MTU issue deserves special attention because it is disproportionately common and disproportionately hard to spot. When a tunnel encapsulation header (IPsec adds roughly 60 to 80 bytes, VXLAN adds 50 bytes) pushes the total packet size above the path MTU, the packet is fragmented or dropped. Fragmented packets may be blocked by firewalls that do not permit fragments, and dropped packets manifest as intermittent application-level timeouts — the kind of failure that gets blamed on application code rather than on the network. The diagnostic is simple: run the `ping -M do` test above with progressively smaller payloads until it succeeds, then set the tunnel or Pod network MTU to that value minus a small safety margin.

### Common Cross-Cluster Issues

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| DNS resolution fails for `.clusterset.local` | Submariner CoreDNS plugin not installed or MCS CRDs not applied | Run `subctl diagnose all`; verify `ServiceExport` and `ServiceImport` CRDs exist on the cluster |
| Intermittent timeouts on large payloads | MTU mismatch — tunnel encapsulation pushes packets above the path MTU | Set tunnel interface MTU to 1400 (for VXLAN) or 1380 (for IPsec); verify with `ping -M do` |
| Service reachable from one cluster but not the other | Asymmetric routing — packets arrive but the return path is missing or blocked | Check route tables on gateway nodes in both directions; verify symmetric tunnel configuration |
| ClusterMesh shows "connected" but Services are not shared | Missing `service.cilium.io/global: "true"` annotation on the service, or the namespace does not exist in the consuming cluster | Verify annotation exists; create the matching namespace in the consuming cluster |
| VPN tunnel flaps repeatedly | Keep-alive timeout too aggressive, or intermediate firewall drops idle connections | Increase Dead Peer Detection interval; check cloud provider VPN connection limits; add redundant tunnels |
| Cross-cluster latency is consistently higher than expected | Traffic is routing through a distant gateway node or hairpinning through an intermediate hop | Verify gateway node placement (should be on nodes with direct network connectivity); check `traceroute` between clusters |

---

## Patterns and Anti-Patterns

### Patterns

**Pattern 1: CIDR-First Planning.** Before deploying the first cluster, allocate all CIDR ranges — Node, Pod, and Service — for every planned cluster across every environment and every region. Record the allocations in a central registry. Treat CIDR allocation like a database schema: easy to design correctly at the start, expensive and risky to change later. This pattern eliminates the most common blocker to flat, low-latency multi-cluster networking.

**Pattern 2: Graduated Connectivity.** Start with independent clusters that share nothing at the network layer. Add DNS-based failover for north-south traffic through external-dns. Only when east-west service-to-service communication is needed across clusters, introduce a mesh or tunnel-based approach, starting with the smallest possible surface area — export one service, verify it works end-to-end, then expand. Each layer of connectivity adds operational complexity; do not add a layer that you do not need.

**Pattern 3: Cluster-Level Health Checks.** Do not rely on Pod-level health checks for failover decisions. Implement a cluster-local health endpoint that validates DNS resolution, service connectivity to a known-good service, and a lightweight database query. Use this endpoint as the health check signal for removing a cluster from the traffic rotation. A cluster whose Pods appear healthy but whose DNS is broken will silently drop traffic.

**Pattern 4: Periodic Failover Drills.** Schedule a monthly exercise where one cluster is removed from the traffic rotation and the failover behavior is observed and measured. Record the time from health check failure to complete traffic shift. Record any application errors during the transition. Treat failover time as an SLO and drive it down through configuration improvements. A failover mechanism that has never been tested is a failover mechanism that does not work.

### Anti-Patterns

| Anti-Pattern | Why It's Harmful | Better Approach |
|--------------|-----------------|-----------------|
| Deploying all clusters with the same default CIDR | Creates an overlapping CIDR problem that can only be fixed by rebuilding clusters or accepting the latency penalty of double-NAT overlay solutions | Allocate unique /16 blocks from the 10.0.0.0/8 range for each cluster before creation; document all allocations |
| Assuming two clusters equals high availability | Traffic will not shift automatically unless you have configured and tested the failover mechanism — DNS health checks, service mesh locality routing, or global load balancer rules | Implement cluster-level health checks, configure the failover mechanism for each critical service, and run monthly failover drills |
| Opening all ports between clusters "just to get it working" | Creates a security boundary violation that is almost never tightened later; cross-cluster traffic should be as restricted as intra-cluster traffic | Whitelist only the specific ports required by your chosen connectivity mechanism: TCP 2379 and 4240 for Cilium ClusterMesh, UDP 4500 and 4490 for Submariner |
| Using high DNS TTLs on records used for failover | When a cluster fails and its DNS record is removed, clients continue sending traffic to the failed cluster for the full TTL duration — a 300-second TTL means up to 5 minutes of traffic to a dead cluster | Set TTL to 30 to 60 seconds for records involved in failover; accept the modest increase in DNS query volume |
| Running cross-cluster traffic without monitoring cross-cluster latency | Teams monitor per-cluster metrics (Pod latency, Service latency) but not the cross-cluster hop, which is typically where problems manifest | Deploy blackbox exporters or mesh-native latency probes that measure the full path from a Pod in cluster A to a Service in cluster B; set SLOs on cross-cluster latency |
| Exporting services without documenting the dependency | Cross-cluster dependencies become invisible: nobody knows that cluster A's payment service depends on cluster B's fraud-detection service until cluster B is taken down for maintenance and payments start failing | Maintain a registry of exported services with ownership, contact information, and SLO expectations; treat cross-cluster dependencies like any other service dependency |

---

## Decision Framework

Use this decision framework to evaluate whether, how, and with which tools to implement multi-cluster networking. The framework moves from strategic questions (do you need it at all?) through architectural questions (which model fits?) to implementation questions (which tool?).

```
┌─────────────────────────────────────────────────────────────────────┐
│                  Multi-Cluster Networking Decision Flow               │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  Q1: Do you genuinely need multiple clusters?                         │
│      ├── Yes, for blast-radius isolation ──→ Continue to Q2           │
│      ├── Yes, for regional/latency proximity ──→ Continue to Q2       │
│      ├── Yes, for regulatory/data-residency ──→ Continue to Q2        │
│      └── No, a single larger cluster is simpler ──→ Stop here         │
│                                                                       │
│  Q2: What kind of traffic crosses clusters?                           │
│      ├── Only external/north-south (users → cluster)                  │
│      │   └── DNS-based failover (external-dns + health checks)        │
│      ├── East-west service-to-service                                │
│      │   └── Continue to Q3                                           │
│      └── Both                                                        │
│          └── Continue to Q3 for east-west; DNS for north-south        │
│                                                                       │
│  Q3: Can you control CIDR allocation across all clusters?             │
│      ├── Yes, all clusters use non-overlapping CIDRs                  │
│      │   └── Flat networking is viable (Cilium ClusterMesh,           │
│      │       direct VPC peering + routing)                            │
│      └── No, overlapping CIDRs exist or cannot be controlled          │
│          └── Overlay or service-level model required                  │
│              └── Submariner Globalnet (CIDR overlap + mesh)           │
│              └── Istio/Linkerd multi-cluster (service-level)          │
│                                                                       │
│  Q4: Do you need cross-cluster NetworkPolicy enforcement?             │
│      ├── Yes ──→ Cilium ClusterMesh (identity-based policies)         │
│      │          or Istio (AuthorizationPolicy across clusters)        │
│      └── No ──→ Broader tool choice; evaluate on other criteria       │
│                                                                       │
│  Q5: Are all clusters running the same CNI?                           │
│      ├── Yes, all Cilium ──→ Cilium ClusterMesh is the natural choice │
│      ├── Mixed CNIs ──→ Submariner (CNI-agnostic) or service mesh     │
│      └── Some are non-K8s workloads ──→ Skupper (application layer)   │
│                                                                       │
└─────────────────────────────────────────────────────────────────────┘
```

The decision tree above encodes two important principles. First, **start at the requirement, not at the tool**. The question "should we use Cilium ClusterMesh or Submariner?" is premature until you have answered Q1 through Q4. The tool is an implementation detail of the architecture; the architecture is an implementation detail of the requirement.

Second, **prefer the simplest mechanism that satisfies the requirement**. If your only cross-cluster traffic is external users hitting an Ingress, do not deploy a service mesh. Use external-dns and DNS health checks. If you need east-west service-to-service communication between two clusters in the same VPC, do not deploy Submariner Globalnet. Use flat networking with VPC peering and CoreDNS stub domains. Each additional component — a gateway, a tunnel, a NAT layer, a service registry federation — adds operational burden. Add only the components that solve a requirement you actually have.

---

## Did You Know?

- Cilium ClusterMesh can connect up to 255 clusters in a single mesh with a shared Pod identity system. Pods in any cluster can reach Pods in any other cluster using standard Kubernetes Service names, with no application changes. Each cluster maintains its own control plane — there is no single point of failure.

- Submariner, a CNCF Sandbox project, creates encrypted tunnels between clusters using IPsec or WireGuard. It supports non-overlapping and overlapping Pod CIDRs through its Globalnet component, which assigns unique "global" IPs to exported Services. This means you can connect clusters that were provisioned with the same default 10.244.0.0/16 range without rebuilding either one.

- The `external-dns` project can synchronize Kubernetes Service and Ingress resources with over 30 DNS providers (Route53, Cloudflare, Google Cloud DNS, Azure DNS, and others). In a multi-cluster setup, external-dns in each cluster creates DNS records for that cluster's services. When a cluster goes down, its external-dns stops updating, health checks fail, and traffic shifts to the remaining healthy clusters — all without any cross-cluster networking tool.

- The Multi-Cluster Services (MCS) API, defined in the `multicluster.x-k8s.io` API group, provides a vendor-neutral way for clusters to share Services through `ServiceExport` and `ServiceImport` resources. When a Service is exported, consuming clusters can reach it at `<name>.<namespace>.svc.clusterset.local` — a domain name that resolves to endpoints across all clusters that export that Service. This standard, originally proposed as KEP-1645, is implemented natively by Submariner and partially by other tools through their own mechanisms.

---

## Common Mistakes

| Mistake | Why It Happens | How to Fix It |
|---------|---------------|---------------|
| Using the same Pod CIDR on all clusters | Default kubeadm, kind, and many cloud-provider cluster templates use 10.244.0.0/16 or similar ranges | Plan unique, non-overlapping CIDRs before cluster creation; use Submariner Globalnet if clusters already exist with overlaps |
| Not testing failover before an incident | Teams assume failover works because they configured it, but configuration errors, firewall changes, and certificate expirations silently break failover paths | Schedule monthly failover drills; automate the DNS health check and weighted routing configuration; measure failover time as an SLO |
| Monitoring per-cluster metrics but not cross-cluster latency | Observability is typically scoped to a single cluster; the cross-cluster hop is invisible in dashboards and alerts | Deploy cross-cluster latency probes (blackbox exporter, mesh-native tracing) measuring the full path from source Pod to destination Service; alert on cross-cluster latency breaches |
| Opening all ports between clusters for expediency | Security teams are not involved in the initial connectivity setup; firewall rules are configured as "allow all" and never tightened | Whitelist only the specific ports required: TCP 2379 and TCP 4240 for Cilium, UDP 4500 and UDP 4490 for Submariner; document the port requirements |
| Using DNS TTL values inherited from general-purpose records | Teams copy the default TTL (often 300 seconds) from their DNS provider without considering the failover implications | Set TTL to 30 to 60 seconds for records used in multi-cluster failover; verify that the DNS provider supports health checks on those records |
| Not documenting cross-cluster service dependencies | Individual teams export services without coordination; the dependency graph across clusters is invisible | Maintain a central registry of exported services with ownership, SLO expectations, and contact information; make cross-cluster dependencies visible in service catalogs |
| Deploying cross-cluster connectivity without considering MTU | Tunnel encapsulation (IPsec, VXLAN, WireGuard) adds overhead that reduces the effective MTU, causing fragmentation and silent drops | Measure the path MTU between clusters before deploying applications; set tunnel or Pod network MTU appropriately (typically 1400 for VXLAN, 1380 for IPsec) |
| Assuming multi-cluster is always better than a single larger cluster | The complexity of multi-cluster networking is underestimated; teams deploy multiple clusters by default without evaluating whether a single cluster would suffice | Evaluate whether a single cluster can meet your requirements for blast-radius isolation, scaling, and regional proximity; only add clusters when the single-cluster approach hits a concrete limit |

---

## Quiz

<details>
<summary>1. What are the three multi-cluster networking models, and what drives the choice between them?</summary>

The three models are flat networking (routed Pod IPs with non-overlapping CIDRs), overlay networking (tunneled with address translation for overlapping CIDRs), and service-level connectivity (only explicitly exported Services are shared). The choice is driven by two primary constraints: whether you can allocate non-overlapping CIDRs across all clusters (flat wins if yes, overlay or service-level if no), and whether you need universal Pod-to-Pod reachability or can accept controlled, service-based connectivity (overlay for the former, service-level for the latter). Security posture also matters — service-level connectivity gives you the most control over what crosses the cluster boundary and is the right default for security-conscious environments.
</details>

<details>
<summary>2. How does Cilium ClusterMesh handle cross-cluster service discovery, and what role does the shared identity store play?</summary>

Cilium ClusterMesh uses a shared etcd-based API server that synchronizes endpoint information across all connected clusters. When a Service is annotated with `service.cilium.io/global: "true"`, its endpoints are published to the ClusterMesh API server. Every cluster watches this shared state, so Pods in any cluster resolve the standard DNS name and Cilium's eBPF dataplane selects an endpoint based on affinity configuration (`local` prefers same-cluster endpoints; remote endpoints serve as fallback). The identity store synchronizes numeric security identities derived from Pod labels and namespaces, which enables CiliumNetworkPolicies to reference identities from remote clusters and enforce policy consistently across the mesh. This is one of the few implementations that provides cross-cluster NetworkPolicy enforcement without a separate service mesh layer.
</details>

<details>
<summary>3. What problem does Submariner's Globalnet solve, and what is the operational cost of that solution?</summary>

Globalnet solves the overlapping Pod CIDR problem. When two clusters use the same Pod CIDR (a common situation because many distributions default to 10.244.0.0/16), direct Pod-to-Pod routing is impossible — the same IP could exist in both clusters. Globalnet assigns each cluster a unique global CIDR and performs double NAT on cross-cluster traffic: the source Pod IP is translated to a global IP on the sending side, the packet traverses the encrypted tunnel, and the destination global IP is translated back to the actual Pod IP on the receiving side. The operational cost is added latency — typically 1 to 3 milliseconds of processing delay from the double NAT, plus the tunnel encapsulation overhead. This is acceptable for most workloads but can breach SLOs for latency-sensitive applications that make multiple cross-cluster calls per transaction.
</details>

<details>
<summary>4. Why does DNS TTL matter for multi-cluster failover, and what TTL value should you choose?</summary>

DNS TTL determines how long clients and intermediate resolvers cache a DNS response. When a cluster fails and its DNS record is removed or deprioritized by the health-checking DNS provider, clients with cached responses continue sending traffic to the failed cluster until the TTL expires. A TTL of 300 seconds means up to 5 minutes of traffic directed at a dead cluster after the DNS update. A TTL of 30 seconds means at most 30 seconds of misdirected traffic. The trade-off is query volume and resolution latency: lower TTLs increase DNS query load and add a small per-request cost for initial resolutions. For services where fast failover matters, set TTL to 30 to 60 seconds. For services where a few minutes of downtime is tolerable, 300 seconds is acceptable. The right value is a function of your recovery time objective (RTO) for the service.
</details>

<details>
<summary>5. Scenario: You need to connect an on-premises Kubernetes cluster to an EKS cluster in AWS. Both clusters use 10.244.0.0/16 for Pods. What are your viable options, and what are the trade-offs between them?</summary>

Three viable options exist. First, Submariner with Globalnet — the fastest to deploy because it handles the CIDR overlap through NAT, but it adds latency from double NAT and tunnel encapsulation. Second, rebuild one cluster with non-overlapping CIDRs — the best long-term solution because it enables flat, low-latency networking, but it requires a blue-green migration or a maintenance window with downtime. Third, Skupper — operates at the application layer, so IP overlap is irrelevant, and it works behind restrictive firewalls, but performance is lower than network-layer approaches and it does not provide cross-cluster Pod routing or NetworkPolicy enforcement. For a production on-premises to cloud connection, the pragmatic sequence is Submariner Globalnet for immediate connectivity, with a plan to rebuild the on-premises cluster with unique CIDRs during the next hardware refresh cycle.
</details>

<details>
<summary>6. What firewall ports must be opened for Cilium ClusterMesh between two clusters, and why is each port needed?</summary>

Cilium ClusterMesh requires four categories of ports. TCP 2379 is the etcd client port used by the ClusterMesh API server to synchronize endpoint and identity state between clusters — this is the control-plane connection and must be reliable and low-latency. TCP 4240 is the Cilium health check port between nodes; it carries cluster health status and is used to determine whether remote nodes are reachable. For data-plane traffic, UDP 8472 carries VXLAN-encapsulated Pod-to-Pod traffic or UDP 51871 carries WireGuard-encrypted traffic, depending on the tunnel mode configured. TCP 4244 is for Hubble relay if you are using Hubble for cross-cluster observability. Additionally, if the ClusterMesh API server is exposed via NodePort, the assigned NodePort (typically 32379) must be reachable. Only open the ports your specific configuration uses — a Cilium deployment using WireGuard does not need the VXLAN port, and a deployment without Hubble does not need port 4244.
</details>

<details>
<summary>7. How does external-dns enable multi-cluster failover without any multi-cluster networking tool, and what are the limitations of this approach?</summary>

external-dns runs independently in each cluster, creating and updating DNS records for Services, Ingresses, and Gateway API resources. Each instance uses a unique `--txt-owner-id` so records from different clusters do not conflict. The DNS provider (Route53, Cloudflare, Google Cloud DNS) is configured with health checks for each cluster's endpoint and with weighted routing that distributes traffic across the healthy clusters. When a cluster fails its health check, the DNS provider removes its records from the rotation, and traffic shifts to the remaining clusters. This provides cluster-level failover with no cross-cluster networking component — each cluster is entirely independent. The limitation is scope: DNS-based failover only works for north-south traffic (external users hitting an Ingress or Gateway). East-west Pod-to-Pod traffic between clusters — service A in cluster A calling service B in cluster B — does not go through external DNS and requires a mesh or tunnel-based approach for failover.
</details>

<details>
<summary>8. What is the most consequential mistake in multi-cluster networking, and how do you prevent it?</summary>

The most consequential mistake is deploying clusters with overlapping CIDRs. Overlapping Pod CIDRs make direct cross-cluster Pod routing impossible and force you into overlay solutions that add latency, complexity, and operational burden. Changing a cluster's Pod CIDR after deployment is effectively a full rebuild — you must drain every node, reconfigure the CNI, and recreate every Pod. For a production cluster with hundreds of services, this is a multi-day operation with significant outage risk. Prevention is straightforward: allocate unique, non-overlapping /16 blocks from the 10.0.0.0/8 range for every cluster before creation, maintain a central CIDR registry, and reserve address space for future clusters. The cost of CIDR planning at the start is near zero; the cost of fixing an overlap retroactively is high and disruptive.
</details>

---

## Hands-On Exercises

### Exercise 1: Multi-Cluster with Cilium ClusterMesh (kind)

```bash
# Create two kind clusters
cat <<'EOF' > cluster-a.yaml
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
networking:
  disableDefaultCNI: true
  podSubnet: "10.1.0.0/16"
  serviceSubnet: "10.96.0.0/16"
nodes:
  - role: control-plane
  - role: worker
EOF

cat <<'EOF' > cluster-b.yaml
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
networking:
  disableDefaultCNI: true
  podSubnet: "10.2.0.0/16"
  serviceSubnet: "10.97.0.0/16"
nodes:
  - role: control-plane
  - role: worker
EOF

kind create cluster --name cluster-a --config cluster-a.yaml
kind create cluster --name cluster-b --config cluster-b.yaml
```

**Task 1**: Install Cilium on both clusters with unique cluster IDs so that each cluster has a distinct numeric identity in the mesh.

```bash
# Cluster A
cilium install --context kind-cluster-a --cluster-name cluster-a --cluster-id 1 \
  --set cluster.name=cluster-a --set cluster.id=1

# Cluster B
cilium install --context kind-cluster-b --cluster-name cluster-b --cluster-id 2 \
  --set cluster.name=cluster-b --set cluster.id=2

# Wait for ready
cilium status --context kind-cluster-a --wait
cilium status --context kind-cluster-b --wait
```

**Task 2**: Enable ClusterMesh on both clusters and establish the cross-cluster connection between them.

```bash
cilium clustermesh enable --context kind-cluster-a --service-type NodePort
cilium clustermesh enable --context kind-cluster-b --service-type NodePort

cilium clustermesh status --context kind-cluster-a --wait
cilium clustermesh status --context kind-cluster-b --wait

cilium clustermesh connect --context kind-cluster-a --destination-context kind-cluster-b
```

**Task 3**: Deploy a global service in Cluster B, annotate it for cross-cluster sharing, and verify that it is reachable from Cluster A.

```bash
# Deploy service in Cluster B
kubectl --context kind-cluster-b create namespace shared
kubectl --context kind-cluster-b run echo-server -n shared \
  --image=hashicorp/http-echo:1.0 -- -listen=:8080 -text="from-cluster-b"
kubectl --context kind-cluster-b expose pod echo-server -n shared --port=8080

# Annotate as global
kubectl --context kind-cluster-b annotate service echo-server -n shared \
  service.cilium.io/global="true"

# Create matching namespace in Cluster A
kubectl --context kind-cluster-a create namespace shared

# Test from Cluster A
kubectl --context kind-cluster-a run test -n shared --rm -it --restart=Never \
  --image=busybox:1.36 -- wget -qO- http://echo-server.shared.svc.cluster.local:8080
# Expected: "from-cluster-b"
```

### Exercise 2: DNS-Based Failover Simulation

```bash
# Deploy the same service in BOTH clusters
kubectl --context kind-cluster-a create namespace app
kubectl --context kind-cluster-a run web -n app --image=hashicorp/http-echo:1.0 \
  -- -listen=:8080 -text="cluster-a"
kubectl --context kind-cluster-a expose pod web -n app --port=8080

kubectl --context kind-cluster-b create namespace app
kubectl --context kind-cluster-b run web -n app --image=hashicorp/http-echo:1.0 \
  -- -listen=:8080 -text="cluster-b"
kubectl --context kind-cluster-b expose pod web -n app --port=8080

# Annotate both as global with local affinity
for CTX in kind-cluster-a kind-cluster-b; do
  kubectl --context $CTX annotate service web -n app \
    service.cilium.io/global="true" \
    service.cilium.io/affinity="local"
done
```

**Task**: Simulate a failure in Cluster A by deleting the local Pod and verify that traffic automatically fails over to the healthy instance in Cluster B.

```bash
# From Cluster A, traffic goes to local first
kubectl --context kind-cluster-a run test -n app --rm -it --restart=Never \
  --image=busybox:1.36 -- wget -qO- http://web.app.svc.cluster.local:8080
# Expected: "cluster-a" (local affinity)

# Delete the local Pod to simulate failure
kubectl --context kind-cluster-a delete pod web -n app

# Test again — should fail over to Cluster B
kubectl --context kind-cluster-a run test2 -n app --rm -it --restart=Never \
  --image=busybox:1.36 -- wget -qO- http://web.app.svc.cluster.local:8080
# Expected: "cluster-b" (failover)
```

### Exercise 3: Cross-Cluster Troubleshooting

**Task**: Intentionally break cross-cluster connectivity by removing the global service annotation, then use the diagnostic tools to identify and repair the break.

```bash
# Break connectivity by removing the ClusterMesh annotation
kubectl --context kind-cluster-b annotate service echo-server -n shared \
  service.cilium.io/global-

# From Cluster A, try to reach the service
kubectl --context kind-cluster-a run test -n shared --rm -it --restart=Never \
  --image=busybox:1.36 -- wget --timeout=3 -qO- http://echo-server.shared.svc.cluster.local:8080
# Expected: timeout (no local endpoint, global annotation removed)

# Diagnose
cilium clustermesh status --context kind-cluster-a
kubectl --context kind-cluster-a get endpoints echo-server -n shared
# Shows: no endpoints (service not global anymore)

# Fix: re-add annotation
kubectl --context kind-cluster-b annotate service echo-server -n shared \
  service.cilium.io/global="true"
```

**Success Criteria** — verify that all of the following conditions are met before considering the exercise complete:
- [ ] Two kind clusters running with Cilium and ClusterMesh connected
- [ ] Global service accessible from both clusters
- [ ] Local affinity routing verified (traffic prefers local cluster)
- [ ] Failover tested by deleting local Pod and verifying traffic shifts to remote cluster
- [ ] Cross-cluster connectivity intentionally broken, diagnosed, and repaired

---

## Hypothetical Scenario: The CIDR Collision That Nobody Saw Coming

A company running Kubernetes acquires another company that also runs Kubernetes. Both organizations independently chose the default Pod CIDR — 10.244.0.0/16 — and the default Service CIDR — 10.96.0.0/12. The integration plan calls for connecting the two Kubernetes environments within roughly 90 days so that applications can be gradually migrated and services can interoperate during the transition.

The networking team discovers the CIDR overlap in the first week. Every Pod IP in one cluster could conflict with a Pod IP in the other. Direct Pod-to-Pod routing is impossible. The team evaluates two paths forward.

Path A is to rebuild one cluster with new, non-overlapping CIDRs. This would require draining every node, reconfiguring the CNI, recreating every Pod, and re-verifying every application. The estimated engineering effort is in the hundreds of person-hours, with a multi-day maintenance window and significant risk of application issues during the cutover.

Path B is Submariner with Globalnet. Each cluster gets a unique global CIDR (for example, 242.0.0.0/16 and 243.0.0.0/16 from a private range). Cross-cluster service traffic is NATed through these global IPs, and the encrypted tunnels carry traffic between the clusters' gateway nodes. Deployment takes days, not weeks, and requires no changes to existing workloads.

The team chooses Path B for immediate connectivity and begins planning Path A for the long term. The Globalnet deployment works, but integration testing reveals that the double NAT adds roughly 2 to 3 milliseconds of latency per cross-cluster request. A payments service that makes six cross-cluster calls per transaction sees roughly 12 to 18 milliseconds of added latency — enough to push transaction times near the edge of the service's SLO. The team tunes timeouts and connection pooling to absorb the overhead, but the lesson is clear.

**Lesson**: CIDR allocation is a foundational decision that is extremely expensive to change retroactively. Plan CIDRs across all clusters before the first cluster is created, maintain a central registry, and reserve address space for future expansion. If you inherit overlapping CIDRs through acquisition or organic growth, Submariner Globalnet provides a fast path to connectivity, but accept that you are buying time, not solving the root cause. Budget for a clean CIDR migration during the next major infrastructure refresh.

---

## Sources

- [Cilium ClusterMesh Documentation](https://docs.cilium.io/en/stable/network/clustermesh/clustermesh/)
- [Submariner Project](https://submariner.io/)
- [Submariner Globalnet Architecture](https://submariner.io/getting-started/architecture/globalnet/)
- [Istio Multi-Cluster Deployment](https://istio.io/latest/docs/setup/install/multicluster/)
- [Istio Deployment Models](https://istio.io/latest/docs/ops/deployment/deployment-models/)
- [Linkerd Multi-Cluster Communication](https://linkerd.io/2/tasks/multicluster/)
- [Kubernetes Multi-Cluster Services API (SIG-Multicluster)](https://github.com/kubernetes-sigs/mcs-api)
- [KEP-1645: Multi-Cluster Services API](https://github.com/kubernetes/enhancements/tree/master/keps/sig-multicluster/1645-multi-cluster-services-api)
- [Kubernetes Topology-Aware Routing](https://kubernetes.io/docs/concepts/services-networking/topology-aware-routing/)
- [SPIFFE Concepts](https://spiffe.io/docs/latest/spiffe-about/spiffe-concepts/)
- [SPIFFE Project](https://github.com/spiffe/spiffe)
- [Kubernetes external-dns](https://github.com/kubernetes-sigs/external-dns)
- [CNCF Cilium Project](https://www.cncf.io/projects/cilium/)
- [CNCF Submariner Project](https://www.cncf.io/projects/submariner/)
- [AWS VPC Peering](https://docs.aws.amazon.com/vpc/latest/peering/what-is-vpc-peering.html)
- [GKE Multi-Cluster Services](https://cloud.google.com/kubernetes-engine/docs/concepts/multi-cluster-services)

---

## Summary

Multi-cluster and hybrid networking extends Kubernetes beyond a single cluster boundary. The key decisions are:

1. **Articulate why you need multiple clusters** — blast-radius isolation, regional proximity, regulatory boundaries, scale, or migration — because the driver determines the networking requirement.
2. **Choose your connectivity model** — flat networking for performance and simplicity when CIDRs are clean, overlay for flexibility when they are not, service-level for explicit control and security.
3. **Plan CIDRs first** — non-overlapping ranges across all clusters. This is the most consequential networking decision you will make, and it is vastly cheaper to get right at the start than to fix later.
4. **Match the tool to the requirement** — Cilium ClusterMesh for Cilium-managed clusters, Submariner for CNI-agnostic clusters or CIDR-overlap situations, Istio or Linkerd multi-cluster when you already run those meshes, Skupper for hybrid Kubernetes and non-Kubernetes workloads.
5. **Build cross-cluster identity** — shared trust roots and federated identity enable mTLS, authorization policies, and audit trails that span cluster boundaries.
6. **DNS and health checks are your simplest failover mechanism** — external-dns with health checks handles cluster-level failover for external traffic without any cross-cluster networking tool.
7. **Test failover regularly** — having two clusters is not high availability until you have measured and validated that traffic shifts correctly when one cluster fails.

Multi-cluster networking is hard because it spans every networking layer — DNS, routing, encryption, identity, service discovery, and traffic policy — and because failures at any one of those layers can silently break cross-cluster communication. But it is essential for any organization running Kubernetes across regions, across clouds, or at a scale that exceeds a single cluster's practical limits.

---

## Next Module

This module completes the Kubernetes Networking discipline. You now have a comprehensive understanding of how traffic flows into, within, and between Kubernetes clusters — from CNI fundamentals through Ingress and Gateway API, service mesh strategy, and multi-cluster networking.

**Recommended next tracks:**

- [SRE Discipline](/platform/disciplines/core-platform/sre/) — Apply networking knowledge to reliability engineering: error budgets, SLOs, and incident response for distributed systems
- [DevSecOps Discipline](/platform/disciplines/reliability-security/devsecops/) — Secure the networking layer in CI/CD pipelines: policy as code, network security scanning, and zero-trust deployment
- [Networking Toolkit](/platform/toolkits/infrastructure-networking/networking/) — Deep dive into specific mesh implementations, CNI performance tuning, and advanced networking tooling
