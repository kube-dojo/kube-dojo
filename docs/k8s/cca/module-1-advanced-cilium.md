# Module 1: Advanced Cilium for CCA

> **CCA Track** | Complexity: `[COMPLEX]` | Time: 75-90 minutes

## Prerequisites

- [Cilium Toolkit Module](../../platform/toolkits/networking/module-5.1-cilium.md) -- eBPF fundamentals, basic Cilium architecture, identity-based security
- [Hubble Toolkit Module](../../platform/toolkits/observability/module-1.7-hubble.md) -- Hubble CLI, flow observation
- Kubernetes networking basics (Services, Pods, DNS)
- Comfort with `kubectl` and YAML

---

## Why This Module Matters

The Cilium Toolkit module taught you *what* Cilium does. This module teaches you *how it works at the level the CCA exam expects*.

Here is the difference. A junior engineer knows "Cilium uses eBPF for networking." A CCA-certified engineer knows that the Cilium agent on each node compiles endpoint-specific eBPF programs, attaches them to the TC (traffic control) hook on each pod's veth pair, and uses eBPF maps shared across programs to enforce identity-aware policy decisions in O(1) time -- without a single iptables rule.

That depth is what separates passing from failing. This module fills every gap between our existing content and what the CCA demands: architecture internals, policy enforcement modes, Cluster Mesh, BGP peering, and the Cilium CLI workflows you need to know cold.

---

## Did You Know?

- **Cilium assigns identities using a cluster-wide numeric allocator.** Every unique set of security-relevant labels gets exactly one identity number. If 500 pods share the same labels, they all share one identity. This is why Cilium scales to tens of thousands of pods without policy rule explosion -- the number of identities stays small.

- **Cluster Mesh doesn't require a VPN or overlay between clusters.** It uses standard TLS connections between Cilium agents and a shared etcd (or kvstore) to synchronize identities and service endpoints. As long as the clusters can reach each other's API endpoints, Cluster Mesh works -- even across cloud providers.

- **CiliumBGPPeeringPolicy was introduced in Cilium 1.12, replacing the older MetalLB integration.** It's a native, first-class BGP speaker built into the Cilium agent. No separate BGP daemon needed. One CRD, and your cluster advertises pod CIDRs or LoadBalancer VIPs to your network infrastructure.

- **The Cilium agent compiles a unique eBPF program per endpoint.** When a pod is created, the agent generates a tailored eBPF program that encodes the policies applicable to that specific pod. This means policy evaluation isn't a generic rule walk -- it's a pre-compiled, per-pod decision tree. That's why policy enforcement adds near-zero latency.

---

## Part 1: Cilium Architecture in Depth

The Toolkit module showed you the big picture. Now let's open each box.

### The Cilium Agent (DaemonSet)

The agent is the workhorse. One runs on every node.

```
CILIUM AGENT INTERNALS
================================================================

                    Kubernetes API Server
                           |
                    watches: Pods, Services,
                    Endpoints, NetworkPolicies,
                    CiliumNetworkPolicies, Nodes
                           |
                    ┌──────▼──────────────────────────────┐
                    │         CILIUM AGENT                  │
                    │                                       │
                    │  ┌─────────────┐  ┌───────────────┐  │
                    │  │  K8s Watcher │  │  Policy Engine│  │
                    │  │  (informers) │─▶│  (rule graph) │  │
                    │  └─────────────┘  └───────┬───────┘  │
                    │                           │          │
                    │  ┌─────────────┐  ┌───────▼───────┐  │
                    │  │  Identity   │  │  eBPF Compiler│  │
                    │  │  Allocator  │  │  & Map Writer │  │
                    │  └──────┬──────┘  └───────┬───────┘  │
                    │         │                 │          │
                    │  ┌──────▼─────────────────▼───────┐  │
                    │  │         eBPF DATAPLANE          │  │
                    │  │  ┌─────┐ ┌──────┐ ┌──────────┐ │  │
                    │  │  │ TC  │ │ XDP  │ │ Socket   │ │  │
                    │  │  │hooks│ │hooks │ │ hooks    │ │  │
                    │  │  └─────┘ └──────┘ └──────────┘ │  │
                    │  └────────────────────────────────┘  │
                    │                                       │
                    │  ┌────────────────────────────────┐  │
                    │  │      HUBBLE OBSERVER            │  │
                    │  │  (reads eBPF perf ring buffer)  │  │
                    │  └────────────────────────────────┘  │
                    └──────────────────────────────────────┘
```

**What each sub-component does:**

| Component | Role | Why It Matters |
|-----------|------|----------------|
| K8s Watcher | Receives events from API server via informers | Detects pod creation, policy changes, service updates |
| Identity Allocator | Maps label sets to numeric identities | Enables O(1) policy lookups instead of label matching |
| Policy Engine | Builds a rule graph from all applicable policies | Determines allowed (src identity, dst identity, port, L7) tuples |
| eBPF Compiler | Generates per-endpoint eBPF programs | Tailored programs = faster enforcement, no generic rule walk |
| eBPF Maps | Shared kernel data structures (hash maps, LPM tries) | Policy decisions, connection tracking, NAT, service lookup |
| Hubble Observer | Reads the perf event ring buffer from eBPF programs | Every forwarded/dropped packet becomes a flow event |

### The Cilium Operator (Deployment)

The operator handles cluster-wide coordination. There is **one active instance** per cluster (with leader election for HA).

```
CILIUM OPERATOR RESPONSIBILITIES
================================================================

1. IPAM (IP Address Management)
   - Allocates pod CIDR ranges to nodes
   - In "cluster-pool" mode: carves /24 blocks from a larger pool
   - In AWS ENI mode: manages ENI attachment and IP allocation

2. CRD Management
   - Ensures CiliumIdentity, CiliumEndpoint, CiliumNode CRDs exist
   - Garbage-collects stale CiliumIdentity objects

3. Cluster Mesh
   - Manages the clustermesh-apiserver deployment
   - Synchronizes identities across clusters

4. Resource Cleanup
   - Removes orphaned CiliumEndpoints when pods are deleted
   - Cleans up leaked IPs from terminated nodes
```

**Key exam point**: The operator does NOT enforce policies or program eBPF. If the operator goes down, existing networking continues to work. New pod CIDR allocations will fail, and identity garbage collection pauses, but traffic keeps flowing. This is a common exam question.

### IPAM Modes

Cilium supports multiple IPAM strategies. The CCA expects you to know when to use each.

| IPAM Mode | How It Works | When to Use |
|-----------|-------------|-------------|
| `cluster-pool` (default) | Operator allocates /24 CIDRs from a configurable pool to each node. Agent assigns IPs from its node's pool. | Most clusters. Simple, works everywhere. |
| `kubernetes` | Delegates to the Kubernetes `--pod-cidr` allocation (node.spec.podCIDR). | When you want K8s to control CIDR allocation. |
| `multi-pool` | Multiple named pools with different CIDRs. Pods select pool via annotation. | Multi-tenant clusters needing separate IP ranges. |
| `eni` (AWS) | Allocates IPs directly from AWS ENI secondary addresses. Pods get VPC-routable IPs. | AWS EKS. No overlay needed. Native VPC routing. |
| `azure` | Allocates from Azure VNET. Similar to ENI mode for Azure. | AKS clusters. |
| `crd` | External IPAM controller manages CiliumNode CRDs. | Custom IPAM integrations. |

```bash
# Check which IPAM mode your cluster uses
cilium config view | grep ipam

# In cluster-pool mode, see the allocated ranges
kubectl get ciliumnodes -o jsonpath='{range .items[*]}{.metadata.name}: {.spec.ipam.podCIDRs}{"\n"}{end}'
```

---

## Part 2: CiliumNetworkPolicy vs Kubernetes NetworkPolicy

The CCA exam tests this comparison heavily. You need to know exactly what Cilium adds.

### Feature Comparison

| Feature | K8s NetworkPolicy | CiliumNetworkPolicy |
|---------|-------------------|---------------------|
| L3/L4 filtering (IP + port) | Yes | Yes |
| Label-based pod selection | Yes | Yes (+ identity-based) |
| Namespace selection | Yes | Yes |
| **L7 HTTP filtering** (method, path, headers) | No | Yes |
| **L7 Kafka filtering** (topic, role) | No | Yes |
| **L7 DNS filtering** (FQDN) | No | Yes |
| **Entity-based rules** (host, world, dns, kube-apiserver) | No | Yes |
| **Cluster-wide scope** | No | Yes (CiliumClusterwideNetworkPolicy) |
| **CIDR-based egress with FQDN** | No | Yes (toFQDNs) |
| **Policy enforcement mode control** | No | Yes (default/always/never) |
| **Identity-aware enforcement** | No | Yes (eBPF identity lookup) |
| **Deny rules** | No (allow-only model) | Yes (explicit deny) |

### L7 HTTP-Aware Policies

This is one of Cilium's most powerful features. Standard Kubernetes NetworkPolicies work at L3/L4 -- they can allow or deny traffic based on IP and port. Cilium goes further.

```yaml
# L7 HTTP policy: allow only specific API calls
apiVersion: cilium.io/v2
kind: CiliumNetworkPolicy
metadata:
  name: api-l7-policy
  namespace: production
spec:
  endpointSelector:
    matchLabels:
      app: api-server
  ingress:
  - fromEndpoints:
    - matchLabels:
        app: frontend
    toPorts:
    - ports:
      - port: "8080"
        protocol: TCP
      rules:
        http:
        # Allow reading products
        - method: "GET"
          path: "/api/v1/products"
        # Allow reading a specific product by ID
        - method: "GET"
          path: "/api/v1/products/[0-9]+"
        # Allow creating orders with JSON
        - method: "POST"
          path: "/api/v1/orders"
          headers:
          - 'Content-Type: application/json'
        # Everything else: DENIED
```

**What this means in practice**: Even if an attacker compromises the frontend pod, they cannot:
- Send DELETE requests to any endpoint
- Access `/api/v1/admin` or any path not explicitly listed
- POST to arbitrary endpoints
- Send non-JSON payloads to the orders endpoint

The network itself enforces your API contract. This is defense in depth at the infrastructure layer.

### Policy Enforcement Modes

Cilium has three policy enforcement modes that control behavior when no policy matches.

```
POLICY ENFORCEMENT MODES
================================================================

MODE: "default" (the default)
─────────────────────────────
- If NO policies select an endpoint: all traffic allowed
- If ANY policy selects an endpoint: only explicitly allowed traffic passes
- This is how standard K8s NetworkPolicy works
- Think: "policies are opt-in"

MODE: "always"
─────────────────────────────
- ALL traffic is denied unless explicitly allowed by policy
- Even endpoints with no policies get default-deny
- Think: "zero-trust by default"
- Use this in production for maximum security

MODE: "never"
─────────────────────────────
- Policy enforcement is completely disabled
- All traffic flows freely regardless of policies
- Think: "debugging mode"
- NEVER use in production. Useful for ruling out policy
  issues during troubleshooting.
```

```bash
# Check the current enforcement mode
cilium config view | grep policy-enforcement

# Change enforcement mode (requires Helm upgrade or config change)
# Via Helm:
cilium upgrade --set policyEnforcementMode=always

# Via cilium config (runtime, non-persistent):
cilium config PolicyEnforcement=always
```

**Exam tip**: Know that "default" mode means traffic is allowed when no policies exist for an endpoint. Once you apply even one policy to an endpoint, it switches to deny-by-default for that endpoint's direction (ingress or egress).

### Entity-Based Rules

Cilium defines semantic entities that represent well-known traffic sources/destinations. These eliminate the need to track IP addresses for infrastructure services.

```yaml
# Allow pods to reach essential infrastructure
apiVersion: cilium.io/v2
kind: CiliumClusterwideNetworkPolicy
metadata:
  name: allow-infrastructure
spec:
  endpointSelector: {}
  egress:
  - toEntities:
    - dns             # CoreDNS / kube-dns
    - kube-apiserver  # Kubernetes API server
  ingress:
  - fromEntities:
    - health          # Kubelet health probes
```

Available entities:

| Entity | Meaning |
|--------|---------|
| `host` | The node the pod runs on |
| `remote-node` | Other cluster nodes |
| `kube-apiserver` | The Kubernetes API server (regardless of IP) |
| `health` | Cilium health check probes |
| `dns` | DNS servers (kube-dns/CoreDNS) |
| `world` | Anything outside the cluster |
| `all` | Everything (use with caution) |

---

## Part 3: Cluster Mesh -- Multi-Cluster Connectivity

Cluster Mesh is how Cilium connects multiple Kubernetes clusters. It enables cross-cluster service discovery, global services, and unified policy enforcement -- without VPNs or overlay networks.

### When You Need Cluster Mesh

- **High availability**: Services span clusters in different regions/AZs
- **Migration**: Gradual workload migration between clusters
- **Separation of concerns**: Different teams own different clusters but services need to communicate
- **Compliance**: Data locality requirements (EU data stays in EU cluster) with cross-region coordination

### Architecture

```
CLUSTER MESH ARCHITECTURE
================================================================

    Cluster A (us-east-1)              Cluster B (eu-west-1)
    ┌──────────────────────┐          ┌──────────────────────┐
    │  ┌────────────────┐  │          │  ┌────────────────┐  │
    │  │ Cilium Agents  │  │          │  │ Cilium Agents  │  │
    │  └───────┬────────┘  │          │  └───────┬────────┘  │
    │          │           │          │          │           │
    │  ┌───────▼────────┐  │   TLS    │  ┌───────▼────────┐  │
    │  │  ClusterMesh   │◄─┼──────────┼─▶│  ClusterMesh   │  │
    │  │  API Server    │  │          │  │  API Server    │  │
    │  │  (etcd-backed) │  │          │  │  (etcd-backed) │  │
    │  └────────────────┘  │          │  └────────────────┘  │
    │                      │          │                      │
    │  Pods:               │          │  Pods:               │
    │  ┌────────┐          │          │  ┌────────┐          │
    │  │frontend│ ─────────┼─── cross-cluster ────▶│ backend│  │
    │  │(id:100)│          │          │  │(id:200)│          │
    │  └────────┘          │          │  └────────┘          │
    └──────────────────────┘          └──────────────────────┘

    Shared: CA certificate, identity allocation range
    Required: Pod CIDRs must NOT overlap between clusters
    Network: Clusters must have IP connectivity (direct or via LB)
```

### Requirements

| Requirement | Why |
|-------------|-----|
| Shared CA certificate | Agents authenticate to remote ClusterMesh API servers via mTLS |
| Non-overlapping pod CIDRs | Packets must be routable; overlapping CIDRs cause ambiguity |
| Network connectivity | Agents must reach remote ClusterMesh API server (port 2379 by default) |
| Unique cluster names | Each cluster needs a distinct name and numeric ID (1-255) |
| Compatible Cilium versions | Minor version skew is tolerated; major version must match |

### Enabling Cluster Mesh

```bash
# Step 1: Enable Cluster Mesh on each cluster
# On Cluster A:
cilium clustermesh enable --context kind-cluster-a --service-type LoadBalancer

# On Cluster B:
cilium clustermesh enable --context kind-cluster-b --service-type LoadBalancer

# Step 2: Connect the clusters
cilium clustermesh connect \
  --context kind-cluster-a \
  --destination-context kind-cluster-b

# Step 3: Wait for readiness
cilium clustermesh status --context kind-cluster-a --wait

# Step 4: Verify connectivity
cilium connectivity test --context kind-cluster-a --multi-cluster
```

### Global Services

Once Cluster Mesh is connected, you can create services that span clusters.

```yaml
# A service in Cluster A that is discoverable from Cluster B
apiVersion: v1
kind: Service
metadata:
  name: payment-service
  namespace: production
  annotations:
    # This annotation makes the service global
    service.cilium.io/global: "true"
spec:
  selector:
    app: payment
  ports:
  - port: 443
```

When a pod in Cluster B resolves `payment-service.production.svc.cluster.local`, Cilium returns endpoints from BOTH clusters. Traffic is load-balanced across all available backends.

### Service Affinity

You can control where traffic prefers to go:

```yaml
apiVersion: v1
kind: Service
metadata:
  name: payment-service
  annotations:
    service.cilium.io/global: "true"
    # Prefer local cluster, fall back to remote
    service.cilium.io/affinity: "local"
spec:
  selector:
    app: payment
  ports:
  - port: 443
```

| Affinity | Behavior |
|----------|----------|
| `local` | Prefer local cluster endpoints. Use remote only if local has none. |
| `remote` | Prefer remote cluster endpoints. Use local only if remote has none. |
| `none` (default) | Load-balance equally across all clusters. |

**Exam tip**: `local` affinity is the most common production choice. It minimizes latency while providing cross-cluster failover.

---

## Part 4: BGP with Cilium

### Why BGP in Kubernetes?

By default, pod IPs are only routable within the cluster. External networks (corporate LAN, internet) cannot reach pod IPs directly. You typically use LoadBalancer services or Ingress to expose workloads.

BGP (Border Gateway Protocol) changes this. Cilium can advertise pod CIDRs and service IPs to external routers, making them directly routable.

```
WITHOUT BGP
================================================================

External Client ──▶ LoadBalancer VIP ──▶ NodePort ──▶ Pod
                         │
                    Extra hop, SNAT,
                    source IP lost

WITH BGP (Cilium)
================================================================

External Client ──▶ Router ──▶ Pod (direct)
                      │
                 BGP learned route:
                 "10.244.1.0/24 via Node-1"
                 "10.244.2.0/24 via Node-2"
```

### CiliumBGPPeeringPolicy

This is the CRD that configures BGP peering on Cilium nodes.

```yaml
# Configure BGP peering with a ToR (Top-of-Rack) router
apiVersion: cilium.io/v2alpha1
kind: CiliumBGPPeeringPolicy
metadata:
  name: rack-1-bgp
spec:
  # Which nodes this policy applies to
  nodeSelector:
    matchLabels:
      rack: rack-1
  virtualRouters:
  - localASN: 65001          # Your cluster's ASN
    exportPodCIDR: true       # Advertise pod CIDRs to peers
    neighbors:
    - peerAddress: "10.0.0.1/32"  # ToR router IP
      peerASN: 65000               # Router's ASN
      # Optional: authentication
      # authSecretRef: bgp-auth-secret
    serviceSelector:
      # Advertise LoadBalancer service VIPs
      matchExpressions:
      - key: service.cilium.io/bgp-announce
        operator: In
        values: ["true"]
```

**What this does:**

1. Nodes labeled `rack: rack-1` establish BGP sessions with the router at 10.0.0.1
2. They advertise their pod CIDR ranges (e.g., "10.244.1.0/24 is reachable via me")
3. They advertise LoadBalancer VIPs for services with the `bgp-announce` annotation
4. External routers learn these routes and can send traffic directly to the correct node

### BGP Concepts for the CCA

| Concept | Meaning |
|---------|---------|
| ASN (Autonomous System Number) | A unique identifier for a BGP-speaking network. Private range: 64512-65534. |
| Peering | Two BGP speakers establishing a session to exchange routes. |
| Route Advertisement | Announcing "I can reach this IP range" to peers. |
| eBGP | External BGP -- peering between different ASNs (cluster to external router). |
| iBGP | Internal BGP -- peering within the same ASN (less common in Cilium). |
| `exportPodCIDR` | Tell peers how to reach pods on this node. |

```bash
# Check BGP peering status
cilium bgp peers

# Expected output:
# Node       Local AS   Peer AS   Peer Address   State        Since
# worker-1   65001      65000     10.0.0.1       established  2h15m
# worker-2   65001      65000     10.0.0.1       established  2h15m

# Check advertised routes
cilium bgp routes advertised ipv4 unicast
```

---

## Part 5: Gateway API, Bandwidth Manager, Egress Gateway, and L2 Announcements

These four features extend Cilium beyond basic CNI duties. The CCA expects you to know the CRDs and when to use each.

### Cilium Gateway API

Cilium natively implements the Kubernetes Gateway API, replacing the need for a separate ingress controller. It uses Envoy under the hood, managed entirely by the Cilium agent.

```yaml
# Gateway: the listener that accepts traffic
apiVersion: gateway.networking.k8s.io/v1
kind: Gateway
metadata:
  name: cilium-gw
  namespace: production
spec:
  gatewayClassName: cilium    # Cilium's built-in GatewayClass
  listeners:
  - name: http
    protocol: HTTP
    port: 80
    allowedRoutes:
      namespaces:
        from: Same
---
# HTTPRoute: route HTTP traffic to backends
apiVersion: gateway.networking.k8s.io/v1
kind: HTTPRoute
metadata:
  name: app-routes
  namespace: production
spec:
  parentRefs:
  - name: cilium-gw
  rules:
  - matches:
    - path:
        type: PathPrefix
        value: /api
    backendRefs:
    - name: api-service
      port: 8080
  - matches:
    - path:
        type: PathPrefix
        value: /
    backendRefs:
    - name: frontend-service
      port: 3000
---
# GRPCRoute: route gRPC traffic to backends
apiVersion: gateway.networking.k8s.io/v1
kind: GRPCRoute
metadata:
  name: grpc-routes
  namespace: production
spec:
  parentRefs:
  - name: cilium-gw
  rules:
  - matches:
    - method:
        service: payments.PaymentService
    backendRefs:
    - name: payment-grpc
      port: 9090
```

**Why this matters**: Gateway API is the successor to Ingress. Cilium's implementation means no separate NGINX or Envoy Gateway deployment -- the same agent that enforces network policy also handles north-south traffic routing.

### Bandwidth Manager

CiliumBandwidthPolicy lets you enforce rate limits on pod traffic using the eBPF EDT (Earliest Departure Time) scheduler. This replaces the old `kubernetes.io/egress-bandwidth` annotation approach with a cluster-wide CRD.

```yaml
apiVersion: cilium.io/v2
kind: CiliumBandwidthPolicy
metadata:
  name: rate-limit-batch-jobs
spec:
  endpointSelector:
    matchLabels:
      workload-type: batch
  egress:
    rate: "50M"     # 50 Mbit/s egress cap
    burst: "10M"    # Allow short bursts up to 10 Mbit above rate
```

**Use cases**: Prevent batch jobs or log shippers from saturating node bandwidth and starving latency-sensitive services. The eBPF-based approach is more efficient than traditional Linux `tc` shaping because it avoids queuing overhead -- packets are scheduled with precise departure timestamps.

### Egress Gateway

CiliumEgressGatewayPolicy routes outbound traffic from selected pods through dedicated gateway nodes. External services see a predictable source IP (the gateway node's IP) instead of whichever node the pod happens to run on.

```yaml
apiVersion: cilium.io/v2
kind: CiliumEgressGatewayPolicy
metadata:
  name: db-egress-via-gateway
spec:
  selectors:
  - podSelector:
      matchLabels:
        app: backend
        needs-stable-ip: "true"
  destinationCIDRs:
  - "10.200.0.0/16"       # External database subnet
  egressGateway:
    nodeSelector:
      matchLabels:
        role: egress-gateway   # Dedicated gateway nodes
    egressIP: "192.168.1.50"   # Stable SNAT IP
```

**Why you need this**: Many external firewalls, databases, and SaaS APIs allowlist traffic by source IP. Without an egress gateway, pod traffic exits from whatever node the pod runs on, and the source IP changes if the pod gets rescheduled. The egress gateway ensures a stable, predictable source IP regardless of pod placement.

### CiliumL2AnnouncementPolicy

CiliumL2AnnouncementPolicy provides Layer 2 service announcement for LoadBalancer-type services -- similar to MetalLB's L2 mode but built natively into Cilium. One node responds to ARP requests for the service VIP, attracting traffic to itself and then forwarding it to the correct backend.

```yaml
apiVersion: cilium.io/v2alpha1
kind: CiliumL2AnnouncementPolicy
metadata:
  name: l2-services
spec:
  serviceSelector:
    matchLabels:
      l2-announce: "true"
  nodeSelector:
    matchLabels:
      node.kubernetes.io/role: worker
  interfaces:
  - eth0
  externalIPs: true
  loadBalancerIPs: true
---
# A service that uses L2 announcement
apiVersion: v1
kind: Service
metadata:
  name: web
  labels:
    l2-announce: "true"
spec:
  type: LoadBalancer
  selector:
    app: web
  ports:
  - port: 80
    targetPort: 8080
```

**When to use**: Bare-metal clusters without a cloud load balancer. CiliumL2AnnouncementPolicy eliminates the need for a separate MetalLB deployment. One node becomes the "leader" for each VIP and answers ARP queries. If that node fails, another takes over. The limitation is the same as any L2 approach: all traffic for a VIP funnels through a single node, so it does not scale horizontally for high-bandwidth services. For that, use BGP.

---

## Part 6: Cilium CLI Deep Dive

The CCA tests your knowledge of Cilium CLI commands. Here's what you need to know.

### Installation and Status

```bash
# Install Cilium (most common invocation)
cilium install \
  --set kubeProxyReplacement=true \
  --set hubble.enabled=true \
  --set hubble.relay.enabled=true \
  --set hubble.ui.enabled=true

# Check status (the first command you run after install)
cilium status
# Shows: agent, operator, relay status + features enabled

# Wait for all components to be ready
cilium status --wait

# View full Cilium configuration
cilium config view

# View specific config value
cilium config view | grep policy-enforcement
```

### Connectivity Testing

```bash
# Run the full connectivity test suite
cilium connectivity test

# What it does:
# - Deploys test client and server pods
# - Tests pod-to-pod (same node and cross-node)
# - Tests pod-to-Service (ClusterIP and NodePort)
# - Tests pod-to-external
# - Tests NetworkPolicy enforcement
# - Tests DNS resolution
# - Tests Hubble flow visibility
# - Cleans up test resources when done

# Run specific tests only
cilium connectivity test --test pod-to-pod
cilium connectivity test --test pod-to-service

# Run with extra logging for debugging
cilium connectivity test --debug
```

### Endpoint and Identity Management

```bash
# List all Cilium-managed endpoints on this node
kubectl exec -n kube-system ds/cilium -- cilium endpoint list

# Get details on a specific endpoint
kubectl exec -n kube-system ds/cilium -- cilium endpoint get <endpoint-id>

# List all identities
cilium identity list

# Get labels for a specific identity
cilium identity get <identity-number>
```

### Troubleshooting

```bash
# Check if Cilium agent is healthy
cilium status

# View Cilium agent logs
kubectl -n kube-system logs ds/cilium -c cilium-agent --tail=100

# Check eBPF map status
kubectl exec -n kube-system ds/cilium -- cilium bpf ct list global | head

# Monitor policy verdicts in real-time
kubectl exec -n kube-system ds/cilium -- cilium monitor --type policy-verdict

# Debug a specific pod's connectivity
kubectl exec -n kube-system ds/cilium -- cilium endpoint list | grep <pod-name>
```

---

## War Story: The Cluster Mesh Migration That Almost Wasn't

*A fintech company was migrating from an aging Kubernetes cluster (v1.24) to a new one (v1.29). They couldn't afford downtime -- the payment API processed $2M per hour.*

The plan: run both clusters simultaneously, use Cilium Cluster Mesh to share the payment service across both clusters, then gradually shift traffic.

**Week 1**: Cluster Mesh connected. Global services worked. Everything looked perfect in staging.

**Week 2, Day 1 (Monday)**: Production migration started. Cluster Mesh connected. Global service annotation applied. Traffic began flowing to both clusters. Monitoring showed healthy requests.

**Week 2, Day 2 (Tuesday, 3:17 PM)**: Alerts fired. Payment failures spiking. But only from the *new* cluster.

The engineer ran:
```bash
hubble observe --from-pod new-cluster/payment-api --verdict DROPPED --protocol tcp
```

Output showed drops on port 5432 -- the payment API in the new cluster couldn't reach PostgreSQL in the old cluster. Cross-cluster database traffic was being blocked.

**Root cause**: The CiliumClusterwideNetworkPolicy on the old cluster only allowed ingress from identities with `cluster: old-cluster` labels. Pods in the new cluster had `cluster: new-cluster`. The policy was written 18 months earlier, before Cluster Mesh was even planned.

```yaml
# The offending policy (old cluster)
spec:
  endpointSelector:
    matchLabels:
      app: postgres
  ingress:
  - fromEndpoints:
    - matchLabels:
        cluster: old-cluster  # Oops -- blocks new cluster pods
```

**Fix**: Update the policy to use identity-based matching without the cluster label, or add an explicit rule for the new cluster's identity range.

**Time to diagnose**: 6 minutes (thanks to Hubble).
**Time it would have taken without Hubble**: Hours. The "payment API works on old cluster but not new cluster" symptom points to a dozen possible causes.

**Lesson**: When planning Cluster Mesh migrations, audit every CiliumNetworkPolicy and CiliumClusterwideNetworkPolicy for assumptions about cluster-local identities.

---

## Common Mistakes

| Mistake | Why It Hurts | How To Avoid |
|---------|--------------|--------------|
| **Overlapping pod CIDRs with Cluster Mesh** | Packets can't be routed; silent failures | Plan CIDR allocation before deploying clusters |
| **Forgetting `service.cilium.io/global: "true"`** | Service stays cluster-local; Cluster Mesh doesn't help | Annotate every service that needs cross-cluster discovery |
| **Using `policyEnforcementMode: always` without baseline policies** | All traffic drops immediately, including DNS | Deploy allow-dns and allow-health policies BEFORE switching to `always` |
| **BGP with wrong ASN** | Peering session never establishes; stays in "active" state | Verify ASNs match what your network team configured on the router |
| **Assuming operator downtime = outage** | Panicking when operator restarts | Know that existing networking continues; only new IPAM allocations pause |
| **Mixing K8s NetworkPolicy and CiliumNetworkPolicy** | Both apply, creating confusing interactions | Pick one. CiliumNetworkPolicy is strictly superior. |
| **Not testing Cluster Mesh with connectivity test** | Missing subtle cross-cluster failures | Always run `cilium connectivity test --multi-cluster` after connecting clusters |

---

## Quiz

### Question 1
What is the role of the Cilium Operator, and what happens if it goes down?

<details>
<summary>Show Answer</summary>

The Cilium Operator handles **cluster-wide coordination tasks**:
- IPAM (allocating pod CIDR ranges to nodes)
- CRD management and garbage collection of stale CiliumIdentity objects
- Cluster Mesh API server management

**If the operator goes down:**
- Existing networking, policies, and traffic continue to work (the agent handles all data plane operations)
- New pod CIDR allocations will fail (new nodes can't join)
- Identity garbage collection pauses (stale identities accumulate)
- No immediate impact on running workloads

This is a key distinction: the agent is the data plane, the operator is control plane coordination.

</details>

### Question 2
Explain the three policy enforcement modes and when you would use each.

<details>
<summary>Show Answer</summary>

| Mode | Behavior | Use Case |
|------|----------|----------|
| `default` | Traffic allowed if no policy selects the endpoint. Once any policy selects an endpoint, unmatched traffic is denied for that direction. | Development, staging, gradual policy rollout |
| `always` | All traffic denied by default, even with no policies. Must explicitly allow everything. | Production zero-trust environments |
| `never` | Policy enforcement disabled. All traffic flows freely. | Debugging to rule out policy issues. Never in production. |

Example scenario: You switch to `always` mode. Immediately, all pods lose DNS resolution because there's no policy allowing DNS egress. You need to deploy a CiliumClusterwideNetworkPolicy allowing `toEntities: [dns]` before (or simultaneously with) enabling `always` mode.

</details>

### Question 3
What are three features CiliumNetworkPolicy supports that standard Kubernetes NetworkPolicy does not?

<details>
<summary>Show Answer</summary>

1. **L7 HTTP filtering** -- match on HTTP method, path, and headers (e.g., allow GET /api/products but deny DELETE /api/products)
2. **FQDN-based egress** -- allow traffic to `api.stripe.com` by domain name, with automatic IP tracking via DNS interception
3. **Entity-based rules** -- use semantic entities like `dns`, `kube-apiserver`, `health`, `world` instead of tracking IP addresses
4. **Cluster-wide scope** -- CiliumClusterwideNetworkPolicy applies across all namespaces
5. **Explicit deny rules** -- K8s NetworkPolicy is allow-only; Cilium supports deny rules that override allows
6. **L7 Kafka/gRPC filtering** -- protocol-aware filtering beyond HTTP

(Any three of these is a complete answer.)

</details>

### Question 4
What are the requirements for connecting two clusters with Cluster Mesh?

<details>
<summary>Show Answer</summary>

1. **Shared CA certificate** -- both clusters must trust the same certificate authority for mTLS between ClusterMesh API servers and agents
2. **Non-overlapping pod CIDRs** -- pod IP ranges must be unique across clusters (e.g., Cluster A uses 10.244.0.0/16, Cluster B uses 10.245.0.0/16)
3. **Network connectivity** -- Cilium agents must be able to reach the remote ClusterMesh API server (port 2379 by default)
4. **Unique cluster names and IDs** -- each cluster needs a distinct name (string) and ID (1-255)
5. **Compatible Cilium versions** -- minor version skew is tolerated, but major versions must match

</details>

### Question 5
A service in Cluster A has `service.cilium.io/affinity: "local"`. When does traffic go to Cluster B?

<details>
<summary>Show Answer</summary>

With `local` affinity, traffic is routed to endpoints in the **local cluster** (Cluster A) whenever local endpoints are available.

Traffic goes to Cluster B **only when there are zero healthy endpoints in Cluster A**. This provides:
- **Low latency** during normal operations (local routing)
- **Failover** when local endpoints are unavailable (cross-cluster fallback)

This is the most common production configuration for Cluster Mesh because it minimizes cross-cluster latency while providing high availability.

</details>

### Question 6
What does `exportPodCIDR: true` do in a CiliumBGPPeeringPolicy?

<details>
<summary>Show Answer</summary>

`exportPodCIDR: true` causes the Cilium agent on each node to advertise its **pod CIDR range** to the BGP peer (typically an external router).

For example, if Node-1 has pod CIDR 10.244.1.0/24, the BGP advertisement tells the router: "To reach 10.244.1.0/24, send traffic to Node-1's IP."

This makes pod IPs directly routable from outside the cluster, eliminating the need for NodePort or LoadBalancer services for internal (east-west) traffic between the cluster and the corporate network.

</details>

### Question 7
You apply a CiliumNetworkPolicy with an L7 HTTP rule allowing only `GET /api/v1/users`. A pod tries to `POST /api/v1/users`. What happens at the network level?

<details>
<summary>Show Answer</summary>

The POST request is **denied at the network layer by Cilium's eBPF proxy**.

Here is the sequence:
1. The TCP connection to port 8080 is allowed (the L4 port rule matches)
2. Cilium's L7 proxy (Envoy-based) intercepts the HTTP request
3. The proxy inspects the HTTP method and path
4. `POST /api/v1/users` does not match the allowed rule (`GET /api/v1/users`)
5. The proxy returns an **HTTP 403 Forbidden** response
6. Hubble records this as a DROPPED flow with reason "Policy denied (L7)"

Key point: L7 policies work by inserting an Envoy proxy into the data path. The L4 connection is established, but the L7 proxy inspects and filters individual HTTP requests within that connection.

</details>

### Question 8
How does Cilium's identity-based policy enforcement achieve O(1) lookup time?

<details>
<summary>Show Answer</summary>

Cilium stores policy decisions in **eBPF hash maps** in the Linux kernel.

The process:
1. Each unique set of security-relevant labels gets a **numeric identity** (e.g., `{app=frontend, env=prod}` = identity 48291)
2. The policy engine pre-computes all allowed `(source identity, destination identity, port)` tuples
3. These tuples are inserted into an eBPF hash map
4. When a packet arrives, the eBPF program reads the source identity (from the packet or the identity-to-IP mapping) and the destination identity
5. It does a **single hash map lookup**: `key = (src_id, dst_id, port)` -> `value = ALLOW or DENY`
6. Hash map lookup is O(1) regardless of how many policies or endpoints exist

This is fundamentally different from iptables, which does a **linear walk** through rules (O(n) where n = number of rules). At scale (thousands of services, hundreds of policies), the difference is enormous.

</details>

---

## Hands-On Exercise: Cluster Mesh and BGP Fundamentals

### Objective

Set up a two-cluster environment with Cilium Cluster Mesh, deploy a global service, verify cross-cluster connectivity, and configure a basic CiliumBGPPeeringPolicy.

### Part 1: Create Two Clusters

```bash
# Cluster A configuration
cat > cluster-a.yaml << 'EOF'
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
name: cluster-a
networking:
  disableDefaultCNI: true
  podSubnet: "10.244.0.0/16"
  serviceSubnet: "10.96.0.0/16"
nodes:
- role: control-plane
- role: worker
EOF

# Cluster B configuration (different pod CIDR!)
cat > cluster-b.yaml << 'EOF'
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
name: cluster-b
networking:
  disableDefaultCNI: true
  podSubnet: "10.245.0.0/16"
  serviceSubnet: "10.97.0.0/16"
nodes:
- role: control-plane
- role: worker
EOF

# Create both clusters
kind create cluster --config cluster-a.yaml
kind create cluster --config cluster-b.yaml
```

### Part 2: Install Cilium on Both Clusters

```bash
# Install on Cluster A (cluster ID = 1)
cilium install \
  --context kind-cluster-a \
  --set cluster.name=cluster-a \
  --set cluster.id=1 \
  --set hubble.enabled=true \
  --set hubble.relay.enabled=true

# Install on Cluster B (cluster ID = 2)
cilium install \
  --context kind-cluster-b \
  --set cluster.name=cluster-b \
  --set cluster.id=2 \
  --set hubble.enabled=true \
  --set hubble.relay.enabled=true

# Wait for both to be ready
cilium status --context kind-cluster-a --wait
cilium status --context kind-cluster-b --wait
```

### Part 3: Enable and Connect Cluster Mesh

```bash
# Enable Cluster Mesh on both clusters
cilium clustermesh enable --context kind-cluster-a --service-type NodePort
cilium clustermesh enable --context kind-cluster-b --service-type NodePort

# Wait for Cluster Mesh to be ready
cilium clustermesh status --context kind-cluster-a --wait
cilium clustermesh status --context kind-cluster-b --wait

# Connect the clusters
cilium clustermesh connect \
  --context kind-cluster-a \
  --destination-context kind-cluster-b

# Verify the connection
cilium clustermesh status --context kind-cluster-a --wait
```

### Part 4: Deploy a Global Service

```bash
# Deploy a backend service in Cluster A
kubectl --context kind-cluster-a create namespace demo
kubectl --context kind-cluster-a -n demo apply -f - << 'EOF'
apiVersion: apps/v1
kind: Deployment
metadata:
  name: echo
spec:
  replicas: 2
  selector:
    matchLabels:
      app: echo
  template:
    metadata:
      labels:
        app: echo
    spec:
      containers:
      - name: echo
        image: cilium/json-mock:v1.3.8
        ports:
        - containerPort: 8080
---
apiVersion: v1
kind: Service
metadata:
  name: echo
  annotations:
    service.cilium.io/global: "true"
    service.cilium.io/affinity: "local"
spec:
  selector:
    app: echo
  ports:
  - port: 8080
EOF

# Deploy the same service in Cluster B
kubectl --context kind-cluster-b create namespace demo
kubectl --context kind-cluster-b -n demo apply -f - << 'EOF'
apiVersion: apps/v1
kind: Deployment
metadata:
  name: echo
spec:
  replicas: 2
  selector:
    matchLabels:
      app: echo
  template:
    metadata:
      labels:
        app: echo
    spec:
      containers:
      - name: echo
        image: cilium/json-mock:v1.3.8
        ports:
        - containerPort: 8080
---
apiVersion: v1
kind: Service
metadata:
  name: echo
  annotations:
    service.cilium.io/global: "true"
    service.cilium.io/affinity: "local"
spec:
  selector:
    app: echo
  ports:
  - port: 8080
EOF
```

### Part 5: Test Cross-Cluster Connectivity

```bash
# Deploy a test client in Cluster A
kubectl --context kind-cluster-a -n demo run client \
  --image=curlimages/curl --restart=Never --command -- sleep 3600

# Wait for client pod to be ready
kubectl --context kind-cluster-a -n demo wait --for=condition=ready pod/client --timeout=60s

# Test: traffic should go to local (Cluster A) endpoints due to affinity
kubectl --context kind-cluster-a -n demo exec client -- \
  curl -s echo:8080

# Now scale down Cluster A's echo to 0 replicas
kubectl --context kind-cluster-a -n demo scale deployment echo --replicas=0

# Wait for endpoints to drain (15-30 seconds)
sleep 15

# Test again: traffic should now fail over to Cluster B
kubectl --context kind-cluster-a -n demo exec client -- \
  curl -s echo:8080

# Restore Cluster A replicas
kubectl --context kind-cluster-a -n demo scale deployment echo --replicas=2
```

### Part 6: Explore BGP Configuration (Conceptual)

BGP requires external router infrastructure that kind clusters don't provide. This section is for understanding the CRD structure.

```bash
# Apply a BGP peering policy (it won't establish a session
# without a real router, but you can verify the CRD is accepted)
kubectl --context kind-cluster-a apply -f - << 'EOF'
apiVersion: cilium.io/v2alpha1
kind: CiliumBGPPeeringPolicy
metadata:
  name: lab-bgp
spec:
  nodeSelector:
    matchLabels:
      kubernetes.io/os: linux
  virtualRouters:
  - localASN: 65001
    exportPodCIDR: true
    neighbors:
    - peerAddress: "172.18.0.100/32"
      peerASN: 65000
EOF

# Verify the policy was accepted
kubectl --context kind-cluster-a get ciliumbgppeeringpolicy

# Check BGP status (will show "active" since no real peer exists)
cilium bgp peers --context kind-cluster-a
```

### Success Criteria

- [ ] Both clusters have Cilium installed with unique cluster names and IDs
- [ ] Cluster Mesh status shows "connected" between clusters
- [ ] Global service annotation (`service.cilium.io/global: "true"`) applied
- [ ] Service with `local` affinity routes to local cluster endpoints
- [ ] When local endpoints are scaled to 0, traffic fails over to the remote cluster
- [ ] CiliumBGPPeeringPolicy CRD is accepted by the cluster
- [ ] `cilium clustermesh status` shows healthy connection

### Cleanup

```bash
kind delete cluster --name cluster-a
kind delete cluster --name cluster-b
rm cluster-a.yaml cluster-b.yaml
```

---

## Next Module

Return to the [CCA Learning Path](README.md) to review other exam domains and identify any remaining study areas.

---

*"Multi-cluster networking used to require a PhD in network engineering. Cilium Cluster Mesh makes it a kubectl annotation."*
